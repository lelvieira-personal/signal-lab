# 0016 — Measurement hypotheses: a second class, with its own objective

Status: designed 2026-09-09, built in phase 2. Extends SUBSTRATE section 7.

## The problem

The factor loadings are part of the model, not infrastructure beneath it
(`decisions/0015`). So the estimator has to be researched rather than chosen.
The obvious way to research it — try five estimators, keep the one whose
portfolios score best — is circular, and badly so:

- It selects the mapping on the outcome. That is the same error as picking a
  signal because it backtested well, one level down and much harder to see,
  because the leaderboard would show a *signal* result while what was actually
  selected was a *matrix*.
- It multiplies the search. Five estimators across eleven families is a 55-cell
  space, and Romano-Wolf across 55 correlated cells sets a bar nothing clears.
- It hides the interesting failure. If an instrument has no true sensitivity to
  a factor, that is a fact about the instrument worth knowing on its own. Buried
  inside a strategy backtest it looks like a weak signal instead.

## The decision

Two classes of hypothesis, registered in the same way, tested against different
objectives, ranked on separate leaderboards, with multiplicity controlled
separately within each.

**Signal hypotheses** — the existing kind. Objective: net information ratio
against the 50/50 benchmark, per SUBSTRATE section 3.

**Measurement hypotheses** — about the exposure matrix itself. Objective:
**out-of-sample loading fidelity**. Does a loading estimated on data up to time
*t* predict the instrument's realised sensitivity after *t*?

That objective is the point. It is falsifiable, it is about the instrument
rather than about the strategy, and it can be answered without computing a
single portfolio return. An estimator that wins on it wins for a reason that has
nothing to do with making the signals look good, which is exactly what breaks
the circularity.

Measurement hypotheses run **before** the signal search in a cycle. Their output
is the matrix the signal search then uses.

## What a measurement hypothesis looks like

The same YAML template as section 7, plus `kind: measurement`, and with the
fields reinterpreted:

- `signal` names the estimator, not a predictor: `ols_60m`,
  `shrunk_to_peer_mean`, `michaud_resampled_loadings`,
  `regime_conditional_hmm2`.
- `direction` becomes the pre-registered claim about fidelity — that this
  estimator's loadings predict realised sensitivity better than the incumbent's.
- `rationale` argues why, in the same paragraph-of-economics style.
- `target_axis` names the exposure being estimated.

The candidate estimators the owner has named or that follow from the project's
methods, none of them yet registered: shrinkage toward a prior (Bayesian, or
Theil-Goldberger); Michaud resampling applied to loadings rather than weights;
robust regression discounting outliers; regime-conditional loadings via HMM,
which is honest that the equity-rate beta changed sign this decade and expensive
in effective sample size.

## Which vetoes apply

The data-integrity vetoes apply unchanged: `lookahead` (extended to estimated
parameters per `decisions/0015`), `frequency`, `coverage`, `seed_stability`,
`multiple_testing`, `direction`.

The portfolio vetoes do not: `turnover`, `cash`, `positions`,
`tracking_error` and `active_drawdown` are properties of a portfolio, and a
measurement run does not produce one. They are recorded as `not_applicable`
rather than passed, so the distinction is visible in the store and a measurement
run can never be mistaken for a portfolio run that happened to pass everything.

## The honest cost

This makes the lab slower. Two searches, two multiplicity budgets, and the
signal search cannot open until a matrix has been chosen. That is the price of
not selecting the mapping on the outcome, and the alternative is a result nobody
can defend to a room of investment professionals — which is the standard the
owner has set for this project.

## Built now, in phase 0

Only the schema: `kind: signal | measurement` on the hypothesis template,
defaulting to `signal` so the eleven existing registrations are unambiguous. The
separate objective, the separate leaderboard and the fidelity metric land with
the estimator in phase 2. Adding the field now costs nothing and means the
registry does not change shape later.
