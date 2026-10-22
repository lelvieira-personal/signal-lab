# 0064 -- Three lanes, and a faster trigger

**Status:** decided 2026-10-21 by the owner ("it is acceptable as written and 15min poll is fine"). Drafted by Cowork at the owner's request. Amends `decisions/0062`
(the nightly run) and the HANDOFF contract. Owner-only: `0062` is a decided record.

## Evidence (2026-10-21, measured, not assumed)

1. Cowork's `device_bash` is a Linux VM on the laptop (2 cores, 3.9 GB, ~9 GB session disk), not WSL.
   It has make/uv/git; the locked environment built in ~100 s.
2. `make test-fast` there: **889 passed, 2 failed** in 62 s. The two are
   `tests/test_baseline.py::test_the_truth_shuffle_and_its_stream_are_unchanged_by_the_score_shuffle`
   and `::test_the_score_mode_is_bit_for_bit_unchanged_by_score_span`: both compare the first 16 hex of a
   SHA-256 of the raw bytes of a planted-signal score array to a pinned value. The RNG golden passes;
   the score array differs. Same locked versions, so the cause is the machine (cause not isolated;
   a CPU-dispatch difference in numpy/OpenBLAS is the guess). Conclusion: **numbers of record are made in WSL only.**
3. Task 63 took ~7 h (written 08:20, run 12:30, re-released 15:20, done 15:30) for ~1 h of work; the wait
   was the two nightly slots and the owner's release, not the work.
4. A device-shell `git commit` would need delete permission (`.git/*.lock`); not tested. Pushes need `git_key` (WSL).

## Proposal

**A. Lanes.**
1. *Direct* (Cowork or Claude Code interactive, no HANDOFF task, one-line receipt in `## Done`):
   records-only commits (`decisions/`, `hypotheses/`, docs, `HANDOFF.md`, `OWNER-QUEUE.md`), structure
   reports of `data/raw/` files, read-only reviews. Cowork may run non-number-making commands in its
   own shell (lint, governance, most tests) as a pre-check, never as the definition of done.
2. *Task* (as today): `src/`, `scripts/`, `tests/`, `params/`, `vetoes/`, any push, anything that makes a number.
3. *Nightly/long*: audits and anything over an hour.

**B. Trigger.** Run the wrapper's gate every 15 minutes, all day, through a new `poll` slot that has no clock window (the `day` and `night` windows stay as they are; `night` at 23:00 remains the only slot for `long` releases). A poll run that is not `long` gets a 5-hour wall (`POLL_WALL`); anything longer needs `long`, as before. The gate already
exits without a model call when nothing is released, so an idle poll costs nothing (`0062` item 3). The
existing caps, lock, `long` rule and power check stay. The gate's change is `poll-slot.patch` (3 files, 51 nightly tests pass on a scratch copy, 5 of them new or extended). Residual risks, named: a poll can start while the owner works in the tree (the lock covers `unattended.sh` runs, not an interactive session; the gate's `.git/index.lock` check is best-effort), and a `wsl.exe` launch every 15 minutes may flash a console window and keep WSL awake (a guess, not tested). Cowork's re-release by=cowork (item 8) then starts
within minutes. *Owner/WSL action: a scheduler entry change; Cowork cannot make it.*

**C. Release authority.** Standing release for lane 1 and lane 2 tasks that touch no owner-only path and have
`push=no`, by=cowork, when the owner has asked for the work in chat. Pushes, params, vetoes, SUBSTRATE and
any task that changes what a verdict means stay with the owner's explicit "release".

## What this does not fix
Claude Code in WSL stays the only place numbers are made. If the 2 hash tests are ever wanted green on the
VM, the pinned values would be per-machine, which defeats their purpose.

## Owner's answers (2026-10-21)
- 15-minute poll: acceptable.
- C (release authority): acceptable as written.
