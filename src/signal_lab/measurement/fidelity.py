"""
The score of decisions/0046 section 3: out-of-sample loading fidelity.

The prediction for week t+1 is `b_t' f_{t+1}` with `b_t` estimated on data up to
week t (the intercept is left out, so only the loadings are scored). The error is
scaled by the instrument's own robust volatility known at t (1.4826 x the MAD of
its returns over the 156-week window ending at t) and judged by Huber's loss at
1.345, so no instrument dominates and the robust estimators are not punished by
the outliers they exist to resist.

The statistic for a candidate is the mean, over weeks, of the cross-sectional mean
of (incumbent loss - candidate loss): positive is better than the incumbent. The
gate is `stats.multiple_testing.gate` over the four candidates, with its null from
a centred block bootstrap of the weekly differentials -- one resampling shared by
all candidates in each draw. Estimators are compared on the same cells: a week and
instrument count only when the incumbent and every candidate has an estimate there.

The uncertainty check is pass or fail, not a score: the standardised prediction
errors `e / sqrt(f' V f + s^2)`, read per calendar year at the worst year, against
`vetoes.risk_calibration.max_worst_annual_bias`. The slices are reported and never
gated.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from signal_lab.measurement.estimators import MAD_TO_SD, WINDOW, LoadingPath
from signal_lab.params import Params, get_params
from signal_lab.stats.calibration import annual_bias, worst_year
from signal_lab.stats.multiple_testing import gate

HUBER_C = 1.345
BLOCK_WEEKS = 26
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 20261001
SUBPERIODS = (("2004-2007", 2004, 2007), ("2008-2009", 2008, 2009), ("2010-2019", 2010, 2019))
TOP_DECILE = 0.10


def huber_loss(u: np.ndarray, c: float = HUBER_C) -> np.ndarray:
    a = np.abs(u)
    return np.where(a <= c, 0.5 * u * u, c * a - 0.5 * c * c)


def robust_scale(R: np.ndarray) -> np.ndarray:
    """(T, N): at week t, 1.4826 x MAD of each instrument's returns in the window ending at t."""
    T, N = R.shape
    out = np.full((T, N), np.nan)
    for t in range(T):
        w = R[max(0, t - WINDOW + 1) : t + 1]
        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", RuntimeWarning)  # an all-NaN window is a NaN scale
            med = np.nanmedian(w, axis=0)
            out[t] = MAD_TO_SD * np.nanmedian(np.abs(w - med), axis=0)
    return out


@dataclass
class Evaluation:
    """Everything the scoring needs, on the cells where every estimator has an estimate."""

    names: list[str]  # incumbent first
    loss: np.ndarray  # (E, T, N) Huber loss of week t+1's error, stored at row t+1
    z: np.ndarray  # (E, T, N) standardised prediction error, at row t+1
    mask: np.ndarray  # (T, N) the common cells
    weeks: pd.DatetimeIndex


def evaluate(
    R: np.ndarray,
    F: np.ndarray,
    paths: dict[str, list[LoadingPath]],
    names: list[str],
    weeks: pd.DatetimeIndex,
) -> Evaluation:
    """
    `R` (T, N) weekly returns, `F` (T, 6) factors, `paths[name][i]` the loadings of
    instrument i. Row `t+1` of the outputs holds the prediction made at `t`.
    """
    T, N = R.shape
    scale = robust_scale(R)
    E = len(names)
    loss = np.full((E, T, N), np.nan)
    z = np.full((E, T, N), np.nan)
    have = np.ones((T, N), dtype=bool)
    for i in range(N):
        for name in names:
            h = paths[name][i].has()
            have[:, i] &= h
    target_ok = np.isfinite(R[1:]) & np.isfinite(F[1:]).all(axis=1)[:, None]
    scale_ok = np.isfinite(scale[:-1]) & (scale[:-1] > 0)
    mask = np.zeros((T, N), dtype=bool)
    mask[1:] = have[:-1] & target_ok & scale_ok
    for e, name in enumerate(names):
        for i in range(N):
            p = paths[name][i]
            m = mask[1:, i]
            if not m.any():
                continue
            t = np.flatnonzero(m)  # predictions made at t, for week t+1
            beta = p.beta[t]
            f = F[t + 1]
            err = R[t + 1, i] - np.einsum("tk,tk->t", beta, f)
            loss[e, t + 1, i] = huber_loss(err / scale[t, i])
            var = np.einsum("tk,tkl,tl->t", f, p.cov[t], f) + p.resid_var[t]
            z[e, t + 1, i] = err / np.sqrt(var)
    return Evaluation(names=names, loss=loss, z=z, mask=mask, weeks=weeks)


def weekly_differentials(ev: Evaluation) -> pd.DataFrame:
    """Weeks x candidates: the cross-sectional mean of (incumbent loss - candidate loss)."""
    inc = ev.loss[0]
    cols = {}
    for e, name in enumerate(ev.names[1:], start=1):
        diff = np.where(ev.mask, inc - ev.loss[e], 0.0)
        count = ev.mask.sum(axis=1)
        with np.errstate(all="ignore"):
            cols[name] = np.where(count > 0, diff.sum(axis=1) / count, np.nan)
    d = pd.DataFrame(cols, index=ev.weeks)
    return d.dropna(how="any")


def block_bootstrap_null(
    D: np.ndarray,
    block: int = BLOCK_WEEKS,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> np.ndarray:
    """
    (draws, K): means of centred weekly differentials, resampled in moving blocks.
    One set of block starts per draw is shared by all K candidates, which keeps
    their dependence in the null.
    """
    T, K = D.shape
    Dc = D - D.mean(axis=0)
    rng = np.random.default_rng(seed)
    n_blocks = -(-T // block)
    starts = rng.integers(0, max(T - block + 1, 1), size=(draws, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)).reshape(draws, -1)[:, :T]
    return Dc[idx].mean(axis=1)


def score(
    ev: Evaluation,
    factors: pd.DataFrame,
    params: Params | None = None,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    """The statistic, the gate, the uncertainty check and the slices, per candidate."""
    params = params or get_params()
    D = weekly_differentials(ev)
    cands = list(D.columns)
    stats = D.to_numpy().mean(axis=0)
    T0 = block_bootstrap_null(D.to_numpy(), draws=draws, seed=seed)
    verdict = gate(stats, T0, params)

    cap = float(params.require("vetoes.risk_calibration.max_worst_annual_bias"))
    min_obs = int(params.get("vetoes.risk_calibration.min_observations_per_year", 40))
    weeks = D.index
    sd = factors.std()
    move = np.sqrt(((factors.reindex(weeks) / sd) ** 2).sum(axis=1))
    stress = move >= move.quantile(1 - TOP_DECILE)

    out = {
        "gate": {
            "procedure": verdict["procedure"],
            "fwer_alpha": verdict["fwer_alpha"],
            "g": verdict["g"],
            "n_tests": verdict["n_tests"],
            "n_shuffles": verdict["n_shuffles"],
            "block_weeks": BLOCK_WEEKS,
        },
        "n_weeks_scored": int(len(D)),
        "n_cells_scored": int(ev.mask.sum()),
        "estimators": {},
    }
    for e, name in enumerate(ev.names):
        zs = pd.Series(ev.z[e][ev.mask], index=np.repeat(ev.weeks, ev.mask.sum(axis=1)))
        annual = annual_bias(zs, min_obs)
        year, worst = worst_year(annual)
        row = {
            "worst_year": year,
            "worst_annual_bias": worst,
            "bias_ok": bool(np.isfinite(worst) and worst <= cap),
            "annual_bias": {int(k): v for k, v in annual.items()},
        }
        if e > 0:
            k = cands.index(name)
            d = D[name]
            row.update(
                statistic=float(stats[k]),
                p_adjusted=float(verdict["p_adjusted"][k]),
                gate_passed=bool(verdict["rejected"][k] and stats[k] > 0),
                slices={
                    "top_decile_factor_moves": float(
                        d[stress.reindex(d.index, fill_value=False)].mean()
                    ),
                    **{
                        label: float(d[(d.index.year >= lo) & (d.index.year <= hi)].mean())
                        for label, lo, hi in SUBPERIODS
                    },
                },
            )
            row["eligible"] = bool(row["gate_passed"] and row["bias_ok"])
            row["verdict"] = "candidate" if row["eligible"] else "not_detected"
        out["estimators"][name] = row
    return out
