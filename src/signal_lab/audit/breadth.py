"""
Effective breadth, in two dimensions, reported separately.

The fundamental law counts breadth as independent bets per year. Thirty
positions rebalanced weekly is not 52 x 30 of them, for two reasons that have
different fixes and are therefore measured apart:

  * Cross-section. The instruments are correlated -- a global equity universe
    and a duration ladder are a handful of bets wearing a hundred tickers. The
    effective number of bets is Meucci's: exp of the entropy of the normalised
    eigenvalues of the correlation matrix. Measured on ACTIVE returns (in excess
    of the benchmark), because a bet the benchmark already holds is not a bet.

  * Time. A signal with a 26-week horizon does not make 52 independent
    decisions a year. The ladder's IC is a correlation with the h-week forward
    return, so the count that matches it is the non-overlapping one: 52 / h
    decisions a year (decisions/0027).

    It used to be 52 (1 - phi) / (1 + phi) at the signal's measured lag-one
    autocorrelation -- the effective-sample correction for estimating a MEAN
    from an AR(1) series. At phi = (h - 1) / h that is about 52 / (2h - 1),
    half the count above, and on the first lean audit it put the fundamental
    law's TC = 1 "ceiling" above what the constrained, costed ladder achieved
    at h = 26. The measured phi is still recorded; it no longer sets breadth.

The product is the FORMULA breadth. It is a statement to be checked, not a
measurement: the frictionless cells (`ladder.run_frictionless`) measure the
breadth the pipeline actually delivers, and the report prints both.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from signal_lab.portfolio.covariance import effective_bets


@dataclass(frozen=True)
class Breadth:
    n_series: int
    effective_bets_total: float  # on total returns
    effective_bets_active: float  # on returns in excess of the benchmark
    decisions_per_year: dict[int, float]  # horizon -> independent decisions a year, 52 / h
    signal_phi: dict[int, float] = field(default_factory=dict)  # measured, reported only

    def effective_breadth(self, horizon: int) -> float:
        return self.effective_bets_active * self.decisions_per_year[horizon]

    def implied_ic(self, target_ir: float, horizon: int, transfer: float = 1.0) -> float:
        """The IC the fundamental law would require: IR = IC sqrt(BR) TC."""
        br = self.effective_breadth(horizon)
        if not np.isfinite(br) or br <= 0:
            return float("nan")
        return float(target_ir / (np.sqrt(br) * transfer))


def independent_decisions_per_year(phi: float, periods_per_year: float = 52.0) -> float:
    """
    The AR(1) effective-sample count for lag-one autocorrelation `phi`.

    Kept as a diagnostic. It is NOT the time breadth of a planted signal; see
    the module docstring and `decisions_per_year`.
    """
    phi = float(np.clip(phi, -0.999, 0.999))
    return float(periods_per_year * (1.0 - phi) / (1.0 + phi))


def effective_breadth(
    weekly: pd.DataFrame,
    benchmark: pd.Series,
    horizons: list[int],
    signal_phi: dict[int, float] | None = None,
    periods_per_year: float = 52.0,
    min_periods: int = 104,
) -> Breadth:
    """
    Breadth over the development window as a description of the universe.

    Full-sample correlation, deliberately: this is a statement about how many
    bets the universe contains, not a forecast, and the walk-forward covariance
    the solver uses is a different object with a different job. Series with
    fewer than `min_periods` observations are left out of the count rather than
    padded.

    Time breadth is `periods_per_year / h` (decisions/0027). `signal_phi`, the
    measured lag-one autocorrelation per horizon, is carried through for the
    report and does not enter the count.
    """
    keep = weekly.columns[weekly.notna().sum() >= min_periods]
    total = weekly[keep].dropna(how="any")
    if total.shape[1] < 2:
        raise ValueError("fewer than two series have enough history for a breadth count")
    active = total.sub(benchmark.reindex(total.index), axis=0).dropna(how="any")

    decisions = {int(h): decisions_per_year(int(h), periods_per_year) for h in horizons}

    return Breadth(
        n_series=int(total.shape[1]),
        effective_bets_total=effective_bets(total.corr()),
        effective_bets_active=effective_bets(active.corr()),
        decisions_per_year=decisions,
        signal_phi={int(k): float(v) for k, v in (signal_phi or {}).items()},
    )


def decisions_per_year(horizon: int, periods_per_year: float = 52.0) -> float:
    """Non-overlapping h-period decisions a year: the time breadth (decisions/0027)."""
    if horizon < 1:
        raise ValueError("horizon must be at least one period")
    return float(periods_per_year / horizon)
