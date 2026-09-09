# 0004 — Is gross IR shown as a number, or not shown at all?

Status: proposed, 2026-09-07, agent. Blocking: no. Conservative option taken.

## Question

SUBSTRATE section 3: "Gross IR is recorded and never used for ranking."
SUBSTRATE section 12: "gross IR is never plotted."

Neither sentence settles whether gross IR may appear on the report as a text
statistic. The mock render provided showed it as a stat tile beside net IR.

## What was done

Removed. `render/views.py:run_summary_stats` does not return gross IR, and
`tests/test_render.py` asserts it appears nowhere in the rendered document. It
remains in the results store, which section 3 requires.

## Why that way

Section 12 bars plotting it; the strict reading of section 3 is that it exists
for diagnostics, not for the reader of a leaderboard. Showing net and gross
side by side invites exactly the comparison the substrate forbids — the reader
does the ranking in their head — and the cost of removing it is that a
diagnostic question needs a query rather than a glance.

## What to decide

Whether a gross figure belongs on the run-detail view for cost-attribution
purposes, perhaps as gross-minus-net (the cost drag) rather than as gross
itself. The drag is arguably the useful number and carries no ranking
temptation.

---
## Owner decision (2026-09-09, Leo)

Gross IR stays off the report entirely. The **cost drag** is reported in its
place: "the cost drag is important, no need to have Gross IR as we can infer
from net and cost drag."

Implemented: `params/costs.yaml` sets `application.report_cost_drag: true`;
`render/views.py:run_summary_stats` shows `cost_drag` and never `gross_ir`;
`tests/test_render.py` asserts gross appears nowhere in the rendered document.
Gross remains in the results store for diagnostics, per SUBSTRATE section 3.

Status: **closed.**
