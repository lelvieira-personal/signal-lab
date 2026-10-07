"""
Descriptions of the loading estimators' output, made AFTER the test's results were seen
(HANDOFF task 48, decisions/0046 addendum of 2026-10-03). Nothing here is a test and nothing
here changes a verdict. Two descriptions:

* `stability`: how much each estimator's loadings move, from `loadings.parquet` alone.
* `fit_metrics`: how well the stored loadings predict at all, on the cells the score used.

The mean-reverting candidate stores its forecast for week t+1 and the others a value at t.
Both are compared as stored, because that is what would be handed to an exposure matrix.
Pure functions on arrays and frames; the script does the I/O.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from signal_lab.measurement.fidelity import huber_loss

LAGS = {"weekly_change": 1, "annual_change": 52}
STRESS_YEARS = (2008, 2009)
MIN_WEEKS_FOR_TS_CORR = 26
MIN_INSTRUMENTS_FOR_XS_CORR = 5
ROLLING_CORR_WEEKS = 52


# --- stability --------------------------------------------------------------------------------


def loading_arrays(
    long: pd.DataFrame, estimators: list[str]
) -> tuple[np.ndarray, pd.DatetimeIndex, list[str], list[str]]:
    """(E, T, N, K) loadings on the grid of dates and instruments the frame holds, NaN where none."""
    dates = pd.DatetimeIndex(sorted(long["date"].unique()))
    instruments = sorted(long["instrument"].unique())
    factors = list(dict.fromkeys(long["factor"]))
    t_idx = dates.get_indexer(long["date"])
    i_idx = pd.Index(instruments).get_indexer(long["instrument"])
    k_idx = pd.Index(factors).get_indexer(long["factor"])
    e_idx = pd.Index(estimators).get_indexer(long["estimator"])
    out = np.full((len(estimators), len(dates), len(instruments), len(factors)), np.nan)
    keep = e_idx >= 0
    out[e_idx[keep], t_idx[keep], i_idx[keep], k_idx[keep]] = long["loading"].to_numpy()[keep]
    return out, dates, instruments, factors


def _mean_abs_change(
    B: np.ndarray, common: np.ndarray, lag: int, week_ok: np.ndarray
) -> np.ndarray:
    """(E, K): mean over instruments of the mean over weeks of |b_t - b_(t-lag)|, on common cells."""
    E, T, N, K = B.shape
    out = np.full((E, K), np.nan)
    if T <= lag:
        return out
    both = common[lag:] & common[:-lag] & week_ok[lag:, None]  # (T-lag, N)
    d = np.abs(B[:, lag:] - B[:, :-lag])  # (E, T-lag, N, K)
    d = np.where(both[None, :, :, None], d, np.nan)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # a slice with no common pair is a NaN
        per_instrument = np.nanmean(d, axis=1)  # (E, N, K)
        out = np.nanmean(per_instrument, axis=1)  # (E, K)
    return out


def _rank_agreement(B: np.ndarray, common: np.ndarray) -> np.ndarray:
    """(E, K): median over weeks of the cross-sectional Spearman correlation with estimator 0."""
    E, T, N, K = B.shape
    out = np.full((E, K), np.nan)
    for e in range(E):
        for k in range(K):
            rho = []
            for t in range(T):
                m = common[t]
                if m.sum() < MIN_INSTRUMENTS_FOR_XS_CORR:
                    continue
                a, b = rankdata(B[e, t, m, k]), rankdata(B[0, t, m, k])
                if a.std() == 0 or b.std() == 0:
                    continue
                rho.append(float(np.corrcoef(a, b)[0, 1]))
            if rho:
                out[e, k] = float(np.median(rho))
    return out


def stability(long: pd.DataFrame, estimators: list[str]) -> dict:
    """
    For each estimator and factor, over the cells where EVERY estimator has a loading at the
    week (and, for a change, at the week it is differenced against): `weekly_change`,
    `annual_change`, each as an absolute mean and as a ratio to `estimators[0]` (rolling OLS),
    the same for 2008-2009 alone, and `rank_agreement` with rolling OLS.
    """
    B, dates, _, factors = loading_arrays(long, estimators)
    common = np.isfinite(B).all(axis=(0, 3))  # (T, N)
    everywhere = np.ones(len(dates), dtype=bool)
    crisis = np.isin(dates.year, STRESS_YEARS)
    out: dict = {"estimators": estimators, "factors": factors, "cells": int(common.sum())}
    for label, lag in LAGS.items():
        for tag, week_ok in (("", everywhere), ("_2008_2009", crisis)):
            a = _mean_abs_change(B, common, lag, week_ok)
            out[label + tag] = {
                "abs": {
                    e: dict(zip(factors, a[i].tolist(), strict=True))
                    for i, e in enumerate(estimators)
                },
                "ratio": {
                    e: dict(zip(factors, (a[i] / a[0]).tolist(), strict=True))
                    for i, e in enumerate(estimators)
                },
            }
    r = _rank_agreement(B, common)
    out["rank_agreement"] = {
        e: dict(zip(factors, r[i].tolist(), strict=True)) for i, e in enumerate(estimators)
    }
    out["summary"] = {
        e: {
            **{
                f"{label}{tag}_ratio": float(np.mean(list(out[label + tag]["ratio"][e].values())))
                for label in LAGS
                for tag in ("", "_2008_2009")
            },
            "rank_agreement": float(np.mean(list(out["rank_agreement"][e].values()))),
        }
        for e in estimators
    }
    return out


# --- absolute fit -----------------------------------------------------------------------------


def scored_cells(have: np.ndarray, R: np.ndarray, F: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """The score's mask (fidelity.evaluate): row t+1 is scored when week t's loading exists."""
    target_ok = np.isfinite(R[1:]) & np.isfinite(F[1:]).all(axis=1)[:, None]
    scale_ok = np.isfinite(scale[:-1]) & (scale[:-1] > 0)
    mask = np.zeros(R.shape, dtype=bool)
    mask[1:] = have[:-1] & target_ok & scale_ok
    return mask


def predictions(beta: np.ndarray, F: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    `p[t+1, i] = b_t' f_(t+1)` and its per-factor parts `c[t+1, i, k] = b_(t,k) f_(t+1,k)`,
    both stored at row t+1 (NaN at row 0). `beta` is (T, N, K).
    """
    c = np.full(beta.shape, np.nan)
    c[1:] = beta[:-1] * F[1:, None, :]
    return c.sum(axis=2), c


def _skill(r, p, scale_prev, m) -> dict:
    """r2_oos and huber_skill on the cells `m` (T, N); loss_zero is the score's loss at p = 0."""
    if not m.any():
        return {"r2_oos": None, "huber_skill": None, "cells": 0}
    rr, pp, ss = r[m], p[m], scale_prev[m]
    loss = huber_loss((rr - pp) / ss).sum()
    loss0 = huber_loss(rr / ss).sum()
    return {
        "r2_oos": float(1.0 - np.sum((rr - pp) ** 2) / np.sum(rr * rr)),
        "huber_skill": float(1.0 - loss / loss0),
        "cells": int(m.sum()),
    }


def _pearson(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def fit_metrics(
    R: np.ndarray,
    F: np.ndarray,
    betas: dict[str, np.ndarray],
    scale: np.ndarray,
    classes: list[str],
    ids: list[str],
    weeks: pd.DatetimeIndex,
    slices: dict[str, np.ndarray],
    mask: np.ndarray | None = None,
) -> dict:
    """
    How well each estimator's stored loadings predict, on the scored cells. `R` (T, N) weekly
    returns, `F` (T, K) factors, `betas[name]` (T, N, K), `scale` (T, N) the score's robust
    volatility, `slices[label]` a (T,) week mask over the prediction week. No intercept, as in
    the score: the benchmark for r2_oos and huber_skill is a loading of zero.
    """
    if mask is None:
        have = np.ones(R.shape, dtype=bool)
        for b in betas.values():
            have &= np.isfinite(b).all(axis=2)
        mask = scored_cells(have, R, F, scale)
    scale_prev = np.full(R.shape, np.nan)
    scale_prev[1:] = scale[:-1]
    cls = np.array(classes)
    out: dict = {"cells": int(mask.sum()), "estimators": {}}
    for name, beta in betas.items():
        p, c = predictions(beta, F)
        e: dict = {"pooled": _skill(R, p, scale_prev, mask), "by_class": {}, "slices": {}}
        for k in sorted(set(classes)):
            e["by_class"][k] = _skill(R, p, scale_prev, mask & (cls == k)[None, :])
        for label, wk in slices.items():
            e["slices"][label] = _skill(R, p, scale_prev, mask & wk[:, None])
        # per-instrument time-series correlation of p and r
        ts = {}
        for i, sid in enumerate(ids):
            m = mask[:, i]
            if m.sum() >= MIN_WEEKS_FOR_TS_CORR:
                ts[sid] = _pearson(p[m, i], R[m, i])
        ts = {s: v for s, v in ts.items() if v is not None}
        e["ts_corr"] = {
            "by_class": {
                k: _quartiles([v for s, v in ts.items() if classes[ids.index(s)] == k])
                for k in sorted(set(classes))
            },
            "pooled": _quartiles(list(ts.values())),
            "lowest_ten": [[s, v] for s, v in sorted(ts.items(), key=lambda kv: kv[1])[:10]],
        }
        # per-week cross-sectional Spearman of p and r (conditional on the realised factor moves)
        rho = []
        for t in np.flatnonzero(mask.any(axis=1)):
            m = mask[t]
            if m.sum() < MIN_INSTRUMENTS_FOR_XS_CORR:
                continue
            a, b = rankdata(p[t, m]), rankdata(R[t, m])
            v = _pearson(a, b)
            if v is not None:
                rho.append(v)
        rho = np.array(rho)
        e["xs_corr"] = {
            "mean": float(rho.mean()) if len(rho) else None,
            "sd": float(rho.std(ddof=1)) if len(rho) > 1 else None,
            "share_above_zero": float((rho > 0).mean()) if len(rho) else None,
            "weeks": int(len(rho)),
        }
        # factor_share: each factor's share of the predicted variation, sum p c_k / sum p^2
        e["factor_share"] = {"pooled": _shares(p, c, mask)}
        for k in sorted(set(classes)):
            e["factor_share"][k] = _shares(p, c, mask & (cls == k)[None, :])
        e["mean_huber_loss"] = float(huber_loss((R[mask] - p[mask]) / scale_prev[mask]).mean())
        out["estimators"][name] = e
    return out


def _shares(p: np.ndarray, c: np.ndarray, m: np.ndarray) -> list[float] | None:
    den = float(np.sum(p[m] ** 2))
    return None if den == 0 else ((p[m][:, None] * c[m]).sum(axis=0) / den).tolist()


def _quartiles(v: list[float]) -> dict:
    if not v:
        return {"n": 0, "q1": None, "median": None, "q3": None}
    a = np.asarray(v, dtype=float)
    return {
        "n": int(len(a)),
        "q1": float(np.quantile(a, 0.25)),
        "median": float(np.median(a)),
        "q3": float(np.quantile(a, 0.75)),
    }


def rolling_corr(p: np.ndarray, r: np.ndarray, window: int = ROLLING_CORR_WEEKS) -> np.ndarray:
    """52-observation rolling correlation of p and r over an instrument's scored weeks."""
    s = pd.DataFrame({"p": p, "r": r})
    return s["p"].rolling(window).corr(s["r"]).to_numpy()
