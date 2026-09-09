# 0019 — Conviction is a function of signal strength

Status: measures built 2026-09-09; the two coefficients are unset and the
objective refuses without them. Resolves the functional form left open in
`decisions/0003`.

## What the owner said

> "conviction needs to be dependent on the signal strength. For example, in HMM
> a 3 component state model capturing [risk on, neutral, risk off] should be
> weaker if the risk-on signal has probabilities [0.4, 0.3, 0.3] than if the
> signal has probabilities [0.7, 0.2, 0.1]."

So SUBSTRATE section 4's tracking-error coefficient is a **function**, not a
number. That is why `decisions/0003` could not be closed with a single value.

## The penalty

```
lambda(c) = lambda_low - (lambda_low - lambda_high) * c        c in [0, 1]
te_penalty = lambda(c) * max(0, trailing_te - ceiling) / periods_per_year
```

`lambda_low` applies when the model knows nothing and TE is dear; `lambda_high`
when it is certain and TE is cheap. Two numbers rather than one, which is more
honest than a single value pretending to cover both regimes. Both are `null` in
`params/constraints.yaml`; the objective refuses to build.

**The coefficient floors at `lambda_high` rather than reaching zero.** This is
the bound that matters: an overfit regime model reporting a spurious
[0.99, 0.005, 0.005] would otherwise buy itself unlimited tracking error at
exactly the moment its estimate is worthless. `te_coefficient` also refuses if
`lambda_high > lambda_low`, which would invert section 4.

## Two properties the measure must have

**Direction-agnostic.** [0.7, 0.2, 0.1] and [0.1, 0.2, 0.7] carry identical
conviction and opposite views. Conviction sizes the tilt; the view sets its
sign. Collapsing them would read a confident risk-off call as weak enthusiasm.

**Bounded in [0, 1]**, 0 at uniform and 1 at a point mass, so the penalty cannot
be driven anywhere unbounded by an extreme estimate.

## Which measure — entropy, as the owner uses elsewhere

Both are implemented in `harness/conviction.py`. On the owner's examples:

| Probability vector | Entropy | Max-probability |
|---|---|---|
| [0.33, 0.33, 0.33] uniform | 0.000 | 0.000 |
| [0.40, 0.30, 0.30] weak | 0.009 | 0.100 |
| [0.55, 0.25, 0.20] moderate | 0.092 | 0.325 |
| [0.70, 0.20, 0.10] strong | 0.270 | 0.550 |
| [0.45, 0.45, 0.10] split | 0.136 | 0.175 |
| [0.95, 0.03, 0.02] near certain | 0.789 | 0.925 |

Two things to note before accepting entropy.

**It discriminates about 30x between the owner's two examples**, against 5.5x
for the modal measure. On entropy, [0.4, 0.3, 0.3] scores 0.009 — near enough
zero that the portfolio would hug the benchmark almost entirely. That is
arguably correct: that vector genuinely carries almost no information. But it is
an aggressive setting and it is a calibration choice, not a fact.

**Entropy sees a state being ruled out; the modal measure barely can.**
[0.45, 0.45, 0.10] has decided something — the third state is out — without
picking a winner. Entropy scores it well above the weak case; max-probability
scores it *below*, because the mode hardly moved. Since a regime model's useful
output is often "not that one" rather than "definitely this one", this is the
stronger argument for entropy, and it does not depend on taste.

## The distinction still open

Section 4 says "conviction **dispersion**". The owner's example is about
**certainty**. These are different measurements and they can disagree: a model
can be certain about a regime that implies almost no cross-sectional tilt, and
an unsure model can produce widely dispersed views.

`dispersion_conviction()` implements the second reading. Which one the penalty
reads — or some combination — is not settled. The conservative default in the
code is certainty, because that is what the owner described.

## Conviction scaling is itself a falsifiable claim

This is the same pattern as `decisions/0016`. Conviction scaling asserts that
**high-conviction periods produce better risk-adjusted active returns than
low-conviction ones**. If that is false, the scaling adds turnover — the
coefficient moves, so the optimal portfolio moves — and risk for nothing.

It should be registered as a `kind: measurement` hypothesis and judged on its
own criterion, not on whether the strategy scores better with it switched on.
Tuning `lambda_low` and `lambda_high` against net IR would be selecting on the
outcome and adding two dimensions Romano-Wolf never sees.

## And it can leak, the same way loadings can

Conviction must come from **walk-forward, out-of-sample** state probabilities.
An HMM fitted on the full sample and asked for its 2004 state probabilities
knows how the decade ended. That is the same class of leak as `decisions/0015`:
not in the returns, not in the signals, in the machinery — and the `lookahead`
veto as built would not see it. Whatever extension covers estimated loadings
must cover estimated state probabilities too.

## What is needed

1. `lambda_low` — the TE coefficient at zero conviction.
2. `lambda_high` — the TE coefficient at full conviction. Not zero.
3. A decision on certainty versus dispersion, or how to combine them.

None can be sensibly chosen before there is a candidate model to look at, so
this is expected to close in phase 2 rather than now.
