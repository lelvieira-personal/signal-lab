Built from `decisions/0049`. It chooses nothing about the matrix's columns (OWNER-QUEUE L27).

# Characteristics store `huber6-v3`

- Estimator `huber_m` (H-2026-0013): c = 1.345, MAD scale, 156 weeks, at least 104 valid weeks, sandwich covariance, all six factors in one regression, walk-forward. Factors: equity, real_yield, inflation, credit, dollar, commodities.
- Dates: 2002-12-27 to 2019-12-27; development window only.
- Instruments: 84 estimated, 8 not (tradable-only series (daily start after 2009) inherit loadings and are never estimated, SUBSTRATE section 5.2).
- Rows: loadings 435,636, fit 72,606, measured 21,722, instruments 92.
- Hashes: directory `84a5088d82b135c4`, params `b3d41267a752b9d7`, weekly returns `0377b3fc550ec8e5`, factors `3401475eb25cd3c0`. Threads (OMP/OPENBLAS/MKL) 1/1/1.

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
| European Equities | 12 | 2002-12-27 |
| Ex-USD Bonds | 6 | 2002-12-27 |
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

| class | full sample | last week | n at last week | lowest at last week | below 0.5 |
|---|---|---|---|---|---|
| APAC ex-Japan Equities | 0.744 | 0.514 | 1 | NDDUPXJ 0.514 | 0 |
| Cash | 0.013 | 0.012 | 1 | LD20TRUU 0.012 | 1 |
| Commodities | 1.000 | 0.999 | 1 | BCOMTR 0.999 | 0 |
| DM ex-US Equities | 0.902 | 0.778 | 9 | MXCA 0.701 | 0 |
| EM Corporate Bonds | 0.447 | 0.485 | 1 | I12877US 0.485 | 1 |
| EM Equities | 0.701 | 0.535 | 12 | MXIN 0.126 | 4 |
| EM Sovereign Bonds | 0.503 | 0.437 | 2 | I20344US 0.359 | 1 |
| European Equities | 0.735 | 0.620 | 12 | MXEU0UT 0.313 | 4 |
| Ex-USD Bonds | 0.844 | 0.830 | 6 | I12823GB 0.488 | 1 |
| Gold | 0.311 | 0.493 | 1 | BCOMGCTR 0.493 | 1 |
| HY Corporates | 0.624 | 0.586 | 5 | I00188US 0.439 | 1 |
| IG Corporates | 0.821 | 0.816 | 2 | LDC5TRUU 0.707 | 0 |
| Japanese Equities | 0.421 | 0.521 | 1 | NDDUJN 0.521 | 0 |
| Long Treasuries | 0.863 | 0.908 | 2 | LT11TRUU 0.907 | 0 |
| MBS | 0.591 | 0.691 | 1 | LUMSTRUU 0.691 | 0 |
| Real Assets | 0.811 | 0.633 | 4 | ENXG 0.346 | 1 |
| TIPS | 0.889 | 0.928 | 1 | LBUTTRUU 0.928 | 0 |
| Treasuries | 0.863 | 0.900 | 3 | LT01TRUU 0.673 | 0 |
| US Equities | 0.761 | 0.755 | 19 | MXUS0UT 0.172 | 4 |

Commodities' share is an identity, not a finding: the commodities factor is that index less cash, so the regression recovers it exactly.

## Standard error against loading

Median over instruments of `se / |loading|` at 2019-12-27, by factor and class. Large where a class has little exposure to a factor.

| class | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| APAC ex-Japan Equities | 0.15 | 91.58 | 2.91 | 1.61 | 0.38 | 0.60 |
| Cash | 0.86 | 0.35 | 0.91 | 5.00 | 0.80 | 1.59 |
| Commodities | 0.86 | 0.35 | 0.91 | 5.00 | 0.80 | 0.00 |
| DM ex-US Equities | 0.07 | 0.44 | 0.63 | 0.56 | 0.19 | 1.01 |
| EM Corporate Bonds | 0.28 | 0.10 | 0.20 | 0.11 | 0.70 | 1.29 |
| EM Equities | 0.11 | 0.59 | 1.85 | 1.25 | 0.40 | 0.96 |
| EM Sovereign Bonds | 0.19 | 0.21 | 0.59 | 4.40 | 0.29 | 168.29 |
| European Equities | 0.11 | 0.66 | 0.68 | 0.63 | 0.26 | 0.54 |
| Ex-USD Bonds | 0.49 | 0.14 | 0.32 | 0.53 | 0.05 | 0.73 |
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

## Converted to dollars (`decisions/0053`)

Series delivered in their quote currency, converted in the loader with Bloomberg generic spot on the same date. *before* is `huber6-v2`, *after* this store. Medians over weeks of the dollar loading and of the explained share. *FX dates dropped* are dates, from each series' true daily start to the holdout, with a local level and no rate: they have no dollar level and nothing is carried.

| instrument | currency | FX column | weeks | dollar loading before | dollar loading after | explained share before | explained share after | FX dates dropped |
|---|---|---|---|---|---|---|---|---|
| I02513EU | EUR | EURUSD | 888 | 0.10 | -1.08 | 0.47 | 0.86 | 0 |
| MXCA | CAD | USDCAD | 888 | 0.29 | -0.06 | 0.68 | 0.72 | 2086 |
| MXCN | HKD | USDHKD | 888 | -0.01 | -0.02 | 0.42 | 0.42 | 0 |
| MXEU0CD | EUR | EURUSD | 888 | 0.71 | -0.50 | 0.73 | 0.77 | 32 |
| MXEU0CS | EUR | EURUSD | 888 | 0.75 | -0.44 | 0.51 | 0.60 | 32 |
| MXEU0EN | EUR | EURUSD | 888 | 0.85 | -0.32 | 0.60 | 0.63 | 32 |
| MXEU0FN | EUR | EURUSD | 888 | 0.58 | -0.58 | 0.75 | 0.79 | 32 |
| MXEU0HC | EUR | EURUSD | 888 | 0.82 | -0.41 | 0.50 | 0.53 | 32 |
| MXEU0IN | EUR | EURUSD | 888 | 0.66 | -0.54 | 0.79 | 0.80 | 32 |
| MXEU0IT | EUR | EURUSD | 888 | 0.79 | -0.38 | 0.64 | 0.62 | 32 |
| MXEU0MT | EUR | EURUSD | 888 | 0.65 | -0.58 | 0.71 | 0.75 | 32 |
| MXEU0TC | EUR | EURUSD | 888 | 0.56 | -0.60 | 0.49 | 0.51 | 32 |
| MXEU0UT | EUR | EURUSD | 888 | 0.46 | -0.74 | 0.51 | 0.54 | 32 |
| MXEUG | EUR | EURUSD | 888 | 0.60 | -0.53 | 0.84 | 0.86 | 32 |
| MXIN | INR | USDINR | 888 | 0.26 | 0.13 | 0.34 | 0.35 | 60 |
| MXKR | KRW | USDKRW | 888 | 0.21 | -0.10 | 0.45 | 0.50 | 0 |
| TAMSCI | TWD | USDTWD | 886 | 0.21 | 0.03 | 0.38 | 0.39 | 1 |

## Estimated against measured, 23 of 23 estimated bond-class instruments have a measured duration

Medians and their ratio are over the weeks with both a loading and a measured `INDEX_OAD_TSY`; `-OAD` is minus its median over those weeks. A ratio of 1 means the loading equals minus the measured duration. *weekly* is the median of the weekly `loading / -OAD` with its 10th and 90th percentiles. A dash is an instrument with no measured duration. Not merged: the two stay separate in the store (`decisions/0015`).

| instrument | class | weeks | weeks measured | real yield | inflation | credit | -OAD | ratio real yield | ratio inflation | ratio credit | weekly real yield | weekly inflation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 636 | 636 | -3.060 | -2.169 | -5.920 | -4.80 | 0.64 | 0.45 | 1.23 | 0.59 [0.50, 0.69] | 0.44 [0.29, 0.63] |
| EMUSTRUU | EM Sovereign Bonds | 888 | 888 | -3.172 | -1.818 | -5.213 | -5.89 | 0.54 | 0.31 | 0.88 | 0.54 [0.39, 0.79] | 0.29 [0.15, 0.71] |
| I20344US | EM Sovereign Bonds | 492 | 492 | -3.721 | -1.004 | -1.926 | -5.26 | 0.71 | 0.19 | 0.37 | 0.66 [0.23, 0.82] | 0.19 [-0.06, 0.43] |
| I02513EU | Ex-USD Bonds | 888 | 888 | -2.619 | -2.686 | -0.422 | -6.61 | 0.40 | 0.41 | 0.06 | 0.40 [0.23, 0.49] | 0.42 [0.28, 0.67] |
| I02913JP | Ex-USD Bonds | 888 | 96 | -7.989 | -6.057 | 2.511 | -9.42 | 0.85 | 0.64 | -0.27 | 0.85 [0.75, 0.91] | 0.65 [0.53, 0.74] |
| I12823GB | Ex-USD Bonds | 627 | 545 | -2.084 | -2.435 | -0.435 | -4.44 | 0.47 | 0.55 | 0.10 | 0.45 [0.11, 0.80] | 0.56 [0.09, 1.29] |
| LET1TREU | Ex-USD Bonds | 888 | 888 | 0.276 | -0.211 | -0.056 | -1.84 | -0.15 | 0.11 | 0.03 | -0.15 [-0.44, 0.35] | 0.12 [-0.66, 0.78] |
| LG38TRUU | Ex-USD Bonds | 888 | 888 | -3.313 | -3.187 | -0.589 | -6.26 | 0.53 | 0.51 | 0.09 | 0.52 [0.45, 0.62] | 0.47 [0.30, 0.61] |
| LP05TREU | Ex-USD Bonds | 888 | 888 | -2.130 | -2.195 | -2.945 | -5.30 | 0.40 | 0.41 | 0.56 | 0.39 [0.30, 0.55] | 0.44 [0.25, 0.59] |
| I00183US | HY Corporates | 888 | 888 | -1.792 | -1.069 | -6.362 | -4.06 | 0.44 | 0.26 | 1.57 | 0.44 [0.35, 0.61] | 0.26 [0.01, 0.63] |
| I00184US | HY Corporates | 888 | 888 | -3.523 | -2.599 | -8.753 | -9.23 | 0.38 | 0.28 | 0.95 | 0.36 [0.30, 0.53] | 0.27 [0.07, 0.57] |
| I00185US | HY Corporates | 888 | 888 | -1.451 | -0.708 | -7.690 | -4.01 | 0.36 | 0.18 | 1.92 | 0.36 [0.26, 0.51] | 0.19 [-0.14, 0.48] |
| I00188US | HY Corporates | 888 | 888 | -1.449 | -0.688 | -10.964 | -3.58 | 0.40 | 0.19 | 3.06 | 0.39 [0.13, 0.59] | 0.18 [-0.30, 0.62] |
| LF98TRUU | HY Corporates | 888 | 888 | -1.674 | -0.952 | -8.084 | -4.24 | 0.40 | 0.22 | 1.91 | 0.40 [0.31, 0.52] | 0.24 [-0.04, 0.55] |
| LDC5TRUU | IG Corporates | 758 | 758 | -2.150 | -1.806 | -2.247 | -2.76 | 0.78 | 0.65 | 0.81 | 0.81 [0.64, 0.97] | 0.66 [0.49, 0.82] |
| LUACTRUU | IG Corporates | 888 | 888 | -5.613 | -5.531 | -5.660 | -6.61 | 0.85 | 0.84 | 0.86 | 0.84 [0.77, 0.96] | 0.85 [0.80, 0.91] |
| LT11TRUU | Long Treasuries | 888 | 888 | -11.913 | -14.471 | -0.605 | -17.19 | 0.69 | 0.84 | 0.04 | 0.84 [0.66, 0.90] | 0.90 [0.80, 1.06] |
| LUTLTRUU | Long Treasuries | 888 | 888 | -10.355 | -11.526 | -0.541 | -14.62 | 0.71 | 0.79 | 0.04 | 0.84 [0.68, 0.95] | 0.91 [0.81, 1.04] |
| LUMSTRUU | MBS | 888 | 888 | -2.937 | -2.384 | -0.276 | -3.56 | 0.82 | 0.67 | 0.08 | 0.81 [0.57, 1.30] | 0.71 [0.41, 1.19] |
| LBUTTRUU | TIPS | 888 | 888 | -7.052 | -0.316 | -0.117 | -5.77 | 1.22 | 0.05 | 0.02 | 1.24 [1.02, 1.56] | 0.05 [-0.14, 0.15] |
| LT01TRUU | Treasuries | 888 | 888 | -1.062 | -0.764 | 0.308 | -1.85 | 0.57 | 0.41 | -0.17 | 0.56 [0.30, 0.86] | 0.41 [0.23, 0.74] |
| LT09TRUU | Treasuries | 888 | 888 | -7.210 | -6.943 | 0.186 | -7.55 | 0.95 | 0.92 | -0.02 | 0.97 [0.93, 1.03] | 0.93 [0.88, 0.98] |
| LT13TRUU | Treasuries | 888 | 677 | -3.973 | -3.446 | 0.482 | -4.51 | 0.88 | 0.76 | -0.11 | 0.89 [0.79, 0.98] | 0.78 [0.64, 0.85] |

## By period, median weekly ratio of the loading to -OAD

| instrument | class | real yield 2002-08 | real yield 2009-15 | real yield 2016-19 | inflation 2002-08 | inflation 2009-15 | inflation 2016-19 |
|---|---|---|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 0.61 | 0.59 | 0.56 | 0.41 | 0.42 | 0.49 |
| EMUSTRUU | EM Sovereign Bonds | 0.68 | 0.48 | 0.56 | 0.33 | 0.23 | 0.55 |
| I20344US | EM Sovereign Bonds | - | 0.52 | 0.68 | - | 0.15 | 0.26 |
| I02513EU | Ex-USD Bonds | 0.46 | 0.29 | 0.42 | 0.38 | 0.35 | 0.65 |
| I02913JP | Ex-USD Bonds | - | - | 0.85 | - | - | 0.65 |
| I12823GB | Ex-USD Bonds | - | 0.47 | 0.41 | - | 0.31 | 1.11 |
| LET1TREU | Ex-USD Bonds | 0.31 | -0.22 | -0.31 | 0.29 | 0.33 | -0.03 |
| LG38TRUU | Ex-USD Bonds | 0.51 | 0.50 | 0.60 | 0.32 | 0.50 | 0.60 |
| LP05TREU | Ex-USD Bonds | 0.51 | 0.35 | 0.37 | 0.44 | 0.40 | 0.56 |
| I00183US | HY Corporates | 0.45 | 0.41 | 0.57 | 0.47 | 0.19 | 0.28 |
| I00184US | HY Corporates | 0.41 | 0.37 | 0.34 | 0.50 | 0.20 | 0.28 |
| I00185US | HY Corporates | 0.33 | 0.36 | 0.49 | 0.37 | 0.13 | 0.18 |
| I00188US | HY Corporates | 0.28 | 0.42 | 0.57 | 0.35 | 0.14 | 0.15 |
| LF98TRUU | HY Corporates | 0.37 | 0.39 | 0.50 | 0.41 | 0.15 | 0.26 |
| LDC5TRUU | IG Corporates | 0.95 | 0.78 | 0.76 | 0.80 | 0.66 | 0.61 |
| LUACTRUU | IG Corporates | 0.95 | 0.80 | 0.84 | 0.87 | 0.81 | 0.87 |
| LT11TRUU | Long Treasuries | 0.88 | 0.71 | 0.86 | 0.87 | 0.89 | 1.04 |
| LUTLTRUU | Long Treasuries | 0.94 | 0.76 | 0.85 | 0.91 | 0.87 | 1.02 |
| LUMSTRUU | MBS | 0.91 | 0.75 | 0.65 | 0.88 | 0.59 | 0.56 |
| LBUTTRUU | TIPS | 1.20 | 1.24 | 1.36 | 0.07 | 0.03 | 0.02 |
| LT01TRUU | Treasuries | 0.80 | 0.42 | 0.51 | 0.69 | 0.37 | 0.35 |
| LT09TRUU | Treasuries | 1.01 | 0.94 | 0.99 | 0.93 | 0.92 | 0.93 |
| LT13TRUU | Treasuries | 0.99 | 0.86 | 0.90 | 0.84 | 0.78 | 0.77 |

## Measured coverage

First week with a measured duration; weeks with a loading and no measured duration; empty weeks inside the measured span (a week between the first and last measured week with no observation).

| instrument | class | first measured week | loading, no duration | empty inside |
|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 2007-10-26 | 0 | 0 |
| EMUSTRUU | EM Sovereign Bonds | 2002-12-27 | 0 | 0 |
| I20344US | EM Sovereign Bonds | 2010-07-30 | 0 | 0 |
| I02513EU | Ex-USD Bonds | 2002-12-27 | 0 | 0 |
| I02913JP | Ex-USD Bonds | 2018-03-02 | 792 | 0 |
| I12823GB | Ex-USD Bonds | 2009-07-24 | 82 | 0 |
| LET1TREU | Ex-USD Bonds | 2002-12-27 | 0 | 0 |
| LG38TRUU | Ex-USD Bonds | 2002-12-27 | 0 | 0 |
| LP05TREU | Ex-USD Bonds | 2002-12-27 | 0 | 0 |
| I00183US | HY Corporates | 2002-12-27 | 0 | 0 |
| I00184US | HY Corporates | 2002-12-27 | 0 | 0 |
| I00185US | HY Corporates | 2002-12-27 | 0 | 0 |
| I00188US | HY Corporates | 2002-12-27 | 0 | 0 |
| LF98TRUU | HY Corporates | 2002-12-27 | 0 | 0 |
| LDC5TRUU | IG Corporates | 2005-06-24 | 0 | 0 |
| LUACTRUU | IG Corporates | 2002-12-27 | 0 | 0 |
| LT11TRUU | Long Treasuries | 2002-12-27 | 0 | 0 |
| LUTLTRUU | Long Treasuries | 2002-12-27 | 0 | 0 |
| LUMSTRUU | MBS | 2002-12-27 | 0 | 0 |
| LBUTTRUU | TIPS | 2002-12-27 | 0 | 0 |
| LT01TRUU | Treasuries | 2002-12-27 | 0 | 0 |
| LT09TRUU | Treasuries | 2002-12-27 | 0 | 0 |
| LT13TRUU | Treasuries | 2007-01-12 | 211 | 0 |

## Duration times spread

For each instrument with an `INDEX_OAS_TSY`: the median over weeks of the credit loading over `-OAD x OAS / OAS of LUACTRUU`. 1 means the credit loading is duration times spread, scaled to the reference. **Left out:** the Treasuries, Long Treasuries, TIPS classes and the government ex-USD indices `I02513EU`, `I02913JP`, `I12823GB`, `LET1TREU`. Their spread over Treasuries is near zero, so the ratio divides by almost nothing and means nothing.

| instrument | class | weeks | credit loading over duration x spread |
|---|---|---|---|
| I12877US | EM Corporate Bonds | 636 | 0.51 |
| EMUSTRUU | EM Sovereign Bonds | 888 | 0.38 |
| I20344US | EM Sovereign Bonds | 492 | 0.85 |
| LP05TREU | Ex-USD Bonds | 888 | 0.57 |
| I00183US | HY Corporates | 888 | 0.68 |
| I00184US | HY Corporates | 888 | 0.37 |
| I00185US | HY Corporates | 888 | 0.59 |
| I00188US | HY Corporates | 888 | 0.58 |
| LF98TRUU | HY Corporates | 888 | 0.58 |
| LDC5TRUU | IG Corporates | 758 | 1.22 |
| LUACTRUU | IG Corporates | 888 | 0.89 |
| LUMSTRUU | MBS | 886 | 0.30 |

## Checks the build made on itself

- Huber loadings against the run of record: `M-20261003T181155Z` stores 339,744 Huber loadings for the instruments it shares with this build and that were not converted to dollars; the largest absolute difference is 0.0e+00 (tolerance zero)
- no lookahead: `assert_no_lookahead` passed on every instrument's path
- factors: the factors hash equals the run of record's: True
- fit on the shared cells (reported, not compared): 66 instruments, 53,638 cells scored by the test's rule: pooled r2_oos 0.7454, mean Huber loss 0.2126; `fit.json` pools 86 instruments (70,326 cells): 0.7030 and 0.2303
- against huber6-v2: 345,072 loadings of the instruments neither left nor converted to dollars; the largest absolute difference is 0.0e+00 in the loading and 0.0e+00 in its standard error (tolerance zero); 0 unmatched rows
- the converted series: 90,564 loadings of the 17 converted series on both sides; the largest absolute difference is 7.711
