"""
The score of decisions/0046 section 3: the statistic, the gate under a null, the uncertainty check.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.measurement import fidelity as fid
from signal_lab.measurement.estimators import LoadingPath
from signal_lab.stats.calibration import annual_bias, worst_year

K = 6
NAMES = [
    "rolling_ols",
    "huber_m",
    "theil_goldberger_peer_prior",
    "hmm2_regime_conditional",
    "kalman_dlm_discount",
    "mean_reverting_dlm_own_mean",
]
START = 110  # weeks before an estimate exists, as a window would leave it


def _world(T=320, N=4, seed=0):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2004-01-02", periods=T, freq="W-FRI")
    F = rng.normal(size=(T, K)) * 0.01
    b = rng.normal(size=(N, K))
    R = np.einsum("tk,nk->tn", F, b) + rng.normal(size=(T, N)) * 0.01
    return weeks, F, R, b


def _path(rng, b_i, T, noise, cov_scale=1.0, s2=1e-4):
    """Loadings = truth + independent noise; a covariance that says how big the noise is."""
    p = LoadingPath.empty(T, K)
    p.beta[START:] = b_i + rng.normal(size=(T - START, K)) * noise
    p.cov[START:] = np.eye(K) * (noise**2 * cov_scale)
    p.resid_var[START:] = s2
    p.last_index[START:] = np.arange(START, T)
    return p


def _paths(weeks, b, noises, seed, cov_scale=None):
    rng = np.random.default_rng(seed)
    T, N = len(weeks), len(b)
    cov_scale = cov_scale or {}
    return {
        name: [_path(rng, b[i], T, noises[name], cov_scale.get(name, 1.0)) for i in range(N)]
        for name in NAMES
    }


def _evaluate(seed, noises, cov_scale=None, T=320):
    weeks, F, R, b = _world(T=T, seed=seed)
    return fid.evaluate(R, F, _paths(weeks, b, noises, seed + 1, cov_scale), NAMES, weeks), F, weeks


def test_the_huber_loss_is_quadratic_then_linear_and_continuous():
    c = fid.HUBER_C
    assert fid.huber_loss(np.array([0.5]))[0] == pytest.approx(0.125)
    assert fid.huber_loss(np.array([c + 1.0]))[0] == pytest.approx(c * (c + 1.0) - 0.5 * c * c)
    below, above = fid.huber_loss(np.array([c - 1e-9, c + 1e-9]))
    assert below == pytest.approx(above, rel=1e-6)


def test_a_candidate_identical_to_the_incumbent_scores_exactly_zero():
    weeks, F, R, b = _world(seed=1)
    paths = _paths(weeks, b, dict.fromkeys(NAMES, 0.3), seed=2)
    paths["huber_m"] = [
        LoadingPath(p.beta.copy(), p.cov.copy(), p.resid_var.copy(), p.last_index.copy())
        for p in paths["rolling_ols"]
    ]
    ev = fid.evaluate(R, F, paths, NAMES, weeks)
    d = fid.weekly_differentials(ev)
    assert (d["huber_m"] == 0.0).all()
    assert d["huber_m"].mean() == 0.0
    assert d["kalman_dlm_discount"].abs().max() > 0  # a different path is not zero


def test_only_cells_every_estimator_has_are_scored():
    weeks, F, R, b = _world(seed=3)
    paths = _paths(weeks, b, dict.fromkeys(NAMES, 0.2), seed=4)
    paths["kalman_dlm_discount"][0].last_index[
        :200
    ] = -1  # one estimator is late for one instrument
    ev = fid.evaluate(R, F, paths, NAMES, weeks)
    assert not ev.mask[:200, 0].any()
    assert ev.mask[250, 0] and ev.mask[250, 1]
    assert np.isnan(ev.loss[:, :START, :]).all()


def test_the_block_bootstrap_is_centred_seeded_and_shared_by_candidates():
    rng = np.random.default_rng(0)
    base = rng.normal(size=(300, 1)) + 0.4
    D = np.hstack([base, base, rng.normal(size=(300, 1))])
    T0 = fid.block_bootstrap_null(D, draws=400, seed=5)
    assert T0.shape == (400, 3)
    assert abs(T0.mean()) < 0.02  # centred: the null has no advantage in it
    assert np.array_equal(T0[:, 0], T0[:, 1])  # the same resampling for every candidate
    assert np.array_equal(T0, fid.block_bootstrap_null(D, draws=400, seed=5))
    assert not np.array_equal(T0, fid.block_bootstrap_null(D, draws=400, seed=6))


def test_the_gate_reports_g_equal_one_for_five_candidates(params):
    ev, F, weeks = _evaluate(5, dict.fromkeys(NAMES, 0.3))
    out = fid.score(ev, pd.DataFrame(F, index=weeks), params, draws=200)
    assert out["gate"]["g"] == 1
    assert out["gate"]["n_tests"] == 5


def test_each_candidate_reports_its_first_and_second_half(params):
    ev, F, weeks = _evaluate(5, dict.fromkeys(NAMES, 0.3))
    out = fid.score(ev, pd.DataFrame(F, index=weeks), params, draws=100)
    for name in NAMES[1:]:
        h = out["estimators"][name]["halves"]
        assert np.isfinite(h["first_half"]) and np.isfinite(h["second_half"])
        assert pd.Timestamp(h["split_at"]) in weeks
    assert "halves" not in out["estimators"]["rolling_ols"]


# --- the gate under a null, and with a planted advantage ----------------------------------


def _rejects(seed, noises, params, cov_scale=None, draws=200, T=320):
    ev, F, weeks = _evaluate(seed, noises, cov_scale, T)
    out = fid.score(ev, pd.DataFrame(F, index=weeks), params, draws=draws)
    return out["estimators"]


@pytest.mark.slow
def test_the_gate_holds_its_level_under_a_null(params):
    """
    The null: the incumbent and every candidate are the truth plus the SAME size of
    independent noise in their loadings. No candidate is better, so a rejection is a
    false one; the stepdown at alpha = 5% should make it in about 5% of runs.

    Run at the length of the real sample: about 840 scored weeks (2004-2019), 32
    blocks of 26. At 210 scored weeks (8 blocks) the same gate rejects in 15% of null
    runs -- a short sample's block bootstrap understates the variance of a mean --
    so the property is only claimed at the length the run has.
    """
    noises = dict.fromkeys(NAMES, 0.25)
    runs = 1000
    hits = 0
    for seed in range(runs):
        est = _rejects(seed, noises, params, draws=fid.BOOTSTRAP_DRAWS, T=950)
        hits += any(v["gate_passed"] for k, v in est.items() if k != "rolling_ols")
    assert 0.03 <= hits / runs <= 0.07, hits / runs


@pytest.mark.slow
def test_a_planted_advantage_is_rejected_in_most_runs(params):
    noises = dict.fromkeys(NAMES, 0.3)
    noises["huber_m"] = 0.05  # one candidate's loadings are far closer to the truth
    wins = sum(_rejects(s, noises, params)["huber_m"]["gate_passed"] for s in range(30))
    assert wins >= 20, wins


# --- the uncertainty check -------------------------------------------------------------------


def test_an_understated_covariance_fails_the_uncertainty_check(params):
    """
    Kalman's loadings are far off (noise 1.0) but it reports the covariance of
    loadings that are not (noise 0.3): its standardised errors come out too big.
    """
    noises = dict.fromkeys(NAMES, 0.3)
    honest = _rejects(7, noises, params)
    assert all(v["bias_ok"] for v in honest.values())
    noises["kalman_dlm_discount"] = 1.0
    claimed = {"kalman_dlm_discount": (0.3 / 1.0) ** 2}
    out = _rejects(7, noises, params, cov_scale=claimed)
    assert not out["kalman_dlm_discount"]["bias_ok"]
    assert out["kalman_dlm_discount"]["verdict"] == "not_detected"
    assert out["huber_m"]["bias_ok"]
    # the same loadings with an honest covariance are fine
    assert _rejects(7, noises, params)["kalman_dlm_discount"]["bias_ok"]


def test_the_worst_year_is_read_with_the_shared_calibration_helper():
    idx = pd.to_datetime(["2005-01-07"] * 50 + ["2006-01-06"] * 50 + ["2007-01-05"] * 10)
    z = pd.Series(
        np.r_[
            np.random.default_rng(0).normal(size=50),
            2.0 * np.random.default_rng(1).normal(size=50),
            np.random.default_rng(2).normal(size=10),
        ],
        index=idx,
    )
    annual = annual_bias(z, 40)
    assert set(annual) == {2005, 2006}  # 2007 has too few readings to read
    assert worst_year(annual)[0] == 2006
    assert worst_year({}) == (None, float("nan")) or worst_year({})[0] is None


def test_mean_huber_loss_and_the_by_class_table_are_reported(params):
    ev, F, weeks = _evaluate(5, dict.fromkeys(NAMES, 0.3))
    classes = ["A", "A", "B", "B"]
    out = fid.score(ev, pd.DataFrame(F, index=weeks), params, draws=200, classes=classes)
    for name in NAMES:  # the incumbent's included, so a statistic reads as a share of it
        loss = out["estimators"][name]["mean_huber_loss"]
        assert loss == pytest.approx(float(ev.loss[NAMES.index(name)][ev.mask].mean()))
        assert loss > 0
    assert set(out["by_class"]) == {"A", "B"}
    assert out["by_class"]["A"]["n_instruments"] == 2
    # the by-class statistics are a breakdown, not a second test: nothing in the gate moved
    plain = fid.score(ev, pd.DataFrame(F, index=weeks), params, draws=200)
    assert "by_class" not in plain
    assert plain["estimators"]["huber_m"]["statistic"] == out["estimators"]["huber_m"]["statistic"]
