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

## Addendum, 2026-10-23: the cross-sectional views demean the standardised scores

**Owner ruling, 2026-10-23** (chat, in answer to the question Cowork raised while writing HANDOFF task 70): "demean the standardized scores". Recorded by Cowork.

- **The rule.** For a cross-sectional test, `z` is built first, per group, by `standardise` (`portfolio/views.py`, task 70): the expanding mean and standard deviation of that group's own knowledge-dated scores, winsorised at the clip. Then, at each date, the groups' `z` are demeaned across the groups: `zc_g(t) = z_g(t) - mean_g z_g(t)`. The view is `v_g(t) = ic_prior * sigma_g(t) * zc_g(t) / sqrt(h)`. The directional form uses `z` undemeaned.
- **What the demeaning gives, stated so it is not rediscovered.** `zc` sums to zero across groups at every date. The *views* sum to zero only when `sigma` is the same for every group, which holds for the duration, real_nominal, credit and cash axes (one `sigma_k` per axis). On the region axis `sigma_g` is per group (section A), so the views `v_g` do not sum exactly to zero; the *standardised* scores do. This is the reading the owner chose; the alternative (demeaning the views themselves, which would force a zero sum) was not chosen.
- **Which groups are demeaned over.** The groups that are present at the date: a group still in its burn-in has `z = 0` (task 70) and stays in the mean.  *Cowork's reading, not ruled; one line to change if the owner prefers to drop burn-in groups from the mean.*

## Addendum, 2026-11-05: the phase-2 rule is built signal-agnostic, before any signal module

**Owner ruling, 2026-11-05** (chat: "regarding pending decision on task 82 question, go on option (a)"), answering the chain stop of the 2026-11-05 morning review (Project doc `claude/nightly-review-2026-11-05-morning.md`, "Options"). Recorded by Cowork.

Section C says the phase-2 rule differs from the audit's only in where its alpha comes from. It did not say what the rule is fed while `signals/` is empty, how the universe and cost model are supplied outside the audit, or what happens to the test that pins `OptimiserMissing`. Ruled, option (a):

1. **The rule is signal-agnostic.** A `Phase2Rule` takes a raw-scores frame (dates by groups, section B's contract) as an argument, with the hypothesis's axis, expression, `group_by`, `scope` and horizon. It builds `z` (`views.standardise`), the views (`views.view_scale`, or `alpha.cross_sectional_views` for the cross-sectional form), the alpha (`alpha.alpha_from_views` / `alpha_from_group_views` on `ExposureMap.at(t)`), and calls the extracted rebalance step (`portfolio.rebalance.RebalanceStep`). No signal is built by it.
2. **The universe and the cost model are arguments,** as `RebalanceStep` already takes them. How a real run constructs them outside the audit is decided with the first signal module (M7), not here.
3. **`build_weight_rule` is not wired yet.** It keeps raising `SignalModuleMissing` and then `OptimiserMissing` until a signal module exists (M7); `tests/test_experiment.py` is not edited.
4. **The hard checks of section F that need no real signal are tests on synthetic scores** in the build task: F1 to F4 and F6. F5 (`lookahead` on the new parameter kinds) and F7 (the tables of E) need the `parameter_usage` rows and the reports, which are the next chain task (83).

Rejected: (b) waiting to write the rule with the first signal module, so it is first exercised on real input; (c) another shape. Reason given with the recommendation: (a) keeps M5 moving and leaves M7 to plug in.

## Addendum, 2026-11-07: sections D and E are built as functions, before any storage or wiring

**Owner ruling, 2026-11-07** (chat, 13:58 ET: "Go option a on pending decision number 1"), answering the chain stop of the 2026-11-05 afternoon review (Project doc `claude/nightly-review-2026-11-05-afternoon.md`, "Options"), which said D and E sit under "The draft — NOT ruled" and left open who writes the `parameter_usage` rows and where the reports of E live. Recorded by Cowork. Sections D and E are adopted as written, with these points:

1. **Who writes the rows.** `Phase2Rule` records, at every `__call__`, one row per kind it consumed, and returns them from a `parameter_usage()` method in `ExposureMap.usage()`'s columns (`instrument`, `parameter`, `store_week`, `fitted_through`, `used_on_date`): `covariance`, `sigma_<axis>` and `zscore_<hypothesis>` (D). The caller concatenates them with the exposure map's own `loadings` rows. No veto change (D).
2. **Where the reports live.** Plain functions in `portfolio/` returning frames, fed the books the rule solved; no file, no run-summary section, no results-store column. Their destination in a real run is decided with the first signal module (M7), as the universe and cost model were (2026-11-05 addendum item 2).
3. **The transfer measure (E, third bullet).** Directional: the correlation across rebalance dates of the book's active exposure on the target axis with the view. Cross-sectional: at each date, the correlation across groups of each group's active exposure with its view, then the mean over dates. *Cowork's definition, written into the task; one function to change if the owner prefers another.*
4. **F5 and F7 are tests** on synthetic input: F5 runs `veto_lookahead` on an honest rule's rows and on one late row of each new kind; F7 checks that the two tables of E come back with one row per rebalance the rule solved.

Rejected: (b) ruling D and E line by line first; (c) another shape. Built by HANDOFF task 83.

## Addendum, 2026-11-09: the transfer measure reads the view's own instruments; several directional views are averaged

**Owner ruling, 2026-11-09** (chat, 07:59 ET on task 83's receipt choice (5): "only scope, agree"; 08:33 ET on Cowork's suggestion for choice (6): "agree"). Recorded by Cowork. It amends item 3 of the 2026-11-07 addendum; nothing else in D, E or F moves.

1. **The active exposure in the transfer measure is taken over the instruments the view can reach**, not the whole book (task 83 choice (5)). Directional with one view: `sum_i (w_i - b_i) m_i x_i`, `m_i` the scope mask (`portfolio.alpha.scope_mask`), the same mask the alpha uses. With `group_by`: each group's sum over its members as `groups_for` gives them (already inside the scope). Region axis: the region cells multiplied by the scope mask, so an out-of-scope instrument counts in no region (Cowork's reading of "only scope" for the region axis, flagged: `_region_alpha` applies that mask, so the measure reads what the view could move). The `active_exposure` table of E is unchanged: it stays the whole book.
2. **A directional rule with several views** (`group_by`, or the region axis) gets, for each view, the Pearson correlation across rebalance dates of that view's active exposure (item 1) with that view; `transfer` is the equal-weight mean over the views that have at least `MIN_POINTS` (3) usable dates, `nan` if none. The per-view correlations are reported too. With one view this is the 2026-11-07 definition, scope-masked.
3. **Rejected:** (b) one correlation pooled over every (date, view) pair, because the views' structurally different average exposures (each curve's typical active duration) move it without saying whether the book followed the views; demeaning each view first makes it a weighted form of item 2 and harder to read. (c) Weighting the views by their share of tracking variance, because that weights by how the solver spent risk, the thing the measure diagnoses. *Cowork's caveat, accepted:* each per-view correlation is noisy at h = 13 with few rebalances; that holds for one view too, and is why the per-view numbers are kept.

Built by HANDOFF task 85.

## Addendum, 2026-11-10: how the pilot of G is run (delegated)

**Delegated ruling, 2026-11-10, Cowork** (under `decisions/0069` items 3 and 4; the first one made). G says what the pilot plants, its grid and what it reports. It does not say what the pilot runs *on*, because `build_weight_rule` is unwired until M7 and the 2026-11-05 and 2026-11-07 addenda left "how the caller builds the universe and the cost model" open. The questions, the choices and their bases:

1. **The universe, the cost model, the engine and the baseline.** *Options:* (a) the audit's own (`audit.universe.bloomberg_universe`, `audit.ladder.audit_cost_model`, the engine and the block-shuffled baseline of `run_cell`); (b) wire `build_weight_rule` first and run the pilot through `run_experiment`; (c) a third harness written for the pilot. *Choice:* (a). *Basis:* section C: the phase-2 rule is the audit's rebalance step with one difference, where its alpha comes from, and that step was extracted under a gate of exact reproduction (task 69). The audit's universe and cost path is therefore the only one whose numbers have been reproduced; (b) would put an unvalidated wiring under the test that is meant to validate the rule, and (c) is a second copy of what C removed. This does **not** decide M7's question: how `build_weight_rule` builds them for a registered hypothesis stays open.
2. **The exposure map and the factors.** The store pinned in `params/data.yaml`, read through `ExposureMap` as any run reads it. The duration truth is the factor of section A's table (minus the weekly change in the 10y real yield); a region group's truth is its relative return as A defines it (`alpha.relative_factor`: the equal-weighted `region_view` members less `NDUEACWF`). `sigma` comes from `alpha.factor_sigma` and `alpha.relative_sigma`, as `phase2.py` expects of its caller. *Basis:* A and the 2026-11-05 addendum; no new choice.
3. **The planted score.** For each column (one for duration directional; one per view region for region cross-sectional): the truth is the forward *h*-week sum of the column's factor, standardised; the score is `IC * truth + sqrt(1 - IC^2) * noise`, the noise AR(1) and orthogonalised against the truth per column, with the persistence rule `audit/signals.py` uses at the same *h*. For the cross-section the truth is demeaned across regions at each date before standardising, since the rule demeans the scores. *Basis:* G ("the same way `audit/signals.py` does for instruments"); the demeaning follows `0060`'s cross-sectional form.
4. **Dates.** *h* = 13 for every pilot run, so the rule gets `horizon_weeks` (13, 13). A score is dated *t* and its truth reads returns to *t* + 13 weeks, so the last score date is at least 13 weeks before `HOLDOUT_START`; nothing on or after 2020-01-01 is read, and the loader's lock is not touched. The burn-in is 52 weeks (addendum of 2026-10-16). *Basis:* G; SUBSTRATE §2 (the holdout).
5. **Where the numbers go.** A run directory under `results/audit/` like every audit grid, with a `summary.json` and a `report.md`; nothing is written to the leaderboard store and no verdict is recorded, because a planted run is not a hypothesis. *Basis:* HANDOFF's contract ("measurements belong in `results/`"); SUBSTRATE §7 (only registered hypotheses are tested).
6. **When it may run.** The pilot's grid is a guess of two to three hours (G). The Thursday-to-Saturday rule binds a run of more than five hours (HANDOFF's contract, `long`). The pilot is not `long`: it may start at any slot, after the run task times four runs and stops if the whole grid extrapolates past five hours. *Basis:* the contract's own threshold; `0069` item 9 reads "audits" as those `long` runs.

*Which numbers this can move:* only the pilot's own, which are planted. No recorded audit number, no golden, no hypothesis verdict. *What would reverse it:* the reviewer finding that the audit's universe or cost path differs from what a registered hypothesis's run will use in a way that changes the pilot's dose-response (then the pilot waits for M7's wiring); or the owner striking it.

**Not delegated, and unchanged:** the pilot's pass thresholds (owner, after the pilot; `0069` item 2).

**Reviewer (`0069` item 4):** pending. HANDOFF task 90 runs in a fresh Opus session that did not make this ruling; its step 1 is to read this addendum against the code and write its line here before building anything.

**Reviewer, 2026-11-10, Claude Code (Opus), HANDOFF task 90:** agrees, with three details settled inside the cited records and built to the settled text. *Point 1:* the basis is true. `Phase2Rule` subclasses `portfolio.rebalance.RebalanceStep`, which `_OptimiserRule` also subclasses (task 69's extraction), so the solve, covariance, spec, cost vector and shadow term are one implementation. The cost model's levels come from `params/costs.yaml` through `audit_cost_model`, which on a Bloomberg panel adds no bucket the universe map lacks. Membership is the owner's `investable_universe.csv`. Nothing touches `0069` item 2. One difference would move a dose-response, and section C settles it. The audit universe treats every investable unhedged series with a full covariance window as holdable, including those with no exposure row (the store's `not_estimated`, tradable-only instruments). In a phase-2 book these would be zero-alpha diversifiers that a registered run cannot hold, because C defines holdable as "investable, with a full covariance window, and with an exposure row" and `ExposureMap.requires_row` refuses a weight on one. *Settled:* at each date the pilot holds only the instruments with a row in `ExposureMap.at(t)`. The engine keeps `run_cell`'s constant exposure rule, so its path is the audit's in every other respect. *Point 2:* agrees. Two things only the caller can fix. First, the factor frame is the one the pinned store was fitted on: the store manifest's `factor_set` and `estimation_start`, read through the same `load_inputs` that built it. Second, `sigma`'s overlay is the scalar of `decisions/0042`, computed as `covariance.volatility_scalar` on the same window and holdable block the solver's covariance uses (A: "read through the same resolver"). *Point 3:* agrees, with one refinement. The truth keeps the pooled standardisation, so the cross-sectional truth still sums to zero across regions. The orthogonalised noise is scaled per column to that column's truth standard deviation, so each column's correlation with its truth is the planted IC exactly (as `audit/signals.py` makes the pooled IC exact). Without that, a region with a quiet relative return would carry less than the planted IC. *Point 4:* agrees. The rule refuses a date with no score, so the engine's panel ends at the last score date: no book is held over the last 13 weeks before `dev_end`. *Points 5 and 6:* agree. `IC_prior` at half and twice is set on an in-memory copy of `Params`, and each row records it. `params/` and the recorded `params_hash` are untouched.

