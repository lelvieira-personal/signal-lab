# 0013 — The investable universe, and what the characteristic map is for

Status: partly decided, 2026-09-09. Supersedes the `index_etf_map.csv`
requirement in SUBSTRATE section 5.1 for v0.3.

## The universe

SUBSTRATE section 5.1 refers to an owner-maintained
`data/universe/index_etf_map.csv`. The owner reframed this, and the reframing is
better:

> "I believe that we can infer this from the dataset … All of the indices that
> track a long-only market, regional, sector, style, credit bucket, duration
> bucket, local currency bonds or hedged to USD bonds are potential candidates
> … I can worry about the specific ETF to implement later when a leading
> candidate model proves this is time well spent."

So the universe is the set of indices that *could* be implemented; ETF selection
is deferred to one candidate model in phase 4. What is needed now is not a
ticker-to-ETF map but two columns on the coverage table — `investable` and
`cost_bucket` — plus the `reporting_class` column below.

**Universe size versus holdings.** These are different. SUBSTRATE section 4 caps
*holdings* at 30 non-zero, which matches the owner's "20–35 line items to
discuss with investors". The universe should be considerably larger, because the
optimiser needs candidates to select among.

## Resolved: hedged series are out (2026-09-09, Leo)

> "Let's leave the hedged series out. I believe we already have more than enough
> levers to use and create a strong diversified exposure with what we have."

The six hedged series carry `investable: false` in
`data/universe/investable_universe.csv`. They keep a `reporting_class` so the
counterfactual can still be reported when phase 2 computes it. 96 of 102 series
are investable.

### The argument, retained



The owner listed "hedged to USD bonds" as candidates. SUBSTRATE section 4 says
hedged series are "the counterfactual, not a separate live axis in v0.3", and
section 5.1.6 says they are not mixed with unhedged peers in a region signal.

If both the hedged and the unhedged version of the same exposure are selectable,
the optimiser expresses an FX view by choosing between them, which is a live FX
axis by the back door. Either the six hedged series are excluded from
`investable`, or section 4 changes.

Conservative option taken: **excluded**, pending the owner's answer.

## Resolved: the sector series are total return (2026-09-09, Leo)

The owner checked `MXUS0EN` directly and confirms it returns
`INDEX_TOTAL_RETURN_GROSS_DVD` values. The `likely_price_only` column in
`bbg_index_coverage.csv` is a false positive from the coverage script's
heuristic, not a property of the pulled data. No re-pull is needed and the
sector axis is intact.

The column should be dropped or renamed when the coverage table is next rebuilt,
so it does not mislead a future reader the way it misled this one.

### The original concern, retained



`data/universe/bbg_index_coverage.csv` carries a `likely_price_only` column
flagging 29 of 97 series, including all 11 US MSCI sectors and all 11 European
MSCI sectors. The owner reports pulling with `TOT_RETURN_INDEX_GROSS_DVDS`,
which Bloomberg computes even for a price-index ticker — so the flag is probably
a false positive from a naming heuristic.

It is not certain: the flag is not purely name-based (1 of 3 US region series
and 2 of 7 developed ex-US are flagged, from the same ticker families), so
something discriminated among them and it is not known what.

**Decisive test:** pull `PX_LAST` for one flagged ticker over the same window
and compare against the column in `TR Levels`. Identical means Bloomberg had no
dividend data and the field returned the price index. The phase 2 loader will
settle it as a by-product, and unlike an ad-hoc read of the raw workbook it
truncates at `HOLDOUT_START`.

If the flag is real, it corrupts the sector axis rather than blocking it: a
price index understates return by its dividend yield, so the optimiser would
systematically avoid sectors for a reason unrelated to any signal. That would
make it the highest-priority data request in the lab.

## The characteristic map — two objects, one file

The owner asked whether the characteristic map is "only for aggregation
purposes and not for quantitative estimation or optimization". It is not: per
section 6, views are formed in exposure space and *"mapped to ETF weights by
solving for the long-only portfolio whose exposures best match the view"*. The
map is the matrix in that solve. A wrong duration number changes the weights,
not just a label.

Three distinct things now live in `data/characteristics/`, and keeping them
distinct is the point:

1. **The exposure matrix** — duration, credit, region, sector, style,
   real/nominal, cash. Definitional and economically named, mostly a lookup plus
   two columns lifted from the analytics panel (OAD, OAS). Load-bearing in the
   optimiser.
2. **Factor loadings** — statistical, quasi-orthogonal, estimated from returns,
   used to extend covariance backward for short-history series (section 5.2).
   Built by the harness in phase 2.
3. **`reporting_class`** — the bank's asset-class taxonomy (Cash, Treasuries,
   Long Treasuries, US IG, US HY, US Equities, European Equities, …), requested
   by the owner for reporting final results. **Explicitly excluded from the
   exposure matrix** so it can never leak into the solve.

## Open: what is an equity index's duration exposure?

Definitionally zero, or its empirically estimated rate beta? Zero keeps the map
definitional and makes "duration" mean bond duration. A rate beta is more honest
— equities do respond to rates — but then the exposure matrix is partly a
statistical estimate and stops being a lookup. This changes weights and should
be decided rather than defaulted. The same question applies to credit exposure
on high-yield-adjacent equity sectors.

No conservative default is available here, so nothing is implemented until the
owner answers.

---
## Reporting classes (2026-09-09, Leo)

The taxonomy supplied by the owner, implemented as the `reporting_class` column
of `data/universe/investable_universe.csv`, built by `scripts/build_universe.py`
from an explicit per-ticker lookup rather than a name heuristic:

Cash · Treasuries · Long Treasuries · TIPS · MBS · Ex-USD Bonds · IG Corporates ·
HY Corporates · EM Sovereign Bonds · EM Corporate Bonds · US Equities ·
European Equities · Japanese Equities · APAC ex-Japan Equities · EM Equities ·
Commodities · Gold

### Two classes added to reach full coverage — confirm or change

Seventeen classes leave **17 of 102 series** with no home. Rather than force
them somewhere misleading, two classes were added:

- **DM ex-US Equities** (13 series) — `MXCA` (Canada, which is not US, European,
  Japanese, APAC ex-Japan or EM), the six EAFE factor/style series and the six
  World-ex-US factor/style series. EAFE and World-ex-US span several regions by
  construction, so no single regional class fits them.
- **Real Assets** (4 series) — `M2WDCOMP` (ACWI Commodity Producers), `SPGNRUT`
  (Global Natural Resources), `FGCIICUT` (Global Core Infrastructure), `ENXG`
  (Global REITs). These are listed **equities**, not commodities. Reporting
  8% in "Commodities" when the holding is listed infrastructure would mislead
  an investor, which is the one thing a reporting class must not do.

Change either by editing `REPORTING_CLASSES` and `REPORTING` in
`scripts/build_universe.py` and re-running it.

### Three assignments that are approximations, flagged rather than hidden

- `SPBDALB` (Morningstar LSTA US Leveraged Loans) → **HY Corporates**. Loans are
  senior secured and floating rate; they are not high yield corporates. The
  taxonomy has no loan class and this is the nearest.
- `EMUSTRUU` (EM USD Aggregate) → **EM Sovereign Bonds**. The index contains
  both sovereign and corporate issuers; the split is not available at index
  level.
- Sector and style series roll up into their regional equity class, so
  `reporting_class` cannot distinguish a sector tilt from a market position.
  That is the intended behaviour — the tilt lives in the exposure matrix, the
  rollup is what the investor sees — but it is worth stating.

### Cost buckets

Assigned per SUBSTRATE section 8, read literally. `low` is "Treasuries, T-bills,
US large-cap equity" and nothing else, so US mid- and small-cap sit in `mid`,
and MBS sits in `mid` rather than `low` because section 8 does not name it. The
dear bucket applies wherever the text is not clear, per decisions/0002.
