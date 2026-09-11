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
    LongOnlySpec,
    SolverFailed,
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
