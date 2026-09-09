# 0011 — What a cycle records when there is no engine

Status: proposed, 2026-09-07, agent. Blocking: no.

## Question

KICKOFF item 8 asks for `scripts/nightly_cycle.py` as a stub: "load → for each
pending hypothesis: validate → run → vetoes → record; budgets enforced; no
signal logic yet". With no engine, "run" cannot produce a RunContext, and the
vetoes fail closed on a context full of `None`. A cycle that ran the vetoes
anyway would record ten "cannot evaluate" failures per hypothesis and the
leaderboard would show runs that were killed by `lookahead` when the real cause
is that phase 1 has not happened.

## What was done

`run_experiment()` exists and raises `EngineNotImplemented`. The cycle catches
it and records the run with `status='blocked:no_engine'`,
`killed_by='engine_missing'`, no metrics and no verdicts. The veto call is
wired and will execute unchanged the moment `run_experiment` returns a context.

## Why that way

Recording a veto failure that was really a missing engine would put a false
cause of death in an append-only store, and the store cannot be corrected. A
status naming the actual reason is honest and costs nothing.

## What to decide

Nothing, unless you would rather the cycle recorded no row at all for a
hypothesis it could not run. The current behaviour makes the blockage visible
on the digest, which seemed more useful than silence.

---
## Owner decision (2026-09-09, Leo)

Accepted as implemented. A cycle with no engine records
`status='blocked:no_engine'` and no verdicts, rather than recording eleven
"cannot evaluate" veto failures against a run that was never measured.

Status: **closed.**
