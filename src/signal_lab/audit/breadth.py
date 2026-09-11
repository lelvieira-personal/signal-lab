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
    decisions a year. For a lag-one autocorrelation phi the independent
    decisions per year are 52 (1 - phi) / (1 + phi), the usual effective-sample
    correction for an AR(1) series.

The product is the breadth the fundamental law would use, and the IC it then
implies for the target IR (at transfer coefficient one) is reported next to the
IC the simulated ladder actually needed. The gap between the two is the price
of the constraints -- long-only, cash, positions, turnover -- and of the
covariance error the solver works with. It is the number the Research OS
advice asked for, measured rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from signal_lab.portfolio.covariance import effective_bets


@dataclass(frozen=True)
class Breadth:
    n_series: int
    effective_bets_total: float  # on total returns
    effective_bets_active: float  # on returns in excess of the benchmark
    decisions_per_year: dict[int, float]  # horizon -> independent decisions a year

    def effective_breadth(self, horizon: int) -> float:
        return self.effective_bets_active * self.decisions_per_year[horizon]

    def implied_ic(self, target_ir: float, horizon: int, transfer: float = 1.0) -> float:
        """The IC the fundamental law would require: IR = IC sqrt(BR) TC."""
        br = self.effective_breadth(horizon)
        if not np.isfinite(br) or br <= 0:
            return float("nan")
        return float(target_ir / (np.sqrt(br) * transfer))


def independent_decisions_per_year(phi: float, periods_per_year: float = 52.0) -> float:
    """Independent decisions a year for lag-one autocorrelation `phi`."""
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

    `signal_phi` supplies the measured lag-one autocorrelation per horizon; when
    absent the construction's value (h - 1) / h is used.
    """
    keep = weekly.columns[weekly.notna().sum() >= min_periods]
    total = weekly[keep].dropna(how="any")
    if total.shape[1] < 2:
        raise ValueError("fewer than two series have enough history for a breadth count")
    active = total.sub(benchmark.reindex(total.index), axis=0).dropna(how="any")

    decisions = {}
    for h in horizons:
        phi = (signal_phi or {}).get(h, (h - 1) / h)
        decisions[h] = independent_decisions_per_year(phi, periods_per_year)

    return Breadth(
        n_series=int(total.shape[1]),
        effective_bets_total=effective_bets(total.corr()),
        effective_bets_active=effective_bets(active.corr()),
        decisions_per_year=decisions,
    )
