#!/usr/bin/env python3
"""
Rebuild data/universe/bbg_index_coverage.csv from the workbook's Index Map.

WHY THIS EXISTS. The coverage table's `first_daily` column disagreed with the
Index Map's "First daily date" for 65 of the 97 series, and SUBSTRATE section
5.1.2 makes the Index Map the authority. The disagreement is not noise; it has a
shape, and both directions of it are wrong:

  * For 58 series the coverage date is LATER, and lands on the first business day
    of a January. The old rule appears to have been "the first observation in the
    first calendar year holding at least 150 observations", which is a
    year-granular test. A series going daily in June is then dated to the
    following January and loses six months of genuine daily history. (This
    reconstruction is inferred from the pattern -- the script that built the
    original table is not in the repository -- but the direction and size of the
    error are measured, not inferred.)

  * For 7 series the coverage date is EARLIER, which is the dangerous direction.
    `LUTLTRUU` and `LT11TRUU` are both dated 1994-01-31 against a true daily
    start of 1994-03-01, and 1994-01-31 is a month-end print from the sparse era.
    Truncating there admits month-end observations to a daily panel, understating
    volatility by roughly sqrt(21) on those observations and corrupting every
    correlation drawn through them. That is precisely what the `frequency` veto
    exists to catch, and it would have been the loader handing it the wrong
    reference point.

The Index Map's rule is month-granular -- the first calendar month holding at
least fifteen observations, with a guard for a partial first month -- and it is
maintained alongside the pull. This script copies it rather than recomputing it,
so the workbook and the lab cannot drift apart.

Tier follows from the corrected date, per SUBSTRATE section 5.2. Four series
move: H09122US and H12823US from tradable-only to second, M1EAMVOL and M1EFMVOL
from second to backbone. Recorded in decisions/0022.

    make coverage        # then: make universe

`likely_price_only` is not carried forward. decisions/0013 resolved it as a false
positive from a naming heuristic and asked for it to be dropped at the next
rebuild; leaving it would go on misleading readers the way it misled that one.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import _bootstrap  # noqa: F401

REPO = Path(__file__).resolve().parents[1]
UNIVERSE = REPO / "data" / "universe"
OUT = UNIVERSE / "bbg_index_coverage.csv"

# Index Map sections that make up the 97-series TR Levels block. The hedged
# overlay (15.), the replacement candidate (16.), the analytics inventory (17.)
# and the benchmarks (18.) live on their own tabs and are not universe members.
TR_SECTION_PREFIXES = (
    "1. ",
    "2. ",
    "3. ",
    "4. ",
    "5. ",
    "6. ",
    "7. ",
    "8. ",
    "9. ",
    "10. ",
    "11. ",
    "12. ",
    "13. ",
    "14. ",
    "15. Real Assets",
)

FIELDNAMES = [
    "ticker",
    "Bloomberg Security Name",
    "Section",
    "first_any",
    "first_daily",
    "tier_by_daily_start",
    "frequency_flag",
    "sparse_era_obs",
]


def is_tr_section(section: str) -> bool:
    if section.startswith("15.") and "Hedged" in section:
        return False
    return any(section.startswith(p) for p in TR_SECTION_PREFIXES)


def main(argv=None) -> int:
    from signal_lab.loaders.bloomberg import BloombergLoader, read_index_map
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--out", default=str(OUT))
    parser.add_argument("--raw-dir", default=None)
    parser.add_argument("--dry-run", action="store_true", help="report the diff, write nothing")
    args = parser.parse_args(argv)

    params = get_params()
    loader = BloombergLoader(params, raw_dir=args.raw_dir)
    entry = loader._entry("index_map")
    index_map = read_index_map(loader._path(entry), entry["sheet"])

    from signal_lab.loaders.bloomberg import _tier_from_start

    existing = {}
    out_path = Path(args.out)
    if out_path.exists():
        with out_path.open(newline="", encoding="utf-8-sig") as fh:
            existing = {r["ticker"]: r for r in csv.DictReader(fh)}

    rows, moved, redated = [], [], []
    for _, r in index_map.iterrows():
        section = str(r.get("section") or "")
        if not is_tr_section(section):
            continue
        start = r.get("first_daily")
        if start is None:
            raise SystemExit(f"{r['ticker']} has no First daily date in the Index Map")
        tier = _tier_from_start(start, params)
        row = {
            "ticker": r["ticker"],
            "Bloomberg Security Name": r.get("name") or "",
            "Section": section,
            "first_any": str(r["first_any"].date()) if r.get("first_any") is not None else "",
            "first_daily": str(start.date()),
            "tier_by_daily_start": tier,
            "frequency_flag": r.get("frequency_flag") or "",
            "sparse_era_obs": r.get("sparse_obs") or "0",
        }
        rows.append(row)
        was = existing.get(r["ticker"])
        if was:
            if was.get("first_daily") != row["first_daily"]:
                redated.append((r["ticker"], was.get("first_daily"), row["first_daily"]))
            if was.get("tier_by_daily_start") != tier:
                moved.append((r["ticker"], was.get("tier_by_daily_start"), tier))

    rows.sort(key=lambda x: x["ticker"])
    print(f"{len(rows)} series from the Index Map")
    print(f"{len(redated)} first_daily dates change, {len(moved)} tiers move")
    for ticker, was, now in moved:
        print(f"  tier  {ticker:<10} {was} -> {now}")

    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwritten to {out_path}")
    print("now run: make universe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
