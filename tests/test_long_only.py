"""
The long-only solver. SUBSTRATE section 4, decisions/0023.

A solver is where a constraint quietly stops being enforced, so most of these
are arithmetic on a problem small enough to reason about: does the budget bind,
does the cash cap hold, does the turnover cap hold, does the position cap hold,
and do the two implementations agree. The agreement test is the important one:
cvxpy shapes every weight in the lab and a transposed selection matrix or a
budget in the wrong units would be invisible in any single run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.portfolio.long_only import (
    INFEASIBLE_STATUS,
    POLISH_WARN,
    LongOnlySpec,
    SolverFailed,
    _arrays,
    _polish,
    solve,
)

IDS = ["EQ", "BD", "A", "B", "C", "CASH"]
HOLD = ["A", "B", "C", "CASH"]

try:  # the reference path only needs scipy; cvxpy is compared against when present
    import cvxpy  # noqa: F401

    HAVE_CVXPY = True
except ImportError:  # pragma: no cover - depends on the environment
    HAVE_CVXPY = False


def toy_sigma() -> pd.DataFrame:
    """
    A covariance from simulated weekly returns, so the benchmark legs are
    genuinely spanned by the holdables and the tracking-error question is well
    posed: EQ is the average of A and B plus a little of its own, BD is C plus
    a little of its own. A hand-written correlation matrix would not be a
    consistent covariance and the minimum achievable tracking error would be
    whatever the numbers happened to imply.
    """
    rng = np.random.default_rng(20260911)
    n = 5000
    a = rng.normal(0, 0.18 / np.sqrt(52), n)
    b = rng.normal(0, 0.14 / np.sqrt(52), n)
    c = rng.normal(0, 0.06 / np.sqrt(52), n)
    cash = rng.normal(0, 0.002 / np.sqrt(52), n)
    eq = 0.5 * a + 0.5 * b + rng.normal(0, 0.01 / np.sqrt(52), n)
    bd = c + rng.normal(0, 0.004 / np.sqrt(52), n)
    frame = pd.DataFrame({"EQ": eq, "BD": bd, "A": a, "B": b, "C": c, "CASH": cash})
    return frame[IDS].cov(ddof=0)


def toy_spec(te: float = 0.06, max_positions: int | None = 30, max_cash: float = 0.2):
    return LongOnlySpec(
        ids=IDS,
        holdable=HOLD,
        cash=["CASH"],
        benchmark=pd.Series({"EQ": 0.5, "BD": 0.5}),
        te_budget_annual=te,
        max_cash=max_cash,
        max_positions=max_positions,
    )


ALPHA = pd.Series({"A": 0.0020, "B": 0.0005, "C": 0.0003, "CASH": 0.0})
BOOK = pd.Series({"A": 0.35, "B": 0.15, "C": 0.50, "CASH": 0.0})
FREE = pd.Series(0.0, index=HOLD)
SOLVERS = ["scipy"] + (["cvxpy"] if HAVE_CVXPY else [])


# --- the constraint set ------------------------------------------------------


@pytest.mark.parametrize("solver", SOLVERS)
def test_the_book_is_long_only_and_fully_invested(solver):
    sol = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    assert sol.weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert (sol.weights >= -1e-9).all()


@pytest.mark.parametrize("solver", SOLVERS)
def test_the_tracking_error_budget_is_hard(solver):
    """Free trading: the budget is the only thing stopping the solver."""
    for te in (0.02, 0.06):
        sol = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(te=te), solver=solver)
        assert sol.te_ex_ante_annual <= te * (1.0 + 1e-3), f"budget {te} breached"
        assert sol.te_binding, "with free alpha the budget should bind"


@pytest.mark.parametrize("solver", SOLVERS)
def test_a_tighter_budget_cannot_earn_more_alpha(solver):
    """Monotone by construction: the tighter problem's feasible set is a subset."""
    tight = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(te=0.02), solver=solver)
    loose = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(te=0.06), solver=solver)
    assert loose.objective >= tight.objective - 1e-9


@pytest.mark.parametrize("solver", SOLVERS)
def test_the_cash_cap_holds_when_cash_is_the_only_thing_worth_holding(solver):
    alpha = pd.Series({"A": -0.003, "B": -0.003, "C": -0.003, "CASH": 0.0})
    sol = solve(alpha, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    assert sol.weights["CASH"] <= 0.2 + 1e-6
    assert sol.cash_binding, "the cap should bind when everything else has negative alpha"


@pytest.mark.parametrize("solver", SOLVERS)
def test_the_turnover_cap_holds_and_costs_alpha(solver):
    free = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    capped = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), turnover_cap=0.05, solver=solver)
    assert capped.turnover <= 0.05 + 1e-6
    assert capped.turnover_binding
    assert capped.objective <= free.objective + 1e-9, "a cap cannot improve the objective"


@pytest.mark.parametrize("solver", SOLVERS)
def test_the_position_cap_is_enforced_and_reported(solver):
    sol = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(max_positions=2), solver=solver)
    assert sol.n_positions <= 2, sol.weights.round(4).to_dict()
    assert sol.positions_capped


@pytest.mark.parametrize("solver", SOLVERS)
def test_trading_costs_hold_the_book_still_when_alpha_is_small(solver):
    """A cost above the alpha it would earn makes the drifted book the answer."""
    dear = pd.Series(0.05, index=HOLD)  # 500bp a unit, far above any alpha here
    sol = solve(ALPHA, toy_sigma(), BOOK, dear, toy_spec(), solver=solver)
    assert sol.turnover == pytest.approx(0.0, abs=1e-4)


# --- the tie-breaker and the infeasible case ---------------------------------


@pytest.mark.parametrize("solver", SOLVERS)
def test_with_no_alpha_the_answer_is_the_minimum_tracking_error_book(solver):
    """
    Zero alpha must not leave the choice to the solver's arithmetic. The
    tie-breaking risk term makes it the closest book to the benchmark, which
    is what the IC = 0 rung of the ruler audit has to measure.
    """
    zero = pd.Series(0.0, index=HOLD)
    sol = solve(zero, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    assert sol.te_ex_ante_annual < 0.02, "no alpha should mean no tracking error worth taking"
    assert not sol.te_binding


@pytest.mark.parametrize("solver", SOLVERS)
def test_an_unreachable_budget_falls_back_to_minimum_te_and_says_so(solver):
    """
    A book far from the benchmark, a budget it cannot meet in one week, and a
    turnover cap that will not let it back. The solver keeps every other
    constraint, drops the budget, and labels the answer -- because refusing
    would stop the walk-forward and guessing would hide it.
    """
    stranded = pd.Series({"A": 1.0, "B": 0.0, "C": 0.0, "CASH": 0.0})
    sol = solve(
        ALPHA, toy_sigma(), stranded, FREE, toy_spec(te=0.01), turnover_cap=0.01, solver=solver
    )
    assert sol.status == INFEASIBLE_STATUS
    assert sol.turnover <= 0.01 + 1e-6, "the turnover cap still holds"
    assert sol.weights.sum() == pytest.approx(1.0, abs=1e-6)


def test_a_holdable_series_outside_the_covariance_is_refused():
    with pytest.raises(ValueError, match="not in the covariance"):
        LongOnlySpec(
            ids=IDS,
            holdable=HOLD + ["MISSING"],
            cash=[],
            benchmark=pd.Series({"EQ": 0.5, "BD": 0.5}),
            te_budget_annual=0.06,
            max_cash=0.2,
            max_positions=30,
        )


def test_a_benchmark_leg_may_not_be_holdable():
    """Holding the benchmark leg itself would make the tracking error trivial."""
    with pytest.raises(ValueError, match="not holdable"):
        LongOnlySpec(
            ids=IDS,
            holdable=HOLD + ["EQ"],
            cash=[],
            benchmark=pd.Series({"EQ": 0.5, "BD": 0.5}),
            te_budget_annual=0.06,
            max_cash=0.2,
            max_positions=30,
        )


# --- the two implementations must agree --------------------------------------


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy is not installed in this environment")
@pytest.mark.parametrize(
    "case",
    [
        {"turnover_cap": None, "cost": 0.0},
        {"turnover_cap": 0.20, "cost": 0.0},
        {"turnover_cap": None, "cost": 0.001},
        {"turnover_cap": 0.05, "cost": 0.001},
    ],
)
def test_cvxpy_and_the_reference_solver_agree(case):
    cost = pd.Series(case["cost"], index=HOLD)
    kwargs = {"turnover_cap": case["turnover_cap"]}
    a = solve(ALPHA, toy_sigma(), BOOK, cost, toy_spec(), solver="cvxpy", **kwargs)
    b = solve(ALPHA, toy_sigma(), BOOK, cost, toy_spec(), solver="scipy", **kwargs)
    assert a.objective == pytest.approx(b.objective, abs=2e-5), "different optimal values"
    assert (a.weights - b.weights).abs().max() < 5e-3, "different books"


def test_an_impossible_problem_raises_rather_than_returning_something():
    """A cash cap below zero has no feasible point; the solver must not invent one."""
    spec = LongOnlySpec(
        ids=IDS,
        holdable=["CASH"],
        cash=["CASH"],
        benchmark=pd.Series({"EQ": 0.5, "BD": 0.5}),
        te_budget_annual=0.06,
        max_cash=0.5,  # the book must be 100% cash but cash is capped at 50%
        max_positions=30,
    )
    with pytest.raises(SolverFailed):
        solve(
            pd.Series({"CASH": 0.0}),
            toy_sigma(),
            pd.Series({"CASH": 1.0}),
            pd.Series({"CASH": 0.0}),
            spec,
            solver="scipy",
        )


# --- the book is inside the mandate exactly, not to a solver tolerance -------


@pytest.mark.parametrize("solver", SOLVERS)
def test_the_returned_book_is_inside_the_mandate_exactly(solver):
    """
    The cash veto compares at a 1e-9 relative tolerance, meant for summation
    error. A solver lands within ITS tolerance of the cap -- CLARABEL put cash at
    0.2 + 5e-10 on the synthetic audit and three of four cells failed the veto
    for it. The book the engine trades must be inside the mandate with no
    tolerance at all.
    """
    alpha = pd.Series({"A": -0.003, "B": -0.003, "C": -0.003, "CASH": 0.0})
    sol = solve(alpha, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    assert sol.weights["CASH"] <= 0.2, repr(sol.weights["CASH"])
    assert (sol.weights >= 0.0).all()
    assert sol.weights.sum() == pytest.approx(1.0, abs=1e-12)
    assert sol.meta["polish_shift"] < POLISH_WARN, "the projection is rounding, not repair"


def _toy_arrays():
    spec = toy_spec()
    return _arrays(ALPHA, toy_sigma(), BOOK, FREE, spec, None, None)


def test_polish_pulls_a_tolerance_overshoot_back_inside_and_says_how_far():
    arr = _toy_arrays()
    over = 5e-10  # the size CLARABEL left on the synthetic audit
    w = np.array([0.30, 0.25, 0.25 - over, 0.20 + over])
    out, shift = _polish(w, arr)
    assert out[3] <= 0.20
    assert out.sum() == pytest.approx(1.0, abs=1e-15)
    assert shift == pytest.approx(over, rel=1e-3)


def test_polish_clears_dust_and_negatives_without_opening_a_position():
    arr = _toy_arrays()
    w = np.array([0.60, -1e-10, 0.30 + 1e-10 - 3e-8, 0.10 + 3e-8])
    out, _ = _polish(w, arr)
    assert out[1] == 0.0, "a solver's negative zero is not a short"
    assert (out >= 0.0).all()
    assert out.sum() == pytest.approx(1.0, abs=1e-15)
    held = np.array([0.60, 0.0, 0.30, 0.10])
    assert ((out > 0) == (held > 0)).all()


def test_an_inaccurate_solve_is_labelled_and_still_projected(monkeypatch):
    """
    `optimal_inaccurate` used to be accepted silently -- the warnings on the
    first audit run were the only trace. The flag travels with the solution so
    the audit can count it, and the book is projected like any other.
    """
    from signal_lab.portfolio import long_only

    def inaccurate_run(arr, backend, params):
        w = np.array([0.30, 0.25, 0.25 - 5e-10, 0.20 + 5e-10])
        return w, long_only.INACCURATE, "CLARABEL"

    monkeypatch.setattr(long_only, "_run", inaccurate_run)
    sol = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver="cvxpy")
    assert sol.inaccurate
    assert sol.status == long_only.INACCURATE
    assert sol.solver == "CLARABEL"
    assert sol.weights["CASH"] <= 0.2


def test_an_accurate_solve_is_not_labelled_inaccurate():
    sol = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver="scipy")
    assert not sol.inaccurate


# --- HANDOFF task 36: the created-turnover shadow, decisions/0040 -----------


def _S(x: float, a: float, b: float) -> float:
    return a * max(0.0, b + x) ** 2


@pytest.mark.parametrize("solver", SOLVERS)
def test_shadow_quadratic_none_leaves_the_solve_unchanged(solver):
    default = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    explicit_none = solve(
        ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver, shadow_quadratic=None
    )
    assert explicit_none.objective == pytest.approx(default.objective)
    pd.testing.assert_series_equal(explicit_none.weights, default.weights)


@pytest.mark.parametrize("solver", SOLVERS)
def test_a_large_shadow_quadratic_restrains_trading(solver):
    """A positive control: the term must actually bind on something."""
    free = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver)
    shadowed = solve(
        ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver=solver, shadow_quadratic=(50.0, 0.0)
    )
    assert shadowed.turnover < free.turnover - 1e-6


@pytest.mark.skipif(not HAVE_CVXPY, reason="cvxpy is not installed in this environment")
def test_cvxpy_and_scipy_agree_with_a_shadow_quadratic():
    kwargs = {"shadow_quadratic": (8.0, -0.1)}
    a = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver="cvxpy", **kwargs)
    b = solve(ALPHA, toy_sigma(), BOOK, FREE, toy_spec(), solver="scipy", **kwargs)
    assert a.objective == pytest.approx(b.objective, abs=2e-5)
    assert (a.weights - b.weights).abs().max() < 5e-3


@pytest.mark.parametrize("a,b", [(2.0, 0.5), (2.0, -0.3), (5.0, 0.0), (5.0, -2.0)])
def test_shadow_quadratic_S_is_convex_in_trade_size(a, b):
    """
    decisions/0040 builds S as the integral of a non-decreasing marginal cost
    curve, so it must be convex in trade size: the discrete second difference
    is non-negative everywhere. This is the property behind "one lump costs
    more than the same trading spread over several weeks" -- tested on `S`
    itself, not an engine run.
    """
    for x in (0.3, 1.0, 2.5):
        h = 0.4
        second_difference = _S(x + h, a, b) - 2 * _S(x, a, b) + _S(x - h, a, b)
        assert second_difference >= -1e-9


def test_shadow_quadratic_derivative_matches_the_0024_curve_exactly():
    """
    decisions/0040: `S'(x)` must equal the existing linear shadow curve
    evaluated at the POST-trade trailing turnover `T(x)`, so "coefficient bp at
    150%" keeps its meaning under the new form.
    """
    coefficient, start, reference, ppy, w_periods = 20.0, 0.75, 1.50, 52.0, 52
    kappa = coefficient * 1e-4
    span = reference - start
    p_trailing = 0.6  # traded notional over the trailing window before this trade
    a = kappa * ppy / (2.0 * span * w_periods)
    b = p_trailing - start * w_periods / ppy
    for x in (0.0, 0.1, 0.5, 1.2, 3.0):
        derivative = 2.0 * a * max(0.0, b + x)
        t_x = (p_trailing + x) * ppy / w_periods
        curve = kappa * max(0.0, t_x - start) / span
        assert derivative == pytest.approx(curve, abs=1e-12)
