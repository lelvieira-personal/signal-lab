"""
The multiple-testing module (HANDOFF task 34). SUBSTRATE section 9.
"""

from __future__ import annotations

import numpy as np
import pytest

from signal_lab.stats.multiple_testing import (
    benjamini_hochberg,
    benjamini_yekutieli,
    holm,
    marginal_pvalues,
    romano_shaikh_wolf_fdr,
    romano_wolf,
)

# --- a hand-worked example ----------------------------------------------------
#
# p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.3],
# alpha = q = 0.05, m = 10. Worked by hand (not lifted from a named source, to
# avoid misquoting a textbook table from memory):
#
# Holm: threshold at rank i is alpha/(m-i+1): 0.005, 0.00556, 0.00625, ...,
# 0.05. p_(1)=0.001 <= 0.005 (reject); p_(2)=0.008 <= 0.00556 is FALSE, so the
# stepdown stops. Holm rejects rank 1 only.
#
# BH: threshold at rank i is i*q/m: 0.005, 0.01, 0.015, .... p_(1)=0.001<=0.005
# and p_(2)=0.008<=0.01 both hold; p_(3)=0.039<=0.015 fails. The largest i with
# p_(i) <= i*q/m is i=2, so BH rejects ranks 1-2.
#
# BY: same as BH but scaled by c(10) = sum(1/i, i=1..10) ~= 2.928968.
# Threshold at rank i is i*q/(m*c_m): rank 1 -> 0.05/29.28968 ~= 0.001707,
# rank 2 -> 0.003414. p_(1)=0.001 <= 0.001707 holds; p_(2)=0.008 <= 0.003414
# fails. BY rejects rank 1 only -- same as Holm here, less powerful than BH.

HAND_P = np.array([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.3])


def test_holm_rejects_only_the_smallest_on_the_hand_worked_example():
    reject, p_adj = holm(HAND_P, alpha=0.05)
    assert reject.tolist() == [True, False, False, False, False, False, False, False, False, False]
    assert p_adj[0] == pytest.approx(0.01)  # (10-1+1)*0.001
    assert p_adj[1] == pytest.approx(0.072)  # (10-2+1)*0.008, before the cummax with p_adj[0]
    assert np.all(np.diff(np.sort(p_adj)) >= -1e-12), "adjusted p-values are monotone by rank"


def test_benjamini_hochberg_rejects_the_two_smallest_on_the_hand_worked_example():
    reject, p_adj = benjamini_hochberg(HAND_P, q=0.05)
    assert reject.tolist() == [True, True, False, False, False, False, False, False, False, False]
    assert p_adj[0] == pytest.approx(0.01)  # min(10/1*0.001, 10/2*0.008) = min(0.01, 0.04)
    assert p_adj[1] == pytest.approx(0.04)


def test_benjamini_yekutieli_is_more_conservative_and_matches_holm_here():
    reject, p_adj = benjamini_yekutieli(HAND_P, q=0.05)
    assert reject.tolist() == [True, False, False, False, False, False, False, False, False, False]
    c10 = sum(1.0 / i for i in range(1, 11))
    assert p_adj[0] == pytest.approx(c10 * 0.01)


def test_bh_is_at_least_as_powerful_as_by_in_general():
    reject_bh, _ = benjamini_hochberg(HAND_P, q=0.05)
    reject_by, _ = benjamini_yekutieli(HAND_P, q=0.05)
    assert reject_bh.sum() >= reject_by.sum()


# --- marginal p-values ---------------------------------------------------------


def test_marginal_pvalues_matches_the_stated_formula():
    rng = np.random.default_rng(0)
    T0 = rng.standard_normal((999, 3))
    t = np.array([T0[:, 0].max() + 1, np.median(T0[:, 1]), T0[:, 2].min() - 1])
    p = marginal_pvalues(t, T0)
    assert p[0] == pytest.approx(1.0 / 1000.0)  # nothing in the null draw beats it
    assert p[2] == pytest.approx(1.0)  # every draw beats it
    assert 0.3 < p[1] < 0.7  # roughly the median


def test_marginal_pvalues_rejects_a_mismatched_shape():
    with pytest.raises(ValueError):
        marginal_pvalues(np.zeros(3), np.zeros((10, 4)))


# --- romano-wolf vs holm, independent columns ----------------------------------


def test_romano_wolf_matches_holm_closely_under_independent_columns():
    rng = np.random.default_rng(1)
    m = 8
    T0 = rng.standard_normal((20_000, m))
    # Away from any decision boundary: four clearly significant, four clearly not.
    t = np.array([4.0, 3.5, 3.2, 3.0, 0.3, 0.1, -0.2, -0.1])
    p = marginal_pvalues(t, T0)
    reject_holm, _ = holm(p, alpha=0.05)
    reject_rw, _ = romano_wolf(t, T0, alpha=0.05)
    assert reject_holm.tolist() == [True, True, True, True, False, False, False, False]
    assert reject_rw.tolist() == reject_holm.tolist()


def test_romano_wolf_is_at_least_as_powerful_as_holm_under_positive_dependence():
    """
    Positive dependence (a shared factor) is what the audit's block-shuffled
    null actually has, and it is exactly the case Holm cannot exploit.
    """
    rng = np.random.default_rng(2)
    m = 6
    factor = rng.standard_normal((50_000, 1))
    T0 = 0.8 * factor + 0.6 * rng.standard_normal((50_000, m))
    t = np.array([2.6, 2.5, 2.4, 0.1, -0.1, 0.0])
    p = marginal_pvalues(t, T0)
    reject_holm, _ = holm(p, alpha=0.05)
    reject_rw, _ = romano_wolf(t, T0, alpha=0.05)
    assert reject_rw.sum() >= reject_holm.sum()
    assert np.all(reject_rw[reject_holm]), "everything Holm rejects, Romano-Wolf also rejects"


def test_romano_wolf_adjusted_pvalues_are_monotone_in_rejection_order():
    rng = np.random.default_rng(3)
    m = 10
    T0 = rng.standard_normal((5_000, m))
    t = np.sort(rng.standard_normal(m))[::-1] + 2.0  # descending, all somewhat significant
    # standardise=False: with it on, per-column standardisation can reorder t
    # relative to its raw values, which is not what this test is about.
    _, p_adj = romano_wolf(t, T0, alpha=0.05, standardise=False)
    # t is sorted descending, so its own order is the rejection order.
    assert np.all(np.diff(p_adj) >= -1e-12)


# --- complete-null simulation: realised FWER / FDR within MC error ------------


def _complete_null_replications(n_reps, m, k, alpha, q, rng):
    fwer_holm = fwer_rw = fdp_bh = fdp_by = 0.0
    for _ in range(n_reps):
        t = rng.standard_normal(m)
        T0 = rng.standard_normal((k, m))
        p = marginal_pvalues(t, T0)
        reject_holm, _ = holm(p, alpha)
        reject_rw, _ = romano_wolf(t, T0, alpha)
        reject_bh, _ = benjamini_hochberg(p, q)
        reject_by, _ = benjamini_yekutieli(p, q)
        fwer_holm += reject_holm.any()
        fwer_rw += reject_rw.any()
        # under the complete null every hypothesis is truly null, so any
        # rejection is a false discovery and FDP is 1 whenever there is one.
        fdp_bh += reject_bh.any()
        fdp_by += reject_by.any()
    return fwer_holm / n_reps, fwer_rw / n_reps, fdp_bh / n_reps, fdp_by / n_reps


@pytest.mark.slow
def test_realised_error_rates_stay_within_mc_error_of_their_nominal_level():
    rng = np.random.default_rng(4)
    alpha, q = 0.05, 0.05
    n_reps, m, k = 1500, 6, 300
    fwer_holm, fwer_rw, fdr_bh, fdr_by = _complete_null_replications(n_reps, m, k, alpha, q, rng)
    # SE of a ~5% proportion at n=1500 is ~0.0056; allow a generous margin.
    margin = 0.03
    assert fwer_holm <= alpha + margin
    assert fwer_rw <= alpha + margin
    assert fdr_bh <= q + margin
    assert fdr_by <= q + margin


def test_everything_is_deterministic_under_a_seed():
    rng = np.random.default_rng(5)
    t = rng.standard_normal(7)
    T0 = rng.standard_normal((400, 7))
    p = marginal_pvalues(t, T0)
    for fn, args in (
        (holm, (p, 0.05)),
        (benjamini_hochberg, (p, 0.05)),
        (benjamini_yekutieli, (p, 0.05)),
        (romano_wolf, (t, T0, 0.05)),
    ):
        r1, a1 = fn(*args)
        r2, a2 = fn(*args)
        assert r1.tolist() == r2.tolist()
        np.testing.assert_array_equal(a1, a2)


def test_romano_shaikh_wolf_fdr_is_not_implemented_and_says_why():
    with pytest.raises(NotImplementedError, match="not implemented"):
        romano_shaikh_wolf_fdr(np.zeros(3), np.zeros((10, 3)), q=0.10)


# --- HANDOFF task 40: standardised Romano-Wolf, decisions/0041 --------------


def _reference_romano_wolf_unstandardised(t, T0, alpha):
    """A direct re-implementation of the pre-task-40 stepdown (no standardising),
    as an independent oracle for `romano_wolf(..., standardise=False)`."""
    m = t.shape[0]
    k = T0.shape[0]
    p_adj = np.empty(m)
    remaining = np.arange(m)
    floor = 0.0
    while remaining.size:
        M = T0[:, remaining].max(axis=1)
        p_active = (1.0 + (M[:, None] >= t[remaining][None, :]).sum(axis=0)) / (k + 1.0)
        reject_now = p_active <= alpha
        if not reject_now.any():
            p_adj[remaining] = np.maximum(floor, p_active)
            break
        p_adj[remaining[reject_now]] = np.maximum(floor, p_active[reject_now])
        floor = max(floor, float(p_active[reject_now].max()))
        remaining = remaining[~reject_now]
    return p_adj <= alpha, p_adj


def test_standardise_false_reproduces_the_pre_task_40_stepdown_exactly():
    rng = np.random.default_rng(20)
    m = 9
    T0 = rng.standard_normal((2000, m)) * rng.uniform(0.5, 2.0, m)
    t = rng.standard_normal(m) * 2.0
    reject_r, p_adj_r = _reference_romano_wolf_unstandardised(t, T0, 0.05)
    reject, p_adj = romano_wolf(t, T0, 0.05, standardise=False)
    assert reject.tolist() == reject_r.tolist()
    np.testing.assert_array_equal(p_adj, p_adj_r)


def test_marginal_pvalues_are_invariant_to_standardising():
    rng = np.random.default_rng(21)
    m = 6
    T0 = rng.standard_normal((500, m)) * rng.uniform(0.5, 3.0, m) + rng.uniform(-1, 1, m)
    t = rng.standard_normal(m) * 2.0
    from signal_lab.stats.multiple_testing import _standardise_columns

    t_s, T0_s = _standardise_columns(t, T0)
    np.testing.assert_allclose(marginal_pvalues(t, T0), marginal_pvalues(t_s, T0_s), atol=1e-12)


def test_standardising_prevents_a_wide_null_column_from_costing_the_others_power():
    """
    decisions/0041's implementation note: an unstandardised max-T stepdown lets
    a hypothesis with a wider null dominate the shared maximum. Column 0's null
    is 3x as wide as the rest; columns 1-4 carry a real, moderate effect.
    """
    rng = np.random.default_rng(22)
    m = 5
    k = 3000
    T0 = rng.standard_normal((k, m))
    T0[:, 0] *= 3.0
    t = np.array([0.2, 2.6, 2.5, 2.4, 2.3])  # column 0 near-null; 1-4 a real effect
    reject_std, _ = romano_wolf(t, T0, alpha=0.05, standardise=True)
    reject_raw, _ = romano_wolf(t, T0, alpha=0.05, standardise=False)
    assert reject_std[1:].sum() >= reject_raw[1:].sum()
    assert reject_std[1:].all(), "standardised should reject all four real effects"
    assert not reject_raw[1:].all(), "the wide null column should cost the raw version power"


def test_a_zero_or_nonfinite_null_column_sd_is_refused():
    rng = np.random.default_rng(23)
    T0 = rng.standard_normal((10, 3))
    T0[:, 0] = 5.0  # constant column: sd = 0
    with pytest.raises(ValueError, match="zero or non-finite"):
        romano_wolf(np.array([1.0, 1.0, 1.0]), T0, alpha=0.05, standardise=True)
