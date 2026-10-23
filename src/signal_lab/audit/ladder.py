"""
The simulated-IC ladder: planted signals through the real solver, engine and
cost model, one cell per (ic, horizon, seed, cost multiplier, turnover cap).

Why a ladder and not the fundamental law. Under long-only, a cash cap, a
position cap and a turnover cap, on a correlated universe, with persistent
signals, Grinold's IR = IC sqrt(BR) TC is unreliable in both BR and TC. The
ladder measures the whole chain instead: a signal of known IC and known speed
is solved weekly with the constraints the mandate actually imposes, run through
the engine that charges what trading actually costs, and the net IR is read
off the result. `breadth.py` reports what the law would have said, so the
difference is visible.

Two things the engine does not know about are handled here:

  * The solver needs the DRIFTED book to price the trade. The engine hands it
    to a weight rule that accepts `drifted=`; the rule below does.
  * The covariance at a date is the same for every cell, so it is estimated
    once per date and cached on the universe object. With four ICs, four
    horizons and three seeds that is a forty-eight-fold saving on the slowest
    step after the solve itself.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.audit.signals import (
    POOLED,
    SCORE_SHUFFLE,
    SCORE_SHUFFLES,
    SHUFFLES,
    SPAN_SHUFFLE,
    TRUTH_SHUFFLE,
    PlantedSignal,
    plant_signal,
    realised_ic,
    signal_autocorrelation,
)
from signal_lab.audit.transfer import path_transfer
from signal_lab.harness.costs import CostModel
from signal_lab.harness.engine import (
    PortfolioPath,
    constant_exposures,
    rebalance_dates,
    run_walk_forward,
)
from signal_lab.loaders.base import ReturnPanel
from signal_lab.params import Params, get_params
from signal_lab.portfolio.covariance import ShrunkCovariance, period_returns, trailing_covariance
from signal_lab.portfolio.rebalance import RebalanceStep
from signal_lab.stats.calibration import annual_bias

BENCHMARK_SECTION_PREFIX = "18."

# The cell family that calibrates the ruler itself (decisions/0027).
FRICTIONLESS = "frictionless"
BASELINE = "baseline"


# --- the universe the audit runs on ---------------------------------------


@dataclass
class AuditUniverse:
    """Everything a cell needs that does not depend on the cell."""

    panel: ReturnPanel  # daily, development window, holdable series only
    legs: pd.DataFrame  # daily returns of the benchmark legs
    leg_weights: pd.Series  # over the legs, sums to one
    holdable: list[str]
    cash: list[str]
    dates: pd.DatetimeIndex  # every rebalance date the panel supports
    weekly: pd.DataFrame  # period returns, holdable + legs, indexed on dates[1:]
    benchmark_weekly: pd.Series  # the 50/50 benchmark's period return
    window: int
    first_audit_date: pd.Timestamp  # first rebalance with a full covariance window
    _cov_cache: dict[tuple[pd.Timestamp, float | None, str], ShrunkCovariance] = field(
        default_factory=dict, repr=False
    )

    @property
    def leg_ids(self) -> list[str]:
        return list(self.legs.columns)

    def covariance(
        self,
        date: pd.Timestamp,
        vol_halflife: float | None = None,
        vol_overlay: str = "per_series",
    ) -> ShrunkCovariance:
        """Trailing covariance as of `date`, holdable + legs, cached.

        The cache is keyed on the halflife as well as the date: one universe is
        shared across cells, and two cells that size their volatilities
        differently do not share a covariance.
        """
        date = pd.Timestamp(date)
        cache_key = (date, vol_halflife, vol_overlay)
        cov = self._cov_cache.get(cache_key)
        if cov is None:
            cov = trailing_covariance(
                self.weekly,
                date,
                self.window,
                legs=self.leg_ids,
                vol_halflife=vol_halflife,
                vol_overlay=vol_overlay,
            )
            self._cov_cache[cache_key] = cov
        return cov

    def audit_dates(self) -> pd.DatetimeIndex:
        return self.dates[self.dates >= self.first_audit_date]

    def engine_panel(self) -> ReturnPanel:
        """The daily panel from the first audit date, for the engine."""
        start = self.first_audit_date
        return ReturnPanel(
            levels=self.panel.levels.loc[self.panel.levels.index >= start],
            returns=self.panel.returns.loc[self.panel.returns.index >= start],
            meta=self.panel.meta,
            splices=self.panel.splices,
            snapshot_id=self.panel.snapshot_id,
            source=self.panel.source,
        )

    def panel_hash(self) -> str:
        """A hash of the daily returns the audit ran on, so a table is regenerable."""
        h = hashlib.sha256()
        for frame in (self.panel.returns, self.legs):
            h.update(",".join(map(str, frame.columns)).encode())
            h.update(np.ascontiguousarray(frame.fillna(-999.0).values).tobytes())
        return h.hexdigest()


def audit_cost_model(
    universe: AuditUniverse, params: Params, spread_multiplier: float = 1.0
) -> CostModel:
    """
    The cost model for a cell, with the PANEL's buckets filling the gaps in
    the universe map.

    `CostModel` maps buckets from `investable_universe.csv` by ticker. The
    synthetic panel's ids (`SYN000`...) are not in that file, so on the first
    lean audit every synthetic series fell to `default_bucket` and paid the
    high bucket's 20bp spread and 35bp fee -- a cost drag of exactly
    35bp + 20bp per unit of turnover, residual 5e-9 -- even though the panel
    carries its own `cost_bucket` for each series. decisions/0002 charges the
    dear bucket to an instrument WITH NO BUCKET; these had one.

    The universe map still wins wherever it has an entry, so a Bloomberg run,
    whose holdable tickers are all in the map and whose panel buckets come from
    the same file, is costed exactly as before. A bucket name the cost params do
    not define is ignored and falls to the default. decisions/0027.
    """
    model = CostModel(params, spread_multiplier=spread_multiplier)
    known = set(params.require("costs.buckets"))
    from_panel = {
        sid: str(meta.cost_bucket)
        for sid, meta in universe.panel.meta.items()
        if str(getattr(meta, "cost_bucket", "")) in known
    }
    model.buckets = {**from_panel, **model.buckets}
    return model


def _is_cash(section: str) -> bool:
    return "cash" in (section or "").lower()


def build_universe(
    panel: ReturnPanel,
    legs: pd.DataFrame,
    leg_weights: pd.Series,
    params: Params | None = None,
    investable: dict[str, bool] | None = None,
) -> AuditUniverse:
    """
    Assemble the audit universe from a daily panel and the benchmark legs.

    Holdable: unhedged, not a benchmark leg, and `investable` where the map
    says (an unmapped series is holdable -- the synthetic panel has no map).
    Cash: any holdable series whose section names it. The legs are carried in
    the weekly frame so the covariance sees them; they are never holdable.
    """
    params = params or get_params()
    window = int(params.require("audit.covariance.window_periods"))
    day = str(params.get("audit.rebalance_day", "FRI"))
    investable = investable or {}
    holdable = [
        s
        for s, m in panel.meta.items()
        if not m.hedged
        and not str(m.section).startswith(BENCHMARK_SECTION_PREFIX)
        and investable.get(s, True)
        and s in panel.returns.columns
        and s not in legs.columns
    ]
    if not holdable:
        raise ValueError("no holdable series in the panel")
    cash = [s for s in holdable if _is_cash(panel.meta[s].section)]

    weights = leg_weights.reindex(legs.columns).astype(float)
    if abs(float(weights.sum()) - 1.0) > 1e-9:
        raise ValueError("benchmark leg weights must sum to one")

    daily = panel.returns[holdable].join(legs, how="outer").sort_index()
    daily = daily.loc[daily.index.isin(panel.returns.index)]
    dates = rebalance_dates(daily.index, day, params)
    weekly = period_returns(daily, dates)
    bench_weekly = (weekly[legs.columns] * weights).sum(axis=1, min_count=len(legs.columns))

    # First date with a full window for the legs themselves; holdables enter
    # as their own windows fill.
    legs_ok = weekly[legs.columns].notna().all(axis=1)
    full = legs_ok.rolling(window, min_periods=window).sum() >= window
    if not full.any():
        raise ValueError(f"the benchmark legs never have {window} periods of history")
    first = pd.Timestamp(full[full].index[0])

    return AuditUniverse(
        panel=ReturnPanel(
            levels=panel.levels[holdable],
            returns=panel.returns[holdable],
            meta={s: panel.meta[s] for s in holdable},
            splices=panel.splices,
            snapshot_id=panel.snapshot_id,
            source=panel.source,
        ),
        legs=legs,
        leg_weights=weights,
        holdable=holdable,
        cash=cash,
        dates=dates,
        weekly=weekly,
        benchmark_weekly=bench_weekly,
        window=window,
        first_audit_date=first,
    )


# --- one cell ------------------------------------------------------------------


class _FromParams:
    """Singleton marker: "read this from params" -- distinct from `None`, which
    on `vol_halflife` means "no overlay" and must keep meaning it."""

    _instance: _FromParams | None = None

    def __new__(cls) -> _FromParams:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "FROM_PARAMS"

    def __copy__(self) -> _FromParams:
        return self

    def __deepcopy__(self, memo: dict) -> _FromParams:
        return self


FROM_PARAMS = _FromParams()


@dataclass(frozen=True)
class AuditCell:
    ic: float
    horizon: int
    seed: int
    cost_multiplier: float = 1.0
    turnover_cap: float | None = None  # annualised traded notional; None = no annual wall
    per_rebalance_cap: float | None = None  # traded notional in ONE session; None = uncapped
    tag: str = "base"
    # How the planted truth is standardised. `pooled` is the default and what
    # every run before 2026-09-17 used; `cross_sectional` plants purely relative
    # information. See `audit.signals` and the standardisation probe.
    standardise: str = POOLED
    # Halflife in weeks for the covariance's volatilities; the correlation keeps
    # the full window. `None` is the equal-weighted estimate every run before
    # 2026-09-17 used. See `portfolio.covariance.rescale_volatility` and the TE
    # path probe, which is what this exists to test.
    vol_halflife: float | None | _FromParams = FROM_PARAMS
    # How that halflife is applied: `per_series` moves each volatility and so
    # the composition too; `scalar` moves only the risk level. Ignored when
    # `vol_halflife` is None.
    #
    # decisions/0042 (HANDOFF task 42): both default to `FROM_PARAMS`, which reads
    # `audit.covariance.vol_overlay` -- the overlay is policy. `None` keeps meaning "no
    # overlay", the equal-weighted estimate, so every historical key still
    # decodes; see `resolve_vol_overlay`.
    vol_overlay: str | _FromParams = FROM_PARAMS
    # decisions/0036 section 4b: the score is blended from a block-shuffled truth.
    # Everything else about the cell is its live twin's, so the key must say so.
    baseline: bool = False
    # HANDOFF task 25: what the baseline shuffles -- the truth alone (the
    # default, and every baseline before it) or the whole score -- and, for the
    # score shuffle, which permutation. The defaults leave every existing key as it was.
    shuffle: str = TRUTH_SHUFFLE
    perm: int = 0
    # HANDOFF task 32: override `constraints.turnover.penalty.coefficient` for this
    # cell only. `None` (the default) reads params, exactly as every cell before it.
    shadow_coefficient: float | None = None
    # HANDOFF task 36 / 39, decisions/0040: which shadow-cost form the cell
    # prices turnover with. `None` (the default) reads
    # `constraints.turnover.penalty.form` from params, exactly as
    # `shadow_coefficient` already does -- see `resolve_shadow_form`. `trailing`
    # is the pre-0040 flat per-unit cost on PRE-trade trailing turnover, kept in
    # code as an explicit override so earlier runs stay reproducible. `created`
    # prices the marginal unit at the turnover IT creates (decisions/0040's
    # ruling), as a convex term the solver sees instead of a per-unit cost.
    shadow_form: str | None = None

    def __post_init__(self) -> None:
        if self.shuffle not in SHUFFLES:
            raise ValueError(f"shuffle must be one of {SHUFFLES}, got {self.shuffle!r}")
        if self.shuffle in SCORE_SHUFFLES and not self.baseline:
            raise ValueError("a score shuffle is a baseline; set baseline=True")
        if self.shuffle == TRUTH_SHUFFLE and self.perm != 0:
            raise ValueError("perm indexes the score shuffle only")
        if self.shadow_form not in (None, "trailing", "created"):
            raise ValueError(
                f"shadow_form must be None, 'trailing' or 'created', got {self.shadow_form!r}"
            )

    def key(self, params: Params | None = None) -> str:
        """The cell's identity, with the overlay and its halflife RESOLVED
        (decisions/0042): a cell that follows params reads `..._vhl26scalar`, an
        explicit `vol_halflife=None` cell keeps its pre-task-42 key. The shadow
        form is resolved too (task 43, F3): `_created` is appended when the cell
        PRICES turnover with the created form, explicit or read from params, so a
        default cell's key says how it priced. Frictionless cells price nothing."""
        cap = "none" if self.turnover_cap is None else f"{self.turnover_cap:.2f}"
        per = "none" if self.per_rebalance_cap is None else f"{self.per_rebalance_cap:.2f}"
        key = (
            f"ic{self.ic:.2f}_h{self.horizon}_s{self.seed}"
            f"_c{self.cost_multiplier:.1f}_t{cap}_r{per}"
        )
        if self.standardise != POOLED:
            key = f"{key}_{self.standardise}"
        halflife, overlay = resolve_vol_overlay(self, params)
        if halflife is not None:
            key = f"{key}_vhl{halflife:g}"
            if overlay != "per_series":
                key = f"{key}{overlay}"
        if self.baseline:
            key = f"{key}_baseline"
            if self.shuffle != TRUTH_SHUFFLE:
                key = f"{key}_{self.shuffle.replace('_', '')}_p{self.perm:02d}"
        if self.shadow_coefficient is not None:
            key = f"{key}_shadow{self.shadow_coefficient:g}"
        if (
            self.tag != FRICTIONLESS
            and resolve_shadow_form(self, params or get_params()) == "created"
        ):
            key = f"{key}_created"
        return f"{key}_frictionless" if self.tag == FRICTIONLESS else key


def resolve_vol_overlay(cell: AuditCell, params: Params | None = None) -> tuple[float | None, str]:
    """
    `(halflife_weeks, overlay)` the cell's covariance is built with
    (decisions/0042, HANDOFF task 42). An explicit value on the cell wins, and
    `None` is an explicit "no overlay" -- the equal-weighted estimate every run
    before task 42 used -- so `vol_halflife=None` keeps every historical key.
    `FROM_PARAMS` reads `audit.covariance.vol_overlay` (`halflife_weeks`, `form`);
    params with no such block mean no overlay.

    An explicit halflife with the overlay left at `FROM_PARAMS` is the legacy
    `per_series` form, not params' form: it is the call every pre-task-42 cell
    meant, and a halflife of 26 must not silently change shape under it. With no
    halflife the overlay is `per_series` by convention, as the key ignores it.
    """
    halflife = cell.vol_halflife
    overlay = cell.vol_overlay
    if halflife is FROM_PARAMS or overlay is FROM_PARAMS:
        params = params or get_params()
        cfg = params.get("audit.covariance.vol_overlay", None) or {}
        if halflife is FROM_PARAMS:
            hl = cfg.get("halflife_weeks")
            halflife = None if hl is None else float(hl)
            if overlay is FROM_PARAMS:
                overlay = str(cfg.get("form", "scalar")) if halflife is not None else "per_series"
        else:
            overlay = "per_series"
    if halflife is None:
        overlay = "per_series"
    return halflife, str(overlay)


def resolve_shadow_form(cell: AuditCell, params: Params) -> str:
    """
    `cell.shadow_form`'s effective value: `"trailing"` or `"created"`,
    `AuditCell.key()`'s vocabulary. An explicit override on the cell wins;
    `None` (the default) reads `constraints.turnover.penalty.form` from
    params, exactly as `shadow_coefficient` already does -- `linear` maps to
    `trailing`, `created_marginal` to `created` (decisions/0040). HANDOFF
    task 39: this is what makes `linear` not the one reached by default once
    params adopts `created_marginal`.
    """
    if cell.shadow_form is not None:
        return cell.shadow_form
    form = str(params.get("constraints.turnover.penalty.form", "linear") or "linear")
    return "created" if form == "created_marginal" else "trailing"


class _OptimiserRule(RebalanceStep):
    """
    The weight rule for one cell: the portfolio's rebalance step
    (`portfolio.rebalance.RebalanceStep`: a solve at every rebalance under a
    per-session cap and a progressive shadow cost), fed the planted signal's
    alpha. The cell's settings are resolved here; the rebalance is not.
    """

    def __init__(
        self,
        universe: AuditUniverse,
        signal: PlantedSignal,
        cell: AuditCell,
        params: Params,
        solver: str,
    ):
        self.signal = signal
        self.cell = cell
        vol_halflife, vol_overlay = resolve_vol_overlay(cell, params)
        override = cell.shadow_coefficient
        super().__init__(
            universe,
            audit_cost_model(universe, params, cell.cost_multiplier),
            params,
            solver,
            shadow_form=resolve_shadow_form(cell, params),
            vol_halflife=vol_halflife,
            vol_overlay=vol_overlay,
            shadow_coeff=(
                float(override)
                if override is not None
                else float(params.get("constraints.turnover.penalty.coefficient", 0) or 0)
            ),
            per_rebalance_cap=cell.per_rebalance_cap,
            turnover_cap=cell.turnover_cap,
        )

    def __call__(self, date: pd.Timestamp, _panel: ReturnPanel, drifted: pd.Series | None = None):
        date = pd.Timestamp(date)
        cov = self.u.covariance(date, self.vol_halflife, self.vol_overlay)
        hold = [h for h in self.u.holdable if h in cov.ids]
        alpha = self.signal.alpha.reindex(index=[date], columns=hold).iloc[0].fillna(0.0)
        return self.step(date, alpha, drifted)


def _gross_information_ratio(path, periods_per_year: float) -> float:
    """
    `path.information_ratio()`, on gross returns instead of net (decisions/0004:
    reported for diagnostics, never for ranking or the leaderboard).
    """
    active = (path.gross_returns - path.benchmark_returns).dropna()
    if len(active) < 2:
        return float("nan")
    sd = float(active.std())
    if not np.isfinite(sd) or sd < 1e-12:
        return float("nan")
    return float(active.mean() * periods_per_year / (sd * np.sqrt(periods_per_year)))


def run_cell(
    universe: AuditUniverse,
    cell: AuditCell,
    params: Params | None = None,
    solver: str | None = None,
) -> tuple[dict[str, Any], PortfolioPath]:
    """One cell: plant, solve weekly, run the engine, summarise."""
    params = params or get_params()
    if cell.tag == FRICTIONLESS:
        return run_frictionless(universe, cell, params)
    solver = solver or str(params.get("audit.solver", "auto"))
    started = time.time()

    signal = _plant(universe, cell)
    rule = _OptimiserRule(universe, signal, cell, params, solver)
    vol_halflife, vol_overlay = rule.vol_halflife, rule.vol_overlay
    engine_panel = universe.engine_panel()
    exposures = constant_exposures(pd.DataFrame(0.0, index=universe.holdable, columns=["f0"]))
    path = run_walk_forward(
        engine_panel,
        rule,
        universe.benchmark_weekly,  # per period already; the engine compounds it to itself
        exposures,
        cost_model=audit_cost_model(universe, params, cell.cost_multiplier),
        params=params,
        rebalance_day=str(params.get("audit.rebalance_day", "FRI")),
        cash_instrument=universe.cash[0] if len(universe.cash) == 1 else None,
    )
    if len(universe.cash) > 1:
        path.cash_weights = path.weights.reindex(columns=universe.cash).fillna(0.0).sum(axis=1)

    te = path.tracking_error().dropna()
    ic = realised_ic(signal)
    diag = pd.DataFrame(rule.diagnostics)
    row = {
        "tag": cell.tag,
        "key": cell.key(params),
        "baseline": cell.baseline,
        "shuffle": cell.shuffle if cell.baseline else "",
        "perm": cell.perm,
        "ic": cell.ic,
        "horizon": cell.horizon,
        "seed": cell.seed,
        "cost_multiplier": cell.cost_multiplier,
        "turnover_cap": cell.turnover_cap,
        "per_rebalance_cap": cell.per_rebalance_cap,
        "shadow_coefficient": cell.shadow_coefficient,
        "shadow_form": rule.shadow_form,
        "vol_halflife": vol_halflife,
        "vol_overlay": vol_overlay if vol_halflife is not None else "",
        "turnover_per_rebalance_max": float(path.turnover.max()),
        "turnover_per_rebalance_p95": float(path.turnover.quantile(0.95)),
        "turnover_from_repairs_annual": rule.repair_turnover * rule.ppy / max(len(path.dates), 1),
        "shadow_bps_mean": float(diag["shadow_bps"].mean()),
        "shadow_bps_max": float(diag["shadow_bps"].max()),
        "shadow_paid_bps_mean": float(diag["shadow_paid_bps"].mean())
        if "shadow_paid_bps" in diag.columns
        else float("nan"),
        # HANDOFF task 36 / decisions/0040 "Why": the lag-53 echo the friction
        # sweep found (a large trade ages out of the trailing window and the
        # backlog trades at once), for every cell so the created form's effect
        # on it is visible beside the trailing form's.
        "turnover_autocorr_lag26": float(path.turnover.autocorr(26)),
        "turnover_autocorr_lag52": float(path.turnover.autocorr(52)),
        "turnover_autocorr_lag53": float(path.turnover.autocorr(53)),
        "turnover_autocorr_lag78": float(path.turnover.autocorr(78)),
        "net_ir": path.information_ratio(),
        "gross_ir": _gross_information_ratio(path, rule.ppy),
        "active_return_annual": float(path.active_returns.mean() * rule.ppy),
        "active_vol_annual": float(path.active_returns.std() * np.sqrt(rule.ppy)),
        "te_p95": float(te.quantile(0.95)) if len(te) else float("nan"),
        "te_max": float(te.max()) if len(te) else float("nan"),
        "te_ex_ante_mean": float(diag["te_ex_ante"].mean()),
        "turnover_annual": path.annualised_turnover(),
        "turnover_p95_rolling_1y": rolling_annual_turnover_quantile(path, rule.ppy, 0.95),
        "turnover_max_rolling_1y": rolling_annual_turnover_quantile(path, rule.ppy, 1.0),
        "cost_drag_annual": path.total_cost_drag(),
        "max_active_drawdown": path.max_active_drawdown(),
        "max_cash": float(path.cash_weights.max()),
        "n_positions_max": int(path.n_positions().max()),
        "n_positions_mean": float(path.n_positions().mean()),
        "n_holdable_mean": float(diag["n_holdable"].mean()),
        "realised_ic_pooled": ic["pooled"],
        "realised_ic_cross_sectional": ic["cross_sectional"],
        "realised_ic_cross_sectional_pearson": ic["cross_sectional_pearson"],
        "realised_ic_cross_sectional_demeaned": ic["cross_sectional_demeaned"],
        "signal_phi": signal_autocorrelation(signal.score),
        "te_binding_share": float(diag["te_binding"].mean()),
        "turnover_binding_share": float(diag["turnover_binding"].mean()),
        "cash_binding_share": float(diag["cash_binding"].mean()),
        "positions_capped_share": float(diag["positions_capped"].mean()),
        "infeasible_te_share": float(diag["status"].str.startswith("infeasible").mean()),
        "repair_share": float(diag["status"].str.endswith("repair").mean()),
        "inaccurate_share": float(diag["inaccurate"].mean()),
        "polish_shift_max": float(diag["polish_shift"].max()),
        "n_rebalances": int(len(path.dates)),
        "first_date": str(path.dates[0].date()),
        "last_date": str(path.dates[-1].date()),
        "solver": solver,  # what was asked for; `solvers_used` is what ran
        "solvers_used": solvers_used(diag["solver"]),
        "seconds": time.time() - started,
    }
    row.update(
        risk_calibration(
            path.active_returns,
            diag.set_index("date")["te_ex_ante"],
            rule.ppy,
            float(params.require("constraints.tracking_error.max_trailing_3y")),
            te_p95=row["te_p95"],
            active_vol=row["active_vol_annual"],
            ex_ante_mean=row["te_ex_ante_mean"],
        )
    )
    row.update(
        path_transfer(
            path, universe, replace(cell, vol_halflife=vol_halflife, vol_overlay=vol_overlay)
        )
    )
    row.update(portfolio_veto_verdicts(row, params))
    return row, path


# Ex-ante TE below this (annual) carries no scale to calibrate against: a blind
# book hugging the benchmark would divide by rounding.
_MIN_EX_ANTE_TE = 1e-4

# The 5th percentile of a standard normal. `left_tail_L` divides by it so that a
# correctly specified risk model reads 1, as the bias statistic does.
_Z05 = 1.6448536269514722


def params_min_obs() -> int:
    """Readings a calendar year needs before its bias statistic is read.

    From params, so the audit's column and the veto of decisions/0030 cannot
    drift apart: a cell that reports a worst year the veto would not have read
    is a cell whose verdict nobody can reproduce.
    """
    return int(get_params().get("vetoes.risk_calibration.min_observations_per_year", 40))


def risk_calibration(
    active: pd.Series,
    ex_ante_annual: pd.Series,
    periods_per_year: float,
    budget: float,
    te_p95: float,
    active_vol: float,
    ex_ante_mean: float,
) -> dict[str, float]:
    """
    Does the risk the book was SIZED to match the risk it RAN? decisions/0027.

    Measured and reported, never a gate. Three readings:

      * `te_realised_to_ex_ante` -- realised active volatility over the mean
        ex-ante TE. Below one, the covariance overstates risk; above, it
        understates it.
      * `te_p95_to_ex_ante`, `te_p95_to_budget` -- the statistic the TE veto
        reads, against what the solver aimed at and against the budget. A book
        that spends its budget can breach a p95 veto set at the same level on
        sampling error alone; these say by how much.
      * `bias_stat` -- the standard deviation of z = r / sigma_ex_ante, one
        observation per period, each return standardised by the ex-ante TE of
        the book that EARNED it (set at the previous rebalance). One when the
        risk model is calibrated; `bias_band` is the approximate 95%
        half-width, 1.96 / sqrt(2T), for iid normal z.
      * `bias_worst_annual` and `bias_worst_year` -- the same statistic read
        per calendar year and taken at its worst, which is what decisions/0030
        made the `risk_calibration` VETO. The full-sample reading is kept
        beside it and is not a gate: measured on Bloomberg base cells it runs
        0.87 to 1.05 while the worst year runs 1.39 to 2.21, so it cannot tell
        a book running twice its sized risk for a year from one that is not.
        A year with fewer than `min_observations_per_year` readings is not
        read; `bias_years_read` says how many were.

    `ex_ante_annual` is indexed by the rebalance date the book was set on, so
    it is shifted one period onto the return that book earned.
    """
    sigma = ex_ante_annual.sort_index().shift(1).reindex(active.index)
    ok = sigma.notna() & active.notna() & (sigma > _MIN_EX_ANTE_TE)
    z = active[ok] / (sigma[ok] / np.sqrt(periods_per_year))
    n = int(ok.sum())
    bias = float(z.std()) if n > 1 else float("nan")
    q05 = float(np.quantile(z, 0.05)) if n > 1 else float("nan")
    band = float(1.96 / np.sqrt(2.0 * n)) if n > 0 else float("nan")

    def ratio(num: float, den: float) -> float:
        return (
            float(num / den) if np.isfinite(num) and np.isfinite(den) and den > 0 else float("nan")
        )

    min_obs = int(params_min_obs())
    annual = annual_bias(z, min_obs) if n > 1 else {}
    worst_year = max(annual, key=annual.__getitem__) if annual else None
    return {
        "te_realised_to_ex_ante": ratio(active_vol, ex_ante_mean),
        "te_p95_to_ex_ante": ratio(te_p95, ex_ante_mean),
        "te_p95_to_budget": ratio(te_p95, budget),
        "bias_stat": bias,
        "bias_band": band,
        "bias_n": n,
        "bias_worst_annual": annual[worst_year] if worst_year else float("nan"),
        "bias_worst_year": float(worst_year) if worst_year else float("nan"),
        "bias_years_read": len(annual),
        "left_tail_q05": q05,
        "left_tail_L": abs(q05) / _Z05 if np.isfinite(q05) else float("nan"),
    }


def _plant(universe: AuditUniverse, cell: AuditCell) -> PlantedSignal:
    return plant_signal(
        universe.weekly[universe.holdable],
        universe.benchmark_weekly,
        ic=cell.ic,
        horizon=cell.horizon,
        seed=cell.seed,
        vol_window=universe.window,
        standardise=cell.standardise,
        baseline=cell.baseline,
        shuffle=cell.shuffle,
        perm=cell.perm,
    )


def run_frictionless(
    universe: AuditUniverse, cell: AuditCell, params: Params | None = None
) -> tuple[dict[str, Any], pd.Series]:
    """
    The ruler for the ruler. decisions/0027.

    The same planted signal and the same estimated covariance as a base cell,
    and nothing else: no long-only constraint, no cash or position cap, no
    turnover limit, no costs. Each week the active book is the mean-variance
    direction on returns in excess of the benchmark,

        x = k * inv(Sigma_x) * alpha,     x' Sigma_x x = TE^2 / periods_per_year,

    held for one period and marked on the excess returns that follow. This is
    the setting the fundamental law describes (TC = 1), up to the error in the
    estimated covariance. So:

      * frictionless IR over IC, per horizon, is the EMPIRICAL breadth, to set
        beside the formula's;
      * a base cell's net IR over its frictionless twin is the measured price
        of long-only, the caps and the costs.

    "Up to the error in the estimated covariance" is not a small caveat. An
    unconstrained inv(Sigma) book loads hardest on the directions the shrunk
    covariance understates. On the synthetic panel (10 seeds, h = 4 to 52) its
    bias statistic is about 1.21, where 1.00 means calibrated, and the empirical
    breadth is 0.71 to 0.85 of the 52/h formula. The long-only books sit at
    0.93 to 0.97 on the same covariance: the constraint absorbs the error
    (Jagannathan and Ma, 2003). One seed's IR carries a standard deviation of
    about 0.25 to 0.30 here, which is why `empirical_breadth` fits a slope over
    every cell rather than reading one.

    A linear solve a week rather than a QP: the whole family costs seconds.
    Returns the row and the weekly active-return series.
    """
    params = params or get_params()
    started = time.time()
    ppy = float(params.get("costs.application.weeks_per_year", 52))
    budget = float(params.require("constraints.tracking_error.max_trailing_3y"))
    te_var = budget**2 / ppy
    signal = _plant(universe, cell)
    vol_halflife, vol_overlay = resolve_vol_overlay(cell, params)
    dates = universe.audit_dates()
    legs = universe.leg_ids

    returns: dict[pd.Timestamp, float] = {}
    ex_ante: dict[pd.Timestamp, float] = {}
    for held_from, marked_at in zip(dates[:-1], dates[1:], strict=True):
        cov = universe.covariance(held_from, vol_halflife, vol_overlay)
        ids = cov.ids
        hold = [h for h in universe.holdable if h in ids]
        if not hold:
            continue
        pos = {sid: i for i, sid in enumerate(ids)}
        bench = np.zeros(len(ids))
        for leg in legs:
            bench[pos[leg]] = float(universe.leg_weights[leg])
        excess = -np.repeat(bench[:, None], len(hold), axis=1)
        for j, h in enumerate(hold):
            excess[pos[h], j] += 1.0
        sigma_x = excess.T @ cov.matrix.to_numpy(dtype=float) @ excess
        alpha = (
            signal.alpha.reindex(index=[held_from], columns=hold)
            .iloc[0]
            .fillna(0.0)
            .to_numpy(dtype=float)
        )
        direction = np.linalg.lstsq(sigma_x, alpha, rcond=None)[0]
        quad = float(alpha @ direction)
        book = direction * np.sqrt(te_var / quad) if quad > 0 else np.zeros(len(hold))
        realised = universe.weekly.loc[marked_at, hold].fillna(0.0).to_numpy(dtype=float) - float(
            universe.benchmark_weekly.loc[marked_at]
        )
        returns[marked_at] = float(book @ realised)
        if quad > 0:
            # Only sized books carry an ex-ante TE. The last `horizon` weeks have
            # no forward window, hence no alpha and no book; they earn zero and
            # stay in the IR, as the base cell's benchmark-hugging weeks do.
            ex_ante[held_from] = float(np.sqrt(max(book @ sigma_x @ book, 0.0) * ppy))

    active = pd.Series(returns, dtype="float64").sort_index()
    ex_ante_series = pd.Series(ex_ante, dtype="float64")
    te = active.rolling(int(3 * ppy), min_periods=int(3 * ppy)).std().dropna() * np.sqrt(ppy)
    sd = float(active.std())
    ic = realised_ic(signal)
    row: dict[str, Any] = {
        "tag": cell.tag,
        "key": cell.key(params),
        "ic": cell.ic,
        "horizon": cell.horizon,
        "seed": cell.seed,
        "cost_multiplier": 0.0,
        "turnover_cap": None,
        "per_rebalance_cap": None,
        "net_ir": float(active.mean() * ppy / (sd * np.sqrt(ppy))) if sd > 1e-12 else float("nan"),
        "active_return_annual": float(active.mean() * ppy),
        "active_vol_annual": float(sd * np.sqrt(ppy)),
        "te_p95": float(te.quantile(0.95)) if len(te) else float("nan"),
        "te_max": float(te.max()) if len(te) else float("nan"),
        "te_ex_ante_mean": float(ex_ante_series.mean()),
        "turnover_annual": float("nan"),
        "cost_drag_annual": 0.0,
        "inaccurate_share": float("nan"),
        "realised_ic_pooled": ic["pooled"],
        "realised_ic_cross_sectional": ic["cross_sectional"],
        "realised_ic_cross_sectional_pearson": ic["cross_sectional_pearson"],
        "realised_ic_cross_sectional_demeaned": ic["cross_sectional_demeaned"],
        "signal_phi": signal_autocorrelation(signal.score),
        "n_rebalances": int(len(active)),
        "first_date": str(active.index[0].date()),
        "last_date": str(active.index[-1].date()),
        "solver": "linear",
        "solvers_used": f"linear:{len(active)}",
        "seconds": time.time() - started,
    }
    row.update(
        risk_calibration(
            active,
            ex_ante_series,
            ppy,
            budget,
            te_p95=row["te_p95"],
            active_vol=row["active_vol_annual"],
            ex_ante_mean=row["te_ex_ante_mean"],
        )
    )
    row["passes_portfolio_vetoes"] = False
    row["veto_detail"] = "not judged: a frictionless cell has no mandate"
    return row, active


def empirical_breadth(table: pd.DataFrame) -> pd.DataFrame:
    """
    Per horizon, the breadth the frictionless cells actually delivered.

    Under the fundamental law at TC = 1, IR = IC * sqrt(BR), so IR is linear in
    IC through the origin with slope sqrt(BR). The slope is fitted over every
    frictionless cell below the oracle (all ICs, all seeds) rather than read off
    one cell, which would carry that cell's sampling error squared. The IC the
    frictionless book needs for the bar is `target / slope`.
    """
    sub = table[(table["tag"] == FRICTIONLESS) & (table["ic"] < 1.0) & (table["ic"] > 0.0)]
    out = []
    for h, group in sub.groupby("horizon"):
        g = group[np.isfinite(group["net_ir"])]
        denom = float((g["ic"] ** 2).sum())
        slope = float((g["ic"] * g["net_ir"]).sum() / denom) if denom > 0 else float("nan")
        out.append(
            {
                "horizon": int(h),
                "ir_per_unit_ic": slope,
                "empirical_breadth": slope**2 if np.isfinite(slope) and slope > 0 else float("nan"),
                "n_cells": int(len(g)),
            }
        )
    return pd.DataFrame(out)


def ladder_breadth(table: pd.DataFrame) -> pd.DataFrame:
    """
    Per horizon, the breadth the CONSTRAINED ladder delivered. decisions/0029 s4.

    The frictionless twin measures its own covariance error, so breadth is read
    off the base cells instead. There IR = TC * IC * sqrt(BR), so the slope of
    net IR on IC through the origin is TC * sqrt(BR), and dividing by the
    measured transfer coefficient leaves sqrt(BR). Net IR carries the costs, so
    this is breadth net of them, and it is NaN where no coefficient was measured
    rather than a breadth that silently assumes TC = 1.
    """
    sub = table[(table["tag"] == "base") & (table["ic"] < 1.0) & (table["ic"] > 0.0)]
    out = []
    for h, group in sub.groupby("horizon"):
        g = group[np.isfinite(group["net_ir"])]
        denom = float((g["ic"] ** 2).sum())
        slope = float((g["ic"] * g["net_ir"]).sum() / denom) if denom > 0 else float("nan")
        tc = float("nan")
        if "transfer_coefficient" in g.columns:
            v = pd.to_numeric(g["transfer_coefficient"], errors="coerce").dropna()
            tc = float(v.median()) if len(v) else float("nan")
        ok = np.isfinite(slope) and slope > 0 and np.isfinite(tc) and tc > 0
        out.append(
            {
                "horizon": int(h),
                "ir_per_unit_ic": slope,
                "transfer_coefficient": tc,
                "ladder_breadth": (slope / tc) ** 2 if ok else float("nan"),
                "n_cells": int(len(g)),
            }
        )
    return pd.DataFrame(out)


def transfer_ratio(table: pd.DataFrame) -> pd.DataFrame:
    """
    Base net IR over frictionless IR at the same (IC, horizon, seed), averaged.

    The measured price of long-only, the cash and position caps and the costs,
    as a fraction of what the same signal and covariance deliver without them.
    It is not Clarke's transfer coefficient -- costs are in it -- and it is not
    bounded by one on a single noisy cell.
    """
    keys = ["ic", "horizon", "seed"]
    base = table[table["tag"] == "base"].set_index(keys)["net_ir"]
    fric = table[table["tag"] == FRICTIONLESS].set_index(keys)["net_ir"]
    joined = pd.concat({"base": base, "frictionless": fric}, axis=1, join="inner").reset_index()
    if joined.empty:
        return pd.DataFrame()
    joined = joined[joined["frictionless"].abs() > 1e-9]
    joined["ratio"] = joined["base"] / joined["frictionless"]
    return joined.pivot_table(index="ic", columns="horizon", values="ratio", aggfunc="mean")


def solvers_used(names: pd.Series) -> str:
    """
    Which solver produced each rebalance's book, as `NAME:count` pairs.

    `solver` in the cell table is the backend REQUESTED ("auto"), which says
    nothing about whether CLARABEL, a fallback, or the SLSQP reference path
    actually ran. This does.
    """
    counts = names.astype(str).value_counts()
    return ";".join(f"{name}:{int(n)}" for name, n in counts.items())


def rolling_annual_turnover_quantile(
    path: PortfolioPath, periods_per_year: float, q: float
) -> float:
    """
    A quantile of ROLLING one-year traded notional.

    The full-sample mean says what the strategy averaged; it cannot say whether
    a single high-conviction year ran hot. Since the owner reads the 150% figure
    as an annual budget that conviction may exceed (2026-09-11), the statistic
    that matters is the distribution of one-year windows, exactly as
    `decisions/0003` made the tracking-error veto a p95 of trailing readings
    rather than a maximum. Reported so the question can be settled on evidence;
    which statistic the veto READS is an owner decision, not this module's.
    """
    window = int(round(periods_per_year))
    rolled = path.turnover.rolling(window, min_periods=window).sum()
    rolled = rolled.dropna()
    if rolled.empty:
        return float("nan")
    return float(rolled.max() if q >= 1.0 else rolled.quantile(q))


def portfolio_veto_verdicts(row: dict[str, Any], params: Params) -> dict[str, Any]:
    """
    Evaluate the three PORTFOLIO vetoes against a cell, at the real thresholds
    (decisions/0038 removed the fourth, `turnover`: disclosed and highlighted
    above `constraints.turnover.highlight_annualised`, never vetoed -- see
    `turnover_highlight` below).

    The audit is not a run and never records one, but a cell that clears the net
    IR bar while breaching the tracking-error veto would be killed in phase 3 --
    so counting it as clearing makes the bar optimistic. The required-IC table
    is therefore reported twice: on net IR alone, and on net IR among cells that
    would survive.

    Maximum active drawdown is still REPORTED per cell; it is no longer a gate.
    decisions/0026 removed the active_drawdown veto because drawdown is a
    consequence of the tracking-error budget, which decisions/0025 now derives
    from the drawdown tolerance -- gating on the realised figure as well would
    charge the same risk twice and would select on the luck of the path.
    decisions/0030 applied the same argument to the tracking error itself: the
    realised level is a characteristic, and what is checked here is whether the
    book ran the risk it was SIZED for. `te_p95` is still reported on every
    cell; it simply no longer decides anything.

    The six vetoes not evaluated here need a signal, a hypothesis or a search
    (coverage, lookahead, frequency, seed_stability, multiple_testing,
    direction) and have no meaning for a planted signal. They are absent, not
    passed.

    SUBSTRATE section 10: a veto whose input is absent FAILS. A cell whose
    window holds no calendar year long enough to read has no worst-annual bias,
    so it fails `risk_calibration` for want of data rather than for breaching
    anything, and `veto_detail` says which.
    """
    checks = {
        "risk_calibration": (
            row.get("bias_worst_annual"),
            float(params.require("vetoes.risk_calibration.max_worst_annual_bias")),
        ),
        "cash": (row["max_cash"], float(params.require("vetoes.cash.max_weight"))),
        "positions": (
            float(row["n_positions_max"]),
            float(params.require("vetoes.positions.max_nonzero")),
        ),
    }
    failed = []
    for name, (value, cap) in checks.items():
        if value is None or not np.isfinite(value):
            failed.append(f"{name}:no-input")
        elif value > cap * (1.0 + 1e-9):
            failed.append(f"{name}:{value:.4g}>{cap:g}")
    # decisions/0038 (L17 addendum): a REPORTING flag, never a gate. A cell is
    # highlighted when its annual traded notional or its rolling one-year p95
    # exceeds the threshold; the rolling max is reported but not highlighted.
    highlight_cap = float(params.require("constraints.turnover.highlight_annualised"))
    windows = params.get("constraints.turnover.highlight_windows", ["annual", "rolling_1y_p95"])
    candidates = {
        "annual": row.get("turnover_annual"),
        "rolling_1y_p95": row.get("turnover_p95_rolling_1y"),
    }
    unknown = [w for w in windows if w not in candidates]
    if unknown:
        raise ValueError(
            f"constraints.turnover.highlight_windows names {unknown}; "
            f"known windows are {sorted(candidates)}"
        )
    turnover_highlight = any(
        (v := candidates.get(w)) is not None and np.isfinite(v) and v > highlight_cap
        for w in windows
    )
    return {
        "passes_portfolio_vetoes": not failed,
        "veto_detail": "; ".join(failed) if failed else "all three pass",
        "turnover_highlight": turnover_highlight,
    }


# --- the grid -----------------------------------------------------------------


def grid_cells(params: Params | None = None, lean: bool = False) -> list[AuditCell]:
    """
    The cells decisions/0023 asks for, in the order they run.

    The BASE cells carry no hard turnover cap. The owner's reading of section 4
    (2026-09-11) is that 150% is an annual budget rather than a per-period wall,
    and that a high-conviction period may exceed it: "it is allowed to have a
    larger turnover if conviction is higher, even if the annualized figure
    surpass 150%". Hard-capping the base cells would have measured the cap
    instead of the layer -- and it was binding on half to nine tenths of
    rebalances, so the required-IC table was reporting a constrained answer as
    if it were the layer's answer.

    What still restrains the base cells is the progressive shadow cost of
    `decisions/0024`: zero up to 75% trailing annual turnover, 10bp at 150%,
    rising without bound on the same slope. Turnover goes where the alpha
    justifies it, and the realised figure is reported rather than assumed.

    Hard caps remain an EXPERIMENT, in the `turnover` cells, which is what the
    turnover-shortfall curve measures: what the layer gives up when the budget
    really is a wall.
    """
    params = params or get_params()
    ics = [float(x) for x in params.require("audit.ic_grid")]
    horizons = [int(x) for x in params.require("audit.horizon_weeks")]
    seeds = list(range(int(params.require("audit.seeds"))))
    if lean:
        ics = [ic for ic in ics if ic in (0.05, 0.10)] or ics[:2]
        horizons = [h for h in horizons if h in (4, 26)] or horizons[:2]
        seeds = seeds[:1]

    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)

    cells: list[AuditCell] = []
    for h in horizons:
        for ic in ics:
            for s in seeds:
                cells.append(AuditCell(ic, h, s, 1.0, None, default_per, "base"))
    # decisions/0027: every base cell has a frictionless twin, in the lean grid
    # too. It is a linear solve a week, and it is what says whether the breadth
    # the report prints is the breadth the pipeline has.
    if bool(params.get("audit.include_frictionless", False)):
        for h in horizons:
            for ic in ics:
                for s in seeds:
                    cells.append(AuditCell(ic, h, s, 0.0, None, None, FRICTIONLESS))
    if lean:
        return cells

    if bool(params.get("audit.include_oracle", True)):
        for h in horizons:
            cells.append(AuditCell(1.0, h, 0, 1.0, None, default_per, "oracle"))

    stress_h = int(params.get("audit.stress_horizon_weeks", horizons[len(horizons) // 2]))
    for mult in params.get("audit.cost_multipliers", [1.0]) or []:
        if float(mult) == 1.0:
            continue
        for ic in ics:
            for s in seeds:
                cells.append(AuditCell(ic, stress_h, s, float(mult), None, default_per, "cost"))
    for tcap in params.get("audit.turnover_caps", []) or []:
        if tcap is None:
            continue  # the uncapped case is the base cell; it is not run twice
        for ic in ics:
            for s in seeds:
                cells.append(AuditCell(ic, stress_h, s, 1.0, float(tcap), default_per, "turnover"))
    # The per-session cap is the owner's first requirement and has no chosen
    # value yet, so the audit SWEEPS it and reports what each costs. That is a
    # measurement; picking the number is an owner decision, open after 0024.
    for per in params.get("audit.per_rebalance_caps", []) or []:
        value = None if per is None else float(per)
        if value == default_per:
            continue
        for ic in ics:
            for s in seeds:
                cells.append(AuditCell(ic, stress_h, s, 1.0, None, value, "per_rebalance"))
    return cells


BASELINE_GRIDS = ("baseline-pilot", "baseline")

# The `knee` grid (HANDOFF task 20): where the response begins between IC 0.20,
# which the ladder already measured, and the oracle at 1.0. The rungs live here
# and not in `params/audit.yaml`, which is owner-only and not authorised to grow
# a key by any record; the grid values the ladder shares with it are still read
# from params, so `params_hash` is unmoved and the pairing against earlier runs holds.
KNEE_IC_RUNGS = (0.35, 0.50, 0.70)
KNEE_HORIZON = 13
KNEE_GRID = "knee"

# The `power` grid (HANDOFF task 25): bar 2's power on a single history. Score-
# shuffle cells only, at two knee rungs and two seeds; their live twins are the
# knee run's base cells and are not re-run. Constants here, like the knee rungs,
# because params/ is owner-only.
POWER_GRID = "power"
POWER_IC_RUNGS = (0.35, 0.70)
POWER_SEEDS = (0, 1)
POWER_PERMS = 20
POWER_LIVE_RUN = "A-20260922-005316"
# The `power10` grid (HANDOFF task 30): the same measurement at ten seeds, with the
# span-limited score shuffle, at one rung. Live and truth-shuffle twins for every
# seed are the knee run's cells, `POWER_LIVE_RUN`.
POWER10_GRID = "power10"
POWER10_IC_RUNGS = (0.70,)
POWER10_SEEDS = tuple(range(10))
POWER10_PERMS = 20

# The `friction` grid (HANDOFF task 32): live cells only, at two knee rungs and ten
# seeds, with the turnover shadow-cost coefficient overridden to 10, 20 and 40 bp
# (`params/` stays 10, unmoved). The 10 bp arm's live twin is `POWER_LIVE_RUN`'s
# base cell at the same (ic, seed); real costs are unchanged, so net IR stays
# honest and only the weights the shadow cost shapes can move.
FRICTION_GRID = "friction"
FRICTION_IC_RUNGS = (0.35, 0.70)
FRICTION_SEEDS = tuple(range(10))
FRICTION_COEFFICIENTS = (10.0, 20.0, 40.0)

# The `friction_created` grid (HANDOFF task 36): the same 60 cells as `friction`,
# but priced with decisions/0040's created-turnover shadow (`shadow_form="created"`)
# instead of the flat trailing one. The 10 bp arm's control is `FRICTION_LIVE_RUN`,
# task 32's grid, at the SAME (ic, seed, coefficient) -- not the knee run, because
# the knee run has no `shadow_coefficient` override to pair a coefficient against.
FRICTION_CREATED_GRID = "friction_created"
FRICTION_LIVE_RUN = "A-20260928-151055"

# The `halflife` grid (HANDOFF task 35, OWNER-QUEUE B1/L13): the volatility
# overlay's halflife sweep. Live cells only, three horizons, two IC rungs, ten
# seeds and four halflife arms -- the `vol_halflife=None` arm at h13 is the
# identity check against `POWER_LIVE_RUN`'s live cell (same seed, ic, h13,
# constraints and costs; only the covariance's volatility estimator differs).
# Horizon order matters: `HALFLIFE_HORIZONS` is iterated in the order listed,
# not sorted, so an interrupted run leaves h13 (the identity check) complete
# before h26, and h26 before h4.
HALFLIFE_GRID = "halflife"
HALFLIFE_IC_RUNGS = (0.35, 0.70)
HALFLIFE_SEEDS = tuple(range(10))
HALFLIFE_HORIZONS = (13, 26, 4)
HALFLIFE_ARMS = (None, 13, 26, 52)
AUDIT_GRIDS = (
    *BASELINE_GRIDS,
    KNEE_GRID,
    POWER_GRID,
    POWER10_GRID,
    FRICTION_GRID,
    FRICTION_CREATED_GRID,
    HALFLIFE_GRID,
)


def baseline_cells(params: Params | None = None, grid: str = "baseline") -> list[AuditCell]:
    """
    The block-shuffled baseline cells of decisions/0036, and only those.

    `baseline-pilot` is h13 only; `baseline` is every horizon. Both take the IC
    rungs, horizons and seeds from `params/audit.yaml` and add nothing to it: a
    standing `audit.include_baseline` would be an owner-only params change that
    the record does not authorise (section 4b.5). The cells match the base
    cells' constraints and costs, so each has a live twin in the standing grid.
    """
    if grid not in BASELINE_GRIDS:
        raise ValueError(f"grid must be one of {BASELINE_GRIDS}, got {grid!r}")
    params = params or get_params()
    ics = [float(x) for x in params.require("audit.ic_grid")]
    horizons = [int(x) for x in params.require("audit.horizon_weeks")]
    seeds = list(range(int(params.require("audit.seeds"))))
    if grid == "baseline-pilot":
        horizons = [13]
    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    return [
        AuditCell(ic, h, s, 1.0, None, default_per, BASELINE, baseline=True)
        for h in horizons
        for ic in ics
        for s in seeds
    ]


def knee_cells(params: Params | None = None) -> list[AuditCell]:
    """
    Both halves of each knee rung: a live base cell and its block-shuffled twin,
    at `KNEE_HORIZON` only, over every seed. Constraints and costs match the base
    cells, so the pair differs only in whether the score is aligned with the future.
    """
    params = params or get_params()
    seeds = list(range(int(params.require("audit.seeds"))))
    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    cells: list[AuditCell] = []
    for ic in KNEE_IC_RUNGS:
        for s in seeds:
            cells.append(AuditCell(ic, KNEE_HORIZON, s, 1.0, None, default_per, "base"))
            cells.append(
                AuditCell(ic, KNEE_HORIZON, s, 1.0, None, default_per, BASELINE, baseline=True)
            )
    return cells


def power_cells(params: Params | None = None) -> list[AuditCell]:
    """
    Score-shuffle baselines at `KNEE_HORIZON`: every IC in `POWER_IC_RUNGS`, every
    seed in `POWER_SEEDS`, `POWER_PERMS` permutations each. Constraints and costs
    match the knee grid's cells, so each set of 20 sits beside a live twin in
    `POWER_LIVE_RUN`.

    `shadow_form="trailing"` pinned explicitly (HANDOFF task 39, same reason as
    `friction_cells`): `POWER_LIVE_RUN` was computed under the pre-0040
    trailing form, and the implicit default now reads live params'
    `created_marginal` instead. `vol_halflife=None` pinned explicitly too
    (HANDOFF task 42, decisions/0042): the live twins were computed with no
    volatility overlay, and the default now reads the 26-week scalar overlay.
    """
    params = params or get_params()
    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    return [
        AuditCell(
            ic,
            KNEE_HORIZON,
            s,
            1.0,
            None,
            default_per,
            BASELINE,
            baseline=True,
            shuffle=SCORE_SHUFFLE,
            perm=p,
            shadow_form="trailing",
            vol_halflife=None,
        )
        for ic in POWER_IC_RUNGS
        for s in POWER_SEEDS
        for p in range(POWER_PERMS)
    ]


def power10_cells(params: Params | None = None) -> list[AuditCell]:
    """
    Span-limited score-shuffle baselines at `KNEE_HORIZON`: every IC in
    `POWER10_IC_RUNGS`, seeds `POWER10_SEEDS`, `POWER10_PERMS` permutations each.
    Constraints and costs match the knee cells', so each set of 20 sits beside a
    live twin and a truth-shuffle twin in `POWER_LIVE_RUN`.

    `shadow_form="trailing"` pinned explicitly (HANDOFF task 39), for the same
    reason as `power_cells` (and `vol_halflife=None`, HANDOFF task 42).
    """
    params = params or get_params()
    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    return [
        AuditCell(
            ic,
            KNEE_HORIZON,
            s,
            1.0,
            None,
            default_per,
            BASELINE,
            baseline=True,
            shuffle=SPAN_SHUFFLE,
            perm=p,
            shadow_form="trailing",
            vol_halflife=None,
        )
        for ic in POWER10_IC_RUNGS
        for s in POWER10_SEEDS
        for p in range(POWER10_PERMS)
    ]


def friction_cells(params: Params | None = None) -> list[AuditCell]:
    """
    Live cells only, at `KNEE_HORIZON`: every IC in `FRICTION_IC_RUNGS`, every
    seed in `FRICTION_SEEDS`, the turnover shadow-cost coefficient overridden to
    each of `FRICTION_COEFFICIENTS`. The 10 bp arm has the same constraints,
    costs and RNG draw as `POWER_LIVE_RUN`'s base cell at the same (ic, seed), so
    it should reproduce that cell's net IR exactly.

    `shadow_form="trailing"` is pinned explicitly (HANDOFF task 39): `None`
    (the default) now reads `constraints.turnover.penalty.form` from params,
    which is `created_marginal` since decisions/0040 -- this grid is
    specifically the LEGACY trailing-form sweep `friction_created_cells()`
    pairs against, and `POWER_LIVE_RUN` was computed under `trailing`, so an
    implicit default would silently break both. `vol_halflife=None` is pinned
    for the same reason (HANDOFF task 42, decisions/0042): both runs were
    computed with no volatility overlay, and the default is now the 26-week
    scalar overlay. `friction_created_cells()` inherits the pin.
    """
    params = params or get_params()
    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    return [
        AuditCell(
            ic,
            KNEE_HORIZON,
            s,
            1.0,
            None,
            default_per,
            "base",
            shadow_coefficient=coef,
            shadow_form="trailing",
            vol_halflife=None,
        )
        for ic in FRICTION_IC_RUNGS
        for s in FRICTION_SEEDS
        for coef in FRICTION_COEFFICIENTS
    ]


def friction_created_cells(params: Params | None = None) -> list[AuditCell]:
    """
    `friction_cells()`, with `shadow_form="created"` (decisions/0040) instead of
    the default `"trailing"`. Same rungs, seeds and coefficients, same
    constraints and costs, so each cell pairs against `friction_cells()`'s
    cell at the same (ic, seed, coefficient) in `FRICTION_LIVE_RUN`.
    """
    return [replace(c, shadow_form="created") for c in friction_cells(params)]


def halflife_cells(params: Params | None = None) -> list[AuditCell]:
    """
    HANDOFF task 35 (OWNER-QUEUE B1, L13): live cells only, at every horizon in
    `HALFLIFE_HORIZONS`, every IC in `HALFLIFE_IC_RUNGS`, every seed in
    `HALFLIFE_SEEDS`, crossed with every halflife arm in `HALFLIFE_ARMS`.
    Constraints and costs match the knee grid's live cells (no turnover cap,
    cost multiplier 1.0, `per_rebalance_cap` from
    `audit.per_rebalance_cap_default`, no shadow-coefficient override).

    Ordering is deliberate, for a deadline-truncated run: horizon outermost, in
    `HALFLIFE_HORIZONS`'s listed order (13 first, so the identity check is
    complete before anything else); within a horizon, by (ic, seed); within a
    (horizon, ic, seed), all four halflife arms back to back, so a stop between
    seeds never leaves one arm of a pair without its `None` control.

    A `vol_halflife=None` cell's key is unchanged (the pre-task-35 key), so its
    h13 cells are byte-identical in key to `POWER_LIVE_RUN`'s live cells at the
    same (ic, seed) -- the identity check the receipt reports.

    `shadow_form="trailing"` pinned explicitly (HANDOFF task 39, added after
    this grid first ran under the pre-task-39 implicit default, which was
    `trailing` at the time): `POWER_LIVE_RUN` was computed under `trailing`,
    and an implicit default would silently diverge to `created_marginal` on
    any future re-run, now that live params carry decisions/0040. Its arms set
    `vol_halflife` and `vol_overlay` explicitly (task 42: the `None` arm is
    "no overlay", not "follow params"), so the sweep stays reproducible.
    """
    params = params or get_params()
    default_per = params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    return [
        AuditCell(
            ic,
            h,
            s,
            1.0,
            None,
            default_per,
            "base",
            vol_halflife=hl,
            vol_overlay="scalar" if hl is not None else "per_series",
            shadow_form="trailing",
        )
        for h in HALFLIFE_HORIZONS
        for ic in HALFLIFE_IC_RUNGS
        for s in HALFLIFE_SEEDS
        for hl in HALFLIFE_ARMS
    ]


def net_ir_excess(table: pd.DataFrame) -> pd.Series:
    """
    Per row, net IR less the net IR of its seed-matched block-shuffled baseline.

    Rows pair on (ic, horizon, seed, cost_multiplier, turnover_cap,
    per_rebalance_cap). A baseline row is its own baseline, so its excess is
    zero by construction; a row with no baseline in the table is NaN, never
    zero. Oracle and frictionless rows pair like any other and are NaN unless a
    baseline at their own coordinates was run.
    """
    keys = ["ic", "horizon", "seed", "cost_multiplier", "turnover_cap", "per_rebalance_cap"]
    is_base = (
        table["baseline"].astype(bool)
        if "baseline" in table.columns
        else pd.Series(False, index=table.index)
    )
    # The paired floor is the truth shuffle; a score-shuffle row is a draw from a
    # null, not a seed-matched twin (HANDOFF task 25).
    if "shuffle" in table.columns:
        is_base = is_base & table["shuffle"].fillna(TRUTH_SHUFFLE).isin([TRUTH_SHUFFLE, ""])
    frame = table[keys].astype(float)
    # NaN never matches NaN in a join, and "no cap" is a coordinate, not a gap.
    frame[["turnover_cap", "per_rebalance_cap"]] = frame[
        ["turnover_cap", "per_rebalance_cap"]
    ].fillna(-1.0)
    baselines = (
        pd.concat([frame[is_base], table.loc[is_base, ["net_ir"]]], axis=1)
        .drop_duplicates(keys)
        .set_index(keys)["net_ir"]
    )
    index = pd.MultiIndex.from_frame(frame)
    floor = pd.Series(baselines.reindex(index).to_numpy(), index=table.index)
    return table["net_ir"] - floor


def run_grid(
    universe: AuditUniverse,
    params: Params | None = None,
    lean: bool = False,
    solver: str | None = None,
    progress=None,
    cells: list[AuditCell] | None = None,
) -> pd.DataFrame:
    """Run every cell; `progress(i, n, row)` is called after each, if given."""
    params = params or get_params()
    cells = cells if cells is not None else grid_cells(params, lean)
    rows = []
    for i, cell in enumerate(cells, start=1):
        row, _ = run_cell(universe, cell, params, solver)
        rows.append(row)
        if progress is not None:
            progress(i, len(cells), row)
    return pd.DataFrame(rows)


# --- the bar ------------------------------------------------------------------


def required_ic(
    table: pd.DataFrame, target: float, tag: str = "base", surviving_only: bool = False
) -> pd.DataFrame:
    """
    Per horizon, the IC at which mean net IR (over seeds) crosses `target`,
    linearly interpolated between grid points. Outside the grid the answer is
    a bound, and the table says which.

    `surviving_only` restricts to cells that would pass the three portfolio
    vetoes. A cell that clears the bar on net IR but breaches one of them
    would be killed in phase 3, so counting it makes the bar optimistic;
    the report shows both readings side by side.
    """
    base = table[table["tag"] == tag]
    if surviving_only:
        if "passes_portfolio_vetoes" not in base.columns:
            return pd.DataFrame()
        base = base[base["passes_portfolio_vetoes"]]
    if base.empty:
        return pd.DataFrame()
    out = []
    for h, group in base.groupby("horizon"):
        by_ic = group.groupby("ic")["net_ir"].agg(["mean", "min", "max"]).sort_index()
        ics, means = by_ic.index.to_numpy(), by_ic["mean"].to_numpy()
        note, value = "", float("nan")
        if len(ics) == 0:
            continue
        display = ""
        if means.max() < target:
            note, value = f"> {ics.max():.2f} (not reached in grid)", float("inf")
            display = f"> {ics.max():.3f}"
        elif means.min() >= target:
            note, value = f"≤ {ics.min():.2f} (cleared at every grid point)", float(ics.min())
            display = f"≤ {ics.min():.3f}"
        else:
            for lo, hi in zip(range(len(ics) - 1), range(1, len(ics)), strict=True):
                if means[lo] < target <= means[hi]:
                    frac = (target - means[lo]) / (means[hi] - means[lo])
                    value = float(ics[lo] + frac * (ics[hi] - ics[lo]))
                    note = "interpolated"
                    display = f"{value:.3f}"
                    break
            if not note:
                note, value = "non-monotone; first crossing not found", float("nan")
        n_seeds = int(group.groupby("ic")["net_ir"].count().min())
        out.append(
            {
                "horizon": int(h),
                "target_net_ir": target,
                "required_ic": value,
                # What the report prints: a bound is shown as a bound, never as
                # the grid point it was read at.
                "display": display or "—",
                "note": note,
                "net_ir_at_grid": {float(k): float(v) for k, v in by_ic["mean"].items()},
                # One seed has no range; 0.00 would read as perfect stability.
                "seed_range_max": float((by_ic["max"] - by_ic["min"]).max())
                if n_seeds > 1
                else float("nan"),
                "n_seeds": n_seeds,
            }
        )
    return pd.DataFrame(out)
