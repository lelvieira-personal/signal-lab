"""
The Japan loader's report table (HANDOFF task 79, decisions/0066), on the synthetic workbook that
tests/test_japan_govt.py builds. Nothing reads data/raw/.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_japan_report  # noqa: E402
from test_japan_govt import TICKERS, _fixture, _loader, pin  # noqa: E402, F401

from signal_lab.loaders.bloomberg import read_universe  # noqa: E402


def test_the_table_has_the_five_tickers_the_fields_and_the_comparison(tmp_path, params, pin):  # noqa: F811
    built = _fixture(tmp_path, with_japan=True)
    pin(built)
    loader = _loader(built, params)
    loader.load_returns()
    universe = read_universe(built["universe"])
    table = check_japan_report.build_table(loader.report["japan_govt"], universe)

    assert list(table) == TICKERS
    wanted = {*check_japan_report.FIELDS, "first_daily_in_universe", "differs"}
    assert all(set(row) == wanted for row in table.values())

    # the fixture's levels start 2012-11-30; the universe table says 2013-01-31
    assert all(r["differs"] is True for r in table.values())

    # the same table with the universe's date moved onto the loader's start: nothing differs
    for t in TICKERS:
        universe[t]["first_daily"] = table[t]["daily_start"]
    same = check_japan_report.build_table(loader.report["japan_govt"], universe)
    assert all(r["differs"] is False for r in same.values())
    assert all(r["first_daily_in_universe"] == r["daily_start"] for r in same.values())
