# 0027 — Calibrating the ruler after the first lean audit

Status: decided, 2026-09-16, Leo. Amends `decisions/0023` §A (time breadth) and
adds a cell family to its grid; touches `params/audit.yaml`. Holds
`decisions/0025` unwired. Does not change any veto or any threshold.

## Context

The first `make audit-lean` (A-20260916-181109, synthetic, 4 cells, one seed)
ran end to end in 384 s, about 96 s a cell. Reading it turned up four problems.
The owner chose among the options put to him; his choices are quoted as he
selected them.

| cell | net IR | TE p95 | mean ex-ante TE | turnover | verdict |
|---|---|---|---|---|---|
| ic0.05 h4 | 0.26 | 5.84% | 5.76% | 167% | cash 0.2000000005 > 0.2 |
| ic0.10 h4 | 0.86 | 6.46% | 5.89% | 320% | TE, cash |
| ic0.05 h26 | 0.32 | 5.17% | 5.37% | 19% | pass |
| ic0.10 h26 | 0.42 | 5.94% | 5.68% | 77% | cash 0.20000000075 > 0.2 |

One seed over a 16-year window gives a standard error of roughly 0.25 on an
annualised IR, so no difference in this table is decision-grade. The lean grid
also has no per-session, cost or turnover cells, so the per-session cap
(`decisions/0024`) cannot be chosen from it.

## 1. The solver's book is projected onto the mandate — *"Fix it in the solver"*

Two of the three veto failures were solver tolerance: CLARABEL landed cash
5e-10 above its cap. The veto's 1e-9 relative tolerance (0024 addendum) is for
summation error, and **it stays**. The solver now projects every book onto the
mandate exactly and reports how far that moved it, and the audit counts
`optimal_inaccurate` solves and records which solver actually ran. Neither the
veto nor any params file changes for this.

## 2. The TE budget and the TE veto — *"Measure first"*

The solver's hard budget is 6.0% ex ante. The veto reads the p95 of realised
trailing-3y TE against the same 6.0%. A book that uses its budget can fail on
sampling error alone: ic0.10/h4 averaged 5.89% ex ante and realised a p95 of
6.46%. This has the same structure `decisions/0026` removed for drawdown: a
target set at the veto level makes some breaches mandatory. With 0025's
`may_exceed_mandate: true`, it also means that any derived budget much above
~5.5% would be vetoed in practice.

**Decided: nothing changes yet.** `budget_from_drawdown.enabled` stays `false`.
Every audit cell now reports the evidence, and none of it gates anything:

- `te_realised_to_ex_ante`: realised active volatility over the mean ex-ante TE;
- `te_p95_to_ex_ante` and `te_p95_to_budget`: how far the statistic the veto
  reads sits above what the solver aimed at;
- `bias_stat`: the standard deviation of each period's active return divided by
  the ex-ante TE the book was sized to. It is 1 when the risk model is
  calibrated, with an approximate 95% band of ±1.96/√(2T) printed beside it.

Whether the solver aims below the veto, the veto reads something else, or the
thresholds move is decided after `make audit` on Bloomberg data.

The **statistic for the `risk_calibration` check** named in `decisions/0026` is
still open. `bias_stat` is reported as a candidate. The alternative is 0026's
realised maximum drawdown against the ex-ante p95, which has one observation per
run and, at a p95 target, fails one run in twenty by design.

## 3. A frictionless cell calibrates the ruler — *"Add a frictionless check cell"*

At h26 the lean audit's constrained book cleared 0.30 at IC ≤ 0.05, but the
fundamental-law column said IC 0.098 was needed at a transfer coefficient of
one. A constrained, costed book cannot beat a frictionless ceiling, so the
breadth behind that column was wrong. Its time dimension, `52(1−φ)/(1+φ)` at
φ = (h−1)/h, is about 52/(2h−1): half the non-overlapping count 52/h that
matches how the ladder defines IC (a correlation with the h-week forward
return).

**Decided:**

- **Time breadth is 52/h** in `decisions/0023` §A. The measured φ is still
  reported beside it.
- **A `frictionless` cell family** runs at every (IC, horizon, seed) of the
  base grid, and in the lean grid too. It uses the same planted signal and the
  same estimated covariance, with no long-only constraint, no caps, no cash
  limit and no costs. Its active book is the mean-variance direction
  Σₓ⁻¹α, scaled each week to the tracking-error budget. Solving it is a linear
  solve, not a QP, so it costs seconds.
- It is a **ruler for the ruler**. Up to covariance error it should reproduce
  the fundamental law with TC = 1. The report now reads the chain in three
  steps:
  1. formula breadth against **empirical breadth** (the squared slope of
     frictionless IR on IC, per horizon);
  2. frictionless IR against the fundamental law, which isolates covariance
     error and the breadth formula;
  3. **base IR over frictionless IR** at the same (IC, horizon, seed), which is
     the measured price of long-only, the caps and costs.

  The sentence the report used to print about the gap is replaced by those
  three measurements.
- `params/audit.yaml: include_frictionless: true`.

## 4. The next run — *"Bloomberg audit"*

After these patches: first the Bloomberg loader against the real workbook,
which has never run; then `make audit` on the full grid, about 4 h at the
measured pace. The per-session cap, the TE question in §2 and the
`risk_calibration` statistic are all decided from that run, not from synthetic
data.

## Also found, and fixed without an owner decision

- The synthetic panel was costed entirely at the high bucket (20 bp spread,
  35 bp fee). Its `SYN###` ids are absent from `investable_universe.csv`, so
  every series fell to `default_bucket`, even though the panel carries its own
  `cost_bucket`. The audit now uses the panel's bucket where the universe map
  has none. That is `decisions/0002` as written: the dear bucket is for an
  instrument *with no bucket*. Bloomberg tickers are all in the map, so their
  costs do not change.
- Report presentation: bounds are printed as bounds ("< 0.050"); the seed range
  reads "n/a" with one seed; the stress tables state the horizon they actually
  used; docstrings no longer mention a fifth portfolio veto.
- For the record: the mid bucket is a **10 bp** half-spread plus a 15 bp fee,
  not the "15 bp spread" some notes carried. The 43 bp backstop in
  `decisions/0024` is therefore about 4× the mid spread, not 3×.

## Changed

- `src/signal_lab/portfolio/long_only.py`: `_polish`, `Solution.inaccurate`,
  one solver-chain helper
- `src/signal_lab/audit/ladder.py`: calibration columns, the frictionless
  cell, panel cost buckets, solver provenance
- `src/signal_lab/audit/breadth.py`: time breadth 52/h; φ still reported
- `src/signal_lab/audit/report.py`: the calibration and frictionless sections,
  bounds shown as bounds
- `params/audit.yaml`: `include_frictionless`
- `decisions/0023`: §A amended by reference to this record
