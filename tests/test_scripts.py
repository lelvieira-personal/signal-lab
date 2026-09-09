"""
Snapshots and the scripts. The cycle is exercised end to end with no engine.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

from signal_lab.harness.snapshot import (  # noqa: E402
    build_snapshot,
    hash_directory,
    load_snapshot,
    verify_snapshot,
)


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    from signal_lab.params import get_params

    out = tmp_path_factory.mktemp("snapshots")
    return build_snapshot("test-v1", "synthetic", get_params(), snapshots_dir=out)


def test_snapshot_hashes_its_contents(snapshot):
    assert len(snapshot.data_snapshot_hash) == 64
    assert hash_directory(snapshot.path) == snapshot.data_snapshot_hash


def test_snapshot_manifest_carries_full_provenance(snapshot, params):
    m = snapshot.manifest
    assert m["params_version"] == params.params_version
    assert m["params_hash"] == params.params_hash
    assert m["holdout_start"] == "2020-01-01"
    assert m["n_series"] == 100
    assert len(m["hedged_ids"]) == 6
    assert m["last_date"] < m["holdout_start"], "a snapshot never contains holdout dates"


def test_snapshot_verification_catches_a_changed_file(snapshot):
    ok, detail = verify_snapshot(snapshot)
    assert ok, detail
    (snapshot.path / "returns.parquet").write_bytes(b"tampered")
    ok, detail = verify_snapshot(snapshot)
    assert not ok and "changed on disk" in detail


def test_a_snapshot_is_immutable(tmp_path, params):
    build_snapshot("imm", "synthetic", params, snapshots_dir=tmp_path)
    with pytest.raises(FileExistsError, match="immutable"):
        build_snapshot("imm", "synthetic", params, snapshots_dir=tmp_path)


def test_available_ids_covers_returns_and_macro(snapshot):
    ids = snapshot.available_ids()
    assert len(ids) >= 100
    assert any(i.startswith("SYN") for i in ids)
    assert any("." in i for i in ids), "macro series are addressable too"


def test_missing_snapshot_says_how_to_build_it(tmp_path):
    with pytest.raises(FileNotFoundError, match="build_snapshot"):
        load_snapshot("nope", snapshots_dir=tmp_path)


# --- scripts -----------------------------------------------------------------


def test_build_snapshot_script_runs(tmp_path, capsys):
    import build_snapshot as script

    rc = script.main(["--id", "cli-v1", "--overwrite", "--snapshots-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "data_snapshot_hash" in out and "tiers" in out


def test_nightly_cycle_records_blocked_not_a_fake_veto_failure(tmp_path, capsys):
    """
    The important behaviour of the phase 0 cycle: with no engine, a hypothesis
    is recorded as blocked, never as killed by a veto it was never measured
    against. See decisions/proposed/0011.
    """
    import nightly_cycle as cycle

    from signal_lab.params import get_params
    from signal_lab.results.store import ResultsStore

    params = get_params()
    build_snapshot("cyc-v1", "synthetic", params, snapshots_dir=tmp_path)
    db = tmp_path / "runs.db"
    rc = cycle.main(["--snapshot", "cyc-v1", "--db", str(db), "--snapshots-dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "search gate: CLOSED" in out, "the section 5.6 gate must be visible"
    assert "model roles: enabled" in out, (
        "decisions/0007 assigned every role and both ceilings, so the roles are "
        "configured even though phase 0 makes no model call"
    )

    runs = ResultsStore(db).list_runs()
    assert len(runs) == 11
    assert set(runs["status"]) <= {"blocked:data", "blocked:no_engine"}
    assert not runs["passed"].any()
    for _, r in runs.iterrows():
        assert r["verdicts"] == {}, "no veto was evaluated, so none is recorded"


def test_nightly_cycle_refuses_a_tampered_snapshot(tmp_path, capsys):
    import nightly_cycle as cycle

    from signal_lab.params import get_params

    build_snapshot("tamp-v1", "synthetic", get_params(), snapshots_dir=tmp_path)
    (tmp_path / "tamp-v1" / "returns.parquet").write_bytes(b"tampered")
    rc = cycle.main(
        ["--snapshot", "tamp-v1", "--db", str(tmp_path / "r.db"), "--snapshots-dir", str(tmp_path)]
    )
    assert rc == 1
    assert "does not match its manifest" in capsys.readouterr().out


def test_run_experiment_is_the_only_entry_point_and_it_raises():
    """SUBSTRATE section 2: experiments run through run_experiment() and only it."""
    import nightly_cycle as cycle

    with pytest.raises(cycle.EngineNotImplemented, match="phase 1"):
        cycle.run_experiment(None, None, None, 0)


def test_digest_writes_a_markdown_summary(tmp_path, params, store):
    import digest as digest_script

    from signal_lab.harness.hypotheses import HypothesisRegistry
    from signal_lab.results.store import Verdict

    store.record_run(
        "R-a", status="completed", data_snapshot_hash="h", family="trend", params=params
    )
    store.record_metrics("R-a", {"net_ir": 0.33})
    store.record_verdicts("R-a", {"turnover": Verdict(True, "ok")})
    store.record_run(
        "R-b",
        status="killed",
        killed_by="turnover",
        data_snapshot_hash="h",
        family="carry",
        params=params,
    )

    registry = HypothesisRegistry(store=store, params=params)
    text = digest_script.build_digest(store, params, registry, tmp_path)
    assert "# Signal Lab — digest" in text
    assert params.params_hash[:12] in text
    assert "What died and why" in text and "turnover" in text
    body = text.split("## Waiting on the owner")[0]
    assert "gross" not in body.lower(), "gross IR does not appear among the digest's metrics"
    assert "decisions/proposed" in text
