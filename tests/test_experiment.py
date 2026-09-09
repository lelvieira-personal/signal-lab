"""
`run_experiment()` and the pipeline validation. SUBSTRATE section 2.

The point of these tests is that a missing link says WHICH link, and that a
validation run can never be mistaken for a result.
"""

from __future__ import annotations

import pandas as pd
import pytest

from signal_lab.harness.experiment import (
    SIGNAL_MODULES,
    ExperimentBlocked,
    ExposureMatrixMissing,
    OptimiserMissing,
    SignalModuleMissing,
    resolve_exposures,
    resolve_signal_module,
    run_experiment,
    validate_pipeline,
)
from signal_lab.harness.hypotheses import HypothesisRegistry


@pytest.fixture(scope="module")
def a_hypothesis(params):
    return HypothesisRegistry(params=params).load("pending")[0]


# --- the missing links name themselves ---------------------------------------


def test_no_signal_module_is_registered_yet():
    """
    Empty by design. SUBSTRATE section 5.6 keeps the search shut until the macro
    block lands, so a module registered now could not be run anyway.
    """
    assert SIGNAL_MODULES == {}


def test_a_missing_signal_module_names_the_signal(a_hypothesis):
    with pytest.raises(SignalModuleMissing, match=a_hypothesis.signal):
        resolve_signal_module(a_hypothesis)


def test_every_blocked_status_is_distinct_and_specific():
    """
    'blocked: no signal module for real_policy_rate_change_3m' tells the owner
    what to build next. 'blocked: no engine' told them nothing.
    """
    statuses = {
        cls.status for cls in (SignalModuleMissing, ExposureMatrixMissing, OptimiserMissing)
    }
    assert len(statuses) == 3
    assert all(s.startswith("blocked:") and s != "blocked:unknown" for s in statuses)
    assert all(issubclass(c, ExperimentBlocked) for c in (SignalModuleMissing, OptimiserMissing))


def test_the_exposure_matrix_raises_rather_than_returning_an_identity(params):
    """
    A silent identity matrix would make every exposure equal its weight, the
    risk decomposition would report pure idiosyncratic risk, and nothing would
    look broken.
    """
    with pytest.raises(ExposureMatrixMissing, match="characteristic map"):
        resolve_exposures(None, params)


def test_a_real_hypothesis_blocks_on_the_first_missing_link(a_hypothesis, panel, params):
    with pytest.raises(SignalModuleMissing) as exc:
        run_experiment(a_hypothesis, None, panel, None, params)
    assert exc.value.status == "blocked:no_signal_module"


# --- the validation path -----------------------------------------------------


@pytest.fixture(scope="module")
def validation(panel, params):
    return validate_pipeline(panel, "R-test-validate", params, target_ir=0.5, target_te=0.04)


def test_validation_recovers_the_planted_ir_exactly(validation):
    assert validation.metrics["ir_recovery_error"] < 1e-9
    assert validation.metrics["net_ir"] == pytest.approx(validation.metrics["planted_ir"])


def test_validation_is_tagged_so_it_cannot_rank(validation):
    assert validation.status == "validation"


def test_validation_populates_every_artifact_the_report_needs(validation):
    expected = {
        "weights",
        "active_returns",
        "net_returns",
        "turnover",
        "cost_drag",
        "exposures",
        "active_drawdown",
        "tracking_error",
    }
    assert expected <= set(validation.artifacts)
    for name, frame in validation.artifacts.items():
        assert isinstance(frame, pd.DataFrame) and not frame.empty, name


def test_validation_records_both_turnover_conventions(validation):
    turnover = validation.artifacts["turnover"]
    assert {"traded_notional", "one_way"} == set(turnover.columns)
    assert turnover["traded_notional"].to_numpy() == pytest.approx(
        turnover["one_way"].to_numpy() * 2
    ), "decisions/0017: traded notional is twice the one-way figure, always"


def test_validation_metrics_never_include_gross_ir(validation):
    assert not any("gross" in k for k in validation.metrics), "decisions/0004"
    assert "cost_drag" in validation.metrics


def test_the_vetoes_run_on_the_validation_path_and_bite(validation, params):
    """
    The planted path trades ~500% of NAV a year, so the turnover veto must kill
    it. A veto set that passed everything on a deliberately extreme path would
    not be enforcing anything.
    """
    from vetoes import apply_vetoes

    verdicts, failure = apply_vetoes(validation.run_context, params)
    assert len(verdicts) == 11
    assert failure == "turnover", {k: v.detail for k, v in verdicts.items() if not v.passed}
    assert verdicts["positions"].passed and verdicts["active_drawdown"].passed


def test_the_veto_inputs_that_need_a_signal_fail_closed(validation, params):
    """
    A planted weight path has no signal behind it, so coverage, lookahead and
    the statistical gates cannot be evaluated -- and must fail rather than pass.
    """
    from vetoes import apply_vetoes

    verdicts, _ = apply_vetoes(validation.run_context, params)
    for name in ("coverage", "lookahead", "multiple_testing", "direction"):
        assert not verdicts[name].passed
        assert "cannot evaluate" in verdicts[name].detail


# --- the leaderboard must not rank a validation run --------------------------


def test_a_validation_run_is_kept_off_the_leaderboard(tmp_path, params, store):
    import sys

    sys.path.insert(0, str(tmp_path))
    from render.sources import StoreSource

    store.record_run(
        "V-1", status="validation", family="pipeline", data_snapshot_hash="h", params=params
    )
    store.record_metrics("V-1", {"net_ir": 9.99, "ir_recovery_error": 1e-16})
    store.record_run(
        "R-1", status="completed", family="trend", data_snapshot_hash="h", params=params
    )
    store.record_metrics("R-1", {"net_ir": 0.20})

    data = StoreSource(
        db_path=store.db_path, artifacts_dir=store.artifacts_dir, params=params
    ).load()
    ids = [r["run_id"] for r in data.runs]
    assert "R-1" in ids
    assert "V-1" not in ids, "a 9.99 IR from a planted path must never top the leaderboard"
    assert data.n_runs == 1
    assert any("validated" in note for note in data.notes), "but it is reported, not hidden"
