"""The results store. SUBSTRATE section 11: append-only, and provenance on every run."""

from __future__ import annotations

import sqlite3
from datetime import UTC

import pandas as pd
import pytest

from signal_lab.results.store import StoreError, Verdict, new_run_id


def a_run(store, run_id="R-1", params=None, **kw):
    return store.record_run(
        run_id,
        status=kw.pop("status", "completed"),
        data_snapshot_hash=kw.pop("data_snapshot_hash", "snap123"),
        params=params,
        **kw,
    )


def test_every_run_records_its_provenance(store, params):
    a_run(store, family="trend", aggregation="shrunk z-score mean", seed=7, params=params)
    row = store.list_runs().iloc[0]
    assert row["params_version"] == params.params_version
    assert row["params_hash"] == params.params_hash
    assert row["data_snapshot_hash"] == "snap123"
    assert row["seed"] == 7


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE runs SET status = 'x'",
        "DELETE FROM runs",
        "UPDATE metrics SET value = 9",
        "DELETE FROM metrics",
        "UPDATE verdicts SET passed = 1",
        "DELETE FROM verdicts",
        "UPDATE hypothesis_transitions SET to_state = 'done'",
        "DELETE FROM hypothesis_transitions",
    ],
)
def test_history_cannot_be_rewritten(store, params, statement):
    a_run(store, params=params)
    store.record_metrics("R-1", {"net_ir": 0.3})
    store.record_verdicts("R-1", {"turnover": Verdict(True, "ok")})
    store.record_transition("H-1", "pending", "running")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        with store.connect() as conn:
            conn.execute(statement)


def test_recording_the_same_run_twice_is_refused(store, params):
    a_run(store, params=params)
    with pytest.raises(StoreError, match="append-only"):
        a_run(store, params=params)


def test_metrics_and_verdicts_need_their_run_first(store):
    with pytest.raises(StoreError, match="no such run"):
        store.record_metrics("R-ghost", {"net_ir": 0.3})
    with pytest.raises(StoreError, match="no such run"):
        store.record_verdicts("R-ghost", {"turnover": Verdict(True)})


def test_list_runs_joins_metrics_and_verdicts(store, params):
    a_run(store, "R-a", params=params)
    a_run(store, "R-b", params=params)
    store.record_metrics("R-a", {"net_ir": 0.42, "te": 4.1})
    store.record_verdicts("R-a", {"turnover": Verdict(True, "ok"), "cash": Verdict(True, "ok")})
    store.record_verdicts("R-b", {"turnover": Verdict(False, "260% over 150%")})

    runs = store.list_runs().set_index("run_id")
    assert runs.loc["R-a", "net_ir"] == 0.42
    assert runs.loc["R-a", "passed"]
    assert not runs.loc["R-b", "passed"]
    assert runs.loc["R-b", "verdict_details"]["turnover"].startswith("260%")


def test_a_run_with_no_verdicts_has_not_passed(store, params):
    """Vetoes are applied to every run; absence of verdicts is not a pass."""
    a_run(store, params=params)
    assert not store.list_runs().loc[0, "passed"]


def test_list_runs_offers_no_ordering_by_metric(store):
    """
    SUBSTRATE section 12 allows one sort, the objective, and it belongs to the
    render layer. A store that offered order_by would be offering selection.
    """
    import inspect

    args = set(inspect.signature(store.list_runs).parameters)
    assert not (args & {"order_by", "sort", "sort_by", "ascending", "rank"})


def test_artifacts_round_trip_as_parquet(store, params):
    a_run(store, params=params)
    frame = pd.DataFrame({"w": [0.1, 0.2]}, index=pd.date_range("2010-01-04", periods=2, freq="B"))
    store.write_artifact("R-1", "weights", frame)
    loaded = store.load_artifacts("R-1")
    assert set(loaded) == {"weights"}
    assert loaded["weights"]["w"].tolist() == [0.1, 0.2]


def test_load_artifacts_is_empty_not_an_error_when_there_are_none(store, params):
    a_run(store, params=params)
    assert store.load_artifacts("R-1") == {}


def test_transitions_are_ordered_and_complete(store):
    store.record_transition("H-1", "pending", "running", "R-1")
    store.record_transition("H-1", "running", "done", "R-1", "killed by turnover")
    trans = store.transitions("H-1")
    assert list(trans["to_state"]) == ["running", "done"]
    assert trans.iloc[1]["detail"] == "killed by turnover"


def test_summary_counts_runs_kills_and_tokens(store, params):
    a_run(store, "R-a", cost_tokens=1000, params=params)
    a_run(store, "R-b", status="killed", killed_by="budget", cost_tokens=500, params=params)
    s = store.summary()
    assert s["n_runs"] == 2 and s["n_killed"] == 1 and s["cost_tokens"] == 1500


def test_run_ids_are_sortable_by_time():
    from datetime import datetime

    early = new_run_id(when=datetime(2026, 1, 1, tzinfo=UTC))
    late = new_run_id(when=datetime(2026, 6, 1, tzinfo=UTC))
    assert early < late
