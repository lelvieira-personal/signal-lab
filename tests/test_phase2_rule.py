"""
`portfolio.phase2.Phase2Rule`: the phase-2 weight rule, fed a scores frame
(HANDOFF task 82, decisions/0059 C and F and its 2026-11-05 addendum).

Synthetic scores and a hand-built exposure stub over a synthetic universe. No vendor data, no
store, no label map, nothing on or after 2020-01-01 except where a test hands the rule such a
date to see it refused. One test per check of 0059 F that needs no real signal: F1 (the two
solvers agree), F2 (zero scores give the minimum-TE book), F3 (the sign of a view moves the
book the right way), F4 (a view reaches only the instruments it names), F6 (the holdout).
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from signal_lab.audit.ladder import AuditCell, _OptimiserRule, _plant, build_universe
from signal_lab.characteristics.exposures import VIEW_REGIONS
from signal_lab.loaders.base import ReturnPanel
from signal_lab.loaders.holdout import HoldoutViolation
from signal_lab.portfolio.phase2 import Phase2Rule
from signal_lab.portfolio.rebalance import RebalanceStep

try:  # the reference path only needs scipy; cvxpy is compared against when present
    import cvxpy  # noqa: F401

    HAVE_CVXPY = True
except ImportError:  # pragma: no cover
    HAVE_CVXPY = False

SIGMA = 0.5  # large on purpose: the views must be big enough to move a solved book visibly
T = 60  # a position after the 52-week burn-in


@pytest.fixture(scope="module")
def small_universe(params, panel):
    """Fourteen series and a spannable pair of legs, from 2016 on (as test_rebalance_step)."""
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


@pytest.fixture(scope="module")
def settings(small_universe):
    universe, params = small_universe
    cell = AuditCell(0.20, 13, 0, shadow_form="created")
    base = _OptimiserRule(universe, _plant(universe, cell), cell, params, "scipy")
    return base.costs, dict(
        shadow_form=base.shadow_form,
        vol_halflife=base.vol_halflife,
        vol_overlay=base.vol_overlay,
        shadow_coeff=base.shadow_coeff,
        per_rebalance_cap=cell.per_rebalance_cap,
        turnover_cap=cell.turnover_cap,
    )


@pytest.fixture(scope="module")
def dates(small_universe):
    index = pd.DatetimeIndex(small_universe[0].audit_dates())
    assert len(index) > T + 4
    assert index[-1] < pd.Timestamp("2020-01-01")
    return index


class StubExposures:
    """`ExposureMap.at` and `.axis("region", ...)` for the universe's holdable ids, by hand."""

    def __init__(self, ids, cash):
        ids = list(ids)
        n = len(ids)
        frame = pd.DataFrame(index=pd.Index(ids))
        duration = np.linspace(1.0, 9.0, n)
        duration[12:] = np.nan  # the last two carry no cell on any axis
        frame["axis_duration"] = duration
        frame["axis_real_nominal"] = np.linspace(-0.5, 0.5, n)
        frame["axis_credit"] = np.linspace(0.0, 4.0, n)
        frame["axis_cash"] = [1.0 if i in cash else 0.0 for i in ids]
        for col in ("curve_currency", "rating_class", "market_label", "rating", "hy_bucket"):
            frame[col] = ""
        frame["market"] = ""
        frame["region"] = ["US"] * 4 + ["Japan"] * 4 + ["Developed Europe"] * 2 + [""] * (n - 10)
        frame["curve"] = ["UST"] * 3 + ["EUR"] * 2 + ["JPY"] + [""] * (n - 6)
        self.frame = frame
        cells = pd.DataFrame(0.0, index=frame.index, columns=list(VIEW_REGIONS))
        cells.loc[ids[0:4], "US"] = 1.0
        cells.loc[ids[4:8], "Japan"] = 1.0  # ids 8, 9 are labelled but not region_view
        self.cells = cells

    def at(self, date):
        return self.frame.copy()

    def axis(self, name, date):
        assert name == "region"
        return self.cells.copy()


@pytest.fixture(scope="module")
def stub(small_universe):
    universe, _ = small_universe
    return StubExposures(universe.holdable, set(universe.cash))


def noise(dates, columns, seed=0, last=None):
    """Deterministic scores; `last` (a dict column -> value) overrides the score at `dates[T]`."""
    rng = np.random.default_rng(seed)
    scores = pd.DataFrame(rng.normal(size=(len(dates), len(columns))), index=dates, columns=columns)
    for col, value in (last or {}).items():
        scores.loc[dates[T], col] = value
    return scores


def sigma_of(dates):
    return pd.Series(SIGMA, index=dates)


def make_rule(small_universe, settings, stub, dates, solver="scipy", **kw):
    universe, params = small_universe
    costs, rebalance = settings
    kw.setdefault("sigma", sigma_of(dates))
    kw.setdefault("exposures", stub)
    kw.setdefault("horizon", (4, 13))
    return Phase2Rule(universe, costs, params, solver, **kw, **rebalance)


def make_step(small_universe, settings, solver="scipy"):
    universe, params = small_universe
    costs, rebalance = settings
    return RebalanceStep(universe, costs, params, solver, **rebalance)


def active(universe, weights, column):
    """`sum (w - b) * column` over the union of the book and the benchmark legs."""
    idx = weights.index.union(pd.Index(universe.leg_ids))
    b = pd.Series(0.0, index=idx)
    b[list(universe.leg_ids)] = universe.leg_weights[list(universe.leg_ids)].values
    w = weights.reindex(idx).fillna(0.0)
    return float(((w - b) * column.reindex(idx).fillna(0.0)).sum())


DURATION = dict(axis="duration", expression="directional")


# --- F1: the two solvers agree on the rule's own problems ---------------------


@pytest.mark.slow
@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy is not installed in this environment")
@pytest.mark.parametrize(
    "case",
    [
        dict(
            axis="duration",
            expression="directional",
            cols=["d"],
            last={"d": 4.0},
        ),
        dict(
            axis="region",
            expression="cross_sectional",
            cols=["US", "Japan"],
            last={"US": 4.0, "Japan": -4.0},
        ),
    ],
    ids=["directional", "cross_sectional"],
)
def test_f1_cvxpy_and_the_reference_solver_agree(small_universe, settings, stub, dates, case):
    scores = noise(dates, case["cols"], last=case["last"])
    kw = dict(scores=scores, axis=case["axis"], expression=case["expression"])
    books = {}
    for solver in ("cvxpy", "scipy"):
        rule = make_rule(small_universe, settings, stub, dates, solver=solver, **kw)
        first = rule(dates[T], None)  # the first book, then a later rebalance from it
        second = rule(dates[T + 1], None, drifted=first)
        books[solver] = (first, second)
    for a, b in zip(books["cvxpy"], books["scipy"], strict=True):
        assert (a - b).abs().max() < 5e-3, "different books"


# --- F2: zero scores are the minimum-TE book ----------------------------------


@pytest.mark.parametrize(
    "case",
    [
        dict(axis="duration", expression="directional", cols=["d"]),
        dict(axis="region", expression="cross_sectional", cols=["US", "Japan"]),
    ],
    ids=["directional", "cross_sectional"],
)
def test_f2_zero_scores_give_the_book_of_a_zero_alpha(small_universe, settings, stub, dates, case):
    universe, _ = small_universe
    scores = pd.DataFrame(0.0, index=dates, columns=case["cols"])
    rule = make_rule(
        small_universe, settings, stub, dates, scores=scores, axis=case["axis"],
        expression=case["expression"],
    )  # fmt: skip
    step = make_step(small_universe, settings)
    drifted = None
    for date in dates[T : T + 3]:
        ids = universe.covariance(date, rule.vol_halflife, rule.vol_overlay).ids
        hold = [h for h in universe.holdable if h in ids]
        got = rule(date, None, drifted=drifted)
        expected = step.step(date, pd.Series(0.0, index=hold), drifted=drifted)
        pd.testing.assert_series_equal(got, expected, check_exact=True)
        drifted = got


# --- F3: the sign of a view moves the book the right way ----------------------


def test_f3_a_positive_duration_score_raises_active_duration(small_universe, settings, stub, dates):
    universe, _ = small_universe
    zero = make_rule(
        small_universe, settings, stub, dates,
        scores=pd.DataFrame(0.0, index=dates, columns=["d"]), **DURATION,
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    live = make_rule(
        small_universe, settings, stub, dates,
        scores=noise(dates, ["d"], last={"d": 4.0}), **DURATION,
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    base = active(universe, zero(dates[T], None), stub.frame["axis_duration"])
    tilted = active(universe, live(dates[T], None), stub.frame["axis_duration"])
    assert live.z.loc[dates[T], "d"] > 0.0
    assert tilted > base


def test_f3_a_cross_sectional_pair_of_regions_moves_their_weights_apart(
    small_universe, settings, stub, dates
):
    ids = list(small_universe[0].holdable)
    us, japan = ids[0:4], ids[4:8]
    zero = make_rule(
        small_universe, settings, stub, dates,
        scores=pd.DataFrame(0.0, index=dates, columns=["US", "Japan"]),
        axis="region", expression="cross_sectional",
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    live = make_rule(
        small_universe, settings, stub, dates,
        scores=noise(dates, ["US", "Japan"], last={"US": 4.0, "Japan": -4.0}),
        axis="region", expression="cross_sectional",
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    base, tilted = zero(dates[T], None), live(dates[T], None)
    assert live.views.loc[dates[T], "US"] > 0.0 > live.views.loc[dates[T], "Japan"]
    assert tilted.reindex(us).fillna(0.0).sum() > base.reindex(us).fillna(0.0).sum()
    assert tilted.reindex(japan).fillna(0.0).sum() < base.reindex(japan).fillna(0.0).sum()


# --- F4: a view reaches only the instruments it names ------------------------


def handed_alpha(rule, date):
    return rule.alpha().loc[date]


def test_f4_a_region_view_reaches_only_region_view_instruments(
    small_universe, settings, stub, dates
):
    rule = make_rule(
        small_universe, settings, stub, dates,
        scores=noise(dates, ["US", "Japan"], last={"US": 4.0, "Japan": -4.0}),
        axis="region", expression="cross_sectional",
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    rule(dates[T], None)
    alpha = handed_alpha(rule, dates[T])
    in_view = stub.cells.sum(axis=1) > 0
    assert (alpha[~in_view] == 0.0).all()
    assert (alpha[in_view] != 0.0).all()


def test_f4_a_scoped_view_reaches_only_matching_instruments(small_universe, settings, stub, dates):
    ids = list(small_universe[0].holdable)
    presence = pd.DataFrame(True, index=dates[:T], columns=ids)
    rule = make_rule(
        small_universe, settings, stub, dates,
        scores=noise(dates, ["d"], last={"d": 4.0}), scope={"curve": ["UST", "EUR"]},
        presence=presence, **DURATION,
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    rule(dates[T], None)
    alpha = handed_alpha(rule, dates[T])
    inside = stub.frame["curve"].isin(["UST", "EUR"])
    assert (alpha[~inside] == 0.0).all()
    assert (alpha[inside] != 0.0).all()


def test_f4_an_instrument_without_the_label_gets_zero_alpha(small_universe, settings, stub, dates):
    rule = make_rule(
        small_universe, settings, stub, dates,
        scores=noise(dates, ["UST", "EUR", "JPY"], last={"UST": 4.0, "EUR": -4.0, "JPY": 3.0}),
        group_by="curve", **DURATION,
        amortise_costs=False, free_first_book=True,
    )  # fmt: skip
    rule(dates[T], None)
    alpha = handed_alpha(rule, dates[T])
    blank = stub.frame["curve"] == ""
    assert (alpha[blank] == 0.0).all()
    assert (alpha[~blank] != 0.0).any()


def test_an_instrument_with_no_exposure_row_gets_zero_alpha_on_the_holdable_ids(
    small_universe, settings, stub, dates
):
    """The alpha is reindexed to the holdable ids and filled with 0.0, as the audit rule does."""

    class Short(StubExposures):
        def at(self, date):
            return self.frame.iloc[:-2].copy()

    short = Short(small_universe[0].holdable, set(small_universe[0].cash))
    rule = make_rule(
        small_universe, settings, short, dates,
        scores=noise(dates, ["d"], last={"d": 4.0}), **DURATION,
    )  # fmt: skip
    rule(dates[T], None)
    alpha = handed_alpha(rule, dates[T])
    assert list(alpha.index) == [h for h in small_universe[0].holdable if h in alpha.index]
    assert (alpha.iloc[-2:] == 0.0).all()


# --- F6: the holdout ----------------------------------------------------------


def holdout_dates():
    return pd.DatetimeIndex(["2019-12-20", "2019-12-27", "2020-01-03", "2020-01-10"])


def test_f6_scores_on_or_after_the_holdout_are_refused(small_universe, settings, stub, dates):
    late = pd.DataFrame(1.0, index=holdout_dates(), columns=["d"])
    with pytest.raises(HoldoutViolation):
        make_rule(
            small_universe, settings, stub, dates,
            scores=late, sigma=pd.Series(SIGMA, index=late.index), **DURATION,
        )  # fmt: skip


def test_f6_a_sigma_on_or_after_the_holdout_is_refused(small_universe, settings, stub, dates):
    with pytest.raises(HoldoutViolation):
        make_rule(
            small_universe, settings, stub, dates,
            scores=noise(dates, ["d"]), sigma=pd.Series(SIGMA, index=holdout_dates()), **DURATION,
        )  # fmt: skip


def test_f6_a_presence_on_or_after_the_holdout_is_refused(small_universe, settings, stub, dates):
    ids = list(small_universe[0].holdable)
    with pytest.raises(HoldoutViolation):
        make_rule(
            small_universe, settings, stub, dates,
            scores=noise(dates, ["d"]), scope={"curve": ["UST"]},
            presence=pd.DataFrame(True, index=holdout_dates(), columns=ids), **DURATION,
        )  # fmt: skip


def test_f6_a_call_on_a_holdout_date_is_refused(small_universe, settings, stub, dates):
    rule = make_rule(small_universe, settings, stub, dates, scores=noise(dates, ["d"]), **DURATION)
    with pytest.raises(HoldoutViolation):
        rule(pd.Timestamp("2020-01-03"), None)


# --- the rest of the rule's contract -------------------------------------------


def test_both_is_refused_because_it_is_two_tests(small_universe, settings, stub, dates):
    with pytest.raises(ValueError, match="one rule per test"):
        make_rule(
            small_universe, settings, stub, dates,
            scores=noise(dates, ["d"]), axis="duration", expression="both",
        )  # fmt: skip


def test_a_directional_rule_with_no_group_by_and_two_columns_is_refused(
    small_universe, settings, stub, dates
):
    with pytest.raises(ValueError, match="exactly one column"):
        make_rule(
            small_universe, settings, stub, dates,
            scores=noise(dates, ["a", "b"]), **DURATION,
        )  # fmt: skip


def test_a_scope_without_presence_is_refused(small_universe, settings, stub, dates):
    with pytest.raises(ValueError, match="presence"):
        make_rule(
            small_universe, settings, stub, dates,
            scores=noise(dates, ["d"]), scope={"curve": ["UST"]}, **DURATION,
        )  # fmt: skip


def test_a_scope_that_reaches_one_instrument_fails_a_cross_section_but_not_a_directional_rule(
    small_universe, settings, stub, dates
):
    ids = list(small_universe[0].holdable)
    presence = pd.DataFrame(True, index=dates[:T], columns=ids)
    scope = {"curve": ["JPY"]}  # one instrument
    with pytest.raises(ValueError, match="0057 rule 4"):
        make_rule(
            small_universe, settings, stub, dates,
            scores=noise(dates, ids[:4]), axis="duration", expression="cross_sectional",
            scope=scope, presence=presence,
        )  # fmt: skip
    rule = make_rule(
        small_universe, settings, stub, dates,
        scores=noise(dates, ["d"]), scope=scope, presence=presence, **DURATION,
    )  # fmt: skip
    assert rule.reach == 1


def test_inside_the_burn_in_the_alpha_is_zero(small_universe, settings, stub, dates):
    rule = make_rule(small_universe, settings, stub, dates, scores=noise(dates, ["d"]), **DURATION)
    assert (rule.alpha_at(dates[10]) == 0.0).all()
    assert (rule.alpha_at(dates[T]) != 0.0).any()


def test_a_date_the_scores_do_not_carry_is_refused(small_universe, settings, stub, dates):
    rule = make_rule(
        small_universe, settings, stub, dates, scores=noise(dates[:T], ["d"]),
        sigma=sigma_of(dates[:T]), **DURATION,
    )  # fmt: skip
    with pytest.raises(ValueError, match="no score"):
        rule(dates[T + 1], None)
