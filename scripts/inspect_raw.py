#!/usr/bin/env python3
"""
Describe the shape of the raw vendor pulls, and nothing else.

Phase 2 needs the exact layout of data/raw/ before the Bloomberg loader can be
written, and `data/universe/raw_manifest.csv` is stale: it names
`research_data_values_only.xlsx` and `bbg_exUSD__bonds_values_only.xlsx`, while
the files actually on disk are `bbg_data_values_only.xlsx` and
`bbg_exusd_bonds_usd_unhedged.csv`. Guessing at the difference is how a loader
ends up silently reading the wrong column.

This script emits STRUCTURE ONLY -- sheet names, grid dimensions, header rows,
per-column non-empty counts, and first/last observed dates. It never prints or
writes an index level, a spread, a yield or a duration. That is deliberate: the
vendor data stays on this machine under the honour code in the project notes,
and the structure is not the data.

    make inspect-raw

Writes data/universe/raw_structure.json and prints a summary.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
OUT = REPO / "data" / "universe" / "raw_structure.json"
META_OUT = REPO / "data" / "universe" / "raw_meta.json"

# Sheets transcribed in full rather than merely described. These are the
# workbook's own documentation -- the pull specification and the per-ticker
# frequency audit -- and they carry tickers, dates, flags and observation
# counts, not index levels. SUBSTRATE section 5.1.2 makes the Index Map column
# "First daily date" the authority on where each series' daily history starts,
# so the loader has to read it rather than infer it.
META_SHEETS = ("Index Map", "Loader Notes")
META_SHEET_MAX_ROWS = 500

HEADER_ROWS = 8  # how many leading rows to transcribe verbatim as headers
MAX_COLS_LISTED = 400


def _cell(value) -> str | None:
    """A header cell as text. Dates become ISO; everything else str()."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()[:10]
    return str(value).strip() or None


def _is_datelike(value) -> bool:
    return isinstance(value, (datetime, date))


def describe_sheet(ws, name: str) -> dict:
    """
    One pass over the sheet in read-only mode.

    Records, per column: how many non-empty cells it holds, and the first and
    last row index at which it holds one. For the columns that look like dates,
    also the first and last date. No other cell content is retained.
    """
    header: list[list[str | None]] = []
    n_rows = 0
    n_cols = 0
    counts: dict[int, int] = {}
    first_row: dict[int, int] = {}
    last_row: dict[int, int] = {}
    date_cols: dict[int, list] = {}

    for r, row in enumerate(ws.iter_rows(values_only=True), start=1):
        n_rows = r
        if row:
            n_cols = max(n_cols, len(row))
        if r <= HEADER_ROWS:
            header.append([_cell(v) for v in row[:MAX_COLS_LISTED]])
        for c, value in enumerate(row, start=1):
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            counts[c] = counts.get(c, 0) + 1
            first_row.setdefault(c, r)
            last_row[c] = r
            if _is_datelike(value):
                seen = date_cols.setdefault(c, [None, None])
                iso = value.isoformat()[:10]
                if seen[0] is None or iso < seen[0]:
                    seen[0] = iso
                if seen[1] is None or iso > seen[1]:
                    seen[1] = iso

    columns = []
    for c in sorted(counts)[:MAX_COLS_LISTED]:
        entry = {
            "col": c,
            "n_non_empty": counts[c],
            "first_row": first_row[c],
            "last_row": last_row[c],
        }
        if c in date_cols:
            entry["date_min"], entry["date_max"] = date_cols[c]
        columns.append(entry)

    return {
        "sheet": name,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "header_rows": header,
        "columns": columns,
        "n_columns_reported": len(columns),
        "columns_truncated": len(counts) > MAX_COLS_LISTED,
    }


def dump_sheet_full(ws, name: str) -> dict:
    """
    Every cell of a documentation sheet, as text.

    Guarded by row count rather than by trust: a sheet that turns out to be
    large is truncated and says so, so this can never become a way to read a
    price grid out of the workbook.
    """
    rows = []
    truncated = False
    for r, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if r > META_SHEET_MAX_ROWS:
            truncated = True
            break
        cells = [_cell(v) for v in row]
        while cells and cells[-1] is None:
            cells.pop()
        rows.append(cells)
    while rows and not rows[-1]:
        rows.pop()
    return {"sheet": name, "n_rows": len(rows), "truncated": truncated, "rows": rows}


def describe_workbook(path: Path) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = [describe_sheet(wb[name], name) for name in wb.sheetnames]
        dumped = [dump_sheet_full(wb[name], name) for name in META_SHEETS if name in wb.sheetnames]
    finally:
        wb.close()
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "kind": "xlsx",
        "sheet_names": list(wb.sheetnames),
        "sheets": sheets,
        "meta_sheets": dumped,
    }


def describe_csv(path: Path) -> dict:
    """Header, row count, per-column non-empty counts, and the date range."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return {"file": path.name, "bytes": path.stat().st_size, "kind": "csv", "empty": True}
        counts = [0] * len(header)
        n_rows = 0
        first_field: str | None = None
        last_field: str | None = None
        for row in reader:
            n_rows += 1
            for i, value in enumerate(row[: len(header)]):
                if value is not None and value.strip():
                    counts[i] += 1
            if row and row[0].strip():
                first_field = first_field or row[0].strip()
                last_field = row[0].strip()

    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "kind": "csv",
        "header": header,
        "n_rows": n_rows,
        "columns": [
            {"col": i + 1, "name": name, "n_non_empty": counts[i]} for i, name in enumerate(header)
        ],
        "first_col_first_value": first_field,
        "first_col_last_value": last_field,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", default=str(RAW), help="data/raw/ root")
    parser.add_argument("-o", "--out", default=str(OUT))
    parser.add_argument("--meta-out", default=str(META_OUT))
    args = parser.parse_args(argv)

    raw = Path(args.raw)
    if not raw.exists():
        raise SystemExit(f"no such directory: {raw}")

    described = []
    for path in sorted(raw.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.name.startswith("~$"):
            # Excel's lock file, left beside a workbook while it is open (HANDOFF
            # task 58: 165 bytes, not a zip). Not data.
            print(f"skipped Excel lock file: {path.name}")
            continue
        if path.suffix.lower() in (".xlsx", ".xlsm"):
            described.append(describe_workbook(path))
        elif path.suffix.lower() in (".csv", ".tsv"):
            described.append(describe_csv(path))

    report = {"raw_root": str(raw), "files": described}

    # Split the transcribed sheets out before serialising, so raw_structure.json
    # stays a description and the transcription lives in its own file.
    meta = {f["file"]: f.pop("meta_sheets") for f in described if f.get("meta_sheets")}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    meta_out = Path(args.meta_out)
    if meta:
        meta_out.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    for f in described:
        print(f"\n=== {f['file']}  ({f['bytes']:,} bytes, {f['kind']})")
        if f["kind"] == "csv":
            print(f"  {f['n_rows']:,} rows x {len(f['header'])} columns")
            print(f"  header: {f['header'][:12]}{' ...' if len(f['header']) > 12 else ''}")
            print(f"  col 1 runs {f['first_col_first_value']} .. {f['first_col_last_value']}")
            continue
        for sh in f["sheets"]:
            print(f"  [{sh['sheet']}]  {sh['n_rows']:,} rows x {sh['n_cols']} cols")
            for i, hrow in enumerate(sh["header_rows"], start=1):
                shown = [c for c in hrow[:10]]
                print(f"    row {i}: {shown}{' ...' if sh['n_cols'] > 10 else ''}")
            dated = [c for c in sh["columns"] if "date_min" in c]
            if dated:
                c = dated[0]
                print(
                    f"    date column {c['col']}: {c['n_non_empty']:,} values, "
                    f"{c['date_min']} .. {c['date_max']}"
                )

    for fname, dumps in meta.items():
        for sh in dumps:
            note = " (TRUNCATED)" if sh["truncated"] else ""
            print(f"\n  transcribed [{sh['sheet']}] of {fname}: {sh['n_rows']} rows{note}")

    print(f"\nwritten to {out}")
    if meta:
        print(f"written to {meta_out}")
    print("structure only: no index level, spread, yield or duration was read out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
