#!/usr/bin/env python3
"""
Candidate catalogue names for the JPMaQS tickers that do not resolve.
HANDOFF task 27, for OWNER-QUEUE L14. Names only; it chooses nothing.

    make jpmaqs-candidates

Reads the catalogue task 23 cached (`data/raw/jpmaqs_catalogue.json`, a JSON
list of ticker strings) -- no vendor call. For each row of
`data/requests/jpmaqs_catalogue_check.csv` with `resolves == False`:

  1. the xcat's stem is its leading token, before the first `_`;
  2. candidates are catalogue tickers with the same cid whose xcat starts with
     that stem (`match = stem`); failing that, with the stem's first four
     characters (`match = relaxed`); failing that, one row with no candidate
     (`match = none`).

Writes `data/requests/jpmaqs_candidates.csv`, at most `CAP` candidates per
requested ticker. There is deliberately no ranking column: which name, if any,
replaces a registered ticker is the owner's call (the `decisions/0032`
precedent), and a rename is a dated addendum to the hypothesis.

Prints counts and match levels only. Nothing but ticker names leaves
`data/raw/`, and those only into the CSV.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_CATALOGUE = REPO_ROOT / "data" / "raw" / "jpmaqs_catalogue.json"
CHECK_CSV = REPO_ROOT / "data" / "requests" / "jpmaqs_catalogue_check.csv"
CANDIDATES_CSV = REPO_ROOT / "data" / "requests" / "jpmaqs_candidates.csv"

CAP = 40
RELAXED_CHARS = 4
FIELDS = ["hypothesis", "requested", "cid", "stem", "match", "candidate"]


def stem_of(xcat: str) -> str:
    """`INTRGDP_NSA_P1M1ML12_D1M1ML3` -> `INTRGDP`."""
    return xcat.split("_", 1)[0]


def find_candidates(
    unresolved: list[dict[str, str]], catalogue: list[str], cap: int = CAP
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """
    Candidate rows for each unresolved ticker, and the requested tickers whose
    candidate count exceeded `cap` (mapped to the uncapped count).
    """
    from signal_lab.loaders.jpmaqs import is_jpmaqs_ticker, split_ticker

    by_cid: dict[str, list[tuple[str, str]]] = {}
    for ticker in catalogue:
        ticker = ticker.upper()
        if is_jpmaqs_ticker(ticker):
            cid, xcat = split_ticker(ticker)
            by_cid.setdefault(cid, []).append((xcat, ticker))

    rows: list[dict[str, str]] = []
    capped: dict[str, int] = {}
    for row in unresolved:
        cid, xcat = row["cid"].upper(), row["xcat"].upper()
        stem = stem_of(xcat)
        same_cid = by_cid.get(cid, [])
        found = sorted({t for x, t in same_cid if x.startswith(stem)})
        match = "stem"
        if not found:
            found = sorted({t for x, t in same_cid if x.startswith(stem[:RELAXED_CHARS])})
            match = "relaxed"
        if not found:
            found, match = [""], "none"
        if len(found) > cap:
            capped[row["ticker"]] = len(found)
            found = found[:cap]
        base = {
            "hypothesis": row["hypothesis"],
            "requested": row["ticker"],
            "cid": cid,
            "stem": stem,
        }
        rows.extend({**base, "match": match, "candidate": c} for c in found)

    rows.sort(key=lambda r: (r["requested"], r["candidate"]))
    return rows, capped


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

    with CHECK_CSV.open("r", encoding="utf-8", newline="") as fh:
        unresolved = [r for r in csv.DictReader(fh) if r["resolves"].strip().lower() == "false"]
    if not unresolved:
        print(f"no unresolved rows in {CHECK_CSV}; nothing to do.")
        return 0

    rows, capped = find_candidates(unresolved, catalogue)

    with CANDIDATES_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(unresolved)} unresolved tickers; wrote {len(rows)} rows to {CANDIDATES_CSV}.")
    for r in unresolved:
        mine = [x for x in rows if x["requested"] == r["ticker"]]
        n = sum(1 for x in mine if x["candidate"])
        note = f" (capped at {CAP} of {capped[r['ticker']]})" if r["ticker"] in capped else ""
        print(f"  {r['ticker']}: {n} candidates, match={mine[0]['match']}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
