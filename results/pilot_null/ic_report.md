# Step 1: the IC 0 baseline's realised IC under the null (no solves)

Planted IC 0, h 13, seeds [0, 1, 2, 3, 4], 40 block-shuffle draws per seed (the twin's function and block). `realised_ic_by_column` as the pilot's rows compute it. HANDOFF task 98.

## directional (duration)

Reproduction of task 94's IC 0 baseline (`realised_ic_by_column`, tolerance 1e-9):

| key | task 94 | probe | gap |
|---|---|---|---|
| duration-dir_ic0.00_h13_s0_baseline | 0.112609819314 | 0.112609819314 | 5.6e-17 |
| duration-dir_ic0.00_h13_s1_baseline | 0.002719316898 | 0.002719316898 | 5.2e-17 |
| duration-dir_ic0.00_h13_s2_baseline | 0.033473020798 | 0.033473020798 | 9.0e-17 |
| duration-dir_ic0.00_h13_s3_baseline | 0.034399422990 | 0.034399422990 | 5.6e-17 |
| duration-dir_ic0.00_h13_s4_baseline | 0.144778639746 | 0.144778639746 | 0.0e+00 |

| n | mean | SD | 1/sqrt(BxK) (B=75, K=1) | p05 | p95 | 3 SD/sqrt(n) | mean within it |
|---|---|---|---|---|---|---|---|
| 200 | +0.0668 | 0.0504 | 0.1155 | +0.0082 | +0.1442 | 0.0107 | NO |

Per seed over its draws (the noise draw is the seed's; only the shuffle changes):

| seed | mean | SD |
|---|---|---|
| 0 | +0.1105 | 0.0093 |
| 1 | +0.0116 | 0.0105 |
| 2 | +0.0361 | 0.0076 |
| 3 | +0.0358 | 0.0070 |
| 4 | +0.1401 | 0.0100 |

SD of the five seed means 0.0553; mean within-seed SD 0.0089.

## cross_sectional (region)

Reproduction of task 94's IC 0 baseline (`realised_ic_by_column`, tolerance 1e-9):

| key | task 94 | probe | gap |
|---|---|---|---|
| region-xs_ic0.00_h13_s0_baseline | -0.031176946550 | -0.031176946550 | 7.3e-17 |
| region-xs_ic0.00_h13_s1_baseline | 0.038075479944 | 0.038075479944 | 1.4e-17 |
| region-xs_ic0.00_h13_s2_baseline | 0.019804699102 | 0.019804699102 | 8.7e-17 |
| region-xs_ic0.00_h13_s3_baseline | 0.003865088984 | 0.003865088984 | 1.3e-18 |
| region-xs_ic0.00_h13_s4_baseline | 0.096273294062 | 0.096273294062 | 8.3e-17 |

| n | mean | SD | 1/sqrt(BxK) (B=75, K=6) | p05 | p95 | 3 SD/sqrt(n) | mean within it |
|---|---|---|---|---|---|---|---|
| 200 | +0.0253 | 0.0432 | 0.0471 | -0.0338 | +0.1014 | 0.0092 | NO |

Per seed over its draws (the noise draw is the seed's; only the shuffle changes):

| seed | mean | SD |
|---|---|---|
| 0 | -0.0303 | 0.0041 |
| 1 | +0.0384 | 0.0038 |
| 2 | +0.0136 | 0.0037 |
| 3 | +0.0059 | 0.0036 |
| 4 | +0.0990 | 0.0042 |

SD of the five seed means 0.0480; mean within-seed SD 0.0039.

## Reading (task 98 step 1's rule)

Reproduction of task 94's values: held. The mean is NOT within 3 x SD/sqrt(200) of 0 in at least one expression: task 98 step 1's stop branch. Cowork rules from this report.

