"""
`scripts/inspect_raw.py` skips Excel lock files (HANDOFF task 59, step 1).

Excel leaves a `~$name.xlsx` of a few bytes beside a workbook while it is open;
task 58's first run died on one with `BadZipFile`. Synthetic workbooks only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

openpyxl = pytest.importorskip("openpyxl")

import inspect_raw  # noqa: E402


def test_a_lock_file_beside_a_workbook_is_skipped_and_said_so(tmp_path, capsys):
    raw = tmp_path / "raw"
    raw.mkdir()
    wb = openpyxl.Workbook()
    wb.active.append(["date", "x"])
    wb.active.append(["2019-01-04", 1.0])
    wb.save(raw / "real.xlsx")
    (raw / "~$real.xlsx").write_bytes(b"\x00junk" * 20)

    out = tmp_path / "structure.json"
    rc = inspect_raw.main(
        ["--raw", str(raw), "-o", str(out), "--meta-out", str(tmp_path / "meta.json")]
    )

    assert rc == 0
    files = [f["file"] for f in json.loads(out.read_text(encoding="utf-8"))["files"]]
    assert files == ["real.xlsx"]
    assert "skipped Excel lock file: ~$real.xlsx" in capsys.readouterr().out
