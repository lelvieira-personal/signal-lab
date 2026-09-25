"""
The catalogue name search (HANDOFF task 29).

The catalogue here is hand-written, not vendor data.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

import jpmaqs_name_search as script  # noqa: E402

CATALOGUE = [
    "USD_ALPHA1_NSA",
    "USD_ALPHA2_SA",
    "EUR_ALPHA1_NSA",
    "GBP_ALPHA1_NSA",  # outside a USD|EUR cid filter
    "USD_BETA_SA",
    "usd_lower_sa",  # vendor case is normalised
    "NOT-A-TICKER",
]


def _tickers(rows):
    return [r["ticker"] for r in rows]


def test_prefix_and_cid_filter():
    rows, summary = script.search(CATALOGUE, [("H-T", ("USD", "EUR"), ("ALPHA",))])
    assert _tickers(rows) == ["EUR_ALPHA1_NSA", "USD_ALPHA1_NSA", "USD_ALPHA2_SA"]
    assert summary[0]["n_matches"] == 3 and not summary[0]["capped"]
    assert {r["n_matches"] for r in rows} == {"3"}


def test_every_cid_and_case_normalised():
    rows, summary = script.search(
        CATALOGUE, [("H-T", None, ("ALPHA1",)), ("H-T", None, ("LOWER",))]
    )
    assert "GBP_ALPHA1_NSA" in _tickers(rows)
    assert "USD_LOWER_SA" in _tickers(rows)
    assert summary[0]["found_cids"] == ["EUR", "GBP", "USD"]


def test_no_match_is_one_empty_row():
    rows, summary = script.search(CATALOGUE, [("H-T", ("USD",), ("ZZZ",))])
    assert rows == [
        {"hypothesis": "H-T", "cids": "USD", "xcat_prefix": "ZZZ", "n_matches": "0", "ticker": ""}
    ]
    assert summary[0]["n_matches"] == 0


def test_cap_truncates_but_reports_the_full_count():
    catalogue = [f"USD_MANY{i:03d}" for i in range(70)]
    rows, summary = script.search(catalogue, [("H-T", ("USD",), ("MANY",))], cap=60)
    assert len(rows) == 60
    assert summary[0]["n_matches"] == 70 and summary[0]["capped"]
    assert {r["n_matches"] for r in rows} == {"70"}


def test_rows_sort_by_hypothesis_then_ticker_and_carry_no_ranking():
    rows, _ = script.search(
        CATALOGUE, [("H-B", ("USD",), ("BETA",)), ("H-A", ("USD",), ("ALPHA",))]
    )
    assert [(r["hypothesis"], r["ticker"]) for r in rows] == sorted(
        (r["hypothesis"], r["ticker"]) for r in rows
    )
    assert set(rows[0]) == set(script.FIELDS)


def test_membership_is_exact_and_case_insensitive():
    assert script.membership(CATALOGUE, ["USD_ALPHA1_NSA", "usd_beta_sa"]) == []
    assert script.membership(CATALOGUE, ["USD_ALPHA1_NSA", "USD_ALPHA"]) == ["USD_ALPHA"]
