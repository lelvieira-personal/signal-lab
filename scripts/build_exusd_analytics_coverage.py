#!/usr/bin/env python3
"""
Write `data/universe/bbg_exusd_analytics_coverage.csv` (decisions/0052, HANDOFF task 52).

    make exusd-analytics-coverage

One row per ticker and field of the ex-USD analytics file: the first observation, the true
daily start by the one rule in `signal_lab.loaders.exusd_analytics`, and the number of
observations before the holdout. Dates and counts only; no value is printed or written.
"""

from __future__ import annotations

import sys
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

OUT = Path(__file__).resolve().parents[1] / "data" / "universe" / "bbg_exusd_analytics_coverage.csv"


def main() -> int:
    from signal_lab.loaders import exusd_analytics as exusd
    from signal_lab.loaders.bloomberg import BloombergLoader, _sheet_rows
    from signal_lab.params import get_params

    params = get_params()
    loader = BloombergLoader(params)
    entry = loader._entry(exusd.ROLE)
    path = loader._path(entry)
    sha = exusd.check_file(path)
    markers = list(params.get("data.calendar.missing_markers", []))
    long = exusd.rows_to_long(_sheet_rows(path, entry["sheet"]), markers)
    _, _, table = exusd.split_by_field(long, params)
    table = table.sort_values("ticker_field")
    table.to_csv(OUT, index=False, lineterminator="\n")
    print(f"file sha256 {sha}; {len(long)} rows, {long['ticker'].nunique()} tickers")
    print(table.to_string(index=False))
    print(f"written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
