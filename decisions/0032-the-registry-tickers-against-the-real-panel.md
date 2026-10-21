# 0032 — The registry's `data_required` against the panel that actually exists

Proposed 2026-09-18 by Cowork. **Owner rulings 2026-09-19 folded in** (§3 §3b §4
§5 §6). Status: **decided**. Machine-readable map:
`data/requests/ticker_resolution.csv`.

## Why this exists

The twelve hypotheses were written in phase 0, against plausible ticker names.
The Bloomberg workbook was mapped in phase 2 and carries different ones. Nobody
had reconciled the two, and the eleven files in `data/requests/` were generated
from the phase-0 names.

If this is not done first, the hypotheses resolve to `blocked:data` on
instruments that mostly exist, and it reads as a data gap when it is a naming
gap. `H-2026-0009` was worst affected — six of its seven names did not
resolve — and it is the harness control.

Reconciled against `investable_universe.csv` (102 rows), `bbg_index_coverage.csv`
(97), `bbg_analytics_coverage.csv`, `bbg_exusd_bonds_coverage.csv` and
`fred_coverage.csv` (35). Nothing under `data/raw/` was opened.

## 1. The count

| status | n | meaning |
|---|---|---|
| `ok` | 31 | resolves as written |
| `jpmaqs_gap` | 27 | genuine phase-3 gap, correctly named |
| `rename` | 8 | instrument exists under another ticker |
| `fabricated` | 2 | the ticker does not exist; owner does not recognise it |
| `benchmark_leg` | 2 | exists, but is a benchmark leg and not holdable |
| `fred_gap` | 1 | valid-looking FRED id absent from the pull |
| `source_correction` | 1 | requested from the wrong vendor |

27 of the 42 unresolved names are legitimate JPMaQS gaps. The rest is
bookkeeping, and all of it is now resolved.

## 2. The renames

| requested | resolves to | note |
|---|---|---|
| `MXUS` | `SPXT` | S&P 500 Total Return |
| `MXJP` | `NDDUJN` | MSCI Japan Net TR, USD |
| `MXEF` | `M1EF` | MSCI EM Net TR |
| `MXEU` | `MXEUG` + `NDDUUK` | Europe ex-UK plus UK — see §3b |
| `MXWO` | `NDUEACWF` | benchmark equity leg, `params/constraints.yaml`; not holdable |
| `LEGATRUU` | — | benchmark bond leg; not holdable |
| `MOVE` | `MOVE Index\|PX_LAST` | **Bloomberg, not FRED**; `data/requests/H-2026-0008.yaml` says `source: unknown` |

With those applied, **`H-2026-0008` is fully resolvable on data the lab already
holds.** It is the only one of the twelve with no gap of any kind.

## 3. WITHDRAWN — the "price-only" concern was wrong, and was already settled

The first draft of this record raised a decision about regional equity series
being on mixed return bases, on the strength of the `likely_price_only` column
in `bbg_index_coverage.csv`, which flags `MXEUG`, `MXCA`, `MXCN`, `MXIN`,
`MXKR`, `MXLA` and `MXUSMC`.

**That was wrong and the lab had already established it was wrong.** Owner,
2026-09-19: the index pull uses `TOT_RETURN_INDEX_GROSS_DVDS`, not `PX_LAST`.
`data/universe/raw_manifest.csv` confirms it — every returns sheet (`TR Levels`,
`TR Levels Hedged`, `TR Levels Candidates`, `TR Benchmarks`) carries
`field: TOT_RETURN_INDEX_GROSS_DVDS`. Bloomberg computes that field even for a
price-index ticker, so a price-index *name* does not mean a price-index *series*.

`decisions/0013` resolved this on 2026-09-09, after the owner checked `MXUS0EN`
directly: the column "is a false positive from the coverage script's heuristic,
not a property of the pulled data", and it "should be dropped or renamed when
the coverage table is next rebuilt, so it does not mislead a future reader the
way it misled this one."

**It misled the next reader.** The mechanism is worth recording because it will
recur: `scripts/build_coverage.py` has been changed to stop emitting the column,
and its docstring says so — but `bbg_index_coverage.csv` on disk still carries
it, because the table has not been rebuilt since. A stale artefact outlived the
decision that retired it, and nothing in the file says it is stale.

**Action:** `make coverage && make universe`, so the column leaves the table. It
needs the shell, so it queues in `HANDOFF.md`. No hypothesis changes. There is
no mixed-basis problem and none of the regional series need dropping.

## 3b. Europe is not missing

Also corrected. The panel carries 14 series with `reporting_class:
European Equities` — `MXEUG` (Europe ex-UK), `NDDUUK` and `NDDLUK` (UK, USD and
local), and the 11 MSCI Europe sector indices. Europe is represented as
**ex-UK plus UK**, which together span the region, and the earlier claim of a
"hole in the regional set" was an artefact of reading only section 7 of the
index map.

What is genuinely absent is a single pan-Europe *line item*: the parent MSCI
Europe (`MXEU`) is not in the pull, though its 11 sectors are.

**Ruled by the owner, 2026-09-19: keep Europe at the sub-country and sector
level only for now.** `MXEU` is not added to the next pull. Europe enters as
`MXEUG` (ex-UK) and `NDDUUK` (UK), plus the 11 `MXEU0xx` sector indices.

One consequence to state rather than discover. In a regional cross-section the
US is one slot (`SPXT`) and Japan is one (`NDDUJN`), while Europe is two. A
cross-sectional rank therefore gives Europe two draws where other regions get
one, which tilts the rank distribution toward it. That is defensible — the UK
genuinely is a distinct market and treating it as its own region is a modelling
choice, not an accident — but it must be disclosed in the risk decomposition
for `H-2026-0009` and `H-2026-0011` rather than left for a reader to infer from
the count.

Two live cautions that survive, both currency rather than return-basis:
`NDDLUK` is local currency and `NDDUUK` is USD — one cross-section may not hold
both, or it is an FX view wearing a region label. And invariant 6 already
forbids the hedged/unhedged version of the same mistake.

## 4. Two of the three unresolved tickers do not exist

Owner, 2026-09-19, on `LUALTRUU`: *"I don't know about this index. For sure not
one that I use today. Maybe it was a typo or LLM mistake."* On `LT08TRUU`: the
maturity buckets in the panel already cover the curve.

- **`LUALTRUU`** (`H-2026-0004`, and as an OAS field in `H-2026-0007`) —
  **fabricated.** Removed from both, not substituted. `H-2026-0004`'s credit
  legs are `LF98TRUU` and `LUACTRUU`, which resolve as written.
- **`LT08TRUU`** (`H-2026-0010`) — **fabricated.** The panel's Treasury buckets
  are `LT01TRUU` (1-3y), `LT13TRUU` (3-7y), `LT09TRUU` (7-10y), `LT11TRUU`
  (20+y) and `LUTLTRUU` (long), all with `INDEX_YIELD_TO_WORST`. The only gap is
  10-20y and nothing needs it. **Term spread: `LT01TRUU`
  against `LT11TRUU`** — confirmed by the owner 2026-09-19, with `LT09TRUU`
  available as a mid-curve check.
- **`DRTSCILM`** (`H-2026-0004`) — **real, and a genuine pull gap.** Owner
  approved adding it to the FRED request (2026-09-19).

## 5. `H-2026-0007`'s cross-section is expanded — owner approved

Owner, 2026-09-19: *"let's expand and adjust the hypothesis accordingly."*

The hypothesis named four segments, one of which was fabricated. The analytics
pull carries 20 series with `INDEX_OAS_TSY`. 0007's own logic — each segment
scored against its own five-year history, never one against another — extends to
any of them.

**The constraint that decides the set: pick one granularity per market.**
`LF98TRUU` *is* the aggregate of the Ba/B/Caa ladder, and `EMUSTRUU` contains
`I12877US`. Holding a parent and its children in one cross-section double-counts
and manufactures collinear segments — the breadth problem this lab already has,
made worse on purpose. Two candidate sets, both investable, unhedged and
`INDEX_OAS_TSY`-covered:

**A — quality ladder. CHOSEN by the owner, 2026-09-19. 6 segments.**

    LUACTRUU   US IG corporate
    LUMSTRUU   US MBS
    I00183US   US HY, intermediate Ba
    I00185US   US HY, B
    I00188US   US HY, Caa
    EMUSTRUU   EM USD aggregate

**B — conservative, 4 segments. Not taken; retained for the record.**

    LUACTRUU   US IG corporate
    LF98TRUU   US HY aggregate
    LUMSTRUU   US MBS
    EMUSTRUU   EM USD aggregate

A was recommended and taken because spread mean-reversion differs most across
the quality ladder, which is where a cross-sectional signal has something to find. **Stated
in advance, as 0007's other risks are:** Ba, B and Caa are highly correlated
with each other, so three segments is not three bets — it is one credit-beta
factor plus a quality tilt, and the risk decomposition should say so rather than
the count implying otherwise.

Deliberately excluded and why: `I00184US` (long Ba) is a maturity split of
`I00183US`, so holding both is a curve bet inside one rating; `LDC5TRUU` overlaps
`LUACTRUU`; `I20344US` is EM local currency, where a spread to Treasuries is
contaminated by FX and local rates; `H02549US` and `LP01TRUH` are hedged and
`investable: False`.

This changes what the hypothesis claims, so it lands as an amendment to
`H-2026-0007` citing this record, dated before any result exists.

## 6. The validator never checks that a `data_required` name exists

The root cause, and the only part of this that generalises.

`harness/hypotheses.py` rejects a `literature` provenance whose reference will
not resolve — SUBSTRATE section 7 treats a fabricated citation as a failure of
the proposer. It type-checks `data_required` as a list of strings and **never
checks the strings name anything.** Resolution happens later, at run time, where
a name that does not exist produces `blocked:data` — indistinguishable from a
series the lab simply has not pulled yet.

So a fabricated instrument is the same class of error as a fabricated citation,
and the registry catches one and hides the other behind a status that looks
routine. Two survived here, in hypotheses written by an agent, and they were
found by hand rather than by the harness.

**Proposed:** `validate_hypothesis` resolves every `data_required` entry at
registration against the coverage tables and the JPMaQS naming convention
(`decisions/0014`), and rejects an entry matching neither. A name that is real
but not yet pulled still validates and still becomes `blocked:data`; a name that
is real nowhere is refused at the door, which is where 0007's fabricated segment
should have died.

## 7. Closed

Nothing open. Every item in this record was decided on 2026-09-19, and section 6
moves to its own record by the owner's ruling the same day:
`decisions/proposed/0034-a-data-required-name-must-resolve.md`. Section 6 is
retained above as the statement of the problem this record found.

## 8. What is NOT proposed

No silent edits to `hypotheses/pending/*.yaml`. On approval the corrections and
the 0007 amendment land as a patch citing this record, the request files
regenerate from the map, and the phase-0 names stay visible in git history.

## Addendum, 2026-09-24 — `H-2026-0001`'s JPMaQS names (OWNER-QUEUE L14)

**Owner ruling, 2026-09-24:** apply the resolved renames. The vendor catalogue
check (HANDOFF task 23) found 12 of the 27 genuine-gap names absent. Task 27
listed catalogue names sharing each stem. The Macrosynergy *Macro-Quantimental
Investment Handbook* (2025), Appendix 4, fixed the meaning of the suffixes
(`D3M3ML3` = "change q/q", last 3 months vs the prior 3; `3MMAv5YMA` =
"difference vs 5-year moving average") and names `UNEMPLRATE_SA_3MMAv5YMA` as
the unemployment-gap factor.

| phase-0 name | now | why |
|---|---|---|
| `{USD,EUR,JPY,GBP}_INTRGDP_NSA_P1M1ML12_D1M1ML3` | `..._P1M1ML12_D3M3ML3` | same 3-month change of intuitive GDP growth, the form the catalogue carries |
| `USD_UNEMPLRATE_SA_D1Q1QL4` | `USD_UNEMPLRATE_SA_3MMAV5YMA` | the rationale says "unemployment gap"; the phase-0 name was a 4-quarter change of a monthly series. Enters with a negative sign |

The hypothesis's direction, horizon, target and rationale are unchanged.
`ticker_resolution.csv` carries the new names under the same tag, so
`jpmaqs_catalogue_check` verifies them on its next run.
`jpmaqs_catalogue_check.csv` still shows the old names until then.

**Not decided here, still open under L14:**
- `H-2026-0004`: the only catalogue matches (`BLSDSCORE`) look like loan
  *demand*, not lending *standards*. A rename would change the hypothesis.
- `H-2026-0005`: nothing for real broad money. Neither the handbook's
  `INTLIQGDP` nor `XPCREDITBN` is broad money, so this needs re-specifying or
  holding.
- `H-2026-0010`: `USD_GB10YCRY_NSA` is a lead, and EUR needs a `DEM_` search.

## Addendum, 2026-09-27 — `H-2026-0004`, `0005`, `0010`'s JPMaQS names (OWNER-QUEUE L14)

**Owner ruling, 2026-09-27:** "recs on all". HANDOFF task 27 listed catalogue
names sharing each unresolved ticker's cid and stem; HANDOFF task 29 (the
2026-09-24 names-only search, `data/requests/jpmaqs_name_search.csv`) found
what a stem search alone could not, using Macrosynergy's Academy notebooks
"Bank survey scores", "Monetary aggregates" and "Government bond yields and
carry" for what each series measures.

| hypothesis | phase-0 name | now | why |
|---|---|---|---|
| 0004 | `{USD,EUR}_BLSDCLN_SA_D1Q1QL1` | `{USD,EUR}_BLSCSCORE_NSA_D2Q2QL2` | lending *standards* z-score (credit supply; positive = easing), 2 quarters over the prior 2, matching the signal's "2q change". **Enters negated**, so the registered direction `negative` (on tightening) is unchanged. NSA z-score, not an SA balance. `BLSDSCORE` is credit *demand* and was not used |
| 0005 | `EUR_RM3GDP_SA_D1M1ML12` | `EUR_RMBROAD_SJA_P1M1ML12` | real broad money (M3, CPI-deflated), % over a year ago -- the hypothesis's title. A growth rate, not "% of GDP" |
| 0005 | `USD_RM1GDP_SA_D1M1ML12` | `USD_RMBROAD_SJA_P1M1ML12` | as above. **USD broad money is M2.** The narrow-money leg is dropped: the hypothesis is about broad money |
| 0005 | `USD_MBASEGDP_SA_D1M1ML12` | **dropped** | no 12-month change exists for it (only 1/3/6-month); monetary base is a different mechanism from broad money; a derived 12-month change would mix vintages |
| 0010 | `USD_GB10YXGB_NSA` | `USD_GB10YCRY_NSA` | no `XGB` series and no term-spread category exist in the catalogue. 10y carry is "yield plus roll-down", the rationale's own words, so the signal is **re-specified from term spread to carry** |
| 0010 | `EUR_GB10YXGB_NSA` | `DEM_GB10YCRY_NSA` | no euro-area bond cross-section exists; euro-area government bonds are carried by country in JPMaQS, and the Bund (`DEM_`) is the benchmark curve |
| 0004 | `DRTSCILM` (FRED, `decisions/0032` §4, approved 2026-09-19, `OWNER-QUEUE` L6) | **dropped** (owner, 2026-09-27) | the Fed's Senior Loan Officer survey duplicates the `USD_BLSCSCORE` leg and runs the opposite sign (positive = tightening, against `BLSCSCORE`'s positive = easing). This withdraws the 2026-09-19 approval to add it to the FRED request |

Direction, horizon, target and rationale are otherwise unchanged for all three
hypotheses. The phase-0 names remain in git history (this record, and the
hypothesis files' own prior revisions).

**Caveat, not a change:** `H-2026-0010`'s rationale calls for a risk
decomposition to show whether cross-sectional carry is a tilt or a single
term-premium factor wearing its clothes (`decisions/0016`). That decomposition
still cannot be built; re-specifying the signal from term spread to carry does
not resolve it.

## Addendum 2026-10-21 (owner)

`LT08TRUU` is a real Bloomberg index: the US Treasury: Intermediate Index, 1 to
9.9999 years, future ticker `I00049US` (owner's statement, not verified by
Cowork). "Fabricated" at the lines naming it was wrong for it, and right for
`LUALTRUU` on the owner's word. The rulings stand: `LT01TRUU` against `LT11TRUU`
was chosen on the panel and not on the existence of `LT08TRUU`.
