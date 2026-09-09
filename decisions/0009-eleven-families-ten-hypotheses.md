# 0009 — Eleven families, ten hypotheses

Status: proposed, 2026-09-07, agent. Blocking: no. Resolved in favour of coverage.

## Question

KICKOFF item 5 asks for "**ten** pre-registered hypotheses ... at least one per
family listed in `SUBSTRATE.md §6`". SUBSTRATE section 6 lists **eleven**
families: growth, inflation, policy/real rates, credit conditions,
liquidity/money, terms of trade/external, spreads & curve, volatility & stress,
trend/momentum, carry, valuation.

Ten hypotheses cannot cover eleven families with at least one each. The two
instructions are not jointly satisfiable.

## What was done

Eleven hypotheses were registered, `H-2026-0001` through `H-2026-0011`, one per
family. `tests/test_hypotheses.py` asserts the covered set equals the family
set, so the coverage rule is enforced rather than assumed.

## Why that way

The count of ten is arbitrary; the coverage rule is substantive. SUBSTRATE
section 5.6 is explicit that the search must not open on a subset of the signal
set, because "a leaderboard built on price signals alone would tacitly decide
what works before the macro block is tested". Leaving a family unregistered at
phase 0 is a milder version of the same error. Coverage wins.

## Note on provenance

All eleven are registered as `provenance: adaptation` with no `reference`. None
claims `literature`. This is deliberate: SUBSTRATE section 7 says the harness
fetches a literature reference and that a fabricated citation is a failure of
the proposer. No reference resolver is enabled in `params/data_sources.yaml`,
so no citation could be verified, and writing DOIs from memory is exactly how a
fabricated citation enters a registry. Several of these effects do have
well-established literatures and should be re-registered as `literature` with
checked references once a resolver is enabled — see the `reference_resolver`
block in `params/data_sources.yaml`.

---
## Owner decision (2026-09-09, Leo)

Confirmed as a kickoff inconsistency only, not a substantive conflict. Eleven
hypotheses stand, one per family. No issue with the extra one.

The provenance note below is unchanged and still applies: none of the eleven
claims a citation, and they should be re-registered as `literature` with
checked references once a resolver host is allowlisted.

Status: **closed.**
