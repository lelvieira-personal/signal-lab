# 0100 — Amendments to SUBSTRATE.md

Status: **all eleven applied in v0.4 on 2026-09-10** (`decisions/0020`).
Running list; reopens whenever a decision changes what the constitution says.

An agent never originates a change to `SUBSTRATE.md`. Where a decision changes
what the constitution says, the change is recorded here, the owner approves it,
and an agent may then transcribe the approved wording citing the decision
(§2, as amended in v0.4).

This file exists so that drift between code and constitution is visible in one
place rather than scattered across decision records. **An empty table here means
the code and the constitution agree.**

## Applied in v0.4 (2026-09-10)

| Section | Amendment | Decision |
|---|---|---|
| 10 | Eleven vetoes, not ten: add `active_drawdown`. The `tracking_error` row reads "95th percentile of trailing-3y readings ≤ 6.0%" rather than a bare ceiling. | 0003 |
| 11 | Add `hypothesis_transitions(id, ts, hypothesis_id, from_state, to_state, run_id, detail)` to the results schema. | 0008 |
| 14 | First bullet reads "hard token **and cost** ceilings per run and per cycle". Model tiering names one model per section 13 role rather than `cheap`/`expensive`. | 0007, 0012 |
| 15 | `src/` contains a single `signal_lab/` package; `loaders/`, `signals/`, `harness/`, `portfolio/`, `stats/` sit under it. `vetoes/` and `render/` unchanged. | 0010 |
| 4, 8, 10 | Turnover is **traded notional** (buys plus sells). Section 8's formula is then literal. Section 4's 100% is a soft target with a one-sided penalty, not a second ceiling. | 0017, 0018 |
| 5.1 | `index_etf_map.csv` is replaced for v0.3 by `investable`, `cost_bucket` and `reporting_class` columns on the coverage table. ETF selection deferred to phase 4. | 0013 |
| 13 | The cycle's proposer runs **weekly**, not nightly. The deterministic steps may run nightly. | 0007 |
| 5.6 | `VintagePanel`'s period field is `period_end`, not `real_date`: JPMaQS uses `real_date` for the knowledge date and the two inverted. | 0014 |
| 6 | The characteristic map carries per-cell provenance (measured vs estimated) and is **time-varying**; estimated loadings are fitted walk-forward. | 0015 |
| 10 | The `lookahead` veto extends to estimated parameters, not only observed vintages — an exposure matrix or a set of regime probabilities fitted on the full sample leaks without misdating anything. | 0015, 0019 |
| 4 | The tracking-error penalty coefficient is a function of conviction, not a number. | 0019 |

## Open questions — NOT amendments, and deliberately not applied

The constitution should not pretend to settle what the lab has not learned.
These stay open in the code as nulls that refuse, or as registered hypotheses.

- Section 4's asymmetric TE penalty has two coefficients and both are null. The
  objective refuses to build until they are set, deferred by the owner until a
  candidate model exists. (0003, 0019)
- ~~Whether hedged series belong in the investable universe.~~ Answered: they do
  not. `investable: false` on all six. (0013, closed 2026-09-10)
- ~~Section 6 does not say whether an equity index carries a duration exposure
  of zero or an estimated rate beta.~~ Answered: estimated, robustly. (0015)
- The robust estimator for factor loadings is unchosen — shrinkage, resampling,
  robust regression or regime-conditional. It will live in
  `params/characteristics.yaml`, which does not exist yet. (0015)
- ~~The turnover penalty coefficient and shape.~~ Settled: 10bp per unit of
  excess turnover, linear, one-sided above the 100% target. 5bp/yr at the 150%
  ceiling, a third of the real spread. (0018)
- The tracking-error penalty's FORM is settled: conviction-scaled, linear
  between two endpoints, floored (0019). The two coefficients stay null until a
  candidate model exists (owner, 2026-09-09) and the objective refuses until
  then, which is the correct state rather than a gap. (0003, 0019)
- ~~Whether the penalty reads certainty or dispersion.~~ Registered as
  H-2026-0012, a measurement hypothesis: the combination is a finding, not a
  setting. Placeholder default is `minimum`. (0019)
- Conviction scaling is a falsifiable claim and should be registered as a
  measurement hypothesis rather than tuned against net IR. (0016, 0019)
