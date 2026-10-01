"""
The optimiser's objective. SUBSTRATE sections 3, 4 and 8.

    objective = net_return - te_penalty - turnover_penalty

The penalties shape the weights. They do **not** enter the reported net return
or the net IR, which are computed from actual costs only (decisions/0018). That
separation is the point of this module existing apart from `costs.py`:

  * `costs.py` charges what trading actually costs. Those charges are real, they
    reduce the return an investor receives, and they belong in the reported
    figure.
  * `objective.py` adds shadow costs for things the spread does not capture --
    capacity, implementation risk, the discomfort of tracking error. They are
    preferences, not outcomes.

Let a shadow cost into the reported return and a heavily penalised run looks
worse for a reason that is not performance, so two runs with different
coefficients stop being comparable -- which is the one thing the leaderboard
exists to be.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from signal_lab.params import Params, get_params

BPS = 1e-4


class ObjectiveNotConfigured(Exception):
    """A penalty coefficient is null, so the objective refuses to build."""


@dataclass(frozen=True)
class ObjectiveTerms:
    """One period's objective, decomposed so the digest can show why."""

    net_return: float
    turnover_penalty: float
    te_penalty: float

    @property
    def total(self) -> float:
        return self.net_return - self.turnover_penalty - self.te_penalty

    @property
    def reported_net_return(self) -> float:
        """
        What the leaderboard sees: actual costs only, no shadow costs.

        decisions/0018. This is deliberately not `total`.
        """
        return self.net_return


def turnover_penalty(
    annualised_turnover: float, params: Params | None = None, periods_per_year: float = 52.0
) -> float:
    """
    One period's shadow cost for trading above the start of the curve.

    Linear, one-sided and unbounded (decisions/0018, re-anchored by 0024):

        shadow(T) = coefficient * max(0, T - start) / (reference - start)

    in return units per period, with `coefficient` basis points reached exactly
    at `reference`. Zero at or below `start`, which sits BELOW the 100% target
    so the cost is already biting as turnover approaches it and there is no kink
    at the target for the optimiser to sit in.

    Accepts `constraints.turnover.penalty.form` of `linear` (decisions/0018,
    0024's original flat-at-post-trade charge, kept in code so pre-0040 runs
    reproduce exactly -- `AuditCell.shadow_form="trailing"`) or
    `created_marginal` (decisions/0040): both read the SAME marginal-rate curve
    above. What differs between the two is how a whole TRADE is charged, not
    the rate at a given trailing level -- `created_marginal` integrates this
    rate across the trade's own size instead of charging it once at the
    post-trade level, so one lump costs more than the same trading spread out.
    That integral (`AuditCell.shadow_form="created"`) is `created_marginal_shadow`
    below, and `created_marginal_quadratic` is the form the solver takes; this
    function only ever returns the marginal rate, which decisions/0040 keeps
    unchanged from the retired `linear` form's calibration.

    There is no annual wall and no turnover veto either (decisions/0024,
    0038): turnover is disclosed on every run and highlighted above
    `constraints.turnover.highlight_annualised`, never gated.

    `annualised_turnover` is traded notional (decisions/0017).
    """
    params = params or get_params()
    cfg = params.get("constraints.turnover.penalty", {}) or {}
    coefficient = cfg.get("coefficient")
    if coefficient is None:
        raise ObjectiveNotConfigured(
            "constraints.turnover.penalty.coefficient is null in params/. The lab "
            "does not invent thresholds; set it and record the decision."
        )
    form = str(cfg.get("form", "linear"))
    if form not in ("linear", "created_marginal"):
        raise ObjectiveNotConfigured(f"unsupported penalty form {form!r}")

    start = float(params.require("constraints.turnover.shadow_start_annualised"))
    reference = float(params.require("constraints.turnover.shadow_reference_annualised"))
    span = reference - start
    if span <= 0:
        raise ObjectiveNotConfigured(
            "constraints.turnover.shadow_reference_annualised must exceed "
            "shadow_start_annualised; the curve has no slope otherwise."
        )
    excess = max(0.0, float(annualised_turnover) - start)
    return float(coefficient) * BPS * excess / span / periods_per_year


def prefilled_trailing_traded(
    prev_traded: Sequence[float], params: Params | None = None, periods_per_year: float = 52.0
) -> float:
    """
    `P`, decisions/0040 "the ruling, made precise": traded notional over the
    PREVIOUS `W - 1` rebalances (`W = round(periods_per_year)`), with any
    missing entry (before a full window of history exists) filled at
    `target_annualised / periods_per_year` -- the owner's "prefill at 100%
    target" (item 2). The window it feeds is always `W` long once this
    rebalance's own trade is added, which is what keeps a week-2 trade from
    counting ~26 times over.
    """
    params = params or get_params()
    target = float(params.require("constraints.turnover.target_annualised"))
    w_periods = int(round(periods_per_year))
    recent = list(prev_traded)[-(w_periods - 1) :] if w_periods > 1 else []
    missing = max(0, (w_periods - 1) - len(recent))
    # Per-period fill, then times the count: bit-for-bit with the pre-task-42 arithmetic.
    fill = target / periods_per_year
    return float(np.sum(recent)) + missing * fill


def created_marginal_quadratic(
    prev_traded: Sequence[float],
    params: Params | None = None,
    periods_per_year: float = 52.0,
    coefficient: float | None = None,
) -> tuple[float, float]:
    """
    `(a, b)` for `S(x) = a * (pos(b + x)**2 - pos(b)**2)`, `x` this rebalance's
    total traded notional -- decisions/0040 item 1, rearranged so the solver
    never has to know about turnover windows:

        T(x) - s = (ppy / W) * (x + P - s*W/ppy) = (ppy / W) * (x + b)
        a = kappa * ppy / (2 * span * W),   b = P - s*W/ppy

    The solver's convex term takes `(a, b)`; the constant `-a*pos(b)**2` does
    not affect the solve and is added back by `created_marginal_shadow`.
    `coefficient` overrides `constraints.turnover.penalty.coefficient` (a cell's
    `shadow_coefficient`); `None` reads params. This is the one implementation
    of the created-turnover shadow cost: `audit.ladder` calls it.
    """
    params = params or get_params()
    if coefficient is None:
        coefficient = float(params.get("constraints.turnover.penalty.coefficient", 0) or 0)
    start = float(params.require("constraints.turnover.shadow_start_annualised"))
    reference = float(params.require("constraints.turnover.shadow_reference_annualised"))
    w_periods = int(round(periods_per_year))
    span = reference - start
    kappa = float(coefficient) * BPS
    p_trailing = prefilled_trailing_traded(prev_traded, params, periods_per_year)
    a = kappa * periods_per_year / (2.0 * span * w_periods) if span > 0 else 0.0
    b = p_trailing - start * w_periods / periods_per_year
    return a, b


def created_marginal_shadow(
    prev_traded: Sequence[float],
    x: float,
    params: Params | None = None,
    periods_per_year: float = 52.0,
    coefficient: float | None = None,
) -> float:
    """
    `S(x)` of decisions/0040: the shadow cost, in return units, of trading `x`
    (traded notional, buys plus sells) this rebalance, the marginal unit paying
    the curve at the turnover it creates. Zero at `x = 0`, convex in `x`, and
    `dS/dx` is `annual_turnover_penalty` at the post-trade trailing level.
    """
    a, b = created_marginal_quadratic(prev_traded, params, periods_per_year, coefficient)
    return a * (max(0.0, b + x) ** 2 - max(0.0, b) ** 2)


def annual_turnover_penalty(annualised_turnover: float, params: Params | None = None) -> float:
    """The same penalty expressed per year, which is how a human reads it."""
    return turnover_penalty(annualised_turnover, params, periods_per_year=1.0)


def te_coefficient(conviction: float, params: Params | None = None) -> float:
    """
    The tracking-error penalty coefficient at a given conviction.

    SUBSTRATE section 4 makes this a function rather than a number: TE is cheap
    when conviction is high and expensive when it is not. Linear between the two
    endpoints, and floored at the high-conviction value rather than reaching
    zero -- an overconfident regime estimate must not be able to buy unlimited
    tracking error (decisions/0019).
    """
    params = params or get_params()
    cfg = params.get("constraints.tracking_error.penalty", {}) or {}
    low = cfg.get("coefficient_low_conviction")
    high = cfg.get("coefficient_high_conviction")
    if low is None or high is None:
        raise ObjectiveNotConfigured(
            "constraints.tracking_error.penalty.coefficient_{low,high}_conviction "
            "are null in params/. SUBSTRATE section 4 requires a conviction-scaled "
            "penalty and states no coefficients; see decisions/0019."
        )
    if float(high) > float(low):
        raise ObjectiveNotConfigured(
            "the high-conviction coefficient must not exceed the low-conviction one; "
            "section 4 says TE is CHEAPER when conviction is high"
        )
    c = float(np.clip(conviction, 0.0, 1.0))
    return float(low) - (float(low) - float(high)) * c


def tracking_error_penalty(
    trailing_te: float,
    conviction: float = 0.0,
    params: Params | None = None,
    periods_per_year: float = 52.0,
) -> float:
    """
    The asymmetric, conviction-scaled tracking-error penalty (section 4).

    One-sided above the ceiling, like the turnover penalty. `conviction`
    defaults to 0 -- the dear end -- so a caller that forgets to supply it is
    penalised rather than let off.
    """
    params = params or get_params()
    coefficient = te_coefficient(conviction, params)
    cap = float(params.require("constraints.tracking_error.max_trailing_3y"))
    excess = max(0.0, float(trailing_te) - cap)
    return coefficient * excess / periods_per_year


def is_configured(params: Params | None = None) -> tuple[bool, str]:
    """Whether the full objective can be built, and what is missing if not."""
    params = params or get_params()
    missing = [
        name
        for name, path in (
            ("turnover penalty", "constraints.turnover.penalty.coefficient"),
            (
                "tracking-error penalty (low conviction)",
                "constraints.tracking_error.penalty.coefficient_low_conviction",
            ),
            (
                "tracking-error penalty (high conviction)",
                "constraints.tracking_error.penalty.coefficient_high_conviction",
            ),
        )
        if params.get(path, None) is None
    ]
    if missing:
        return False, f"unset: {', '.join(missing)}"
    return True, "objective fully configured"
