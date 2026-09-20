# 0036 — The bar is measured as excess over a no-information baseline

Proposed 2026-09-20 by Cowork. **DECIDED by the owner 2026-09-20: §3 and §4(a)
taken — the metric is reported as excess over a block-shuffled, seed- and
magnitude-matched baseline. §6: the owner chose
**position 2 — re-derive the number** (2026-09-20). The number itself is NOT
set; `decisions/0023` and `params/audit.yaml: target_net_ir` are untouched and
stay at 0.30 until it is. See §6 and `OWNER-QUEUE` L9.** §4(b), the `alpha_scale` knob, is not
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

**DECIDED 2026-09-20: position 2 — re-derive the number.** Positions 1 (keep
0.30 on the excess metric) and 3 (two bars) are not taken. Recorded here; the
number is not set and `params/audit.yaml` is unchanged.

Why position 1 was refused, for the record. Keeping 0.30 on excess would require
**18% / 30% / 34% / 69%** of a *perfect* forecast's excess at h4 / h13 / h26 /
h52, which translates to a realised IC between **0.18 and 2.31** depending on
which response shape is assumed — against real macro signals at IC 0.02 to 0.10,
and with several readings above 1.00, which is impossible. The largest excess any
of the 484 judged cells produced over its own floor was **+0.083**. It would be a
bar nothing could clear.

### Two things the word "re-derive" has to confront

**1. There is nothing to re-derive it *the way 0023 did*, because 0023 did not
derive it.** `decisions/0023` records the bar as a quotation — *"0.3 net IR is a
good target"* — and `params/audit.yaml` line 11 carries that quotation as the
comment above `target_net_ir`. It was stated, not computed. `0027` did not touch
it either; its recalibration was of the breadth dimension.

So a derivation needs a **new input the owner supplies**, exactly as
`decisions/0025` needed the drawdown tolerance before it could produce a TE
budget. Three candidate inputs, none chosen here:

- a target **active return** over the 50/50 benchmark at the 5-6% budget, from
  which the IR falls out;
- an external reference — what an institutional multi-asset overlay is expected
  to deliver net of the §8 cost model;
- **the measured floor plus a stated margin**, which is the most direct reading
  of this record but is circular unless the margin itself is argued from
  something.

**2. The bar and the tracking-error budget are coupled, and the arrow runs from
the bar.** `decisions/0025` derives the TE budget *from* the target IR —
*"at the lab's own target of net IR 0.30, the implied budget is 5.91%"*, against
a 32%-at-p95 drawdown tolerance. **Changing the bar therefore propagates into the
constraint set every audit has run under.**

One subtlety that decides how far it propagates: 0025's input is the IR an
investor *experiences*, because drawdown is experienced on the level and not on
the excess. If the re-derived bar is an excess bar, the level implied by it is
`excess + floor`, and the floor is 0.311 on this window. A re-derivation that
forgets this would feed an excess number into a formula expecting a level and
move the budget the wrong way.

**Neither of these is settled here, and the number remains blocked on tasks 18
and 20**, which pin the response shape the required-IC arithmetic depends on.

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
