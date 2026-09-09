"""
The walk-forward engine. SUBSTRATE section 16, phase 1.

Given a weight path, this computes what the portfolio actually did: gross and
net returns, turnover, costs, active return against the 50/50 benchmark,
tracking error, active drawdown, and the exposure path through the
characteristic map. It does not choose weights. Choosing them is the optimiser's
job in phase 2, and keeping the two apart is what lets phase 1 validate the
accounting against planted ground truth.

The accounting is where a backtest quietly lies, so the invariants are explicit:

  * Weights drift between rebalances. Turnover is measured from the drifted book
    to the new target, never from the previous target. Measuring from the
    previous target is simply wrong rather than biased in a known direction: it
    understates when the rule is persistent (a book that has drifted and needs
    trading back reports zero turnover) and overstates when drift happens to
    have moved toward the new target.
  * A rebalance happens at the close on the rebalance date, so that week's
    return is earned on the OLD book and the new book starts the following
    period. Charging the new weights for the week that produced the signal is a
    one-period lookahead worth several basis points a week.
  * Costs are charged at the rebalance, on traded notional, and are deducted
    from that period's return rather than smeared.
  * The exposure matrix is a function of date, not a constant (decisions/0015).
    Phase 2 makes the loadings time-varying and walk-forward; phase 1 passes a
    constant matrix through the same signature so nothing has to be rewritten.
  * Alternate rebalance days are AVERAGED, never selected (SUBSTRATE sections 4
    and 9). `run_averaged_over_rebalance_days` returns the mean path.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.harness.costs import CostModel, drift_weights, portfolio_return
from signal_lab.harness.run_context import RunContext
from signal_lab.loaders.base import ReturnPanel
from signal_lab.loaders.holdout import enforce_holdout
from signal_lab.params import Params, get_params

# A weight rule: (date, panel) -> target weights. Phase 1 is handed a path; the
# optimiser fills this in during phase 2.
WeightRule = Callable[[pd.Timestamp, ReturnPanel], pd.Series]

# The exposure matrix as of a date: instruments x factors. Constant in phase 1.
ExposureRule = Callable[[pd.Timestamp], pd.DataFrame]

DAY_CODES = {"MON": "W-MON", "TUE": "W-TUE", "WED": "W-WED", "THU": "W-THU", "FRI": "W-FRI"}


@dataclass
class PortfolioPath:
    """Everything one walk-forward pass produced. Every series is per rebalance."""

    dates: pd.DatetimeIndex
    weights: pd.DataFrame
    gross_returns: pd.Series
    net_returns: pd.Series
    benchmark_returns: pd.Series
    active_returns: pd.Series
    turnover: pd.Series  # traded notional per rebalance, sum |dw|
    turnover_one_way: pd.Series  # half of it, for comparison with other conventions
    cost_drag: pd.Series
    cash_weights: pd.Series
    exposures: pd.DataFrame
    rebalance_day: str = "FRI"
    meta: dict[str, Any] = field(default_factory=dict)

    # --- derived statistics --------------------------------------------------

    def cumulative_active(self) -> pd.Series:
        return (1.0 + self.active_returns).cumprod()

    def active_drawdown(self) -> pd.Series:
        cum = self.cumulative_active()
        return cum / cum.cummax() - 1.0

    def max_active_drawdown(self) -> float:
        return float(-self.active_drawdown().min())

    def tracking_error(self, window_years: int = 3, periods_per_year: int = 52) -> pd.Series:
        window = int(window_years * periods_per_year)
        return self.active_returns.rolling(window, min_periods=window).std() * np.sqrt(
            periods_per_year
        )

    def information_ratio(self, periods_per_year: int = 52) -> float:
        """
        Annualised mean active return over annualised active volatility.

        Net by construction: `active_returns` is built from `net_returns`.
        SUBSTRATE section 3 ranks on this and on nothing else.
        """
        active = self.active_returns.dropna()
        if len(active) < 2:
            return float("nan")
        sd = float(active.std())
        if not np.isfinite(sd) or sd < 1e-12:
            return float("nan")
        return float(active.mean() * periods_per_year / (sd * np.sqrt(periods_per_year)))

    def annualised_turnover(self, periods_per_year: int = 52) -> float:
        """Annualised traded notional, the figure the 150% ceiling applies to."""
        return float(self.turnover.mean() * periods_per_year)

    def annualised_turnover_one_way(self, periods_per_year: int = 52) -> float:
        return float(self.turnover_one_way.mean() * periods_per_year)

    def total_cost_drag(self, periods_per_year: int = 52) -> float:
        """Annualised cost drag, the number that replaces gross IR (decisions/0004)."""
        return float(self.cost_drag.mean() * periods_per_year)

    def n_positions(self) -> pd.Series:
        return (self.weights.abs() > 0).sum(axis=1)

    def summary(self) -> dict[str, float]:
        return {
            "net_ir": self.information_ratio(),
            "te": float(self.tracking_error().max() * 100)
            if self.tracking_error().notna().any()
            else float("nan"),
            "turnover": self.annualised_turnover() * 100,
            "turnover_one_way": self.annualised_turnover_one_way() * 100,
            "max_cash": float(self.cash_weights.max() * 100),
            "n_positions": float(self.n_positions().max()),
            "max_active_drawdown": self.max_active_drawdown() * 100,
            "cost_drag": self.total_cost_drag() * 100,
        }


def rebalance_dates(
    index: pd.DatetimeIndex, day: str = "FRI", params: Params | None = None
) -> pd.DatetimeIndex:
    """
    The trading dates on which the book is rebalanced.

    Anchored to the panel's own dates rather than to a calendar: the last
    available trading date on or before each nominal weekly date, so a rebalance
    never lands on a holiday and is never silently skipped.
    """
    params = params or get_params()
    code = DAY_CODES.get(day.upper())
    if code is None:
        raise ValueError(f"unknown rebalance day {day!r}; expected one of {sorted(DAY_CODES)}")
    index = pd.DatetimeIndex(index).sort_values()
    nominal = pd.date_range(index.min(), index.max(), freq=code)
    positions = index.searchsorted(nominal, side="right") - 1
    positions = positions[positions >= 0]
    return pd.DatetimeIndex(index[np.unique(positions)])


def constant_exposures(matrix: pd.DataFrame) -> ExposureRule:
    """
    Wrap a static matrix in the time-varying signature.

    Phase 1 uses this. Phase 2 replaces it with walk-forward estimated loadings
    without the engine or its artifacts changing shape (decisions/0015).
    """

    def rule(_date: pd.Timestamp) -> pd.DataFrame:
        return matrix

    return rule


def run_walk_forward(
    panel: ReturnPanel,
    weight_rule: WeightRule,
    benchmark_returns: pd.Series,
    exposure_rule: ExposureRule,
    cost_model: CostModel | None = None,
    params: Params | None = None,
    rebalance_day: str = "FRI",
    cash_instrument: str | None = None,
) -> PortfolioPath:
    """
    One walk-forward pass. Returns the path; computes no verdict.

    The loop, per rebalance period:
      1. earn the period's return on the book held THROUGH it (the old book);
      2. drift that book with the same returns;
      3. ask the weight rule for a new target as of the period end;
      4. charge the move from the drifted book to the target;
      5. hold the target through the next period.

    Step 1 before step 3 is the ordering that matters. A rule that sees the
    period's return and is charged that same period's return on its new weights
    earns a one-period lookahead, and on weekly data that is worth more than
    most of the signals in this lab.
    """
    params = params or get_params()
    cost_model = cost_model or CostModel(params)

    enforce_holdout(panel.returns, params, what="walk-forward engine (panel)")
    enforce_holdout(benchmark_returns, params, what="walk-forward engine (benchmark)")

    dates = rebalance_dates(panel.returns.index, rebalance_day, params)
    if len(dates) < 3:
        raise ValueError(f"{len(dates)} rebalance dates is not a walk-forward")

    daily = panel.returns
    periods_per_year = float(params.get("costs.application.weeks_per_year", 52))

    book = weight_rule(dates[0], panel)
    if book is None or book.empty:
        raise ValueError("the weight rule returned no weights on the first rebalance date")

    rows: list[dict[str, Any]] = []
    weight_rows: dict[pd.Timestamp, pd.Series] = {}
    exposure_rows: dict[pd.Timestamp, pd.Series] = {}

    for previous, current in zip(dates[:-1], dates[1:], strict=True):
        # 1. the period's compounded return, earned on the book held through it
        window = daily.loc[(daily.index > previous) & (daily.index <= current)]
        held = book.copy()
        gross = 1.0
        for day in window.index:
            day_returns = window.loc[day]
            gross *= 1.0 + portfolio_return(held, day_returns)
            held = drift_weights(held, day_returns)
        gross -= 1.0

        # 2-4. rebalance at the close, charged on the drifted book
        target = weight_rule(current, panel)
        breakdown = cost_model.rebalance_cost(target, held)
        net = gross - breakdown.total

        exposures = exposure_rule(current)
        aligned = target.reindex(exposures.index).fillna(0.0)
        exposure_rows[current] = exposures.T.dot(aligned)

        cash = float(target.get(cash_instrument, 0.0)) if cash_instrument else 0.0
        weight_rows[current] = target
        rows.append(
            {
                "date": current,
                "gross": gross,
                "net": net,
                "turnover": breakdown.traded_notional,
                "turnover_one_way": breakdown.turnover_one_way,
                "cost_drag": breakdown.total,
                "cash": cash,
            }
        )
        book = target

    frame = pd.DataFrame(rows).set_index("date")
    index = pd.DatetimeIndex(frame.index)
    bench = benchmark_returns.reindex(index).fillna(0.0)

    return PortfolioPath(
        dates=index,
        weights=pd.DataFrame(weight_rows).T.reindex(index).fillna(0.0),
        gross_returns=frame["gross"],
        net_returns=frame["net"],
        benchmark_returns=bench,
        active_returns=frame["net"] - bench,
        turnover=frame["turnover"],
        turnover_one_way=frame["turnover_one_way"],
        cost_drag=frame["cost_drag"],
        cash_weights=frame["cash"],
        exposures=pd.DataFrame(exposure_rows).T.reindex(index),
        rebalance_day=rebalance_day,
        meta={"periods_per_year": periods_per_year, "n_rebalances": len(index)},
    )


def run_averaged_over_rebalance_days(
    panel: ReturnPanel,
    weight_rule: WeightRule,
    benchmark_returns: pd.Series,
    exposure_rule: ExposureRule,
    cost_model: CostModel | None = None,
    params: Params | None = None,
    days: list[str] | None = None,
) -> tuple[PortfolioPath, dict[str, PortfolioPath]]:
    """
    Average over alternate rebalance days. SUBSTRATE sections 4 and 9.

    "Alternates tested by averaging over Tue/Wed/Fri" and "alternative rebalance
    days are averaged, not selected". Reporting the best day would be selection
    on a nuisance parameter, and the spread across days is itself a stability
    diagnostic worth keeping -- a strategy whose IR depends on rebalancing on a
    Wednesday has not found anything.

    Returns the averaged path and the per-day paths behind it.
    """
    params = params or get_params()
    days = days or list(params.get("constraints.rebalance.alternates", ["FRI"]))

    paths = {
        day: run_walk_forward(
            panel, weight_rule, benchmark_returns, exposure_rule, cost_model, params, day
        )
        for day in days
    }

    def mean_series(attr: str) -> pd.Series:
        # sort=True is explicit: the per-day paths have different rebalance
        # dates, so the union index must be ordered or the averaged series comes
        # back shuffled and every rolling statistic on it is nonsense.
        frame = pd.concat([getattr(p, attr) for p in paths.values()], axis=1, sort=True)
        return frame.mean(axis=1).dropna()

    primary = paths[days[-1]]
    averaged = PortfolioPath(
        dates=primary.dates,
        weights=primary.weights,
        gross_returns=mean_series("gross_returns"),
        net_returns=mean_series("net_returns"),
        benchmark_returns=mean_series("benchmark_returns"),
        active_returns=mean_series("active_returns"),
        turnover=mean_series("turnover"),
        turnover_one_way=mean_series("turnover_one_way"),
        cost_drag=mean_series("cost_drag"),
        cash_weights=mean_series("cash_weights"),
        exposures=primary.exposures,
        rebalance_day="averaged:" + ",".join(days),
        meta={
            "averaged_over": days,
            "ir_by_day": {d: p.information_ratio() for d, p in paths.items()},
        },
    )
    return averaged, paths


def to_run_context(
    path: PortfolioPath,
    run_id: str,
    panel: ReturnPanel,
    **overrides: Any,
) -> RunContext:
    """Populate the veto inputs from a completed path."""
    ctx = RunContext(
        run_id=run_id,
        weights=path.weights,
        cash_weights=path.cash_weights,
        turnover=path.turnover,
        rebalances_per_year=float(path.meta.get("periods_per_year", 52)),
        te_trailing_3y=path.tracking_error(),
        active_returns=path.active_returns,
        series_meta=panel.meta,
    )
    for key, value in overrides.items():
        setattr(ctx, key, value)
    return ctx
