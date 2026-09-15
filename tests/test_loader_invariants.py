"""
The seven loader invariants of SUBSTRATE section 5.1, one test group each.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.loaders.base import SeriesMeta
from signal_lab.loaders.invariants import (
    InvariantViolation,
    SpliceRefused,
    apply_splices,
    assert_no_forward_fill,
    cross_region_covariance,
    filter_business_days,
    flag_net_of_withholding,
    frequency_breaches,
    hedge_mixing_breach,
    overlapping_returns,
    propagate_hedge_flags,
    region_signal_universe,
    returns_from_prior_observation,
    same_day_cross_region_pairs,
    spanned_gap_days,
    to_missing,
    truncate_at_daily_start,
)


def meta_for(series_id, start, **kw):
    return SeriesMeta(
        series_id=series_id, true_daily_start=pd.Timestamp(start), tier="backbone", **kw
    )


# --- 1. business days and missing markers -----------------------------------


def test_na_marker_becomes_nan_not_zero():
    frame = pd.DataFrame(
        {"A": ["100.0", "#N/A", "102.0"]}, index=pd.date_range("2010-01-04", periods=3)
    )
    out = to_missing(frame, ["#N/A"])
    assert out["A"].isna().iloc[1]
    assert not (out["A"] == 0).any(), "a missing observation must never become a zero return"


def test_weekends_are_dropped():
    index = pd.date_range("2010-01-01", "2010-01-11", freq="D")
    frame = pd.DataFrame({"A": range(len(index))}, index=index)
    out = filter_business_days(frame)
    assert (pd.DatetimeIndex(out.index).dayofweek < 5).all()
    assert len(out) < len(frame)


def test_named_holidays_are_dropped():
    index = pd.bdate_range("2010-01-04", "2010-01-08")
    frame = pd.DataFrame({"A": range(len(index))}, index=index)
    out = filter_business_days(frame, holidays=[pd.Timestamp("2010-01-06")])
    assert pd.Timestamp("2010-01-06") not in out.index


def test_forward_fill_is_detected():
    index = pd.date_range("2010-01-04", periods=4, freq="B")
    before = pd.DataFrame({"A": [1.0, np.nan, 3.0, 4.0]}, index=index)
    assert_no_forward_fill(before, before)  # identity passes
    after = before.ffill()
    with pytest.raises(InvariantViolation, match="Forward fill is forbidden"):
        assert_no_forward_fill(before, after)


# --- 2. truncation at the true daily start -----------------------------------


def test_truncation_blanks_everything_before_the_daily_start():
    index = pd.date_range("2010-01-04", periods=6, freq="B")
    levels = pd.DataFrame({"A": np.arange(6, dtype=float)}, index=index)
    meta = {"A": meta_for("A", index[3])}
    out = truncate_at_daily_start(levels, meta)
    assert out["A"].iloc[:3].isna().all()
    assert out["A"].iloc[3:].notna().all()


def test_truncation_needs_metadata_for_every_column():
    levels = pd.DataFrame({"A": [1.0]}, index=pd.to_datetime(["2010-01-04"]))
    with pytest.raises(InvariantViolation, match="no metadata"):
        truncate_at_daily_start(levels, {})


def test_frequency_breaches_finds_pre_start_contributions():
    meta = {"A": meta_for("A", "2005-01-03")}
    contributions = pd.DataFrame(
        {
            "series_id": ["A", "A", "A"],
            "date": pd.to_datetime(["2004-11-30", "2005-01-03", "2006-02-01"]),
        }
    )
    breaches = frequency_breaches(contributions, meta)
    assert len(breaches) == 1
    assert breaches["date"].iloc[0] == pd.Timestamp("2004-11-30")


# --- 3. returns from each series' own prior observation ----------------------


def test_return_spans_a_gap_rather_than_becoming_nan():
    """
    The invariant that pct_change() gets wrong.

    B does not trade on the 5th. Its return on the 6th is measured against its
    own last observation on the 4th, not against a NaN.
    """
    index = pd.to_datetime(["2010-01-04", "2010-01-05", "2010-01-06"])
    levels = pd.DataFrame({"A": [100.0, 101.0, 102.0], "B": [100.0, np.nan, 110.0]}, index=index)
    rets = returns_from_prior_observation(levels)
    assert np.isnan(rets["B"].iloc[1]), "no observation means no return, not a zero"
    assert rets["B"].iloc[2] == pytest.approx(0.10)
    assert rets["A"].iloc[2] == pytest.approx(102.0 / 101.0 - 1)
    # Both of pandas' pct_change behaviours are wrong here, in different ways,
    # and SUBSTRATE forbids each of them. Asserted explicitly so the reason this
    # invariant exists survives a pandas default change.
    unfilled = levels.pct_change(fill_method=None)
    assert np.isnan(unfilled["B"].iloc[2]), (
        "without a fill, pct_change measures against a NaN and silently loses a real 10% return"
    )
    padded = levels.ffill().pct_change(fill_method=None)
    assert padded["B"].iloc[1] == 0.0, (
        "with a forward fill it invents a 0% return on a day the series did not "
        "trade, which SUBSTRATE section 5.1.1 forbids as loudly as it forbids "
        "treating missing as zero"
    )


def test_first_observation_has_no_return():
    index = pd.date_range("2010-01-04", periods=3, freq="B")
    levels = pd.DataFrame({"A": [100.0, 101.0, 102.0]}, index=index)
    assert np.isnan(returns_from_prior_observation(levels)["A"].iloc[0])


def test_single_observation_series_yields_no_returns():
    index = pd.date_range("2010-01-04", periods=3, freq="B")
    levels = pd.DataFrame({"A": [np.nan, 100.0, np.nan]}, index=index)
    assert returns_from_prior_observation(levels)["A"].isna().all()


def test_spanned_gap_days_flags_a_month_end_print():
    index = pd.to_datetime(["2010-01-29", "2010-02-26", "2010-03-01"])
    levels = pd.DataFrame({"A": [100.0, 101.0, 101.5]}, index=index)
    gaps = spanned_gap_days(levels)
    assert gaps["A"].iloc[1] == 28
    assert gaps["A"].iloc[2] == 3


# --- 4. gross / net ----------------------------------------------------------


def test_net_of_withholding_is_flagged_not_corrected():
    meta = {
        "NDDUUS": meta_for("NDDUUS", "2000-01-03"),
        "LEGATRUU": meta_for("LEGATRUU", "2000-01-03"),
    }
    out = flag_net_of_withholding(meta, ["NDDU", "M1"])
    assert out["NDDUUS"].gross is False
    assert out["LEGATRUU"].gross is True


# --- 5. splices --------------------------------------------------------------


def test_splice_fills_only_the_gap_and_is_logged():
    """
    The target still wins where both print, but the source is RESCALED first.

    This test previously asserted that the source's levels were copied across
    unchanged, which is what the loader used to do. That is wrong, and wrong in a
    way nothing downstream would catch: `LT13TRUU` and `G3OC` are different index
    families whose level scales are unrelated, so a raw copy leaves a step at the
    seam and `returns_from_prior_observation` reads that step as a real one-day
    return. Here it would be 50/11 - 1, a move of +354%, sitting inside an
    otherwise well-formed panel. The workbook's own loader notes say to chain
    returns rather than levels; rescaling the source at the seam is the same
    thing expressed in levels.
    """
    index = pd.date_range("2010-01-04", periods=4, freq="B")
    levels = pd.DataFrame(
        {"LT13TRUU": [np.nan, np.nan, 50.0, 51.0], "G3OC": [10.0, 11.0, 12.0, 13.0]}, index=index
    )
    meta = {"LT13TRUU": meta_for("LT13TRUU", index[0]), "G3OC": meta_for("G3OC", index[0])}
    spec = [{"target": "LT13TRUU", "source": "G3OC", "reason": "ICE BofA", "active": True}]
    out, new_meta, records = apply_splices(levels, spec, meta)

    scale = 50.0 / 12.0  # target over source on the seam date, the first both print
    assert out["LT13TRUU"].tolist() == pytest.approx(
        [10.0 * scale, 11.0 * scale, 50.0, 51.0]
    ), "the target wins where both exist; the source is put on the target's scale"
    assert len(records) == 1
    assert records[0].n_observations_taken == 2
    assert records[0].splice_date == index[0].date()
    assert records[0].scale_factor == pytest.approx(scale)
    assert records[0].seam_date == index[2].date()
    assert new_meta["LT13TRUU"].splice is records[0]

    # The property that matters: no fabricated jump anywhere in the joined series.
    returns = returns_from_prior_observation(out)["LT13TRUU"].dropna()
    assert float(np.abs(returns).max()) < 0.5


def test_splice_without_an_overlap_is_refused():
    """
    No overlapping observation means no common scale.

    Choosing one anyway would fabricate a level, and a fabricated level is
    indistinguishable from a measured one by the time it reaches a covariance
    estimate. Refusing is the only honest answer.
    """
    index = pd.date_range("2010-01-04", periods=4, freq="B")
    levels = pd.DataFrame(
        {"T": [np.nan, np.nan, 50.0, 51.0], "S": [10.0, 11.0, np.nan, np.nan]}, index=index
    )
    meta = {"T": meta_for("T", index[0]), "S": meta_for("S", index[0])}
    with pytest.raises(SpliceRefused):
        apply_splices(levels, [{"target": "T", "source": "S", "active": True}], meta)


def test_inactive_and_unresolved_splices_are_skipped():
    index = pd.date_range("2010-01-04", periods=2, freq="B")
    levels = pd.DataFrame({"SPBDALB": [np.nan, 1.0], "OTHER": [5.0, 6.0]}, index=index)
    meta = {"SPBDALB": meta_for("SPBDALB", index[0]), "OTHER": meta_for("OTHER", index[0])}
    specs = [
        {"target": "SPBDALB", "source": None, "reason": "no TR loan index", "active": False},
        {"target": "SPBDALB", "source": "MISSING", "reason": "not in panel", "active": True},
    ]
    out, _, records = apply_splices(levels, specs, meta)
    assert records == []
    assert np.isnan(out["SPBDALB"].iloc[0])


# --- 6. hedge flags ----------------------------------------------------------


def test_hedge_flags_propagate_from_params():
    meta = {sid: meta_for(sid, "2000-01-03") for sid in ["H09122US", "LEGATRUU"]}
    out = propagate_hedge_flags(meta, ["H09122US"])
    assert out["H09122US"].hedged is True
    assert out["LEGATRUU"].hedged is False


def test_region_signal_universe_excludes_hedged_by_default():
    meta = propagate_hedge_flags(
        {sid: meta_for(sid, "2000-01-03") for sid in ["H09122US", "LEGATRUU"]}, ["H09122US"]
    )
    assert region_signal_universe(meta) == ["LEGATRUU"]
    assert region_signal_universe(meta, allow_hedged=True) == ["H09122US"]


def test_mixing_hedged_and_unhedged_is_reported():
    meta = propagate_hedge_flags(
        {sid: meta_for(sid, "2000-01-03") for sid in ["H09122US", "LEGATRUU"]}, ["H09122US"]
    )
    assert hedge_mixing_breach(["H09122US", "LEGATRUU"], meta) == ["H09122US"]
    assert hedge_mixing_breach(["LEGATRUU"], meta) == []


def test_synthetic_panel_carries_exactly_six_hedged_series(panel, params):
    assert len(panel.hedged_ids()) == params.get("data.synthetic.n_hedged")


# --- 7. cross-region covariance on overlapping returns -----------------------


def test_overlapping_returns_compound_the_window():
    rets = pd.Series([0.01, 0.02, -0.01], index=pd.date_range("2010-01-04", periods=3, freq="B"))
    out = overlapping_returns(rets.to_frame("A"), 2)["A"]
    assert np.isnan(out.iloc[0])
    assert out.iloc[1] == pytest.approx(1.01 * 1.02 - 1)


def test_cross_region_pairs_use_overlapping_returns():
    """
    Built so same-day correlation understates the truth: EUR reacts to the US
    factor one day late, exactly the non-synchronous-close problem.
    """
    rng = np.random.default_rng(0)
    n = 900
    index = pd.bdate_range("2010-01-04", periods=n)
    shock = rng.normal(0, 0.01, n)
    us = shock + rng.normal(0, 0.002, n)
    eur = np.concatenate([[0.0], shock[:-1]]) + rng.normal(0, 0.002, n)
    returns = pd.DataFrame({"US1": us, "EUR1": eur}, index=index)
    meta = {
        "US1": meta_for("US1", index[0], region="US"),
        "EUR1": meta_for("EUR1", index[0], region="EUR"),
    }
    same_day = returns.cov().loc["US1", "EUR1"]
    cov = cross_region_covariance(returns, meta, overlap_days=2)
    assert cov.loc["US1", "EUR1"] > same_day, "overlapping returns must recover the lagged link"
    assert cov.loc["US1", "EUR1"] == cov.loc["EUR1", "US1"]


def test_same_region_pairs_keep_daily_covariance():
    rng = np.random.default_rng(1)
    index = pd.bdate_range("2010-01-04", periods=400)
    returns = pd.DataFrame(rng.normal(0, 0.01, (400, 2)), index=index, columns=["US1", "US2"])
    meta = {
        "US1": meta_for("US1", index[0], region="US"),
        "US2": meta_for("US2", index[0], region="US"),
    }
    cov = cross_region_covariance(returns, meta, overlap_days=2)
    assert cov.loc["US1", "US2"] == pytest.approx(returns.cov().loc["US1", "US2"])


def test_cross_region_pairs_are_enumerable(panel):
    pairs = same_day_cross_region_pairs(panel.meta, panel.series_ids[:12])
    assert pairs, "the synthetic universe must contain cross-region pairs to test the rule on"
