# 0059 — The phase-2 solver: views become alphas on the exposure map, one rebalance step for the lab

**Status:** decided 2026-10-14 by the owner (OWNER-QUEUE L37: "agree with
proposal"). Drafted by Cowork at the owner's request ("yes", 2026-10-12). Four
design points were ruled on 2026-10-12 (each the option Cowork recommended;
"What the owner decided"); the five open points were ruled on 2026-10-14, each
as Cowork proposed ("The five open points, ruled"). The rest of the draft is
adopted with them (Cowork's reading of "agree with proposal"). Follows `decisions/0019`, `0040`, `0042`, `0043`, `0044`,
`0050`, `0051`, `0055`, `0057` and `0058`. **Needs a params patch
(owner-only)**, written by Cowork after the `huber6-v4` params patch so the two
do not collide; no change to `vetoes/` and none to `SUBSTRATE.md`. **Nothing is
built from this record until a HANDOFF task says so.** The registry questions
it exposed (OWNER-QUEUE L38) are ruled in `decisions/0060`.

## The question

`decisions/0051` ruled the form: each view becomes expected returns on the
instruments that carry its axis, and `portfolio/long_only.solve` sizes the
book under §4. It left open how a score becomes a view in return units, what
the two expressions of §6 mean on an axis, and what the solver must pass on
planted signals before a registered hypothesis runs. `build_weight_rule`
still raises `OptimiserMissing`.

## What the owner decided (2026-10-12)

1. **A view's scale is Grinold's, with one fixed IC prior.** For axis *k* at
   rebalance *t*:

       v_k(t) = IC_prior × σ_k(t) × z_k(t) / √h

   `IC_prior` is one number in `params/`, the same for every hypothesis. It is
   never estimated from the run, so it adds no fitted parameter and cannot be
   tuned per hypothesis. This is the construction the ruler audit already uses
   (`audit/signals.py`, step 4), so phase-2 numbers stay comparable with it.
2. **Directional and cross-sectional are defined, and `both` is two tests.**
   - *Directional:* one view per group, from that group's own time-series
     score, not demeaned. On an axis with no grouping there is one group, so
     one view.
   - *Cross-sectional:* the groups' scores demeaned across groups at each
     date, so the views sum to zero across groups.
   - A hypothesis registered `expected_expression: both` is **two tests** in
     the stepdown (SUBSTRATE §9). The registry's *m* counts both.
3. **The tracking-error budget stays hard** at 6% ex ante (`decisions/0044`).
   The `decisions/0019` coefficients stay null; conviction stays H-2026-0012's
   question. *Consequence, recorded so it is not rediscovered:* a week whose
   alpha clears the cost hurdle spends close to the whole budget however weak
   its score. Only costs and the shadow turnover cost keep a weak week quiet.
4. **Acceptance is pilot first, thresholds second.** The hard checks below are
   fixed now. A short pilot then proposes the numeric pass bars, and the owner
   rules them in an addendum before the acceptance run.

## The draft — NOT ruled

### A. What a view is, per axis

A view is the expected per-week move of the axis's factor, signed so that a
positive view favours instruments with a positive cell on the axis. With the
exposure cells of `decisions/0050`, an instrument's alpha is

    alpha_i(t) = Σ_k  X_ik(t) × v_{k, g(i)}(t) × m_ik

where `X_ik` is the axis cell `ExposureMap.at(t)` returns, `g(i)` is the
instrument's group on the axis, and `m_ik` is the scope mask (`0057`): 1 if
the instrument matches the hypothesis's scope and 0 if it does not or lacks
the label. With no scope, `m` is 1.

| Axis | Cell `X_ik` | Factor the view is on | `σ_k`, trailing |
|---|---|---|---|
| duration | measured OAD or minus the real-yield loading | minus the weekly change in the 10y real yield (decimal) | the real-yield factor's volatility |
| real_nominal | minus the inflation loading | minus the weekly change in the 10y breakeven | the inflation factor's |
| credit | minus the credit loading | minus the weekly change in the credit spread (`BAA10Y` from `huber6-v4`) | the credit factor's |
| cash | 1 for cash, else 0 | cash's weekly return less the benchmark's | that difference's |
| region | 1 where `region_view` is yes and the instrument is in group *r*, else 0 | group *r*'s weekly return less `NDUEACWF` | that difference's, per group |

- **A region group's return** is the equal-weighted mean of its `region_view`
  instruments that hold a row at *t*. No new choice of index is made.
  *Cowork's proposal.*
- **`σ_k` uses the covariance's window and overlay:** 156 weeks and the
  scalar 26-week overlay of `decisions/0042`, read through the same resolver,
  so one risk model serves every book (SUBSTRATE §4).
- **Units.** The three yield-like factors are in decimal (`measurement/factors.py`),
  so an OAD in years times a view in decimal yield is a return. The same holds
  for the loadings, which is what `0050` relies on.
- **Equity, dollar and commodities stay columns, not axes** (`0050` item 3).
  They are reported, never targeted.

### B. The score a signal module hands over

The solver does not build signals; `signals/` does, in phase 3. The contract:

- A frame of **raw scores**, dates by groups, each value dated by its
  knowledge date. A slow signal holds its vintage value between releases
  (SUBSTRATE §6).
- **`z` is built in one place, by the rule, not by each module:** an
  expanding-window mean and standard deviation of the knowledge-dated scores,
  winsorised at ±3, after a burn-in of 156 weeks of score history. Before the
  burn-in is met the view is zero, and the book is the minimum-TE book the
  tie-breaker gives. *Cowork's proposal; the burn-in matches the covariance
  window so neither starts before the other.*
- **The standardisation is an estimated parameter.** Its mean and standard
  deviation, and every `σ_k`, join `parameter_usage` with `fitted_through`
  and `used_on_date` (see D).
- **`h`** is the geometric mean of the hypothesis's `horizon_weeks` range,
  rounded: 4-13 gives 7, 8-26 gives 14, 13-52 gives 26. *Cowork's proposal.*
  It only scales the view, and in a single-hypothesis run that trades against
  costs, not against the budget.

### C. One rebalance step for the lab

The ruler audit's weight rule (`audit/ladder.py`, the class whose `__call__`
builds the covariance, the spec, the cost vector and the `0040` shadow term,
then calls `solve`) is already the phase-2 rebalance with a planted alpha.
**Extract that sequence into one `portfolio/` rebalance step and have the
audit call it,** rather than writing a second copy. That honours the three
requirements HANDOFF lists for the phase-2 solver (overlay through the
resolver, turnover through `harness.objective.created_marginal_*`, the gate
through `stats.multiple_testing.gate`).

- **The gate for the extraction:** every recorded audit number it can reach
  reproduces exactly, as task 48 reproduced the run of record. If one moves,
  the task stops.
- **The phase-2 rule** then differs from the audit's in one place: where its
  alpha comes from (section A instead of a planted instrument-level frame).
- **Holdable at *t*** means: investable, with a full covariance window, and
  with an exposure row. An instrument without a row has no alpha and is not
  holdable (task 54's `NoExposureRow` already refuses a weight on one).

### D. Lookahead

`parameter_usage` gains rows beside the loadings, with a `parameter` column
naming each kind: `covariance` (fitted through the last week of its window),
`sigma_<axis>` and `zscore_<hypothesis>`. The veto reads only
`fitted_through` and `used_on_date` (`vetoes/rules.py`, the second half), so
**no veto change is needed.** *Cowork's reading of the veto; the build task
tests it with a late row of each kind.*

### E. What every run reports (`0051` item 4)

- **Active exposure on each of the six factors and each axis,** per
  rebalance. The benchmark's exposure comes through its replicating portfolio
  (`portfolio/covariance.embed_benchmark_legs`), because the legs have no row
  in the store. *Cowork's reading of the code, not checked on a run.*
- **Each factor's share of ex-ante tracking variance** (Euler: exposure times
  the factor covariance times the exposure vector, over the total), and the
  residual share. This is the control the `0051` caveat asks for: a sector or
  region book that is quietly long equity beta shows it here every week.
- The realised active exposure on the target axis against the score, as a
  transfer measure.

### F. The hard checks, fixed now (owner, 2026-10-12, item 4)

Each is a test in the build task:
1. `solve_cvxpy` and `solve_reference` agree on the phase-2 rule's problems,
   at the tolerance the suite already uses.
2. A zero view gives exactly the minimum-TE book.
3. On a fixed date: a positive directional duration view raises the book's
   active duration against a zero view; a cross-sectional +1/−1 on two
   regions raises one region's weight and lowers the other's.
4. A region view reaches only `region_view` instruments; a scoped view
   reaches only matching instruments; an instrument without the label gets
   zero alpha.
5. `lookahead` passes on an honest run, and fails on one late row of each new
   parameter kind.
6. Nothing on or after 2020-01-01 is read.
7. The exposure and tracking-variance tables of E are on every run.

### G. The pilot (proposes the thresholds)

- **Planted at the axis level,** on real development-window returns: the
  truth is the forward *h*-week move of the axis factor (directional) or of
  each group's relative return (cross-sectional), and the score blends it
  with orthogonalised AR(1) noise at the planted IC, the same way
  `audit/signals.py` does for instruments.
- **Grid:** duration directional and region cross-sectional; planted IC 0,
  0.05, 0.10, 0.20, 0.35; *h* = 13; five seeds; each run with its
  block-shuffled baseline for bar 2. That is 50 runs and 50 baselines. **Plus**
  `IC_prior` at half and twice the proposed value on the IC 0.10 cells, to
  show how much the prior moves the answer through costs.
- **Runtime:** *a guess from the audit's ~75 s a cell:* two to three hours.
- **It reports:** net IR and `net_ir_excess` by planted IC; the bar-2 pass
  rate at IC 0 (the false-pass rate); the transfer measure; the share of
  tracking variance in equity beta; turnover; `bias_stat`; the inaccurate
  and infeasible shares.
- **From it Cowork proposes:** a dose-response bar (for example, net IR
  rising with planted IC, with the IC 0.35 cells clear of the IC 0 cells) and
  a false-pass bar at IC 0. The owner rules them; then the acceptance run.

## The five open points, ruled (owner, 2026-10-14)

Ruled as proposed (owner, 2026-10-14: "L37: agree with proposal"). The text
below is the proposal as it stood, unchanged.

1. **The value of `IC_prior`.** *Cowork proposes 0.05.* That is a prior, not
   a measurement: realistic macro-signal ICs are usually quoted between about
   0.02 and 0.10, and the pilot shows the sensitivity.
2. **`h` as the geometric mean of the horizon range** (B).
3. **The 156-week burn-in and the ±3 winsorisation** (B).
4. **The extraction of the audit's rebalance step** (C), gated on exact
   reproduction, against writing the phase-2 rule separately.
5. **Equal-weighted region baskets** for the region factor's return (A).

## What it exposes in the registry

Cross-sectional is defined across groups, and an axis has groups only through
region or a `group_by` (`0057`). Four pending hypotheses ask for a
cross-section on an axis with no grouping registered:
- **H-2026-0002** (real/nominal, `both`) and **H-2026-0003** (duration,
  `both`): their directional test is defined; their cross-sectional test is
  not.
- **H-2026-0007** (credit, cross-sectional, "OAS z-score vs own 5y history")
  and **H-2026-0010** (duration, cross-sectional, "duration carry, term
  spread"): their only test is undefined. *Cowork's reading:* both read like
  instrument-level scores (one OAS or one carry per index), which `0051` does
  not authorise.

Each needs a registered `group_by`, a change of expression, or a ruling on
instrument-level signals **before any result is seen** (`0057` rule 1). That
is an OWNER-QUEUE item, not something this record decides.

*Ruled 2026-10-14 (owner, OWNER-QUEUE L38): see `decisions/0060`.*

## What it does not decide

- **Aggregation across hypotheses and families** (§6's shrunk z-score
  average). The first solver runs one hypothesis at a time.
- **Instrument-level signals** (`0051`).
- **Conviction** (`0019`, H-2026-0012).
- **The pass thresholds** (owner, after the pilot).
- **The first date of a run.** It follows `0058`: once `huber6-v4` is pinned
  the matrix covers `dev_start`. The covariance and the burn-in may read
  before it (`0058` item 1).

## What it would take to build (after the ruling)

1. **Params patch** (owner-only, cites this record): `IC_prior`, the horizon
   rule, the burn-in and the winsorisation, `params_version` in all seven
   files. After task 56's params patch, so the two do not collide.
2. **Build task:** the rebalance step extracted, with the audit's
   reproduction as the gate; `portfolio/views.py` (A and B); the phase-2
   rule; `build_weight_rule` wired; `scope` and `group_by` in the hypothesis
   validator, with `0057` rule 4; the `parameter_usage` rows; the reports of
   E; the tests of F. No hypothesis runs.
3. **Pilot task** (G), then the owner's thresholds, then the acceptance run.
4. Then `signals/`.

## Addendum, 2026-10-16: the burn-in is 52 weeks, lab-wide

**Ruled 2026-10-16 (owner):** "52 weeks, lab wide". This replaces open point
3's 156 weeks; the ±3 winsorisation stands. One rule for every hypothesis,
built in one place as B says. No family-specific burn-in.

Why it changed:
- **B's reason for 156 does not hold.** It said the burn-in "matches the
  covariance window so neither starts before the other". The covariance is
  fitted on instrument returns, which exist from 2001 whatever a signal's own
  history is, so a shorter score burn-in never starts a view before the
  covariance is ready. Cowork's error in the draft.
- **What prompted it:** the options-implied tail-asymmetry family
  (`claude/impvol-coverage-2026-10-15.md` in the Project) has a common start
  near 2008-04; at 156 weeks its first view would land near 2011-04.
- **The cost:** an early `z` estimated on 52 weeks of an autocorrelated score
  rests on far fewer independent observations than 52; the winsorisation is
  what bounds it. *Cowork's reading, not measured.*

Nothing is built yet: the params patch of "What it would take to build" item
1 carries 52, not 156.
