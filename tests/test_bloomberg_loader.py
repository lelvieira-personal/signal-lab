"""
The Bloomberg loader, against a workbook shaped like the vendor pull.

The real pull is licensed data that stays on the owner's machine, so these run
against `tests/fixtures/bloomberg_fixture.py`, which reproduces the workbook's
sheet names, header structure and pathologies with generated numbers. Each test
names the SUBSTRATE invariant it defends, because a loader test that does not say
what it is protecting turns into a change-detector the first time the code moves.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import bloomberg_fixture  # noqa: E402


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return bloomberg_fixture.build(tmp_path_factory.mktemp("bbg"))


@pytest.fixture(scope="module")
def loader(built, params):
    from signal_lab.loaders.bloomberg import BloombergLoader

    return BloombergLoader(
        params,
        raw_dir=built["root"] / "data" / "raw",
        universe_dir=built["universe"],
    )


@pytest.fixture(scope="module")
def panel(loader):
    return loader.load_returns()


# --- invariant 1: business days, and #N/A is missing --------------------------


def test_no_weekend_rows_survive(panel):
    """SUBSTRATE 5.1.1. The fixture writes weekday observations only, but the
    calendar spine carries every calendar day, so an unfiltered read keeps them."""
    assert (pd.DatetimeIndex(panel.levels.index).dayofweek < 5).all()


def test_missing_never_becomes_zero(panel):
    """`#N/A` is missing. A zero level is a real number and would compound."""
    assert not bool((panel.levels == 0).to_numpy().any())
    assert panel.levels.isna().to_numpy().any(), "fixture should leave genuine gaps"


def test_gaps_are_not_filled(panel):
    """SUBSTRATE section 2 forbids forward fill. The ex-USD series carry planted
    holes where no FX fix existed; they must still be holes."""
    exusd = panel.levels["LET1TREU"]
    observed = exusd.dropna()
    assert len(observed) < len(exusd)


# --- invariant 2: truncation at the true daily start --------------------------


def test_no_return_before_its_true_daily_start(panel):
    """SUBSTRATE 5.1.2 and the `frequency` veto. This is the one that matters:
    a month-end observation admitted to a daily panel understates volatility by
    roughly sqrt(21) and corrupts every correlation drawn from it."""
    from signal_lab.loaders.invariants import frequency_breaches

    log = pd.concat(
        [
            pd.DataFrame({"series_id": c, "date": panel.returns[c].dropna().index})
            for c in panel.returns.columns
        ],
        ignore_index=True,
    )
    assert frequency_breaches(log, panel.meta).empty


def test_month_end_era_is_gone(panel):
    """`LUACTRUU` is month-end only until 2003 in the fixture."""
    first = panel.returns["LUACTRUU"].dropna().index.min()
    assert first >= pd.Timestamp(panel.meta["LUACTRUU"].true_daily_start)
    assert first.year == 2003


def test_a_series_without_a_daily_start_is_refused(built, params):
    """Defaulting the start would disable invariant 2 for the raggedest series."""
    from signal_lab.loaders.bloomberg import build_series_meta
    from signal_lab.loaders.invariants import InvariantViolation

    empty = pd.DataFrame(columns=["ticker", "section", "first_daily", "currency"])
    with pytest.raises(InvariantViolation, match="no true daily start"):
        build_series_meta(["MYSTERY"], empty, {}, params)


# --- invariant 3: returns from each series' own prior observation --------------


def test_returns_span_gaps_rather_than_vanishing(panel):
    """`pct_change` on a holed frame drops a real return; the loader must not."""
    series = panel.levels["LET1TREU"]
    observed = series.dropna()
    expected = observed / observed.shift(1) - 1.0
    got = panel.returns["LET1TREU"].dropna()
    assert np.allclose(got.to_numpy(), expected.dropna().to_numpy())


# --- invariant 5: splices, applied and logged ---------------------------------


def test_splice_leaves_no_false_jump(panel):
    """
    The point of the rescale.

    `LT13TRUU` sits near 1800 and `G3OC` near 240. Copying G3OC's levels into
    LT13TRUU's missing history puts a 1800/240 step at the seam, which the return
    calculation reads as a one-day move of roughly +650%. Nothing downstream
    would catch it: the panel is well-formed, the veto thresholds are on
    portfolio statistics, and a single day of +650% inside a twenty-year
    covariance estimate is invisible in a summary.
    """
    returns = panel.returns["LT13TRUU"].dropna()
    assert float(np.abs(returns).max()) < 0.05


def test_splice_is_recorded_with_its_scale(panel):
    """A splice that is not auditable is indistinguishable from a fabrication."""
    (record,) = [s for s in panel.splices if s.target == "LT13TRUU"]
    assert record.source == "G3OC"
    assert record.scale_factor == pytest.approx(1800.0 / 240.0, rel=1e-6)
    assert record.seam_date is not None
    assert record.n_observations_taken > 0


def test_splice_extends_the_true_daily_start(panel):
    """Otherwise every spliced observation is a `frequency` veto breach."""
    assert panel.meta["LT13TRUU"].true_daily_start <= pd.Timestamp("2001-01-02")


def test_splice_with_no_overlap_is_refused():
    """No overlap means no common scale, and inventing one fabricates a level."""
    from signal_lab.loaders.base import SeriesMeta
    from signal_lab.loaders.invariants import SpliceRefused, apply_splices

    idx = pd.bdate_range("2020-01-01", periods=6)
    frame = pd.DataFrame(
        {"T": [np.nan] * 3 + [100.0, 101.0, 102.0], "S": [10.0, 11.0, 12.0] + [np.nan] * 3},
        index=idx,
    )
    meta = {
        "T": SeriesMeta("T", idx[3], "backbone"),
        "S": SeriesMeta("S", idx[0], "backbone"),
    }
    with pytest.raises(SpliceRefused, match="no date on which both series print"):
        apply_splices(frame, [{"target": "T", "source": "S", "active": True}], meta)


def test_skipped_splices_are_reported(loader, panel):
    """A splice that quietly did nothing looks like one never configured."""
    skipped = {s["target"] for s in loader.report["splices_skipped"]}
    assert "SPBDALB" in skipped


def test_candidate_is_not_served_as_a_series(panel):
    """`G3OC` exists to be spliced; it is not a member of the universe."""
    assert "G3OC" not in panel.series_ids


# --- invariants 4 and 6: flags carried, never corrected -----------------------


def test_net_of_withholding_is_flagged_not_corrected(panel):
    """SUBSTRATE 5.1.4: note the mismatch. Correcting it assumes a tax rate."""
    assert panel.meta["NDDUJN"].gross is False
    assert panel.meta["SPXT"].gross is True


def test_hedge_flag_is_carried(panel):
    """SUBSTRATE 5.1.6, and the reason region signals are built from one side."""
    from signal_lab.loaders.invariants import hedge_mixing_breach, region_signal_universe

    assert panel.meta["H09122US"].hedged is True
    assert "H09122US" in panel.hedged_ids()
    assert "H09122US" not in region_signal_universe(panel.meta, allow_hedged=False)
    assert hedge_mixing_breach(panel.series_ids, panel.meta) == ["H09122US"]


# --- the holdout ---------------------------------------------------------------


@pytest.mark.holdout
def test_no_observation_reaches_the_holdout(panel, params):
    """
    The fixture runs to 2021-06-30 on purpose.

    A loader that simply never saw holdout data would pass a weaker test than
    this one: here the data is present in the workbook and must be refused.
    """
    from signal_lab.loaders.holdout import holdout_start

    start = holdout_start(params)
    assert panel.levels.index.max() < start
    assert panel.returns.index.max() < start


@pytest.mark.holdout
def test_returns_are_computed_after_the_cut(panel, params):
    """No return may span the boundary: the last return must be an in-window move."""
    from signal_lab.loaders.holdout import holdout_start

    last = panel.returns.dropna(how="all").index.max()
    assert last < holdout_start(params)


# --- analytics -----------------------------------------------------------------


def test_each_analytics_metric_truncates_at_its_own_start(loader):
    """
    SUBSTRATE 5.3, and the trap the loader notes flag.

    `LUACTRUU` yield-to-worst goes daily years before its OAS does. Truncating
    both at the return series' start would admit month-end OAS to a daily panel.
    """
    analytics = loader.load_analytics()
    ytw = analytics.field("INDEX_YIELD_TO_WORST")["LUACTRUU"].dropna()
    oas = analytics.field("INDEX_OAS_TSY")["LUACTRUU"].dropna()
    assert ytw.index.min() < oas.index.min()
    assert oas.index.min() >= pd.Timestamp("2004-10-01")


def test_treasury_oas_is_dropped(loader):
    """Zero by construction, and Bloomberg returns a small negative instead."""
    analytics = loader.load_analytics()
    assert "LT13TRUU" not in analytics.field("INDEX_OAS_TSY").columns
    assert "LT13TRUU" in analytics.field("INDEX_YIELD_TO_WORST").columns


@pytest.mark.holdout
def test_analytics_respect_the_holdout(loader, params):
    from signal_lab.loaders.holdout import holdout_start

    analytics = loader.load_analytics()
    for name in analytics.field_names:
        assert analytics.field(name).index.max() < holdout_start(params)


# --- benchmark -----------------------------------------------------------------


def test_benchmark_legs_load_with_the_net_flag(loader):
    """`NDUEACWF` is net of withholding; `LEGATRUU` is not. The pair is mixed."""
    bench = loader.load_benchmark()
    assert set(("LEGATRUU", "NDUEACWF")).issubset(bench.levels.columns)
    assert bench.meta["NDUEACWF"].gross is False
    assert bench.meta["LEGATRUU"].gross is True


@pytest.mark.holdout
def test_benchmark_respects_the_holdout(loader, params):
    from signal_lab.loaders.holdout import holdout_start

    assert loader.load_benchmark().levels.index.max() < holdout_start(params)


# --- the report ----------------------------------------------------------------


def test_report_records_what_was_decided(loader, panel):
    """
    The loader's own account of what it did.

    Tier changes and skipped splices are the two things that alter the panel
    without altering a number in it, so they are the two most worth reporting.
    """
    report = loader.report
    assert report["n_series"] == len(panel.series_ids)
    assert "retiered_by_splice" in report
    assert report["dropped_after_splice"] == ["G3OC"]
    assert report["region_source"].startswith("Section")
