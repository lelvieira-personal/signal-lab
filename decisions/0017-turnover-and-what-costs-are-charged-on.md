# 0017 — Turnover is traded notional

Status: decided 2026-09-09 by the owner. Resolves an ambiguity in SUBSTRATE
sections 4, 8 and 10.

## The ambiguity

SUBSTRATE section 8 says:

> Net return = gross − turnover × half-spread − drag/52 per week

Section 4 caps turnover at "≤ 150% annualised" and section 10 makes it a veto.
Neither says which turnover, and the readings differ by a factor of two:
one-way (`0.5 × Σ|Δw|`) or traded notional (`Σ|Δw|`, buys plus sells).

## Decision

> "max 150% is traded notional as per the conventional definition." — owner

**Turnover is traded notional.** Both the veto ceiling and the cost formula read
the same figure.

This is the tighter of the two readings — half the trading the one-way
interpretation would have permitted — and it makes section 8 *literally*
correct rather than requiring reinterpretation: `turnover × half_spread` is the
cost, because a half-spread is paid on every unit traded in either direction.
That self-consistency is evidence the reading is the intended one.

`turnover_one_way` is still computed and reported alongside, since some
conventions use it and a reader comparing against another manager's figures
will want it. Nothing in the lab is measured against it.
`tests/test_engine.py` asserts a book that breaches the ceiling on traded
notional would have passed on the one-way figure, so the distinction cannot
quietly regress.

## The related error, guarded in the same place

Turnover is measured from the **drifted** book to the new target, never from the
previous target. The previous-target version is not biased in a knowable
direction, which is what makes it dangerous: a persistent rule that returns the
same target every week reports *zero* turnover and zero cost while the real book
has drifted and must be traded back; a rule whose drift happens to move toward
the next target reports too much.

## The 100% figure is a target, not a second ceiling

Section 4's "aim to reduce to 100% later" is not a stricter veto in waiting. It
is a soft constraint and a research question — see `decisions/0018`.
