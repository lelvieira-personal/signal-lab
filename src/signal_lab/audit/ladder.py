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

    def key(self) -> str:
        cap = "none" if self.turnover_cap is None else f"{self.turnover_cap:.2f}"
        per = "none" if self.per_rebalance_cap is None else f"{self.per_rebalance_cap:.2f}"
        return (
            f"ic{self.ic:.2f}_h{self.horizon}_s{self.seed}"
            f"_c{self.cost_multiplier:.1f}_t{cap}_r{per}"
        )


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
        self.costs = CostModel(params, spread_multiplier=cell.cost_multiplier)
        self.shadow_coeff = float(params.get("constraints.turnover.penalty.coefficient", 0) or 0)
        self.shadow_target = float(params.require("constraints.turnover.target_annualised"))
        self.shadow_budget = float(params.require("constraints.turnover.max_annualised"))
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

        Zero at or below the soft target; `coefficient` basis points when
        trailing turnover has reached the budget, which preserves the
        decisions/0018 calibration exactly at that point; and rising on the same
        slope beyond it rather than stopping. Progressive and unbounded, never a
        wall:

            shadow(T) = coefficient * max(0, T - target) / (budget - target)

        At the 100% target it costs nothing; at the 150% budget it costs the
        10bp decisions/0018 set; at 250% it costs 30bp, which a week carrying
        real alpha can still justify and a routine week cannot.
        """
        span = self.shadow_budget - self.shadow_target
        if span <= 0 or self.shadow_coeff <= 0:
            return 0.0
        excess = max(0.0, self.trailing_annual_turnover() - self.shadow_target)
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
    solver = solver or str(params.get("audit.solver", "auto"))
    started = time.time()

    signal = plant_signal(
        universe.weekly[universe.holdable],
        universe.benchmark_weekly,
        ic=cell.ic,
        horizon=cell.horizon,
        seed=cell.seed,
        vol_window=universe.window,
    )
    rule = _OptimiserRule(universe, signal, cell, params, solver)
    engine_panel = universe.engine_panel()
    exposures = constant_exposures(pd.DataFrame(0.0, index=universe.holdable, columns=["f0"]))
    path = run_walk_forward(
        engine_panel,
        rule,
        universe.benchmark_weekly,  # per period already; the engine compounds it to itself
        exposures,
        cost_model=CostModel(params, spread_multiplier=cell.cost_multiplier),
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
        "n_rebalances": int(len(path.dates)),
        "first_date": str(path.dates[0].date()),
        "last_date": str(path.dates[-1].date()),
        "solver": solver,
        "seconds": time.time() - started,
    }
    row.update(portfolio_veto_verdicts(row, params))
    return row, path


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

    What still restrains the base cells is the section 4 shadow cost
    (`decisions/0018`): 10bp per unit of annualised turnover above the 100%
    target, one-sided. Turnover goes where the alpha justifies it, and the
    realised figure is reported rather than assumed.

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
    # measurement; picking the number is an owner decision (proposed/0024).
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

    `surviving_only` restricts to cells that would pass the five portfolio
    vetoes. A cell that clears the bar on net IR but breaches the tracking-error
    or active-drawdown veto would be killed in phase 3, so counting it makes the
    bar optimistic; the report shows both readings side by side.
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
        if means.max() < target:
            note, value = f"> {ics.max():.2f} (not reached in grid)", float("inf")
        elif means.min() >= target:
            note, value = f"< {ics.min():.2f} (cleared at every grid point)", float(ics.min())
        else:
            for lo, hi in zip(range(len(ics) - 1), range(1, len(ics)), strict=True):
                if means[lo] < target <= means[hi]:
                    frac = (target - means[lo]) / (means[hi] - means[lo])
                    value = float(ics[lo] + frac * (ics[hi] - ics[lo]))
                    note = "interpolated"
                    break
            if not note:
                note, value = "non-monotone; first crossing not found", float("nan")
        out.append(
            {
                "horizon": int(h),
                "target_net_ir": target,
                "required_ic": value,
                "note": note,
                "net_ir_at_grid": {float(k): float(v) for k, v in by_ic["mean"].items()},
                "seed_range_max": float((by_ic["max"] - by_ic["min"]).max()),
            }
        )
    return pd.DataFrame(out)
