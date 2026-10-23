"""
`portfolio.rebalance.RebalanceStep` is the audit rule's rebalance, moved
(HANDOFF task 69, decisions/0059 C). Given the planted alpha it must return the
same weights and the same diagnostics as `audit.ladder._OptimiserRule`, and the
portfolio package must not reach back into the audit.
"""

from __future__ import annotations

import dataclasses
import sys

import pandas as pd
import pytest

from signal_lab.audit.ladder import AuditCell, _OptimiserRule, _plant, build_universe
from signal_lab.loaders.base import ReturnPanel
from signal_lab.portfolio.rebalance import RebalanceStep


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


@pytest.mark.parametrize("shadow_form", ["trailing", "created"])
def test_step_with_the_planted_alpha_is_the_audit_rule(small_universe, shadow_form):
    universe, params = small_universe
    cell = AuditCell(0.20, 13, 0, shadow_form=shadow_form)
    signal = _plant(universe, cell)
    rule = _OptimiserRule(universe, signal, cell, params, "scipy")
    step = RebalanceStep(
        universe,
        rule.costs,
        params,
        "scipy",
        shadow_form=rule.shadow_form,
        vol_halflife=rule.vol_halflife,
        vol_overlay=rule.vol_overlay,
        shadow_coeff=rule.shadow_coeff,
        per_rebalance_cap=cell.per_rebalance_cap,
        turnover_cap=cell.turnover_cap,
    )

    drifted = None
    for date in universe.audit_dates()[:3]:  # the first book, then two later rebalances
        cov = universe.covariance(date, rule.vol_halflife, rule.vol_overlay)
        hold = [h for h in universe.holdable if h in cov.ids]
        alpha = signal.alpha.reindex(index=[date], columns=hold).iloc[0].fillna(0.0)
        expected = rule(date, None, drifted=drifted)
        got = step.step(date, alpha, drifted=drifted)
        pd.testing.assert_series_equal(got, expected, check_exact=True)
        drifted = expected

    assert step.diagnostics == rule.diagnostics
    assert step.turnover_log == rule.turnover_log
    pd.testing.assert_frame_equal(step.alpha(), rule.alpha(), check_exact=True)


def test_the_portfolio_package_does_not_import_the_audit():
    # Take every lab module out of `sys.modules`, import the portfolio fresh, see
    # whether the audit came with it, and put the originals back.
    saved = {m: sys.modules.pop(m) for m in list(sys.modules) if m.startswith("signal_lab")}
    try:
        import signal_lab.portfolio  # noqa: F401
        import signal_lab.portfolio.rebalance  # noqa: F401

        pulled = [m for m in sys.modules if m.startswith("signal_lab.audit")]
    finally:
        for m in [m for m in sys.modules if m.startswith("signal_lab")]:
            del sys.modules[m]
        sys.modules.update(saved)
    assert pulled == []
