"""
The ruler audit. decisions/0023, phase 2.5.

The audit's job is to produce a number the whole programme is then judged
against, so these tests attack the construction rather than the plumbing: does
a planted signal have the IC it claims, is the forward return actually forward,
does the covariance price a replicating book correctly, does effective breadth
count what it says it counts, and does an audit path stay out of the results
store.

The ladder itself is exercised on a deliberately small universe and a short
window -- it solves at every rebalance, and a full-window cell is minutes, not
seconds.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from signal_lab.audit.breadth import effective_breadth, independent_decisions_per_year
from signal_lab.audit.ladder import AuditCell, build_universe, grid_cells, required_ic, run_cell
from signal_lab.audit.signals import (
    forward_active_return,
    plant_signal,
    realised_ic,
    signal_autocorrelation,
)
from signal_lab.loaders.base import ReturnPanel
from signal_lab.portfolio.covariance import (
    effective_bets,
    embed_benchmark_legs,
    ledoit_wolf,
    period_returns,
    trailing_covariance,
)

WEEKS = 260


@pytest.fixture(scope="module")
def weekly() -> pd.DataFrame:
    """Five years of weekly returns with a two-factor structure."""
    rng = np.random.default_rng(4242)
    index = pd.bdate_range("2010-01-08", periods=WEEKS, freq="W-FRI")
    f = rng.normal(0, 0.02, (WEEKS, 2))
    load = rng.normal(0, 1, (8, 2))
    noise = rng.normal(0, 0.01, (WEEKS, 8))
    return pd.DataFrame(f @ load.T + noise, index=index, columns=[f"S{i}" for i in range(8)])


@pytest.fixture(scope="module")
def benchmark(weekly) -> pd.Series:
    return weekly.mean(axis=1)


# --- the planted signal ------------------------------------------------------


def test_the_forward_return_is_forward_and_runs_out_at_the_end(weekly, benchmark):
    """
    The value at t must describe t+1..t+h. If it were shifted by one the audit
    would measure a signal that knows this week's return, and every net IR in
    the table would be wrong in the flattering direction.
    """
    fwd = forward_active_return(weekly, benchmark, horizon=4)
    t = weekly.index[10]
    window = weekly.iloc[11:15]["S0"]
    bench = benchmark.iloc[11:15]
    expected = float((1 + window).prod() - 1) - float((1 + bench).prod() - 1)
    assert fwd.loc[t, "S0"] == pytest.approx(expected, rel=1e-9)
    assert fwd.iloc[-4:].isna().all().all(), "the last h rows have no forward window"


@pytest.mark.parametrize("ic", [0.02, 0.05, 0.10, 0.20])
def test_a_planted_signal_has_the_information_coefficient_it_claims(weekly, benchmark, ic):
    signal = plant_signal(weekly, benchmark, ic=ic, horizon=13, seed=1, vol_window=52)
    measured = realised_ic(signal)["pooled"]
    assert measured == pytest.approx(ic, abs=0.02), f"planted {ic}, measured {measured}"


def test_the_oracle_is_perfectly_correlated_with_the_truth(weekly, benchmark):
    signal = plant_signal(weekly, benchmark, ic=1.0, horizon=13, seed=1, vol_window=52)
    assert realised_ic(signal)["pooled"] == pytest.approx(1.0, abs=1e-9)


def test_signal_persistence_matches_the_horizon(weekly, benchmark):
    """
    A 26-week signal that flipped weekly would make the turnover-shortfall
    curve meaningless: the cap would bind for a reason the construction
    invented rather than one the horizon implies.
    """
    fast = plant_signal(weekly, benchmark, ic=0.05, horizon=4, seed=2, vol_window=52)
    slow = plant_signal(weekly, benchmark, ic=0.05, horizon=52, seed=2, vol_window=52)
    assert signal_autocorrelation(slow.score) > signal_autocorrelation(fast.score)
    assert signal_autocorrelation(slow.score) > 0.8


def test_an_information_coefficient_outside_zero_to_one_is_refused(weekly, benchmark):
    with pytest.raises(ValueError, match="ic must be"):
        plant_signal(weekly, benchmark, ic=1.5, horizon=4, seed=0, vol_window=52)


# --- the covariance ----------------------------------------------------------


def test_period_returns_compound_within_the_window_and_never_across_it():
    index = pd.bdate_range("2015-01-05", periods=10)
    daily = pd.DataFrame(0.01, index=index, columns=["A"])
    dates = pd.DatetimeIndex([index[0], index[5], index[9]])
    out = period_returns(daily, dates)
    assert out.loc[index[5], "A"] == pytest.approx(1.01**5 - 1)
    assert out.loc[index[9], "A"] == pytest.approx(1.01**4 - 1)


def test_shrinkage_is_bounded_and_the_matrix_stays_positive_definite(weekly):
    cov = ledoit_wolf(weekly)
    assert 0.0 <= cov.shrinkage <= 1.0
    assert np.allclose(cov.matrix.values, cov.matrix.values.T)
    assert np.linalg.eigvalsh(cov.matrix.values).min() > 0


def test_shrinkage_falls_as_the_sample_grows():
    """The intensity is a function of estimation error; more data, less shrinkage."""
    rng = np.random.default_rng(7)
    load = rng.normal(0, 1, (10, 2))
    intensities = []
    for n in (100, 1000):
        f = rng.normal(0, 0.02, (n, 2))
        frame = pd.DataFrame(f @ load.T + rng.normal(0, 0.01, (n, 10)))
        intensities.append(ledoit_wolf(frame).shrinkage)
    assert intensities[0] > intensities[1]


def test_a_replicating_book_is_priced_as_replicating(weekly):
    """
    The failure this exists to catch: shrinking a benchmark leg alongside the
    holdables tells a book that replicates it exactly that it carries several
    percent of tracking error, and a 6% budget then looks infeasible while the
    realised tracking error is near zero.
    """
    holdables = list(weekly.columns)
    leg = weekly.mean(axis=1).rename("LEG")
    frame = weekly.join(leg)
    naive = ledoit_wolf(frame)
    embedded = embed_benchmark_legs(ledoit_wolf(weekly), frame, ["LEG"])

    book = pd.Series(1.0 / len(holdables), index=holdables)  # exactly the leg

    def te(cov):
        active = book.reindex(cov.ids).fillna(0.0) - pd.Series({"LEG": 1.0}).reindex(
            cov.ids
        ).fillna(0.0)
        return float(np.sqrt(active.values @ cov.matrix.values @ active.values * 52))

    assert te(embedded) < 0.005, "an exact replication must carry almost no tracking error"
    assert te(embedded) < te(naive), "embedding must beat shrinking the leg with the holdables"
    assert embedded.legs["LEG"]["r2"] > 0.99


def test_a_series_without_a_full_window_is_left_out_rather_than_imputed(weekly):
    late = weekly.copy()
    late.iloc[: WEEKS - 30, 0] = np.nan  # S0 starts 30 weeks before the end
    cov = trailing_covariance(late, late.index[-1], window=52)
    assert "S0" not in cov.ids
    assert len(cov.ids) == 7


def test_a_benchmark_leg_without_a_full_window_is_an_error_not_a_silent_drop(weekly):
    frame = weekly.join(weekly.mean(axis=1).rename("LEG"))
    frame.iloc[: WEEKS - 10, -1] = np.nan
    with pytest.raises(ValueError, match="lack a full window"):
        trailing_covariance(frame, frame.index[-1], window=52, legs=["LEG"])


# --- effective breadth -------------------------------------------------------


def test_effective_bets_counts_independent_directions():
    n = 6
    assert effective_bets(pd.DataFrame(np.eye(n))) == pytest.approx(n)
    ones = pd.DataFrame(np.ones((n, n)))
    assert effective_bets(ones) == pytest.approx(1.0, abs=1e-6)


def test_a_correlated_universe_counts_for_fewer_bets_than_it_has_series(weekly, benchmark):
    b = effective_breadth(weekly, benchmark, [4, 26])
    assert b.n_series == 8
    assert b.effective_bets_active < b.n_series, "correlated series are not independent bets"
    assert b.effective_bets_active > 1


def test_a_persistent_signal_makes_fewer_decisions_a_year():
    assert independent_decisions_per_year(0.0) == pytest.approx(52.0)
    assert independent_decisions_per_year(0.9) == pytest.approx(52 * 0.1 / 1.9)
    assert independent_decisions_per_year(0.96) < 2.0


def test_the_implied_ic_rises_as_breadth_falls(weekly, benchmark):
    b = effective_breadth(weekly, benchmark, [4, 52])
    assert b.implied_ic(0.3, 52) > b.implied_ic(0.3, 4), "a slower signal needs a better IC"


# --- the ladder, end to end on a small universe ------------------------------


@pytest.fixture(scope="module")
def small_universe(params, panel):
    """Fourteen series and a spannable pair of legs, from 2016 on."""
    from signal_lab.audit.universe import synthetic_universe

    audit = dict(params.audit)
    audit["covariance"] = {"estimator": "ledoit_wolf", "window_periods": 52}
    slim = dataclasses.replace(params, audit=audit)
    universe = synthetic_universe(slim, start="2016-01-01")
    keep = universe.holdable[:14]
    trimmed = ReturnPanel(
        levels=universe.panel.levels[keep],
        returns=universe.panel.returns[keep],
        meta={s: universe.panel.meta[s] for s in keep},
        snapshot_id=universe.panel.snapshot_id,
        source=universe.panel.source,
    )
    return build_universe(trimmed, universe.legs, universe.leg_weights, slim), slim


def test_a_cell_runs_the_whole_chain_and_reports_what_bound(small_universe):
    universe, params = small_universe
    row, path = run_cell(universe, AuditCell(0.10, 13, 0), params, solver="scipy")
    assert np.isfinite(row["net_ir"])
    assert row["realised_ic_pooled"] == pytest.approx(0.10, abs=0.05)
    assert row["n_positions_max"] <= params.require("constraints.positions.max_nonzero")
    assert 0.0 <= row["te_binding_share"] <= 1.0
    assert row["max_cash"] <= params.require("constraints.cash.max_weight") + 1e-6
    assert len(path.dates) == row["n_rebalances"] > 20


def test_the_oracle_beats_a_blind_signal(small_universe):
    """
    The weakest property the ladder must have: perfect foresight through this
    pipeline must beat no foresight. If it does not, the alpha is not reaching
    the weights and no number in the table means anything.
    """
    universe, params = small_universe
    blind, _ = run_cell(universe, AuditCell(0.0, 13, 0), params, solver="scipy")
    oracle, _ = run_cell(universe, AuditCell(1.0, 13, 0, tag="oracle"), params, solver="scipy")
    assert oracle["net_ir"] > blind["net_ir"] + 0.5


def test_a_blind_signal_hugs_the_benchmark(small_universe):
    """
    IC = 0 is the control: no information, so no tracking error worth paying
    for and almost no trading.

    Measured against the oracle rather than against an absolute tracking error,
    because the floor is a property of the universe, not of the solver: these
    fourteen series replicate the benchmark legs only to about R^2 0.97, so the
    minimum achievable tracking error here is around 2% however good the
    optimiser is. Asserting an absolute number would have been a test of the
    fixture.
    """
    universe, params = small_universe
    blind, _ = run_cell(universe, AuditCell(0.0, 13, 0), params, solver="scipy")
    oracle, _ = run_cell(universe, AuditCell(1.0, 13, 0, tag="oracle"), params, solver="scipy")
    budget = params.require("constraints.tracking_error.max_trailing_3y")
    assert blind["te_ex_ante_mean"] < oracle["te_ex_ante_mean"], (
        "no information should buy less tracking error than perfect information"
    )
    assert blind["te_ex_ante_mean"] < budget, "a blind book should not spend the budget"
    assert blind["turnover_annual"] < 0.3, "nothing to trade on means little trading"


def test_the_turnover_cap_binds_and_costs_return(small_universe):
    universe, params = small_universe
    capped, _ = run_cell(
        universe, AuditCell(0.20, 13, 0, turnover_cap=0.50), params, solver="scipy"
    )
    loose, _ = run_cell(universe, AuditCell(0.20, 13, 0, turnover_cap=None), params, solver="scipy")
    assert capped["turnover_annual"] < loose["turnover_annual"]
    assert capped["turnover_annual"] <= 0.50 * 1.05, (
        "the cap must hold on average; an earlier version dropped it inside the "
        "infeasibility fallback and this cell reported 70% against a 25% cap"
    )
    assert capped["repair_share"] < 0.25, (
        "a repair relaxes the cap, so a cell where most weeks are repairs is not "
        "measuring the cap at all"
    )


def test_a_dearer_spread_makes_the_solver_trade_less(small_universe):
    """
    Note what is NOT asserted: that the dearer cell has a higher cost drag. It
    usually does not, because the solver responds to a dearer spread by trading
    less, and less trading at a higher rate can cost less in total. That is the
    behaviour the turnover-shortfall curve exists to measure, and asserting the
    naive direction would have written the wrong economics into a test.
    """
    universe, params = small_universe
    cheap, _ = run_cell(universe, AuditCell(0.20, 13, 0), params, solver="scipy")
    dear, _ = run_cell(
        universe, AuditCell(0.20, 13, 0, cost_multiplier=3.0), params, solver="scipy"
    )
    assert dear["turnover_annual"] < cheap["turnover_annual"]


def test_the_spread_multiplier_charges_what_it_says(params):
    """The multiplier scales the half-spread and leaves the holding drag alone."""
    from signal_lab.harness.costs import CostModel

    one, three = CostModel(params), CostModel(params, spread_multiplier=3.0)
    assert three.half_spread("anything") == pytest.approx(3.0 * one.half_spread("anything"))
    assert three.annual_drag("anything") == pytest.approx(one.annual_drag("anything"))
    with pytest.raises(ValueError, match="must be positive"):
        CostModel(params, spread_multiplier=0.0)


# --- the grid and the bar ----------------------------------------------------


def test_the_base_cells_carry_no_hard_turnover_cap(params):
    """
    The owner reads 150% as an annual budget a high-conviction period may
    exceed, not a per-period wall (decisions/proposed/0024). Hard-capping the
    base cells measured the cap instead of the layer: it bound on half to nine
    tenths of rebalances. Restraint comes from the section 4 shadow cost, and
    hard caps stay where they belong -- in the turnover-shortfall experiment.
    """
    cells = grid_cells(params)
    base = [c for c in cells if c.tag in ("base", "oracle", "cost")]
    assert base and all(c.turnover_cap is None for c in base)
    caps = {c.turnover_cap for c in cells if c.tag == "turnover"}
    assert caps and None not in caps, "the uncapped case is the base cell, not run twice"
    assert caps <= {float(x) for x in params.require("audit.turnover_caps") if x is not None}


def test_rolling_one_year_turnover_is_reported_for_the_budget_question(small_universe):
    """
    A full-sample mean cannot say whether one conviction-rich year ran hot, so
    the rolling one-year distribution is reported. Which statistic the VETO
    reads is an owner decision (decisions/proposed/0024); this only measures it.
    """
    universe, params = small_universe
    row, _ = run_cell(universe, AuditCell(0.20, 13, 0), params, solver="scipy")
    assert row["turnover_cap"] is None
    assert np.isfinite(row["turnover_p95_rolling_1y"])
    assert row["turnover_max_rolling_1y"] >= row["turnover_p95_rolling_1y"] - 1e-12


def test_the_grid_covers_the_declared_cells_and_tags_the_stress_ones(params):
    cells = grid_cells(params)
    base = [c for c in cells if c.tag == "base"]
    expected = (
        len(params.require("audit.ic_grid"))
        * len(params.require("audit.horizon_weeks"))
        * params.require("audit.seeds")
    )
    assert len(base) == expected
    assert {c.tag for c in cells} == {"base", "oracle", "cost", "turnover"}
    assert all(c.ic == 1.0 for c in cells if c.tag == "oracle")
    assert {c.cost_multiplier for c in cells if c.tag == "cost"} == {2.0, 3.0}


def test_the_lean_grid_is_small_and_carries_no_stress_cells(params):
    cells = grid_cells(params, lean=True)
    assert len(cells) <= 6
    assert {c.tag for c in cells} == {"base"}


def test_required_ic_interpolates_and_says_when_it_is_a_bound():
    table = pd.DataFrame(
        [
            {"tag": "base", "horizon": 13, "ic": 0.02, "seed": 0, "net_ir": 0.10},
            {"tag": "base", "horizon": 13, "ic": 0.05, "seed": 0, "net_ir": 0.50},
            {"tag": "base", "horizon": 52, "ic": 0.02, "seed": 0, "net_ir": 0.05},
            {"tag": "base", "horizon": 52, "ic": 0.05, "seed": 0, "net_ir": 0.20},
        ]
    )
    out = required_ic(table, 0.30).set_index("horizon")
    assert out.loc[13, "required_ic"] == pytest.approx(0.02 + 0.03 * (0.20 / 0.40))
    assert out.loc[13, "note"] == "interpolated"
    assert np.isinf(out.loc[52, "required_ic"]), "a bar never reached is a bound, not a number"
    assert "not reached" in out.loc[52, "note"]


# --- the audit is not a run --------------------------------------------------


def test_the_audit_writes_no_run_to_the_results_store(small_universe, store):
    """
    SUBSTRATE section 2 and decisions/0023: the planted signal is a lookahead by
    construction, so an audit path must never be able to reach the leaderboard.
    Running a cell touches no store at all.
    """
    universe, params = small_universe
    run_cell(universe, AuditCell(0.05, 13, 0), params, solver="scipy")
    assert store.list_runs().empty
    assert store.summary()["n_runs"] == 0


def test_the_report_names_the_panel_and_the_params_it_ran_on(small_universe, tmp_path):
    from signal_lab.audit.report import write_outputs

    universe, params = small_universe
    row, _ = run_cell(universe, AuditCell(0.05, 13, 0), params, solver="scipy")
    table = pd.DataFrame([row])
    breadth = effective_breadth(universe.weekly[universe.holdable], universe.benchmark_weekly, [13])
    meta = {
        "run_id": "A-TEST",
        "source": "synthetic",
        "snapshot_id": universe.panel.snapshot_id,
        "panel_hash": universe.panel_hash(),
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "generated_at": "2026-09-11T00:00:00",
        "te_budget": 0.06,
        "first_date": row["first_date"],
        "last_date": row["last_date"],
        "n_rebalances": row["n_rebalances"],
        "solver": "scipy",
    }
    out = write_outputs(tmp_path / "audit", table, breadth, 0.30, meta)
    markdown = (out / "ruler.md").read_text(encoding="utf-8")
    html = (out / "ruler.html").read_text(encoding="utf-8")
    assert universe.panel_hash()[:16] in markdown and params.params_hash[:16] in markdown
    assert "lookahead by construction" in markdown and "Not a run" in html
    assert "http://" not in html and "https://" not in html, "the page loads nothing"
    assert (out / "cells.csv").exists() and (out / "summary.json").exists()


# --- the vetoes, and the stress tables ---------------------------------------


def test_a_cell_is_judged_against_the_real_veto_thresholds(params):
    """
    A cell that clears the bar on net IR but breaches the tracking-error or
    active-drawdown veto would be killed in phase 3. Counting it as clearing
    makes the bar optimistic, so every cell carries a verdict.
    """
    from signal_lab.audit.ladder import portfolio_veto_verdicts

    good = {
        "te_p95": 0.05,
        "max_active_drawdown": 0.12,
        "turnover_annual": 1.2,
        "max_cash": 0.15,
        "n_positions_max": 25,
    }
    assert portfolio_veto_verdicts(good, params)["passes_portfolio_vetoes"]

    breach = dict(good, max_active_drawdown=0.20)  # the 18% veto, 3x the 6% TE ceiling
    verdict = portfolio_veto_verdicts(breach, params)
    assert not verdict["passes_portfolio_vetoes"]
    assert "active_drawdown" in verdict["veto_detail"]

    absent = dict(good, te_p95=float("nan"))
    verdict = portfolio_veto_verdicts(absent, params)
    assert not verdict["passes_portfolio_vetoes"], "SUBSTRATE section 10: no input means fail"
    assert "no-input" in verdict["veto_detail"]


def test_the_bar_among_surviving_cells_is_never_easier_than_the_raw_bar():
    table = pd.DataFrame(
        [
            {
                "tag": "base",
                "horizon": 13,
                "ic": 0.02,
                "seed": 0,
                "net_ir": 0.10,
                "passes_portfolio_vetoes": True,
            },
            {
                "tag": "base",
                "horizon": 13,
                "ic": 0.05,
                "seed": 0,
                "net_ir": 0.50,
                "passes_portfolio_vetoes": False,
            },
            {
                "tag": "base",
                "horizon": 13,
                "ic": 0.10,
                "seed": 0,
                "net_ir": 0.60,
                "passes_portfolio_vetoes": True,
            },
        ]
    )
    raw = required_ic(table, 0.30).set_index("horizon")
    surviving = required_ic(table, 0.30, surviving_only=True).set_index("horizon")
    assert surviving.loc[13, "required_ic"] > raw.loc[13, "required_ic"], (
        "dropping a veto-breaching cell that cleared the bar must raise the required IC"
    )


def test_the_stress_tables_compare_one_horizon_with_itself(params):
    """
    The stress cells run at one horizon and the base cells span all four, so an
    unfiltered pivot made the 1x-spread column a four-horizon average and the
    2x and 3x columns single-horizon ones. Part of every apparent cost effect
    was the horizon mix.
    """
    from signal_lab.audit.report import summarise

    rows = []
    for h in (4, 13):
        for mult in (1.0, 2.0):
            rows.append(
                {
                    "tag": "base" if mult == 1.0 else "cost",
                    "horizon": h,
                    "ic": 0.05,
                    "seed": 0,
                    "net_ir": 0.4 if h == 4 else 0.2,
                    "cost_multiplier": mult,
                    "turnover_cap": 1.5,
                    "turnover_annual": 1.0,
                    "cost_drag_annual": 0.002,
                    "passes_portfolio_vetoes": True,
                }
            )
    breadth = effective_breadth(
        pd.DataFrame(
            np.random.default_rng(0).normal(0, 0.01, (200, 4)),
            index=pd.bdate_range("2015-01-02", periods=200, freq="W-FRI"),
            columns=list("ABCD"),
        ),
        pd.Series(0.0, index=pd.bdate_range("2015-01-02", periods=200, freq="W-FRI")),
        [4, 13],
    )
    summary = summarise(pd.DataFrame(rows), breadth, 0.30, {"stress_horizon": 13})
    assert summary["stress_horizon"] == 13
    horizons = {r.get("horizon") for r in summary["cost_stress"]}
    assert horizons == {None} or horizons == set(), "the pivot must not span horizons"
    assert all(abs(r["net_ir"] - 0.2) < 1e-9 for r in summary["cost_stress"]), (
        "only the stress horizon's cells should appear"
    )
