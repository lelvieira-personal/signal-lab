# 0023 — The ruler audit, and net IR 0.30 as the bar

Status: decided, 2026-09-11, Leo. Introduces phase 2.5, a seventh owner-only
parameter file, `src/signal_lab/portfolio/` and `src/signal_lab/audit/`.

## What the owner said

> "0.3 net IR is a good target. I approve the decision to build the ruler audit."

And, asked three questions before any code was written:

- the audit ships **the lab's first long-only solver** as the reference
  implementation, not an audit-only copy to be rewritten in phase 2;
- the first real-data run uses the **full grid**, not a lean one;
- the numbers live in a **new `params/audit.yaml`**, owner-only like the other
  six, rather than as a section of `constraints.yaml`.

Context: advice from the Research OS session that the lab should measure the
weekly ETF layer before generating a single hypothesis — the ceiling at the
5–6% TE budget, the implied required IC, the achievable transfer coefficient,
and the effective breadth counted properly rather than as 52 × 30 — and fix the
bar and the charge budget before the agents start, so the trial-count arms race
that ended the SAA programme does not reappear at twenty times the rate.

## Decided

1. **The bar is a net information ratio of 0.30** against the 50/50 benchmark
   over the development window, after the section 8 cost model, at the section 4
   tracking-error budget. It is `params/audit.yaml: target_net_ir`.

2. **Phase 2.5 — the ruler audit — runs before phase 3 opens.** It is a
   computation on returns, the covariance, the constraint set and the cost
   model. It contains no hypothesis, consumes no trial, and carries no
   multiple-testing charge. Its output is a fixed table — the IC a signal must
   carry, at each signal speed, to clear 0.30 net — and that table is what the
   family structure and the per-cycle charge budget are then set against.

3. **The ruler is a simulated-IC ladder through the real pipeline, not the
   analytic fundamental law.** Grinold's IR = IC·√BR·TC is reported beside it for
   intuition, but under long-only, a cash cap, a position cap and a turnover cap,
   with persistent signals on a correlated universe, the analytic decomposition
   is unreliable in both BR and TC. So the audit plants signals of known IC and
   known persistence, runs each through the actual solver, engine and cost model,
   and reads net IR off the result. The gap between the ladder's required IC and
   the law's is the price of the constraints, measured rather than assumed.

4. **The audit ships the long-only solver**, in
   `src/signal_lab/portfolio/long_only.py`. The audit formulation uses a *hard*
   tracking-error budget and so needs neither of the null conviction-scaled
   coefficients from `decisions/0019`: it builds without touching them. The phase
   2 optimiser is this solver plus that penalty once the coefficients exist.

5. **The audit runs outside `run_experiment()` and never touches the
   leaderboard.** Its signals are forward returns with noise — an oracle dialled
   down to a chosen IC — which is a lookahead by construction and would fail the
   `lookahead` veto. That is the point, not a defect, but it means an audit path
   must never be mistaken for a run. Output lives under `results/audit/<run_id>/`
   and carries the panel hash and the params hash, so a table produced on the
   synthetic snapshot cannot be confused with one produced on Bloomberg data.

## What the audit computes

All on weekly returns over the development window, on the investable universe as
of each date, with the benchmark legs carried as pseudo-instruments so tracking
error is measured against the benchmark's own returns rather than a proxy.

**A. Effective breadth, two dimensions, reported separately.** Cross-sectional:
Meucci's effective number of bets — the exponential of the entropy of the
normalised eigenvalues — of the correlation matrix, on total returns and on
returns in excess of the benchmark. Time: independent decisions a year implied
by the signal's measured weekly autocorrelation, `52(1−φ)/(1+φ)`. The product is
the breadth the fundamental law would use. Both dimensions are reported because
they have different fixes: the first is breadth of instruments, the second is
signal speed.

**B. The simulated-IC ladder.** IC ∈ {0.02, 0.05, 0.10, 0.20} × horizon ∈
{4, 13, 26, 52} weeks × 3 seeds. The signal blends the standardised forward
active return with persistent noise; alpha follows Grinold. Each cell is solved
weekly, run through the engine, charged by the cost model. Net IR, realised TE,
turnover, cost drag, active drawdown and the share of rebalances on which each
constraint bound are recorded per cell. The IC = 1 oracle is run and reported as
a ceiling, labelled as such — it is not the ruler.

**C. Required IC.** Per horizon, the IC at which mean net IR crosses
`target_net_ir`, interpolated, with the seed range. This is the table the bar is
set against, and a bar never reached inside the grid is reported as a bound
rather than as a number.

**D. Costs, net first.** Every IR is net. Half-spread stress at 1×, 2× and 3×.
Turnover-shortfall curve at caps of none, 150%, 100% and 50%, so the alpha lost
to the turnover constraint by signal speed sits beside the explicit cost.

**E. Holdout power, stated once.** The holdout is roughly 350 weeks. A strategy
with a true net IR of 0.30 yields a holdout t-statistic near 0.30·√6.7 ≈ 0.8.
**The holdout cannot confirm a strategy at conventional significance; it can only
fail one.** The bar is cleared on the development window under Romano-Wolf, and
the holdout is a falsifier. This belongs in SUBSTRATE section 3 at the next
amendment round, so a holdout IR of 0.6 is never read as confirmation.

## The solver, and four things found while building it

`maximise a'w − c'|w − w₀| − λ(Sw − b)'Σ(Sw − b)` subject to the section 4
constraint set with a hard TE budget, cvxpy with the chain in
`params/constraints.yaml` and a scipy SLSQP reference implementation the test
suite checks it against. `λ` is a tie-breaker, worth under a tenth of a basis
point at the budget, so it never competes with alpha but makes the answer the
minimum-tracking-error book when there is no alpha.

Four defects, each found by a measurement rather than by reading the code, and
each recorded because the same mistake is available to the phase 2 optimiser:

1. **The engine read the benchmark on the rebalance date, not over the period.**
   It compounds the strategy's daily returns through the week, then took the
   benchmark's single return on the Friday. A week of strategy return against a
   day of benchmark return: the "active return" was mostly the strategy's own
   gross return. The planted path never exposed it because its benchmark is
   built per period; the synthetic benchmark and the nightly cycle both pass
   daily series and would have.

2. **Shrinking a benchmark leg alongside the holdables made the budget look
   infeasible.** Every shrinkage target pulls the leg's correlations toward an
   average, so a book replicating the leg almost exactly was told it carried
   6–10% of tracking error while its realised tracking error was under 1%. The
   legs are now priced through their long-only tracking portfolios, and the
   replication R² is recorded at every rebalance. The holdable block also moved
   from the identity target (Ledoit-Wolf 2004) to constant correlation (2003).

3. **The infeasibility fallback dropped the turnover cap.** A drifted book
   marginally outside the budget made the problem infeasible; the fallback then
   traded without a cap, and the 25%-cap cell reported 70% annual turnover. The
   cap is now relaxed only to repair a cash-cap or position-cap breach — a
   mandate breach must be traded back whatever a turnover budget says — the
   repair is the smallest compliant trade rather than the minimum-TE book, and
   the overspend is repaid out of following weeks' allowance.

4. **The reference solver returned the first feasible answer, not the best.**
   "Stay put" is feasible in most weeks and SLSQP barely moves from it when the
   alpha is small, so the IC = 0 rung held whatever book it opened with at 4%
   tracking error instead of hugging the benchmark.

A fifth, in the audit rather than the solver: **the planted noise is now
orthogonalised against the truth.** A raw blend gives the target IC only in
expectation, and because the noise is persistent the effective sample behind
that correlation is a fraction of the cells — enough to label a 0.10 rung with a
signal carrying 0.07. The realised IC is still measured and reported; it is now
a check on the arithmetic rather than on luck.

## Parameters (`params/audit.yaml`, owner-only)

`target_net_ir: 0.30`; `ic_grid`; `horizon_weeks`; `seeds: 3`;
`include_oracle`; `cost_multipliers`; `turnover_caps`; `turnover_bank_periods`;
`stress_horizon_weeks`; `covariance: {window_periods: 156, estimator:
ledoit_wolf}`; `rebalance_day: FRI`; `solver: auto`; `output_dir`. All six other
parameter files move to `params_version: 0.5.0` so the set still agrees.

## Validation before real data

`make audit-lean` runs the ladder on the synthetic panel, where the planted IC
is known exactly. The test suite asserts the realised IC equals the planted one
at every rung, that the oracle beats a blind signal through the full pipeline,
that a blind signal hugs the benchmark, and that the turnover cap holds on
average. What it does **not** assert is monotonicity of net IR in IC on the
synthetic panel: on one seed and a short window the ordering is noisy, and
forcing it would be a test of the fixture. Monotonicity is a property to read
off the real table across three seeds, and a non-monotone real table is a
finding, not a pass.

## Still open, deliberately

- Whether the table becomes the per-cycle charge budget directly or through a
  further decision once the family structure is written into the hypothesis
  registry. This decision fixes the bar; it does not yet fix the budget.
- The cvxpy path has never been executed: the container this was built in has no
  cvxpy, so the solver ran on the scipy reference implementation throughout and
  the cross-implementation agreement test skipped. It runs for the first time
  under `make check` on the owner's machine. Until it passes there, the cvxpy
  formulation is unverified.
- A turnover cap below the level drift alone requires cannot bind exactly. At
  25% a year on a weekly 6%-TE book the repairs dominate, and the realised
  figure sits above the cap. The audit reports `repair_share` per cell so such a
  cell is visibly not measuring the cap; the grid's lowest cap is 50%.
- Region labels (`decisions/0022`) remain a placeholder. The audit does not need
  them at weekly frequency; the phase 2 daily covariance does.
