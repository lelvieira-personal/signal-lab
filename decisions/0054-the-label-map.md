# 0054 — The label map: seven regions, and what a bond is labelled by

**Status:** decided in part on 2026-10-10 and 2026-10-11 by the owner
(OWNER-QUEUE L28 and L29). Drafted by Cowork. Follows `decisions/0050` (the
label block) and `0022` (region labels were placeholders). No change to
`SUBSTRATE.md`, `params/` or `vetoes/`. **Not built:** this record writes no
file under `data/universe/`. A later task writes
`data/universe/label_map.csv` from it.

## What the owner said

**2026-10-10:** the regions are US, Developed Europe, Japan, APAC ex-Japan,
EM and Global; gold and commodities are "its own Commodities bucket" with no
region; a sector or style index carries its parent's region; sector and
style labels wait until a hypothesis targets them.

**2026-10-11,** to the five questions of Cowork's draft (Project doc
`claude/label-map-draft-2026-10-11.md`):

| Question | The owner's answer |
|---|---|
| Does a region view reach bonds? | "it is important for hypotheses to ditinguish the currency for bonds in terms of the yield curve currency that the bond is associated to. Also important the rating class and whether is developed or emerging market." |
| Twelve composites that span several regions, drafted as Global | "ok. They are themselves a regional bet" |
| Canada (`MXCA`) fits none of the six regions | "ok, add it as standalone region" |
| Korea, Taiwan, China and India as EM | "yes, EM is fine" |
| The eight tradable-only instruments stay unholdable in the development window | "ok" |

**2026-10-11, later,** to the two readings Cowork put back to him: "yes" to
the region view axis reading equities only, and "yes" to Global being its
own line in the region exposure report with no Global view formed. On the
bond labels: "will do later".

## The ruling

1. **Seven regions:** US, Developed Europe, Japan, APAC ex-Japan, Canada, EM
   and Global.
2. **Each equity instrument's region** is in the table below. A sector or
   style index carries its parent's region.
3. **Global means the index spans more than one region.** The twelve EAFE,
   World ex USA and ACWI ex USA style indices are Global, and so are the four
   global real-asset equity indices. No registered hypothesis forms a Global
   view, so they receive no region view today.
4. **Korea, Taiwan, China and India are EM,** following MSCI's
   classification. APAC ex-Japan is then `NDDUPXJ` alone, which holds
   developed markets.
5. **`BCOMTR` and `BCOMGCTR` are the Commodities bucket** and carry no
   region.
6. **A bond is labelled by three things:** the currency of the yield curve
   it is priced off, its rating class, and whether its market is developed
   or emerging. The draft of those labels is below and is not yet corrected.
7. **The eight tradable-only instruments have no row and are not holdable in
   the development window.** Their parents are chosen in phase 4, when one
   candidate is implemented in ETFs. This closes OWNER-QUEUE L29. Cowork's
   draft parents are kept at the end as a starting point, not a ruling.
8. **Sector and style labels wait** (owner, 2026-10-10).
9. **The region view axis reads equities only.** That is the 61 equity
   indices and the four real-asset equity indices of the table below. A bond
   keeps a region for reporting and receives no region view.
10. **Global is its own line in the region exposure report,** so a book that
    holds EAFE against the US shows it. No Global view is formed.

### Equity regions

| Region | Instruments | Tickers |
|---|---|---|
| US | 20 | `M1CXNNA`, `M1US000G`, `M1US000V`, `M1USMMT`, `M1USMVOL`, `M1USQU`, `M1USSC`, `MXUS0CD`, `MXUS0CS`, `MXUS0EN`, `MXUS0FN`, `MXUS0HC`, `MXUS0IN`, `MXUS0IT`, `MXUS0MT`, `MXUS0RE`, `MXUS0TC`, `MXUS0UT`, `MXUSMC`, `SPXT` |
| Developed Europe | 13 | `MXEU0CD`, `MXEU0CS`, `MXEU0EN`, `MXEU0FN`, `MXEU0HC`, `MXEU0IN`, `MXEU0IT`, `MXEU0MT`, `MXEU0RL`, `MXEU0TC`, `MXEU0UT`, `MXEUG`, `NDDUUK` |
| Japan | 1 | `NDDUJN` |
| APAC ex-Japan | 1 | `NDDUPXJ` |
| Canada | 1 | `MXCA` |
| EM | 13 | `M1CXBRV`, `M1EF`, `M1EF000G`, `M1EF000V`, `M1EFHDY`, `M1EFMMT`, `M1EFMVOL`, `M1EFQU`, `MXCN`, `MXIN`, `MXKR`, `MXLA`, `TAMSCI` |
| Global | 16 | `M1CXVRSD`, `M1EA000G`, `M1EA000V`, `M1EAHDVD`, `M1EAMM`, `M1EAMVOL`, `M1EAQU`, `M1WDU00G`, `M1WDUMMT`, `M1WDUQU`, `M1WOUDY`, `NDUVWXUS`, `ENXG`, `FGCIICUT`, `M2WDCOMP`, `SPGNRUT` |

65 instruments: 61 equity indices and the four real-asset equity indices
(`ENXG`, `FGCIICUT`, `M2WDCOMP`, `SPGNRUT`). Eight are tradable-only (item 7).

## What is not ruled

- **The bond labels themselves,** below. Every entry is Cowork's. The
  owner corrects them later ("will do later", 2026-10-11).
- **How a hypothesis uses a bond label.** SUBSTRATE §6 has seven view axes
  and none is a curve currency or a rating class. A duration view on the
  euro curve only, or a credit view on HY only, needs either a new axis or a
  qualifier on an existing one. Not designed, and it would amend SUBSTRATE.

## The draft bond labels — NOT ruled

| Ticker | Name | Curve currency | Rating class | Market | Note |
|---|---|---|---|---|---|
| `LET1TREU` | euro_treasury_1_3y | EUR | Government | DM | 1-3y. |
| `I02513EU` | Bloomberg Pan-European Governm | European, several (mostly EUR) | Government | DM | Pan-European: EUR, GBP and smaller markets. Cowork's recollection of the index; not verified. |
| `LP05TREU` | pan_euro_agg_corporate | European, several (mostly EUR) | IG | DM | Pan-European Aggregate Corporate. |
| `I12823GB` | uk_gilt_1_10y | GBP | Government | DM |  |
| `I02913JP` | japan_aggregate | JPY | Aggregate, IG (mostly government) | DM |  |
| `LUMSTRUU` | Bloomberg US MBS Index Total R | USD | Agency MBS | DM |  |
| `LT01TRUU` | Bloomberg U.S. Treasury: 1-3 Y | USD | Government | DM |  |
| `LT09TRUU` | Bloomberg U.S. Treasury: 7-10 | USD | Government | DM |  |
| `LT11TRUU` | Bloomberg U.S. Treasury: 20+ Y | USD | Government | DM |  |
| `LT13TRUU` | Bloomberg U.S. Treasury 3-7 Yr | USD | Government | DM |  |
| `LUTLTRUU` | Bloomberg US Long Treasury Tot | USD | Government | DM |  |
| `LD20TRUU` | Bloomberg US Treasury Bills To | USD | Government (bills) | DM |  |
| `I00185US` | Bloomberg B US High Yield  TR | USD | HY B | DM |  |
| `I00183US` | Bloomberg Intermediate Ba U.S. | USD | HY Ba | DM | Intermediate maturities. |
| `I00184US` | Bloomberg Long Ba U.S. High Yi | USD | HY Ba | DM | Long maturities. |
| `I00188US` | Bloomberg Caa US High Yield To | USD | HY Caa | DM |  |
| `LF98TRUU` | Bloomberg US Corporate High Yi | USD | HY, all ratings | DM |  |
| `LDC5TRUU` | Bloomberg USD Corporate Bonds | USD | IG | DM | USD corporates; issuers may be foreign. |
| `LUACTRUU` | Bloomberg US Corporate Total R | USD | IG | DM |  |
| `LBUTTRUU` | Bloomberg US Treasury Inflatio | USD real | Government, inflation-linked | DM | The real curve, not the nominal one. |
| `LTP5TRUU` | Bloomberg US Treasury TIPS 0-5 | USD real | Government, inflation-linked | DM | The real curve, not the nominal one. |
| `LG38TRUU` | global_agg_ex_usd | Several (EUR, JPY, GBP and others) | Aggregate, IG | DM, with some EM | Cowork's recollection that it holds some EM issuers; not verified. |
| `I20344US` | Bloomberg EM Local Currency Go | EM local, several | Government, mixed IG and HY | EM | Many local curves; no single currency. |
| `EMUSTRUU` | Bloomberg EM USD Aggregate Tot | USD | Mixed IG and HY | EM | Hard currency: the curve is the US one, the credit is EM. Sovereign, quasi-sovereign and corporate. |
| `I12877US` | Bloomberg: EM USD Aggregate: C | USD | Mixed IG and HY | EM | Hard-currency corporates. |

- **Hard-currency EM debt** is priced off the US curve and carries EM credit.
  That is why the curve currency and the market are separate labels.
- **Three indices span several curves:** `I02513EU`, `LP05TREU` and
  `LG38TRUU`. `I20344US` spans many EM local curves.

## The draft parents — NOT ruled, kept for phase 4

| Instrument | Name | Daily from | Draft parent |
|---|---|---|---|
| `LTP5TRUU` | Bloomberg US Treasury TIPS 0-5 | 2010-06-03 | `LBUTTRUU` |
| `M1EAQU` | MSCI EAFE Quality Net Total Re | 2015-03-02 | `M1WDUQU` |
| `M1CXVRSD` | MSCI WORLD ex USA MINIMUM VOLA | 2015-07-01 | `M1EAMVOL` |
| `M1EFHDY` | MSCI EM (EMERGING MARKETS) HIG | 2015-08-03 | `M1EF000V` |
| `M1CXNNA` | MSCI USA High Dividend Yield N | 2016-06-01 | `M1US000V` |
| `M1EAMM` | MSCI EAFE MOMENTUM USD Net Tot | 2016-08-01 | `M1EA000G` |
| `MXEU0RL` | MSCI Europe Real Estate GICS L | 2016-09-01 | `MXEUG` |
| `M1WDUMMT` | MSCI ACWI ex USA MOMENTUM USD | 2017-05-04 | `M1WDU00G` |

The reasons and alternatives are in the Project doc.

## What it does not decide

- **How the map lands.** *Cowork's proposal:* a new file read by
  `resolve_exposures`, leaving `SeriesMeta.region` as the loader sets it. The
  loader's docstring says the non-synchronous covariance rule reads that
  field, so replacing it would move recorded numbers.
- **Sector and style labels.**

## What would reopen it

- A registered hypothesis that forms a view on Global, on a bond's region,
  or on a sector or style.
- The corrected bond labels, which complete item 6.
- A candidate reaching phase 4, for item 7.

## Addendum, 2026-10-11 (night): the bond labels are ruled

**What the owner said** (22:10), on L28: "I am ok with the labels for
currency, rating class and market in the decisions tabe".

1. **Item 6 is complete.** The draft bond labels above (curve currency,
   rating class, market, all 25 rows, `LD20TRUU` included) are the ruling as
   written. The heading "The draft bond labels — NOT ruled" is superseded by
   this addendum and left as it was, because this record is append-only.
2. **The notes stay notes.** Two rows rest on Cowork's unverified
   recollection of what an index holds (`I02513EU`'s currencies, `LG38TRUU`
   holding some EM). The ruling fixes the labels, not those descriptions.
3. **How a hypothesis uses a bond label** ("design and ammend", 22:25) is
   proposed in `decisions/proposed/0057`. It is not decided. Until it is, no
   axis reads a bond label.
4. **The map lands as `data/universe/label_map.csv`** (HANDOFF task 55): a
   new file read by `resolve_exposures`, as this record's "What it does not
   decide" proposed. The loader's `SeriesMeta.region` is not changed, so no
   recorded number moves.
   - Its rows are the 84 instruments that are not tradable-only. The eight of
     item 7 have no row.
   - Region view (item 9): 46 equities, US 19, Developed Europe 12, EM 12,
     Japan 1, APAC ex-Japan 1, Canada 1. The 12 Global instruments (8 equity
     indices and the 4 real-asset equity indices) receive no region view
     (item 10).
   - Counts are Cowork's, from `Claude outputs/label_map_draft_2026-10-11.csv`
     less the eight tradable-only rows; task 55 checks them against the
     tables above.

**Still open:** sector and style (item 8), and `0057`.
