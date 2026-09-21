# 0035 — The transfer coefficient measures the benchmark, not the tilt

Proposed 2026-09-20 by Cowork. **DECIDED by the owner 2026-09-21: §4 option (a)
and §5 both taken.** All three estimators are computed on `w - w_baseline` with
the long-only NNLS tracking portfolio as the baseline; weights, alpha and the
rebalance-date index are persisted per run. §4a below is added with the
implementation spec and one measurement the owner's question exposed as missing. Amends `decisions/0033`, which is otherwise unchanged. Evidence:
`A-20260919-155557` (644 cells, 13.3 h, rc=0).

## 1. What the first measurement said

| statistic | median | max | literature |
|---|---|---|---|
| `transfer_coefficient` (full matrix) | **0.018** | 0.085 | 0.3-0.8 |
| `transfer_coefficient_diagonal` | 0.050 | 0.241 | 0.620 (CDT 2006, EAFE) |
| `transfer_coefficient_alignment` | 0.030 | 0.386 | — |

`transfer_n_dates` is healthy — 782 to 830 of 834 rebalances, median 821, and no
cell returned zero. The alpha reaches the estimator and the conditioning is not
silently dropping dates. The numbers are what the estimator computed.

## 2. They are not measuring what 0033 intended

Two independent lines of evidence, reached separately and agreeing.

**The oracle cells.** At **IC = 1** — a perfect forecast of the forward active
return — the same cells read **0.039 to 0.042** full and **-0.003 to 0.029**
diagonal. A perfect signal cannot have a transfer coefficient of four per cent.
Whatever this measures, it is not how much of the forecast reaches the book.

**Constructed books, through the repo's own `transfer.coefficients()`:**

| book | full | diagonal |
|---|---|---|
| the ideal direction itself | ±1.00 | 0.80 |
| **pure benchmark replication, no view at all** | **-0.017** | **0.009** |
| replication + a perfectly aligned tilt, **total** weights | **0.026** | **0.085** |
| the same book, **active** weights (`w - w_baseline`) | **0.984** | **0.799** |

The second row is the finding: a book holding **no view whatsoever** reads the
same coefficient as every cell in the audit. The estimator cannot distinguish a
book with a view from one without.

## 3. Why

The benchmark legs are not holdable. The book replicates the benchmark out of
the holdable universe and tilts away from it, so `w` is
`w_replicating + tilt`, where the replicating part is almost the whole book and
is uncorrelated with alpha by construction.

`active_covariance()` is right and its test is right: because the book is fully
invested, `w' Omega w` really is the active variance, with the benchmark legs
carried at `-b`. The error is in the **numerator and the correlations**, which
take the same total `w`. `a'w` is not the active exposure and
`corr(a_i/sigma_i, w_i sigma_i)` is not the active tilt; both are dominated by
replication, which drags all three estimators toward zero.

**One subtlety worth recording, because it nearly refutes the above.** The
alignment form `corr(a, Omega w)` is **invariant** to adding any multiple of the
minimum-active-variance portfolio, since `Omega w_minvar` is a constant vector
and correlation ignores constants — verified. So if the baseline were the
minimum-variance portfolio, alignment would be immune and its reading of 0.030
would be real. It is not immune: the book's baseline is the **long-only NNLS
tracking portfolio**, whose `Omega w` is not constant. Alignment is contaminated
too, just less transparently.

## 4. Proposed fix — owner decision 1

Compute all three estimators on the **active** weight,
`w_active = w - w_baseline`, where `w_baseline` is the long-only NNLS tracking
portfolio the lab already builds to embed the benchmark legs. `Omega` and
`w' Omega w` are unchanged; only the numerator and the correlations move.

The definition question the owner settles: **what "active weight" means when the
benchmark legs are not holdable.** Two defensible answers:

- **(a) The NNLS tracking portfolio is the baseline.** Recommended. It is the
  book the strategy would hold with no view, it already exists in the code, and
  it makes TC answer the question 0033 asked: how much of the forecast survives
  into the deviation from the benchmark.
- **(b) The minimum-active-variance portfolio is the baseline.** Cleaner
  mathematically — it is the argmin of `w' Omega w` subject to the budget, so it
  is the unique no-view book in `Omega`'s own metric — but it is not the book the
  strategy actually holds, and TC would then measure deviation from a portfolio
  nobody builds.

Under either, the acceptance test is the one this record used: **an IC = 1
oracle cell must read a TC near its achievable ceiling, and a no-view book must
read near zero.** Both are cheap and neither exists today. They should be tests,
not a one-off check.

## 4a. Implementation spec, and the replication quality nobody has measured

Added 2026-09-21, after the owner asked whether the NNLS tracking portfolio is
"basically the same as holding the benchmark".

**It is the intent, and it is not the same thing.** `portfolio/covariance.py`
builds it by regressing each benchmark leg's returns on the holdable
instruments with `scipy.optimize.nnls`, weights constrained non-negative and
sum-to-one imposed softly as a heavily weighted extra row. So it is the closest
long-only holdable approximation to the benchmark, which is exactly what §4
wants. Three differences matter for what the corrected TC will mean:

1. **It is a fitted replication with a residual.** The same function already
   computes `residual_variance` and `r2` per leg and stores them in its
   `diagnostics` dict — and **nothing surfaces them.** No run report, no
   `summary.json` key, no test asserts a floor. So the quality of the baseline
   that the corrected transfer coefficient will now be measured against is
   **unmeasured**. If `r2` is around 0.97 the owner's intuition holds; if it is
   0.80 the baseline carries a large idiosyncratic lump and every corrected TC
   inherits it.
2. **It moves.** The fit runs on the covariance window, so the baseline is a
   time-varying replication, not a fixed benchmark holding. `w - w_baseline` is
   therefore "active against this week's replication", which is the right
   definition for a book that must hold the benchmark synthetically, but it is
   not "active against the benchmark" in the textbook sense.
3. **It is not the minimum-active-variance book.** §3 records why that matters:
   `Omega w` is constant for the min-variance portfolio and not for NNLS, so the
   alignment estimator is immune to the former and not to the latter. Taking
   option (a) keeps alignment contaminated in principle — correctly now, because
   it is contaminated by the book the strategy actually holds.

**Therefore, added to this record as a requirement, not a suggestion:** surface
`r2` and `residual_variance` per benchmark leg wherever the corrected TC is
reported, and assert a floor on `r2` in a test so a degraded replication fails
loudly rather than quietly re-basing the transfer coefficient. The numbers are
already computed; only the plumbing is missing.

## 5. Persist the weights and the alpha — owner decision 2

`results/artifacts/` is **empty**. `STATUS.md` says artifacts are parquet under
`results/artifacts/<run_id>/`; the audit writes none. So a measurement computed
during a run cannot be recomputed after it, and correcting this column costs
another **13.3 hours** rather than minutes.

Proposed: persist `weights`, `alpha` and the rebalance-date index for at least
the base cells of an audit. The cost is disk; the saving is that the next
measurement bug — and on this evidence there will be one — is a re-derivation
instead of a re-run.

This is what turned a definition error into an overnight job, and it will do so
again for `L`, for the breadth work, and for anything the search adds later.

## 6. What is NOT proposed

- **No change to `decisions/0033`'s choice of estimator.** The full-matrix form
  is still the reported TC, with the diagonal for comparability and the
  alignment as the control. Only the weight vector they consume changes.
- **No conditioning of `Omega`.** `decisions/0029` §2 stays deferred. The
  condition number of 9.1e4 median, 2.9e5 max is reported and unchanged.
- **No re-run scheduled here.** Whether to spend another 13.3 h on a corrected
  TC depends on the dose-response probe (`claude/dose-response-probe-plan.md`),
  which may want a different grid anyway. Sequence them before spending the
  night.

## 7. What this does not explain

The ladder's flatness. Net IR runs 0.28-0.37 whether IC is 0.02 or 0.20, and a
corrected TC would explain that **only if** transfer is genuinely low. As
computed, TC cannot bear on the question at all, because it reads the same for a
book with a view and a book without one. The two are the same investigation and
neither settles first.
