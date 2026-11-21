# Task 100 step 3: the pilot's acceptance run, region cross-sectional, seeds 15 to 29

decisions/0074 (delegated), judged by decisions/0072's (a2) and (b1) as arithmetic only; the acceptance itself is Cowork's review. Planted data, the decisions/0070 defaults, h 13, `IC_prior` x1. 150 runs, 75 live/twin pairs. Lookahead passed on every run: yes.

## Per planted IC

| IC | quantity | n | mean | SD | min | max |
|---|---|---|---|---|---|---|
| 0.00 | net IR | 15 | +0.0833 | 0.1404 | -0.1242 | +0.3070 |
| 0.00 | net_ir_excess | 15 | -0.0070 | 0.0666 | -0.1820 | +0.1172 |
| 0.00 | realised IC, live | 15 | +0.0000 | 0.0000 | -0.0000 | +0.0000 |
| 0.00 | realised IC, twin | 15 | +0.0231 | 0.0347 | -0.0367 | +0.0975 |
| 0.05 | net IR | 15 | +0.1408 | 0.1500 | -0.0501 | +0.4109 |
| 0.05 | net_ir_excess | 15 | +0.0495 | 0.0713 | -0.1307 | +0.2121 |
| 0.05 | realised IC, live | 15 | +0.0500 | 0.0000 | +0.0500 | +0.0500 |
| 0.05 | realised IC, twin | 15 | +0.0242 | 0.0353 | -0.0371 | +0.1006 |
| 0.10 | net IR | 15 | +0.1961 | 0.1690 | -0.0256 | +0.4312 |
| 0.10 | net_ir_excess | 15 | +0.1041 | 0.1150 | -0.1634 | +0.2705 |
| 0.10 | realised IC, live | 15 | +0.1000 | 0.0000 | +0.1000 | +0.1000 |
| 0.10 | realised IC, twin | 15 | +0.0251 | 0.0359 | -0.0374 | +0.1035 |
| 0.20 | net IR | 15 | +0.3030 | 0.1549 | +0.0504 | +0.4753 |
| 0.20 | net_ir_excess | 15 | +0.1987 | 0.1169 | +0.0355 | +0.3934 |
| 0.20 | realised IC, live | 15 | +0.2000 | 0.0000 | +0.2000 | +0.2000 |
| 0.20 | realised IC, twin | 15 | +0.0269 | 0.0374 | -0.0377 | +0.1085 |
| 0.35 | net IR | 15 | +0.4637 | 0.1932 | +0.1342 | +0.8034 |
| 0.35 | net_ir_excess | 15 | +0.3655 | 0.1417 | +0.1261 | +0.6111 |
| 0.35 | realised IC, live | 15 | +0.3500 | 0.0000 | +0.3500 | +0.3500 |
| 0.35 | realised IC, twin | 15 | +0.0290 | 0.0400 | -0.0374 | +0.1140 |

## The bars, as arithmetic

- OLS slope of excess on planted IC over the 75 pairs: 1.0526 (SE 0.0969), t 10.861. (a2) t >= 2: meets.
- Gap, mean excess at IC 0.35 minus at IC 0: +0.3726. (a2) gap >= 0.10: meets.
- IC 0 pairs with net IR >= 0.30 and excess > 0: 0 of 15 (0.0%). (b1) <= 10%: meets.
- Baseline twins with net IR >= 0.30: 5.3% of 75.

