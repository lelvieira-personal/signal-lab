"""
Agent budgets. SUBSTRATE section 14.

"Hard token ceiling per run and per nightly cycle; the wrapper kills on breach,
it does not warn."

Three deliberate design choices:

  * Ceilings come from params/agents.yaml and are currently null, because
    SUBSTRATE requires them but does not state numbers and this lab does not
    invent thresholds. A null ceiling means the wrapper REFUSES to make the
    call. Fail-closed: an unbounded agent is the failure mode the budget exists
    to prevent, so "no ceiling configured" cannot mean "no ceiling".

  * The kill is injectable. In production it terminates the process; in tests it
    raises. Otherwise "test the kill path" would mean killing the test runner.

  * Usage is read from the API response's usage fields rather than estimated
    from string lengths, and cache-read and cache-write tokens are counted
    separately, because a cached prompt is cheap but not free and a budget that
    ignores it will drift.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from signal_lab.params import ParamNotConfigured, Params, get_params
from signal_lab.results.store import ResultsStore


class BudgetExceeded(Exception):
    """The ceiling was reached. The run is over."""


class BudgetNotConfigured(Exception):
    """A required ceiling is null in params/agents.yaml, so no call is made."""


@dataclass
class Usage:
    """Token usage from one model call, as the API reports it."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    model: str | None = None
    batch: bool = False

    @property
    def total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_input_tokens
            + self.cache_read_input_tokens
        )

    @classmethod
    def from_response(cls, response: Any) -> Usage:
        """
        Read usage off a response object or a dict.

        A response with no usage information raises rather than counting zero:
        an uncounted call is an uncapped call.
        """
        usage = (
            response.get("usage")
            if isinstance(response, dict)
            else getattr(response, "usage", None)
        )
        if usage is None:
            raise BudgetExceeded(
                "model response carried no usage field, so its cost cannot be counted. "
                "An uncounted call is an uncapped call; refusing to continue."
            )
        get = (
            (lambda k: usage.get(k, 0))
            if isinstance(usage, dict)
            else (lambda k: getattr(usage, k, 0))
        )
        model = (
            response.get("model")
            if isinstance(response, dict)
            else getattr(response, "model", None)
        )
        return cls(
            input_tokens=int(get("input_tokens") or 0),
            output_tokens=int(get("output_tokens") or 0),
            cache_creation_input_tokens=int(get("cache_creation_input_tokens") or 0),
            cache_read_input_tokens=int(get("cache_read_input_tokens") or 0),
            model=model,
        )

    def cost_usd(self, pricing: dict, batch_discount: float = 0.0) -> float | None:
        """
        Dollar cost of this call, or None when the model has no price entry.

        Priced per token class rather than by a blended rate: on Fable a cache
        read is 40x cheaper than fresh input, so a blended figure would
        misattribute most of the bill. None rather than zero for an unknown
        model, because zero would silently exempt it from the dollar ceiling.
        """
        if not self.model:
            return None
        rates = pricing.get(self.model)
        if not rates:
            return None
        cost = (
            self.input_tokens * float(rates.get("input", 0.0))
            + self.output_tokens * float(rates.get("output", 0.0))
            + self.cache_creation_input_tokens * float(rates.get("cache_write_5m", 0.0))
            + self.cache_read_input_tokens * float(rates.get("cache_read", 0.0))
        ) / 1e6
        if self.batch and batch_discount:
            cost *= 1.0 - float(batch_discount)
        return cost


def _default_killer(message: str) -> None:
    """
    Terminate the process. SUBSTRATE section 14: kill, do not warn.

    os._exit rather than sys.exit because sys.exit raises SystemExit, and a
    broad `except Exception` somewhere in an agent loop would swallow it and
    carry on spending.
    """
    import sys

    print(f"BUDGET KILL: {message}", file=sys.stderr, flush=True)
    os._exit(70)


@dataclass
class CycleBudget:
    """The cycle-wide ceiling, shared by every run in a cycle."""

    limit_tokens: int | None
    limit_usd: float | None = None
    spent_tokens: int = 0
    spent_usd: float = 0.0

    def charge(self, tokens: int, usd: float | None = None) -> None:
        self.spent_tokens += tokens
        if usd:
            self.spent_usd += usd

    def breached(self) -> str | None:
        if self.limit_usd is not None and self.spent_usd > self.limit_usd:
            return f"cycle spent ${self.spent_usd:.2f}, ceiling ${self.limit_usd:.2f}"
        if self.limit_tokens is not None and self.spent_tokens > self.limit_tokens:
            return f"cycle spent {self.spent_tokens} tokens, ceiling {self.limit_tokens}"
        return None


@dataclass
class BudgetLedger:
    """
    Per-run token accounting with a hard ceiling.

    Usage:
        ledger = BudgetLedger(run_id="R-1", store=store)
        response = ledger.call(client.messages.create, model=..., messages=[...])
        ...
        ledger.finalise(status="completed")
    """

    run_id: str
    params: Params | None = None
    store: ResultsStore | None = None
    cycle: CycleBudget | None = None
    killer: Callable[[str], None] = _default_killer
    spent_tokens: int = 0
    spent_usd: float = 0.0
    n_calls: int = 0
    calls: list[Usage] = field(default_factory=list)
    killed: bool = False
    kill_reason: str | None = None

    def __post_init__(self) -> None:
        self.params = self.params or get_params()

    # --- ceilings -----------------------------------------------------------

    def run_ceiling(self) -> int:
        """
        The per-run token ceiling. Raises BudgetNotConfigured when null.

        SUBSTRATE requires a hard ceiling and does not give a number, and
        KICKOFF forbids inventing thresholds. Refusing is the only option that
        breaks neither rule. See decisions/proposed/0007.
        """
        try:
            return int(self.params.require("agents.budgets.tokens_per_run"))
        except ParamNotConfigured as exc:
            raise BudgetNotConfigured(
                "agents.budgets.tokens_per_run is null in params/agents.yaml. "
                "SUBSTRATE section 14 requires a hard ceiling and the lab does not "
                "invent thresholds, so no model call is made until the owner sets one. "
                "See decisions/proposed/0007."
            ) from exc

    def run_cost_ceiling(self) -> float | None:
        """
        The per-run dollar ceiling. None means only the token ceiling applies.

        decisions/0012: a token cap is a poor proxy for a dollar cap when model
        prices span 10x, and the owner's constraint is stated in dollars.
        """
        return self.params.get("agents.budgets.cost_per_run_usd", None)

    def pricing(self) -> dict:
        return self.params.get("agents.pricing.per_million_tokens", {}) or {}

    def batch_discount(self) -> float:
        if not self.params.get("agents.runtime.use_batch_api", False):
            return 0.0
        return float(self.params.get("agents.pricing.batch_discount", 0.0) or 0.0)

    def cost_usd(self) -> float | None:
        """
        Cost in dollars, or None when nothing could be priced.

        None is recorded rather than a made-up figure; a fabricated cost on a
        digest is worse than a blank one.
        """
        return self.spent_usd if self.n_priced_calls() else None

    def n_priced_calls(self) -> int:
        pricing, discount = self.pricing(), self.batch_discount()
        return sum(1 for u in self.calls if u.cost_usd(pricing, discount) is not None)

    # --- accounting ---------------------------------------------------------

    def charge(self, usage: Usage) -> None:
        """Add a call's usage and kill if that crossed any ceiling."""
        self.spent_tokens += usage.total
        self.n_calls += 1
        self.calls.append(usage)
        cost = usage.cost_usd(self.pricing(), self.batch_discount())
        if cost:
            self.spent_usd += cost
        if self.cycle is not None:
            self.cycle.charge(usage.total, cost)
        self._check()

    def _check(self) -> None:
        """Token and dollar ceilings, whichever binds first."""
        cost_ceiling = self.run_cost_ceiling()
        if cost_ceiling is not None and self.spent_usd > float(cost_ceiling):
            self._kill(
                f"run {self.run_id} spent ${self.spent_usd:.2f} over {self.n_calls} call(s), "
                f"ceiling ${float(cost_ceiling):.2f}"
            )
        ceiling = self.run_ceiling()
        if self.spent_tokens > ceiling:
            self._kill(
                f"run {self.run_id} spent {self.spent_tokens} tokens over {self.n_calls} "
                f"call(s), ceiling {ceiling}"
            )
        if self.cycle is not None:
            breach = self.cycle.breached()
            if breach:
                self._kill(f"{breach}, breached during run {self.run_id}")

    def _kill(self, message: str) -> None:
        self.killed = True
        self.kill_reason = message
        self.record(status="killed", killed_by="budget")
        self.killer(message)
        # If the killer returned (a test double), make the breach non-optional
        # for the caller too.
        raise BudgetExceeded(message)

    def call(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Make one model call and charge it.

        The ceiling is checked before the call as well as after: a run already
        at its limit does not get one more request "to finish up".
        """
        cost_ceiling = self.run_cost_ceiling()
        if cost_ceiling is not None and self.spent_usd > float(cost_ceiling):
            self._kill(f"run {self.run_id} was already over its ${float(cost_ceiling):.2f} ceiling")
        ceiling = self.run_ceiling()
        if self.spent_tokens > ceiling:
            self._kill(f"run {self.run_id} was already over its {ceiling}-token ceiling")
        response = fn(*args, **kwargs)
        self.charge(Usage.from_response(response))
        return response

    # --- recording ----------------------------------------------------------

    def record(self, status: str, killed_by: str | None = None, **run_kwargs) -> None:
        """
        Write the run's cost to the store.

        Tolerates the run already existing: a kill records the cost, and a
        subsequent finalise must not crash on the append-only constraint.
        """
        if self.store is None:
            return
        from signal_lab.results.store import StoreError

        try:
            self.store.record_run(
                self.run_id,
                status=status,
                killed_by=killed_by,
                cost_tokens=self.spent_tokens,
                cost_usd=self.cost_usd(),
                params=self.params,
                data_snapshot_hash=run_kwargs.pop("data_snapshot_hash", "unknown"),
                **run_kwargs,
            )
        except StoreError:
            pass

    def finalise(self, status: str = "completed", **run_kwargs) -> None:
        self.record(status=status, **run_kwargs)


def cycle_budget(params: Params | None = None) -> CycleBudget:
    """The cycle ceiling from params. Null means refuse, not unlimited."""
    params = params or get_params()
    try:
        limit = int(params.require("agents.budgets.tokens_per_cycle"))
    except ParamNotConfigured as exc:
        raise BudgetNotConfigured(
            "agents.budgets.tokens_per_cycle is null in params/agents.yaml; see decisions/0007"
        ) from exc
    return CycleBudget(
        limit_tokens=limit, limit_usd=params.get("agents.budgets.cost_per_cycle_usd", None)
    )


def model_calls_enabled(params: Params | None = None) -> tuple[bool, str]:
    """
    Whether any model-driven role may run at all.

    The deterministic parts of a cycle -- load, validate, apply vetoes, record --
    need no model and proceed regardless. This is what lets phase 0 run a cycle
    with the budgets unset instead of blocking on them.
    """
    params = params or get_params()
    for key in ("agents.budgets.tokens_per_run", "agents.budgets.tokens_per_cycle"):
        if params.get(key) is None:
            return False, f"{key} is null in params/agents.yaml (see decisions/0007)"
    roles = ("proposer", "implementer", "critic", "diagnostician", "evaluator", "coordinator")
    unset = [r for r in roles if params.get(f"agents.models.{r}", None) is None]
    if unset:
        return False, f"agents.models.{{{','.join(unset)}}} unset in params/agents.yaml"
    if not params.get("agents.pricing.per_million_tokens", {}):
        return False, "agents.pricing.per_million_tokens is empty; cost cannot be enforced"
    return True, (
        f"budgets configured (${params.get('agents.budgets.cost_per_run_usd')}/run, "
        f"${params.get('agents.budgets.cost_per_cycle_usd')}/cycle), "
        f"{len(roles)} model roles assigned"
    )
