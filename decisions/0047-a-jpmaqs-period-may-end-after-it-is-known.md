# 0047 — A JPMaQS period may end after the number is known; the holdout binds on the knowledge date

**Status:** decided 2026-10-02 by the owner (OWNER-QUEUE L21: "accept").
Drafted by Cowork. Extends `decisions/0014`. Amends SUBSTRATE §5.6 (v0.9).
Applied by HANDOFF task 46.

## The measurement

The owner's pull `P-20261002T032635Z` (150,644 rows, 26 tickers, to
2019-12-31) carries **13,562 valued rows with a negative `eop_lag`**, on seven
tickers: the bank-lending survey scores (`USD_` and `EUR_BLSCSCORE_NSA_D2Q2QL2`),
the business-confidence scores (`USD_` and `EUR_MBCSCORE_SA`) and three
intuitive-GDP series (`JPY_`, `EUR_` and `GBP_INTRGDP_NSA_P1M1ML12_D3M3ML3`).
They serve H-2026-0001 and H-2026-0004. Task 44's loader refused them, as
Cowork's spec told it to, because `period_end = real_date − eop_lag` then falls
after `knowledge_date`, and `VintagePanel` rejects that.

The vendor defines `eop_lag` as "days elapsed since the end of the observation
period". The vendor pages Cowork read do not explain negative values. **The
reading adopted here is that the number is published before the period it
describes has ended** (a survey, a nowcast). *That reading is Cowork's and is
not verified against the vendor; §3 below is the check on it.*

## The ruling

1. **The seven tickers are kept.** Nothing is dropped, clipped or shifted.
   `period_end` stays `real_date − eop_lag`, as `decisions/0014` defines it.
2. **For JPMaQS, `period_end` may fall after `knowledge_date`.** What protects
   against lookahead is the knowledge date, which is the vendor's own
   `real_date`. `period_end` is a label for what the number describes.
   `VintagePanel` keeps its check by default and the JPMaQS loader switches it
   off explicitly; every other source keeps it.
3. **A checkpoint on the reading.** The loader counts negative lags by size.
   **If any valued row has an `eop_lag` below −92 days, nothing is built and
   the owner is asked.** A period ending within about a quarter fits a survey
   or a nowcast; one ending a year out would not. *The 92 days are Cowork's
   choice.*
4. **The holdout binds on the knowledge date.** A number known on 2019-12-20
   about a quarter ending 2020-03-31 is 2019 information. So for JPMaQS the
   lock is enforced on `real_date` and `knowledge_date`, and not on
   `period_end`. `loaders/holdout.py` is not changed and gains no bypass. The
   snapshot manifest records the latest `period_end` and how many rows have a
   `period_end` on or after `HOLDOUT_START`, so the exception is visible.

## Consequences

- `SUBSTRATE.md` §5.6 gains two sentences (v0.9).
- No row with a `knowledge_date` on or after 2020-01-01 is ever stored or
  loaded. That is unchanged.
- A signal that aligns on `period_end` rather than reading through
  `VintagePanel.as_of` would now be able to mis-date these series. `as_of`
  remains the only sanctioned way to read the panel (`decisions/0014`).
