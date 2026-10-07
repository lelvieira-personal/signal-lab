"""
Huber loadings on six factors, walk-forward, and what goes beside them (decisions/0049).

Pure functions on arrays and frames; `scripts/build_characteristics.py` does the I/O. The
estimator is `measurement.estimators.HuberM` exactly as registered (H-2026-0013), imported and
not copied, so a change to it is a change to the map.

Every row says what kind of number it is: `estimated` rows carry the estimator's name,
`measured` rows come from the analytics panel and are never merged with them (decisions/0015).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.loaders.holdout import enforce_holdout
from signal_lab.measurement import run as measurement_run
from signal_lab.measurement.estimators import WINDOW, HuberM, LoadingPath, valid_rows
from signal_lab.measurement.factors import FACTOR_NAMES, weekly_levels
from signal_lab.params import Params, get_params

ESTIMATOR = "huber_m"
ESTIMATED = "estimated"
MEASURED = "measured"
EXPLAINED_WINDOW = WINDOW  # weeks
EXPLAINED_MIN = 52  # out-of-sample weeks the share needs; NaN before that
MEASURED_FIELDS = {"oad": "INDEX_OAD_TSY", "oas": "INDEX_OAS_TSY"}


def explained_share(r: np.ndarray, F: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """
    `1 - sum (r_s - p_s)^2 / sum r_s^2` over the 156 weeks ending at t, `p_s = b_(s-1)' f_s`:
    last week's loading, this week's factors, no intercept. A week counts when `b_(s-1)`,
    `r_s` and `f_s` all exist; fewer than 52 such weeks is NaN. Out of sample, uses nothing
    after t, and is not clipped: it may be negative. `beta` is (T, K), NaN where there is none.
    """
    T = len(r)
    p = np.full(T, np.nan)
    p[1:] = np.einsum("tk,tk->t", beta[:-1], F[1:])
    ok = np.isfinite(p) & np.isfinite(r)
    err = np.where(ok, (r - p) ** 2, 0.0)
    den = np.where(ok, r * r, 0.0)
    out = np.full(T, np.nan)
    for t in range(T):
        lo = max(0, t - EXPLAINED_WINDOW + 1)
        if ok[lo : t + 1].sum() >= EXPLAINED_MIN:
            d = den[lo : t + 1].sum()
            if d > 0:
                out[t] = 1.0 - err[lo : t + 1].sum() / d
    return out


def window_count(valid: np.ndarray) -> np.ndarray:
    """Valid weeks in the 156-week window ending at each t."""
    csum = np.concatenate([[0], np.cumsum(valid.astype(int))])
    t = np.arange(len(valid))
    return csum[t + 1] - csum[np.maximum(0, t - WINDOW + 1)]


def estimate_paths(R: np.ndarray, F: np.ndarray) -> list[LoadingPath]:
    """Huber loadings for each column of `R`, checked for lookahead before anything is kept."""
    paths = [HuberM().path(R[:, i], F) for i in range(R.shape[1])]
    measurement_run.assert_no_lookahead({ESTIMATOR: paths})
    return paths


def build_estimated(
    R: np.ndarray,
    F: np.ndarray,
    ids: list[str],
    classes: list[str],
    weeks: pd.DatetimeIndex,
    params: Params | None = None,
) -> dict[str, pd.DataFrame | list[LoadingPath]]:
    """
    The estimated half. `R` (T, N) weekly returns, `F` (T, 6) factors, `weeks` the Friday that
    closes each row. Returns the long loadings, the per-row fit fields, the per-instrument
    table and the paths. Raises HoldoutViolation on a week on or after HOLDOUT_START.
    """
    params = params or get_params()
    enforce_holdout(pd.DatetimeIndex(weeks), params, what="characteristics weeks")
    paths = estimate_paths(R, F)
    K = len(FACTOR_NAMES)
    load_frames, fit_frames, inst_rows = [], [], []
    for i, (sid, klass) in enumerate(zip(ids, classes, strict=True)):
        p = paths[i]
        t = np.flatnonzero(p.has())
        share = explained_share(R[:, i], F, p.beta)
        n_valid = window_count(valid_rows(R[:, i], F))
        full = _full_sample_share(R[:, i], F, p.beta)
        inst_rows.append(
            {
                "instrument": sid,
                "class": klass,
                "estimated": bool(len(t)),
                "first_date": weeks[t[0]] if len(t) else pd.NaT,
                "last_date": weeks[t[-1]] if len(t) else pd.NaT,
                "n_rows": int(len(t)),
                "explained_share_full": full,
                "kind": ESTIMATED,
                "estimator": ESTIMATOR,
            }
        )
        if not len(t):
            continue
        se = np.sqrt(np.stack([p.cov[t, k, k] for k in range(K)], axis=1))
        load_frames.append(
            pd.DataFrame(
                {
                    "instrument": sid,
                    "date": np.repeat(weeks[t].to_numpy(), K),
                    "factor": np.tile(list(FACTOR_NAMES), len(t)),
                    "loading": p.beta[t].reshape(-1),
                    "se": se.reshape(-1),
                    "kind": ESTIMATED,
                    "estimator": ESTIMATOR,
                }
            )
        )
        fit_frames.append(
            pd.DataFrame(
                {
                    "instrument": sid,
                    "date": weeks[t],
                    "resid_var": p.resid_var[t],
                    "n_valid_weeks": n_valid[t],
                    "last_data_date": weeks[p.last_index[t]],
                    "explained_share": share[t],
                    "kind": ESTIMATED,
                    "estimator": ESTIMATOR,
                }
            )
        )
    return {
        "loadings": pd.concat(load_frames, ignore_index=True),
        "fit": pd.concat(fit_frames, ignore_index=True),
        "instruments": pd.DataFrame(inst_rows),
        "paths": paths,
    }


def _full_sample_share(r: np.ndarray, F: np.ndarray, beta: np.ndarray) -> float:
    """The same share over every out-of-sample week the instrument has (reported, not stored per row)."""
    p = np.full(len(r), np.nan)
    p[1:] = np.einsum("tk,tk->t", beta[:-1], F[1:])
    ok = np.isfinite(p) & np.isfinite(r)
    if ok.sum() < EXPLAINED_MIN or not (r[ok] ** 2).sum() > 0:
        return float("nan")
    return float(1.0 - ((r[ok] - p[ok]) ** 2).sum() / (r[ok] ** 2).sum())


def measured_cells(
    analytics_fields: dict[str, pd.DataFrame],
    ids: list[str],
    dates: pd.DatetimeIndex,
    weeks: pd.DatetimeIndex,
    params: Params | None = None,
) -> pd.DataFrame:
    """
    `INDEX_OAD_TSY` and `INDEX_OAS_TSY` for each instrument that has them, at each weekly date:
    the last observation in the week ending on that Friday (`weekly_levels`), never a later
    one, and never carried over an empty week (SUBSTRATE section 2: no forward fill). A row
    exists where at least one of the two is observed. Marked `measured`.
    """
    params = params or get_params()
    enforce_holdout(pd.DatetimeIndex(weeks), params, what="characteristics measured weeks")
    frames = []
    for sid in ids:
        cols = {}
        for name, field in MEASURED_FIELDS.items():
            panel = analytics_fields.get(field)
            if panel is not None and sid in panel.columns:
                cols[name] = weekly_levels(panel[sid], dates).reindex(weeks)
        if not cols:
            continue
        f = pd.DataFrame(cols)
        for name in MEASURED_FIELDS:
            if name not in f:
                f[name] = np.nan
        f = f[list(MEASURED_FIELDS)].dropna(how="all")
        if f.empty:
            continue
        f.insert(0, "instrument", sid)
        f.index.name = "date"
        frames.append(f.reset_index())
    if not frames:
        return pd.DataFrame(columns=["instrument", "date", *MEASURED_FIELDS, "kind"])
    out = pd.concat(frames, ignore_index=True)
    out["kind"] = MEASURED
    return out
