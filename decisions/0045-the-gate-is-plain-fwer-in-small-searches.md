# 0045 — In a search of fewer than 8 tests, the gate is ordinary FWER (g = 1)

**Status:** decided 2026-10-01 by the owner (OWNER-QUEUE L20, "I accept your
recs"). Drafted by Cowork. Amends `decisions/0043` and SUBSTRATE §9 and §10.

## The problem

`romano_wolf_gfwer` with g = 2 controls P(two or more false passes). A set of
fewer than g tests can't produce g false passes, so its critical value is −∞.
**A search of one test is rejected (passes) unconditionally**, and bar 2
reduces to `net_ir_excess > 0`, which a null clears about half the time. This
is mathematically correct, and no gate at all. `family_then_within`
(OWNER-QUEUE L12) runs the stepdown inside families, and today each holds one
hypothesis, so every within-family step is m = 1.

Cowork's check (independent nulls, k = 100, step 1 only, so these are lower
bounds) of the per-null-hypothesis false-pass rate under g = 2:

| m | 1 | 2 | 3 | 4 | 6 | 8 | 12 |
|---|---|---|---|---|---|---|---|
| false-pass rate | 1.00 | 0.22 | 0.13 | 0.10 | 0.06 | 0.05 | 0.03 |

## The ruling

1. **When the stepdown is run over m < 8 statistics, it runs at g = 1**:
   ordinary Romano-Wolf FWER at α = 5%, standardised against the pooled null,
   with k = 100 shuffles. At m ≥ 8 it runs at g = 2, as in `decisions/0043`.
2. **m is the number of statistics the stepdown is actually run over**: the
   `n_tests` the gate reports. The rule therefore binds at every level of
   `family_then_within`, whatever L12 decides about grouping.
3. g = 1 is `romano_wolf_gfwer(…, g=1)`, which equals `romano_wolf` by
   construction. The verdict's `procedure` stays `romano_wolf_gfwer`.
4. **The floor (8) is Cowork's**, chosen as the smallest m at which g = 2's
   per-hypothesis false-pass rate falls to α in the check above. It lives in
   params (`small_search_below`), and the owner can change it.

## Consequences

- `params/vetoes.yaml` `multiple_testing`: `small_search_below: 8` and
  `small_search_g: 1`.
- `vetoes/rules.py`: the required g depends on the verdict's `n_tests`, and a
  verdict without `n_tests` fails as a missing input. The veto also checks
  the verdict's `standardise` against params (task 42 review, F7), and a
  verdict without it fails as a missing input.
- `stats.multiple_testing.gate` picks g from m by the same rule, and reports
  `standardise`.
- **Power:** at m = 1 and g = 1 the gate is a single block-shuffle test at
  5%. Single-test power at IC 0.70 was about 35-45% on one history
  (`decisions/0039`).
- `params_hash` changes.

- **params_hash, 2026-10-01 (HANDOFF task 43):** params_version 0.8.0 -> 0.9.0 (CRLF form throughout; `.gitattributes` pins `params/*.yaml` to `eol=crlf`); `params_hash` moved `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8` -> `b3d41267a752b9d76e2ddf17264cccb5b5b9ea6f0f45edc8bf1517524674376a`.
