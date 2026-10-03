"""
Orchestration for the loading-estimator test (decisions/0046): every estimator on
every instrument, the checks that nothing looked ahead, and the tables the report
reads. Pure functions on arrays and frames; the script does the I/O.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from signal_lab.measurement import estimators as E
from signal_lab.measurement.estimators import (
    CANDIDATES,
    INCUMBENT,
    Context,
    LoadingPath,
    RegimePath,
)

ALL_NAMES = [INCUMBENT, *CANDIDATES]
ROLLING_CORR_WEEKS = 156


def class_members(classes: list[str]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for i, c in enumerate(classes):
        out.setdefault(c, []).append(i)
    return out


def assert_no_lookahead(paths: dict[str, list[LoadingPath]]) -> None:
    """Every estimate records the last data week it used; none may be after its own."""
    for name, plist in paths.items():
        for i, p in enumerate(plist):
            t = np.flatnonzero(p.has())
            bad = p.last_index[t] > t
            if bad.any():
                raise AssertionError(
                    f"{name}, instrument {i}: an estimate at week {int(t[bad][0])} used "
                    f"data from week {int(p.last_index[t][bad][0])}"
                )


def estimate_all(
    R: np.ndarray,
    F: np.ndarray,
    classes: list[str],
    regimes: RegimePath,
    instruments: list[int] | None = None,
) -> dict[str, list[LoadingPath]]:
    """
    Every estimator's path for each instrument in `instruments` (default all).
    Peers are always drawn from the whole class, so a subset still sees its class.
    """
    N = R.shape[1]
    members = class_members(classes)
    ols = [E.RollingOLS().path(R[:, i], F) for i in range(N)]
    todo = list(range(N)) if instruments is None else instruments
    paths: dict[str, list[LoadingPath]] = {name: [] for name in ALL_NAMES}
    for i in todo:
        ctx = Context(
            peer_betas=E.peer_beta_array(ols, i, members[classes[i]]),
            regimes=regimes,
        )
        y = R[:, i]
        paths[INCUMBENT].append(ols[i])
        for name in CANDIDATES:
            paths[name].append(E.ESTIMATORS[name]().path(y, F, ctx))
    assert_no_lookahead(paths)
    return paths


def project_runtime(
    R: np.ndarray, F: np.ndarray, classes: list[str], n_time: int = 10, hmm_fits: int = 8
) -> dict[str, float]:
    """
    Time the work on `n_time` instruments and a few HMM fits, and project to the full
    run: the HMM is one fit a week for everyone, the rest scales with instruments.
    """
    N, n = R.shape[1], R.shape[0]
    ok = np.flatnonzero(np.isfinite(F).all(axis=1))
    first_fit = int(ok[E.WINDOW - 1]) if len(ok) >= E.WINDOW else n
    n_fits = max(n - first_fit, 0)
    mid = first_fit + max(n_fits // 2, 0)
    t0 = time.perf_counter()
    for t in range(mid, min(mid + hmm_fits, n)):
        rows = np.flatnonzero(np.isfinite(F[: t + 1]).all(axis=1))
        E.fit_hmm2(F[rows])
    hmm_per_fit = (time.perf_counter() - t0) / max(min(hmm_fits, n - mid), 1)

    # A regime path restricted to the last weeks, so the HMM estimator has something to
    # read on the timing instruments; its own per-instrument cost is what is timed.
    stub = E.regime_path(F, start=max(n - hmm_fits, 0))
    t0 = time.perf_counter()
    estimate_all(R, F, classes, stub, instruments=list(range(min(n_time, N))))
    per_instrument = (time.perf_counter() - t0) / max(min(n_time, N), 1)

    total = hmm_per_fit * n_fits + per_instrument * N
    return {
        "hmm_seconds_per_fit": hmm_per_fit,
        "hmm_fits": float(n_fits),
        "seconds_per_instrument": per_instrument,
        "instruments": float(N),
        "projected_seconds": float(total),
    }


def pair_shares(
    paths: dict[str, list[LoadingPath]], mask: np.ndarray, name: str
) -> dict[str, object]:
    """
    How often each (half-life, q) pair of `name` was the one in force, over the scored
    cells: instrument i, prediction made at t, for week t+1 (`mask[t + 1, i]`). Shares sum to 1.
    """
    counts = np.zeros(len(E.MR_PAIRS))
    for i, p in enumerate(paths[name]):
        t = np.flatnonzero(mask[1:, i])
        picked = p.extra["pair"][t]
        picked = picked[picked >= 0]
        counts += np.bincount(picked, minlength=len(E.MR_PAIRS))
    total = counts.sum()
    share = counts / total if total else counts
    return {
        "n_cells": int(total),
        "pairs": {f"h{h}_q{q:g}": float(s) for (h, q), s in zip(E.MR_PAIRS, share, strict=True)},
        "by_half_life": {
            f"h{h}": float(sum(s for (hh, _), s in zip(E.MR_PAIRS, share, strict=True) if hh == h))
            for h in E.MR_HALF_LIVES
        },
        "by_q": {
            f"q{q:g}": float(
                sum(s for (_, qq), s in zip(E.MR_PAIRS, share, strict=True) if qq == q)
            )
            for q in E.MR_Q
        },
    }


def hmm_stability(regimes: RegimePath) -> dict[str, float | int]:
    """Whether the regimes held across the ten restarts: label-aligned agreement with the best."""
    lo = np.array(list(regimes.agreement_min.values()), dtype=float)
    med = np.array(list(regimes.agreement_median.values()), dtype=float)
    if len(lo) == 0:
        return {"n_fits": 0}
    return {
        "n_fits": int(len(lo)),
        "agreement_min_over_restarts_median_over_weeks": float(np.median(lo)),
        "agreement_min_over_restarts_worst_week": float(lo.min()),
        "agreement_median_over_restarts_median_over_weeks": float(np.median(med)),
        "weeks_with_a_restart_below_90pct_agreement": int((lo < 0.90).sum()),
    }


def loadings_long(
    paths: dict[str, list[LoadingPath]],
    ids: list[str],
    weeks: pd.DatetimeIndex,
    factors: list[str],
) -> pd.DataFrame:
    """instrument, date, estimator, factor, loading, se -- the week the loading was estimated at."""
    frames = []
    for name, plist in paths.items():
        for i, p in enumerate(plist):
            t = np.flatnonzero(p.has())
            if len(t) == 0:
                continue
            se = np.sqrt(np.clip(np.einsum("tkk->tk", p.cov[t]), 0.0, None))
            for k, factor in enumerate(factors):
                frames.append(
                    pd.DataFrame(
                        {
                            "instrument": ids[i],
                            "date": weeks[t],
                            "estimator": name,
                            "factor": factor,
                            "loading": p.beta[t, k],
                            "se": se[:, k],
                        }
                    )
                )
    return pd.concat(frames, ignore_index=True)


def factor_correlations(frame: pd.DataFrame) -> dict:
    """Full-sample correlations and the range of each pair's rolling 156-week value."""
    clean = frame.dropna()
    full = clean.corr()
    roll = clean.rolling(ROLLING_CORR_WEEKS).corr().dropna()
    names = list(clean.columns)
    ranges = {}
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            s = roll.xs(names[a], level=1)[names[b]]
            ranges[f"{names[a]}~{names[b]}"] = {"min": float(s.min()), "max": float(s.max())}
    return {"full_sample": full.round(4).to_dict(), "rolling_156w_range": ranges}
