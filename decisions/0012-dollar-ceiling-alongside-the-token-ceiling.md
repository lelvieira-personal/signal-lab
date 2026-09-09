# 0012 — A dollar ceiling as well as a token ceiling

Status: decided, 2026-09-09. Amends SUBSTRATE section 14.

## Question

SUBSTRATE section 14 specifies "a hard token ceiling per run and per nightly
cycle". Model prices span 10x across the tiers this lab uses: a million output
tokens costs $5 on Haiku and $50 on Fable. A token ceiling therefore permits ten
times the spend on one model as on another, and the owner's constraint is stated
in dollars.

## Decision

Enforce both. `params/agents.yaml:budgets` carries `cost_per_run_usd`,
`cost_per_cycle_usd` and `cost_per_month_usd` alongside `tokens_per_run` and
`tokens_per_cycle`. The wrapper kills on whichever binds first.

The token ceiling is not redundant: it is the guard that stops a runaway loop on
a cheap model, where the dollar ceiling would take a long time to bite.
`tests/test_budgets.py` covers both paths.

Cost is computed per token class from `agents.pricing.per_million_tokens`
rather than from a blended rate, because on Fable a cache read is 40x cheaper
than fresh input and a blended figure would misattribute most of the bill. A
model with no price entry costs `None`, not zero — zero would silently exempt
an unknown model from the ceiling.

## Consequence for the constitution

Section 14's first bullet should read "hard token and cost ceilings per run and
per cycle". Recorded in `decisions/0100-substrate-amendments.md`.

## What this does not solve

`cost_per_month_usd` is recorded but not yet enforced; enforcing it needs the
cycle to read prior months' spend out of the results store at startup. That
lands with the scheduler in phase 4.
