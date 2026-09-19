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

## Addendum, same day — the boundary tolerance

Raising the ceiling exposed a latent arithmetic defect rather than creating one.
`vetoes/rules.py` compared a realised float aggregate to its threshold with a
bare `<=`. A realised figure is a mean over 52 weeks, a percentile or a max, so
summation error can put a book trading *exactly* the ceiling a few ulps above
it. At 1.50 the arithmetic happened to land clean; at 4.00, `4.00 / 52 * 52`
does not, and the ceiling itself failed — which SUBSTRATE §10 says must pass.

The four float-valued vetoes (`turnover`, `cash`, `tracking_error`,
`seed_stability`) now compare at a **relative tolerance of 1e-9**. That is nine
orders of magnitude below any threshold in `params/vetoes.yaml` and cannot admit
a breach anyone could measure. `positions` is an integer count and stays exact.

This is the reading `audit.ladder.portfolio_veto_verdicts` already used, so the
audit's verdicts and the live veto set now agree at the boundary; they did not
before, and a cell sitting exactly on a threshold could have been judged
differently by the two.

## Resolved: the rebalance policy is weekly re-solve, deliberately (2026-09-19, Leo)

0024 priced turnover rather than walling it. What it never said is whether the
book re-solves every week at all, and nothing else in the repo said it either:
the engine re-solves unconditionally and no record explains that this is a
choice. The owner raised the question on 2026-09-18 — signals observed weekly,
positions allowed to persist for weeks or up to a year, skipping a week's
rebalance acceptable — and three policies were on the table: weekly re-solve, a
no-trade band, or partial adjustment toward an aim portfolio
(Garleanu and Pedersen 2013).

**Decided: weekly re-solve stays, and the alternatives are not built.** The
ten-seed audit `A-20260918-201042` settled it on the numbers.

The whole prize a trade-reducing policy competes for is the cost actually paid,
and across the entire grid that is **17 to 35 bp a year** — 17 bp at IC 0.02 and
2% annual turnover, 35 bp at IC 0.20 and 172%. At the 6% TE budget of
`decisions/0025`, 35 bp is about 0.06 of information ratio, and a band can
recover only part of it.

Against that, a band costs transfer coefficient by construction: a book that
deliberately does not trade sits away from its own optimum, and TC is the linear
term in `IR = TC x IC x sqrt(BR)` where breadth is under a square root
(`decisions/0033` §7a, which states the measurement consequence and stands as
written — its condition is now known not to hold).

The turnover-cap ladder is the direct test. At IC 0.20, capping annual traded
notional at 50% saved 12 bp of cost and cost **0.033 of net IR** (0.323 against
0.356 uncapped). Restricting trade lost more alpha than it saved.

And the persistence the owner asked for is already what this objective produces
when the signal is slow: at h13 and IC 0.02 the book turns over **2% a year**
under forced weekly re-solve. No new mechanism was needed to deliver it.

**What would wake this.** Not a measurement — a cost-model revision. The buckets
in `params/costs.yaml` are 5/10/20 bp half-spread plus 5/15/35 bp fee. If real
execution proves several times worse, the prize scales with it and the
arithmetic above changes sign.

**Read with care.** The cost drag figures are accounting numbers — basis points
actually paid — and are reliable. The net IR differences beside them are not:
per-cell seed range on that run is 0.26 to 1.42 IR, and the cost stress at
IC 0.20 is non-monotone (0.356, 0.277, 0.421), which reads as a defect rather
than a result. The decision rests on the drag, not on the IR deltas. The cells
are also planted synthetic signals on the Bloomberg panel, so this is evidence
about the machinery and not a forecast for any registered hypothesis.
