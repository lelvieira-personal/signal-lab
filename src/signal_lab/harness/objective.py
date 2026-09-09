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

from dataclasses import dataclass

from signal_lab.params import ParamNotConfigured, Params, get_params

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
    One period's shadow cost for trading above the target.

    Linear and one-sided: `coefficient * max(0, T - target)`, in return units per
    period. Zero at or below the target, so the penalty buys lower turnover
    without forbidding it -- the 150% veto remains the hard ceiling.

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
    if str(cfg.get("form", "linear")) != "linear":
        raise ObjectiveNotConfigured(f"unsupported penalty form {cfg.get('form')!r}")

    target = float(params.require("constraints.turnover.target_annualised"))
    excess = max(0.0, float(annualised_turnover) - target)
    return float(coefficient) * BPS * excess / periods_per_year


def annual_turnover_penalty(annualised_turnover: float, params: Params | None = None) -> float:
    """The same penalty expressed per year, which is how a human reads it."""
    return turnover_penalty(annualised_turnover, params, periods_per_year=1.0)


def tracking_error_penalty(
    trailing_te: float, params: Params | None = None, periods_per_year: float = 52.0
) -> float:
    """
    The asymmetric tracking-error penalty of SUBSTRATE section 4.

    "TE is cheap when conviction dispersion is high and expensive when it is
    not", which makes the coefficient conviction-dependent rather than constant.
    Unset, so this refuses. See decisions/0003.
    """
    params = params or get_params()
    try:
        coefficient = params.require("constraints.tracking_error.penalty.coefficient")
    except ParamNotConfigured as exc:
        raise ObjectiveNotConfigured(
            "constraints.tracking_error.penalty.coefficient is null in params/. "
            "SUBSTRATE section 4 requires an asymmetric penalty and states no "
            "coefficient; see decisions/0003."
        ) from exc
    cap = float(params.require("constraints.tracking_error.max_trailing_3y"))
    excess = max(0.0, float(trailing_te) - cap)
    return float(coefficient) * excess / periods_per_year


def is_configured(params: Params | None = None) -> tuple[bool, str]:
    """Whether the full objective can be built, and what is missing if not."""
    params = params or get_params()
    missing = [
        name
        for name, path in (
            ("turnover penalty", "constraints.turnover.penalty.coefficient"),
            ("tracking-error penalty", "constraints.tracking_error.penalty.coefficient"),
        )
        if params.get(path, None) is None
    ]
    if missing:
        return False, f"unset: {', '.join(missing)}"
    return True, "objective fully configured"
