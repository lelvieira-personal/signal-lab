# 0007 — The agent budget numbers. BLOCKING for phase 4.

Status: proposed, 2026-09-07, agent. Blocking: yes, for any model-driven role.

## Question

SUBSTRATE section 14 requires a "hard token ceiling per run and per nightly
cycle", a maximum number of proposals per family per cycle, a maximum number of
refinement rounds per proposal, a quota for `novel` provenance (section 7), and
a cheap and an expensive model tier. It states none of the numbers, and KICKOFF
forbids inventing thresholds.

## What was done

Every one of them is `null` in `params/agents.yaml`, and the code fails closed:

- `BudgetLedger.call` raises `BudgetNotConfigured` rather than making a model
  call while `tokens_per_run` is null.
- `cycle_budget()` raises while `tokens_per_cycle` is null.
- `model_calls_enabled()` returns False, and `scripts/nightly_cycle.py` reports
  "model roles: disabled" and proceeds with its deterministic steps only.

The enforcement mechanism is tested against ceilings set inside the test
fixture, so the kill path is proven without an invented number reaching the
repository's configuration.

## Why that way

The alternative to refusing is a generous default, and a generous default is
indistinguishable from no ceiling on the night it matters. Phase 0 needs no
model calls, so refusing costs nothing today and prevents an unbounded agent
loop later.

## What to decide

Six numbers, please:

1. `budgets.tokens_per_run`
2. `budgets.tokens_per_cycle`
3. `quotas.max_proposals_per_family_per_cycle`
4. `quotas.max_refinement_rounds_per_proposal`
5. `quotas.novel_provenance_per_cycle`
6. `models.cheap` and `models.expensive` — model ids, not descriptions

And optionally `pricing.per_million_tokens.blended`, without which `cost_usd`
is recorded as NULL rather than as a guess.

---
## Owner decision (2026-09-09, Leo)

### Spend

> "I don't want to spend more than $30 / month on top of my claude subscription
> with this routine, but I would be fine to spend $100 in the beginning
> considering there are things that need to be built before we are in autonomous
> routine mode."

Set: `cost_per_month_usd: 100.00` (early build), with `30.00` noted as the
steady-state figure to switch to.

### Transport: API, not the subscription

The owner holds both a Pro subscription and Console API keys. The autonomous
cycle runs against the **API**, headless, with `ANTHROPIC_API_KEY` from the
environment. Three reasons:

- the budget wrapper reads per-call usage off the API response; a subscription
  session does not expose those fields to the script, so the ceiling could not
  be enforced;
- cron in WSL needs a headless process, not a desktop app that must be open;
- a nightly batch on the subscription would consume the same rate limits the
  owner uses interactively.

Development of the harness stays on the subscription. Only the unattended
routine is metered. Recorded as `agents.runtime.transport: api`.

### Cadence: weekly, and the reason is statistical

Set `cycle_cadence: weekly`. Seven proposals x 30 nights is 210 correlated tests
a month; Romano-Wolf across 210 draws sets a bar a real macro signal will not
clear. Weekly gives 28. The model's own clock is weekly-to-quarterly, so nightly
proposals mostly redraw from the same information.

This is the rare case where the cost lever and the statistical lever point the
same way, and the statistical argument is the binding one. The deterministic
parts of the cycle may still run nightly; it is the *proposer* that is weekly.

### Costing

Per-million-token prices as of 2026-09-09, recorded in
`params/agents.yaml:pricing` with their source and date:

| Model | Input | Output | Cache read |
|---|---|---|---|
| Fable 5.1 | $10 | $50 | $0.25 |
| Opus 5 | $5 | $25 | $0.50 |
| Sonnet 5 | $2 | $10 | $0.20 |
| Haiku 4.5 | $1 | $5 | $0.10 |

**Fable is the dearest tier, twice Opus on output** — which inverts the usual
assumption and matters because the owner's tiering puts Fable on two of the six
roles.

Estimated cost per proposal, assuming the ~30k-token stable context is
prompt-cached as section 14 requires and the Implementer runs ~6 agentic turns:

| Role | Model | Est. |
|---|---|---|
| Proposer | Fable 5.1 | $0.10 |
| Implementer | Sonnet 5 | $0.16 |
| Critic | Sonnet 5 | $0.03 |
| Evaluator | Fable 5.1 | $0.19 |
| **Per proposal** | | **~$0.48** |

At 7 proposals that is ~$3.35 a cycle: **~$100/month nightly, ~$13/month
weekly, ~$7/month weekly on the Batch API.** These are estimates with stated
assumptions, not quotes; the Implementer turn count is the largest uncertainty
and could double. The Evaluator is the single most expensive step, because
evaluation output is long prose at Fable's output rate — if the bill binds,
shorten the evaluator's output before cutting anywhere else.

`use_batch_api: true` is set. The cycle is async by nature, so the 50% batch
discount costs nothing in usability.

### Model tiering, as stated by the owner

| Role | Model |
|---|---|
| Proposer | Fable 5.1 |
| Implementer | Sonnet 5 |
| Critic | Sonnet 5 |
| Diagnostician | Opus 5 |
| Evaluator | Fable 5.1 |
| Coordinator | Sonnet 5 |

The two-tier `cheap`/`expensive` schema in the original `agents.yaml` was
replaced with one entry per section 13 role. Ids are validated against the API
at cycle start; an unknown id refuses rather than falling back to a default.

### Quotas

`max_proposals_per_family_per_cycle: 7`, as stated.

On refinement rounds the owner was undecided and raised a real risk:

> "It would be a shame to throw away a promising hypothesis due to cap on
> refinement runs."

That has a design answer rather than a numeric one. `on_refinement_cap:
requeue_to_pending`: a proposal that exhausts its rounds is **not discarded**.
It returns to `hypotheses/pending/` with the Diagnostician's notes attached and
is picked up next cycle. The cap therefore limits spend *per cycle* without ever
losing an idea, which is what makes a low cap safe. K is set to 2 and should be
reset from four weeks of logged rounds-used rather than guessed now.

`novel_provenance_per_cycle: 2`.

### Amendment to section 14

Section 14 specifies a token ceiling. Both a token ceiling and a **dollar**
ceiling are now enforced, whichever binds first — see `decisions/0012`.

Status: **closed**, with K to be revisited from logged data after four weeks.
