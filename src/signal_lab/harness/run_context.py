"""
RunContext: everything a veto needs, and nothing it should not have.

A veto is a pure function of this object. Making the inputs explicit means a
veto cannot reach into a backtest and recompute something a different way, and
it means a veto can be tested on a hand-built context rather than on a full run.

Fields are optional because phase 0 has no engine. A veto whose input is absent
FAILS (params/vetoes.yaml: evaluation.on_missing_input: fail). Fail-open would
let an unmeasured run onto the leaderboard, which is the one outcome the veto
set exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


class MissingInput(Exception):
    """A veto's input is absent, so the veto cannot be evaluated."""


@dataclass
class RunContext:
    """
    Inputs to the veto set. See SUBSTRATE section 10 for what each veto uses.
    """

    run_id: str
    hypothesis_id: str | None = None
    family: str | None = None
    aggregation: str | None = None
    seed: int | None = None
    data_snapshot_hash: str = "unknown"

    # --- portfolio-shape inputs ---
    weights: pd.DataFrame | None = None  # dates x instrument, sums to 1 with cash
    cash_weights: pd.Series | None = None  # dates, fraction of NAV in cash
    turnover: pd.Series | None = None  # per rebalance, TRADED NOTIONAL (sum |dw|)
    rebalances_per_year: float = 52.0
    te_trailing_3y: pd.Series | None = None  # annualised, as a fraction
    active_returns: pd.Series | None = None  # per rebalance, strategy minus benchmark

    # --- data-integrity inputs ---
    signal_availability: pd.DataFrame | None = None  # dates x series, bool
    estimation_universe: list[str] = field(default_factory=list)
    observation_usage: pd.DataFrame | None = None  # knowledge_date, used_on_date, ...
    return_contributions: pd.DataFrame | None = None  # series_id, date
    series_meta: dict[str, Any] = field(default_factory=dict)

    # --- statistical inputs ---
    seed_irs: dict[int, float] | None = None  # seed -> net IR
    romano_wolf: dict[str, Any] | None = None  # {"rejected": bool, "fwer_alpha": float, ...}
    realised_direction: str | None = None  # "positive" | "negative" | "flat"
    preregistered_direction: str | None = None  # from the hypothesis file

    # --- diagnostics, never used by a veto ---
    notes: dict[str, Any] = field(default_factory=dict)

    def require(self, name: str) -> Any:
        value = getattr(self, name, None)
        if value is None:
            raise MissingInput(name)
        if isinstance(value, (pd.Series, pd.DataFrame)) and value.empty:
            raise MissingInput(f"{name} (empty)")
        if isinstance(value, (list, dict)) and len(value) == 0:
            raise MissingInput(f"{name} (empty)")
        return value

    def annualised_turnover(self) -> float:
        """
        Annualised traded notional -- buys plus sells (decisions/0017).

        Not the one-way figure. Reading one-way here would let a strategy trade
        300% of NAV a year against a ceiling meant to permit 150%.
        """
        turnover = self.require("turnover")
        return float(turnover.mean() * self.rebalances_per_year)
