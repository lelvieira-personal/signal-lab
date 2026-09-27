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

### L14. Twelve registered JPMaQS tickers do not exist as named
Added 2026-09-23 by Cowork, from task 23. Bears on L12, `decisions/0032` and what
is bought.

The vendor catalogue (31,728 tickers) resolves **15 of the 27** registered names.
Every failure is at the xcat — the cid resolves elsewhere in the list — so these
look misnamed or absent, not a coverage gap.

| hypothesis | unresolved | effect |
|---|---|---|
| H-2026-0001 | ~~`INTRGDP_NSA_P1M1ML12_D1M1ML3` x USD/EUR/JPY/GBP, `USD_UNEMPLRATE_SA_D1Q1QL4`~~ | **renamed 2026-09-24** (owner), `decisions/0032` addendum: `..._D3M3ML3`, `USD_UNEMPLRATE_SA_3MMAV5YMA`. 7 of 7 named; **7 of 7 in the cached catalogue** (task 29, cache membership, not a vendor pull) |
| H-2026-0004 | `BLSDCLN_SA_D1Q1QL1` x USD/EUR | **fully blocked** |
| H-2026-0005 | `USD_MBASEGDP_SA_D1M1ML12`, `USD_RM1GDP_SA_D1M1ML12`, `EUR_RM3GDP_SA_D1M1ML12` | **fully blocked** |
| H-2026-0010 | `GB10YXGB_NSA` x USD/EUR | JPMaQS leg blocked |

**The decision, per ticker:** rename to a catalogue name, drop it (the 0032
precedent for `LUALTRUU`/`LT08TRUU`), or hold the hypothesis. A rename changes a
pre-registered hypothesis, so it should be recorded as a dated addendum, not a
silent edit — the thing `decisions/proposed/0034` exists about.

**Partly retirable by measuring:** task 27 lists catalogue names sharing each
cid and xcat stem. The list informs the choice; it does not make it.

**Restated 2026-09-24 (Claude Code), after the Macrosynergy handbook's
Appendix 4.** *Superseded for 0004 and 0005 by the 2026-09-25 restatement
below.* Still open, with what the evidence said then:
- **0004:** task 27's only matches are `BLSDSCORE_NSA_*`, which reads as loan
  *demand*. The hypothesis is about lending *standards*. Renaming to it would
  test a different hypothesis. A names-only catalogue search for a `BLSC*` stem
  would retire the doubt.
- **0005:** nothing for real broad money. The handbook's money and credit
  factors are `INTLIQGDP` (intervention liquidity) and `XPCREDITBN` (private
  credit), and neither is broad money. The choice is to re-specify or hold.
- **0010:** `USD_GB10YCRY_NSA`, 10y government bond carry, is closer to the
  rationale ("yield plus roll-down") than the registered spread. EUR has no
  euro-area curve; a `DEM_` search is needed.

**Restated 2026-09-25 (Cowork), after task 29's names-only search
(`data/requests/jpmaqs_name_search.csv`) and Macrosynergy's Academy notebooks
for each category.** The search retires the doubts it was asked about; the
choices stay the owner's.
- **0004 — a standards series exists.** `BLSCSCORE_NSA` with `_D1Q1QL1`,
  `_D2Q2QL2` and `_D1Q1QL4`, for USD and EUR. Macrosynergy defines it as
  "Bank lending survey, credit supply (easing standards) z-score", *positive =
  easing*; `BLSDSCORE` is credit *demand*, so it is not a candidate. Three
  things a rename has to state: **(a)** which change — the registered name is a
  1-quarter change, the signal is named "2q change", and both exist; **(b)**
  **the sign flips**: the registry's "−" on tightening becomes "+" on an
  easing-positive score; **(c)** NSA z-score, not an SA net-percentage balance.
- **0005 — real money growth exists; "nothing for real broad money" was
  wrong.** `RMBROAD_SJA_P1M1ML12` and `RMNARROW_SJA_P1M1ML12` exist for USD and
  EUR (also `_D1M1ML3`, `P3M3ML3AR`, `P6M6ML6AR`): money deflated by headline
  CPI, % over a year ago. `RMBROAD_SJA_P1M1ML12` is literally the hypothesis's
  title. Caveats: these are growth rates, not "% of GDP" as registered; USD
  "broad" is **M2**, not M3 (Macrosynergy's note); that USD "narrow" is M1 is
  **unconfirmed**. `MBASEGDP` has only `_SA` and 1/3/6-month changes for USD
  and EUR — **no 12-month change**. Choice for that leg: drop it, use `_D1M1ML6`,
  or derive a 12-month change from the `_SA` level (which mixes vintages).
- **0010 — no `GB10YXGB`, and no term-spread category.** Nothing named `XGB`
  exists and Macrosynergy documents no curve/spread category. What exists:
  `GB10YYLD_NSA`, `GB10YCRY_NSA/_VT10`, `GB10YXR_*` for USD and for `DEM`,
  `FRF`, `ITL`, `ESP`; **no `EUR_GB10Y*`** (euro-area bonds are by country).
  Choice: re-specify as 10y carry (`GB10YCRY`, closer to "yield plus
  roll-down"), derive a spread, or drop the JPMaQS leg (the request already
  carries FRED `DGS2/DGS10/DGS30` for the US curve).
  **Retirable by measuring:** a derived 10y−2y spread needs `GB02YYLD_NSA`,
  which task 29 did not search (prefix `GB10Y` only). A names-only check for
  `USD_`/`DEM_GB02YYLD_NSA` belongs in `HANDOFF.md`.

**Owner ruling, 2026-09-27: Cowork's recommendations on all three.** Queued
as `HANDOFF.md` task 31, which records them as an addendum to
`decisions/0032`. L14 closes when that lands and the vendor check passes.
- **0004:** `{USD,EUR}_BLSCSCORE_NSA_D2Q2QL2`. It enters **negated**
  (−easing = tightening), so the registered direction `negative` stays as
  written, following the precedent of H-0001's unemployment gap.
- **0005:** `{USD,EUR}_RMBROAD_SJA_P1M1ML12`. The `RM1GDP` and `MBASEGDP`
  legs are dropped. USD broad money is M2 and EUR is M3. These are growth
  rates, not "% of GDP".
- **0010:** `USD_GB10YCRY_NSA` and `DEM_GB10YCRY_NSA`. The signal is
  re-specified from term spread to 10-year carry (yield plus roll-down).
- **0004, FRED `DRTSCILM`: dropped** (owner, 2026-09-27). It duplicates the USD
  leg with the opposite sign. This withdraws its 2026-09-19 FRED-request
  approval.

**Done 2026-09-24:** the colleague's confirmation that JPMaQS may be pulled into
a personal environment is recorded in `decisions/0037`, as the owner stated it.

### L15. Bar 2 has 14–33% power on one history — what is the lab for?
Added 2026-09-25 by Cowork, from Claude Code's read of task 25
(`results/audit/A-20260924-194115/power-on-one-history-2026-09-24.md`).
Bears on L4, L12, SUBSTRATE §3 and §9, `decisions/0036`.

**The measurement.** The score-shuffle null's sd is 0.174 pooled (0.144–0.203
by cell), narrower than the 0.25 assumed. A single one-sided 5% test rejects at
an excess of about 0.29 and needs about 0.43 expected excess for 80% power.
Against the knee grid's measured excess, **single-test power is about 14% at
IC 0.35, 16% at 0.50 and 33% at 0.70**, before Romano-Wolf lowers it further.
Cowork re-derived these three figures from the stated sd and excesses (normal
approximation); they check. The grid behind the sd is only 2 independent noise
draws.

**Why.** Each signal's non-informative component gets one draw of timing luck
on this history, worth −0.39 to +0.11 here — as large as the null's sd — while
information adds 0.00–0.23. More history shrinks both by `1/√years` and leaves
the ratio unchanged; breadth raises the information term; FDR moves the
critical value, not the luck.

**Two defects the read found in bar 2 itself:**
- **The shuffle leaks static tilt.** It is meant to keep each signal's static
  tilt so that beta earns no excess, but it keeps ~80% for full-history series
  and 35–60% for late starters (re-masking 168 of ~991 rows). The rest of an
  in-sample tilt's payoff leaks into `net_ir_excess`, **biasing bar 2 toward
  passing beta** — small for planted signals, possibly large for persistent
  tilts such as carry (0010). Also unmatched: the live book binds TE harder
  and is more persistent than its shuffles. Unmeasured how much either moves
  net IR.
- **k = 20 permutations cannot reject under a stepdown** (smallest p = 1/21 =
  0.048). A real bar-2 run needs k in the hundreds.

**The decisions:**
1. **What the lab is for,** given this power: more breadth (design B), a
   different evidence bar (FDR, SUBSTRATE §9), or accept that it **screens
   rather than confirms** — which is where the numbers point. More history
   alone does not help (see above).
2. **Approve compute (none queued).** A: fix the shuffle to permute only rows
   where the score exists, add a test, then a power grid at IC 0.70, seeds
   0–9, 20 perms — 200 cells, ~6 h. B: same without the fix, ~5.5 h. C: design
   B first, no compute. Claude Code recommends **A** (measuring power against a
   leaky null bakes the leak in). The fix touches the audit, not `params/`, but
   it changes what bar 2 means, so it is listed here.

**Owner, 2026-09-25: option A approved** — fix the shuffle, then the 10-seed
grid. Queued as `HANDOFF.md` task 30 (new mode `score_span`; task 25's `score`
cells stay as they are). Decision 1 stays open until task 30 reports.

**Task 30 reported 2026-09-26** (`A-20260926-161749`, rc=0, hashes match;
Cowork re-derived the figures below from `cells.csv` and `summary.json`):
- The fix works: full-history columns keep their mean exactly (slope 1.00,
  was 0.81); late starters 0.76 (was 0.58).
- IC 0.70, 10 seeds: live beats all 20 shuffles in **4 of 10** seeds (the
  only rank that rejects at 5% with k = 20). Mean excess over the null 0.255,
  sd across seeds 0.193, null sd 0.168 pooled. **Power at IC 0.70 is about
  35-45%, not 33%**, and the binomial range on 4 of 10 is wide (~12-74%).
- Noise timing still dominates single histories: seed 0's excess is −0.15
  while seed 9's is +0.47, at the same planted IC.
- Unexplained: on seeds 0 and 1 the fixed null's mean is **lower** than the
  old one (0.24/0.33 vs 0.30/0.39), although it now keeps more tilt. Each gap
  is about 1.8 standard errors. Cowork's guess, unverified: the kept tilt pays
  negatively on the planted panel, or the block seams moved.
**Decision 1 is now live:** the numbers still point to "screens rather than
confirms" at any realistic IC.

### L13. `risk_calibration` vetoes a quarter to a half of every grid, on 2008
Added 2026-09-22 by Cowork. Bears on B1, B4, `decisions/0030` and SUBSTRATE §10.

Share of cells with `bias_worst_annual` > 1.72, from each run's `cells.csv`:
`A-20260919-155557` base 23% (frictionless 100%); knee 47%, live and baseline
alike; full baseline grid 26%; baseline pilot 30%. **2008 is the worst year in
every failure of the three newer runs and in 240 of 260 run-wide in the first.**
A correctly specified model at the p99 fails about 1%. Kurtosis (B4) does not
rescue it: at the κ = 4 threshold of 1.92, 3-8% still fail. Live and baseline
fail together, so it is the risk model in 2008, not the signal.

`decisions/0030` foresaw it: 5 of 17 base cells failed without the volatility
overlay, 0 of 11 with it.

**Why it is live.** Under SUBSTRATE v0.5 every real hypothesis carries roughly a
25-45% chance of dying on 2008 whatever its signal. The overlay (B1) is opt-in,
tested at one halflife and one horizon, and a standing refusal in `HANDOFF.md`.

**Update 2026-09-25:** task 25's power grid fails `risk_calibration` in 32 of
80 shuffles and 3 of 4 live twins — the same pattern, live and null together.

**The decision:** queue B1's halflife sweep now as critical-path work, or accept
and disclose the veto's 2008 behaviour. `vetoes/` and `params/` are owner-only.

**Partly retirable by measuring:** the sweep shows whether an overlay brings the
fail rate near 1%. Adopting it stays the owner's call.

### L12. Is the registry the right shape, now that the stepdown is the bar?
Added 2026-09-21 at the owner's request. Bears on `decisions/0036` §6,
SUBSTRATE §9 and §13, and on what is bought from Macrosynergy.

SUBSTRATE v0.5 made the `multiple_testing` veto — Romano-Wolf at FWER 5%, family
level then within family — **bar 2, how a signal is judged**. It used to be a
footnote at the end of a pipeline nobody had run. It is now the gate.

The registry was written before that was true, and it does not sit well against
it. **`effective_bets_active` is 11.67 across 95 series.** Of twelve
hypotheses, **five target `region` and four target `credit`.** A stepdown learns
dependence from the block bootstrap, so correlated tests do not pay full
multiplicity — but they do not buy twelve independent shots either. Twelve
registrations concentrated on two axes over roughly twelve effective bets means
the **family definitions do most of the work**, and nobody has chosen them
against this constraint.

Two decisions inside it:

- **How families are defined.** SUBSTRATE §6 lists eleven, and the stepdown runs
  at family level first. Whether `region` with five entrants and `credit` with
  four are one family each, or should be split or merged, decides most of what
  survives.
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

### L4. Holdout power belongs in SUBSTRATE §3
~350 weeks gives t ≈ 0.8 at a true IR of 0.30, so the holdout can only ever
fail a strategy, never confirm one. That is a material property of the lab's
own final test and it is currently recorded only in these notes. Transcribing
it into §3 is an owner act.

---

## Blocked — waiting on a measurement

### B1. Whether the volatility overlay becomes policy, and at what halflife
Built and tested: seed-paired over 5 seeds at h=13, a scalar 26-week overlay
moved 2008 bias −0.36/−0.54, calm-year bias +0.10, `te_p95` −0.0141 at IC 0.20
in all five seeds, and net IR up +0.10/+0.06. All ten paired calibration
differences went the right way.

**Retired by:** a halflife sweep across horizons. 26 weeks was the only value
tested, at one horizon and two IC rungs. Nothing reads it by default.

**Note for when it lands:** it competes with `H-2026-0008` for the same
variance. Once the book de-risks through its covariance, 0008 must be measured
as incremental to that, not against a never-de-risks baseline, or it gets
credited for what the risk model did.

### B3. The 400% turnover backstop vs fast, strong signals
A small-universe cell ran 414% annual traded notional on realistic costs in the
synthetic grid. The Bloomberg grid's worst was 342%, inside the backstop.

**Retired by:** the ten-seed audit's turnover column at high IC and short
horizon. If nothing approaches 400%, the question closes itself.

**Update 2026-09-25 — now partly a wording question.** In task 25's power grid,
**rolling one-year turnover exceeds 400% in 68 of 80 cells** (peak ~631%) while
annual turnover passes everywhere. SUBSTRATE §10 says "annualised traded
notional" without saying which window. Which measure the backstop reads is an
owner call; the measurement no longer settles B3 on its own.

**Owner's stance, 2026-09-25:** turnover is restrained by friction, not by
limits. If a book still trades heavily after friction, the owner reviews the
result for practicality to an investor. It may still show what is valuable,
and it may prompt a run with higher friction to see how results respond.
**Still open:**
- **(a) Is the 400% `vetoes.turnover.max_annualised` still a veto?** Today it
  fails a cell outright, so the owner never sees the result. The stance reads
  as "disclose, then judge", like `decisions/0030` did for TE. That would be a
  `vetoes/` change and needs a `decisions/` record.
- **(b) If it stays, which window:** annual or rolling one-year.
- **(c) "More friction" has two dials, and they differ.** The shadow cost
  (`constraints.turnover.penalty.coefficient`, 10 bp at 150%) shapes weights
  and never enters net IR. The real half-spreads (`costs.yaml`, 5/10/20 bp)
  do. Raising the shadow cost tests whether the alpha survives slower trading.
  Raising spreads above reality understates performance. Cowork recommends
  the shadow coefficient for the owner's experiment, e.g. a sweep of 10/20/40.
**Task 30's turnover (210 cells, IC 0.70, h13):** annual above 400% in
**0** (median 318% live, 338% shuffled; max 355%). Rolling one-year max above
400% in **all 210** (median ~500-520%, max 612%). So an annual-window veto never
bites, and a rolling-window veto would fail every cell. Separately, **the
median book trades 3.2-3.4x a year against a 100% target**, so the shadow cost
is not holding turnover near its target. That bears on (c).

### B4. `decisions/0030`'s threshold sensitivity to kurtosis
The ceiling is 1.72, the p99 of the worst annual bias under a correct model at
the measured excess kurtosis of 2.37. But p99 is 1.48 at κ=1 and 1.92 at κ=4,
and one Bloomberg cell read κ=14.65. Whether the threshold should sit at a
conservative κ, or be re-measured per run, is unsettled.

**Retired by:** the ten-seed audit's kurtosis distribution across cells. One
outlier out of seventeen is not enough to choose on.

### B5. The robust factor-loading estimator (`decisions/0015`)
Unchosen: shrinkage, resampling, robust regression or regime-conditional. It
will live in `params/characteristics.yaml`, which does not exist.

`H-2026-0010` declares that risk decomposition is the check on whether its
cross-sectional carry signal is really a single term-premium bet — so 0010 is
testable while its own stated safeguard is not.

**Retired by:** nothing measured yet; this is a modelling choice that needs a
candidate. Listed here because a hypothesis already depends on it.

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

### D2. Test-suite split — model-validity checks vs wiring
Deferred by the owner. **Wakes when:** `make check` runtime becomes an obstacle
to iteration. It went 1642 s → 417 s on 2026-09-18 for unknown reasons, so this
may have receded on its own.

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

### B2 — the per-session (per-rebalance) turnover cap. CLOSED 2026-09-25.
**Owner:** no per-rebalance turnover cap. Turnover is restrained by friction,
the costs and the shadow cost of `decisions/0024`. This is already the state
of `params/audit.yaml` (`per_rebalance_cap_default: null`), so no params
change. The `per_rebalance_caps` sweep stays a diagnostic. It should be
recorded in `decisions/` with B3's answer.

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

