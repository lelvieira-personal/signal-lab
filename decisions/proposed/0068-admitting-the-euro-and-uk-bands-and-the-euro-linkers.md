# 0068 — Admitting the Euro Treasury and UK Gilt bands and the euro linkers: labels, the aggregates, cost, tier and the rebuild

**Status:** PROPOSED by Cowork, 2026-11-03, at the owner's "i agree with all suggestions" in chat (the suggestion was to draft this record). Not ruled. No change to `params/`, `vetoes/` or `SUBSTRATE.md` is made by this record; the owner-only patch that follows it is described at the end and written only after the rulings. Follows `0053`, `0054`, `0056`, `0057`, `0060`, `0066`; same shape as `0066`.

Everything marked **guess** is Cowork's, not a measurement. Cowork has not opened the file (structure only, HANDOFF task 58).

## Why now

`0060` ruled that H-2026-0002, H-2026-0003 and H-2026-0010 form their cross-section by curve and are `blocked:data` until these instruments land ("a missing instrument is a data request, not a redesign"). The pull was made on 2026-10-15 and described on 2026-10-16 (task 58, `bbg_exusd_bonds_extra.xlsx`), and then nothing admitted it: no record, no label-map or universe rows, no store, no queue item. `0066` (2026-10-23) said Cowork did not know whether the file had been pulled; it had been. This record closes that gap. The Japan family (`0066`, store `huber6-v5`) is done.

## What is already on disk (task 58, structure only)

- `levels`: 15 columns after `date`, all `_local_<CCY>`: `LEATTREU`, `LET3TREU`, `LET5TREU`, `LET7TREU`, `LET0TREU` (EUR); `LSG1TRGU`, `I08043GB` to `I08048GB` (GBP); `BEIG1T`, `BEIG3T` (EUR). The date column runs 1990-01-01 to 2019-12-31; each series' own start is not known yet.
- `analytics`: long form (`date, ticker, index_name, oad_tsy, yield_to_worst, oas, oas_field`), the 12 nominal tickers only, from 1998-06-30. `analytics_wide` duplicates it.
- `linker_fields`: the FLDS test for the two linkers' real-duration and real-yield fields. Its contents were not read.
- `Pull Report`: per ticker and field, `first_unbroken_daily_run_start` (task 58 saw only its range across 55 rows, 1998-07-31 to 2015-06-12).
- Nothing on or after 2020-01-01. Levels are local currency, so `0053`/`0056` already rule the conversion (Bloomberg's close, EUR and GBP). Nothing new to decide there.

## The points

**1. Labels.** *Proposal:* the twelve nominal rows copy `LET1TREU` and `I12823GB` (`asset_group` bond, `reporting_class` Ex-USD Bonds, `region` Developed Europe, `region_view` no, `curve_currency` and `curve` EUR or GBP, `rating_class` and `rating` Government, `hy_bucket` blank, `market_label` and `market` DM). The two linkers copy `LBUTTRUU`: `curve_currency` "EUR real", `rating_class` "Government, inflation-linked", `curve` **`EUR_real`**, `rating` Government. `0060`'s reading for H-2026-0002 (a linker and its nominal sit in one currency group) is a mapping in the build, as it already is for `USD_real`. No maturity label: the bands separate on the duration axis through their measured `oad_tsy`, as `0066` point 1 ruled for Japan.

**2. The two all-maturities aggregates and the held bands.** This is the point that is new. `LEATTREU` and `LSG1TRGU` are the whole curve of which the bands are the parts, and the lab already holds `LET1TREU` (Euro 1-3y) and `I12823GB` (Gilt 1-10y), which overlap the bands. `0060` ruling 1 (addendum 2026-11-03) kept `LF98TRUU` out of the HY cross-section because an index and its own components double-count.
- *(a)* admit the aggregates as instruments, but they form no group in any curve-band cross-section (the `LF98TRUU` rule, applied by the build);
- *(b)* admit them as reference series only (in the store, not investable), so they can feed a signal or a check but are never held;
- *(c)* leave them out.
- **Cowork recommends (b)**, weakly. The bands span the curve, so holding the aggregate adds a duplicate the solver can trade against its own parts. **Guess:** the euro band boundaries are 1-3, 3-5, 5-7, 7-10 and 10y+, so `LET1TREU` is the first band of the same family and stays as it is. Cowork has not confirmed the boundaries; the loader task reports each index name.
- `I12823GB` (Gilt 1-10y) overlaps the six Gilt bands. *Proposal:* keep it, unchanged, and let the solver see the overlap (no ruling asks to remove a held instrument). Say if you would rather retire it.

**3. Cost bucket.** *Proposal:* `mid` for all fourteen, as every ex-USD government bond today. **Guess:** the longest bands and the linkers may deserve `high`; the repo has no bid-ask evidence, and Cowork will not invent one.

**4. Tier.** *Proposal:* blank, so the loader derives it from each true daily start (`_tier_from_start`, the 2026-10-28 ruling under `0066`): on or before 2001-12-31 backbone, 2002 to 2009 second, 2010 on tradable-only. From `0060`'s ASKB notes (not measured): Gilts 1999-01-29 and linkers 2000-01-03 would be backbone; the euro bands, "about 2002", sit on the backbone/second boundary. The loader's report decides; Cowork flags it because a second-tier euro curve changes what 0002 and 0003 can estimate on.

**5. The linkers' real duration.** H-2026-0002 matches duration across a linker and its nominal (`0060`, the data request). If `linker_fields` shows the real-duration field returned numbers, the loader reads it; if not, the linkers carry no duration loading and 0002's EUR leg cannot match. *Proposal:* the loader task reports, as counts only, how many dates each of the linker fields is numeric, and this record's ruling on the linkers waits for that count if it is zero.

**6. When the store is rebuilt.** One new store (`huber6-v6`) and one params version (the label-map hash and the store name in `params/`), owner-only, after the rulings. Nothing else is waiting for a rebuild today.

## What follows the rulings

1. Cowork finalises this record as `decisions/0068-...` (records-only).
2. A lane-2 task (no push): the loader for `bbg_exusd_bonds_extra.xlsx` (levels and long analytics, dollars per `0053`/`0056`), the label-map and universe rows from the generators, a per-ticker report like task 79's (true daily start, tier, rows before the holdout, dates lost to conversion, index name, linker-field numeric counts), the store build, `check-full`.
3. The owner-only params patch naming `huber6-v6` and the new label-map hash, released by the owner with a push, as tasks 60, 74 and 77.
4. H-2026-0002, 0003 and 0010 leave `blocked:data` for EUR and GBP.

## Questions for the owner, in order

1. Point 1 (labels, `EUR_real` for the linkers): accept as written?
2. Point 2: the aggregates (a), (b) or (c); and keep `I12823GB`?
3. Points 3 and 4: accept `mid` and the derived tier?
4. Point 5: accept that the linkers wait on the field count if it is zero?
