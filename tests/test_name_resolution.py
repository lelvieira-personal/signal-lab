"""
`data_required` names must resolve at registration (decisions/0034).

Every test runs against small fixture tables in a temporary directory, never the
real registry or the real coverage tables, except the one that reads the seed row.
"""

from __future__ import annotations

import pytest
import yaml

from signal_lab.harness.hypotheses import (
    UNIVERSE_DIR,
    HypothesisRegistry,
    HypothesisRejected,
    unresolved_names,
    validate_hypothesis,
)


def good_doc(**over):
    doc = {
        "id": "H-2026-9001",
        "family": "policy_rates",
        "signal": "real_policy_rate_change_3m",
        "direction": "negative",
        "target_axis": "duration",
        "rationale": "A rising real policy rate raises the discount rate on every future coupon "
        "and raises the probability of further tightening being priced into the curve, and "
        "policy moves in persistent same-signed sequences, so the past quarter informs the next.",
        "horizon_weeks": "4-13",
        "expected_expression": "both",
        "proposed_by": "agent",
        "provenance": "adaptation",
        "data_required": ["DGS2"],
    }
    doc.update(over)
    return doc


def measurement_doc(**over):
    return good_doc(
        kind="measurement",
        family="exposure_estimation",
        target_axis="loadings",
        signal="shrunk_to_peer_mean",
        **over,
    )


@pytest.fixture
def universe(tmp_path):
    d = tmp_path / "universe"
    d.mkdir()
    (d / "investable_universe.csv").write_text("ticker,name\nAAAAAA,a\n", encoding="utf-8")
    (d / "bbg_index_coverage.csv").write_text("ticker,x\nBBBBBB,b\n", encoding="utf-8")
    (d / "bbg_exusd_bonds_coverage.csv").write_text("ticker,name\nCCCCCC,c\n", encoding="utf-8")
    (d / "fred_coverage.csv").write_text("series_id,description\nDGS2,y\n", encoding="utf-8-sig")
    (d / "bbg_analytics_coverage.csv").write_text(
        "ticker_field,n\nAAAAAA Index|INDEX_OAS_TSY,1\n", encoding="utf-8"
    )
    (d / "bbg_exusd_analytics_coverage.csv").write_text(
        "ticker_field,n\nCCCCCC|INDEX_OAD_TSY,1\n", encoding="utf-8"
    )
    (d / "owner_confirmed_names.csv").write_text(
        "name,field,confirmed_by,confirmed_on,how,note\n"
        "ZZREAL,,owner,2026-10-21,statement,n\n"
        "YYREAL Index,SOME_FIELD,owner,2026-10-21,statement,n\n",
        encoding="utf-8",
    )
    return d


def bad(names, universe, params):
    return unresolved_names(names, params, universe)


# rule 1: Bloomberg and FRED names


def test_bare_tickers_resolve_in_every_table(universe, params):
    assert bad(["AAAAAA", "BBBBBB", "CCCCCC", "DGS2"], universe, params) == []


def test_an_unknown_bare_ticker_is_named(universe, params):
    assert bad(["AAAAAA", "NOSUCH"], universe, params) == ["NOSUCH"]


def test_a_trailing_index_is_dropped_but_only_the_trailing_one(universe, params):
    assert bad(["AAAAAA Index"], universe, params) == []
    assert bad(["Index AAAAAA"], universe, params) == ["Index AAAAAA"]


def test_ticker_and_field_resolve_as_a_pair(universe, params):
    assert bad(["AAAAAA Index|INDEX_OAS_TSY", "CCCCCC|INDEX_OAD_TSY"], universe, params) == []


def test_a_field_not_in_the_analytics_tables_is_rejected(universe, params):
    assert bad(["AAAAAA Index|INDEX_OAD_TSY"], universe, params) == ["AAAAAA Index|INDEX_OAD_TSY"]
    # the ticker is real, the pair is not: a field never rescues a ticker, nor the reverse
    assert bad(["NOSUCH|INDEX_OAS_TSY"], universe, params) == ["NOSUCH|INDEX_OAS_TSY"]


def test_a_benchmark_leg_resolves(universe, params):
    assert bad(["NDUEACWF", "LEGATRUU", "MXWO", "SBWGU"], universe, params) == []


def test_the_owner_confirmed_list_admits_a_name_and_a_pair(universe, params):
    assert bad(["ZZREAL", "YYREAL Index|SOME_FIELD"], universe, params) == []
    assert bad(["YYREAL"], universe, params) == ["YYREAL"]


def test_the_seed_row_admits_lt08truu_and_the_real_list_holds_only_it(params):
    assert unresolved_names(["LT08TRUU"], params, UNIVERSE_DIR) == []
    rows = (UNIVERSE_DIR / "owner_confirmed_names.csv").read_text(encoding="utf-8").splitlines()
    assert rows[0] == "name,field,confirmed_by,confirmed_on,how,note"
    assert [r.split(",")[0] for r in rows[1:]] == ["LT08TRUU"]


def test_without_the_confirmed_file_a_confirmed_name_is_rejected(universe, params):
    (universe / "owner_confirmed_names.csv").unlink()
    assert bad(["ZZREAL"], universe, params) == ["ZZREAL"]


# rule 2: JPMaQS names


def test_a_well_formed_jpmaqs_name_resolves_without_a_table(universe, params):
    assert bad(["USD_RIR_NSA", "EUR_CPIC_SJA_P6M6ML6AR"], universe, params) == []


def test_a_malformed_jpmaqs_name_is_rejected(universe, params):
    names = ["usd_rir_nsa", "USD_", "US_RIR_NSA", "USDRIRNSA"]
    assert bad(names, universe, params) == names


# rule 3: the rejection names the entry, and the measurement boundary


def test_validation_with_names_rejects_and_names_the_entry(universe, params):
    doc = good_doc(data_required=["DGS2", "FAKE123"])
    with pytest.raises(HypothesisRejected, match="FAKE123"):
        validate_hypothesis(doc, params, resolve_names=True, universe_dir=universe)
    validate_hypothesis(good_doc(), params, resolve_names=True, universe_dir=universe)


def test_without_resolve_names_nothing_changes(universe, params):
    h = validate_hypothesis(good_doc(data_required=["FAKE123"]), params, universe_dir=universe)
    assert h.data_required == ["FAKE123"]


def test_a_measurement_hypothesis_with_an_empty_list_still_validates(universe, params):
    h = validate_hypothesis(
        measurement_doc(data_required=[]), params, resolve_names=True, universe_dir=universe
    )
    assert h.data_required == []


# the registry: load_tolerant is unchanged, register is strict


def test_load_tolerant_keeps_an_unresolved_file_that_register_rejects(universe, params, tmp_path):
    root = tmp_path / "hypotheses"
    reg = HypothesisRegistry(
        root, params=params, requests_dir=tmp_path / "requests", universe_dir=universe
    )
    incoming = tmp_path / "H-2026-9003.yaml"
    incoming.write_text(
        yaml.safe_dump(good_doc(id="H-2026-9003", data_required=["FAKE123"])), encoding="utf-8"
    )
    with pytest.raises(HypothesisRejected, match="FAKE123"):
        reg.register(incoming)
    assert incoming.exists() and not (root / "pending" / incoming.name).exists()

    (root / "pending" / incoming.name).write_text(incoming.read_text(encoding="utf-8"))
    good, rejected = reg.load_tolerant("pending")
    assert [h.id for h in good] == ["H-2026-9003"] and rejected == []


def test_register_moves_a_good_file_in_and_never_overwrites(universe, params, tmp_path):
    root = tmp_path / "hypotheses"
    reg = HypothesisRegistry(
        root, params=params, requests_dir=tmp_path / "requests", universe_dir=universe
    )
    incoming = tmp_path / "H-2026-9004.yaml"
    incoming.write_text(
        yaml.safe_dump(good_doc(id="H-2026-9004", data_required=["DGS2"])), encoding="utf-8"
    )
    target = reg.register(incoming)
    assert target == root / "pending" / "H-2026-9004.yaml" and target.exists()
    assert not incoming.exists()
    assert reg.register(target) == target  # already pending: validated, left alone

    incoming.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(FileExistsError):
        reg.register(incoming)
