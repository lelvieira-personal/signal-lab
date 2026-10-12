Built from `decisions/0049`. It chooses nothing about the matrix's columns (OWNER-QUEUE L27).

# Characteristics store `huber6-v4`

- Estimator `huber_m` (H-2026-0013): c = 1.345, MAD scale, 156 weeks, at least 104 valid weeks, sandwich covariance, all six factors in one regression, walk-forward. Factors: equity, real_yield, inflation, credit, dollar, commodities.
- Dates: 2001-01-12 to 2019-12-27; development window only.
- Instruments: 84 estimated, 8 not (tradable-only series (daily start after 2009) inherit loadings and are never estimated, SUBSTRATE section 5.2).
- Rows: loadings 474,750, fit 79,125, measured 23,117, instruments 92.
- Hashes: directory `b6181bcde28b7e95`, params `413d84f6b631359b`, weekly returns `2fef64ef2014066d`, factors `605fe4e763c01292`. Threads (OMP/OPENBLAS/MKL) 1/1/1.

## Instruments estimated, by reporting class

| class | instruments | first week with loadings |
|---|---|---|
| APAC ex-Japan Equities | 1 | 2001-01-19 |
| Cash | 1 | 2001-01-12 |
| Commodities | 1 | 2001-01-12 |
| DM ex-US Equities | 9 | 2001-01-12 |
| EM Corporate Bonds | 1 | 2007-10-26 |
| EM Equities | 12 | 2001-01-12 |
| EM Sovereign Bonds | 2 | 2001-01-12 |
| European Equities | 12 | 2001-01-12 |
| Ex-USD Bonds | 6 | 2001-01-19 |
| Gold | 1 | 2001-01-12 |
| HY Corporates | 5 | 2001-01-12 |
| IG Corporates | 2 | 2001-01-12 |
| Japanese Equities | 1 | 2001-01-19 |
| Long Treasuries | 2 | 2001-01-12 |
| MBS | 1 | 2001-01-12 |
| Real Assets | 4 | 2001-01-19 |
| TIPS | 1 | 2001-01-12 |
| Treasuries | 3 | 2001-01-12 |
| US Equities | 19 | 2001-01-12 |

## Explained share, by reporting class

Out of sample: `1 - sum (r - p)^2 / sum r^2`, `p` this week's factors times last week's loadings, no intercept. *Full sample* is over every week an instrument has; *last week* is the 156 weeks ending 2019-12-27 (instruments with a value there). Medians over instruments. It may be negative.

| class | full sample | last week | n at last week | lowest at last week | below 0.5 |
|---|---|---|---|---|---|
| APAC ex-Japan Equities | 0.727 | 0.516 | 1 | NDDUPXJ 0.516 | 0 |
| Cash | 0.035 | 0.016 | 1 | LD20TRUU 0.016 | 1 |
| Commodities | 1.000 | 0.999 | 1 | BCOMTR 0.999 | 0 |
| DM ex-US Equities | 0.894 | 0.772 | 9 | MXCA 0.700 | 0 |
| EM Corporate Bonds | 0.393 | 0.375 | 1 | I12877US 0.375 | 1 |
| EM Equities | 0.677 | 0.535 | 12 | MXIN 0.130 | 4 |
| EM Sovereign Bonds | 0.444 | 0.415 | 2 | I20344US 0.365 | 2 |
| European Equities | 0.716 | 0.617 | 12 | MXEU0UT 0.305 | 4 |
| Ex-USD Bonds | 0.848 | 0.829 | 6 | I12823GB 0.458 | 1 |
| Gold | 0.292 | 0.496 | 1 | BCOMGCTR 0.496 | 1 |
| HY Corporates | 0.433 | 0.531 | 5 | I00188US 0.454 | 1 |
| IG Corporates | 0.652 | 0.764 | 2 | LDC5TRUU 0.642 | 0 |
| Japanese Equities | 0.395 | 0.536 | 1 | NDDUJN 0.536 | 0 |
| Long Treasuries | 0.900 | 0.930 | 2 | LT11TRUU 0.929 | 0 |
| MBS | 0.593 | 0.696 | 1 | LUMSTRUU 0.696 | 0 |
| Real Assets | 0.794 | 0.631 | 4 | ENXG 0.343 | 1 |
| TIPS | 0.887 | 0.929 | 1 | LBUTTRUU 0.929 | 0 |
| Treasuries | 0.875 | 0.908 | 3 | LT01TRUU 0.687 | 0 |
| US Equities | 0.720 | 0.757 | 19 | MXUS0UT 0.175 | 4 |

Commodities' share is an identity, not a finding: the commodities factor is that index less cash, so the regression recovers it exactly.

## Standard error against loading

Median over instruments of `se / |loading|` at 2019-12-27, by factor and class. Large where a class has little exposure to a factor.

| class | equity | real_yield | inflation | credit | dollar | commodities |
|---|---|---|---|---|---|---|
| APAC ex-Japan Equities | 0.14 | 9.76 | 2.30 | 3.72 | 0.39 | 0.60 |
| Cash | 1.63 | 0.42 | 1.16 | 0.68 | 0.77 | 1.85 |
| Commodities | 1.63 | 0.42 | 1.16 | 0.68 | 0.77 | 0.00 |
| DM ex-US Equities | 0.08 | 0.45 | 0.56 | 0.74 | 0.19 | 1.05 |
| EM Corporate Bonds | 0.22 | 0.13 | 0.28 | 0.19 | 0.92 | 2.57 |
| EM Equities | 0.10 | 0.60 | 1.87 | 0.89 | 0.39 | 0.97 |
| EM Sovereign Bonds | 0.17 | 0.20 | 0.57 | 2.45 | 0.33 | 31.26 |
| European Equities | 0.10 | 0.63 | 0.67 | 0.95 | 0.27 | 0.53 |
| Ex-USD Bonds | 0.40 | 0.15 | 0.36 | 0.74 | 0.05 | 0.75 |
| Gold | 1.82 | 0.18 | 0.46 | 1.33 | 0.14 | 0.33 |
| HY Corporates | 0.12 | 0.28 | 1.36 | 0.26 | 2.50 | 1.61 |
| IG Corporates | 1.65 | 0.05 | 0.09 | 0.40 | 152.84 | 6.12 |
| Japanese Equities | 0.08 | 15.05 | 1.53 | 1.45 | 0.81 | 1.71 |
| Long Treasuries | 0.78 | 0.03 | 0.05 | 0.17 | 1.36 | 8.23 |
| MBS | 22.12 | 0.08 | 0.15 | 7.41 | 0.45 | 0.51 |
| Real Assets | 0.10 | 0.85 | 0.30 | 3.22 | 1.49 | 0.40 |
| TIPS | 0.47 | 0.03 | 1.06 | 0.76 | 10.32 | 0.54 |
| Treasuries | 0.41 | 0.04 | 0.06 | 0.35 | 4.78 | 1.20 |
| US Equities | 0.06 | 0.51 | 1.37 | 0.92 | 0.38 | 0.84 |

## Estimated against measured, 23 of 23 estimated bond-class instruments have a measured duration

Medians and their ratio are over the weeks with both a loading and a measured `INDEX_OAD_TSY`; `-OAD` is minus its median over those weeks. A ratio of 1 means the loading equals minus the measured duration. *weekly* is the median of the weekly `loading / -OAD` with its 10th and 90th percentiles. A dash is an instrument with no measured duration. Not merged: the two stay separate in the store (`decisions/0015`).

| instrument | class | weeks | weeks measured | real yield | inflation | credit | -OAD | ratio real yield | ratio inflation | ratio credit | weekly real yield | weekly inflation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 636 | 636 | -3.457 | -1.920 | -4.470 | -4.80 | 0.72 | 0.40 | 0.93 | 0.68 [0.50, 0.82] | 0.37 [0.08, 0.55] |
| EMUSTRUU | EM Sovereign Bonds | 990 | 990 | -3.770 | -1.899 | -2.934 | -5.84 | 0.65 | 0.33 | 0.50 | 0.64 [0.47, 0.92] | 0.31 [0.12, 0.69] |
| I20344US | EM Sovereign Bonds | 492 | 492 | -3.761 | -0.860 | -0.399 | -5.26 | 0.71 | 0.16 | 0.08 | 0.66 [0.22, 0.86] | 0.17 [-0.07, 0.36] |
| I02513EU | Ex-USD Bonds | 989 | 914 | -2.685 | -2.858 | -0.689 | -6.48 | 0.41 | 0.44 | 0.11 | 0.41 [0.25, 0.52] | 0.45 [0.28, 0.66] |
| I02913JP | Ex-USD Bonds | 888 | 96 | -7.600 | -5.780 | 2.634 | -9.42 | 0.81 | 0.61 | -0.28 | 0.81 [0.72, 0.89] | 0.61 [0.51, 0.70] |
| I12823GB | Ex-USD Bonds | 627 | 545 | -2.097 | -2.437 | -0.265 | -4.44 | 0.47 | 0.55 | 0.06 | 0.45 [-0.03, 0.81] | 0.56 [0.12, 1.33] |
| LET1TREU | Ex-USD Bonds | 989 | 923 | 0.386 | -0.242 | -0.258 | -1.83 | -0.21 | 0.13 | 0.14 | -0.21 [-0.44, 0.30] | 0.13 [-0.56, 0.82] |
| LG38TRUU | Ex-USD Bonds | 888 | 888 | -3.461 | -3.186 | -0.533 | -6.26 | 0.55 | 0.51 | 0.09 | 0.54 [0.46, 0.64] | 0.48 [0.31, 0.59] |
| LP05TREU | Ex-USD Bonds | 989 | 989 | -2.335 | -2.524 | -2.307 | -5.24 | 0.45 | 0.48 | 0.44 | 0.44 [0.34, 0.59] | 0.47 [0.31, 0.63] |
| I00183US | HY Corporates | 990 | 990 | -2.095 | -0.989 | -2.646 | -4.09 | 0.51 | 0.24 | 0.65 | 0.52 [0.28, 0.69] | 0.24 [-0.13, 0.70] |
| I00184US | HY Corporates | 990 | 990 | -4.084 | -2.031 | -6.109 | -9.12 | 0.45 | 0.22 | 0.67 | 0.43 [0.32, 0.65] | 0.21 [0.07, 0.71] |
| I00185US | HY Corporates | 990 | 990 | -1.794 | -0.675 | -3.657 | -4.07 | 0.44 | 0.17 | 0.90 | 0.47 [0.19, 0.68] | 0.15 [-0.29, 0.62] |
| I00188US | HY Corporates | 990 | 990 | -1.896 | 0.201 | -6.765 | -3.66 | 0.52 | -0.05 | 1.85 | 0.54 [0.02, 0.89] | -0.05 [-0.84, 0.87] |
| LF98TRUU | HY Corporates | 990 | 990 | -2.061 | -0.851 | -4.118 | -4.27 | 0.48 | 0.20 | 0.96 | 0.50 [0.24, 0.71] | 0.21 [-0.25, 0.71] |
| LDC5TRUU | IG Corporates | 758 | 758 | -2.189 | -1.500 | -0.423 | -2.76 | 0.79 | 0.54 | 0.15 | 0.79 [0.64, 1.04] | 0.54 [0.38, 0.77] |
| LUACTRUU | IG Corporates | 990 | 990 | -6.039 | -5.434 | -3.942 | -6.45 | 0.94 | 0.84 | 0.61 | 0.93 [0.85, 1.07] | 0.84 [0.73, 0.97] |
| LT11TRUU | Long Treasuries | 990 | 990 | -13.190 | -15.722 | -6.106 | -16.31 | 0.81 | 0.96 | 0.37 | 0.91 [0.74, 1.00] | 0.95 [0.89, 1.10] |
| LUTLTRUU | Long Treasuries | 990 | 990 | -11.241 | -12.136 | -4.175 | -13.60 | 0.83 | 0.89 | 0.31 | 0.91 [0.75, 1.04] | 0.96 [0.88, 1.08] |
| LUMSTRUU | MBS | 990 | 990 | -2.998 | -2.460 | 0.016 | -3.39 | 0.88 | 0.73 | -0.00 | 0.84 [0.56, 1.50] | 0.75 [0.41, 1.31] |
| LBUTTRUU | TIPS | 990 | 990 | -7.122 | -0.341 | -0.628 | -5.62 | 1.27 | 0.06 | 0.11 | 1.29 [1.05, 2.01] | 0.07 [-0.12, 0.16] |
| LT01TRUU | Treasuries | 990 | 990 | -1.047 | -0.801 | 0.460 | -1.84 | 0.57 | 0.44 | -0.25 | 0.55 [0.29, 1.00] | 0.42 [0.23, 0.67] |
| LT09TRUU | Treasuries | 990 | 990 | -6.995 | -6.875 | 0.210 | -7.51 | 0.93 | 0.92 | -0.03 | 0.98 [0.93, 1.04] | 0.93 [0.88, 0.97] |
| LT13TRUU | Treasuries | 990 | 677 | -3.839 | -3.397 | 0.872 | -4.51 | 0.85 | 0.75 | -0.19 | 0.86 [0.77, 0.94] | 0.76 [0.61, 0.82] |

## By period, median weekly ratio of the loading to -OAD

| instrument | class | real yield 2002-08 | real yield 2009-15 | real yield 2016-19 | inflation 2002-08 | inflation 2009-15 | inflation 2016-19 |
|---|---|---|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 0.62 | 0.75 | 0.56 | 0.46 | 0.38 | 0.27 |
| EMUSTRUU | EM Sovereign Bonds | 0.78 | 0.53 | 0.55 | 0.40 | 0.19 | 0.39 |
| I20344US | EM Sovereign Bonds | - | 0.63 | 0.66 | - | 0.15 | 0.19 |
| I02513EU | Ex-USD Bonds | 0.48 | 0.30 | 0.45 | 0.40 | 0.37 | 0.64 |
| I02913JP | Ex-USD Bonds | - | - | 0.81 | - | - | 0.61 |
| I12823GB | Ex-USD Bonds | - | 0.47 | 0.39 | - | 0.43 | 1.07 |
| LET1TREU | Ex-USD Bonds | 0.23 | -0.31 | -0.34 | 0.29 | 0.24 | 0.01 |
| LG38TRUU | Ex-USD Bonds | 0.54 | 0.52 | 0.60 | 0.33 | 0.51 | 0.58 |
| LP05TREU | Ex-USD Bonds | 0.55 | 0.40 | 0.36 | 0.51 | 0.40 | 0.51 |
| I00183US | HY Corporates | 0.52 | 0.55 | 0.51 | 0.47 | 0.16 | -0.10 |
| I00184US | HY Corporates | 0.46 | 0.50 | 0.38 | 0.59 | 0.17 | 0.09 |
| I00185US | HY Corporates | 0.40 | 0.53 | 0.45 | 0.37 | 0.06 | -0.23 |
| I00188US | HY Corporates | 0.39 | 0.60 | 0.57 | 0.39 | 0.08 | -0.72 |
| LF98TRUU | HY Corporates | 0.46 | 0.59 | 0.48 | 0.39 | 0.10 | -0.19 |
| LDC5TRUU | IG Corporates | 0.91 | 0.83 | 0.72 | 0.76 | 0.55 | 0.49 |
| LUACTRUU | IG Corporates | 1.02 | 0.88 | 0.88 | 0.93 | 0.82 | 0.75 |
| LT11TRUU | Long Treasuries | 0.98 | 0.77 | 0.93 | 0.93 | 0.95 | 1.10 |
| LUTLTRUU | Long Treasuries | 1.01 | 0.81 | 0.92 | 0.97 | 0.91 | 1.07 |
| LUMSTRUU | MBS | 0.95 | 0.74 | 0.63 | 0.92 | 0.57 | 0.54 |
| LBUTTRUU | TIPS | 1.24 | 1.27 | 1.40 | 0.08 | 0.05 | 0.04 |
| LT01TRUU | Treasuries | 0.74 | 0.39 | 0.47 | 0.64 | 0.36 | 0.35 |
| LT09TRUU | Treasuries | 1.00 | 0.94 | 0.99 | 0.93 | 0.92 | 0.95 |
| LT13TRUU | Treasuries | 0.95 | 0.83 | 0.87 | 0.83 | 0.75 | 0.76 |

## Measured coverage

First week with a measured duration; weeks with a loading and no measured duration; empty weeks inside the measured span (a week between the first and last measured week with no observation).

| instrument | class | first measured week | loading, no duration | empty inside |
|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 2007-10-26 | 0 | 0 |
| EMUSTRUU | EM Sovereign Bonds | 2001-01-12 | 0 | 0 |
| I20344US | EM Sovereign Bonds | 2010-07-30 | 0 | 0 |
| I02513EU | Ex-USD Bonds | 2002-06-28 | 75 | 0 |
| I02913JP | Ex-USD Bonds | 2018-03-02 | 792 | 0 |
| I12823GB | Ex-USD Bonds | 2009-07-24 | 82 | 0 |
| LET1TREU | Ex-USD Bonds | 2002-04-26 | 66 | 0 |
| LG38TRUU | Ex-USD Bonds | 2002-12-27 | 0 | 0 |
| LP05TREU | Ex-USD Bonds | 2001-01-19 | 0 | 0 |
| I00183US | HY Corporates | 2001-01-12 | 0 | 0 |
| I00184US | HY Corporates | 2001-01-12 | 0 | 0 |
| I00185US | HY Corporates | 2001-01-12 | 0 | 0 |
| I00188US | HY Corporates | 2001-01-12 | 0 | 0 |
| LF98TRUU | HY Corporates | 2001-01-12 | 0 | 0 |
| LDC5TRUU | IG Corporates | 2005-06-24 | 0 | 0 |
| LUACTRUU | IG Corporates | 2001-01-12 | 0 | 0 |
| LT11TRUU | Long Treasuries | 2001-01-12 | 0 | 0 |
| LUTLTRUU | Long Treasuries | 2001-01-12 | 0 | 0 |
| LUMSTRUU | MBS | 2001-01-12 | 0 | 0 |
| LBUTTRUU | TIPS | 2001-01-12 | 0 | 0 |
| LT01TRUU | Treasuries | 2001-01-12 | 0 | 0 |
| LT09TRUU | Treasuries | 2001-01-12 | 0 | 0 |
| LT13TRUU | Treasuries | 2007-01-12 | 313 | 0 |

## Duration times spread

For each instrument with an `INDEX_OAS_TSY`: the median over weeks of the credit loading over `-OAD x OAS / OAS of LUACTRUU`. 1 means the credit loading is duration times spread, scaled to the reference. **Left out:** the Treasuries, Long Treasuries, TIPS classes and the government ex-USD indices `I02513EU`, `I02913JP`, `I12823GB`, `LET1TREU`. Their spread over Treasuries is near zero, so the ratio divides by almost nothing and means nothing.

| instrument | class | weeks | credit loading over duration x spread |
|---|---|---|---|
| I12877US | EM Corporate Bonds | 636 | 0.33 |
| EMUSTRUU | EM Sovereign Bonds | 900 | 0.22 |
| I20344US | EM Sovereign Bonds | 492 | 0.18 |
| LP05TREU | Ex-USD Bonds | 900 | 0.47 |
| I00183US | HY Corporates | 900 | 0.33 |
| I00184US | HY Corporates | 900 | 0.23 |
| I00185US | HY Corporates | 900 | 0.30 |
| I00188US | HY Corporates | 900 | 0.31 |
| LF98TRUU | HY Corporates | 900 | 0.30 |
| LDC5TRUU | IG Corporates | 758 | 0.24 |
| LUACTRUU | IG Corporates | 900 | 0.59 |
| LUMSTRUU | MBS | 898 | -0.04 |

## Checks the build made on itself

- gates against the run of record: skipped: the factors differ from the run of record's by design (credit is FRED BAA10Y, estimation starts at the factors' common start), decisions/0058
- no lookahead: `assert_no_lookahead` passed on every instrument's path
- factors: huber6-baa10y, estimation from common; all six factors exist from 1999-01-01
