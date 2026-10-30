#!/usr/bin/env python3
"""
The Japan government loader's per-ticker report, printed (decisions/0066, HANDOFF task 79).

    make japan-report

`BloombergLoader.load_returns()` fills `report["japan_govt"]["tickers"]` in memory every time and
nothing printed it. This loads the panel, reads that section and sets each ticker's true daily
start beside the `first_daily` the universe table carries (a placeholder, `scripts/build_universe.py`).
Writes `results/japan/loader_report.md` and `.json`. Dates and counts only: no level, no return and
no rate is printed or written. A start that differs from the table is a finding, not a failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

OUT_DIR = Path(__file__).resolve().parents[1] / "results" / "japan"
TICKERS = ("I29064JP", "I29065JP", "I29066JP", "I29067JP", "I29068JP")
FIELDS = (
    "daily_start",
    "tier",
    "level_rows_before_holdout",
    "dates_dropped_for_want_of_a_jpy_rate",
)


def build_table(report: dict, universe: dict[str, dict[str, str]]) -> dict[str, dict]:
    """One row per ticker: the loader's four fields and the comparison with the universe table."""
    tickers = report["tickers"]
    missing = [t for t in TICKERS if t not in tickers]
    if missing:
        raise KeyError(f"not in the loader's report: {missing}")
    table = {}
    for t in TICKERS:
        row = {k: tickers[t][k] for k in FIELDS}
        in_universe = str(universe[t]["first_daily"])[:10]
        row["first_daily_in_universe"] = in_universe
        row["differs"] = bool(row["daily_start"] != in_universe)
        table[t] = row
    return table


def render(table: dict[str, dict]) -> list[str]:
    lines = [
        "# Japan government loader report (decisions/0066, HANDOFF task 79)",
        "",
        "True daily start the loader found, against the `first_daily` in "
        "`data/universe/investable_universe.csv`. Dates and counts only.",
        "",
        "| Ticker | Daily start | Tier | Level rows before holdout | Dates dropped (no JPY rate) "
        "| First daily in universe | Differs |",
        "|---|---|---|---|---|---|---|",
    ]
    lines += [
        f"| `{t}` | {r['daily_start']} | {r['tier']} | {r['level_rows_before_holdout']} "
        f"| {r['dates_dropped_for_want_of_a_jpy_rate']} | {r['first_daily_in_universe']} "
        f"| {r['differs']} |"
        for t, r in table.items()
    ]
    differing = sorted(t for t, r in table.items() if r["differs"])
    lines += [
        "",
        f"- Starts that differ from the universe table: {', '.join(differing) or 'none'}.",
    ]
    return lines


def main() -> int:
    from signal_lab.loaders.bloomberg import BloombergLoader, read_universe
    from signal_lab.params import get_params

    loader = BloombergLoader(get_params())
    loader.load_returns()
    report = loader.report.get("japan_govt")
    if report is None or "tickers" not in report:
        print("the loader's report has no japan_govt tickers; stopping", file=sys.stderr)
        return 1
    try:
        table = build_table(report, read_universe(loader.universe_dir))
    except KeyError as exc:
        print(exc.args[0], file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "loader_report.json").write_text(
        json.dumps(table, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = render(table)
    (OUT_DIR / "loader_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
