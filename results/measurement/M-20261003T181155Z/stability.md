# Stability of the loadings, M-20261003T181155Z

**A description made after the results were seen. It is not a test and it changes no verdict, whichever way it reads.**

Compared as stored: `mean_reverting_dlm_own_mean` stores its one-step FORECAST of the loading for week t+1, the others a filtered or fitted value at t. The exposure matrix would be handed what is stored, so that is what is compared.

Cells: 70424 instrument-weeks at which every estimator has a loading. A change counts when both dates are such cells. Ratios are to rolling OLS (1.00 is as stable as OLS); an absolute mean is the mean over instruments of the mean over weeks of the absolute change, in loading units.

## Summary: mean of each ratio across the six factors

| estimator | weekly | weekly 2008-09 | annual | annual 2008-09 | rank agreement |
|---|---|---|---|---|---|
| rolling_ols | 1.00 | 1.00 | 1.00 | 1.00 | 1.000 |
| huber_m | 1.03 | 1.01 | 0.95 | 0.91 | 0.981 |
| theil_goldberger_peer_prior | 0.85 | 0.85 | 0.84 | 0.83 | 0.966 |
| hmm2_regime_conditional | 1.27 | 2.01 | 0.65 | 1.03 | 0.829 |
| kalman_dlm_discount | 1.79 | 2.01 | 1.41 | 1.52 | 0.903 |
| mean_reverting_dlm_own_mean | 1.20 | 1.61 | 0.81 | 0.92 | 0.878 |

## Weekly change, ratio to rolling OLS

| estimator | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| rolling_ols | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| huber_m | 1.03 | 1.03 | 1.03 | 1.05 | 1.02 | 1.02 |
| theil_goldberger_peer_prior | 0.90 | 0.85 | 0.83 | 0.78 | 0.85 | 0.88 |
| hmm2_regime_conditional | 1.47 | 1.24 | 0.98 | 1.20 | 1.51 | 1.24 |
| kalman_dlm_discount | 1.72 | 1.81 | 1.81 | 1.70 | 1.86 | 1.84 |
| mean_reverting_dlm_own_mean | 1.16 | 1.25 | 1.16 | 1.05 | 1.26 | 1.30 |

## Weekly change in 2008-2009, ratio to rolling OLS

| estimator | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| rolling_ols | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| huber_m | 1.01 | 1.00 | 0.99 | 1.06 | 0.97 | 1.00 |
| theil_goldberger_peer_prior | 0.92 | 0.80 | 0.83 | 0.77 | 0.83 | 0.92 |
| hmm2_regime_conditional | 2.20 | 1.76 | 1.31 | 1.81 | 2.47 | 2.52 |
| kalman_dlm_discount | 2.01 | 1.97 | 1.93 | 1.64 | 2.14 | 2.36 |
| mean_reverting_dlm_own_mean | 1.71 | 1.68 | 1.46 | 1.61 | 1.51 | 1.70 |

## Annual change, ratio to rolling OLS

| estimator | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| rolling_ols | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| huber_m | 0.96 | 0.93 | 0.94 | 0.98 | 0.93 | 0.93 |
| theil_goldberger_peer_prior | 0.92 | 0.84 | 0.81 | 0.75 | 0.86 | 0.85 |
| hmm2_regime_conditional | 0.63 | 0.64 | 0.55 | 0.75 | 0.70 | 0.64 |
| kalman_dlm_discount | 1.25 | 1.44 | 1.61 | 1.34 | 1.35 | 1.48 |
| mean_reverting_dlm_own_mean | 0.71 | 0.87 | 0.83 | 0.74 | 0.79 | 0.89 |

## Annual change in 2008-2009, ratio to rolling OLS

| estimator | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| rolling_ols | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| huber_m | 0.92 | 0.91 | 0.90 | 1.01 | 0.84 | 0.90 |
| theil_goldberger_peer_prior | 0.94 | 0.82 | 0.78 | 0.74 | 0.82 | 0.87 |
| hmm2_regime_conditional | 0.89 | 0.89 | 0.77 | 1.07 | 1.19 | 1.35 |
| kalman_dlm_discount | 1.33 | 1.42 | 1.71 | 1.40 | 1.46 | 1.79 |
| mean_reverting_dlm_own_mean | 0.88 | 0.94 | 0.84 | 0.98 | 0.84 | 1.05 |

## Rank agreement with rolling OLS (median weekly cross-sectional Spearman)

| estimator | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| rolling_ols | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| huber_m | 0.99 | 0.99 | 0.97 | 0.97 | 0.99 | 0.98 |
| theil_goldberger_peer_prior | 0.99 | 0.97 | 0.95 | 0.94 | 0.97 | 0.97 |
| hmm2_regime_conditional | 0.92 | 0.85 | 0.76 | 0.73 | 0.91 | 0.81 |
| kalman_dlm_discount | 0.96 | 0.93 | 0.83 | 0.87 | 0.94 | 0.89 |
| mean_reverting_dlm_own_mean | 0.95 | 0.88 | 0.74 | 0.86 | 0.95 | 0.89 |

## Weekly change, absolute (loading units)

| estimator | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| rolling_ols | 0.0055 | 0.0844 | 0.1445 | 0.1953 | 0.0087 | 0.0044 |
| huber_m | 0.0056 | 0.0866 | 0.1484 | 0.2055 | 0.0089 | 0.0045 |
| theil_goldberger_peer_prior | 0.0050 | 0.0718 | 0.1202 | 0.1524 | 0.0074 | 0.0038 |
| hmm2_regime_conditional | 0.0080 | 0.1049 | 0.1412 | 0.2345 | 0.0131 | 0.0054 |
| kalman_dlm_discount | 0.0094 | 0.1527 | 0.2619 | 0.3312 | 0.0162 | 0.0080 |
| mean_reverting_dlm_own_mean | 0.0064 | 0.1059 | 0.1679 | 0.2048 | 0.0110 | 0.0057 |
