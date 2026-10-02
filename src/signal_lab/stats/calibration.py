"""
The per-calendar-year bias statistic of decisions/0027 and 0030, as one function.

`z` is a series of standardised errors indexed by date; the statistic is its
standard deviation (ddof 1) within each calendar year, read only for a year with
at least `min_obs` readings, and the gate is the worst year. 1 is a calibrated
model. `audit.ladder.risk_calibration` and the loading-estimator test
(`measurement.fidelity`) both call this, so the two cannot drift apart. (The veto
itself, `vetoes/rules.py`, is owner-only and carries its own copy of the same two
lines; it was not touched.)
"""

from __future__ import annotations

import pandas as pd


def annual_bias(z: pd.Series, min_obs: int) -> dict[int, float]:
    """`{year: std(z within year, ddof=1)}` for each calendar year with `min_obs` readings."""
    if not isinstance(z.index, pd.DatetimeIndex) or len(z) < 2:
        return {}
    return {
        int(year): float(group.std(ddof=1))
        for year, group in z.groupby(z.index.year)
        if len(group) >= min_obs
    }


def worst_year(annual: dict[int, float]) -> tuple[int | None, float]:
    """The year with the largest statistic and its value, or `(None, nan)`."""
    if not annual:
        return None, float("nan")
    year = max(annual, key=annual.__getitem__)
    return year, annual[year]
