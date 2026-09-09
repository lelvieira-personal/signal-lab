"""
Agent budgets. SUBSTRATE section 14, as amended by decisions/0007 and 0012:
the wrapper kills on breach, it does not warn, and it enforces a dollar ceiling
alongside the token ceiling because model prices span 10x.

The killer is injected so the kill path can be tested without killing pytest.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from signal_lab.harness.budgets import (
    BudgetExceeded,
    BudgetLedger,
    BudgetNotConfigured,
    CycleBudget,
    Usage,
    cycle_budget,
    model_calls_enabled,
)
from signal_lab.params import PARAM_FILES, load_params

SONNET = "claude-sonnet-5"  # $2 in / $10 out / $0.20 cache read per Mtok
FABLE = "claude-fable-5-1"  # $10 in / $50 out / $0.25 cache read per Mtok


def variant(tmp_path, params, **replacements):
    """params/ with specific lines rewritten, for tests only."""
    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "agents.yaml"
    text = target.read_text()
    for old, new in replacements.items():
        text = text.replace(old.replace("__", " "), new.replace("__", " "))
    target.write_text(text)
    return load_params(tmp_path)


class Killed(Exception):
    """Stands in for process termination."""


def raising_killer(message: str) -> None:
    raise Killed(message)


def response(model=SONNET, input_tokens=0, output_tokens=0, cache_read=0, cache_write=0):
    return {
        "model": model,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_write,
        },
    }


# --- usage accounting --------------------------------------------------------


def test_usage_counts_every_token_class():
    u = Usage.from_response(
        response(input_tokens=100, output_tokens=50, cache_read=400, cache_write=20)
    )
    assert u.total == 570, "cached tokens are cheap but not free and are counted"


def test_a_response_without_usage_is_refused():
    with pytest.raises(BudgetExceeded, match="no usage field"):
        Usage.from_response({"content": "hi"})


def test_usage_reads_an_object_as_well_as_a_dict():
    class R:
        model = SONNET

        class usage:
            input_tokens = 10
            output_tokens = 5
            cache_read_input_tokens = 0
            cache_creation_input_tokens = 0

    assert Usage.from_response(R()).total == 15


def test_cost_is_priced_per_token_class_not_blended(params):
    """
    A blended rate would misattribute the bill: on Fable a cache read is 40x
    cheaper than fresh input, so a run that is mostly cache reads costs almost
    nothing while a blended figure would call it expensive.
    """
    pricing = params.require("agents.pricing.per_million_tokens")
    cheap = Usage.from_response(response(FABLE, cache_read=1_000_000)).cost_usd(pricing)
    dear = Usage.from_response(response(FABLE, output_tokens=1_000_000)).cost_usd(pricing)
    assert cheap == pytest.approx(0.25)
    assert dear == pytest.approx(50.0)


def test_an_unpriced_model_returns_none_rather_than_zero(params):
    """Zero would silently exempt an unknown model from the dollar ceiling."""
    pricing = params.require("agents.pricing.per_million_tokens")
    assert (
        Usage.from_response(response("some-new-model", output_tokens=10_000)).cost_usd(pricing)
        is None
    )


def test_fable_is_the_most_expensive_tier(params):
    """
    Guards the assumption in decisions/0007. If tiering changes, this fails and
    the cost estimates in that decision need revisiting.
    """
    pricing = params.require("agents.pricing.per_million_tokens")
    assert pricing[FABLE]["output"] > pricing["claude-opus-5"]["output"] > pricing[SONNET]["output"]


# --- the dollar ceiling ------------------------------------------------------


def test_the_kill_path_fires_on_the_dollar_ceiling(params, store):
    """1M Fable output tokens is $50, well past the $3.50 per-run ceiling."""
    ledger = BudgetLedger(run_id="R-usd", params=params, store=store, killer=raising_killer)
    with pytest.raises(Killed, match=r"ceiling \$3.50"):
        ledger.call(lambda: response(FABLE, output_tokens=1_000_000))
    assert ledger.killed


def test_calls_under_the_ceiling_are_charged_and_survive(params, store):
    ledger = BudgetLedger(run_id="R-ok", params=params, store=store, killer=raising_killer)
    for _ in range(3):
        ledger.call(lambda: response(SONNET, input_tokens=20_000, output_tokens=5_000))
    assert ledger.n_calls == 3
    assert ledger.spent_usd == pytest.approx(3 * (20_000 * 2 + 5_000 * 10) / 1e6)
    assert not ledger.killed


def test_the_dollar_boundary_is_the_ceiling_itself(params, store):
    """Exactly at the ceiling survives; past it does not."""
    ledger = BudgetLedger(run_id="R-edge", params=params, store=store, killer=raising_killer)
    ledger.call(lambda: response(SONNET, output_tokens=350_000))  # exactly $3.50
    assert ledger.spent_usd == pytest.approx(3.50)
    assert not ledger.killed
    with pytest.raises(Killed):
        ledger.call(lambda: response(SONNET, output_tokens=1_000))


def test_the_token_ceiling_still_binds_when_the_model_is_cheap(params, store):
    """
    Both ceilings are live, whichever binds first. Haiku output would have to
    run to $2 before the dollar cap fires, so the token cap is what stops a
    runaway loop on a cheap model.
    """
    ledger = BudgetLedger(run_id="R-tok", params=params, store=store, killer=raising_killer)
    with pytest.raises(Killed, match="tokens"):
        ledger.call(lambda: response("claude-haiku-4-5", cache_read=500_000))


def test_the_batch_discount_is_applied_when_enabled(params, store):
    pricing = params.require("agents.pricing.per_million_tokens")
    u = Usage.from_response(response(SONNET, output_tokens=1_000_000))
    u.batch = True
    assert u.cost_usd(pricing, batch_discount=0.5) == pytest.approx(5.0)
    assert u.cost_usd(pricing, batch_discount=0.0) == pytest.approx(10.0)


def test_a_kill_records_the_cost_in_the_store(params, store):
    ledger = BudgetLedger(run_id="R-cost", params=params, store=store, killer=raising_killer)
    with pytest.raises(Killed):
        ledger.call(lambda: response(FABLE, output_tokens=1_000_000))
    runs = store.list_runs()
    assert list(runs["run_id"]) == ["R-cost"]
    assert runs.loc[0, "status"] == "killed"
    assert runs.loc[0, "killed_by"] == "budget"
    assert runs.loc[0, "cost_tokens"] == 1_000_000
    assert runs.loc[0, "cost_usd"] == pytest.approx(50.0)


def test_a_run_already_over_budget_gets_no_further_call(params, store):
    ledger = BudgetLedger(run_id="R-over", params=params, store=store, killer=raising_killer)
    ledger.spent_usd = 99.0
    calls = []
    with pytest.raises(Killed, match="already over"):
        ledger.call(lambda: calls.append(1) or response(SONNET, output_tokens=1))
    assert calls == [], "no request is sent once the ceiling is already breached"


# --- the cycle ceiling -------------------------------------------------------


def test_the_cycle_ceiling_kills_even_when_each_run_is_within_its_own(params, store):
    cycle = CycleBudget(limit_tokens=10_000_000, limit_usd=6.0)
    for i in range(2):
        led = BudgetLedger(
            run_id=f"R-c{i}", params=params, store=store, cycle=cycle, killer=raising_killer
        )
        led.call(lambda: response(SONNET, output_tokens=300_000))  # $3.00 each
        led.finalise(status="completed")
    assert cycle.spent_usd == pytest.approx(6.0)

    led = BudgetLedger(
        run_id="R-c2", params=params, store=store, cycle=cycle, killer=raising_killer
    )
    with pytest.raises(Killed, match="cycle spent"):
        led.call(lambda: response(SONNET, output_tokens=100_000))


def test_cycle_budget_reads_both_ceilings_from_params(params):
    cb = cycle_budget(params)
    assert cb.limit_tokens == params.require("agents.budgets.tokens_per_cycle")
    assert cb.limit_usd == params.require("agents.budgets.cost_per_cycle_usd")


# --- fail-closed when unconfigured -------------------------------------------


def test_a_null_token_ceiling_refuses_the_call_rather_than_allowing_it(tmp_path, params, store):
    """
    Fail-closed. SUBSTRATE requires a ceiling; the lab does not invent one; so
    with none configured no model call is made.
    """
    unset = variant(tmp_path, params, **{"tokens_per_run: 400000": "tokens_per_run: null"})
    ledger = BudgetLedger(run_id="R-unset", params=unset, store=store, killer=raising_killer)
    with pytest.raises(BudgetNotConfigured, match="tokens_per_run"):
        ledger.call(lambda: response(SONNET, output_tokens=1))


def test_cycle_budget_refuses_when_unset(tmp_path, params):
    unset = variant(tmp_path, params, **{"tokens_per_cycle: 3000000": "tokens_per_cycle: null"})
    with pytest.raises(BudgetNotConfigured, match="tokens_per_cycle"):
        cycle_budget(unset)


def test_model_calls_are_enabled_now_that_the_roles_are_assigned(params):
    enabled, reason = model_calls_enabled(params)
    assert enabled, reason
    assert "$3.5/run" in reason or "3.5" in reason


def test_model_calls_are_disabled_when_a_role_is_unassigned(tmp_path, params):
    unset = variant(tmp_path, params, **{"critic: claude-sonnet-5": "critic: null"})
    enabled, reason = model_calls_enabled(unset)
    assert not enabled and "critic" in reason


def test_cost_is_null_rather_than_invented_when_nothing_could_be_priced(params, store):
    ledger = BudgetLedger(run_id="R-nocost", params=params, store=store, killer=raising_killer)
    ledger.call(lambda: response("some-unpriced-model", output_tokens=100))
    assert ledger.cost_usd() is None
    ledger.finalise(status="completed")
    assert store.list_runs().loc[0, "cost_usd"] is None
