"""
The loading estimators of decisions/0046, each on synthetic data with a planted truth.
"""

from __future__ import annotations

import numpy as np
import pytest

from signal_lab.measurement import estimators as E
from signal_lab.measurement.estimators import (
    Context,
    HMM2RegimeConditional,
    HuberM,
    KalmanDLMDiscount,
    RollingOLS,
    TheilGoldbergerPeerPrior,
    peer_beta_array,
    regime_path,
)

K = 6
TRUTH = np.array([1.0, -5.0, 2.0, -1.0, 0.3, 0.5])


def _factors(n, seed=0, vol=0.01):
    return np.random.default_rng(seed).normal(size=(n, K)) * vol


def _context(y_peers, X, own=0, hmm=False, hmm_start=0):
    """Peers' OLS loadings, and the regime path if asked (it is the slow part)."""
    ols = [RollingOLS().path(y, X) for y in y_peers]
    members = list(range(len(y_peers)))
    regimes = regime_path(X, start=hmm_start) if hmm else None
    return Context(peer_betas=peer_beta_array(ols, own, members), regimes=regimes)


def _all_paths(y_peers, X, own=0, hmm=False, hmm_start=0):
    ctx = _context(y_peers, X, own, hmm, hmm_start)
    y = y_peers[own]
    out = {
        "rolling_ols": RollingOLS().path(y, X, ctx),
        "huber_m": HuberM().path(y, X, ctx),
        "theil_goldberger_peer_prior": TheilGoldbergerPeerPrior().path(y, X, ctx),
        "kalman_dlm_discount": KalmanDLMDiscount().path(y, X, ctx),
    }
    if hmm:
        out["hmm2_regime_conditional"] = HMM2RegimeConditional().path(y, X, ctx)
    return out


def _peers(X, n_peers=5, noise=0.005, seed=1, dev=0.0, truth=TRUTH):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_peers):
        b = truth + rng.normal(size=K) * dev
        out.append(X @ b + rng.normal(size=len(X)) * noise)
    return out


# --- every estimator recovers constant loadings ---------------------------------------


@pytest.mark.slow
def test_constant_loadings_are_recovered_by_all_five():
    X = _factors(200)
    paths = _all_paths(_peers(X), X, hmm=True, hmm_start=190)
    for name, p in paths.items():
        err = np.abs(p.beta[-1] - TRUTH).max()
        assert err < 0.15, (name, err)
        assert p.has()[-1]


# --- each candidate beats OLS on the structure it was registered for ----------------------


def _mean_abs_err(path, truth_path, ts):
    return float(np.mean([np.abs(path.beta[t] - truth_path[t]).mean() for t in ts]))


def test_huber_beats_ols_under_planted_outliers():
    rng = np.random.default_rng(3)
    X = _factors(300, seed=3)
    y = X @ TRUTH + rng.normal(size=300) * 0.003
    hit = rng.random(300) < 0.06
    y = y + hit * rng.choice([-1, 1], 300) * 0.25  # a handful of enormous weeks
    ols, hub = RollingOLS().path(y, X), HuberM().path(y, X)
    ts = range(200, 300)
    truth = {t: TRUTH for t in ts}
    assert _mean_abs_err(hub, truth, ts) < _mean_abs_err(ols, truth, ts)


def test_shrinkage_beats_ols_under_planted_peer_structure():
    n = 220
    X = _factors(n, seed=4)
    peers = _peers(X, n_peers=12, noise=0.05, seed=4, dev=0.1)  # individuals are noisy
    ctx = _context(peers, X)
    ols, tg = RollingOLS().path(peers[0], X), TheilGoldbergerPeerPrior().path(peers[0], X, ctx)
    ts = range(170, n)
    # The class mean is the truth up to individual deviation; judge against the
    # instrument's own planted loadings by regenerating them with the same seed.
    rng = np.random.default_rng(4)
    own = TRUTH + rng.normal(size=K) * 0.1
    truth = {t: own for t in ts}
    assert _mean_abs_err(tg, truth, ts) < _mean_abs_err(ols, truth, ts)


@pytest.mark.slow
def test_the_hmm_beats_ols_after_a_planted_regime_switch():
    rng = np.random.default_rng(5)
    n = 420
    state = np.zeros(n, dtype=int)
    for t in range(1, n):  # persistent two-state chain, turbulent state is rarer
        stay = 0.97 if state[t - 1] == 0 else 0.92
        state[t] = state[t - 1] if rng.random() < stay else 1 - state[t - 1]
    X = rng.normal(size=(n, K)) * np.where(state[:, None] == 1, 0.04, 0.01)
    b_calm, b_stress = TRUTH, TRUTH * np.array([2.0, 0.2, 2.0, 3.0, -1.0, 0.0])
    y = np.einsum("tk,tk->t", X, np.where(state[:, None] == 1, b_stress, b_calm))
    y = y + rng.normal(size=n) * 0.002
    ctx = Context(regimes=regime_path(X, start=330))
    ols, hmm = RollingOLS().path(y, X), HMM2RegimeConditional().path(y, X, ctx)
    ts = [t for t in range(330, n - 1) if hmm.has()[t]]
    truth = {t: (b_stress if state[t + 1] else b_calm) for t in ts}
    assert _mean_abs_err(hmm, truth, ts) < _mean_abs_err(ols, truth, ts)


def test_kalman_beats_ols_under_planted_drift():
    rng = np.random.default_rng(6)
    n = 400
    X = _factors(n, seed=6)
    drift = np.cumsum(rng.normal(size=(n, K)) * 0.04, axis=0)
    B = TRUTH + drift
    y = np.einsum("tk,tk->t", X, B) + rng.normal(size=n) * 0.002
    ols, kal = RollingOLS().path(y, X), KalmanDLMDiscount().path(y, X)
    ts = range(200, n)
    truth = {t: B[t] for t in ts}
    assert _mean_abs_err(kal, truth, ts) < _mean_abs_err(ols, truth, ts)


# --- no lookahead, bit for bit, for all five ---------------------------------------------


def test_the_four_pooled_estimators_do_not_see_past_t():
    _no_lookahead(hmm=False, n=330, t0=220, hmm_start=0)


@pytest.mark.slow
def test_the_hmm_does_not_see_past_t():
    _no_lookahead(hmm=True, n=190, t0=175, hmm_start=170)


def _no_lookahead(hmm, n, t0, hmm_start):
    X = _factors(n, seed=7)
    peers = _peers(X, n_peers=5, noise=0.01, seed=7, dev=0.05)
    base = _all_paths(peers, X, hmm=hmm, hmm_start=hmm_start)

    rng = np.random.default_rng(99)
    X2 = X.copy()
    X2[t0 + 1 :] = rng.normal(size=(n - t0 - 1, K)) * 0.05
    peers2 = [p.copy() for p in peers]
    for p in peers2:
        p[t0 + 1 :] = rng.normal(size=n - t0 - 1) * 0.3
    changed = _all_paths(peers2, X2, hmm=hmm, hmm_start=hmm_start)

    for name, p in base.items():
        q = changed[name]
        assert p.has()[: t0 + 1].any(), name
        for field in ("beta", "cov", "resid_var", "last_index"):
            a, b = getattr(p, field)[: t0 + 1], getattr(q, field)[: t0 + 1]
            assert np.array_equal(a, b, equal_nan=True), (name, field)
        assert (p.last_index[p.has()] <= np.flatnonzero(p.has())).all(), name


@pytest.mark.slow
def test_a_returned_covariance_is_symmetric_and_psd():
    X = _factors(200, seed=8)
    paths = _all_paths(_peers(X, noise=0.02, dev=0.1, seed=8), X, hmm=True, hmm_start=185)
    for name, p in paths.items():
        for t in np.flatnonzero(p.has())[::17]:
            V = p.cov[t]
            assert np.allclose(V, V.T, rtol=1e-8, atol=1e-14), name
            assert np.linalg.eigvalsh(0.5 * (V + V.T)).min() >= -1e-9 * np.abs(V).max(), name
            assert p.resid_var[t] >= 0


# --- the robust fit is the textbook one --------------------------------------------------


def test_huber_loadings_match_statsmodels_rlm():
    import statsmodels.api as sm

    rng = np.random.default_rng(10)
    X = _factors(156, seed=10)
    y = X @ TRUTH + rng.standard_t(3, 156) * 0.004
    beta, cov, _ = E.huber_fit(y, X)
    fit = sm.RLM(y, sm.add_constant(X), M=sm.robust.norms.HuberT(t=1.345)).fit()
    assert np.allclose(beta, fit.params[1:], atol=2e-3)
    assert np.all(np.diag(cov) > 0)


# --- data sufficiency ---------------------------------------------------------------------


def test_no_estimate_without_enough_history():
    X = _factors(300, seed=11)
    y = X @ TRUTH
    y[:120] = np.nan  # the instrument starts late
    p = RollingOLS().path(y, X)
    assert not p.has()[: 120 + E.MIN_OBS - 2].any()
    assert p.has()[-1]


def test_a_class_with_too_few_peers_gets_no_prior():
    assert E.peer_prior(np.full((2, K), 0.1)) is None
    assert E.peer_prior(np.vstack([np.eye(K)[:2] * 0.1, np.full((3, K), np.nan)])) is None
