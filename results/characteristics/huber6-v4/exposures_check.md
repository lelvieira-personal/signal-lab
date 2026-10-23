# Exposure map check, store `huber6-v4` (HANDOFF task 54)


Every store week walked through `resolve_exposures`, then the Tuesday after each one. Counts, dates, means and medians only.

| Figure | Got | Cowork's read |
|---|---|---|
| Store weeks | 990 (2001-01-12 to 2019-12-27) | 888, 2002-12-27 to 2019-12-27 |
| All Fridays / none skipped | True / True | yes / yes |
| Instrument-weeks | 79,125 | 72,606 |
| Rule rows equal instrument-weeks (no row dropped for a missing value) | True | |
| Instruments at the first / last week | 53 / 84 | 73 / 84 |
| Duration cells measured / estimated / missing | 7,375 / 71,750 / 0 | 6,763 / 65,843 / 0 |
| Measured duration cells at or below zero | 0 | 0 |
| Mean of `axis_duration` | 1.4178 | 1.4274 |
| Mean of `axis_real_nominal` | 1.2671 | 1.2792 |
| Mean of `axis_credit` | 0.8908 | 1.3006 |
| Usage rows on the Fridays | 79,125, fitted_through = used_on_date: True | 72,606, yes |
| Usage rows on the Tuesdays | 79,125, used four days after fitted_through: True | yes |
| 2001-01-05 and 2002-12-20 raise | {'2001-01-05': True, '2002-12-20': False} | both raise |

## Duration, measured and estimated weeks

| Instrument | Measured | Estimated | Estimated from | Estimated to | Cowork's read |
|---|---|---|---|---|---|
| `LT13TRUU` | 677 | 313 | 2001-01-12 | 2007-01-05 | 677 / 211 |
| `LDC5TRUU` | 758 | 0 | - | - | 758 / 0 |
| `LT01TRUU` | 990 | 0 | - | - | 888 / 0 |
| `LT09TRUU` | 990 | 0 | - | - | 888 / 0 |
| `LT11TRUU` | 990 | 0 | - | - | 888 / 0 |
| `LUTLTRUU` | 990 | 0 | - | - | 888 / 0 |
| `LBUTTRUU` | 990 | 0 | - | - | 888 / 0 |
| `LUACTRUU` | 990 | 0 | - | - | 888 / 0 |

## Median `axis_duration` by reporting class at 2019-12-27

Gold reads above a 7-10y Treasury because it reads minus its real-yield loading. That is `decisions/0050` as ruled.

| Class | Median | Cowork's read |
|---|---|---|
| European Equities | -1.24 | -1.14 |
| APAC ex-Japan Equities | -0.17 |  |
| US Equities | 0.03 |  |
| Cash | 0.06 |  |
| Commodities | 0.06 |  |
| Japanese Equities | 0.09 |  |
| HY Corporates | 1.15 |  |
| DM ex-US Equities | 1.31 |  |
| Real Assets | 1.66 |  |
| EM Corporate Bonds | 2.26 |  |
| Ex-USD Bonds | 2.63 |  |
| EM Equities | 2.63 | 2.12 |
| EM Sovereign Bonds | 3.27 |  |
| MBS | 3.72 |  |
| Treasuries | 4.48 | 4.48 |
| TIPS | 4.55 | 4.55 |
| IG Corporates | 5.22 | 5.22 |
| Gold | 8.29 | 8.63 |
| Long Treasuries | 18.32 | 18.32 |

## Figures that differ from Cowork's read

- {'figure': 'store_weeks', 'expected': 888, 'got': 990}
- {'figure': 'first_week', 'expected': '2002-12-27', 'got': '2001-01-12'}
- {'figure': 'instrument_weeks', 'expected': 72606, 'got': 79125}
- {'figure': 'instruments_first_week', 'expected': 73, 'got': 53}
- {'figure': 'duration_measured', 'expected': 6763, 'got': 7375}
- {'figure': 'duration_estimated', 'expected': 65843, 'got': 71750}
- {'figure': 'mean_axis_duration', 'expected': 1.4274, 'got': 1.4178450886164642}
- {'figure': 'mean_axis_real_nominal', 'expected': 1.2792, 'got': 1.2671008568223194}
- {'figure': 'mean_axis_credit', 'expected': 1.3006, 'got': 0.8907879539915978}
- {'figure': 'LT13TRUU', 'expected': [677, 211], 'got': [677, 313]}
- {'figure': 'LT01TRUU', 'expected': [888, 0], 'got': [990, 0]}
- {'figure': 'LT09TRUU', 'expected': [888, 0], 'got': [990, 0]}
- {'figure': 'LT11TRUU', 'expected': [888, 0], 'got': [990, 0]}
- {'figure': 'LUTLTRUU', 'expected': [888, 0], 'got': [990, 0]}
- {'figure': 'LBUTTRUU', 'expected': [888, 0], 'got': [990, 0]}
- {'figure': 'LUACTRUU', 'expected': [888, 0], 'got': [990, 0]}
- {'figure': 'friday_usage_rows', 'expected': 72606, 'got': 79125}
- {'figure': 'raises', 'expected': ['2001-01-05', '2002-12-20'], 'got': {'2001-01-05': True, '2002-12-20': False}}
