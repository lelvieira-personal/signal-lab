# 0017 — Turnover: which figure the veto reads, which the cost is charged on

Status: decided 2026-09-09. Clarifies SUBSTRATE sections 4, 8 and 10.

## The ambiguity

SUBSTRATE section 8 says:

> Net return = gross − turnover × half-spread − drag/52 per week

Section 4 caps turnover at "≤ 150% annualised" and section 10 makes it a veto.
Neither says which turnover, and the two conventional readings differ by a
factor of two:

- **one-way**: `0.5 × Σ|Δw|`. The portfolio replacing itself once a year is
  100%. This is what a turnover limit conventionally means, and what a
  reasonable reader assumes "150%" refers to.
- **traded notional**: `Σ|Δw|`, buys plus sells. This is what actually crosses
  a spread, because a half-spread is paid on every unit traded in either
  direction.

Read section 8 with the one-way figure and every cost in the lab is halved.

## Decision

Both are computed and named separately in `harness/costs.py`:

- `turnover_one_way` is what the `turnover` veto measures against the 150%
  ceiling, and what the leaderboard reports.
- `traded_notional` is what the spread cost is charged on:
  `spread_cost = Σ|Δw| × half_spread`, per instrument at that instrument's
  bucket rate.

So a 150%-annualised strategy in the mid bucket pays roughly
`1.5 × 2 × 10bp = 30bp` a year in spread, plus its fee-and-tracking drag. That
is the conservative reading of both sections and it does not require either to
be rewritten — only for the word "turnover" in section 8 to be read as traded
notional, which is what makes it dimensionally correct.

`tests/test_engine.py` asserts the factor of two explicitly, so the convention
cannot drift silently.

## The related error, guarded in the same place

Turnover is measured from the **drifted** book to the new target, never from the
previous target. The previous-target version is not biased in a knowable
direction, which is what makes it dangerous: a persistent rule that returns the
same target every week reports *zero* turnover and zero cost while the real book
has drifted and must be traded back, and a rule whose drift happens to move
toward the next target reports too much.

## What is still not settled

Section 4 also names a 100% annualised turnover **target** ("aim to reduce to
100% later"), distinct from the 150% ceiling. It is recorded in
`params/constraints.yaml` as `turnover.target_annualised` and is not enforced
anywhere. Whether it should become a penalty term in the objective, alongside
the asymmetric TE penalty, is an open question for phase 2 — and it needs a
coefficient, which nobody has chosen.
