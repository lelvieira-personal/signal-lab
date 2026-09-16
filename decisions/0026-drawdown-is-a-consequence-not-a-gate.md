# 0026 — Active drawdown is a consequence of the TE budget, not a separate gate

Status: decided, 2026-09-16, Leo. Removes the eleventh veto. Amends SUBSTRATE
sections 4 and 10; touches `vetoes/`, `params/vetoes.yaml`.

## What the owner said

> "just let's get rid of this relative drawdown cap, it is at the end of the day
> a consequence of the TE budget which is calibrated by conviction in the IR of
> the signal and the persistence"

## Decided

**The `active_drawdown` veto is removed.** The veto set returns to the ten of
SUBSTRATE section 10. Maximum active drawdown remains a first-class **reported**
metric — on every run's summary, in the audit's cell table, and on the report's
charts — but it no longer kills anything.

## Why

`decisions/0003` introduced the cap as 3× the tracking-error budget: 18% at a 6%
budget. At the time the budget was a fixed mandate number and the cap was an
independent check on the shape of the path.

`decisions/0025` changed the relationship. The tracking-error budget is now
*derived from* the drawdown tolerance: pick a tolerance (32%), a statistic (p95)
and a conviction on the signal's IR and persistence, and the exact
Magdon-Ismail–Atiya scaling law returns the budget. Drawdown is the input to the
budget, not an independent constraint on it. Vetoing on the realised figure as
well charges the same risk twice — once ex ante, where it is controllable, and
once ex post, where it is not.

Three things follow, and each on its own would be enough.

**1. The cap contradicts its own calibration.** Measured with
`scripts/drawdown_map.py` at the 0025 budget of 6% and IR 0.30, **51.9% of
simulated paths breach 18%** — 63.7% at IR 0.20. These are strategies performing
*exactly to specification*. A gate that kills half of the population it was
sized for is not enforcing a mandate; it is a coin toss dressed as governance.

**2. A p95 target makes breaches mandatory by construction.** The budget is set
so that the 95th percentile of the drawdown distribution equals the tolerance.
That is a deliberate choice to allow episodic excursions (`decisions/0025`).
One run in twenty is *designed* to exceed it. Vetoing that run does not reduce
the risk taken — the budget already did that — it only deletes the evidence.

**3. It selects on the luck of the path.** Two books with identical ex-ante risk
and identical alpha differ in realised maximum drawdown by the draw. Killing the
unlucky one and keeping the lucky one adds no information about the signal and
biases every downstream statistic — the leaderboard, the seed-stability range,
the multiple-testing count — toward paths that happened to avoid a bad run. It
is survivorship selection inside the lab's own governance.

## What this does NOT do

It does not raise the risk appetite. The 32% tolerance of `decisions/0025` is
unchanged and is what sets the budget. Risk control moves entirely to the point
where it can act — before the trade — instead of being applied twice, once
uselessly.

## The residual risk, and the successor check

With the veto gone, nothing catches the case where the **ex-ante covariance
understates risk out of sample**: a book sized to a 6% tracking error that
realises 10%, and a drawdown to match. The tracking-error veto catches the
realised TE, but nothing currently asks whether the drawdown the budget *implied*
matched the drawdown that arrived.

That is the owner's own falsification test —

> "then we test if the backtested results match the expectation"

— and it becomes a check, not a cap. A `risk_calibration` check, landing with
the derived-budget solver change, that compares each run's realised maximum
active drawdown against the ex-ante p95 the budget targeted for that run's
conviction and persistence, and flags a systematic shortfall of the model rather
than an unlucky draw. It is a **diagnostic on the estimator**, not a gate on the
strategy, and its threshold is a further owner decision. Until it exists, this
is an open risk, recorded here rather than covered by a cap that does not work.

## Changed

- `vetoes/rules.py` — `veto_active_drawdown` removed
- `vetoes/registry.py`, `vetoes/__init__.py` — VETOES and SUBSTRATE_VETOES now 10
- `params/vetoes.yaml` — the `active_drawdown` block and its order entry removed
- `src/signal_lab/harness/hypotheses.py` — PORTFOLIO_VETOES now four
- `src/signal_lab/audit/ladder.py` — the audit's per-cell verdict checks four
  vetoes; `max_active_drawdown` is still recorded per cell
- `render/views.py`, `render/mock_data.py` — the veto row removed, the drawdown
  charts kept
- `SUBSTRATE.md` — §10 row removed; §4 now reads that active drawdown is
  controlled ex ante through the tracking-error budget
- `decisions/0003` is superseded on this point only; its drawdown scaling law,
  now validated by `scripts/drawdown_map.py`, is what `decisions/0025` uses.
