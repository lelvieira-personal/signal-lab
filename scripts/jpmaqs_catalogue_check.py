#!/usr/bin/env python3
"""
Check the 27 JPMaQS tickers tagged `genuine phase-3 gap` in
`data/requests/ticker_resolution.csv` against the vendor's own catalogue.
HANDOFF task 23. Metadata only.

    make jpmaqs-catalogue

`JPMaQSDownload.get_catalogue()` -- and nothing else. No `download()`, no
vintage pull, no touching `params/data.yaml: jpmaqs.status`. The 27 named
tickers are 8 cids x 12 xcats; the download API would return their cross
product (96) if this were a real pull, which it is not.

On success, writes:
  * `data/raw/jpmaqs_catalogue.json` -- the raw catalogue, git-ignored, cached
    as the offline resolver `decisions/proposed/0034` would need.
  * `data/requests/jpmaqs_catalogue_check.csv` -- hypothesis, ticker, cid,
    xcat, resolves, for every one of the 27.
  * `data/jpmaqs/request.txt` -- ONLY if all 27 resolve.

If any of the 27 does not resolve, or the connection fails, this stops and
reports rather than substituting or retrying with a different proxy setting.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
TICKER_RESOLUTION_CSV = REPO_ROOT / "data" / "requests" / "ticker_resolution.csv"
RAW_CATALOGUE = REPO_ROOT / "data" / "raw" / "jpmaqs_catalogue.json"
FINDINGS_CSV = REPO_ROOT / "data" / "requests" / "jpmaqs_catalogue_check.csv"
REQUEST_TXT = REPO_ROOT / "data" / "jpmaqs" / "request.txt"

TAG = "genuine phase-3 gap"


def _gap_rows() -> list[dict[str, str]]:
    with TICKER_RESOLUTION_CSV.open("r", encoding="utf-8", newline="") as fh:
        return [
            row
            for row in csv.DictReader(fh)
            if row.get("source") == "jpmaqs" and row.get("note") == TAG
        ]


def main(argv=None) -> int:
    from signal_lab.loaders.jpmaqs import JPMaQSLoader, cross_product_size, split_ticker
    from signal_lab.params import get_params

    rows = _gap_rows()
    if not rows:
        print(f"no rows tagged {TAG!r} in {TICKER_RESOLUTION_CSV}", file=sys.stderr)
        return 2
    tickers = [r["requested"] for r in rows]
    if len(set(tickers)) != len(tickers):
        print("duplicate tickers among the tagged rows; expected 27 distinct", file=sys.stderr)
        return 2

    requested, cross = cross_product_size(tickers)
    print(f"{requested} named tickers ({TAG!r}); the cross product is {cross}.")

    params = get_params()
    loader = JPMaQSLoader(params)
    client_id, client_secret = loader.credentials()  # never printed
    proxy = loader.proxies()

    from macrosynergy.download import JPMaQSDownload

    print("connecting to DataQuery (check_connection=True)...", flush=True)
    try:
        with JPMaQSDownload(
            client_id=client_id,
            client_secret=client_secret,
            proxy=proxy,
            check_connection=True,
        ) as dq:
            catalogue = dq.get_catalogue()
    except Exception as exc:  # noqa: BLE001 -- report and stop, per the task's stop rule
        print(f"catalogue call failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("stopping. Not varying the proxy setting or retrying with another host.")
        return 1

    RAW_CATALOGUE.parent.mkdir(parents=True, exist_ok=True)
    RAW_CATALOGUE.write_text(json.dumps(catalogue, indent=0), encoding="utf-8")
    catalogue_set = {t.upper() for t in catalogue}
    print(f"catalogue size: {len(catalogue)} tickers (cached at {RAW_CATALOGUE}).")

    findings = []
    missing = []
    for row in rows:
        ticker = row["requested"]
        cid, xcat = split_ticker(ticker)
        resolves = ticker.upper() in catalogue_set
        findings.append(
            {
                "hypothesis": row["hypothesis"],
                "ticker": ticker,
                "cid": cid,
                "xcat": xcat,
                "resolves": resolves,
            }
        )
        if not resolves:
            missing.append(ticker)

    FINDINGS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with FINDINGS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["hypothesis", "ticker", "cid", "xcat", "resolves"])
        writer.writeheader()
        writer.writerows(findings)
    print(f"wrote {FINDINGS_CSV} ({len(findings)} rows).")

    if missing:
        print(f"\n{len(missing)} of {len(tickers)} did NOT resolve:", file=sys.stderr)
        for t in missing:
            print(f"  {t}", file=sys.stderr)
        print(
            "\nSTOP: not substituting, not guessing a near-miss, not dropping these. "
            "Substitution is the owner's call (decisions/0032 precedent). "
            "data/jpmaqs/request.txt was NOT written.",
            file=sys.stderr,
        )
        return 1

    REQUEST_TXT.write_text(
        "# Pull list for the JPMaQS loader (SUBSTRATE section 5.6).\n"
        "# All 27 registered tickers resolved against the vendor catalogue\n"
        "# (HANDOFF task 23, data/requests/jpmaqs_catalogue_check.csv).\n"
        "#\n"
        "# The download API returns the cross product of the requested cids and\n"
        "# xcats, not just these named tickers -- filter the result back to this\n"
        "# list before it reaches the loader (see split_tickers()/filter_panel()\n"
        "# in signal_lab/loaders/jpmaqs.py and the module docstring).\n"
        + "\n".join(sorted(tickers))
        + "\n",
        encoding="utf-8",
    )
    print(f"all {len(tickers)} resolved. wrote {REQUEST_TXT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
