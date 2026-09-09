"""
The hypothesis registry. SUBSTRATE section 7.

The registered set is validated as data: if a hypothesis file drifts out of
spec, the suite says so, which is what makes pre-registration binding rather
than decorative.
"""

from __future__ import annotations

import pytest
import yaml

from signal_lab.harness.hypotheses import (
    FAMILIES,
    HypothesisRegistry,
    HypothesisRejected,
    check_data,
    validate_hypothesis,
    write_data_request,
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
        "data_required": ["DGS2", "DGS10"],
    }
    doc.update(over)
    return doc


# --- validation --------------------------------------------------------------


def test_a_well_formed_hypothesis_validates(params):
    h = validate_hypothesis(good_doc(), params)
    assert h.id == "H-2026-9001"
    assert h.horizon_range() == (4, 13)
    assert not h.is_proxy


@pytest.mark.parametrize("field", ["direction", "rationale", "family", "signal", "data_required"])
def test_missing_required_field_is_rejected(params, field):
    doc = good_doc()
    doc.pop(field)
    with pytest.raises(HypothesisRejected, match="missing required field"):
        validate_hypothesis(doc, params)


def test_direction_must_be_positive_or_negative(params):
    with pytest.raises(HypothesisRejected, match="direction"):
        validate_hypothesis(good_doc(direction="maybe"), params)


def test_a_thin_rationale_is_rejected(params):
    """SUBSTRATE section 7 asks for a paragraph of economics, not a sentence."""
    with pytest.raises(HypothesisRejected, match="rationale"):
        validate_hypothesis(good_doc(rationale="Rates go up, bonds go down."), params)


def test_unknown_family_is_rejected(params):
    with pytest.raises(HypothesisRejected, match="family"):
        validate_hypothesis(good_doc(family="vibes"), params)


def test_unknown_target_axis_is_rejected(params):
    with pytest.raises(HypothesisRejected, match="target_axis"):
        validate_hypothesis(good_doc(target_axis="alpha"), params)


def test_malformed_id_is_rejected(params):
    with pytest.raises(HypothesisRejected, match="id"):
        validate_hypothesis(good_doc(id="my-idea"), params)


def test_malformed_horizon_is_rejected(params):
    with pytest.raises(HypothesisRejected, match="horizon_weeks"):
        validate_hypothesis(good_doc(horizon_weeks="a few months"), params)
    with pytest.raises(HypothesisRejected, match="sane range"):
        validate_hypothesis(good_doc(horizon_weeks="13-4"), params)


def test_literature_without_a_reference_is_rejected(params):
    with pytest.raises(HypothesisRejected, match="no reference"):
        validate_hypothesis(good_doc(provenance="literature"), params)


def test_literature_with_an_unresolvable_reference_is_rejected(params):
    """
    No resolver is enabled, so no citation can be verified, so none is accepted.
    SUBSTRATE section 7 treats a fabricated citation as a failure of the
    proposer; accepting unverified ones on trust is how that happens.
    """
    doc = good_doc(provenance="literature", reference="10.1000/does-not-exist")
    with pytest.raises(HypothesisRejected, match="did not resolve"):
        validate_hypothesis(doc, params)


def test_proxy_must_be_declared_as_a_mapping(params):
    with pytest.raises(HypothesisRejected, match="proxy_for"):
        validate_hypothesis(good_doc(proxy_for="DGS10"), params)
    h = validate_hypothesis(good_doc(proxy_for={"DGS10": "JPMAQS.USD_GB10YXGB_NSA"}), params)
    assert h.is_proxy


# --- data availability -------------------------------------------------------


def test_missing_series_blocks_and_writes_a_request(params, tmp_path):
    h = validate_hypothesis(good_doc(data_required=["DGS2", "USD_RIR_NSA"]), params)
    check = check_data(h, {"DGS2"})
    assert check.blocked and check.status == "blocked:data"
    assert check.missing == ["USD_RIR_NSA"]

    path = write_data_request(h, check, tmp_path)
    doc = yaml.safe_load(path.read_text())
    assert doc["hypothesis_id"] == h.id
    assert doc["series"][0]["id"] == "USD_RIR_NSA"
    assert doc["series"][0]["source"] == "jpmaqs"
    assert doc["series"][0]["fields"]
    assert doc["status"] == "awaiting_owner"


def test_a_fully_covered_hypothesis_is_ready(params):
    h = validate_hypothesis(good_doc(), params)
    assert not check_data(h, {"DGS2", "DGS10", "SPX"}).blocked


def test_source_hints_distinguish_the_three_vendors(params):
    """
    A JPMaQS ticker and a Bloomberg ticker are both bare uppercase strings.
    Misrouting one sends the owner to the wrong vendor on a data request.
    """
    from signal_lab.harness.hypotheses import _guess_source

    assert _guess_source("USD_INTRGDP_NSA_P1M1ML12_D1M1ML3") == "jpmaqs"
    assert _guess_source("EUR_CPIC_SJA_P6M6ML6AR") == "jpmaqs"
    assert _guess_source("LUACTRUU") == "bloomberg"
    assert _guess_source("MXUS0EN") == "bloomberg"
    assert _guess_source("BCOMGCTR") == "bloomberg"
    assert _guess_source("DGS10") == "fred"
    assert _guess_source("VIXCLS") == "fred"
    assert _guess_source("MOVE") == "unknown"


def test_every_registered_jpmaqs_ticker_is_well_formed(params):
    """
    The registry's tickers must survive split_ticker(), or phase 3 discovers
    eleven malformed pre-registrations on the night the search opens.
    """
    from signal_lab.harness.hypotheses import HypothesisRegistry
    from signal_lab.loaders.jpmaqs import is_jpmaqs_ticker, split_ticker

    reg = HypothesisRegistry(params=params)
    n = 0
    for h in reg.load("pending"):
        for sid in h.data_required:
            if is_jpmaqs_ticker(sid):
                cid, xcat = split_ticker(sid)
                assert len(cid) == 3 and xcat
                n += 1
    assert n >= 20, f"expected the macro families to name JPMaQS tickers, found {n}"


# --- the lifecycle -----------------------------------------------------------


def test_move_records_a_transition(params, store, tmp_path):
    root = tmp_path / "hypotheses"
    (root / "pending").mkdir(parents=True)
    (root / "pending" / "H-2026-9001.yaml").write_text(yaml.safe_dump(good_doc()), encoding="utf-8")

    reg = HypothesisRegistry(root, store=store, params=params, requests_dir=tmp_path / "requests")
    assert len(reg.load("pending")) == 1

    reg.move("H-2026-9001", "running", run_id="R-1", detail="cycle 1")
    reg.move("H-2026-9001", "done", run_id="R-1", detail="blocked:data")

    assert reg.paths("pending") == []
    assert len(reg.paths("done")) == 1
    trans = store.transitions("H-2026-9001")
    assert list(trans["from_state"]) == ["pending", "running"]
    assert list(trans["to_state"]) == ["running", "done"]


def test_move_refuses_to_overwrite_an_existing_registration(params, store, tmp_path):
    root = tmp_path / "hypotheses"
    for state in ("pending", "done"):
        (root / state).mkdir(parents=True)
        (root / state / "H-2026-9001.yaml").write_text(yaml.safe_dump(good_doc()), encoding="utf-8")
    reg = HypothesisRegistry(root, store=store, params=params)
    with pytest.raises(FileExistsError):
        reg.move("H-2026-9001", "done")


def test_triage_splits_ready_blocked_and_rejected(params, store, tmp_path):
    root = tmp_path / "hypotheses"
    (root / "pending").mkdir(parents=True)
    (root / "pending" / "H-2026-9001.yaml").write_text(yaml.safe_dump(good_doc()), encoding="utf-8")
    (root / "pending" / "H-2026-9002.yaml").write_text(
        yaml.safe_dump(good_doc(id="H-2026-9002", data_required=["NOT_IN_SNAPSHOT"])),
        encoding="utf-8",
    )
    (root / "pending" / "H-2026-9003.yaml").write_text(
        yaml.safe_dump(good_doc(id="H-2026-9003", rationale="too short")), encoding="utf-8"
    )
    reg = HypothesisRegistry(root, store=store, params=params, requests_dir=tmp_path / "requests")
    out = reg.triage({"DGS2", "DGS10"})
    assert [h.id for h in out["ready"]] == ["H-2026-9001"]
    assert [h.id for h, _, _ in out["blocked"]] == ["H-2026-9002"]
    assert len(out["rejected"]) == 1
    assert (tmp_path / "requests" / "H-2026-9002.yaml").exists()


# --- the registered set ------------------------------------------------------


def test_every_registered_hypothesis_parses(params):
    reg = HypothesisRegistry(params=params)
    hyps = reg.load("pending")
    assert len(hyps) >= 10, "SUBSTRATE section 6 lists 11 families; see decisions/proposed/0009"


def test_registered_set_covers_every_substrate_family(params):
    """
    KICKOFF item 5: at least one per family listed in SUBSTRATE section 6.
    Measurement hypotheses are excluded: they have no section 6 family.
    """
    reg = HypothesisRegistry(params=params)
    covered = {h.family for h in reg.load("pending") if not h.is_measurement}
    assert covered == set(FAMILIES), f"families with no hypothesis: {set(FAMILIES) - covered}"


def test_no_registered_hypothesis_claims_an_unverified_citation(params):
    """
    Every registered hypothesis is `adaptation` or `novel`, because no reference
    resolver is enabled and a citation nobody checked is worse than none.
    """
    reg = HypothesisRegistry(params=params)
    for h in reg.load("pending"):
        assert h.provenance in ("adaptation", "novel")
        assert h.reference is None


def test_kind_defaults_to_signal_so_the_existing_eleven_are_unambiguous(params):
    h = validate_hypothesis(good_doc(), params)
    assert h.kind == "signal"
    assert not h.is_measurement
    assert h.objective == "net_ir"


def measurement_doc(**over):
    doc = good_doc(
        kind="measurement",
        family="exposure_estimation",
        target_axis="loadings",
        signal="shrunk_to_peer_mean",
        data_required=[],
    )
    doc.update(over)
    return doc


def test_a_measurement_hypothesis_is_ranked_on_a_different_objective(params):
    """
    decisions/0016: choosing a loading estimator on the strategy's own objective
    would select the mapping on the outcome. The two classes are ranked apart.
    """
    h = validate_hypothesis(measurement_doc(), params)
    assert h.is_measurement
    assert h.objective == "loading_fidelity"


def test_the_two_kinds_have_separate_vocabularies(params):
    """
    A conviction hypothesis has no SUBSTRATE section 6 family and targets no
    exposure axis. Validating it against the signal vocabulary would force a
    proposer to file it under something false.
    """
    validate_hypothesis(measurement_doc(family="conviction", target_axis="conviction"), params)

    with pytest.raises(HypothesisRejected, match="signal hypothesis"):
        validate_hypothesis(good_doc(family="conviction"), params)
    with pytest.raises(HypothesisRejected, match="measurement hypothesis"):
        validate_hypothesis(measurement_doc(family="policy_rates"), params)
    with pytest.raises(HypothesisRejected, match="measurement hypothesis"):
        validate_hypothesis(measurement_doc(target_axis="duration_typo"), params)


def test_a_measurement_hypothesis_may_need_nothing_from_a_vendor(params):
    """
    Its inputs are the harness's own outputs. The field must still be present,
    so "needs nothing" is an explicit claim rather than an omission.
    """
    h = validate_hypothesis(measurement_doc(data_required=[]), params)
    assert h.data_required == []
    assert not check_data(h, set()).blocked

    doc = measurement_doc()
    doc.pop("data_required")
    with pytest.raises(HypothesisRejected, match="data_required"):
        validate_hypothesis(doc, params)

    with pytest.raises(HypothesisRejected, match="data_required"):
        validate_hypothesis(good_doc(data_required=[]), params)


def test_portfolio_vetoes_do_not_apply_to_a_measurement_run(params):
    """
    A measurement run produces no portfolio, so turnover and drawdown are not
    passes -- they are not applicable, and the store must show the difference.
    """
    from vetoes import VETOES

    signal = validate_hypothesis(good_doc(), params)
    measurement = validate_hypothesis(measurement_doc(), params)

    assert set(signal.applicable_vetoes(list(VETOES))) == set(VETOES)
    applicable = set(measurement.applicable_vetoes(list(VETOES)))
    assert {
        "turnover",
        "cash",
        "positions",
        "tracking_error",
        "active_drawdown",
    } & applicable == set()
    assert {"lookahead", "frequency", "coverage", "multiple_testing", "direction"} <= applicable


def test_an_unknown_kind_is_rejected(params):
    with pytest.raises(HypothesisRejected, match="kind"):
        validate_hypothesis(good_doc(kind="vibes"), params)


def test_the_registry_holds_both_kinds(params):
    reg = HypothesisRegistry(params=params)
    hyps = reg.load("pending")
    kinds = {h.kind for h in hyps}
    assert kinds == {"signal", "measurement"}
    measurement = [h for h in hyps if h.is_measurement]
    assert len(measurement) >= 1
    assert all(h.objective == "loading_fidelity" for h in measurement)


def test_registered_ids_are_unique(params):
    reg = HypothesisRegistry(params=params)
    ids = [h.id for h in reg.load("pending")]
    assert len(ids) == len(set(ids))
