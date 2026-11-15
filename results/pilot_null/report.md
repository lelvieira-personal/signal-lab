# Task 99 step 2: the pilot's null over ten more seeds, and the zero-view floor

IC 0, h 13, the decisions/0070 defaults. Pooled: task 94's IC 0 rows (`A-20261114-030208`, seeds 0 to 4) and the null grid's (seeds 5 to 14). Bar 1's `target_net_ir` 0.30 (params/audit.yaml), read as a share only; no verdict. HANDOFF task 99.

## directional (duration)

| | n | mean | SD | min | max |
|---|---|---|---|---|---|
| net IR, IC 0 live | 15 | +0.293 | 0.259 | -0.214 | +0.685 |
| net_ir_excess | 15 | -0.009 | 0.081 | -0.249 | +0.072 |
| net IR, baseline twins | 15 | +0.301 | 0.241 | -0.221 | +0.643 |

Shares over the 15 IC 0 live runs: net IR >= 0.30 40%; excess > 0 67%; both 27%. Over the 15 baseline twins: net IR >= 0.30 47%.

Zero-score run (`duration-dir_ic0.00_h13_s0_noview`; the no-view arm keeps its own arguments, legacy True): net IR -0.077, active return -0.0009 a year, cost drag 0.0014, turnover 0%.

Factor attribution, the null grid's 10 IC 0 live runs (seeds 5 to 14; exposure at t times the factor's move t to t+1, annualised; task 94's rows carry none). Mean active return +0.0131 a year.

| factor | mean active exposure | explained a year | seeds with the mean's sign |
|---|---|---|---|
| equity | +0.0503 | +0.0057 | 8/10 |
| real_yield | -1.2739 | +0.0032 | 8/10 |
| inflation | -1.8497 | +0.0025 | 8/10 |
| credit | -0.9447 | -0.0035 | 9/10 |
| dollar | +0.0669 | +0.0010 | 6/10 |
| commodities | +0.0064 | -0.0003 | 5/10 |
| unexplained | | +0.0044 | |

Explained by factors whose sign holds on at least two-thirds of the seeds: +0.0079, 60% of the mean active return. The twins' `realised_ic_by_column` matches step 1 (a) seed by seed to 9.0e-17.

## cross_sectional (region)

| | n | mean | SD | min | max |
|---|---|---|---|---|---|
| net IR, IC 0 live | 15 | +0.103 | 0.167 | -0.139 | +0.395 |
| net_ir_excess | 15 | +0.014 | 0.087 | -0.167 | +0.193 |
| net IR, baseline twins | 15 | +0.089 | 0.211 | -0.310 | +0.386 |

Shares over the 15 IC 0 live runs: net IR >= 0.30 7%; excess > 0 60%; both 7%. Over the 15 baseline twins: net IR >= 0.30 20%.

Zero-score run (`region-xs_ic0.00_h13_s0_noview`; the no-view arm keeps its own arguments, legacy True): net IR -0.077, active return -0.0009 a year, cost drag 0.0014, turnover 0%.

Factor attribution, the null grid's 10 IC 0 live runs (seeds 5 to 14; exposure at t times the factor's move t to t+1, annualised; task 94's rows carry none). Mean active return +0.0032 a year.

| factor | mean active exposure | explained a year | seeds with the mean's sign |
|---|---|---|---|
| equity | +0.1002 | +0.0038 | 10/10 |
| real_yield | -0.1754 | +0.0005 | 8/10 |
| inflation | -0.1369 | -0.0010 | 8/10 |
| credit | -0.4493 | -0.0010 | 6/10 |
| dollar | +0.0306 | +0.0004 | 5/10 |
| commodities | +0.0413 | -0.0009 | 7/10 |
| unexplained | | +0.0015 | |

Explained by factors whose sign holds on at least two-thirds of the seeds: +0.0023, 71% of the mean active return. The twins' `realised_ic_by_column` matches step 1 (a) seed by seed to 9.0e-17.

## Reading, with its basis (reported, not a stop)

Rule (task 98 step 2): a real premium if the zero-score run's net IR is at most 0 and the IC 0 runs' mean active return is at least two-thirds explained by factor exposures whose sign holds on at least two-thirds of the seeds; otherwise say what is unexplained.

- directional: not shown to be a real premium under the rule (zero-score net IR -0.077; 60% explained by sign-holding factors; unexplained +0.0044 a year).
- cross_sectional: a real premium under the rule (zero-score net IR -0.077; 71% explained by sign-holding factors; unexplained +0.0015 a year).

