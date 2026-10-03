"""The orchestration of the loading-estimator test, on a small synthetic world."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.measurement import estimators as E
from signal_lab.measurement import run
from signal_lab.measurement.estimators import LoadingPath

K = 6


def _world(T=190, N=5, seed=0):
    rng = np.random.default_rng(seed)
    F = rng.normal(size=(T, K)) * 0.01
    b = rng.normal(size=(N, K))
    R = np.einsum("tk,nk->tn", F, b) + rng.normal(size=(T, N)) * 0.01
    return R, F


def test_every_estimator_runs_on_every_instrument_and_nothing_looks_ahead():
    R, F = _world()
    classes = ["A", "A", "A", "A", "B"]  # B has no peers: no prior, OLS falls through
    regimes = E.regime_path(F, start=180)
    paths = run.estimate_all(R, F, classes, regimes)
    assert set(paths) == set(run.ALL_NAMES)
    assert all(len(v) == 5 for v in paths.values())
    assert paths["hmm2_regime_conditional"][0].has()[185]
    # the class with no peers is plain OLS for the shrinkage estimator
    assert np.array_equal(
        paths["theil_goldberger_peer_prior"][4].beta, paths["rolling_ols"][4].beta, equal_nan=True
    )
    # a class with peers is not
    t = np.flatnonzero(paths["rolling_ols"][0].has())[-1]
    assert not np.allclose(
        paths["theil_goldberger_peer_prior"][0].beta[t], paths["rolling_ols"][0].beta[t]
    )


def test_pair_shares_count_scored_cells_and_sum_to_one():
    R, F = _world()
    paths = run.estimate_all(R, F, ["A"] * 5, E.regime_path(F, start=180))
    mask = np.zeros(R.shape, dtype=bool)
    mask[150:, :] = True
    out = run.pair_shares(paths, mask, "mean_reverting_dlm_own_mean")
    assert out["n_cells"] > 0
    assert sum(out["pairs"].values()) == pytest.approx(1.0)
    assert sum(out["by_half_life"].values()) == pytest.approx(1.0)
    assert sum(out["by_q"].values()) == pytest.approx(1.0)
    assert len(out["pairs"]) == len(E.MR_PAIRS)


def test_a_lookahead_in_an_estimate_is_caught():
    p = LoadingPath.empty(10, K)
    p.last_index[5] = 7
    with pytest.raises(AssertionError, match="used data from week 7"):
        run.assert_no_lookahead({"x": [p]})


def test_loadings_long_has_one_row_per_estimate_and_factor():
    R, F = _world()
    weeks = pd.date_range("2004-01-02", periods=len(R), freq="W-FRI")
    regimes = E.regime_path(F, start=185)
    paths = run.estimate_all(R, F, ["A"] * 5, regimes)
    long = run.loadings_long(paths, list("abcde"), weeks, list("123456"))
    assert list(long.columns) == ["instrument", "date", "estimator", "factor", "loading", "se"]
    n_est = sum(int(p.has().sum()) for plist in paths.values() for p in plist)
    assert len(long) == n_est * K
    assert (long["se"] >= 0).all()


def test_hmm_stability_reports_agreement_across_restarts():
    R, F = _world()
    regimes = E.regime_path(F, start=185)
    s = run.hmm_stability(regimes)
    assert s["n_fits"] == len(regimes.rows) > 0
    assert 0.0 <= s["agreement_min_over_restarts_worst_week"] <= 1.0
    assert run.hmm_stability(E.RegimePath()) == {"n_fits": 0}


def test_factor_correlations_cover_every_pair():
    _, F = _world(T=300)
    frame = pd.DataFrame(F, columns=list("abcdef"))
    out = run.factor_correlations(frame)
    assert len(out["rolling_156w_range"]) == 15
    assert out["full_sample"]["a"]["a"] == pytest.approx(1.0)


def test_the_runtime_projection_is_finite_and_scales_with_instruments():
    R, F = _world(T=190, N=5)
    proj = run.project_runtime(R, F, ["A"] * 5, n_time=2, hmm_fits=2)
    assert proj["projected_seconds"] > 0 and np.isfinite(proj["projected_seconds"])
    assert proj["instruments"] == 5
