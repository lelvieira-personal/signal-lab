# 0055 — The wiring: params names the store a run reads, and the lookahead veto checks loadings

**Status:** decided 2026-10-11 by the owner. Cowork asked whether to write
the wiring task with two owner-only patches, "pinning the store id in
`params/`" and "extending the `lookahead` veto to estimated loadings". He
answered "yes". **The wording of both patches is Cowork's.** They are applied
in the working tree for HANDOFF task 54, and the owner reviews the diff.
Follows `decisions/0015`, `0049` and `0050`. Changes `params/` (v0.10.0) and
`vetoes/rules.py`. **No change to `SUBSTRATE.md`:** §10's `lookahead` row
already reads "and no estimated parameter fitted on data unavailable when it
is used", and §6 already says the veto covers estimated parameters.

## Why both are owner-only

- **Which store a run reads is part of the model** (`decisions/0015`: "The
  exposure matrix is not infrastructure that the model runs on. It is part of
  the model"). A view mapped through other loadings is another portfolio.
  Named in `params/`, the store is in the params hash every run records.
- **The veto is the only check on a leak that no return shows.** Loadings
  fitted on the full sample and used at every rebalance look clean in every
  downstream number (`decisions/0015`).

## The ruling

1. **`params/data.yaml` names the store:**

   ```yaml
   characteristics:
     store_id: huber6-v3
     directory_hash: "84a5088d82b135c48ba7da5709ebae3f58186c06b08575d1b233ba19e27270f7"
   ```

   - `resolve_exposures` reads that store and no other.
   - It refuses a store whose manifest hash is not the one in `params/`.
   - Changing either line is an owner decision with its own record.
2. **`params_version` becomes `0.10.0`** in all seven files. The params hash
   is `413d84f6b631359bee74883cb63f93660023cc50d4ff49306579c401a4d61623`
   (CRLF form, computed by Cowork from the working tree; task 54 confirms
   it).
3. **`veto_lookahead` has two halves.**
   - **Observations,** as before: no row of `observation_usage` with
     `used_on_date` earlier than `knowledge_date`.
   - **Estimated parameters,** new: no row of `parameter_usage` with
     `fitted_through` later than `used_on_date`. A row with either date
     missing is a breach.
   - **Either table absent fails,** as every veto does on a missing input
     (SUBSTRATE §10).
4. **`parameter_usage` holds the loadings today:** one row per instrument
   and rebalance, with `fitted_through` taken from the store's
   `last_data_date`.

## What the veto does not cover yet

Other numbers a run estimates from past data are the return covariance, the
volatility overlay and a signal's standardisation. They are fitted on
trailing windows by construction, and nothing records that in a table a veto
reads. They join `parameter_usage` when the phase-2 solver is built. Until
then the veto's second half is a check on the loadings only, and a pass must
not be read as more.

## What the wiring does (not owner-only; built by task 54)

- **One store week per rebalance.** A rebalance on date `d` reads the store's
  latest week on or before `d`. That week must be within six days of `d`;
  otherwise there is no row. Nothing older is carried.
- **Axes as `decisions/0050` rules them,** with its 2026-10-10 addendum.
  Duration reads the measured `INDEX_OAD_TSY` for Treasuries, Long
  Treasuries, IG Corporates and TIPS where that week has one, and minus the
  real-yield loading everywhere else. Real/nominal is minus the inflation
  loading and credit is minus the credit loading. Cash is a label.
- **Every cell carries its provenance,** `measured` or `estimated`.
- **Region, sector and style raise** until the label map lands
  (`decisions/0054`).
- **An instrument with no row on a date is not in the matrix on that date,**
  and a book may not hold it then.

## What it does not decide

- **A run's first date.** The store begins on 2002-12-27 and the development
  window on 2001-01-05. A run that needs exposures cannot rebalance in the
  first 103 weeks (OWNER-QUEUE L35).
- **The solver,** how a score becomes a view in return units, and what the
  solver must pass on planted signals.
- **Shrinking estimated cells toward a prior** (`decisions/0015`).

## What would reopen it

- A new store (`huber6-v4` or another estimator): a new record, a new params
  version.
- A veto verdict that passes a run later shown to have used a number from
  the future.
