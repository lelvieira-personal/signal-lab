# 0024 — Turnover is priced, not walled

Status: decided, 2026-09-16, Leo. Supersedes the 150% hard ceiling of
SUBSTRATE §4 and §10. Amends `SUBSTRATE.md`, `params/constraints.yaml`,
`params/vetoes.yaml`.

## What the owner said

> "no hard wall, just higher cost as turnover increases near or above 100% in a
> rolling year."

And, asked two questions before the change was written:

- the `turnover` veto **stays**, moved to a far backstop rather than removed —
  ten vetoes, one threshold changed;
- the cost curve **starts at 75%**, below the target, linear, so it is already
  biting as the year approaches 100%.

## Decided

1. **There is no annual turnover wall.** `constraints.turnover.max_annualised`
   is gone. The annual figure is priced and never capped.

2. **The shadow cost is a one-sided linear function of trailing one-year traded
   notional**, unbounded above:

       shadow(T) = coefficient · max(0, T − start) / (reference − start)

   with `start = 0.75`, `reference = 1.50`, `coefficient = 10bp`:

   | trailing annual turnover | 0.75 | 1.00 | 1.50 | 2.00 | 3.00 | 4.00 |
   |---|---|---|---|---|---|---|
   | shadow cost (bps) | 0.0 | 3.3 | 10.0 | 16.7 | 30.0 | 43.3 |

   against roughly 15bp of real mid-bucket half-spread on that same trading.

3. **The `turnover` veto survives as a backstop at 400% a year.** At that level
   the shadow cost is 43bp, three times the real spread: a book arriving there
   is not making an expensive choice, it is malfunctioning. The veto exists to
   catch a solver defect or a degenerate book, and nothing about 150%, 200% or
   300% a year is forbidden.

4. **The per-session cap is unaffected.** It answers a different question — that
   no single rebalance consumes the year — and its value is still to be chosen
   from the audit's swept evidence.

## Why the wall had to go

A hard annual cap is free to trade right up to the limit and then forbids
trading entirely. That is the failure the owner named on 2026-09-11: *"avoid a
situation where we rebalanced too much on previous windows and then cannot do
more when we really need it due to TO budget constraints."* The wall gives the
worst incentive at both ends — no restraint until the budget is nearly spent,
then total prohibition regardless of how good the opportunity is. A cost that
rises without bound inverts both: the quiet week already pays something, and the
week carrying real alpha can always pay more.

## Why the curve starts below the target

A cost that switches on exactly at 100% leaves a kink. Turnover just under the
target is free and turnover just over it is not, so the optimiser has a reason
to sit at 99% that has nothing to do with the alpha. Starting at 75% removes the
kink from the operating range: by the time the year reaches the target the cost
is already 3.3bp and rising smoothly, and there is no threshold to hug.

## What this changes numerically

The slope is *gentler* per unit than the old curve — 13.3bp per unit of turnover
rather than 20bp — because the anchor at 150% was held fixed while the start
moved down. Below about 125% a year the new curve charges more; above it,
slightly less. `coefficient` is the dial if the owner wants it steeper; the
shape is what this decision fixes.

## An inconsistency this fixes

`harness/objective.py` and `audit/ladder.py` had both implemented the penalty
and **disagreed by a factor of two**: the former read `coefficient · (T − target)`
unnormalised, giving 5bp at 150%, while the latter normalised by the span and
gave 10bp. Both now read the same three parameters and agree at every point.
The audit's ladder was the one matching `decisions/0018`; the objective was
wrong and has never been used in a scored run.

## Superseded

`decisions/0018` set `coefficient = 10bp` as bps per unit of excess turnover
measured from the 100% target. The coefficient and its magnitude survive; what
it is measured from does not. `decisions/0003`'s reading of 150% as a mandate
ceiling is withdrawn for turnover only — the tracking-error ceiling is
untouched.
