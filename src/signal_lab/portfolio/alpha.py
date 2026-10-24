"""
From a view to an alpha: the factor volatility, the scope mask and the alpha map
(decisions/0059 A, 0057), for the directional form on the duration, real_nominal and
credit axes. The cash and region axes, and the cross-sectional form with its groups,
are not built here (HANDOFF task 72).

    alpha_i = X_i * v * m_i

Pure functions. Nothing here reads data or calls the solver.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.characteristics.exposures import (
    _AXIS_OF,
    LABEL_COLUMNS,
    UNBUILT_LABEL_AXES,
    LabelMapMissing,
)
from signal_lab.params import Params

# The factor each yield-like axis is a view on (decisions/0059 A, the table).
_FACTOR_OF = {
    "duration": "real_yield",
    "real_nominal": "inflation",
    "credit": "credit",
}
_DIRECTIONAL_AXES = tuple(_FACTOR_OF)
_COVARIANCE_WINDOW = "audit.covariance.window_periods"


def _refuse_unbuilt(axis: str) -> None:
    if axis in ("cash", "region"):
        raise NotImplementedError(f"the {axis} axis is built in HANDOFF task 72")
    if axis not in _FACTOR_OF:
        raise ValueError(f"unknown axis {axis!r}; valid names are {_DIRECTIONAL_AXES}")


def factor_sigma(
    factors: pd.DataFrame,
    axis: str,
    params: Params,
    overlay_scale: float | pd.Series = 1.0,
) -> pd.Series:
    """
    `sigma_k(t)`: the trailing standard deviation of the weekly changes of the factor `axis`
    is a view on, over the covariance's window (`audit.covariance.window_periods`), using
    the weeks up to and including `t` and nothing later; NaN until the window is full.

    `factors` is a weekly frame with the six factor columns (`FactorFrame.frame`), whose
    values are already weekly changes. The standard deviation divides by the window length,
    as the covariance's diagonal does (`ledoit_wolf`, `x.T @ x / n`).

    `overlay_scale` is the scalar of `decisions/0042` (`portfolio.covariance.volatility_scalar`,
    computed by the caller): the scalar overlay multiplies the covariance by `s**2`
    (`trailing_covariance`, `vol_overlay="scalar"`), so a standard deviation is multiplied by
    `s`. A Series must be indexed like `factors`.
    """
    _refuse_unbuilt(axis)
    column = _FACTOR_OF[axis]
    if column not in factors.columns:
        raise ValueError(f"the factor frame has no {column!r} column")
    window = int(params.require(_COVARIANCE_WINDOW))
    sigma = factors[column].astype(float).rolling(window, min_periods=window).std(ddof=0)
    if isinstance(overlay_scale, pd.Series):
        if not overlay_scale.index.equals(factors.index):
            raise ValueError("overlay_scale does not align with the factor frame's dates")
        sigma = sigma * overlay_scale
    else:
        sigma = sigma * float(overlay_scale)
    return sigma.rename(axis)


def scope_mask(frame: pd.DataFrame, scope: dict[str, list[str]] | None) -> pd.Series:
    """
    1.0 for an instrument inside the scope and 0.0 outside it (decisions/0057), over the
    frame's instruments. `scope` is None (everything is inside) or a mapping label -> allowed
    values. An instrument matches when, for every key, its label is one of the values; a
    blank label never matches. A key that is not a label column raises `ValueError`; an unbuilt
    label axis (`sector`, `style`) raises the exposure map's `LabelMapMissing`.
    """
    mask = pd.Series(1.0, index=frame.index)
    if not scope:
        return mask
    for key, allowed in scope.items():
        if key in UNBUILT_LABEL_AXES:
            raise LabelMapMissing(f"the {key} axis has no label map yet (decisions/0054 item 8)")
        if key not in LABEL_COLUMNS or key not in frame.columns:
            raise ValueError(f"{key!r} is not a label column of the frame; labels: {LABEL_COLUMNS}")
        labels = frame[key].astype(str)
        hit = labels.isin([str(v) for v in allowed]) & (labels != "")
        mask = mask.where(hit, 0.0)
    return mask


def alpha_from_views(
    frame: pd.DataFrame,
    axis: str,
    view: float,
    scope: dict[str, list[str]] | None = None,
) -> pd.Series:
    """
    `alpha_i = X_i * view * m_i` over the frame's instruments, `X_i` the cell on the axis
    (`ExposureMap.at`'s `axis_*` column) and `m_i` the scope mask. An instrument with a
    missing cell has no alpha: 0.0. `view` is a scalar for the date.
    """
    _refuse_unbuilt(axis)
    column = _AXIS_OF[axis]
    cell = frame[column].astype(float)
    mask = scope_mask(frame, scope)
    alpha = (cell * float(view) * mask).where(cell.notna(), 0.0)
    # 0 * inf / 0 * -x leaves signed zeros; the alpha of an excluded instrument is 0.0.
    alpha = alpha.where(mask > 0.0, 0.0) + 0.0
    return alpha.replace({np.nan: 0.0}).rename(axis)
