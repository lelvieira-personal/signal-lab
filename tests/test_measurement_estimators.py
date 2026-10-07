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
    MeanRevertingDLMOwnMean,
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
        "mean_reverting_dlm_own_mean": MeanRevertingDLMOwnMean().path(y, X, ctx),
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


# --- H-2026-0017: mean-reverting loadings around the instrument's own mean ----------------------


def _mr_world(seed, n=520, noise=0.01, dev=0.15, half_life=26):
    """Loadings = TRUTH + a stationary AR(1) deviation; returns (X, y, B) with B the planted path."""
    rng = np.random.default_rng(seed)
    X = _factors(n, seed=seed)
    phi = 0.5 ** (1 / half_life)
    d, B = np.zeros(K), np.empty((n, K))
    for t in range(n):
        d = phi * d + rng.normal(size=K) * dev * np.sqrt(1 - phi**2)
        B[t] = TRUTH + d
    return X, np.einsum("tk,tk->t", X, B) + rng.normal(size=n) * noise, B


def _err_vs_next_week(path, B, ts):
    """What a stored value at t is judged on: the planted loading of week t+1."""
    return float(np.mean([np.abs(path.beta[t] - B[t + 1]).mean() for t in ts]))


def test_mean_reverting_recovers_constant_loadings():
    X = _factors(300, seed=21)
    y = X @ TRUTH + np.random.default_rng(21).normal(size=300) * 0.003
    p = MeanRevertingDLMOwnMean().path(y, X)
    assert p.has()[-1] and not p.has()[: E.MIN_OBS - 2].any()
    assert np.abs(p.beta[-1] - TRUTH).max() < 0.15


def test_mean_reverting_beats_ols_and_kalman_on_average_under_planted_mean_reversion():
    """
    On average over twelve planted histories, not draw by draw: at these settings it beat
    rolling OLS in 9 of 12 and the Kalman candidate in 7 of 12, so a single draw is close
    to a coin flip against Kalman and the claim only holds in the mean.
    """
    ts = range(250, 519)
    errs = {"mr": [], "ols": [], "kalman": []}
    for seed in range(12):
        X, y, B = _mr_world(seed)
        errs["mr"].append(_err_vs_next_week(MeanRevertingDLMOwnMean().path(y, X), B, ts))
        errs["ols"].append(_err_vs_next_week(RollingOLS().path(y, X), B, ts))
        errs["kalman"].append(_err_vs_next_week(KalmanDLMDiscount().path(y, X), B, ts))
    assert np.mean(errs["mr"]) < np.mean(errs["ols"])
    assert np.mean(errs["mr"]) < np.mean(errs["kalman"])


def test_mean_reverting_converges_after_a_permanent_level_shift(record_property):
    """Reported, no threshold: how many weeks the stored loading takes to get most of the way."""
    rng = np.random.default_rng(31)
    n, shift_at = 700, 400
    X = _factors(n, seed=31)
    B = np.tile(TRUTH, (n, 1))
    jump = np.array([0.6, 0.0, 0.0, 0.0, 0.0, 0.0])
    B[shift_at:] += jump
    y = np.einsum("tk,tk->t", X, B) + rng.normal(size=n) * 0.005
    p = MeanRevertingDLMOwnMean().path(y, X)
    gap = np.abs(p.beta[:, 0] - B[:, 0])
    assert gap[shift_at - 5] < 0.1  # settled on the old level before the shift
    assert gap[-1] < 0.5 * abs(jump[0])  # and it does converge to the new one
    after = np.flatnonzero(gap[shift_at:] < 0.5 * abs(jump[0]))
    weeks = int(after[0]) if len(after) else None
    record_property("weeks_to_halve_the_gap_after_a_level_shift", weeks)
    print(f"\nweeks to halve a permanent 0.6 level shift: {weeks}")
    assert weeks is not None


def test_mean_reverting_stores_the_forecast_not_the_filtered_loading():
    X, y, B = _mr_world(5, n=330, dev=0.3)
    n, k = X.shape
    valid = E.valid_rows(y, X)
    ok = E.window_ok(valid)
    t0 = int(np.flatnonzero(ok)[0])
    Cs = np.full((n, k, k), np.nan)
    coefs = {}
    for t in np.flatnonzero(ok):
        w = E._window(int(t))
        coef, G, s2, nobs = E._ols_full(y[w][valid[w]], X[w][valid[w]])
        Cs[t] = G[1:, 1:]
        coefs[int(t)] = (coef, G, s2, nobs)
    coef, G, s2, nobs = coefs[t0]
    phi, q = 0.5 ** (1 / 26), 1.0

    def seed(q_):
        m = np.zeros(1 + 2 * k)
        m[: 1 + k] = coef
        C = np.zeros((1 + 2 * k, 1 + 2 * k))
        C[: 1 + k, : 1 + k] = G
        C[1 + k :, 1 + k :] = q_ * Cs[t0]
        return m, C, s2, float(nobs - (1 + k))

    fb, _, _, _, mf = E._mr_filter(y, X, Cs, ok, t0, seed, phi, q, k)
    t = n - 1
    mu, d = mf[t][1 : 1 + k], mf[t][1 + k :]
    assert np.abs(d).max() > 0.01  # a real deviation, so the two values differ
    assert np.allclose(fb[t], mu + phi * d, rtol=0, atol=1e-12)
    assert not np.allclose(fb[t], mu + d, atol=1e-6)  # the filtered loading is not what is stored


def test_mean_reverting_covariance_is_symmetric_and_psd():
    X, y, _ = _mr_world(6, n=330)
    p = MeanRevertingDLMOwnMean().path(y, X)
    for t in np.flatnonzero(p.has())[::7]:
        V = p.cov[t]
        assert np.allclose(V, V.T, rtol=1e-9, atol=1e-16)
        assert np.linalg.eigvalsh(0.5 * (V + V.T)).min() >= -1e-9 * np.abs(V).max()
        assert p.resid_var[t] > 0


def test_mean_reverting_records_which_grid_pair_it_chose():
    X, y, _ = _mr_world(7, n=330)
    p = MeanRevertingDLMOwnMean().path(y, X)
    chosen = p.extra["pair"][p.has()]
    assert ((chosen >= 0) & (chosen < len(E.MR_PAIRS))).all()
    assert (p.extra["pair"][~p.has()] == -1).all()
    assert len(E.MR_PAIRS) == 12


# --- no lookahead, bit for bit, for all five ---------------------------------------------


def test_the_five_pooled_estimators_do_not_see_past_t():
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
        for key, a in p.extra.items():  # the diagnostics are causal too
            assert np.array_equal(a[: t0 + 1], q.extra[key][: t0 + 1]), (name, key)


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


# --- HANDOFF task 48: the covariance update of the two filters ---------------------------------


def _break_series(n=260, seed=3):
    """One loading, a tenfold volatility break halfway: the variance estimate has to move."""
    X = _factors(n, seed)
    rng = np.random.default_rng(seed + 1)
    noise = rng.normal(size=n) * np.where(np.arange(n) < n // 2, 0.002, 0.02)
    return X @ TRUTH + noise, X


def test_the_coded_and_textbook_covariance_updates_differ_on_a_volatility_break():
    y, X = _break_series()
    _, C_coded, S_coded, _ = E._kalman_filter(y, X, 0.99)
    _, C_text, S_text, _ = E._kalman_filter(y, X, 0.99, conjugate=True)
    # C feeds Q and Q feeds S_new, so the two filters part on the variance estimate as well
    assert not np.allclose(C_coded[-1], C_text[-1], rtol=1e-3)
    assert not np.allclose(S_coded, S_text, rtol=1e-3)


def test_the_two_updates_agree_when_the_variance_prior_is_tight():
    # S then barely moves, so the ratio S / S_new is 1 and the recursions coincide. The ratio
    # compounds at about n / n0 times |e^2 / var - 1|: over 260 weeks with a volatility break
    # that is 1e-8 on the means and up to 2e-5 on near-zero covariance entries at n0 = 1e9
    # (the diffuse c0 = 1e6 start amplifies it), so 1e-8 throughout needs n0 = 1e12.
    y, X = _break_series()
    for n0, tol in ((1e9, 1e-4), (1e12, 1e-8)):
        coded = E._kalman_filter(y, X, 0.99, n0=n0)
        text = E._kalman_filter(y, X, 0.99, n0=n0, conjugate=True)
        for a, b in zip(coded, text, strict=True):
            np.testing.assert_allclose(a, b, atol=tol, rtol=tol)


def test_the_conjugate_keyword_reaches_both_estimators_and_defaults_off():
    y, X = _break_series(n=330)
    for cls in (KalmanDLMDiscount, MeanRevertingDLMOwnMean):
        assert cls().conjugate_update is False
        default = cls().path(y, X)
        coded = cls(conjugate_update=False).path(y, X)
        text = cls(conjugate_update=True).path(y, X)
        np.testing.assert_array_equal(default.cov, coded.cov)
        np.testing.assert_array_equal(default.beta, coded.beta)
        t = np.flatnonzero(default.has())
        assert not np.allclose(coded.cov[t[-1]], text.cov[t[-1]], rtol=1e-3), cls.name
