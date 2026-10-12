"""
The label map (HANDOFF task 55, decisions/0054 and its addendum, decisions/0057): the committed
`data/universe/label_map.csv` against the owner's tables in the decisions, and the script that
writes it. Nothing here reads data/raw/, data/snapshots/ or a date.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

import build_label_map  # noqa: E402

from signal_lab.characteristics.exposures import LABEL_MAP_PATH, load_label_map  # noqa: E402

DECISION_0054 = REPO_ROOT / "decisions" / "0054-the-label-map.md"
TRADABLE_ONLY = {"LTP5TRUU"}


@pytest.fixture(scope="module")
def label_map() -> pd.DataFrame:
    return load_label_map(LABEL_MAP_PATH)


def _table(text: str, heading: str) -> list[list[str]]:
    """The rows of the first markdown table after `heading`, cells as written."""
    block = text.split(heading, 1)[1]
    rows = []
    for line in block.splitlines():
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    return rows[2:]  # header and rule


def _equity_regions() -> dict[str, str]:
    rows = _table(DECISION_0054.read_text(encoding="utf-8"), "### Equity regions")
    return {t: region for region, _n, cell in rows for t in re.findall(r"`([^`]+)`", cell)}


def _bond_labels() -> dict[str, tuple[str, str, str]]:
    text = DECISION_0054.read_text(encoding="utf-8")
    rows = _table(text, "## The draft bond labels")
    return {r[0].strip("`"): (r[2], r[3], r[4]) for r in rows}


def test_the_counts_are_the_ones_the_record_expects(label_map):
    m = label_map
    assert len(m) == 84
    assert Counter(m.asset_group) == {
        "equity": 54,
        "bond": 23,
        "real_asset_equity": 4,
        "commodity": 2,
        "cash": 1,
    }
    view = m[m.region_view == "yes"]
    assert len(view) == 46
    assert Counter(view.region) == {
        "US": 19,
        "Developed Europe": 12,
        "EM": 12,
        "Japan": 1,
        "APAC ex-Japan": 1,
        "Canada": 1,
    }
    assert Counter(m.region) == {
        "US": 34,
        "Developed Europe": 16,
        "EM": 15,
        "Global": 13,
        "Japan": 2,
        "Commodities": 2,
        "APAC ex-Japan": 1,
        "Canada": 1,
    }
    bonds = m[m.curve_currency != ""]
    assert len(bonds) == 24  # the 23 bonds and LD20TRUU
    assert Counter(bonds.curve) == {
        "USD": 16,
        "EUR_multi": 2,
        "USD_real": 1,
        "EUR": 1,
        "GBP": 1,
        "JPY": 1,
        "DM_multi": 1,
        "EM_local_multi": 1,
    }
    assert Counter(bonds.rating) == {
        "Government": 11,
        "HY": 5,
        "IG": 3,
        "Aggregate": 2,
        "Mixed": 2,
        "Agency": 1,
    }
    assert Counter(bonds.hy_bucket[bonds.hy_bucket != ""]) == {"Ba": 2, "B": 1, "Caa": 1, "all": 1}
    assert Counter(bonds.market) == {"DM": 21, "EM": 3}
    assert not m.index.has_duplicates


def test_every_equity_region_equals_the_table_in_decisions_0054(label_map):
    table = _equity_regions()
    assert len(table) == 65
    both = set(table) & set(label_map.index)
    assert len(both) == 58  # the 54 equity and 4 real-asset equity indices
    for t in both:
        assert label_map.loc[t, "region"] == table[t], t
    absent = set(table) - set(label_map.index)
    # the table's other tradable-only tickers; the eighth, LTP5TRUU, is a bond (below)
    assert len(absent) == 7


def test_every_bond_label_equals_the_table_in_decisions_0054(label_map):
    table = _bond_labels()
    assert len(table) == 25
    assert set(table) - set(label_map.index) == TRADABLE_ONLY
    for t, (curve_currency, rating_class, market) in table.items():
        if t in TRADABLE_ONLY:
            continue
        row = label_map.loc[t]
        assert (row.curve_currency, row.rating_class, row.market_label) == (
            curve_currency,
            rating_class,
            market,
        ), t


def test_the_normalised_columns_follow_decisions_0057(label_map):
    m = label_map
    assert m.loc["LBUTTRUU", "curve"] == "USD_real"
    assert m.loc["I02513EU", "curve"] == m.loc["LP05TREU", "curve"] == "EUR_multi"
    assert m.loc["LG38TRUU", ["curve", "market"]].tolist() == ["DM_multi", "DM"]
    assert m.loc["I20344US", ["curve", "rating", "market"]].tolist() == [
        "EM_local_multi",
        "Government",
        "EM",
    ]
    assert m.loc["EMUSTRUU", ["curve", "rating", "market"]].tolist() == ["USD", "Mixed", "EM"]
    assert m.loc["LUMSTRUU", "rating"] == "Agency"
    assert m.loc["LD20TRUU", ["curve", "rating", "market"]].tolist() == ["USD", "Government", "DM"]
    assert m.loc["I00188US", ["rating", "hy_bucket"]].tolist() == ["HY", "Caa"]
    assert m.loc["LF98TRUU", ["rating", "hy_bucket"]].tolist() == ["HY", "all"]


def test_labels_are_blank_outside_the_bonds_and_cash(label_map):
    others = label_map[label_map.asset_group.isin(["equity", "real_asset_equity", "commodity"])]
    label_cols = ["curve_currency", "rating_class", "market_label", "curve", "rating", "market"]
    assert (others[label_cols] == "").all().all()
    assert (others.hy_bucket == "").all()


def test_region_view_is_yes_only_for_equities_that_are_not_global(label_map):
    m = label_map
    expected = m.asset_group.isin(["equity", "real_asset_equity"]) & (m.region != "Global")
    assert ((m.region_view == "yes") == expected).all()
    assert (m.loc[m.asset_group == "bond", "region_view"] == "no").all()
    assert set(m.region_view) == {"yes", "no"}


def test_the_columns_are_in_the_order_the_task_names():
    header = LABEL_MAP_PATH.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == list(build_label_map.COLUMNS)


def _draft_row(**kw):
    row = {
        "ticker": "X",
        "tier": "backbone",
        "asset_group": "bond",
        "reporting_class": "Treasuries",
        "region": "US",
        "curve_currency": "USD",
        "rating_class": "Government",
        "market": "DM",
    }
    return {**row, **kw}


def test_a_verbatim_value_the_vocabulary_does_not_map_is_an_error_not_a_blank():
    for column, value in (
        ("curve_currency", "CHF"),
        ("rating_class", "Junk"),
        ("market", "Frontier"),
    ):
        with pytest.raises(ValueError, match=re.escape(repr(value))):
            build_label_map.build_rows([_draft_row(**{column: value})])


def test_tradable_only_rows_are_left_out_and_the_commodities_bucket_is_renamed():
    rows = build_label_map.build_rows(
        [
            _draft_row(ticker="A", tier="tradable-only"),
            _draft_row(
                ticker="B",
                asset_group="commodity",
                region="(Commodities bucket)",
                curve_currency="",
                rating_class="",
                market="",
            ),
        ]
    )
    assert [r["ticker"] for r in rows] == ["B"]
    assert rows[0]["region"] == "Commodities" and rows[0]["curve"] == ""


def test_the_script_regenerates_the_committed_file_byte_for_byte(tmp_path):
    if not build_label_map.DRAFT.exists():
        pytest.skip("the owner's draft is git-ignored and absent on this machine")
    out = tmp_path / "label_map.csv"
    assert build_label_map.main(["--out", str(out)]) == 0
    committed = LABEL_MAP_PATH.read_bytes().replace(b"\r\n", b"\n")
    assert out.read_bytes() == committed


def test_a_draft_with_another_hash_is_refused(tmp_path, capsys):
    draft = tmp_path / "draft.csv"
    draft.write_text("ticker,tier\nX,backbone\n", encoding="utf-8")
    assert build_label_map.main(["--draft", str(draft), "--out", str(tmp_path / "o.csv")]) == 1
    assert not (tmp_path / "o.csv").exists()
    assert "refusing" in capsys.readouterr().out
