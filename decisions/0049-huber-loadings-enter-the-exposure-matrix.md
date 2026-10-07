# 0049 — Huber loadings, on the six factors, enter the exposure matrix

**Status:** decided 2026-10-07 by the owner (OWNER-QUEUE B5 and L25: "i accept
all of your suggestions for the pending decisions"). Drafted by Cowork.
Follows `decisions/0015`, `0016` and `0046`. Applied in part by HANDOFF task
51. No change to `SUBSTRATE.md`, `params/` or `vetoes/`.

## What 0046 produced

Five candidates were tested against rolling OLS on out-of-sample loading
fidelity (run of record `M-20261003T181155Z`; 86 instruments, 835 weeks).
**None was detected.** 0046 §3 says that in that case the incumbent stays. The
incumbent fails 0046's own uncertainty check (worst-year bias 1.80 against a
ceiling of 1.72). So §3 has no output that satisfies all of §3, and choosing
any estimator waives one part of it.

Task 48 then described what the test had not scored:

- **The fit is the same for all six estimators.** Pooled out-of-sample R² runs
  from 0.691 to 0.704.
- **The order of the two filters depends on one line of code.** With West and
  Harrison's covariance update the Kalman candidate reads +0.0027 (adjusted p
  0.052) and the mean-reverting candidate +0.0018 (0.264). As coded they read
  −0.0005 and +0.0028 (0.057).
- **Huber's numbers are the same in both runs.** Statistic +0.0016, adjusted p
  0.20, worst-year bias 1.68 (passes). Its loadings are as stable as rolling
  OLS's (weekly change 1.03 times, annual 0.95 times) and agree with them in
  rank (0.98).

## The ruling

1. **The estimated cells of the exposure matrix are Huber loadings,** in the
   configuration registered as H-2026-0013 and not changed: Huber M-estimator,
   c = 1.345, MAD scale, 156 weeks, at least 104 valid weeks, sandwich
   covariance, all six factors in one regression, walk-forward.
2. **It is adopted on the owner's judgement. It was not detected by the
   gate.** H-2026-0013's recorded verdict stays `not_detected`. The part of
   0046 §3 that is waived is "the incumbent stays", because the incumbent is
   not eligible under the same section.
3. **The reason is robustness and simplicity, with the fit equal.** The owner
   asked for robustness first (2026-10-01). The mean-reverting candidate
   (H-2026-0017) had the lowest loss as coded; that edge did not survive the
   filter-update sensitivity.
4. **The six factors stay** (equity, real yield, inflation, credit, dollar,
   commodities; `decisions/0046` §1). A wider factor set is not tested first.
5. **Each instrument carries its explained share,** so the risk decomposition
   can say how much of a position the six factors do not cover. The fit runs
   from 0.30 (Gold) to 0.92 (Treasuries) by class
   (`results/measurement/M-20261003T181155Z/fit.md`).
6. **Measured cells stay measured** (`decisions/0015`): a bond index's
   duration and spread come from the analytics panel, not from a regression.
   One yield factor understates long-bond duration by about 30%.

## What it does not decide

- **The columns of the exposure matrix, and which cells are measured.**
  SUBSTRATE §6 names seven view axes (duration, credit, region, sector, style,
  real/nominal, cash). The regression has six factors. How the one maps to the
  other is `decisions/proposed/0050` and OWNER-QUEUE L27. Task 51 builds only
  what every answer to L27 needs.
- **The `lookahead` veto's extension to estimated parameters** (SUBSTRATE §6,
  `decisions/0015`). It lands with the task that wires the matrix into
  `resolve_exposures`, as an owner-only patch.
- **Tradable-only series,** which inherit loadings (SUBSTRATE §5.2).

## What would reopen it

- A new measurement round on a wider factor set. It would be chosen after
  seeing where the fit is weak, and would be charged for that.
- Evidence that Huber's loadings behave badly inside the solver, once there is
  one.
