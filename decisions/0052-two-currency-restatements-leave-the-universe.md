# 0052 — Two currency restatements leave the investable universe

**Status:** decided 2026-10-07 by the owner. Drafted by Cowork. Applied by
HANDOFF task 52. Follows `decisions/0013` and `0022`. No change to
`SUBSTRATE.md`, `params/` or `vetoes/`.

## What the owner found

Pulling analytics for the ex-USD bond indices on 2026-10-07, the owner found
that `LGTRTRJU` returned the same analytics as a series already in the pull:

> "this JPY denominated LEGATRUU, not sure what the value for our research
> in just evaluating an existing index in another currency. If there are
> other cases like this probably not worth either. LGTRTRGU i think is the
> same thing, just LEGATRUU, but evaluated in GBP."

So both are the global aggregate, the benchmark's own bond leg, restated in
yen and in sterling. A dollar investor cannot hold either without a currency
overlay, and the lab has none (SUBSTRATE §4).

## What the store shows

From `huber6-v1`, the median loading on the dollar factor and the
full-sample explained share *(Cowork's read of the store; medians over
weeks)*:

| Index | Dollar loading | Explained share |
|---|---|---|
| `LGTRTRGU` | 0.08 | 0.28 |
| `LGTRTRJU` | −0.01 | 0.15 |
| `LET1TREU` Euro Treasury 1-10y | −1.15 | 0.89 |
| `LP05TREU` Pan-Euro Corporate | −1.00 | 0.87 |
| `LG38TRUU` Global Aggregate ex-USD | −0.84 | 0.82 |
| `I12823GB` UK Gilt 1-10y | −0.67 | 0.41 |
| `I02913JP` Japan Aggregate | −0.61 | 0.42 |
| `I02513EU` Pan-European Government | 0.10 | 0.44 |

An unhedged foreign bond loses when the dollar rises. The two restated
series do not, and they are the two worst-explained series in their class.

## The ruling

1. **`LGTRTRGU` and `LGTRTRJU` are not investable.** They stay in the panel,
   flagged, as `SPBDALB` does (`decisions/0022`). Their reporting class is
   unchanged.
2. **The reason recorded on each:** the global aggregate restated in another
   currency, not an instrument.
3. **Numbers recorded before today stand.** The estimator test's run of
   record, `M-20261003T181155Z`, scored 86 instruments including these two,
   and is not re-run. `huber6-v1` is not edited; task 52 builds `huber6-v2`.

## What follows

- Investable series: 95 to 93.
- The estimator test's selection: 86 to 84. The store: 87 to 85 estimated.
- Ex-USD Bonds estimated: 8 to 6.
- SUBSTRATE §5.4a names these two among the series that represent the FX
  axis "until they land". The unhedged series it was waiting for have
  landed. The sentence is stale and its tidying is the owner's (OWNER-QUEUE
  L31).

## What it does not decide

- **`I02513EU`.** Its dollar loading is 0.10, which reads like a euro return
  treated as a dollar one. *That is Cowork's inference.* SUBSTRATE §5.4a
  already flags its currency as unconfirmed. The owner did not rule on it;
  it stays investable (OWNER-QUEUE L29).
- **A longer history for `M1CXNNA`.** The gross sibling `M2CXNNA` is daily
  from 2000-12-29. The owner did not take the splice. It would be an
  owner-only edit to `params/data.yaml`, and it mixes a gross series with
  net siblings.
- **`MXEU0RL`.** Its predecessor `MXEU0RE` is daily from 1995 but was pulled
  as a price index in euros. It needs `TOT_RETURN_INDEX_GROSS_DVDS` in
  dollars.
- **The other six tradable-only series,** for which no earlier daily history
  was found.

## The two files the owner supplied, 2026-10-07

Both are in `data/raw/bloomberg/`, git-ignored, unchanged from what he sent.

| File | sha256 begins | Holds | Read by |
|---|---|---|---|
| `bbg_exusd_bonds_analytics.xlsx` | `a76df50225f99128` | Duration, yield to worst and OAS for seven ex-USD bond indices, 44,190 rows | HANDOFF task 52 |
| `bbg_tradable_only_longer_history.xlsx` | `299ead6ba64b4146` | `PX_LAST` for the eight tradable-only tickers and two siblings, 37,721 rows | nothing yet |
