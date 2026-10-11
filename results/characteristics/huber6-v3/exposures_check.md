# Exposure map check, store `huber6-v3` (HANDOFF task 54)

Every store week walked through `resolve_exposures`, then the Tuesday after each one. Counts, dates, means and medians only.

| Figure | Got | Cowork's read |
|---|---|---|
| Store weeks | 888 (2002-12-27 to 2019-12-27) | 888, 2002-12-27 to 2019-12-27 |
| All Fridays / none skipped | True / True | yes / yes |
| Instrument-weeks | 72,606 | 72,606 |
| Rule rows equal instrument-weeks (no row dropped for a missing value) | True | |
| Instruments at the first / last week | 73 / 84 | 73 / 84 |
| Duration cells measured / estimated / missing | 6,763 / 65,843 / 0 | 6,763 / 65,843 / 0 |
| Measured duration cells at or below zero | 0 | 0 |
| Mean of `axis_duration` | 1.4274 | 1.4274 |
| Mean of `axis_real_nominal` | 1.2792 | 1.2792 |
| Mean of `axis_credit` | 1.3006 | 1.3006 |
| Usage rows on the Fridays | 72,606, fitted_through = used_on_date: True | 72,606, yes |
| Usage rows on the Tuesdays | 72,606, used four days after fitted_through: True | yes |
| 2001-01-05 and 2002-12-20 raise | {'2001-01-05': True, '2002-12-20': True} | both raise |

## Duration, measured and estimated weeks

| Instrument | Measured | Estimated | Estimated from | Estimated to | Cowork's read |
|---|---|---|---|---|---|
| `LT13TRUU` | 677 | 211 | 2002-12-27 | 2007-01-05 | 677 / 211 |
| `LDC5TRUU` | 758 | 0 | - | - | 758 / 0 |
| `LT01TRUU` | 888 | 0 | - | - | 888 / 0 |
| `LT09TRUU` | 888 | 0 | - | - | 888 / 0 |
| `LT11TRUU` | 888 | 0 | - | - | 888 / 0 |
| `LUTLTRUU` | 888 | 0 | - | - | 888 / 0 |
| `LBUTTRUU` | 888 | 0 | - | - | 888 / 0 |
| `LUACTRUU` | 888 | 0 | - | - | 888 / 0 |

## Median `axis_duration` by reporting class at 2019-12-27

Gold reads above a 7-10y Treasury because it reads minus its real-yield loading. That is `decisions/0050` as ruled.

| Class | Median | Cowork's read |
|---|---|---|
| European Equities | -1.14 | -1.14 |
| Japanese Equities | -0.16 |  |
| US Equities | -0.02 |  |
| APAC ex-Japan Equities | -0.02 |  |
| Commodities | 0.08 |  |
| Cash | 0.08 |  |
| DM ex-US Equities | 1.33 |  |
| HY Corporates | 1.34 |  |
| Real Assets | 1.81 |  |
| EM Equities | 2.12 | 2.12 |
| EM Corporate Bonds | 2.48 |  |
| Ex-USD Bonds | 2.73 |  |
| EM Sovereign Bonds | 3.30 |  |
| MBS | 3.71 |  |
| Treasuries | 4.48 | 4.48 |
| TIPS | 4.55 | 4.55 |
| IG Corporates | 5.22 | 5.22 |
| Gold | 8.63 | 8.63 |
| Long Treasuries | 18.32 | 18.32 |

## Figures that differ from Cowork's read

- none
