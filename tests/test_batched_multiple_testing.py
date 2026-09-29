"""
The batched (vectorised) multiple-testing procedures `scripts/fdr_vs_fwer.py`
uses, checked row by row against the single-replication reference in
`signal_lab.stats.multiple_testing` (HANDOFF task 34).
"""

from __future__ import annotations

import numpy as np

from signal_lab.stats._batched import (
    batched_benjamini_hochberg,
    batched_benjamini_yekutieli,
    batched_holm,
    batched_marginal_pvalues,
    batched_romano_wolf,
    batched_romano_wolf_gfwer,
)
from signal_lab.stats.multiple_testing import (
    benjamini_hochberg,
    benjamini_yekutieli,
    holm,
    marginal_pvalues,
    romano_wolf,
    romano_wolf_gfwer,
)


def _random_batch(rng, n, m, k):
    t = rng.standard_normal((n, m)) * 1.5
    factor = rng.standard_normal((n, k, 1))
    T0 = 0.5 * factor + 0.7 * rng.standard_normal((n, k, m))
    return t, T0


def test_batched_marginal_pvalues_matches_row_by_row():
    rng = np.random.default_rng(10)
    t, T0 = _random_batch(rng, n=40, m=9, k=200)
    batched = batched_marginal_pvalues(t, T0)
    for i in range(t.shape[0]):
        np.testing.assert_allclose(batched[i], marginal_pvalues(t[i], T0[i]))


def test_batched_holm_matches_row_by_row():
    rng = np.random.default_rng(11)
    p = rng.uniform(0, 1, size=(60, 12))
    reject_b, p_adj_b = batched_holm(p, alpha=0.05)
    for i in range(p.shape[0]):
        reject_i, p_adj_i = holm(p[i], alpha=0.05)
        assert reject_b[i].tolist() == reject_i.tolist()
        np.testing.assert_allclose(p_adj_b[i], p_adj_i)


def test_batched_benjamini_hochberg_and_yekutieli_match_row_by_row():
    rng = np.random.default_rng(12)
    p = rng.uniform(0, 1, size=(60, 12))
    for batched_fn, ref_fn, q in (
        (batched_benjamini_hochberg, benjamini_hochberg, 0.05),
        (batched_benjamini_yekutieli, benjamini_yekutieli, 0.10),
    ):
        reject_b, p_adj_b = batched_fn(p, q)
        for i in range(p.shape[0]):
            reject_i, p_adj_i = ref_fn(p[i], q)
            assert reject_b[i].tolist() == reject_i.tolist()
            np.testing.assert_allclose(p_adj_b[i], p_adj_i)


def test_batched_romano_wolf_matches_row_by_row_including_dependence():
    rng = np.random.default_rng(13)
    t, T0 = _random_batch(rng, n=50, m=10, k=300)
    reject_b, p_adj_b = batched_romano_wolf(t, T0, alpha=0.05)
    for i in range(t.shape[0]):
        reject_i, p_adj_i = romano_wolf(t[i], T0[i], alpha=0.05)
        assert reject_b[i].tolist() == reject_i.tolist(), f"row {i} rejection set differs"
        np.testing.assert_allclose(p_adj_b[i], p_adj_i, err_msg=f"row {i}")


def test_batched_romano_wolf_handles_rows_that_finish_at_different_rounds():
    """
    Some rows reject everything in round 1 (large, well-separated t); others
    reject nothing ever. Mixed in one batch, to exercise the per-row stopping.
    """
    rng = np.random.default_rng(14)
    m, k = 6, 500
    t = np.vstack(
        [
            np.full(m, 5.0),  # rejects immediately, every round
            np.full(m, -5.0),  # never rejects
            rng.standard_normal(m),  # ordinary case
        ]
    )
    T0 = rng.standard_normal((3, k, m))
    reject_b, p_adj_b = batched_romano_wolf(t, T0, alpha=0.05)
    assert reject_b[0].all()
    assert not reject_b[1].any()
    for i in range(3):
        reject_i, p_adj_i = romano_wolf(t[i], T0[i], alpha=0.05)
        assert reject_b[i].tolist() == reject_i.tolist()
        np.testing.assert_allclose(p_adj_b[i], p_adj_i)


# --- HANDOFF task 40: standardised Romano-Wolf, both settings ---------------


def test_batched_standardise_columns_matches_row_by_row():
    from signal_lab.stats._batched import batched_standardise_columns
    from signal_lab.stats.multiple_testing import _standardise_columns

    rng = np.random.default_rng(24)
    t, T0 = _random_batch(rng, n=20, m=7, k=200)
    t_s, T0_s = batched_standardise_columns(t, T0)
    for i in range(t.shape[0]):
        t_i, T0_i = _standardise_columns(t[i], T0[i])
        np.testing.assert_allclose(t_s[i], t_i)
        np.testing.assert_allclose(T0_s[i], T0_i)


def test_batched_romano_wolf_matches_row_by_row_standardise_false():
    rng = np.random.default_rng(25)
    t, T0 = _random_batch(rng, n=30, m=8, k=250)
    reject_b, p_adj_b = batched_romano_wolf(t, T0, alpha=0.05, standardise=False)
    for i in range(t.shape[0]):
        reject_i, p_adj_i = romano_wolf(t[i], T0[i], alpha=0.05, standardise=False)
        assert reject_b[i].tolist() == reject_i.tolist(), f"row {i} rejection set differs"
        np.testing.assert_allclose(p_adj_b[i], p_adj_i, err_msg=f"row {i}")


# --- HANDOFF task 40: the batched generalized-FWER stepdown -----------------


def test_batched_romano_wolf_gfwer_matches_row_by_row():
    rng = np.random.default_rng(26)
    t, T0 = _random_batch(rng, n=25, m=8, k=200)
    for standardise in (False, True):
        reject_b, p_adj_b = batched_romano_wolf_gfwer(
            t, T0, alpha=0.05, g=2, standardise=standardise
        )
        for i in range(t.shape[0]):
            reject_i, p_adj_i = romano_wolf_gfwer(t[i], T0[i], 0.05, g=2, standardise=standardise)
            assert reject_b[i].tolist() == reject_i.tolist(), f"row {i}, standardise={standardise}"
            np.testing.assert_allclose(p_adj_b[i], p_adj_i, err_msg=f"row {i}")
