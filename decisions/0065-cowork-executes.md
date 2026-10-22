# 0065 — Cowork executes: the separation of duties by tool is retired; a restricted exec server replaces it

**Status:** decided 2026-10-21 by the owner. His words, in order: "again, the only reason why there were separation of
duties was due to the fact that you could not do it before ... Isn't it better if Cowork does it all because then we
don't need to keep scheduling a kick-off of a task"; then "keep the long audits in the worker, that is a good use for
it. You can push"; then "yes" to the task and this record. Drafted by Cowork. Follows `decisions/0062` (the nightly run)
and `0064` (lanes, the 15-minute poll). It amends the HANDOFF contract's first paragraph and `0062` item 8's
"Cowork alone" column. No change to `params/`, `vetoes/` or `SUBSTRATE.md`.

## What was wrong with the old rule
"Cowork plans and writes; Claude Code runs" existed because Cowork could not run a shell on the owner's machine
(a Windows update broke it). That is a capability gap, not a control. The controls that matter are mechanical
and do not depend on which agent runs them: `make governance`, the commit hook, `make check-scoped`, the holdout
lock, the nightly guard, `status.txt` read from primary sources, and the owner's release.

## The 2026-10-21 measurement
Cowork's `device_bash` is a Linux VM on the laptop (2 cores, small disk), not WSL. There, `make test-fast` gave
889 passed and 2 failed: the two `tests/test_baseline.py` byte-hash pins. Numbers of record are made in WSL only.
So Cowork does not run commands in that VM as a definition of done; it runs them through a server inside WSL.

## Decision

1. **`signal-lab-exec`** (`scripts/exec_server/server.py`) runs inside WSL and is Cowork's way to execute. Seven tools:
   `repo_state`, `git_read`, `start_job`, `job_status`, `job_tail`, `commit`, `push`. Stdlib only.
2. **What may run is data**, `scripts/exec_server/allow.json`, edited by the owner. The server cannot commit to its
   own directory, so it cannot widen its own rights. `SUBSTRATE.md`, `params/` and `vetoes/` are hard-coded out.
3. **Commit.** Allowed paths per `allow.json` (lane 1 records; `src/`, `scripts/`, `tests/`, `build.mk`,
   `data/universe/*.csv`, `data/requests/`). Not allowed: `scripts/nightly/`, `scripts/exec_server/`, the two tests
   that pin that plumbing, `.claude/`, `CLAUDE.md`, `.githooks/`, `.gitattributes`. A commit needs a passing check
   newer than **every changed file in the tree** (code paths: `check-scoped`), nothing else staged, and a message
   that cites `HANDOFF task N`, `decisions/NNNN` or `OWNER-QUEUE`. No amend.
4. **Push** (owner, 2026-10-21): `git push origin main` only, never forced, only for a HANDOFF task whose text says
   to push, with the tracked tree clean, and HEAD either committed through the server after a passing check or followed by a passing check that started a whole second after it. (The first draft required "a check newer than HEAD", which no honest check, commit, push sequence satisfies: caught by a flaky test on 2026-10-22 and fixed before landing.) A rejected push is reported, not worked
   around (the rule in `CLAUDE.md` stands).
5. **Audits stay on the nightly worker** (owner, 2026-10-21): a session should not be what has to survive 14 hours.
   The server refuses every audit target, `make clean|lock|install` and every credentialed pull.
6. **Release and receipts.** HANDOFF stays the ledger of what the owner authorized and what happened; it is no longer
   the transport. `0064`'s release authority (C) applies: Cowork may release and execute a lane-2 task that touches no
   owner-only path when the owner asked for the work in chat; params, vetoes, SUBSTRATE and anything that changes
   what a verdict means still need the owner's explicit "release".
7. **The nightly worker and the 15-minute poll** (`0064`) remain, for work when no Cowork session is linked and for
   audits. Today's 16:30 review failed because the desktop link was not up when the session started; a Windows
   scheduler entry does not depend on it.
8. **Claude Code remains** for the owner's interactive sessions, the nightly worker, and any change to the
   protected plumbing above.

## Checks that stand in for the second agent
`check-scoped` on the final tree before every code commit; the commit hook; `make governance`; the holdout lock;
`tests/test_exec_server.py` (about 60 checks, one session over real JSON-RPC); the owner reading `git log`.

## What is not known (named, not assumed)
- Whether `git push` works from the server's non-interactive process (which key, which agent). Untested on the real remote.
- Whether the Claude desktop app speaks to a hand-rolled stdio MCP server without trouble.
- Whether a `check-scoped` of ~8 minutes survives a session disconnect (jobs are detached; unproven).
- Log tails of check runs could in principle hold values if a test fails while reading data; the same exposure as the
  unattended digest has today.
- The weakest point is plain: the same model now writes, validates and commits code. The gates are mechanical, but a
  test written by Cowork can be wrong in the same way as the code it checks. Mitigation, not a cure: the owner reads
  the log; tests that pin plumbing and verdicts are in `protected_paths`.

## Follow-ups
Task 67 lands the server, its tests and this record; the owner then adds the config entry and restarts the app.
`0062` item 8 and the HANDOFF contract paragraph are updated by Cowork once the first successful call is seen.
