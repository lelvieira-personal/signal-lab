# 0071 -- How the euro linkers' durations are pulled: Excel now, and whether the lab gets its own Bloomberg puller

**Status:** RULED by the owner: option (c) on 2026-11-13; the linkers' duration request closed and `BEIG1T` made a reference series on 2026-11-14 (see the two "Owner ruling" sections). Proposed 2026-11-12 by Cowork (morning review). Moved from `decisions/proposed/` to `decisions/` by Cowork (review, 2026-11-14 afternoon); committed by HANDOFF task 97 step 0.

## Where things stand

- The pull itself is **approved** (`decisions/0068`, owner ruling 2026-11-11): `BEIG1T Index` and `BEIG3T Index` x `INDEX_OAD_TSY` and `MODIFIED_DURATION`, daily, 1999-12-31 to 2019-12-31, trading days only, no fill.
- `0068` says who pulls it is still open: "the lab's own Bloomberg puller (Desktop API from WSL ...) Its decision record is drafted after task 89 lands. The owner may pull it in Excel instead." Task 89 landed on 2026-11-11 (`a631614`, pushed). This is that record.
- Today `params/data_sources.yaml` lists Bloomberg as `kind: file`, `network: false`: the lab reads files you saved under `data/raw/bloomberg/` and calls nothing. Every Bloomberg pull so far (Japan, Ex-USD analytics, the euro/UK bands) was yours, in Excel.
- On 2026-11-11 you turned on WSL mirrored networking and a `ReferenceDataRequest` for `BEIG3T Index` `NAME` returned a response, so the Desktop API is reachable from WSL (what `0068` records; Cowork has not re-checked it).

## Options

- **(a) Excel, now, as before.** You pull the four series with `BDH` into one workbook, save it under `data/raw/bloomberg/` (suggested name `bbg_euro_linkers_duration.xlsx`, long layout `date, ticker, field, value`, or wide: say which), and a Cowork-written task describes it and loads it into store `huber6-v7`. *For:* no change to `params/` or the vendor-data rule; the path every earlier pull took; about ten minutes of your time. *Against:* every future pull costs your time, and the request, the sheet layout and the description are re-done by hand each time.
- **(b) The lab's own puller, built now, used for this pull.** A script (`scripts/bbg_pull.py`) on `blpapi` against the Desktop API (`localhost:8194`), with: (1) Bloomberg moved to `kind: sdk` in `params/data_sources.yaml`, host `localhost` only, `network: localhost`; (2) it pulls only from a request file you approved, named in a decision record (tickers, fields, dates, no override, no fill); (3) it writes only under `data/raw/bloomberg/` plus a manifest row (request id, time, row counts, a hash), never prints a value, and never runs in the nightly worker (interactive, on your session, `scripts/nightly/` deny list unchanged); (4) a dry-run mode that checks the request against the allowlist and prints only counts. *For:* reproducible pulls, the request is the record. *Against:* a code path that touches vendor data and a change to an owner-only file before the data it unblocks; a bug here sits on the vendor-data rule; Bloomberg's Desktop API terms bind the data to your licensed terminal use, which this keeps (nothing leaves the machine), but **Cowork has not read the terms for this use: a guess, for you to confirm.**
- **(c) Both: (a) for this pull, (b) built later** as its own task after the M6 grid, first used on the next pull, and checked then by pulling one series both ways and comparing the counts and the hash of the values on the laptop (no value printed).

**Cowork recommends (c).** The linkers' measured duration is the only thing waiting, and (a) gets it in minutes with no change to the rules. A puller is worth having, since the M4/M7 work will want more fields, but it should be built and reviewed without a dataset waiting on it, and its first use should be a pull that can be checked against an Excel copy.

## Questions for the owner

1. (a), (b) or (c)?
2. If (a) or (c): the file name and layout above, or yours? Cowork then writes the load-and-store task (`huber6-v7`, the linkers' measured cell; which of the two fields the duration axis reads for the linkers is put to you with that task, as `0068` says).
3. If (b) or (c): do you approve the guardrails (1) to (4) as the shape of the `data_sources.yaml` change? The exact patch would come to you as a draft before any build.

## Owner ruling, 2026-11-13

Owner, chat, 19:41 ET: "Agree with all recommendations from the digest" (the weekly digest of 2026-11-13, section 1 item 1, which recommends (c)). Recorded by Cowork, not answered by it.

1. **Option (c).** The owner pulls the four series in Excel now. The lab's own `blpapi` puller is built later, as its own task after the M6 grid, and its first use is checked against an Excel copy (counts and a hash of the values, no value printed).
2. **File and layout:** `data/raw/bloomberg/bbg_euro_linkers_duration.xlsx`, long layout `date, ticker, field, value`, as suggested above. *The layout is Cowork's reading of "agree" (the record offered long first and asked the owner to say which); if the sheet arrives wide, the load task reads it wide.*
3. **Guardrails (1) to (4)** of option (b) are approved as the shape of the later `params/data_sources.yaml` change. The exact patch still comes to the owner as a draft before any build (it is an owner-only file).

Next: the owner's Excel pull; then Cowork writes the load-and-store task (`huber6-v7`), which puts to the owner which field the linkers' duration axis reads (`0068`).

## The Excel pull, 2026-11-14 (owner, through Claude in Excel; notes sheet as reported in chat, counts and dates only)

BDH `Per=D, Days=T, Fill=B`, no overrides, 11:31 ET.
- `INDEX_OAD_TSY`: **no value on any date**, both tickers (dates returned, every value empty).
- `MODIFIED_DURATION`: `BEIG1T` 858 rows, 2017-01-01 to 2019-12-31, no gap over 5 weekdays; `BEIG3T` 513 rows, 2017-08-17 to 2019-12-31, one gap 2017-08-29 to 2018-02-06. Nothing on or before 2016-12-31.
- `Days=T` still returned weekend dates (80 rows `BEIG1T`, 11 `BEIG3T`), kept as returned.
- `BDP NAME` returned the bare ticker (`BEIG1T`, `BEIG3T`); `CRNCY` EUR for both.

**Reading (Cowork):** the approved pull does not deliver a measured duration for the development window: at most 3 of 19 years, on one field whose meaning for a linker `0068` left unverified. The load task is not written until the owner decides what to do with this (a field probe first is Cowork's suggestion in chat, 2026-11-14).

## ASKB, 2026-11-14 11:42 ET (owner's query; ASKB's claims, not verified by Cowork)

- `BEIG1T Index` is Bloomberg Euro Govt Inflation-Linked Bond **All Maturities** TR. `BEIG3T` not identified ("likely a maturity band").
- `INDEX_OAD_TSY` holds OAS constant and shocks the **nominal** government curve; Bloomberg has no index-level real-duration field. Real-yield duration exists only per bond (`INFLATION_ADJ_DUR_MID`).
- No duration history before about 2017 for either ticker, under any field it tried (the Barclays-to-Bloomberg transition).
- Candidates with longer history: ICE BofA `EG0I Index` (entitlement through IND), iBoxx EUR Inflation-Linked (separate entitlement).

**Cowork's flags.** (1) ASKB explains the empty `INDEX_OAD_TSY` as the 2017 start, but the pull found it empty on 2017 to 2019 too, so that explanation does not fit. (2) If `BEIG1T` is the all-maturities index and `BEIG3T` one of its bands, `0068` point 2's rule (an aggregate and its own band are not both held) would apply to them; `0068` admitted both as investable. Unconfirmed until `BEIG3T` is identified. (3) ASKB's "nominal curve" reading conflicts with the owner's L30 answer of 2026-10-10 that `INDEX_OAD_TSY` on `LBUTTRUU` is real-rate duration, which the TIPS measured cell relies on. To be put on OWNER-QUEUE by the next review.

## The probe, 2026-11-14 11:54 ET (owner, through Claude in Excel; coverage only)

- **`EG0I Index`** (ICE BofA Euro Inflation-Linked Government) resolves, but no duration field returned a value 1999-12-31 to 2019-12-31: nine "Field Not Applicable", four invalid fields, and `DURATION` an authorization error (ICE analytics not entitled, Cowork's reading).
- **`BEIG3T Index`** is `INDX_DES` "Bloomberg Euro Govt inflation-linked ILB 1 to 10 Year TR": the 1-10y band of `BEIG1T` (All Maturities). Family fields disagree (`BEIG3T` "Bloomberg B-Series Benchmark", `BEIG1T` "Bloomberg Emerging Market Bond Indices"); the second looks like a Bloomberg metadata error (a guess).
- **`LBUTTRUU` `INDEX_OAD_TSY`:** FLDS (owner's screenshot) shocks "the par yield curve" with OAS held constant; the header shows YTW 5.21 with `CHARACTERISTICS_SOURCE_OVERRIDE` = PROJECTED, against a 10y TIPS real yield near 2.66% (FRED-derived press, 2026-11-09). Cowork's reading: projected nominal cash flows on the nominal curve, inflation held fixed, which is a real-yield shock in effect, read a little short. The TIPS measured cell stands; flag (3) above is downgraded to this note.

**Cowork's reading:** no source on the terminal gives the euro linkers a measured duration for 2001 to 2016. Two questions go to the owner (chat, 2026-11-14): whether `BEIG1T` becomes a reference series under `0068` point 2's reasoning, and whether the linker-duration request is closed with the EUR leg left blocked.

## Owner ruling, 2026-11-14 (chat, 12:04 ET: "1 yes, 2 yes", on Cowork's two questions at 11:54 ET). Recorded by Cowork.

1. **`BEIG1T` becomes a reference series** (in the store, `investable` False, never held), on `0068` point 2's reasoning: it is the all-maturities aggregate of which `BEIG3T` (1-10y) is a band. `BEIG3T` stays investable and is the euro linker the lab holds (curve `EUR_real`). It lands in the next store version and params pin, not a store of its own; until then the current store holds both as investable.
2. **The linkers' duration request is closed.** No terminal source gives a measured duration for 2001 to 2016 (Bloomberg from 2017 only; ICE analytics not entitled). The 2026-11-14 Excel file is kept under `data/raw/bloomberg/` as the record of the pull and is not loaded. **H-2026-0002's EUR leg stays `blocked:data`** (`0068`, ruling of 2026-11-11); its USD leg is unaffected. Store `huber6-v7` and its load task are not written. The puller of option (c) is still built later, as ruled on 2026-11-13.

**For the next review:** move this record to `decisions/0071-...` and commit it; add to `decisions/0070` the owner's (i) on the prefill and to `OWNER-QUEUE.md` the spend-cap "no change" (weekly digest of 2026-11-13, owner response); note in `0068` that ruling 1 above applies its point 2 to the linkers; carry the `BEIG1T` change into the next store task.

## What it would move

Nothing until the pull lands. Then: store `huber6-v7` (a pin under `0069` item 6), the euro linkers' duration cell (estimated to measured), H-2026-0002's EUR leg leaving `blocked:data`. Option (b) also changes `params/data_sources.yaml`.
