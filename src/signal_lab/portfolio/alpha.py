"""
From a view to an alpha: the factor volatility, the scope mask and the alpha map
(decisions/0059 A, 0057), for the directional form on the duration, real_nominal and
credit axes (HANDOFF task 71), and for the cash and region axes and the cross-sectional
form with demeaned standardised scores (HANDOFF task 72, decisions/0059 A and its
2026-10-23 addendum).

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
        raise NotImplementedError(
            f"the {axis} axis has no factor column: use relative_sigma; built in HANDOFF task 72"
        )
    if axis not in _FACTOR_OF:
        raise ValueError(f"unknown axis {axis!r}; valid names are {_DIRECTIONAL_AXES}")


def group_return(returns: pd.DataFrame, members: list[str]) -> pd.Series:
    """
    The equal-weighted mean of the `members` columns that hold a value at each week
    (NaN members skipped; NaN if none). `returns` is a weekly frame of instrument returns
    (Friday week close); each value uses its own week only.
    """
    if not members:
        raise ValueError("a group needs at least one member")
    missing = [m for m in members if m not in returns.columns]
    if missing:
        raise ValueError(f"returns has no column for {missing}")
    return returns[list(members)].astype(float).mean(axis=1, skipna=True)


def relative_factor(returns: pd.DataFrame, members: list[str], benchmark: str) -> pd.Series:
    """`group_return` less the benchmark column's return (the caller names the benchmark)."""
    if benchmark not in returns.columns:
        raise ValueError(f"returns has no {benchmark!r} column")
    return group_return(returns, members) - returns[benchmark].astype(float)


def relative_sigma(
    factor: pd.Series,
    params: Params,
    overlay_scale: float | pd.Series = 1.0,
) -> pd.Series:
    """
    The trailing standard deviation of one difference series (cash less the benchmark, or a
    region group less the benchmark), over the window and with the overlay of `factor_sigma`:
    `ddof=0`, NaN until the window is full, weeks up to and including `t` only.
    """
    window = int(params.require(_COVARIANCE_WINDOW))
    sigma = factor.astype(float).rolling(window, min_periods=window).std(ddof=0)
    if isinstance(overlay_scale, pd.Series):
        if not overlay_scale.index.equals(factor.index):
            raise ValueError("overlay_scale does not align with the factor's dates")
        return sigma * overlay_scale
    return sigma * float(overlay_scale)


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
    view: float | pd.Series,
    scope: dict[str, list[str]] | None = None,
    region_cells: pd.DataFrame | None = None,
) -> pd.Series:
    """
    `alpha_i = X_i * view * m_i` over the frame's instruments, `X_i` the cell on the axis
    (`ExposureMap.at`'s `axis_*` column) and `m_i` the scope mask. An instrument with a
    missing cell has no alpha: 0.0. `view` is a scalar for the date.

    The region axis: `view` is a Series indexed by the view regions (a scalar raises
    `ValueError`), `region_cells` is `ExposureMap.axis("region", date)` (one 0/1 column per
    region) and `alpha_i = sum_r cell_ir * v_r * m_i`; a missing cell or view adds nothing.
    """
    if axis == "region":
        return _region_alpha(frame, view, scope, region_cells)
    if axis != "cash":
        _refuse_unbuilt(axis)
    column = _AXIS_OF[axis]
    cell = frame[column].astype(float)
    mask = scope_mask(frame, scope)
    alpha = (cell * float(view) * mask).where(cell.notna(), 0.0)
    # 0 * inf / 0 * -x leaves signed zeros; the alpha of an excluded instrument is 0.0.
    alpha = alpha.where(mask > 0.0, 0.0) + 0.0
    return alpha.replace({np.nan: 0.0}).rename(axis)


def _region_alpha(frame, view, scope, region_cells) -> pd.Series:
    if not isinstance(view, pd.Series):
        raise ValueError("the region axis needs one view per region: a Series, not a scalar")
    if region_cells is None:
        raise ValueError("the region axis needs region_cells (ExposureMap.axis('region', date))")
    mask = scope_mask(frame, scope)
    total = pd.Series(0.0, index=frame.index)
    for region in region_cells.columns:
        v = view.get(region, np.nan)
        if pd.isna(v):
            continue
        cell = region_cells[region].astype(float).reindex(frame.index)
        total = total + cell.fillna(0.0) * float(v)
    alpha = (total * mask).where(mask > 0.0, 0.0) + 0.0
    return alpha.replace({np.nan: 0.0}).rename("region")


def cross_sectional_views(
    z: pd.DataFrame, sigma: pd.DataFrame | pd.Series, scale: float
) -> pd.DataFrame:
    """
    `v = scale * sigma * (z - mean_g z)` with the mean taken row-wise over the groups present
    at the date (decisions/0059 addendum of 2026-10-23). A group in its burn-in has `z = 0` and
    stays in the mean; a NaN group is left out of the mean and given the view 0.0; a row with
    one group present gives 0.0 (a single group cannot be ranked). `scale = ic_prior / sqrt(h)`.
    """
    if isinstance(sigma, pd.Series):
        if not sigma.index.equals(z.index):
            raise ValueError("sigma does not align with z's dates")
        sig = pd.DataFrame({c: sigma for c in z.columns})
    else:
        if not (sigma.index.equals(z.index) and sigma.columns.equals(z.columns)):
            raise ValueError("sigma does not align with z")
        sig = sigma
    zc = z.sub(z.mean(axis=1, skipna=True), axis=0)
    zc = zc.where(z.notna().sum(axis=1) > 1, 0.0)
    v = float(scale) * sig * zc
    return v.where(z.notna(), 0.0) + 0.0
