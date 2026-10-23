"""
How a hypothesis's score becomes a view in return units (decisions/0059 A, B).

    v_k(t) = ic_prior * sigma_k(t) * z_k(t) / sqrt(h)

Three pure functions: the horizon `h`, the one-place standardisation `z`, and
the view scale. Nothing here reads data or calls the solver. Every number comes
from the `views` block of `params/constraints.yaml` or from the arguments.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from signal_lab.params import Params, ParamsError


def horizon_h(lo: int, hi: int, rule: str = "geometric_mean_rounded") -> int:
    """
    The horizon of a hypothesis's `horizon_weeks` range, in weeks.

    The geometric mean `sqrt(lo * hi)` rounded to the nearest week: 4-13 gives
    7, 8-26 gives 14, 13-52 gives 26.
    """
    if rule != "geometric_mean_rounded":
        raise ParamsError(f"unknown views.horizon_rule: {rule!r}")
    if lo < 1 or hi < lo:
        raise ValueError(f"a horizon range needs 1 <= lo <= hi, got {lo}-{hi}")
    return int(math.floor(math.sqrt(lo * hi) + 0.5))


def horizon_h_from_params(lo: int, hi: int, params: Params) -> int:
    """`horizon_h` with the rule named in `views.horizon_rule`."""
    return horizon_h(lo, hi, params.require("constraints.views.horizon_rule"))


def standardise(scores: pd.DataFrame, burn_in_weeks: int, winsorise_at: float) -> pd.DataFrame:
    """
    z-scores by column, built from knowledge-dated raw scores, same shape and index.

    The mean and the standard deviation (`ddof=1`) are expanding over the
    column's non-missing scores up to and including the date, so nothing later
    is read. `z` is clipped to `[-winsorise_at, +winsorise_at]`. It is 0.0
    until the column has `burn_in_weeks` non-missing scores, when the standard
    deviation is zero, and on a date where the score itself is missing.
    """
    count = scores.notna().cumsum()
    mean = scores.expanding().mean()
    std = scores.expanding().std(ddof=1)
    z = (scores - mean) / std
    z = z.clip(lower=-winsorise_at, upper=winsorise_at)
    live = (count >= burn_in_weeks) & scores.notna() & (std > 0)
    return z.where(live, 0.0).astype(float)


def standardise_from_params(scores: pd.DataFrame, params: Params) -> pd.DataFrame:
    """`standardise` with the burn-in and the clip of `views.standardisation`."""
    window = params.require("constraints.views.standardisation.window")
    if window != "expanding":
        raise ParamsError(f"unknown views.standardisation.window: {window!r}")
    return standardise(
        scores,
        int(params.require("constraints.views.standardisation.burn_in_weeks")),
        float(params.require("constraints.views.standardisation.winsorise_at")),
    )


def view_scale(
    z: pd.DataFrame,
    sigma: float | pd.Series | pd.DataFrame,
    h: int,
    ic_prior: float,
) -> pd.DataFrame:
    """
    `v = ic_prior * sigma * z / sqrt(h)`, elementwise.

    `sigma` is a scalar, a Series over `z`'s dates, or a DataFrame like `z`. A
    Series or DataFrame whose index (or columns) is not `z`'s is refused rather
    than broadcast.
    """
    if isinstance(h, bool) or not isinstance(h, (int, np.integer)) or h <= 0:
        raise ValueError(f"h must be a positive int, got {h!r}")
    if isinstance(sigma, pd.DataFrame):
        if not (sigma.index.equals(z.index) and sigma.columns.equals(z.columns)):
            raise ValueError("sigma does not align with z")
        scaled = z * sigma
    elif isinstance(sigma, pd.Series):
        if not sigma.index.equals(z.index):
            raise ValueError("sigma does not align with z's dates")
        scaled = z.mul(sigma, axis=0)
    else:
        scaled = z * float(sigma)
    return ic_prior * scaled / math.sqrt(h)


def view_scale_from_params(
    z: pd.DataFrame,
    sigma: float | pd.Series | pd.DataFrame,
    h: int,
    params: Params,
) -> pd.DataFrame:
    """`view_scale` with `views.ic_prior`."""
    return view_scale(z, sigma, h, float(params.require("constraints.views.ic_prior")))
