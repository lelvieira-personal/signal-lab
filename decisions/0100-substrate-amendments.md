# 0100 — Amendments to SUBSTRATE.md awaiting the owner's edit

Status: running list, opened 2026-09-09.

Agents may not edit `SUBSTRATE.md` (section 2). Where a decision changes what
the constitution says, the change is recorded here for the owner to apply, and
the code is written to the amended reading with the decision cited in place.

This file exists so that the drift between code and constitution is visible in
one place rather than scattered across decision records.

| Section | Amendment | Decision |
|---|---|---|
| 10 | Eleven vetoes, not ten: add `active_drawdown`. The `tracking_error` row reads "95th percentile of trailing-3y readings ≤ 6.0%" rather than a bare ceiling. | 0003 |
| 11 | Add `hypothesis_transitions(id, ts, hypothesis_id, from_state, to_state, run_id, detail)` to the results schema. | 0008 |
| 14 | First bullet reads "hard token **and cost** ceilings per run and per cycle". Model tiering names one model per section 13 role rather than `cheap`/`expensive`. | 0007, 0012 |
| 15 | `src/` contains a single `signal_lab/` package; `loaders/`, `signals/`, `harness/`, `portfolio/`, `stats/` sit under it. `vetoes/` and `render/` unchanged. | 0010 |
| 5.1 | `index_etf_map.csv` is replaced for v0.3 by `investable`, `cost_bucket` and `reporting_class` columns on the coverage table. ETF selection deferred to phase 4. | 0013 |
| 13 | The cycle's proposer runs **weekly**, not nightly. The deterministic steps may run nightly. | 0007 |

## Not yet amendments, but open questions against the constitution

- Section 4's asymmetric TE penalty has no coefficient. The objective refuses to
  build until one is set. (0003)
- Section 4 says hedged series are not a live axis; whether they belong in the
  investable universe follows from that and is unanswered. (0013)
- Section 6 does not say whether an equity index carries a duration exposure of
  zero or an estimated rate beta. (0013)
