# Loading-estimator test, M-20261002T131820Z

Reporting classes not scored (decisions/0046 addendum, 2026-10-02): ['Cash'].

A measurement run (decisions/0016, decisions/0046): out-of-sample loading fidelity against rolling OLS. No portfolio, no net IR. **The run chooses nothing**; adoption is the owner's decision.

- Sample: 2001-01-05 to 2019-12-27; 991 weeks with all six factors; 835 weeks and 86 instruments scored (70326 instrument-weeks).
- Units: {'real_yield': 'percent -> decimal', 'inflation': 'percent -> decimal', 'credit': 'percent -> decimal'}
- Gate: `romano_wolf_gfwer`, alpha 0.05, g = 1, 4 candidates, 1000 centred block-bootstrap draws (26-week blocks).
- Hashes: params `b3d41267a752b9d7`, returns `14a03fd587f6dd2e`, factors `3401475eb25cd3c0`.

## Estimators

Statistic: mean over weeks of the cross-sectional mean of (incumbent loss - candidate loss), Huber loss on volatility-scaled errors; positive is better than rolling OLS.

| estimator | mean Huber loss | statistic | adj. p | gate | worst-year bias | year | bias check | top-decile moves | 2004-07 | 2008-09 | 2010-19 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rolling_ols (incumbent) | 0.2319 | - | - | - | 1.80 | 2008 | fail | - | - | - | - |
| huber_m | 0.2303 | 1.568e-03 | 0.178 | fail | 1.68 | 2008 | pass | 1.02e-02 | -5.43e-05 | 7.04e-03 | 1.13e-03 |
| theil_goldberger_peer_prior | 0.2310 | 8.778e-04 | 0.160 | fail | 1.83 | 2008 | fail | 8.14e-03 | 1.34e-03 | 4.51e-03 | -3.12e-05 |
| hmm2_regime_conditional | 0.2385 | -6.615e-03 | 1.000 | fail | 1.38 | 2008 | pass | -1.41e-02 | -7.56e-03 | -9.21e-03 | -5.72e-03 |
| kalman_dlm_discount | 0.2325 | -5.301e-04 | 0.938 | fail | 1.58 | 2008 | pass | -1.48e-02 | 3.12e-03 | -1.63e-02 | 1.15e-03 |

## Statistic by reporting class (reported, never gated)

| class | instruments | huber_m | theil_goldberger_peer_prior | hmm2_regime_conditional | kalman_dlm_discount |
|---|---|---|---|---|---|
| APAC ex-Japan Equities | 1 | -2.79e-03 | 0.00e+00 | 5.12e-03 | 4.07e-03 |
| Commodities | 1 | -4.02e-06 | 0.00e+00 | -2.72e-05 | 3.72e-06 |
| DM ex-US Equities | 9 | 1.12e-03 | -1.35e-03 | -5.08e-04 | -7.48e-04 |
| EM Corporate Bonds | 1 | 2.43e-02 | 0.00e+00 | -2.03e-02 | 7.06e-03 |
| EM Equities | 12 | 1.58e-03 | 2.22e-03 | -3.30e-03 | -1.88e-03 |
| EM Sovereign Bonds | 2 | 2.31e-02 | 0.00e+00 | 3.19e-03 | 1.24e-02 |
| European Equities | 13 | 2.62e-03 | 2.89e-03 | -7.91e-03 | -4.39e-03 |
| Ex-USD Bonds | 8 | 1.49e-03 | 1.95e-03 | -1.47e-02 | 9.64e-04 |
| Gold | 1 | 2.16e-03 | 0.00e+00 | 9.08e-04 | 1.33e-02 |
| HY Corporates | 5 | -5.46e-03 | -5.68e-03 | -1.09e-02 | 7.36e-03 |
| IG Corporates | 2 | 3.13e-03 | 0.00e+00 | -8.77e-03 | -1.95e-03 |
| Japanese Equities | 1 | 5.93e-04 | 0.00e+00 | 1.23e-03 | 4.85e-03 |
| Long Treasuries | 2 | -1.56e-03 | 0.00e+00 | -1.74e-02 | 1.22e-03 |
| MBS | 1 | -7.48e-03 | 0.00e+00 | 1.16e-02 | 1.85e-02 |
| Real Assets | 4 | 2.79e-03 | 5.45e-05 | -8.99e-03 | -1.01e-02 |
| TIPS | 1 | 3.56e-03 | 0.00e+00 | 3.56e-03 | 7.66e-05 |
| Treasuries | 3 | 4.20e-04 | 0.00e+00 | -2.32e-02 | 7.96e-03 |
| US Equities | 19 | 1.57e-03 | 1.77e-03 | -5.52e-03 | -2.18e-03 |

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
