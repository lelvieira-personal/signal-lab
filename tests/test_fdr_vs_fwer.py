"""
The FDR-vs-FWER study script's own machinery (HANDOFF task 34): reading the
registry's axis groups, spreading true hypotheses across them, and the
equicorrelated draw. The procedures themselves are covered in
`tests/test_multiple_testing.py` and `tests/test_batched_multiple_testing.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

import fdr_vs_fwer as study  # noqa: E402


def test_reads_twelve_hypotheses_grouped_as_the_task_describes():
    hyp_ids, group_index, axis_order, by_axis = study.read_axis_groups()
    assert len(hyp_ids) == 12
    sizes = sorted((len(v) for v in by_axis.values()), reverse=True)
    assert sizes == [4, 3, 2, 1, 1, 1]
    assert axis_order[0] == "region" and len(by_axis["region"]) == 4
    assert group_index.shape == (12,)
    assert hyp_ids == sorted(hyp_ids), "sorted by hypothesis id"


def test_valid_correlations_exclude_rho_w_less_than_rho_b():
    assert (0.0, 0.2) not in study.VALID_CORRELATIONS
    assert (0.0, 0.2) in study.SKIPPED_CORRELATIONS
    assert all(rw >= rb for rw, rb in study.VALID_CORRELATIONS)


def test_spread_true_covers_every_axis_before_doubling_up():
    _, group_index, axis_order, _ = study.read_axis_groups()
    mask = study.spread_true(6, group_index, axis_order)  # 6 axes exist
    assert mask.sum() == 6
    covered = {int(group_index[i]) for i in np.flatnonzero(mask)}
    assert covered == set(range(len(axis_order))), "one from every axis"


def test_spread_true_is_deterministic_and_monotone_in_n_true():
    _, group_index, axis_order, _ = study.read_axis_groups()
    m3 = study.spread_true(3, group_index, axis_order)
    m3_again = study.spread_true(3, group_index, axis_order)
    m6 = study.spread_true(6, group_index, axis_order)
    assert (m3 == m3_again).all()
    assert m3.sum() == 3 and m6.sum() == 6
    assert np.all(m6[m3]), "everyone true at n_true=3 is still true at n_true=6"


def test_draw_batch_reproduces_the_target_correlation_structure():
    """
    A large batch's empirical correlation should land near rho_w within an
    axis and rho_b between axes -- the equicorrelation model's whole point.
    """
    rng = np.random.default_rng(0)
    m = 6
    group_index = np.array([0, 0, 0, 1, 1, 2])  # axis sizes 3, 2, 1
    true_mask = np.zeros(m, dtype=bool)
    t, _ = study.draw_batch(
        rng,
        n_reps=200_000,
        k=1,
        m=m,
        group_index=group_index,
        rho_w=0.5,
        rho_b=0.2,
        true_mask=true_mask,
        mu=0.0,
        s=1.0,
    )
    corr = np.corrcoef(t, rowvar=False)
    assert corr[0, 1] == pytest.approx(0.5, abs=0.02)  # both in axis 0
    assert corr[0, 3] == pytest.approx(0.2, abs=0.02)  # axis 0 vs axis 1
    assert corr[3, 5] == pytest.approx(0.2, abs=0.02)  # axis 1 vs axis 2 (singleton)


def test_draw_batch_shifts_only_the_true_columns():
    rng = np.random.default_rng(1)
    m = 4
    group_index = np.zeros(m, dtype=int)
    true_mask = np.array([True, False, True, False])
    t, T0 = study.draw_batch(
        rng,
        n_reps=50_000,
        k=5,
        m=m,
        group_index=group_index,
        rho_w=0.0,
        rho_b=0.0,
        true_mask=true_mask,
        mu=3.0,
        s=1.0,
    )
    assert t[:, true_mask].mean() == pytest.approx(3.0, abs=0.03)
    assert t[:, ~true_mask].mean() == pytest.approx(0.0, abs=0.03)
    # T0 is the null: every column mean-zero regardless of true_mask.
    assert T0.mean() == pytest.approx(0.0, abs=0.03)
