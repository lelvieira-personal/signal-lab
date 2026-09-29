"""
Multiple-testing procedures. SUBSTRATE section 9; HANDOFF task 34.

The module the real bar-2 gate will use once a search runs: every hypothesis's
test statistic `t` (shape `m`, one per hypothesis) is compared against a joint
null distribution obtained by block-shuffling the whole signal (`stats.blocks`)
and re-running the statistic, one shuffle at a time, giving `T0` (shape
`k x m`): `k` shuffles, one row each, with the SAME permutation shared across
every hypothesis's column so the dependence between hypotheses under the null
is learned from the data rather than assumed independent (SUBSTRATE s9).

Every procedure assumes a one-sided test that rejects for a LARGE statistic
(net_ir_excess, or any monotone transform of it). Marginal p-values from the
null draws, used by the p-value-based procedures:

    p_j = (1 + #{T0[:, j] >= t_j}) / (k + 1)

`holm` and the Benjamini procedures take p-values directly (they do not need
the joint draws, only the marginal ones -- or literature p-values from
elsewhere). `romano_wolf` takes `t` and `T0` directly because its critical
value at each step is the max of the ACTIVE hypotheses' null draws, which
`marginal_pvalues` alone cannot reconstruct once a hypothesis has been removed
from the active set.

`romano_shaikh_wolf_fdr` is NOT implemented -- see its docstring.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "marginal_pvalues",
    "holm",
    "romano_wolf",
    "benjamini_hochberg",
    "benjamini_yekutieli",
    "romano_shaikh_wolf_fdr",
]


def marginal_pvalues(t: np.ndarray, T0: np.ndarray) -> np.ndarray:
    """
    One-sided marginal p-value for each of `m` statistics against its own
    column of `k` null draws: `p_j = (1 + #{T0[:, j] >= t_j}) / (k + 1)`.

    `t` is shape `(m,)`, `T0` is shape `(k, m)`.
    """
    t = np.asarray(t, dtype=float)
    T0 = np.asarray(T0, dtype=float)
    if T0.ndim != 2 or T0.shape[1] != t.shape[0]:
        raise ValueError(f"T0 must be (k, {t.shape[0]}), got {T0.shape}")
    exceed = (T0 >= t[None, :]).sum(axis=0)
    return (1.0 + exceed) / (T0.shape[0] + 1.0)


def holm(p: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Holm (1979) stepdown Bonferroni. FWER <= alpha under arbitrary dependence
    (it makes no dependence assumption at all, which is also why it is
    conservative relative to `romano_wolf` whenever the statistics are
    positively dependent, as the audit's shuffled cells are).

    Sort p ascending; the i-th smallest (1-indexed, `m` total) is compared
    against `alpha / (m - i + 1)`. Rejects the hypotheses up to and including
    the first `i` for which this fails. The adjusted p-value at rank `i` is
    `(m - i + 1) * p_(i)`, made monotone non-decreasing by a running maximum
    (Holm's own construction; see e.g. Wright 1992 for the closed form used
    here) and capped at 1.

    Returns `(reject, p_adjusted)`, both shape `(m,)`, in the ORIGINAL order
    of `p`.
    """
    p = np.asarray(p, dtype=float)
    m = p.shape[0]
    if m == 0:
        return np.zeros(0, dtype=bool), np.zeros(0, dtype=float)
    order = np.argsort(p, kind="stable")
    ranks = np.arange(1, m + 1)
    raw = (m - ranks + 1) * p[order]
    adj_sorted = np.minimum(np.maximum.accumulate(raw), 1.0)
    p_adj = np.empty(m, dtype=float)
    p_adj[order] = adj_sorted
    return p_adj <= alpha, p_adj


def _step_up_adjust(p: np.ndarray, scale: float) -> np.ndarray:
    """
    Shared machinery for BH and BY: sort ascending, adjusted p-value at rank
    `i` (1-indexed) is `scale * m / i * p_(i)`, made monotone non-INCREASING
    from the largest rank down (a running minimum read backwards), capped at 1.
    """
    m = p.shape[0]
    order = np.argsort(p, kind="stable")
    ranks = np.arange(1, m + 1)
    raw = scale * m / ranks * p[order]
    adj_sorted = np.minimum(np.minimum.accumulate(raw[::-1])[::-1], 1.0)
    p_adj = np.empty(m, dtype=float)
    p_adj[order] = adj_sorted
    return p_adj


def benjamini_hochberg(p: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Benjamini & Hochberg (1995) step-up FDR control at level `q`. Exact under
    independence or positive regression dependence (PRDS); SUBSTRATE s9 notes
    the audit's shuffled null is dependence-aware, which BH itself is not --
    `romano_shaikh_wolf_fdr` would be the dependence-robust FDR analogue, and
    it is not implemented here (see its docstring).

    Returns `(reject, p_adjusted)` in the original order of `p`.
    """
    p = np.asarray(p, dtype=float)
    if p.shape[0] == 0:
        return np.zeros(0, dtype=bool), np.zeros(0, dtype=float)
    p_adj = _step_up_adjust(p, scale=1.0)
    return p_adj <= q, p_adj


def benjamini_yekutieli(p: np.ndarray, q: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Benjamini & Yekutieli (2001) step-up FDR control at level `q`, valid under
    ARBITRARY dependence: the same procedure as BH but with the threshold
    scaled down by `c(m) = sum_{i=1}^m 1/i`, the price of not assuming PRDS.

    Returns `(reject, p_adjusted)` in the original order of `p`.
    """
    p = np.asarray(p, dtype=float)
    m = p.shape[0]
    if m == 0:
        return np.zeros(0, dtype=bool), np.zeros(0, dtype=float)
    c_m = float(np.sum(1.0 / np.arange(1, m + 1)))
    p_adj = _step_up_adjust(p, scale=c_m)
    return p_adj <= q, p_adj


def romano_wolf(t: np.ndarray, T0: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Romano & Wolf (2005, Econometrica 73(4); 2016, Statistics & Probability
    Letters 113) stepdown max-T. FWER <= alpha, using the ACTUAL joint null
    (`T0`'s columns share the permutation the audit drew, so real dependence
    between hypotheses raises power over Holm rather than being ignored).

    At each step, the critical region for the still-active hypotheses is the
    upper tail of the MAX of their own null columns (so a hypothesis already
    rejected can no longer inflate the multiplicity charged to the rest):

        M_b = max_{j in active} T0[b, j]          for each of the k draws
        p_j = (1 + #{b : M_b >= t_j}) / (k + 1)    for j in active

    Any active hypothesis with `p_j <= alpha` is rejected this round and
    removed from the active set; the max is then recomputed over the smaller
    set and the round repeats until a round rejects nothing. Adjusted
    p-values are floored at the running maximum of every already-rejected
    round's p-value, so they are monotone non-decreasing in rejection order
    (a hypothesis rejected earlier never reports a larger adjusted p-value
    than one rejected later) -- the enforcement step every stepdown procedure
    needs (Romano & Wolf 2005 s2.3).

    `t` is shape `(m,)`; `T0` is shape `(k, m)`, one row per shuffle. Returns
    `(reject, p_adjusted)` in the original order of `t`.
    """
    t = np.asarray(t, dtype=float)
    T0 = np.asarray(T0, dtype=float)
    m = t.shape[0]
    if T0.ndim != 2 or T0.shape[1] != m:
        raise ValueError(f"T0 must be (k, {m}), got {T0.shape}")
    k = T0.shape[0]
    p_adj = np.empty(m, dtype=float)
    remaining = np.arange(m)
    floor = 0.0
    while remaining.size:
        M = T0[:, remaining].max(axis=1)  # (k,)
        p_active = (1.0 + (M[:, None] >= t[remaining][None, :]).sum(axis=0)) / (k + 1.0)
        reject_now = p_active <= alpha
        if not reject_now.any():
            p_adj[remaining] = np.maximum(floor, p_active)
            break
        p_adj[remaining[reject_now]] = np.maximum(floor, p_active[reject_now])
        floor = max(floor, float(p_active[reject_now].max()))
        remaining = remaining[~reject_now]
    return p_adj <= alpha, p_adj


def romano_shaikh_wolf_fdr(t: np.ndarray, T0: np.ndarray, q: float):
    """
    NOT IMPLEMENTED. HANDOFF task 34 asked for the bootstrap FDR-under-
    dependence stepdown of Romano, Shaikh & Wolf (2008), cited there as
    Econometric Theory 24(2). That citation is Romano, Shaikh & Wolf,
    "Formalized data snooping based on generalized error rates" (Econometric
    Theory 24(2), 2008), which controls the generalised familywise error rate
    k-FWER (the probability of `k` or more false rejections) via a bootstrap
    stepdown, not the false discovery rate. The FDR-under-dependence result
    with a bootstrap/subsampling construction is a DIFFERENT paper by the same
    three authors (Romano, Shaikh & Wolf, "Control of the false discovery rate
    under dependence using the bootstrap and subsampling", TEST 17(3), 2008).

    Implementing either faithfully from memory, without the source in hand to
    check the exact stepdown construction and the choice it leaves open (both
    papers have one), risks shipping a plausible-looking but wrong procedure
    under a name that claims paper fidelity -- exactly what SUBSTRATE's
    fail-loud discipline exists to prevent. Per the task's own instruction,
    this raises rather than approximates. `holm`, `romano_wolf`,
    `benjamini_hochberg` and `benjamini_yekutieli` are implemented and tested;
    this one is not.
    """
    raise NotImplementedError(
        "romano_shaikh_wolf_fdr is not implemented -- see this function's docstring "
        "for which of the two 2008 Romano-Shaikh-Wolf papers is ambiguous here and why "
        "it was not approximated. Use benjamini_yekutieli for a dependence-robust FDR "
        "bound, or benjamini_hochberg under PRDS."
    )
