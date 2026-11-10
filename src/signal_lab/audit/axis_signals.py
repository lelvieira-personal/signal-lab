"""
Planted signals at the AXIS level, for the phase-2 pilot (decisions/0059 G and its addendum of
2026-11-10, points 2 to 4; HANDOFF task 90).

`audit/signals.py` plants an instrument-level score. The phase-2 rule takes a score per view
(one column for a directional axis, one per view region for the region cross-section), so the
pilot plants there, the same way:

  1. The TRUTH at date t for a column is the forward `horizon`-week SUM of its factor, periods
     t+1 .. t+horizon (the factors are weekly changes or weekly relative returns, so they add).
     Directional: standardised pooled. Cross-sectional: demeaned across the columns at each date
     first, then standardised pooled (`signals._standardise_truth`, CROSS_SECTIONAL), so it
     still sums to zero across the columns at each date.
  2. The NOISE is `signals._ar1_noise` at phi = (horizon - 1) / horizon, made exactly orthogonal
     to the truth PER COLUMN and scaled to that column's truth standard deviation, so each
     column's correlation with its truth is the planted IC by construction (the reviewer's
     refinement of point 3, decisions/0059 addendum of 2026-11-10).
  3. The SCORE is `ic * truth + sqrt(1 - ic^2) * noise`.
  4. The BASELINE (decisions/0036 section 4b, the twin `run_cell` pairs against) blends the score
     from a block-shuffled copy of the truth (`stats.blocks.baseline_rng(seed)`, blocks of
     `signals.BASELINE_BLOCK`), with the live noise draw; `truth` stays the real one so
     `realised_ic` reads what the score carries about the future.

Holdout (SUBSTRATE section 2): a score dated t reads factor values to t + horizon weeks, so no
score date may be within `horizon` weeks of HOLDOUT_START. `check_score_dates` refuses a frame
that reaches past it. The signal is a lookahead by construction; it measures the pipeline and is
never a run.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from signal_lab.audit.signals import (
    BASELINE_BLOCK,
    CROSS_SECTIONAL,
    POOLED,
    _ar1_noise,
    _per_date_pearson,
    _standardise_truth,
)
from signal_lab.loaders.holdout import HoldoutViolation, enforce_holdout
from signal_lab.params import Params
from signal_lab.stats.blocks import baseline_rng, block_shuffle_rows

EXPRESSIONS = ("directional", "cross_sectional")


@dataclass(frozen=True)
class AxisPlant:
    ic: float
    horizon: int
    seed: int
    expression: str
    score: pd.DataFrame  # dates x columns, the blended score handed to the rule
    truth: pd.DataFrame  # dates x columns, the standardised forward factor move (the real one)
    blend_truth: pd.DataFrame  # what the score was blended from: the truth, or its shuffle
    baseline: bool = False


def holdout_cutoff(horizon: int, params: Params) -> pd.Timestamp:
    """The last date a score may carry: `horizon` weeks before HOLDOUT_START, exclusive."""
    start = pd.Timestamp(params.require("data.windows.holdout_start"))
    return start - pd.Timedelta(weeks=int(horizon)) - pd.Timedelta(days=1)


def check_score_dates(index: pd.Index, horizon: int, params: Params) -> None:
    """Refuse a score date within `horizon` weeks of HOLDOUT_START (its truth would read it)."""
    enforce_holdout(pd.DatetimeIndex(index), params, "axis-level planted scores")
    cutoff = holdout_cutoff(horizon, params)
    late = pd.DatetimeIndex(index)[pd.DatetimeIndex(index) > cutoff]
    if len(late):
        raise HoldoutViolation(
            f"{len(late)} score date(s) from {late[0].date()} are within {horizon} weeks of "
            f"HOLDOUT_START: their truth would read the holdout"
        )


def forward_sum(factor: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Sum of periods t+1 .. t+horizon, indexed at t; NaN where the window is incomplete."""
    if horizon < 1:
        raise ValueError("horizon must be at least one period")
    return factor[::-1].rolling(horizon, min_periods=horizon).sum()[::-1].shift(-1)


def plant_axis_signal(
    factor: pd.DataFrame,
    ic: float,
    horizon: int,
    seed: int,
    expression: str,
    params: Params,
    baseline: bool = False,
) -> AxisPlant:
    """
    The planted score for one pilot run. `factor` is weekly, dates x columns (one column per
    view); its dates must end at or before the holdout cutoff's horizon (`check_score_dates`
    runs on the score's index). The score is dropped from the dates whose truth is not
    defined at the end of the frame, so the frame handed to the rule stops at the last date
    with a truth.
    """
    if not 0.0 <= ic <= 1.0:
        raise ValueError(f"ic must be in [0, 1], got {ic}")
    if expression not in EXPRESSIONS:
        raise ValueError(f"expression must be one of {EXPRESSIONS}, got {expression!r}")
    if expression == "cross_sectional" and factor.shape[1] < 2:
        raise ValueError("a cross-section needs at least two columns")
    enforce_holdout(factor.index, params, "axis-level factor")
    factor = factor.astype(float)
    fwd = forward_sum(factor, horizon)
    # the frame stops at the last date any column has a truth; nothing later is handed on
    defined = fwd.notna().any(axis=1)
    if not defined.any():
        raise ValueError("no date has a forward truth")
    last = defined[defined].index[-1]
    fwd = fwd.loc[:last]
    check_score_dates(fwd.index, horizon, params)

    mode = CROSS_SECTIONAL if expression == "cross_sectional" else POOLED
    truth = _standardise_truth(fwd, mode)
    blend = truth
    if baseline:
        shuffled = block_shuffle_rows(truth, BASELINE_BLOCK, baseline_rng(seed))
        blend = shuffled.where(truth.notna()).fillna(0.0).where(truth.notna())

    rng = np.random.default_rng(seed)
    phi = (horizon - 1) / horizon
    raw = _ar1_noise(len(truth.index), truth.shape[1], phi, rng)
    noise = pd.DataFrame(raw, index=truth.index, columns=truth.columns).where(truth.notna())
    for column in truth.columns:
        y = blend[column]
        e = noise[column]
        ok = y.notna() & e.notna()
        yv, ev = y[ok].to_numpy(float), e[ok].to_numpy(float)
        if len(yv) < 3 or float(np.dot(yv - yv.mean(), yv - yv.mean())) <= 0.0:
            continue
        yc, ec = yv - yv.mean(), ev - ev.mean()
        resid = ec - yc * float(np.dot(ec, yc) / np.dot(yc, yc))
        sd = float(resid.std())
        target = float(yv.std())
        if sd > 0.0:
            noise.loc[ok[ok].index, column] = resid / sd * target
    noise = noise.where(blend.notna())
    score = ic * blend + np.sqrt(1.0 - ic * ic) * noise
    return AxisPlant(
        ic=float(ic),
        horizon=int(horizon),
        seed=int(seed),
        expression=expression,
        score=score,
        truth=truth,
        blend_truth=blend,
        baseline=bool(baseline),
    )


def realised_ic(plant: AxisPlant) -> dict[str, float]:
    """
    What the score carries about the REAL truth: `pooled` over every (date, column) cell;
    `by_column_mean`, the mean of each column's correlation over dates; and, for the
    cross-section, `cross_sectional_demeaned`, the mean over dates of the per-date correlation
    across columns after demeaning both (`signals._per_date_pearson`).
    """
    s, y = plant.score, plant.truth
    mask = s.notna() & y.notna()
    sv, yv = s.to_numpy()[mask.to_numpy()], y.to_numpy()[mask.to_numpy()]
    pooled = float(np.corrcoef(sv, yv)[0, 1]) if len(sv) > 2 else float("nan")
    per_column = []
    for column in s.columns:
        both = pd.concat([s[column], y[column]], axis=1).dropna()
        if len(both) > 2 and both.iloc[:, 0].std() > 0 and both.iloc[:, 1].std() > 0:
            per_column.append(float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]))
    out = {
        "pooled": pooled,
        "by_column_mean": float(np.mean(per_column)) if per_column else float("nan"),
    }
    if plant.expression == "cross_sectional":
        out["cross_sectional_demeaned"] = _per_date_pearson(s, y, demean=True, min_n=3)
    else:
        out["cross_sectional_demeaned"] = float("nan")
    return out
