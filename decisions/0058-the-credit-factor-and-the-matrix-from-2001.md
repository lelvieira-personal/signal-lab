# 0058 — The exposure matrix covers the whole development window: estimation reads before it, and the credit factor is `BAA10Y`

**Status:** decided 2026-10-11 by the owner (OWNER-QUEUE L35). Drafted by
Cowork. Follows `decisions/0046` §1, `0049`, `0055` and `0056`. **Changes
`params/` later, not here:** the new store's hash is known only after HANDOFF
task 56 builds it, so the params patch is a separate step with its own task.
**SUBSTRATE §5.4 gets new wording** for one FRED spread, approved by the owner
on 2026-10-12 and transcribed with the params change, so the constitution never
describes a store the lab is not reading.

## What the owner said

- **22:10,** on L35: "Is there any work around so we don't lose past data?
  It would be better if we could use pre tech bubble data so this scenario
  can be added".
- **22:25:** "L35: accept recommendation (A)". Cowork's option A: estimation
  may read returns before `dev_start`, and the credit factor moves to one
  series with daily history before 1999; the development window does not
  move.
- **22:39:** "L35: go with FRED. There is no OAS stat for this index in
  bloomberg apparently." That is `BAA10Y`, of the two Cowork offered.
- **Also 22:39,** "4) yes": the label map's hash is pinned in `params/` beside
  the store, with this record's params change.

## Why the store started on 2002-12-27

Two causes, either of which alone would have started it there:
- `scripts/run_measurement.py` cuts the factor frame at `dev_start`. The
  constitution does not ask for that: SUBSTRATE §2 lets an agent read
  everything in `data/` except the holdout.
- The credit factor, `LUACOAS`, is daily from 2001
  (`data/universe/bbg_analytics_coverage.csv`, which gives only the year).
  Before that it is monthly, and month-end observations are not spliced onto
  daily ones (SUBSTRATE §2).

## The ruling

1. **Estimation may read returns and factors before `dev_start`.** The holdout
   lock is unchanged: nothing on or after 2020-01-01.
2. **The development window does not move.** `dev_start` stays 2001-01-05.
   Only 9 of 26 JPMaQS tickers and 52 of 92 investable series are daily by
   1999-01-01, so most hypotheses could not run earlier.
3. **The credit factor is the daily change in FRED `BAA10Y`,** for the whole
   sample, never spliced with `LUACOAS`.
   - `BAA10Y` is Moody's seasoned Baa corporate yield less the 10-year
     constant-maturity Treasury, daily from 1986-01-02 (checked on FRED,
     2026-10-11).
   - **It is not an option-adjusted spread.** Moody's index holds bonds of 20
     years and more (FRED's note on `DBAA`) and the Treasury leg is 10 years,
     so the spread moves partly with the slope of the curve. The real-yield
     and inflation factors, in the same regression, take some of that.
   - The other five factors are unchanged (`0046` §1, `0049` §4).
4. **A `BAA10Y` value is dated by its observation date,** like every
   Bloomberg close the lab reads (owner, 2026-10-11, 23:05: "Yes", to Cowork's
   proposal following his question "Why not just consider the monday FRED
   data as last friday data in the timestamp?").
   - **The fact:** FRED posts a day's value the next business day. Its page
     on 2026-10-11 showed the 2026-10-08 observation posted on 2026-10-09
     (`DBAA` at 10:31 CDT, `BAA10Y` at 16:03 CDT).
   - **Why it is dated by observation anyway:** the value measures Friday's
     market, Moody's Baa yields and the 10-year Treasury at Friday's close.
     The delay is publication, not information from after Friday. The lab
     already decides and trades on the same close it observes, with
     Bloomberg closes (`LUACOAS` among them) that are also computed after
     the close. JPMaQS is dated the same way: SUBSTRATE §5.6 takes "the
     information state as observed by the markets".
   - **A one-day lag would have been an exception for one source.** If the
     spread later serves as a signal, its comparison with Bloomberg spreads
     would then measure the dating rule rather than the signal.
   - **`loaders/fred.py`'s warning still holds for revised series.** It is
     about macro data revised in place after release. *Cowork's
     understanding, not verified:* daily market yields such as these are not
     revised in that sense.
   - **What the lab assumes everywhere:** a decision and a trade on the same
     Friday close. That is optimistic for every series, and the half-spread
     cost model covers it only in part. It is a lab-wide question with its
     own record if it is ever tested, not a rule for one source.
   - **So nothing changes in the map:** `huber6-v4` dates each week by its
     Friday, as `v3` does, and `0055`'s rule stands ("latest week on or
     before `d`, within six days").
5. **A new store, `huber6-v4`,** built once with this record and
   `decisions/0056` together: the four ex-USD bonds converted with Bloomberg's
   close, the new credit factor and estimation before `dev_start`. Same
   estimator as `0049` item 1, unchanged.
6. **The params change, after the build** (owner-only; a later HANDOFF task
   commits it, citing this record):
   - `data.characteristics.store_id: huber6-v4` and its `directory_hash`, as
     task 56 reports it;
   - the label map pinned beside it: its path and its sha256, as task 55
     reports it;
   - `params_version` to `0.11.0` in all seven files.
7. **The 2000 leg of the bubble is a stress scenario,** not part of the
   backtest: a phase-4 replay of 1998-2002 factor moves through a candidate's
   loadings. `BAA10Y` reaches that far; so do the real yield (1997) and the
   dollar and commodities. The equity factor and the breakeven start in 1999.
   Not designed.

## What it does not decide

- **Instruments that begin daily in 2001 or later,** such as `M1EF` and
  `M1USSC`. Each still needs its own 104 valid weeks.
- **The stress scenario's design** (item 7).
- **Whether a credit factor closer to an OAS** is worth a vendor search. The
  owner found no OAS field for the ICE index on Bloomberg.

## SUBSTRATE §5.4 — approved 2026-10-12 ("5.4 wording approved"); transcribed with the params change of item 6

The section's list gains `BAA10Y`, and its last paragraph changes. Now:

> FRED's ICE BofA spread series start 2023-09 and are **not used**. Spreads
> come from Bloomberg.

Proposed:

> FRED's ICE BofA spread series start 2023-09 and are **not used**. Index
> spreads come from Bloomberg. One spread comes from FRED: Moody's seasoned
> Baa yield less the 10-year Treasury (`BAA10Y`, daily from 1986), the credit
> factor of the exposure matrix, dated by its observation like a Bloomberg
> close (`decisions/0058`).

And in the list, after "WTI and Brent": "; `BAA10Y` (see below)".

## What would reopen it

- A daily IG option-adjusted spread with history before 1999.
- The store's first week landing later than 2001-01-05 (task 56 reports it).
