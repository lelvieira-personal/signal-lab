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

Tasks **0-4 are complete**; their receipts are in `## Done` and the text as
issued is in git history (`033897e`, `7acd0a8`). The queue below starts at 5.

### 5. Commit the decision records and the resolution map

Four records and a map written by Cowork on 2026-09-18/19, plus the
`OWNER-QUEUE.md` and `HANDOFF.md` updates that carry the owner's rulings. All
untracked or modified, none in an owner-only path.

    git add decisions/proposed/0031-a-left-tail-check-for-h-2026-0007.md \
            decisions/proposed/0032-the-registry-tickers-against-the-real-panel.md \
            decisions/proposed/0033-measuring-the-transfer-coefficient.md \
            decisions/proposed/0034-a-data-required-name-must-resolve.md \
            data/requests/ticker_resolution.csv HANDOFF.md OWNER-QUEUE.md
    git commit -m "decisions: 0031-0034 and the ticker resolution map

0031 a left-tail calibration check for H-2026-0007, which lost both of the
checks it was registered against when 0026 dropped the active-drawdown gate and
0030 dropped the tracking-error veto. Decided: L = |q05(z)| / 1.645 is a
reported characteristic, not an eleventh veto.

0032 the registry's data_required against the panel that actually exists. 27 of
42 unresolved names are genuine JPMaQS gaps; the rest was bookkeeping. Two
tickers -- LUALTRUU and LT08TRUU -- do not exist and were removed rather than
substituted. The price-only concern raised in the first draft is withdrawn:
decisions/0013 had already settled it.

0033 measuring the transfer coefficient without rebuilding the frictionless
twin. breadth.implied_ic() has taken a transfer argument since it was written
and nothing has ever estimated it.

0034 a data_required name must resolve at registration -- the validator refuses
a fabricated citation and accepts a fabricated instrument. Proposed, not
decided.

data/requests/ticker_resolution.csv is the machine-readable map behind 0032."

**Receipt should say:** the commit hash.

### 6. Promote the three decided records out of `proposed/`

0031, 0032 and 0033 were decided by the owner on 2026-09-18/19; the rulings are
recorded in each file's header and in `OWNER-QUEUE.md`'s `## Closed`. **0034
stays in `proposed/`** -- it has not been decided.

    git mv decisions/proposed/0031-a-left-tail-check-for-h-2026-0007.md decisions/
    git mv decisions/proposed/0032-the-registry-tickers-against-the-real-panel.md decisions/
    git mv decisions/proposed/0033-measuring-the-transfer-coefficient.md decisions/
    git commit -m "decisions: 0031, 0032 and 0033 decided

0031: shape 1 -- L is a reported characteristic named in a dated addendum as
H-2026-0007's pre-registered check, gating nothing.

0032: price-only withdrawn; Europe stays sub-country and sector only; LUALTRUU
and LT08TRUU are fabricated and removed; H-2026-0010's term spread is LT01TRUU
against LT11TRUU; DRTSCILM joins the FRED request; H-2026-0007 takes the
six-segment quality ladder.

0033: TC gates nothing; the full-matrix estimator is the reported TC with the
diagonal and alignment forms alongside; implied_ic prints at both TC = 1 and
measured TC."

**Receipt should say:** the commit hash and that 0034 is still in `proposed/`.

### 7. Rebuild the coverage tables, so the stale column leaves

`decisions/0013` (2026-09-09) established that `likely_price_only` in
`bbg_index_coverage.csv` is a false positive from a naming heuristic, and asked
for it to be dropped at the next rebuild. `scripts/build_coverage.py` no longer
emits it and its docstring says so -- but the table on disk still carries the
column, because it has not been rebuilt since. It misled a Cowork session on
2026-09-18 into raising a decision that did not exist.

    make coverage
    make universe
    git diff --ignore-cr-at-eol --stat data/universe/

**Expect:** `bbg_index_coverage.csv` loses the `likely_price_only` column.
`investable_universe.csv` should be **unchanged in substance** -- the same 102
rows, the same 95 investable, the same tiers and cost buckets.

**STOP AND REPORT if the investable set, a tier or a cost bucket moves.** That
would mean the rebuild changed the universe rather than dropping a column, which
is a `decisions/0022` matter and not something to commit past. A test asserts
the committed table is what `build_universe` produces (`5501f54`), so `make
check` will catch it too -- but the diff is the cheaper read.

If the diff is clean:

    git add data/universe/
    git commit -m "data: rebuild the coverage table without likely_price_only

decisions/0013 resolved the column as a false positive from the coverage
script's naming heuristic and asked for it to be dropped at the next rebuild.
build_coverage.py stopped emitting it; the table on disk kept it, and a stale
artefact outlived the decision that retired it."

Then verify:

    scripts/unattended.sh check --digest

**Receipt should say:** the commit hash, whether anything but the column moved
in `investable_universe.csv`, and the check's rc, runtime and test count.

---

### 8. Commit the registry corrections (`decisions/0032`)

**The edits are already in the tree.** Cowork made them on 2026-09-19 in
`hypotheses/pending/`; nothing here needs authoring, only committing. Six files
changed, every change cited in the file's own `notes:` block:

| file | change |
|---|---|
| 0004 | `LUALTRUU` removed — does not exist |
| 0006 | `MXEF` → `M1EF` |
| 0007 | cross-section expanded to set A: `LUACTRUU`, `LUMSTRUU`, `I00183US`, `I00185US`, `I00188US`, `EMUSTRUU`, each with `INDEX_OAS_TSY` and its return series. `LUALTRUU` removed; `LF98TRUU` dropped, since it aggregates the Ba/B/Caa ladder |
| 0009 | `SPXT`, `MXEUG`, `NDDUUK`, `NDDUJN`, `M1EF`, `LUACTRUU`. Benchmark legs dropped — they live in `params/constraints.yaml` |
| 0010 | `LT08TRUU` → `LT11TRUU` (20+y), against `LT01TRUU` |
| 0011 | same regional correction, plus `GBP_EQCRR_NSA` so the UK equity leg has a UK real yield |

Verified by Cowork before handover: all 12 parse through `parse_hypothesis`,
`tests/test_hypotheses.py` is 33 passed, and every `data_required` entry now
resolves against the coverage tables except the 27 JPMaQS gaps and `DRTSCILM`,
which is real and joins the FRED request.

**Do not hand-edit `data/requests/*.yaml`.** `write_data_request()` generates
them from the registry; they regenerate on the next run against a manifest.

    git add hypotheses/pending/
    git commit -m "hypotheses: data_required against the panel that exists (decisions/0032)

The registry was written in phase 0 against plausible ticker names; the workbook
was mapped in phase 2 and carries different ones. 27 of 42 unresolved names are
genuine JPMaQS gaps. The rest was bookkeeping, and two names -- LUALTRUU and
LT08TRUU -- do not exist at all and are removed rather than substituted.

H-2026-0007's cross-section goes from four segments to six, at one level of
granularity, by owner ruling 2026-09-19 and before any result for it exists.
H-2026-0009 and H-2026-0011 take Europe at the sub-country level, so Europe has
two slots where the US and Japan have one; the risk decomposition discloses it.

The phase-0 names stay visible in history."

**Receipt should say:** the commit hash and the test count if you ran more than
the hypothesis module.

### 9. Implement `L` (0031) and the transfer coefficient (0033) — one series

**Write the code yourself; do not wait for a patch from Cowork.** The usual
route was Cowork building a verified series in its own sandbox. That sandbox is
gone: this Cowork session reaches the repo through a shell on Leo's machine with
a 180 s ceiling per call, and the suite takes longer than that, so Cowork can
verify a single test module in seconds but cannot prove a full series green.
Implementing from the spec here is strictly faster than a blind patch plus a
round trip. The specs are `decisions/0031` and `decisions/0033`, both decided.

**`L`, from 0031.** `L = |q05(z)| / 1.645` on the same standardised active
return `bias_worst_annual` already uses, `z_t = r_t / (sigma_ex_ante(t-1)/sqrt(52))`.
Reported per cell as a characteristic. **It gates nothing** — no eleventh veto.
The threshold comes from `scripts/bias_map.py`'s simulated null at the measured
kurtosis, at p99, and is not needed for this task.

**TC, from 0033.** Three estimators per cell: the full-matrix form
(`a'w / [sqrt(a' Omega^-1 a) sqrt(w' Omega w)]`, Clarke-de Silva-Thorley 2006
eq. 23) as the reported TC, the diagonal form for comparability, and
`corr(a, Omega w)` as the inversion-free control. Report the condition number of
`Omega` beside them. `implied_ic` prints at **both** TC = 1 and measured TC —
every prior audit printed the TC = 1 version and a silent change of meaning in
an append-only report is worse than a wider table.

**The migration that makes TC possible**, and the real work: only the weight
rule knows its own alpha. `audit/ladder.py` builds it inside the rule's
`__call__` and discards it. Follow the `RunContext.te_ex_ante` precedent from
the 0030 series exactly — a rule MAY expose `alpha()`, the engine reads it off
by `getattr` and carries it onto the path, and **a rule that does not expose it
yields no TC rather than a wrong one.**

No owner-only path is touched: `src/`, `tests/` only. `make check` is the
definition of done.

**Receipt should say:** the commit hashes, the test count, and confirmation that
a rule without `alpha()` leaves TC unevaluated rather than defaulting it.

### 10. Rerun the audit once, after 9 lands

    scripts/unattended.sh audit --digest

`A-20260918-201042` took 50,572 s. `L` and `transfer_coefficient` are both new
per-cell measurements, so each needs a run to populate it — **which is why 9 is
one series and not two.** Do not start this until 9 is committed and green.

Follow the `Routine, unattended work` section of `CLAUDE.md` for the digest, and
add the new columns: `L` against the cells' own distribution, `transfer_coefficient`
in all three forms against the published range (Clarke-de Silva-Thorley report
0.671 for a long-only capped 21-country book; Ding cites their simulation range
as 0.3-0.8), and `implied_ic` at both TC = 1 and measured TC.

**Receipt should say:** rc, runtime, the run id, and the three new columns' medians.

---

## Not queued yet, and what each is waiting on

The registry corrections, `L` and the transfer coefficient moved into the queue
above on 2026-09-19. What is left here is not waiting on a patch; it is waiting
on the owner.

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
- **`decisions/proposed/0029`.** Awaiting the owner, and now overtaken by
  evidence: the ten-seed audit put `transfer_ratio` between -4 and +48 and
  empirical breadth at 0.12 against a formula 151.7, so the frictionless-derived
  numbers in the report are worse than stale. The recommendation on file is
  still to take §1/§3/§4/§5 and defer §2.
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

