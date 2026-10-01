"""
HANDOFF task 42: the volatility overlay is policy (decisions/0042), the gate is the
generalized stepdown (decisions/0043), the turnover highlight is shown (decisions/
0038), and decisions/0040's shadow cost has one implementation.

Every test here is wiring: no engine run. The bit-for-bit goldens that do run the
engine live beside their siblings in `tests/test_baseline.py`.
"""

from __future__ import annotations

import dataclasses
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from signal_lab.audit.ladder import (
    FROM_PARAMS,
    AuditCell,
    baseline_cells,
    friction_cells,
    friction_created_cells,
    grid_cells,
    halflife_cells,
    knee_cells,
    portfolio_veto_verdicts,
    power10_cells,
    power_cells,
    resolve_vol_overlay,
)
from signal_lab.harness.objective import (
    annual_turnover_penalty,
    created_marginal_quadratic,
    created_marginal_shadow,
    prefilled_trailing_traded,
)
from signal_lab.harness.run_context import RunContext
from signal_lab.params import PARAM_FILES, load_params
from signal_lab.stats.multiple_testing import gate, romano_wolf, romano_wolf_gfwer, verdict_for
from vetoes.rules import veto_multiple_testing

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "render")]

import static_report  # noqa: E402
import views as v  # noqa: E402


def variant(tmp_path, params, filename, old, new):
    """The live params with one substring replaced in one file."""
    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / filename
    text = target.read_text()
    assert old in text, f"{old!r} is not in {filename}"
    target.write_text(text.replace(old, new))
    return load_params(tmp_path)


# --- 1. the overlay as the default (decisions/0042) --------------------------


def test_live_params_carry_the_26_week_scalar_overlay_and_a_default_cell_resolves_it(params):
    """Guards the lookup path itself: a misspelled path would read as "no overlay"."""
    assert params.get("audit.covariance.vol_overlay.halflife_weeks") == 26
    cell = AuditCell(0.35, 13, 0)
    assert cell.vol_halflife is FROM_PARAMS and cell.vol_overlay is FROM_PARAMS
    assert resolve_vol_overlay(cell, params) == (26.0, "scalar")
    assert cell.key(params).endswith("_vhl26scalar_created")  # default shadow form too


def test_none_keeps_meaning_no_overlay_and_keeps_every_historical_key(params):
    cell = AuditCell(0.35, 13, 0, 1.0, None, 0.25, vol_halflife=None, shadow_form="trailing")
    assert resolve_vol_overlay(cell, params) == (None, "per_series")
    assert cell.key(params) == "ic0.35_h13_s0_c1.0_tnone_r0.25"
    # an explicit overlay name with no halflife is still no overlay
    assert resolve_vol_overlay(dataclasses.replace(cell, vol_overlay="scalar"), params)[0] is None


def test_an_explicit_value_wins_and_a_bare_halflife_is_the_legacy_per_series_form(params):
    assert resolve_vol_overlay(AuditCell(0.1, 13, 0, vol_halflife=13), params) == (
        13.0,
        "per_series",
    )
    both = AuditCell(0.1, 13, 0, vol_halflife=52, vol_overlay="scalar")
    assert resolve_vol_overlay(both, params) == (52.0, "scalar")
    assert "_vhl52scalar" in both.key(params)
    # the halflife from params, the overlay form explicit
    form_only = AuditCell(0.1, 13, 0, vol_overlay="per_series")
    assert resolve_vol_overlay(form_only, params) == (26.0, "per_series")


def test_params_without_an_overlay_block_mean_no_overlay(tmp_path, params):
    bare = variant(
        tmp_path,
        params,
        "audit.yaml",
        "  vol_overlay:\n    form: scalar\n",
        "  _x:\n    form: scalar\n",
    )
    assert resolve_vol_overlay(AuditCell(0.1, 13, 0), bare) == (None, "per_series")


def test_the_overlay_follows_params_when_params_change(tmp_path, params):
    other = variant(tmp_path, params, "audit.yaml", "halflife_weeks: 26", "halflife_weeks: 13")
    assert resolve_vol_overlay(AuditCell(0.1, 13, 0), other) == (13.0, "scalar")


def test_a_live_cell_and_its_baseline_twin_resolve_to_the_same_overlay(params):
    for cells in (knee_cells(params), baseline_cells(params, "baseline-pilot")):
        assert {resolve_vol_overlay(c, params) for c in cells} == {(26.0, "scalar")}
    live = [c for c in knee_cells(params) if not c.baseline]
    twin = [c for c in knee_cells(params) if c.baseline]
    assert len(live) == len(twin) > 0
    for a, b in zip(live, twin, strict=True):
        assert resolve_vol_overlay(a, params) == resolve_vol_overlay(b, params)
        assert a.key(params) == b.key(params).replace("_baseline", "")
    # the standing grid's base cells and the baseline grid's are twins too
    grid = {resolve_vol_overlay(c, params) for c in grid_cells(params)}
    assert grid == {(26.0, "scalar")}


@pytest.mark.parametrize(
    "builder", [power_cells, power10_cells, friction_cells, friction_created_cells]
)
def test_grids_that_claim_identity_with_a_named_run_pin_no_overlay(builder, params):
    cells = builder(params)
    assert cells and all(c.vol_halflife is None for c in cells)
    assert {resolve_vol_overlay(c, params) for c in cells} == {(None, "per_series")}
    assert not any("_vhl" in c.key(params) for c in cells), "their keys are the pre-task-42 keys"


def test_a_default_cells_key_says_it_priced_turnover_created(params):
    """F3: the key encodes the RESOLVED shadow form, so the default cell and the
    halflife grid's h26 arm (pinned trailing, same overlay) are different cells."""
    default = AuditCell(0.35, 26, 0, 1.0, None, None)
    assert default.key(params) == "ic0.35_h26_s0_c1.0_tnone_rnone_vhl26scalar_created"
    arm = next(
        c
        for c in halflife_cells(params)
        if (c.horizon, c.ic, c.seed, c.vol_halflife) == (26, 0.35, 0, 26)
    )
    assert arm.key(params) == "ic0.35_h26_s0_c1.0_tnone_rnone_vhl26scalar"
    assert default.key(params) != arm.key(params)
    # explicit created keeps its key; trailing keeps its; frictionless prices nothing
    created = dataclasses.replace(default, shadow_coefficient=10.0, shadow_form="created")
    assert created.key(params).endswith("_shadow10_created")
    assert not dataclasses.replace(default, shadow_form="trailing").key(params).endswith("created")
    frictionless = dataclasses.replace(default, tag="frictionless")
    assert frictionless.key(params).endswith("_vhl26scalar_frictionless")
    assert all(c.key(params).endswith("_created") for c in friction_created_cells(params))
    assert not any(c.key(params).endswith("_created") for c in friction_cells(params))


def test_the_halflife_grid_sets_every_arm_explicitly(params):
    cells = halflife_cells(params)
    assert all(
        c.vol_halflife is not FROM_PARAMS and c.vol_overlay is not FROM_PARAMS for c in cells
    )
    none_arm = [c for c in cells if c.vol_halflife is None]
    assert none_arm and all("_vhl" not in c.key(params) for c in none_arm)


# --- 2. the gate as one callable (decisions/0043) ----------------------------


def _draws(m=6, k=100, seed=0, lift=(6.0, 5.0)):
    rng = np.random.default_rng(seed)
    T0 = rng.normal(size=(k, m))
    t = rng.normal(size=m)
    t[: len(lift)] = lift
    return t, T0


def test_gate_reproduces_romano_wolf_gfwer_exactly_and_reports_what_it_ran(params):
    t, T0 = _draws(m=12)  # >= small_search_below, so g = 2 (decisions/0045)
    out = gate(t, T0, params)
    reject, p_adj = romano_wolf_gfwer(t, T0, 0.05, 2, True)
    assert out["rejected"].tolist() == reject.tolist()
    assert np.array_equal(out["p_adjusted"], p_adj)
    assert (out["procedure"], out["fwer_alpha"], out["g"]) == ("romano_wolf_gfwer", 0.05, 2)
    assert (out["n_shuffles"], out["n_tests"], out["standardise"]) == (100, 12, True)
    assert out["rejected"].shape == out["p_adjusted"].shape == (12,)


def test_gate_reads_params_not_constants(tmp_path, params):
    t, T0 = _draws(m=12)
    g3 = variant(tmp_path, params, "vetoes.yaml", "  g: 2\n", "  g: 3\n")
    out = gate(t, T0, g3)
    assert out["g"] == 3
    assert out["rejected"].tolist() == romano_wolf_gfwer(t, T0, 0.05, 3, True)[0].tolist()
    assert out["p_adjusted"].tolist() != gate(t, T0, params)["p_adjusted"].tolist()


def test_a_small_search_runs_at_g1_and_the_floor_is_eight(params):
    """decisions/0045: m = 1 reports g = 1, m = 8 reports g = 2; procedure unchanged."""
    for m, g in ((1, 1), (7, 1), (8, 2), (12, 2)):
        t, T0 = _draws(m=m, lift=(6.0,))
        out = gate(t, T0, params)
        assert (out["g"], out["procedure"]) == (g, "romano_wolf_gfwer"), m
        assert out["rejected"].tolist() == romano_wolf_gfwer(t, T0, 0.05, g, True)[0].tolist()
    assert verdict_for(out, 0)["standardise"] is True


def test_a_single_test_under_a_complete_null_rejects_about_alpha_of_the_time(params):
    """F1: before decisions/0045 this was 1.00 -- at g = 2 one test has no second
    false pass to guard against, its critical value was -inf, and it always passed."""
    rng = np.random.default_rng(20261001)
    rejected = sum(
        bool(gate(rng.normal(size=1), rng.normal(size=(100, 1)), params)["rejected"][0])
        for _ in range(2000)
    )
    assert 0.03 <= rejected / 2000 <= 0.07, rejected / 2000


def test_gate_runs_romano_wolf_if_params_say_so(tmp_path, params):
    t, T0 = _draws()
    rw = variant(
        tmp_path, params, "vetoes.yaml", "procedure: romano_wolf_gfwer", "procedure: romano_wolf"
    )
    out = gate(t, T0, rw)
    assert (out["procedure"], out["g"]) == ("romano_wolf", 1)
    assert out["rejected"].tolist() == romano_wolf(t, T0, 0.05, True)[0].tolist()


def test_gate_refuses_a_procedure_that_is_not_a_gate(tmp_path, params):
    t, T0 = _draws()
    bad = variant(
        tmp_path, params, "vetoes.yaml", "procedure: romano_wolf_gfwer", "procedure: holm"
    )
    with pytest.raises(ValueError, match="holm"):
        gate(t, T0, bad)


def test_gate_raises_below_min_shuffles(params):
    t, T0 = _draws(k=99)
    with pytest.raises(ValueError, match="99.*100|100.*99"):
        gate(t, T0, params)


def test_the_veto_passes_on_the_gates_own_output_for_a_rejected_hypothesis(params):
    t, T0 = _draws(m=12, lift=(25.0,))
    t[1:] = 0.0  # nothing else near the null's tail
    out = gate(t, T0, params)
    assert out["rejected"][0] and not out["rejected"][1:].any()
    ctx = lambda i: RunContext(run_id="R", romano_wolf=verdict_for(out, i))  # noqa: E731
    assert veto_multiple_testing(ctx(0), params).passed
    assert not veto_multiple_testing(ctx(1), params).passed, "an unrejected hypothesis fails"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: {**d, "g": 3},
        lambda d: {**d, "n_shuffles": 99},
        lambda d: {k: x for k, x in d.items() if k != "g"},
        lambda d: {k: x for k, x in d.items() if k != "n_shuffles"},
        lambda d: {k: x for k, x in d.items() if k != "n_tests"},
        lambda d: {k: x for k, x in d.items() if k != "standardise"},
        lambda d: {**d, "standardise": False},
    ],
    ids=[
        "wrong-g",
        "too-few-shuffles",
        "missing-g",
        "missing-n_shuffles",
        "missing-n_tests",
        "missing-standardise",
        "standardise-false",
    ],
)
def test_the_veto_fails_a_gate_verdict_that_is_not_the_params_test(mutate, params):
    t, T0 = _draws(m=12, lift=(25.0,))
    verdict = verdict_for(gate(t, T0, params), 0)
    assert veto_multiple_testing(RunContext(run_id="R", romano_wolf=verdict), params).passed
    bent = mutate(verdict)
    assert not veto_multiple_testing(RunContext(run_id="R", romano_wolf=bent), params).passed


# --- 3. the turnover highlight (decisions/0038) -------------------------------


def _row(annual=1.0, p95=1.0, rmax=1.0):
    return {
        "turnover_annual": annual,
        "turnover_p95_rolling_1y": p95,
        "turnover_max_rolling_1y": rmax,
        "bias_worst_annual": 1.0,
        "max_cash": 0.1,
        "n_positions_max": 20,
    }


def test_highlight_on_annual_only(params):
    assert portfolio_veto_verdicts(_row(annual=2.4), params)["turnover_highlight"] is True


def test_highlight_on_rolling_p95_only(params):
    assert portfolio_veto_verdicts(_row(p95=2.4), params)["turnover_highlight"] is True


def test_rolling_max_alone_is_reported_not_highlighted(params):
    assert portfolio_veto_verdicts(_row(rmax=5.0), params)["turnover_highlight"] is False


def test_exactly_at_the_threshold_is_not_highlighted(params):
    cap = float(params.require("constraints.turnover.highlight_annualised"))
    assert cap == 2.00
    assert portfolio_veto_verdicts(_row(annual=cap, p95=cap), params)["turnover_highlight"] is False


def test_highlight_never_gates(params):
    verdict = portfolio_veto_verdicts(_row(annual=9.0), params)
    assert verdict["turnover_highlight"] and verdict["passes_portfolio_vetoes"]


def test_an_unknown_highlight_window_raises(tmp_path, params):
    bad = variant(
        tmp_path,
        params,
        "constraints.yaml",
        "highlight_windows: [annual, rolling_1y_p95]",
        "highlight_windows: [annual, rolling_1y_p96]",
    )
    with pytest.raises(ValueError, match="rolling_1y_p96"):
        portfolio_veto_verdicts(_row(), bad)


def _highlight_table(params):
    rows = []
    cells = (("hot-annual", 2.4, 1.0), ("hot-p95", 1.0, 2.6), ("cool", 1.0, 1.1))
    for seed, (key, annual, p95) in enumerate(cells):
        r = _row(annual, p95, 3.0)
        r.update(
            key=key,
            tag="base",
            horizon=13,
            ic=0.1,
            seed=seed,
            net_ir=0.3,
            cost_multiplier=1.0,
            turnover_cap=None,
            cost_drag_annual=0.002,
            **portfolio_veto_verdicts(r, params),
        )
        rows.append(r)
    return pd.DataFrame(rows)


def test_the_summary_counts_and_lists_highlighted_cells_per_grid(params):
    from signal_lab.audit.report import _turnover_highlight

    th = _turnover_highlight(_highlight_table(params), params)
    assert (th["n_highlighted"], th["n_cells"], th["cap"]) == (2, 3, 2.0)
    assert [c["key"] for c in th["cells"]] == ["hot-annual", "hot-p95"]


def test_a_table_without_the_flag_says_so_rather_than_reporting_zero(params):
    from signal_lab.audit.report import _md_turnover_highlight, _turnover_highlight

    table = _highlight_table(params).drop(columns=["turnover_highlight"])
    th = _turnover_highlight(table, params)
    assert th["recorded"] is False
    assert "nothing to report" in "\n".join(_md_turnover_highlight(th))


def test_the_report_marks_highlighted_cells_in_markdown_and_html(params):
    from signal_lab.audit.report import (
        _html_turnover_highlight,
        _md_turnover_highlight,
        _turnover_highlight,
    )

    th = _turnover_highlight(_highlight_table(params), params)
    md = "\n".join(_md_turnover_highlight(th))
    assert "▲ **2 of 3**" in md and "▲ `hot-annual`" in md and "hot-p95" in md
    assert "cool" not in md
    html = _html_turnover_highlight(th)
    assert "2 of 3" in html and "▲" in html and "hot-annual" in html and "cool" not in html


def test_the_full_report_carries_the_highlight_section(params):
    from signal_lab.audit.breadth import effective_breadth
    from signal_lab.audit.report import summarise, to_html, to_markdown

    table = _highlight_table(params)
    idx = pd.bdate_range("2015-01-02", periods=200, freq="W-FRI")
    breadth = effective_breadth(
        pd.DataFrame(
            np.random.default_rng(0).normal(0, 0.01, (200, 4)), index=idx, columns=list("ABCD")
        ),
        pd.Series(0.0, index=idx),
        [13],
    )
    meta = {
        "stress_horizon": 13, "source": "synthetic", "snapshot_id": "t", "panel_hash": "0" * 64,
        "params_version": "x", "params_hash": "0" * 64, "run_id": "A-TEST", "generated_at": "now",
        "first_date": "2004-01-09", "last_date": "2019-12-27", "n_rebalances": 834,
        "te_budget": 0.06, "solver": "auto",
    }  # fmt: skip
    summary = summarise(table, breadth, 0.30, meta)
    assert summary["turnover_highlight"]["n_highlighted"] == 2
    assert "highlighted above 200%" in to_markdown(summary, table)
    assert "highlighted above 200%" in to_html(summary, table)


def test_the_leaderboard_marks_a_run_above_the_threshold(params):
    def run(rid, turnover):
        return {
            "run_id": rid, "family": "f", "aggregation": "a", "net_ir": 0.4, "te": 4.0,
            "turnover": turnover, "max_cash": 5.0, "n_positions": 20, "passed": True,
            "verdicts": {"cash": True},
        }  # fmt: skip

    html = static_report.leaderboard_html(
        [run("R-hot", 250), run("R-cool", 150), run("R-edge", 200)], None, params
    )
    hot, cool, edge = (
        html.split(f">{r}<")[1].split("</tr>")[0] for r in ("R-hot", "R-cool", "R-edge")
    )
    assert "hot" in hot and "▲" in hot
    assert "▲" not in cool and "▲" not in edge, "150% and exactly 200% are not highlighted"


def test_the_veto_legend_carries_the_turnover_disclosure_and_the_stepdown_it_runs(params):
    note = v.turnover_disclosure(params)
    assert note["cap"] == 2.0 and "never a veto" in note["text"] and "200%" in note["text"]
    legend = dict(v.veto_legend(params))
    assert "turnover" not in legend
    assert "2 or more false passes" in legend["multiple_testing"]
    assert [
        s["highlight"]
        for s in v.run_summary_stats({"turnover": 250}, params)
        if s["label"] == "Turnover"
    ] == [True]
    assert [
        s["highlight"]
        for s in v.run_summary_stats({"turnover": 150}, params)
        if s["label"] == "Turnover"
    ] == [False]


# --- 4. one implementation of decisions/0040's shadow cost ---------------------

PPY = 52.0


def _annualised_after(prev, x, params):
    """Trailing annualised turnover once `x` is added: the level the trade creates."""
    w = int(round(PPY))
    return (PPY / w) * (x + prefilled_trailing_traded(prev, params, PPY))


def test_the_prefill_fills_missing_weeks_at_the_target(params):
    target = float(params.require("constraints.turnover.target_annualised"))
    assert prefilled_trailing_traded([], params, PPY) == pytest.approx(51 * target / PPY)
    assert prefilled_trailing_traded([0.1] * 60, params, PPY) == pytest.approx(5.1)


def test_the_derivative_of_S_is_the_marginal_rate_at_the_post_trade_level(params):
    prev = [0.05] * 60  # a full window: 51 * 0.05 = 2.55 of traded notional
    for x in (0.02, 0.08, 0.30):
        h = 1e-6
        numeric = (
            created_marginal_shadow(prev, x + h, params, PPY)
            - created_marginal_shadow(prev, x - h, params, PPY)
        ) / (2 * h)
        assert numeric == pytest.approx(
            annual_turnover_penalty(_annualised_after(prev, x, params), params), rel=1e-6
        )


def test_S_is_zero_at_zero_trade_and_convex(params):
    for prev in ([0.05] * 60, [0.0] * 60, []):
        assert created_marginal_shadow(prev, 0.0, params, PPY) == 0.0
        xs = np.linspace(0.0, 0.5, 26)
        s = np.array([created_marginal_shadow(prev, x, params, PPY) for x in xs])
        assert (np.diff(s, 2) >= -1e-15).all(), "second differences are non-negative"
        assert (np.diff(s) >= 0).all(), "and the cost never falls as the trade grows"


def test_a_lump_costs_more_than_the_same_trading_split_over_two_weeks(params):
    prev = [0.02] * 60
    lump = created_marginal_shadow(prev, 0.40, params, PPY)
    split = created_marginal_shadow(prev, 0.20, params, PPY) + created_marginal_shadow(
        [*prev, 0.20], 0.20, params, PPY
    )
    assert lump > split > 0


def test_the_quadratic_pair_is_the_shadow_up_to_its_constant(params):
    prev = [0.05] * 60
    a, b = created_marginal_quadratic(prev, params, PPY)
    for x in (0.0, 0.1, 0.4):
        assert created_marginal_shadow(prev, x, params, PPY) == pytest.approx(
            a * (max(0.0, b + x) ** 2 - max(0.0, b) ** 2), rel=1e-12, abs=1e-18
        )


def test_the_coefficient_override_scales_the_shadow_linearly(params):
    prev = [0.05] * 60
    base = created_marginal_shadow(prev, 0.2, params, PPY, coefficient=10.0)
    assert created_marginal_shadow(prev, 0.2, params, PPY, coefficient=40.0) == pytest.approx(
        4 * base
    )
    assert created_marginal_shadow(prev, 0.2, params, PPY) == pytest.approx(
        created_marginal_shadow(
            prev,
            0.2,
            params,
            PPY,
            coefficient=float(params.require("constraints.turnover.penalty.coefficient")),
        )
    )


def test_the_ladder_prices_through_objective_and_keeps_no_second_copy():
    """The solver's convex term and the diagnostics both come from `harness.objective`."""
    import inspect

    from signal_lab.audit import ladder

    src = inspect.getsource(ladder._OptimiserRule)
    assert "created_marginal_quadratic" in src and "created_marginal_shadow" in src
    assert "prefilled_trailing_traded" in src
    assert "span * w_periods" not in src, "the (a, b) arithmetic lives in objective only"


def test_an_unconfigured_coefficient_raises_rather_than_pricing_at_zero(tmp_path, params):
    """F8: as `turnover_penalty` does. An explicit override still works."""
    from signal_lab.harness.objective import ObjectiveNotConfigured

    old = "coefficient: 40.0"
    text = (Path(params.params_dir) / "constraints.yaml").read_text()
    assert old in text
    null = variant(tmp_path, params, "constraints.yaml", old, "coefficient: null  ")
    with pytest.raises(ObjectiveNotConfigured):
        created_marginal_quadratic([0.05] * 60, null, PPY)
    with pytest.raises(ObjectiveNotConfigured):
        created_marginal_shadow([0.05] * 60, 0.1, null, PPY)
    assert created_marginal_shadow([0.05] * 60, 0.1, null, PPY, coefficient=10.0) > 0


def test_below_the_start_of_the_curve_a_lump_and_a_split_cost_the_same(params):
    """decisions/0040, addendum 2026-10-01 (task 42 review F5): S prices the annual
    total, not lumpiness. With a window that drops nothing (a book that has traded
    nothing, `prev=[0.0]*60`), a lump and the same trading split over two weeks cost
    exactly the same, whether the trade crosses the curve's start (x = 1.6) or sits
    mostly under it (x = 1.0): the cumulative notional is identical and nothing has
    rolled out. Under the start the cost is zero either way."""
    prev = [0.0] * 60
    for x in (1.0, 1.6):
        lump = created_marginal_shadow(prev, x, params, PPY)
        split = created_marginal_shadow(prev, x / 2, params, PPY) + created_marginal_shadow(
            [*prev[1:], x / 2], x / 2, params, PPY
        )
        assert lump == pytest.approx(split, rel=1e-9, abs=1e-18)
    assert created_marginal_shadow(prev, 0.30, params, PPY) == 0.0, "below the start"
