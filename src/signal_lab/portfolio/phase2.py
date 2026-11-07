"""
The phase-2 weight rule: views from a scores frame, an alpha from the views, one rebalance
(decisions/0059 C and F and its 2026-11-05 addendum, option (a); HANDOFF task 82).

The rule is signal-agnostic. It is *fed* a raw-scores frame (dates by groups) and never builds
one: it imports nothing from `signals/`, `audit/` or `loaders/` (other than `loaders.holdout`)
and reads no file. The chain, all existing pieces:

    z      = views.standardise_from_params(scores, params)            (once, expanding)
    h      = views.horizon_h_from_params(lo, hi, params)
    v      = views.view_scale_from_params(z, sigma, h, params)        (directional)
           = alpha.cross_sectional_views(z, sigma, ic_prior / sqrt(h)) (cross-sectional)
    alpha  = alpha.alpha_from_views / alpha_from_group_views at the date
    weights = RebalanceStep.step(date, alpha, drifted)

`expected_expression: both` is two tests (decisions/0059 item 2): one rule per test, so `both` is
refused here. `sigma` is an argument (decisions/0059 addendum item 1, read as keeping the rule
pure): a Series over the scores' dates, or a frame like the scores, computed by the caller with
`alpha.factor_sigma` or `alpha.relative_sigma`.

Holdout: a scores frame, a `sigma` or a `presence` with a date on or after HOLDOUT_START is
refused at construction, and `__call__` refuses such a date. The check is
`loaders.holdout.enforce_holdout`; there is no bypass.

Lookahead rows and the books (decisions/0059 D and E and the 2026-11-07 addendum, HANDOFF task
83): at every `__call__` the rule records what it consumed, returned by `parameter_usage()` in
`characteristics.exposures.USAGE_COLUMNS` for the caller to concatenate with the exposure map's
own `loadings` rows: `covariance`, `sigma_<axis>` and `zscore_<hypothesis_id>`. The rows show the
rule read nothing past `t` from its own inputs; they cannot check how the caller built `sigma`.
It also keeps, by date, the books the reports of `portfolio.reports` need (`self.books`); nothing
is written to disk, and `reports(factor_cov)` returns the frames.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from signal_lab.characteristics.exposures import _AXIS_OF, USAGE_COLUMNS
from signal_lab.loaders.holdout import enforce_holdout
from signal_lab.params import Params
from signal_lab.portfolio import alpha as alpha_mod
from signal_lab.portfolio import views as views_mod
from signal_lab.portfolio.rebalance import RebalanceStep

EXPRESSIONS = ("directional", "cross_sectional")
AXES = (*_AXIS_OF, "region")


class Phase2Rule(RebalanceStep):
    """
    The weight rule for one test of one hypothesis (decisions/0059 C, F; addendum of
    2026-11-05): `__call__(date, panel, drifted=None)` builds the alpha from the views at `date`
    and returns `self.step(date, alpha, drifted)`.

    `scores`: raw scores, dates by groups (the columns are what the views are one-per-column of:
    one column for a directional view with no `group_by`; group keys for `group_by`; view regions
    for the region axis; tickers for a cross-section with no `group_by`). `sigma`: a Series over
    the scores' dates or a frame like the scores. `exposures`: any object with `.at(date)`
    returning `ExposureMap.at`'s frame and, for the region axis, `.axis("region", date)`.
    `horizon`: the hypothesis's `(lo, hi)` `horizon_weeks`. `presence`: dates by instruments,
    boolean, required with `scope` (decisions/0057 rule 4's reach). `rebalance_settings` are
    `RebalanceStep`'s keyword arguments.
    """

    def __init__(
        self,
        universe: Any,
        costs: Any,
        params: Params,
        solver: str,
        *,
        scores: pd.DataFrame,
        sigma: pd.Series | pd.DataFrame,
        exposures: Any,
        axis: str,
        expression: str,
        horizon: tuple[int, int],
        group_by: tuple[str, ...] | list[str] | str | None = None,
        scope: dict[str, list[str]] | None = None,
        presence: pd.DataFrame | None = None,
        hypothesis_id: str | None = None,
        **rebalance_settings: Any,
    ):
        if expression == "both":
            raise ValueError(
                "expected_expression 'both' is two tests (decisions/0059 item 2): "
                "the caller builds one rule per test"
            )
        if expression not in EXPRESSIONS:
            raise ValueError(f"expression must be one of {EXPRESSIONS}, got {expression!r}")
        if axis not in AXES:
            raise ValueError(f"unknown axis {axis!r}; valid names are {AXES}")
        if not isinstance(scores, pd.DataFrame):
            raise ValueError("scores must be a frame, dates by groups")
        if axis == "region" and group_by:
            raise ValueError("the region axis has its own groups (region_cells); no group_by")
        if axis != "region" and expression == "directional" and not group_by:
            if scores.shape[1] != 1:
                raise ValueError(
                    "a directional rule with no group_by is one view: the scores frame has "
                    f"exactly one column, got {scores.shape[1]}"
                )
        if scope and presence is None:
            raise ValueError("a scope needs `presence` for decisions/0057 rule 4's reach check")

        enforce_holdout(scores.index, params, "phase-2 scores")
        enforce_holdout(sigma.index, params, "phase-2 sigma")
        if presence is not None:
            enforce_holdout(presence.index, params, "phase-2 presence")

        self.exposures = exposures
        self.hypothesis_id = hypothesis_id
        self.scores = scores
        self.sigma = sigma
        self.axis = axis
        self.expression = expression
        self.group_by = group_by
        self.scope = scope
        self.h = views_mod.horizon_h_from_params(int(horizon[0]), int(horizon[1]), params)
        self.z = views_mod.standardise_from_params(scores, params)
        if expression == "directional":
            self.views = views_mod.view_scale_from_params(self.z, sigma, self.h, params)
        else:
            ic_prior = float(params.require("constraints.views.ic_prior"))
            self.views = alpha_mod.cross_sectional_views(
                self.z, sigma, ic_prior / math.sqrt(self.h)
            )

        self.reach: int | None = None
        if scope:
            frame = exposures.at(presence.index[0])
            mask = alpha_mod.scope_mask(frame, scope)
            self.reach = alpha_mod.check_reach(expression, presence, mask)

        super().__init__(universe, costs, params, solver, **rebalance_settings)
        self._usage: list[dict[str, Any]] = []
        self.books: dict[pd.Timestamp, dict[str, Any]] = {}
        # True when the universe exposes its weekly panel, so the covariance's `fitted_through`
        # is the last period it read; False when the date itself stands in for it.
        self.covariance_fitted_from_panel = isinstance(
            getattr(self.u, "weekly", None), pd.DataFrame
        )

    def alpha_at(self, date: pd.Timestamp) -> pd.Series:
        """The alpha over the exposure frame's instruments at `date` (not yet on the holdable ids)."""
        date = pd.Timestamp(date)
        if date not in self.views.index:
            raise ValueError(f"no score for {date.date()}: the scores frame does not carry it")
        row = self.views.loc[date]
        frame = self.exposures.at(date)
        if self.axis == "region":
            return alpha_mod.alpha_from_views(
                frame,
                "region",
                row,
                self.scope,
                region_cells=self.exposures.axis("region", date),
            )
        if self.expression == "directional" and not self.group_by:
            return alpha_mod.alpha_from_views(frame, self.axis, float(row.iloc[0]), self.scope)
        groups = alpha_mod.groups_for(frame, self.axis, self.group_by, self.scope)
        return alpha_mod.alpha_from_group_views(frame, self.axis, row, groups, self.scope)

    def __call__(self, date: pd.Timestamp, _panel: Any = None, drifted: pd.Series | None = None):
        date = pd.Timestamp(date)
        enforce_holdout([date], self.params, "phase-2 rule date")
        cov = self.u.covariance(date, self.vol_halflife, self.vol_overlay)
        hold = [h for h in self.u.holdable if h in cov.ids]
        alpha = self.alpha_at(date).reindex(hold).fillna(0.0)
        weights = self.step(date, alpha, drifted)
        self._record(date, cov, weights)
        return weights

    # -- what the rule consumed, and the books the reports read ---------------------------

    def _covariance_fitted_through(self, date: pd.Timestamp) -> pd.Timestamp:
        weekly = getattr(self.u, "weekly", None)
        if isinstance(weekly, pd.DataFrame):
            seen = weekly.index[weekly.index <= date]
            if len(seen):
                return pd.Timestamp(seen[-1])
        return date

    def _record(self, date: pd.Timestamp, cov: Any, weights: pd.Series) -> None:
        def row(parameter: str, instrument: str, through: pd.Timestamp) -> None:
            self._usage.append(
                {
                    "instrument": instrument,
                    "parameter": parameter,
                    "store_week": pd.NaT,
                    "fitted_through": pd.Timestamp(through),
                    "used_on_date": date,
                }
            )

        row("covariance", "", self._covariance_fitted_through(date))
        sigma_parameter = f"sigma_{self.axis}"
        # the views at `date` were built from the sigma row at `date`
        if isinstance(self.sigma, pd.DataFrame):
            for column in self.sigma.columns:
                row(sigma_parameter, str(column), date)
        else:
            row(sigma_parameter, "", date)
        score_dates = self.scores.index[self.scores.index <= date]
        zscore_parameter = (
            "zscore" if self.hypothesis_id is None else f"zscore_{self.hypothesis_id}"
        )
        for column in self.scores.columns:
            row(zscore_parameter, str(column), score_dates[-1])

        self.books[date] = {
            "weights": weights,
            "cov": cov,
            "leg_weights": self.u.leg_weights,
            "frame": self.exposures.at(date),
            "views": self.views.loc[date],
        }

    def parameter_usage(self) -> pd.DataFrame:
        """What every `__call__` consumed, in `ExposureMap.usage()`'s columns, without duplicates."""
        if not self._usage:
            return pd.DataFrame(columns=list(USAGE_COLUMNS))
        out = pd.DataFrame(self._usage).drop_duplicates()
        return out[list(USAGE_COLUMNS)].reset_index(drop=True)

    def reports(self, factor_cov: Any) -> dict[str, Any]:
        """
        The reports of decisions/0059 E over the dates the rule solved: `active_exposure` (dates
        by the factors, axes and region columns), `tracking_variance` (dates by factors plus
        `residual`) and `transfer`. `factor_cov` is a factors-by-factors frame or a callable
        from date to one. Nothing is written anywhere.
        """
        from signal_lab.portfolio import reports as reports_mod

        return reports_mod.run_reports(self, factor_cov)
