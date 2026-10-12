"""
Pull FRED's BAA10Y into data/raw/fred/fred_baa10y.csv (HANDOFF task 56 step 1, decisions/0058).

    set -a; source .env; set +a; python scripts/fetch_fred_baa10y.py     (the owner's shell)

The key is read from FRED_API_KEY by `FredLoader.api_key`, never printed and never written; an HTTP
error prints the status code and nothing else, because the URL carries the key. The request ends
on 2019-12-31, so nothing on or after HOLDOUT_START is asked for. FRED's `.` is written blank.

Also registers the file: a `fred_credit_spread` row in data/universe/raw_manifest.csv and a row in
data/universe/fred_coverage.csv with the first and last date and the observation count. Re-running
replaces those rows. data/raw/ is not committed (FRED's page carries Moody's copyright notice).

Prints the first and last date and the count, which are the only values it reports.
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]

from signal_lab.loaders.fred import FredLoader  # noqa: E402

SERIES = "BAA10Y"
START, END = "1986-01-01", "2019-12-31"
BASE = "https://api.stlouisfed.org/fred/series/observations"
OUT = ROOT / "data" / "raw" / "fred" / "fred_baa10y.csv"
MANIFEST = ROOT / "data" / "universe" / "raw_manifest.csv"
COVERAGE = ROOT / "data" / "universe" / "fred_coverage.csv"
MANIFEST_ROW = {
    "file": "fred/fred_baa10y.csv",
    "sheet": "",
    "layout": "wide_single_date",
    "field": SERIES,
    "currency": "n/a",
    "role": "fred_credit_spread",
    "header_rows": "1",
    "first_data_row": "2",
}
DESCRIPTION = "Moody's Baa corporate yield less the 10y Treasury (task 56, decisions/0058)"


def fetch(key: str) -> list[tuple[str, str]]:
    query = urllib.parse.urlencode(
        {
            "series_id": SERIES,
            "api_key": key,
            "file_type": "json",
            "observation_start": START,
            "observation_end": END,
        }
    )
    try:
        with urllib.request.urlopen(f"{BASE}?{query}", timeout=60) as resp:  # noqa: S310
            body = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"FRED answered HTTP {exc.code}; stopping (task 56 step 1)") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"FRED unreachable: {type(exc.reason).__name__}") from None
    return [(o["date"], "" if o["value"] == "." else o["value"]) for o in body["observations"]]


def _rewrite(path: Path, key: str, row: dict[str, str]) -> None:
    """Replace the row whose `key` column equals `row[key]`, else append."""
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames
        rows = [r for r in reader if r[key] != row[key]]
    rows.append(row)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator=newline)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    key = FredLoader().api_key()
    obs = fetch(key)
    if not obs or max(d for d, _ in obs) >= "2020-01-01":
        raise SystemExit("no observations, or one on or after the holdout; nothing written")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["date", SERIES])
        writer.writerows(obs)
    present = [d for d, v in obs if v != ""]
    _rewrite(MANIFEST, "file", MANIFEST_ROW)
    _rewrite(
        COVERAGE,
        "series_id",
        {
            "series_id": SERIES,
            "description": DESCRIPTION,
            "status": "ok",
            "first": present[0],
            "last": present[-1],
            "n_obs": str(len(present)),
        },
    )
    print(f"{SERIES}: first {present[0]}, last {present[-1]}, {len(present)} observations")
    print(f"({len(obs) - len(present)} blank) wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
