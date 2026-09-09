"""
All ten vetoes of SUBSTRATE section 10.

Each gets a passing case, a failing case and a boundary case, because a
threshold implemented as `<` instead of `<=` is a silent, permanent, invisible
change to the mandate. `lookahead` and `frequency` are additionally tested
against the synthetic panel's known break dates, so they are exercised on the
shape of data they will actually see.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.harness.run_context import RunContext
from vetoes import VETO_ORDER, VETOES, apply_vetoes, first_failure
from vetoes.rules import (
    veto_active_drawdown,
    veto_cash,
    veto_coverage,
    veto_direction,
    veto_frequency,
    veto_lookahead,
    veto_multiple_testing,
    veto_positions,
    veto_seed_stability,
    veto_tracking_error,
    veto_turnover,
)

DATES = pd.bdate_range("2010-01-04", periods=52)


def ctx(**kw) -> RunContext:
    return RunContext(run_id="R-test", **kw)


# --- the set itself ----------------------------------------------------------


def test_exactly_the_eleven_vetoes_of_substrate_section_10_as_amended():
    """SUBSTRATE section 10 plus active_drawdown (decisions/0003)."""
    assert set(VETOES) == {
        "turnover",
        "cash",
        "tracking_error",
        "positions",
        "coverage",
        "lookahead",
        "frequency",
        "active_drawdown",
        "seed_stability",
        "multiple_testing",
        "direction",
    }
    assert len(VETOES) == 11


def test_every_veto_is_ordered(params):
    assert sorted(VETO_ORDER(params)) == sorted(VETOES)


def test_evaluation_order_follows_the_substrate_table(params):
    """decisions/0005: the section 10 table order is authoritative."""
    order = VETO_ORDER(params)
    assert order[:5] == ["turnover", "cash", "tracking_error", "positions", "coverage"]
    assert order[-1] == "direction"


# --- 1. turnover -------------------------------------------------------------


def test_turnover_passes_under_the_ceiling(params):
    c = ctx(turnover=pd.Series(0.02, index=DATES))  # 104% annualised
    assert veto_turnover(c, params).passed


def test_turnover_fails_over_the_ceiling(params):
    c = ctx(turnover=pd.Series(0.05, index=DATES))  # 260% annualised
    v = veto_turnover(c, params)
    assert not v.passed and "260" in v.detail


def test_turnover_boundary_is_inclusive(params):
    cap = params.require("vetoes.turnover.max_annualised")
    c = ctx(turnover=pd.Series(cap / 52.0, index=DATES))
    assert veto_turnover(c, params).passed, "the ceiling itself must pass"
    c_over = ctx(turnover=pd.Series(cap / 52.0 * 1.001, index=DATES))
    assert not veto_turnover(c_over, params).passed


def test_turnover_without_input_fails_closed(params):
    v = veto_turnover(ctx(), params)
    assert not v.passed and "cannot evaluate" in v.detail


# --- 2. cash -----------------------------------------------------------------


def test_cash_passes_fails_and_boundary(params):
    cap = params.require("vetoes.cash.max_weight")
    assert veto_cash(ctx(cash_weights=pd.Series([0.0, 0.12], index=DATES[:2])), params).passed
    assert not veto_cash(ctx(cash_weights=pd.Series([0.0, 0.31], index=DATES[:2])), params).passed
    assert veto_cash(ctx(cash_weights=pd.Series([cap], index=DATES[:1])), params).passed
    assert not veto_cash(ctx(cash_weights=pd.Series([cap + 1e-6], index=DATES[:1])), params).passed


def test_cash_without_input_fails_closed(params):
    assert not veto_cash(ctx(), params).passed


# --- 3. tracking_error -------------------------------------------------------


def test_tracking_error_passes_fails_and_boundary(params):
    cap = params.require("vetoes.tracking_error.max_trailing_3y")
    assert veto_tracking_error(ctx(te_trailing_3y=pd.Series([0.041, 0.052])), params).passed
    assert not veto_tracking_error(ctx(te_trailing_3y=pd.Series([0.041, 0.071])), params).passed
    assert veto_tracking_error(ctx(te_trailing_3y=pd.Series([cap])), params).passed
    assert not veto_tracking_error(ctx(te_trailing_3y=pd.Series([cap + 1e-9])), params).passed


def test_tracking_error_tolerates_one_episodic_excursion(params):
    """
    decisions/0003: the statistic is p95, not the maximum. A single excursion in
    a long run of compliant readings passes; a persistent breach does not. This
    is what "episodic excursions allowed" (SUBSTRATE section 4) has to mean if
    it means anything.
    """
    episodic = ctx(te_trailing_3y=pd.Series([0.04] * 40 + [0.075]))
    assert veto_tracking_error(episodic, params).passed

    persistent = ctx(te_trailing_3y=pd.Series([0.075] * 40 + [0.04]))
    assert not veto_tracking_error(persistent, params).passed


def test_tracking_error_reports_the_worst_reading_even_when_it_passes(params):
    """The excursion is not hidden just because it did not kill the run."""
    v = veto_tracking_error(ctx(te_trailing_3y=pd.Series([0.04] * 40 + [0.075])), params)
    assert v.passed and "worst reading 7.50%" in v.detail


def test_unknown_tracking_error_statistic_fails_closed(params, tmp_path):
    import shutil
    from pathlib import Path as _P

    from signal_lab.params import PARAM_FILES, load_params

    src = _P(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "vetoes.yaml"
    target.write_text(target.read_text().replace("statistic: p95", "statistic: vibes"))
    v = veto_tracking_error(ctx(te_trailing_3y=pd.Series([0.01])), load_params(tmp_path))
    assert not v.passed and "unknown tracking_error statistic" in v.detail


def test_tracking_error_all_nan_fails_closed(params):
    assert not veto_tracking_error(ctx(te_trailing_3y=pd.Series([np.nan, np.nan])), params).passed


# --- 4. positions ------------------------------------------------------------


def weights_with(n_nonzero: int, n_cols: int = 40) -> pd.DataFrame:
    frame = pd.DataFrame(0.0, index=DATES[:3], columns=[f"I{i}" for i in range(n_cols)])
    frame.iloc[1, :n_nonzero] = 1.0 / n_nonzero
    return frame


def test_positions_passes_fails_and_boundary(params):
    cap = int(params.require("vetoes.positions.max_nonzero"))
    assert veto_positions(ctx(weights=weights_with(cap - 5)), params).passed
    assert not veto_positions(ctx(weights=weights_with(cap + 1)), params).passed
    assert veto_positions(ctx(weights=weights_with(cap)), params).passed


def test_positions_without_input_fails_closed(params):
    assert not veto_positions(ctx(), params).passed


# --- 5. coverage -------------------------------------------------------------


def availability(universe_frac: float, date_frac: float, n_series: int = 50) -> pd.DataFrame:
    n_dates = 100
    frame = pd.DataFrame(
        False,
        index=pd.bdate_range("2010-01-04", periods=n_dates),
        columns=[f"S{i}" for i in range(n_series)],
    )
    n_good_dates = int(round(date_frac * n_dates))
    n_cols = int(round(universe_frac * n_series))
    frame.iloc[:n_good_dates, :n_cols] = True
    return frame


def test_coverage_passes_fails_and_boundary(params):
    good = ctx(signal_availability=availability(0.95, 0.97))
    assert veto_coverage(good, params).passed

    thin_universe = ctx(signal_availability=availability(0.60, 1.00))
    assert not veto_coverage(thin_universe, params).passed

    thin_dates = ctx(signal_availability=availability(0.95, 0.70))
    assert not veto_coverage(thin_dates, params).passed

    boundary = ctx(signal_availability=availability(0.80, 0.90))
    assert veto_coverage(boundary, params).passed, "80% of universe on 90% of dates must pass"


def test_coverage_measured_on_the_estimation_universe_only(params, panel):
    """
    Tradable-only series never estimate a signal (SUBSTRATE 5.2), so covering
    them must not rescue a signal that misses the estimation universe.
    """
    estimation = panel.estimation_universe()[:40]
    tradable = panel.by_tier("tradable-only")
    cols = estimation + tradable
    frame = pd.DataFrame(False, index=pd.bdate_range("2010-01-04", periods=100), columns=cols)
    frame.loc[:, tradable] = True
    frame.loc[:, estimation[:4]] = True
    c = ctx(signal_availability=frame, estimation_universe=estimation)
    assert not veto_coverage(c, params).passed


def test_coverage_without_input_fails_closed(params):
    assert not veto_coverage(ctx(), params).passed


# --- 6. lookahead ------------------------------------------------------------


def test_lookahead_passes_when_nothing_is_used_early(params):
    usage = pd.DataFrame(
        {
            "series_id": ["growth.gdp_intuitive"] * 2,
            "real_date": pd.to_datetime(["2010-01-31", "2010-02-28"]),
            "knowledge_date": pd.to_datetime(["2010-03-01", "2010-03-29"]),
            "used_on_date": pd.to_datetime(["2010-03-05", "2010-04-02"]),
        }
    )
    v = veto_lookahead(ctx(observation_usage=usage), params)
    assert v.passed and "none used before" in v.detail


def test_lookahead_fails_on_a_single_peek(params):
    usage = pd.DataFrame(
        {
            "series_id": ["growth.gdp_intuitive"],
            "real_date": pd.to_datetime(["2010-01-31"]),
            "knowledge_date": pd.to_datetime(["2010-03-01"]),
            "used_on_date": pd.to_datetime(["2010-02-15"]),
        }
    )
    v = veto_lookahead(ctx(observation_usage=usage), params)
    assert not v.passed and "14 days" in v.detail


def test_lookahead_boundary_same_day_use_is_allowed(params):
    day = pd.Timestamp("2010-03-01")
    usage = pd.DataFrame(
        {
            "series_id": ["x"],
            "real_date": [pd.Timestamp("2010-01-31")],
            "knowledge_date": [day],
            "used_on_date": [day],
        }
    )
    assert veto_lookahead(ctx(observation_usage=usage), params).passed
    early = usage.copy()
    early["used_on_date"] = [day - pd.Timedelta(1, "D")]
    assert not veto_lookahead(ctx(observation_usage=early), params).passed


def test_lookahead_against_the_synthetic_vintage_panel(macro, params):
    """
    The real shape: as_of produces a usage log that must pass, and reading the
    panel by real_date instead of knowledge_date must fail.
    """
    as_of_date = pd.Timestamp("2008-06-30")
    honest = macro.usage_log(as_of_date)
    assert len(honest) > 0
    assert veto_lookahead(ctx(observation_usage=honest), params).passed

    # The mistake this veto exists to catch: treating real_date as if it were
    # the knowledge date, which uses every number the moment its period ends.
    cheating = macro.frame[macro.frame["real_date"] <= as_of_date][
        ["series_id", "real_date", "knowledge_date"]
    ].copy()
    cheating["used_on_date"] = cheating["real_date"]
    v = veto_lookahead(ctx(observation_usage=cheating), params)
    assert not v.passed, "using a number on its period end date is a peek at the release"


def test_lookahead_without_input_fails_closed(params):
    assert not veto_lookahead(ctx(), params).passed


# --- 7. frequency ------------------------------------------------------------


def contributions_for(panel, series_ids, offset_days: int) -> pd.DataFrame:
    rows = []
    for sid in series_ids:
        start = pd.Timestamp(panel.meta[sid].true_daily_start)
        rows.append({"series_id": sid, "date": start + pd.Timedelta(offset_days, "D")})
    return pd.DataFrame(rows)


def test_frequency_passes_when_nothing_predates_its_daily_start(panel, params):
    ids = panel.series_ids[:20]
    c = ctx(return_contributions=contributions_for(panel, ids, +30), series_meta=panel.meta)
    v = veto_frequency(c, params)
    assert v.passed and "none before" in v.detail


def test_frequency_fails_on_a_month_end_splice(panel, params):
    """
    Against the synthetic panel's known break dates: the series that were
    month-end only before their break are exactly the ones whose pre-break
    observations must never contribute a daily return.
    """
    broken = [s for s, m in panel.meta.items() if m.month_end_only_before is not None]
    assert broken, "the synthetic panel must contain frequency breaks"
    rows = []
    for sid in broken[:5]:
        start = pd.Timestamp(panel.meta[sid].true_daily_start)
        rows.append({"series_id": sid, "date": start - pd.DateOffset(years=2)})
    c = ctx(return_contributions=pd.DataFrame(rows), series_meta=panel.meta)
    v = veto_frequency(c, params)
    assert not v.passed and "before the series' true daily start" in v.detail


def test_frequency_boundary_the_start_date_itself_is_allowed(panel, params):
    ids = panel.series_ids[:10]
    on_start = ctx(return_contributions=contributions_for(panel, ids, 0), series_meta=panel.meta)
    assert veto_frequency(on_start, params).passed
    day_before = ctx(return_contributions=contributions_for(panel, ids, -1), series_meta=panel.meta)
    assert not veto_frequency(day_before, params).passed


def test_frequency_without_input_fails_closed(params):
    assert not veto_frequency(ctx(), params).passed


# --- 8. active_drawdown ------------------------------------------------------


def active_with_drawdown(depth: float, n_down: int = 100, n_up: int = 400) -> pd.Series:
    """
    An active return stream whose max drawdown is `depth`, by construction.

    Built rather than sampled so the test asserts against arithmetic instead of
    against a random draw.
    """
    down = (1.0 - depth) ** (1.0 / n_down) - 1.0
    return pd.Series([down] * n_down + [0.0005] * n_up)


def test_active_drawdown_passes_fails_and_boundary(params):
    cap = float(params.require("vetoes.active_drawdown.te_multiple")) * float(
        params.require("vetoes.tracking_error.max_trailing_3y")
    )
    assert cap == pytest.approx(0.18)

    assert veto_active_drawdown(ctx(active_returns=active_with_drawdown(0.09)), params).passed
    assert not veto_active_drawdown(ctx(active_returns=active_with_drawdown(0.30)), params).passed

    at_cap = veto_active_drawdown(ctx(active_returns=active_with_drawdown(cap - 1e-6)), params)
    assert at_cap.passed, "the ceiling itself must pass"
    over = veto_active_drawdown(ctx(active_returns=active_with_drawdown(cap + 0.005)), params)
    assert not over.passed


def test_active_drawdown_scales_with_the_te_budget(params, tmp_path):
    """
    The coupling is the point: halve the TE budget and the drawdown ceiling
    halves with it, because the two are not independent quantities.
    """
    import shutil
    from pathlib import Path as _P

    from signal_lab.params import PARAM_FILES, load_params

    src = _P(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "vetoes.yaml"
    target.write_text(
        target.read_text().replace("max_trailing_3y: 0.060", "max_trailing_3y: 0.030")
    )
    tighter = load_params(tmp_path)

    series = active_with_drawdown(0.12)
    assert veto_active_drawdown(ctx(active_returns=series), params).passed
    assert not veto_active_drawdown(ctx(active_returns=series), tighter).passed


def test_active_drawdown_absolute_overrides_the_multiple(params, tmp_path):
    import shutil
    from pathlib import Path as _P

    from signal_lab.params import PARAM_FILES, load_params

    src = _P(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "vetoes.yaml"
    target.write_text(target.read_text().replace("absolute: null", "absolute: 0.10"))
    absolute = load_params(tmp_path)
    v = veto_active_drawdown(ctx(active_returns=active_with_drawdown(0.12)), absolute)
    assert not v.passed and "absolute" in v.detail


def test_active_drawdown_measures_the_active_stream_not_the_total(params):
    """
    A strategy that fell 40% alongside a benchmark that fell 40% has no active
    drawdown at all. Measuring the total return stream here would kill every
    run that lived through 2008.
    """
    flat_active = pd.Series([0.0] * 500)
    assert veto_active_drawdown(ctx(active_returns=flat_active), params).passed


def test_active_drawdown_without_input_fails_closed(params):
    assert not veto_active_drawdown(ctx(), params).passed


# --- 9. seed_stability -------------------------------------------------------


def test_seed_stability_passes_fails_and_boundary(params):
    cap = params.require("vetoes.seed_stability.max_ir_range")
    assert veto_seed_stability(ctx(seed_irs={1: 0.30, 2: 0.36, 3: 0.33}), params).passed
    assert not veto_seed_stability(ctx(seed_irs={1: 0.10, 2: 0.55}), params).passed
    assert veto_seed_stability(ctx(seed_irs={1: 0.20, 2: 0.20 + cap}), params).passed
    assert not veto_seed_stability(ctx(seed_irs={1: 0.20, 2: 0.20 + cap + 1e-6}), params).passed


def test_seed_stability_needs_at_least_two_seeds(params):
    assert not veto_seed_stability(ctx(seed_irs={1: 0.30}), params).passed


# --- 9. multiple_testing -----------------------------------------------------


def test_multiple_testing_passes_when_the_stepdown_rejects(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, "procedure": "romano_wolf", "n_tests": 120}
    assert veto_multiple_testing(ctx(romano_wolf=rw), params).passed


def test_multiple_testing_fails_when_the_stepdown_does_not_reject(params):
    rw = {"rejected": False, "fwer_alpha": 0.05, "procedure": "romano_wolf", "n_tests": 120}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "did not reject" in v.detail


def test_multiple_testing_rejects_a_verdict_from_a_looser_alpha(params):
    """The boundary that matters: a stepdown run at 10% is not this test."""
    rw = {"rejected": True, "fwer_alpha": 0.10, "procedure": "romano_wolf"}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "0.1" in v.detail


def test_multiple_testing_rejects_a_verdict_from_another_procedure(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, "procedure": "bonferroni"}
    assert not veto_multiple_testing(ctx(romano_wolf=rw), params).passed


def test_multiple_testing_without_input_fails_closed(params):
    assert not veto_multiple_testing(ctx(), params).passed


# --- 10. direction -----------------------------------------------------------


def test_direction_passes_on_a_match(params):
    c = ctx(preregistered_direction="negative", realised_direction="negative")
    assert veto_direction(c, params).passed


def test_direction_fails_on_a_flip_and_is_not_reinterpreted(params):
    """
    SUBSTRATE section 7: a result contradicting its stated direction is a
    failure, not a discovery with the sign flipped.
    """
    c = ctx(preregistered_direction="negative", realised_direction="positive")
    v = veto_direction(c, params)
    assert not v.passed and "pre-registered negative, realised positive" in v.detail


def test_direction_boundary_flat_is_not_a_match(params):
    c = ctx(preregistered_direction="positive", realised_direction="flat")
    assert not veto_direction(c, params).passed


def test_direction_without_input_fails_closed(params):
    assert not veto_direction(ctx(), params).passed


# --- apply_vetoes ------------------------------------------------------------


def full_context(panel, **overrides) -> RunContext:
    ids = panel.estimation_universe()[:25]
    base = dict(
        turnover=pd.Series(0.02, index=DATES),
        cash_weights=pd.Series(0.10, index=DATES),
        te_trailing_3y=pd.Series([0.045, 0.050]),
        active_returns=pd.Series([0.0004] * 300),
        weights=weights_with(25),
        signal_availability=availability(0.95, 0.97),
        estimation_universe=None,
        observation_usage=pd.DataFrame(
            {
                "series_id": ["x"],
                "real_date": [pd.Timestamp("2010-01-31")],
                "knowledge_date": [pd.Timestamp("2010-03-01")],
                "used_on_date": [pd.Timestamp("2010-03-05")],
            }
        ),
        return_contributions=contributions_for(panel, ids, +30),
        series_meta=panel.meta,
        seed_irs={1: 0.30, 2: 0.34},
        romano_wolf={
            "rejected": True,
            "fwer_alpha": 0.05,
            "procedure": "romano_wolf",
            "n_tests": 90,
        },
        preregistered_direction="positive",
        realised_direction="positive",
    )
    base.pop("estimation_universe")
    base.update(overrides)
    return RunContext(run_id="R-full", **base)


def test_apply_vetoes_passes_a_clean_run(panel, params):
    verdicts, failure = apply_vetoes(full_context(panel), params)
    assert failure is None, {k: v.detail for k, v in verdicts.items() if not v.passed}
    assert len(verdicts) == 11
    assert all(v.passed for v in verdicts.values())


def test_apply_vetoes_records_every_verdict_not_only_the_failure(panel, params):
    c = full_context(
        panel, cash_weights=pd.Series(0.35, index=DATES), turnover=pd.Series(0.06, index=DATES)
    )
    verdicts, failure = apply_vetoes(c, params)
    assert len(verdicts) == 11
    failed = {k for k, v in verdicts.items() if not v.passed}
    assert failed == {"cash", "turnover"}, "both breaches must be visible, not only the first"
    assert failure == "turnover", "first failure follows the configured order"


def test_apply_vetoes_returns_first_failure_in_configured_order(panel, params):
    c = full_context(
        panel,
        cash_weights=pd.Series(0.35, index=DATES),
        observation_usage=pd.DataFrame(
            {
                "series_id": ["x"],
                "real_date": [pd.Timestamp("2010-01-31")],
                "knowledge_date": [pd.Timestamp("2010-03-01")],
                "used_on_date": [pd.Timestamp("2010-02-01")],
            }
        ),
    )
    _, failure = apply_vetoes(c, params)
    assert failure == "cash", (
        "decisions/0005: the SUBSTRATE table order names cash before lookahead. "
        "The lookahead verdict is still recorded and still visible in the store."
    )
    verdicts, _ = apply_vetoes(c, params)
    assert not verdicts["lookahead"].passed, "the integrity breach is not lost, only not named"


def test_apply_vetoes_writes_verdicts_to_the_store(panel, params, store):
    ctx_full = full_context(panel)
    store.record_run(ctx_full.run_id, status="completed", data_snapshot_hash="h", params=params)
    apply_vetoes(ctx_full, params, store=store)
    rows = store.list_runs()
    assert rows.loc[0, "passed"]
    assert len(rows.loc[0, "verdicts"]) == 11


def test_a_crashing_veto_fails_rather_than_passing(panel, params, monkeypatch):
    from vetoes import registry

    def explode(ctx, params=None):
        raise RuntimeError("boom")

    monkeypatch.setitem(registry.VETOES, "turnover", explode)
    verdicts, failure = registry.apply_vetoes(full_context(panel), params)
    assert not verdicts["turnover"].passed
    assert "RuntimeError" in verdicts["turnover"].detail
    assert failure == "turnover"


def test_first_failure_is_none_when_all_pass():
    from signal_lab.results.store import Verdict

    assert first_failure({"a": Verdict(True), "b": Verdict(True)}, ["a", "b"]) is None
