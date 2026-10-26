"""Task 71: the factor volatility, the scope mask and the alpha map (decisions/0059 A). Synthetic frames only."""

from __future__ import annotations

import copy
import dataclasses
import math

import numpy as np
import pandas as pd
import pytest

from signal_lab.characteristics.exposures import LabelMapMissing
from signal_lab.portfolio.alpha import (
    alpha_from_views,
    cross_sectional_views,
    factor_sigma,
    group_return,
    relative_factor,
    relative_sigma,
    scope_mask,
)
from signal_lab.portfolio.views import standardise, view_scale

FACTORS = ["equity", "real_yield", "inflation", "credit", "dollar", "commodities"]


def _with_window(params, window):
    audit = copy.deepcopy(params.audit)
    audit["covariance"]["window_periods"] = window
    return dataclasses.replace(params, audit=audit)


def _factors(n=12, seed=3):
    idx = pd.date_range("2005-01-07", periods=n, freq="W-FRI")
    rng = np.random.default_rng(seed)
    return pd.DataFrame(rng.normal(0.0, 0.01, (n, len(FACTORS))), index=idx, columns=FACTORS)


def _map(**cells):
    """A three-instrument frame like `ExposureMap.at` returns, the columns the task reads."""
    frame = pd.DataFrame(
        {
            "axis_duration": [7.0, -2.0, 0.5],
            "axis_real_nominal": [0.1, -0.3, 0.2],
            "axis_credit": [0.0, 1.5, -0.5],
            "curve": ["US", "EUR", ""],
            "rating": ["AAA", "BBB", ""],
            "market": ["US", "EUR", ""],
        },
        index=["UST", "EURBOND", "BLANK"],
    )
    for col, values in cells.items():
        frame[col] = values
    return frame


# --- factor_sigma ----------------------------------------------------------


def test_factor_sigma_equals_a_hand_computed_trailing_std(params):
    f = _factors()
    p = _with_window(params, 4)
    s = factor_sigma(f, "duration", p)
    x = f["real_yield"].to_numpy()
    for t in range(3, len(x)):
        window = x[t - 3 : t + 1]
        assert s.iloc[t] == pytest.approx(math.sqrt(np.mean((window - window.mean()) ** 2)))


def test_factor_sigma_is_nan_until_the_window_is_full(params):
    s = factor_sigma(_factors(), "credit", _with_window(params, 5))
    assert s.iloc[:4].isna().all()
    assert s.iloc[4:].notna().all()


def test_factor_sigma_uses_the_factor_of_each_axis(params):
    f = _factors()
    p = _with_window(params, 4)
    for axis, col in (
        ("duration", "real_yield"),
        ("real_nominal", "inflation"),
        ("credit", "credit"),
    ):
        want = f[col].rolling(4).std(ddof=0)
        assert np.allclose(factor_sigma(f, axis, p).to_numpy(), want.to_numpy(), equal_nan=True)


def test_factor_sigma_has_no_lookahead(params):
    f = _factors(20)
    p = _with_window(params, 4)
    base = factor_sigma(f.iloc[:12], "duration", p)
    changed = f.copy()
    changed.iloc[12:] = changed.iloc[12:] * 50.0
    longer = factor_sigma(changed, "duration", p).iloc[:12]
    assert base.equals(longer)
    assert factor_sigma(f, "duration", p).iloc[:12].equals(base)


def test_factor_sigma_reads_the_window_from_params(params):
    f = _factors()
    a = factor_sigma(f, "duration", _with_window(params, 4))
    b = factor_sigma(f, "duration", _with_window(params, 6))
    assert a.notna().sum() != b.notna().sum()
    assert not np.allclose(a.iloc[-1], b.iloc[-1])


def test_factor_sigma_default_window_is_the_covariances(params):
    n = int(params.require("audit.covariance.window_periods"))
    s = factor_sigma(_factors(n + 2), "duration", params)
    assert s.iloc[: n - 1].isna().all() and s.iloc[n - 1 :].notna().all()


def test_factor_sigma_overlay_multiplies_the_standard_deviation(params):
    f = _factors()
    p = _with_window(params, 4)
    base = factor_sigma(f, "duration", p)
    assert np.allclose(
        factor_sigma(f, "duration", p, 1.5).to_numpy(), (base * 1.5).to_numpy(), equal_nan=True
    )
    series = pd.Series(np.linspace(0.5, 2.0, len(f)), index=f.index)
    got = factor_sigma(f, "duration", p, series)
    assert np.allclose(got.to_numpy(), (base * series).to_numpy(), equal_nan=True)
    with pytest.raises(ValueError):
        factor_sigma(f, "duration", p, series.iloc[:-1])


@pytest.mark.parametrize("axis", ["cash", "region"])
def test_factor_sigma_refuses_the_axes_of_task_72(params, axis):
    with pytest.raises(NotImplementedError, match="72"):
        factor_sigma(_factors(), axis, params)


# --- scope_mask ------------------------------------------------------------


def test_scope_mask_none_is_all_ones():
    assert (scope_mask(_map(), None) == 1.0).all()


def test_scope_mask_keeps_only_the_matching_label_and_zeroes_blanks():
    m = scope_mask(_map(), {"curve": ["EUR"]})
    assert m.to_dict() == {"UST": 0.0, "EURBOND": 1.0, "BLANK": 0.0}
    both = scope_mask(_map(), {"curve": ["US", "EUR"], "rating": ["BBB"]})
    assert both.to_dict() == {"UST": 0.0, "EURBOND": 1.0, "BLANK": 0.0}


def test_scope_mask_unknown_key_raises():
    with pytest.raises(ValueError):
        scope_mask(_map(), {"colour": ["red"]})


@pytest.mark.parametrize("key", ["sector", "style"])
def test_scope_mask_refuses_the_unbuilt_label_axes(key):
    with pytest.raises(LabelMapMissing):
        scope_mask(_map(), {key: ["x"]})


# --- alpha_from_views ------------------------------------------------------


@pytest.mark.parametrize(
    "axis,col",
    [
        ("duration", "axis_duration"),
        ("real_nominal", "axis_real_nominal"),
        ("credit", "axis_credit"),
    ],
)
def test_a_zero_view_gives_exactly_zero_alpha(axis, col):
    a = alpha_from_views(_map(), axis, 0.0)
    assert (a == 0.0).all()
    assert not np.signbit(a.to_numpy()).any()


def test_a_positive_view_has_the_sign_of_the_cell():
    f = _map()
    a = alpha_from_views(f, "duration", 0.002)
    assert np.sign(a.to_numpy()).tolist() == np.sign(f["axis_duration"].to_numpy()).tolist()
    assert a["UST"] == pytest.approx(7.0 * 0.002)
    neg = alpha_from_views(f, "duration", -0.002)
    assert np.allclose(neg.to_numpy(), -a.to_numpy())


def test_out_of_scope_and_unlabelled_instruments_get_exactly_zero():
    a = alpha_from_views(_map(), "credit", 0.01, scope={"curve": ["EUR"]})
    assert a["UST"] == 0.0 and a["BLANK"] == 0.0
    assert a["EURBOND"] == pytest.approx(1.5 * 0.01)
    assert not np.signbit(a.to_numpy()).any()


def test_a_missing_cell_gets_zero():
    f = _map(axis_duration=[7.0, np.nan, 0.5])
    a = alpha_from_views(f, "duration", 0.01)
    assert a["EURBOND"] == 0.0
    assert a["UST"] == pytest.approx(0.07)


# Task 72 replaced the refusal of `cash` and `region` that stood here (revision note 1).

REGIONS = ["US", "Developed Europe", "Japan"]


def _cells():
    return pd.DataFrame(
        {"US": [1.0, 0.0, 0.0], "Developed Europe": [0.0, 1.0, 0.0], "Japan": [0.0, 0.0, 0.0]},
        index=["UST", "EURBOND", "BLANK"],
    )


def test_cash_alpha_is_the_cash_cell_times_the_view():
    f = _map(axis_cash=[0.0, 0.0, 1.0])
    a = alpha_from_views(f, "cash", 0.003)
    assert a.to_dict() == {"UST": 0.0, "EURBOND": 0.0, "BLANK": 0.003}
    z = alpha_from_views(f, "cash", 0.0)
    assert (z == 0.0).all() and not np.signbit(z.to_numpy()).any()


def test_region_alpha_has_the_sign_of_the_cell_in_that_region_only():
    view = pd.Series({"US": 0.01, "Developed Europe": -0.02, "Japan": 0.0})
    a = alpha_from_views(_map(), "region", view, region_cells=_cells())
    assert a["UST"] == pytest.approx(0.01)
    assert a["EURBOND"] == pytest.approx(-0.02)
    assert a["BLANK"] == 0.0 and not np.signbit(a["BLANK"])
    only_us = alpha_from_views(_map(), "region", pd.Series({"US": 0.01}), region_cells=_cells())
    assert only_us["UST"] == pytest.approx(0.01)
    assert only_us["EURBOND"] == 0.0


def test_a_zero_region_view_gives_exactly_zero_alpha():
    a = alpha_from_views(_map(), "region", pd.Series(0.0, index=REGIONS), region_cells=_cells())
    assert (a == 0.0).all() and not np.signbit(a.to_numpy()).any()


def test_a_scalar_region_view_raises():
    with pytest.raises(ValueError):
        alpha_from_views(_map(), "region", 0.01, region_cells=_cells())
    with pytest.raises(ValueError):
        alpha_from_views(_map(), "region", pd.Series(0.01, index=REGIONS))


# --- group_return, relative_factor, relative_sigma -------------------------


def _returns():
    idx = pd.date_range("2005-01-07", periods=8, freq="W-FRI")
    rng = np.random.default_rng(9)
    r = pd.DataFrame(rng.normal(0.0, 0.01, (8, 3)), index=idx, columns=["A", "B", "BM"])
    r.loc[idx[2], "B"] = np.nan
    return r


def test_group_return_skips_nan_members_and_is_nan_if_none():
    r = _returns()
    g = group_return(r, ["A", "B"])
    assert g.iloc[2] == pytest.approx(r["A"].iloc[2])
    assert g.iloc[3] == pytest.approx((r["A"].iloc[3] + r["B"].iloc[3]) / 2)
    r.loc[r.index[4], ["A", "B"]] = np.nan
    assert np.isnan(group_return(r, ["A", "B"]).iloc[4])


def test_relative_factor_is_the_group_less_the_benchmark():
    r = _returns()
    rel = relative_factor(r, ["A", "B"], "BM")
    assert rel.iloc[3] == pytest.approx((r["A"].iloc[3] + r["B"].iloc[3]) / 2 - r["BM"].iloc[3])


def test_group_return_has_no_lookahead():
    r = _returns()
    base = relative_factor(r.iloc[:5], ["A", "B"], "BM")
    changed = r.copy()
    changed.iloc[5:] = changed.iloc[5:] * 50.0
    assert relative_factor(changed, ["A", "B"], "BM").iloc[:5].equals(base)


def test_relative_sigma_equals_a_hand_computed_trailing_std(params):
    rel = relative_factor(_returns(), ["A", "BM"], "BM")
    s = relative_sigma(rel, _with_window(params, 4))
    x = rel.to_numpy()
    assert s.iloc[:3].isna().all()
    for t in range(3, len(x)):
        w = x[t - 3 : t + 1]
        assert s.iloc[t] == pytest.approx(math.sqrt(np.mean((w - w.mean()) ** 2)))


def test_relative_sigma_overlay_multiplies_it(params):
    rel = relative_factor(_returns(), ["A"], "BM")
    p = _with_window(params, 4)
    base = relative_sigma(rel, p)
    assert np.allclose(
        relative_sigma(rel, p, 2.0).to_numpy(), (base * 2.0).to_numpy(), equal_nan=True
    )


# --- cross_sectional_views -------------------------------------------------


def _z():
    idx = pd.date_range("2005-01-07", periods=4, freq="W-FRI")
    return pd.DataFrame(
        {"g1": [1.0, 2.0, 0.0, 0.5], "g2": [-1.0, 0.0, 0.0, 1.5], "g3": [3.0, np.nan, 0.0, np.nan]},
        index=idx,
    )


def test_demeaned_scores_sum_to_zero_across_present_groups():
    z = _z()
    sig = pd.DataFrame(1.0, index=z.index, columns=z.columns)
    v = cross_sectional_views(z, sig, 1.0)
    present = z.notna()
    assert np.allclose(v.where(present).sum(axis=1).iloc[[0, 1, 2]], 0.0)


def test_equal_sigma_views_sum_to_zero_and_unequal_do_not():
    z = _z().iloc[[0]]
    equal = pd.DataFrame(0.02, index=z.index, columns=z.columns)
    assert cross_sectional_views(z, equal, 0.5).sum(axis=1).iloc[0] == pytest.approx(0.0, abs=1e-15)
    unequal = pd.DataFrame([[0.01, 0.02, 0.05]], index=z.index, columns=z.columns)
    assert abs(cross_sectional_views(z, unequal, 0.5).sum(axis=1).iloc[0]) > 1e-6


def test_a_burn_in_group_stays_in_the_mean():
    z = _z().iloc[[2]].copy()
    z["g1"] = 3.0
    sig = pd.DataFrame(1.0, index=z.index, columns=z.columns)
    v = cross_sectional_views(z, sig, 1.0)
    assert v["g1"].iloc[0] == pytest.approx(2.0)
    assert v["g2"].iloc[0] == pytest.approx(-1.0)


def test_a_row_with_one_group_gives_zero():
    z = _z()
    sig = pd.DataFrame(1.0, index=z.index, columns=z.columns)
    v = cross_sectional_views(z, sig, 1.0)
    one = pd.DataFrame({"g1": [2.0], "g2": [np.nan]}, index=z.index[:1])
    assert (cross_sectional_views(one, one.fillna(1.0), 1.0).iloc[0] == 0.0).all()
    assert v["g3"].iloc[1] == 0.0


def test_swapping_two_groups_swaps_their_views():
    z = _z().iloc[[0]]
    sig = pd.DataFrame(0.02, index=z.index, columns=z.columns)
    v = cross_sectional_views(z, sig, 0.5)
    swapped = z.copy()
    swapped["g1"], swapped["g2"] = z["g2"], z["g1"]
    sw = cross_sectional_views(swapped, sig, 0.5)
    assert sw["g2"].iloc[0] == pytest.approx(v["g1"].iloc[0])
    assert sw["g1"].iloc[0] == pytest.approx(v["g2"].iloc[0])


# --- through views.py ------------------------------------------------------


def test_scores_to_alpha_through_views_equals_the_product_by_hand(params):
    p = _with_window(params, 10)
    n = 80
    rng = np.random.default_rng(11)
    f = _factors(n, seed=5)
    scores = pd.DataFrame({"duration": rng.normal(size=n)}, index=f.index)
    z = standardise(scores, 52, 3.0)
    sigma = factor_sigma(f, "duration", p, 1.1)
    h, ic = 7, 0.05
    v = view_scale(z, sigma.fillna(0.0), h, ic)
    t = f.index[-1]
    alpha = alpha_from_views(
        _map(), "duration", float(v.loc[t, "duration"]), scope={"curve": ["US", "EUR"]}
    )

    x = scores["duration"].to_numpy()
    zt = float(np.clip((x[-1] - x.mean()) / x.std(ddof=1), -3.0, 3.0))
    w = f["real_yield"].to_numpy()[-10:]
    sig = 1.1 * math.sqrt(np.mean((w - w.mean()) ** 2))
    view = ic * sig * zt / math.sqrt(h)
    want = {"UST": 7.0 * view, "EURBOND": -2.0 * view, "BLANK": 0.0}
    for name, value in want.items():
        assert alpha[name] == pytest.approx(value, rel=1e-12, abs=1e-18)
