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

### 0. Commit this file and the pointer to it

`HANDOFF.md`, `OWNER-QUEUE.md` and the `CLAUDE.md` section that points at them
were written by Cowork and are uncommitted. They are the coordination
mechanism, so they should be in history before the queue is worked.

`OWNER-QUEUE.md` is the other half: decisions only Leo can make. **Never answer
an item in it.** You may add one, restate one, or move a closed one to its
`## Closed` section with the decision and date. If an item there says a
measurement would retire it and that measurement is queued below, say so in the
receipt.

    git add HANDOFF.md OWNER-QUEUE.md CLAUDE.md
    git commit -m "tooling: HANDOFF.md, the queue Cowork writes and Claude Code runs

Cowork can read this repo and write patches into it, but it cannot run make,
cannot run an audit, and must not run a git command that writes the index --
its sandbox cannot delete .git/index.lock, which blocks git in WSL. Until now
that work was handed over in an ad-hoc markdown file under results/, which is
the wrong place: results/ is untracked run output, and nothing told Claude Code
to look there.

HANDOFF.md is that queue at a fixed path, and CLAUDE.md now says to read it at
the start of every session. OWNER-QUEUE.md is its mirror for the owner:
judgements, risk appetites and governance signatures that no agent may answer. The contract is in the file: tasks in order with
the exact command, receipts appended to a Done section rather than tasks edited
in place, findings kept out, and no task treated as authorising an owner-only
change."

**Receipt should say:** the commit hash.

### 1. Apply the 0030 patch series

Six patches in `patches/0030-realised-te-characteristic/`, applying directly
onto `c0853d6`. Patch 0001 promotes `decisions/proposed/0030-…` to a decision
and leaves the already-committed `scripts/bias_map.py` alone, so there is no
prerequisite and nothing to delete first.

    git am patches/0030-realised-te-characteristic/*.patch

| # | subject | owner-only paths |
|---|---|---|
| 0001 | decisions: 0030 decided | — |
| 0002 | harness: the ex-ante TE reaches the veto set | — |
| 0003 | vetoes: risk_calibration replaces tracking_error | `vetoes/`, `params/vetoes.yaml` (cites 0030) |
| 0004 | substrate: sections 4 and 10 | `SUBSTRATE.md` (cites 0030) |
| 0005 | audit: the worst annual bias, and the verdict it decides | — |
| 0006 | audit: a risk-characteristics section | — |

Verified in the Cowork sandbox on the locked environment: applied clean with
`git am` onto a fresh clone at `c0853d6`, **446 tests pass**, ruff clean over
what `make check` lints, and every commit is individually green (441 at 0002,
443 at 0003 and 0004, 446 at 0005 and 0006).

If a patch fails to apply, stop and report which one and the conflict. Do not
resolve it by hand — the series was built from committed objects and a conflict
means the tree moved, which Cowork needs to know about.

`_superseded/` holds an earlier cut that assumed 0030 had not been committed.
Ignore it; the `*.patch` glob does not match it.

**Receipt should say:** the six commit hashes, or which patch failed.

### 2. Verify, then report

    scripts/unattended.sh check --digest

Expect **446 tests** and rc=0. `git am` does not run the commit-msg hook,
which is why `make governance` is part of `check` — confirm it reports no
uncited owner-only change.

**Receipt should say:** rc, runtime, test count, and the governance line.

### 3. One timed cell — decides whether the audit is 2 h or 9 h

`make check` took 417 s on 2026-09-18 against 1642 s on 2026-09-16, same
machine. Nobody knows why. The Cowork sandbox does an audit base cell in
16–21 s; the overnight WSL audit averaged ~85 s. If WSL is now at sandbox
speed, the 484-cell ten-seed audit is about 2 h rather than 8–11 h, which
changes how freely it can be rerun.

    time uv run --python 3.12 --group dev python scripts/te_path_probe.py \
      --run-id TE-timing-default --cells 0.05:13:9

    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      time uv run --python 3.12 --group dev python scripts/te_path_probe.py \
      --run-id TE-timing-1thread --cells 0.05:13:8

**Receipt should say:** both wall times. That is the whole deliverable — do
not change any default on the strength of it.

### 4. Ten seeds, then rerun the Bloomberg audit

Only after 1–3. Apply the ten-seeds patch, which carries `decisions/0028`:

    git am patches/0023-ruler-audit/0023-params-ten-seeds-per-audit-cell-decisions-0028.patch
    scripts/unattended.sh audit --digest

**A-20260917-020949 cannot be reformatted into the new shape** — its cells
carry no `bias_worst_annual`, so its verdicts are the old veto's. It has to be
rerun, not reprocessed.

The digest for this one matters more than usual: it is the first audit whose
surviving-cells bar is reachable, because `decisions/0030` removed the veto
that was failing 40 of 48 base cells. Follow the `Routine, unattended work`
section of `CLAUDE.md`, and add the two new columns: `bias_worst_annual`
against the 1.72 ceiling, and `bias_worst_year` — if the worst year is 2008 in
most cells, that is the expected shape and worth saying plainly.

---

## Not queued, deliberately

- **Turning the volatility overlay on.** It is opt-in code with no parameter
  reading it, tested at one horizon, two IC rungs and one halflife. Switching
  it on is an owner decision that does not exist yet.
- **`decisions/proposed/0029`.** Awaiting the owner. The recommendation on file
  is to take §1/§3/§4/§5 and defer §2 rather than tune a ridge to a target on
  the evaluation panel.
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
