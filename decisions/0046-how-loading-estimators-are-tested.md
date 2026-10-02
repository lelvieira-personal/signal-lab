# 0046 — How factor-loading estimators are tested: the factors, the score, the candidates

**Status:** decided 2026-10-01 by the owner (OWNER-QUEUE B5: "046 is
approved"). Drafted by Cowork. The approval covers the record as written:
the items marked *Cowork's choice*, the bootstrap null of §3 as a ruling for
measurement tests, and leaving Michaud resampling out. The owner also agreed
that the factors are not orthogonalised and that nothing is added for it now.
Nothing here is applied until HANDOFF task 45 lands it. Extends
`decisions/0015` and `0016`. No change to `SUBSTRATE.md`, `params/` or
`vetoes/`.

## What the owner said

- "It is important to have robust factor estimates. OLS may not deal well with
  outliers and not capture coefs uncertainty or change in coef regime."
- The factors "need to capture as independently as possible factor that capture
  the variance of the market such as equity beta, credit spreads, yields,
  currency effect, inflation, commodities, etc."
- Loadings are **partial betas from one joint regression**, not one factor at
  a time.
- The fidelity metric is the out-of-sample fit of next-period returns on factor
  returns, using loadings estimated only up to the earlier date (2026-10-01).

## Why this may run now

SUBSTRATE §16 puts "characteristic map, factor loadings" in phase 2, "still no
search". `decisions/0016` has measurement hypotheses run **before** the signal
search. §5.6 closes the *signal* search until JPMaQS lands; a test of
estimators on Bloomberg returns is not a signal test, ranks nothing on net IR,
and builds no portfolio. *This is Cowork's reading of the three texts.*

## 1. The factors

Six, weekly (Friday to Friday), all from series already in the Bloomberg
snapshot. Each is signed so that its name says what a positive value means.

| Factor | Definition | Series | Daily from |
|---|---|---|---|
| Equity | ACWI total return minus cash | `NDUEACWF` − `LD20TRUU` | 1999 |
| Real yield | change in the 10y TIPS yield | `GTII10` | 1997 |
| Inflation | change in the 10y breakeven | `USGGBE10` | 1999 |
| Credit | change in US IG corporate OAS | `LUACOAS` | 2001 |
| Dollar | log change in the dollar index | `DXY` | 1971 |
| Commodities | commodity index return minus cash | `BCOMTR` − `LD20TRUU` | 1970 |

- **Real yield and inflation, not nominal yield and inflation.** A nominal
  yield is the sum of the two, so using it beside the breakeven would put the
  same move in two factors. Split this way, a nominal bond loads about minus
  its duration on both, and a TIPS index loads on the real yield only.
  *Cowork's choice.*
- **Credit is a spread, so it is already net of rates.** IG, not HY, so that an
  IG index's loading reads as its spread duration. *Cowork's choice.*
- **`DXY`, not `BBDXY`,** because `BBDXY` starts in 2005. `DXY` is heavy in the
  euro, and that is a known weakness. *Cowork's choice.*
- **The factors are not orthogonalised.** The joint regression already gives
  partial betas. Orthogonalising needs an ordering, and the ordering would
  decide the answer. The run reports the factors' rolling correlation matrix,
  so "as independently as possible" is measured and not assumed. Equity
  against credit is the pair to watch.
- **Left out, for the owner to add if wanted:** volatility, liquidity, and a
  second (HY) credit factor.
- **Common sample.** Credit starts in 2001, so the first 156-week estimate is
  in 2004, and loadings are scored from then to 2019. *The exact first date is
  for task 45 to report; Cowork has not read the series.*
- **A built-in sanity check.** The matrix also holds measured cells
  (`decisions/0015`). A Treasury bucket's estimated real-yield loading should
  sit near minus its measured `INDEX_OAD_TSY`, and an IG index's credit loading
  near minus its duration. The run reports both side by side. It is a check on
  the harness, not a score.

## 2. What is estimated, and on what

- **Instruments:** every investable series in the backbone and second tiers.
  Tradable-only series inherit loadings and are never used to estimate
  (SUBSTRATE §5.2).
- **Model:** `r_i,t = a_i + b_i' f_t + e_i,t`, weekly, all six factors at once.
- **Walk-forward:** the loading used for week t+1 is estimated on data up to
  the Friday of week t. Nothing after it. No observation on or after
  2020-01-01 is read.
- **Known limitation:** Asian and European closes lead the US close by part of
  a day, which biases a weekly beta slightly toward zero. It is reported, not
  corrected, in this first test.

## 3. The score

**The ranking metric (one number per estimator, the only one the gate tests).**
- The prediction for week t+1 is `b_i,t' f_t+1`. The intercept is left out, so
  only the loadings are scored.
- The error is scaled by the instrument's own robust volatility known at t
  (1.4826 × the median absolute deviation of its returns over the estimation
  window), so no instrument dominates.
- The loss is **Huber's**, at the standard tuning constant 1.345. Squared
  error would itself be driven by outliers and would punish the robust
  estimators this test exists to find.
- The statistic is the mean, over weeks, of the cross-sectional mean of
  (incumbent's loss − candidate's loss). Positive means better than the
  incumbent.

**The gate.** `stats.multiple_testing.gate`, with four candidates, so g = 1
(`decisions/0045`), α = 5%.
- **The null is a centred block bootstrap of the weekly loss differentials**
  (White 2000; Romano and Wolf 2005), not a block shuffle. There is no signal
  to shuffle here; the question is whether a loss difference is
  distinguishable from zero. `decisions/0041` covers signal tests, so **this
  is a new ruling for measurement tests** (owner, 2026-10-01).
- Blocks of 26 weeks, 1,000 draws. *Both are Cowork's choices.* The run is
  cheap, so the draw count is not the binding cost that it is for signals.

**The uncertainty check (pass or fail, not a score).**
- Every estimator must output a covariance for its loadings.
- Its standardised prediction errors, `e / sqrt(f' V f + s²)`, are read with
  the bias statistic of `decisions/0027` and `0030`: per calendar year, taken
  at the worst year, against the existing ceiling
  `vetoes.risk_calibration.max_worst_annual_bias` (1.72). No new threshold.
- An estimator that fails is not eligible, whatever its rank.

**Regime slices (reported, never gated).**
- The decile of weeks with the largest factor moves.
- Three sub-periods: 2004-2007, 2008-2009, 2010-2019.

**How a winner is chosen.** Among candidates that pass the gate and the
uncertainty check, the one with the largest statistic. If none passes, the
incumbent stays and the record says so. **The run chooses nothing by itself:**
adopting an estimator into the exposure matrix is a separate owner decision,
made on the report.

## 4. The incumbent and the candidates

One configuration each, fixed here before any result exists. Trying several
windows or tunings per method would be the multiplicity problem this lab
exists to control.

| | Estimator | Configuration | Answers |
|---|---|---|---|
| Incumbent | Rolling OLS | 156 weeks, equal weights, classical covariance | the baseline |
| H-2026-0013 | Robust regression | Huber M-estimator, c = 1.345, MAD scale, 156 weeks, sandwich covariance | outliers |
| H-2026-0014 | Theil-Goldberger shrinkage | OLS on 156 weeks mixed with a stochastic prior: the mean loading of the instrument's reporting class at t, with the class's cross-sectional dispersion as the prior covariance | coefficient uncertainty |
| H-2026-0015 | Regime-conditional | two-state Gaussian HMM on the six factors, expanding window, refitted weekly; per-regime weighted least squares; the prediction mixes the regimes by the state probability forecast for t+1 | discrete regime change |
| H-2026-0016 | Time-varying (Kalman) | random-walk loadings in a dynamic linear model with a discount factor, chosen at each t by one-step predictive likelihood on data up to t from {0.97, 0.98, 0.99, 0.995, 0.999} | gradual drift, and uncertainty |

- **The 156 weeks** match the covariance window (`params/audit.yaml`).
- **The HMM uses a fixed seed and ten restarts,** and the run reports whether
  the regimes are stable across restarts.
- **The discount grid and the reporting-class prior are Cowork's choices.**
- **Michaud resampling is not registered** (owner agreed, 2026-10-01).
  Applied to a linear estimator, the average of resampled loadings is the OLS
  loading again, to within simulation noise. It would enter the gate as a
  candidate that cannot beat the incumbent on the ranking metric. Its value
  is an honest covariance, and that can be added to any estimator later
  without a test of its own.

## Consequences

- Four hypothesis files, drafted in `hypotheses/proposed/`. Task 45 moves them
  to `hypotheses/pending/` before any estimator touches real data, which is
  the pre-registration.
- A measurement run produces no portfolio, so the portfolio vetoes are
  `not_applicable` (`decisions/0016`).
- The result is a report. It changes no parameter and opens no search.
