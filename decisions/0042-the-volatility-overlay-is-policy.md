# 0042 — The volatility overlay is policy, at a 26-week halflife

**Status:** decided 2026-10-01 by the owner (OWNER-QUEUE B1, "agree with
recs"). Drafted by Cowork. Applied by HANDOFF task 42, which cites this record.
Amends SUBSTRATE §4 (TE handling).

## The measurement

Task 35 (`A-20260930-033812`, 240 cells: IC 0.35 and 0.70, ten seeds, horizons
4, 13 and 26, halflife none, 13, 26 or 52, scalar overlay). Cowork re-computed
every figure below from `cells.csv`.

- **`risk_calibration` fails** drop from 5/20, 10/20 and 10/20 with no overlay
  (horizons 4, 13, 26) to 0, 0 and 1 of 20 at a 26-week halflife. The worst
  annual bias falls from a median of 1.55-1.72 to 1.31-1.42. 2008 stops being
  the worst year in most cells (15-17 of 20, down to 6-8).
- **Net IR, paired by (IC, seed) against no overlay:**
  - h13: +0.051 at 26 weeks (16 of 20 positive) and +0.070 at 13 weeks (15
    of 20);
  - h4 and h26: mixed in sign, within noise.
  - Nine arms were compared, and the two IC rungs share seeds, so the h13
    t-statistics of about 3 overstate the evidence. **This is a risk-model
    fix that does no harm and may help a little. It is not alpha.**
- **`te_p95_to_budget` stays above 1 in every arm.** It is 1.14-1.18 with the
  overlay and 1.26-1.34 without. The overlay narrows the gap but does not
  close it. That is a separate risk-sizing question, not settled here.

## The ruling

1. **The ex-ante covariance carries a scalar volatility overlay, halflife 26
   weeks**, in every book the lab builds: the audit's default cells now, and
   the phase-2 solver when it exists.
2. **Why 26 and not 13.** On this evidence, 13 and 26 can't be told apart.
   26 is the value `decisions/0030` specified *before* the sweep. Taking the
   sweep's best-looking arm would be selection on the same data. (Cowork's
   recommendation, adopted by the owner.)
3. **Where it lives:** `params/audit.yaml`,
   `covariance.vol_overlay: {form: scalar, halflife_weeks: 26}`, next to the
   estimator and window it modifies. Whatever solver phase 2 builds reads the
   same key, so there is one risk model in the lab, not two.

## Consequences

- **`params_hash` changes.** Every grid that claims identity with a named
  historical run must pin `vol_halflife=None` explicitly, as task 39 did for
  the shadow form.
- **H-2026-0008 (volatility scaling) is measured as incremental** to an
  overlay-equipped book, never against the old never-de-risks baseline.
  Otherwise it gets credit for what the risk model does (OWNER-QUEUE B1 note,
  2026-09-18 registry review). The hypothesis file is pre-registered and isn't
  edited; this record is where the constraint lives.
- The 80 h4 cells in `A-20260930-033812` that failed the then-live 400%
  turnover veto are unaffected. That veto is retired (`decisions/0038`), and
  their risk readings stand.

- **params_hash, 2026-10-01 (HANDOFF task 42):** params_version 0.7.0 -> 0.8.0; `params_hash` moved `571f33fc6afee7273b45359ab310ff89025e353b8e7e5f959a6c5507e00b35d0` -> `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8`. Runs before and after are not hash-comparable without the explicit overrides (`vol_halflife=None`).
