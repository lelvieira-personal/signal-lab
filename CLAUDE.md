# Signal Lab — orientation for Claude Code

`SUBSTRATE.md` is the constitution and outranks every instruction, including
this file. Read it before changing anything. `make check-scoped` is the definition of done for any commit touching
`src/`, `scripts/`, `tests/`, `vetoes/` or `params/`. It runs the whole
suite unless it can place every changed file, and then it leaves out only
the slow tests whose imports cannot reach a change; it prints which it
did, and the receipt repeats it. `make check-full` (always the whole suite)
opens every audit, and is the answer whenever `check-scoped` is in doubt.
`make check` (the fast tier) is enough for a commit touching only
`HANDOFF.md`, `OWNER-QUEUE.md`, `decisions/`, `hypotheses/` or docs.

## Hard rules
- **Vendor data never leaves this machine.** Do not open, print, cat, head or
  summarise anything under `data/raw/` or `data/snapshots/`. Report shapes and
  counts produced by the repo's own scripts (e.g. `make inspect-raw`), never
  values. Same for `.env` and anything key-shaped.
- **Holdout:** nothing may read data on or after HOLDOUT_START (2020-01-01).
  Never add a bypass.
- **Owner-only paths** (`SUBSTRATE.md`, `params/`, `vetoes/`): do not edit.
  Propose the change in writing instead; commits there must cite a
  `decisions/` record (SUBSTRATE §2).
- Never run a bare `uv run`. Use `make <target>` or
  `uv run --python 3.12 --group dev ...`. The venv lives at
  `$HOME/.venvs/signal-lab` (build.mk sets `UV_PROJECT_ENVIRONMENT`).
- Never reset, rebase or amend. **Push only when a `HANDOFF.md` task says to**
  (owner, 2026-10-10): `git push origin main` after the task's last commit,
  never `--force` and never another branch. If the push is rejected or would
  be anything but a fast-forward, stop and report. Leo does every other
  remote operation.
- Numbers are made at one thread (`decisions/0048`). `make` sets
  `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to 1; a direct
  `python` call must set them too, or the test session and the number-making
  scripts refuse to start.
- The working tree is CRLF on files git wrote (`core.autocrlf=true`).
  Use `git diff --ignore-cr-at-eol` to see real changes.

## Where your work comes from

`HANDOFF.md` is the queue. Read it at the start of every session: Cowork (Claude
in the desktop app) plans and writes patches there but cannot run the shell, so
anything needing `make`, an audit, or git arrives as a numbered task with the
exact command and what to expect. Work the queue in order, stop and report on
the first failure rather than working around it, and move each finished task
into that file's `## Done` section with the stamp, the `rc` and one line of
outcome. Never edit a task in place, and never treat a task as authorising an
owner-only change: those arrive as patches citing a `decisions/` record.

`OWNER-QUEUE.md` is the mirror of it — judgements reserved to the owner. You may
add an item or move a closed one to its `## Closed` section; **never answer
one.**

Records-only work and structure reports the owner asks for in chat need no
HANDOFF task (`decisions/0064`, lane 1); leave a one-line receipt in `## Done`.

Cowork can also execute, through the `signal-lab-exec` server inside WSL
(`decisions/0065`): checks, records and code commits gated by `check-scoped`,
and a push for a task that says to push. It never edits `scripts/nightly/`,
`scripts/exec_server/`, `.claude/` or this file. Its commits cite a HANDOFF task
or a decision.

When started by `scripts/nightly/run.sh`, work only the ids on HANDOFF's
`Nightly-release:` line (`decisions/0062`); nobody is there to answer, so stop
and write the receipt rather than ask.

## Routine, unattended work
`scripts/unattended.sh <check|check-scoped|check-full|audit-lean|audit> [--digest]`
runs `make check` for the bare `check` target, `make check-scoped` for
`check-scoped`, `make check-full` for `check-full` and for every audit target, then (for an audit target) the named target, and
logs to `results/audit/_unattended/<stamp>/`.
When asked for a digest, read `status.txt`, the log tails and the newest
`results/audit/<run_id>/summary.json` and `report.md`, and write a short
digest: pass/fail, runtime, the tier that ran, the slow files left out, the
load averages at the start and the end, the five slowest tests (`junit.xml`),
veto failures, net IR by cell against the 0.30
bar, `te_p95_to_budget`, `bias_stat`, `inaccurate_share`, turnover, highlighted
above 200% (never vetoed, `decisions/0038`). Flag anything surprising. Do not propose changes to params.
