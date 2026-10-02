"""
The six weekly factors (decisions/0046 section 1): sign conventions, a missing series, the holdout.

Synthetic panels only -- the series are named like the vendor's, the numbers are invented.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel
from signal_lab.loaders.holdout import HoldoutViolation
from signal_lab.measurement.factors import (
    FACTOR_NAMES,
    FactorSeriesMissing,
    build_factors,
    credit_scale,
    weekly_levels,
)


def _panels(start="2004-01-05", end="2006-12-29", credit_level=100.0, credit_from=None):
    idx = pd.bdate_range(start, end)
    n = np.arange(len(idx))
    week = n / 5.0

    def level(base, step):  # a level that moves `step` per week
        return pd.Series(base + step * week, index=idx)

    returns = pd.DataFrame({"LD20TRUU": 0.0001, "BCOMTR": 0.002}, index=idx)
    bench = pd.DataFrame({"NDUEACWF": 0.001}, index=idx)
    credit = level(credit_level, 2.0 if credit_level >= 20 else 0.02)
    if credit_from is not None:
        credit[credit.index < credit_from] = np.nan
    fields = {
        "YLD_YTM_MID": pd.DataFrame({"GTII10": level(1.0, 0.05)}),  # +5bp a week (percent)
        "PX_LAST": pd.DataFrame(
            {
                "USGGBE10": level(2.0, 0.02),  # +2bp a week
                "LUACOAS": credit,
                "DXY": pd.Series(100.0 * 1.01**week, index=idx),  # +1% a week
            }
        ),
    }

    def panel(frame):
        return ReturnPanel(levels=frame, returns=frame, meta={})

    return panel(returns), panel(bench), AnalyticsPanel(fields=fields, meta={})


def test_each_factor_is_signed_as_its_name_reads(params):
    ff = build_factors(*_panels(), params=params)
    f = ff.frame.dropna()
    assert list(f.columns) == list(FACTOR_NAMES)
    assert (f["equity"] > 0).all()  # ACWI beat cash
    assert np.allclose(f["real_yield"], 0.0005)  # a yield that rose 5bp is +0.0005
    assert np.allclose(f["inflation"], 0.0002)
    assert np.allclose(f["credit"], 0.0002)  # a spread 2bp wider is positive
    assert np.allclose(f["dollar"], np.log(1.01), atol=1e-9)  # the dollar rose
    assert (f["commodities"] > 0).all()
    expect_equity = (1.001**5 - 1) - (1.0001**5 - 1)
    assert np.allclose(f["equity"].iloc[3:10], expect_equity, atol=1e-12)


def test_a_falling_yield_and_a_tightening_spread_are_negative(params):
    returns, bench, analytics = _panels()
    for field, col in (("YLD_YTM_MID", "GTII10"), ("PX_LAST", "LUACOAS")):
        analytics.fields[field][col] = -analytics.fields[field][col]
    f = build_factors(returns, bench, analytics, params=params).frame.dropna()
    assert (f["real_yield"] < 0).all()
    assert (f["credit"] < 0).all()


def test_the_credit_unit_is_read_not_assumed(params):
    bp = build_factors(*_panels(credit_level=100.0), params=params)
    pct = build_factors(*_panels(credit_level=1.0), params=params)
    assert bp.units["credit"].startswith("basis points")
    assert pct.units["credit"].startswith("percent")
    assert np.allclose(bp.frame["credit"].dropna(), 0.0002)
    assert np.allclose(pct.frame["credit"].dropna(), 0.0002)
    assert credit_scale(pd.Series([80.0, 120.0]))[0] == 1e-4
    assert credit_scale(pd.Series([0.8, 1.2]))[0] == 1e-2


@pytest.mark.parametrize(
    ("which", "column"),
    [("returns", "LD20TRUU"), ("returns", "BCOMTR"), ("bench", "NDUEACWF")],
)
def test_a_missing_return_series_raises(params, which, column):
    returns, bench, analytics = _panels()
    target = returns if which == "returns" else bench
    target.returns = target.returns.drop(columns=column)
    with pytest.raises(FactorSeriesMissing, match=column):
        build_factors(returns, bench, analytics, params=params)


@pytest.mark.parametrize(
    ("field", "column"),
    [
        ("YLD_YTM_MID", "GTII10"),
        ("PX_LAST", "USGGBE10"),
        ("PX_LAST", "LUACOAS"),
        ("PX_LAST", "DXY"),
    ],
)
def test_a_missing_analytics_series_raises(params, field, column):
    returns, bench, analytics = _panels()
    analytics.fields[field] = analytics.fields[field].drop(columns=column)
    with pytest.raises(FactorSeriesMissing, match=column):
        build_factors(returns, bench, analytics, params=params)


def test_the_common_sample_starts_when_the_last_factor_does(params):
    ff = build_factors(*_panels(credit_from=pd.Timestamp("2005-03-01")), params=params)
    assert ff.common_start >= pd.Timestamp("2005-03-01")
    assert ff.n_weeks == int(ff.frame.notna().all(axis=1).sum())
    assert ff.frame["equity"].first_valid_index() < ff.common_start


def test_weekly_levels_take_the_last_observation_in_the_week():
    idx = pd.bdate_range("2004-01-05", "2004-01-30")
    s = pd.Series(np.arange(len(idx), dtype=float), index=idx)
    dates = pd.DatetimeIndex(["2004-01-09", "2004-01-16", "2004-01-23"])
    out = weekly_levels(s, dates)
    assert list(out.values) == [4.0, 9.0, 14.0]


@pytest.mark.holdout
def test_a_panel_that_reaches_the_holdout_raises(params):
    with pytest.raises(HoldoutViolation):
        build_factors(*_panels(end="2020-03-27"), params=params)
