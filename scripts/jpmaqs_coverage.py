#!/usr/bin/env python3
"""
JPMaQS coverage report from a macro snapshot. HANDOFF task 44, part B.

    make jpmaqs-coverage [MACRO_SNAPSHOT=jpmaqs-macro-v1]

One row per ticker, to `results/jpmaqs_coverage.csv` and `.md`. Dates and
counts only -- no `value`. The distinct grading values are listed with their
row counts so the owner can see whether fractional grades occur and whether a
rule is needed.

Which rows each count is over:
  * no-value rows, grade-excluded rows, grading values and eop_lag buckets come
    from the snapshot manifest, counted on the raw pull before compression
    (grading values: valued rows before the grade filter; eop_lag buckets: valued
    rows that survived it);
  * vintages, distinct periods, the knowledge-date range and the longest gap
    are over the snapshot's own rows, which are the change points -- a gap is
    the longest stretch with no new vintage, not the longest without a row in
    the vendor's daily series.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
RESOLUTION_CSV = REPO_ROOT / "data" / "requests" / "ticker_resolution.csv"
OUT_DIR = REPO_ROOT / "results"


def hypotheses_by_ticker(path: Path = RESOLUTION_CSV) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("source") != "jpmaqs":
                continue
            # A renamed ticker (decisions/0032 precedent) registers under resolves_to.
            ticker = row.get("resolves_to") or row["requested"]
            out.setdefault(ticker, []).append(row["hypothesis"])
    return out


def coverage_rows(snapshot, hyps: dict[str, list[str]]) -> list[dict]:
    import pandas as pd

    frame = pd.read_parquet(snapshot.path / "macro.parquet")
    counts = snapshot.manifest["counts"]["per_ticker"]
    dev_start = pd.Timestamp(snapshot.manifest["dev_start"])
    rows = []
    for ticker in sorted(counts):
        c = counts[ticker]
        g = frame[frame["series_id"] == ticker].sort_values("knowledge_date")
        kd = g["knowledge_date"]
        gaps = kd.diff().dt.days.dropna()
        rows.append(
            {
                "ticker": ticker,
                "hypotheses": ";".join(sorted(set(hyps.get(ticker, [])))),
                "first_knowledge_date": str(kd.min().date()) if len(g) else "",
                "last_knowledge_date": str(kd.max().date()) if len(g) else "",
                "first_period_end": str(g["period_end"].min().date()) if len(g) else "",
                "last_period_end": str(g["period_end"].max().date()) if len(g) else "",
                "n_vintages": int(len(g)),
                "n_periods": int(g["period_end"].nunique()),
                "rows_no_value": c["rows_no_value"],
                "rows_grade_excluded": c["rows_grade_excluded"],
                "gradings": ";".join(f"{k}:{v}" for k, v in c["grading_counts"].items()),
                "eop_lag_0": c["eop_lag_buckets"].get("0", 0),
                "eop_lag_1_31": c["eop_lag_buckets"].get("1-31", 0),
                "eop_lag_32_92": c["eop_lag_buckets"].get("32-92", 0),
                "eop_lag_over_92": c["eop_lag_buckets"].get(">92", 0),
                "longest_gap_days": int(gaps.max()) if len(gaps) else 0,
                "starts_by_dev_start": bool(len(g) and kd.min() <= dev_start),
            }
        )
    return rows


def write_reports(rows: list[dict], snapshot, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path, md_path = out_dir / "jpmaqs_coverage.csv", out_dir / "jpmaqs_coverage.md"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    m = snapshot.manifest
    late = [r["ticker"] for r in rows if not r["starts_by_dev_start"]]
    fractional = sorted(
        {
            k
            for r in rows
            for k in (p.split(":")[0] for p in r["gradings"].split(";") if p)
            if k not in {"1.0", "2.0", "3.0"}
        }
    )
    lines = [
        "# JPMaQS coverage",
        "",
        f"Macro snapshot `{m['snapshot_id']}`, raw pull `{m['pull_id']}`, data hash "
        f"`{snapshot.data_snapshot_hash}`. Counts and dates only; no values.",
        "",
        f"- Tickers: {len(rows)}. Starting after dev_start ({m['dev_start']}): {len(late)}"
        + (f" ({', '.join(late)})" if late else "")
        + ".",
        f"- Grading values other than 1, 2, 3: {fractional if fractional else 'none'}.",
        "",
        "| ticker | hypotheses | first kd | last kd | first pe | last pe | vintages | periods | "
        "no value | grade-excl | gradings | eop 0 | 1-31 | 32-92 | >92 | longest gap (d) | by dev_start |",
        "|" + "---|" * 17,
    ]
    for r in rows:
        lines.append(
            f"| {r['ticker']} | {r['hypotheses']} | {r['first_knowledge_date']} | "
            f"{r['last_knowledge_date']} | {r['first_period_end']} | {r['last_period_end']} | "
            f"{r['n_vintages']} | {r['n_periods']} | {r['rows_no_value']} | "
            f"{r['rows_grade_excluded']} | {r['gradings']} | {r['eop_lag_0']} | "
            f"{r['eop_lag_1_31']} | {r['eop_lag_32_92']} | {r['eop_lag_over_92']} | "
            f"{r['longest_gap_days']} | {'yes' if r['starts_by_dev_start'] else 'NO'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def main(argv=None) -> int:
    from signal_lab.harness.snapshot import load_snapshot, verify_snapshot

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", default="jpmaqs-macro-v1", help="macro snapshot id")
    parser.add_argument("--snapshots-dir", default=None)
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args(argv)

    snapshot = load_snapshot(args.id, args.snapshots_dir)
    ok, msg = verify_snapshot(snapshot)
    if not ok:
        print(msg, file=sys.stderr)
        return 1
    rows = coverage_rows(snapshot, hypotheses_by_ticker())
    csv_path, md_path = write_reports(rows, snapshot, Path(args.out_dir))
    print(f"wrote {csv_path} and {md_path}: {len(rows)} tickers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
