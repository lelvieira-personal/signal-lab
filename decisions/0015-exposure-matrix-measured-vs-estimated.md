# 0015 — The exposure matrix: measured, estimated, and estimated *when*

Status: decided in principle 2026-09-09; built in phase 2. One consequence
lands in phase 1 and is flagged below.

## What the owner asked for

> "I would like to have robust estimation of the factor exposures at some point.
> One of the ways that we implement a coherent strategy across hundreds and in
> the future potentially thousands of mandates is by propagating target factor
> exposures to each account. The factor targets are based on the optimal
> allocation that the model generates for the 50/50."

This settles the question left open in `decisions/0013` — an equity index's
duration exposure is an **estimated** rate beta, not a definitional zero — and
it also changes what the exposure matrix *is for*. Recording both, because the
second part is easy to lose and it reframes the deliverable.

## The deliverable is the exposure vector, not the weights

The 30-instrument portfolio is a means. What travels to production is the
**target factor exposure vector**, propagated to individual accounts that have
their own benchmarks, constraints and implementation vehicles. The weights are
one instantiation of the targets against one benchmark.

Three consequences follow. The first two are design, the third is a caution.

1. **The exposure vector deserves first-class treatment in the render layer and
   the artifact store**, alongside weights and active returns. Its *stability*
   over time matters as much as its level, because an unstable target is
   thousands of accounts trading.

2. **A per-cell provenance flag.** An exposure matrix that mixes measured and
   estimated cells without labelling which is which invites treating a noisy
   regression coefficient with the same confidence as a contractual property.
   These are not the same kind of number:

   - **measured** — a fact about the instrument, read from the analytics panel.
     A bond index's effective duration (`INDEX_OAD_TSY`) and option-adjusted
     spread (`INDEX_OAS_TSY`) are measured. So is a sector or region label.
   - **estimated** — a behaviour, inferred from returns, with a standard error.
     An equity index's rate sensitivity, its credit beta, its inflation beta.

   The risk decomposition can then report how much active risk rests on
   estimated exposures, and the solver can shrink the estimated cells toward a
   prior while leaving the measured ones alone. Without the flag, neither is
   possible.

3. **Propagation is explicitly out of scope for now** (owner, 2026-09-09). The
   multi-account context is why exposure accuracy matters, not a thing to build
   for. The project's objective is unchanged: beat the 50/50 net of costs, with
   risk management strong enough and a model legible enough to defend in front
   of a room of investment professionals. Anything account-level waits.

## "Robust" is a research question, not a parameter

This note originally proposed putting the estimator in
`params/characteristics.yaml` as a threshold for the owner to set. That was
wrong, and the owner said so:

> "Robust estimation for the factor loadings is something that requires research
> too. I don't have the answer and it is something that the agents will need to
> study as part of the hypothesis too, because at the end of the day getting the
> correct combination of factor exposures will not yield good results if the
> instruments don't have a true sensitivity to them."

The exposure matrix is not infrastructure that the model runs on. It is **part
of the model**. A correct view mapped through a wrong loading produces a wrong
portfolio, and the failure is invisible: the signal was right, the weights were
wrong, and the leaderboard shows a dead idea.

So the estimator is pre-registered and tested like anything else. Because
choosing it on the strategy's own objective would be circular, it needs a
separate class of hypothesis with a separate objective — see
`decisions/0016`.

## The part that is not obvious: an estimated matrix can leak

A definitional exposure matrix is constant, so using it at every rebalance date
is harmless. An **estimated** one is not. Estimating loadings on the full sample
and then using them at every rebalance date is lookahead — the 2004 portfolio
would be built on a rate beta measured partly from 2019.

It is a nastier leak than the usual kind, because it is not in the returns and
not in the signals. It is in the *mapping*, and every downstream number looks
clean. The `lookahead` veto as built checks macro observation vintages; it would
not see this at all, because no macro observation was misdated.

So: **loadings must be estimated walk-forward**, on data available at each
rebalance date, and the `lookahead` veto needs extending to cover estimated
parameters as well as observed vintages. That extension belongs with the
estimator in phase 2.

## Consequence for phase 1 — the one thing that lands now

The walk-forward engine must accept a **time-varying** exposure matrix,
`exposures(date) -> DataFrame`, rather than a static one. The interface costs
nothing to write correctly now and would mean rewriting the engine and every
artifact it produces if it were written static and changed in phase 2.

Phase 1 will pass it a constant matrix derived from the synthetic panel's five
latent factors. The signature is what matters, not the contents.
