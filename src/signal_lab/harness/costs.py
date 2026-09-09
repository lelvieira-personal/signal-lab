"""
The cost model. SUBSTRATE section 8.

    net = gross - traded_notional * half_spread - annual_drag / weeks_per_year

Turnover is **traded notional**: `sum |w_target - w_drifted|`, buys plus sells
(owner, decisions/0017). Both the 150% veto ceiling and the section 8 cost
formula read this same figure, which is what makes

    net = gross - turnover * half_spread - drag / weeks_per_year

dimensionally correct exactly as written: a half-spread is paid on every unit
traded in either direction.

`turnover_one_way` (half of it) is computed and reported alongside, because it
is the figure some conventions use and a reader comparing against another
manager's numbers will want it. Nothing in the lab is measured against it.

Weight drift is the other thing this module exists to get right. Between
rebalances a portfolio drifts with its own returns, so turnover is the distance
from the DRIFTED weights to the new target, not from the previous target.

The previous-target version is not biased in a known direction, which is what
makes it dangerous. A persistent rule that returns the same target every week
reports ZERO turnover and zero cost, while the real book has drifted and must be
traded back. A rule whose drift happens to move toward the next target reports
too much. Either way the cost is wrong by an amount that depends on what the
market did, and it is largest in the volatile weeks where costs matter most.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from signal_lab.params import Params, get_params

REPO_ROOT = Path(__file__).resolve().parents[3]
UNIVERSE = REPO_ROOT / "data" / "universe" / "investable_universe.csv"

BPS = 1e-4


@dataclass(frozen=True)
class CostBreakdown:
    """Costs for one rebalance, kept apart so the digest can show why."""

    traded_notional: float  # sum |dw| -- THE turnover figure, veto and cost
    turnover_one_way: float  # half of it; reported for comparison only
    spread_cost: float
    drag_cost: float

    @property
    def total(self) -> float:
        return self.spread_cost + self.drag_cost


class CostModel:
    """
    Per-instrument costs from params/costs.yaml and the universe's bucket map.

    An instrument with no bucket is charged the dearest bucket (decisions/0002).
    Costing an unmapped instrument cheaply flatters it, and the failure is
    silent: a signal that happens to concentrate in unmapped instruments gets a
    free subsidy nobody sees.
    """

    def __init__(
        self,
        params: Params | None = None,
        buckets: dict[str, str] | None = None,
        universe_csv: Path | str | None = None,
    ):
        self.params = params or get_params()
        self.weeks_per_year = float(self.params.require("costs.application.weeks_per_year"))
        self.default_bucket = str(self.params.require("costs.default_bucket"))
        self._rates = self.params.require("costs.buckets")
        self.buckets = buckets if buckets is not None else self._load_buckets(universe_csv)

    def _load_buckets(self, universe_csv: Path | str | None) -> dict[str, str]:
        path = Path(universe_csv or UNIVERSE)
        if not path.exists():
            return {}
        frame = pd.read_csv(path)
        return dict(zip(frame["ticker"], frame["cost_bucket"], strict=True))

    # --- per-instrument rates ------------------------------------------------

    def bucket(self, instrument: str) -> str:
        return self.buckets.get(instrument, self.default_bucket)

    def half_spread(self, instrument: str) -> float:
        return float(self._rates[self.bucket(instrument)]["half_spread_bps"]) * BPS

    def annual_drag(self, instrument: str) -> float:
        return float(self._rates[self.bucket(instrument)]["annual_fee_tracking_bps"]) * BPS

    def half_spread_vector(self, instruments) -> pd.Series:
        return pd.Series({i: self.half_spread(i) for i in instruments}, dtype="float64")

    def annual_drag_vector(self, instruments) -> pd.Series:
        return pd.Series({i: self.annual_drag(i) for i in instruments}, dtype="float64")

    # --- the model -----------------------------------------------------------

    @staticmethod
    def turnover(target: pd.Series, drifted: pd.Series) -> tuple[float, pd.Series]:
        """
        (traded notional, per-instrument traded notional).

        Both series are reindexed to their union with zeros, so an instrument
        entering or leaving the portfolio is a full-size trade rather than a
        silently dropped one.
        """
        idx = target.index.union(drifted.index)
        delta = (target.reindex(idx).fillna(0.0) - drifted.reindex(idx).fillna(0.0)).abs()
        return float(delta.sum()), delta

    def rebalance_cost(self, target: pd.Series, drifted: pd.Series) -> CostBreakdown:
        """Spread cost of moving from the drifted book to the target, plus one week of drag."""
        traded, delta = self.turnover(target, drifted)
        spread = float((delta * self.half_spread_vector(delta.index)).sum())
        held = target[target.abs() > 0]
        drag = float((held.abs() * self.annual_drag_vector(held.index)).sum() / self.weeks_per_year)
        return CostBreakdown(
            traded_notional=traded,
            turnover_one_way=traded / 2.0,
            spread_cost=spread,
            drag_cost=drag,
        )

    def annualised_turnover(self, traded_notional: pd.Series) -> float:
        """Annualised traded notional. This is the figure the veto reads."""
        return float(pd.Series(traded_notional).mean() * self.weeks_per_year)


def drift_weights(weights: pd.Series, returns: pd.Series) -> pd.Series:
    """
    Carry weights through one period of returns.

    w' = w(1+r) / sum(w(1+r)). Instruments with no return that period keep their
    value rather than being dropped: a missing observation is not a -100%
    return. The result renormalises, so a fully invested book stays fully
    invested and drift is a relative effect.
    """
    idx = weights.index
    grown = weights * (1.0 + returns.reindex(idx).fillna(0.0))
    total = grown.sum()
    if not np.isfinite(total) or abs(total) < 1e-12:
        return weights.copy()
    return grown / total


def portfolio_return(weights: pd.Series, returns: pd.Series) -> float:
    """
    One period's return on a book of weights.

    NaN returns contribute zero rather than propagating: an instrument that did
    not print did not move the portfolio, and letting one NaN turn the whole
    period's return into NaN would silently drop a week.
    """
    idx = weights.index
    return float((weights * returns.reindex(idx).fillna(0.0)).sum())
