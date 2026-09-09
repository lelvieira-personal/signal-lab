#!/usr/bin/env python3
"""
Build data/universe/investable_universe.csv.

Three columns the rest of the lab depends on, derived from the coverage tables
by explicit rules rather than by hand-editing a spreadsheet, so the rules are
reviewable and the file is regenerable:

  investable       may the optimiser hold it (decisions/0013)
  cost_bucket      low | mid | high, per SUBSTRATE section 8
  reporting_class  the bank's asset-class taxonomy, for investor-facing rollups

`reporting_class` is aggregation only. It is deliberately NOT part of the
exposure matrix in data/characteristics/ and must never enter the optimiser --
see decisions/0013. Keeping it in a separate column of a separate file is what
stops that happening by accident.

    python scripts/build_universe.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import _bootstrap  # noqa: F401

REPO = Path(__file__).resolve().parents[1]
COVERAGE = REPO / "data" / "universe" / "bbg_index_coverage.csv"
EXUSD = REPO / "data" / "universe" / "bbg_exusd_bonds_coverage.csv"
OUT = REPO / "data" / "universe" / "investable_universe.csv"

# SUBSTRATE section 5.1.6, and excluded from the investable universe by
# decisions/0013: section 4 makes hedged series the counterfactual, not a live
# axis, and letting the optimiser choose between a hedged and an unhedged
# version of the same exposure would be an FX axis by the back door.
HEDGED = {"H09122US", "H12823US", "BTSYTRUH", "H02549US", "LP01TRUH", "M0JPHUSD"}

# The owner's taxonomy, plus two classes added to reach full coverage; the two
# additions are flagged in decisions/0013 for confirmation.
REPORTING_CLASSES = [
    "Cash",
    "Treasuries",
    "Long Treasuries",
    "TIPS",
    "MBS",
    "Ex-USD Bonds",
    "IG Corporates",
    "HY Corporates",
    "EM Sovereign Bonds",
    "EM Corporate Bonds",
    "US Equities",
    "European Equities",
    "Japanese Equities",
    "APAC ex-Japan Equities",
    "EM Equities",
    "DM ex-US Equities",  # ADDED: Canada, EAFE styles, World-ex-US styles
    "Real Assets",  # ADDED: commodity producers, natural resources, infra, REITs
    "Commodities",
    "Gold",
]

# Explicit per-ticker assignment. A lookup rather than a heuristic: a regex over
# ticker names would misfile exactly the awkward cases (M0JPHUSD, SPBDALB,
# M2WDCOMP) that matter, and silently.
REPORTING = {
    "LD20TRUU": "Cash",
    "LT01TRUU": "Treasuries",
    "LT09TRUU": "Treasuries",
    "LT13TRUU": "Treasuries",
    "LUTLTRUU": "Long Treasuries",
    "LT11TRUU": "Long Treasuries",
    "LBUTTRUU": "TIPS",
    "LTP5TRUU": "TIPS",
    "LUMSTRUU": "MBS",
    "I02513EU": "Ex-USD Bonds",
    "LGTRTRGU": "Ex-USD Bonds",
    "LGTRTRJU": "Ex-USD Bonds",
    "BTSYTRUH": "Ex-USD Bonds",
    "H09122US": "Ex-USD Bonds",
    "H12823US": "Ex-USD Bonds",
    "H02549US": "Ex-USD Bonds",
    "LET1TREU": "Ex-USD Bonds",
    "I12823GB": "Ex-USD Bonds",
    "I02913JP": "Ex-USD Bonds",
    "LP05TREU": "Ex-USD Bonds",
    "LG38TRUU": "Ex-USD Bonds",
    "LUACTRUU": "IG Corporates",
    "LDC5TRUU": "IG Corporates",
    "LF98TRUU": "HY Corporates",
    "I00183US": "HY Corporates",
    "I00184US": "HY Corporates",
    "I00185US": "HY Corporates",
    "I00188US": "HY Corporates",
    "LP01TRUH": "HY Corporates",
    "SPBDALB": "HY Corporates",  # leveraged loans; no separate loan class in the taxonomy
    "EMUSTRUU": "EM Sovereign Bonds",
    "I20344US": "EM Sovereign Bonds",
    "I12877US": "EM Corporate Bonds",
    "NDDUJN": "Japanese Equities",
    "M0JPHUSD": "Japanese Equities",
    "NDDUPXJ": "APAC ex-Japan Equities",
    "MXCA": "DM ex-US Equities",
    "BCOMTR": "Commodities",
    "BCOMGCTR": "Gold",
    "M2WDCOMP": "Real Assets",
    "SPGNRUT": "Real Assets",
    "FGCIICUT": "Real Assets",
    "ENXG": "Real Assets",
}

# Sections whose members all share a reporting class.
SECTION_REPORTING = {
    "6. Equity Regions - US": "US Equities",
    "6. Equity Regions - US (also 11. Factor/Style - US)": "US Equities",
    "9. US Sectors (MSCI USA)": "US Equities",
    "11. Factor / Style - US": "US Equities",
    "10. European Sectors (MSCI Europe)": "European Equities",
    "8. Equity Regions - Emerging Markets": "EM Equities",
    "14. Factor / Style - EM": "EM Equities",
    "12. Factor / Style - EAFE": "DM ex-US Equities",
    "13. Factor / Style - World ex-US": "DM ex-US Equities",
}

# SUBSTRATE section 8. `low` is "Treasuries, T-bills, US large-cap equity"
# exactly as written -- US mid and small cap are not large cap and go to `mid`.
COST_LOW = {
    "LD20TRUU",
    "LT01TRUU",
    "LT09TRUU",
    "LT13TRUU",
    "LUTLTRUU",
    "LT11TRUU",
    "LBUTTRUU",
    "LTP5TRUU",
    "SPXT",
}
COST_HIGH_CLASSES = {
    "HY Corporates",
    "EM Sovereign Bonds",
    "EM Corporate Bonds",
    "EM Equities",
    "Real Assets",
    "Commodities",
    "Gold",
}


def reporting_class(ticker: str, section: str) -> str:
    if ticker in REPORTING:
        return REPORTING[ticker]
    if section in SECTION_REPORTING:
        return SECTION_REPORTING[section]
    if section == "7. Equity Regions - Developed ex-US":
        # MXEUG (Europe ex UK), NDDLUK / NDDUUK (UK). Japan, APAC and Canada are
        # named individually above.
        return "European Equities"
    raise KeyError(f"no reporting class for {ticker!r} in section {section!r}")


def cost_bucket(ticker: str, klass: str) -> str:
    """The dear bucket wherever the section 8 text does not clearly say otherwise."""
    if ticker in COST_LOW:
        return "low"
    if klass in COST_HIGH_CLASSES:
        return "high"
    return "mid"


def build() -> list[dict]:
    rows: list[dict] = []

    with COVERAGE.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            ticker, section = r["ticker"], r["Section"]
            klass = reporting_class(ticker, section)
            hedged = ticker in HEDGED
            rows.append(
                {
                    "ticker": ticker,
                    "name": r["Bloomberg Security Name"],
                    "section": section,
                    "first_daily": r["first_daily"],
                    "tier": r["tier_by_daily_start"],
                    "hedged": hedged,
                    "investable": not hedged,
                    "cost_bucket": cost_bucket(ticker, klass),
                    "reporting_class": klass,
                    "source_file": "bbg_index_coverage.csv",
                }
            )

    if EXUSD.exists():
        with EXUSD.open(newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                ticker = r["ticker"]
                rows.append(
                    {
                        "ticker": ticker,
                        "name": r["name"],
                        "section": "3. International Government Bonds",
                        "first_daily": r["usd_series_daily_start"],
                        "tier": "",  # assigned by the loader from first_daily
                        "hedged": False,
                        "investable": True,
                        "cost_bucket": "mid",
                        "reporting_class": "Ex-USD Bonds",
                        "source_file": "bbg_exusd_bonds_coverage.csv",
                    }
                )

    return sorted(rows, key=lambda r: (r["reporting_class"], r["ticker"]))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--out", default=str(OUT))
    args = parser.parse_args(argv)

    rows = build()
    unknown = {r["reporting_class"] for r in rows} - set(REPORTING_CLASSES)
    if unknown:
        raise SystemExit(f"reporting classes not in the taxonomy: {sorted(unknown)}")

    out = Path(args.out)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    n_inv = sum(r["investable"] for r in rows)
    print(f"{len(rows)} series, {n_inv} investable, {len(rows) - n_inv} excluded (hedged)")
    print(f"\n{'reporting_class':<24} {'n':>3}  {'investable':>10}  buckets")
    for klass in REPORTING_CLASSES:
        sub = [r for r in rows if r["reporting_class"] == klass]
        if not sub:
            print(f"{klass:<24}   0           0  -- EMPTY")
            continue
        buckets = ",".join(sorted({r["cost_bucket"] for r in sub}))
        print(f"{klass:<24} {len(sub):>3}  {sum(r['investable'] for r in sub):>10}  {buckets}")
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
