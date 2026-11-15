# Task 99 step 1: the pilot's null with the seed as the unit, and the shuffle itself

Planted h 13; seeds 0 to 14; block 52 weeks. `realised_ic_by_column` as the pilot's rows compute it. HANDOFF task 99, decisions/0073. No solves.

## directional (duration), B 75, K 1

### (a) The seed as the unit: each seed's twin, its own draw (`baseline_rng(seed)`)

| seed | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IC | +0.113 | +0.003 | +0.033 | +0.034 | +0.145 | -0.136 | -0.072 | -0.040 | +0.107 | -0.079 | -0.078 | -0.052 | -0.044 | +0.043 | -0.067 |

Reproduction of task 94 (seeds 0 to 4, tolerance 1e-9): max gap 9.0e-17, held.

| n | mean | SD | SE = 1/sqrt(BxK)/sqrt(n) | z = mean/SE | abs(z) > 3 |
|---|---|---|---|---|---|
| 15 | -0.0060 | 0.0826 | 0.0298 | -0.20 | no |

### (b) The shuffle itself: corr(block_shuffle_rows(truth), truth), `null_shuffle_rng(0, d)`, d 0 to 199

| n | mean | SD | 3 SD/sqrt(n) | 1/(blocks) | blocks (rows) | mean > 0.05 and beyond band |
|---|---|---|---|---|---|---|
| 200 | +0.0030 | 0.1019 | 0.0216 | 0.0526 | 19 (977) | no |

### (c) The twin's design (report only; the owner's, decisions/proposed/0072)

Mean (SD) over 15 seeds of `realised_ic_by_column`. Variant (k) reproduces `plant_axis_signal` to 8.9e-16.

| IC | variant | live | twin | live - twin |
|---|---|---|---|---|
| 0.00 | (k) as built (twin's noise orthogonal to the shuffled truth) | -0.0000 (0.0000) | -0.0060 (0.0826) | +0.0060 (0.0826) |
| 0.00 | (m) twin's noise orthogonal to the shuffled and the real truth | -0.0000 (0.0000) | +0.0000 (0.0000) | -0.0000 (0.0000) |
| 0.00 | (n) no orthogonalisation in either cell | -0.0035 (0.0815) | -0.0035 (0.0815) | -0.0000 (0.0000) |
| 0.35 | (k) as built (twin's noise orthogonal to the shuffled truth) | +0.3500 (0.0000) | -0.0034 (0.0804) | +0.3534 (0.0804) |
| 0.35 | (m) twin's noise orthogonal to the shuffled and the real truth | +0.3500 (0.0000) | +0.0022 (0.0342) | +0.3478 (0.0342) |
| 0.35 | (n) no orthogonalisation in either cell | +0.3455 (0.0667) | -0.0018 (0.0828) | +0.3474 (0.0351) |

## cross_sectional (region), B 75, K 6

### (a) The seed as the unit: each seed's twin, its own draw (`baseline_rng(seed)`)

| seed | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IC | -0.031 | +0.038 | +0.020 | +0.004 | +0.096 | +0.016 | -0.108 | -0.089 | -0.025 | -0.017 | +0.030 | -0.012 | -0.078 | -0.037 | +0.020 |

Reproduction of task 94 (seeds 0 to 4, tolerance 1e-9): max gap 8.7e-17, held.

| n | mean | SD | SE = 1/sqrt(BxK)/sqrt(n) | z = mean/SE | abs(z) > 3 |
|---|---|---|---|---|---|
| 15 | -0.0116 | 0.0534 | 0.0122 | -0.95 | no |

### (b) The shuffle itself: corr(block_shuffle_rows(truth), truth), `null_shuffle_rng(0, d)`, d 0 to 199

| n | mean | SD | 3 SD/sqrt(n) | 1/(blocks) | blocks (rows) | mean > 0.05 and beyond band |
|---|---|---|---|---|---|---|
| 200 | +0.0091 | 0.0652 | 0.0138 | 0.0526 | 19 (977) | no |

### (c) The twin's design (report only; the owner's, decisions/proposed/0072)

Mean (SD) over 15 seeds of `realised_ic_by_column`. Variant (k) reproduces `plant_axis_signal` to 8.9e-16.

| IC | variant | live | twin | live - twin |
|---|---|---|---|---|
| 0.00 | (k) as built (twin's noise orthogonal to the shuffled truth) | +0.0000 (0.0000) | -0.0116 (0.0534) | +0.0116 (0.0534) |
| 0.00 | (m) twin's noise orthogonal to the shuffled and the real truth | +0.0000 (0.0000) | +0.0000 (0.0000) | -0.0000 (0.0000) |
| 0.00 | (n) no orthogonalisation in either cell | -0.0116 (0.0537) | -0.0116 (0.0537) | -0.0000 (0.0000) |
| 0.35 | (k) as built (twin's noise orthogonal to the shuffled truth) | +0.3500 (0.0000) | -0.0115 (0.0466) | +0.3615 (0.0466) |
| 0.35 | (m) twin's noise orthogonal to the shuffled and the real truth | +0.3500 (0.0000) | -0.0006 (0.0239) | +0.3506 (0.0239) |
| 0.35 | (n) no orthogonalisation in either cell | +0.3382 (0.0451) | -0.0119 (0.0471) | +0.3501 (0.0228) |

## Reading (task 99 step 1's stop branch, decisions/0073's reversal)

Reproduction: held. Not the stop branch: in both expressions (b)'s mean is not both above 0.05 and beyond 3 SD/sqrt(200), and abs(z) in (a) is at most 3.

