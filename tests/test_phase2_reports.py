"""
`Phase2Rule.parameter_usage()` and `portfolio.reports` (HANDOFF task 83, decisions/0059 D, E, F and
its 2026-11-07 addendum): checks F5 (the lookahead veto on the rule's rows) and F7 (the two tables
of E come back with one row per rebalance), and the reports' own arithmetic.

Synthetic scores, a hand-built exposure stub and hand-built factor covariances over the synthetic
universe of `test_phase2_rule`. No vendor data, no store, nothing on or after 2020-01-01.
"""

# ruff: noqa: F811  (the fixtures of test_phase2_rule are imported by name, as test_japan_report does)
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_phase2_rule import (  # noqa: E402, F401
    DURATION,
    StubExposures,
    T,
    dates,
    make_rule,
    noise,
    settings,
    small_universe,
)

from signal_lab.characteristics.exposures import (  # noqa: E402
    AXIS_COLUMNS,
    REGION_COLUMNS,
    USAGE_COLUMNS,
)
from signal_lab.harness.run_context import RunContext  # noqa: E402
from signal_lab.portfolio import reports  # noqa: E402
from vetoes.rules import veto_lookahead  # noqa: E402

FACTORS = ["real_yield", "inflation", "credit"]
HYPOTHESIS = "H-2026-0099"


class ReportStub(StubExposures):
    """The stub of `test_phase2_rule` plus the factor and region reporting columns."""

    def __init__(self, ids, cash):
        super().__init__(ids, cash)
        n = len(self.frame)
        for k, name in enumerate(FACTORS):
            self.frame[name] = np.linspace(-1.0 + 0.3 * k, 1.0 - 0.2 * k, n)
        regions = self.frame["region"]
        for col, region in zip(
            REGION_COLUMNS,
            ["US", "Developed Europe", "Japan", "APAC ex-Japan", "Canada", "EM", "Global"],
            strict=True,
        ):
            self.frame[col] = (regions == region).astype(float)


@pytest.fixture(scope="module")
def rstub(small_universe):
    universe, _ = small_universe
    return ReportStub(universe.holdable, set(universe.cash))


FACTOR_COV = pd.DataFrame(
    [[0.04, 0.01, 0.005], [0.01, 0.03, 0.002], [0.005, 0.002, 0.05]],
    index=FACTORS,
    columns=FACTORS,
)


def run_rule(small_universe, settings, rstub, dates, n=4, **kw):
    kw.setdefault("scores", noise(dates, ["d"], last={"d": 4.0}))
    kw.setdefault("hypothesis_id", HYPOTHESIS)
    rule = make_rule(small_universe, settings, rstub, dates, **{**DURATION, **kw})
    drifted = None
    for date in dates[T : T + n]:
        drifted = rule(date, None, drifted=drifted)
    return rule


def loadings_rows(rstub, dates):
    """The exposure map's own rows, in the same columns, honest: fitted on the date used."""
    rows = [
        pd.DataFrame(
            {
                "instrument": list(rstub.frame.index.astype(str)),
                "parameter": "loadings",
                "store_week": date,
                "fitted_through": date,
                "used_on_date": date,
            }
        )
        for date in dates
    ]
    return pd.concat(rows, ignore_index=True)


def empty_observations():
    """
    One honest observation, known before it is used. The veto fails closed on an EMPTY
    `observation_usage` (`ctx.require` treats it as absent), so a frame with no rows cannot be
    handed in; `tests/test_exposures.py` does the same. Only the parameter rows are under test.
    """
    return pd.DataFrame(
        {
            "series_id": ["x"],
            "period_end": [pd.Timestamp("2010-01-31")],
            "knowledge_date": [pd.Timestamp("2010-03-01")],
            "used_on_date": [pd.Timestamp("2010-03-05")],
        }
    )


# --- parameter_usage ------------------------------------------------------------


def test_parameter_usage_before_any_call_is_an_empty_frame_in_the_usage_columns(
    small_universe, settings, rstub, dates
):
    rule = make_rule(small_universe, settings, rstub, dates, scores=noise(dates, ["d"]), **DURATION)
    usage = rule.parameter_usage()
    assert usage.empty
    assert list(usage.columns) == list(USAGE_COLUMNS)


# --- F5: the lookahead veto on the rule's rows -----------------------------------


def test_f5_the_three_kinds_are_present_and_named_for_the_hypothesis(
    small_universe, settings, rstub, dates
):
    rule = run_rule(small_universe, settings, rstub, dates)
    usage = rule.parameter_usage()
    assert list(usage.columns) == list(USAGE_COLUMNS)
    assert set(usage["parameter"]) == {"covariance", "sigma_duration", f"zscore_{HYPOTHESIS}"}
    assert len(usage) == 3 * 4  # one row per kind per rebalance, a directional rule, one column
    bare = run_rule(small_universe, settings, rstub, dates, n=1, hypothesis_id=None)
    assert "zscore" in set(bare.parameter_usage()["parameter"])


def test_f5_an_honest_rule_passes_the_lookahead_veto(
    small_universe, settings, rstub, dates, params
):
    rule = run_rule(small_universe, settings, rstub, dates)
    solved = dates[T : T + 4]
    usage = pd.concat([rule.parameter_usage(), loadings_rows(rstub, solved)], ignore_index=True)
    ctx = RunContext(run_id="R", observation_usage=empty_observations(), parameter_usage=usage)
    verdict = veto_lookahead(ctx, params)
    assert verdict.passed, verdict.detail
    # the rule's own inputs were read no later than the date they were used
    own = rule.parameter_usage()
    assert (own["fitted_through"] <= own["used_on_date"]).all()


@pytest.mark.parametrize("kind", ["covariance", "sigma_duration", f"zscore_{HYPOTHESIS}"])
def test_f5_one_row_fitted_a_week_late_fails_the_lookahead_veto(
    small_universe, settings, rstub, dates, params, kind
):
    rule = run_rule(small_universe, settings, rstub, dates)
    solved = dates[T : T + 4]
    usage = pd.concat([rule.parameter_usage(), loadings_rows(rstub, solved)], ignore_index=True)
    row = usage.index[usage["parameter"] == kind][0]
    usage.loc[row, "fitted_through"] = usage.loc[row, "used_on_date"] + pd.Timedelta(days=7)
    ctx = RunContext(run_id="R", observation_usage=empty_observations(), parameter_usage=usage)
    verdict = veto_lookahead(ctx, params)
    assert not verdict.passed
    assert "fitted past the date" in verdict.detail


def test_the_covariance_row_reads_the_universes_last_weekly_period(
    small_universe, settings, rstub, dates
):
    universe, _ = small_universe
    rule = run_rule(small_universe, settings, rstub, dates, n=2)
    assert rule.covariance_fitted_from_panel
    cov_rows = rule.parameter_usage().query("parameter == 'covariance'")
    for _, row in cov_rows.iterrows():
        last = universe.weekly.index[universe.weekly.index <= row["used_on_date"]][-1]
        assert row["fitted_through"] == last


def test_a_frame_sigma_gives_one_sigma_row_per_column(small_universe, settings, rstub, dates):
    scores = noise(dates, ["US", "Japan"], last={"US": 4.0, "Japan": -4.0})
    sigma = pd.DataFrame(0.5, index=dates, columns=["US", "Japan"])
    rule = make_rule(
        small_universe, settings, rstub, dates, scores=scores, sigma=sigma, axis="region",
        expression="cross_sectional", hypothesis_id=HYPOTHESIS,
    )  # fmt: skip
    rule(dates[T], None)
    usage = rule.parameter_usage()
    assert set(usage.loc[usage["parameter"] == "sigma_region", "instrument"]) == {"US", "Japan"}
    assert set(usage.loc[usage["parameter"] == f"zscore_{HYPOTHESIS}", "instrument"]) == {
        "US",
        "Japan",
    }


# --- F7: the two tables of E, one row per solved rebalance -----------------------


def test_f7_the_reports_have_exactly_the_solved_dates_and_each_variance_row_sums_to_one(
    small_universe, settings, rstub, dates
):
    n = 4
    rule = run_rule(small_universe, settings, rstub, dates, n=n)
    out = rule.reports(FACTOR_COV)
    solved = list(dates[T : T + n])
    assert list(out["active_exposure"].index) == solved
    assert list(out["tracking_variance"].index) == solved
    assert list(out["active_exposure"].columns) == [*FACTORS, *AXIS_COLUMNS, *REGION_COLUMNS]
    assert list(out["tracking_variance"].columns) == [*FACTORS, "residual"]
    np.testing.assert_allclose(out["tracking_variance"].sum(axis=1).to_numpy(), 1.0, atol=1e-9)
    assert isinstance(out["transfer"], float)
    # a callable factor covariance gives the same tables
    again = rule.reports(lambda date: FACTOR_COV)
    pd.testing.assert_frame_equal(again["tracking_variance"], out["tracking_variance"])


def test_the_reports_of_a_region_cross_section_run(small_universe, settings, rstub, dates):
    scores = noise(dates, ["US", "Japan", "Developed Europe"])
    sigma = pd.DataFrame(0.5, index=dates, columns=scores.columns)
    cells = pd.DataFrame(0.0, index=rstub.frame.index, columns=scores.columns)
    cells.iloc[0:4, 0] = 1.0
    cells.iloc[4:8, 1] = 1.0
    cells.iloc[8:10, 2] = 1.0

    class Cells(ReportStub):
        def axis(self, name, date):
            return cells.copy()

    stub = Cells(small_universe[0].holdable, set(small_universe[0].cash))
    rule = make_rule(
        small_universe, settings, stub, dates, scores=scores, sigma=sigma, axis="region",
        expression="cross_sectional",
    )  # fmt: skip
    drifted = None
    for date in dates[T : T + 3]:
        drifted = rule(date, None, drifted=drifted)
    out = rule.reports(FACTOR_COV)
    assert len(out["active_exposure"]) == 3
    assert isinstance(out["transfer"], float)


def test_an_instrument_with_no_row_contributes_nothing_and_is_counted(
    small_universe, settings, rstub, dates
):
    rule = run_rule(small_universe, settings, rstub, dates, n=1)
    book = rule.books[dates[T]]
    bench = reports.benchmark_holdings(book["cov"], book["leg_weights"])
    short = book["frame"].iloc[:-2]
    full = reports.active_exposure(book["weights"], bench, book["frame"], FACTORS)
    cut = reports.active_exposure(book["weights"], bench, short, FACTORS)
    dropped = list(book["frame"].index[-2:])
    active = reports._active_weights(book["weights"], bench)
    expected = int((active.reindex(dropped).fillna(0.0) != 0.0).sum())
    assert reports.unrowed_with_weight(book["weights"], bench, short) == expected
    assert reports.unrowed_with_weight(book["weights"], bench, book["frame"]) == 0
    if expected:
        assert not np.allclose(full.to_numpy(), cut.to_numpy())


# --- the functions' own arithmetic --------------------------------------------------


def test_benchmark_holdings_of_a_one_leg_universe_is_that_legs_tracking_weights():
    tracking = pd.Series([0.5, 0.3, 0.2], index=["A", "B", "C"])
    cov = SimpleNamespace(legs={"L": {"weights": tracking}})
    got = reports.benchmark_holdings(cov, pd.Series({"L": 1.0}))
    pd.testing.assert_series_equal(got, tracking)
    two = SimpleNamespace(
        legs={
            "L": {"weights": tracking},
            "M": {"weights": tracking.iloc[::-1].set_axis(tracking.index)},
        }
    )
    mix = reports.benchmark_holdings(two, pd.Series({"L": 0.6, "M": 0.4}))
    np.testing.assert_allclose(mix.to_numpy(), [0.5 * 0.6 + 0.2 * 0.4, 0.3, 0.2 * 0.6 + 0.5 * 0.4])


def test_a_book_equal_to_the_benchmark_holdings_has_zero_active_exposure_everywhere(
    small_universe, settings, rstub, dates
):
    rule = run_rule(small_universe, settings, rstub, dates, n=1)
    book = rule.books[dates[T]]
    bench = reports.benchmark_holdings(book["cov"], book["leg_weights"])
    got = reports.active_exposure(bench, bench, book["frame"], FACTORS)
    assert list(got.index) == [*FACTORS, *AXIS_COLUMNS, *REGION_COLUMNS]
    np.testing.assert_allclose(got.to_numpy(), 0.0, atol=1e-12)


def test_the_euler_shares_of_a_two_factor_three_instrument_case_are_exact():
    ids = ["A", "B", "C", "L"]
    cov = SimpleNamespace(matrix=pd.DataFrame(np.eye(4), index=ids, columns=ids))
    weights = pd.Series({"A": 1.0, "B": 0.0, "C": 0.0})
    legs = pd.Series({"L": 1.0})
    x = pd.Series({"f1": 2.0, "f2": 1.0})
    f = pd.DataFrame([[0.5, 0.1], [0.1, 0.25]], index=x.index, columns=x.index)
    got = reports.tracking_variance_shares(weights, cov, legs, x, f)
    # a = (1, 0, 0, -1), total = 2; F x = (1.1, 0.45); x_k (F x)_k = (2.2, 0.45)
    np.testing.assert_allclose(got["f1"], 1.1, rtol=1e-12)
    np.testing.assert_allclose(got["f2"], 0.225, rtol=1e-12)
    np.testing.assert_allclose(got["residual"], 1.0 - 1.325, rtol=1e-12)
    np.testing.assert_allclose(got.sum(), 1.0, atol=1e-12)


def test_a_zero_total_active_variance_is_refused():
    ids = ["A", "L"]
    cov = SimpleNamespace(matrix=pd.DataFrame(np.eye(2), index=ids, columns=ids))
    x = pd.Series({"f1": 1.0})
    f = pd.DataFrame([[1.0]], index=x.index, columns=x.index)
    with pytest.raises(ValueError, match="undefined"):
        reports.tracking_variance_shares(pd.Series({"A": 0.0}), cov, pd.Series({"L": 0.0}), x, f)


def test_transfer_is_one_for_an_exposure_proportional_to_the_view_and_nan_below_three_points():
    index = pd.date_range("2018-01-05", periods=6, freq="W-FRI")
    view = pd.Series([0.1, -0.2, 0.3, 0.05, -0.1, 0.2], index=index)
    assert reports.transfer(3.0 * view, view, "directional") == pytest.approx(1.0)
    assert reports.transfer(-2.0 * view, view, "directional") == pytest.approx(-1.0)
    assert np.isnan(reports.transfer(view.iloc[:2], view.iloc[:2], "directional"))

    groups = pd.DataFrame(
        np.arange(24, dtype=float).reshape(6, 4) ** 1.5, index=index, columns=list("abcd")
    )
    assert reports.transfer(2.0 * groups, groups, "cross_sectional") == pytest.approx(1.0)
    assert np.isnan(reports.transfer(groups[["a", "b"]], groups[["a", "b"]], "cross_sectional"))
    with pytest.raises(ValueError):
        reports.transfer(view, view, "both")
