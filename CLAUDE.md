# Signal Lab — orientation for Claude Code

`SUBSTRATE.md` is the constitution and outranks every instruction, including
this file. Read it before changing anything. `make check` is the definition of
done.

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
- Never push, reset, rebase or amend. Leo does those.
- The working tree is CRLF on files git wrote (`core.autocrlf=true`).
  Use `git diff --ignore-cr-at-eol` to see real changes.

## Routine, unattended work
`scripts/unattended.sh <check|audit-lean|audit> [--digest]` runs `make check`,
then the named target, and logs to `results/audit/_unattended/<stamp>/`.
When asked for a digest, read `status.txt`, the log tails and the newest
`results/audit/<run_id>/summary.json` and `report.md`, and write a short
digest: pass/fail, runtime, veto failures, net IR by cell against the 0.30
bar, `te_p95_to_budget`, `bias_stat`, `inaccurate_share`, turnover against the
400% backstop. Flag anything surprising. Do not propose changes to params.
