# 0063 — The Japan government family joins the bond panel: `I29064JP` to `I29068JP`, from 2013

**Status:** decided 2026-10-21 by the owner ("L39: option A"). Drafted by Cowork
on the same day. Settles OWNER-QUEUE L39. Follows `decisions/0060` (a missing
instrument is a data request, not a redesign) and `0057` (curve labels).
No change to `params/`, `vetoes/` or `SUBSTRATE.md`, and no hypothesis file is
edited. Nothing is pulled or loaded by this record: it admits the *request*.

## What the owner said

- 2026-10-15 (`0060`): the Japan government family exists from 2013-01-31 only;
  whether to add it is L39.
- 2026-10-21: he ran ASKB on the Japan tickers and passed on the result (the
  longer histories are yield series, not total-return indices; `I29063JP` still
  does not resolve; `BNJPGVJP` and `LJPNGVJP` were not in the query). Then:
  "L39: option A."

## The decision

1. **Add the 2013 family:** `I29064JP` (1-3y), `I29065JP` (3-5y), `I29066JP`
   (5-10y), `I29067JP` (10-20y), `I29068JP` (20y+). The JPY curve group enters
   the panel in 2013.
2. **Not part of it:** `I29063JP` (all maturities; it does not resolve), and
   the JGB yield series (`JGBS*`, `GJGB*`). Option (d), a JPY return built from
   those yields, is not adopted and is not designed.
3. **The request** is the Japan rows of
   `Claude outputs/bbg_pull_nonusd_govt_2026-10-15.csv`, restated in
   `Claude outputs/bbg_pull_japan_govt_2026-10-21.csv` (both git-ignored):
   daily from 2013-01-31, fields `PX_LAST`, `INDEX_OAD_TSY`,
   `INDEX_YIELD_TO_WORST`, ending **2019-12-31** at the latest. Nothing on or
   after `HOLDOUT_START` (2020-01-01) is pulled.
4. **Disclosed in advance** (the option's own stated cost): `H-2026-0003`'s
   JPY leg is tested mostly on 2013-2019, near the zero bound. A result for
   that leg is read with that sentence beside it. The hypothesis file is not
   amended to say so; the disclosure lives here and in any report that cites
   the leg.
5. **Still open, and not blocked by this record:** the owner's Terminal check
   of `BNJPGVJP` and `LJPNGVJP`. *Cowork's inference:* it was the measurement
   that could have changed (a); the owner has chosen (a) regardless. If it
   later finds daily history before 2001, a longer Japan curve can be proposed
   as its own item.

## What it takes to build, in order

1. **The owner pulls the file** from the request above and saves it under
   `data/raw/bloomberg/`. Cowork cannot pull vendor data.
2. **HANDOFF task 65** describes the file: structure only, no values leave
   the machine (the pattern of task 58).
3. **A later record, written from task 65's structure report,** admits the
   five instruments: labels (`curve` JPY, `rating`, `market`), cost bucket,
   tier, the label-map rows, the `investable_universe` rows, and a rebuilt
   store (`0060`: "a new record admits the instruments"). Its loader is a
   third task.
4. Until then `H-2026-0003`, `0002` and `0010` stay `blocked:data` for the
   JPY leg, as `0060` ruling 2 says.

## What this does not decide

- The labels, cost bucket and tier of the five instruments.
- Whether the store is rebuilt as a new version or extended.
- Anything about `H-2026-0003`'s design.
