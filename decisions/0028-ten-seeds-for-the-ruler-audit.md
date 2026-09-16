# 0028 — Ten seeds per audit cell

Status: decided, 2026-09-16, Leo ("let's go with 10 seeds"). Touches
`params/audit.yaml` (`seeds: 3` → `seeds: 10`). Amends `decisions/0023` §B.

## Why

The seed chooses the random noise blended into a planted signal. Cells that
differ only in the seed still give different net IRs, and that spread is luck,
not information.

Measured on the synthetic panel with 10 seeds per frictionless cell (horizons 4
to 52 weeks, IC 0.05 and 0.10), the standard deviation of IR across seeds is
**0.24 to 0.31**, about 0.26 typically. At h26 and IC 0.05, single seeds ranged
from −0.28 to +0.49 around a mean of 0.20. The first lean audit's one-seed h26
frictionless cells (−0.05 and 0.11) were such draws.

The error on a cell's mean IR is that spread divided by √seeds:

| seeds | error on mean IR | required IC at h26 (IR per unit IC ≈ 3.7) |
|---|---|---|
| 3 | ±0.15 | ±0.04, as wide as the grid step |
| 10 | ±0.08 | ±0.02 |

The audit exists to set the bar at net IR 0.30 and to choose the per-session
turnover cap. At ±0.15 it cannot tell 0.30 from 0.45.

## Cost

On Leo's machine a base cell takes about 59 s and a frictionless cell about
1 s. The full grid grows from 148 + 48 frictionless cells to 484 + 160: about
**8 h** instead of about 2.5 h. The IC = 1 oracle stays at one seed per horizon.

## What this does not change

The seed-stability veto (`vetoes.seed_stability.max_ir_range: 0.15`) judges
hypotheses in phase 3, not audit cells, and is untouched. For the record,
though: a *planted* signal's seed range over 3 seeds would typically be about
1.7 × 0.26 ≈ 0.44. Whether real signals face a comparable spread across their
own nuisance choices is a question for phase 3.
