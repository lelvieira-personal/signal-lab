# 0043 — The multiple-testing gate: two false passes at 5%, 100 shuffles per test

**Status:** decided 2026-10-01 by the owner (OWNER-QUEUE L16(a), "agree with
recs"). Drafted by Cowork. Applied by HANDOFF task 42, which cites this record.
Amends SUBSTRATE §9, §10 and §13. Closes L16.

## The measurement

All numbers are from the registry-shaped Monte Carlo (`scripts/fdr_vs_fwer.py`):
m = 12, rho_w 0.3, rho_b 0.2, n_true = 3, 5,000 reps. The final run is task
41's, `results/fdr_vs_fwer/20260930-031720/`, after the pooled-standardisation
fix. Power at IC 0.70 (and IC 0.35), by shuffles per test k:

| procedure | k = 50 | k = 100 | k = 1000 |
|---|---|---|---|
| Romano-Wolf, FWER 5% | 0.13 (0.03) | 0.16 (0.04) | 0.18 (0.04) |
| **generalized, P(V ≥ 2) ≤ 5%** | **0.28 (0.09)** | **0.32 (0.10)** | 0.35 (0.10) |
| BH, FDR 10% | 0.07 (0.02) | 0.14 (0.03) | 0.29 (0.07) |

Under the complete null, the generalized procedure holds P(V ≥ 2) at
0.042-0.055 at every k. It lets at least one false pass through in 17-21% of
null cycles. Its power is nearly flat in k. BH needs k ≥ 500 to match it, at
about 140 engine-hours per cycle.

## The ruling

1. **The gate is the Romano-Wolf generalized stepdown** (Romano & Wolf 2007,
   *Annals of Statistics* 35(4), Algorithm 2.1; `stats.multiple_testing.romano_wolf_gfwer`).
   It holds **P(two or more false passes in a search) ≤ 5%**: g = 2, α = 0.05.
2. **Each statistic is standardised against its pooled null** (observed value
   plus the k draws) before the maximum (`decisions/0041`, task 41).
3. **k = 100 block shuffles per test.** That's about 28 engine-hours per cycle
   at 12 hypotheses, which fits the weekly cadence of §13. k = 50 costs half
   and loses about 0.04 of power. **The choice of 100 within the owner's
   approved 50-100 range is Cowork's;** the owner can change it in params.
4. **Why this and not FDR.** The lab is a screen (`decisions/0039`), so
   tolerating one false candidate is acceptable. Replication and economic
   intuition catch it downstream. But BH's power advantage only appears at a
   shuffle budget the lab can't afford, while the generalized stepdown buys
   twice Romano-Wolf's power at any k. RSW-FDR stays unimplemented (task 38).
5. **Reporting.** A candidate that passes is reported with the expected number
   of false passes in its cycle's gate, never as a confirmation.

## Consequences

- The `multiple_testing` veto checks that the verdict was produced by this
  procedure, at this α and g, with k ≥ the params value.
- `params_hash` changes.
- The family-then-within structure of §9 is unchanged and still undefined in
  practice (OWNER-QUEUE L12). It becomes measurable once `signals/` exists.

- **params_hash, 2026-10-01 (HANDOFF task 42):** params_version 0.7.0 -> 0.8.0; `params_hash` moved `571f33fc6afee7273b45359ab310ff89025e353b8e7e5f959a6c5507e00b35d0` -> `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8`. Runs before and after are not hash-comparable without the explicit overrides (`vol_halflife=None`).
