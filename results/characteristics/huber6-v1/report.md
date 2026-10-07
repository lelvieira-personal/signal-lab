Built from `decisions/0049`. It chooses nothing about the matrix's columns (OWNER-QUEUE L27).

# Characteristics store `huber6-v1`

- Estimator `huber_m` (H-2026-0013): c = 1.345, MAD scale, 156 weeks, at least 104 valid weeks, sandwich covariance, all six factors in one regression, walk-forward. Factors: equity, real_yield, inflation, credit, dollar, commodities.
- Dates: 2002-12-27 to 2019-12-27; development window only.
- Instruments: 87 estimated, 8 not (tradable-only series (daily start after 2009) inherit loadings and are never estimated, SUBSTRATE section 5.2).
- Rows: loadings 451,572, fit 75,262, measured 16,256, instruments 95.
- Hashes: directory `95db155edf972bf9`, params `b3d41267a752b9d7`, weekly returns `5987bafe9f1944c5`, factors `3401475eb25cd3c0`. Threads (OMP/OPENBLAS/MKL) 1/1/1.

## Instruments estimated, by reporting class

| class | instruments | first week with loadings |
|---|---|---|
| APAC ex-Japan Equities | 1 | 2002-12-27 |
| Cash | 1 | 2002-12-27 |
| Commodities | 1 | 2002-12-27 |
| DM ex-US Equities | 9 | 2002-12-27 |
| EM Corporate Bonds | 1 | 2007-10-26 |
| EM Equities | 12 | 2002-12-27 |
| EM Sovereign Bonds | 2 | 2002-12-27 |
| European Equities | 13 | 2002-12-27 |
| Ex-USD Bonds | 8 | 2002-12-27 |
| Gold | 1 | 2002-12-27 |
| HY Corporates | 5 | 2002-12-27 |
| IG Corporates | 2 | 2002-12-27 |
| Japanese Equities | 1 | 2002-12-27 |
| Long Treasuries | 2 | 2002-12-27 |
| MBS | 1 | 2002-12-27 |
| Real Assets | 4 | 2002-12-27 |
| TIPS | 1 | 2002-12-27 |
| Treasuries | 3 | 2002-12-27 |
| US Equities | 19 | 2002-12-27 |

## Explained share, by reporting class

Out of sample: `1 - sum (r - p)^2 / sum r^2`, `p` this week's factors times last week's loadings, no intercept. *Full sample* is over every week an instrument has; *last week* is the 156 weeks ending 2019-12-27 (instruments with a value there). Medians over instruments. It may be negative.

| class | full sample | last week | n at last week |
|---|---|---|---|
| APAC ex-Japan Equities | 0.744 | 0.514 | 1 |
| Cash | 0.013 | 0.012 | 1 |
| Commodities | 1.000 | 0.999 | 1 |
| DM ex-US Equities | 0.902 | 0.778 | 9 |
| EM Corporate Bonds | 0.447 | 0.485 | 1 |
| EM Equities | 0.701 | 0.537 | 12 |
| EM Sovereign Bonds | 0.503 | 0.437 | 2 |
| European Equities | 0.716 | 0.528 | 13 |
| Ex-USD Bonds | 0.432 | 0.514 | 8 |
| Gold | 0.311 | 0.493 | 1 |
| HY Corporates | 0.624 | 0.586 | 5 |
| IG Corporates | 0.821 | 0.816 | 2 |
| Japanese Equities | 0.421 | 0.521 | 1 |
| Long Treasuries | 0.863 | 0.908 | 2 |
| MBS | 0.591 | 0.691 | 1 |
| Real Assets | 0.811 | 0.633 | 4 |
| TIPS | 0.889 | 0.928 | 1 |
| Treasuries | 0.863 | 0.900 | 3 |
| US Equities | 0.761 | 0.755 | 19 |

## Standard error against loading

Median over instruments of `se / |loading|` at 2019-12-27, by factor and class. Large where a class has little exposure to a factor.

| class | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| APAC ex-Japan Equities | 0.15 | 91.58 | 2.91 | 1.61 | 0.38 | 0.60 |
| Cash | 0.86 | 0.35 | 0.91 | 5.00 | 0.80 | 1.59 |
| Commodities | 0.86 | 0.35 | 0.91 | 5.00 | 0.80 | 0.00 |
| DM ex-US Equities | 0.07 | 0.44 | 0.63 | 0.56 | 0.18 | 1.01 |
| EM Corporate Bonds | 0.28 | 0.10 | 0.20 | 0.11 | 0.70 | 1.29 |
| EM Equities | 0.11 | 0.60 | 1.85 | 1.25 | 0.42 | 0.96 |
| EM Sovereign Bonds | 0.19 | 0.21 | 0.59 | 4.40 | 0.29 | 168.29 |
| European Equities | 0.11 | 1.51 | 0.90 | 0.63 | 0.26 | 0.79 |
| Ex-USD Bonds | 0.56 | 0.16 | 0.36 | 0.48 | 0.12 | 1.25 |
| Gold | 1.54 | 0.17 | 0.43 | 6.04 | 0.14 | 0.34 |
| HY Corporates | 0.13 | 0.20 | 0.58 | 0.20 | 5.50 | 1.67 |
| IG Corporates | 2.18 | 0.04 | 0.06 | 0.08 | 20.45 | 1.82 |
| Japanese Equities | 0.09 | 8.60 | 1.75 | 6.69 | 0.81 | 1.74 |
| Long Treasuries | 1.15 | 0.03 | 0.05 | 1.65 | 2.02 | 77.69 |
| MBS | 25.80 | 0.08 | 0.14 | 12.31 | 0.44 | 0.51 |
| Real Assets | 0.10 | 0.64 | 0.30 | 1.99 | 1.45 | 0.42 |
| TIPS | 0.98 | 0.03 | 1.58 | 1.56 | 6.45 | 0.55 |
| Treasuries | 0.30 | 0.04 | 0.06 | 0.54 | 21.06 | 1.00 |
| US Equities | 0.06 | 0.47 | 1.56 | 1.05 | 0.38 | 0.87 |

## Estimated against measured, every bond index

The estimated loadings are medians over the weeks an instrument has them; `-OAD` is minus the median measured `INDEX_OAD_TSY` over the same weeks. A ratio of 1 means the regression's loading equals minus the measured duration. Not merged: the two stay separate in the store (`decisions/0015`).

| instrument | class | weeks | real yield | inflation | credit | -OAD | ratio real yield | ratio inflation | ratio credit |
|---|---|---|---|---|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 636 | -3.060 | -2.169 | -5.920 | -4.80 | 0.64 | 0.45 | 1.23 |
| EMUSTRUU | EM Sovereign Bonds | 888 | -3.172 | -1.818 | -5.213 | -5.89 | 0.54 | 0.31 | 0.88 |
| I20344US | EM Sovereign Bonds | 492 | -3.721 | -1.004 | -1.926 | -5.26 | 0.71 | 0.19 | 0.37 |
| I00183US | HY Corporates | 888 | -1.792 | -1.069 | -6.362 | -4.06 | 0.44 | 0.26 | 1.57 |
| I00184US | HY Corporates | 888 | -3.523 | -2.599 | -8.753 | -9.23 | 0.38 | 0.28 | 0.95 |
| I00185US | HY Corporates | 888 | -1.451 | -0.708 | -7.690 | -4.01 | 0.36 | 0.18 | 1.92 |
| I00188US | HY Corporates | 888 | -1.449 | -0.688 | -10.964 | -3.58 | 0.40 | 0.19 | 3.06 |
| LF98TRUU | HY Corporates | 888 | -1.674 | -0.952 | -8.084 | -4.24 | 0.40 | 0.22 | 1.91 |
| LDC5TRUU | IG Corporates | 758 | -2.150 | -1.806 | -2.247 | -2.76 | 0.78 | 0.65 | 0.81 |
| LUACTRUU | IG Corporates | 888 | -5.613 | -5.531 | -5.660 | -6.61 | 0.85 | 0.84 | 0.86 |
| LT11TRUU | Long Treasuries | 888 | -11.913 | -14.471 | -0.605 | -17.19 | 0.69 | 0.84 | 0.04 |
| LUTLTRUU | Long Treasuries | 888 | -10.355 | -11.526 | -0.541 | -14.62 | 0.71 | 0.79 | 0.04 |
| LUMSTRUU | MBS | 888 | -2.937 | -2.384 | -0.276 | -3.56 | 0.82 | 0.67 | 0.08 |
| LBUTTRUU | TIPS | 888 | -7.052 | -0.316 | -0.117 | -5.77 | 1.22 | 0.05 | 0.02 |
| LT01TRUU | Treasuries | 888 | -1.062 | -0.764 | 0.308 | -1.85 | 0.57 | 0.41 | -0.17 |
| LT09TRUU | Treasuries | 888 | -7.210 | -6.943 | 0.186 | -7.55 | 0.95 | 0.92 | -0.02 |
| LT13TRUU | Treasuries | 888 | -4.025 | -3.496 | 0.564 | -4.51 | 0.89 | 0.77 | -0.13 |

## Checks the build made on itself

- reproduces the estimator test: 70326 cells; pooled r2_oos differs from `M-20261003T181155Z/fit.json` by 0.00e+00 and mean Huber loss by 0.00e+00 (tolerance 1e-06)
- no lookahead: `assert_no_lookahead` passed on every instrument's path
- inputs: weekly returns (Cash out) and factors hash-equal to the run of record: True
