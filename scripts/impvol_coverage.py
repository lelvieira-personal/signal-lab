#!/usr/bin/env python3
"""
Coverage report for the implied-vol file (decisions/0061, HANDOFF task 59).

    make impvol-coverage

Writes `results/impvol/coverage.{md,json}`: per lab id, the sheet, the first and last Friday, the
weeks before the stale rule, the stale weeks removed, the weeks kept, and the Fridays missing
between the first and the last. Dates and counts only; no value is printed or written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "bloomberg" / "bbg_impvol_values_only.xlsx"
OUT = ROOT / "results" / "impvol"


def coverage_table(panel):
    import pandas as pd

    removed = panel.stale.groupby("series_id").size()
    rows = []
    for sid, g in panel.long.groupby("series_id", sort=True):
        n_removed = int(removed.get(sid, 0))
        before = len(g) + n_removed
        first, last = g["date"].min(), g["date"].max()
        span = len(pd.date_range(first, last, freq="W-FRI"))
        rows.append(
            {
                "series_id": sid,
                "sheet": str(g["sheet"].iloc[0]),
                "first_friday": str(first.date()),
                "last_friday": str(last.date()),
                "weeks_before_rule": before,
                "stale_removed": n_removed,
                "weeks_kept": len(g),
                "missing_fridays": span - before if before else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["sheet", "series_id"], ascending=[False, True])


def render_md(table, sha, totals) -> str:
    lines = [
        "# Implied-vol file coverage (decisions/0061, HANDOFF task 59)",
        "",
        f"File sha256 `{sha}`. Dates and counts only.",
        "",
        f"**{totals['series']} series, {totals['weeks_before_rule']:,} weeks before the stale "
        f"rule, {totals['stale_removed']:,} removed, {totals['weeks_kept']:,} kept.**",
        "",
        "| series | sheet | first Friday | last Friday | weeks before rule | stale removed | "
        "kept | missing Fridays |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in table.itertuples(index=False):
        lines.append(
            f"| {r.series_id} | {r.sheet} | {r.first_friday} | {r.last_friday} | "
            f"{r.weeks_before_rule} | {r.stale_removed} | {r.weeks_kept} | {r.missing_fridays} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    from signal_lab.loaders import impvol
    from signal_lab.params import get_params

    params = get_params()
    sha = impvol.check_file(RAW)
    panel = impvol.load_impvol(RAW, params)
    table = coverage_table(panel)
    totals = {
        "series": int(len(table)),
        "weeks_before_rule": int(table["weeks_before_rule"].sum()),
        "stale_removed": int(table["stale_removed"].sum()),
        "weeks_kept": int(table["weeks_kept"].sum()),
        "stale_run_weeks": impvol.STALE_RUN_WEEKS,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "coverage.md").write_text(render_md(table, sha, totals), encoding="utf-8")
    (OUT / "coverage.json").write_text(
        json.dumps({"sha256": sha, "totals": totals, "series": table.to_dict("records")}, indent=2),
        encoding="utf-8",
    )
    print(f"file sha256 {sha[:16]}; {totals}")
    print(f"written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
