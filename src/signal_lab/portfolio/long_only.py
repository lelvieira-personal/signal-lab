"""
The long-only solver. SUBSTRATE section 4 and section 15 (`portfolio/`).

One rebalance: given per-period alphas on the holdable instruments, a
covariance over the holdable instruments AND the benchmark legs, the drifted
book, and a per-unit trading cost, choose the long-only, fully invested book
that maximises alpha net of trading cost inside a hard tracking-error budget.

    maximise   a'w - c'|w - w0| - lambda (S w - b)' Sigma (S w - b)
    subject to (S w - b)' Sigma (S w - b) <= TE^2 / periods_per_year
               w >= 0,  1'w = 1
               sum(w[cash]) <= max_cash
               sum |w - w0| <= turnover budget          (optional)
               |support(w)| <= max_positions             (heuristic, below)

`S` places the holdable weights inside the full covariance; the benchmark `b`
has support only on the benchmark columns, which are not holdable. Tracking
error is therefore measured against the benchmark's own returns rather than
against a proxy built from panel members.

`lambda` is a TIE-BREAKER, not a risk aversion: `LongOnlySpec.risk_aversion`
defaults to a value at which the term is worth a small fraction of a basis
point at the budget, so it never competes with alpha, but with zero alpha --
the IC = 0 rung of the ruler audit, or a week with no forecast -- it makes the
answer the minimum-tracking-error book rather than whichever vertex the
solver landed on. It is also what the infeasibility fallback uses: when the
budget cannot be met (a drifted book outside it and a turnover cap that will
not let it back in one week), the solver keeps every other constraint, drops
the budget, and minimises tracking error, so the book moves toward the budget
as fast as the cap allows. `Solution.status` says `infeasible_te:min_te`
when that happened, and the audit counts it.

What this is and is not. It is the lab's first optimiser, written for the
ruler audit (`decisions/0023`), and it is the base the phase 2 optimiser
extends. It holds tracking error at a HARD budget and carries no
conviction-scaled penalty: the coefficients in `decisions/0019` are null, and
the audit's question -- what is achievable AT the budget -- is the hard-budget
question anyway. When those coefficients exist, the penalty is added to this
objective; the constraint set does not change.

Two implementations, deliberately. `solve_cvxpy` is the production path, with
the solver chain from `params/constraints.yaml`. `solve_reference` is the same
problem handed to scipy's SLSQP through split trade variables with analytic
Jacobians, dependency-free. The test suite requires the two to agree, so a bug
in the cvxpy formulation -- a transposed selection matrix, a budget in the
wrong units -- fails a test rather than shaping every weight in the lab.

The position cap is enforced heuristically: solve relaxed, and if more than
`max_positions` instruments are held, keep the largest and re-solve on that
support. It is not the mixed-integer optimum, and it says so in the solution
so a reader can see how often the cap bound.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.params import Params, get_params

BPS = 1e-4

# Tie-breaker risk aversion, in return per unit of per-period active variance.
# At a 6% annual budget the per-period variance is 6.9e-5, so this term is
# worth 0.07bp a period: far below any alpha, decisive only when there is none.
TIE_BREAK_RISK_AVERSION = 0.1
INFEASIBLE_STATUS = "infeasible_te:min_te"

# A weight below this is solver noise, not a position. The same threshold
# decides what counts as held for the position cap.
DUST = 1e-7

# How far `_polish` may move a book before the move is itself a finding. An
# interior-point solver lands within ~1e-8 of a bound; a shift beyond this is
# not rounding, and the audit reports the largest one per cell.
POLISH_WARN = 1e-4


class SolverFailed(Exception):
    """No solver in the chain returned an optimal solution."""


@dataclass(frozen=True)
class LongOnlySpec:
    """The constraint set for one rebalance. Every number came from params."""

    ids: list[str]  # every series in Sigma: holdable plus benchmark legs
    holdable: list[str]  # the subset the book may hold
    cash: list[str]  # holdable series that count as cash
    benchmark: pd.Series  # weights over `ids`, support on the benchmark legs only
    te_budget_annual: float
    max_cash: float
    max_positions: int | None
    periods_per_year: float = 52.0
    risk_aversion: float = TIE_BREAK_RISK_AVERSION

    def __post_init__(self) -> None:
        missing = [h for h in self.holdable if h not in self.ids]
        if missing:
            raise ValueError(f"holdable series not in the covariance: {missing[:5]}")
        overlap = [h for h in self.holdable if self.benchmark.get(h, 0.0) != 0.0]
        if overlap:
            raise ValueError(f"benchmark legs are not holdable: {overlap}")
        if abs(float(self.benchmark.reindex(self.ids).fillna(0.0).sum()) - 1.0) > 1e-9:
            raise ValueError("benchmark weights must sum to one over `ids`")

    @property
    def te_variance_per_period(self) -> float:
        return self.te_budget_annual**2 / self.periods_per_year

    def selection(self) -> np.ndarray:
        """S: len(ids) x len(holdable), placing holdable weights inside `ids`."""
        pos = {s: i for i, s in enumerate(self.ids)}
        s = np.zeros((len(self.ids), len(self.holdable)))
        for j, h in enumerate(self.holdable):
            s[pos[h], j] = 1.0
        return s

    @classmethod
    def from_params(
        cls,
        ids: list[str],
        holdable: list[str],
        cash: list[str],
        benchmark: pd.Series,
        params: Params | None = None,
    ) -> LongOnlySpec:
        params = params or get_params()
        return cls(
            ids=list(ids),
            holdable=list(holdable),
            cash=list(cash),
            benchmark=benchmark,
            te_budget_annual=float(params.require("constraints.tracking_error.max_trailing_3y")),
            max_cash=float(params.require("constraints.cash.max_weight")),
            max_positions=int(params.require("constraints.positions.max_nonzero")),
            periods_per_year=float(params.get("costs.application.weeks_per_year", 52)),
        )


@dataclass
class Solution:
    """One rebalance's answer, with enough diagnostics to see which walls it hit."""

    weights: pd.Series  # over holdable; zeros kept so the book has a fixed shape
    status: str
    solver: str
    objective: float  # per period, alpha net of trading cost
    te_ex_ante_annual: float
    turnover: float  # sum |w - w0|, traded notional
    n_positions: int
    te_binding: bool
    turnover_binding: bool
    cash_binding: bool
    positions_capped: bool
    # The solver reported `optimal_inaccurate`: it stopped at its reduced
    # tolerances. The book is still projected onto the mandate (`_polish`), but
    # how often this happens is a property of the solver worth counting.
    inaccurate: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


# --- the problem, once, so both implementations read the same arrays --------


@dataclass(frozen=True)
class _Arrays:
    a: np.ndarray  # alpha per period, holdable
    c: np.ndarray  # cost per unit traded, holdable
    w0: np.ndarray  # drifted book, holdable
    sigma: np.ndarray  # ids x ids
    s: np.ndarray  # ids x holdable
    b: np.ndarray  # ids
    cash_mask: np.ndarray  # holdable, bool
    te_var: float
    max_cash: float
    turnover_cap: float | None
    support: np.ndarray  # holdable, bool: which may be non-zero
    risk_aversion: float

    @property
    def n(self) -> int:
        return len(self.a)

    def active(self, w: np.ndarray) -> np.ndarray:
        return self.s @ w - self.b

    def active_var(self, w: np.ndarray) -> float:
        a = self.active(w)
        return float(a @ self.sigma @ a)

    def active_var_grad(self, w: np.ndarray) -> np.ndarray:
        return 2.0 * (self.s.T @ (self.sigma @ self.active(w)))


def _arrays(
    alpha: pd.Series,
    sigma: pd.DataFrame,
    drifted: pd.Series,
    cost: pd.Series,
    spec: LongOnlySpec,
    turnover_cap: float | None,
    support: np.ndarray | None,
) -> _Arrays:
    ids, hold = spec.ids, spec.holdable
    sig = sigma.reindex(index=ids, columns=ids)
    if sig.isna().any().any():
        missing = [i for i in ids if i not in sigma.index]
        raise ValueError(f"covariance is missing series: {missing[:5]}")
    a = alpha.reindex(hold).fillna(0.0).to_numpy(dtype=float)
    c = cost.reindex(hold).fillna(cost.max() if len(cost) else 0.0).to_numpy(dtype=float)
    w0 = drifted.reindex(hold).fillna(0.0).to_numpy(dtype=float)
    cash_mask = np.array([h in set(spec.cash) for h in hold], dtype=bool)
    sup = np.ones(len(hold), dtype=bool) if support is None else np.asarray(support, dtype=bool)
    return _Arrays(
        a=a,
        c=c,
        w0=w0,
        sigma=sig.to_numpy(dtype=float),
        s=spec.selection(),
        b=spec.benchmark.reindex(ids).fillna(0.0).to_numpy(dtype=float),
        cash_mask=cash_mask,
        te_var=spec.te_variance_per_period,
        max_cash=spec.max_cash,
        turnover_cap=turnover_cap,
        support=sup,
        risk_aversion=float(spec.risk_aversion),
    )


def _polish(w: np.ndarray, arr: _Arrays) -> tuple[np.ndarray, float]:
    """
    Project a solved book onto the mandate EXACTLY, and say how far it moved.

    A conic solver returns a point within its feasibility tolerance of the
    constraint set, not inside it: on the synthetic audit CLARABEL put cash at
    0.2 + 5e-10 against a 0.2 cap, which the cash veto -- compared at a 1e-9
    relative tolerance meant for summation error, decisions/0024 addendum --
    correctly refused. The fix belongs here rather than in the veto. The engine
    trades and earns on these weights, so a book that is outside the mandate by
    a solver tolerance is outside it, and loosening the veto to the solver's
    tolerance would make the veto's meaning depend on which solver ran.

    In order: off-support and dust weights (including the solver's tiny
    negatives) become zero; a cash block above its cap is scaled down to the
    cap; and the shortfall or excess against full investment is spread over the
    risky positions in proportion to their size, so no new position is opened
    and cash is not pushed back over its cap. The largest absolute change is
    returned, so a projection that is doing more than rounding is visible.
    """
    raw = np.asarray(w, dtype=float)
    out = raw.copy()
    out[~arr.support] = 0.0
    out[out < DUST] = 0.0
    cash = arr.cash_mask
    if cash.any():
        held_cash = float(out[cash].sum())
        if held_cash > arr.max_cash:
            out[cash] *= arr.max_cash / held_cash
    total = float(out.sum())
    if total <= 0.0:
        raise SolverFailed("the solved book holds nothing")
    risky = ~cash & (out > 0.0)
    gap = 1.0 - total
    if gap != 0.0:
        if risky.any():
            out[risky] += gap * out[risky] / float(out[risky].sum())
        else:  # an all-cash book; only reachable when the cap is not binding
            out /= total
    return out, float(np.max(np.abs(out - raw))) if len(raw) else 0.0


def _diagnose(
    w: np.ndarray,
    arr: _Arrays,
    spec: LongOnlySpec,
    status: str,
    solver: str,
    inaccurate: bool = False,
    polish_shift: float = 0.0,
) -> Solution:
    w = np.where(np.abs(w) < DUST, 0.0, w)
    var = arr.active_var(w)
    turnover = float(np.abs(w - arr.w0).sum())
    objective = float(arr.a @ w - arr.c @ np.abs(w - arr.w0))
    tol = 1e-4
    return Solution(
        weights=pd.Series(w, index=spec.holdable),
        status=status,
        solver=solver,
        objective=objective,
        te_ex_ante_annual=float(np.sqrt(max(var, 0.0) * spec.periods_per_year)),
        turnover=turnover,
        n_positions=int((w > 0).sum()),
        te_binding=bool(var >= arr.te_var * (1.0 - 1e-3)),
        turnover_binding=bool(
            arr.turnover_cap is not None and turnover >= arr.turnover_cap * (1.0 - 1e-3) - tol
        ),
        cash_binding=bool(w[arr.cash_mask].sum() >= arr.max_cash - tol),
        positions_capped=bool(not arr.support.all()),
        inaccurate=bool(inaccurate),
        meta={"polish_shift": polish_shift},
    )


# --- production path: cvxpy ---------------------------------------------------


def _solver_chain(params: Params | None) -> list[str]:
    params = params or get_params()
    chain = [str(params.get("constraints.solver.default", "CLARABEL"))]
    chain += [str(s) for s in params.get("constraints.solver.fallbacks", []) or []]
    return chain


INACCURATE = "optimal_inaccurate"


def _solve_with_chain(problem, w, params: Params | None, what: str) -> tuple[np.ndarray, str, str]:
    """
    Solve `problem` with the first solver in the chain that returns an answer.

    `optimal_inaccurate` is accepted and passed on in the status rather than
    retried down the chain: the fallbacks are OSQP, a first-order method whose
    default tolerances are looser than an interior-point solver's reduced
    ones, and ECOS. Falling from an almost-solved CLARABEL to a "solved" OSQP
    would trade a flagged approximation for an unflagged, coarser one. The book
    is projected onto the mandate either way (`_polish`), and the caller counts
    the inaccurate solves. cvxpy's own warning is silenced for the same reason:
    the count replaces it.
    """
    import cvxpy as cp

    errors = []
    for name in _solver_chain(params):
        if name not in cp.installed_solvers():
            errors.append(f"{name}: not installed")
            continue
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Solution may be inaccurate")
                problem.solve(solver=name)
        except cp.error.SolverError as exc:  # pragma: no cover - depends on installed solvers
            errors.append(f"{name}: {exc}")
            continue
        if problem.status in ("optimal", INACCURATE) and w.value is not None:
            return np.asarray(w.value, dtype=float), str(problem.status), name
        errors.append(f"{name}: {problem.status}")
    raise SolverFailed(f"{what}: " + "; ".join(errors))


def solve_cvxpy(arr: _Arrays, params: Params | None = None) -> tuple[np.ndarray, str, str]:
    import cvxpy as cp

    n = arr.n
    w = cp.Variable(n, nonneg=True)
    trade = w - arr.w0
    active = arr.s @ w - arr.b
    # Scaled to basis points so the solver sees O(1) numbers rather than 1e-4.
    sigma_bps = cp.psd_wrap(arr.sigma / BPS)
    risk = cp.quad_form(active, sigma_bps)
    objective = cp.Maximize((arr.a @ w - arr.c @ cp.abs(trade)) / BPS - arr.risk_aversion * risk)
    constraints = [cp.sum(w) == 1.0]
    if np.isfinite(arr.te_var):
        constraints.append(risk <= arr.te_var / BPS)
    if arr.cash_mask.any():
        constraints.append(cp.sum(w[np.flatnonzero(arr.cash_mask)]) <= arr.max_cash)
    if arr.turnover_cap is not None:
        constraints.append(cp.sum(cp.abs(trade)) <= arr.turnover_cap)
    if not arr.support.all():
        constraints.append(w[np.flatnonzero(~arr.support)] == 0.0)
    problem = cp.Problem(objective, constraints)
    return _solve_with_chain(problem, w, params, "the budgeted problem")


# --- reference path: scipy, split trades ------------------------------------


def _minimum_trade_cvxpy(arr: _Arrays, params: Params | None) -> tuple[np.ndarray, str, str]:
    import cvxpy as cp

    w = cp.Variable(arr.n, nonneg=True)
    constraints = [cp.sum(w) == 1.0]
    if arr.cash_mask.any():
        constraints.append(cp.sum(w[np.flatnonzero(arr.cash_mask)]) <= arr.max_cash)
    if not arr.support.all():
        constraints.append(w[np.flatnonzero(~arr.support)] == 0.0)
    problem = cp.Problem(cp.Minimize(cp.sum(cp.abs(w - arr.w0))), constraints)
    return _solve_with_chain(problem, w, params, "the minimum-trade repair")


def _minimum_trade_reference(arr: _Arrays) -> tuple[np.ndarray, str, str]:
    """The nearest feasible book to the drifted one, by traded notional (an LP)."""
    from scipy.optimize import linprog

    n = arr.n
    # variables (u, v) >= 0, w = w0 + u - v; minimise sum(u + v)
    a_eq = np.concatenate([np.ones(n), -np.ones(n)])[None, :]
    b_eq = np.array([1.0 - arr.w0.sum()])
    rows, rhs = [-np.hstack([np.eye(n), -np.eye(n)])], [arr.w0.copy()]  # w >= 0
    if arr.cash_mask.any():
        cash = arr.cash_mask.astype(float)
        rows.append(np.concatenate([cash, -cash])[None, :])
        rhs.append(np.array([arr.max_cash - arr.w0[arr.cash_mask].sum()]))
    bounds = [(0.0, None)] * (2 * n)
    for j in np.flatnonzero(~arr.support):
        bounds[j] = (0.0, 0.0)
        bounds[n + j] = (arr.w0[j], arr.w0[j])
    res = linprog(
        np.ones(2 * n),
        A_ub=np.vstack(rows),
        b_ub=np.concatenate(rhs),
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    if not res.success:
        raise SolverFailed(f"the minimum-trade repair did not solve: {res.message}")
    return np.clip(arr.w0 + res.x[:n] - res.x[n:], 0.0, None), "optimal", "HiGHS"


def _feasible(w: np.ndarray, z: np.ndarray, arr: _Arrays, tol: float = 1e-6) -> bool:
    """SLSQP reports success on slightly infeasible points; check before trusting."""
    n = arr.n
    if abs(w.sum() - 1.0) > tol or (w < -tol).any():
        return False
    if not arr.support.all() and (w[~arr.support] > tol).any():
        return False
    if np.isfinite(arr.te_var) and arr.active_var(w) > arr.te_var * (1.0 + 1e-3) + tol * BPS:
        return False
    if arr.cash_mask.any() and w[arr.cash_mask].sum() > arr.max_cash + tol:
        return False
    if arr.turnover_cap is not None and (z[:n] + z[n:]).sum() > arr.turnover_cap + tol:
        return False
    return True


def _as_trades(w: np.ndarray, arr: _Arrays) -> np.ndarray:
    """A book expressed as the split (buy, sell) vector the reference path uses."""
    delta = w - arr.w0
    return np.concatenate([np.clip(delta, 0.0, None), np.clip(-delta, 0.0, None)])


def _starts(arr: _Arrays, include_minimum_te: bool = False):
    """
    Candidate starting points, cheapest first.

    1. Stay put. Feasible whenever the drifted book is already compliant.
    2. The NEAREST COMPLIANT book, from the minimum-trade LP: feasible whenever
       the linear constraints admit anything inside the turnover cap, and it is
       the start that matters. Without it, a book that drifts a hundredth of a
       percent past the cash cap has no feasible start -- staying put breaks the
       cap, equal weight breaks the cap on turnover -- and a repair fires for a
       breach a single basis point of trading would have fixed. On the synthetic
       panel that turned a 25% turnover cell into a 32% one.
    3. Equal weight over the support, for a book starting from nothing.
    4. For the alpha problem, the minimum-tracking-error book, so SLSQP only has
       to climb the alpha from a point well inside the budget.
    """
    n = arr.n
    yield np.zeros(2 * n)
    try:
        w_near, _, _ = _minimum_trade_reference(arr)
        yield _as_trades(w_near, arr)
    except SolverFailed:
        pass
    target = np.where(arr.support, 1.0, 0.0)
    target = target / target.sum() if target.sum() > 0 else np.full(n, 1.0 / n)
    yield _as_trades(target, arr)
    if include_minimum_te:
        try:
            w_min, _, _ = _minimum_te_reference(arr)
        except SolverFailed:
            return
        yield _as_trades(w_min, arr)


def solve_reference(arr: _Arrays) -> tuple[np.ndarray, str, str]:
    """
    The same problem for SLSQP: w = w0 + u - v with u, v >= 0, so the trading
    cost is linear in (u, v) and every constraint is smooth, with analytic
    Jacobians throughout. Exact enough to check the cvxpy path against.
    """
    from scipy.optimize import minimize

    n = arr.n
    scale = 1.0 / BPS
    ones, eye = np.ones(n), np.eye(n)
    cash = arr.cash_mask.astype(float)

    def unpack(z):
        return arr.w0 + z[:n] - z[n:]

    def objective(z):
        w = unpack(z)
        value = arr.a @ w - arr.c @ (z[:n] + z[n:]) - arr.risk_aversion * arr.active_var(w)
        return -value * scale

    def grad(z):
        g = arr.a - arr.risk_aversion * arr.active_var_grad(unpack(z))
        return -np.concatenate([g - arr.c, -g - arr.c]) * scale

    cons = [
        {
            "type": "eq",
            "fun": lambda z: unpack(z).sum() - 1.0,
            "jac": lambda z: np.concatenate([ones, -ones]),
        },
        {"type": "ineq", "fun": lambda z: unpack(z), "jac": lambda z: np.hstack([eye, -eye])},
    ]
    if np.isfinite(arr.te_var):

        def te_jac(z):
            g = -arr.active_var_grad(unpack(z)) * scale
            return np.concatenate([g, -g])

        cons.append(
            {
                "type": "ineq",
                "fun": lambda z: (arr.te_var - arr.active_var(unpack(z))) * scale,
                "jac": te_jac,
            }
        )
    if arr.cash_mask.any():
        cons.append(
            {
                "type": "ineq",
                "fun": lambda z: arr.max_cash - unpack(z)[arr.cash_mask].sum(),
                "jac": lambda z: np.concatenate([-cash, cash]),
            }
        )
    if arr.turnover_cap is not None:
        cons.append(
            {
                "type": "ineq",
                "fun": lambda z: arr.turnover_cap - (z[:n] + z[n:]).sum(),
                "jac": lambda z: -np.ones(2 * n),
            }
        )
    bounds = [(0.0, None)] * (2 * n)
    if not arr.support.all():
        # Off-support instruments are sold in full and may not be bought.
        for j in np.flatnonzero(~arr.support):
            bounds[j] = (0.0, 0.0)
            bounds[n + j] = (arr.w0[j], arr.w0[j])

    # Every start is run and the BEST feasible answer wins, rather than the
    # first. Returning the first was a quiet defect: "stay put" is feasible in
    # most weeks, SLSQP moves very little from it when the alpha is small, and
    # the audit's IC = 0 rung -- which must hug the benchmark -- instead held
    # whatever book it opened with at 4% tracking error.
    best, best_value, last = None, np.inf, None
    for start in _starts(arr, include_minimum_te=True):
        res = minimize(
            objective,
            start,
            jac=grad,
            bounds=bounds,
            constraints=cons,
            method="SLSQP",
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        if _feasible(unpack(res.x), res.x, arr):
            value = objective(res.x)
            if value < best_value:
                best, best_value = res.x, value
        else:
            last = str(res.message)
    if best is None:
        raise SolverFailed(f"SLSQP found no feasible optimum: {last}")
    return np.clip(unpack(best), 0.0, None), "optimal", "SLSQP"


# --- the entry point ----------------------------------------------------------


def _available(solver: str) -> str:
    if solver == "auto":
        try:
            import cvxpy  # noqa: F401

            return "cvxpy"
        except ImportError:
            return "scipy"
    return solver


def _run(arr: _Arrays, backend: str, params: Params | None) -> tuple[np.ndarray, str, str]:
    return solve_cvxpy(arr, params) if backend == "cvxpy" else solve_reference(arr)


def _minimum_te_cvxpy(arr: _Arrays, params: Params | None) -> tuple[np.ndarray, str, str]:
    import cvxpy as cp

    w = cp.Variable(arr.n, nonneg=True)
    active = arr.s @ w - arr.b
    constraints = [cp.sum(w) == 1.0]
    if arr.cash_mask.any():
        constraints.append(cp.sum(w[np.flatnonzero(arr.cash_mask)]) <= arr.max_cash)
    if arr.turnover_cap is not None:
        constraints.append(cp.sum(cp.abs(w - arr.w0)) <= arr.turnover_cap)
    if not arr.support.all():
        constraints.append(w[np.flatnonzero(~arr.support)] == 0.0)
    problem = cp.Problem(
        cp.Minimize(cp.quad_form(active, cp.psd_wrap(arr.sigma / arr.te_var))), constraints
    )
    return _solve_with_chain(problem, w, params, "the minimum-tracking-error problem")


def _minimum_te_reference(arr: _Arrays) -> tuple[np.ndarray, str, str]:
    """
    Minimise active variance subject to the linear constraints.

    Its own problem rather than the general path with zero alpha, for two
    reasons: the objective is scaled by the budget so it is O(1) at the budget
    and SLSQP is well conditioned, and the drifted book is always feasible, so
    a guaranteed answer exists and is returned when the optimiser fails to
    improve on it. Never trading is a poor answer; an infeasible one would be a
    wrong one.
    """
    from scipy.optimize import minimize

    n = arr.n
    scale = 1.0 / arr.te_var if np.isfinite(arr.te_var) and arr.te_var > 0 else 1.0

    def unpack(z):
        return arr.w0 + z[:n] - z[n:]

    def objective(z):
        return arr.active_var(unpack(z)) * scale

    def grad(z):
        g = arr.active_var_grad(unpack(z)) * scale
        return np.concatenate([g, -g])

    ones, eye = np.ones(n), np.eye(n)
    cash = arr.cash_mask.astype(float)
    cons = [
        {
            "type": "eq",
            "fun": lambda z: unpack(z).sum() - 1.0,
            "jac": lambda z: np.concatenate([ones, -ones]),
        },
        {"type": "ineq", "fun": lambda z: unpack(z), "jac": lambda z: np.hstack([eye, -eye])},
    ]
    if arr.cash_mask.any():
        cons.append(
            {
                "type": "ineq",
                "fun": lambda z: arr.max_cash - unpack(z)[arr.cash_mask].sum(),
                "jac": lambda z: np.concatenate([-cash, cash]),
            }
        )
    if arr.turnover_cap is not None:
        cons.append(
            {
                "type": "ineq",
                "fun": lambda z: arr.turnover_cap - (z[:n] + z[n:]).sum(),
                "jac": lambda z: -np.ones(2 * n),
            }
        )
    bounds = [(0.0, None)] * (2 * n)
    if not arr.support.all():
        for j in np.flatnonzero(~arr.support):
            bounds[j] = (0.0, 0.0)
            bounds[n + j] = (arr.w0[j], arr.w0[j])

    no_trade = np.zeros(2 * n)
    unconstrained = replace(arr, te_var=float("inf"))
    best = no_trade if _feasible(arr.w0, no_trade, unconstrained) else None
    # `best` is the guaranteed answer when the book already satisfies every
    # linear constraint; it is None when it does not (an off-support holding,
    # say) and the optimiser must find one.
    for start in _starts(arr):
        res = minimize(
            objective,
            start,
            jac=grad,
            bounds=bounds,
            constraints=cons,
            method="SLSQP",
            options={"maxiter": 1000, "ftol": 1e-14},
        )
        if _feasible(unpack(res.x), res.x, unconstrained) and (
            best is None or objective(res.x) < objective(best) - 1e-12
        ):
            best = res.x
    if best is None:
        raise SolverFailed("the minimum-tracking-error problem has no feasible point")
    return np.clip(unpack(best), 0.0, None), "optimal", "SLSQP"


def _needs_repair(arr: _Arrays) -> bool:
    """
    Whether the drifted book breaks a constraint that trading MUST fix.

    The cash cap and the position cap are mandate limits, not preferences: a
    book that drifts to 23% cash, or that holds an instrument the position cap
    has just excluded, is outside the mandate and has to be traded back whatever
    a turnover budget says. The turnover cap is the one constraint that may be
    exceeded to repair them, and only then.
    """
    free = replace(arr, te_var=float("inf"), turnover_cap=None)
    return not _feasible(arr.w0, np.zeros(2 * arr.n), free)


def _minimum_te(arr: _Arrays, backend: str, params: Params | None):
    return _minimum_te_cvxpy(arr, params) if backend == "cvxpy" else _minimum_te_reference(arr)


def _minimum_trade(arr: _Arrays, backend: str, params: Params | None):
    """
    The smallest trade that brings the book back inside the mandate.

    Used only for a repair. Minimising tracking error instead would be a much
    larger trade -- it rebuilds the whole book rather than selling the excess
    cash -- and on the synthetic panel two such repairs spent 1.4 units of
    turnover in a cell whose annual budget was 0.25. A repair should buy
    compliance and nothing else.
    """
    return (
        _minimum_trade_cvxpy(arr, params) if backend == "cvxpy" else _minimum_trade_reference(arr)
    )


def _run_or_minimum_te(arr: _Arrays, backend: str, params: Params | None):
    """
    Solve; if the budget cannot be met, keep every other constraint and
    minimise tracking error instead, so the book moves back toward the budget
    as fast as the turnover cap allows.

    The turnover cap is NOT dropped to make the budget reachable. It was, in an
    earlier version, and the effect was a silent leak: a drifted book marginally
    outside the budget made the problem infeasible, the fallback traded without
    a cap, and the audit's 25%-cap cell reported 70% annual turnover against it.
    The cap is relaxed only to repair a cash-cap or position-cap breach
    (`_needs_repair`), the repair is the SMALLEST trade that restores compliance
    rather than the minimum-tracking-error book, and the status records that it
    happened.

    Returns `(weights, status, solver, inaccurate)`. The status names the path
    taken; `inaccurate` says whether the solve that produced the weights
    stopped at reduced tolerances, whichever path that was.
    """
    try:
        w, status, name = _run(arr, backend, params)
        return w, status, name, status == INACCURATE
    except SolverFailed:
        pass
    try:
        w, status, name = _minimum_te(arr, backend, params)
        return w, INFEASIBLE_STATUS, name, status == INACCURATE
    except SolverFailed:
        if not _needs_repair(arr):
            raise
    w, status, name = _minimum_trade(replace(arr, turnover_cap=None), backend, params)
    return w, f"{INFEASIBLE_STATUS}:repair", name, status == INACCURATE


def solve(
    alpha: pd.Series,
    sigma: pd.DataFrame,
    drifted: pd.Series,
    cost: pd.Series,
    spec: LongOnlySpec,
    turnover_cap: float | None = None,
    solver: str = "auto",
    params: Params | None = None,
) -> Solution:
    """
    One rebalance. `alpha` and `cost` are per period and per unit traded, over
    the holdable series; `sigma` covers `spec.ids`; `drifted` is the book as it
    stands at the close. `turnover_cap` is traded notional for this rebalance.

    The position cap is applied by re-solving on the largest positions of the
    relaxed solution; `Solution.positions_capped` says when that happened.

    The returned book is inside the mandate exactly, not to a solver's
    tolerance: `_polish` projects it, and `Solution.meta["polish_shift"]` says
    how far that moved it.
    """
    backend = _available(solver)
    arr = _arrays(alpha, sigma, drifted, cost, spec, turnover_cap, None)
    w, status, name, inaccurate = _run_or_minimum_te(arr, backend, params)
    held = (w > DUST).sum()
    if spec.max_positions is not None and held > spec.max_positions:
        keep = np.zeros(len(w), dtype=bool)
        keep[np.argsort(-w)[: spec.max_positions]] = True
        arr = _arrays(alpha, sigma, drifted, cost, spec, turnover_cap, keep)
        w, status, name, inaccurate = _run_or_minimum_te(arr, backend, params)
    w, shift = _polish(w, arr)
    return _diagnose(w, arr, spec, status, name, inaccurate, shift)
