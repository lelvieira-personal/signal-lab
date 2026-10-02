# Loading-estimator test, M-20261002T033239Z

A measurement run (decisions/0016, decisions/0046): out-of-sample loading fidelity against rolling OLS. No portfolio, no net IR. **The run chooses nothing**; adoption is the owner's decision.

- Sample: 2001-01-05 to 2019-12-27; 991 weeks with all six factors; 835 weeks and 87 instruments scored (71161 instrument-weeks).
- Units: {'real_yield': 'percent -> decimal', 'inflation': 'percent -> decimal', 'credit': 'percent -> decimal'}
- Gate: `romano_wolf_gfwer`, alpha 0.05, g = 1, 4 candidates, 1000 centred block-bootstrap draws (26-week blocks).
- Hashes: params `b3d41267a752b9d7`, returns `5987bafe9f1944c5`, factors `3401475eb25cd3c0`.

## Estimators

Statistic: mean over weeks of the cross-sectional mean of (incumbent loss - candidate loss), Huber loss on volatility-scaled errors; positive is better than rolling OLS.

| estimator | statistic | adj. p | gate | worst-year bias | year | bias check | top-decile moves | 2004-07 | 2008-09 | 2010-19 |
|---|---|---|---|---|---|---|---|---|---|---|
| rolling_ols (incumbent) | - | - | - | 1.80 | 2008 | fail | - | - | - | - |
| huber_m | 5.615e+05 | 0.310 | fail | 1.68 | 2008 | pass | 8.98e-03 | -1.82e-04 | 5.69e-03 | 8.98e+05 |
| theil_goldberger_peer_prior | 8.672e-04 | 0.164 | fail | 1.83 | 2008 | fail | 8.05e-03 | 1.32e-03 | 4.46e-03 | -3.08e-05 |
| hmm2_regime_conditional | -8.944e+06 | 1.000 | fail | 1.38 | 2008 | pass | -1.93e-02 | -7.38e-03 | -1.01e-02 | -1.43e+07 |
| kalman_dlm_discount | -9.869e+05 | 1.000 | fail | 1.57 | 2008 | pass | -1.40e-02 | 3.33e-03 | -1.54e-02 | -1.58e+06 |

Bias ceiling: 1.72 (`vetoes.risk_calibration.max_worst_annual_bias`).

## Verdicts recorded

- H-2026-0013 (huber_m): not_detected
- H-2026-0014 (theil_goldberger_peer_prior): not_detected
- H-2026-0015 (hmm2_regime_conditional): not_detected
- H-2026-0016 (kalman_dlm_discount): not_detected

## HMM regime stability across restarts

```json
{
  "n_fits": 836,
  "agreement_min_over_restarts_median_over_weeks": 1.0,
  "agreement_min_over_restarts_worst_week": 0.6416184971098265,
  "agreement_median_over_restarts_median_over_weeks": 1.0,
  "weeks_with_a_restart_below_90pct_agreement": 62
}
```

## Factor correlations

Full sample:

```
             equity  real_yield  inflation  credit  dollar  commodities
equity         1.00        0.02       0.47   -0.48   -0.31         0.45
real_yield     0.02        1.00      -0.18   -0.01    0.29        -0.10
inflation      0.47       -0.18       1.00   -0.41   -0.16         0.35
credit        -0.48       -0.01      -0.41    1.00    0.10        -0.27
dollar        -0.31        0.29      -0.16    0.10    1.00        -0.43
commodities    0.45       -0.10       0.35   -0.27   -0.43         1.00
```

Range of the rolling 156-week correlation, by pair:

- equity~real_yield: -0.28 to 0.37
- equity~inflation: 0.05 to 0.68
- equity~credit: -0.72 to -0.27
- equity~dollar: -0.60 to 0.11
- equity~commodities: 0.06 to 0.72
- real_yield~inflation: -0.50 to 0.21
- real_yield~credit: -0.40 to 0.28
- real_yield~dollar: 0.00 to 0.46
- real_yield~commodities: -0.34 to 0.18
- inflation~credit: -0.54 to -0.03
- inflation~dollar: -0.49 to 0.20
- inflation~commodities: 0.09 to 0.63
- credit~dollar: -0.21 to 0.43
- credit~commodities: -0.47 to 0.06
- dollar~commodities: -0.60 to -0.23

## Measured against estimated (decisions/0046 section 1)

| instrument | class | factor | minus_measured_oad | rolling_ols | huber_m | theil_goldberger_peer_prior | hmm2_regime_conditional | kalman_dlm_discount |
|---|---|---|---|---|---|---|---|---|
| LT01TRUU | Treasuries | real_yield | -1.85 | -1.08 | -1.06 | -1.08 | -1.27 | -1.04 |
| LT13TRUU | Treasuries | real_yield | -4.51 | -4.05 | -4.03 | -4.05 | -4.11 | -4.01 |
| LT09TRUU | Treasuries | real_yield | -7.55 | -7.19 | -7.21 | -7.19 | -6.97 | -7.12 |
| LUTLTRUU | Long Treasuries | real_yield | -14.62 | -10.38 | -10.36 | -10.38 | -10.33 | -10.43 |
| LT11TRUU | Long Treasuries | real_yield | -17.19 | -11.88 | -11.91 | -11.88 | -11.87 | -12.22 |
| LUACTRUU | IG Corporates | credit | -6.61 | -5.74 | -5.66 | -5.74 | -5.40 | -5.74 |
| LDC5TRUU | IG Corporates | credit | -2.76 | -2.38 | -2.25 | -2.38 | -1.88 | -2.52 |

Median over the weeks scored. A check on the harness, not a score.

## Known limitation

Asian and European closes lead the US close by part of a day, which biases a weekly beta slightly toward zero. Reported, not corrected, in this first test.
