# 0018 — The turnover penalty, and how to look at the alpha/turnover trade

Status: designed 2026-09-09; the coefficient is unset and the objective refuses
to build without it. Built in phase 2.

## What the owner asked for

> "the 100% later is that while 150% is acceptable it would be interesting to
> evaluate how sensitive to lower turnover leading models would be. we might
> accept slightly lower expected alpha for much lower turnover. A penalty (soft
> constraint) for above 100% could be a solution."

Two distinct things, and separating them matters more than either.

## 1. A one-sided soft constraint above the target

The optimiser's objective gains a penalty that is zero at or below 100%
annualised turnover and bites above it, so lower turnover can be *bought* with a
little expected alpha rather than being either free or forbidden. The 150% veto
stands unchanged as the hard ceiling.

Recorded in `params/constraints.yaml` under `turnover.penalty`, expressed as a
**shadow cost in basis points per unit of annualised turnover above target**
rather than an abstract lambda. A lambda is a knob; a shadow cost is a claim an
investment professional can argue with — "we charge an extra X bps for turnover
above 100%, being our estimate of the capacity and implementation risk the
half-spread does not capture." Given the standard this project is held to
(a model defensible to a room of professionals), the interpretable form is worth
more than the convenient one.

`coefficient: null`. Nobody has chosen it and the lab does not invent
thresholds, so the objective refuses to build until it is set. It sits beside
the asymmetric TE penalty, which is null for the same reason.

## 2. The trap: the penalty must not touch the reported IR

The penalty is already a *second* charge on turnover — the cost model charges
the spread, and the penalty charges again for what the spread does not capture.
That double charge is deliberate in the objective and wrong in the report.

So: **the penalty shapes the weights, and the reported net IR is computed from
actual costs only.** If the penalty entered the reported return, a heavily
penalised run would look worse for a reason that is not performance, and the
leaderboard would stop being comparable across runs with different
coefficients — which is the one thing the leaderboard exists to be. Both figures
are recorded; only the actual-cost one ranks.

## 3. The sensitivity curve, and why it is a diagnostic and not a search

The interesting output is the **alpha/turnover trade curve**: sweep the penalty
coefficient for one candidate model and plot realised net IR against realised
annualised turnover. That curve answers the owner's question directly — how much
alpha does this model give up to halve its trading — and a model whose IR
collapses as turnover falls is one whose edge lives in the trading rather than
in the signal, which is worth knowing before defending it to anyone.

**It is not a selection mechanism, and the distinction has to hold.** Sweeping
the coefficient and keeping the knee of the curve would be selecting on the
outcome, exactly like choosing a loading estimator by which one flatters the
signals (`decisions/0016`), and it would add an uncounted dimension to the
search that Romano-Wolf never sees.

So the rule: the curve is computed **for a candidate that has already survived
the veto set on the pre-registered objective**, at the pre-registered
coefficient. It informs an owner decision about implementation. It never ranks,
and a point on the curve is never promoted to the leaderboard.

## What is needed before this can be built

1. The penalty coefficient, in bps per unit of turnover above target.
2. A decision on shape: linear in the excess (a literal shadow cost, and the
   natural reading of "extra bps") or quadratic (smoother for the solver, and
   it punishes large excesses disproportionately). Linear is the more
   defensible; quadratic is the more tractable. Not chosen.
