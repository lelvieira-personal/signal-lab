"""
The block-shuffled baseline. decisions/0036 sections 4b and 5.

The acceptance tests are tests, not a one-off check, because the number they
guard would gate. The one that matters most for what follows is the fourth: the
shuffle switched off must reproduce the net IR the audit has always produced,
bit for bit, because the baseline cells are paired against live cells that
already exist (A-20260919-155557) instead of re-running them.
"""

from __future__ import annotations

import dataclasses
import hashlib

import numpy as np
import pandas as pd
import pytest

import signal_lab.audit.signals as signals_mod
from signal_lab.audit.ladder import (
    BASELINE,
    FRICTION_COEFFICIENTS,
    FRICTION_IC_RUNGS,
    FRICTION_SEEDS,
    HALFLIFE_ARMS,
    HALFLIFE_HORIZONS,
    HALFLIFE_IC_RUNGS,
    HALFLIFE_SEEDS,
    KNEE_IC_RUNGS,
    POWER10_IC_RUNGS,
    POWER10_PERMS,
    POWER10_SEEDS,
    POWER_IC_RUNGS,
    POWER_PERMS,
    POWER_SEEDS,
    AuditCell,
    baseline_cells,
    build_universe,
    friction_cells,
    grid_cells,
    halflife_cells,
    knee_cells,
    net_ir_excess,
    power10_cells,
    power_cells,
    run_cell,
)
from signal_lab.audit.signals import (
    BASELINE_BLOCK,
    SCORE_SHUFFLE,
    SPAN_SHUFFLE,
    plant_signal,
    realised_ic,
)
from signal_lab.loaders.base import ReturnPanel
from signal_lab.stats.blocks import (
    BASELINE_STREAM,
    baseline_rng,
    block_permutation,
    block_shuffle_rows,
    score_shuffle_rng,
    score_span_rng,
)

WEEKS = 260

# Recorded at the commit before the baseline was added (HEAD 37491a9 + the
# request-file commit), from this same construction. If either moves, the
# shuffle-off path is no longer today's.
GOLDEN_SCORE_HASH = "3c56e07462d30d6d"
# Re-recorded 2026-10-07 at one thread (decisions/0048; HANDOFF task 50); was
# -0.8793457503233992 with threads unset.
GOLDEN_NET_IR = -0.8792060912640641
# The truth shuffle's score and its permutation stream, recorded before the
# score shuffle was added (HEAD 0534478). HANDOFF task 25 requires the existing
# baseline call to reproduce today's stream exactly.
GOLDEN_TRUTH_BASELINE_HASH = "654969df17ddcd1a"
GOLDEN_BASELINE_RNG_1 = [308728382, 18655402, 1802871816]
# The task 25 `score` shuffle's score, recorded before `score_span` was added
# (HEAD 21ab064): HANDOFF task 30 leaves that mode exactly as it was.
GOLDEN_SCORE_SHUFFLE_HASH = "b40b2106fad807c4"


@pytest.fixture(scope="module")
def weekly() -> pd.DataFrame:
    rng = np.random.default_rng(4242)
    index = pd.bdate_range("2010-01-08", periods=WEEKS, freq="W-FRI")
    f = rng.normal(0, 0.02, (WEEKS, 2))
    load = rng.normal(0, 1, (8, 2))
    noise = rng.normal(0, 0.01, (WEEKS, 8))
    return pd.DataFrame(f @ load.T + noise, index=index, columns=[f"S{i}" for i in range(8)])


@pytest.fixture(scope="module")
def benchmark(weekly) -> pd.Series:
    return weekly.mean(axis=1)


@pytest.fixture(scope="module")
def ragged(weekly) -> pd.DataFrame:
    """The same panel with two series that start late, as the real one does."""
    out = weekly.copy()
    out.iloc[:90, out.columns.get_loc("S6")] = np.nan
    out.iloc[:150, out.columns.get_loc("S7")] = np.nan
    return out


@pytest.fixture(scope="module")
def small_universe(params, panel):
    from signal_lab.audit.universe import synthetic_universe

    audit = dict(params.audit)
    audit["covariance"] = {
        "estimator": "ledoit_wolf",
        "window_periods": 52,
        # decisions/0042: the live policy rides along, so a default cell here runs
        # the 26-week scalar overlay exactly as it does in the audit.
        "vol_overlay": dict(params.audit["covariance"]["vol_overlay"]),
    }
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


# --- the primitive -----------------------------------------------------------


@pytest.mark.parametrize("n", [0, 1, 51, 52, 53, 260, 999])
def test_a_block_permutation_is_a_permutation_of_whole_blocks(n):
    order = block_permutation(n, BASELINE_BLOCK, np.random.default_rng(0))
    assert sorted(order.tolist()) == list(range(n))
    # Inside a block the rows keep their order: the sequence can only jump where
    # a block ends (a multiple of the block length, or the end of the panel).
    for i in range(len(order) - 1):
        if order[i + 1] != order[i] + 1:
            assert (order[i] + 1) % BASELINE_BLOCK == 0 or order[i] + 1 == n


def test_one_permutation_serves_every_column_and_dates_do_not_move(weekly):
    shuffled = block_shuffle_rows(weekly, BASELINE_BLOCK, np.random.default_rng(3))
    assert shuffled.index.equals(weekly.index) and list(shuffled.columns) == list(weekly.columns)
    # Each output row is some input row, whole: the cross-section on a date survives.
    source = {tuple(np.round(r, 12)) for r in weekly.to_numpy()}
    assert all(tuple(np.round(r, 12)) in source for r in shuffled.to_numpy())
    assert not shuffled.equals(weekly)


def test_the_permutation_stream_is_not_the_seed_stream():
    assert BASELINE_STREAM != 0
    a = np.random.default_rng(7).standard_normal(5)
    b = baseline_rng(7).standard_normal(5)
    assert not np.allclose(a, b)


# --- section 4b -------------------------------------------------------------


def test_the_noise_draw_is_bit_identical_between_a_live_cell_and_its_baseline(
    weekly, benchmark, monkeypatch
):
    """4b.3. The permutation must not advance the generator the noise comes from."""
    draws: list[np.ndarray] = []
    original = signals_mod._ar1_noise

    def spy(*args, **kwargs):
        out = original(*args, **kwargs)
        draws.append(out.copy())
        return out

    monkeypatch.setattr(signals_mod, "_ar1_noise", spy)
    plant_signal(weekly, benchmark, ic=0.2, horizon=13, seed=5, vol_window=52)
    plant_signal(weekly, benchmark, ic=0.2, horizon=13, seed=5, vol_window=52, baseline=True)
    assert len(draws) == 2
    assert np.array_equal(draws[0], draws[1])


def test_a_baseline_never_gives_a_series_a_value_before_its_start(ragged, benchmark):
    """4b.2. Availability is the live cell's, exactly -- the `frequency` veto."""
    live = plant_signal(ragged, benchmark, ic=0.2, horizon=13, seed=2, vol_window=52)
    base = plant_signal(ragged, benchmark, ic=0.2, horizon=13, seed=2, vol_window=52, baseline=True)
    assert base.score.notna().equals(live.score.notna())
    assert base.alpha.notna().equals(live.alpha.notna())
    assert base.score["S7"].iloc[:150].isna().all()


def test_a_live_cell_and_its_baseline_have_different_keys():
    """4b.4. The store is append-only; a collision would be two runs under one key."""
    live = AuditCell(
        0.2, 13, 3, vol_halflife=None, shadow_form="trailing"
    )  # None: the pre-task-42 key
    base = AuditCell(
        0.2, 13, 3, tag=BASELINE, baseline=True, vol_halflife=None, shadow_form="trailing"
    )
    assert live.key() != base.key()
    assert base.key().endswith("_baseline")
    assert live.key() == "ic0.20_h13_s3_c1.0_tnone_rnone", "the live key is unchanged"


def test_the_baseline_grids_read_the_ladder_from_params_and_add_nothing_to_it(params):
    pilot = baseline_cells(params, "baseline-pilot")
    full = baseline_cells(params, "baseline")
    ics, seeds = params.require("audit.ic_grid"), int(params.require("audit.seeds"))
    horizons = params.require("audit.horizon_weeks")
    assert {c.horizon for c in pilot} == {13}
    assert len(pilot) == len(ics) * seeds
    assert len(full) == len(horizons) * len(ics) * seeds
    assert all(c.baseline and c.tag == BASELINE for c in pilot + full)
    assert not any(c.baseline for c in grid_cells(params)), "the default grid is untouched"
    assert len({c.key() for c in full}) == len(full)
    with pytest.raises(ValueError):
        baseline_cells(params, "everything")


def test_the_knee_grid_pairs_a_live_cell_with_its_baseline_at_rungs_outside_params(params):
    cells = knee_cells(params)
    seeds = int(params.require("audit.seeds"))
    assert len(cells) == len(KNEE_IC_RUNGS) * seeds * 2 == 60
    assert {c.horizon for c in cells} == {13}
    assert {c.ic for c in cells} == {0.35, 0.50, 0.70}
    assert not {c.ic for c in cells} & {float(x) for x in params.require("audit.ic_grid")}, (
        "the knee rungs are not in params/audit.yaml, and must not be added there"
    )
    assert sum(c.baseline for c in cells) == sum(not c.baseline for c in cells)
    assert len({c.key() for c in cells}) == len(cells), "a live cell and its twin never collide"
    # Every live cell has its baseline at the same coordinates, so the excess is defined.
    live = {(c.ic, c.seed) for c in cells if not c.baseline}
    twin = {(c.ic, c.seed) for c in cells if c.baseline}
    assert live == twin


# --- section 5 --------------------------------------------------------------


@pytest.mark.slow
def test_the_shuffle_switched_off_reproduces_todays_score_and_net_ir_bit_for_bit(
    weekly, benchmark, small_universe
):
    """
    GOLDEN_NET_IR was recorded under the pre-task-39 default (`trailing` at
    10bp); pinned explicitly here so this test stays about the SCORE
    construction, not about which shadow-cost form `params/` currently picks
    (decisions/0038, 0040 changed that default; see
    test_the_default_now_reads_created_marginal_from_params).
    """
    sig = plant_signal(weekly, benchmark, ic=0.10, horizon=13, seed=1, vol_window=52)
    digest = hashlib.sha256(np.ascontiguousarray(sig.score.to_numpy()).tobytes()).hexdigest()
    assert digest[:16] == GOLDEN_SCORE_HASH
    universe, params = small_universe
    row, _ = run_cell(
        universe,
        AuditCell(0.10, 13, 0, shadow_form="trailing", shadow_coefficient=10.0, vol_halflife=None),
        params,
        solver="scipy",
    )
    assert row["net_ir"] == GOLDEN_NET_IR


def test_the_baseline_carries_no_information_about_the_future_and_the_live_cell_does(
    weekly, benchmark
):
    live = plant_signal(weekly, benchmark, ic=0.5, horizon=13, seed=1, vol_window=52)
    base = plant_signal(weekly, benchmark, ic=0.5, horizon=13, seed=1, vol_window=52, baseline=True)
    assert realised_ic(live)["pooled"] == pytest.approx(0.5, abs=1e-9)
    assert abs(realised_ic(base)["pooled"]) < 0.25, "well below the 0.5 the live cell carries"
    assert base.truth.equals(live.truth), "`truth` stays the real forward truth"


def test_the_shuffle_stays_inside_the_panel_it_is_given(weekly, benchmark):
    """No observation crosses HOLDOUT_START: dates do not move, and none are added."""
    from signal_lab.loaders import holdout_start
    from signal_lab.params import get_params

    holdout = pd.Timestamp(holdout_start(get_params()))
    base = plant_signal(weekly, benchmark, ic=0.2, horizon=13, seed=0, vol_window=52, baseline=True)
    assert base.score.index.equals(weekly.index)
    assert base.score.index.max() < holdout


def test_a_baseline_cells_own_excess_is_zero_and_a_lone_live_cell_is_nan():
    table = pd.DataFrame(
        {
            "ic": [0.2, 0.2, 0.2],
            "horizon": [13, 13, 13],
            "seed": [0, 0, 1],
            "cost_multiplier": [1.0] * 3,
            "turnover_cap": [np.nan] * 3,
            "per_rebalance_cap": [np.nan] * 3,
            "baseline": [False, True, False],
            "net_ir": [0.50, 0.31, 0.44],
        }
    )
    excess = net_ir_excess(table)
    assert excess.iloc[0] == pytest.approx(0.19)
    assert excess.iloc[1] == 0.0
    assert np.isnan(excess.iloc[2]), "no baseline for seed 1 means no excess, not zero"


def test_an_oracle_cells_excess_is_close_to_its_net_ir_when_the_baseline_earns_the_floor():
    table = pd.DataFrame(
        {
            "ic": [1.0, 1.0],
            "horizon": [13, 13],
            "seed": [0, 0],
            "cost_multiplier": [1.0, 1.0],
            "turnover_cap": [np.nan, np.nan],
            "per_rebalance_cap": [np.nan, np.nan],
            "baseline": [False, True],
            "net_ir": [1.80, 0.31],
        }
    )
    assert net_ir_excess(table).iloc[0] == pytest.approx(1.49)


# --- HANDOFF task 25: the score shuffle -------------------------------------


def test_the_truth_shuffle_and_its_stream_are_unchanged_by_the_score_shuffle(weekly, benchmark):
    assert baseline_rng(1).integers(0, 2**31, 3).tolist() == GOLDEN_BASELINE_RNG_1
    sig = plant_signal(weekly, benchmark, ic=0.10, horizon=13, seed=1, vol_window=52, baseline=True)
    digest = hashlib.sha256(np.ascontiguousarray(sig.score.to_numpy()).tobytes()).hexdigest()
    assert digest[:16] == GOLDEN_TRUTH_BASELINE_HASH


def test_existing_keys_are_unchanged_and_a_score_cell_says_what_it_is():
    # `vol_halflife=None` throughout: the explicit "no overlay" is what keeps a
    # pre-task-42 key (decisions/0042 moved the default to the params overlay).
    plain = AuditCell(0.35, 13, 0, 1.0, None, 0.25, vol_halflife=None, shadow_form="trailing")
    assert plain.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25"
    truth = AuditCell(
        0.35,
        13,
        0,
        1.0,
        None,
        0.25,
        BASELINE,
        baseline=True,
        vol_halflife=None,
        shadow_form="trailing",
    )
    assert truth.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25_baseline"
    score = dataclasses.replace(truth, shuffle=SCORE_SHUFFLE, perm=7)
    assert score.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25_baseline_score_p07"


def test_a_score_shuffle_must_be_a_baseline():
    with pytest.raises(ValueError, match="baseline"):
        AuditCell(0.35, 13, 0, shuffle=SCORE_SHUFFLE)
    with pytest.raises(ValueError, match="perm"):
        AuditCell(0.35, 13, 0, baseline=True, perm=3)


def test_score_permutations_are_deterministic_distinct_and_not_the_other_streams():
    draw = lambda g: g.integers(0, 2**31, 8).tolist()  # noqa: E731
    assert draw(score_shuffle_rng(1, 4)) == draw(score_shuffle_rng(1, 4))
    assert draw(score_shuffle_rng(1, 4)) != draw(score_shuffle_rng(1, 5))
    assert draw(score_shuffle_rng(1, 0)) != draw(baseline_rng(1))
    assert draw(score_shuffle_rng(1, 0)) != draw(np.random.default_rng(1))


def test_the_score_shuffle_moves_the_live_score_whole_and_keeps_its_mask(ragged, benchmark):
    kw = dict(ic=0.35, horizon=13, seed=1, vol_window=52)
    live = plant_signal(ragged, benchmark, **kw)
    a = plant_signal(ragged, benchmark, **kw, baseline=True, shuffle=SCORE_SHUFFLE, perm=0)
    b = plant_signal(ragged, benchmark, **kw, baseline=True, shuffle=SCORE_SHUFFLE, perm=1)
    again = plant_signal(ragged, benchmark, **kw, baseline=True, shuffle=SCORE_SHUFFLE, perm=0)
    assert a.score.equals(again.score)
    assert not a.score.equals(b.score)
    assert a.score.notna().equals(live.score.notna()), "availability is the live cell's"
    # Every value is a live value or the neutral fill: the score moved, it was not redrawn.
    live_values = set(np.round(live.score.stack().to_numpy(), 12)) | {0.0}
    assert set(np.round(a.score.stack().to_numpy(), 12)) <= live_values
    # sigma is not shuffled; alpha is rebuilt from the shuffled score.
    assert a.sigma.equals(live.sigma)
    expected = 0.35 * a.sigma * a.score / np.sqrt(13)
    pd.testing.assert_frame_equal(a.alpha, expected)


def test_the_power_grid_is_80_score_cells_at_rungs_outside_params(params):
    cells = power_cells(params)
    assert len(cells) == len(POWER_IC_RUNGS) * len(POWER_SEEDS) * POWER_PERMS == 80
    assert all(c.baseline and c.shuffle == SCORE_SHUFFLE and c.horizon == 13 for c in cells)
    assert {c.ic for c in cells} == {0.35, 0.70} <= set(KNEE_IC_RUNGS)
    assert len({c.key() for c in cells}) == 80
    knee_keys = {c.key() for c in knee_cells(params)}
    assert not knee_keys & {c.key() for c in cells}, "nothing collides with the knee run"
    # Same constraints and costs as the knee cells, so the live twins pair.
    knee = next(c for c in knee_cells(params) if not c.baseline)
    assert {(c.cost_multiplier, c.turnover_cap, c.per_rebalance_cap) for c in cells} == {
        (knee.cost_multiplier, knee.turnover_cap, knee.per_rebalance_cap)
    }


def test_a_score_row_is_never_taken_as_the_paired_truth_baseline():
    table = pd.DataFrame(
        {
            "ic": [0.35, 0.35, 0.35],
            "horizon": [13, 13, 13],
            "seed": [0, 0, 0],
            "cost_multiplier": [1.0, 1.0, 1.0],
            "turnover_cap": [None, None, None],
            "per_rebalance_cap": [0.25, 0.25, 0.25],
            "baseline": [False, True, True],
            "shuffle": ["", SCORE_SHUFFLE, "truth"],
            "net_ir": [0.60, 0.90, 0.40],
        }
    )
    assert net_ir_excess(table).iloc[0] == pytest.approx(0.20)


# --- HANDOFF task 30: the span-limited score shuffle ------------------------


def _span_kw():
    return dict(ic=0.35, horizon=13, seed=1, vol_window=52, baseline=True)


def test_the_score_mode_is_bit_for_bit_unchanged_by_score_span(ragged, benchmark):
    sig = plant_signal(ragged, benchmark, **_span_kw(), shuffle=SCORE_SHUFFLE, perm=3)
    digest = hashlib.sha256(np.ascontiguousarray(sig.score.to_numpy()).tobytes()).hexdigest()
    assert digest[:16] == GOLDEN_SCORE_SHUFFLE_HASH


def test_a_span_cell_is_keyed_apart_and_existing_keys_are_unchanged():
    truth = AuditCell(
        0.70,
        13,
        0,
        1.0,
        None,
        0.25,
        BASELINE,
        baseline=True,
        vol_halflife=None,
        shadow_form="trailing",
    )
    assert truth.key() == "ic0.70_h13_s0_c1.0_tnone_r0.25_baseline"
    assert (
        dataclasses.replace(truth, shuffle=SCORE_SHUFFLE, perm=7).key()
        == "ic0.70_h13_s0_c1.0_tnone_r0.25_baseline_score_p07"
    )
    assert (
        dataclasses.replace(truth, shuffle=SPAN_SHUFFLE, perm=7).key()
        == "ic0.70_h13_s0_c1.0_tnone_r0.25_baseline_scorespan_p07"
    )
    with pytest.raises(ValueError, match="baseline"):
        AuditCell(0.70, 13, 0, shuffle=SPAN_SHUFFLE)


def test_span_permutations_are_deterministic_distinct_and_their_own_stream():
    draw = lambda g: g.integers(0, 2**31, 8).tolist()  # noqa: E731
    assert draw(score_span_rng(1, 4)) == draw(score_span_rng(1, 4))
    assert draw(score_span_rng(1, 4)) != draw(score_span_rng(1, 5))
    for other in (score_shuffle_rng(1, 4), baseline_rng(1), np.random.default_rng(1)):
        assert draw(score_span_rng(1, 4)) != draw(other)


def test_the_span_shuffle_keeps_full_history_column_means_exactly(ragged, benchmark):
    live = plant_signal(ragged, benchmark, **{**_span_kw(), "baseline": False})
    full = [c for c in ragged.columns if ragged[c].notna().all()]
    assert full and len(full) < ragged.shape[1]
    for perm in range(4):
        sh = plant_signal(ragged, benchmark, **_span_kw(), shuffle=SPAN_SHUFFLE, perm=perm)
        np.testing.assert_allclose(sh.score[full].mean(), live.score[full].mean(), atol=1e-12)
        assert sh.score.notna().equals(live.score.notna()), "availability is the live cell's"
        assert sh.sigma.equals(live.sigma)
        pd.testing.assert_frame_equal(sh.alpha, 0.35 * sh.sigma * sh.score / np.sqrt(13))


def test_the_span_shuffle_is_deterministic_moves_only_the_span_and_stays_in_dev(ragged, benchmark):
    from signal_lab.loaders.holdout import enforce_holdout

    live = plant_signal(ragged, benchmark, **{**_span_kw(), "baseline": False})
    a = plant_signal(ragged, benchmark, **_span_kw(), shuffle=SPAN_SHUFFLE, perm=0)
    b = plant_signal(ragged, benchmark, **_span_kw(), shuffle=SPAN_SHUFFLE, perm=1)
    again = plant_signal(ragged, benchmark, **_span_kw(), shuffle=SPAN_SHUFFLE, perm=0)
    assert a.score.equals(again.score)
    assert not a.score.equals(b.score)
    empty = ~live.score.notna().any(axis=1)
    assert empty.any() and a.score[empty].isna().all().all(), "no value enters the empty rows"
    assert a.score.index.equals(live.score.index)
    enforce_holdout(a.score.dropna(how="all").index)


def test_the_power10_grid_is_200_span_cells_outside_params(params):
    cells = power10_cells(params)
    assert len(cells) == len(POWER10_IC_RUNGS) * len(POWER10_SEEDS) * POWER10_PERMS == 200
    assert all(c.baseline and c.shuffle == SPAN_SHUFFLE and c.horizon == 13 for c in cells)
    assert {c.ic for c in cells} == {0.70} and {c.seed for c in cells} == set(range(10))
    assert len({c.key() for c in cells}) == 200
    other = {c.key() for c in [*knee_cells(params), *power_cells(params)]}
    assert not other & {c.key() for c in cells}, "nothing collides with the knee or power runs"
    knee = next(c for c in knee_cells(params) if not c.baseline)
    assert {(c.cost_multiplier, c.turnover_cap, c.per_rebalance_cap) for c in cells} == {
        (knee.cost_multiplier, knee.turnover_cap, knee.per_rebalance_cap)
    }


def test_the_power10_preflight_reads_a_cells_csv_from_before_the_shuffle_column(tmp_path):
    """The knee run predates `shuffle`; the first attempt at power10 died on that."""
    import json
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts")]
    import run_audit

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    run = tmp_path / POWER_LIVE_RUN
    run.mkdir()
    (run / "summary.json").write_text(json.dumps({"panel_hash": "p", "params_hash": "q"}))
    rows = [
        {"tag": "base", "baseline": b, "horizon": 13, "ic": 0.7, "seed": s, "net_ir": 0.1}
        for s in range(10)
        for b in (False, True)
    ]
    pd.DataFrame(rows).to_csv(run / "cells.csv", index=False)  # no `shuffle` column
    universe = SimpleNamespace(panel_hash=lambda: "p")
    params = SimpleNamespace(params_hash="q")
    cells = [SimpleNamespace(ic=0.7, seed=s) for s in range(10)]
    assert run_audit._power10_preflight(cells, universe, params, tmp_path) is None
    pd.DataFrame(rows[:-1]).to_csv(run / "cells.csv", index=False)  # seed 9's twin missing
    assert "seed=9" in run_audit._power10_preflight(cells, universe, params, tmp_path)
    assert run_audit._power10_preflight(cells, universe, SimpleNamespace(params_hash="x"), tmp_path)


# --- HANDOFF task 32: the shadow-cost override -------------------------------


@pytest.mark.slow
def test_shadow_coefficient_none_matches_params_exactly(small_universe):
    """An explicit override at the SAME value params already supplies must
    reproduce the default cell exactly -- read live rather than hardcoded, since
    `constraints.turnover.penalty.coefficient` is 40.0 as of decisions/0040,
    not task 32's original 10.0."""
    universe, params = small_universe
    coefficient = float(params.require("constraints.turnover.penalty.coefficient"))
    default_row, _ = run_cell(universe, AuditCell(0.20, 13, 0), params, solver="scipy")
    same, _ = run_cell(
        universe, AuditCell(0.20, 13, 0, shadow_coefficient=coefficient), params, solver="scipy"
    )
    assert same["net_ir"] == default_row["net_ir"]
    assert same["shadow_bps_mean"] == pytest.approx(default_row["shadow_bps_mean"])


@pytest.mark.slow
def test_a_different_shadow_coefficient_moves_weights_not_costs(small_universe):
    universe, params = small_universe
    cheap, _ = run_cell(
        universe, AuditCell(0.20, 13, 0, shadow_coefficient=10.0), params, solver="scipy"
    )
    dear, _ = run_cell(
        universe, AuditCell(0.20, 13, 0, shadow_coefficient=40.0), params, solver="scipy"
    )
    assert dear["shadow_bps_mean"] != pytest.approx(cheap["shadow_bps_mean"])
    assert dear["net_ir"] != cheap["net_ir"]


def test_existing_keys_are_unchanged_and_a_friction_cell_says_what_it_is():
    plain = AuditCell(0.35, 13, 0, 1.0, None, 0.25, vol_halflife=None, shadow_form="trailing")
    assert plain.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25"
    dear = dataclasses.replace(plain, shadow_coefficient=20.0)
    assert dear.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25_shadow20"


def test_the_friction_grid_is_60_live_cells_outside_params(params):
    cells = friction_cells(params)
    assert (
        len(cells)
        == len(FRICTION_IC_RUNGS) * len(FRICTION_SEEDS) * len(FRICTION_COEFFICIENTS)
        == 60
    )
    assert all(not c.baseline and c.horizon == 13 and c.tag == "base" for c in cells)
    assert {c.ic for c in cells} == set(FRICTION_IC_RUNGS) <= set(KNEE_IC_RUNGS)
    assert {c.shadow_coefficient for c in cells} == set(FRICTION_COEFFICIENTS)
    assert len({c.key() for c in cells}) == 60
    other = {c.key() for c in [*knee_cells(params), *power_cells(params)]}
    assert not other & {c.key() for c in cells}, "nothing collides with the knee or power runs"
    knee = next(c for c in knee_cells(params) if not c.baseline)
    assert {(c.cost_multiplier, c.turnover_cap, c.per_rebalance_cap) for c in cells} == {
        (knee.cost_multiplier, knee.turnover_cap, knee.per_rebalance_cap)
    }


# --- HANDOFF task 36: the created-turnover shadow, decisions/0040 -----------


@pytest.mark.slow
def test_an_explicit_trailing_override_reproduces_the_legacy_golden_bit_for_bit(small_universe):
    """
    `shadow_form="trailing"` is kept in code so a pre-0040 run reproduces
    exactly -- but the COEFFICIENT must also be pinned to 10.0, since
    `constraints.turnover.penalty.coefficient` in live params now carries
    0040's 40bp (there is no longer a separate "old" coefficient in params/).
    """
    universe, params = small_universe
    explicit, _ = run_cell(
        universe,
        AuditCell(0.10, 13, 0, shadow_form="trailing", shadow_coefficient=10.0, vol_halflife=None),
        params,
        solver="scipy",
    )
    assert explicit["net_ir"] == GOLDEN_NET_IR
    assert explicit["shadow_form"] == "trailing"


# GOLDEN_NET_IR_CREATED_MARGINAL: recorded 2026-09-30 (HANDOFF task 39), the
# first default-cell run after decisions/0038 and 0040 (created_marginal at
# 40bp). If this moves, something about the live default's pricing changed.
# Re-recorded 2026-10-07 at one thread (decisions/0048; HANDOFF task 50); was
# -0.3916592047250338 with threads unset.
GOLDEN_NET_IR_CREATED_MARGINAL = -0.3916378876353463


@pytest.mark.slow
def test_the_default_now_reads_created_marginal_from_params(small_universe):
    """
    HANDOFF task 39: `AuditCell.shadow_form=None` (the default, unset by any
    cell builder before this task) reads `constraints.turnover.penalty.form`
    from params rather than hard-coding `trailing` -- so `linear`
    (decisions/0018/0024's retired form) is not what a default cell reaches
    once `params/` adopts `created_marginal` (decisions/0040).
    """
    universe, params = small_universe
    # `vol_halflife=None`: the pre-task-42 default, no volatility overlay, so this
    # golden still isolates the shadow form (decisions/0042 moved the overlay default).
    row, _ = run_cell(universe, AuditCell(0.10, 13, 0, vol_halflife=None), params, solver="scipy")
    assert row["shadow_form"] == "created"
    assert row["net_ir"] == GOLDEN_NET_IR_CREATED_MARGINAL
    assert row["net_ir"] != GOLDEN_NET_IR, "the default's pricing changed, so its net IR must too"


# GOLDEN_NET_IR_V080: the same cell as GOLDEN_NET_IR_CREATED_MARGINAL at today's
# FULL default -- created_marginal at 40bp (decisions/0040) AND the 26-week scalar
# overlay (decisions/0042), params 0.8.0. Recorded 2026-10-01 (HANDOFF task 42)
# from a live `run_cell` call, not computed by hand.
# Re-recorded 2026-10-07 at one thread (decisions/0048; HANDOFF task 50); was
# -0.40475664238417963 with threads unset.
GOLDEN_NET_IR_V080 = -0.4046626602695416


@pytest.mark.slow
def test_the_full_default_cell_runs_the_overlay_and_reproduces_its_golden(small_universe):
    universe, params = small_universe
    row, _ = run_cell(universe, AuditCell(0.10, 13, 0), params, solver="scipy")
    assert row["vol_halflife"] == 26.0 and row["vol_overlay"] == "scalar"
    assert row["shadow_form"] == "created"
    assert row["key"].endswith("_vhl26scalar_created")
    assert row["net_ir"] == GOLDEN_NET_IR_V080
    assert row["net_ir"] != GOLDEN_NET_IR_CREATED_MARGINAL, "the overlay moves the weights"


def test_run_frictionless_records_a_key_computed_with_the_runs_params(small_universe):
    """F4: the recorded key follows the params the cell RAN under, not the process-wide
    ones. A params with no overlay block runs no overlay, and its key must say so."""
    from signal_lab.audit.ladder import FRICTIONLESS, run_frictionless

    universe, params = small_universe
    cell = AuditCell(0.10, 13, 0, 0.0, None, None, FRICTIONLESS)
    with_overlay, _ = run_frictionless(universe, cell, params)
    assert "_vhl26scalar" in with_overlay["key"]
    cov = {k: v for k, v in params.audit["covariance"].items() if k != "vol_overlay"}
    bare = dataclasses.replace(params, audit={**params.audit, "covariance": cov})
    row, _ = run_frictionless(universe, cell, bare)
    assert "_vhl" not in row["key"]


def test_a_shadow_form_cell_says_what_it_is_and_existing_keys_are_unchanged():
    trailing = AuditCell(
        0.35,
        13,
        0,
        1.0,
        None,
        0.25,
        shadow_coefficient=20.0,
        vol_halflife=None,
        shadow_form="trailing",
    )
    assert trailing.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25_shadow20"
    created = dataclasses.replace(trailing, shadow_form="created")
    assert created.key() == "ic0.35_h13_s0_c1.0_tnone_r0.25_shadow20_created"
    with pytest.raises(ValueError, match="shadow_form"):
        AuditCell(0.35, 13, 0, shadow_form="quadratic")


# --- HANDOFF task 35: the volatility-overlay halflife sweep (OWNER-QUEUE B1, L13) ---


def test_the_halflife_grid_is_240_live_cells_outside_params(params):
    cells = halflife_cells(params)
    assert (
        len(cells)
        == len(HALFLIFE_HORIZONS)
        * len(HALFLIFE_IC_RUNGS)
        * len(HALFLIFE_SEEDS)
        * len(HALFLIFE_ARMS)
        == 240
    )
    assert all(not c.baseline and c.tag == "base" for c in cells)
    assert {c.horizon for c in cells} == set(HALFLIFE_HORIZONS)
    assert {c.ic for c in cells} == set(HALFLIFE_IC_RUNGS) <= set(KNEE_IC_RUNGS)
    assert len({c.key() for c in cells}) == 240
    for c in cells:
        if c.vol_halflife is not None:
            assert c.vol_overlay == "scalar"


def test_a_halflife_none_arm_at_h13_matches_the_knee_live_cell_exactly(params):
    """The identity check the receipt reports: a `vol_halflife=None` h13 cell's
    key and constraints must be byte-identical to the knee run's live cell at
    the same (ic, seed) -- POWER_LIVE_RUN is that knee run."""
    knee = next(c for c in knee_cells(params) if not c.baseline)
    none_h13 = [c for c in halflife_cells(params) if c.horizon == 13 and c.vol_halflife is None]
    assert len(none_h13) == len(HALFLIFE_IC_RUNGS) * len(HALFLIFE_SEEDS)
    for c in none_h13:
        assert (c.cost_multiplier, c.turnover_cap, c.per_rebalance_cap) == (
            knee.cost_multiplier,
            knee.turnover_cap,
            knee.per_rebalance_cap,
        )
        # The knee grid follows params (task 42), so its cells now carry the 26-week
        # overlay; POWER_LIVE_RUN, the run this identity is with, was computed with none.
        twin = dataclasses.replace(
            knee, ic=c.ic, seed=c.seed, vol_halflife=None, shadow_form="trailing"
        )
        assert c.key() == twin.key()


def test_the_halflife_grid_orders_h13_first_then_h26_then_h4_with_arms_back_to_back(params):
    cells = halflife_cells(params)
    block = len(HALFLIFE_IC_RUNGS) * len(HALFLIFE_SEEDS) * len(HALFLIFE_ARMS)
    expected_horizons = [h for h in HALFLIFE_HORIZONS for _ in range(block)]
    assert [c.horizon for c in cells] == expected_horizons
    for i in range(0, len(cells), len(HALFLIFE_ARMS)):
        arm_group = cells[i : i + len(HALFLIFE_ARMS)]
        keys = {(c.horizon, c.ic, c.seed) for c in arm_group}
        assert keys == {(arm_group[0].horizon, arm_group[0].ic, arm_group[0].seed)}
        assert {c.vol_halflife for c in arm_group} == set(HALFLIFE_ARMS)


def test_the_halflife_preflight_checks_the_knee_run_at_every_ic_seed(tmp_path):
    import json
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts")]
    import run_audit

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    run = tmp_path / POWER_LIVE_RUN
    run.mkdir()
    (run / "summary.json").write_text(json.dumps({"panel_hash": "p", "params_hash": "q"}))
    rows = [
        {"tag": "base", "baseline": False, "horizon": 13, "ic": ic, "seed": s, "net_ir": 0.1}
        for ic in HALFLIFE_IC_RUNGS
        for s in HALFLIFE_SEEDS
    ]
    pd.DataFrame(rows).to_csv(run / "cells.csv", index=False)
    universe = SimpleNamespace(panel_hash=lambda: "p")
    params = SimpleNamespace(params_hash="q")
    cells = [SimpleNamespace(ic=ic, seed=s) for ic in HALFLIFE_IC_RUNGS for s in HALFLIFE_SEEDS]
    assert run_audit._halflife_preflight(cells, universe, params, tmp_path) is None
    pd.DataFrame(rows[:-1]).to_csv(run / "cells.csv", index=False)  # last (ic, seed) missing
    problem = run_audit._halflife_preflight(cells, universe, params, tmp_path)
    assert problem is not None and f"seed={HALFLIFE_SEEDS[-1]}" in problem
    assert run_audit._halflife_preflight(
        cells, universe, SimpleNamespace(params_hash="x"), tmp_path
    )


def _import_run_audit():
    import sys
    from pathlib import Path

    sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "scripts")]
    import run_audit

    return run_audit


def test_halflife_deadline_parses_an_offset_timestamp_and_is_none_when_unset():
    from datetime import datetime, timedelta, timezone

    run_audit = _import_run_audit()
    ts = run_audit._parse_halflife_deadline("2026-09-30T06:30:00-04:00")
    expected = datetime(2026, 9, 30, 6, 30, tzinfo=timezone(timedelta(hours=-4))).timestamp()
    assert ts == expected
    assert run_audit._parse_halflife_deadline(None) is None
    assert run_audit._parse_halflife_deadline("") is None


def test_halflife_should_stop_true_when_the_deadline_is_already_past():
    """Task 35's amendment: a deadline already past gives zero cells."""
    run_audit = _import_run_audit()
    assert (
        run_audit._halflife_should_stop(now_ts=2_000.0, deadline_ts=1_000.0, durations=[]) is True
    )


def test_halflife_should_stop_false_when_the_deadline_is_far_ahead():
    """Task 35's amendment: a deadline far ahead leaves the output unchanged
    (the grid never stops early)."""
    run_audit = _import_run_audit()
    assert (
        run_audit._halflife_should_stop(
            now_ts=1_000.0, deadline_ts=1_000_000.0, durations=[80.0, 90.0, 100.0]
        )
        is False
    )
    assert run_audit._halflife_should_stop(now_ts=1_000.0, deadline_ts=None, durations=[]) is False


def test_write_halflife_run_handles_zero_cells_without_crashing(tmp_path):
    """The deadline-already-past case: zero cells, a PARTIAL report, no crash."""
    import json
    import time
    from types import SimpleNamespace

    run_audit = _import_run_audit()
    universe = SimpleNamespace(
        panel_hash=lambda: "p", panel=SimpleNamespace(snapshot_id="synthetic-v1")
    )
    params = SimpleNamespace(params_hash="q", params_version="v0.5")
    args = SimpleNamespace(grid="halflife", source="synthetic", quiet=True)
    rc = run_audit._write_halflife_run(
        args, params, universe, pd.DataFrame(), "A-test-empty", tmp_path, time.time(), 240, True
    )
    assert rc == 0
    summary = json.loads((tmp_path / "A-test-empty" / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "PARTIAL"
    assert summary["n_cells"] == 0
    assert summary["n_cells_total"] == 240
    assert summary["per_horizon_cell_count"] == {}


def test_halflife_by_cell_summarises_a_small_fake_grid(tmp_path):
    """A hand-built table (no engine run) exercises the summary, paired-delta
    and flagging logic the real grid's cells.csv will feed."""
    from types import SimpleNamespace

    run_audit = _import_run_audit()
    rows = []
    for h in (13, 26):
        for ic in (0.35, 0.70):
            for s in (0, 1):
                for hl in (None, 13.0, 26.0, 52.0):
                    rows.append(
                        {
                            "horizon": h,
                            "ic": ic,
                            "seed": s,
                            "vol_halflife": hl,
                            "net_ir": 0.5 + (0.1 if hl is not None else 0.0) + 0.01 * s,
                            "veto_detail": "all four pass",
                            "bias_worst_annual": 1.2,
                            "bias_worst_year": 2008 if h == 13 else 2015,
                            "bias_stat": 1.0,
                            "te_p95": 0.05,
                            "te_p95_to_budget": 0.8,
                            "turnover_annual": 1.0,
                            "cost_drag_annual": 0.002,
                            "inaccurate_share": 0.0,
                            "infeasible_te_share": 0.0,
                        }
                    )
    table = pd.DataFrame(rows)
    universe = SimpleNamespace(panel_hash=lambda: "p")
    params = SimpleNamespace(params_hash="q")
    hashes, identity, by_hh, by_hh_ic, paired, flagged = run_audit._halflife_by_cell(
        table, universe, params, tmp_path
    )
    assert hashes["found"] is False  # no POWER_LIVE_RUN under this empty out_root
    assert identity is None
    assert len(by_hh) == 2 * 4  # 2 horizons x 4 halflife labels (including "none")
    assert len(paired) == 2 * 2 * 3  # 2 horizons x 2 ICs x 3 non-None arms
    np.testing.assert_allclose(paired["mean_diff"].to_numpy(), 0.1)
    assert (paired["n_positive"] == 2).all()
    assert flagged.empty


@pytest.mark.slow
def test_at_coefficient_zero_created_equals_trailing(small_universe):
    """A coefficient of zero prices no shadow under either form."""
    universe, params = small_universe
    trailing, _ = run_cell(
        universe,
        AuditCell(0.20, 13, 0, shadow_coefficient=0.0, shadow_form="trailing"),
        params,
        solver="scipy",
    )
    created, _ = run_cell(
        universe,
        AuditCell(0.20, 13, 0, shadow_coefficient=0.0, shadow_form="created"),
        params,
        solver="scipy",
    )
    assert created["net_ir"] == pytest.approx(trailing["net_ir"])
    assert created["shadow_bps_mean"] == pytest.approx(0.0, abs=1e-9)
    assert trailing["shadow_bps_mean"] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.slow
def test_the_created_form_actually_moves_weights_relative_to_trailing(small_universe):
    """A positive control: at a real coefficient the two forms must differ."""
    universe, params = small_universe
    trailing, _ = run_cell(
        universe,
        AuditCell(0.35, 13, 1, shadow_coefficient=40.0, shadow_form="trailing"),
        params,
        solver="scipy",
    )
    created, _ = run_cell(
        universe,
        AuditCell(0.35, 13, 1, shadow_coefficient=40.0, shadow_form="created"),
        params,
        solver="scipy",
    )
    assert created["net_ir"] != pytest.approx(trailing["net_ir"])


def test_prefilled_P_at_the_second_rebalance(small_universe):
    """
    decisions/0040 s2: at rebalance 2, exactly one trade is logged (from
    rebalance 1) and the rest of the `W - 1`-long window is prefilled at the
    100% target. `P` should equal `(W - 2) * target/ppy` plus that one trade.
    """
    from signal_lab.audit.ladder import _OptimiserRule, _plant

    universe, params = small_universe
    cell = AuditCell(0.20, 13, 0, shadow_form="created")
    signal = _plant(universe, cell)
    rule = _OptimiserRule(universe, signal, cell, params, "scipy")
    w_periods = int(round(rule.ppy))
    first_trade = 0.37
    rule.turnover_log.append(first_trade)
    expected = (w_periods - 2) * rule.target_annualised / rule.ppy + first_trade
    assert rule._prefilled_P() == pytest.approx(expected)


def test_the_friction_created_grid_is_60_cells_pairing_the_friction_grid(params):
    from signal_lab.audit.ladder import friction_created_cells

    trailing_cells = friction_cells(params)
    created_cells = friction_created_cells(params)
    assert len(created_cells) == 60
    assert all(c.shadow_form == "created" for c in created_cells)
    assert {c.key() for c in created_cells} & {c.key() for c in trailing_cells} == set()
    # Every other field matches its trailing twin exactly.
    trailing_by_id = {(c.ic, c.seed, c.shadow_coefficient): c for c in trailing_cells}
    for c in created_cells:
        twin = trailing_by_id[(c.ic, c.seed, c.shadow_coefficient)]
        assert dataclasses.replace(c, shadow_form="trailing") == twin
