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

## Addendum, 2026-10-02: the Cash class is not scored (owner, OWNER-QUEUE L22)

§2 scored "every investable series in the backbone and second tiers". That
included the T-bill index (`LD20TRUU`, reporting class Cash). Its robust
volatility is near zero, so its scaled errors are enormous: in the registered
run `M-20261002T033239Z` it is about 100% of the loss differential for three
of the four candidates, and their statistics there mean nothing. Cash is also
what the equity and commodity factors are measured over, so its loading on
them was never a measurement target. **This was Cowork's spec error.**

**The owner's ruling: the Cash class is excluded** ("yes exclude cash").

- **The result of record is the run without Cash,** `M-20261002T034221Z-sens`:
  86 instruments, 835 weeks. All four candidates are `not_detected`, the same
  verdicts the registered run recorded, so no hypothesis moves.
- **This is a fix made after the results were seen,** and it is disclosed as
  such. It changes which instruments are scored. It changes no estimator, no
  configuration and no verdict.
- HANDOFF task 46 makes the exclusion the default and re-runs once, to add
  the incumbent's mean loss and a by-class breakdown to the report. Its four
  statistics must equal the sensitivity run's.

**Also recorded, not ruled:** rolling OLS itself reads 1.80 against the 1.72
ceiling of the uncertainty check, in 2008. §3's "if none passes, the incumbent
stays" did not anticipate an ineligible incumbent. Which estimator enters the
exposure matrix is still the owner's decision (OWNER-QUEUE B5).

## Addendum, 2026-10-02: a fifth candidate, mean-reverting Bayesian loadings (owner, OWNER-QUEUE B5)

**The owner asked** whether any method tried combines Bayesian regression, a
time-varying component and shrinkage toward a long-run mean. None does. The
Kalman candidate is Bayesian and time-varying, but its loadings follow a
random walk, so there is no mean to return to. The Theil-Goldberger candidate
shrinks, but toward a peer average on a fixed window. **The owner's ruling:**
register and test such a method, with **the instrument's own long-run mean**
as the level it shrinks to ("the long run mean could be the instrument's own
mean").

**H-2026-0017, `mean_reverting_dlm_own_mean`.** One configuration, fixed here
before it runs. *Everything below except the choice of the instrument's own
mean is Cowork's design, for the owner to change before task 47 starts.*

- **The model.** `r_t = a + b_t' f_t + e_t`, with `b_t = mu + d_t` and
  `d_t = phi * d_(t-1) + w_t`. `mu` is the instrument's own long-run loading
  and `d_t` is a deviation that decays back to zero.
- **`mu` is in the state, not estimated separately.** The Kalman filter
  carries `(a, mu, d_t)`, with `mu` constant and a diffuse prior. So the
  long-run mean is learned from all of the instrument's own history to date,
  its uncertainty is carried, and no step can see past t.
- **The loading scored for week t+1 is the one-step forecast,**
  `mu_hat + phi * d_hat_t`, with its forecast covariance. This is where the
  shrinkage acts: each week the loading is pulled toward `mu` by `1 − phi`.
- **The size of the deviations.** The innovation covariance is
  `(1 − phi²) * q * C_t`, where `C_t` is the scaled covariance of the 156-week
  rolling OLS loading at t. So `q` reads as how far a loading wanders from its
  long-run mean, in units of a three-year OLS estimate's sampling variance.
- **Two settings, chosen walk-forward and never tuned on the weeks scored.**
  At each t, `(phi, q)` is the pair with the highest cumulative one-step
  predictive likelihood on data up to t, from a fixed grid: half-lives of 13,
  26, 52 and 104 weeks, and `q` of 0.25, 1 and 4. This is the same device as
  the Kalman candidate's discount grid.
- **Observation variance:** learned as in the existing Kalman candidate
  (variance learning, Student-t predictive).
- **Minimum history:** the lab's existing 104-valid-week rule.

**How much history the long-run mean has.** The indices themselves go back
well before 2001, but the six factors only exist together from 2001-01-05,
which is also the start of the development window. So the long-run mean rests
on about three years of data at the first scored week in 2004 and on nineteen
by 2019, and on less for the twelve second-tier instruments. Early in the
sample this candidate is close to a filtered OLS; its distinct behaviour grows
with history.

**The test.** Same factors, score, uncertainty check and slices as §1-§3, on
the instruments of the Cash addendum.
- **The gate runs over all five candidates, at g = 1.** This one was designed
  after the first four results were seen, so it is charged for the whole
  search and not tested alone.
- **The recorded verdicts of H-2026-0013 to 0016 stand.** If the five-way run
  would flip one, task 47 stops and reports.
- The run chooses nothing. Adoption remains the owner's decision.

## Addendum, 2026-10-03: how the fifth candidate starts, and what task 47 found (recorded by Cowork)

**The start (owner, 2026-10-03).** The 2026-10-02 addendum gave `mu` a
diffuse prior and also made the innovation covariance depend on the 156-week
rolling OLS, which does not exist before an instrument has 104 valid weeks.
Both cannot hold, so Claude Code stopped and asked. **The owner's ruling, as
the task 47 receipt reports it** (Cowork did not witness it): the filter
starts at the first week a rolling OLS exists and is seeded from it. `a` and
`mu` take that OLS's coefficients and their covariance; the deviation starts
at zero with covariance `q * C_ols`. Until this addendum the ruling was
recorded only in the estimator's docstring and in commit `b0c7713`.

**The result: `not_detected`.** Run `M-20261003T181155Z`, 86 instruments, 835
weeks, Cash excluded, the gate over five candidates at g = 1.

| Estimator | Mean Huber loss | Statistic | Adj. p | Worst-year bias (ceiling 1.72) |
|---|---|---|---|---|
| Rolling OLS (incumbent) | 0.2319 | – | – | 1.80, fails |
| Huber | 0.2303 | +0.0016 | 0.200 | 1.68, passes |
| Theil-Goldberger | 0.2310 | +0.0009 | 0.179 | 1.83, fails |
| HMM | 0.2385 | −0.0066 | 1.000 | 1.38, passes |
| Kalman | 0.2325 | −0.0005 | 0.941 | 1.58, passes |
| Mean-reverting (H-2026-0017) | 0.2291 | +0.0028 | 0.057 | 1.59, passes |

The incumbent and the first four reproduce task 46's run field for field
(Cowork compared the two `summary.json` files). The recorded verdicts of
H-2026-0013 to 0016 stand.

**Read by Cowork, not ruled** (detail in the Project doc
`claude/task-47-review-2026-10-03.md`):
- **§3's rule has no eligible output.** No candidate passes the gate, so "the
  incumbent stays"; but the incumbent fails the uncertainty check. Whatever
  enters the exposure matrix waives one part of §3.
- **0.057 is 57 exceedances in 1,001.** At 1,000 draws its simulation error is
  about 0.007, so the miss is one standard error wide. The verdict stands as
  registered. Re-drawing to chase it would be a second look.
- **Where the gain is.** By sub-period the statistic is 0.0009 (2004-07),
  0.0024 (2008-09) and 0.0037 (2010-19); by halves 0.0031 and 0.0025. Solving
  the two together puts about 0.008 in 2010-11 and 0.0025 in 2012-19
  (Cowork's arithmetic, approximate). The gain is largest while 2008 sits in
  the rolling window. That is the mechanism the hypothesis named. The claim
  that the gain grows with history is not supported.
- **The grid binds at both ends.** Half-lives of 13 and 104 weeks hold 90% of
  the scored cells and `q = 4` holds 70%. A wider grid is a sixth test.
- **A permanent level shift.** On the test's synthetic series the stored
  loading halves the gap in 78 weeks. Rolling OLS takes 77 and Huber 78 on the
  same series; the Kalman candidate takes 42 (Cowork's run of the committed
  code).
- **The filter's covariance update is not West and Harrison's.** Both Kalman
  candidates carry a ratio `S / S_new` that the textbook recursion does not
  have in scaled form. It is a coherent filter (each observation enters at the
  variance estimate of the week before). On synthetic series it changes the
  mean-reverting candidate's error by 1% or less and the Kalman candidate's
  reported covariance by more. HANDOFF task 48 names it in the docstrings and
  runs one sensitivity on real data. **That sensitivity changes no verdict,
  whichever way it reads.**

**Still the owner's:** which estimator enters the exposure matrix
(OWNER-QUEUE B5).
