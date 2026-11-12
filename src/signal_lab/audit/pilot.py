"""
The planted-signal pilot of decisions/0059 G, run as its addendum of 2026-11-10 rules
(HANDOFF task 90): the phase-2 rule on the audit's universe, cost model and engine, fed an
axis-level planted score, beside its block-shuffled baseline on the same seed.

What each piece is, and why:

* **The universe** is `audit.universe.bloomberg_universe` (or the synthetic one in tests), with one
  restriction the reviewer settled inside decisions/0059 C: an instrument is holdable at `t` only
  if it has a row in `ExposureMap.at(t)` (`RowedUniverse`). The covariance, its cache and every
  other attribute are the audit universe's own.
* **The cost model** is `audit.ladder.audit_cost_model`, multiplier 1; the shadow form, the
  coefficient and the volatility overlay are resolved from params exactly as `run_cell` resolves
  them for a default cell.
* **The engine** is `harness.engine.run_walk_forward` with `run_cell`'s constant exposure rule;
  its panel ends at the last score date, because the rule refuses a date with no score.
* **The truth** is the duration factor (minus the weekly change in the 10y real yield) or each
  view region's relative return (`alpha.relative_factor`: the equal-weighted `region_view` members
  with a row at `t`, less `NDUEACWF`), planted by `audit.axis_signals.plant_axis_signal`.
* **`sigma`** is `alpha.factor_sigma` / `alpha.relative_sigma` times the scalar overlay of
  decisions/0042, computed as `covariance.volatility_scalar` on the solver's own window and
  holdable block (decisions/0059 A: "read through the same resolver").
* **The factor covariance** the tracking-variance report reads is the six factors' trailing
  sample covariance over the same window, `ddof=0` as `factor_sigma`, times the same overlay
  squared.
* **`IC_prior`** at half and twice is set on an in-memory copy of `Params` (`with_ic_prior`);
  `params/` and its hash are untouched, and the row records the value used.

Nothing here judges a number: the pass bars are the owner's (decisions/0069 item 2).
"""

from __future__ import annotations

import copy
import dataclasses
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.audit.axis_signals import plant_axis_signal, realised_ic
from signal_lab.audit.ladder import (
    AuditCell,
    AuditUniverse,
    audit_cost_model,
    resolve_shadow_form,
    resolve_vol_overlay,
    risk_calibration,
    rolling_annual_turnover_quantile,
)
from signal_lab.characteristics.exposures import VIEW_REGIONS, ExposureMatrixMissing
from signal_lab.harness.engine import constant_exposures, run_walk_forward
from signal_lab.harness.run_context import RunContext
from signal_lab.loaders.base import ReturnPanel
from signal_lab.loaders.holdout import enforce_holdout
from signal_lab.params import Params
from signal_lab.portfolio import alpha as alpha_mod
from signal_lab.portfolio.covariance import ledoit_wolf, volatility_scalar
from signal_lab.portfolio.phase2 import Phase2Rule

PILOT_GRID = "phase2-pilot"
PILOT_SMOKE_GRID = "phase2-pilot-smoke"
PILOT_GRIDS = (PILOT_GRID, PILOT_SMOKE_GRID)
PILOT_DIAG_GRID = "phase2-pilot-diag"  # HANDOFF task 91
PILOT_HORIZON_GRID = "phase2-pilot-horizon"  # HANDOFF task 92
PILOT_0070_GRID = "phase2-pilot-0070"  # HANDOFF task 93, decisions/0070's condition
DIAG_SEED = 0
DIAG_IC = 0.35
DIAG_MULTIPLIERS = (1.0, 2.0, 4.0, 8.0)
PILOT_HORIZON = 13
PILOT_ICS = (0.0, 0.05, 0.10, 0.20, 0.35)
PILOT_SEEDS = (0, 1, 2, 3, 4)
PRIOR_IC = 0.10
PRIOR_MULTIPLIERS = (0.5, 2.0)
SMOKE_ICS = (0.0, 0.35)
SMOKE_SEEDS = (0,)
AXIS_OF_EXPRESSION = {"directional": "duration", "cross_sectional": "region"}
BENCHMARK_EQUITY = "NDUEACWF"

# Every field a pilot row carries (HANDOFF task 90 step 2); the tests check them.
ROW_FIELDS = (
    "key",
    "axis",
    "expression",
    "ic",
    "seed",
    "baseline",
    "horizon",
    "ic_prior",
    "ic_prior_multiplier",
    "net_ir",
    "transfer",
    "equity_tracking_variance_share",
    "turnover_annual",
    "bias_stat",
    "bias_worst_annual",
    "inaccurate_share",
    "infeasible_te_share",
    "realised_ic_pooled",
    "realised_ic_by_column",
    "realised_ic_cross_sectional_demeaned",
    "lookahead_passed",
    "lookahead_detail",
    "status",
    "n_rebalances",
    "first_date",
    "last_date",
    "seconds",
)


@dataclass(frozen=True)
class PilotCell:
    expression: str
    ic: float
    seed: int
    prior_multiplier: float = 1.0
    baseline: bool = False
    horizon: int = PILOT_HORIZON
    # HANDOFF task 91's diagnostic arms: scores identically zero (the no-view book), and the
    # cost model and the decisions/0040 shadow term both off. Neither is a G cell.
    zero_scores: bool = False
    frictionless: bool = False
    # HANDOFF task 92's arms (evidence for decisions/proposed/0070), all off by default:
    # (A) the half-spread the *solve* sees divided by `horizon` (the engine still charges the
    # full half-spread); (B) the shadow coefficient the solve sees divided by `horizon` too;
    # (C) the first book is the no-view book, so the first trade toward the view is a costed
    # rebalance like any other.
    amortise: bool = False
    amortise_shadow: bool = False
    start_noview: bool = False
    # decisions/0070 (HANDOFF task 93): False, the default, runs the ruled objective (the
    # solve sees the half-spread over h, the run starts from the no-view book). True runs the
    # objective in force before it (divisor 1, the first book built free with the view): the
    # recorded grids of tasks 90 to 92 pass it, and task 92's switches above are arms on that
    # objective, so any of them implies it (`legacy_objective`). The key is unchanged.
    legacy: bool = False

    def __post_init__(self) -> None:
        if self.expression not in AXIS_OF_EXPRESSION:
            raise ValueError(f"expression must be one of {tuple(AXIS_OF_EXPRESSION)}")

    @property
    def axis(self) -> str:
        return AXIS_OF_EXPRESSION[self.expression]

    @property
    def legacy_objective(self) -> bool:
        """True when the rule is built with the pre-0070 objective (`legacy`, or a task 92 arm)."""
        return self.legacy or self.amortise or self.amortise_shadow or self.start_noview

    def key(self) -> str:
        short = "dir" if self.expression == "directional" else "xs"
        key = f"{self.axis}-{short}_ic{self.ic:.2f}_h{self.horizon}_s{self.seed}"
        if self.prior_multiplier != 1.0:
            key = f"{key}_prior{self.prior_multiplier:g}"
        if self.zero_scores:
            key = f"{key}_noview"
        if self.frictionless:
            key = f"{key}_frictionless"
        if self.amortise:
            key = f"{key}_amort"
        if self.amortise_shadow:
            key = f"{key}_amortshadow"
        if self.start_noview:
            key = f"{key}_fromnoview"
        return f"{key}_baseline" if self.baseline else key

    @property
    def arm(self) -> str:
        """HANDOFF task 92's arm label: `default`, `A`, `B` or `C`; task 93's `A+C` (the
        amortised half-spread and the no-view first book together, decisions/0070)."""
        if self.amortise and self.amortise_shadow:
            return "B"
        if self.amortise and self.start_noview:
            return "A+C"
        if self.amortise:
            return "A"
        if self.start_noview:
            return "C"
        return "default"


def pilot_cells(grid: str = PILOT_GRID) -> list[PilotCell]:
    """
    G's grid as data, each live cell followed by its baseline twin: 2 expressions x 5 ICs x 5
    seeds, plus `IC_prior` at half and twice on the IC 0.10 cells (140 runs). The smoke grid is
    one seed at IC 0 and 0.35, both expressions (8 runs).
    """
    if grid not in PILOT_GRIDS:
        raise ValueError(f"grid must be one of {PILOT_GRIDS}, got {grid!r}")
    ics, seeds = (SMOKE_ICS, SMOKE_SEEDS) if grid == PILOT_SMOKE_GRID else (PILOT_ICS, PILOT_SEEDS)
    cells: list[PilotCell] = []
    for expression in AXIS_OF_EXPRESSION:
        for ic in ics:
            for seed in seeds:
                for baseline in (False, True):
                    cells.append(PilotCell(expression, ic, seed, baseline=baseline, legacy=True))
        if grid == PILOT_GRID:
            for mult in PRIOR_MULTIPLIERS:
                for seed in seeds:
                    for baseline in (False, True):
                        cells.append(
                            PilotCell(expression, PRIOR_IC, seed, mult, baseline, legacy=True)
                        )
    # HANDOFF task 90's grids are recorded: the objective before decisions/0070
    return cells


def diag_cells() -> list[PilotCell]:
    """
    HANDOFF task 91's diagnostics as data, one seed, h = 13, both expressions: (a) the no-view
    book; (b) planted IC 0.35 at `IC_prior` x1, x2, x4, x8; (c) planted IC 0.35 and 0 with the
    costs and the shadow term off. No baselines: the task reads none (14 runs).
    """
    cells: list[PilotCell] = []
    # recorded (HANDOFF task 91): the objective before decisions/0070
    for expression in AXIS_OF_EXPRESSION:
        cells.append(PilotCell(expression, 0.0, DIAG_SEED, zero_scores=True, legacy=True))
        for mult in DIAG_MULTIPLIERS:
            cells.append(PilotCell(expression, DIAG_IC, DIAG_SEED, mult, legacy=True))
        for ic in (DIAG_IC, 0.0):
            cells.append(PilotCell(expression, ic, DIAG_SEED, frictionless=True, legacy=True))
    return cells


def horizon_cells() -> list[PilotCell]:
    """
    HANDOFF task 92's arms as data, one seed, h = 13, `IC_prior` at the params value, both
    expressions. First the two task 91 x1 rows at the defaults (IC 0.35, live: the reference
    that the switches off reproduce task 91, and the "first book today" numbers of (C)); then
    (A) IC 0 and 0.35, each with its baseline twin; (B) IC 0.35 live; (C) IC 0 and 0.35 live
    (16 runs).
    """
    cells: list[PilotCell] = []
    # recorded (HANDOFF task 92): the default arm is task 91's x1 row, the objective before
    # decisions/0070; the arms A to C imply it (`PilotCell.legacy_objective`)
    for expression in AXIS_OF_EXPRESSION:
        cells.append(PilotCell(expression, DIAG_IC, DIAG_SEED, legacy=True))
    for expression in AXIS_OF_EXPRESSION:
        for ic in (0.0, DIAG_IC):
            for baseline in (False, True):
                cells.append(PilotCell(expression, ic, DIAG_SEED, baseline=baseline, amortise=True))
        cells.append(PilotCell(expression, DIAG_IC, DIAG_SEED, amortise=True, amortise_shadow=True))
        for ic in (0.0, DIAG_IC):
            cells.append(PilotCell(expression, ic, DIAG_SEED, start_noview=True))
    return cells


def cells_0070() -> list[PilotCell]:
    """
    HANDOFF task 93, the owner's condition on decisions/0070: the half-spread the solve sees
    divided by h and the no-view first book, together. Both expressions, planted IC 0 and 0.35,
    h = 13, seed 0, `IC_prior` at the params value, each live run followed by its block-shuffled
    baseline twin (8 runs). Step 1 ran these as task 92's switches `amortise` and `start_noview`
    on the old objective (`A-20261112-143331`); since step 4 they are the plain defaults, and
    every row reproduces step 1's.
    """
    cells: list[PilotCell] = []
    for expression in AXIS_OF_EXPRESSION:
        for ic in (0.0, DIAG_IC):
            for baseline in (False, True):
                cells.append(PilotCell(expression, ic, DIAG_SEED, baseline=baseline))
    return cells


class AmortisedCosts:
    """
    HANDOFF task 92 (A): the cost model the *solve* sees, its half-spread divided by
    `divisor` (the view's horizon). Everything else is the wrapped model's. The engine is
    handed the wrapped model itself, so the net return charges every trade its full cost.
    """

    def __init__(self, costs: Any, divisor: float):
        if not divisor > 0:
            raise ValueError(f"divisor must be positive, got {divisor}")
        self._costs = costs
        self.divisor = float(divisor)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._costs, name)

    def half_spread(self, instrument: str) -> float:
        return float(self._costs.half_spread(instrument)) / self.divisor

    def half_spread_vector(self, instruments) -> pd.Series:
        return self._costs.half_spread_vector(instruments) / self.divisor


class FromNoViewRule(Phase2Rule):
    """
    HANDOFF task 92 (C): the phase-2 rule whose first book is the no-view book (task 91 (a):
    every alpha 0, so the rebalance step returns the minimum-TE book, built from nothing as
    every first book is). Every later call is `Phase2Rule`'s, so the first trade toward the
    view is solved against the half-spread and the shadow term from the drifted no-view book,
    and the engine charges it, like any other rebalance.
    """

    def __call__(self, date: pd.Timestamp, _panel: Any = None, drifted: pd.Series | None = None):
        if drifted is not None or self.books:
            return super().__call__(date, _panel, drifted)
        date = pd.Timestamp(date)
        enforce_holdout([date], self.params, "phase-2 rule date")
        cov = self.u.covariance(date, self.vol_halflife, self.vol_overlay)
        hold = [h for h in self.u.holdable if h in cov.ids]
        weights = self.step(date, pd.Series(0.0, index=hold), None)
        self._record(date, cov, weights)
        return weights


def first_book_report(rule: Phase2Rule, path: Any) -> dict[str, float]:
    """
    HANDOFF task 92 (C): how the first book enters the run. The first book is built from an
    empty book with no cost and no shadow (`RebalanceStep.step`, `first`) and the engine
    records no turnover row for it (`run_walk_forward` holds it from the first date), so its
    traded notional is reported here beside the recorded turnover after it; and the
    correlation of the first book's active weights with the last book's.
    """
    dates = sorted(rule.books)
    first, last = rule.books[dates[0]], rule.books[dates[-1]]

    def active(book: dict[str, Any]) -> pd.Series:
        w = book["weights"].astype(float)
        legs = book["leg_weights"].astype(float)
        ids = sorted(set(w.index) | set(legs.index))
        return w.reindex(ids).fillna(0.0) - legs.reindex(ids).fillna(0.0)

    a_first, a_last = active(first), active(last)
    ids = sorted(set(a_first.index) | set(a_last.index))
    x = a_first.reindex(ids).fillna(0.0).to_numpy()
    y = a_last.reindex(ids).fillna(0.0).to_numpy()
    corr = float(np.corrcoef(x, y)[0, 1]) if x.std() > 0 and y.std() > 0 else float("nan")
    ppy = int(round(rule.ppy))
    turnover = path.turnover.astype(float)
    return {
        "first_book_traded_notional": float(first["weights"].astype(float).abs().sum()),
        "first_recorded_rebalance_turnover": float(turnover.iloc[0]),
        "turnover_first_year": float(turnover.iloc[:ppy].sum()),
        "turnover_after_first_year_annual": float(turnover.iloc[ppy:].mean() * ppy)
        if len(turnover) > ppy
        else float("nan"),
        "first_last_active_weight_corr": corr,
    }


def with_ic_prior(params: Params, value: float) -> Params:
    """An in-memory copy of `params` with `constraints.views.ic_prior` set to `value`."""
    constraints = copy.deepcopy(params.constraints)
    constraints.setdefault("views", {})["ic_prior"] = float(value)
    return dataclasses.replace(params, constraints=constraints)


class RowedUniverse:
    """
    The audit universe with decisions/0059 C's holdable set: `holdable` is the audit's, less the
    instruments with no exposure row at the date of the last `covariance` call (the rebalance
    step always asks for the covariance before it reads `holdable`). Everything else, the
    covariance cache included, is the wrapped universe's.
    """

    def __init__(self, universe: AuditUniverse, rowed: dict[pd.Timestamp, frozenset[str]]):
        self._u = universe
        self._rowed = rowed
        self._date: pd.Timestamp | None = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._u, name)

    def covariance(self, date, vol_halflife=None, vol_overlay="per_series"):
        self._date = pd.Timestamp(date)
        return self._u.covariance(date, vol_halflife, vol_overlay)

    @property
    def holdable(self) -> list[str]:
        if self._date is None:
            return list(self._u.holdable)
        rows = self._rowed.get(self._date, frozenset())
        return [h for h in self._u.holdable if h in rows]


@dataclass
class PilotInputs:
    """Everything a pilot run needs that does not depend on the run."""

    universe: AuditUniverse
    exposures: Any
    factors: pd.DataFrame  # the six weekly factors, the store's factor set, full history
    overlay: pd.Series  # the scalar overlay by universe date (NaN before a full window)
    rowed: dict[pd.Timestamp, frozenset[str]]
    duration_factor: pd.DataFrame  # one column, "duration"
    region_factor: pd.DataFrame  # one column per view region
    duration_sigma: pd.Series
    region_sigma: pd.DataFrame
    notes: dict[str, Any] = field(default_factory=dict)


def clear_usage(exposures: Any) -> pd.DataFrame:
    """The exposure map's usage log so far, then emptied so one run's rows stay one run's."""
    usage = exposures.usage()
    log = getattr(exposures, "_usage", None)
    if isinstance(log, list):
        log.clear()
    return usage


def overlay_scalars(universe: AuditUniverse, params: Params) -> pd.Series:
    """
    The scalar overlay `s(t)` the solver's covariance carries at each universe date
    (`trailing_covariance`'s `scalar` branch: the window, the live-at-start and 90% rules, the
    Ledoit-Wolf matrix, `volatility_scalar`), NaN where the window is short. Refused unless
    params' overlay is the scalar form (decisions/0042).
    """
    halflife, form = resolve_vol_overlay(AuditCell(0.0, PILOT_HORIZON, 0), params)
    if halflife is None or form != "scalar":
        raise ValueError(f"the pilot expects the scalar overlay of decisions/0042, got {form!r}")
    weekly = universe.weekly[universe.holdable]
    out = pd.Series(np.nan, index=weekly.index, dtype=float)
    for i, date in enumerate(weekly.index):
        if i + 1 < universe.window:
            continue
        history = weekly.iloc[i + 1 - universe.window : i + 1]
        present = history.notna()
        keep = history.columns[present.iloc[0] & (present.mean(axis=0) >= 0.9)]
        if len(keep) == 0:
            continue
        block = history[keep].fillna(0.0)
        out[date] = volatility_scalar(ledoit_wolf(block), block, halflife)
    return out


def build_inputs(
    universe: AuditUniverse,
    exposures: Any,
    factors: pd.DataFrame,
    params: Params,
    benchmark_equity: str = BENCHMARK_EQUITY,
    overlay: pd.Series | None = None,
) -> PilotInputs:
    """The truths' factors, their `sigma`, the overlay and the rowed sets, once per universe."""
    dates = universe.weekly.index
    rowed: dict[pd.Timestamp, frozenset[str]] = {}
    cells: dict[pd.Timestamp, pd.DataFrame] = {}
    for date in dates:
        try:
            region_cells = exposures.axis("region", date)
        except ExposureMatrixMissing:
            rowed[pd.Timestamp(date)] = frozenset()
            continue
        rowed[pd.Timestamp(date)] = frozenset(map(str, exposures.at(date).index))
        cells[pd.Timestamp(date)] = region_cells
    clear_usage(exposures)

    if benchmark_equity not in universe.weekly.columns:
        raise ValueError(f"the universe's weekly frame has no {benchmark_equity!r} column")
    members = {r: set() for r in VIEW_REGIONS}
    for frame in cells.values():
        for region in VIEW_REGIONS:
            if region in frame.columns:
                members[region] |= set(frame.index[frame[region] > 0].astype(str))
    every = sorted(set().union(*members.values()) & set(universe.weekly.columns))
    presence = pd.DataFrame(
        {s: [s in rowed.get(pd.Timestamp(d), frozenset()) for d in dates] for s in every},
        index=dates,
    )
    masked = universe.weekly[every].where(presence) if every else pd.DataFrame(index=dates)
    masked = masked.join(universe.weekly[[benchmark_equity]])
    region_factor = pd.DataFrame(
        {
            r: alpha_mod.relative_factor(masked, sorted(members[r] & set(every)), benchmark_equity)
            for r in VIEW_REGIONS
            if members[r] & set(every)
        },
        index=dates,
    )

    if overlay is None:
        overlay = overlay_scalars(universe, params)
    overlay = overlay.reindex(dates)
    duration = (-factors["real_yield"]).rename("duration")
    duration_factor = duration.reindex(dates).to_frame()
    unscaled = alpha_mod.factor_sigma(factors, "duration", params).reindex(dates)
    duration_sigma = (unscaled * overlay).rename("duration")
    region_sigma = pd.DataFrame(
        {r: alpha_mod.relative_sigma(region_factor[r], params) * overlay for r in region_factor},
        index=dates,
    )
    notes = {
        "dates": len(dates),
        "dates_without_duration_factor": int(duration_factor["duration"].isna().sum()),
        "region_members": {r: len(members[r] & set(every)) for r in VIEW_REGIONS},
        "dates_without_rows": int(sum(1 for d in dates if not rowed[pd.Timestamp(d)])),
    }
    return PilotInputs(
        universe=universe,
        exposures=exposures,
        factors=factors,
        overlay=overlay,
        rowed=rowed,
        duration_factor=duration_factor,
        region_factor=region_factor,
        duration_sigma=duration_sigma,
        region_sigma=region_sigma,
        notes=notes,
    )


def factor_covariance(inputs: PilotInputs, date: pd.Timestamp, params: Params) -> pd.DataFrame:
    """The six factors' trailing covariance at `date`, ddof=0, times the overlay squared."""
    window = int(params.require("audit.covariance.window_periods"))
    history = inputs.factors.loc[inputs.factors.index <= pd.Timestamp(date)].tail(window).dropna()
    if len(history) < 2:
        raise ValueError(f"no factor history at {pd.Timestamp(date).date()}")
    x = history.to_numpy(float)
    x = x - x.mean(axis=0)
    cov = pd.DataFrame(x.T @ x / len(x), index=history.columns, columns=history.columns)
    s = float(inputs.overlay.get(pd.Timestamp(date), np.nan))
    return cov * (s * s if np.isfinite(s) else 1.0)


def _clip_panel(panel: ReturnPanel, last: pd.Timestamp) -> ReturnPanel:
    return ReturnPanel(
        levels=panel.levels.loc[panel.levels.index <= last],
        returns=panel.returns.loc[panel.returns.index <= last],
        meta=panel.meta,
        splices=panel.splices,
        snapshot_id=panel.snapshot_id,
        source=panel.source,
    )


def _observations(usage: pd.DataFrame) -> pd.DataFrame:
    """The score observations the rule read, as `observation_usage` (knowledge date = score date)."""
    scores = usage[usage["parameter"].astype(str).str.startswith("zscore")]
    return pd.DataFrame(
        {
            "series_id": scores["instrument"].astype(str).to_numpy(),
            "period_end": scores["fitted_through"].to_numpy(),
            "knowledge_date": scores["fitted_through"].to_numpy(),
            "used_on_date": scores["used_on_date"].to_numpy(),
        }
    )


def run_pilot_cell(
    inputs: PilotInputs,
    cell: PilotCell,
    params: Params,
    *,
    lookahead_veto: Callable[[RunContext, Params], Any],
    solver: str | None = None,
    keep: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Phase2Rule, Any]:
    """
    One pilot run: plant, build the `Phase2Rule`, run the engine, report. Returns the row, the
    rule and the path. `lookahead_veto` is `vetoes.rules.veto_lookahead` (`portfolio` and
    `audit` do not import `vetoes`); a run that fails it is recorded with `lookahead_passed`
    False and kept.
    """
    started = time.time()
    solver = solver or str(params.get("audit.solver", "auto"))
    base_prior = float(params.require("constraints.views.ic_prior"))
    run_params = (
        params
        if cell.prior_multiplier == 1.0
        else with_ic_prior(params, base_prior * cell.prior_multiplier)
    )
    universe = inputs.universe
    factor = inputs.duration_factor if cell.expression == "directional" else inputs.region_factor
    plant = plant_axis_signal(
        factor, cell.ic, cell.horizon, cell.seed, cell.expression, run_params, cell.baseline
    )
    scores = plant.score
    if cell.zero_scores:
        # the no-view book (HANDOFF task 91 (a)): z is 0 everywhere, so every view and every
        # alpha is 0 and the rule returns the minimum-TE book of decisions/0059 F2
        scores = scores * 0.0
    if cell.expression == "directional":
        sigma: pd.Series | pd.DataFrame = inputs.duration_sigma.reindex(scores.index)
    else:
        sigma = inputs.region_sigma.reindex(index=scores.index, columns=scores.columns)

    default_per = run_params.get("audit.per_rebalance_cap_default", None)
    default_per = None if default_per is None else float(default_per)
    audit_cell = AuditCell(cell.ic, cell.horizon, cell.seed, per_rebalance_cap=default_per)
    vol_halflife, vol_overlay = resolve_vol_overlay(audit_cell, run_params)
    # HANDOFF task 91 (c): no friction is the half-spread at zero and the shadow
    # coefficient at 0, in the solve and in the engine; the fee drag stays in the net return,
    # which is why a frictionless row is read on `gross_ir`
    costs = audit_cost_model(universe, run_params)
    shadow_coeff = float(run_params.get("constraints.turnover.penalty.coefficient", 0) or 0)
    if cell.frictionless:
        # `CostModel` refuses a multiplier of 0 at construction (a stored run is always at 1);
        # this diagnostic model is set after it, and `half_spread` reads the attribute
        costs.spread_multiplier = 0.0
        shadow_coeff = 0.0
    # HANDOFF task 92: what the solve sees; the engine below is always handed `costs` itself
    solve_costs: Any = AmortisedCosts(costs, cell.horizon) if cell.amortise else costs
    if cell.amortise_shadow:
        shadow_coeff = shadow_coeff / cell.horizon
    rule_class = FromNoViewRule if cell.start_noview else Phase2Rule
    # decisions/0070: the ruled objective unless the cell is recorded (or a task 92 arm). The
    # no-view arm is a rule with no view (the addendum's item 2, and its reviewer's detail
    # (i)): it keeps the legacy arguments, so its run is unchanged.
    legacy = cell.legacy_objective or cell.zero_scores
    clear_usage(inputs.exposures)
    rule = rule_class(
        RowedUniverse(universe, inputs.rowed),
        solve_costs,
        run_params,
        solver,
        scores=scores,
        sigma=sigma,
        exposures=inputs.exposures,
        axis=cell.axis,
        expression=cell.expression,
        horizon=(cell.horizon, cell.horizon),
        shadow_form=resolve_shadow_form(audit_cell, run_params),
        vol_halflife=vol_halflife,
        vol_overlay=vol_overlay,
        shadow_coeff=shadow_coeff,
        per_rebalance_cap=default_per,
        turnover_cap=None,
        amortise_costs=not legacy,
        free_first_book=legacy,
    )
    panel = _clip_panel(universe.engine_panel(), pd.Timestamp(scores.index[-1]))
    exposure_rule = constant_exposures(pd.DataFrame(0.0, index=universe.holdable, columns=["f0"]))
    path = run_walk_forward(
        panel,
        rule,
        universe.benchmark_weekly,
        exposure_rule,
        cost_model=costs,
        params=run_params,
        rebalance_day=str(run_params.get("audit.rebalance_day", "FRI")),
        cash_instrument=universe.cash[0] if len(universe.cash) == 1 else None,
    )
    if len(universe.cash) > 1:
        path.cash_weights = path.weights.reindex(columns=universe.cash).fillna(0.0).sum(axis=1)

    diag = pd.DataFrame(rule.diagnostics)
    te = path.tracking_error().dropna()
    reports = rule.reports(lambda d: factor_covariance(inputs, d, run_params))
    solved = set(rule.books)
    loadings = clear_usage(inputs.exposures)
    loadings = loadings[pd.to_datetime(loadings["used_on_date"]).isin(solved)]
    usage = pd.concat([rule.parameter_usage(), loadings], ignore_index=True)
    verdict = lookahead_veto(
        RunContext(
            run_id=cell.key(),
            observation_usage=_observations(rule.parameter_usage()),
            parameter_usage=usage,
        ),
        run_params,
    )
    ic = realised_ic(plant)
    tv = reports["tracking_variance"]
    row: dict[str, Any] = {
        "key": cell.key(),
        "axis": cell.axis,
        "expression": cell.expression,
        "ic": cell.ic,
        "seed": cell.seed,
        "baseline": cell.baseline,
        "horizon": cell.horizon,
        "ic_prior": float(run_params.require("constraints.views.ic_prior")),
        "ic_prior_multiplier": cell.prior_multiplier,
        "net_ir": path.information_ratio(),
        "gross_ir": gross_ir(path, rule.ppy),
        "zero_scores": cell.zero_scores,
        "frictionless": cell.frictionless,
        "amortise": cell.amortise,
        "amortise_shadow": cell.amortise_shadow,
        "start_noview": cell.start_noview,
        "legacy": legacy,
        "transfer": float(reports["transfer"]),
        "equity_tracking_variance_share": float(tv["equity"].mean())
        if "equity" in tv.columns
        else float("nan"),
        "turnover_annual": path.annualised_turnover(),
        "turnover_p95_rolling_1y": rolling_annual_turnover_quantile(path, rule.ppy, 0.95),
        "te_p95": float(te.quantile(0.95)) if len(te) else float("nan"),
        "te_ex_ante_mean": float(diag["te_ex_ante"].mean()),
        "active_return_annual": float(path.active_returns.mean() * rule.ppy),
        "cost_drag_annual": path.total_cost_drag(),
        "inaccurate_share": float(diag["inaccurate"].mean()),
        "infeasible_te_share": float(diag["status"].str.startswith("infeasible").mean()),
        "max_cash": float(path.cash_weights.max()),
        "n_positions_max": int(path.n_positions().max()),
        "n_holdable_mean": float(diag["n_holdable"].mean()),
        "realised_ic_pooled": ic["pooled"],
        "realised_ic_by_column": ic["by_column_mean"],
        "realised_ic_cross_sectional_demeaned": ic["cross_sectional_demeaned"],
        "lookahead_passed": bool(verdict.passed),
        "lookahead_detail": str(verdict.detail),
        "status": "ok" if verdict.passed else "failed:lookahead",
        "n_rebalances": int(len(path.dates)),
        "first_date": str(path.dates[0].date()),
        "last_date": str(path.dates[-1].date()),
        "solvers_used": ",".join(sorted(set(diag["solver"].astype(str)))),
    }
    row.update(
        risk_calibration(
            path.active_returns,
            diag.set_index("date")["te_ex_ante"],
            rule.ppy,
            float(run_params.require("constraints.tracking_error.max_trailing_3y")),
            te_p95=row["te_p95"],
            active_vol=float(path.active_returns.std() * np.sqrt(rule.ppy)),
            ex_ante_mean=row["te_ex_ante_mean"],
        )
    )
    row["seconds"] = time.time() - started
    if keep is not None:
        keep["reports"] = reports
        keep["costs"] = costs
        keep["solve_costs"] = solve_costs
    return row, rule, path


def alpha_arithmetic(rule: Phase2Rule, costs: Any, horizon: int = PILOT_HORIZON) -> pd.DataFrame:
    """
    HANDOFF task 91 (d), by solved date: the largest absolute instrument alpha (the rule's own
    alpha rows, per week, over the holdable ids), annualised and over the horizon, in bp, beside
    the round trip on that instrument: twice its half-spread plus twice the marginal shadow
    rate the solve paid that week (`diagnostics.shadow_bps`). Derived numbers only.
    """
    diag = pd.DataFrame(rule.diagnostics).set_index("date")
    rows = {}
    for date, alpha in rule._alpha_rows.items():
        a = alpha.astype(float).abs()
        if a.empty or not np.isfinite(a.to_numpy()).any():
            continue
        top = str(a.idxmax())
        half = float(costs.half_spread_vector([top]).iloc[0]) / 1e-4
        shadow = float(diag.at[date, "shadow_bps"]) if date in diag.index else float("nan")
        rows[date] = {
            "instrument": top,
            "max_abs_alpha_annual_bp": float(a.max()) * rule.ppy / 1e-4,
            "max_abs_alpha_horizon_bp": float(a.max()) * horizon / 1e-4,
            "half_spread_bp": half,
            "shadow_marginal_bp": shadow,
            "round_trip_bp": 2.0 * half + 2.0 * shadow,
        }
    return pd.DataFrame(rows).T


def hand_check(rule: Phase2Rule, date: pd.Timestamp, params: Params) -> dict[str, Any]:
    """
    HANDOFF task 91 (e): one date of a cross-sectional region rule, rebuilt outside the rule
    from its raw scores and `sigma` with `views.standardise_from_params`,
    `alpha.cross_sectional_views` and `alpha.alpha_from_views`, beside what the rule used.
    Returns the frames and the largest absolute difference of each.
    """
    from signal_lab.portfolio import views as views_mod

    date = pd.Timestamp(date)
    lo = hi = PILOT_HORIZON
    h = views_mod.horizon_h_from_params(lo, hi, params)
    z = views_mod.standardise_from_params(rule.scores, params)
    scale = float(params.require("constraints.views.ic_prior")) / np.sqrt(h)
    views = alpha_mod.cross_sectional_views(z, rule.sigma, scale)
    frame = rule.exposures.at(date)
    alpha = alpha_mod.alpha_from_views(
        frame, "region", views.loc[date], None, region_cells=rule.exposures.axis("region", date)
    )
    used = rule._alpha_rows.get(date)
    by_region = pd.DataFrame(
        {
            "score": rule.scores.loc[date],
            "sigma": rule.sigma.loc[date],
            "z_rule": rule.z.loc[date],
            "z_hand": z.loc[date],
            "view_rule": rule.views.loc[date],
            "view_hand": views.loc[date],
        }
    )
    hold = list(used.index) if used is not None else list(alpha.index)
    by_instrument = pd.DataFrame(
        {
            "alpha_rule": used if used is not None else pd.Series(np.nan, index=hold),
            "alpha_hand": alpha.reindex(hold).fillna(0.0),
        }
    )

    def gap(a: pd.Series, b: pd.Series) -> float:
        d = (a.astype(float) - b.astype(float)).abs()
        return float(d.max()) if len(d) else float("nan")

    return {
        "date": date,
        "by_region": by_region,
        "by_instrument": by_instrument,
        "max_gap_z": gap(by_region["z_rule"], by_region["z_hand"]),
        "max_gap_view": gap(by_region["view_rule"], by_region["view_hand"]),
        "max_gap_alpha": gap(by_instrument["alpha_rule"], by_instrument["alpha_hand"]),
    }


def gross_ir(path: Any, ppy: float = 52.0) -> float:
    """The IR of the gross active return (`gross_returns - benchmark_returns`), annualised:
    a diagnostic for the frictionless arm only, never ranked (SUBSTRATE section 3)."""
    active = (path.gross_returns - path.benchmark_returns).dropna()
    sd = float(active.std()) if len(active) > 1 else float("nan")
    if not np.isfinite(sd) or sd < 1e-12:
        return float("nan")
    return float(active.mean() * ppy / (sd * np.sqrt(ppy)))


def with_excess(table: pd.DataFrame) -> pd.DataFrame:
    """`net_ir_excess`: each row's net IR less its baseline twin's (same expression, IC, seed,
    prior multiplier); a baseline row's excess is NaN, as is a live row with no twin."""
    keys = ["expression", "ic", "seed", "ic_prior_multiplier"]
    # HANDOFF task 92: a twin is the same arm's (a column absent from older tables is skipped)
    keys += [
        c for c in ("amortise", "amortise_shadow", "start_noview", "legacy") if c in table.columns
    ]
    base = table[table["baseline"].astype(bool)].set_index(keys)["net_ir"]
    live = ~table["baseline"].astype(bool)
    index = pd.MultiIndex.from_frame(table[keys])
    floor = pd.Series(base.reindex(index).to_numpy(), index=table.index)
    out = table.copy()
    out["baseline_net_ir"] = floor.where(live)
    out["net_ir_excess"] = (table["net_ir"] - floor).where(live)
    return out


def summarise(table: pd.DataFrame) -> pd.DataFrame:
    """G's table: per expression, planted IC and prior multiplier, over seeds. No pass or fail."""
    live = with_excess(table)
    live = live[~live["baseline"].astype(bool)]
    grouped = live.groupby(["expression", "ic", "ic_prior_multiplier"])
    out = grouped.agg(
        n=("net_ir", "count"),
        net_ir_mean=("net_ir", "mean"),
        net_ir_min=("net_ir", "min"),
        net_ir_max=("net_ir", "max"),
        baseline_net_ir_mean=("baseline_net_ir", "mean"),
        net_ir_excess_mean=("net_ir_excess", "mean"),
        excess_positive_share=("net_ir_excess", lambda s: float((s > 0).mean())),
        transfer_mean=("transfer", "mean"),
        equity_tv_share_mean=("equity_tracking_variance_share", "mean"),
        turnover_mean=("turnover_annual", "mean"),
        bias_stat_mean=("bias_stat", "mean"),
        inaccurate_share_mean=("inaccurate_share", "mean"),
        infeasible_share_mean=("infeasible_te_share", "mean"),
        realised_ic_mean=("realised_ic_by_column", "mean"),
        lookahead_passed=("lookahead_passed", "all"),
        seconds_mean=("seconds", "mean"),
    )
    return out.reset_index()
