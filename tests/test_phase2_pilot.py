"""
The phase-2 pilot's harness (HANDOFF task 90, decisions/0059 G and its addendum of 2026-11-10):
the axis-level plant (`audit.axis_signals`) and the pilot cell runner (`audit.pilot`).

Synthetic factors, the synthetic universe of `test_phase2_rule` and a hand-built exposure stub.
No vendor data, no store, nothing on or after 2020-01-01 except where a test hands such a date
over to see it refused.
"""

# ruff: noqa: F811  (the fixtures of test_phase2_rule are imported by name, as test_phase2_reports does)
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_phase2_rule import StubExposures, small_universe  # noqa: E402, F401

from signal_lab.audit import pilot  # noqa: E402
from signal_lab.audit.axis_signals import (  # noqa: E402
    check_score_dates,
    holdout_cutoff,
    plant_axis_signal,
    realised_ic,
)
from signal_lab.characteristics.exposures import REGION_COLUMNS, USAGE_COLUMNS  # noqa: E402
from signal_lab.loaders.holdout import HoldoutViolation  # noqa: E402
from signal_lab.measurement.factors import FACTOR_NAMES  # noqa: E402
from vetoes.rules import veto_lookahead  # noqa: E402

H = 13


def weekly_factor(columns, seed=0, start="2001-01-05", end="2019-12-27"):
    """Persistent weekly changes, one column per view; nothing on or after 2020-01-01."""
    index = pd.date_range(start, end, freq="W-FRI")
    rng = np.random.default_rng(seed)
    x = rng.normal(scale=0.01, size=(len(index), len(columns)))
    for t in range(1, len(index)):
        x[t] += 0.3 * x[t - 1]
    return pd.DataFrame(x, index=index, columns=columns)


@pytest.mark.parametrize("ic", [0.0, 0.10, 0.35])
@pytest.mark.parametrize("expression", ["directional", "cross_sectional"])
def test_the_planted_score_recovers_the_planted_ic(params, ic, expression):
    columns = ["d"] if expression == "directional" else ["US", "Japan", "EM", "Canada"]
    pooled = []
    for seed in range(5):
        plant = plant_axis_signal(weekly_factor(columns, seed), ic, H, seed, expression, params)
        got = realised_ic(plant)
        # each column carries the planted IC exactly (orthogonal noise scaled to the column)
        assert got["by_column_mean"] == pytest.approx(ic, abs=1e-9)
        pooled.append(got["pooled"])
    # pooled over columns it is the planted IC up to the columns' differing means
    assert np.mean(pooled) == pytest.approx(ic, abs=0.03)


@pytest.mark.parametrize("expression", ["directional", "cross_sectional"])
def test_the_noise_is_orthogonal_to_the_truth_per_column(params, expression):
    columns = ["d"] if expression == "directional" else ["US", "Japan", "EM"]
    ic = 0.20
    plant = plant_axis_signal(weekly_factor(columns, 3), ic, H, 3, expression, params)
    noise = (plant.score - ic * plant.blend_truth) / np.sqrt(1.0 - ic * ic)
    for column in columns:
        both = pd.concat([noise[column], plant.blend_truth[column]], axis=1).dropna()
        assert len(both) > 500
        assert abs(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]) < 1e-9


def test_no_score_date_is_within_the_horizon_of_the_holdout(params):
    plant = plant_axis_signal(weekly_factor(["d"]), 0.35, H, 0, "directional", params)
    cutoff = holdout_cutoff(H, params)
    assert plant.score.index[-1] <= cutoff
    assert plant.score.index[-1] + pd.Timedelta(weeks=H) < pd.Timestamp("2020-01-01")
    assert plant.score.notna().any(axis=1).iloc[-1]  # the frame ends on a scored date


def test_a_score_frame_that_reaches_past_the_cutoff_is_refused(params):
    late = pd.date_range("2019-09-06", "2019-12-27", freq="W-FRI")
    with pytest.raises(HoldoutViolation):
        check_score_dates(late, H, params)
    with pytest.raises(HoldoutViolation):
        check_score_dates(pd.DatetimeIndex(["2020-01-03"]), H, params)
    check_score_dates(late[late <= holdout_cutoff(H, params)], H, params)  # the early part is fine


def test_a_factor_frame_reaching_the_holdout_is_refused(params):
    factor = weekly_factor(["d"], end="2020-03-27")
    with pytest.raises(HoldoutViolation):
        plant_axis_signal(factor, 0.1, H, 0, "directional", params)


def test_an_ic_zero_cell_and_its_baseline_are_different_shuffles_of_the_same_seed(params):
    factor = weekly_factor(["US", "Japan", "EM"], 7)
    live = plant_axis_signal(factor, 0.0, H, 7, "cross_sectional", params)
    base = plant_axis_signal(factor, 0.0, H, 7, "cross_sectional", params, baseline=True)
    # the same real truth; the baseline blends from a block shuffle of it, the live cell from it
    pd.testing.assert_frame_equal(live.truth, base.truth)
    pd.testing.assert_frame_equal(live.blend_truth, live.truth)
    assert not base.blend_truth.equals(live.truth)
    a = np.sort(live.truth.stack().to_numpy())
    b = np.sort(base.blend_truth.where(live.truth.notna()).stack().to_numpy())
    assert len(a) == len(b)  # the same availability
    # the scores differ (noise orthogonalised against different truths) but share the seed's draw
    assert not base.score.equals(live.score)
    for column in factor.columns:
        both = pd.concat([live.score[column], base.score[column]], axis=1).dropna()
        assert np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1] > 0.9
    # another seed is another draw
    other = plant_axis_signal(factor, 0.0, H, 8, "cross_sectional", params)
    both = pd.concat([live.score["US"], other.score["US"]], axis=1).dropna()
    assert abs(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]) < 0.5


def test_the_cross_sectional_truth_sums_to_zero_across_regions(params):
    factor = weekly_factor(["US", "Japan", "EM", "Canada"], 2)
    plant = plant_axis_signal(factor, 0.2, H, 2, "cross_sectional", params)
    full = plant.truth.dropna()
    assert len(full) > 500
    assert np.abs(full.sum(axis=1)).max() < 1e-9


def test_the_grid_is_g_as_data():
    full = pilot.pilot_cells(pilot.PILOT_GRID)
    assert len(full) == 140
    assert len(pilot.pilot_cells(pilot.PILOT_SMOKE_GRID)) == 8
    live = [c for c in full if not c.baseline]
    assert {c.prior_multiplier for c in live if c.ic != pilot.PRIOR_IC} == {1.0}
    assert {c.prior_multiplier for c in live if c.ic == pilot.PRIOR_IC} == {0.5, 1.0, 2.0}
    for a, b in zip(full[::2], full[1::2], strict=True):  # each live cell is followed by its twin
        assert not a.baseline and b.baseline
        assert (a.expression, a.ic, a.seed, a.prior_multiplier) == (
            b.expression,
            b.ic,
            b.seed,
            b.prior_multiplier,
        )
    assert len({c.key() for c in full}) == len(full)


def test_ic_prior_is_varied_in_memory_never_in_params(params):
    before = params.require("constraints.views.ic_prior")
    doubled = pilot.with_ic_prior(params, 2 * before)
    assert doubled.require("constraints.views.ic_prior") == 2 * before
    assert params.require("constraints.views.ic_prior") == before
    assert doubled.params_hash == params.params_hash


# --- the cell runner on the synthetic universe ----------------------------------------------


class PilotStub(StubExposures):
    """The stub of `test_phase2_rule`, with the six factors, the region reporting columns, a
    usage log, and the last two ids without a row (as a store's tradable-only instruments)."""

    def __init__(self, ids, cash):
        super().__init__(ids, cash)
        n = len(self.frame)
        for k, name in enumerate(FACTOR_NAMES):
            self.frame[name] = np.linspace(-1.0 + 0.2 * k, 1.0 - 0.1 * k, n)
        regions = self.frame["region"]
        names = ["US", "Developed Europe", "Japan", "APAC ex-Japan", "Canada", "EM", "Global"]
        for col, region in zip(REGION_COLUMNS, names, strict=True):
            self.frame[col] = (regions == region).astype(float)
        self.unrowed = list(self.frame.index[-2:])
        self.frame = self.frame.drop(index=self.unrowed)
        self.cells = self.cells.drop(index=self.unrowed)
        self._usage = []

    def at(self, date):
        frame = self.frame.copy()
        self._usage.append(
            pd.DataFrame(
                {
                    "instrument": frame.index.astype(str),
                    "parameter": "loadings",
                    "store_week": pd.Timestamp(date),
                    "fitted_through": pd.Timestamp(date),
                    "used_on_date": pd.Timestamp(date),
                }
            )
        )
        return frame

    def axis(self, name, date):
        self.at(date)
        return super().axis(name, date)

    def usage(self):
        if not self._usage:
            return pd.DataFrame(columns=list(USAGE_COLUMNS))
        return pd.concat(self._usage, ignore_index=True).drop_duplicates()


@pytest.fixture(scope="module")
def pilot_inputs(small_universe):
    universe, params = small_universe
    stub = PilotStub(universe.holdable, set(universe.cash))
    index = universe.weekly.index
    rng = np.random.default_rng(11)
    factors = pd.DataFrame(
        rng.normal(scale=0.002, size=(len(index), len(FACTOR_NAMES))),
        index=index,
        columns=list(FACTOR_NAMES),
    )
    overlay = pd.Series(1.0, index=index)
    inputs = pilot.build_inputs(
        universe, stub, factors, params, benchmark_equity="SYN_EQ", overlay=overlay
    )
    return inputs, params, stub


def test_the_rowed_universe_drops_instruments_without_a_row(pilot_inputs):
    inputs, _, stub = pilot_inputs
    rowed = pilot.RowedUniverse(inputs.universe, inputs.rowed)
    date = inputs.universe.audit_dates()[5]
    rowed.covariance(date)
    assert set(stub.unrowed) <= set(inputs.universe.holdable)
    assert not set(stub.unrowed) & set(rowed.holdable)
    assert rowed.weekly is inputs.universe.weekly  # everything else is the universe's


@pytest.mark.slow
@pytest.mark.parametrize("expression", ["directional", "cross_sectional"])
def test_a_pilot_row_has_every_reported_field(pilot_inputs, expression):
    inputs, params, stub = pilot_inputs
    rows = []
    for baseline in (False, True):
        cell = pilot.PilotCell(expression, 0.35, 0, baseline=baseline)
        row, rule, path = pilot.run_pilot_cell(
            inputs, cell, params, lookahead_veto=veto_lookahead, solver="scipy"
        )
        assert set(pilot.ROW_FIELDS) <= set(row)
        assert row["lookahead_passed"], row["lookahead_detail"]
        assert row["status"] == "ok"
        assert np.isfinite(row["net_ir"]) and np.isfinite(row["turnover_annual"])
        assert np.isfinite(row["equity_tracking_variance_share"])
        assert row["n_rebalances"] > 10
        # no weight on an instrument without a row, at any rebalance
        held = path.weights.reindex(columns=stub.unrowed).fillna(0.0)
        assert float(held.abs().to_numpy().max()) == 0.0
        rows.append(row)
    table = pilot.with_excess(pd.DataFrame(rows))
    live = table[~table["baseline"]]
    assert live["net_ir_excess"].iloc[0] == pytest.approx(rows[0]["net_ir"] - rows[1]["net_ir"])
    summary = pilot.summarise(pd.DataFrame(rows))
    assert len(summary) == 1 and summary["n"].iloc[0] == 1


# --- HANDOFF task 91: the diagnostic arms --------------------------------------------------


def test_the_diag_grid_is_task_91_as_data():
    cells = pilot.diag_cells()
    assert len(cells) == 14
    assert len({c.key() for c in cells}) == 14
    assert not any(c.baseline for c in cells)
    assert {c.seed for c in cells} == {pilot.DIAG_SEED}
    for expression in pilot.AXIS_OF_EXPRESSION:
        mine = [c for c in cells if c.expression == expression]
        assert [c.ic for c in mine if c.zero_scores] == [0.0]
        sized = [c for c in mine if not c.zero_scores and not c.frictionless]
        assert sorted(c.prior_multiplier for c in sized) == [1.0, 2.0, 4.0, 8.0]
        assert {c.ic for c in sized} == {pilot.DIAG_IC}
        assert sorted(c.ic for c in mine if c.frictionless) == [0.0, pilot.DIAG_IC]
    assert pilot.PilotCell("directional", 0.0, 0, zero_scores=True).key().endswith("_noview")
    assert (
        pilot.PilotCell("directional", 0.35, 0, frictionless=True).key().endswith("_frictionless")
    )


@pytest.fixture(scope="module")
def diag_runs(pilot_inputs):
    inputs, params, _ = pilot_inputs
    out = {}
    arms = {
        "x1": pilot.PilotCell("cross_sectional", 0.35, 0),
        "x2": pilot.PilotCell("cross_sectional", 0.35, 0, 2.0),
        "noview": pilot.PilotCell("cross_sectional", 0.0, 0, zero_scores=True),
        "frictionless": pilot.PilotCell("cross_sectional", 0.35, 0, frictionless=True),
    }
    for name, cell in arms.items():
        keep = {}
        row, rule, path = pilot.run_pilot_cell(
            inputs, cell, params, lookahead_veto=veto_lookahead, solver="scipy", keep=keep
        )
        out[name] = (row, rule, path, keep)
    return out, params


@pytest.mark.slow
def test_the_no_view_book_has_no_view_and_no_alpha(diag_runs):
    runs, _ = diag_runs
    row, rule, _, _ = runs["noview"]
    assert float(rule.scores.abs().to_numpy().max()) == 0.0
    assert float(rule.z.abs().to_numpy().max()) == 0.0
    assert float(rule.views.fillna(0.0).abs().to_numpy().max()) == 0.0
    alpha = rule.alpha().fillna(0.0)
    assert float(alpha.abs().to_numpy().max()) == 0.0
    assert row["zero_scores"] and row["status"] == "ok"


@pytest.mark.slow
def test_the_multiplier_arm_scales_every_view(diag_runs):
    runs, params = diag_runs
    one, two = runs["x1"][1], runs["x2"][1]
    assert runs["x2"][0]["ic_prior"] == pytest.approx(
        2 * params.require("constraints.views.ic_prior")
    )
    # the same plant: the z-scores are identical and the views are exactly twice
    pd.testing.assert_frame_equal(one.z, two.z)
    pd.testing.assert_frame_equal(2.0 * one.views, two.views)
    # the first solve's alpha does not depend on the book, so it is exactly twice
    first = min(one._alpha_rows)
    pd.testing.assert_series_equal(2.0 * one._alpha_rows[first], two._alpha_rows[first])


@pytest.mark.slow
def test_the_frictionless_switch_turns_off_the_spread_and_the_shadow(diag_runs):
    runs, _ = diag_runs
    row, rule, _, keep = runs["frictionless"]
    hold = list(rule.u.holdable)
    assert float(keep["costs"].half_spread_vector(hold).abs().max()) == 0.0
    assert rule.shadow_coeff == 0.0
    diag = pd.DataFrame(rule.diagnostics)
    assert float(diag["shadow_bps"].abs().max()) == 0.0
    assert row["frictionless"] and np.isfinite(row["gross_ir"])
    # the live arm pays a spread; the frictionless one does not
    assert float(runs["x1"][3]["costs"].half_spread_vector(hold).max()) > 0.0


@pytest.mark.slow
def test_one_date_by_hand_matches_the_rule(diag_runs):
    runs, params = diag_runs
    rule = runs["x1"][1]
    dates = sorted(rule.books)
    date = dates[len(dates) // 2]
    check = pilot.hand_check(rule, date, params)
    assert check["max_gap_z"] < 1e-12
    assert check["max_gap_view"] < 1e-12
    assert check["max_gap_alpha"] < 1e-12
    # and without the library: v = ic_prior / sqrt(h) * sigma * (z - mean z)
    z = rule.z.loc[date]
    scale = params.require("constraints.views.ic_prior") / np.sqrt(13)
    hand = scale * rule.sigma.loc[date] * (z - z[z.notna()].mean())
    np.testing.assert_allclose(
        rule.views.loc[date].fillna(0.0).to_numpy(), hand.fillna(0.0).to_numpy(), atol=1e-15
    )


@pytest.mark.slow
def test_the_arithmetic_table_is_derived_from_the_alpha_and_the_costs(diag_runs):
    runs, _ = diag_runs
    _, rule, _, keep = runs["x1"]
    table = pilot.alpha_arithmetic(rule, keep["costs"])
    assert len(table) == len(rule._alpha_rows)
    date = sorted(rule._alpha_rows)[3]
    top = float(rule._alpha_rows[date].abs().max())
    assert float(table.loc[date, "max_abs_alpha_annual_bp"]) == pytest.approx(top * 52 / 1e-4)
    rt = 2 * float(table.loc[date, "half_spread_bp"]) + 2 * float(
        table.loc[date, "shadow_marginal_bp"]
    )
    assert float(table.loc[date, "round_trip_bp"]) == pytest.approx(rt)
