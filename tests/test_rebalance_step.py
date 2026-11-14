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
    cell = AuditCell(0.20, 13, 0, shadow_form=shadow_form, legacy_0070=True)
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


def test_the_window_records_the_forced_sale_of_an_instrument_that_left_the_holdable_set(
    small_universe,
):
    """
    decisions/0040, addendum of 2026-11-13 (HANDOFF task 97): when a held instrument leaves the
    holdable set on date k, the solve drops it from `w0`, the engine sells it and charges both
    legs, and the trailing window records what the engine records -- both legs -- so the shadow's
    coefficients on date k+1 read it. `sol.turnover` and `shadow_paid_bps` stay the solve's own.
    """
    from signal_lab.audit.pilot import RowedUniverse
    from signal_lab.harness.costs import CostModel, drift_weights
    from signal_lab.harness.objective import created_marginal_quadratic

    universe, params = small_universe
    cell = AuditCell(0.20, 13, 0, shadow_form="created", legacy_0070=True)
    signal = _plant(universe, cell)
    rule = _OptimiserRule(universe, signal, cell, params, "scipy")
    dates = list(universe.audit_dates()[:5])
    k = 3

    def make_step(u):
        return RebalanceStep(
            u,
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

    def alpha_at(date, hold):
        return signal.alpha.reindex(index=[date], columns=hold).iloc[0].fillna(0.0)

    def drift(book, previous, current):
        daily = universe.panel.returns
        window = daily.loc[(daily.index > previous) & (daily.index <= current)]
        for day in window.index:
            book = drift_weights(book, window.loc[day])
        return book

    # A dry run on the full holdable set picks the instrument to drop: the largest
    # non-cash, non-leg holding of the book drifted into date k.
    probe = make_step(universe)
    book = probe.step(dates[0], alpha_at(dates[0], universe.holdable), None)
    for previous, current in zip(dates[:-1], dates[1:k], strict=False):
        held = drift(book, previous, current)
        book = probe.step(current, alpha_at(current, universe.holdable), held)
    held_into_k = drift(book, dates[k - 1], dates[k])
    candidates = held_into_k.drop(labels=universe.cash + universe.leg_ids, errors="ignore")
    gone = str(candidates.idxmax())
    assert held_into_k[gone] > 1e-3

    full = frozenset(universe.holdable)
    rowed = {d: (full - {gone} if i >= k else full) for i, d in enumerate(dates)}
    u = RowedUniverse(universe, rowed)
    step = make_step(u)

    book, engine_traded, coeffs_before, forced = None, {}, {}, {}
    for i, date in enumerate(dates):
        held = None if i == 0 else drift(book, dates[i - 1], date)
        coeffs_before[i] = step._shadow_quadratic_coeffs()
        hold = [h for h in universe.holdable if h in rowed[date]]
        target = step.step(date, alpha_at(date, hold), held)
        if held is not None:
            engine_traded[i] = CostModel.turnover(target, held)[0]
            forced[i] = float(held[~held.index.isin(hold)].abs().sum())
        book = target

    # the sale is forced on date k and on no other date
    assert forced[k] == pytest.approx(held_into_k[gone], abs=1e-12)
    assert all(forced[i] == 0.0 for i in forced if i != k)
    # on every date, k included, the window holds the engine's traded notional, both legs
    for i in range(1, len(dates)):
        assert step.turnover_log[i - 1] == pytest.approx(engine_traded[i], abs=1e-12)
    # the coefficients of date k were fixed before the trade, from the window without date k
    assert coeffs_before[k] == created_marginal_quadratic(
        step.turnover_log[: k - 1], params, step.ppy, step.shadow_coeff
    )
    # the shadow's coefficients on date k+1 read the window with the forced leg in it
    assert coeffs_before[k + 1] == created_marginal_quadratic(
        step.turnover_log[:k], params, step.ppy, step.shadow_coeff
    )
    without = list(step.turnover_log[:k])
    without[k - 1] -= forced[k]
    assert coeffs_before[k + 1] != created_marginal_quadratic(
        without, params, step.ppy, step.shadow_coeff
    )


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
