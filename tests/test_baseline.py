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
    KNEE_IC_RUNGS,
    POWER_IC_RUNGS,
    POWER_PERMS,
    POWER_SEEDS,
    AuditCell,
    baseline_cells,
    build_universe,
    grid_cells,
    knee_cells,
    net_ir_excess,
    power_cells,
    run_cell,
)
from signal_lab.audit.signals import (
    BASELINE_BLOCK,
    SCORE_SHUFFLE,
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
)

WEEKS = 260

# Recorded at the commit before the baseline was added (HEAD 37491a9 + the
# request-file commit), from this same construction. If either moves, the
# shuffle-off path is no longer today's.
GOLDEN_SCORE_HASH = "3c56e07462d30d6d"
GOLDEN_NET_IR = -0.8793457503233992
# The truth shuffle's score and its permutation stream, recorded before the
# score shuffle was added (HEAD 0534478). HANDOFF task 25 requires the existing
# baseline call to reproduce today's stream exactly.
GOLDEN_TRUTH_BASELINE_HASH = "654969df17ddcd1a"
GOLDEN_BASELINE_RNG_1 = [308728382, 18655402, 1802871816]


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
    live, base = AuditCell(0.2, 13, 3), AuditCell(0.2, 13, 3, tag=BASELINE, baseline=True)
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


def test_the_shuffle_switched_off_reproduces_todays_score_and_net_ir_bit_for_bit(
    weekly, benchmark, small_universe
):
    sig = plant_signal(weekly, benchmark, ic=0.10, horizon=13, seed=1, vol_window=52)
    digest = hashlib.sha256(np.ascontiguousarray(sig.score.to_numpy()).tobytes()).hexdigest()
    assert digest[:16] == GOLDEN_SCORE_HASH
    universe, params = small_universe
    row, _ = run_cell(universe, AuditCell(0.10, 13, 0), params, solver="scipy")
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
    assert AuditCell(0.35, 13, 0, 1.0, None, 0.25).key() == "ic0.35_h13_s0_c1.0_tnone_r0.25"
    truth = AuditCell(0.35, 13, 0, 1.0, None, 0.25, BASELINE, baseline=True)
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
