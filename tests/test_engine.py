"""
The walk-forward engine and the cost model. SUBSTRATE section 16, phase 1.

The engine's job is accounting, and accounting is where a backtest lies
quietly. So most of these tests are arithmetic on a panel small enough to work
out by hand, rather than statistics on a panel large enough to hide an error.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.harness.costs import CostModel, drift_weights, portfolio_return
from signal_lab.harness.engine import (
    constant_exposures,
    rebalance_dates,
    run_averaged_over_rebalance_days,
    run_walk_forward,
    to_run_context,
)
from signal_lab.loaders.base import ReturnPanel, SeriesMeta

FLAT = pd.DataFrame(0.0, index=["A", "B"], columns=["f0"])


def tiny_panel(returns: pd.DataFrame) -> ReturnPanel:
    meta = {
        c: SeriesMeta(series_id=c, true_daily_start=returns.index[0], tier="backbone")
        for c in returns.columns
    }
    levels = (1.0 + returns.fillna(0.0)).cumprod() * 100.0
    return ReturnPanel(levels=levels, returns=returns, meta=meta, snapshot_id="tiny")


def flat_panel(days: int = 25, start: str = "2015-01-01") -> ReturnPanel:
    index = pd.bdate_range(start, periods=days)
    return tiny_panel(pd.DataFrame(0.0, index=index, columns=["A", "B"]))


def fixed(weights: dict) -> callable:
    series = pd.Series(weights)
    return lambda _date, _panel: series.copy()


# --- weight drift, the piece everything else rests on ------------------------


def test_drift_renormalises_and_moves_toward_the_winner():
    w = pd.Series({"A": 0.5, "B": 0.5})
    r = pd.Series({"A": 0.10, "B": 0.00})
    out = drift_weights(w, r)
    assert out.sum() == pytest.approx(1.0)
    assert out["A"] == pytest.approx(0.55 / 1.05)
    assert out["B"] == pytest.approx(0.50 / 1.05)


def test_a_missing_return_is_not_a_total_loss():
    """
    NaN means the instrument did not print, not that it went to zero. Treating
    a gap as -100% would delete a position on a public holiday.
    """
    w = pd.Series({"A": 0.5, "B": 0.5})
    r = pd.Series({"A": 0.10, "B": np.nan})
    out = drift_weights(w, r)
    assert out["B"] == pytest.approx(0.50 / 1.05)
    assert portfolio_return(w, r) == pytest.approx(0.05)


# --- turnover measured from the drifted book ---------------------------------


def test_turnover_is_measured_from_the_drifted_book_not_the_previous_target():
    """
    The error this guards against reports ZERO turnover for a persistent rule
    whose book has drifted and must be traded back.
    """
    cm = CostModel()
    target = pd.Series({"A": 0.5, "B": 0.5})
    drifted = drift_weights(target, pd.Series({"A": 0.10, "B": 0.0}))

    one_way, delta = cm.turnover(target, drifted)
    expected = abs(0.5 - 0.55 / 1.05)
    assert one_way == pytest.approx(expected)
    assert delta.sum() == pytest.approx(2 * expected)

    naive, _ = cm.turnover(target, target)
    assert naive == 0.0, "the previous-target version would report no trade at all"


def test_an_instrument_entering_the_book_is_a_full_size_trade():
    cm = CostModel()
    one_way, delta = cm.turnover(pd.Series({"A": 0.5, "C": 0.5}), pd.Series({"A": 1.0}))
    assert delta["C"] == pytest.approx(0.5)
    assert one_way == pytest.approx(0.5)


# --- costs -------------------------------------------------------------------


def test_costs_are_charged_on_traded_notional_not_on_one_way_turnover():
    """
    decisions/0017. Charging the one-way figure halves every cost in the lab.
    """
    cm = CostModel(buckets={"A": "low", "B": "low"})
    target, drifted = pd.Series({"A": 0.6, "B": 0.4}), pd.Series({"A": 0.4, "B": 0.6})
    b = cm.rebalance_cost(target, drifted)

    assert b.turnover_one_way == pytest.approx(0.2)
    assert b.traded_notional == pytest.approx(0.4)
    assert b.spread_cost == pytest.approx(0.4 * 5e-4)
    assert b.spread_cost == pytest.approx(2 * b.turnover_one_way * 5e-4)


def test_drag_is_one_week_of_the_annual_fee_on_what_is_held():
    cm = CostModel(buckets={"A": "low"})
    b = cm.rebalance_cost(pd.Series({"A": 1.0}), pd.Series({"A": 1.0}))
    assert b.spread_cost == pytest.approx(0.0)
    assert b.drag_cost == pytest.approx(5e-4 / 52)


def test_an_unmapped_instrument_is_charged_the_dearest_bucket(params):
    """decisions/0002: costing an unmapped instrument cheaply flatters it."""
    cm = CostModel(params, buckets={})
    assert cm.bucket("NEVER_SEEN") == "high"
    assert cm.half_spread("NEVER_SEEN") == pytest.approx(20e-4)


def test_the_real_universe_supplies_buckets():
    cm = CostModel()
    assert len(cm.buckets) > 90
    assert cm.bucket("SPXT") == "low"
    assert cm.bucket("LF98TRUU") == "high"


# --- the walk-forward loop ---------------------------------------------------


def test_a_flat_panel_produces_only_cost():
    """Nothing moves, so gross is zero and net is exactly the drag."""
    panel = flat_panel()
    path = run_walk_forward(
        panel,
        fixed({"A": 0.5, "B": 0.5}),
        pd.Series(0.0, index=panel.returns.index),
        constant_exposures(FLAT),
        cost_model=CostModel(buckets={"A": "low", "B": "low"}),
    )
    assert (path.gross_returns == 0.0).all()
    assert path.turnover.sum() == pytest.approx(0.0), "a flat panel does not drift"
    assert path.net_returns.iloc[0] == pytest.approx(-5e-4 / 52)


def test_gross_return_compounds_the_days_inside_the_period():
    """One 10% day and one 5% day compound to 15.5%, not 15%."""
    index = pd.bdate_range("2015-01-01", periods=25)
    returns = pd.DataFrame(0.0, index=index, columns=["A", "B"])
    dates = rebalance_dates(index, "FRI")
    inside = index[(index > dates[0]) & (index <= dates[1])]
    returns.loc[inside[0], ["A", "B"]] = 0.10
    returns.loc[inside[1], ["A", "B"]] = 0.05

    path = run_walk_forward(
        tiny_panel(returns),
        fixed({"A": 0.5, "B": 0.5}),
        pd.Series(0.0, index=index),
        constant_exposures(FLAT),
        cost_model=CostModel(buckets={"A": "low", "B": "low"}),
    )
    assert path.gross_returns.iloc[0] == pytest.approx(1.10 * 1.05 - 1.0)


def test_the_period_return_is_earned_on_the_book_held_through_it():
    """
    The one-period lookahead this ordering prevents.

    A rule that holds nothing, then switches into an instrument that has just
    risen 50%, must NOT earn that 50%. It bought at the close after the move.
    """
    index = pd.bdate_range("2015-01-01", periods=25)
    returns = pd.DataFrame(0.0, index=index, columns=["A", "B"])
    dates = rebalance_dates(index, "FRI")
    spike = index[(index > dates[0]) & (index <= dates[1])][2]
    returns.loc[spike, "B"] = 0.50

    def switch(date, _panel):
        return pd.Series({"A": 1.0, "B": 0.0} if date <= dates[0] else {"A": 0.0, "B": 1.0})

    path = run_walk_forward(
        tiny_panel(returns),
        switch,
        pd.Series(0.0, index=index),
        constant_exposures(FLAT),
        cost_model=CostModel(buckets={"A": "low", "B": "low"}),
    )
    assert path.gross_returns.iloc[0] == pytest.approx(0.0), (
        "the 50% move was earned by the book held through the period, which was all A"
    )


def test_rebalance_dates_fall_back_when_friday_is_a_holiday(panel):
    dates = rebalance_dates(panel.returns.index, "FRI")
    assert dates.isin(panel.returns.index).all(), "every rebalance is a real trading date"
    assert (dates.dayofweek == 4).mean() > 0.95
    assert (dates.dayofweek < 4).any(), "some Fridays are holidays and roll back"


def test_an_unknown_rebalance_day_is_refused(panel):
    with pytest.raises(ValueError, match="unknown rebalance day"):
        rebalance_dates(panel.returns.index, "CANDLEMAS")


def test_the_engine_enforces_the_holdout(panel, params):
    from signal_lab.loaders.holdout import HoldoutViolation

    index = pd.bdate_range("2019-12-01", "2020-02-01")
    returns = pd.DataFrame(0.0, index=index, columns=["A", "B"])
    with pytest.raises(HoldoutViolation):
        run_walk_forward(
            tiny_panel(returns),
            fixed({"A": 0.5, "B": 0.5}),
            pd.Series(0.0, index=index),
            constant_exposures(FLAT),
            params=params,
        )


# --- exposures are a function of date ----------------------------------------


def test_the_exposure_rule_is_called_per_date_not_once(params):
    """
    decisions/0015: phase 2 makes loadings walk-forward. The engine must already
    ask for them per date, or every artifact changes shape later.
    """
    panel = flat_panel()
    seen: list[pd.Timestamp] = []

    def rule(date):
        seen.append(date)
        return pd.DataFrame({"f0": [1.0, 0.0]}, index=["A", "B"])

    path = run_walk_forward(
        panel, fixed({"A": 0.5, "B": 0.5}), pd.Series(0.0, index=panel.returns.index), rule
    )
    assert len(seen) == len(path.dates) > 1
    assert len(set(seen)) == len(seen), "a different date each rebalance"
    assert path.exposures["f0"].iloc[0] == pytest.approx(0.5)


# --- alternate rebalance days are averaged, never selected -------------------


def test_alternate_days_are_averaged_and_every_day_is_reported(panel, params, planted):
    from signal_lab.loaders.synthetic import make_benchmark

    rule, bench, _ = planted
    averaged, per_day = run_averaged_over_rebalance_days(
        panel, rule, bench, constant_exposures(pd.DataFrame()), params=params
    )
    days = list(params.get("constraints.rebalance.alternates"))
    assert set(per_day) == set(days)
    assert averaged.rebalance_day.startswith("averaged:")

    irs = averaged.meta["ir_by_day"]
    assert set(irs) == set(days)
    assert averaged.information_ratio() < max(irs.values()) + 1e-9, (
        "the average cannot beat the best day; reporting the best would be selection"
    )
    assert make_benchmark(panel).notna().all()


# --- the planted recovery test, SUBSTRATE section 16 phase 1 -----------------


def test_the_engine_recovers_a_planted_information_ratio(planted, planted_path):
    """
    "The engine must recover a planted IR of 0.5 within its own confidence
    interval" -- SUBSTRATE section 16, phase 1.

    The active stream is exact by construction, so this is tighter than a
    confidence interval: any error in drift, cost or timing arithmetic changes
    the net return the benchmark was defined against, and the recovered IR
    stops matching.
    """
    _rule, _bench, truth = planted
    path = planted_path

    assert truth.target_ir == pytest.approx(0.5, abs=0.05), "the draw itself is near the target"
    assert path.information_ratio() == pytest.approx(truth.target_ir, abs=1e-6)
    assert path.max_active_drawdown() == pytest.approx(truth.target_max_drawdown, abs=1e-6)
    assert path.active_returns.std() * np.sqrt(52) == pytest.approx(truth.target_te, abs=1e-6)


def test_the_recovery_test_would_fail_if_costs_were_dropped(panel, planted):
    """
    The control on the test above. If the engine stopped charging costs, the net
    return would no longer match what the benchmark was built from, and the
    planted IR would not come back. Without this, the recovery test could pass
    on an engine that ignored the cost model entirely.
    """
    rule, bench, truth = planted
    ids = rule(panel.returns.index[0], panel).index
    free = CostModel(buckets={i: "low" for i in ids})
    free._rates = {"low": {"half_spread_bps": 0, "annual_fee_tracking_bps": 0}}

    path = run_walk_forward(
        panel,
        rule,
        bench,
        constant_exposures(pd.DataFrame(0.0, index=ids, columns=["f0"])),
        cost_model=free,
    )
    assert abs(path.information_ratio() - truth.target_ir) > 0.05


# --- feeding the vetoes ------------------------------------------------------


def test_a_completed_path_populates_the_veto_inputs(panel, params, planted_path):
    from vetoes.rules import veto_active_drawdown, veto_positions, veto_turnover

    ctx = to_run_context(planted_path, "R-engine", panel)

    assert veto_positions(ctx, params).passed, "20 instruments is inside the 30 ceiling"
    for veto in (veto_turnover, veto_active_drawdown):
        verdict = veto(ctx, params)
        assert "cannot evaluate" not in verdict.detail, verdict.detail


def test_the_summary_reports_cost_drag_and_never_gross_ir(planted_path):
    summary = planted_path.summary()
    assert "cost_drag" in summary and summary["cost_drag"] > 0
    assert not any("gross" in k for k in summary), "decisions/0004"
