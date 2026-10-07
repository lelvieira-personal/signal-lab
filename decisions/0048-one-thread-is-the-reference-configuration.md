# 0048 — One thread is the lab's reference configuration

**Status:** decided 2026-10-07 by the owner (OWNER-QUEUE L26: "i accept all of
your suggestions for the pending decisions"; Cowork's suggestion was option
(a)). Drafted by Cowork. Applied by HANDOFF task 50. No change to
`SUBSTRATE.md`, `params/` or `vetoes/`.

## The measurement

HANDOFF task 49, step 2, on a 32-core machine (from its receipt; the two
timing runs left no log):

- **The slow tier took 1,319 s with the thread count unset and 37 s with one
  thread.** The numerical library ran about 30 threads on matrices of fewer
  than 100 instruments.
- **With one thread, four exact comparisons in `tests/test_baseline.py` fail,**
  on three recorded constants:

  | Constant | Recorded (threads unset) | One thread | Difference |
  |---|---|---|---|
  | `GOLDEN_NET_IR` (two tests) | −0.8793457503233992 | −0.8792060912640641 | 0.00014 |
  | `GOLDEN_NET_IR_CREATED_MARGINAL` | −0.3916592047250338 | −0.3916378876353463 | 0.00002 |
  | `GOLDEN_NET_IR_V080` | −0.40475664238417963 | −0.4046626602695416 | 0.00009 |

- The three recorded hashes in that file (`GOLDEN_SCORE_HASH`,
  `GOLDEN_TRUTH_BASELINE_HASH`, `GOLDEN_SCORE_SHUFFLE_HASH`) did not move.

## Why it needed a ruling

Every number the lab has recorded was produced at whatever thread count the
machine had. The same code on a machine with a different core count gives
slightly different numbers. A net IR that moves by 0.0001 changes no verdict:
the bar is 0.30 and one seed's sampling error is 0.26. But "this run
reproduces" and "bit for bit" are claims the lab makes, and they were true
only on one machine.

## The ruling

1. **One thread is the reference.** `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`
   and `MKL_NUM_THREADS` are 1 for every `make` target, every check and every
   audit.
2. **Every run records the thread setting it ran with,** next to its hashes.
3. **The three constants above are re-recorded once,** at one thread, and
   nothing else is. The conditions are in task 50: the new values must repeat
   exactly across two fresh runs and must equal the one-thread values in the
   table above.
4. **Numbers recorded before this decision stand as recorded.** They are not
   re-run. Where one is compared with a later number, the comparison says
   which side was made before 0048.

## What it does not decide

- **Parallel tests** (`pytest-xdist`). Not trialled. Not adopted.
- **Whether the ruler audit should be re-run.** It should be faster at one
  thread. *That is Cowork's guess and is not measured.*
- **Other sources of non-determinism** (the solver's own threads, if it has
  any). Task 50 reports what it finds.

## Addendum slot

Task 50's receipt gives old against new for the three constants as measured on
the day, and whether the estimator test's run of record
(`M-20261003T181155Z`) still reproduces at one thread. Cowork copies both here
when the receipt lands.

## Addendum, 2026-10-07: what task 50 measured

Copied by Cowork from task 50's receipt (`2995f34`) and checked against `git`,
the logs and the two `summary.json` files. The ruling was applied in `273182e`.
The review is the Project doc `claude/tasks-50-51-review-2026-10-07.md`.

**The three constants, old against new, as measured on the day.** The new
values equal the one-thread column of the table above, digit for digit.

| Constant | Recorded before (threads unset) | Re-recorded (one thread) |
|---|---|---|
| `GOLDEN_NET_IR` (two tests) | −0.8793457503233992 | −0.8792060912640641 |
| `GOLDEN_NET_IR_CREATED_MARGINAL` | −0.3916592047250338 | −0.3916378876353463 |
| `GOLDEN_NET_IR_V080` | −0.40475664238417963 | −0.4046626602695416 |

- **Exactly three constants changed.** Across `tests/`, the diff from
  `d5e7f95` to `fa63936` removes three lines, and they are these. No hash, no
  tolerance and no test mark moved. Each constant carries the old value and
  this decision in the comment above it.
- **The values repeat.** The receipt says two fresh processes gave them to the
  last digit; those two runs left no log. Two logged whole-suite runs made
  afterwards pass all 55 tests of `tests/test_baseline.py` on the new values:
  `20261007-084257-check-full` (784 passed) and `20261007-091756-check-scoped`
  (tier FULL, 795 passed).
- **The whole suite took 545 s at one thread,** against 3,908 s with threads
  unset (task 49).

**The estimator test's run of record reproduces at one thread.**
`M-20261007T125909Z` (one thread, `16a063b`) against `M-20261003T181155Z`
(threads unset):
- The two `loadings.parquet` files are the same file, byte for byte (sha256
  `216319a1…7401`).
- Of the 378 numeric fields the two `summary.json` files share, 374 are equal.
  The four that differ are timings (`runtime_seconds` and three under
  `projection`). No statistic, loss, adjusted p, bias check or verdict differs,
  and the three hashes are equal.
- The new summary adds two keys, `thread_setting` and `conjugate_update`.
- So the estimator test does not depend on the thread count. The baseline
  constants do.

**What the solver does.** The repo passes no thread option to the optimiser:
`problem.solve(solver=name)` and nothing else (`portfolio/long_only.py`).
Task 50 changed nothing there.

**One script that makes numbers is not gated.** `scripts/describe_loadings.py`
writes `fit.json` and `stability.json` and does not call `require_one_thread`.
`make` sets one thread for it; a direct `python` call would not be refused.
