# 0041 — The joint null is a block shuffle, not a block bootstrap

**Status:** decided 2026-09-29 by the owner ("amend substrate to do shuffle
instead of bootstrap"). Drafted by Cowork. Applied by HANDOFF task 40, which
cites this record. Amends SUBSTRATE §9 and the §15 layout line.

## Why

SUBSTRATE §9 says the joint distribution that the Romano-Wolf stepdown uses
comes from "block bootstrap on the daily panel". The code has never done that.
`stats/blocks.py` block-*permutes* the signal's rows, with one permutation
shared by every hypothesis in each draw, and `stats/multiple_testing.py` takes
those draws as `T0`. The constitution and the code disagree, and the code is
the one that matches the question being asked.

**Bar 2 (§3) asks whether this is signal or the sample's beta.** Its null is
"the same book on the same history, with the signal's alignment to future
returns destroyed". A block shuffle builds exactly that world. It keeps the
market path, the constraints, the static tilt and the signal's persistence,
and breaks only the timing. A block bootstrap of the panel answers a different
question: how much would the statistic vary across other plausible histories?
It resamples the static tilt and beta along with everything else, which are
the confounds bar 2 exists to remove, and it needs stationarity across the
window plus a centring scheme of its own.

What Romano-Wolf needs from its resampling is the **joint** null distribution
of the statistics, with their real dependence. A shared permutation per draw
supplies that. It is the permutation (Westfall-Young) form of the stepdown.

## The ruling

1. **Every null used by a test** (the bar-2 excess, the search null, the
   multiple-testing gate) comes from a **block shuffle of the signal**: its
   rows are permuted in contiguous blocks, block length ≥ the longest signal
   horizon, with one permutation shared by every hypothesis in a draw.
2. **Confidence intervals stay on the block bootstrap.** A shuffle yields a
   null distribution, not a sampling distribution, and can't produce an
   interval for the IR. This scoping is Cowork's reading of the ruling; the
   owner may widen or narrow it.

## What the shuffle does and does not license (recorded, not ruled)

- **It is a conditional test:** "better than chance on this history". Whether
  the effect generalises to other histories is the job of replication
  (`decisions/0039`), not of this test.
- **It assumes blocks are exchangeable.** A block shorter than the signal's
  persistence makes the null too narrow and inflates false passes. Block
  length should be checked against each signal's autocorrelation once
  `signals/` exists.
- **It keeps each seed's static tilt**, which is why the shuffled null is
  narrower than the spread across seeds (0.174 against 0.26, task 25). That is
  correct for this question.
- **Romano, Shaikh & Wolf (2008, *TEST*) prove their FDR procedure for the
  i.i.d. bootstrap only** (task 38). Any later procedure has to be checked for
  whether its argument covers permutation nulls.

## Implementation note: the gate standardises before taking the maximum

This is a code-level fix recorded here, not a change to SUBSTRATE's text.
`romano_wolf` takes the maximum across hypotheses of the raw `net_ir_excess`
null draws. Hypotheses whose null is wider (more tracking error) would then
dominate the maximum and cost the narrow-null ones power. Romano and Wolf
recommend studentised statistics for this reason. HANDOFF task 40 transforms
each column, and its observed value, by the column's own null mean and
standard deviation before the stepdown. Marginal p-values are unchanged by
this; only the comparison across hypotheses is.

**2026-09-29, task 41:** task 40's version standardised each column by `T0`'s
own mean and sd, excluding the observed value -- that breaks exchangeability
between the observed row and the null draws and inflated small-k FWER (0.127
at k=20 against nominal 0.05). The fix pools the observed value into the mean
and sd (`k + 1` values), which keeps the transform symmetric and exact.

## Amended text (task 40 transcribes it verbatim)

**§9, first bootstrap bullet.** Replace

> - Confidence intervals and the search null come from a **block bootstrap**
>   on the daily panel, block length ≥ the longest signal horizon.

with

> - Confidence intervals come from a **block bootstrap** on the daily panel,
>   block length ≥ the longest signal horizon. Every null used by a test —
>   bar 2's excess, the search null and the multiple-testing gate — comes
>   from a **block shuffle** of the signal: its rows permuted in contiguous
>   blocks of at least the longest signal horizon, the same book on the same
>   history with only the signal's alignment to future returns destroyed
>   (`decisions/0041`).

**§9, Romano-Wolf bullet.** In

> The joint distribution of all test statistics in a search is obtained by
> block bootstrap on the daily panel, so dependence between experiments is
> learned from the data, not assumed.

replace "by block bootstrap on the daily panel" with "from block shuffles of
the signals, one permutation shared by every hypothesis in each draw". The
rest of the bullet is unchanged.

**§15 layout.** `stats/         HAC, block bootstrap, search null, deflated IR`
becomes `stats/         HAC, block bootstrap, block shuffle, search null,
multiple testing, deflated IR`. Keep the line's alignment and wrap it if it
exceeds the block's width.

Nothing else in SUBSTRATE changes. The status line and version are the
owner's.

## Consequences

- `decisions/0100` gains a row for this amendment when task 40 applies it.
- No `params/` change and no `params_hash` change.
