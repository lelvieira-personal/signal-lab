#!/usr/bin/env python3
"""
Name search of the cached JPMaQS catalogue for H-2026-0004, 0005 and 0010.
HANDOFF task 29, for OWNER-QUEUE L14. Names only; it chooses nothing.

    make jpmaqs-name-search

Reads the catalogue task 23 cached (`data/raw/jpmaqs_catalogue.json`, a JSON
list of ticker strings) -- no vendor call. For each pattern in `PATTERNS`
(a cid set, or every cid, and one xcat prefix) it lists the catalogue tickers
whose cid is in the set and whose xcat starts with the prefix, and writes
`data/requests/jpmaqs_name_search.csv`, at most `CAP` tickers per pattern. A
pattern with no match is one row with `ticker` empty and `n_matches` 0;
`n_matches` is the uncapped count.

It also tests the seven H-2026-0001 names for exact, case-insensitive
membership of the catalogue. That is a cache test, not the vendor check.

What a stem measures is the owner's reading of the vendor documentation, not a
name pattern's, so there is deliberately no ranking and no recommendation.
Prints counts only. Nothing but ticker names leaves `data/raw/`, and those only
into the CSV.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_CATALOGUE = REPO_ROOT / "data" / "raw" / "jpmaqs_catalogue.json"
OUT_CSV = REPO_ROOT / "data" / "requests" / "jpmaqs_name_search.csv"

CAP = 60
FIELDS = ["hypothesis", "cids", "xcat_prefix", "n_matches", "ticker"]

# (hypothesis, cids or None for every cid, xcat prefixes)
PATTERNS: list[tuple[str, tuple[str, ...] | None, tuple[str, ...]]] = [
    ("H-2026-0004", ("USD", "EUR"), ("BLS",)),
    ("H-2026-0010", ("DEM", "FRF", "ITL", "ESP", "NLG", "EUR", "USD"), ("GB10Y",)),
    ("H-2026-0010", None, ("GB10YCRY",)),
    (
        "H-2026-0005",
        ("USD", "EUR"),
        ("MBASE", "MBROAD", "MNARROW", "M1", "M2", "M3", "RM", "INTLIQ", "PCREDIT"),
    ),
]

# H-2026-0001's names after the 2026-09-24 renames, plus the two that resolved.
H0001_NAMES = [
    "USD_INTRGDP_NSA_P1M1ML12_D3M3ML3",
    "EUR_INTRGDP_NSA_P1M1ML12_D3M3ML3",
    "JPY_INTRGDP_NSA_P1M1ML12_D3M3ML3",
    "GBP_INTRGDP_NSA_P1M1ML12_D3M3ML3",
    "USD_UNEMPLRATE_SA_3MMAV5YMA",
    "USD_MBCSCORE_SA",
    "EUR_MBCSCORE_SA",
]


def search(
    catalogue: list[str],
    patterns=PATTERNS,
    cap: int = CAP,
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    """
    CSV rows, and a summary per (hypothesis, cids, prefix) pattern:
    `n_matches` (uncapped) and whether the cap was hit.
    """
    from signal_lab.loaders.jpmaqs import is_jpmaqs_ticker, split_ticker

    parsed: list[tuple[str, str, str]] = []
    for ticker in catalogue:
        ticker = ticker.upper()
        if is_jpmaqs_ticker(ticker):
            cid, xcat = split_ticker(ticker)
            parsed.append((cid, xcat, ticker))

    rows: list[dict[str, str]] = []
    summary: list[dict[str, object]] = []
    for hypothesis, cids, prefixes in patterns:
        cid_set = None if cids is None else {c.upper() for c in cids}
        cid_label = "*" if cids is None else "|".join(cids)
        for prefix in prefixes:
            found = sorted(
                {
                    t
                    for c, x, t in parsed
                    if (cid_set is None or c in cid_set) and x.startswith(prefix.upper())
                }
            )
            n = len(found)
            base = {
                "hypothesis": hypothesis,
                "cids": cid_label,
                "xcat_prefix": prefix,
                "n_matches": str(n),
            }
            rows.extend({**base, "ticker": t} for t in (found[:cap] or [""]))
            summary.append(
                {
                    "hypothesis": hypothesis,
                    "cids": cid_label,
                    "xcat_prefix": prefix,
                    "n_matches": n,
                    "capped": n > cap,
                    "found_cids": sorted({c for c, x, t in parsed if t in set(found)}),
                }
            )
    rows.sort(key=lambda r: (r["hypothesis"], r["ticker"]))
    return rows, summary


def membership(catalogue: list[str], names: list[str] = H0001_NAMES) -> list[str]:
    """The names that are not exact, case-insensitive members of the catalogue."""
    have = {t.upper() for t in catalogue}
    return [n for n in names if n.upper() not in have]


def main(argv=None) -> int:
    if not RAW_CATALOGUE.exists():
        print(
            f"{RAW_CATALOGUE} not found; it is cached by `make jpmaqs-catalogue` (task 23).",
            file=sys.stderr,
        )
        return 2
    catalogue = json.loads(RAW_CATALOGUE.read_text(encoding="utf-8"))
    if not isinstance(catalogue, list) or not all(isinstance(t, str) for t in catalogue):
        print(f"{RAW_CATALOGUE} is not a JSON list of ticker strings.", file=sys.stderr)
        return 2

    rows, summary = search(catalogue)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT_CSV}.")
    for s in summary:
        note = f" CAP HIT (>{CAP})" if s["capped"] else ""
        print(
            f"  {s['hypothesis']} cids={s['cids']} prefix={s['xcat_prefix']}: n_matches={s['n_matches']}{note}"
        )
        if s["cids"] == "*" and s["n_matches"] <= 30:
            print(f"    cids carrying it: {', '.join(s['found_cids'])}")
        elif s["cids"] == "*":
            print(f"    cids carrying it: {len(s['found_cids'])}")

    missing = membership(catalogue)
    if missing:
        print(
            f"H-2026-0001: {len(H0001_NAMES) - len(missing)} of {len(H0001_NAMES)} resolve; missing:"
        )
        for m in missing:
            print(f"  {m}")
    else:
        print(f"H-2026-0001: {len(H0001_NAMES)} of {len(H0001_NAMES)} resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
