"""
Reading a recorded estimator-test run for what a build must agree with (HANDOFF task 52).

The test scored a cell only where every estimator had a loading. A build that wants to be
scored on the same cells takes that set from the run's stored loadings, and takes **presence
only**: which cells are finite, never what the other estimators' values are.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def reference_arrays(
    stored: pd.DataFrame,
    estimators: list[str],
    ids: list[str],
    weeks: pd.DatetimeIndex,
    factors: list[str],
) -> dict[str, np.ndarray]:
    """`name -> (T, N, K)` loadings from a run's long `loadings.parquet`, NaN where absent."""
    t_idx = weeks.get_indexer(stored["date"])
    i_idx = pd.Index(ids).get_indexer(stored["instrument"])
    k_idx = pd.Index(factors).get_indexer(stored["factor"])
    out = {}
    for name in estimators:
        sel = (stored["estimator"] == name).to_numpy()
        a = np.full((len(weeks), len(ids), len(factors)), np.nan)
        a[t_idx[sel], i_idx[sel], k_idx[sel]] = stored["loading"].to_numpy()[sel]
        out[name] = a
    return out


def presence_mask(arrays: dict[str, np.ndarray]) -> np.ndarray:
    """(T, N): True where every estimator has a finite loading on every factor."""
    have = np.ones(next(iter(arrays.values())).shape[:2], dtype=bool)
    for a in arrays.values():
        have &= np.isfinite(a).all(axis=2)
    return have
