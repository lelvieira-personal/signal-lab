"""
The candidate lister for unresolved JPMaQS tickers (HANDOFF task 27).

The catalogue here is hand-written, not vendor data.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

import jpmaqs_candidates as script  # noqa: E402

CATALOGUE = [
    "USD_FAKEGDP_SA_P1M1ML12",
    "USD_FAKEGDP_NSA_D1M1ML3",
    "EUR_FAKEGDP_SA_P1M1ML12",  # other cid: never a candidate for USD
    "USD_FAKEOTHER_NSA",  # shares only the first four characters
    "USD_ZZZ_NSA",
    "gbp_lowercase_sa",  # vendor case is normalised
    "NOT-A-TICKER",
]


def _row(ticker: str, hypothesis: str = "H-TEST-0001") -> dict[str, str]:
    cid, xcat = ticker.split("_", 1)
    return {"hypothesis": hypothesis, "ticker": ticker, "cid": cid, "xcat": xcat}


def _for(rows, requested):
    return [r for r in rows if r["requested"] == requested]


def test_the_stem_is_the_leading_token():
    assert script.stem_of("INTRGDP_NSA_P1M1ML12_D1M1ML3") == "INTRGDP"
    assert script.stem_of("RIR") == "RIR"


def test_a_stem_match_lists_same_cid_names_only():
    rows, capped = script.find_candidates([_row("USD_FAKEGDP_SA_D1Q1QL4")], CATALOGUE)
    assert [r["candidate"] for r in rows] == ["USD_FAKEGDP_NSA_D1M1ML3", "USD_FAKEGDP_SA_P1M1ML12"]
    assert {r["match"] for r in rows} == {"stem"}
    assert {r["stem"] for r in rows} == {"FAKEGDP"}
    assert capped == {}


def test_no_stem_match_relaxes_to_four_characters():
    rows, _ = script.find_candidates([_row("USD_FAKEXYZ_SA")], CATALOGUE)
    assert {r["match"] for r in rows} == {"relaxed"}
    assert "USD_FAKEOTHER_NSA" in [r["candidate"] for r in rows]
    assert all(r["candidate"].startswith("USD_FAKE") for r in rows)


def test_nothing_found_writes_one_empty_row():
    rows, _ = script.find_candidates([_row("USD_QQQQ_SA")], CATALOGUE)
    assert rows == [
        {
            "hypothesis": "H-TEST-0001",
            "requested": "USD_QQQQ_SA",
            "cid": "USD",
            "stem": "QQQQ",
            "match": "none",
            "candidate": "",
        }
    ]


def test_case_is_normalised():
    rows, _ = script.find_candidates([_row("GBP_LOWERCASE_NSA")], CATALOGUE)
    assert [r["candidate"] for r in rows] == ["GBP_LOWERCASE_SA"]


def test_the_cap_truncates_and_is_reported():
    catalogue = [f"USD_MANY_V{i:02d}" for i in range(50)]
    rows, capped = script.find_candidates([_row("USD_MANY_X")], catalogue, cap=40)
    assert len(rows) == 40
    assert capped == {"USD_MANY_X": 50}


def test_rows_sort_by_requested_then_candidate_and_carry_no_ranking():
    unresolved = [_row("USD_QQQQ_SA"), _row("USD_FAKEGDP_SA_D1Q1QL4")]
    rows, _ = script.find_candidates(unresolved, CATALOGUE)
    keys = [(r["requested"], r["candidate"]) for r in rows]
    assert keys == sorted(keys)
    assert set(rows[0]) == set(script.FIELDS)
    assert len(_for(rows, "USD_QQQQ_SA")) == 1
