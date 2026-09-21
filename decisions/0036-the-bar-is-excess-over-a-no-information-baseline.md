# 0036 — The bar is measured as excess over a no-information baseline

Proposed 2026-09-20 by Cowork. **DECIDED by the owner 2026-09-20: §3 and §4(a)
taken — the metric is reported as excess over a block-shuffled, seed- and
magnitude-matched baseline. §6: **position 3 — two bars**
(owner, 2026-09-21, superseding a same-week reading of position 2). A product
bar on the level, derived from a stated 150 bp appetite, and an evidence bar on
the excess that is a significance test rather than a threshold.
`params/audit.yaml: target_net_ir` stays 0.30 — now derived rather than
asserted — and `decisions/0025`'s tracking-error budget is unmoved. See §6.** §4(b), the `alpha_scale` knob, is not
taken here and survives only as the separate magnitude-vs-information probe §4
describes. Evidence: `A-20260919-155557` and the Cowork project doc
`claude/dose-response-step1-2026-09-20.md`. Bears on `decisions/0023` (the bar),
`0027` (its calibration) and `0028` (ten seeds); amends none of them yet.

## 1. The finding

`decisions/0023` set the bar at **net IR 0.30**. On the development window a
book holding **no usable information** reads **0.311**.

The control was already in the grid and nobody had read it as one. At the
IC 0.02 rung the planted score is `0.02*truth + 0.9998*noise`, so the truth is
**0.04% of its variance**. That rung is the zero-information control to within
four parts in ten thousand:

| | IC 0.02 rung, base cells |
|---|---:|
| realised per-date Pearson IC | 0.0160 |
| ex-ante TE it still runs (budget 6%) | **4.55%** |
| realised active vol | 4.42% |
| **net IR** | **0.3106** |
| SE clustered on seed (10 clusters) | 0.0752, **t = 4.1** |
| by horizon (h4 / h13 / h26 / h52) | 0.286 / 0.290 / 0.304 / 0.363 |

To pay for 0.311 out of 0.016 of realised IC would need a slope of **19.4 IR
per unit IC**. Every slope this lab has measured is two orders below it:

| source | slope | what 0.02 of IC buys |
|---|---:|---:|
| frictionless twin, h4 / h13 / h26 / h52 | 0.387 / 0.245 / 0.187 / 0.130 | 0.008 / 0.005 / 0.004 / 0.003 |
| oracle-anchored linear, h13 | 1.03 | 0.021 |
| **required to explain 0.311** | **19.4** | — |

Between 1% and 7% of the 0.311 is attributable to the rung's information. The
rest is the long-only constraint set meeting this particular 16-year path.

**What the "no-information book" actually is, and how much it varies.** Added
2026-09-21 after the owner asked whether such a book really generates 1.5% a
year. It is not a benchmark-like portfolio with a small tilt. It holds
**10.8 instruments on average out of 85.4 holdable** (cap 30), long-only, fully
invested, cash 1.4%, re-solved weekly, measured against a 50/50 global
benchmark. Eleven lines cannot replicate a global 50/50, so the book is a
**concentrated, essentially arbitrary risk-premium portfolio**. It carries no
forecasting information; it carries a great deal of exposure.

And the 144 bp is a mean over a wide distribution, on **one history**:

| across the 40 IC 0.02 cells | |
|---|---:|
| active return, mean | **+144 bp** |
| active return, range | **−141 to +280 bp** |
| net IR, mean / sd | 0.311 / **0.255** |
| cells with negative net IR | **12%** |
| max active drawdown | 16.5% |

The ten seeds average over **tilts, not over paths**. All 40 cells run on the
same 2004-2019 history, so this is not evidence that an arbitrary tilt earns
144 bp in expectation — only that on this path, the average one did, while one
in eight lost money and the spread was 420 bp wide.

This matters for how the finding is stated. **1.5% of alpha is hard; 1.5% from
concentrated risk-premium exposure over 2004-2019 is unremarkable**, and the
latter is what this is. `bias_worst_year` is 2008 in 420 of 484 judged cells —
the floor is a crisis-exposed beta tilt, and it is paid for in the one year that
tilt does not work.

**Scope, stated precisely.** The ten seeds average over *tilts*, not over
*paths*. A single macro window can systematically reward long-only deviations
from 50/50 — 2004-2019 rewarded equity, credit and EM overweights. What is
established is that **on this panel, this benchmark and this window**, a
long-only book running 4.5% ex-ante TE on a 99.96%-noise signal earns 0.31 net
IR. Whether the floor survives another window is untestable here: the holdout is
locked and, per `OWNER-QUEUE` L4, could not confirm it anyway.

## 2. What it means for readings already taken

Every `required_ic`, `required_ic_surviving` and surviving-cell count in both
Bloomberg audits is read against a bar that the floor already clears. This is
not a second measurement bug like `decisions/proposed/0035` — the numbers are
correct. It is that **net IR against zero is the wrong comparison**, so a cell
clearing 0.30 is evidence about the universe and the constraint set, not about
the signal.

## 3. The proposal

Report, per cell, a second metric:

    net_ir_excess = net_ir - net_ir(baseline)

where `baseline` is a **seed-matched, constraint-matched, magnitude-matched**
book with the information destroyed and everything else held. Rank and judge on
`net_ir_excess`. `net_ir` stays reported beside it, unchanged, because it is
what SUBSTRATE §3 pre-registers and because the level is still what an investor
experiences.

Nothing about the objective the solver optimises changes. This is a change to
what the reported number is measured **against**.

## 4. Owner decision 1 — how the baseline is built

Three constructions. **(a) is recommended.**

**(a) Block-shuffled truth.** Keep the cell's `ic`, `horizon`, `seed`,
constraints and costs exactly as they are, and replace `truth_z` with a
block-shuffled copy of itself before the score is blended. The alpha's magnitude
is then matched *by construction* — same `ic`, same `sigma`, same `horizon` —
and only the alignment with forward returns is destroyed.

Two reasons it is the right primitive, not just a workable one:

1. **It is the only construction that generalises to a real hypothesis.** A real
   signal has no `ic` parameter and no "scale" to match, so (b) is a
   synthetic-ladder-only device. Any signal can be shuffled. If the bar is to
   mean the same thing in phase 3 as it does on the ladder, the baseline has to
   be constructible from the signal itself.
2. **SUBSTRATE §9 already requires this machinery and it does not exist.** §9
   mandates a block bootstrap on the daily panel for the search null and for the
   Romano-Wolf stepdown, block length ≥ the longest signal horizon.
   `src/signal_lab/stats/` is one line. Building the baseline builds the thing
   `veto_multiple_testing` currently reads a verdict from and cannot get.

Sub-decisions inside (a) — recommended, not settled:

- **Shuffle the truth panel along the date axis, in blocks, with the same
  permutation for every instrument.** That destroys timing alignment while
  preserving the cross-sectional covariance of the truth, so the baseline book
  takes tilts of the same size and shape as the live one. A per-instrument
  permutation would also destroy the cross-section and make the baseline a
  different kind of book.
- **Block length = 52 weeks**, the longest signal horizon on the grid, per §9's
  own rule.
- **One baseline per (ic, horizon, seed)**, matched. Pooling baselines across
  seeds would reintroduce exactly the level noise the pairing exists to remove.
- **Shuffles per cell: start at k = 1** and measure the baseline's own dispersion
  before committing. k shuffles cut the baseline's sampling error by sqrt(k) at
  k times the cost; whether that is worth buying is a question for the pilot,
  not a guess now.

**(b) `ic = 0` at a matched alpha scale.** Add `alpha_scale` to `AuditCell` and
run `ic = 0` with the scale matched to each rung. Simpler — one multiply — and
it answers the same question on the ladder. It does not generalise to a real
signal, and it leaves §9's machinery unbuilt. Worth keeping as a **separate,
smaller probe** for a different question: the ladder confounds information
content with view magnitude (`alpha = ic * sigma * score / sqrt(h)` sets both),
and `alpha_scale` is the only way to separate them. That is not this record.

**(c) The minimum-tracking-error book.** What `ic = 0` produces today, because
`portfolio/long_only.py`'s tie-breaker resolves a zero alpha to the minimum-TE
book — the comment names "the IC = 0 rung of the ruler audit" explicitly.
**Rejected as the baseline:** it runs the least tracking error it can, where the
live book runs 4.4-5.6%. It is not the same book, so the difference is not
attributable to information. It is worth reporting once as the replication basis
of the holdable universe; it is not a baseline.

## 4b. Implementation spec — written after reading the code, 2026-09-20

Five things a careful implementer hits that §4 does not settle. They are pinned
here so the implementation is a transcription, not a series of judgement calls.

**1. The shuffle acts on whole date-rows, in contiguous blocks, before
standardisation.** In `audit/signals.py::plant_signal`, `truth = fwd / (sigma *
sqrt(horizon))` is a (dates x ids) panel. Permute its **rows** in contiguous
blocks of **52 rows**, one permutation shared by every instrument, and do it
**before** `_standardise_truth`. Shuffling whole rows is what preserves the
cross-section: the baseline book must take tilts of the same size and shape as
the live one, and only their alignment with the forward return may be broken.
Row-shuffling commutes with both standardisation modes, so the order is a
convenience, not a result.

**2. Re-apply the original availability mask after the shuffle.** The panel is
ragged — series start at different dates and are NaN before. If a date-row moves,
its NaN pattern moves with it, and a series acquires values before its true
daily start. That is a **`frequency` veto breach** (SUBSTRATE §5.1 invariant 2,
§10), introduced by the measurement device rather than by the data. So:

    truth_shuffled = truth_shuffled.where(truth.notna())

Values permute; availability does not. `plant_signal` already does exactly this
for the noise (`noise = noise.where(truth_z.notna())`), so it is the house
pattern, not a new one.

**3. The permutation RNG must be independent of the noise RNG.** `plant_signal`
builds its noise from `np.random.default_rng(seed)`. Drawing the permutation
from that same stream would advance it and change the noise, which destroys the
seed-matching the whole baseline exists for — the live cell and its baseline
would no longer share a noise draw, and the pairing that makes the contrast
worth measuring would be gone. Draw the permutation from a **separate, derived
stream** (`default_rng([seed, BASELINE_STREAM])` or equivalent), and assert in a
test that the noise panel is bit-identical between a live cell and its baseline
at the same seed.

**4. The cell key must encode it.** `AuditCell.key()` builds the run identity
from the fields. A baseline cell has the same `ic`, `horizon`, `seed`,
`cost_multiplier` and caps as its live twin, so without a suffix the two collide
and the results store — which SUBSTRATE §11 makes append-only — would carry two
different runs under one key. Add the field, add the suffix, and test that a
live cell and its baseline produce different keys.

**5. Governance: the standing grid flag is owner-only; the pilot must not need
it.** `ladder.py::grid_cells` reads every optional block from `params/audit.yaml`
(`include_frictionless`, `include_oracle`). A standing baseline block would be
`audit.include_baseline` in that file, which is **owner-only under SUBSTRATE §2
and is not authorised by this record.** And `run_audit.py --lean` hardcodes a
different grid (ICs 0.05/0.10, horizons 4/26, one seed), so it cannot express the
pilot either.

Therefore: build the pilot grid in `ladder.py` as its own function, selected by a
new flag on `scripts/run_audit.py`, and add the target to `build.mk` and to
`scripts/unattended.sh`'s whitelist. All four are agent-writable. **Nothing in
`params/` changes and the default `make audit` path is untouched.** If the owner
later wants the baseline standing in every audit, that is a params patch citing
this record — a separate, later act, and only worth making once the pilot has
said the baseline behaves.

## 5. Acceptance tests — tests, not a one-off check

`decisions/proposed/0035` §4 made the same point about the transfer coefficient
and it applies harder here, because this number would gate.

- A **baseline cell's own excess is zero** to numerical tolerance, by
  construction.
- The **IC 0.02 rung's excess is indistinguishable from zero** — §1 expressed as
  a test.
- An **IC = 1 oracle cell's excess is close to its `net_ir`** — the baseline
  earns the floor, not the oracle's return.
- **The shuffle switched off reproduces today's `net_ir` bit for bit** on a
  fixed cell, so the change is provably additive.
- The shuffle **respects `HOLDOUT_START`**: a permutation must not move an
  observation across the holdout boundary, and must not move a series' returns
  before its true daily start (SUBSTRATE §5.1 invariant 2, veto `frequency`).

## 6. Owner decision 2 — what happens to 0.30

**DECIDED 2026-09-21: position 3 — two bars.** The owner's reasoning, in his own
framing: 150 bp of active return is a satisfactory outcome, *and* he does not
want to arrive at it "simply because I reached an arbitrary combination of betas
that already tends to achieve that 150 bps in the sample period we are
analyzing." Those are two different questions and they get two different bars.

*(A position-2 reading — re-derive a single number — was taken on 2026-09-20 and
superseded the next day once §1's dispersion was stated properly. The record of
the intermediate step is kept rather than erased.)*

### Bar 1 — the product bar, on the level. **net IR ≥ 0.30. Unchanged, and now derived.**

"Is this worth running?" At the 5-6% tracking-error budget, 150 bp of active
return is `150 / 500 = 0.30`. That is the number `decisions/0023` already
carries, which until now rested on a quotation — *"0.3 net IR is a good
target"* — and nothing else. **`params/audit.yaml: target_net_ir` does not
change**; it acquires a derivation.

Two consequences worth recording:

- **`decisions/0025` is unmoved.** It derives the tracking-error budget from the
  IR an investor *experiences*, which is the level, and the level is still 0.30.
  The 5.91%-against-a-6%-mandate result stands, and the coupling this record
  worried about does not fire.
- The precision caveat of §9 still applies to this bar: a cell mean over ten
  seeds carries SE 0.082, so "clears 0.30" read as a lower bound rather than a
  point estimate wants roughly 0.46.

### Bar 2 — the evidence bar, on the excess. **No number. A significance test.**

"Is it signal, or is it this sample's beta?" §1 shows why a threshold is the
wrong instrument here: the floor is the mean of a 420 bp-wide distribution on a
single history, so any number subtracted from it inherits that noise. The right
gate is not *how large* the excess is but *whether it is distinguishable from a
book with the information destroyed*.

**That gate already exists and has never been implementable.** SUBSTRATE §10
lists `multiple_testing`, and `params/vetoes.yaml` already sets
`procedure: romano_wolf`, `fwer_alpha: 0.05`, `level: family_then_within`. §9
already requires the block bootstrap it runs on. What has been missing is
`src/signal_lab/stats/`, which was one line until §4(a)'s block shuffle landed.

So bar 2 is: **`net_ir_excess > 0` and the hypothesis survives Romano-Wolf at
FWER 5% with the excess as the test statistic.** No new veto, no new threshold,
no new parameter — the excess becomes what the existing veto tests, and the
existing α is the bar.

### Why this unblocks L9

The half of `OWNER-QUEUE` L9 that was blocked on tasks 18 and 20 was *the
number*, because the required-IC arithmetic depends on the response shape
between IC 0.20 and IC 1.00. **Neither bar needs that shape.** Bar 1 is a
product statement at a given risk level; bar 2 is a test. **L9 closes.**

Tasks 18 and 20 remain worth running — they measure whether this lab can ever
*detect* a signal that clears bar 2, which is the science. They are no longer
on the critical path of the bar.

### Both must be cleared, and both are disclosed

A candidate clearing bar 1 but not bar 2 is beta that could be bought more
cheaply. A candidate clearing bar 2 but not bar 1 is a real signal not worth the
operational cost. Reporting both says which, where one number said neither.

### What this still needs from the owner

Naming the excess statistic in SUBSTRATE §3, and saying there that
`multiple_testing` runs on it, is an **owner act** under §2. It is not queued and
no agent may originate it. Until it is written, this record is the authority and
`params/` is untouched.

## 7. What is NOT proposed

- **No change to the objective the solver optimises.** SUBSTRATE §3's net IR of
  active return versus the 50/50 benchmark stands.
- **No change to the veto set**, and no new veto. `net_ir_excess` is a reported
  metric under this record; whether it ever gates is §6.
- **No change to `0023`'s number.** §6.
- **No re-run scheduled here.** The pilot and the grid are sequenced in
  `HANDOFF.md` and gated on this record being decided.
- **No claim that this fixes precision.** §9 below.

## 8. Cost

At the measured 74 s a cell (`A-20260919-155557`: 644 cells in 47,908 s), a
baseline for every base cell is 160 cells, about **3.3 hours**. An h13-only
pilot at four rungs and ten seeds is 40 cells, about **50 minutes**.

The baseline is **not** needed for the frictionless twin, the cost grid, the
turnover grid or the per-rebalance grid unless those are to be judged on the new
metric too. If they are, add 324 cells and about 6.7 hours.

## 9. What this does not fix

**Precision.** The floor is a *location* error; the bar also has a *scale*
problem. Its estimator's irreducible standard deviation is 0.250 over the
16.0-year window — `1/sqrt(16)` — so a single cell mean over ten seeds carries
SE 0.082 and a 95% interval of about ±0.16 before any multiplicity correction.
Seed-pairing buys the constrained book only **1.55x** (0.117 unpaired to 0.075
paired), where the frictionless twin gets 17x, because long-only clipping,
position caps, turnover priced off the drifted book and a numerical solver make
the path chaotic in the seed.

The precision answer is to move discrimination onto the terms of
`IR = IC * sqrt(BR) * TC` rather than the product — on the same ten seeds and
the same contrast, realised per-date Pearson IC reads t = 155 where net IR reads
t = 0.4. That is **blocked behind `decisions/proposed/0035`**: TC is the
transfer term and it currently cannot tell a book with a view from a book
without one. Sequence 0035 §4 first.
