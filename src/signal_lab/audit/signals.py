"""
Planted signals of known information coefficient and known speed.

The construction, so the audit's numbers are about the pipeline and not about
the construction:

  1. The TRUTH at date t for instrument i is the forward active return over the
     next `horizon` periods, per unit of risk:

         y[t, i] = (F[t, i] - F_bench[t]) / (sigma_i * sqrt(horizon))

     where F compounds periods t+1 .. t+horizon and sigma_i is the instrument's
     trailing per-period volatility. Dividing by risk makes y comparable across
     a T-bill index and an EM equity index; keeping the benchmark's forward
     return in the difference keeps the directional (cash-timing) information a
     pure cross-sectional z-score would throw away.

  2. The NOISE is AR(1) per instrument with the same persistence an overlapping
     `horizon`-period return has at lag one, phi = (horizon - 1) / horizon, so a
     26-week signal drifts like a 26-week signal rather than flipping weekly.
     Unit variance, independent across instruments.

  3. The SIGNAL is the blend  s = ic * y + sqrt(1 - ic^2) * e,  with y and e
     each standardised to unit variance over the panel AND e first made exactly
     orthogonal to y by regressing it out. Orthogonalising is what makes the
     realised IC equal the planted one rather than merely equal it in
     expectation: the noise is persistent (phi close to one for a slow signal),
     so the effective sample behind corr(e, y) is a fraction of the cells and
     the sampling error on a raw blend runs to several hundredths -- enough to
     label a 0.10 rung with a signal that carries 0.07. The audit still
     measures and reports the realised IC, which is now a check on the
     arithmetic rather than on luck.

  4. The ALPHA handed to the solver follows Grinold: expected active return per
     period is  ic * sigma_i * s[t, i] / sqrt(horizon).  The division by
     sqrt(horizon) converts a score about an h-period return into a per-period
     forecast. This scaling does not decide the tracking error -- the budget
     does -- but it decides how alpha trades off against the spread, which is
     what the turnover-shortfall curve measures.

The signal is a lookahead by construction. It exists to measure the pipeline
and is never a run.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PlantedSignal:
    ic: float
    horizon: int
    seed: int
    score: pd.DataFrame  # dates x ids, the blended signal s
    truth: pd.DataFrame  # dates x ids, the standardised forward active return y
    alpha: pd.DataFrame  # dates x ids, per-period expected active return
    sigma: pd.DataFrame  # dates x ids, trailing per-period volatility used

    @property
    def persistence(self) -> float:
        """The AR(1) coefficient the noise was built with."""
        return (self.horizon - 1) / self.horizon


def forward_active_return(weekly: pd.DataFrame, benchmark: pd.Series, horizon: int) -> pd.DataFrame:
    """
    Compounded return over periods t+1 .. t+horizon, less the benchmark's.

    Indexed at t: what an oracle at the close of t would know. The last
    `horizon` rows are NaN -- the window runs past the data -- and the audit
    never fills them.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least one period")
    log_growth = np.log1p(weekly)
    log_bench = np.log1p(benchmark.reindex(weekly.index))
    # Sum of the NEXT `horizon` log returns: reverse-cumulate then shift back.
    fwd = log_growth[::-1].rolling(horizon, min_periods=horizon).sum()[::-1].shift(-1)
    fwd_b = log_bench[::-1].rolling(horizon, min_periods=horizon).sum()[::-1].shift(-1)
    return np.expm1(fwd).sub(np.expm1(fwd_b), axis=0)


def trailing_volatility(weekly: pd.DataFrame, window: int) -> pd.DataFrame:
    """Per-period volatility from the trailing window, NaN until the window fills."""
    return weekly.rolling(window, min_periods=window).std()


def _ar1_noise(n_periods: int, n_ids: int, phi: float, rng: np.random.Generator) -> np.ndarray:
    """Unit-variance AR(1) noise, one independent chain per instrument."""
    e = np.empty((n_periods, n_ids))
    e[0] = rng.standard_normal(n_ids)
    scale = np.sqrt(1.0 - phi * phi)
    for t in range(1, n_periods):
        e[t] = phi * e[t - 1] + scale * rng.standard_normal(n_ids)
    return e


def plant_signal(
    weekly: pd.DataFrame,
    benchmark: pd.Series,
    ic: float,
    horizon: int,
    seed: int,
    vol_window: int,
) -> PlantedSignal:
    """
    Build the planted signal on `weekly` (periods x ids) against `benchmark`
    (periods). `ic` in [0, 1]; 1 is the oracle.
    """
    if not 0.0 <= ic <= 1.0:
        raise ValueError(f"ic must be in [0, 1], got {ic}")
    sigma = trailing_volatility(weekly, vol_window)
    fwd = forward_active_return(weekly, benchmark, horizon)
    truth = fwd / (sigma * np.sqrt(horizon))

    # Standardise the truth over the whole panel (pooled), not per date, so the
    # directional component survives; the IC is then the pooled correlation.
    truth_z = (truth - np.nanmean(truth.values)) / np.nanstd(truth.values)

    rng = np.random.default_rng(seed)
    phi = (horizon - 1) / horizon
    noise = _ar1_noise(len(weekly.index), weekly.shape[1], phi, rng)
    noise = pd.DataFrame(noise, index=weekly.index, columns=weekly.columns)
    noise = noise.where(truth_z.notna())
    noise = (noise - np.nanmean(noise.values)) / np.nanstd(noise.values)

    # Make the noise exactly orthogonal to the truth, then restandardise, so the
    # blend's correlation with the truth is `ic` by construction.
    mask = truth_z.notna() & noise.notna()
    y = truth_z.values[mask.values]
    e = noise.values[mask.values]
    if len(y) > 2 and np.dot(y, y) > 0:
        noise = noise - truth_z * float(np.dot(e, y) / np.dot(y, y))
        residual_sd = float(np.nanstd(noise.values[mask.values]))
        if residual_sd > 0:
            noise = noise / residual_sd

    score = ic * truth_z + np.sqrt(1.0 - ic * ic) * noise
    alpha = ic * sigma * score / np.sqrt(horizon)
    return PlantedSignal(
        ic=ic,
        horizon=horizon,
        seed=seed,
        score=score,
        truth=truth_z,
        alpha=alpha,
        sigma=sigma,
    )


def realised_ic(signal: PlantedSignal) -> dict[str, float]:
    """
    Two readings of the IC the construction actually delivered.

    `pooled` is the correlation over every (date, instrument) cell, which is
    what the construction targets. `cross_sectional` is the mean over dates of
    the per-date rank correlation, the conventional reading, and is lower when
    the signal's information is partly directional -- a difference the audit
    reports rather than hides.
    """
    s, y = signal.score, signal.truth
    mask = s.notna() & y.notna()
    sv, yv = s.values[mask.values], y.values[mask.values]
    pooled = float(np.corrcoef(sv, yv)[0, 1]) if len(sv) > 2 else float("nan")

    per_date = []
    for date in s.index:
        row_s, row_y = s.loc[date], y.loc[date]
        ok = row_s.notna() & row_y.notna()
        if ok.sum() >= 5:
            per_date.append(row_s[ok].rank().corr(row_y[ok].rank()))
    cross = float(np.nanmean(per_date)) if per_date else float("nan")
    return {"pooled": pooled, "cross_sectional": cross, "n_dates": float(len(per_date))}


def signal_autocorrelation(score: pd.DataFrame, lag: int = 1) -> float:
    """Pooled lag-`lag` autocorrelation of the signal, the time half of breadth."""
    a = score.iloc[:-lag].values.ravel()
    b = score.iloc[lag:].values.ravel()
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 3:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])
