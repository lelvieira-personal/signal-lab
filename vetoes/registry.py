"""
apply_vetoes: run the whole set, record every verdict, return the first failure.

Ordering comes from params/vetoes.yaml. Data-integrity vetoes run first, because
a lookahead or frequency breach makes every downstream number meaningless and
should be the reason logged, rather than a turnover breach that happens to sit
earlier in a table.
"""

from __future__ import annotations

from collections.abc import Callable

from signal_lab.harness.run_context import RunContext
from signal_lab.params import Params, get_params
from signal_lab.results.store import ResultsStore, Verdict
from vetoes import rules

VETOES: dict[str, Callable[..., Verdict]] = {
    "turnover": rules.veto_turnover,
    "cash": rules.veto_cash,
    "tracking_error": rules.veto_tracking_error,
    "positions": rules.veto_positions,
    "coverage": rules.veto_coverage,
    "lookahead": rules.veto_lookahead,
    "frequency": rules.veto_frequency,
    "active_drawdown": rules.veto_active_drawdown,
    "seed_stability": rules.veto_seed_stability,
    "multiple_testing": rules.veto_multiple_testing,
    "direction": rules.veto_direction,
}

# SUBSTRATE section 10 as amended by decisions/0003: eleven, not ten. Asserted
# rather than assumed, so that a row added to the constitution and not to this
# package is a loud failure rather than a silent gap.
SUBSTRATE_VETOES = frozenset(
    {
        "turnover",
        "cash",
        "tracking_error",
        "positions",
        "coverage",
        "lookahead",
        "frequency",
        "active_drawdown",
        "seed_stability",
        "multiple_testing",
        "direction",
    }
)
assert set(VETOES) == SUBSTRATE_VETOES, (
    "veto set does not match SUBSTRATE section 10 + decisions/0003"
)


def VETO_ORDER(params: Params | None = None) -> list[str]:
    """Evaluation order from params, validated against the implemented set."""
    params = params or get_params()
    order = list(params.get("vetoes.evaluation.order", list(VETOES)))
    unknown = [v for v in order if v not in VETOES]
    if unknown:
        raise ValueError(f"params/vetoes.yaml orders unknown vetoes: {unknown}")
    missing = [v for v in VETOES if v not in order]
    if missing:
        raise ValueError(
            f"params/vetoes.yaml omits {missing}; every veto is applied to every run "
            f"(SUBSTRATE section 10), so an omission is not a configuration option"
        )
    return order


def apply_vetoes(
    ctx: RunContext,
    params: Params | None = None,
    store: ResultsStore | None = None,
) -> tuple[dict[str, Verdict], str | None]:
    """
    Evaluate every veto, record all verdicts, and return (verdicts, first_failure).

    Every veto runs even after one has failed. Stopping at the first failure
    would save a few milliseconds and lose the diagnostic that a run breached
    five constraints rather than one, which is the difference between "tune the
    turnover penalty" and "this idea does not fit the mandate".

    A veto that raises is caught and recorded as a failure with the exception
    text. A crashing veto is an unenforced constraint, and unenforced is the one
    thing a veto may not be.
    """
    params = params or get_params()
    order = VETO_ORDER(params)

    verdicts: dict[str, Verdict] = {}
    for name in order:
        try:
            verdict = VETOES[name](ctx, params)
        except Exception as exc:  # noqa: BLE001 - a crashing veto must not pass
            verdict = Verdict(
                passed=False,
                veto=name,
                detail=f"veto raised {type(exc).__name__}: {exc}",
            )
        verdicts[name] = verdict

    failure = first_failure(verdicts, order)

    if store is not None:
        store.record_verdicts(ctx.run_id, verdicts)

    return verdicts, failure


def first_failure(verdicts: dict[str, Verdict], order: list[str] | None = None) -> str | None:
    """The name of the first failing veto in evaluation order, or None."""
    for name in order or list(verdicts):
        if name in verdicts and not verdicts[name].passed:
            return name
    return None
