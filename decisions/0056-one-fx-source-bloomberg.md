# 0056 — One FX source: every return not delivered in dollars is converted with Bloomberg's close

**Status:** decided 2026-10-11 by the owner (OWNER-QUEUE L33, option (b)).
Drafted by Cowork. Follows `decisions/0053`. **Not built here:** it lands with
the store that OWNER-QUEUE L35 needs, so the lab moves to one new store and one
new params version, not two. No change to `params/` or `vetoes/` in this
record. **SUBSTRATE §5.4a is amended in v0.11** with the wording below, which
the owner approved on 2026-10-11 ("0056: approved proposed change").

## What the owner said

- **2026-10-11, 22:10:** "let's go with bloomberg (b)".
- **2026-10-11, 22:25,** when Cowork said a Bloomberg pull of local-currency
  levels was needed: "I already shared this data from bloomberg for the 5
  indices, they were already in local currency as the argument FX=USD was not
  passed. Not sure what is missing here".

## What Cowork had wrong

Nothing is missing. `data/universe/raw_structure.json` (written by
`make inspect-raw`; structure only) shows that
`bbg_exusd_bonds_usd_unhedged.csv` carries three columns for each of four
tickers, `<ticker>_local_<CCY>`, `<ticker>_USD_unhedged` and
`<ticker>_fx_USDper<CCY>`. `LG38TRUU` has only `LG38TRUU_USD_unhedged`.
`read_exusd_csv` reads the `_USD_unhedged` columns and nothing else, so the
local levels were in the repo all along and unused.

| Ticker | Currency | Non-empty local | Non-empty USD | Difference | Dropped where no FRED fix (`bbg_exusd_bonds_coverage.csv`) |
|---|---|---|---|---|---|
| `LET1TREU` | EUR | 7,031 | 6,813 | 218 | 218 |
| `I12823GB` | GBP | 5,264 | 5,094 | 170 | 170 |
| `I02913JP` | JPY | 6,537 | 6,303 | 234 | 234 |
| `LP05TREU` | EUR | 7,039 | 6,820 | 219 | 219 |

Counts are over the whole file, holdout rows included, as `inspect-raw`
reports them. The FRED conversion was done when the file was built, outside
the repo.

## The ruling

1. **One source.** Every return series not delivered in dollars is converted
   with `data/raw/bloomberg/bbg_curncy_hist.xlsx`, through the convention
   table of `decisions/0053`, on the same date, never carried.
2. **The four ex-USD bonds above** are read from their `_local_<CCY>` columns
   and converted like the eighteen series of `0053`.
   - The file's `_USD_unhedged` and `_fx_` columns are no longer read for
     these four. The vendor file is not edited.
   - The quote currency is the column's suffix. It must equal `local_ccy` in
     `data/universe/bbg_exusd_bonds_coverage.csv`, or the loader refuses.
   - The `exempt` set that `load_returns` passes to `_to_usd` shrinks to
     `LG38TRUU`.
3. **`LG38TRUU` stays as pulled, in dollars.** It has no local column. It is
   Bloomberg's own conversion, so it is not a second FX source in the sense
   of L33. *Cowork's understanding, not verified:* Bloomberg converts its
   indices at the WM/Reuters 4pm London fix.
4. **The test, before the store is built** (as in `0053`): the four
   re-converted series against the same series converted at FRED spot,
   weekly Friday closes, development window, same day.
   - *Cowork's read in L33:* the two conversions differ by 195 to 210 bp/yr
     weekly, reverting the next week.
   - Above 1,000 bp/yr, stop: the direction or the series is wrong.
5. **Days come back.** Where the FRED fix was missing and Bloomberg has a
   rate, the day returns as an observation. How many fall in the
   development window is measured by the build, not assumed here.

## SUBSTRATE §5.4a — applied in v0.11 (owner approved 2026-10-11: "0056: approved proposed change")

The first sentence now reads:

> The unhedged-USD series requested from Bloomberg have landed
> (`data/raw/bloomberg/bbg_exusd_bonds_usd_unhedged.csv`, local level times FRED
> spot):

Proposed:

> The ex-USD bond series requested from Bloomberg have landed
> (`data/raw/bloomberg/bbg_exusd_bonds_usd_unhedged.csv`). Four are delivered in
> their local currency and converted in the loader with Bloomberg's close, like
> every other series (`decisions/0056`); the file's FRED-converted columns are
> not read. `LG38TRUU` is delivered in dollars:

The list beneath it is unchanged.

## What it does not decide

- **A London 4pm source** (L33 option (d)). Neither source the lab has is the
  fix MSCI and Bloomberg convert at.
- **The new store's name and the params change.** Both are in
  `decisions/0058`.

## What would reopen it

- A London 4pm FX source that resolves on Bloomberg.
- The step-4 test reading above its bar.
