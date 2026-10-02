"""
Loading estimators, decisions/0046 section 4. One configuration each, fixed
before any result existed: nothing here is tuned and nothing here is a knob.

    rolling_ols                 the incumbent           156 weeks, classical cov
    huber_m                     H-2026-0013             c = 1.345, MAD scale, sandwich cov
    theil_goldberger_peer_prior H-2026-0014             OLS mixed with a reporting-class prior
    hmm2_regime_conditional     H-2026-0015             2-state Gaussian HMM, per-regime WLS
    kalman_dlm_discount         H-2026-0016             random-walk loadings, discount factor

Model: `r_t = a + b' f_t + e_t`, weekly, all factors at once. Every estimator
exposes ONE interface, `path(y, X, ctx) -> LoadingPath`: the loading vector, its
covariance and its residual variance at every week t, each computed from rows
`<= t` and nothing else. `last_index[t]` records the last row it used and the run
raises if that is ever after t; the tests change every observation after t and
require the answer at t unchanged, bit for bit.

Data sufficiency (the same for all five, so they are scored on the same cells):
an estimate exists at t only when the 156-week window ending at t holds at least
`MIN_OBS` weeks in which the instrument and all six factors are observed. That is
a rule about data, not a setting of any method.

No new dependency: the HMM is a short numpy EM (hmmlearn is not installed) and
the robust fit is a short IRLS, checked against statsmodels' RLM in the tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from scipy.special import gammaln

WINDOW = 156  # weeks; matches audit.covariance.window_periods (decisions/0046 section 4)
MIN_OBS = 104  # two thirds of the window: the data-sufficiency rule above
HUBER_C = 1.345
MAD_TO_SD = 1.4826
KALMAN_DISCOUNTS = (0.97, 0.98, 0.99, 0.995, 0.999)
HMM_RESTARTS = 10
HMM_SEED = 20261001
HMM_MAX_ITER = 100
HMM_TOL = 1e-6
MIN_PEERS = 3  # fewer peers than this and a class has no dispersion worth using
MIN_REGIME_WEIGHT = 14.0  # effective weeks a regime needs for its own WLS (2 x (k + 1))


@dataclass
class LoadingPath:
    """Loadings at every week; rows with no estimate are NaN and `last_index == -1`."""

    beta: np.ndarray  # (n, k)
    cov: np.ndarray  # (n, k, k)
    resid_var: np.ndarray  # (n,)
    last_index: np.ndarray  # (n,) int: the last row used, -1 if none

    @classmethod
    def empty(cls, n: int, k: int) -> LoadingPath:
        return cls(
            beta=np.full((n, k), np.nan),
            cov=np.full((n, k, k), np.nan),
            resid_var=np.full(n, np.nan),
            last_index=np.full(n, -1, dtype=int),
        )

    def has(self) -> np.ndarray:
        return self.last_index >= 0


@dataclass
class RegimePath:
    """The factor-only HMM, refitted weekly. `rows[t]` are the factor rows used at t."""

    rows: dict[int, np.ndarray] = field(default_factory=dict)
    smoothed: dict[int, np.ndarray] = field(default_factory=dict)  # (len(rows), 2)
    pi_next: dict[int, np.ndarray] = field(default_factory=dict)  # (2,)
    agreement_min: dict[int, float] = field(default_factory=dict)
    agreement_median: dict[int, float] = field(default_factory=dict)


@dataclass
class Context:
    """What a candidate may need beyond the instrument itself, all causal."""

    peer_betas: np.ndarray | None = None  # (n, n_peers, k): peers' OLS loadings at t, NaN if none
    regimes: RegimePath | None = None


class Estimator(Protocol):
    name: str

    def path(self, y: np.ndarray, X: np.ndarray, ctx: Context | None = None) -> LoadingPath: ...


# --- shared pieces ------------------------------------------------------------


def _window(t: int) -> slice:
    return slice(max(0, t - WINDOW + 1), t + 1)


def valid_rows(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    return np.isfinite(y) & np.isfinite(X).all(axis=1)


def window_ok(valid: np.ndarray) -> np.ndarray:
    """True at t when the 156-week window ending at t holds at least MIN_OBS valid weeks."""
    csum = np.concatenate([[0], np.cumsum(valid.astype(int))])
    n = len(valid)
    t = np.arange(n)
    lo = np.maximum(0, t - WINDOW + 1)
    return (csum[t + 1] - csum[lo]) >= MIN_OBS


def _design(X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X])


def ols_fit(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """(loadings, their classical covariance, residual variance) of `y = a + X b`."""
    Z = _design(X)
    n, p = Z.shape
    coef, *_ = np.linalg.lstsq(Z, y, rcond=None)
    resid = y - Z @ coef
    s2 = float(resid @ resid) / max(n - p, 1)
    cov = s2 * np.linalg.pinv(Z.T @ Z)
    return coef[1:], cov[1:, 1:], s2


def _fill(out: LoadingPath, t: int, beta, cov, s2, last: int) -> None:
    out.beta[t] = beta
    out.cov[t] = cov
    out.resid_var[t] = s2
    out.last_index[t] = last


# --- the incumbent -------------------------------------------------------------


class RollingOLS:
    name = "rolling_ols"

    def path(self, y, X, ctx=None):
        n, k = X.shape
        out = LoadingPath.empty(n, k)
        valid = valid_rows(y, X)
        ok = window_ok(valid)
        for t in np.flatnonzero(ok):
            w = _window(int(t))
            m = valid[w]
            beta, cov, s2 = ols_fit(y[w][m], X[w][m])
            _fill(out, int(t), beta, cov, s2, int(t))
        return out


# --- H-2026-0013: Huber M-estimator ----------------------------------------------


def huber_fit(
    y: np.ndarray, X: np.ndarray, c: float = HUBER_C, max_iter: int = 200
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Huber M-estimate of `y = a + X b` by IRLS: MAD scale (1.4826 x the median
    absolute deviation of the residuals, re-estimated each pass), tuning constant
    `c`, and the sandwich covariance `s^2 A^-1 B A^-1 / n` with
    `A = mean(psi' z z')`, `B = mean(psi^2 z z')`. Returns the loadings, their
    covariance and the residual variance RSS / (n - p), so that every estimator's
    `resid_var` means the same thing.
    """
    Z = _design(X)
    n, p = Z.shape
    beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
    scale = 1.0
    for _ in range(max_iter):
        r = y - Z @ beta
        scale = MAD_TO_SD * float(np.median(np.abs(r - np.median(r))))
        if scale < 1e-14:
            break
        u = r / scale
        w = np.minimum(1.0, c / np.maximum(np.abs(u), 1e-300))
        Zw = Z * w[:, None]
        new = np.linalg.solve(Zw.T @ Z + 1e-14 * np.eye(p), Zw.T @ y)
        done = float(np.max(np.abs(new - beta))) < 1e-10 * (1.0 + float(np.max(np.abs(beta))))
        beta = new
        if done:
            break
    r = y - Z @ beta
    u = r / max(scale, 1e-14)
    psi = np.clip(u, -c, c)
    dpsi = (np.abs(u) <= c).astype(float)
    A = (Z * dpsi[:, None]).T @ Z / n
    B = (Z * (psi**2)[:, None]).T @ Z / n
    Ainv = np.linalg.pinv(A)
    cov = (scale**2) * Ainv @ B @ Ainv / n
    s2 = float(r @ r) / max(n - p, 1)
    return beta[1:], cov[1:, 1:], s2


class HuberM:
    name = "huber_m"

    def path(self, y, X, ctx=None):
        n, k = X.shape
        out = LoadingPath.empty(n, k)
        valid = valid_rows(y, X)
        for t in np.flatnonzero(window_ok(valid)):
            w = _window(int(t))
            m = valid[w]
            beta, cov, s2 = huber_fit(y[w][m], X[w][m])
            _fill(out, int(t), beta, cov, s2, int(t))
        return out


def peer_beta_array(ols_paths: list[LoadingPath], i: int, members: list[int]) -> np.ndarray:
    """(n, n_peers, k): the OLS loadings, week by week, of the other members of i's class."""
    peers = [j for j in members if j != i]
    n, k = ols_paths[i].beta.shape
    if not peers:
        return np.full((n, 0, k), np.nan)
    return np.stack([ols_paths[j].beta for j in peers], axis=1)


# --- H-2026-0014: Theil-Goldberger shrinkage toward the reporting class ----------------


def peer_prior(peer_betas: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Mean and (diagonal) dispersion of the other members' loadings, or None when
    fewer than `MIN_PEERS` peers have an estimate. The diagonal is the class's
    per-factor cross-sectional variance; a full matrix from a handful of peers is
    rank-deficient, and decisions/0046 asks only for "the dispersion".
    """
    peers = peer_betas[np.isfinite(peer_betas).all(axis=1)]
    if len(peers) < MIN_PEERS:
        return None
    return peers.mean(axis=0), np.diag(np.maximum(peers.var(axis=0, ddof=1), 1e-12))


def theil_goldberger(
    beta: np.ndarray, cov: np.ndarray, prior_mean: np.ndarray, prior_cov: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """OLS mixed with a stochastic prior: precision-weighted mean and combined covariance."""
    P_ols = np.linalg.pinv(cov)
    P_pri = np.linalg.inv(prior_cov)
    post = np.linalg.inv(P_ols + P_pri)
    return post @ (P_ols @ beta + P_pri @ prior_mean), post


class TheilGoldbergerPeerPrior:
    """
    The prior at t is built from the OTHER members of the instrument's
    reporting class (`ctx.peer_betas` already excludes the instrument itself).
    A class with fewer than `MIN_PEERS` other members with an estimate at t has no
    prior, and the estimate is the OLS one there.
    """

    name = "theil_goldberger_peer_prior"

    def path(self, y, X, ctx=None):
        n, k = X.shape
        out = LoadingPath.empty(n, k)
        valid = valid_rows(y, X)
        for t in np.flatnonzero(window_ok(valid)):
            t = int(t)
            w = _window(t)
            m = valid[w]
            beta, cov, s2 = ols_fit(y[w][m], X[w][m])
            prior = None
            if ctx is not None and ctx.peer_betas is not None:
                prior = peer_prior(ctx.peer_betas[t])
            if prior is not None:
                beta, cov = theil_goldberger(beta, cov, *prior)
            _fill(out, t, beta, cov, s2, t)
        return out


# --- H-2026-0015: two-state Gaussian HMM on the factors ---------------------------------


def _log_emission(X: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """(R, 2, n) log N(x | mu, Sigma) for R restarts x 2 states."""
    d = X.shape[1]
    inv = np.linalg.inv(sigma)
    _, logdet = np.linalg.slogdet(sigma)
    diff = X[None, None, :, :] - mu[:, :, None, :]
    quad = np.einsum("rsnd,rsde,rsne->rsn", diff, inv, diff)
    return -0.5 * (quad + logdet[:, :, None] + d * np.log(2 * np.pi))


def _forward_backward(logB, pi0, A):
    """Scaled forward-backward for R batched 2-state chains. logB is (R, 2, n)."""
    R, S, n = logB.shape
    shift = logB.max(axis=1, keepdims=True)
    B = np.exp(logB - shift)
    alpha = np.empty((n, R, S))
    c = np.empty((n, R))
    a = pi0 * B[:, :, 0]
    c[0] = a.sum(axis=1)
    alpha[0] = a / c[0][:, None]
    for tau in range(1, n):
        a = np.einsum("rs,rsj->rj", alpha[tau - 1], A) * B[:, :, tau]
        c[tau] = a.sum(axis=1)
        alpha[tau] = a / c[tau][:, None]
    beta = np.empty((n, R, S))
    beta[-1] = 1.0
    for tau in range(n - 2, -1, -1):
        nxt = B[:, :, tau + 1] * beta[tau + 1]
        beta[tau] = np.einsum("rsj,rj->rs", A, nxt) / c[tau + 1][:, None]
    loglik = (np.log(c) + shift[:, 0, :].T).sum(axis=0)
    gamma = alpha * beta
    gamma /= gamma.sum(axis=2, keepdims=True)
    # Expected transition counts: sum over tau of alpha_tau(i) A(i,j) B_{tau+1}(j)
    # beta_{tau+1}(j) / c_{tau+1}, which is already a probability for each tau.
    nxt = B[:, :, 1:].transpose(2, 0, 1) * beta[1:] / c[1:][:, :, None]  # (n-1, R, 2)
    xi = np.einsum("trs,rsj,trj->rsj", alpha[:-1], A, nxt)
    return gamma, alpha, xi, loglik


def fit_hmm2(X: np.ndarray, seed: int = HMM_SEED, restarts: int = HMM_RESTARTS):
    """
    Two-state Gaussian HMM (full covariances) by EM from `restarts` seeded random
    starts, run as one batch. Returns the best restart's `(gamma, pi_next, params)`
    and the label-aligned agreement of every restart's most likely states with
    the best one's. State 0 is the calmer state (the smaller covariance trace).
    """
    n, d = X.shape
    rng = np.random.default_rng(seed)
    scale = X.std(axis=0, ddof=1)
    scale[scale == 0] = 1.0
    ridge = 1e-6 * np.diag(scale**2)
    score = ((X - X.mean(axis=0)) / scale) ** 2
    score = score.sum(axis=1)
    R = restarts
    # Each restart splits the weeks into calm and turbulent at a random quantile of
    # a noisy turbulence score; the noise is what makes the restarts differ.
    q = rng.uniform(0.5, 0.95, size=R)
    noisy = score[:, None] + rng.normal(0, 0.5 * score.std(), size=(n, R))
    thresh = np.array([np.quantile(noisy[:, r], q[r]) for r in range(R)])
    resp1 = np.where(noisy > thresh[None, :], 0.95, 0.05)
    resp = np.stack([1 - resp1, resp1], axis=2)  # (n, R, 2)

    def m_step(resp):
        w = resp.transpose(1, 2, 0)  # (R, 2, n)
        nk = w.sum(axis=2)
        mu = np.einsum("rsn,nd->rsd", w, X) / nk[:, :, None]
        diff = X[None, None] - mu[:, :, None, :]
        sig = np.einsum("rsn,rsnd,rsne->rsde", w, diff, diff) / nk[:, :, None, None] + ridge
        pi0 = resp[0]
        return mu, sig, pi0

    mu, sig, pi0 = m_step(resp)
    A = np.full((R, 2, 2), 0.5)
    prev = np.full(R, -np.inf)
    for _ in range(HMM_MAX_ITER):
        logB = _log_emission(X, mu, sig)
        gamma, _, xi, loglik = _forward_backward(logB, pi0, A)
        A = xi / xi.sum(axis=2, keepdims=True)
        mu, sig, _ = m_step(gamma)
        pi0 = gamma[0]
        if np.all(np.abs(loglik - prev) < HMM_TOL * n):
            break
        prev = loglik
    logB = _log_emission(X, mu, sig)
    gamma, alpha, _, loglik = _forward_backward(logB, pi0, A)
    # Order the states calm -> turbulent in every restart.
    order = np.argsort(np.trace(sig, axis1=2, axis2=3), axis=1)  # (R, 2)
    gamma = np.stack([gamma[:, r, order[r]] for r in range(R)], axis=1)
    A = np.stack([A[r][np.ix_(order[r], order[r])] for r in range(R)])
    alpha = np.stack([alpha[:, r, order[r]] for r in range(R)], axis=1)
    best = int(np.argmax(loglik))
    labels = gamma.argmax(axis=2)  # (n, R)
    agree = np.array([(labels[:, r] == labels[:, best]).mean() for r in range(R)])
    agree = np.delete(agree, best)
    filt_last = alpha[-1, best]
    pi_next = filt_last @ A[best]
    return gamma[:, best], pi_next, float(agree.min()), float(np.median(agree))


def regime_path(X: np.ndarray, first_fit_rows: int = WINDOW, start: int = 0) -> RegimePath:
    """
    The HMM refitted every week on the factor rows observed up to t (an expanding
    window), with the fixed seed. Instrument-independent, so computed once. `start`
    skips the fits before that week (a fit at t never reads past t, so skipping
    earlier ones changes none of the later ones).
    """
    n = len(X)
    ok = np.isfinite(X).all(axis=1)
    out = RegimePath()
    for t in range(start, n):
        rows = np.flatnonzero(ok[: t + 1])
        if len(rows) < first_fit_rows or not ok[t]:
            continue
        gamma, pi_next, a_min, a_med = fit_hmm2(X[rows])
        out.rows[t], out.smoothed[t], out.pi_next[t] = rows, gamma, pi_next
        out.agreement_min[t], out.agreement_median[t] = a_min, a_med
    return out


def _wls(y, X, w):
    Z = _design(X)
    Zw = Z * w[:, None]
    G = Z.T @ Zw
    coef = np.linalg.solve(G + 1e-12 * np.eye(Z.shape[1]), Zw.T @ y)
    resid = y - Z @ coef
    s2 = float(w @ (resid**2)) / max(float(w.sum()), 1e-12)
    cov = s2 * np.linalg.pinv(G)
    return coef[1:], cov[1:, 1:], s2


class HMM2RegimeConditional:
    """
    Per-regime weighted least squares on the expanding window, weighted by the
    smoothed regime probabilities (smoothed over data up to t only); the
    prediction mixes the two regimes' loadings by the state probability forecast
    for t + 1. A regime with fewer than `MIN_REGIME_WEIGHT` effective weeks has
    no loading of its own and uses the unweighted one. The mixture covariance
    treats the regimes as independent: `sum(pi_s^2 V_s)`.
    """

    name = "hmm2_regime_conditional"

    def path(self, y, X, ctx=None):
        n, k = X.shape
        out = LoadingPath.empty(n, k)
        if ctx is None or ctx.regimes is None:
            raise ValueError("hmm2_regime_conditional needs ctx.regimes (regime_path(X))")
        valid = valid_rows(y, X)
        ok = window_ok(valid)
        for t in np.flatnonzero(ok):
            t = int(t)
            if t not in ctx.regimes.rows:
                continue
            rows = ctx.regimes.rows[t]
            gamma = ctx.regimes.smoothed[t]
            keep = valid[rows]
            if keep.sum() < MIN_OBS:
                continue
            ys, Xs, gs = y[rows][keep], X[rows][keep], gamma[keep]
            pi = ctx.regimes.pi_next[t]
            beta = np.zeros(k)
            cov = np.zeros((k, k))
            s2 = 0.0
            for s in range(2):
                w = gs[:, s] if gs[:, s].sum() >= MIN_REGIME_WEIGHT else np.ones(len(ys))
                b_s, v_s, s2_s = _wls(ys, Xs, w)
                beta += pi[s] * b_s
                cov += pi[s] ** 2 * v_s
                s2 += pi[s] * s2_s
            _fill(out, t, beta, cov, s2, t)
        return out


# --- H-2026-0016: random-walk loadings with a discount factor -----------------------------


def _kalman_filter(y, X, delta, n0=1.0, s0=1e-4, c0=1e6):
    """
    West-Harrison dynamic linear model with variance learning. State = (a, b),
    random walk, evolution covariance by discounting (R = C / delta). Returns the
    filtered state mean, scaled covariance, observation variance and the
    cumulative one-step Student-t predictive log likelihood after each week.
    """
    n, k = X.shape
    p = k + 1
    m = np.zeros(p)
    C = np.eye(p) * c0
    nu, S = n0, s0
    M = np.empty((n, p))
    Cs = np.empty((n, p, p))
    Ss = np.empty(n)
    ll = np.zeros(n)
    total = 0.0
    for t in range(n):
        R = C / delta
        z = np.concatenate([[1.0], X[t]])
        if np.isfinite(y[t]) and np.isfinite(z).all():
            Rz = R @ z
            Q = 1.0 + float(z @ Rz)
            e = float(y[t]) - float(z @ m)
            var = S * Q
            total += (
                gammaln((nu + 1) / 2)
                - gammaln(nu / 2)
                - 0.5 * np.log(nu * np.pi * var)
                - (nu + 1) / 2 * np.log1p(e * e / (nu * var))
            )
            A = Rz / Q
            nu_new = nu + 1.0
            S_new = S * (nu + e * e / var) / nu_new
            m = m + A * e
            C = (S / S_new) * (R - np.outer(A, A) * Q)
            C = 0.5 * (C + C.T)
            nu, S = nu_new, S_new
        else:
            C = R
        M[t], Cs[t], Ss[t], ll[t] = m, C, S, total
    return M, Cs, Ss, ll


class KalmanDLMDiscount:
    """
    The discount factor is chosen at each t, from the grid, by the cumulative
    one-step predictive likelihood on data up to t. The filter is recursive, so
    one pass per grid value gives every t's answer from data up to t only.
    """

    name = "kalman_dlm_discount"

    def path(self, y, X, ctx=None):
        n, k = X.shape
        out = LoadingPath.empty(n, k)
        valid = valid_rows(y, X)
        ok = window_ok(valid)
        runs = [_kalman_filter(y, X, d) for d in KALMAN_DISCOUNTS]
        LL = np.stack([r[3] for r in runs])  # (grid, n)
        pick = LL.argmax(axis=0)
        for t in np.flatnonzero(ok):
            t = int(t)
            M, Cs, Ss, _ = runs[int(pick[t])]
            _fill(out, t, M[t][1:], Ss[t] * Cs[t][1:, 1:], Ss[t], t)
        return out


ESTIMATORS = {
    cls.name: cls
    for cls in (
        RollingOLS,
        HuberM,
        TheilGoldbergerPeerPrior,
        HMM2RegimeConditional,
        KalmanDLMDiscount,
    )
}
INCUMBENT = RollingOLS.name
CANDIDATES = (
    HuberM.name,
    TheilGoldbergerPeerPrior.name,
    HMM2RegimeConditional.name,
    KalmanDLMDiscount.name,
)
