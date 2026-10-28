# 0066 — Admitting the Japan government family: labels, cost bucket, tier and when the store is rebuilt

**Status:** PROPOSED by Cowork, 2026-10-23, at the owner's "yes" in chat. **RULED by the owner on 2026-10-23 (see the last paragraph).** Settles the
four things `decisions/0063` left open (its "What this does not decide"). No change to `params/`, `vetoes/` or
`SUBSTRATE.md` is made by this record; the owner-only patch that follows it is described at the end and written
only after the rulings. Follows `0053`, `0054`, `0056`, `0057`, `0060`, `0063`.

Everything marked **guess** is Cowork's, not a measurement. The proposals copy what the lab already did for the
nearest instruments; they are not derived from Japanese data, which Cowork has not opened (structure only,
task 65).

## What is already settled

- The five instruments are admitted as a *request* (`0063`): `I29064JP` 1-3y, `I29065JP` 3-5y, `I29066JP` 5-10y,
  `I29067JP` 10-20y, `I29068JP` 20y+. The file is on disk: levels 1,789 dated rows
  (2013-01-31 to 2019-12-31, nothing on or after the holdout), an analytics sheet in long form
  (`date, ticker, index_name, oad_tsy, yield_to_worst`), and a Pull Report. Task 65, structure only.
- The levels are **local JPY** (`I2906xJP_local_JPY`). `0053` and `0056` already rule what happens: converted to
  dollars by the loader with Bloomberg spot, the JPY quote being Reference-Curncy-per-USD. **Nothing new to
  decide here.** Cowork has not checked that `bbg_curncy_hist.xlsx` holds a JPY column on every one of the
  1,788 dates; the loader task must report any date it cannot convert, not carry a rate.

## What the nearest instruments look like today

From `data/universe/label_map.csv` and `investable_universe.csv` at HEAD:

| Ticker | Region | `curve` | `rating` | `market` | Cost bucket | Tier | Source file |
|---|---|---|---|---|---|---|---|
| `I02913JP` (Japan Aggregate) | Japan | JPY | Aggregate | DM | mid | blank | `bbg_exusd_bonds_coverage.csv` |
| `I12823GB` (UK Gilt 1-10y) | Developed Europe | GBP | Government | DM | mid | blank | same |
| `LET1TREU` (Euro Treasury 1-3y) | Developed Europe | EUR | Government | DM | mid | blank | same |

All of them: `asset_group` bond, `reporting_class` Ex-USD Bonds, `region_view` no, `hy_bucket` blank. Every
ex-USD bond in the universe is `mid`; none is `low` or `high` (counted from the table, 12 rows).

## The four points

**1. Labels.** *Proposal:* the five rows copy the Gilt and Euro Treasury pattern, with Japan's own region:
`asset_group` bond; `reporting_class` Ex-USD Bonds; `region` Japan; `region_view` no; `curve_currency` JPY;
`rating_class` Government; `market_label` DM; `curve` JPY; `rating` Government; `hy_bucket` blank; `market` DM.
- *Effect on `0057` scopes:* `curve: [JPY]` now reaches six instruments (the five and `I02913JP`);
  `rating: [Government]` gains five. Whether a Government-only JPY scope should exclude the Aggregate is
  automatic: it matches `Aggregate`, not `Government`.
- *No maturity label.* The label map has no maturity column and `0057` defines none. The five bands differ in
  duration, and the duration axis reads each instrument's **measured OAD** (`oad_tsy`, the analytics sheet), so
  the bands separate on the axis without a label. Cowork has not checked the loader reads `oad_tsy` for these
  five the way it does for the others; the task must.
- *Alternative:* label the maturity band as a new column. Not proposed: it adds a vocabulary no hypothesis
  asks for.

**2. Cost bucket.** *Proposal:* `mid` for all five, as every ex-USD government bond today. **Guess:** the
20y+ band may deserve `high` on spread width; the repo holds no bid-ask evidence for it, and Cowork will not
invent one. If you want it `high`, say so; otherwise the lab prices it as `mid` and a later cost study can move it.

**3. Tier.** *Proposal:* blank, as the three nearest bonds that came from the same kind of pull. **Guess on what
blank means:** Cowork reads it as "not assigned a backbone/second tier because it came from the ex-USD bonds
pull", not as a downgrade. The record that created that pull's tiers (`0052`/`0054`) should be checked by
whoever reads this; Cowork has not re-read it for this point.

**4. When the store is rebuilt.** This is the real decision, because it touches `params/`.
- *Fact:* the label map is **pinned by sha256 in `params/`** (task 60), and the store name `huber6-v4` is named
  there too. Five new label-map rows change the hash; five new instruments need a store that has them. Both are
  owner-only patches (`params/`), citing a record.
- *Precedent:* `0056` held its build until it could land "one new store and one new params version, not two".
- *What else is waiting for the same rebuild:* `0060`'s data request also lists Euro Treasury bands
  (`LEATTREU`, `LET3TREU`, `LET5TREU`, `LET7TREU`, `LET0TREU`), UK Gilt bands (`LSG1TRGU`, `I08043GB`-`I08048GB`)
  and the euro linkers (`BEIG1T`, `BEIG3T`). Cowork does not know whether you have pulled any of them (it has
  not listed `data/raw/`); the board shows no task for them.
- **Option (a): rebuild now** as a new store (`huber6-v5`) and params version for the Japan five only.
  Pro: H-2026-0003's JPY leg (and 0002/0010) stop being `blocked:data` as soon as it lands. Con: a second
  rebuild later when the Euro and UK bands arrive; each rebuild moves a pin and every recorded number that
  reads the store has to be re-read against it (*Cowork's reading, not measured*).
- **Option (b): batch.** Hold the Japan admission until the Euro and UK bands are pulled and described, then
  admit all of them in one record, one store, one params version. Pro: one rebuild. Con: Japan waits on pulls
  that may not exist yet.
- **Cowork recommends (a), weakly.** Reason: the solver build (tasks 69-71) does not need Japan, so nothing
  downstream is stalled by (b) either; the case for (a) is only that it retires a ruled item (L39) sooner. If the
  Euro and UK pulls are close, (b) is the better engineering. **The deciding fact is yours: have you pulled
  them, or will you within about a week?**

## What follows the rulings

1. Cowork finalises this record as `decisions/0066-...` (a direct, records-only commit).
2. Cowork writes the **owner-only patch**: five rows in `data/universe/label_map.csv` and
   `investable_universe.csv` (not owner-only paths), and the new label-map hash and store name in
   `params/*.yaml` with `params_version` (owner-only, citing 0066; you apply or release it).
3. A loader/admission **task** (lane 2, no push): read the long-format analytics sheet and the levels sheet,
   convert to dollars per `0053`/`0056`, add the instruments to the panel, rebuild the store, report counts and
   any date lost to conversion, and run `check-full`. Opus is not needed; the rules are written.
4. L39 closes when that task lands, and the board's M3 moves to done.

## Questions for the owner, in order

1. Points 1-3: **accept the proposals as written**, or change which?
2. Point 4: **(a) rebuild now, or (b) batch with the Euro/UK bands**, and have you pulled those?

---

**Owner ruling, 2026-10-23 (chat, recorded by Cowork):** points 1-3 accepted as written; point 4: (a) rebuild the store now. The owner-only patch and the loader/rebuild task are not yet written.

**Owner ruling, 2026-10-26 (chat, recorded by Cowork):** the owner confirmed the 2026-10-23 ruling: points 1-3 accepted as written; point 4: (a) rebuild now. **Finalised by Cowork on 2026-10-26** (records-only step: moved from `decisions/proposed/` to `decisions/` so the commit hook finds it; the text above is unchanged). Status: DECIDED.

**Owner ruling, 2026-10-28 (chat, recorded by Cowork): point 3, what a blank tier means.** The proposal under point 3 guessed that a blank tier meant "not assigned because it came from the ex-USD pull". That guess was wrong. The loader reads a blank tier as "derive it from the true daily start" (`bloomberg._tier_from_start`), and a 2013 start makes all five instruments **tradable-only** (SUBSTRATE section 5.2). They therefore get no estimated loadings and are never used to estimate a signal. Cowork put this consequence to the owner. **The owner accepted tradable-only for the five.** Nothing in `params/` or `SUBSTRATE.md` changes. The owner also authorised Cowork to release HANDOFF task 77 (the owner-only params patch that pins `huber6-v5`, `push=yes`) once task 76's receipt gives the store's directory hash.
