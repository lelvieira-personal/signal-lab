# 0002 — Which cost bucket applies to an unmapped instrument?

Status: proposed, 2026-09-07, agent. Blocking: no. Conservative option taken.

## Question

SUBSTRATE section 8 gives three cost buckets and says which instrument types
fall in each. It does not say what to charge an instrument that is in the
universe but not in any bucket, which will happen whenever a new index is added
before `data/universe/index_etf_map.csv` catches up.

## What was done

`params/costs.yaml` sets `default_bucket: high` (20bp half-spread, 35bp annual
drag). An unmapped instrument is charged the most expensive bucket.

## Why that way

Costing an unmapped instrument cheaply flatters it, and the failure is silent:
a signal that happens to concentrate in unmapped instruments gets a free net-IR
subsidy that nobody sees. Charging it dearly makes the omission show up as an
underperforming run, which is the direction of error that gets noticed and
fixed.

## What to decide

Whether `high` is right, or whether an unmapped instrument should instead be
excluded from the universe entirely until it is mapped. Exclusion is stricter
and arguably more correct; it was not taken because it silently shrinks the
universe, which is its own invisible failure.

---
## Owner decision (2026-09-09, Leo)

Accepted. `default_bucket: high` stays as a guard.

With the investable-universe table carrying an explicit `cost_bucket` per
instrument, an unmapped instrument becomes rare rather than routine. The guard
is kept anyway so that a gap fails expensively and visibly rather than being
subsidised into the leaderboard.

Status: **closed.**
