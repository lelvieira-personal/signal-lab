# 0030 (PROPOSED) — Realised tracking error is a disclosed characteristic, not a gate

Status: **proposed, 2026-09-18**, from the owner's call on `decisions/0027`
§2 ("make it a disclosed characteristic"). Removes the `tracking_error` veto and
promotes `risk_calibration` in its place. Amends SUBSTRATE §4 and §10, and
`decisions/0026` §"The residual risk, and the successor check". Touches
`vetoes/`, `params/vetoes.yaml`, `SUBSTRATE.md` — owner-only paths, so nothing
here has been applied.

Evidence: `results/audit/_probe/TE-20260917-*` (the TE path probe and the
volatility overlay), `scripts/bias_map.py` (the null distribution below).

## What the owner said

> "0027 - make it a disclosed characteristic"

## Decided

**1. The `tracking_error` veto is removed.** The 95th percentile of trailing-3y
realised tracking error is reported everywhere — on every run's summary, in the
audit's cell table, and in a named section of the report — but it no longer
kills anything. The tracking-error budget remains a hard **ex-ante** constraint
in the solver (`constraints.tracking_error.max_trailing_3y`, a different
parameter from the veto's), so the mandate still binds where the book is built.

**2. `risk_calibration` becomes the tenth veto**, on the **worst annual** bias
statistic rather than the full-sample one. The veto set stays at ten.

## Why the level stops being a gate

`decisions/0024`–`0026` already say it: risk is sized ex ante and priced, never
gated ex post. The tracking-error veto was the last place the lab did the
opposite, and the TE path probe showed what it was actually measuring.

**The overrun is one episode, not sampling error.** Across the nine Bloomberg
base cells, the share of trailing-3y windows over the 6.0% budget is zero in
2006, 2012–2015 and 2019, and 87–100 per cent in 2009–2010. Drop every window
containing 2008-01…2009-12 and the low-IC cells stop breaching entirely. The
premise 0027 §2 offered — a noisy upper tail firing at random — is refuted.

**What the veto kills is a property of the world, not of the book.** Active
volatility clusters. A book honestly sized to 6.0% will run above it in a
crisis and below it in a calm decade, and killing the run that lived through
2008 does not reduce the risk taken — the ex-ante budget already did that. It
deletes the evidence, and it selects the leaderboard on which sixteen years a
strategy happened to be tested in. That is the same argument `decisions/0026`
made against the realised-drawdown cap, applied to the one gate it left
standing.

**And it makes the ruler unreadable.** Under the current wiring 40 of 48 base
cells in A-20260917-020949 fail the TE veto and no cell above IC 0.02 survives
at any horizon, so the audit's "surviving cells" bar is unreachable by
construction. A gate that no honest book can pass is not governance.

## Why something still has to gate, and what

`vetoes/rules.py` calls the tracking-error veto "the lab's only ex-post risk
gate", and `decisions/0026` leaned on it explicitly when it removed the
drawdown cap: *"The tracking-error veto catches the realised TE, but nothing
currently asks whether the drawdown the budget implied matched the drawdown
that arrived."* Removing it without a successor would leave the lab with no
ex-post check of any kind on a risk model that turns out to be wrong.

So the split is between two different questions, which the old veto conflated:

- **How much risk did the book run?** A characteristic. Disclosed.
- **Did it run the risk it was sized for?** A defect if the answer is no, and
  that is what gets vetoed.

The statistic is the one `decisions/0027` §2 introduced — the standard
deviation of `z_t = r_t / sigma_ex_ante(t-1)`, which is 1 when a book realises
the risk it was sized to — **read on the worst year rather than the whole
sample.**

**The full-sample reading has no power, measured.** Across seventeen Bloomberg
base cells the full-sample bias is 0.87 to 1.05 — inside its own ±0.048 band —
while the same cells' worst year runs 1.39 to 2.21, hitting 2.03 in 2008 at
IC 0.20. With the volatility overlay of the TE probe applied, the full-sample
reading is 0.89 to 1.03: **indistinguishable from the broken case**, while the
worst year falls to 1.17 to 1.61. A gate on the full-sample number would have
passed a book running twice its sized risk for a year, and would not notice the
fix either.

## The threshold, derived not chosen

`scripts/bias_map.py` simulates the distribution of the worst annual bias
reading under a **correctly specified** model, so the threshold is a property
of the null and not of any book. Two features of the real `z` series drive it,
both measured on the seventeen Bloomberg base cells:

- **excess kurtosis 2.37** (range 1.04 to 14.65). Tails enter the sampling
  variance of a standard deviation directly, `Var(s^2) = sigma^4 (2/(n-1) +
  kappa/n)`. At kappa = 0 the annual standard deviation is 0.099; at 2.37 it is
  0.146. Deriving the threshold under a Gaussian null would set it about 47 per
  cent too tight and the veto would kill honestly sized books.
- **lag-1 autocorrelation −0.068** (range −0.105 to 0.036), so materially
  absent. It stays a knob because a future signal set could change it.

Worst annual reading over 16 years of 52 readings, 40 000 paths:

| excess kurtosis | median worst | p95 worst | p99 worst | full-sample |
|---|---|---|---|---|
| 0.00 | 1.168 | 1.274 | 1.327 | 1.000 |
| 1.00 | 1.207 | 1.369 | 1.477 | 1.000 |
| **2.37 (measured)** | 1.243 | **1.491** | **1.715** | 0.999 |
| 4.00 | 1.268 | 1.597 | 1.921 | 0.999 |

The full-sample column is the control: it is 1.000 under the null whatever the
tails, which is another way of saying the statistic `decisions/0027` gates on
today cannot distinguish anything.

**Proposed threshold: the p99, 1.72 at the measured kurtosis.** Not the p95,
for the reason `decisions/0026` gave against the drawdown cap — *"a p95 target
makes breaches mandatory by construction… one run in twenty is designed to
exceed it"*. A gate with a 5 per cent by-design false-positive rate kills one
honest book in twenty, and the audit judges about 150 cells a run, so p95 would
fail roughly seven of them on the null alone against about one and a half at
p99.

What the two thresholds do to the evidence on hand:

| | worst-year range | fails at p95 (1.49) | fails at p99 (1.72) |
|---|---|---|---|
| baseline, 17 cells | 1.39–2.21 | 12 | 5 |
| volatility overlay, 11 cells | 1.17–1.61 | 3 | **0** |

The threshold was fixed by the null before either column was computed. It is
not tuned to make the overlay look good.

## What this does NOT do

It does not raise the risk appetite. The 32 per cent drawdown tolerance of
`decisions/0025` and the 6.0 per cent ex-ante budget it implies are unchanged,
and the solver still enforces the budget at every rebalance. Risk control moves
entirely to the point where it can act.

It does not turn the volatility overlay on. The overlay is opt-in code with no
parameter reading it, tested at one horizon, two IC rungs and one halflife.
Whether it becomes policy is a separate decision and this one does not presume
it.

## Open, and deliberately

- **The threshold percentile** is the one number here that is a judgement
  rather than a derivation. p99 is recommended and p95 is a one-line change.
- **Threshold sensitivity to kurtosis is material**: p99 runs 1.48 at kappa = 1,
  1.72 at 2.37, 1.92 at 4.0. The measured median is 2.37 but one cell read
  14.65. Whether the threshold should be set at a conservative kappa, or the
  kurtosis re-measured per run, is unsettled.
- **The simulation assumes `sigma_ex_ante` is known**, while in the lab it is
  itself an estimate, which adds variance to `z` beyond the null. The derived
  threshold is therefore, if anything, slightly too tight. Quantifying that is
  not done.
- **A minimum-observations rule** is needed for a partial calendar year: the
  Bloomberg cells all carry 52–53 readings in every one of 16 years, so nothing
  forced the question, but a run over a shorter window will hit it. Proposed:
  a year with fewer than 40 readings is not read.

## Changed (nothing applied)

- `vetoes/rules.py` — `veto_tracking_error` removed; `veto_risk_calibration`
  added, reading the worst annual bias against `params/vetoes.yaml`
- `vetoes/registry.py`, `vetoes/__init__.py` — VETOES and SUBSTRATE_VETOES swap
  `tracking_error` for `risk_calibration`; still ten
- `params/vetoes.yaml` — the `tracking_error` block replaced by
  `risk_calibration` (`statistic: worst_annual_bias`, `max: 1.72`,
  `min_observations_per_year: 40`), and its `evaluation.order` entry
- `SUBSTRATE.md` — §10 row replaced; §4 now reads that the realised tracking
  error is a reported characteristic and the ex-ante budget is the constraint
- `src/signal_lab/harness/run_context.py` — **a new `te_ex_ante` field.** The
  veto cannot be evaluated without it, and `params/vetoes.yaml` sets
  `on_missing_input: fail`, so every run path has to supply it or every run
  fails closed. This is the largest piece of work in the series and it is not
  optional.
- `src/signal_lab/audit/ladder.py` — `risk_calibration` gains the worst-annual
  reading and the year it fell in; the per-cell verdict swaps vetoes
- `src/signal_lab/audit/report.py` — a named **Risk characteristics** section:
  ex-ante budget against realised p95 and max, the worst trailing-3y window and
  when it occurred, the annual bias profile, and the episode breakdown
- `render/views.py`, `render/mock_data.py` — the veto row swapped, the TE
  charts kept and promoted
- `scripts/bias_map.py` — new, the derivation above (already written, ruff
  clean, not yet committed)
