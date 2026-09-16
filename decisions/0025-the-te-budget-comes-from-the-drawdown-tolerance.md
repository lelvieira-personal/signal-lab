# 0025 — The tracking-error budget is derived from the drawdown tolerance

Status: **decided, 2026-09-16, Leo.** Supersedes the two null coefficients in
`decisions/0019`. One item remains open and is named at the end: whether the
`active_drawdown` veto threshold moves with it.

Supersedes the two null coefficients left open by `decisions/0019`.

## The problem it solves

`decisions/0019` made the tracking-error penalty a function of conviction and
left both endpoints null, because there was no principled way to pick them:

> "The owner has deferred the two coefficients until a candidate model exists."

A year of waiting does not make `lambda_low` and `lambda_high` less arbitrary.
The owner's instinct was to replace tracking error in the objective with a
metric that captures active-drawdown risk directly. That instinct is right about
the target and wrong about the mechanism, for a reason worth stating.

## Why not put a drawdown measure in the objective

Conditional Drawdown-at-Risk (Chekhlov, Uryasev and Zabarankin, 2005) is convex
and LP-representable, and it was built for precisely this. But **CDaR is defined
on a path, and it is only meaningful for weights held across that path.** This
lab rebalances weekly against a moving signal. Putting CDaR into a weekly solve
requires assuming today's book is held for the whole scenario horizon, which is
false by construction, and the constraint would then be governing a portfolio
that is never held.

The deeper reason is that **at the single-period level, drawdown is not a new
axis.** It is a function of the two quantities the optimiser already has.

## The scaling law, and why it makes the inversion trivial

For an active path with annualised drift `mu` and annualised volatility `sigma`,
write `IR = mu / sigma`. The path is then `sigma` times a path with drift `IR`
and unit volatility, so

    E[max drawdown] = sigma * g(IR, horizon)

**exactly** — the drawdown scales linearly in tracking error, and the constant
depends only on the information ratio and the horizon. Inverting is therefore
one division:

    TE budget = drawdown tolerance / g(IR, horizon)

`g` is obtained by simulation rather than from a closed form. Magdon-Ismail and
Atiya (2004) give one for Brownian motion, but simulation costs seconds, uses
the actual return convention, and can be re-run on the strategy's own realised
active returns later — which is what turns this from an assumption into a
measurement.

## The map reproduces the numbers the lab already chose

`decisions/0003` ran 20,000 paths of weekly active returns over the 19-year
development window. Re-running that simulation reproduces its table:

| IR | 0003 published | this simulation | g (median) |
|---|---|---|---|
| 0.20 | 20.5% | 20.3% | 3.38 |
| 0.30 | 18.3% | 18.3% | 3.04 |
| 0.50 | 15.3% | 15.2% | 2.54 |
| 0.80 | 12.2% | 12.2% | 2.03 |

Inverting it at the **18% active-drawdown tolerance** the owner settled in 0003:

| expected IR | g(IR) | implied TE budget | vs the 6% mandate |
|---|---|---|---|
| 0.00 | 4.36 | 4.13% | 0.69x |
| 0.10 | 3.82 | 4.72% | 0.79x |
| 0.20 | 3.38 | 5.32% | 0.89x |
| **0.30** | **3.04** | **5.91%** | **0.99x** |
| 0.40 | 2.77 | 6.50% | 1.08x |
| 0.50 | 2.54 | 7.10% | 1.18x |
| 0.65 | 2.26 | 7.98% | 1.33x |
| 0.80 | 2.03 | 8.85% | 1.47x |
| 1.00 | 1.80 | 9.97% | 1.66x |

**At the lab's own target of net IR 0.30, the implied budget is 5.91% against a
6.00% mandate.** The 18% drawdown veto and the 6% tracking-error ceiling were
chosen separately, months apart, and they are consistent to within one and a
half percent. That is the strongest argument for this mechanism: it is not a new
knob, it is the relationship those two numbers were already implicitly asserting.

It also bounds itself. Across the plausible conviction range the budget moves by
a factor of about two, monotonically, with no coefficient chosen by taste.

## Two findings that change the design

**Fat tails are not the problem; persistence is.** `decisions/0003` warned that
its Monte Carlo was optimistic because "real active returns have fat tails and
volatility clustering, both of which deepen drawdowns". Half of that is wrong.
At IR 0.30 over 19 years, per unit of tracking error:

| active return process | g | vs gaussian | implied TE budget |
|---|---|---|---|
| gaussian iid | 3.04 | 1.00x | 5.91% |
| fat tails, Student-t(5) | 3.02 | 0.99x | 5.96% |
| volatility clustering | 3.46 | 1.14x | 5.21% |
| autocorrelation phi = 0.1 | 3.39 | 1.12x | 5.30% |
| autocorrelation phi = 0.2 | 3.78 | 1.24x | 4.76% |

Marginal kurtosis does nothing, because a 19-year maximum drawdown is built by
sustained adverse runs rather than by single bad weeks. **Autocorrelation of the
active return stream is what deepens it**, and a persistent signal produces
exactly that. So `g` should be a function of `(IR, phi)`, not `IR` alone — and
the audit already measures signal autocorrelation per cell, so the second
argument is available. A 52-week signal should get a tighter budget than a
4-week signal at the same conviction. That interaction is real, it is worth
about 20% of the budget, and no hand-set lambda would ever have captured it.

**The statistic matters more than the tolerance.** "An 18% drawdown" is not one
number until you say which path:

| expected IR | median path | 95th-percentile path | mean |
|---|---|---|---|
| 0.00 | 4.13% | 2.40% | 3.92% |
| 0.20 | 5.32% | 3.01% | 4.98% |
| 0.30 | 5.91% | 3.38% | 5.55% |
| 0.50 | 7.10% | 4.19% | 6.70% |
| 0.80 | 8.85% | 5.45% | 8.39% |

Reading it as the median means **half of all paths breach the tolerance** — that
is what 0003's `te_multiple: 3.0` implicitly chose, and it is why 0003 could say
"roughly the worse half of paths fail at IR 0.3". Reading it as the 95th
percentile is a genuinely different mandate and nearly halves the budget.

## The mechanism, concretely

At each rebalance:

1. Solve with the previous period's budget.
2. Read the ex-ante information ratio at the optimum: expected active return
   divided by ex-ante tracking error, both of which the solver already has.
3. Re-derive the budget as `tolerance / g(IR, phi)`.
4. Re-solve. Two passes suffice.

The fixed point is well behaved. Relaxing the budget raises expected active
return less than proportionally, because long-only, the cash cap and the
position cap all bite harder as the book moves further from the benchmark. So
ex-ante IR *falls* as the budget rises, the iteration is a contraction, and it
converges from either side.

That property also supplies the bound `decisions/0019` was reaching for. Its
worry was that "an overfit regime model reporting a spurious [0.99, 0.005,
0.005] would otherwise buy itself unlimited tracking error at exactly the moment
its estimate is worthless", and it answered with a floor on `lambda_high`. Here
the bound comes from the geometry of the constrained problem rather than from a
chosen number: an overconfident alpha cannot manufacture ex-ante IR faster than
the constraints destroy it.

## What is not changed

Nothing. `params/constraints.yaml` still carries the two null coefficients and
the fixed 6% ceiling; `SUBSTRATE` section 4 is untouched; the ruler audit still
runs at a hard 6%. This note exists so the owner can decide, and so the audit can
measure the mechanism as an extra axis of the ladder before it governs anything.

## What the owner decided

**1. The statistic is the 95th percentile.** Not the median. A tolerance that
half of all paths breach is a coin flip, not a tolerance.

**2. The derived budget may exceed the 6% mandate.** Section 4 permits "episodic
excursions, not rewarded on average", and the `tracking_error` veto reads the
95th percentile of trailing-3y readings (`decisions/0003`), so a high-conviction
period may run hot without breaching the mandate test.

**3. `g` is indexed by signal persistence as well as conviction.** A slow signal
produces autocorrelated active returns and therefore deeper drawdowns per unit
of tracking error, and the audit already measures autocorrelation per cell.

**4. The tolerance is recalibrated to 32%, preserving today's risk appetite.**
This was not in the original three questions and it matters more than any of
them. The 18% figure in `decisions/0003` was a MEDIAN statement -- its own
reasoning was "at 3x, roughly the worse half of paths fail at IR 0.3". Reading
that same 18% at the 95th percentile would have tightened twice: once by
changing the statistic, once by keeping a number calibrated for the other one.
The budget at the lab's own IR 0.30 target would have fallen from 6.00% to
2.74%, less than half today's risk, costing an estimated 0.03-0.04 of net IR
through the fee-and-tracking drag being spread over a smaller active risk
budget -- roughly a tenth of the 0.30 bar. The owner chose to preserve the
appetite and express it honestly: **the tolerance is the value that puts the
IR 0.30 budget at exactly 6.00% under a p95 reading, which is 32.0%.**

That number is not a loosening. It is what the current mandate has always
implied and never stated: at 6% tracking error and an information ratio of 0.30
over nineteen years, the 95th-percentile maximum active drawdown is 32%.

## The calibrated table

TE budget at a 32% tolerance, 95th percentile, 19 years:

| expected IR | phi = 0 | phi = 0.1 | phi = 0.2 |
|---|---|---|---|
| 0.00 | 4.27% | 3.99% | 3.73% |
| 0.10 | 4.77% | 4.40% | 4.07% |
| 0.20 | 5.35% | 4.86% | 4.44% |
| **0.30** | **6.00%** | 5.39% | 4.86% |
| 0.40 | 6.71% | 5.96% | 5.32% |
| 0.50 | 7.44% | 6.55% | 5.81% |
| 0.65 | 8.55% | 7.47% | 6.55% |
| 0.80 | 9.68% | 8.41% | 7.33% |
| 1.00 | 11.14% | 9.64% | 8.35% |

The mechanism now loosens as well as tightens, which is what makes decision 2
meaningful: the budget crosses 6% at an expected IR of 0.30 for a fast signal
and around 0.55 for a slow one. A conviction-rich week can take more risk; a
blind week is held near 4%; and a slow signal is held tighter than a fast one at
the same conviction, which no hand-set coefficient would have done.

## The one thing still open: the active-drawdown veto

`params/vetoes.yaml` fails any run whose realised maximum active drawdown
exceeds **18%** (`te_multiple: 3.0`). Designing to a 32% p95 tolerance while
gating at 18% means designing to one standard and judging by another. Measured,
at the 6% budget:

| expected IR | paths breaching the 18% veto | p95 drawdown |
|---|---|---|
| 0.20 | 63.7% | 35.8% |
| **0.30** | **51.9%** | **32.0%** |
| 0.50 | 29.3% | 25.8% |
| 0.80 | 9.1% | 19.8% |

**At the lab's own target, the veto kills 52% of strategies that are performing
exactly to specification.** `decisions/0003` knew this and accepted it -- "at
3x, roughly the worse half of paths fail at IR 0.3, a real bar that a good
strategy can clear" -- but it chose that when the veto was the only mechanism.
Now that the budget is derived to hold the p95 drawdown at 32%, keeping the gate
at 18% throws away half the successes by construction, and it does so hardest
exactly where the strategy is weakest and needs the search most.

Three coherent positions, all the owner's:

1. **Move the veto to 32%**, matching the derivation. The gate then means what
   the design targets: 95% of paths stay inside, and a breach is genuinely
   exceptional. Internally consistent, and a 32% active drawdown is a large
   number to put in front of an allocator.
2. **Keep 18% as a deliberately demanding filter**, accepting that it is a
   different object from the design tolerance and that half of on-specification
   runs die at it. The status quo, chosen knowingly.
3. **Set an intermediate gate** -- 25% is the p95 at IR 0.50 -- which passes
   strategies performing at or above a stretch target and fails the rest.

Nothing is changed in `params/vetoes.yaml` pending that answer.

## What is transcribed now

`params/constraints.yaml` gains a `tracking_error.budget_from_drawdown` block
carrying the tolerance, the statistic, the persistence flag and the horizon,
with `enabled: false` because the solver does not yet read it. The two null
coefficients from `decisions/0019` stay in place for now rather than being
deleted, because `harness/objective.py` still reads them and a params-only
change should not break working code; they are marked superseded and come out
with the solver change.

`scripts/drawdown_map.py` reproduces every number above, including the
`decisions/0003` check.

## What is next, and the falsification test

The solver change -- a per-rebalance derived budget with a two-pass fixed point
-- is deliberately held until `make audit-lean` has produced a baseline and a
runtime on real data. Layering a risk-budget mechanism onto an unvalidated
baseline would make any surprise impossible to attribute.

The test is the owner's own: run the ladder with the derived budget, then check
realised maximum active drawdown against the ex-ante p95 tolerance across the
cells. If the realised distribution sits above 32% at the 95th percentile, `g`
understates the risk and the divergence says by how much. The most likely
culprits, in order: active-return autocorrelation higher than the planted phi,
volatility clustering (worth 1.14x on its own), and a covariance that understates
tracking error out of sample.
