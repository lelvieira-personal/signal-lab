"""
Batched (vectorised across Monte Carlo replications) versions of
`signal_lab.stats.multiple_testing`'s procedures, for `scripts/fdr_vs_fwer.py`
(HANDOFF task 34). Private: the public, tested, one-replication-at-a-time
functions in `multiple_testing.py` are the spec; this module exists only
because looping the study's ~150 scenarios x 5,000 replications in pure Python
would not "run in minutes". Correctness is pinned by
`tests/test_batched_multiple_testing.py`, which checks every function here
against its single-replication counterpart on random data.

Shapes throughout: `t` is `(n, m)`, `T0` is `(n, k, m)` -- `n` replications,
`k` null draws, `m` hypotheses.
"""

from __future__ import annotations

import numpy as np


def batched_marginal_pvalues(t: np.ndarray, T0: np.ndarray) -> np.ndarray:
    """`(n, m)` marginal p-values, one column of `T0` per hypothesis."""
    exceed = (T0 >= t[:, None, :]).sum(axis=1)
    return (1.0 + exceed) / (T0.shape[1] + 1.0)


def batched_holm(p: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    n, m = p.shape
    order = np.argsort(p, axis=1, kind="stable")
    ranks = np.arange(1, m + 1)[None, :]
    raw = (m - ranks + 1) * np.take_along_axis(p, order, axis=1)
    adj_sorted = np.minimum(np.maximum.accumulate(raw, axis=1), 1.0)
    p_adj = np.empty((n, m), dtype=float)
    np.put_along_axis(p_adj, order, adj_sorted, axis=1)
    return p_adj <= alpha, p_adj


def _batched_step_up(p: np.ndarray, scale: float) -> np.ndarray:
    n, m = p.shape
    order = np.argsort(p, axis=1, kind="stable")
    ranks = np.arange(1, m + 1)[None, :]
    raw = scale * m / ranks * np.take_along_axis(p, order, axis=1)
    adj_sorted = np.minimum(np.minimum.accumulate(raw[:, ::-1], axis=1)[:, ::-1], 1.0)
    p_adj = np.empty((n, m), dtype=float)
    np.put_along_axis(p_adj, order, adj_sorted, axis=1)
    return p_adj


def batched_benjamini_hochberg(p: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    p_adj = _batched_step_up(p, scale=1.0)
    return p_adj <= q, p_adj


def batched_benjamini_yekutieli(p: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    m = p.shape[1]
    c_m = float(np.sum(1.0 / np.arange(1, m + 1)))
    p_adj = _batched_step_up(p, scale=c_m)
    return p_adj <= q, p_adj


def batched_standardise_columns(t: np.ndarray, T0: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The batched form of `multiple_testing._standardise_columns`: `t` is
    `(n, m)`, `T0` is `(n, k, m)`; each (replication, hypothesis) column is
    standardised by its own `T0[i, :, j]` mean and sd (ddof=1)."""
    mean = T0.mean(axis=1)  # (n, m)
    sd = T0.std(axis=1, ddof=1)  # (n, m)
    if not np.all(np.isfinite(sd)) or np.any(sd <= 0):
        raise ValueError("a null column has zero or non-finite standard deviation")
    return (t - mean) / sd, (T0 - mean[:, None, :]) / sd[:, None, :]


def batched_romano_wolf(
    t: np.ndarray, T0: np.ndarray, alpha: float, standardise: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """
    The per-replication stepdown of `multiple_testing.romano_wolf`, run for
    every row of `t` at once. Each row's active set shrinks independently; a
    row stops the moment its own round rejects nothing, and is left alone
    (its `active` mask cleared) while other rows keep going. `standardise`
    matches the single-replication function's default and meaning.
    """
    if standardise:
        t, T0 = batched_standardise_columns(t, T0)
    n, m = t.shape
    k = T0.shape[1]
    p_adj = np.full((n, m), np.nan)
    active = np.ones((n, m), dtype=bool)
    floor = np.zeros(n)
    for _ in range(m):
        if not active.any():
            break
        masked = np.where(active[:, None, :], T0, -np.inf)  # (n, k, m)
        M = masked.max(axis=2)  # (n, k)
        exceed = (M[:, :, None] >= t[:, None, :]).sum(axis=1)  # (n, m)
        p_active = (1.0 + exceed) / (k + 1.0)
        reject_now = active & (p_active <= alpha)
        rows_with_reject = reject_now.any(axis=1)
        stalled = active.any(axis=1) & ~rows_with_reject
        if stalled.any():
            idx = active & stalled[:, None]
            p_adj[idx] = np.maximum(floor[:, None], p_active)[idx]
            active[stalled] = False
        if rows_with_reject.any():
            p_adj[reject_now] = np.maximum(floor[:, None], p_active)[reject_now]
            round_max = np.where(reject_now, p_active, -np.inf).max(axis=1)
            floor = np.where(rows_with_reject, np.maximum(floor, round_max), floor)
            active = active & ~reject_now
    return p_adj <= alpha, p_adj


def batched_romano_wolf_gfwer(
    t: np.ndarray, T0: np.ndarray, alpha: float, g: int = 2, standardise: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """
    `multiple_testing.romano_wolf_gfwer`, run for every row of `t`. Unlike
    the other batched functions here, this is a plain per-row loop, not a
    vectorised one: the paper's own step-down (HANDOFF task 40) requires
    enumerating every size-`(g-1)` subset of each row's OWN rejected set,
    which differs in count and membership row to row, so there is no shared
    array shape to vectorise across rows the way `batched_romano_wolf` does.
    Timed at ~0.3ms/row for m=12, k=1000, g=2 -- fast enough that the study
    (`scripts/fdr_vs_fwer.py`) does not need it vectorised.
    """
    from signal_lab.stats.multiple_testing import romano_wolf_gfwer

    n, m = t.shape
    reject = np.empty((n, m), dtype=bool)
    p_adj = np.empty((n, m), dtype=float)
    for i in range(n):
        reject[i], p_adj[i] = romano_wolf_gfwer(t[i], T0[i], alpha, g=g, standardise=standardise)
    return reject, p_adj
