# OWNER-QUEUE — what only Leo can decide

Companion to `HANDOFF.md`. That file is work for Claude Code; this one is
decisions for the owner. Nothing here is a task: every item is a judgement,
a risk appetite, a tradeoff with no correct answer, or a governance signature
that SUBSTRATE §2 reserves to the owner.

**Maintained by Cowork, read by the Monday/Thursday push.** Agents may add an
item, restate one, or move a closed item to `## Closed` with the decision and
its date. An agent may never answer one. If an item can be settled by measuring
something, it does not belong here — it belongs in `HANDOFF.md` as a task, and
the item should say what measurement would retire it.

**Live** means actionable today. **Blocked** means the answer needs a
measurement that has not run. **Dormant** means it was deliberately deferred and
should stay quiet until its trigger fires.

---

## Live — actionable now

### L12. Is the registry the right shape, now that the stepdown is the bar?
Added 2026-09-21 at the owner's request. Bears on `decisions/0036` §6,
SUBSTRATE §9 and §13, and on what is bought from Macrosynergy.

SUBSTRATE v0.5 made the `multiple_testing` veto — Romano-Wolf at FWER 5%, family
level then within family — **bar 2, how a signal is judged**. It used to be a
footnote at the end of a pipeline nobody had run. It is now the gate.

The registry was written before that was true, and it does not sit well against
it. **`effective_bets_active` is 11.67 across 95 series.** Of twelve
hypotheses, **four target `region`, three `credit` and two `duration`; the
other three (`cash`, `conviction`, `real_nominal`) are one each.** Each of the
twelve sits in its own SUBSTRATE §6 family (`growth`, `inflation`, …,
`conviction`), so "family level first" is trivial today: the dependence lives
in the shared *target axis*, not in the family. A stepdown learns dependence
from the block bootstrap, so correlated tests do not pay full multiplicity,
but they do not buy twelve independent shots either. Twelve registrations
concentrated on three axes over roughly twelve effective bets means **how the
tests are grouped does most of the work**, and nobody has chosen that grouping
against this constraint.

*Corrected 2026-09-28 by Cowork at the owner's request. The earlier text said
five `region` and four `credit`, and treated the target axis as the family.
Counts are from `target_axis` and `family` in `hypotheses/pending/*.yaml` as of
`076c80e`.*

Two decisions inside it:

- **How families are defined.** SUBSTRATE §6 lists eleven, and the stepdown runs
  at family level first. With one hypothesis per family that step does
  nothing. Whether the four `region` tests and the three `credit` tests should
  instead be grouped as families (and the stepdown run on those groups) decides
  most of what survives.
- **How many hypotheses per family per cycle.** `params/agents.yaml` already
  carries the knob (`max proposals per family per cycle`). It was sized as a
  cost lever (`decisions/0007`); it is now also a statistical one.

**And it is live now because of procurement.** 27 JPMaQS tickers are being
bought for nine hypotheses. If those nine collapse to two or three effective
tests under the stepdown, that is a different purchase, and task 23's catalogue
check is already queued.

**Cannot be retired by measuring — yet.** The correlation structure of the
twelve signals cannot be estimated because `src/signal_lab/signals/` is empty,
so nothing builds a signal from a hypothesis file. This is a design judgement
today. **It becomes measurable once signals exist**, at which point the honest
version is to estimate the joint distribution and read the effective number of
independent tests off it rather than guess — and the owner has asked that it be
revisited then.

### L10. The `seed_stability` veto is unreachable as written
Added 2026-09-20 by Cowork.

`params/vetoes.yaml` sets `seed_stability.max_ir_range = 0.15`. Observed
per-cell seed range in `A-20260919-155557` is **0.26 to 1.42**, and at the
per-seed sd of 0.26 that `decisions/0028` already records, the expected range
over ten seeds is about 0.78. The sd is not a simulation artefact: `1/sqrt(16.0
years) = 0.250` is the sampling error of an IR over the development window.

A threshold of 0.15 would require a near-deterministic IR, which 16 years cannot
deliver. It is not applied to audit cells, so nothing has failed on it — but it
would fail every real hypothesis it was ever applied to, and SUBSTRATE §10 is
explicit that a veto whose input is absent **fails**.

Either the threshold is re-derived from the estimator's own sampling error, or
the statistic changes (a range is the worst-behaved summary of ten draws; a
standard error is not), or the veto is retired with its reasoning recorded.
`vetoes/` and `params/` are owner-only.

**Cannot be retired by measuring.** The distribution is in hand.

### L4. Holdout power belongs in SUBSTRATE §3 — RULED 2026-10-01
**Owner, 2026-10-01:** Cowork's draft §3 paragraph (0039 §3 + L4) is accepted. It is applied in SUBSTRATE v0.8, and `decisions/0039` carries the note. *Move to Closed when HANDOFF task 43 lands.*

~350 weeks gives t ≈ 0.8 at a true IR of 0.30, so the holdout can only ever
fail a strategy, never confirm one. That is a material property of the lab's
own final test and it is currently recorded only in these notes. Transcribing
it into §3 is an owner act.
*Cowork, 2026-10-01: a draft §3 paragraph combining 0039 §3 and this item is in
the Project doc `claude/task-42-review-2026-10-01.md` §4. It follows 0043's
gate, not 0039's FDR wording.*

### L19. What the 6% tracking-error budget means: a sizing target or a ceiling (added 2026-10-01) — RULED 2026-10-01
**Owner, 2026-10-01 ("I accept your recs"):** (a), the 6% is the ex-ante sizing target σ, and the p95 is disclosed. Recorded in `decisions/0044`. *Move to Closed when HANDOFF task 43 lands.*

Task 35 (`A-20260930-033812`), policy arm (h26 scalar), recomputed by Cowork:
the mean ex-ante TE is 5.8-5.9% and realised/ex-ante is 0.95-0.99, so the book
is sized correctly on average. But the **p95 of trailing-3y realised TE is
1.12-1.19x the 6% budget** (seeds up to 1.39x). With no overlay it is 1.27-1.34x.

The ratio sits above 1 because a 3-year window swings around its mean. It is
not a sizing error. The choice:
- **(a) 6% is σ, the sizing target.** That is how `decisions/0025` derives
  it. Nothing changes; p95 is disclosed (0030).
- **(b) 6% is a ceiling a client sees on trailing-3y TE.** Size to about 5.1%
  (6%/1.18) and re-anchor 0025's map.

`params/constraints.yaml` names it `max_trailing_3y`, and its comment still
says §10 vetoes it (stale since 0030), which reads like (b). Cowork leans (a)
if the number is the lab's own and (b) if it is an investor-facing mandate.
**Retired by:** the owner's reading of the 6%, recorded in `decisions/`.

### L20. The gate passes every hypothesis in a search smaller than g (added 2026-10-01) — RULED 2026-10-01
**Owner, 2026-10-01 ("I accept your recs"):** g = 1 below m = 8, and g = 2 at or above it. Recorded in `decisions/0045`. *Move to Closed when HANDOFF task 43 lands.*

`romano_wolf_gfwer` with g = 2 sets the critical value to −∞ when a set has
fewer than 2 tests. So **a single-hypothesis search is rejected (passes)
unconditionally**, and bar 2 reduces to `net_ir_excess > 0`.

This is correct for g-FWER, since one test can't make two false passes. But
the first planned real test (0009 alone) is m = 1, and L12's
`family_then_within` runs inside one-hypothesis families. Cowork's check
(independent nulls, k = 100, step 1): the false-pass rate per null hypothesis
is 1.00 at m = 1, 0.22 at m = 2, 0.10 at m = 4, 0.05 at m = 8 and 0.03 at
m = 12. Proposed amendment to 0043: **g = 1 below a floor of about m = 8, and
g = 2 at or above it**, with L12 deciding which m counts. Detail is in the
Project doc `claude/task-42-review-2026-10-01.md` (F1). **This must be settled
before the phase-2 solver runs a real hypothesis.**

### B5. The exposure matrix: how loading estimators are tested (`decisions/0015`, `0016`) — moved to Live and rewritten 2026-10-01
*Corrected by Cowork on 2026-10-01 at the owner's instruction. The earlier
entry said the estimator was "unchosen" and would live in
`params/characteristics.yaml`. `decisions/0015` records the owner overruling
that: the estimator is a research question. It is tested as a measurement
hypothesis (`decisions/0016`) and ranked on out-of-sample loading fidelity,
never on net IR. So the owner does not pick an estimator. What the owner
settles is how the candidates are judged.*

**Why it is on the critical path.** 0016: measurement hypotheses run before
the signal search, and the search "cannot open until a matrix has been
chosen". The JPMaQS loader alone does not open phase 3. `H-2026-0010` also
names the risk decomposition as its own safeguard, so 0010 is testable while
its safeguard is not.

**Settled, 2026-10-01 — the fidelity metric (owner accepted Cowork's
suggestion).** Fidelity is the **out-of-sample fit of next-period returns on
factor returns, using loadings estimated only on data up to the earlier
date**: for instrument i, the loading β_i,t estimated at t predicts r_i,t+1
from the factor returns f_t+1, and candidates are scored on that prediction
error, walk-forward. It is not a comparison against a "realised beta", because
that is itself a noisy estimate and would reward whichever estimator shares
its noise. *Not yet in a `decisions/` record. It goes into one with the three
points below. Still to be written down there: the loss (for example,
out-of-sample R² or squared error), the horizon, and how instruments and dates
are pooled.*

**Still open, for the owner:**
- **The incumbent.** 0016 has each candidate claim better fidelity "than the
  incumbent's", and no incumbent is defined. Cowork's guess is a plain rolling
  OLS on the covariance window (156 weeks). It is a guess, not a
  recommendation with evidence behind it.
- **The factor returns.** What each instrument is regressed on, per exposure
  axis (duration, credit, region, sector, style, real/nominal, cash;
  SUBSTRATE §6). Measured cells (a bond index's duration, a region label) need
  no estimator.
- **Which candidates are registered, and by whom.** Named in 0016, none
  registered: shrinkage toward a prior (Bayesian or Theil-Goldberger), Michaud
  resampling applied to loadings, robust regression, and regime-conditional
  loadings via HMM. With four candidates the gate runs at g = 1
  (`decisions/0045`).

**Retired by:** a `decisions/` record covering the metric and the three open
points, then the measurement hypotheses' own results.

---

## Blocked — waiting on a measurement

### B4. `decisions/0030`'s threshold sensitivity to kurtosis
The ceiling is 1.72, the p99 of the worst annual bias under a correct model at
the measured excess kurtosis of 2.37. But p99 is 1.48 at κ=1 and 1.92 at κ=4,
and one Bloomberg cell read κ=14.65. Whether the threshold should sit at a
conservative κ, or be re-measured per run, is unsettled.

**Retired by:** the ten-seed audit's kurtosis distribution across cells. One
outlier out of seventeen is not enough to choose on.

---

## Dormant — deferred on purpose, with the trigger that wakes them

### D6. Does "phase 3" gate on the loader or on the data?
Moved from Live to Dormant by the owner, 2026-09-21, without being answered —
because on the evidence it does not bind either way.

SUBSTRATE §16 says *"Signal testing may not begin before phase 3,"* and phase 3
is the JPMaQS loader. Four registered hypotheses need no JPMaQS at all:
`H-2026-0007` (12 Bloomberg OAS series), `0008` (MOVE plus four FRED), `0009`
(six Bloomberg, post-`0032`) and `0012` (**zero** series — it is the conviction
measurement question). So the permissive reading would let four run today.

**It buys nothing.** `src/signal_lab/signals/` is empty — `__init__.py` at 44
bytes and a `.keep` — so no code turns a hypothesis file into a signal.
`src/signal_lab/stats/` holds only `blocks.py`, the block shuffle: no
Romano-Wolf stepdown, no HAC, no search null, no deflated IR. And since
SUBSTRATE v0.5 the `multiple_testing` veto **is** §3's evidence bar, so a
hypothesis run today fails bar 2 by construction — §10 is explicit that a veto
whose input is absent fails. Vetoed before it is judged, whichever reading of
§16 applies.

**Wakes when:** `src/signal_lab/signals/` can build a signal from a hypothesis
file **and** the Romano-Wolf stepdown exists. At that point the question becomes
real and should be re-raised as a Live item.

### D1. The two tracking-error penalty coefficients
`decisions/0100` open questions: SUBSTRATE §4's asymmetric TE penalty has two
coefficients, both null, and the objective **refuses to build** until they are
set. Deferred by the owner on 2026-09-09 until a candidate model exists, and
0100 records that refusing is the correct state rather than a gap.

**Wakes when:** a candidate model exists. The form is already settled
(conviction-scaled, linear between two endpoints, floored — `decisions/0019`).

### D7. The two-step one-sided stepdown, and a bootstrap null for bar 2
Added 2026-09-29 by Cowork. **Deferred by the owner the same day** ("keep
things as is for now").

The source is Romano, Shaikh & Wolf (2014, *Econometrica* 82(5)), which the
owner supplied, and Romano & Wolf (2018), "Multiple Testing of One-Sided
Hypotheses: Combining Bonferroni and the Bootstrap". Cowork has not read the
2018 chapter. Two ideas:
- **(a) The two-step correction.** Drop clearly negative hypotheses from
  Romano-Wolf's critical value at a small β, for more power on one-sided
  tests.
- **(b) A block-bootstrap null.** Build the null from the weekly
  live-minus-baseline series instead of engine shuffles, so k stops costing
  engine hours. This would amend `decisions/0036`.

**Wakes when:** the owner reopens it, or real signals exist and the shuffle
budget (k) binds.

### D3. Region labels are still placeholders (`decisions/0022`)
**Wakes when:** a hypothesis needs a region axis it can trust —
`H-2026-0001`, `0006`, `0009` and `0011` all target `region`.

### D4. G3OC as the live 3–7y series
The splice is live; the replacement is not actioned (`decisions/0022` area).

### D5. `git_key` and `git_key.pub` in the repo root
Ignored by `*key*`, so not at risk of being committed, but they sit in a
directory that gets cloned and archived. Hygiene, owner's call.

---

## Closed

### L16. A screen at a confirmation standard, and what confirms a candidate — CLOSED 2026-10-01 (HANDOFF task 42 landed)
**Owner, 2026-10-01, L16(a):** the generalized stepdown, P(two or more false passes) ≤ 5%, at 100 shuffles per test. Cowork picked 100 within the approved 50-100 range. Recorded in `decisions/0043`. Applied by HANDOFF task 42; SUBSTRATE v0.7 and `params/vetoes.yaml` were edited by Cowork. *Task 42 landed 2026-10-01.*

Added 2026-09-28 by Cowork, from the owner's L15 ruling ("screen",
`decisions/0039`). Two things are unruled:
- **FWER or FDR.** Romano-Wolf at FWER 5% controls the chance of *any* false
  pass, a confirmation standard. A screen usually controls the *share* of false
  passes (FDR, SUBSTRATE §9). Keeping FWER means screening at a confirmation
  standard, with 35-45% power at IC 0.70 before the stepdown.
  **Owner, 2026-09-28: "most likely FDR", to be confirmed after task 34's
  FDR-vs-FWER numbers are read. Not ruled.**
  **Task 34 reported 2026-09-29** (`results/fdr_vs_fwer/20260929-031720/`,
  Cowork doc `claude/tasks-34-36-review-2026-09-29.md`). The number of
  shuffles per test, k, decides more than FWER vs FDR:
  - At k ≤ 100, Romano-Wolf 5% has more power than BH 10% (IC 0.70: 0.175 vs
    0.152 at k = 100, and 0.144 vs 0.013 at k = 20).
  - BH 10% wins only at k ≥ 500 (0.274 vs 0.174).
  - k = 500 costs about 140 engine-hours per cycle.

  RSW-FDR, which uses the joint null like Romano-Wolf, was not implemented:
  the task cited the wrong paper (Cowork's error). The right one is Romano,
  Shaikh & Wolf 2008, *TEST* 17(3). **Cowork recommends not ruling yet:**
  implement RSW-FDR from that paper, re-run the study with small k (20-200),
  then choose.
  **Owner, 2026-09-29: yes, and Claude Code may fetch the paper.** Queued as
  HANDOFF task 38. L16(a) is still open until its numbers are read.
  **Task 38 reported 2026-09-29 (`459a257`, `results/fdr_vs_fwer/20260929-154138/`,
  verified by Cowork):**
  - RSW-FDR is **still not implemented**. Claude Code fetched and read the
    paper, but couldn't pin down which stepdown rank each critical value
    belongs to. One reading gave 100% FDR under the null; the other gave zero
    power on a 4-sigma signal. Cowork's note: the zero-power result could be
    an implementation bug rather than a wrong reading. That is unresolved.
  - The study (5,000 reps) now reports pFDR, the false share given at least
    one pass.

  | IC 0.70, n_true 3 | k=20 | 50 | 100 | 200 | 500 | 1000 |
  |---|---|---|---|---|---|---|
  | RW 5% power / pFDR | 0.15 / 0.06 | 0.15 / 0.05 | 0.17 / 0.06 | 0.17 / 0.06 | 0.17 / 0.07 | 0.18 / 0.06 |
  | BH 10% power / pFDR | 0.01 / 0.54 | 0.07 / 0.31 | 0.14 / 0.22 | 0.25 / 0.14 | 0.27 / 0.13 | 0.29 / 0.14 |

  At IC 0.35, RW has power 0.035 and pFDR about 0.25; BH 10% has 0.07 and
  about 0.33 at k ≥ 200.

  **Cowork's recommendation: the ruling is really about compute.** A cycle
  costs about 12 × k × 84 s: 28 h at k = 100, 56 h at k = 200, 140 h at
  k = 500.
  - **At a budget of k ≤ 100:** keep Romano-Wolf at FWER 5%. It has more
    power and a quarter of BH's false share.
  - **At k ≥ 200:** BH at FDR 10% buys about +45% power, and 1 in 7
    candidates is false against 1 in 16.
  - **Drop RSW-FDR** for now. Two faithful attempts failed, and BH already
    represents the FDR option.
  The owner has deferred the two-step and bootstrap-null variants (D7).
  **Owner, 2026-09-29 (evening):** the joint null is a block shuffle, not a
  bootstrap: SUBSTRATE §9 is amended by `decisions/0041`, with confidence
  intervals left on the bootstrap. A third option is now being measured:
  **generalized FWER**, P(2 or more false passes) ≤ α, which reuses
  Romano-Wolf's joint null. It is queued as HANDOFF task 40, together with
  standardising `romano_wolf` so that no hypothesis dominates the maximum by
  scale. **L16(a) stays open until task 40's numbers are read.**
  **Task 40 reported 2026-09-29** (`c0c4093`,
  `results/fdr_vs_fwer/20260929-204223/`). `romano_wolf_gfwer` is implemented
  from Romano & Wolf (2007), *Annals of Statistics* 35(4), Algorithm 2.1
  (fetched from arXiv:0710.2258); standardising `romano_wolf` is implemented
  and is now the default. Under the complete null at k=1000, `p_two_plus_false`
  sits within ~2 MC standard errors of nominal alpha for both variants
  (rw_g2_5: 0.056 vs 0.05; rw_g2_10: 0.109 vs 0.10) — the guarantee the
  procedure actually makes holds.

  | IC 0.70, n_true 3, rho_w 0.3, rho_b 0.2 | k=20 power/fwer | k=1000 power/fwer |
  |---|---|---|
  | romano_wolf_5 (standardised) | 0.218 / 0.099 | 0.179 / 0.042 |
  | rw_g2_5 | 0.343 / 0.224 | 0.348 / 0.177 |
  | rw_g2_10 | 0.419 / 0.309 | 0.426 / 0.276 |
  | bh_10 | 0.010 / 0.011 | 0.289 / 0.154 |

  Like the FWER-vs-FDR choice, `rw_g2_*`'s power is roughly flat across k
  (joint-null max), so it doesn't buy back power by spending shuffle budget
  the way `bh_10` does. **A fourth option is now on the table alongside plain
  Romano-Wolf and BH:** generalized FWER at g=2 nearly doubles power over
  plain Romano-Wolf at any k, at the cost of tolerating a single false pass
  17-22% of the time (only *two or more* false passes are held near 5-10%).
  Whether that tradeoff is acceptable given L15's "screen" ruling is unruled.
  **L16(a) stays open.**

  **Also outstanding, not a judgement call:** `decisions/0041`'s SUBSTRATE §9
  and §15 edits are drafted (verbatim diff in task 40's HANDOFF receipt) but
  **not applied** — Claude Code's permissions refuse writes to `SUBSTRATE.md`
  outright, so this needs Leo or Cowork to apply the three-line diff directly.
  Task 40 also deferred tasks 35 and 39 to the next overnight run (time budget
  against a same-day deadline, not a finding).
  **Correction, 2026-09-29 late evening (Cowork, verified against
  `results/fdr_vs_fwer/20260929-204223/summary.csv`):** the k=20 and k=50 rows
  above are **invalid**. Task 40's standardising used only the null draws'
  mean and sd (Cowork's spec error), which breaks exchangeability. Under the
  complete null, `romano_wolf_5` FWER is 0.127 at k=20 and 0.064 at k=50
  (nominal 0.05), and `rw_g2_5` P(V>=2) is 0.083 at k=20. The k≥100 rows are
  within about 0.01 of nominal. The fix (pool the observed value into the
  mean and sd) is HANDOFF task 41, which re-runs the study. **Don't read the
  small-k power figures until task 41's numbers are in.**
  **Task 41 reported 2026-09-29 (late evening)** (`0a5645f`,
  `results/fdr_vs_fwer/20260930-031720/`): the fix holds. Complete-null,
  headline correlation, k=20: `romano_wolf_5` FWER 0.052 (was 0.127),
  `rw_g2_5` P(V>=2) 0.049 (was 0.083), `rw_g2_10` P(V>=2) 0.098 (nominal
  0.05/0.10) — all within 2-3 MC standard errors of nominal. Against task
  38's pre-standardisation baseline, max |delta FWER| across all (mu, n_true,
  k) cells is now 0.0074 (was 0.066-0.078), consistent with MC noise rather
  than a real shift. **The small-k power/FWER table in the correction above
  is now safe to read** — task 40's g=2 tradeoff description (near-doubled
  power over plain Romano-Wolf, at the cost of a single false pass 17-31% of
  the time) stands under the fix; the earlier `T0`-only numbers it was partly
  drawn from were also individually within noise of the pooled ones except at
  k=20/50, where the direction of the finding (more power, more single-false-
  pass risk) is unchanged. L16(a) stays open.
- ~~**What confirms a candidate.**~~ **Ruled 2026-09-28:** replication and
  economic intuition are the gates, both required. A paper track and a live
  allocation are not. Recorded in `decisions/0039`. ~~Whether to adopt Cowork's
  operational proposal~~ **Ruled 2026-09-28: "yes, adopt all three"**: a thesis
  synthesis that lists what must be true, a replication target fixed before
  looking, and named rival explanations. Recorded in `decisions/0039`.
L4's holdout-power sentence should land in SUBSTRATE §3 in the same edit as
0039's paragraph.
**Partly retirable by measuring:** HANDOFF task 34 (queued 2026-09-28)
measures the power and the realised error of FWER against FDR on the registry's
shape. The choice stays the owner's.

### B1. Whether the volatility overlay becomes policy, and at what halflife — CLOSED 2026-10-01 (HANDOFF task 42 landed)
**Owner, 2026-10-01: policy, at 26 weeks** (Cowork's recommendation: 13 and 26 can't be told apart, and 26 was specified before the sweep). Recorded in `decisions/0042`. Applied by HANDOFF task 42; SUBSTRATE v0.7 and `params/audit.yaml` were edited by Cowork. *Move this item to Closed once task 42 lands.*

Built and tested: seed-paired over 5 seeds at h=13, a scalar 26-week overlay
moved 2008 bias −0.36/−0.54, calm-year bias +0.10, `te_p95` −0.0141 at IC 0.20
in all five seeds, and net IR up +0.10/+0.06. All ten paired calibration
differences went the right way.

**Retired by:** a halflife sweep across horizons. 26 weeks was the only value
tested, at one horizon and two IC rungs. Nothing reads it by default.
**Queued 2026-09-28 as HANDOFF task 35** (owner's L13 ruling). Blocked until it
reports.

**Note for when it lands:** it competes with `H-2026-0008` for the same
variance. Once the book de-risks through its covariance, 0008 must be measured
as incremental to that, not against a never-de-risks baseline, or it gets
credited for what the risk model did.

**Task 35 reported 2026-09-30** (`A-20260930-033812`, HANDOFF receipt has the
full tables). 240/240 cells, rc=0. The h13 no-overlay arm matched the knee
run's live cell to float epsilon at all 20 (ic, seed) pairs, so the sweep is
measuring the same book the earlier, narrower test did.

- **`risk_calibration` fails drop from 5-10 of 20 (no overlay, per horizon)
  to 0-2 of 20 with any halflife arm**, at every horizon (4, 13, 26), not
  just h13. Worst-annual bias falls from a 1.55-1.72 median (no overlay) to
  1.31-1.52 with an overlay; how many cells have 2008 as the worst year falls
  from 15-17/20 to 3-13/20 depending on the arm.
- **Net IR at h13 (the horizon B1's original test used): halflife 13 and 26
  both gain against the no-overlay control in 7-9 of 10 seeds at both IC
  rungs**, mean paired gain +0.05 to +0.07, sd 0.07-0.12 (se ~0.02-0.04) — the
  most consistent net-IR case in the grid. h4 and h26 are mixed in sign.
- **Halflife 13 vs 26 vs 52:** 13 and 26 are close on both risk calibration
  and net IR; 52 is weaker on the h13 net-IR gain at IC 0.35 (-0.003, not
  distinguishable from zero) though still clears risk calibration. Nothing in
  this sweep singles out 26 (the value B1's original test used) as better
  than 13.
- **Not part of this measurement, flagged in the receipt anyway:**
  `te_p95_to_budget` stays above 1 in every cell regardless of overlay
  (1.13-1.34) — an overlay narrows the gap (best at halflife 13) but does not
  close it on this reading.

**Still the owner's call:** whether the overlay becomes policy, and if so at
which halflife (13 and 26 are the strongest candidates on this evidence, 52
the weakest). Not ruled here.

### L17 — how wide the 200% turnover highlight reaches. CLOSED 2026-09-29.
**Owner: "both"**, meaning the annual figure and the rolling one-year p95. The
rolling max is still reported but not highlighted. Recorded as an addendum to
`decisions/0038`, and applied with 0040 by HANDOFF task 39. The full item
text is in git history.

### L18 — the shadow cost's 53-week echo. CLOSED 2026-09-29.
**Owner:** option (a) on 2026-09-28, then **"0040: 40bps"** on 2026-09-29 after
task 36 (`A-20260929-070540`): the largest week is at most 0.84× NAV, with no
detectable change in net IR. `decisions/0040` is adopted at 40 bp and applied
by HANDOFF task 39. A residual lag-52 rhythm (0.24-0.30 at 40 bp) remains; an
exponentially weighted window is the fix if it ever matters. The full item
text is in git history.

### D2 — the test-suite split. CLOSED 2026-09-29.
**Owner: "yes"**, after `make check` reached 3695 s. HANDOFF task 37 splits it
into a fast `make check` and a full `make check-full`.

### L13 — `risk_calibration` vetoes a quarter to a half of every grid, on 2008. CLOSED 2026-09-28.
**Owner: "approved, go ahead"**: B1's halflife sweep is queued now as
critical-path work, HANDOFF task 35. Whether the overlay then becomes policy is
B1, blocked on task 35. The friction sweep adds one data point: 21 of 60 cells
fail, 2008 is the worst year in 50 of 60, and friction does not move it
monotonically. The full item text is in git history.

### L14 — twelve JPMaQS tickers that didn't exist as named. CLOSED 2026-09-28.
The owner renamed H-0001 (2026-09-24) and 0004, 0005 and 0010 (2026-09-27,
"recs on all", plus dropping `DRTSCILM`), recorded as addenda to
`decisions/0032`. Task 31's vendor check: **26 of 26 resolve**
(`7ce2dff`), and `data/jpmaqs/request.txt` is written. The full item text is in
git history (`2448f52`).

### L15 — bar 2's power and what the lab is for. CLOSED 2026-09-28.
**Owner: "screen."** A pass on both bars makes a hypothesis a *candidate*, and
a bar-2 failure is *not detected*, not false. Recorded in `decisions/0039`. The
evidence is task 30 (`A-20260926-161749`): about 35-45% power at IC 0.70, 4 of
10 seeds. Follow-ups are in L16.

### B3 — the 400% turnover backstop. CLOSED 2026-09-28.
**Owner:** "400% level is only reported. Actually anything over 200% should be
highlighted, but no veto. Drop the 400% as a reference." No veto in any window.
The friction sweep is approved. Recorded in `decisions/0038`, together with B2.
Applied by HANDOFF task 33; the sweep is task 32. Reading "anything over 200%"
as both the annual figure and the rolling one-year max is Cowork's
interpretation, noted in 0038.

### B2 — the per-session (per-rebalance) turnover cap. CLOSED 2026-09-25.
**Owner:** no per-rebalance turnover cap. Turnover is restrained by friction,
the costs and the shadow cost of `decisions/0024`. This is already the state
of `params/audit.yaml` (`per_rebalance_cap_default: null`), so no params
change. The `per_rebalance_caps` sweep stays a diagnostic. Recorded in
`decisions/0038` (2026-09-28).

### L11 — SUBSTRATE §3 and the second bar. CLOSED 2026-09-21.
**Decided and transcribed the same day.** SUBSTRATE is at **v0.5**: §3 replaces
the single primary metric with the two bars of `decisions/0036` §6, and §10's
`multiple_testing` row names `net_ir_excess` as the statistic it tests. The
owner instructed the amendment; Cowork held the pen and originated nothing, per
§2. The commit cites `decisions/0036` and is its own diff for review, following
the `decisions/0030` precedent.

Nothing in `params/` or `vetoes/` moved: bar 1 keeps `target_net_ir: 0.30` and
bar 2 is the `multiple_testing` veto that `params/vetoes.yaml` already
configures at `fwer_alpha: 0.05`.

### L9 — the bar, after the no-information floor. CLOSED 2026-09-21.
**Decided: two bars.**

**Bar 1, the product bar, on the level: net IR >= 0.30.** Unchanged in value and
derived for the first time. The owner's appetite is 150 bp of active return, and
at the 5-6% budget `150 / 500 = 0.30`. `decisions/0023` carried that number on a
quotation alone; it now has a derivation. **`params/audit.yaml` does not change,
and `decisions/0025`'s tracking-error budget is unmoved** — 0025 derives the
budget from the IR an investor experiences, which is the level, and the level is
still 0.30. The coupling this item warned about does not fire.

**Bar 2, the evidence bar, on the excess: no number, a significance test.**
`net_ir_excess > 0` and survival of Romano-Wolf at FWER 5% with the excess as
the test statistic. A threshold is the wrong instrument: `decisions/0036` §1
shows the floor is the mean of a **420 bp-wide** distribution (-141 to +280 bp,
12% of tilts negative) on a **single history**, so any number subtracted from it
inherits that noise. **The gate already exists** — SUBSTRATE §10 lists
`multiple_testing` and `params/vetoes.yaml` already sets `romano_wolf`,
`fwer_alpha: 0.05`, `family_then_within`. It has simply never been
implementable, because `src/signal_lab/stats/` was one line until 0036 §4(a)'s
block shuffle landed.

**The owner's reasoning, in his words:** 150 bp is satisfactory, "but I also
don't want to arrive at it simply because I reached an arbitrary combination of
betas that already tends to achieve that 150 bps in the sample period we are
analyzing." Two questions, two bars. A candidate clearing bar 1 but not bar 2 is
beta available more cheaply; one clearing bar 2 but not bar 1 is a real signal
not worth the operational cost.

**Why this closed rather than staying blocked.** The half of this item that
waited on tasks 18 and 20 was the *number*, whose required-IC arithmetic depends
on the response shape between IC 0.20 and IC 1.00. Neither bar needs that shape:
bar 1 is a product statement at a given risk level, bar 2 is a test. Tasks 18
and 20 remain worth running — they measure whether this lab can *detect* a
signal that clears bar 2 — but they are off the bar's critical path.

**One owner act still outstanding, tracked as L11:** naming the excess statistic
in SUBSTRATE §3 and saying there that `multiple_testing` runs on it.

Raised 2026-09-20 when the floor was measured at 0.311 against a 0.30 bar;
closed 2026-09-21.

### L1 — conditioning the frictionless covariance. CLOSED 2026-09-19.
`decisions/0029`. **§1, §3, §4 and §5 taken; §2 deferred.** The frictionless
twin is struck from the report as a ruler and kept as a covariance-error
diagnostic; empirical breadth is read off the constrained ladder; per-date
Pearson IC is reported beside rank IC.

§2 -- a ridge or eigenvalue floor chosen so the frictionless bias sits near 1.00
on the Bloomberg panel -- stays deferred, because that is a free parameter tuned
to a target on the evaluation panel and 0029's own closing section warns against
it.

The ten-seed audit confirmed the finding without the three-seed caveat:
`transfer_ratio` between -4 and +48, empirical breadth 0.12 at h4 against a
formula 151.7. The same reasoning is why `decisions/0033` measures the transfer
coefficient from the constrained book's own weights rather than from a twin.

**Wakes when:** someone proposes a conditioning that can be justified as a
measurement device rather than tuned until the ladder looks right.

### L8 — the rebalance policy. CLOSED 2026-09-19.
**Decided: weekly re-solve stays; no no-trade band, no partial adjustment.**
Recorded as a dated addendum to `decisions/0024`, following the 0013 precedent
rather than amending a decided record in place.

The ten-seed audit settled it: total cost drag across the whole grid is 17-35 bp
a year, about 0.06 of IR at the 6% budget, and that is the entire prize. Capping
turnover at 50% at IC 0.20 saved 12 bp and cost 0.033 of net IR. The persistence
the owner asked for already falls out of a cost-priced objective — 2% annual
turnover at h13, IC 0.02, under forced weekly re-solve.

Raised 2026-09-18 as a gap in the machinery; closed 2026-09-19 as a gap in the
documentation.

**Wakes when:** the cost model is revised, not when something is measured.

### L7 — measuring the transfer coefficient. CLOSED 2026-09-19.
`decisions/proposed/0033`. **All three recommendations taken.** TC gates nothing
and is a disclosed characteristic; the full-matrix estimator (Clarke-de Silva-
Thorley 2006 eq. 23) is the reported TC, with the diagonal form alongside for
comparability and the inversion-free alignment form as a control; `implied_ic`
prints at both TC = 1 and measured TC rather than silently changing meaning.

Published magnitudes for context: CDT (2006) report **0.671** for a long-only,
capped, beta-neutral 21-country EAFE book (0.620 diagonal); Ding (2010) cites
their 2002 simulation range as **0.3 to 0.8**.

The ten-seed audit confirmed why the frictionless twin cannot supply this
number: transfer ratios of -4 to +48, and empirical breadth of 0.12 at h4
against 151.7 from the formula.

Implementation is the same migration `decisions/0030` turned out to be — a rule
exposes `alpha()`, the engine carries it onto the path, a rule that does not
yields no TC rather than a wrong one.

### L6 — the registry's tickers against the real panel. CLOSED 2026-09-19.
`decisions/proposed/0032`; map at `data/requests/ticker_resolution.csv`.
27 of 42 unresolved names were genuine JPMaQS gaps; the rest was bookkeeping.

**Decisions:** the price-only concern is **withdrawn** — the pull is
`TOT_RETURN_INDEX_GROSS_DVDS` and `decisions/0013` had already settled it; the
stale `likely_price_only` column leaves the table on `make coverage && make
universe`. Europe stays **sub-country and sector only**; `MXEU` not pulled, and
the resulting two-draws-for-Europe asymmetry is accepted and disclosed because
the UK is a distinct market. `LUALTRUU` and `LT08TRUU` are **fabricated**,
removed not substituted. `H-2026-0010`'s term spread is **`LT01TRUU` vs
`LT11TRUU`**, `LT09TRUU` as mid-curve check. `DRTSCILM` joins the FRED request.
`H-2026-0007` takes **set A**, the six-segment quality ladder, with the Ba/B/Caa
collinearity disclosed in advance.

The validator gap it uncovered moves to its own record, `0034`.

When an item closes it moves here with the decision and its date rather than
being deleted — the record of how long a question sat is worth keeping.

### L2 / L5 — the left-tail check `H-2026-0007` lost. CLOSED 2026-09-18.
**Decision: shape 1.** `L = |q05(z)| / 1.645` is a reported characteristic on
every cell and is named, in a dated addendum, as `H-2026-0007`'s pre-registered
check. It gates nothing; no eleventh veto is added. Recorded in
`decisions/proposed/0031`, which needs promoting out of `proposed/` and the
addendum writing — both need git, so they queue in `HANDOFF.md` once the running
audit lands. The threshold stays unset and comes from `scripts/bias_map.py`'s
simulated null.

L2 was raised 2026-09-18 and closed the same day, before any result existed for
0007 — which was the whole point of raising it.

