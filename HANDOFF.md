# HANDOFF — work queued for Claude Code

`SUBSTRATE.md` outranks this file, and so does `CLAUDE.md`. Nothing here
authorises an owner-only change: every task that touches `SUBSTRATE.md`,
`params/` or `vetoes/` arrives as a patch that cites a `decisions/` record,
and if it does not, refuse it and say so.

## The contract

**Cowork plans and writes; Claude Code runs.** Cowork (Claude in the desktop
app) can read this repo and edit files in it, but it cannot run `make check`,
cannot run an audit, and must never run a git command that writes the index —
its sandbox cannot delete `.git/index.lock`, which would block git in WSL. So
anything needing the shell lands here as a task, in order, with the exact
command and what to expect.

**Claude Code appends a receipt, and never edits a task in place.** When a task
is finished, move its heading into `## Done` at the bottom with the stamp, the
command's `rc`, and one line of outcome. Leave the task text intact so the next
Cowork session can see what was asked as well as what happened.

**Receipts are a courtesy, not the record.** Cowork verifies from primary
sources — `git log`, `results/audit/_unattended/<stamp>/status.txt`, the run
directories — because a digest can be accurate and still omit the thing that
matters. On 2026-09-18 a `check` run was reported PASS while a second, launched
34 s later, was killed mid-suite; only `status.txt` showed it.

**Findings do not go here.** This file is a queue of actions. Measurements
belong in `results/`, decisions in `decisions/`, and narrative in the Cowork
project docs. If a task produces a number worth keeping, say so in the receipt
and leave the number where the run wrote it.

**One at a time.** Do not launch a second `scripts/unattended.sh` while one is
running; they compete and the loser dies with `Error 143`.

---

## Queue

Tasks **0-11 are complete**; receipts are in `## Done` and the text as issued is
in git history. The queue below starts at 12.

**Read first:** `decisions/0036` (decided 2026-09-20) and the Cowork project doc
`claude/dose-response-step1-2026-09-20.md`. `decisions/proposed/0035` and
`claude/dose-response-probe-plan.md` are still live context; the probe plan's
steps 2 and 3 have been superseded by 0036 and by the withdrawal notice below.

**Run order: 12, 15, 16, 17, 18, 19, 20.** 21 is hygiene, any time. Tasks 13 and 14 are withdrawn — read
the notice, do not run them. 18 is gated on 17's `make check`, 19 on 18, and 20
on what 18 finds; each says so. One `scripts/unattended.sh` at a time.

### 12. Commit the Cowork write-up from 2026-09-20

`decisions/proposed/0035` is the only new repo file; the probe plan and the
rewritten state of play are Cowork project docs and are not in the repo.

    git add decisions/proposed/0035-the-transfer-coefficient-measures-the-benchmark-not-the-tilt.md HANDOFF.md
    git commit -m "decisions: 0035 proposed -- the transfer coefficient measures the benchmark

A-20260919-155557 read a median transfer coefficient of 0.018 against a
published range of 0.3-0.8. transfer_n_dates is healthy at 782-830 of 834
rebalances, so the alpha reaches the estimator and the conditioning is not
dropping dates: the number is what was computed.

It is not what 0033 intended. The oracle cells at IC = 1 -- a perfect forecast
-- read 0.039 to 0.042, and a constructed book holding no view at all reads
-0.017. The estimator cannot distinguish a book with a view from one without.

The benchmark legs are not holdable, so the book replicates the benchmark out
of the holdable universe and tilts away from it. active_covariance is right and
w' Omega w really is the active variance, but the numerator a'w and the
diagonal correlation take the whole fully-invested book, which is dominated by
replication and uncorrelated with alpha by construction.

0035 proposes computing all three estimators on w - w_baseline, and persisting
weights and alpha per run: results/artifacts/ is empty, which is why correcting
a column costs 13.3 hours instead of minutes."

**Receipt should say:** the commit hash.

### 13 and 14 — WITHDRAWN 2026-09-20. Do not run them.

Superseded by `decisions/0036` (decided 2026-09-20) and by the Cowork project doc
`claude/dose-response-step1-2026-09-20.md`. The task text below is left intact
as issued; nothing in it is authorised.

**Why 13 is withdrawn.** It cannot test the hypothesis it was written for.
`audit/signals.py` gives `alpha = ic * sigma * score / sqrt(h)`, so at `ic = 0`
the alpha is identically zero — the task is right about that. But
`portfolio/long_only.py` then resolves a zero alpha to the **minimum-tracking-
error book**, and says so in its own comment, naming "the IC = 0 rung of the
ruler audit". The live book runs 4.4-5.6% ex-ante TE; that one runs the least it
can. It is not the same book, so it is not a control for it.

**And the control was already in the grid.** At IC 0.02 the score is
`0.02*truth + 0.9998*noise` — the truth is 0.04% of its variance. That rung
reads **net IR 0.311** (SE 0.075 clustered on seed) while running 4.55% ex-ante
TE. Explaining it from its own 0.016 of realised IC would need a slope of 19.4
IR per unit IC, against every slope the lab has measured (0.13 to 1.03). The
no-information floor is measured, and `decisions/0023`'s bar is 0.30.

**Why 14 is withdrawn as queued, not cancelled.** Its purpose stands and it is
still the test for noise dominance, but it is now gated on the baseline grid
rather than on 13, and its power needs stating before two hours are spent: at
ten seeds the h13 MDE is **0.166 IR**, so it discriminates a steeply convex
response from a linear one and will not resolve anything shallower. It is
re-queued under "Not queued yet" below.

### 13. The IC = 0 control — the missing cell

`claude/dose-response-probe-plan.md` step 2, and the cheapest decisive
experiment available. The grid's rungs start at IC 0.02, and 0.02 is already
statistically indistinguishable from 0.20. **There is no zero-information
control**, so nothing in either Bloomberg audit establishes that the ladder
responds to signal at all.

Run ten seeds at four horizons with a pure-noise signal. About 40 cells at
roughly 100 s, so about **70 minutes** — not an overnight job.

How to express IC = 0 is yours to judge from the code; `plant()` with an IC of
zero should give an alpha that is identically zero, which is the no-view book.
If that path is not reachable without a code change, **stop and report** rather
than approximating it with a very small IC: a 0.001 rung answers a different
question.

**Expect `transfer_n_dates = 0` and a NaN transfer coefficient on every one of
these cells.** Alpha is identically zero, so there is no view to transfer. That
is the estimator behaving correctly, not a failure, and it is not a reason to
stop.

**Receipt should say:** rc, runtime, the run id, and the net IR by horizon with
its seed range. Nothing else — the interpretation is Cowork's and the owner's,
and the hypotheses it discriminates are in the probe plan.

### 14. Intermediate IC rungs — only if 13 shows no floor

Step 3 of the probe plan. Rungs at **0.35, 0.50 and 0.70**, ten seeds, **h13
only**. About two hours. Do not start it if task 13 showed a floor; in that case
the question has changed and Cowork will requeue.

**Receipt should say:** rc, runtime, run id, net IR by rung with seed ranges.

### 15. Commit 0036 and this queue rewrite

`decisions/0036` is new and **decided by the owner 2026-09-20** — it was never
committed while in `proposed/`, so it lands straight at its decided path.
`HANDOFF.md` and `OWNER-QUEUE.md` are modified.

**Run task 12 first.** Both tasks `git add HANDOFF.md`; whichever runs first
commits it and the other finds nothing to add for that path, which is expected
and not a failure. Note also that task 12's message says 0035 is "the only new
repo file" — true of untracked files when it was written, and 0036 has since
joined it. 12's add list is still correct; do not edit it.

    git add decisions/0036-the-bar-is-excess-over-a-no-information-baseline.md HANDOFF.md OWNER-QUEUE.md
    git commit -m "decisions: 0036 -- the bar is excess over a no-information baseline

decisions/0023 set the bar at net IR 0.30. On the development window a book
holding no usable information reads 0.311.

The control was already in A-20260919-155557 and had not been read as one. At
the IC 0.02 rung the planted score is 0.02*truth + 0.9998*noise, so the truth is
0.04% of its variance. That rung runs 4.55% ex-ante TE and earns 0.3106 net IR,
SE 0.075 clustered on seed. Explaining it from its own 0.016 of realised IC
needs a slope of 19.4 IR per unit IC; the frictionless twin measures 0.13 to
0.39 and the oracle-anchored linear slope is 1.03.

Every required_ic and surviving-cell count in both Bloomberg audits is therefore
read against a bar the floor already clears.

0036 reports net_ir_excess against a seed-matched, magnitude-matched
baseline with the information destroyed by a block shuffle -- the one
construction that also generalises to a real hypothesis, and the machinery
SUBSTRATE section 9 already requires for the search null and Romano-Wolf, which
src/signal_lab/stats/ does not have.

DECIDED by the owner 2026-09-20: sections 3, 4a and 6 taken. The metric is
excess over a block-shuffled baseline; section 4b pins the implementation.
Section 6 takes position 2 -- the bar is RE-DERIVED rather than carried across at
0.30 or split in two -- but the number itself is not set: params/audit.yaml
target_net_ir stays 0.30 and decisions/0023 is untouched until a derivation
exists. What that derivation takes as its input, and the fact that decisions/0025
derives the TE budget FROM the bar, are OWNER-QUEUE L9."

**Receipt should say:** the commit hash.

### 16. Six `data/requests/*.yaml` are modified and nothing commits them

`H-2026-0004`, `0006`, `0007`, `0009`, `0010`, `0011` carry real uncommitted
changes (confirmed with `git diff --ignore-cr-at-eol`; the rest of the tree's
`M` flags are CRLF phantoms). Task 12's `git add` list does not include them and
its message says 0035 is "the only new repo file" — true of untracked files,
not of modified ones.

They look like the ticker-resolution corrections of `decisions/0032` applied to
the request files — e.g. `H-2026-0009` moves `MXUS -> SPXT`, `MXEU -> MXEUG`,
`MXJP -> NDDUJN`, `MXEF -> M1EF` and drops `MXWO` and `LEGATRUU`. **Verify that
before committing**, because I have not established what produced them:

1. Check whether a target regenerates them (`make requests`, or whatever
   `scripts/` writes `data/requests/`), and if so, run it in a clean worktree
   and diff against the working tree.
2. If they match a regeneration, commit citing `decisions/0032`.
3. **If they do not match, stop and report.** Hand-edited pre-registration
   artefacts are exactly what `decisions/proposed/0034` exists about.

**Receipt should say:** rc, whether a regeneration reproduced them, and the
commit hash or the reason for stopping.

### 17. Implement the block-shuffled baseline — `decisions/0036` §4(a) and §4b

**Implement from the record, not from this task.** `0036` §4b pins five things
that the code makes non-obvious; read it before writing anything. In summary:
shuffle whole date-rows in contiguous 52-row blocks with one permutation shared
across instruments, before standardisation; **re-apply the original NaN mask**
afterwards or you breach the `frequency` veto on a ragged panel; draw the
permutation from a **stream independent of the noise RNG** or the seed-matching
the baseline exists for is destroyed; **encode the baseline in `AuditCell.key()`**
or it collides with its live twin in an append-only store; and build the grid
selector in `ladder.py` / `scripts/run_audit.py` / `build.mk` /
`scripts/unattended.sh`, **not** in `params/audit.yaml`, which is owner-only and
not authorised by this record.

Put the shuffle itself in **`src/signal_lab/stats/`**, not in `audit/`. It is
SUBSTRATE §9's block-bootstrap machinery — the same primitive the search null and
the Romano-Wolf stepdown need, and that package is currently one line.

`0036` §5's five acceptance tests are **tests**, not a one-off check. The fourth
one matters most for what follows: the shuffle switched off must reproduce
today's `net_ir` **bit for bit**, because tasks 18 and 19 pair new baseline cells
against the *existing* `A-20260919-155557` live cells rather than re-running
them.

Interface to build, so tasks 18 and 19 have a command:

    make audit-baseline-pilot   ->  run_audit.py --source bloomberg --grid baseline-pilot
    make audit-baseline         ->  run_audit.py --source bloomberg --grid baseline
    scripts/unattended.sh audit-baseline-pilot | audit-baseline   (extend the whitelist)

`baseline-pilot` is h13 only, the four `audit.ic_grid` rungs, all ten seeds — 40
cells. `baseline` is all four horizons — 160 cells. Both read the grid values
from `params/audit.yaml`; neither adds a key to it.

Then:

    scripts/unattended.sh check --digest

**Receipt should say:** rc, test count, runtime, the commit hash, and
explicitly whether the bit-for-bit reproduction test passes. **Stop and report
if it does not** — everything downstream depends on it.

### 18. The baseline pilot — 40 cells, about 50 minutes

Only after 17 is committed and `make check` is rc=0.

    scripts/unattended.sh audit-baseline-pilot --digest

**What it answers.** The live book runs 4.42% active vol at IC 0.02 and 5.58% at
IC 0.20. The question is whether the no-information floor grows with the risk the
book takes. **If the baseline at the IC 0.20 rung also reads about 0.31, every
rung on the ladder is floor** and task 20 is pointless — this run can cancel the
next one.

**Before taking any contrast, check that the new run's `panel_hash` and
`params_hash` in `summary.json` match `A-20260919-155557`'s**
(`dfbf5c5a68a399d90babe84b757f7f849c4f75fbe6babff5b2db646b66575793` and
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c`). If either
differs, the pairing is across panels and the contrast is not valid — **stop and
report** rather than reporting the number.

**Receipt should say:** rc, runtime, the run id, whether both hashes match, and
the baseline `net_ir` by IC rung with its seed range. Nothing else — the
interpretation is Cowork's and the owner's.

### 19. The full baseline grid — 160 cells, about 3.3 hours

Only if 18 is clean and the hashes matched. Do not start it if 18 stopped.

    scripts/unattended.sh audit-baseline --digest

**Receipt should say:** rc, runtime, run id, baseline `net_ir` by IC rung and
horizon with seed ranges.

### 20. Intermediate IC rungs — the old task 14, re-queued

Rungs at **0.35, 0.50 and 0.70**, ten seeds, **h13 only**, about two hours.
Gated on task 18, not on the withdrawn task 13: **do not start it if the pilot
showed the floor at the IC 0.20 scale is the same as at IC 0.02.** In that case
the ladder has never measured signal and Cowork will requeue.

Know its power before spending the two hours: at ten seeds the h13 MDE is
**0.166 IR**. It discriminates a steeply convex response from a linear one and
will not resolve anything shallower.

**Receipt should say:** rc, runtime, run id, net IR by rung with seed ranges.

### 21. Remove the parked lock file Cowork left in `.git`

Not blocking and not urgent — order does not matter. On 2026-09-20 a Cowork
`git status` refreshed the index and created `.git/index.lock`, which the Cowork
mount cannot delete (`Operation not permitted`). It was renamed out of the way
rather than left in place:

    rm -f .git/index.lock.stale-cowork-20260920

Git ignores the parked name, so nothing is currently blocked; this is hygiene.
Do not remove `.git/index.lock` itself if one exists without first checking that
no git process is running — the 2026-09-18 receipt in `## Done` records a stale
lock that vanished on its own.

**Receipt should say:** rc, and whether the file was there.

---

## Not queued yet, and what each is waiting on

What is left here is waiting on the owner, not on a patch.

**The baseline work is now queued** as tasks 17-20 above; `decisions/0036` §4(a)
and §4b are decided and carry the spec.

**The corrected transfer coefficient (`decisions/proposed/0035` §4).** Not
decided, and deliberately not queued: it costs a 13.3 h re-run and the probe
plan may want a different grid anyway. Sequence it after task 13.

**Persisting weights and alpha (`0035` §5).** Not decided. It is what would make
the next measurement bug a re-derivation instead of a re-run.

**The validator (0034).** Not decided by the owner. Do not build it.

### One scheduling point, because the audit costs 14 hours

`A-20260918-201042` took **50,572 s**. The `L` statistic and the
`transfer_coefficient` column are both new per-cell measurements, so each needs
an audit run to populate it. **Land them in one series and rerun the audit
once.** Three separate reruns is 42 hours of machine time to learn what one
run would have said.

### Standing refusals

- **Turning the volatility overlay on.** It is opt-in code with no parameter
  reading it, tested at one horizon, two IC rungs and one halflife. Switching
  it on is an owner decision that does not exist yet.
- **`decisions/0029` §2 only.** §1, §3, §4 and §5 were decided 2026-09-19 and
  are in task 9. **§2 -- conditioning the frictionless covariance -- stays
  deferred**; do not add a ridge or eigenvalue floor on your own initiative.
- **`decisions/proposed/0034`.** Proposed, not decided. Do not build it.
- **Anything in `params/`, `vetoes/` or `SUBSTRATE.md` not arriving as a cited
  patch.** Refuse and say so.

---

## Done

### 2026-09-18 — the landing commits and the first check (Claude Code, Sonnet 5)

- `e1b7687` scripts: build_coverage and inspect_raw
- `6ebed2f` audit: the TE path probe
- `a6efef0` portfolio: an opt-in volatility overlay, off by default
- `c0853d6` decisions: 0030 **proposed**, with `scripts/bias_map.py`
- `scripts/unattended.sh check --digest` at `1b6babf` with the above in the
  tree: **rc=0, 438 tests, 417 s**
  (`results/audit/_unattended/20260918-082014-check/`).
- A second `check` launched 34 s later (`20260918-082048-check`) was killed
  mid-suite, `Error 143`. Duplicate launch, not a failure.

### 2026-09-18 — tasks 0, 1 and 2 (Claude Code, Sonnet 5)

**0. Commit the coordination files** — rc=0.
- `033897e` tooling: HANDOFF.md and OWNER-QUEUE.md. Committed outside this
  session, by `lelvieira`, while a stale `.git/index.lock` (0 bytes, no git
  process running) blocked my own commit; the lock was gone when I went to
  remove it, so nothing was deleted.
- `7acd0a8` tooling: the `CLAUDE.md` pointer, committed by me afterwards.

**1. Apply the 0030 patch series** — `git am` rc=0, six patches, no conflicts.
- `4c9a9f7` 0001 decisions: 0030 decided
- `3a8b8c7` 0002 harness: the ex-ante TE reaches the veto set
- `a26e4f8` 0003 vetoes: risk_calibration replaces tracking_error
- `0d581ef` 0004 substrate: sections 4 and 10
- `208e6a6` 0005 audit: the worst annual bias
- `a913f69` 0006 audit: a risk-characteristics section

**2. Verify** — `scripts/unattended.sh check --digest` at `a913f69`:
**rc=0, 446 tests, 365 s** (`results/audit/_unattended/20260918-154931-check/`).
Governance: `OK, no uncited owner-only change since 85694662`; commit hook
installed (`core.hooksPath=.githooks`). Ruff clean.
Tasks 3 and 4 not started.

### 2026-09-19 — tasks 3 and 4 (Claude Code, Sonnet 5)

**3. One timed cell** — both rc=0.
- `TE-timing-default` (`0.05:13:9`): **3m07s** wall, cell 141 s.
- `TE-timing-1thread` (`0.05:13:8`): **2m16s** wall, cell 125 s (user 21 s vs
  real 136 s). Different seeds, as specified; no default changed.
- WSL is not at sandbox speed (16-21 s). Roughly 130 s a cell puts a serial
  484-cell audit near 17 h, so the "2 h" case is ruled out.

**4. Ten seeds, then the Bloomberg audit** — rc=0.
- `06bcea3` params: ten seeds per audit cell (decisions/0028), `git am` rc=0.
- `scripts/unattended.sh audit --digest` at `06bcea3`: check rc=0 (427 s),
  audit rc=0 (**50572 s, ~14 h**), run `A-20260918-201042`, 644 cells (484
  judged, 160 frictionless not judged), 10 seeds
  (`results/audit/_unattended/20260918-160333-audit/`).
- 100 of 484 judged cells fail a portfolio veto, **all 100 on
  `risk_calibration`** (base cells: 37 of 160). `bias_worst_annual` above the
  1.72 ceiling in exactly those 100; judged median 1.59, max 2.32.
  `bias_worst_year` is 2008 in 420 of 484 judged cells.
- Max per-cell turnover 349%, under the 400% backstop. Max `inaccurate_share`
  0.24%.
- No `report.md` in the run dir; the digest read `summary.json` and the log.


### 2026-09-19 — tasks 5 and 6, and a stop at 7 (Claude Code, Sonnet 5)

**5. Commit the decision records and the resolution map** — rc=0.
- `6db3404` decisions: 0031-0034 and the ticker resolution map.

**6. Promote the three decided records** — rc=0.
- `c8b2070` decisions: 0031, 0032 and 0033 decided. **0034 is still in
  `decisions/proposed/`.**

**7. Rebuild the coverage tables — STOPPED, not committed.** `make coverage`
and `make universe` both rc=0. The task says to stop if a tier moves; four did:
- `M1EAMVOL` and `M1EFMVOL` (both investable): `second` -> `backbone`.
- `H09122US` and `H12823US` (both `investable: false`, hedged): `tradable-only`
  -> `second`.
- Not moved: the investable set (95 before and after, same 102 tickers), and
  every cost bucket.
- Also beyond the task's expectation: 65 `first_daily` dates changed (median
  -63 days, range -275 to +29) and `bbg_index_coverage.csv` gained
  `sparse_era_obs` and `frequency_flag` as well as losing `likely_price_only`.
- The rebuilt `bbg_index_coverage.csv` and `investable_universe.csv` are in the
  working tree, uncommitted. Tasks 8-10 not started, per the stop rule.

### 2026-09-19 — task 7a, and a stop on the check (Claude Code, Sonnet 5)

**7a. Task 7 re-issued** — commit done, **verification FAILED**.
- `d0ee0b6` data: rebuild the coverage table from the Index Map. Verified
  before committing against `decisions/0022`: the four tier moves, census
  **77/12/8**, investable set **95**, and no cost bucket moved.
- `scripts/unattended.sh check --digest` at `d0ee0b6`: **rc=2, 238 s, 445
  passed, 1 failed** (`results/audit/_unattended/20260919-102337-check/`).
  Governance OK; ruff clean.
- Failure: `tests/test_audit.py::test_an_early_over_trade_does_not_block_a_later_one`
  — `0.374 > 0.5 * 0.954` is false. Deterministic (fails alone, 21 s).
- **Cause, established by running the same test in a worktree at `c8b2070`
  (passes):** `loaders/synthetic.py` draws the synthetic panel's ragged starts
  from `bbg_index_coverage.csv`, so the rebuild changed the synthetic panel
  the test runs on. The real panel is untouched. The test's baseline is one
  session at 0.954 (2017-01-20), i.e. the start-up entry its own docstring says
  it excludes, but which now sits at index 1..half instead of index 0.
- Not fixed, per the stop rule: no test edited, nothing worked around. Tasks
  8-11 not started. Needs Cowork/owner: whether the test's start-up exclusion
  should be made robust to the panel, and whether any synthetic-panel result
  (planted-IC ladder) is affected by the changed starts.

### 2026-09-19 — tasks 7a, 7b, 8, 9 and 11 (Claude Code, Sonnet 5)

**7a. Coverage rebuild** — `d0ee0b6` data: rebuild the coverage table from the
Index Map. Checked against `decisions/0022` before committing: four tier moves,
census **77/12/8**, investable set **95**, no cost bucket moved.

**7b. The failing test** — `24b3b9c` tests: exclude universe entry by what it
is. Entry is the last rebalance at which any series is held for the first time,
read off `PortfolioPath.weights` (entry completes at rebalance 23 of 155; same
result at weight tolerances 1e-9, 1e-6 and 1e-4); the comparison runs over what
follows and asserts at least 20 rebalances remain. `check` at `24b3b9c`:
**rc=0, 446 tests, 279 s**. **Frozen snapshot: `build_snapshot.py --verify`
(default id `synthetic-v1`) printed `OK hash matches (da3a96990f56)`, rc=0** --
the freeze held, only freshly built panels moved.

**8. Registry corrections** — `af3717e` hypotheses: data_required against the
panel that exists (decisions/0032). `tests/test_hypotheses.py` 33 passed.

**9. `L`, the transfer coefficient and 0029** — `3eff1b7` audit: the transfer
coefficient, the left tail, and a report that stops printing the twin;
`dd9e4fb` decisions: 0029 decided. `check` at `dd9e4fb`: **rc=0, 461 tests,
369 s** (446 + 15 new), governance OK.
- A rule without `alpha()` leaves TC unevaluated: NaN columns and
  `transfer_n_dates = 0`, tested (`tests/test_transfer.py`). A non-callable
  attribute named `alpha` is not mistaken for the method.
- 0029 is out of `proposed/`; **no ridge or eigenvalue floor was added** to the
  frictionless covariance (s2 deferred).
- New per-cell columns: `transfer_coefficient` (full matrix),
  `transfer_coefficient_diagonal`, `transfer_coefficient_alignment`,
  `omega_condition_median`, `omega_condition_max`, `transfer_n_dates`,
  `left_tail_L`, `left_tail_q05`, `realised_ic_cross_sectional_pearson`,
  `realised_ic_cross_sectional_demeaned`.
- Judgement calls the spec left open: Omega is the covariance of the holdable
  series in EXCESS of the benchmark (so `w' Omega w` is exactly the active
  variance the solver constrains, tested), not the raw ids covariance. Empirical
  breadth off the ladder is `(slope / TC)^2` per horizon, blank where no TC was
  measured. The existing report test asserted the old frictionless section and
  was updated to assert its absence (it is the behaviour 0029 s1 retires).
- Rendered against `A-20260918-201042`'s `cells.csv`, the new report prints
  dashes for the columns that run predates and no frictionless section.

**11. Rebalance-policy resolution** -- `8ef03bc` decisions: 0024 -- weekly re-solve stays, deliberately.

**10. Rerun the audit** -- rc=0, at `8ef03bc`. `make check` 349 s, `make audit`
**47908 s (13.3 h)**, run **`A-20260919-155557`**, 644 cells, 10 seeds
(`results/audit/_unattended/20260919-115007-audit/`). Figures below are from
`cells.csv`, not the digest; the digest's medians agree.
- Engine untouched: **`net_ir` is identical in all 644 cells** to
  `A-20260918-201042`. 100 of 484 judged cells still fail, all `risk_calibration`.
- Base-cell medians of the new columns (160 cells): `transfer_coefficient`
  (full matrix, reported) **0.0205** (range -0.008 to 0.085); diagonal **0.0598**
  (-0.038 to 0.241); alignment **0.0365**; `left_tail_L` **0.934** (0.776 to
  1.147; digest: p05 0.85, p95 1.03).
- `omega_condition_median` **91,153** and max 289,324 in every base cell -- the
  same in each, because it depends on the date's covariance and not on the cell.
- `implied_ic` at TC = 1: 0.024 / 0.044 / 0.062 / 0.088 for h4/13/26/52. At the
  measured TC: 1.09 / 1.62 / 1.97 / 6.14. Ladder empirical breadth 5,900 to
  22,000 against formula 12 to 152.
- **The TC values are not usable as measured, and I have not decided why.**
  Published range is 0.3-0.8 (CDT 0.671 full, 0.620 diagonal). Here TC rises
  with IC (full: 0.003 at IC 0.02, 0.061 at IC 0.20) and the **oracle cells
  (IC = 1) read 0.039 to 0.042 full and -0.003 to 0.029 diagonal**, so a perfect
  signal transfers about 4%. Alignment (the inversion-free control) is also
  0.01-0.07, so this is not only the ill-conditioned inverse in the full form.
  Candidate: `w` is the whole fully-invested book, and in excess-return space the
  benchmark-replicating baseline (`w' Omega w` is tiny for it) is not separated
  from the tilt, so A and B correlate alpha with mostly-baseline weights. That
  is a definition question for `decisions/0033` (what "active weight" means when
  the benchmark legs are not holdable), not something I changed.
- `ruler.md` (there is no `report.md`) no longer has the frictionless tables or
  the base-over-frictionless ratio; its one "frictionless cells" mention is the
  veto sentence. Frictionless rows carry no TC by construction (no alpha exposed).


### 2026-09-20 — tasks 12 and 15, and a stop at 16 (Claude Code, Sonnet 5)

**12. Commit the 0035 write-up** — rc=0. `37491a9` decisions: 0035 proposed.

**15. Commit 0036 and the queue rewrite** — rc=0. `d2f2c4b` decisions: 0036.
HANDOFF.md had already gone in with 12, as anticipated; nothing extra to add.

**16. `data/requests/*.yaml` — STOPPED, not committed.** rc=n/a.
- No `make` target or script regenerates them. The only writer is
  `HypothesisRegistry.triage()` -> `write_data_request()`, reached through
  `scripts/nightly_cycle.py --snapshot <id>`, which also writes to the real
  results store and the real `data/requests/`.
- A faithful regeneration needs the manifest of the snapshot the files were
  produced against. The only target that builds one is `synthetic-v1`, which
  would list nearly every series as absent and would not reproduce the changes.
  I did not identify or list the Bloomberg snapshot (`data/snapshots/` is
  off-limits to me), so I could not run triage against it into a scratch dir.
- The six diffs are real (`git diff --ignore-cr-at-eol`); H-2026-0009 shows the
  0032 corrections (MXUS->SPXT, MXEU->MXEUG, MXJP->NDDUUK/NDDUJN, MXEF->M1EF,
  MXWO and LEGATRUU dropped, count 7->6), but the match to a regeneration is
  unestablished, so per the task they are not committed.
- Needs Cowork/owner: name the snapshot id to triage against (or run the triage
  themselves), or decide these are acceptable as hand edits citing 0032.
- Tasks 17-21 not started, per the stop rule.

**16 (continued, same day).** Owner said to commit the six request files and
HANDOFF.md as they stand. Regeneration match still unestablished; committed on
the owner's instruction, citing decisions/0032.
