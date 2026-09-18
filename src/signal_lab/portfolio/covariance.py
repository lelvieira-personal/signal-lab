"""
Rebalance-frequency returns, a shrunk covariance, and effective breadth.

Three small pieces the solver and the ruler audit both need, kept apart from
the solver so a covariance can be inspected without solving anything.

Why weekly rather than daily. SUBSTRATE section 5.1 invariant 7 says same-day
daily correlation across regions is biased low by non-synchronous closes and is
not to be used for optimisation; the daily rule is 2-day overlapping returns,
which needs a region label per series that no table yet carries
(`decisions/0022`). Compounding returns to the rebalance frequency sidesteps the
problem instead of correcting it: a Tokyo close and a New York close inside the
same week are the same week. The cost is fewer observations, which is why the
estimator shrinks.

Two Ledoit-Wolf shrinkage estimators are implemented here rather than imported
so the dependency set does not grow for two formulas. The default target is the
CONSTANT-CORRELATION matrix (Ledoit and Wolf 2003), not the scaled identity
(2004), and the choice is not cosmetic for a benchmark-relative problem: the
identity target pulls every correlation toward zero, so a book that replicates
the benchmark almost exactly is told its tracking error is several percent,
and a 6% budget can look infeasible when the realised TE is under 1%. That was
observed on the synthetic panel before the target was changed. The constant-
correlation target keeps the average correlation and the replication.

A 156-week equal-weighted window cannot see a volatility spike, which is what
`results/audit/_probe/TE-20260917-bbg1` measured: across 2007-2009 the ex-ante
tracking error of an audit book moved 5.2% -> 6.0% -> 6.0% while its realised
active volatility moved 6.6% -> 12.2% -> 3.7%. `rescale_volatility` is the
opt-in answer to that -- fast volatilities on the slow correlation -- and it is
off unless a caller asks for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


def period_returns(daily: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Compound daily returns over each rebalance period `(previous, current]`.

    A series with no observation at all inside a window is NaN for that period;
    a series that printed on some days and not others contributes zero on the
    missing days, matching how the engine earns returns on the book. The result
    is indexed on `dates[1:]`, one row per period, which is what the engine's
    own `PortfolioPath` is indexed on.
    """
    daily = daily.sort_index()
    rows = {}
    for previous, current in zip(dates[:-1], dates[1:], strict=True):
        window = daily.loc[(daily.index > previous) & (daily.index <= current)]
        if window.empty:
            rows[current] = pd.Series(np.nan, index=daily.columns)
            continue
        seen = window.notna().any(axis=0)
        compounded = (1.0 + window.fillna(0.0)).prod(axis=0) - 1.0
        rows[current] = compounded.where(seen)
    return pd.DataFrame(rows).T.reindex(dates[1:])


@dataclass(frozen=True)
class ShrunkCovariance:
    """A covariance with the shrinkage that produced it, so the audit can report it."""

    matrix: pd.DataFrame
    shrinkage: float
    n_observations: int
    legs: dict[str, dict[str, Any]] = field(default_factory=dict)  # tracking-portfolio diagnostics

    @property
    def ids(self) -> list[str]:
        return list(self.matrix.index)

    def correlation(self) -> pd.DataFrame:
        sd = np.sqrt(np.diag(self.matrix.values))
        with np.errstate(divide="ignore", invalid="ignore"):
            corr = self.matrix.values / np.outer(sd, sd)
        corr = np.nan_to_num(corr, nan=0.0)
        np.fill_diagonal(corr, 1.0)
        return pd.DataFrame(corr, index=self.matrix.index, columns=self.matrix.columns)


def _clean(returns: pd.DataFrame, min_observations: int) -> tuple[np.ndarray, pd.Index, int, int]:
    clean = returns.dropna(axis=0, how="any")
    n, p = clean.shape
    if n < min_observations or p == 0:
        raise ValueError(f"cannot estimate a covariance from {n} observations of {p} series")
    x = clean.values - clean.values.mean(axis=0, keepdims=True)
    return x, clean.columns, n, p


def ledoit_wolf_identity(returns: pd.DataFrame, min_observations: int = 2) -> ShrunkCovariance:
    """
    Ledoit-Wolf (2004) shrinkage toward `mu * I`, closed form. Kept for
    comparison; see the module docstring for why it is not the default.
    """
    x, columns, n, p = _clean(returns, min_observations)
    sample = x.T @ x / n
    mu = float(np.trace(sample) / p)
    target = mu * np.eye(p)
    delta = float(((sample - target) ** 2).sum())
    x2 = x * x
    beta = float(((x2.T @ x2) / n - sample * sample).sum()) / n
    shrink = 0.0 if delta <= 0 else float(np.clip(beta / delta, 0.0, 1.0))
    matrix = shrink * target + (1.0 - shrink) * sample
    return ShrunkCovariance(
        matrix=pd.DataFrame(matrix, index=columns, columns=columns),
        shrinkage=shrink,
        n_observations=int(n),
    )


def ledoit_wolf(returns: pd.DataFrame, min_observations: int = 2) -> ShrunkCovariance:
    """
    Ledoit-Wolf (2003) shrinkage toward the constant-correlation target,
    closed form ("Honey, I shrunk the sample covariance matrix").

    Columns are series, rows are observations; rows with any NaN are dropped,
    which is why callers pass a panel already restricted to series live through
    the window. Shrinkage intensity is clipped to [0, 1].
    """
    x, columns, n, p = _clean(returns, min_observations)
    sample = x.T @ x / n
    var = np.diag(sample)
    sd = np.sqrt(var)
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = sample / np.outer(sd, sd)
    corr = np.nan_to_num(corr, nan=0.0)
    if p > 1:
        r_bar = float((corr.sum() - np.trace(corr)) / (p * (p - 1)))
    else:
        r_bar = 0.0
    target = r_bar * np.outer(sd, sd)
    np.fill_diagonal(target, var)

    # pi: asymptotic variance of the sample covariance entries
    x2 = x * x
    pi_mat = (x2.T @ x2) / n - sample * sample
    pi_hat = float(pi_mat.sum())

    # rho: asymptotic covariance between the sample entries and the target
    # theta_ii,ij = (1/n) sum_t (x_ti^2 - s_ii)(x_ti x_tj - s_ij) = M_ij with
    # M = ((x^2 - s_ii) * x)' x / n, the centring term vanishing.
    a = x2 - var[None, :]
    m = ((a * x).T @ x) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.outer(1.0 / sd, sd)  # sqrt(s_jj / s_ii)
    ratio = np.nan_to_num(ratio, nan=0.0, posinf=0.0)
    off = (r_bar / 2.0) * (ratio * m + ratio.T * m.T)
    np.fill_diagonal(off, 0.0)
    rho_hat = float(np.trace(pi_mat) + off.sum())

    gamma_hat = float(((sample - target) ** 2).sum())
    kappa = (pi_hat - rho_hat) / gamma_hat if gamma_hat > 0 else 0.0
    shrink = float(np.clip(kappa / n, 0.0, 1.0))
    matrix = shrink * target + (1.0 - shrink) * sample
    return ShrunkCovariance(
        matrix=pd.DataFrame(matrix, index=columns, columns=columns),
        shrinkage=shrink,
        n_observations=int(n),
    )


def ewma_weights(n: int, halflife: float) -> np.ndarray:
    """Weights over `n` observations, oldest first, summing to one.

    `halflife` is in observations: the weight on a point `halflife` periods
    back is half the weight on the newest one.
    """
    if halflife <= 0:
        raise ValueError(f"halflife must be positive, got {halflife}")
    lam = 0.5 ** (1.0 / float(halflife))
    w = lam ** np.arange(n - 1, -1, -1, dtype=float)
    return w / w.sum()


def volatility_scalar(cov: ShrunkCovariance, returns: pd.DataFrame, halflife: float) -> float:
    """
    One number: how turbulent the panel is now against its own window average.

        s = sqrt( mean_i var_fast_i / mean_i var_slow_i )

    `rescale_volatility` moves 95 volatilities and so moves the book's
    COMPOSITION as well as its scale, because the solver reads the same matrix
    for both. That costs accuracy in the cross-section -- an exponentially
    weighted variance at a 26-week halflife rests on roughly 37 effective
    observations per series -- to buy accuracy in time. Scaling by one number
    buys the second without paying the first: `s**2 * Sigma` leaves every
    correlation AND every relative volatility exactly as the full window
    estimated them, so the optimum keeps its shape and only its size responds.

    Equal weight across series is deliberate. A benchmark-weighted or
    book-weighted turbulence measure would read the risk of a particular
    portfolio, which is the thing being sized: the scalar has to be a property
    of the panel at that date, not of the answer.
    """
    ids = cov.ids
    window = returns[ids] if list(returns.columns) != ids else returns
    x = window.to_numpy(dtype=float)
    if x.shape[0] == 0:
        return 1.0
    w = ewma_weights(x.shape[0], halflife)
    var_fast = float(np.mean(w @ (x - w @ x) ** 2))
    var_slow = float(np.mean(np.clip(np.diag(cov.matrix.to_numpy(dtype=float)), 0.0, None)))
    if not np.isfinite(var_fast) or not np.isfinite(var_slow) or var_slow <= 0.0:
        return 1.0
    return float(np.sqrt(var_fast / var_slow))


def rescale_volatility(
    cov: ShrunkCovariance, returns: pd.DataFrame, halflife: float
) -> ShrunkCovariance:
    """
    Keep the correlation, swap the volatilities for exponentially weighted ones.

    The estimate the solver sizes against has to answer two questions at once:
    how instruments move TOGETHER, and how much each one moves. The first is a
    cross-sectional structure that a long window estimates well and a short one
    estimates terribly -- it is why the window is 156 weeks and why the result
    is shrunk. The second is a level that clusters in time, and a 156-week
    equal-weighted window is the wrong instrument for it: it gives a 2008
    observation the same weight as a 2005 one.

    So this rescales, leaving the correlation matrix EXACTLY as the shrinkage
    left it and replacing each series' standard deviation with its
    exponentially weighted estimate:

        Sigma_new = D_fast R_slow D_fast,   D_fast = diag(sigma_ewma)

    Separating the two is a modelling choice with a long history (it is what
    RiskMetrics does, and the risk-model literature calls it a volatility
    overlay), and it is the narrowest change that can respond to a regime: one
    channel moves, so a test of it is a test of one hypothesis. If correlations
    also have to respond, this will not be enough, and that is a finding rather
    than a failure.

    `halflife` is in observations -- the panel here is weekly, so 26 is half a
    year. The shrinkage intensity and observation count are carried through
    unchanged; they describe the correlation, which is untouched.
    """
    ids = cov.ids
    window = returns[ids] if list(returns.columns) != ids else returns
    x = window.to_numpy(dtype=float)
    if x.shape[0] == 0:
        return cov
    w = ewma_weights(x.shape[0], halflife)
    mean = w @ x
    var_fast = w @ (x - mean) ** 2
    sd_fast = np.sqrt(np.clip(var_fast, 0.0, None))
    sd_slow = np.sqrt(np.clip(np.diag(cov.matrix.to_numpy(dtype=float)), 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = np.where(sd_slow > 0.0, sd_fast / sd_slow, 0.0)
    scale = np.nan_to_num(scale, nan=0.0, posinf=0.0)
    matrix = cov.matrix.to_numpy(dtype=float) * np.outer(scale, scale)
    return ShrunkCovariance(
        matrix=pd.DataFrame(matrix, index=cov.matrix.index, columns=cov.matrix.columns),
        shrinkage=cov.shrinkage,
        n_observations=cov.n_observations,
        legs=dict(cov.legs),
    )


def embed_benchmark_legs(
    holdable_cov: ShrunkCovariance,
    window: pd.DataFrame,
    legs: list[str],
    halflife: float | None = None,
) -> ShrunkCovariance:
    """
    Price the benchmark legs through their tracking portfolios.

    A benchmark index is not holdable, so it enters the covariance as a
    pseudo-instrument. Shrinking it alongside the holdables is wrong in a way
    that matters: every shrinkage target pulls the leg's correlations toward an
    average, and a book that replicates the leg almost exactly -- a zero-
    variance direction of the sample -- is told it carries several percent of
    tracking error. The budget then looks infeasible while the realised TE is
    under one percent; this was measured on the synthetic panel with both
    Ledoit-Wolf targets.

    So each leg is regressed on the holdables as a long-only, fully invested
    tracking portfolio (non-negative least squares with a sum-to-one row), and

        Sigma[leg, hold] = B' Sigma_hold
        Sigma[leg, leg]  = B' Sigma_hold B + residual variance

    The replication error of the tracking portfolio is then exactly the
    residual variance, whatever the shrinkage did to the holdable block, and
    the tracking weights and R^2 are kept on the result so a poor replication
    is visible rather than absorbed.

    `halflife` weights the residual variance the same way `rescale_volatility`
    weighted the holdable volatilities. It has to: the leg's variance is
    `B' Sigma_hold B + residual`, and mixing an exponentially weighted first
    term with an equal-weighted second one would leave the leg quietly
    mis-sized in exactly the regimes this is meant to catch. The tracking
    weights themselves stay equal-weighted -- they are a replication, which is
    the same structural question the long window answers for correlations.
    """
    from scipy.optimize import nnls

    hold = holdable_cov.ids
    x = window[hold].fillna(0.0).to_numpy(dtype=float)
    n = x.shape[0]
    sigma_h = holdable_cov.matrix.to_numpy(dtype=float)
    ids = hold + list(legs)
    full = np.zeros((len(ids), len(ids)))
    full[: len(hold), : len(hold)] = sigma_h
    diagnostics: dict[str, dict[str, Any]] = {}
    betas = {}
    for k, leg in enumerate(legs):
        y = window[leg].fillna(0.0).to_numpy(dtype=float)
        # sum-to-one as a heavily weighted extra row; NNLS keeps the weights >= 0
        weight = 1e3 * max(float(np.abs(y).mean()), 1e-8) * np.sqrt(n)
        a = np.vstack([x, weight * np.ones((1, len(hold)))])
        b = np.concatenate([y, [weight]])
        beta, _ = nnls(a, b)
        resid = y - x @ beta
        if halflife is None:
            resid_var = float(resid.var())
            total_var = float(y.var())
        else:
            w = ewma_weights(len(resid), halflife)
            resid_var = float(w @ (resid - w @ resid) ** 2)
            total_var = float(w @ (y - w @ y) ** 2)
        betas[leg] = beta
        diagnostics[leg] = {
            "weights": pd.Series(beta, index=hold),
            "residual_variance": resid_var,
            "r2": 1.0 - resid_var / total_var if total_var > 0 else float("nan"),
            "sum_of_weights": float(beta.sum()),
        }
        i = len(hold) + k
        full[i, : len(hold)] = beta @ sigma_h
        full[: len(hold), i] = full[i, : len(hold)]
        full[i, i] = float(beta @ sigma_h @ beta) + resid_var
    for j, leg_j in enumerate(legs):
        for k, leg_k in enumerate(legs):
            if j < k:
                i, m = len(hold) + j, len(hold) + k
                full[i, m] = full[m, i] = float(betas[leg_j] @ sigma_h @ betas[leg_k])
    return ShrunkCovariance(
        matrix=pd.DataFrame(full, index=ids, columns=ids),
        shrinkage=holdable_cov.shrinkage,
        n_observations=holdable_cov.n_observations,
        legs=diagnostics,
    )


def trailing_covariance(
    weekly: pd.DataFrame,
    as_of: pd.Timestamp,
    window: int,
    ids: list[str] | None = None,
    min_fraction: float = 0.9,
    legs: list[str] | None = None,
    vol_halflife: float | None = None,
    vol_overlay: str = "per_series",
) -> ShrunkCovariance:
    """
    The covariance an allocator could have estimated at `as_of`.

    Uses the `window` most recent periods ending on or before `as_of`. `legs`
    names benchmark series to be embedded through their tracking portfolios
    (`embed_benchmark_legs`) rather than shrunk with the holdables. A series
    is included only if it was live at the START of the window and printed in
    at least `min_fraction` of its periods; a series that entered the panel
    last year has no covariance with anything over a three-year window, and
    imputing one would be the guess the lab does not make. Callers treat a
    series absent from the result as unholdable at that date. A live series'
    occasional missing period counts as zero, which is how the engine earns it.

    `vol_halflife`, in periods, makes the estimate respond to the volatility
    regime; `None`, the default, is the equal-weighted estimate every run
    before 2026-09-17 used, to the bit. `vol_overlay` chooses how:

      * `per_series` -- `rescale_volatility`, each series' own exponentially
        weighted volatility. Responds instrument by instrument and moves the
        book's composition with it.
      * `scalar` -- `volatility_scalar`, one multiplier for the whole matrix.
        The composition is left exactly as the full window estimated it and
        only the risk level responds.

    Which is right is an empirical question about where the estimation error
    hurts more; see the TE path probe.
    """
    history = weekly.loc[weekly.index <= as_of]
    if ids is not None:
        history = history[[i for i in ids if i in history.columns]]
    history = history.tail(window)
    if len(history) < window:
        raise ValueError(
            f"{len(history)} periods on or before {as_of.date()} is short of the "
            f"{window}-period window"
        )
    present = history.notna()
    live_at_start = present.iloc[0]
    enough = present.mean(axis=0) >= min_fraction
    keep = [c for c in history.columns[live_at_start & enough] if c not in set(legs or [])]
    holdable = history[keep].fillna(0.0)
    cov = ledoit_wolf(holdable)
    if vol_halflife is not None:
        # Rescale BEFORE the legs are embedded, so each leg's variance is rebuilt
        # from the rescaled holdable block and its replication stays exact.
        if vol_overlay == "per_series":
            cov = rescale_volatility(cov, holdable, vol_halflife)
        elif vol_overlay == "scalar":
            scale = volatility_scalar(cov, holdable, vol_halflife)
            cov = ShrunkCovariance(
                matrix=cov.matrix * scale**2,
                shrinkage=cov.shrinkage,
                n_observations=cov.n_observations,
                legs=dict(cov.legs),
            )
        else:
            raise ValueError(f"unknown vol_overlay {vol_overlay!r}")
    if legs:
        missing = [g for g in legs if not (live_at_start.get(g, False) and enough.get(g, False))]
        if missing:
            raise ValueError(f"benchmark legs {missing} lack a full window at {as_of.date()}")
        cov = embed_benchmark_legs(cov, history, list(legs), halflife=vol_halflife)
    return cov


def effective_bets(correlation: pd.DataFrame) -> float:
    """
    Meucci's effective number of bets: exp of the entropy of the normalised
    eigenvalues of the correlation matrix.

    N series that are uncorrelated score N; N series that are one bet score 1.
    This is the cross-sectional half of effective breadth; the time half is
    `audit.breadth.independent_decisions_per_year`.
    """
    values = np.linalg.eigvalsh(correlation.values)
    values = np.clip(values, 0.0, None)
    total = values.sum()
    if total <= 0:
        return float("nan")
    share = values / total
    share = share[share > 0]
    return float(np.exp(-(share * np.log(share)).sum()))
