# 0022 — The Index Map is the truncation authority; SPBDALB is not investable

Status: decided, 2026-09-11, Leo. Two decisions taken while building the phase 2
Bloomberg loader, both prompted by evidence the loader surfaced. Amends the
series count in `decisions/0013` and the tier census implied by
`data/universe/bbg_index_coverage.csv`.

## 1. `first_daily` comes from the Index Map, and tiers follow from it

**The evidence.** `data/universe/bbg_index_coverage.csv` and the workbook's own
`Index Map` sheet disagree on the true daily start for **65 of 97 series**. The
disagreement has two shapes and both are wrong:

- **58 series: coverage is LATER.** Almost every coverage date is the first
  business day of a January. The rule appears to have been "the first
  observation in the first calendar year holding at least 150 observations" — a
  year-granular test. A series that goes daily in June is dated to the following
  January and loses six months of real daily history. The reconstruction of the
  rule is inferred from the pattern, since the script that built the original
  table is not in the repository; the direction and size of the error are
  measured.

- **7 series: coverage is EARLIER.** This is the dangerous direction.
  `LUTLTRUU` and `LT11TRUU` both carry 1994-01-31 against a true daily start of
  1994-03-01, and 1994-01-31 is a **month-end print from the sparse era**.
  Truncating there admits month-end observations into a daily panel. The others
  are `LGTRTRGU` and `LGTRTRJU` (2001-01-16 against 2001-02-01), `M1EAQU`,
  `BCOMTR` and `BCOMGCTR`.

The Loader Notes sheet calls the monthly-to-daily break "the most dangerous
property of the dataset": 40 of 97 series begin month-end only, 5,887 sparse-era
observations sit before the daily eras, and a naive return across that boundary
understates volatility by roughly sqrt(21) while corrupting every correlation
drawn through it. Handing the loader a start date inside the sparse era is
exactly the failure the `frequency` veto exists to prevent — and the veto reads
its reference point from this table, so a wrong date here disarms it silently.

SUBSTRATE section 5.1.2 already names the authority: the Index Map column
"First daily date". Its rule is month-granular (first calendar month with ≥15
observations, with a guard for a partial first month) and it is maintained
alongside the pull.

**Decided.** `scripts/build_coverage.py` regenerates
`bbg_index_coverage.csv` from the Index Map. Tier is recomputed from the
corrected date, so SUBSTRATE section 5.2 still holds as written — the loader
reads tier assignment from the coverage table and does not choose it; the table
is simply no longer wrong.

**Four tiers move**, and this changes the estimation universe:

| series | was | becomes | corrected daily start |
|---|---|---|---|
| `H09122US` | tradable-only | second | 2009-06-01 |
| `H12823US` | tradable-only | second | 2009-08-03 |
| `M1EAMVOL` | second | backbone | 2001-12-03 |
| `M1EFMVOL` | second | backbone | 2001-12-03 |

Census: 75/12/10 becomes **77/12/8** (backbone/second/tradable-only).

`likely_price_only` is dropped from the rebuilt table, as `decisions/0013`
asked. `frequency_flag` and `sparse_era_obs` are carried across from the Index
Map so a reader can see why a start date is where it is.

**A related consequence, recorded here because it is the same principle.** A
spliced series carries daily history from its source's start, so the loader
recomputes its tier from the spliced start and reports the change. The coverage
table is built before the splice and cannot know about it; leaving the old tier
would bar from estimation a series that demonstrably has the history. For
`LT13TRUU`, spliced from `G3OC`, this is the difference between daily history
from 2007-01-08 and from 1986-11-03.

## 2. `SPBDALB` stays in the panel but is not investable

**The evidence.** Loader Notes line 104: `SPBDALB`'s Bloomberg
`LONG_COMP_NAME` is *"Morningstar LSTA US Leveraged Loan Index (Price)"*. It is
a **price index**, pulled with `TOT_RETURN_INDEX_GROSS_DVDS` alongside 96
total-return series, and it is also the source of the 1,307 weekend prints the
business-day filter discards. Its measured return excludes loan coupon income,
which for leveraged loans is the larger part of total return.

**Decided.** `investable: false`, with the reason recorded in a new
`not_investable_because` column on `investable_universe.csv`. It stays in the
panel so the defect is visible in diagnostics rather than hidden by omission,
and so it can be restored the moment a total-return loan index is pulled —
`params/data.yaml` already carries that splice, marked blocked for this reason.

An optimiser given a price index among total-return peers would avoid loans for
a measurement artefact rather than for a signal. That is the failure mode
`decisions/0013` worried about for the sector axis, where it turned out to be a
false alarm; here the vendor's own long name confirms it is real.

**Amends `decisions/0013`:** 102 series, **95 investable**, 7 excluded — six
hedged plus `SPBDALB`. The reporting class `HY Corporates` keeps `SPBDALB` as a
member for rollup purposes; only holdability changes.

## Still open, deliberately

- **Region labels.** Invariant 7 estimates cross-region covariance on 2-day
  overlapping returns, which needs a region per series, and no table carries
  one. The loader sets `region` to the series' `Section` as a conservative
  placeholder: differing labels mean more pairs get the overlap treatment than
  strictly need it, never fewer, and SUBSTRATE section 5.1.7 forbids the error
  in the other direction. A real region map is an owner decision and has not
  been made.
- **`G3OC` as the live 3-7y series.** `params/data.yaml` splices it into
  `LT13TRUU` and the Index Map recommends replacing the column outright. The
  splice is live; the replacement is not actioned.
