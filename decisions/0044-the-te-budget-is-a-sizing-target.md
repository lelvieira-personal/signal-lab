# 0044 — The 6% tracking-error budget is a sizing target, not a ceiling on realised TE

**Status:** decided 2026-10-01 by the owner (OWNER-QUEUE L19, "I accept your
recs"). Drafted by Cowork. Confirms SUBSTRATE §4's existing "≤ 6.0% ex ante"
reading and `decisions/0025`'s derivation. No sizing changes.

## The measurement

Task 35 (`A-20260930-033812`), the policy arm (26-week scalar overlay,
`decisions/0042`), was recomputed by Cowork from `cells.csv`, with means over
10 seeds:

| horizon | ex-ante TE (mean) | realised / ex-ante | p95 trailing-3y TE / 6% |
|---|---|---|---|
| 4 | 5.8-5.9% | 0.95-0.96 | 1.12-1.15 (seeds to 1.24) |
| 13 | 5.8-5.9% | 0.98-0.99 | 1.15-1.17 (to 1.31) |
| 26 | 5.8-5.9% | 0.99 | 1.18-1.19 (to 1.39) |

With no overlay, the p95 ratio is 1.27-1.34. The book is sized correctly on
average. The p95 is above 1 because a trailing 3-year window swings around its
mean: sampling noise on 156 weeks (about +9% at p95 under iid, a Cowork
approximation) plus volatility clustering that the overlay doesn't fully track.

## The ruling

1. **The 6% is σ, the ex-ante sizing target** the solver enforces at every
   rebalance. It is the quantity `decisions/0025` derives from the 18%
   active-drawdown tolerance (E[max DD] = σ·g(IR)).
2. **The realised trailing-3y TE, including its p95, is a disclosed
   characteristic** (`decisions/0030`), never a ceiling and never a gate.
   Reports show `te_p95_to_budget` beside the budget so a reader sees how hot
   the book runs in its worst windows.
3. **Not chosen:** sizing to about 5.1% so the p95 sits at 6%. That reading
   would apply only if 6% were an investor-facing ceiling on realised
   trailing TE, and the owner's acceptance of Cowork's recommendation records
   that it is not.

## Consequences

- `params/constraints.yaml`: the `tracking_error` comment no longer says §10
  vetoes trailing-3y TE (stale since 0030). The key `max_trailing_3y` keeps
  its name, because code reads it. Its comment states that it is the ex-ante
  sizing target.
- SUBSTRATE §4's Tracking-error row cites this record.
- `params_hash` changes (comment only, in the same version bump as
  `decisions/0045`).
- **Worth knowing, not ruled:** 0025 inverts the *median* max drawdown, so at
  IR 0.30 about half of 19-year paths exceed the 18% tolerance by
  construction.

- **params_hash, 2026-10-01 (HANDOFF task 43):** params_version 0.8.0 -> 0.9.0 (CRLF form throughout; `.gitattributes` pins `params/*.yaml` to `eol=crlf`); `params_hash` moved `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8` -> `b3d41267a752b9d76e2ddf17264cccb5b5b9ea6f0f45edc8bf1517524674376a`.
