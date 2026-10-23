"""Task 70: horizon, standardisation and view scale (decisions/0059 A and B). Synthetic frames only."""

from __future__ import annotations

import copy
import dataclasses
import math

import numpy as np
import pandas as pd
import pytest

from signal_lab.params import ParamsError
from signal_lab.portfolio.views import (
    horizon_h,
    horizon_h_from_params,
    standardise,
    standardise_from_params,
    view_scale,
    view_scale_from_params,
)


def _with_views(params, **changes):
    constraints = copy.deepcopy(params.constraints)
    for dotted, value in changes.items():
        node = constraints["views"]
        parts = dotted.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
    return dataclasses.replace(params, constraints=constraints)


def _frame(values, columns=("a",)):
    idx = pd.date_range("2005-01-07", periods=len(values), freq="W-FRI")
    return pd.DataFrame(values, index=idx, columns=list(columns))


# --- horizon_h --------------------------------------------------------------


@pytest.mark.parametrize("lo, hi, expected", [(4, 13, 7), (8, 26, 14), (13, 52, 26), (5, 5, 5)])
def test_horizon_h_is_the_rounded_geometric_mean(lo, hi, expected):
    assert horizon_h(lo, hi) == expected


@pytest.mark.parametrize("lo, hi", [(0, 5), (-1, 5), (6, 5)])
def test_horizon_h_refuses_a_bad_range(lo, hi):
    with pytest.raises(ValueError):
        horizon_h(lo, hi)


def test_horizon_h_refuses_an_unknown_rule():
    with pytest.raises(ParamsError):
        horizon_h(4, 13, rule="arithmetic")


def test_horizon_h_from_params_reads_the_rule(params):
    assert horizon_h_from_params(4, 13, params) == 7
    with pytest.raises(ParamsError):
        horizon_h_from_params(4, 13, _with_views(params, horizon_rule="other"))


# --- standardise ------------------------------------------------------------


def test_standardise_matches_a_hand_computed_expanding_z():
    s = _frame([1.0, 3.0, 6.0, 2.0, 4.0])
    z = standardise(s, burn_in_weeks=3, winsorise_at=10.0)["a"].to_numpy()
    x = s["a"].to_numpy()
    assert z[0] == 0.0 and z[1] == 0.0
    for t in (2, 3, 4):
        expect = (x[t] - x[: t + 1].mean()) / x[: t + 1].std(ddof=1)
        assert z[t] == pytest.approx(expect, abs=1e-12)
        assert z[t] != 0.0


def test_standardise_clips_a_spike_at_exactly_the_winsorisation():
    s = _frame([0.0, 1.0, -1.0, 0.5, -0.5, 0.2, -0.2, 1000.0])
    z = standardise(s, burn_in_weeks=3, winsorise_at=2.0)["a"]
    assert z.iloc[-1] == 2.0
    assert (z.abs() <= 2.0).all()
    z_neg = standardise(-s, burn_in_weeks=3, winsorise_at=2.0)["a"]
    assert z_neg.iloc[-1] == -2.0


def test_standardise_a_constant_column_is_zero_not_nan():
    z = standardise(_frame([2.0] * 6), burn_in_weeks=3, winsorise_at=3.0)
    assert not z.isna().any().any()
    assert (z == 0.0).all().all()


def test_standardise_a_late_column_burns_in_on_its_own_count():
    early = [1.0, 2.0, 4.0, 3.0, 5.0, 2.0]
    late = [np.nan, np.nan, np.nan, 1.0, 3.0, 6.0]
    z = standardise(_frame(list(zip(early, late, strict=True)), ("e", "l")), 3, 10.0)
    assert z["e"].iloc[2] != 0.0
    assert z["l"].iloc[3] == 0.0 and z["l"].iloc[4] == 0.0
    assert z["l"].iloc[5] != 0.0


def test_standardise_a_missing_score_carries_zero():
    s = _frame([1.0, 2.0, 4.0, np.nan, 3.0, 5.0])
    z = standardise(s, 3, 10.0)["a"]
    assert z.iloc[3] == 0.0
    assert z.iloc[4] != 0.0


def test_standardise_has_the_input_shape_and_index():
    s = _frame(np.random.default_rng(0).normal(size=(30, 3)), ("a", "b", "c"))
    z = standardise(s, 5, 3.0)
    assert z.index.equals(s.index) and list(z.columns) == list(s.columns)


def test_standardise_has_no_lookahead():
    rng = np.random.default_rng(1)
    s = _frame(rng.normal(size=(80, 2)), ("a", "b"))
    base = standardise(s, 10, 3.0)
    longer = pd.concat(
        [
            s,
            _frame(rng.normal(size=(20, 2)), ("a", "b")).set_axis(
                pd.date_range(s.index[-1] + pd.Timedelta(days=7), periods=20, freq="W-FRI")
            ),
        ]
    )
    extended = standardise(longer, 10, 3.0).iloc[: len(s)]
    pd.testing.assert_frame_equal(base, extended, check_exact=True)

    changed = s.copy()
    changed.iloc[-1] = 1e6
    altered = standardise(changed, 10, 3.0)
    pd.testing.assert_frame_equal(base.iloc[:-1], altered.iloc[:-1], check_exact=True)


def test_standardise_from_params_uses_the_live_burn_in_and_clip(params):
    rng = np.random.default_rng(2)
    s = _frame(rng.normal(size=(70, 1)))
    s.iloc[-1] = 1e6
    z = standardise_from_params(s, params)["a"]
    assert (z.iloc[:51] == 0.0).all()
    assert z.iloc[51] != 0.0
    assert z.iloc[-1] == 3.0


def test_standardise_from_params_is_not_hard_coded(params):
    rng = np.random.default_rng(3)
    s = _frame(rng.normal(size=(70, 1)))
    s.iloc[-1] = 1e6
    changed = standardise_from_params(
        s,
        _with_views(
            params, **{"standardisation.burn_in_weeks": 10, "standardisation.winsorise_at": 1.5}
        ),
    )["a"]
    assert (changed.iloc[:9] == 0.0).all()
    assert changed.iloc[9] != 0.0
    assert changed.iloc[-1] == 1.5


def test_standardise_from_params_refuses_another_window(params):
    with pytest.raises(ParamsError):
        standardise_from_params(
            _frame([1.0, 2.0, 3.0]),
            _with_views(params, **{"standardisation.window": "rolling"}),
        )


# --- view_scale -------------------------------------------------------------


def test_view_scale_equals_a_hand_calculation():
    z = _frame([[1.0, -2.0], [0.5, 3.0]], ("a", "b"))
    sigma = pd.DataFrame([[0.1, 0.2], [0.3, 0.4]], index=z.index, columns=z.columns)
    v = view_scale(z, sigma, 4, 0.05)
    expect = np.array(
        [[0.05 * 0.1 * 1.0, 0.05 * 0.2 * -2.0], [0.05 * 0.3 * 0.5, 0.05 * 0.4 * 3.0]]
    ) / math.sqrt(4)
    np.testing.assert_allclose(v.to_numpy(), expect, rtol=1e-14)


def test_view_scale_takes_a_scalar_and_a_series():
    z = _frame([[1.0, -2.0], [0.5, 3.0]], ("a", "b"))
    by_scalar = view_scale(z, 0.2, 9, 0.05)
    by_series = view_scale(z, pd.Series([0.2, 0.2], index=z.index), 9, 0.05)
    pd.testing.assert_frame_equal(by_scalar, by_series)


def test_view_scale_ic_prior_zero_is_exactly_zero():
    z = _frame([[1.0, -2.0], [0.5, 3.0]], ("a", "b"))
    assert (view_scale(z, 0.3, 7, 0.0) == 0.0).all().all()


def test_view_scale_refuses_a_misaligned_sigma():
    z = _frame([[1.0], [2.0]])
    with pytest.raises(ValueError):
        view_scale(z, pd.Series([0.1, 0.1], index=z.index + pd.Timedelta(days=1)), 4, 0.05)
    with pytest.raises(ValueError):
        view_scale(z, pd.DataFrame({"x": [0.1, 0.1]}, index=z.index), 4, 0.05)


@pytest.mark.parametrize("h", [0, -3, 2.5, True])
def test_view_scale_refuses_a_bad_h(h):
    with pytest.raises(ValueError):
        view_scale(_frame([[1.0]]), 0.1, h, 0.05)


def test_view_scale_from_params_reads_ic_prior(params):
    z = _frame([[1.0], [2.0]])
    live = view_scale_from_params(z, 0.2, 4, params)
    pd.testing.assert_frame_equal(live, view_scale(z, 0.2, 4, 0.05))
    zero = view_scale_from_params(z, 0.2, 4, _with_views(params, ic_prior=0.0))
    assert (zero == 0.0).all().all()
