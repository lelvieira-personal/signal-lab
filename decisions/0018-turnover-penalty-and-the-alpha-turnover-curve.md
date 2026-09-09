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

## Owner's answer (2026-09-09), and an arithmetic caveat

> "0.5bp cost for exceeding 100%, linear."

Implemented as `coefficient: 0.5`, `form: linear`, in
`params/constraints.yaml`, read as **0.5bp per unit of annualised turnover above
the target** — the literal reading of the words.

At that setting the penalty is very small next to the cost of the trading it is
meant to discourage:

| Annualised turnover | Penalty | Mid-bucket spread | Penalty as % of spread |
|---|---|---|---|
| 100% | 0.000bp | 10.0bp | 0.0% |
| 125% | 0.125bp | 12.5bp | 1.0% |
| 150% | 0.250bp | 15.0bp | 1.7% |
| 200% | 0.500bp | 20.0bp | 2.5% |

At the 150% veto ceiling the shadow cost is a quarter of a basis point a year
against fifteen basis points of real spread. A term that size will not move an
optimiser: it is roughly a fiftieth of the marginal cost the solver is already
paying, so it cannot buy the "much lower turnover" the owner described.

**The units are genuinely ambiguous and the readings differ by 100x.** "0.5bp
for exceeding 100%" could mean per *unit* of turnover (0.25bp/yr at the ceiling,
as implemented) or per *percentage point* of excess (50pp x 0.5bp = 25bp/yr at
the ceiling, which is more than the entire mid-bucket spread and a very strong
preference). The stated intent — "slightly lower expected alpha for much lower
turnover" — sits between the two: giving up nothing, or giving up 25bp, are both
away from "slightly".

A coefficient near **10bp per unit** would put the shadow cost at 5bp/yr at the
ceiling, about a third of the real spread, which is the range where a soft
constraint actually trades one thing against another.

Recorded as the owner's number with the arithmetic attached rather than
adjusted. `tests/test_objective.py` asserts the magnitude, so changing the
coefficient forces a look at this table.

## Shape

Linear, as the owner chose — a literal shadow cost, and the more defensible of
the two. Quadratic would be smoother for the solver and would punish large
excesses disproportionately; it is not used.
