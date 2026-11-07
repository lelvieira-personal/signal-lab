"""
The reports of decisions/0059 E, as plain functions (2026-11-07 addendum items 2 and 3; HANDOFF
task 83). Each takes the books the phase-2 rule solved and returns a pandas object; none reads or
writes a file. Where the reports go in a real run is decided with the first signal module (M7).

* `benchmark_holdings`: the benchmark's tracking portfolio on the holdables, through the legs'
  replicating weights (`covariance.embed_benchmark_legs`), because the legs have no row in the
  exposure store.
* `active_exposure`: `sum_i (w_i - b_i) X_i` on the factors, the four axes and the region
  reporting columns.
* `tracking_variance_shares`: each factor's Euler share of ex-ante active variance, and the
  residual.
* `transfer`: the realised active exposure on the target axis against the view. Directional: the
  correlation across dates. Cross-sectional: at each date the correlation across groups, then the
  mean over dates. This is Cowork's definition (addendum item 3), one function to change.

`portfolio` does not import `audit`.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from signal_lab.characteristics.exposures import _AXIS_OF, AXIS_COLUMNS, REGION_COLUMNS
from signal_lab.portfolio import alpha as alpha_mod

MIN_POINTS = 3


def benchmark_holdings(cov: Any, leg_weights: pd.Series) -> pd.Series:
    """`sum_leg leg_weight * tracking weights of the leg`, a Series over the holdables."""
    out: pd.Series | None = None
    for leg, weight in leg_weights.items():
        piece = float(weight) * cov.legs[leg]["weights"]
        out = piece if out is None else out.add(piece, fill_value=0.0)
    if out is None:
        raise ValueError("the benchmark has no legs")
    return out


def _active_weights(weights: pd.Series, bench: pd.Series) -> pd.Series:
    index = weights.index.union(bench.index)
    return weights.reindex(index).fillna(0.0) - bench.reindex(index).fillna(0.0)


def report_columns(factors: list[str]) -> list[str]:
    return [*factors, *AXIS_COLUMNS, *REGION_COLUMNS]


def active_exposure(
    weights: pd.Series, bench: pd.Series, frame: pd.DataFrame, factors: list[str]
) -> pd.Series:
    """
    `sum_i (w_i - b_i) * X_i` over the factors, `AXIS_COLUMNS` and `REGION_COLUMNS`. An instrument
    with no row in `frame` contributes nothing, as does a missing cell.
    """
    active = _active_weights(weights, bench)
    cells = frame.reindex(active.index)[report_columns(list(factors))].astype(float).fillna(0.0)
    return pd.Series(active.to_numpy() @ cells.to_numpy(), index=cells.columns)


def unrowed_with_weight(weights: pd.Series, bench: pd.Series, frame: pd.DataFrame) -> int:
    """How many instruments carry a weight (book or benchmark) yet have no row in `frame`."""
    active = _active_weights(weights, bench)
    carried = active[active != 0.0].index
    return int((~carried.isin(frame.index)).sum())


def tracking_variance_shares(
    weights: pd.Series,
    cov: Any,
    leg_weights: pd.Series,
    active_factors: pd.Series,
    factor_cov: pd.DataFrame,
) -> pd.Series:
    """
    Total active variance `a' Sigma a` from `cov.matrix` (`a`: the weights on the holdables, less
    `leg_weights` on the legs); each factor's Euler share `x_k (F x)_k / total`; `residual` is one
    minus their sum. A zero total is refused.
    """
    matrix = cov.matrix
    a = pd.Series(0.0, index=matrix.index)
    held = weights.index.intersection(matrix.index)
    a[held] = weights[held].astype(float)
    a[leg_weights.index] = a[leg_weights.index] - leg_weights.astype(float)
    total = float(a.to_numpy() @ matrix.to_numpy(dtype=float) @ a.to_numpy())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError(f"the total active variance is {total}: shares are undefined")
    x = active_factors.reindex(factor_cov.index).astype(float).to_numpy()
    if np.isnan(x).any():
        raise ValueError("active_factors does not cover the factor covariance's factors")
    shares = x * (factor_cov.to_numpy(dtype=float) @ x) / total
    out = pd.Series(shares, index=factor_cov.index)
    out["residual"] = 1.0 - float(shares.sum())
    return out


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < MIN_POINTS:
        return float("nan")
    if np.std(x) == 0.0 or np.std(y) == 0.0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def transfer(
    active_axis: pd.Series | pd.DataFrame,
    views: pd.Series | pd.DataFrame,
    expression: str,
) -> float:
    """
    Directional: `active_axis` and `views` are Series by date; the Pearson correlation across
    dates. Cross-sectional: frames, dates by groups; at each date the correlation across groups,
    then the mean over the dates that have one. Fewer than three points: `nan`.
    """
    if expression == "directional":
        both = pd.concat([active_axis, views], axis=1, keys=["a", "v"]).dropna()
        return _pearson(both["a"].to_numpy(float), both["v"].to_numpy(float))
    if expression == "cross_sectional":
        scores = []
        for date in active_axis.index.intersection(views.index):
            both = pd.concat([active_axis.loc[date], views.loc[date]], axis=1).dropna()
            scores.append(
                _pearson(both.iloc[:, 0].to_numpy(float), both.iloc[:, 1].to_numpy(float))
            )
        scores = [s for s in scores if not np.isnan(s)]
        return float(np.mean(scores)) if scores else float("nan")
    raise ValueError(f"expression must be 'directional' or 'cross_sectional', got {expression!r}")


def _factor_cov_at(factor_cov: Any, date: pd.Timestamp) -> pd.DataFrame:
    return factor_cov(date) if callable(factor_cov) else factor_cov


def run_reports(rule: Any, factor_cov: Any) -> dict[str, Any]:
    """`Phase2Rule.reports`: the three reports over the dates `rule` solved."""
    dates = sorted(rule.books)
    if not dates:
        raise ValueError("the rule has solved no date")
    factors = list(_factor_cov_at(factor_cov, dates[0]).columns)
    exposure_rows: dict[pd.Timestamp, pd.Series] = {}
    variance_rows: dict[pd.Timestamp, pd.Series] = {}
    axis_rows: dict[pd.Timestamp, Any] = {}
    view_rows: dict[pd.Timestamp, pd.Series] = {}
    for date in dates:
        book = rule.books[date]
        bench = benchmark_holdings(book["cov"], book["leg_weights"])
        active = active_exposure(book["weights"], bench, book["frame"], factors)
        exposure_rows[date] = active
        variance_rows[date] = tracking_variance_shares(
            book["weights"],
            book["cov"],
            book["leg_weights"],
            active[factors],
            _factor_cov_at(factor_cov, date),
        )
        diff = _active_weights(book["weights"], bench)
        axis_rows[date] = _target_active(rule, date, diff, book["frame"])
        view_rows[date] = book["views"]

    out = {
        "active_exposure": pd.DataFrame(exposure_rows).T,
        "tracking_variance": pd.DataFrame(variance_rows).T,
    }
    views = pd.DataFrame(view_rows).T
    if rule.expression == "directional":
        if views.shape[1] != 1:
            # several views under a directional expression: no transfer is defined for it
            out["transfer"] = float("nan")
        else:
            out["transfer"] = transfer(
                pd.Series(axis_rows, dtype=float), views.iloc[:, 0], "directional"
            )
    else:
        out["transfer"] = transfer(pd.DataFrame(axis_rows).T, views, "cross_sectional")
    return out


def _target_active(rule: Any, date: pd.Timestamp, diff: pd.Series, frame: pd.DataFrame) -> Any:
    """The active exposure on the target axis: a float (directional) or a Series by group."""
    if rule.axis == "region":
        cells = rule.exposures.axis("region", date).reindex(diff.index).fillna(0.0)
        return pd.Series(diff.to_numpy() @ cells.to_numpy(), index=cells.columns)
    column = _AXIS_OF[rule.axis]
    x = frame[column].reindex(diff.index).astype(float).fillna(0.0)
    if rule.expression == "directional":
        return float((diff * x).sum())
    groups = alpha_mod.groups_for(frame, rule.axis, rule.group_by, rule.scope)
    contribution = (diff * x).reindex(groups.index).fillna(0.0)
    return contribution.groupby(groups).sum()
