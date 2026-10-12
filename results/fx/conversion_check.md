# FX conversion check (decisions/0053, HANDOFF task 53)

`NDDLUK` converted from GBP against `NDDUUK`, weekly Friday closes, 2002-01-01 to 2019-12-27. FX file sha256 `1d6fbb63e8a33e2e...`. Aggregates only.

| Figure | Same day | Rate lagged one business day | Cowork's read |
|---|---|---|---|
| Weekly tracking error (bp/yr) | 238.46 | 601.11 | 238.0 |
| 4-week tracking error, non-overlapping (bp/yr) | 108.55 | 263.67 | 107.0 |
| Lag-1 autocorrelation of the weekly difference | -0.51 | -0.50 | -0.51 |
| Cumulative gap (bp) | -50.04 | -54.25 | -50.0 |
| 4-week tracking error, overlapping (bp/yr) | 115.93 | 291.76 | |
| Weeks | 938 | 938 | |

- Same-day is the better alignment: **True**.
- Figures differing from Cowork's by more than the tolerance (5 bp, 0.02): none.
- `NDDLUK` dates dropped for want of an FX rate: 0.

## The global aggregate restated, converted, against `LEGATRUU` (same day)

| Series | Currency | Weekly TE (bp/yr) | Lag-1 autocorrelation | Cumulative gap (bp) | Weeks | FX dates dropped |
|---|---|---|---|---|---|---|
| `LGTRTRGU` | GBP | 281.93 | -0.34 | -118.63 | 936 | 0 |
| `LGTRTRJU` | JPY | 273.96 | -0.35 | -58.75 | 936 | 0 |

- Above 1000 bp/yr (the direction or the series would be wrong): none.

## The ex-USD bonds on Bloomberg's close, against FRED's conversion (decisions/0056)

Each bond delivered in local currency, converted with the FX file on the same date, against the same bond converted with FRED's spot (the pull's own USD column). Weekly Friday closes over the development window. Cowork's read: 195 to 210 bp/yr weekly.

| Series | Currency | Weekly TE (bp/yr) | Lag-1 autocorrelation | Cumulative gap (bp) | Weeks | Days regained | FX dates dropped |
|---|---|---|---|---|---|---|---|
| `I02913JP` | JPY | 209.33 | -0.56 | 31.96 | 958 | 162 | 0 |
| `I12823GB` | GBP | 199.23 | -0.47 | -14.26 | 702 | 102 | 0 |
| `LET1TREU` | EUR | 203.11 | -0.49 | -33.96 | 953 | 138 | 0 |
| `LP05TREU` | EUR | 202.83 | -0.49 | -33.96 | 956 | 139 | 0 |

- Above 1000 bp/yr (stop): none.
