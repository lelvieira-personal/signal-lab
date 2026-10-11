# 0053 — Every return is in dollars: local-currency series are converted in the loader

**Status:** decided 2026-10-10 by the owner (OWNER-QUEUE L32). Drafted by
Cowork. Applied by HANDOFF task 53. Follows `decisions/0013` and `0052`.
Changes SUBSTRATE §5.1 (invariant 8) and §5.4a (v0.10). No change to `params/` or `vetoes/`.

## What was found

`data/universe/raw_manifest.csv` declares the whole `TR Levels` sheet of
`bbg_data_values_only.xlsx` in USD. It is not:

- **19 return series are in their quote currency.** The Index Map's
  `Quote ccy` column (Bloomberg `CRNCY`) says so, and the loader mapped that
  column without checking it.
- **The pull carried no currency override.** The workbook's own record gives
  `Per=D, Fill=NA, Days=A` and nothing for currency (`Loader Notes` rows 3-5;
  the cell comments of 2026-09-07).
- **The returns agree.** On the dollar factor in `huber6-v2`, 17 of the 18
  estimated series load +0.10 to +0.85, while every dollar-quoted peer loads
  negative (*Cowork's read*).
- **The cleanest case is MSCI UK:** `NDDLUK` (sterling) loads +0.53 and
  `NDDUUK` (dollars) −0.24.

| Currency | Series |
|---|---|
| EUR | `I02513EU`, `MXEUG`, `MXEU0EN`, `MXEU0MT`, `MXEU0IN`, `MXEU0CD`, `MXEU0CS`, `MXEU0HC`, `MXEU0FN`, `MXEU0IT`, `MXEU0TC`, `MXEU0UT`, `MXEU0RL` |
| GBP | `NDDLUK` |
| CAD | `MXCA` |
| HKD | `MXCN` |
| INR | `MXIN` |
| KRW | `MXKR` |
| TWD | `TAMSCI` |

## What the owner said

> "the indices are coming in their original currency. Maybe this is a good
> thing, because eventually I may want to evaluate signals from the point of
> view of an investor whose base currency is different than the dollar.
> However, for now it is the US Dollar"

On 2026-10-10 he supplied `bbg_curncy_hist.xlsx`, with this rule for reading
it:

> "The quote is market convention so we need to avoid any confusion of
> considering GBP and EUR the same way as JPY for example. The former two are
> USD per EUR or USD per GBP while the JPY and most currencies are the
> Reference Curncy per USD."

## The ruling

1. **The base currency is USD.** Each series is kept as delivered, in its
   quote currency, and the loader expresses every return in the base
   currency. A second base currency is possible later and is not built now.
   No `params/` setting is added until one is needed.
2. **The FX source is `data/raw/bloomberg/bbg_curncy_hist.xlsx`.**
   - Sheet `FX_Spot_USD`, sha256 beginning `1d6fbb63e8a33e2e`. It is
     Bloomberg generic spot, `<CCY> Curncy` `PX_LAST`, with
     `Per=D, Fill=NA, Days=A`.
   - Its own notes say it is **not the WM/Refinitiv 4pm London fix:** the WM
     tickers returned "Invalid Security".
   - Dates on which all eight series were blank were removed before it was
     delivered.
3. **The quote convention is an explicit table, never inferred.**

   | Column | Quote | To get USD per unit |
   |---|---|---|
   | `EURUSD` | USD per EUR | the value |
   | `GBPUSD` | USD per GBP | the value |
   | `USDCAD`, `USDHKD`, `USDINR`, `USDKRW`, `USDTWD`, `USDJPY` | units per USD | 1 / the value |

   A column that is not in the table is refused.
4. **The conversion.**
   - **The rule:** USD level = local level × USD per unit, on the same date.
   - **No carrying:** on a date with a local level and no FX rate, the series
     has no USD level that day. Nothing is carried forward.
   - **Then as before:** returns follow SUBSTRATE §5.1 invariant 3.
   - **Scope:** it applies to every series in the table above, and to any
     later one whose quote currency is not its sheet's.
5. **A guard.** The loader stops on a return series whose quote currency is
   not its sheet's declared currency, unless rule 4 converts it. The ex-USD
   bond file is recorded as already converted (local × FRED spot).
6. **`NDDLUK` is not investable.** Once converted it is MSCI UK in dollars,
   which `NDDUUK` already is: a restatement, by `decisions/0052`'s
   reasoning. It stays in the panel, flagged, as the test of the conversion.
7. **The ex-USD bond file keeps its delivered construction** (local × FRED
   noon spot). Whether the lab moves to one FX source is OWNER-QUEUE L33.
8. **Numbers recorded before today stand.** That covers
   `M-20261003T181155Z`, `huber6-v1`, `huber6-v2` and every audit on real
   data. Task 53 builds `huber6-v3`.

*Rules 5 and 6 and rule 7 were Cowork's proposals (2026-10-10). The owner
said "Update the project accordingly"; his release of task 53 confirms them.*

## The test, before building on it

`NDDLUK` × `GBPUSD` against `NDDUUK`: the same MSCI index, both net of
withholding, one in sterling and one in dollars. The figures are weekly
(Friday closes) *(Cowork's read, Python 3.10 outside the repo's environment;
task 53 reproduces them)*.

| FX for the conversion | Window | Weekly TE | 4-week TE | Lag-1 autocorrelation | Cumulative gap |
|---|---|---|---|---|---|
| none (unconverted) | 1970-2019 | 1,353 bp/yr | | | |
| Bloomberg close, same day | 2002-2019 | 238 bp/yr | 107 bp/yr | −0.51 | −50 bp |
| Bloomberg close, previous day | 1980-2019 | 576 bp/yr | | | |
| Bloomberg close, same day | 2006-2019 | 237 bp/yr | 122 bp/yr | −0.50 | −5 bp |
| FRED noon, same day | 2006-2019 | 141 bp/yr | 66 bp/yr | −0.47 | +10 bp |

- **Same-day is the right alignment.**
- **The residual is fixing time, not bias.** MSCI converts at the 4pm London
  fix and this file is a later close. The residual reverses the next week,
  halves over four weeks and nets to tens of basis points over 14 to 18 years.
- **FRED's noon rate tracks MSCI's conversion better on this pair.** That is
  L33.

## What it does not decide

- **One FX source for everything,** and which one (OWNER-QUEUE L33).
- **A base currency other than USD.**
- **Hedged series** (`decisions/0013`). They remain out.

## SUBSTRATE §5.1, invariant 8 — applied in v0.10 (owner approved 2026-10-10: "i approve the edit to the substrate")

> 8. Returns are in the base currency, USD. A series delivered in another
> currency is converted on the same date with
> `data/raw/bloomberg/bbg_curncy_hist.xlsx` read through an explicit
> quote-convention table, never carried, and a series whose quote currency
> differs from its sheet's is refused unless it is converted
> (`decisions/0053`).
