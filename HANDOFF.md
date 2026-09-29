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

**Run order, as of 2026-09-21: 20, 22, 19, 23, 21.** Tasks 12, 15, 16, 17, 18
and 24 are done — receipts are in `## Done`.

- **20** — gate released by the owner and the task **re-specified**; read its
  AMENDMENT, not the text above it. Commits the outstanding receipts first.
- **22 must land before 19.** 19 is a 3.3 h grid that would otherwise persist
  nothing, which is the hole `decisions/0035` §5 exists to close.
- **23** is independent of all of them and can run whenever.
- **21** is hygiene, any time.
- Tasks **13 and 14 are withdrawn** — read the notice, do not run them.

**As of 2026-09-28 (evening), tasks 0-32 are done. Queued, in order: 34**
(multiple-testing module plus the FDR-vs-FWER Monte Carlo; no engine runs),
then **36** (the created-turnover shadow cost as an override, 60 cells,
`decisions/0040`), then **35** (the volatility-overlay halflife sweep,
OWNER-QUEUE B1/L13, about 240 cells, an overnight run). 36 runs before 35 on
purpose: its code touches the solver, and 35's identity check against the knee
run catches any change to the default path. **Task 33 is ON HOLD**: the owner is holding the
`decisions/0038` ruling (OWNER-QUEUE L17). Do not start it until this line
says otherwise. Task 34's step 0 commits Cowork's queue edits first. Receipts
are in `## Done`.

*(Earlier note, kept for the record: as of 2026-09-28 morning, tasks 0-31 were
done and 32, 33, 34 were queued.)* Task 25's power audit is `A-20260924-194115`, read in
`results/audit/A-20260924-194115/power-on-one-history-2026-09-24.md`. H-2026-0001's
JPMaQS names were renamed 2026-09-24 (`33b84f4`).

**Cowork's project docs, readable here:** Claude Code cannot see the claude.ai
Project. Read-only copies of the docs that tasks cite are in
`Claude outputs/project-mirror/` (git-ignored). Start with `state-of-play.md`.
When a task names `claude/<name>.md`, read `Claude outputs/project-mirror/<name>.md`.

One `scripts/unattended.sh` at a time.

### 24. Commit the records, then the constitution — DO THIS FIRST

**Two commits, in this order.** `SUBSTRATE.md` is amended, so the authorising
record must be in history before the amendment that cites it — the
`decisions/0030` precedent, where the decision landed in one commit and
`substrate: sections 4 and 10` in the next. The `commit-msg` hook
(`.githooks/commit-msg` -> `scripts/check_governance.py`) refuses an owner-only
change whose message does not cite an existing `decisions/` id.

Nothing in the queue commits any of this. Tasks 21-23, the amendment to 18 and
the run-order line were written after task 15 had already committed
`HANDOFF.md`. `decisions/0036` **is** already committed, at `d2f2c4b` by task
15; what is uncommitted are its §1 and §6 amendments of 2026-09-21.
`decisions/0035` was promoted out of `proposed/` after task 15 ran, so its move
is uncommitted entirely.

**Commit A — the records.** `0035` is a move out of `proposed/`; git shows the
old path deleted and the new one untracked, so `git add -A` on both records it
as a rename.

    git add -A decisions/0035-the-transfer-coefficient-measures-the-benchmark-not-the-tilt.md decisions/proposed/0035-the-transfer-coefficient-measures-the-benchmark-not-the-tilt.md
    git add decisions/0036-the-bar-is-excess-over-a-no-information-baseline.md HANDOFF.md OWNER-QUEUE.md
    git commit -m "decisions: 0035 decided, and 0036 amended -- active-weight TC, and two bars

0035, DECIDED 2026-09-21: section 4 option (a) and section 5 both taken. All
three transfer-coefficient estimators are computed on w - w_baseline with the
long-only NNLS tracking portfolio as the baseline, and weights, alpha and the
rebalance-date index are persisted per run. Section 4a is added: covariance.py
already computes r2 and residual_variance per benchmark leg and nothing reads
them, so the quality of the baseline the corrected TC is measured against is
unmeasured; surfacing both, with a test asserting a floor on r2, is now a
requirement.

0036 was committed at d2f2c4b with sections 3, 4a and 4b decided. This amends
it. Section 6, DECIDED 2026-09-21, takes position 3 -- two bars. Bar 1 is the product bar, net IR >= 0.30, unchanged in
value and derived for the first time from the owner's stated 150 bp appetite at
the section 4 budget. Bar 2 is the evidence bar on net_ir_excess against a
block-shuffled baseline, with no threshold: it is the existing multiple_testing
veto, run on the excess. params/audit.yaml does not change and decisions/0025's
tracking-error budget is unmoved, because 0025 inverts the level and the level
is still 0.30.

Section 1 is amended with the dispersion the first draft omitted: the
no-information floor of 0.311 is the mean of a 420 bp-wide distribution across
arbitrary tilts on a single history, -141 to +280 bp, one tilt in eight
negative. 1.5% of alpha is hard; 1.5% from concentrated risk-premium exposure
over 2004-2019 is not, and the latter is what this is.

OWNER-QUEUE L9 closes. L10 and L11 are added. Queue: 22 implements 0035 and must
land before task 19; 23 is the JPMaQS catalogue check, metadata only."

**Commit B — the constitution.** `SUBSTRATE.md` only, so the owner reviews one
small diff, as §2 requires. v0.4 -> v0.5.

    git add SUBSTRATE.md
    git commit -m "substrate: sections 3 and 10 -- the objective is two bars (decisions/0036)

Transcribes decisions/0036 section 6, decided by the owner 2026-09-21. Section 3
replaces the single primary metric with two bars a candidate must both clear:
bar 1, net IR >= target_net_ir, the product bar, still 0.30 and still what the
leaderboard sorts by and what decisions/0025 inverts for the TE budget; bar 2,
net_ir_excess against a no-information baseline, positive and surviving the
multiple_testing veto, with no threshold and the reasoning for why a threshold
is the wrong instrument at this precision. Section 10's multiple_testing row
names the excess as the statistic it tests.

No agent originated this. The wording is transcribed from a decision the owner
made and recorded."

**Do not commit** `data/universe/raw_meta.json`, `raw_structure.json`,
`results/audit-bloomberg.log` or `results/audit/` — regenerable, and SUBSTRATE
§11 keeps them out of git. Everything else `git status` flags is a CRLF phantom;
confirm with `git diff --ignore-cr-at-eol` before adding.

**Then verify the governance check accepts the constitution change:**

    scripts/unattended.sh check --digest

**Receipt should say:** both commit hashes, that git recorded the 0035 move as a
rename rather than a delete plus an add, and the `governance` line from the
check. **Stop and report if governance does not pass** — an uncited owner-only
change is the one failure that must never be worked around.

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

**Amendment, 2026-09-20, after reviewing task 17's receipt.** Task 17 imputes the
standardised truth's mean (0.0) at cells that were live but drew a NaN row in the
shuffle, so the baseline's availability matches its live twin exactly. Cowork has
checked this and it is the right call — `_standardise_truth` leaves `truth_z`
with pooled mean exactly zero, so the fill is neutral mean-imputation and not an
injected tilt, and the second-order shrinkage of the blend's dispersion moves the
alpha magnitude by well under 1% in standard deviation even at a large imputed
share. **No change is asked for.** But the share is unmeasured and the panel is
ragged — late-starting series can reach a quarter of their own rows — so it
should be disclosed rather than assumed.

**Add to the receipt:** the share of live cells that were mean-imputed in the
shuffle, overall and for the worst single instrument, as counts and percentages.
A count is not a vendor value and is reportable under `CLAUDE.md`. If it exceeds
roughly 25% overall, say so and **stop before task 19** — that would mean the
baseline is a materially less dispersed signal than its twin and 0036 §4(a)'s
magnitude-matching claim needs revisiting.

**Also note:** `make audit-baseline-pilot` has never run to completion. Task 17
checked `_write_baseline_run` on a two-cell table only, so this is the first real
exercise of that path and may surface plumbing before it surfaces a number.

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
---

**AMENDMENT, 2026-09-21 — the gate is released and the task is re-specified.
Read this, not the text above.**

**The stop rule above has fired and the owner has released it.** Task 18 showed
the floor at the IC 0.20 alpha scale (0.346) matching its live twin (0.356) and
the floor at IC 0.02 (0.290), so by the letter of task 18 this task should not
start. That rule was written before the baseline existed and is now the wrong
call: it was aimed at "is there signal in the tested range" — answered, no — and
this task asks a different question the pilot does not touch, **where the
response begins between IC 0.20 and IC 1.00.** The oracle reads 1.297 at h13
against a floor of 0.290, so a large response exists somewhere. Owner released
the gate 2026-09-21.

**And the baseline nearly doubles its power.** The warning above about an h13
MDE of 0.166 was for the **level**. On the **excess** the pilot measured SE
0.032 at IC 0.20, so the MDE is **≈0.09** — sharp enough to resolve a shallow
response, which the level was not.

**0. Commit first.** Task 18's receipt and the queue changes since are
uncommitted (`git diff --ignore-cr-at-eol` shows `HANDOFF.md` and
`OWNER-QUEUE.md`). Commit them before running, so the receipt lands against a
committed baseline.

**1. Build a `knee` grid — in `ladder.py`, not in `params/`.** The rungs
**0.35, 0.50, 0.70** are not in `audit.ic_grid`, and `params/audit.yaml` is
owner-only and not authorised by any record here. `baseline_cells()` reads its
rungs from params by design (`decisions/0036` §4b.5) and emits baseline cells
only, so neither serves. Add a third grid whose rungs are a module constant and
which emits **both** a live cell and its matched baseline at each rung:

    h13 only, ten seeds, 3 rungs x 2 = 60 cells

**`params/audit.yaml` must not change.** `params_hash` stays
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c`, or the
pairing against `A-20260919-155557` and `A-20260921-202607` breaks for every
future run.

**2. Do not re-run IC 0.20.** It exists live in `A-20260919-155557` and baseline
in `A-20260921-202607`, both at the same hashes. Pair it from those as the
anchor.

**3. Run.** At the pilot's measured **58 s a cell**, 60 cells is about an hour;
live cells at high IC trade more, so budget 60-90 minutes.

**Receipt should say:** rc, runtime, run id, and per rung **the live net IR, the
baseline net IR, and the seed-paired excess with its standard error** — the
excess is the statistic now (SUBSTRATE §3 bar 2), not the level. Confirm both
hashes match before reporting any contrast, as task 18 did, and **stop and
report if either differs.**

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

### 22. `decisions/0035` §4(a), §4a and §5 — BEFORE task 19

**Decided by the owner 2026-09-21.** `0035` is out of `proposed/` and carries
the spec; read it, not this summary.

**Why it is sequenced here.** Task 19 is a 3.3-hour, 160-cell grid. If it
persists nothing, any later question about those cells costs another 3.3 hours —
which is precisely the hole `0035` §5 was written about, and the lab is one run
away from digging it again. This must land before 19. It need **not** block task
18: the pilot is 40 cells and 50 minutes, cheap to re-run once this exists.

Three pieces:

1. **§5 — persist per run.** `weights`, `alpha` and the rebalance-date index, as
   parquet under `results/artifacts/<run_id>/`, which `STATUS.md` already claims
   exists and which is empty. Base cells at minimum; say in the receipt what the
   disk cost per run turned out to be.

2. **§4(a) — the corrected transfer coefficient.** All three estimators computed
   on `w - w_baseline`, the baseline being the long-only NNLS tracking portfolio
   the lab already builds in `portfolio/covariance.py`. `Omega` and `w' Omega w`
   are unchanged; only the numerator and the correlations move. `0035` §4's
   acceptance test is required and is a **test**, not a check: an IC = 1 oracle
   cell must read a TC near its achievable ceiling, and a no-view book must read
   near zero. Both read wrong today (0.039-0.042 and -0.017).

3. **§4a — surface the replication quality.** `covariance.py` already computes
   `r2` and `residual_variance` per benchmark leg into its `diagnostics` dict and
   **nothing reads them.** The corrected TC is now measured against that
   baseline, so its quality has to be visible: report both per leg wherever TC is
   reported, and assert a floor on `r2` in a test so a degraded replication fails
   loudly instead of quietly re-basing the coefficient.

Then:

    scripts/unattended.sh check --digest

**Receipt should say:** rc, test count, runtime, commit hash, the persisted
artifact size per run, and **the NNLS `r2` per benchmark leg** — that number has
never been looked at and the owner asked for it directly. **Stop and report if
`r2` on either leg is below 0.90**; that would mean the baseline is a poor
replication and `0035` §4's definition needs revisiting before any corrected TC
is reported.

**No re-run of `A-20260919-155557` is authorised here.** Its artifacts do not
exist, so its TC column stays as it is; `0035` §6 says whether to spend the 13.3
hours is a separate decision.

### 23. JPMaQS catalogue check — metadata only, no vintage data

**Independent of 18, 22, 19 and 20.** Different data, different code path,
different gate; run it whenever. Owner authorised 2026-09-21.

**What it is for.** The registry's 27 JPMaQS names have never been checked
against the vendor's catalogue. `decisions/proposed/0034` exists because two
*Bloomberg* names in the pre-registered registry turned out not to exist and were
found by hand. This checks the JPMaQS half before a pull is built on it. **It
does not retire 0034**, which is a standing validator across every source; it
retires the risk for these 27 names, once.

**This call is authorised under SUBSTRATE §2** — `jpmaqs` is listed in
`params/data_sources.yaml` with `enabled: true` and credentials supplied
2026-09-09. It is the lab's first vendor API call.

#### Hard limits

- **Metadata only.** `JPMaQSDownload.get_catalogue(...)` and/or
  `filter_expressions_from_catalogue(expressions, ...)`. **Do not call
  `download()`.** No vintage data, no `value`/`grading`/`eop_lag` pull.
- **Do not touch `params/data.yaml: jpmaqs.status`.** It stays
  `credentials_supplied`. A catalogue is not the macro block, `search_is_open()`
  must stay shut, and `params/` is owner-only regardless.
- **Do not implement `load_macro`.** It stays `LoaderNotImplemented`; that is
  task 24 and is not queued.
- **Never read, print or commit `.env` or anything key-shaped.** Use the existing
  `JPMaQSLoader.credentials()` and `.proxies()`.
- The proxy is `enabled: false` by config — the corporate host does not resolve
  on this machine. **If the call fails on network or auth, report and stop.** Do
  not vary the proxy setting, and do not retry with alternate hosts.

#### Steps

1. **Install the extra.** `make install` is `uv sync --group dev` and the
   `jpmaqs` extra is not in it, so `macrosynergy` is absent from the venv:

       uv sync --group dev --extra jpmaqs

   This changes the venv. Confirm `make check` is still rc=0 afterwards and say
   so in the receipt.

2. **Add a `make jpmaqs-catalogue` target** wrapping a new
   `scripts/jpmaqs_catalogue_check.py`, so the flags live in `build.mk` like
   every other script. Construct the client with `check_connection=True` for a
   clean early failure.

3. **Check the 27 named tickers** tagged `genuine phase-3 gap` in
   `data/requests/ticker_resolution.csv` — **the 27 named, not the 96 the cross
   product returns.** They are 8 cids x 12 xcats; `cross_product_size()` already
   exists for that arithmetic and the receipt should confirm the 96.

4. **Cache the raw catalogue** under `data/raw/` (git-ignored, and off-limits to
   print or summarise per `CLAUDE.md`). It is the offline resolver 0034 would
   need, so it is worth keeping.

5. **Write the findings** to `data/requests/jpmaqs_catalogue_check.csv`:
   hypothesis, ticker, cid, xcat, resolves. Ticker names are not vendor values.

#### Stop rule

**If any of the 27 does not resolve, STOP.** Report the list and do not
substitute, do not guess a near-miss name, and do not drop it. Substitutions are
the owner's call — that is the `decisions/0032` precedent, where `LUALTRUU` and
`LT08TRUU` were removed rather than replaced, and SUBSTRATE §7 makes a silent
substitution a `coverage` veto failure.

**Only if all 27 resolve**, write `data/jpmaqs/request.txt` with them. SUBSTRATE
§5.6 names that file as the pull list and it does not exist — the directory holds
only `.keep`. Note in it that the download returns the cross product and the
loader must filter back to the named tickers.

**Receipt should say:** rc, whether `make check` still passes after the sync, the
catalogue size **as a count**, how many of the 27 resolve, the names of any that
do not, and whether `request.txt` was written.

---

### 25. Bar 2's power on a single history — shuffle the whole score

Added 2026-09-22 by Cowork. **Read `claude/detection-threshold-review-2026-09-22.md`
§1 first** (Cowork project doc).

**Why.** Task 17's baseline keeps its live twin's noise draw and shuffles **only
the truth**. That is the right control for the engine's dose-response — live and
baseline net IR correlate 0.85-1.00 across seeds, so the paired excess is sharp.
It is **not** the null a real hypothesis meets. A real signal has no separate
noise term: bar 2 puts one live IR against the block-shuffle distribution of the
**whole** signal, on one history. This task measures that distribution for
planted signals of known information content, so bar 2's actual power is read
rather than assumed.

**0. Commit first.** `HANDOFF.md` and `OWNER-QUEUE.md` carry this task and
OWNER-QUEUE L13, uncommitted. Commit them before building, so the receipt lands
against a committed queue.

**Build a second shuffle mode, `score`.** Shuffle the fully blended score
(truth and noise together) rather than the truth alone:

1. Build the live score exactly as today, then shuffle its date-rows with
   `block_shuffle_rows` — same 52-row blocks, one permutation shared across
   instruments, as `decisions/0036` §4b.
2. Re-apply the live NaN mask, with the same neutral fill task 17 uses for cells
   that were live but drew a NaN row.
3. Recompute `alpha = ic * sigma * score / sqrt(horizon)` from the shuffled
   score. **`sigma` is not shuffled** — it is the risk model's input, not the
   signal.
4. Each permutation `perm` in 0..19 draws from its own stream, independent of
   the noise RNG **and** of today's `baseline_rng(seed)`. Extend `baseline_rng`
   (or add a sibling) so that the **existing call reproduces today's stream
   exactly** — the bit-for-bit test below depends on it.
5. Add the mode and `perm` to `AuditCell` with defaults that leave every existing
   key unchanged, and append them to `key()` only when non-default (e.g.
   `_baseline_score_p07`), so nothing collides in the append-only store.

**Tests, not checks:** task 17's bit-for-bit reproduction test still passes;
existing live and truth-shuffle keys are unchanged; different `perm` give
different permutations and the same `perm` is deterministic.

**Grid `power`, in `ladder.py`,** rungs as a module constant like `KNEE_IC_RUNGS`
— nothing in `params/`. h13, IC **0.35** and **0.70**, live seeds **0** and
**1**, 20 permutations each: 2 x 2 x 20 = **80 cells**, about 80 minutes at 58 s
a cell. Score-shuffle cells only; the live twins exist in `A-20260922-005316` —
do not re-run them. Add `make audit-power` and extend the `scripts/unattended.sh`
whitelist.

**`params/` must not change.** `params_hash` stays
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c`.

    scripts/unattended.sh check --digest
    scripts/unattended.sh audit-power --digest

**Receipt should say:** rc, runtime, run id, commit hash; whether both hashes
match `A-20260922-005316` (**stop and report if either differs**); whether the
bit-for-bit test passes (**stop and report if not**); and for each (IC, seed) the
live net IR, the mean and sd of its 20 shuffled net IRs, and the live IR's rank
among the 21. Nothing else — the interpretation is Cowork's and the owner's.

---

### 26. `credentials()` refuses a malformed secret — loudly, without printing it

Added 2026-09-23 by Cowork. Independent of every other task.

**0. Commit first.** `HANDOFF.md` (tasks 26-27, the run-order note) and
`OWNER-QUEUE.md` (L14) are uncommitted. Commit them before building. Task 25's own
step 0 will then find nothing to add, which is expected and not a failure.

**Why.** Task 23 lost a day to a `401` that was two credential faults, one of
them a trailing `\r` on `DQ_CLIENT_ID` from a CRLF `.env` sourced in WSL.
`JPMaQSLoader.credentials()` (`src/signal_lab/loaders/jpmaqs.py`) passes
environment values through untouched, so a malformed value reaches the vendor
and comes back as an authentication error that points everywhere but here.

**Build.** In `credentials()`, after the missing-key check, **refuse** — do not
strip — any value that has leading or trailing whitespace or contains a control
character (`\r`, `\n`, `\t`, or anything with `ord < 32` or `== 127`). Raise
`RuntimeError` naming **the variable and the defect only** ("DQ_CLIENT_ID has a
trailing carriage return -- is .env CRLF? run: sed -i 's/\r$//' .env").
**Never include the value, its length, or any slice of it** in the message.
Refusal rather than stripping is deliberate: SUBSTRATE §10's fail-loud rule, and a
silently repaired secret hides which file is wrong.

If `FREDLoader` (or any other loader) reads a key from the environment the same
way, apply the same check there through one shared helper; say in the receipt
whether it did.

**Tests** (new `tests/test_jpmaqs_credentials.py`, `monkeypatch.setenv` with
dummy values only): a clean pair passes; a trailing `\r`, a trailing space, an
embedded `\n` and a leading tab each raise; the raised message contains the
variable name and does **not** contain the dummy value. No network, no
`macrosynergy` import needed.

    scripts/unattended.sh check --digest

**Receipt should say:** rc, test count, runtime, commit hash, which loaders now
use the helper.

### 27. Candidate names for the 12 unresolved JPMaQS tickers — names only, no choice

Added 2026-09-23 by Cowork. **Needs the cached catalogue from task 23**
(`data/raw/jpmaqs_catalogue.json`, a JSON list of ticker strings). **No vendor
call** — work from the cache.

**Why.** 12 of 27 registered tickers do not resolve (task 23 receipt;
`data/requests/jpmaqs_catalogue_check.csv`). Every failure is at the xcat: each
cid resolves elsewhere. OWNER-QUEUE L14 asks the owner to rename, drop or wait
on each. This task gives him a short list to choose from instead of the vendor
documentation. **It chooses nothing.**

**Build `scripts/jpmaqs_candidates.py` and `make jpmaqs-candidates`.** For each
row of `jpmaqs_catalogue_check.csv` with `resolves == False`:

1. Take the xcat's **stem** — the leading token before the first `_`
   (`INTRGDP`, `UNEMPLRATE`, `BLSDCLN`, `MBASEGDP`, `RM1GDP`, `RM3GDP`,
   `GB10YXGB`).
2. List every catalogue ticker with the **same cid** whose xcat starts with that
   stem. If there are none, relax to the first four characters of the stem and
   mark the row `relaxed`. If still none, write one row with `candidate` empty.
3. Write `data/requests/jpmaqs_candidates.csv`: `hypothesis, requested,
   cid, stem, match (stem | relaxed | none), candidate`. Sort by requested, then
   candidate. Cap at 40 candidates per requested ticker and say in the receipt
   if any hit the cap.

**Hard limits.** Ticker **names** only — they are not vendor values and are
reportable; nothing else from the catalogue leaves `data/raw/`. **Do not edit**
`ticker_resolution.csv`, any hypothesis file, `data/requests/H-*.yaml`, or write
`data/jpmaqs/request.txt`. **Do not rank or recommend** — no "best match"
column; the choice is the owner's under the `decisions/0032` precedent.

**Test:** a small fixture catalogue (hand-written names, not vendor data) checks
the stem match, the relaxed fallback and the empty row.

    scripts/unattended.sh check --digest
    make jpmaqs-candidates

**Receipt should say:** rc, commit hash, and per requested ticker the count of
candidates and its `match` level. Not the candidate names themselves — they are
in the CSV.

### 28. The cycle tests write into the real `data/requests/` — isolate them

Added 2026-09-23 by Cowork, from the task 26-27 receipt. **Run this first; it
unblocks 26 and 27.** Claude Code's diagnosis is right and Cowork has confirmed
it in the code:

- `scripts/nightly_cycle.py` has no `--requests-dir`. It builds
  `HypothesisRegistry` with the default `requests_dir=REQUESTS_DIR`, which is
  `REPO_ROOT / "data" / "requests"` (`harness/hypotheses.py:35`).
- The three cycle tests in `tests/test_scripts.py`
  (`test_nightly_cycle_records_blocked_not_a_fake_veto_failure`,
  `test_the_cycle_records_the_specific_blocked_reason` and
  `test_the_validation_run_is_recorded_and_tagged`) isolate the snapshot and the
  store in `tmp_path`, but not the requests. So every `make check` rewrites the
  tracked `data/requests/H-2026-00xx.yaml` from a synthetic snapshot.
- That write, on `/mnt/c`, is what hit `EINVAL`: something on the Windows side
  held the file open. Isolating the write removes that exposure, and an
  intermittent test failure then points at a real problem instead of a
  Windows file lock.

**Build.**

1. Add `--requests-dir` to `nightly_cycle.py`, defaulting to the current
   `REQUESTS_DIR`, and pass it to `HypothesisRegistry(requests_dir=...)`.
   Nothing changes for a real cycle run.
2. Pass `--requests-dir str(tmp_path / "requests")` in every test that calls
   `cycle.main` without `--dry-run`. Grep for all of them rather than trusting the
   three names above.
3. **Add a guard test.** It records the mtimes and hashes of everything under
   `data/requests/` and `hypotheses/`, runs one cycle through `cycle.main` with
   the new flag, and asserts both trees are byte-identical and untouched. The
   cycle can also `shutil.move` hypothesis files between states
   (`hypotheses.py:572`), so this is the guard against any future test that
   forgets the flag.
4. Do not change what triage writes, or where a real run writes.

**Then re-run the check once, with tasks 26 and 27 in the working tree:**

    scripts/unattended.sh check --digest

- **rc=0:** commit in three parts: 28 alone, then 26, then 27. Then run
  `make jpmaqs-candidates` (task 27's last step) and continue to task 25.
- **rc=2 again:** stop and report the failing test ids. Do not re-run hoping it
  clears.

**Receipt should say:** rc, test count, runtime, the three commit hashes,
whether the guard test passes, and task 27's per-ticker candidate counts and
match levels as that task asks.

**One question for the receipt, not for fixing.** Task 16 (2026-09-20) stopped
because six `data/requests/*.yaml` had changed and nothing seemed to regenerate
them. It concluded that a synthetic triage "would not reproduce the changes".
This finding suggests `make check` may have been what wrote them. Say whether
the files these tests produce in `tmp_path` match the committed ones
byte-for-byte (`diff`, names only, no values involved). If they match, task 16's
"hand-edited?" question has its answer.

---

### 31. Apply the owner's L14 renames for H-2026-0004, 0005, 0010, then the vendor check

Added 2026-09-27 by Cowork. **Owner ruling 2026-09-27, OWNER-QUEUE L14:** "recs
on all". This is the same pattern as `33b84f4` (H-2026-0001). No compute.

**0. Commit first.** `OWNER-QUEUE.md` carries L14's ruling and the 2026-09-26
task-30 notes under L15 and B3. `HANDOFF.md` carries this task. Commit the
two alone (`queue: task 31, L14 ruling 2026-09-27`).

**1. Addendum to `decisions/0032`,** `## Addendum, 2026-09-27`, in the same
form as the 2026-09-24 one. Cite OWNER-QUEUE L14, tasks 27 and 29
(`data/requests/jpmaqs_name_search.csv`), and Macrosynergy's Academy notebooks
"Bank survey scores", "Monetary aggregates" and "Government bond yields and
carry" for what each series measures. The table:

| hypothesis | phase-0 name | now | why |
|---|---|---|---|
| 0004 | `{USD,EUR}_BLSDCLN_SA_D1Q1QL1` | `{USD,EUR}_BLSCSCORE_NSA_D2Q2QL2` | lending *standards* z-score (credit supply; positive = easing), 2 quarters over the prior 2, matching the signal's "2q change". **Enters negated**, so the registered direction `negative` (on tightening) is unchanged. NSA z-score, not an SA balance. `BLSDSCORE` is credit *demand* and was not used |
| 0005 | `EUR_RM3GDP_SA_D1M1ML12` | `EUR_RMBROAD_SJA_P1M1ML12` | real broad money (M3, CPI-deflated), % over a year ago, the hypothesis's title. A growth rate, not "% of GDP" |
| 0005 | `USD_RM1GDP_SA_D1M1ML12` | `USD_RMBROAD_SJA_P1M1ML12` | as above. **USD broad money is M2**. The narrow-money leg is dropped: the hypothesis is about broad money |
| 0005 | `USD_MBASEGDP_SA_D1M1ML12` | **dropped** | no 12-month change exists (1/3/6 only); monetary base is a different mechanism; a derived change would mix vintages |
| 0010 | `USD_GB10YXGB_NSA` | `USD_GB10YCRY_NSA` | no `XGB` series and no term-spread category exist. 10y carry is "yield plus roll-down", the rationale's own words, so the signal is **re-specified from term spread to carry** |
| 0010 | `EUR_GB10YXGB_NSA` | `DEM_GB10YCRY_NSA` | no euro-area bond cross-section; bonds are by country, and the Bund is the benchmark |
| 0004 | `DRTSCILM` (FRED) | **dropped** (owner 2026-09-27) | the Fed's own survey of US lending standards duplicates the `USD_BLSCSCORE` leg and runs the opposite sign (positive = tightening). It also withdraws the 2026-09-19 approval to add it to the FRED request (`decisions/0032` §5, OWNER-QUEUE L6) |

Say that direction, horizon, target and rationale are otherwise unchanged. Say
that the phase-0 names remain in git history. **Also
record, in one line,** that 0010's declared safeguard (risk decomposition, B5)
still can't be built. That's a caveat, not a change.

**2. Update the files,** as `33b84f4` did:
- `hypotheses/pending/H-2026-{0004,0005,0010}.yaml`: `data_required`, plus a
  dated "Amended 2026-09-27 by owner ruling" note in each, saying what changed
  and why. Do **not** edit `direction`, `horizon_weeks`, `target_axis` or the
  rationale.
- `data/requests/H-2026-{0004,0005,0010}.yaml`: the same series changes.
  Nothing else.
- `data/requests/ticker_resolution.csv`: the new names under the same status
  (`jpmaqs_gap`, "genuine phase-3 gap"). Remove the rows for the two dropped
  0005 names and for `DRTSCILM`, and give the reasons in the addendum.
- `src/signal_lab/harness/hypotheses.py` mentions `DRTSCILM`. If that's a
  request or series list, remove it there too. If it's a test fixture or an
  example, leave it and say so in the receipt.
- Don't hand-edit `jpmaqs_catalogue_check.csv` or `jpmaqs_candidates.csv`.
  The vendor check rewrites the first one.

**3. Vendor names check.** This is a metadata call, the same one task 23 ran
under `decisions/0037`. It pulls no vintage data.

    scripts/unattended.sh check --digest
    make jpmaqs-catalogue

**Expect 26 names, all resolving** (27 registered; 0005 goes from 3 names to
2, since two legs are dropped and one is added): 7 for 0001, 2 for 0002, 4 for
0003, 2 for 0004, 2 for 0005, 4 for 0006, 2 for 0010 and 3 for 0011. **If any
name fails to resolve, stop and report it. Don't substitute.** If the vendor
call fails for auth or network reasons, stop and report it the way task 23
did. Never print credentials.

**Receipt should say:** rc, commit hashes, the resolve count (or the failures),
and whether `check` passed. **Then stop.** Implementing `load_macro` and the
pull itself are not part of this task.

---

### 32. The friction sweep: the shadow-cost coefficient at 10, 20 and 40

Added 2026-09-28 by Cowork. **Owner-approved 2026-09-28** (OWNER-QUEUE B3c,
`decisions/0038`). **Run this before task 33**: its 10 bp arm checks against
the knee run under today's `params_hash`, which task 33 changes. About 1-1.5 h.

**0. Commit first,** alone: `decisions/0038-turnover-is-disclosed-not-vetoed.md`,
`decisions/0039-the-lab-screens-it-does-not-confirm.md`, `HANDOFF.md` and
`OWNER-QUEUE.md` (`decisions: 0038, 0039 (owner rulings 2026-09-28); queue
tasks 32-34`). Committing 0038 doesn't apply it; that's task 33.

**Why.** Task 30's books trade 3.2-3.4x a year against a 100% target, so the
shadow cost isn't holding turnover near its target. The owner wants to see
how results respond to more friction. The shadow cost
(`constraints.turnover.penalty.coefficient`, 10 bp at 150%) shapes weights and
never enters net IR. The real costs are unchanged, so net IR stays honest.

**Build.** Add `shadow_coefficient: float | None = None` to `AuditCell`.
`None` reads `params/` as today, and any other value overrides the coefficient
for that cell only. Append it to `key()` only when set (e.g. `_shadow20`), so
existing keys don't change. Add a `friction` grid to `ladder.py` as module
constants (nothing in `params/`): h13, IC **0.35 and 0.70**, seeds **0-9**,
coefficient **10, 20, 40**, live cells only. That's **60 cells**, including
the 10 bp arm. Add `make audit-friction` and extend the `unattended.sh`
whitelist.

**Test:** a cell with `shadow_coefficient=None` and one with `10.0` give
identical results. Existing keys are unchanged.

    scripts/unattended.sh check --digest
    scripts/unattended.sh audit-friction --digest

**Receipt should say:**
- rc, runtime, run id, commit hash.
- **The 10 bp arm against the knee run `A-20260922-005316`:** live `net_ir`
  identical, cell by cell, for all 20 (IC, seed) pairs, and whether the hashes
  match. **Stop and report if not.**
- Per (IC, coefficient), median and range over 10 seeds of: net IR, cost drag
  (gross − net), annual turnover, rolling one-year max turnover, `te_p95`, and
  realised IC.
- Paired by seed: net IR at 20 and at 40, minus net IR at 10 (mean, sd, and how
  many seeds are positive).
- Counts above **200%** (the new highlight level), annual and rolling max, per
  arm.
- `risk_calibration` fails per arm.

Interpretation is Cowork's and the owner's. **Then stop.**

### 33. Apply `decisions/0038`: turnover is disclosed, never vetoed

> **ON HOLD, 2026-09-28 (Cowork, at the owner's instruction).** The owner is
> holding the 0038 ruling until he has read the friction sweep (OWNER-QUEUE
> L17, L18). **Do not run any step of this task**, including step 0, whose
> commit has moved to task 34's step 0. Cowork will lift or re-issue it.

Added 2026-09-28 by Cowork. **Owner ruling 2026-09-28** (OWNER-QUEUE B2 and
B3). This touches `SUBSTRATE.md`, `params/` and `vetoes/`, all owner-only.
**Every commit cites `decisions/0038`**, which is in the working tree,
uncommitted. **Run after task 32.**

**0.** 0038 was committed in task 32's step 0. Cowork has since added the
owner's confirmation-gate ruling to `decisions/0039` and L16. Commit those two
files alone first (`decisions: 0039 confirmation gates (owner 2026-09-28)`).

**1. Apply "What changes" 1-5 of 0038 exactly.** Nothing else in `params/`,
`vetoes/` or `SUBSTRATE.md`. The only params change is to `vetoes.yaml` and one
new reporting key in `constraints.yaml`. Don't touch `per_rebalance_caps`.
Bump `params_version` as the repo's convention requires.

**2. Verify past verdicts.** For every `results/audit/A-*/cells.csv`, count the
cells whose verdict names `turnover`. The expected count on Bloomberg runs is
zero. List any that aren't.

**3. Record** the old and new `params_hash` in 0038's "Consequences" section,
as a dated line.

    scripts/unattended.sh check --digest

**Receipt should say:** rc, commit hashes, the old and new `params_hash`, the
verdict count from step 2, and the tests that changed and why. **Then stop.**

---

### 34. FDR against FWER: build the multiple-testing module, then a Monte Carlo on the registry's shape

**0. Commit first, alone** (added 2026-09-28 evening; this replaces task 33's
step 0, which is on hold): `decisions/0039-the-lab-screens-it-does-not-confirm.md`,
`decisions/0040-the-shadow-cost-prices-the-turnover-a-trade-creates.md`,
`OWNER-QUEUE.md` and `HANDOFF.md`, with the message `decisions: 0039 gates
adopted, 0040 created-turnover shadow (in principle); queue: hold 33, add 35-36,
L12 corrected, L17-L18 (owner 2026-09-28)`. Nothing under `params/`, `vetoes/` or `SUBSTRATE.md` is in this
commit. Verify with `git diff --cached --ignore-cr-at-eol --stat` before
committing.

Added 2026-09-28 by Cowork. **Owner-approved 2026-09-28** (OWNER-QUEUE L16).
**No engine runs:** a statistics-level simulation, calibrated on task 30, that
runs in minutes. Independent of tasks 32 and 33, but runs after them in queue
order.

**Why.** The owner ruled the lab a screen (`decisions/0039`). SUBSTRATE §9 still
gates on Romano-Wolf at FWER 5%, and §9 already names FDR as the owner-decided
alternative. **Nothing in `src/` implements either yet:** `stats/` holds only
`blocks.py`, and `run_context.romano_wolf` is a placeholder. The owner wants a
number to decide on: how much power FDR buys over FWER for a registry shaped
like this one, and at what realised error.

**1. Build `src/signal_lab/stats/multiple_testing.py`,** the module the real bar-2
gate will use later. Each procedure takes observed statistics `t` (shape `m`)
and a joint null draw matrix `T0` (shape `k x m`, one row per shuffle, with
columns sharing the permutation, as the audit's shuffles do). Each returns a
boolean reject vector and the adjusted p-values:
- `holm(p, alpha)`: the reference FWER procedure, which ignores dependence.
- `romano_wolf(t, T0, alpha)`: the stepdown max-t, FWER. Romano & Wolf (2005,
  *Econometrica*; 2016, *Statistics & Probability Letters*).
- `benjamini_hochberg(p, q)` and `benjamini_yekutieli(p, q)`.
- `romano_shaikh_wolf_fdr(t, T0, q)`: bootstrap FDR under dependence.
  Romano, Shaikh & Wolf (2008), *Econometric Theory* 24(2). Implement from the
  paper. **Record any choice the paper leaves open in the docstring.** If you
  can't implement it faithfully, say so in the receipt and ship the others;
  don't approximate it silently.
- Marginal p-values from the null draws: `p_j = (1 + #{T0[:, j] >= t_j}) / (k + 1)`.

**Tests, with known answers:**
- BH and BY on a hand-worked example from the paper or a textbook.
- With independent columns, Romano-Wolf's rejections match Holm's closely.
- Under the complete null (all `m` false), a short simulation keeps realised
  FWER ≤ alpha and FDR ≤ q, within MC error.
- Everything is deterministic under a seed.

**2. The study, `scripts/fdr_vs_fwer.py`** plus `make fdr-study`. It writes
`results/fdr_vs_fwer/<stamp>/summary.csv` and `report.md`. The model is at the
level of the test statistic, standardised by the null sd:
- **m = 12**, grouped by `target_axis` from `hypotheses/pending/*.yaml`: region
  4, credit 3, duration 2, three singletons. Read the groups from the files; don't
  hard-code them.
- **Null:** each hypothesis's statistic is N(0, 1). Correlation is `rho_w`
  within an axis and `rho_b` between axes. Grid: `rho_w` in {0, 0.3, 0.6},
  `rho_b` in {0, 0.2}.
- **True hypotheses:** `n_true` in {0, 1, 3, 6}, spread across axes, with mean
  shift `mu` and sd `s`, calibrated on task 30's `A-20260926-161749` and the
  knee run. **IC 0.70:** `mu` = 0.255 / 0.168 ≈ 1.52, `s` = 0.193 / 0.168 ≈ 1.15.
  **IC 0.35:** `mu` from the knee grid's 10-seed paired excess (0.095) over the
  pooled null sd, with `s` as at 0.70 (**say that this `s` is assumed**). Also a
  `mu` sweep of 0.5, 1.0, 1.5, 2.0 and 3.0, for the curve.
- **Shuffles per test**, `k` in {20, 100, 500, 1000}. Draw `T0` from the same
  null correlation.
- **Procedures:** Holm 5%, Romano-Wolf 5%, BH at q = 5% and 10%, BY at 10%,
  RSW-FDR at 10%.
- **5,000 MC replications** per scenario, seeded.

**Report per scenario:** average power (the share of true hypotheses passing),
P(at least one true passes), realised FWER, realised FDR, and mean false passes.
Add a short table for the owner's two headline cases, `n_true` = 3 at IC 0.35
and at IC 0.70, `rho_w` = 0.3, `rho_b` = 0.2, `k` = 1000.

**Caveats the report must state:**
- This models the test, not the engine. It assumes normal statistics and moments
  calibrated on planted signals.
- The registry has one hypothesis per SUBSTRATE §6 family, so "family level
  first, then within" is trivial here, and the study runs flat.

    scripts/unattended.sh check --digest
    make fdr-study

**`params/`, `vetoes/` and `SUBSTRATE.md` do not change.** The gate stays FWER
until the owner rules L16.

**Receipt should say:** rc, runtime, commit hash, the output directory, the two
headline tables, whether RSW-FDR was implemented, and any test that needed a
tolerance and why. Interpretation is Cowork's and the owner's. **Then stop.**

---

### 36. The shadow cost priced at the turnover a trade creates — override and a 60-cell grid

Added 2026-09-28 by Cowork. **Owner ruling 2026-09-28** (OWNER-QUEUE L18,
`decisions/0040`, committed in task 34's step 0). **Measure first:** this adds
a per-cell override, like task 32's `shadow_coefficient`. **Nothing in
`params/`, `vetoes/` or `SUBSTRATE.md` changes.** Run after task 34 and before
task 35. About 60 cells. The quadratic term may make each solve slower than
task 32's ~84 s, so budget 1.5-2.5 h.

**Read first:** `decisions/0040`, especially "The ruling, made precise". The
formula there is the specification. If anything in it can't be implemented as
written, stop and report; don't approximate.

**Build.**

1. **`AuditCell.shadow_form: str = "trailing"`**, accepting `"trailing"` (today)
   and `"created"` (0040). Append `_created` to `key()` only when it isn't
   `"trailing"`, after any `_shadowNN`, so existing keys don't change.
2. **In `_OptimiserRule`, for `"created"` only:**
   - `P` is the sum of the last `W−1` entries of `turnover_log`, with missing
     entries filled at `constraints.turnover.target_annualised / ppy`.
     `W = int(round(ppy))`.
   - Take the shadow **out** of the linear cost vector. The vector keeps the
     real half-spread only.
   - Pass the solver a convex shadow term instead:
     `S(x) = κ/(2(r−s)) · (W/ppy) · [pos(T(x) − s)² − pos(T(0) − s)²]`,
     with `x = Σ|trade|`, `T(x) = (P + x)·ppy/W` and
     `κ = coefficient × 1e-4` (coefficient from the cell override or
     `params/`).
   - The first rebalance stays free, as today.
   - `"trailing"` must follow exactly the code path it does now.
3. **In `portfolio/long_only.solve`:** add an optional argument, for example
   `shadow_quadratic: tuple[float, float] | None` carrying `(a, b)` for
   `S = a·pos(b + x)²`. The constant `−a·pos(b)²` doesn't affect the solve.
   - **cvxpy:** `cp.square(cp.pos(b + cp.sum(cp.abs(trade))))`. Check that
     the problem is DCP, and put `a` into the same bps scaling as the other
     objective terms.
   - **scipy reference:** the same term on `x = Σ(u + v)`, with its analytic
     gradient `2a·pos(b + x)`.
   - `None` must leave both paths byte-for-byte as they are.
4. **Diagnostics:**
   - per rebalance: `shadow_bps` = the marginal shadow at `T(x)` in bp, and
     `shadow_paid_bps` = `S(x)/x` in bp (0 when `x = 0`);
   - per cell: `turnover_autocorr_lag26`, `_lag52`, `_lag53` and `_lag78` of
     `path.turnover`, for **every** cell (a new column is fine: keys don't
     change).
5. **Grid `friction_created`** in `ladder.py`, as module constants: h13, IC
   0.35 and 0.70, seeds 0-9, coefficient 10, 20 and 40, `shadow_form="created"`,
   live cells only, **60 cells**. Add `make audit-friction-created` and extend
   the `unattended.sh` whitelist.
6. **Preflight:** the control run `A-20260928-151055` (task 32) exists, both
   hashes match it, and it has the live cell at every (IC, seed, coefficient).

**Tests:**
- The `"trailing"` default gives identical `net_ir` to before on the small
  universe, and existing keys are unchanged.
- `shadow_quadratic=None` leaves both solvers' results unchanged.
- At a coefficient of 0, `"created"` equals `"trailing"`.
- **The shadow term is convex in trade size:** for fixed `P`, the solver's
  shadow on two trades of size x/2 in consecutive weeks is less than on one
  trade of size x. Test the function `S`, not an engine run.
- **Prefill:** at rebalance 2, `P` equals `(W−2)·target/ppy` plus the first
  logged trade.
- The derivative of `S` at `x` equals the 0024 curve at `T(x)`, to 1e-12.

```
scripts/unattended.sh check --digest
scripts/unattended.sh audit-friction-created --digest
```

**Receipt should say:**
- rc, runtime, run id, and the commit hash.
- Whether the hashes match `A-20260928-151055`, and that `params/` is
  unchanged.
- **Per (IC, coefficient), median and range over 10 seeds, with the same
  figures from `A-20260928-151055` beside them:**
  - net IR and gross IR;
  - cost drag;
  - annual turnover;
  - rolling one-year p95 and max;
  - `turnover_per_rebalance_max`, plus the count of cells with a week of 1.5x
    NAV or more and of 1.95x or more;
  - `turnover_autocorr_lag53` and lag 52;
  - `shadow_bps_mean` and `shadow_paid_bps` mean;
  - `te_p95` and realised IC.
- **Paired by (IC, seed, coefficient):** created minus trailing, for net IR,
  annual turnover and `turnover_per_rebalance_max` (mean, sd, number
  positive).
- Counts above 200%, annual and rolling max, for each arm.
- `risk_calibration` fails for each arm.
- Solver health: `inaccurate_share` max, `infeasible_te_share` max, and
  anything not solved by CLARABEL.

Interpretation is Cowork's and the owner's. Adopting the form, and choosing the
coefficient, happen later in `params/` via 0040. **Then stop.**

---

### 35. The volatility-overlay halflife sweep (OWNER-QUEUE B1, L13)

Added 2026-09-28 by Cowork. **Owner-approved 2026-09-28** (L13: "approved, go
ahead"). **Run after task 34, and before task 33 is released**: the h13
no-overlay arm checks against the knee run under today's `params_hash`,
which task 33 would change. About 240 cells at the friction sweep's ~84 s
each, so **5.5-6 h**. The h4 cells may run slower. Treat it as an overnight run.

**Why.** `risk_calibration` fails 23-47% of cells in every grid, on 2008, live
and baseline alike (L13). In the friction sweep it failed 21 of 60, with 2008
the worst year in 50. `decisions/0030` found a scalar 26-week overlay took the
worst-year bias from 1.39-2.21 to 1.17-1.61 (0 fails of 11). That was tested
at one horizon, two IC rungs and one halflife. B1 is retired only by a sweep
across halflives and horizons.

**This does not turn the overlay on.** It sets `AuditCell.vol_halflife` and
`vol_overlay` per cell, which already exist. Nothing in `params/` reads them.
The standing refusal below stands.

**Build.** Add a `halflife` grid to `ladder.py` as module constants (nothing in
`params/`): live cells only, IC **0.35 and 0.70**, seeds **0-9**, horizons
**4, 13 and 26**, and `vol_halflife` in **None, 13, 26, 52** with
`vol_overlay="scalar"` whenever `vol_halflife` is set. Constraints and costs
are the knee grid's live cells' (`per_rebalance_cap` from
`audit.per_rebalance_cap_default`, no turnover cap, cost multiplier 1.0, shadow
coefficient from `params/`). That's 2 x 10 x 3 x 4 = **240 cells**. Keys already
encode the overlay (`_vhl26scalar`), and a `None` cell's key is unchanged. Add
`make audit-halflife`, extend the `unattended.sh` whitelist, and add a
preflight like `_friction_preflight`: the knee run `A-20260922-005316` exists,
both hashes match, and it has the live h13 cell at every (IC, seed).

**Test:** the grid is 240 unique live keys. Every `vol_halflife=None` cell at
h13 has the same key and constraints as the knee run's live cell. A
`vol_halflife` cell is `scalar`.

    scripts/unattended.sh check --digest
    scripts/unattended.sh audit-halflife --digest

**Receipt should say:**
- rc, runtime, run id, commit hash.
- **The h13 `None` arm against the knee run `A-20260922-005316`:** live
  `net_ir` identical, cell by cell, for all 20 (IC, seed) pairs, and whether the
  hashes match. **Stop and report if not.**
- Per (horizon, halflife), pooled over both ICs (20 cells), and separately per
  IC: `risk_calibration` fails (count), `bias_worst_annual` median and max, how
  many cells have 2008 as the worst year, full-sample `bias_stat` median,
  `te_p95` median, `te_p95_to_budget` median, net IR median and range, annual
  turnover median, cost drag median.
- Paired by (IC, seed, horizon): net IR at each halflife minus net IR at `None`
  (mean, sd, number positive).
- Any cell with `inaccurate_share` > 0.01 or `infeasible_te_share` > 0.

Interpretation is Cowork's and the owner's. Whether the overlay becomes policy
is B1, an owner decision. **Then stop.**

---

## Not queued yet, and what each is waiting on

Rewritten 2026-09-22 by Cowork; the earlier text predated `decisions/0035` being
decided and is in git history.

**Landed since the last rewrite:** the block-shuffled baseline (tasks 17-19), the
knee grid (20), and `0035` §4, §4a and §5 — the corrected TC, the NNLS replication
quality, per-run persistence of weights and alpha (22).

**Exposure-space planting** (design B in
`claude/detection-threshold-review-2026-09-22.md`). Not designed. It plants noise
per SUBSTRATE §6 axis rather than per instrument, to test whether iid noise across
a collinear universe is what depresses transfer. Waits on task 25: if bar 2 is out
of reach on a single history regardless, that changes what B is for.

**`0035` §7 — the transfer coefficient.** Open. The oracle's corrected TC reads
0.022 against an acceptance case of 1.0, with `w` and `w_baseline` nearly
orthogonal (cos 0.011). No task until a hypothesis for it is written.

**The volatility overlay halflife sweep (OWNER-QUEUE B1).** Queued 2026-09-28 as
task 35 (owner's L13 ruling). Turning the overlay **on** stays a standing
refusal below until the owner rules B1.

**The shadow cost's 53-week echo (OWNER-QUEUE L18).** Ruled 2026-09-28 (option
a, `decisions/0040`) and queued as task 36. Adopting it into `params/` waits on
task 36 and lands with task 33.

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

**17. The block-shuffled baseline** — `da214c0` audit: the block-shuffled
baseline. `scripts/unattended.sh check --digest` at `a874b5f` + the working
tree: **rc=0, 294 s, 479 tests** (461 + 18 new in `tests/test_baseline.py`),
governance OK, ruff clean (`20260920-112220-check`). A first check at 9 s failed
`ruff format` on my own files; formatted and rerun.
- **The bit-for-bit reproduction test PASSES.** Golden values (score hash
  `3c56e07462d30d6d`, net IR `-0.8793457503233992` on the small synthetic
  cell) were taken from `HEAD` in a clean worktree, and the working tree
  reproduces both.
- Shuffle is in `src/signal_lab/stats/blocks.py`. Targets `audit-baseline-pilot`
  and `audit-baseline` exist and the unattended whitelist is extended; nothing
  in `params/` changed.
- Two judgement calls beyond 0036: (1) a baseline-only run writes `cells.csv` and
  a `summary.json` (panel/params hashes, net IR by rung with min/max) instead of
  the ruler report, which raises `KeyError: 'horizon'` without base cells;
  (2) cells that were live but received a NaN row in the shuffle are set to zero,
  so availability equals the live cell's exactly rather than shrinking.
- Not run end to end on real data. A full synthetic pilot exceeded 15 min, so
  plumbing was checked on a 2-cell table through `_write_baseline_run`.

### 2026-09-21 — task 24 (Claude Code, Sonnet 5)

**24. Commit the records, then the constitution** — rc=0.
- Commit A `40ff9df` decisions: 0035 decided, and 0036 amended. Git recorded the
  0035 move out of `proposed/` as a **rename**, not a delete plus an add.
- Commit B `d012c37` substrate: sections 3 and 10 (decisions/0036). The
  `commit-msg` hook accepted it. My own attempts to commit `SUBSTRATE.md` were
  refused twice by the permission classifier; the owner committed it by hand.
  The message is the subject line only, without the task's explanatory body.
- `scripts/unattended.sh check --digest` at `d012c37`: **rc=0, 404 s, 479 tests**
  (`results/audit/_unattended/20260921-161337-check/`). Governance line: "OK. No
  uncited owner-only change since `85694662`. Commit hook is installed." Ruff
  clean, holdout lock 15 of 15.
- Not committed, as instructed: `raw_meta.json`, `raw_structure.json`,
  `results/audit-bloomberg.log`, `results/audit/`.

### 2026-09-21 — task 18 (Claude Code, Sonnet 5)

**18. The baseline pilot** — rc=0. `scripts/unattended.sh audit-baseline-pilot
--digest` at `d012c37`: check rc=0 (303 s), audit rc=0 (**2325 s**), run
**`A-20260921-202607`**, 40 cells, h13, ten seeds
(`results/audit/_unattended/20260921-162103-audit-baseline-pilot/`).
- **Hashes match `A-20260919-155557`**: `panel_hash` `dfbf5c5a…5793` and
  `params_hash` `ebdfb70e…b77c`, both identical. The pairing is valid.
- Baseline `net_ir` by rung (mean, seed min to max, n=10):
  - IC 0.02: 0.290 (-0.369 to 0.589)
  - IC 0.05: 0.321 (-0.605 to 0.798)
  - IC 0.10: 0.277 (-0.101 to 0.677)
  - IC 0.20: 0.346 (0.044 to 0.679)
- **Mean-imputed share** (live cells that drew a NaN row in the shuffle and were
  set to 0.0), measured by replaying the shuffle on the real weekly panel with a
  scratch script that prints counts only: 69,175 live cells (990 rows x 95
  holdables). Per seed 7,866 to 16,150, i.e. **10.4% to 23.4%, mean 19.5%**.
  Below the ~25% stop line for every seed, but the top of the range is close.
- **Worst single instrument: 100%.** One series (column index 10, 332 live rows of
  990) has every live row imputed under at least one seed, so at that seed its
  baseline carries no shuffled truth, only noise. Not a stop condition as written
  (the line is on the overall share), but it says the late-starting series are
  where the baseline departs most from its live twin.
- Plumbing: `_write_baseline_run` ran end to end on real data for the first time
  and wrote `cells.csv` and `summary.json` without error. Neither digest step
  nor the run surfaced any problem; the digest's own summary is in `digest.md`.
- The imputation share is not persisted by the run; the scratch script is in the
  session scratchpad, not the repo.

### 2026-09-21 — task 20, re-specified as the knee grid (Claude Code, Sonnet 5)

**20. Live + baseline at IC 0.35, 0.50, 0.70** — rc=0. `457b5e8` audit: the
knee grid. `scripts/unattended.sh audit-knee --digest` at `457b5e8`: check
rc=0 (274 s), audit rc=0 (**3205 s, ~53 min**), run **`A-20260922-005316`**, 60
cells, h13, ten seeds (`results/audit/_unattended/20260921-204838-audit-knee/`).
- **Both hashes match** `A-20260919-155557` and `A-20260921-202607`:
  `panel_hash` `dfbf5c5a…5793`, `params_hash` `ebdfb70e…b77c`. The pairing is
  valid.
- Per rung (live mean, baseline mean, excess mean, excess SE, n=10 seeds):
  - IC 0.35: live 0.390, baseline 0.295, **excess 0.095, SE 0.035**
  - IC 0.50: live 0.473, baseline 0.361, **excess 0.111, SE 0.016**
  - IC 0.70: live 0.535, baseline 0.326, **excess 0.209, SE 0.018**
- Excess is positive and several SE from zero at every rung, growing with IC.
- Not asked for, flagged anyway: `risk_calibration` fails on 28 of 60 cells
  (`bias_worst_annual` 1.726-2.036 against the 1.72 ceiling), concentrated in
  seeds 0, 1, 3, 5, 6, 7 across all three rungs, live and baseline both. Net IR
  and the excess above are unaffected by this veto (it's ex-post risk
  calibration, not a return figure), but it is the one ex-post gate in
  SUBSTRATE and it is failing on nearly half this grid.
- `params/audit.yaml` untouched; `params_hash` unmoved confirms it.

### 2026-09-21 — task 22 (Claude Code, Sonnet 5)

**22. `decisions/0035` s4(a), s4a and s5** — rc=0. `d8f70ef` audit: the
corrected transfer coefficient and its baseline. `scripts/unattended.sh check
--digest` at `457b5e8` + the working tree: **rc=0, 350.7 s, 483 tests** (479 +
4 new: `baseline_weights`, the corrected-TC acceptance test, the r2-floor
test), governance OK, ruff clean, holdout lock 15/15
(`results/audit/_unattended/20260921-215621-check/`).
- **s4, the corrected estimator.** All three estimators now compute on
  `w - w_baseline` (`w_baseline` = the leg-weighted sum of each benchmark leg's
  NNLS tracking portfolio, `portfolio/covariance.py`'s existing `.legs[leg]`
  diagnostics). `w_active` substitutes for `w` everywhere `coefficients()` used
  it, not just the numerator, since a partial substitution still divides by
  the replication-dominated total variance. **Acceptance test, as specified:**
  a book built from `w_baseline` plus the unconstrained optimum's own tilt
  reads TC **1.0** (to 1e-6, `pytest.approx`); a book tilted orthogonal to its
  own alpha reads **0.0** (to 1e-6). Both run on a real NNLS-embedded synthetic
  universe (trimmed, 14 series), not hand-built matrices.
- **s4a, the NNLS r2.** Surfaced as `nnls_r2_<leg>` / `nnls_residual_variance_<leg>`
  on every cell and in `ruler.md`/`ruler.html`'s transfer-coefficient section.
  **On a real Bloomberg base cell (IC 0.10, h13, seed 0), r2 is 0.9998601801189837
  for NDUEACWF and 0.9996685999818131 for LEGATRUU — both far above the 0.90
  floor.** Not a stop condition. A test asserts a 0.90 floor on the synthetic
  legs (spannable by construction, so a breach there is a real regression).
- **s5, persistence.** Weights, alpha and the rebalance-date index for every
  base cell, as parquet under `results/artifacts/<run_id>/<cell key>/`.
  **Measured disk cost: 0.86 MB for one real Bloomberg base cell** (94
  holdable series, 834 dates; two files, weights + alpha). The standard grid
  has 160 base cells, so a full run's artifacts are **roughly 137 MB**,
  extrapolated from one cell, not measured on a full run. Not committed to
  git (results/artifacts/ is regenerable, per SUBSTRATE section 11); confirmed
  via a scratch smoke test on the synthetic lean grid (4 base cells, 3.6 MB)
  and the one real cell above.
- **Beyond the stop rule, an open finding, not a stop condition:** the real
  IC = 1 oracle cell's corrected TC does **not** read near ceiling (full
  0.022, diagonal 0.029 -- close to the OLD estimator's 0.039-0.042), even
  though the estimator recovers 1.0 exactly on the constructed acceptance
  case. Traced one date: the solved book `w` and its NNLS baseline
  `w_baseline` are nearly orthogonal in raw weight space (cos 0.011), and
  `alignment` barely moves under the correction (8th decimal), consistent
  with `w_baseline` sitting close to the min-active-variance portfolio in
  Omega's own metric -- 0035 s3's subtlety, now observed rather than argued.
  This is the open question 0035 s7 already named ("the two are the same
  investigation and neither settles first"); it does not block this task, and
  no re-run of `A-20260919-155557` was authorised or attempted.
- `params/` untouched.

### 2026-09-22 — task 19 (Claude Code, Sonnet 5)

**19. The full baseline grid** — rc=0. `scripts/unattended.sh audit-baseline
--digest` at `941a799`: check rc=0 (283 s), audit rc=0 (**32912 s of reported
elapsed time, but see below**), run **`A-20260922-033647`**, 160 cells, four
horizons, ten seeds (`results/audit/_unattended/20260921-233203-audit-baseline/`).
- **Both hashes match** `A-20260919-155557`, `A-20260921-202607` and
  `A-20260922-005316`: `panel_hash` `dfbf5c5a…5793`, `params_hash`
  `ebdfb70e…b77c`.
- **Not actually 9.1 hours of audit compute.** The log shows 160 cells at the
  usual 40-90s each, except cell 121 (`ic0.02_h52_s0`), which reports
  **23,625.1s (6h 34m)** on its own. The machine (or WSL) slept overnight
  between cells 120 and 121; the process resumed and finished normally, and
  every cell before and after ran at the expected pace. True audit compute is
  close to task 18's per-cell rate (~50-70s), i.e. roughly **2.5-3 hours**, not
  the 9.1 hours the wall clock reports. Net IR is unaffected -- this is only a
  timing artifact.
- Baseline `net_ir` by horizon and IC rung (mean, seed min-max, n=10):

  | h | IC 0.02 | IC 0.05 | IC 0.10 | IC 0.20 |
  |---|---|---|---|---|
  | 4  | 0.299 (-0.200 to 0.620) | 0.306 (-0.062 to 0.669) | 0.228 (-0.036 to 0.500) | 0.314 (-0.025 to 0.525) |
  | 13 | 0.290 (-0.369 to 0.589) | 0.321 (-0.605 to 0.798) | 0.277 (-0.101 to 0.677) | 0.346 (0.044 to 0.679) |
  | 26 | 0.304 (-0.345 to 0.668) | 0.304 (-0.402 to 0.806) | 0.467 (-0.076 to 0.820) | 0.295 (-0.087 to 0.511) |
  | 52 | 0.363 (-0.164 to 0.619) | 0.348 (-0.168 to 0.618) | 0.321 (-0.269 to 0.967) | 0.250 (-0.162 to 0.710) |

- Every rung's mean sits in the 0.23-0.47 band, in line with the h13 rungs
  task 18 and task 20 already measured; no horizon shows the floor collapsing
  or escaping that range.

### 2026-09-22 — task 23, STOPPED before the vendor call (Claude Code, Sonnet 5)

**23. JPMaQS catalogue check** — rc=1 (stopped, not a failure of the code).
`bb4db0b` scripts: the JPMaQS catalogue check.
- **Step 1, the extra:** `uv sync --group dev --extra jpmaqs` installed
  `macrosynergy==1.8.1` and its deps into the shared venv. `pyproject.toml`
  already declared the `jpmaqs` extra, so nothing else changed (`uv.lock`,
  `pyproject.toml` both untouched). `make check` afterward: **rc=0, 483
  tests, 317.5 s**, governance OK.
- **Step 2, the script and target:** `make jpmaqs-catalogue` wraps
  `scripts/jpmaqs_catalogue_check.py`, constructed with
  `check_connection=True` as specified.
- **Step 3, confirmed before any call:** the 27 rows tagged `genuine
  phase-3 gap` in `data/requests/ticker_resolution.csv` are 8 cids x 12
  xcats; `cross_product_size()` confirms the cross product is **96**, as
  expected.
- **Stopped at credentials.** `DQ_CLIENT_ID` and `DQ_CLIENT_SECRET` are not
  set in this session's shell (`env | grep -c DQ_CLIENT` reads 0 -- a count,
  not a value, and `.env` itself was never opened, per the task's own hard
  limit). `JPMaQSLoader.credentials()` raised before any network call was
  attempted, so this is a credentials gap in this session, not a rejection
  from the vendor. Per the task's stop rule for a network/auth failure, this
  stops and reports rather than sourcing `.env`, exporting the values myself,
  or working around the check.
- **Not obtained:** the catalogue size, how many of the 27 resolve, and
  whether `request.txt` was written. `data/raw/jpmaqs_catalogue.json` and
  `data/requests/jpmaqs_catalogue_check.csv` do not exist.
- Needs Cowork/owner: either export `DQ_CLIENT_ID`/`DQ_CLIENT_SECRET` in the
  shell this session runs in, or run `make jpmaqs-catalogue` directly where
  the credentials are already exported.

### 2026-09-22 — task 23, continued: the vendor call itself (Claude Code, Sonnet 5)

**23, continued.** Credentials were exported by the owner directly into a
single shell invocation (`source .env` immediately before the script, never
read by me) and the check was run for real. **rc=1, stopped by the script's
own stop rule -- not a code failure.**
- First attempt used a bare `uv run --python 3.12 --group dev ...` (my
  mistake) rather than `make jpmaqs-catalogue`, so `UV_PROJECT_ENVIRONMENT`
  was unset and it fell back to a fresh local venv without `macrosynergy` --
  exactly the bare-`uv run` failure mode CLAUDE.md warns about. Corrected to
  `make jpmaqs-catalogue`, which sets it via `build.mk`.
- With the right venv: connected, confirmed **27 named tickers, cross
  product 96**, then `JPMaQSDownload(check_connection=True)` failed:
  **`AuthenticationError: 401 Client Error: Unauthorized for url:
  https://authe.jpmchase.com/as/token.oauth2`**.
- This reached the vendor's own auth host directly (no proxy, matching
  `params/data_sources.yaml`'s `proxy.enabled: false` for a personal
  machine) and got a real response, so it is a credentials rejection, not a
  network/resolution problem. Per the task's stop rule, the proxy setting
  was not varied and no alternate host was tried.
- **Nothing was written.** No catalogue cache, no
  `jpmaqs_catalogue_check.csv`, no `request.txt`; `git status` confirms no
  new files from this attempt.
- Needs Cowork/owner: the credentials in `.env` (`DQ_CLIENT_ID` /
  `DQ_CLIENT_SECRET`) are being rejected by the vendor's token endpoint --
  worth checking whether they are current, correctly paired, or need
  reissuing, before task 23 is retried.

### 2026-09-22 — task 23, the 401 explained (owner's own test, not run here)

Not a Claude Code run -- the owner tested the same `DQ_CLIENT_ID`/
`DQ_CLIENT_SECRET` from a work machine, outside this session, and got a
clean auth success (`check_connection=True`, no proxy). This resolves the
open question from the two receipts above:
- **The credentials are valid.** The 401 this session saw was not a bad or
  expired client_id/secret.
- **It is network-origin, not proxy-credential.** The owner's successful
  test also used `proxy=None` -- so the difference between the two attempts
  is which network the request originated from, not whether it went through
  Itaú's authenticated proxy. DataQuery's auth endpoint appears to only
  accept these credentials from Itaú's network.
- **This session cannot finish task 23.** It runs on the same personal
  machine that got the 401, and nothing here can route it onto the
  corporate network. The vendor call (`make jpmaqs-catalogue`) needs to run
  from a machine on that network, with `.env` present there. Once it is, the
  script and target already exist and are unchanged from the earlier
  receipts (`bb4db0b`).

### 2026-09-22 — task 21 (Claude Code, Sonnet 5)

**21. Remove the parked lock file** — rc=0. `.git/index.lock.stale-cowork-20260920`
was present (0 bytes, from 2026-09-20). Confirmed `.git/index.lock` itself did
not exist and no git process was running before removing. Deleted.

### 2026-09-23 — task 23, completed (Claude Code, Sonnet 5)

**23. JPMaQS catalogue check — a real result.** rc=1 (the script's own stop
rule, not a failure). Owner ran `set -a; source .env; set +a; make
jpmaqs-catalogue` directly, with a corrected `DQ_CLIENT_SECRET` (the two
earlier stops in this file -- credentials not present, then a 401 -- are
superseded; the 401 really was a bad secret, not the network-origin
explanation offered in between, since the fix alone made this machine
succeed).
- **Auth succeeded** (no proxy, this machine, the one that gave the earlier
  401). Downloaded the JPMAQS catalogue: **31,728 tickers**, cached at
  `data/raw/jpmaqs_catalogue.json` (git-ignored, not committed).
- **27 named tickers, cross product 96** (8 cids x 12 xcats), confirmed
  before the call, as before.
- **12 of 27 did NOT resolve:**
  `USD_INTRGDP_NSA_P1M1ML12_D1M1ML3`, `EUR_INTRGDP_NSA_P1M1ML12_D1M1ML3`,
  `JPY_INTRGDP_NSA_P1M1ML12_D1M1ML3`, `GBP_INTRGDP_NSA_P1M1ML12_D1M1ML3`,
  `USD_UNEMPLRATE_SA_D1Q1QL4`, `USD_BLSDCLN_SA_D1Q1QL1`,
  `EUR_BLSDCLN_SA_D1Q1QL1`, `USD_MBASEGDP_SA_D1M1ML12`,
  `USD_RM1GDP_SA_D1M1ML12`, `EUR_RM3GDP_SA_D1M1ML12`,
  `USD_GB10YXGB_NSA`, `EUR_GB10YXGB_NSA`.
- **Per the stop rule: not substituted, not guessed, not dropped.**
  `data/requests/jpmaqs_catalogue_check.csv` was written (27 rows, all
  findings). `data/jpmaqs/request.txt` was **not** written -- confirmed by
  `git status` (no such file) -- since not all 27 resolved.
- Needs the owner: the same `decisions/0032` precedent this task's stop rule
  cites -- these 12 xcats or cid/xcat combinations are either misnamed
  (worth a hand check against the JPMaQS documentation) or genuinely absent
  from the vendor's catalogue, and only the owner decides whether to drop,
  rename or wait on them.

### 2026-09-23 — tasks 26 and 27 built, STOPPED on the check (Claude Code, Opus 5.5)

**Step 0 done:** `19c16be` commits Cowork's queue (tasks 26-27, run-order note,
OWNER-QUEUE L14). **Nothing else is committed.** Tasks 26 and 27 stay in the
queue because the check did not pass.

**What is built (uncommitted, in the working tree):**
- **26:** new `src/signal_lab/loaders/env.py` (`check_secret`) **refuses**
  leading or trailing whitespace, CR/LF, and control characters (`ord < 32`,
  127). The error names the variable and the defect only. Used by
  `JPMaQSLoader.credentials()`, by `JPMaQSLoader.proxies()` (`PROXY_PWD`) and by
  `FredLoader.api_key()`. New `tests/test_jpmaqs_credentials.py` has 8 tests, and
  they pass on their own.
- **27:** new `scripts/jpmaqs_candidates.py`, `make jpmaqs-candidates` in
  `build.mk`, and `tests/test_jpmaqs_candidates.py` (7 tests, hand-written
  fixture), passing on their own. **Not run against the cache yet**, so
  `data/requests/jpmaqs_candidates.csv` does not exist.

**The check, run twice:**
- `20260923-172023-check`: **rc=2, 52 s**, lint only. `ruff format` read
  `scripts/jpmaqs_candidates.py` while this session was still writing it. My
  own race; the file was formatted before the second run.
- `20260923-172145-check`: **rc=2, 829 s, 496 passed, 2 failed.** Governance
  OK and ruff clean. Both failures are in `tests/test_scripts.py`
  (`test_nightly_cycle_records_blocked_not_a_fake_veto_failure`,
  `test_the_cycle_records_the_specific_blocked_reason`):
  `OSError: [Errno 22] Invalid argument: .../data/requests/H-2026-0011.yaml`
  from `write_data_request` (`harness/hypotheses.py:411`). **Both pass when
  run alone** (2 passed, 6 s), so the failure is intermittent. EINVAL on a
  `/mnt/c` write usually means something on the Windows side had the file
  open.
- **The real defect it exposes:** these two tests pass `tmp_path` for the
  snapshot and the store, but `triage` writes data requests to the **real**
  `data/requests/`, so every `make check` rewrites the tracked
  `H-2026-00xx.yaml` files. Contents are unchanged this time (`git status`
  clean for `data/requests/`), but the tests are not isolated from the repo.
  Neither failure is in code tasks 26 or 27 touch.

**Needs Cowork:** either a task to point those tests' requests directory at
`tmp_path` (my suggestion, since it removes the exposure), or an
instruction to re-run the check as-is. Task 25 is not started. I read it and
planned the change, but nothing is edited.

### 2026-09-23 — tasks 28, 26 and 27 (Claude Code, Opus 5.5)

**Check:** `scripts/unattended.sh check --digest` with all three in the tree:
**rc=0, 733 s, 499 passed** (`results/audit/_unattended/20260923-174720-check/`).
One run, no retry.

**28. Cycle tests isolated.** Committed as `2aebc87`. `nightly_cycle.py --requests-dir`
defaults to `data/requests/`, so a real run is unchanged. Grepping found four
`cycle.main` calls, and all four now pass it, including the tampered-snapshot
test. Triage writes requests **even under `--dry-run`**, so the rule "only
calls without `--dry-run`" would have missed some. The new
`test_a_cycle_run_by_a_test_leaves_the_real_registry_and_requests_untouched`
passes: it compares mtimes and hashes of `data/requests/` and `hypotheses/`
before and after. The `test_hypotheses.py` registry tests on the real root only
read, so they were not changed.
- **Task 16's question:** a synthetic `--dry-run` triage into a temp dir writes
  11 request files, and **all 11 are byte-identical to the committed `HEAD`
  blobs**. So a synthetic triage does reproduce them, which points to `make
  check` as what rewrote the six files task 16 found. Hand edits are unlikely.

**26. Malformed secrets refused.** Committed as `46c4969`. The loaders using
`check_secret` (`loaders/env.py`) are JPMaQS `credentials()`, JPMaQS
`proxies()` (`PROXY_PWD`) and FRED `api_key()`.
`tests/test_jpmaqs_credentials.py` has 8 tests.

**27. Candidate names.** Committed as `a6a0218`; the CSV is committed with this
receipt. `make jpmaqs-candidates` rc=0 wrote 69 rows to
`data/requests/jpmaqs_candidates.csv`. **No ticker hit the 40 cap.** Candidate
counts and match levels: `INTRGDP_NSA_P1M1ML12_D1M1ML3` x USD/EUR/JPY/GBP 5
each, stem. `USD_UNEMPLRATE_SA_D1Q1QL4` 26, stem. `BLSDCLN_SA_D1Q1QL1` x
USD/EUR 4 each, **relaxed**. `USD_MBASEGDP_SA_D1M1ML12` 4, stem.
`USD_RM1GDP_SA_D1M1ML12` **0, none**. `EUR_RM3GDP_SA_D1M1ML12` **0, none**.
`USD_GB10YXGB_NSA` 8, **relaxed**. `EUR_GB10YXGB_NSA` **0, none**. Nothing
ranked or chosen.

### 2026-09-23 — task 25 built; the audit not yet run (Claude Code, Opus 5.5)

**Build done, audit pending.** `61c53a0` adds the `score` shuffle mode,
`score_shuffle_rng(seed, perm)`, `AuditCell.shuffle`/`perm` (key suffix
`_baseline_score_pNN` only for score cells), the `power` grid (80 cells),
`make audit-power` and the `unattended.sh` whitelist. `params/` is untouched.
The review doc `claude/detection-threshold-review-2026-09-22.md` is a Cowork
project doc and not in the repo, so it was not read.
- `scripts/unattended.sh check --digest`: **rc=0, 1012 s, 506 passed**
  (`results/audit/_unattended/20260923-180524-check/`).
- **The bit-for-bit test passes.** New golden tests pin the truth shuffle's
  score hash and `baseline_rng` stream as recorded before the change, and both
  pass.
- A smoke run of the new summary against `A-20260922-005316`, using fake shuffled
  IRs, found all four live twins and **both hashes matching**. The real match is
  re-checked by the audit itself.
- `audit-power` was launched at 18:23 and **stopped by hand during its opening
  `make check`**, before any cell ran, because the owner needed to put the machine
  to sleep. Nothing was written to `results/audit/` by it. **Next:**
  `scripts/unattended.sh audit-power --digest`, then the receipt task 25 asks for.

### 2026-09-24 — task 25, the power audit (Claude Code, Opus 5.5)

**25. `scripts/unattended.sh audit-power --digest`: rc=0.** Opening `make check`
rc=0 in 718 s. The audit took **9580 s**, against 80 minutes estimated: most cells
took about 105 s, and 7 took 300-450 s. Run **`A-20260924-194115`**, 80 cells,
all `score` shuffle, at commit **`61c53a0`**. Logs are in
`results/audit/_unattended/20260924-152915-audit-power/`.
- **Hashes: both match `A-20260922-005316`.** `panel_hash` `dfbf5c5a...`,
  `params_hash` `ebdfb70e...` (unchanged).
- **The bit-for-bit test passes** (part of the opening check, and of
  `20260923-180524-check`).
- The live twins are that run's base cells `ic{0.35,0.70}_h13_s{0,1}_c1.0_tnone_rnone`,
  checked by hand against its `cells.csv`.

| IC | seed | live net IR | shuffled mean | shuffled sd | live rank of 21 |
|---|---|---|---|---|---|
| 0.35 | 0 | -0.021 | 0.264 | 0.144 | 20 |
| 0.35 | 1 | 0.500 | 0.384 | 0.192 | 6 |
| 0.70 | 0 | 0.091 | 0.301 | 0.203 | 20 |
| 0.70 | 1 | 0.722 | 0.386 | 0.148 | 1 |

Rank 1 is the highest. The full rows are `power_by_cell` in the run's
`summary.json`. Interpretation is left to Cowork and the owner. The unattended
digest has further observations, not repeated here.

### 2026-09-24 — task 29 (Claude Code, Sonnet 5)

**29. Names-only catalogue search for H-2026-0004, 0005, 0010** — rc=0.
- `scripts/unattended.sh check --digest`: **rc=0, 512 passed, 1420 s** (`20260924-225939-check`; an earlier run failed only `ruff format` on my two new files, fixed). `make jpmaqs-name-search` rc=0, 151 rows.
- H-2026-0001 cache membership: **7 of 7 resolve** (cache test, not the vendor check).
- `n_matches`, cap (60) not hit anywhere: 0004 USD|EUR `BLS` 16; 0010 `GB10Y` (DEM,FRF,ITL,ESP,NLG,EUR,USD) 40; 0010 `GB10YCRY` all cids 28, on 14 cids (ATS AUD BEF DEM ESP FIM FRF GBP IEP ITL JPY NZD PTE USD); 0005 USD|EUR: `MBASE` 8, `MBROAD` 8, `MNARROW` 8, `M1` 0, `M2` 0, `M3` 0, `RM` 16, `INTLIQ` 6, `PCREDIT` 18.
- Nothing ranked or recommended; renaming/dropping/holding is OWNER-QUEUE L14. Commit hash: see `git log` (message `handoff: task 29`).

### 2026-09-26 — task 30 (Claude Code, Sonnet 5)

**30. `score_span` and the 10-seed power grid** — rc=0. Run **`A-20260926-161749`**, 200 cells, 20019 s of wall clock (one cell took 4867 s: the machine slept; the ~95 s cells are the real cost).
- Commits: queue `21ab064`; `score_span` + `power10` `a7f92db`; preflight fix `84cc804`. `scripts/unattended.sh audit-power10 --digest` at `84cc804`: check **rc=0, 426 s**. A first attempt at `a7f92db` stopped at my own preflight (`KeyError: 'shuffle'`, the knee run's `cells.csv` predates that column) **before any cell**; fixed, tested, relaunched.
- **Hashes match** `A-20260922-005316`: panel `dfbf5c5a...5793`, params `ebdfb70e...b77c`. All ten seeds' live and truth-twin cells were present (checked before any cell ran). `params/` unchanged.
- Bit-for-bit: `score` mode reproduces its pre-change hash and RNG stream; live, truth-shuffle and `score` keys unchanged; new key `_baseline_scorespan_pNN`. Tests: 34 in `tests/test_baseline.py`, all passing. **The truth shuffle has the same re-masking by construction and was left unchanged.**
- **Slope diagnostic** (synthetic 991 x 95, 20 late starters, 4 (IC, seed) x 20 perms; slope of shuffled column means on live, mean (min-max), corr): full-history `score` 0.81 (0.71-0.91) corr 0.93 -> `score_span` **1.00 (1.00-1.00) corr 1.00**; late-starting `score` 0.58 (0.36-0.91) corr 0.76 -> `score_span` 0.76 (0.48-0.96) corr 0.86. Alpha-mean slopes: full 0.80 -> 0.98, late 0.61 -> 0.77. The script is not in the repo (scratchpad).
- **Per seed (IC 0.70, h13):** live net IR / truth-twin / `score_span` mean +- sd of 20 / live rank of 21:
  s0 0.091 / -0.086 / 0.241 +- 0.151 / 17; s1 0.722 / 0.491 / 0.328 +- 0.139 / 1; s2 0.633 / 0.445 / 0.286 +- 0.143 / 1; s3 0.558 / 0.346 / 0.315 +- 0.168 / 3; s4 0.548 / 0.425 / 0.359 +- 0.173 / 5; s5 0.436 / 0.130 / 0.296 +- 0.146 / 4; s6 0.325 / 0.192 / 0.234 +- 0.167 / 7; s7 0.679 / 0.445 / 0.297 +- 0.200 / 2; s8 0.597 / 0.395 / 0.155 +- 0.212 / 1; s9 0.760 / 0.480 / 0.289 +- 0.166 / 1.
- **Pooled sd** across seeds 0.168 (rms of per-seed sd; sd of all 200 cells 0.173). **Seeds ranking 1 of 21: 4 of 10** (5 of 10 within the top 2).
- **Shuffled cells' pooled realised IC:** 0.065 on average = **0.093 x the planted 0.70** (was ~0.12 under `score`); live twins 0.700.
- **Turnover, for OWNER-QUEUE B3 (reported, not judged):**
  - 200 shuffled cells: annual turnover above 400% in **0**, median 338%, max 355%; rolling one-year (max over the history) above 400% in **200**, median 522%, max 612%; rolling p95 above 400% in 200, median 461%, max 514%.
  - 10 live twins: annual above 400% in **0**, median 318%, max 331%; rolling max above 400% in **10**, median 498%, max 546%; rolling p95 above 400% in 10, median 437%, max 475%.
- Also seen: `risk_calibration` fails 67 of 200 shuffled cells and 4 of 10 live twins.

### 2026-09-28 — task 31 (Claude Code, Sonnet 5)

**31. Apply the owner's L14 renames, then the vendor check** — rc=0.
- Commits: queue `2448f52`; renames `acd02f6`; vendor-check outputs `7ce2dff`.
- Renames applied as the owner ruled (OWNER-QUEUE L14, "recs on all"), recorded
  as the 2026-09-27 addendum to `decisions/0032`: 0004's `BLSDCLN` (demand)
  legs -> `BLSCSCORE_NSA_D2Q2QL2` (standards, entered negated), FRED
  `DRTSCILM` dropped; 0005's `MBASEGDP`/`RM1GDP`/`RM3GDP` -> two
  `RMBROAD_SJA_P1M1ML12` legs (`MBASEGDP` dropped outright); 0010's
  `GB10YXGB` -> `GB10YCRY` (term spread re-specified as carry), EUR leg
  becomes `DEM_`. `src/signal_lab/harness/hypotheses.py`'s `DRTSCILM` mention
  is a generic vendor-prefix hint table, not a request or series list; left
  unchanged.
- `scripts/unattended.sh check --digest` at `acd02f6`: **rc=0, 1928 s.**
- **Vendor call stopped once, then succeeded, both outside my own Bash.**
  `DQ_CLIENT_ID`/`DQ_CLIENT_SECRET` were not in my shell's environment (same
  gap as task 23); I would not source `.env` or export them myself. The owner
  ran `source .env && make jpmaqs-catalogue` via the `!` channel -- same
  failure, because `.env`'s plain `KEY=value` lines aren't exported by a bare
  `source`. `set -a && source .env && set +a && make jpmaqs-catalogue`
  (guessed from the symptom, `.env` never read) then worked.
- **26 of 26 resolve** (27 registered minus 0005's one dropped leg;
  `data/requests/jpmaqs_catalogue_check.csv`). **`data/jpmaqs/request.txt`
  written for the first time**, 26 tickers.
- A second `make check` (also via the owner's `!` channel, at `acd02f6`,
  after `request.txt` existed, while my own Bash tool was down on a
  server-side classifier error for about 30 minutes) also **rc=0, 1928 s**.
- Noted, not fixed (out of task scope): `scripts/jpmaqs_catalogue_check.py`'s
  docstring and `request.txt`'s own header still say "27" in three places; the
  count is now 26 whenever a hypothesis is renamed off a `genuine phase-3
  gap` name onto a different one.
- Implementing `load_macro` and the pull itself are not part of this task, per
  its own stop rule.

**Commit-collision note, same session.** My first attempt to write this
receipt crashed mid-script (`HANDOFF.md` had changed under me -- Cowork had
concurrently added tasks 32 and 33 -- so a fixed-offset string replace no
longer matched and raised before writing). The `git add HANDOFF.md && git
commit` that followed in the same tool call still ran and committed whatever
was on disk at that point, which was Cowork's queue edit (tasks 32, 33, and
a "receipt pending" placeholder for this one), under a commit message
(`ab59120`) that claims to be this receipt but contains none of it. That
commit's content is legitimate (it is Cowork's own queue addition) but its
message is wrong. This commit supplies the actual receipt. `OWNER-QUEUE.md`
and `decisions/0038-turnover-is-disclosed-not-vetoed.md` are still uncommitted
in the working tree; task 33 step 0 asks for those with `HANDOFF.md` together,
and I have not touched them. Tasks 32 and 33 are not started.

### 2026-09-28 — task 32 (Claude Code, Sonnet 5)

**32. The friction sweep: shadow-cost coefficient at 10, 20, 40 bp** — rc=0.
Run **`A-20260928-151055`**, 60 cells, 5214 s (`~87 min`). Commit `81ed2a1`.
`scripts/unattended.sh audit-friction --digest`: check rc=0 (659 s), grid rc=0.
Queue commits (out of order, see the note above under task 31): `ef6c3f5`
(OWNER-QUEUE.md for 32-33), `96d9748` (decisions/0038, 0039; queue 32-34).

- **Hashes match** `A-20260922-005316`: panel `dfbf5c5a...5793`, params
  `ebdfb70e...b77c`. `params/` unchanged.
- **10 bp arm identical to the knee run, cell by cell, all 20 (ic, seed)
  pairs found.** Max `|diff|` in net IR: **8.3e-17** (floating-point noise,
  not a difference). `shadow_coefficient=None` and `=10.0` are the same code
  path with the same result.
- **Per (IC, coefficient), median [min, max] over 10 seeds:**

  | IC | bp | net IR | cost drag | turnover ann. | turnover roll-1y max | TE p95 | realised IC |
  |---|---|---|---|---|---|---|---|
  | 0.35 | 10 | 0.470 [-0.021, 0.618] | 0.453% [0.432, 0.466] | 244% [238, 251] | 390% [354, 418] | 7.94% [7.24, 8.53] | 0.350 |
  | 0.35 | 20 | 0.311 [0.126, 0.784] | 0.389% [0.364, 0.395] | 185% [180, 203] | 297% [268, 309] | 7.48% [6.69, 8.64] | 0.350 |
  | 0.35 | 40 | 0.386 [0.230, 0.920] | 0.358% [0.328, 0.393] | 160% [148, 167] | 237% [224, 282] | 7.72% [7.25, 8.44] | 0.350 |
  | 0.70 | 10 | 0.577 [0.091, 0.760] | 0.560% [0.529, 0.583] | 318% [314, 331] | 498% [461, 546] | 8.16% [7.26, 8.81] | 0.700 |
  | 0.70 | 20 | 0.570 [0.203, 0.820] | 0.457% [0.438, 0.476] | 232% [226, 240] | 362% [330, 386] | 7.58% [7.01, 9.01] | 0.700 |
  | 0.70 | 40 | 0.446 [0.201, 0.950] | 0.395% [0.364, 0.418] | 182% [176, 192] | 262% [255, 298] | 7.49% [6.99, 9.09] | 0.700 |

- **Paired by seed, net IR at 20/40 minus net IR at 10** (mean, sd, n
  positive of 10):
  - IC 0.35, 20bp: -0.015, sd 0.214, 5 positive. IC 0.35, 40bp: +0.066, sd
    0.264, 6 positive.
  - IC 0.70, 20bp: +0.039, sd 0.171, 6 positive. IC 0.70, 40bp: -0.068, sd
    0.178, 4 positive.
  - No coefficient dominates on net IR at either rung; each is inside 1 sd
    of zero on a 10-seed sample.
- **Counts above 200% (OWNER-QUEUE B3's new highlight level), out of 10
  seeds per arm:**
  - Annual: IC 0.35 -- 10bp: 10, 20bp: 1, 40bp: 0. IC 0.70 -- 10bp: 10,
    20bp: 10, 40bp: 0.
  - Rolling one-year max: **10 of 10 in every one of the 6 arms**, including
    at 40 bp.
- **`risk_calibration` fails per arm** (out of 10): IC 0.35 -- 10bp: 6,
  20bp: 3, 40bp: 3. IC 0.70 -- 10bp: 4, 20bp: 1, 40bp: 4. Friction lowers
  turnover monotonically but does not lower `risk_calibration` failures
  monotonically.
- Friction cuts turnover roughly in half from 10 to 40 bp at both rungs, and
  the shadow cost was clearly not holding turnover near its 100% reference at
  10 bp (task 30's finding). It does not clear the rolling-window highlight
  at any coefficient tested here.

Interpretation is Cowork's and the owner's. Stopped per the task's own
instruction; task 33 not started.

### 2026-09-28 (night) — task 34 (Claude Code, Sonnet 5)

**34. Multiple-testing module, then the FDR-vs-FWER Monte Carlo** — rc=0.
`scripts/unattended.sh check --digest`: **rc=0, 546 tests, 1206 s.** Commits:
`566a33f` (step 0, decisions 0039/0040 and queue); `ed65436` (the module and
the study). `make fdr-study` at `ed65436`: **rc=0, 210 s**, run
`results/fdr_vs_fwer/20260929-031720/` (a second, identical run at 190 s
confirms it's deterministic under its seed).

- **`src/signal_lab/stats/multiple_testing.py`:** `holm`, `romano_wolf`
  (stepdown max-T, FWER), `benjamini_hochberg`, `benjamini_yekutieli` (step-up
  FDR), `marginal_pvalues`. All four tested against a hand-worked example
  (Holm and BY both reject only the smallest p on it; BH rejects the two
  smallest), independence and positive-dependence checks against Holm, and a
  1500-replication complete-null simulation keeping realised FWER/FDR within
  MC error of nominal. 12 tests, all passing.
- **`romano_shaikh_wolf_fdr` is NOT implemented.** The task's citation
  ("Romano, Shaikh & Wolf 2008, Econometric Theory 24(2)") is that pair's
  *k-FWER* paper ("Formalized data snooping..."), not their FDR-under-
  dependence result (a different paper, in *TEST* 17(3), same year). Without
  the source in hand to fix which stepdown construction and which open choice
  the paper makes, implementing either from memory risked shipping a
  plausible-looking but wrong procedure under a citation that claims fidelity
  it doesn't have. Per the task's own instruction, this stops rather than
  approximates; `holm`, `romano_wolf`, `benjamini_hochberg` and
  `benjamini_yekutieli` ship, tested, and the study's FDR side is BH and BY
  only.
- **The study is not the literal full cross product the task lays out, by a
  disclosed design choice** (stated in the script's own docstring and the
  report): the correlation grid, k grid and n_true/mu grid are fully crossed
  (140 scenarios), but the mu SWEEP (0.5-3.0, "for the curve") runs only at
  the headline correlation and k=1000 for n_true in {1,3,6} (15 more
  scenarios), not through the whole grid again. Also, (rho_w=0, rho_b=0.2) is
  skipped: it is not a valid equicorrelation structure (between-axis
  correlation can't exceed within-axis under the factor-model construction
  used), stated in both the script and `report.md`.
- **5,000 replications per scenario, every scenario**, not reduced anywhere —
  vectorising every procedure across replications
  (`src/signal_lab/stats/_batched.py`, pinned correct against the
  single-replication functions by 5 tests comparing row by row, including a
  case mixing rows that finish the stepdown at different rounds) is what
  keeps 155 scenarios x 5,000 replications to about 3.5 minutes rather than
  hours.
- **Headline tables, n_true=3, rho_w=0.3, rho_b=0.2, k=1000:**

  IC 0.35 (mu=0.565, s=1.149 — **s assumed, not separately measured at this
  IC**):

  | procedure | avg power | P(>=1 true passes) | FWER | FDR | mean false passes |
  |---|---|---|---|---|---|
  | Holm 5% | 0.034 | 0.095 | 0.033 | 0.029 | 0.037 |
  | Romano-Wolf 5% | 0.038 | 0.106 | 0.039 | 0.033 | 0.045 |
  | BH 5% | 0.043 | 0.106 | 0.047 | 0.033 | 0.065 |
  | BH 10% | 0.073 | 0.169 | 0.098 | 0.067 | 0.163 |
  | BY 10% | 0.026 | 0.067 | 0.024 | 0.017 | 0.032 |

  IC 0.70 (mu=1.518, s=1.149, both measured):

  | procedure | avg power | P(>=1 true passes) | FWER | FDR | mean false passes |
  |---|---|---|---|---|---|
  | Holm 5% | 0.160 | 0.372 | 0.038 | 0.023 | 0.041 |
  | Romano-Wolf 5% | 0.180 | 0.407 | 0.043 | 0.024 | 0.047 |
  | BH 5% | 0.198 | 0.391 | 0.074 | 0.035 | 0.101 |
  | BH 10% | 0.285 | 0.510 | 0.154 | 0.072 | 0.253 |
  | BY 10% | 0.146 | 0.300 | 0.042 | 0.020 | 0.054 |

- Romano-Wolf beats Holm at both ICs (0.038 vs 0.034 at IC 0.35, 0.180 vs
  0.160 at IC 0.70) by exploiting the positive dependence the equicorrelated
  null carries — the mechanism the task asked to measure. BH at q=10% roughly
  doubles power over Holm at both ICs, at 3-6x the false-pass rate.
- Full `summary.csv` (155 scenarios x 5 procedures = 775 rows) has every
  (rho_w, rho_b, k, n_true, mu) combination actually run, plus the mu-sweep
  curve rows.

`params/`, `vetoes/` and `SUBSTRATE.md` untouched — confirmed by
`git diff --cached --ignore-cr-at-eol --stat` before each commit. Interpretation
is Cowork's and the owner's (OWNER-QUEUE L16). Task 36 next, per the current
queue order (34 -> 36 -> 35).
