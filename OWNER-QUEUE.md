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

### L16. A screen at a confirmation standard, and what confirms a candidate
Added 2026-09-28 by Cowork, from the owner's L15 ruling ("screen",
`decisions/0039`). Two things are unruled:
- **FWER or FDR.** Romano-Wolf at FWER 5% controls the chance of *any* false
  pass, a confirmation standard. A screen usually controls the *share* of false
  passes (FDR, SUBSTRATE §9). Keeping FWER means screening at a confirmation
  standard, with 35-45% power at IC 0.70 before the stepdown.
  **Owner, 2026-09-28: "most likely FDR", to be confirmed after task 34's
  FDR-vs-FWER numbers are read. Not ruled.**
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

### L17. How wide the 200% turnover highlight reaches (`decisions/0038`, held)
Added 2026-09-28 by Cowork. **Owner, 2026-09-28: holding the 0038 ruling until
he has read the friction sweep.** HANDOFF task 33 is on hold until then.

0038 applies the 200% highlight to both the annual figure and the rolling
one-year max. The sweep (`A-20260928-151055`, `claude/friction-sweep-2026-09-28.md`)
shows the rolling max above 200% in **60 of 60** cells, even at 40 bp, and the
rolling p95 above 200% in 60 of 60 as well. Much of that is mechanical: a single
lumpy rebalance of up to 200% of NAV is enough by itself to push any one-year
window to 200% (see L18). On the annual figure the highlight discriminates:
20 of 20 cells at 10 bp, 11 of 20 at 20 bp, 0 of 20 at 40 bp.

**The decision:** keep both windows as 0038 reads it, narrow it to the annual
figure, or defer the rolling-window part until L18 is settled.

### L18. The shadow cost echoes on a 53-week cycle (`decisions/0024`'s design; ruled in principle, `decisions/0040`)
Added 2026-09-28 by Cowork, from the friction sweep. Bears on B2, 0038 and
L17.

The shadow cost per unit traded is set from the **trailing 52 weeks** of
turnover, excluding the current trade, and is flat in the size of the current
trade. So a large trade raises the cost for exactly 52 weeks, and when it rolls
out of the window the cost falls off a cliff and the backlog trades at once,
which re-enters the window. Measured on the persisted weights: the
autocorrelation of weekly turnover **at lag 53 is 0.73-0.78 at 40 bp**, 0.23-0.47
at 20 bp and 0.15-0.23 at 10 bp, against about 0 at lags 26, 51, 52 and 78.
The largest single-week trades line up a year apart (e.g. 2015-08-07,
2016-08-12, 2017-08-18). The median maximum single-week trade **rises** with
friction, from about 1.0x NAV at 10 bp to 1.8-1.9x at 40 bp, and 7 of 20 cells at
40 bp have a week at 1.95x NAV or more, close to a full book swap.

**Why it is yours:** B2 ruled out a per-rebalance cap on the premise that
friction restrains trading. As built, more friction makes trading *lumpier*.
The shadow curve is `decisions/0024`, an owner decision. The measurement is on
the audit's optimiser rule (`audit/ladder.py`, `_OptimiserRule._shadow`). Its
docstring says `harness.objective.turnover_penalty` uses the same curve, but
Cowork has not checked whether that path has the same window edge.

**Options (Cowork's, unmeasured):** (a) make the cost depend on the trade
itself, so the trade is priced at the trailing turnover it creates. That makes
the cost convex in trade size, and lumps become expensive. (b) Replace the
hard 52-week window with an exponentially weighted one, so there is no cliff.
(c) Both. **Retirable in part by measuring:** a small grid with (a) and (b) at
10/20/40 bp would show whether the echo goes and what it does to net IR.

**Ruled 2026-09-28 (owner): option (a)**, "charge each trade at the trailing
turnover it would create". Also chosen by the owner: **measure first** (a
per-cell override, HANDOFF task 36, before anything in `params/`); **the
marginal unit** pays the curve at the post-trade turnover, so the cost is the
integral of the 0024 curve; and **missing history is prefilled at the 100%
target**. Recorded in `decisions/0040`. **Still open:** whether to adopt it into
`params/` after task 36, and at what coefficient. That would land with 0038's
params change (L17), so `params_hash` moves once.

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
**Queued 2026-09-28 as HANDOFF task 35** (owner's L13 ruling). Blocked until it
reports.

**Note for when it lands:** it competes with `H-2026-0008` for the same
variance. Once the book de-risks through its covariance, 0008 must be measured
as incremental to that, not against a never-de-risks baseline, or it gets
credited for what the risk model did.

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

