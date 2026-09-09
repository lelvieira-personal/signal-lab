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

3. **A caution I am reasoning to from one sentence, so treat it as a question
   rather than a finding.** If targets propagate to many accounts, the turnover
   that costs money is account-level, not model-level. The `turnover` veto
   measures the model portfolio, and the cost model in SUBSTRATE section 8
   prices the model portfolio's trades. Whether those are the right units for a
   propagated strategy depends on platform mechanics I do not know. Worth a
   look before phase 4, not before phase 1.

## "Robust" is the owner's choice, not a default

Robust estimation of a factor exposure has several reasonable readings, and the
choice materially changes the target that reaches thousands of accounts:

- shrinkage toward a prior (zero, or a peer-group mean) — Bayesian or
  Theil-Goldberger;
- resampling across draws and averaging the loadings — the Michaud argument,
  applied to exposures rather than to weights;
- a robust regression that discounts outliers;
- regime-conditional loadings, which is honest about the fact that the
  equity-rate beta genuinely changed sign in the last decade, and expensive in
  effective sample size.

No default is set. `params/characteristics.yaml` does not exist yet and will
carry the estimator and its parameters when it does, so the choice is versioned
and travels with `params_hash` like every other threshold.

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
