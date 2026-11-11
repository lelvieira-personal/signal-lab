#!/usr/bin/env python3
"""
The per-ticker report of `bbg_exusd_bonds_extra.xlsx`'s loader (decisions/0068, HANDOFF task 89).

    make exusd-extra-report

Loads the panel and the analytics, reads `report["exusd_extra"]`, and writes
`results/exusd_extra/loader_report.md` and `.json`. Counts, dates and labels only: no level, no
return, no rate and no analytics value is printed or written. Per row: the true daily start, the
tier, the currency, whether it is investable, the level rows before the holdout, the dates lost to
conversion, the index name, each analytics field's start, and what the duration axis reads
(decisions/0068 ruling 5). For the two linkers: how many dates each analytics column holds a
number, and the FLDS test's `_is_number` flags.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

OUT_DIR = Path(__file__).resolve().parents[1] / "results" / "exusd_extra"
FIELDS = (
    "daily_start",
    "tier",
    "currency",
    "investable",
    "level_rows_before_holdout",
    "dates_dropped_for_want_of_a_rate",
)
OAD = "INDEX_OAD_TSY"


def duration_reading(row: dict, has_oad: bool, measured_class: bool) -> str:
    """What the exposure map's duration axis reads for a row (exposures._week_frame's rule)."""
    if not row["investable"]:
        return "none: reference series, not held"
    if row["tier"] not in ("backbone", "second"):
        return "none: tradable-only, unheld"
    if has_oad and measured_class:
        return "measured OAD where the week has one, estimated loading otherwise"
    return "estimated loading (minus the real-yield loading)"


def build_table(report: dict, analytics_report: dict, oad_tickers: set[str], classes: dict) -> dict:
    from signal_lab.characteristics.exposures import MEASURED_DURATION_CLASSES

    starts = analytics_report.get("starts", {})
    names = analytics_report.get("index_names", {})
    table = {}
    for t, r in sorted(report["tickers"].items()):
        row = {k: r[k] for k in FIELDS}
        row["index_name"] = names.get(t, "")
        row["analytics_starts"] = {
            k.split("|", 1)[1]: v for k, v in sorted(starts.items()) if k.split("|", 1)[0] == t
        }
        row["duration_axis"] = duration_reading(
            row, t in oad_tickers, classes.get(t) in MEASURED_DURATION_CLASSES
        )
        table[t] = row
    return table


def render(table: dict, analytics_report: dict) -> list[str]:
    lines = [
        "# bbg_exusd_bonds_extra.xlsx loader report (decisions/0068, HANDOFF task 89)",
        "",
        "Counts, dates and labels only.",
        "",
        "| Ticker | Index name | Daily start | Tier | CCY | Investable | Level rows before holdout "
        "| Dates dropped (no rate) | Analytics starts | Duration axis |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for t, r in table.items():
        an = "; ".join(f"{f} {d}" for f, d in r["analytics_starts"].items()) or "none"
        lines.append(
            f"| `{t}` | {r['index_name'] or '-'} | {r['daily_start']} | {r['tier']} "
            f"| {r['currency']} | {r['investable']} | {r['level_rows_before_holdout']} "
            f"| {r['dates_dropped_for_want_of_a_rate']} | {an} | {r['duration_axis']} |"
        )
    lines += ["", "## The linkers", ""]
    for t, counts in sorted(analytics_report.get("linker_dates_numeric", {}).items()):
        lines.append(
            f"- `{t}`: dates with a number in the analytics sheet: "
            + ", ".join(f"{c} {n}" for c, n in counts.items())
        )
    flags = analytics_report.get("linker_fields_is_number")
    if flags:
        lines += ["", "FLDS test (`linker_fields`, the `_is_number` columns only):", ""]
        mnemonics = sorted({m for v in flags.values() for m in v})
        lines += ["| Mnemonic | " + " | ".join(sorted(flags)) + " |"]
        lines += ["|---|" + "---|" * len(flags)]
        for m in mnemonics:
            lines.append(
                f"| `{m}` | " + " | ".join(str(flags[t].get(m)) for t in sorted(flags)) + " |"
            )
    lines += [
        "",
        f"- Analytics rows before the holdout: {analytics_report.get('rows')}; "
        f"on or after: {analytics_report.get('rows_on_or_after_holdout')}.",
    ]
    return lines


def main() -> int:
    from signal_lab.loaders.bloomberg import BloombergLoader, read_universe
    from signal_lab.params import get_params

    loader = BloombergLoader(get_params())
    loader.load_returns()
    report = loader.report.get("exusd_extra")
    if report is None or "tickers" not in report:
        print("the loader's report has no exusd_extra tickers; stopping", file=sys.stderr)
        return 1
    returns_report = dict(report)
    analytics = loader.load_analytics()
    analytics_report = loader.report["analytics"].get("exusd_extra")
    if analytics_report is None:
        print("the loader's analytics report has no exusd_extra section; stopping", file=sys.stderr)
        return 1
    oad = analytics.fields.get(OAD)
    oad_tickers = set() if oad is None else {c for c in oad.columns if oad[c].notna().any()}
    universe = read_universe(loader.universe_dir)
    classes = {t: r.get("reporting_class") for t, r in universe.items()}
    table = build_table(returns_report, analytics_report, oad_tickers, classes)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "file": {
            k: returns_report[k]
            for k in ("sha256_prefix", "level_rows", "level_rows_on_or_after_holdout")
        },
        "tickers": table,
        "linker_dates_numeric": analytics_report.get("linker_dates_numeric"),
        "linker_fields_is_number": analytics_report.get("linker_fields_is_number"),
        "analytics_rows_before_holdout": analytics_report.get("rows"),
        "analytics_rows_on_or_after_holdout": analytics_report.get("rows_on_or_after_holdout"),
    }
    (OUT_DIR / "loader_report.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = render(table, analytics_report)
    (OUT_DIR / "loader_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
