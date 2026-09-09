# 0008 — A table the section 11 schema does not list

Status: proposed, 2026-09-07, agent. Blocking: no.

## Question

SUBSTRATE section 11 specifies three tables: `runs`, `metrics`, `verdicts`.
KICKOFF item 5 requires a mover between `hypotheses/pending`, `running` and
`done` that "records transitions in the results store". There is no table for
that in section 11.

## What was done

Added `hypothesis_transitions(id, ts, hypothesis_id, from_state, to_state,
run_id, detail)` to `src/results/schema.sql`, append-only, with the same
UPDATE/DELETE triggers as the other three.

## Why that way

The alternative was to record transitions as rows in `runs`, which would mean a
run row that is not a run. Polluting the leaderboard's own table to avoid
adding a table seemed the worse trade.

## What to decide

Whether section 11 should be amended to list this table, so the schema in the
constitution matches the schema on disk. Until it is, the divergence is
recorded here.

---
## Owner decision (2026-09-09, Leo)

Approved. SUBSTRATE section 11 is to be amended to list
`hypothesis_transitions` alongside `runs`, `metrics` and `verdicts`. Recorded
in `decisions/0100-substrate-amendments.md` for the owner to apply to the
constitution.

Status: **closed**, pending the SUBSTRATE edit.
