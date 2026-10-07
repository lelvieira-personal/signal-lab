# 0050 — The columns of the exposure matrix, and which cells are measured

**Status:** decided 2026-10-07 by the owner (OWNER-QUEUE L27: "Yes, as
stated", to the rulings Cowork put to him that afternoon). Drafted by Cowork.
It replaces the proposal of the same number, whose text is in git history;
two of that draft's points were wrong and are corrected below. Follows
`decisions/0015` and `0049`. No change to `SUBSTRATE.md`, `params/` or
`vetoes/`. **Not yet built:** wiring the matrix into `resolve_exposures` is a
later task.

## What was measured first

HANDOFF task 51 built the store `huber6-v1` and reported the estimated
loadings against the measured duration
(`results/characteristics/huber6-v1/report.md`). Cowork read the store as
well (Project doc `claude/tasks-50-51-review-2026-10-07.md`). Figures marked
*(Cowork's read)* were made outside the repo's environment; HANDOFF task 52
reproduces them.

Ratio of the estimated real-yield loading to minus the measured duration:

| Index | Report (ratio of medians) | Weekly median *(Cowork's read)* |
|---|---|---|
| Treasuries 1-3y | 0.57 | 0.56 |
| Treasuries 3-7y | 0.89 | 0.89 |
| Treasuries 7-10y | 0.95 | 0.97 |
| Long Treasury, Treasury 20+ | 0.71, 0.69 | 0.84, 0.84 |
| TIPS | 1.22 | 1.24 |
| IG Corporate | 0.85 | 0.84 |
| MBS | 0.82 | 0.81 |
| HY (five indices) | 0.36 to 0.44 | 0.36 to 0.44 |

- **The gap follows maturity.** The real-yield factor is the change in the
  10-year TIPS yield. At that tenor the estimate equals the measurement. Away
  from it the two part, and further in 2009-15.
- **The owner's reading, which Cowork shares:** the 10-year yield captures
  the level of the curve, and slope and curvature move the short end. The
  estimate is the sensitivity to the 10-year factor; the measurement is the
  sensitivity to the index's own yield. Both are right. The direct test, a
  regression on each index's own yield, has not been run.
- **HY's stated duration is 2.3 to 2.8 times what its returns show.**

## The ruling

1. **A factor block, a measured block beside it, and a label block.**
   - **Factor block:** the six Huber loadings and their standard errors, for
     every estimated instrument, as the store holds them. No cell in it is
     replaced by a measured value.
   - **Measured block:** `INDEX_OAD_TSY` and `INDEX_OAS_TSY`, per instrument
     and week, as the store holds them.
   - **Label block:** region, sector, style and cash, 0 or 1.
2. **What each view axis reads.**

   | Axis | Reads |
   |---|---|
   | duration | the measured duration for Treasuries, Long Treasuries and IG Corporates; minus the real-yield loading for every other instrument |
   | real/nominal | minus the inflation loading |
   | credit | minus the credit loading |
   | region, sector, style, cash | the label block |

3. **Equity, dollar and commodities are columns, not view axes.** They are
   reported as exposures on every run and they serve the risk decomposition.
   No hypothesis targets them. The owner, 2026-10-07: an equity overweight
   should be "a natural consequence" of favourable equity signals, and the
   macro allocation "more of an interpretation of the bottom-up results from
   studying many granular signals". `decisions/0051` is what lets that
   happen. SUBSTRATE §6 is not amended here.
4. **Where a measured cell has no value, the estimate stands in,** marked
   `estimated`. Today that is the 3-7y Treasury index before 2007-01-12.
5. **TIPS read the estimate** until the owner confirms what `INDEX_OAD_TSY`
   is for `LBUTTRUU` (OWNER-QUEUE L30).
6. **Every cell carries its provenance** (`measured` or `estimated`) and
   every instrument its explained share (`decisions/0049`).

## Why beside, not in place

The proposal put the measured value in the factor cell. With one 10-year
factor, that would have raised the 1-3y bucket's real-yield cell from 0.57 of
its duration to 1.00, and the long indices' likewise, in a block whose other
cells are sensitivities to that same factor. The factor block is what the
risk decomposition multiplies by the factor covariance, and it is what
`decisions/0046` tested as one regression. Kept beside, both numbers exist,
and which one an axis reads is a line of code that a later decision can
change without a new store.

## Corrections to the proposal

- **Its label block cited columns that do not exist.**
  `data/universe/investable_universe.csv` has `section` and `reporting_class`
  and no region, sector or style column. Only `cash` has a source today.
- **Its point 1 replaced the factor cell.** See above.
- **"About 30%" for long bonds** (also in `decisions/0049` §6, which stands
  as written) is a ratio of two medians. Week by week it is 16% *(Cowork's
  read)*.

## What it does not decide

- **The label map** (OWNER-QUEUE L28). Four hypotheses target `region`.
- **The eight tradable-only instruments,** which have no row (L29).
- **Whether a nominal Treasury's real/nominal cell should read its measured
  duration.** It reads the estimate until someone asks.
- **Cash's factor cells.** They are estimates of something near zero and are
  left as estimated.
- **A slope factor.** It is the principled fix for the maturity gap. It
  would be a new measurement round and would reopen `decisions/0049` §4.
- **The `lookahead` veto's extension to estimated parameters.** It lands
  with the wiring, as an owner-only patch.

## What would reopen it

- Evidence from the phase-2 solver that reading measured duration sends
  duration views to the wrong instruments.
- A registered hypothesis that targets equity, the dollar or commodities.
