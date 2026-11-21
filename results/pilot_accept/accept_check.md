# Task 100 step 1: the 0072 addendum's table, re-run by the reviewer

From `results/audit/A-20261114-030208/cells.csv` (the grid, 25 runs an expression) and `results/audit/A-20261115-105504/cells.csv` (the null grid's IC 0 runs, 10 an expression). Excess = live `net_ir` minus its twin's; `IC_prior` x1; zero-score rows left out. OLS with a constant, classical SE. (b1): IC 0 runs with net IR >= 0.30 and excess > 0.

| | region cross-sectional | duration directional |
|---|---|---|
| (a2) slope, t: the grid's runs (n 25 / 25) | 0.8821, t 6.170 | 0.2921, t 1.860 |
| same, pooled (n 35 / 35) | 0.8372, t 7.281 | 0.3307, t 2.505 |
| (a2) gap, grid / pooled | 0.3258 / 0.2953 | 0.1021 / 0.1197 |
| (b1) count of 15 / 15 | 1 (6.7%) | 4 (26.7%) |

Beside the addendum (tolerance: 0.01 a slope or gap, 0.05 a t, one run a count; the addendum's printed rounding added):

| expression | figure | addendum | check | within |
|---|---|---|---|---|
| cross_sectional | slope (grid) | 0.88 | 0.8821 | yes |
| cross_sectional | t (grid) | 6.17 | 6.1698 | yes |
| cross_sectional | slope (pooled) | 0.84 | 0.8372 | yes |
| cross_sectional | t (pooled) | 7.28 | 7.2808 | yes |
| cross_sectional | gap (grid) | 0.326 | 0.3258 | yes |
| cross_sectional | gap (pooled) | 0.295 | 0.2953 | yes |
| cross_sectional | b1 count (15) | 1 | 1.0000 | yes |
| directional | slope (grid) | 0.29 | 0.2921 | yes |
| directional | t (grid) | 1.86 | 1.8596 | yes |
| directional | slope (pooled) | 0.33 | 0.3307 | yes |
| directional | t (pooled) | 2.5 | 2.5046 | yes |
| directional | gap (grid) | 0.102 | 0.1021 | yes |
| directional | gap (pooled) | 0.12 | 0.1197 | yes |
| directional | b1 count (15) | 4 | 4.0000 | yes |

All within: yes.

