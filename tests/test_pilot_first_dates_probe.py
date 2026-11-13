"""
The first-dates probe (`scripts/pilot_first_dates_probe.py`; HANDOFF tasks 95 and 96) on task
93's synthetic fixture of test (b) (`test_phase2_pilot.runs_0070`'s cross-sectional cell).
What it asserts is the reading of decisions/0070's addendum of 2026-11-13 (the decisions/0040
prefill): the first book is the no-view book; on the first traded date the marginal created
shadow at zero trade is the prefill formula from params; with the shadow's coefficient at 0
the first trade above 1e-4 is on the second date. The instruments leave the run untouched.
Synthetic data only.
"""

# ruff: noqa: F811  (the fixtures are imported by name, as test_phase2_pilot does)
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pilot_first_dates_probe as probe  # noqa: E402
from test_phase2_pilot import pilot_inputs  # noqa: E402, F401
from test_phase2_rule import small_universe  # noqa: E402, F401

from signal_lab.audit import pilot  # noqa: E402
from signal_lab.portfolio import long_only, rebalance  # noqa: E402
from vetoes.rules import veto_lookahead  # noqa: E402


def _prefill_marginal_bps(params) -> float:
    """decisions/0040 item 2 from params alone: on the first traded date the trailing window
    is empty, so P = (W - 1) * target / ppy, and the marginal shadow at zero trade is
    coefficient * (ppy / W) * (P - start * W / ppy) / (reference - start), in bp."""
    ppy = float(params.get("costs.application.weeks_per_year", 52))
    w = int(round(ppy))
    target = float(params.require("constraints.turnover.target_annualised"))
    start = float(params.require("constraints.turnover.shadow_start_annualised"))
    reference = float(params.require("constraints.turnover.shadow_reference_annualised"))
    coefficient = float(params.require("constraints.turnover.penalty.coefficient"))
    p = (w - 1) * target / ppy
    return coefficient * (ppy / w) * max(0.0, p - start * w / ppy) / (reference - start)


@pytest.mark.slow
def test_the_prefill_holds_the_first_trade_and_without_it_the_view_trades_on_date_two(
    pilot_inputs,
):
    inputs, params, _ = pilot_inputs
    real = (rebalance.RebalanceStep.step, rebalance.solve, long_only._run)
    cell = pilot.PilotCell("cross_sectional", 0.35, 0)

    res = probe.probe_cell(inputs, cell, params, veto_lookahead, solver="scipy")
    table = res["table"]
    # the first book is the no-view book: built at a cost of 0, alpha 0, no engine row, no shadow
    assert bool(table["first"].iloc[0]) and bool(table["first_call_branch"].iloc[0])
    assert table["alpha_max_abs"].iloc[0] == 0.0
    assert np.isnan(table["engine_traded_notional"].iloc[0])
    assert np.isnan(table["shadow_marginal_bps_at_0"].iloc[0])
    # the view reaches the solve on the second date, against the half-spread over h ...
    assert table["alpha_max_abs"].iloc[1] > 0.0
    assert table["half_spread_divisor"].iloc[1] == pytest.approx(13.0)
    # ... and the created shadow there is the decisions/0040 prefill, to 1e-9
    assert table["shadow_form"].iloc[1] == "created"
    expected = _prefill_marginal_bps(params)
    assert expected > 0.0
    assert table["shadow_marginal_bps_at_0"].iloc[1] == pytest.approx(expected, abs=1e-9)

    # with the shadow's coefficient at 0 (an in-memory copy of params), the view trades at once
    zero = probe.with_shadow_coefficient(params, 0.0)
    assert params.require("constraints.turnover.penalty.coefficient") > 0  # not mutated
    res0 = probe.probe_cell(inputs, cell, zero, veto_lookahead, solver="scipy")
    t0 = res0["table"]
    assert (t0["shadow_marginal_bps_at_0"].iloc[1:] == 0.0).all()
    shown = t0[
        [
            "index",
            "alpha_max_abs",
            "best_pair_net_bps",
            "solve_turnover",
            "engine_traded_notional",
        ]
    ].head(18)
    assert res0["first_trade"] == {"date": str(t0.index[1].date()), "index": 1}, (
        f"{res0['first_trade']}\n{shown.to_string()}"
    )

    # the instruments are removed and changed nothing
    assert (rebalance.RebalanceStep.step, rebalance.solve, long_only._run) == real
    row, _, path = pilot.run_pilot_cell(
        inputs, cell, params, lookahead_veto=veto_lookahead, solver="scipy"
    )
    pd.testing.assert_series_equal(path.turnover, res["path"].turnover)
    assert row["net_ir"] == res["row"]["net_ir"]
    assert res["timing"]["n_solves"] == len(res["rule"].diagnostics)


def test_best_pair_net_takes_a_held_seller_and_another_buyer():
    ids = ["a", "b", "c"]
    alpha = pd.Series([3e-4, 1e-4, -2e-4], index=ids)
    w0 = pd.Series([0.0, 0.5, 0.5], index=ids)
    cost = pd.Series([1e-4, 1e-4, 1e-4], index=ids)
    gain, pair = probe.best_pair_net(alpha, w0, cost)
    # buy a (3e-4 - 1e-4), sell c (-2e-4 + 1e-4): 2e-4 + 1e-4 = 3e-4
    assert pair == "a/c"
    assert gain == pytest.approx(3e-4)
    # nothing held: no pair
    assert np.isnan(probe.best_pair_net(alpha, w0 * 0.0, cost)[0])
