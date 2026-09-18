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
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.audit.signals import (
    POOLED,
    PlantedSignal,
    plant_signal,
    realised_ic,
    signal_autocorrelation,
)
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
from signal_lab.portfolio.long_only import BPS, LongOnlySpec, solve

BENCHMARK_SECTION_PREFIX = "18."

# The cell family that calibrates the ruler itself (decisions/0027).
FRICTIONLESS = "frictionless"


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
    _cov_cache: dict[pd.Timestamp, ShrunkCovariance] = field(default_factory=dict, repr=False)

    @property
    def leg_ids(self) -> list[str]:
        return list(self.legs.columns)

    def covariance(self, date: pd.Timestamp) -> ShrunkCovariance:
        """Trailing covariance as of `date`, holdable + legs, cached."""
        date = pd.Timestamp(date)
        cov = self._cov_cache.get(date)
        if cov is None:
            cov = trailing_covariance(self.weekly, date, self.window, legs=self.leg_ids)
            self._cov_cache[date] = cov
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

    def key(self) -> str:
        cap = "none" if self.turnover_cap is None else f"{self.turnover_cap:.2f}"
        per = "none" if self.per_rebalance_cap is None else f"{self.per_rebalance_cap:.2f}"
        key = (
            f"ic{self.ic:.2f}_h{self.horizon}_s{self.seed}"
            f"_c{self.cost_multiplier:.1f}_t{cap}_r{per}"
        )
        if self.standardise != POOLED:
            key = f"{key}_{self.standardise}"
        return f"{key}_frictionless" if self.tag == FRICTIONLESS else key


class _OptimiserRule:
    """
    The weight rule for one cell: solve at every rebalance under a per-session
    cap and a progressive shadow cost.

    Two mechanisms, answering the two halves of the owner's requirement
    (2026-09-11): "the model doesn't generate too much trading in a single
    session, unless the scenario really changes", and "avoid a situation where
    we rebalanced too much on previous windows and then cannot do more when we
    really need it".

    **A hard per-session cap** on traded notional. This is the first half. It is
    generous relative to the weekly average -- a regime shift can be acted on in
    one week -- but far below the annual budget, so no single session can
    consume it.

    **A progressive shadow cost keyed to TRAILING one-year turnover**, and no
    annual wall. This is the second half, and the wall is what would break it.
    Trading gets steadily dearer as the year's turnover rises past the soft
    target, so ordinary weeks restrain themselves and the budget is not frittered
    away; but the cost stays finite, so a week with real alpha can always pay it
    and trade. A hard annual cap does the opposite -- it is free to trade right
    up to the limit and then forbids trading entirely, which is exactly the
    failure the owner described.

    The previous version banked unused allowance and let the bank go negative.
    That is the same failure wearing a friendlier face: it made capacity a
    quantity to be spent, so an early over-trade genuinely blocked a later one.
    The bank is gone.
    """

    def __init__(
        self,
        universe: AuditUniverse,
        signal: PlantedSignal,
        cell: AuditCell,
        params: Params,
        solver: str,
    ):
        self.u = universe
        self.signal = signal
        self.cell = cell
        self.params = params
        self.solver = solver
        self.ppy = float(params.get("costs.application.weeks_per_year", 52))
        self.costs = audit_cost_model(universe, params, cell.cost_multiplier)
        self.shadow_coeff = float(params.get("constraints.turnover.penalty.coefficient", 0) or 0)
        self.shadow_start = float(params.require("constraints.turnover.shadow_start_annualised"))
        self.shadow_reference = float(
            params.require("constraints.turnover.shadow_reference_annualised")
        )
        self.per_rebalance_cap = cell.per_rebalance_cap
        self.turnover_log: list[float] = []
        self.repair_turnover = 0.0  # traded to restore mandate compliance, cap or no cap
        self.diagnostics: list[dict[str, Any]] = []

    def annual_wall_remaining(self) -> float | None:
        """
        Traded notional still permitted under a HARD annual cap, or None when
        there is no wall.

        Only the turnover-shortfall cells set one. Their purpose is to measure
        what a wall costs, and this is what a wall does: once the trailing year
        has spent the budget, nothing more may be traded until it rolls off.
        That is the failure the owner described, priced rather than argued.
        """
        if self.cell.turnover_cap is None:
            return None
        spent = float(np.sum(self.turnover_log[-int(self.ppy) :]))
        return max(0.0, self.cell.turnover_cap - spent)

    def session_cap(self) -> float | None:
        """The binding limit on this session: the per-session cap, the annual
        wall's remaining budget, or whichever is tighter."""
        caps = [c for c in (self.per_rebalance_cap, self.annual_wall_remaining()) if c is not None]
        return min(caps) if caps else None

    def trailing_annual_turnover(self) -> float:
        """Traded notional over the trailing year, annualised to a full year."""
        window = int(self.ppy)
        recent = self.turnover_log[-window:]
        if not recent:
            return 0.0
        # Annualise by the window actually observed, so an early rebalance is not
        # judged as though the year were already complete.
        return float(np.sum(recent)) * self.ppy / len(recent)

    def _shadow(self) -> float:
        """
        A shadow cost per unit traded, rising with trailing one-year turnover.

        Zero at or below `shadow_start`, which decisions/0024 put BELOW the 100%
        target so the cost is already biting as the year approaches it;
        `coefficient` basis points at `shadow_reference`, which preserves the
        decisions/0018 calibration at that point; and rising on the same slope
        beyond it rather than stopping. Progressive and unbounded, never a wall:

            shadow(T) = coefficient * max(0, T - start) / (reference - start)

        At 75% it costs nothing, at 100% 3.3bp, at 150% the 10bp
        decisions/0018 set, at 300% 30bp -- which a week carrying real alpha can
        still justify and a routine week cannot. There is no annual ceiling: the
        veto threshold is a backstop for a malfunctioning book (decisions/0024)
        and this function never reads it.

        This is the same curve as `harness.objective.turnover_penalty`, in cost
        per unit traded rather than return per period.
        """
        span = self.shadow_reference - self.shadow_start
        if span <= 0 or self.shadow_coeff <= 0:
            return 0.0
        excess = max(0.0, self.trailing_annual_turnover() - self.shadow_start)
        return self.shadow_coeff * BPS * excess / span

    def __call__(self, date: pd.Timestamp, _panel: ReturnPanel, drifted: pd.Series | None = None):
        date = pd.Timestamp(date)
        cov = self.u.covariance(date)
        ids = cov.ids
        hold = [h for h in self.u.holdable if h in ids]
        legs = [g for g in self.u.leg_ids if g in ids]
        if len(legs) != len(self.u.leg_ids):
            raise ValueError(f"benchmark legs lack a full covariance window at {date.date()}")
        cash = [c for c in self.u.cash if c in hold]

        benchmark = pd.Series(0.0, index=ids)
        benchmark[legs] = self.u.leg_weights[legs].values
        spec = LongOnlySpec.from_params(ids, hold, cash, benchmark, self.params)

        alpha = self.signal.alpha.reindex(index=[date], columns=hold).iloc[0].fillna(0.0)
        first = drifted is None
        w0 = pd.Series(0.0, index=hold) if first else drifted.reindex(hold).fillna(0.0)
        cost = self.costs.half_spread_vector(hold)
        if first:
            cost = cost * 0.0  # the initial book is built, not traded (engine records no row)
            cap = None
        else:
            cost = cost + self._shadow()
            cap = self.session_cap()

        sol = solve(
            alpha,
            cov.matrix,
            w0,
            cost,
            spec,
            turnover_cap=cap,
            solver=self.solver,
            params=self.params,
        )

        if not first:
            self.turnover_log.append(sol.turnover)
            if sol.status.endswith("repair"):
                self.repair_turnover += sol.turnover
        self.diagnostics.append(
            {
                "date": date,
                "n_holdable": len(hold),
                "n_positions": sol.n_positions,
                "te_ex_ante": sol.te_ex_ante_annual,
                "te_binding": sol.te_binding,
                "turnover_binding": sol.turnover_binding,
                "cash_binding": sol.cash_binding,
                "positions_capped": sol.positions_capped,
                "shrinkage": cov.shrinkage,
                "shadow_bps": self._shadow() / BPS,
                "trailing_turnover": self.trailing_annual_turnover(),
                "session_cap": self.session_cap(),
                "status": sol.status,
                "solver": sol.solver,
                "inaccurate": sol.inaccurate,
                "polish_shift": float(sol.meta.get("polish_shift", 0.0)),
            }
        )
        return sol.weights


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
        "key": cell.key(),
        "ic": cell.ic,
        "horizon": cell.horizon,
        "seed": cell.seed,
        "cost_multiplier": cell.cost_multiplier,
        "turnover_cap": cell.turnover_cap,
        "per_rebalance_cap": cell.per_rebalance_cap,
        "turnover_per_rebalance_max": float(path.turnover.max()),
        "turnover_per_rebalance_p95": float(path.turnover.quantile(0.95)),
        "turnover_from_repairs_annual": rule.repair_turnover * rule.ppy / max(len(path.dates), 1),
        "shadow_bps_mean": float(diag["shadow_bps"].mean()),
        "shadow_bps_max": float(diag["shadow_bps"].max()),
        "net_ir": path.information_ratio(),
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
    row.update(portfolio_veto_verdicts(row, params))
    return row, path


# Ex-ante TE below this (annual) carries no scale to calibrate against: a blind
# book hugging the benchmark would divide by rounding.
_MIN_EX_ANTE_TE = 1e-4


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
        half-width, 1.96 / sqrt(2T), for iid normal z. It is a candidate for
        the `risk_calibration` check decisions/0026 named, whose statistic is
        still an owner decision.

    `ex_ante_annual` is indexed by the rebalance date the book was set on, so
    it is shifted one period onto the return that book earned.
    """
    sigma = ex_ante_annual.sort_index().shift(1).reindex(active.index)
    ok = sigma.notna() & active.notna() & (sigma > _MIN_EX_ANTE_TE)
    z = active[ok] / (sigma[ok] / np.sqrt(periods_per_year))
    n = int(ok.sum())
    bias = float(z.std()) if n > 1 else float("nan")
    band = float(1.96 / np.sqrt(2.0 * n)) if n > 0 else float("nan")

    def ratio(num: float, den: float) -> float:
        return (
            float(num / den) if np.isfinite(num) and np.isfinite(den) and den > 0 else float("nan")
        )

    return {
        "te_realised_to_ex_ante": ratio(active_vol, ex_ante_mean),
        "te_p95_to_ex_ante": ratio(te_p95, ex_ante_mean),
        "te_p95_to_budget": ratio(te_p95, budget),
        "bias_stat": bias,
        "bias_band": band,
        "bias_n": n,
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
    dates = universe.audit_dates()
    legs = universe.leg_ids

    returns: dict[pd.Timestamp, float] = {}
    ex_ante: dict[pd.Timestamp, float] = {}
    for held_from, marked_at in zip(dates[:-1], dates[1:], strict=True):
        cov = universe.covariance(held_from)
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
        "key": cell.key(),
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
    Evaluate the four PORTFOLIO vetoes against a cell, at the real thresholds.

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

    The six vetoes not evaluated here need a signal, a hypothesis or a search
    (coverage, lookahead, frequency, seed_stability, multiple_testing,
    direction) and have no meaning for a planted signal. They are absent, not
    passed.

    SUBSTRATE section 10: a veto whose input is absent FAILS. A trailing-3y
    tracking error needs 156 rebalances of active return before its first
    reading, so a short window fails the tracking_error veto for want of data
    rather than for breaching anything, and `veto_detail` says which.
    """
    te_cap = float(params.require("constraints.tracking_error.max_trailing_3y"))
    checks = {
        "tracking_error": (row["te_p95"], te_cap),
        "turnover": (
            row["turnover_annual"],
            float(params.require("vetoes.turnover.max_annualised")),
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
    return {
        "passes_portfolio_vetoes": not failed,
        "veto_detail": "; ".join(failed) if failed else "all four pass",
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

    `surviving_only` restricts to cells that would pass the four portfolio
    vetoes. A cell that clears the bar on net IR but breaches the tracking-error
    veto would be killed in phase 3, so counting it makes the bar optimistic;
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
