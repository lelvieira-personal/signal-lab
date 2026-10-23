"""
The rebalance step: one solve under a per-session cap and a progressive shadow
cost, given an alpha.

This is the ruler audit's weight rule (`audit.ladder._OptimiserRule`) with the
source of the alpha taken out (decisions/0059 C). The audit plants an alpha and
hands it in; the phase-2 rule will hand in one built from views. The rebalance
itself -- covariance, holdable set, `LongOnlySpec`, cost vector, session cap,
shadow cost, `solve`, turnover log, diagnostics -- is one implementation, here.

`portfolio` does not import `audit`: the universe and the cost model are taken
as arguments. The universe needs `covariance(date, halflife, overlay)`,
`holdable`, `leg_ids`, `leg_weights` and `cash`; the cost model needs
`half_spread_vector(hold)`.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from signal_lab.harness.objective import (
    created_marginal_quadratic,
    created_marginal_shadow,
    prefilled_trailing_traded,
)
from signal_lab.params import Params
from signal_lab.portfolio.long_only import BPS, LongOnlySpec, solve


class RebalanceStep:
    """
    The weight rule for one book: solve at every rebalance under a per-session
    cap and a progressive shadow cost.

    Two mechanisms, answering the two halves of the owner's requirement
    (2026-09-11): "the model doesn't generate too much trading in a single
    session, unless the scenario really changes", and "avoid a situation where
    we rebalanced too much on previous windows and then cannot do more when we
    really need it".

    **A hard per-session cap** on traded notional. This is the first half. It is
    generous relative to the weekly average -- a regime shift can be acted on in
    one week -- but far below the annual budget, so no single session can
    consume it.

    **A progressive shadow cost keyed to TRAILING one-year turnover**, and no
    annual wall. This is the second half, and the wall is what would break it.
    Trading gets steadily dearer as the year's turnover rises past the soft
    target, so ordinary weeks restrain themselves and the budget is not frittered
    away; but the cost stays finite, so a week with real alpha can always pay it
    and trade. A hard annual cap does the opposite -- it is free to trade right
    up to the limit and then forbids trading entirely, which is exactly the
    failure the owner described.

    The previous version banked unused allowance and let the bank go negative.
    That is the same failure wearing a friendlier face: it made capacity a
    quantity to be spent, so an early over-trade genuinely blocked a later one.
    The bank is gone.
    """

    def __init__(
        self,
        universe: Any,
        costs: Any,
        params: Params,
        solver: str,
        *,
        shadow_form: str,
        vol_halflife: float | None,
        vol_overlay: str,
        shadow_coeff: float,
        per_rebalance_cap: float | None,
        turnover_cap: float | None,
    ):
        self.u = universe
        self.params = params
        self.solver = solver
        self.ppy = float(params.get("costs.application.weeks_per_year", 52))
        self.costs = costs
        self.shadow_form = shadow_form
        self.vol_halflife, self.vol_overlay = vol_halflife, vol_overlay
        self.shadow_coeff = shadow_coeff
        self.shadow_start = float(params.require("constraints.turnover.shadow_start_annualised"))
        self.shadow_reference = float(
            params.require("constraints.turnover.shadow_reference_annualised")
        )
        # HANDOFF task 36 / decisions/0040 s2: the prefill level for the
        # `created` form's window, before a full window of history exists.
        self.target_annualised = float(params.require("constraints.turnover.target_annualised"))
        self.per_rebalance_cap = per_rebalance_cap
        self.turnover_cap = turnover_cap
        self.turnover_log: list[float] = []
        self.repair_turnover = 0.0  # traded to restore mandate compliance, cap or no cap
        self.diagnostics: list[dict[str, Any]] = []
        self._alpha_rows: dict[pd.Timestamp, pd.Series] = {}

    def annual_wall_remaining(self) -> float | None:
        """
        Traded notional still permitted under a HARD annual cap, or None when
        there is no wall.

        Only the turnover-shortfall cells set one. Their purpose is to measure
        what a wall costs, and this is what a wall does: once the trailing year
        has spent the budget, nothing more may be traded until it rolls off.
        That is the failure the owner described, priced rather than argued.
        """
        if self.turnover_cap is None:
            return None
        spent = float(np.sum(self.turnover_log[-int(self.ppy) :]))
        return max(0.0, self.turnover_cap - spent)

    def session_cap(self) -> float | None:
        """The binding limit on this session: the per-session cap, the annual
        wall's remaining budget, or whichever is tighter."""
        caps = [c for c in (self.per_rebalance_cap, self.annual_wall_remaining()) if c is not None]
        return min(caps) if caps else None

    def trailing_annual_turnover(self) -> float:
        """Traded notional over the trailing year, annualised to a full year."""
        window = int(self.ppy)
        recent = self.turnover_log[-window:]
        if not recent:
            return 0.0
        # Annualise by the window actually observed, so an early rebalance is not
        # judged as though the year were already complete.
        return float(np.sum(recent)) * self.ppy / len(recent)

    def _shadow(self) -> float:
        """
        A shadow cost per unit traded, rising with trailing one-year turnover.

        Zero at or below `shadow_start`, which decisions/0024 put BELOW the 100%
        target so the cost is already biting as the year approaches it;
        `coefficient` basis points at `shadow_reference`, which preserves the
        decisions/0018 calibration at that point; and rising on the same slope
        beyond it rather than stopping. Progressive and unbounded, never a wall:

            shadow(T) = coefficient * max(0, T - start) / (reference - start)

        At 75% it costs nothing, at 100% 3.3bp, at 150% the 10bp
        decisions/0018 set, at 300% 30bp -- which a week carrying real alpha can
        still justify and a routine week cannot. There is no annual ceiling: the
        veto threshold is a backstop for a malfunctioning book (decisions/0024)
        and this function never reads it.

        This is the same curve as `harness.objective.turnover_penalty`, in cost
        per unit traded rather than return per period.
        """
        span = self.shadow_reference - self.shadow_start
        if span <= 0 or self.shadow_coeff <= 0:
            return 0.0
        excess = max(0.0, self.trailing_annual_turnover() - self.shadow_start)
        return self.shadow_coeff * BPS * excess / span

    def _prefilled_P(self) -> float:
        """`P` of decisions/0040, prefill included: `harness.objective` owns it."""
        return prefilled_trailing_traded(self.turnover_log, self.params, self.ppy)

    def _shadow_quadratic_coeffs(self) -> tuple[float, float]:
        """
        `(a, b)` for the solver's convex shadow term, `S(x) = a * pos(b + x)**2`
        (decisions/0040). The single implementation is
        `harness.objective.created_marginal_quadratic`; this passes the cell's
        own history and coefficient override to it.
        """
        return created_marginal_quadratic(
            self.turnover_log, self.params, self.ppy, self.shadow_coeff
        )

    def ex_ante_te(self) -> pd.Series | None:
        """The annualised TE each solved book was sized to, by rebalance date.

        The engine reads this to put `te_ex_ante` on the path, which is what
        `decisions/0030`'s risk_calibration veto divides the realised return by.
        The same numbers already went into `diagnostics`; this is the engine's
        agreed way of asking for them.
        """
        if not self.diagnostics:
            return None
        frame = pd.DataFrame(self.diagnostics)
        return frame.set_index("date")["te_ex_ante"]

    def alpha(self) -> pd.DataFrame | None:
        """The expected active return each book was solved against, by rebalance date.

        The engine reads this to put `alpha` on the path, which is what the
        transfer coefficient of decisions/0033 needs beside the weights: the rule
        builds it inside `step` and used to discard it. The same shape as
        `ex_ante_te`, and a rule without the method yields no coefficient.
        """
        if not self._alpha_rows:
            return None
        return pd.DataFrame(self._alpha_rows).T

    def step(self, date: pd.Timestamp, alpha: pd.Series, drifted: pd.Series | None = None):
        """Solve one rebalance. `alpha` is a Series over the holdable ids at `date`,
        missing values already filled with 0.0 by the caller."""
        date = pd.Timestamp(date)
        cov = self.u.covariance(date, self.vol_halflife, self.vol_overlay)
        ids = cov.ids
        hold = [h for h in self.u.holdable if h in ids]
        legs = [g for g in self.u.leg_ids if g in ids]
        if len(legs) != len(self.u.leg_ids):
            raise ValueError(f"benchmark legs lack a full covariance window at {date.date()}")
        cash = [c for c in self.u.cash if c in hold]

        benchmark = pd.Series(0.0, index=ids)
        benchmark[legs] = self.u.leg_weights[legs].values
        spec = LongOnlySpec.from_params(ids, hold, cash, benchmark, self.params)

        self._alpha_rows[date] = alpha
        first = drifted is None
        w0 = pd.Series(0.0, index=hold) if first else drifted.reindex(hold).fillna(0.0)
        cost = self.costs.half_spread_vector(hold)
        shadow_quad = None
        if first:
            cost = cost * 0.0  # the initial book is built, not traded (engine records no row)
            cap = None
        else:
            cap = self.session_cap()
            if self.shadow_form == "created":
                # HANDOFF task 36: the shadow leaves the linear cost vector entirely
                # -- only the real half-spread stays in `cost` -- and becomes a
                # convex term on total traded notional instead (decisions/0040).
                shadow_quad = self._shadow_quadratic_coeffs()
            else:
                cost = cost + self._shadow()

        sol = solve(
            alpha,
            cov.matrix,
            w0,
            cost,
            spec,
            turnover_cap=cap,
            solver=self.solver,
            params=self.params,
            shadow_quadratic=shadow_quad,
        )

        if not first:
            self.turnover_log.append(sol.turnover)
            if sol.status.endswith("repair"):
                self.repair_turnover += sol.turnover

        if first:
            shadow_bps = shadow_paid_bps = 0.0
        elif self.shadow_form == "created":
            # `shadow_quad` was fixed BEFORE this trade (it prices off the
            # trailing history, not this trade itself), so it is reused here
            # rather than recomputed -- recomputing after the append above would
            # let this trade leak into its own price.
            a_coef, b_coef = shadow_quad
            x = sol.turnover
            shadow_bps = 2.0 * a_coef * max(0.0, b_coef + x) / BPS  # S'(x): the marginal rate paid
            shadow_paid_bps = (
                created_marginal_shadow(
                    self.turnover_log[:-1], x, self.params, self.ppy, self.shadow_coeff
                )
                / x
                / BPS
                if x > 0
                else 0.0
            )
        else:
            flat = self._shadow()  # unchanged: same call, same place, as every run before this task
            shadow_bps = shadow_paid_bps = flat / BPS

        self.diagnostics.append(
            {
                "date": date,
                "n_holdable": len(hold),
                "n_positions": sol.n_positions,
                "te_ex_ante": sol.te_ex_ante_annual,
                "te_binding": sol.te_binding,
                "turnover_binding": sol.turnover_binding,
                "cash_binding": sol.cash_binding,
                "positions_capped": sol.positions_capped,
                "shrinkage": cov.shrinkage,
                "shadow_bps": shadow_bps,
                "shadow_paid_bps": shadow_paid_bps,
                "trailing_turnover": self.trailing_annual_turnover(),
                "session_cap": self.session_cap(),
                "status": sol.status,
                "solver": sol.solver,
                "inaccurate": sol.inaccurate,
                "polish_shift": float(sol.meta.get("polish_shift", 0.0)),
            }
        )
        return sol.weights
