"""
The synthetic backend: shaped like the vendors, and planted with known truth.

These tests are what let phase 1 trust a recovery result. If the panel does not
have ragged starts, gaps and a factor structure, a harness that passes on it
proves nothing about a harness on real data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.loaders.invariants import returns_from_prior_observation
from signal_lab.loaders.synthetic import make_return_panel, plant

# --- shape -------------------------------------------------------------------


def test_panel_has_the_configured_size_and_span(panel, params):
    cfg = params.get("data.synthetic")
    assert len(panel.series_ids) == cfg["n_series"]
    assert panel.returns.index.min() >= pd.Timestamp(cfg["start"])
    assert panel.returns.index.max() <= pd.Timestamp(cfg["end"])


def test_only_business_days(panel):
    assert (pd.DatetimeIndex(panel.levels.index).dayofweek < 5).all()


def test_starts_are_ragged_across_three_decades(panel):
    starts = pd.Series(panel.daily_starts())
    assert starts.nunique() > 30, "a panel where everything starts together tests nothing"
    assert starts.min().year <= 1995
    assert starts.max().year >= 2010


def test_tiers_reflect_the_real_coverage_distribution(panel):
    """
    The real universe is roughly 75 backbone, 12 second, 10 tradable-only.
    The synthetic draw should land in the same neighbourhood, not on the nose.
    """
    counts = {t: len(panel.by_tier(t)) for t in ("backbone", "second", "tradable-only")}
    assert counts["backbone"] > counts["second"] + counts["tradable-only"]
    assert 55 <= counts["backbone"] <= 90
    assert counts["second"] >= 3 and counts["tradable-only"] >= 3


def test_there_are_holiday_and_idiosyncratic_gaps(panel):
    """Gaps must not be aligned across series, or prior-observation returns
    and row-differencing would agree and the invariant would be untested."""
    live = panel.levels.notna()
    started = live.cummax()
    holes = started & ~live
    assert holes.to_numpy().any(), "no gaps after each series started"
    per_date = holes.sum(axis=1)
    assert (per_date > 0).sum() > 100
    assert per_date.max() < len(panel.series_ids), (
        "a date where every series is missing is a holiday, not a gap"
    )


def test_exactly_six_hedged_series_flagged(panel, params):
    assert len(panel.hedged_ids()) == params.get("data.synthetic.n_hedged") == 6
    assert set(panel.hedged_ids()).isdisjoint(panel.unhedged_ids())


def test_frequency_break_series_exist_and_are_dated(panel):
    broken = {s: m for s, m in panel.meta.items() if m.month_end_only_before is not None}
    assert len(broken) >= 5
    for m in broken.values():
        assert m.month_end_only_before == m.true_daily_start


def test_no_return_predates_its_series_daily_start(panel):
    """The invariant the `frequency` veto enforces, checked on the panel itself."""
    for sid, m in panel.meta.items():
        observed = panel.returns[sid].dropna()
        if observed.empty:
            continue
        assert observed.index.min() >= pd.Timestamp(m.true_daily_start), sid


def test_five_latent_factors_are_recoverable(panel):
    """
    A cross-sectional signal needs common structure to find. PCA on the
    backbone slice should show a handful of dominant components.
    """
    backbone = panel.by_tier("backbone")
    sub = panel.returns[backbone].loc["2005-01-01":"2015-12-31"].dropna(axis=1, thresh=2000)
    sub = sub.dropna()
    assert sub.shape[0] > 1000 and sub.shape[1] > 30
    corr = np.corrcoef(sub.to_numpy(), rowvar=False)
    eigs = np.sort(np.linalg.eigvalsh(corr))[::-1]
    share = eigs[:5].sum() / eigs.sum()
    assert 0.25 < share < 0.95, f"top-5 eigenvalue share {share:.2f} is not a factor structure"


def test_returns_match_the_invariant_function(panel):
    rebuilt = returns_from_prior_observation(panel.levels)
    pd.testing.assert_frame_equal(rebuilt, panel.returns)


def test_generation_is_deterministic(params):
    a = make_return_panel(params, seed=123, snapshot_id="t")
    b = make_return_panel(params, seed=123, snapshot_id="t")
    pd.testing.assert_frame_equal(a.returns, b.returns)
    c = make_return_panel(params, seed=124, snapshot_id="t")
    assert not c.returns.equals(a.returns)


# --- analytics and macro -----------------------------------------------------


def test_oas_is_dropped_on_treasury_buckets(analytics):
    treasuries = {"2. US Treasury Maturity Buckets", "1. Risk-Free / Cash"}
    oas = analytics.field("INDEX_OAS_TSY")
    for sid in oas.columns:
        assert analytics.meta[sid].section not in treasuries
    oad = analytics.field("INDEX_OAD_TSY")
    assert any(analytics.meta[s].section in treasuries for s in oad.columns), (
        "OAD on Treasury buckets is kept: it is the duration axis of the characteristic map"
    )


def test_analytics_field_start_dates_follow_substrate_5_3(analytics):
    oas = analytics.field("INDEX_OAS_TSY").dropna(how="all")
    ytw = analytics.field("INDEX_YIELD_TO_WORST").dropna(how="all")
    assert oas.index.min() >= pd.Timestamp("2003-01-01"), "spreads from 2003"
    assert ytw.index.min() < oas.index.min(), "yields start earlier than spreads"


def test_vintage_panel_is_bitemporal_with_revisions(macro):
    counts = macro.frame.groupby(["series_id", "real_date"]).size()
    assert (counts > 1).any(), "no revisions means as_of is never exercised"
    assert (macro.frame["knowledge_date"] >= macro.frame["real_date"]).all()


def test_as_of_hides_what_was_not_yet_published(macro):
    early = macro.as_of("2005-03-15")
    late = macro.as_of("2005-09-15")
    assert early.index.max() < late.index.max(), "later knowledge date sees more periods"
    assert set(early.columns) <= set(late.columns)


def test_as_of_returns_the_latest_vintage_not_the_first(macro):
    sid = macro.frame["series_id"].iloc[0]
    revised = (
        macro.frame[macro.frame["series_id"] == sid]
        .groupby("real_date")
        .filter(lambda g: len(g) > 1)
    )
    if revised.empty:
        pytest.skip("this series has no revision")
    period = revised["real_date"].iloc[0]
    vintages = revised[revised["real_date"] == period].sort_values("knowledge_date")
    first, last = vintages.iloc[0], vintages.iloc[-1]
    seen_early = macro.as_of(first["knowledge_date"], [sid]).loc[period, sid]
    seen_late = macro.as_of(last["knowledge_date"], [sid]).loc[period, sid]
    assert seen_early == pytest.approx(first["value"])
    assert seen_late == pytest.approx(last["value"])


def test_usage_log_never_predates_a_knowledge_date(macro):
    log = macro.usage_log("2010-06-30")
    assert (pd.to_datetime(log["used_on_date"]) >= pd.to_datetime(log["knowledge_date"])).all()


# --- the plant ---------------------------------------------------------------


def test_plant_returns_ground_truth(panel):
    planted, signal, record = plant(panel, "trend", strength_ic=0.05, horizon_days=20, seed=99)
    assert record.strength_ic == 0.05
    assert record.horizon_days == 20
    assert len(record.series_ids) > 20
    assert record.note


def test_planted_relationship_is_recoverable_at_the_stated_strength(panel):
    """
    Ground truth for phase 1.

    Rank IC only. No information ratio is computed anywhere in phase 0; the
    engine that would produce one does not exist yet.
    """
    planted, signal, record = plant(panel, "trend", strength_ic=0.05, horizon_days=20, seed=99)
    ids, h = list(record.series_ids), record.horizon_days
    forward = (1 + planted.returns[ids]).rolling(h).apply(np.prod, raw=True).shift(-h) - 1

    ics = []
    for date in signal.index[::20]:
        a, b = signal.loc[date, ids], forward.loc[date, ids]
        mask = a.notna() & b.notna()
        if mask.sum() >= 20:
            ics.append(a[mask].rank().corr(b[mask].rank()))
    realised = float(np.nanmean(ics))
    assert len(ics) > 100
    assert realised == pytest.approx(0.05, abs=0.02), f"planted 0.05, recovered {realised:.3f}"


def test_the_same_signal_finds_nothing_in_the_unplanted_panel(panel):
    """The control. Without it, the recovery test could be measuring the signal
    construction rather than the plant."""
    _, signal, record = plant(panel, "trend", strength_ic=0.05, horizon_days=20, seed=99)
    ids, h = list(record.series_ids), record.horizon_days
    forward = (1 + panel.returns[ids]).rolling(h).apply(np.prod, raw=True).shift(-h) - 1
    ics = []
    for date in signal.index[::20]:
        a, b = signal.loc[date, ids], forward.loc[date, ids]
        mask = a.notna() & b.notna()
        if mask.sum() >= 20:
            ics.append(a[mask].rank().corr(b[mask].rank()))
    assert abs(float(np.nanmean(ics))) < 0.02


def test_plant_scales_with_requested_strength(panel):
    weak = plant(panel, "trend", strength_ic=0.02, horizon_days=20, seed=5)[2]
    strong = plant(panel, "trend", strength_ic=0.10, horizon_days=20, seed=5)[2]
    assert weak.strength_ic < strong.strength_ic


def test_plant_respects_ragged_starts(panel):
    planted, signal, record = plant(panel, "trend", strength_ic=0.05, seed=1)
    for sid in record.series_ids:
        assert planted.returns[sid].dropna().index.min() >= pd.Timestamp(
            panel.meta[sid].true_daily_start
        )
        assert signal[sid].notna().sum() <= panel.returns[sid].notna().sum()


def test_plant_refuses_a_universe_too_small(panel):
    with pytest.raises(ValueError, match="at least 5"):
        plant(panel, "trend", series_ids=panel.series_ids[:3])


def test_loader_satisfies_the_protocol(params):
    from signal_lab.loaders import get_loader

    loader = get_loader("synthetic", params=params)
    for method in ("load_returns", "load_analytics", "load_macro"):
        assert callable(getattr(loader, method))
    with pytest.raises(ValueError, match="unknown loader"):
        get_loader("bogus")


def test_vendor_backends_raise_rather_than_returning_empty(params):
    from signal_lab.loaders import get_loader
    from signal_lab.loaders.bloomberg import LoaderNotImplemented

    for source in ("bloomberg", "fred", "jpmaqs"):
        with pytest.raises(LoaderNotImplemented):
            get_loader(source, params=params).load_returns("x")


def test_the_search_gate_is_closed_while_jpmaqs_is_pending(params):
    from signal_lab.loaders.jpmaqs import search_is_open

    is_open, detail = search_is_open(params)
    assert not is_open and "5.6" in detail
