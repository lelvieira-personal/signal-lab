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
