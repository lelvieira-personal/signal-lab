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

  5. The STANDARDISATION of the truth is a choice, and the audit can make it
     either way (the probe of 2026-09-17). `pooled` is the default and the
     construction above: the truth keeps whatever common, same-sign-across-
     instruments component the forward active return has, and the planted IC is
     the pooled correlation. `cross_sectional` removes each date's common mean
     from the truth before standardising, so the planted information is purely
     relative -- who beats whom on that date -- which is the conventional
     reading of an IC and the only part a book with no net exposure can spend.
     The two agree on a panel of exchangeable series (the synthetic one) and
     need not agree on 95 real ones. Nothing in the audit chooses between them;
     `plant_signal` takes the mode and the probe measures both.

The signal is a lookahead by construction. It exists to measure the pipeline
and is never a run.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

POOLED = "pooled"
CROSS_SECTIONAL = "cross_sectional"
STANDARDISATIONS = (POOLED, CROSS_SECTIONAL)


@dataclass(frozen=True)
class PlantedSignal:
    ic: float
    horizon: int
    seed: int
    score: pd.DataFrame  # dates x ids, the blended signal s
    truth: pd.DataFrame  # dates x ids, the standardised forward active return y
    alpha: pd.DataFrame  # dates x ids, per-period expected active return
    sigma: pd.DataFrame  # dates x ids, trailing per-period volatility used
    standardise: str = POOLED  # how the truth was standardised; see the module docstring

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


def _standardise_truth(truth: pd.DataFrame, mode: str) -> pd.DataFrame:
    """
    Standardise the truth to unit variance over the panel, one of two ways.

    `pooled` keeps each date's common component, so a signal can carry
    directional information. `cross_sectional` subtracts the date's mean over
    the instruments present first, so the planted information is purely
    relative. Both divide by a single pooled standard deviation, which keeps
    the blend's pooled correlation with the truth equal to the planted IC in
    either mode.
    """
    if mode not in STANDARDISATIONS:
        raise ValueError(f"standardise must be one of {STANDARDISATIONS}, got {mode!r}")
    if mode == CROSS_SECTIONAL:
        truth = truth.sub(truth.mean(axis=1), axis=0)
    return (truth - np.nanmean(truth.values)) / np.nanstd(truth.values)


def plant_signal(
    weekly: pd.DataFrame,
    benchmark: pd.Series,
    ic: float,
    horizon: int,
    seed: int,
    vol_window: int,
    standardise: str = POOLED,
) -> PlantedSignal:
    """
    Build the planted signal on `weekly` (periods x ids) against `benchmark`
    (periods). `ic` in [0, 1]; 1 is the oracle. `standardise` is `pooled` (the
    default, and what every audit run before 2026-09-17 used) or
    `cross_sectional`; see the module docstring.
    """
    if not 0.0 <= ic <= 1.0:
        raise ValueError(f"ic must be in [0, 1], got {ic}")
    sigma = trailing_volatility(weekly, vol_window)
    fwd = forward_active_return(weekly, benchmark, horizon)
    truth = fwd / (sigma * np.sqrt(horizon))

    # Pooled, not per date, keeps the directional component; cross-sectional
    # removes it. Either way the IC is the pooled correlation.
    truth_z = _standardise_truth(truth, standardise)

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
        standardise=standardise,
    )


def _per_date_pearson(a: pd.DataFrame, b: pd.DataFrame, demean: bool, min_n: int = 5) -> float:
    """Mean over dates of the within-date Pearson correlation of `a` and `b`."""
    if demean:
        a = a.sub(a.mean(axis=1), axis=0)
        b = b.sub(b.mean(axis=1), axis=0)
    out = []
    for date in a.index:
        row_a, row_b = a.loc[date], b.loc[date]
        ok = row_a.notna() & row_b.notna()
        if ok.sum() >= min_n:
            x, y = row_a[ok].to_numpy(dtype=float), row_b[ok].to_numpy(dtype=float)
            if x.std() > 1e-12 and y.std() > 1e-12:
                out.append(float(np.corrcoef(x, y)[0, 1]))
    return float(np.mean(out)) if out else float("nan")


def realised_ic(signal: PlantedSignal) -> dict[str, float]:
    """
    Readings of the IC the construction actually delivered.

    `pooled` is the correlation over every (date, instrument) cell, which is
    what the construction targets. `cross_sectional` is the mean over dates of
    the per-date RANK correlation, the conventional reading, and is lower when
    the signal's information is partly directional -- a difference the audit
    reports rather than hides.

    Two further readings, added with the standardisation probe (2026-09-17),
    separate "the metric zeroes the common component" from "there is no
    cross-sectional information". `cross_sectional_pearson` is the per-date
    Pearson correlation on the levels, so a common component that moves both
    still counts; `cross_sectional_demeaned` removes each date's mean from BOTH
    series first, which is exactly the part of the signal a book with no net
    exposure can spend. On a panel where the truth carries no common component
    the three agree; where it does, `pooled` can exceed all of them.
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
    return {
        "pooled": pooled,
        "cross_sectional": cross,
        "cross_sectional_pearson": _per_date_pearson(s, y, demean=False),
        "cross_sectional_demeaned": _per_date_pearson(s, y, demean=True),
        "n_dates": float(len(per_date)),
    }


def truth_decomposition(signal: PlantedSignal) -> dict[str, float]:
    """
    How much of the planted truth is a common move, and how much is selection.

    At each date the truth splits into the mean over the instruments present
    (the common component: every holding wins or loses together, which a book
    can only express by moving between asset classes and cash) and the
    deviations from it (the cross-sectional component). `common_share` is the
    share of the truth's total variance carried by the common part.

    This is a property of the PANEL and the horizon, not of the seed or the IC:
    it says what kind of information a perfect forecast of the forward active
    return would be on this universe.
    """
    y = signal.truth
    common = y.mean(axis=1)
    residual = y.sub(common, axis=0)
    var_total = float(np.nanvar(y.values))
    # Weight the common component by the instruments present on each date, so a
    # date with five live series does not count like one with ninety-five.
    counts = y.notna().sum(axis=1)
    var_common = (
        float(
            np.nansum((common**2) * counts) / max(float(counts.sum()), 1.0)
            - (float(np.nansum(common * counts) / max(float(counts.sum()), 1.0)) ** 2)
        )
        if counts.sum() > 0
        else float("nan")
    )
    var_residual = float(np.nanvar(residual.values))
    return {
        "common_share": var_common / var_total if var_total > 0 else float("nan"),
        "var_total": var_total,
        "var_common": var_common,
        "var_residual": var_residual,
        "common_sd": float(np.nanstd(common.values)),
    }


def signal_autocorrelation(score: pd.DataFrame, lag: int = 1) -> float:
    """Pooled lag-`lag` autocorrelation of the signal, the time half of breadth."""
    a = score.iloc[:-lag].values.ravel()
    b = score.iloc[lag:].values.ravel()
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 3:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])
