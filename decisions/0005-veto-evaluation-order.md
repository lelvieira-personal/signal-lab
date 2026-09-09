# 0005 — In what order are vetoes evaluated?

Status: proposed, 2026-09-07, agent. Blocking: no. Conservative option taken.

## Question

SUBSTRATE section 10 lists ten vetoes in a table. KICKOFF item 4 says
`apply_vetoes()` "returns the first failure". The table's order is not stated
to be an evaluation order, and the substrate does not say which failure should
be recorded as *the* reason a run died.

## What was done

`params/vetoes.yaml` carries an explicit `evaluation.order` that puts the three
data-integrity vetoes first: `lookahead`, `frequency`, `coverage`, then the
portfolio constraints, then the statistical gates. Every veto is still
evaluated and every verdict is still recorded; the order only decides which one
is named as the cause.

## Why that way

A lookahead or frequency breach makes every downstream number meaningless. If a
run both peeked at a future vintage and breached turnover, "killed by turnover"
sends the reader to the optimiser when the actual problem is the data. Naming
the integrity failure first sends them to the right place.

## What to decide

Whether the substrate's table order should instead be authoritative, in which
case `params/vetoes.yaml` should be changed to match it and this note closed.

---
## Owner decision (2026-09-09, Leo)

The SUBSTRATE section 10 table order is authoritative. `params/vetoes.yaml`
now evaluates in table order: turnover, cash, tracking_error, positions,
coverage, lookahead, frequency, active_drawdown, seed_stability,
multiple_testing, direction.

The diagnostic concern raised above is mitigated rather than accepted: every
veto is still evaluated and every verdict still recorded, so a lookahead breach
remains visible in the store and on the report even when a constraint breach is
named as the cause of death. Only the *headline* reason follows table order.
`tests/test_vetoes.py` asserts this explicitly.

Status: **closed.**
