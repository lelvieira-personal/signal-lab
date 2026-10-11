"""
All nine vetoes of SUBSTRATE section 10 (decisions/0038 removed `turnover`).

Each gets a passing case, a failing case and a boundary case, because a
threshold implemented as `<` instead of `<=` is a silent, permanent, invisible
change to the mandate. `lookahead` and `frequency` are additionally tested
against the synthetic panel's known break dates, so they are exercised on the
shape of data they will actually see.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.harness.run_context import RunContext
from vetoes import VETO_ORDER, VETOES, apply_vetoes, first_failure
from vetoes.rules import (
    veto_cash,
    veto_coverage,
    veto_direction,
    veto_frequency,
    veto_lookahead,
    veto_multiple_testing,
    veto_positions,
    veto_risk_calibration,
    veto_seed_stability,
)

DATES = pd.bdate_range("2010-01-04", periods=52)


def ctx(**kw) -> RunContext:
    return RunContext(run_id="R-test", **kw)


def honest_parameters(n: int = 2) -> pd.DataFrame:
    """Loadings fitted through the Friday they are used on (decisions/0055)."""
    days = pd.bdate_range("2010-03-05", periods=n, freq="W-FRI")
    return pd.DataFrame(
        {
            "instrument": [f"I{i}" for i in range(n)],
            "parameter": "loadings",
            "store_week": days,
            "fitted_through": days,
            "used_on_date": days,
        }
    )


# --- the set itself ----------------------------------------------------------


def test_exactly_the_nine_vetoes_of_substrate_section_10_as_amended():
    """SUBSTRATE section 10, less active_drawdown (decisions/0026) and turnover
    (decisions/0038), with tracking_error swapped for risk_calibration
    (decisions/0030)."""
    assert set(VETOES) == {
        "cash",
        "risk_calibration",
        "positions",
        "coverage",
        "lookahead",
        "frequency",
        "seed_stability",
        "multiple_testing",
        "direction",
    }
    assert len(VETOES) == 9
    assert "active_drawdown" not in VETOES, "decisions/0026 removed it"
    assert "turnover" not in VETOES, "decisions/0038 removed it: disclosed, never vetoed"


def test_every_veto_is_ordered(params):
    assert sorted(VETO_ORDER(params)) == sorted(VETOES)


def test_evaluation_order_follows_the_substrate_table(params):
    """decisions/0005: the section 10 table order is authoritative."""
    order = VETO_ORDER(params)
    assert order[:4] == ["cash", "risk_calibration", "positions", "coverage"]
    assert order[-1] == "direction"


# --- 1. cash -----------------------------------------------------------------


def test_cash_passes_fails_and_boundary(params):
    cap = params.require("vetoes.cash.max_weight")
    assert veto_cash(ctx(cash_weights=pd.Series([0.0, 0.12], index=DATES[:2])), params).passed
    assert not veto_cash(ctx(cash_weights=pd.Series([0.0, 0.31], index=DATES[:2])), params).passed
    assert veto_cash(ctx(cash_weights=pd.Series([cap], index=DATES[:1])), params).passed
    assert not veto_cash(ctx(cash_weights=pd.Series([cap + 1e-6], index=DATES[:1])), params).passed


def test_cash_without_input_fails_closed(params):
    assert not veto_cash(ctx(), params).passed


# --- 2. risk_calibration -----------------------------------------------------

CAL_DATES = pd.date_range("2010-01-08", periods=156, freq="W-FRI")
EX_ANTE = 0.05


def _active_with_bias(bias_by_year: dict[int, float], dates=CAL_DATES, ex_ante=EX_ANTE):
    """Active returns whose annual bias statistic is exactly what is asked for.

    The veto divides by sigma_ex_ante SHIFTED one period, so the first reading
    of the series has no sizing to be judged against and drops out. Building the
    z series first and inverting makes the intent of each test readable: the
    number in the dict is the number the veto should report.
    """
    rng = np.random.default_rng(11)
    z = pd.Series(0.0, index=dates)
    usable = dates[1:]  # the first reading has no prior sizing and is dropped
    for year, target in bias_by_year.items():
        mask = pd.Series(usable.year == year, index=usable)
        raw = rng.standard_normal(int(mask.sum()))
        raw = raw - raw.mean()
        z.loc[usable[mask.to_numpy()]] = raw / raw.std(ddof=1) * target
    return z * (ex_ante / np.sqrt(52.0))


def _cal_ctx(bias_by_year, **kw):
    active = _active_with_bias(bias_by_year)
    return ctx(
        active_returns=active,
        te_ex_ante=pd.Series(EX_ANTE, index=CAL_DATES),
        rebalances_per_year=52.0,
        **kw,
    )


def test_risk_calibration_passes_fails_and_boundary(params):
    cap = params.require("vetoes.risk_calibration.max_worst_annual_bias")
    years = [2010, 2011, 2012]
    assert veto_risk_calibration(_cal_ctx({y: 1.0 for y in years}), params).passed
    assert not veto_risk_calibration(_cal_ctx({y: cap + 0.2 for y in years}), params).passed
    assert veto_risk_calibration(_cal_ctx({y: cap for y in years}), params).passed
    assert not veto_risk_calibration(_cal_ctx({y: cap + 1e-6 for y in years}), params).passed


def test_risk_calibration_reads_the_worst_year_not_the_average(params):
    """The whole point of decisions/0030, and the reason 0027's statistic failed.

    A book calibrated on average but running double its sized risk for one year
    is the Bloomberg 2008 case: full-sample 0.92-1.01, worst year 2.03.
    """
    c = _cal_ctx({2010: 0.62, 2011: 2.03, 2012: 0.70})
    v = veto_risk_calibration(c, params)
    assert not v.passed
    assert "2011" in v.detail
    full = float(pd.Series(c.active_returns).std(ddof=1) / (EX_ANTE / np.sqrt(52.0)))
    assert full < params.require("vetoes.risk_calibration.max_worst_annual_bias"), (
        "the full-sample reading must be the one that would have passed"
    )


def test_risk_calibration_does_not_read_a_year_too_short_to_judge(params):
    """A standard deviation of a handful of numbers is not evidence."""
    dates = pd.date_range("2010-11-05", periods=60, freq="W-FRI")  # 2010 has 9
    rng = np.random.default_rng(3)
    z = pd.Series(rng.standard_normal(len(dates)), index=dates)
    z[dates.year == 2010] *= 40.0  # a wild short year that must be ignored
    z[dates.year == 2011] = z[dates.year == 2011] / z[dates.year == 2011].std(ddof=1)
    active = z * (EX_ANTE / np.sqrt(52.0))
    c = ctx(
        active_returns=active,
        te_ex_ante=pd.Series(EX_ANTE, index=dates),
        rebalances_per_year=52.0,
    )
    v = veto_risk_calibration(c, params)
    assert v.passed, v.detail
    assert "2010" not in v.detail


def test_risk_calibration_without_the_ex_ante_series_fails_closed(params):
    """The input decisions/0030 added. Without it there is no ratio to read."""
    active = _active_with_bias({2010: 1.0, 2011: 1.0, 2012: 1.0})
    v = veto_risk_calibration(ctx(active_returns=active), params)
    assert not v.passed
    assert "te_ex_ante" in v.detail


def test_risk_calibration_without_returns_fails_closed(params):
    assert not veto_risk_calibration(ctx(), params).passed


def test_risk_calibration_with_no_readable_year_fails_closed(params):
    dates = pd.date_range("2010-01-08", periods=12, freq="W-FRI")
    c = ctx(
        active_returns=pd.Series(0.001, index=dates),
        te_ex_ante=pd.Series(EX_ANTE, index=dates),
    )
    v = veto_risk_calibration(c, params)
    assert not v.passed
    assert "usable readings" in v.detail


def test_risk_calibration_reports_the_year_and_the_full_sample_beside_it(params):
    v = veto_risk_calibration(_cal_ctx({2010: 0.9, 2011: 1.1, 2012: 1.0}), params)
    assert v.passed
    assert "2011" in v.detail and "full-sample" in v.detail and "3 years read" in v.detail


# --- 3. positions ------------------------------------------------------------


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


# --- 4. coverage -------------------------------------------------------------


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


# --- 5. lookahead ------------------------------------------------------------


def test_lookahead_passes_when_nothing_is_used_early(params):
    usage = pd.DataFrame(
        {
            "series_id": ["growth.gdp_intuitive"] * 2,
            "period_end": pd.to_datetime(["2010-01-31", "2010-02-28"]),
            "knowledge_date": pd.to_datetime(["2010-03-01", "2010-03-29"]),
            "used_on_date": pd.to_datetime(["2010-03-05", "2010-04-02"]),
        }
    )
    v = veto_lookahead(ctx(observation_usage=usage, parameter_usage=honest_parameters()), params)
    assert v.passed and "none used before" in v.detail
    assert "2 observations" in v.detail and "2 estimated parameters" in v.detail


def test_lookahead_fails_on_a_single_peek(params):
    usage = pd.DataFrame(
        {
            "series_id": ["growth.gdp_intuitive"],
            "period_end": pd.to_datetime(["2010-01-31"]),
            "knowledge_date": pd.to_datetime(["2010-03-01"]),
            "used_on_date": pd.to_datetime(["2010-02-15"]),
        }
    )
    v = veto_lookahead(ctx(observation_usage=usage, parameter_usage=honest_parameters()), params)
    assert not v.passed and "14 days" in v.detail


def test_lookahead_boundary_same_day_use_is_allowed(params):
    day = pd.Timestamp("2010-03-01")
    usage = pd.DataFrame(
        {
            "series_id": ["x"],
            "period_end": [pd.Timestamp("2010-01-31")],
            "knowledge_date": [day],
            "used_on_date": [day],
        }
    )
    honest = honest_parameters()
    assert veto_lookahead(ctx(observation_usage=usage, parameter_usage=honest), params).passed
    early = usage.copy()
    early["used_on_date"] = [day - pd.Timedelta(1, "D")]
    assert not veto_lookahead(ctx(observation_usage=early, parameter_usage=honest), params).passed


def test_lookahead_against_the_synthetic_vintage_panel(macro, params):
    """
    The real shape: as_of produces a usage log that must pass, and reading the
    panel by period_end instead of knowledge_date must fail.
    """
    as_of_date = pd.Timestamp("2008-06-30")
    honest = macro.usage_log(as_of_date)
    assert len(honest) > 0
    assert veto_lookahead(
        ctx(observation_usage=honest, parameter_usage=honest_parameters()), params
    ).passed

    # The mistake this veto exists to catch: treating period_end as if it were
    # the knowledge date, which uses every number the moment its period ends.
    cheating = macro.frame[macro.frame["period_end"] <= as_of_date][
        ["series_id", "period_end", "knowledge_date"]
    ].copy()
    cheating["used_on_date"] = cheating["period_end"]
    v = veto_lookahead(ctx(observation_usage=cheating, parameter_usage=honest_parameters()), params)
    assert not v.passed, "using a number on its period end date is a peek at the release"


def test_lookahead_without_input_fails_closed(params):
    assert not veto_lookahead(ctx(), params).passed


def _observations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "series_id": ["x"],
            "period_end": [pd.Timestamp("2010-01-31")],
            "knowledge_date": [pd.Timestamp("2010-03-01")],
            "used_on_date": [pd.Timestamp("2010-03-05")],
        }
    )


def test_loadings_fitted_one_day_after_they_are_used_fail_and_the_same_day_passes(params):
    """decisions/0055: fitted_through later than used_on_date is a loading that saw the future."""
    usage = honest_parameters(3)
    assert veto_lookahead(
        ctx(observation_usage=_observations(), parameter_usage=usage), params
    ).passed

    late = usage.copy()
    late.loc[1, "fitted_through"] = late.loc[1, "used_on_date"] + pd.Timedelta(days=1)
    v = veto_lookahead(ctx(observation_usage=_observations(), parameter_usage=late), params)
    assert not v.passed
    assert "1 estimated parameter(s) fitted past the date they were used" in v.detail
    assert "worst by 1 days" in v.detail and "I1" in v.detail

    earlier = usage.copy()
    earlier["fitted_through"] = earlier["used_on_date"] - pd.Timedelta(days=4)
    assert veto_lookahead(
        ctx(observation_usage=_observations(), parameter_usage=earlier), params
    ).passed


def test_lookahead_fails_closed_without_parameter_usage(params):
    """Either table absent, empty or short of a column is a missing input, never a pass."""
    obs = _observations()
    for missing in (None, honest_parameters(0)):
        v = veto_lookahead(ctx(observation_usage=obs, parameter_usage=missing), params)
        assert not v.passed and "parameter_usage" in v.detail
    for col in ("fitted_through", "used_on_date"):
        v = veto_lookahead(
            ctx(observation_usage=obs, parameter_usage=honest_parameters().drop(columns=[col])),
            params,
        )
        assert not v.passed and f"parameter_usage.{col}" in v.detail
    # the observation half is still required
    assert not veto_lookahead(ctx(parameter_usage=honest_parameters()), params).passed


def test_a_parameter_row_with_a_missing_date_fails_as_undated(params):
    for col in ("fitted_through", "used_on_date"):
        bad = honest_parameters(3)
        bad.loc[0, col] = pd.NaT
        v = veto_lookahead(ctx(observation_usage=_observations(), parameter_usage=bad), params)
        assert not v.passed and "undated" in v.detail, col


def test_a_peek_in_each_half_reports_both(params):
    obs = _observations()
    obs["used_on_date"] = [pd.Timestamp("2010-02-01")]
    late = honest_parameters(2)
    late["fitted_through"] = late["used_on_date"] + pd.Timedelta(days=7)
    v = veto_lookahead(ctx(observation_usage=obs, parameter_usage=late), params)
    assert not v.passed
    assert "observation(s) used before their knowledge date" in v.detail
    assert "estimated parameter(s) fitted past the date they were used" in v.detail


# --- 6. frequency ------------------------------------------------------------


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


# --- 7. seed_stability -------------------------------------------------------


def test_seed_stability_passes_fails_and_boundary(params):
    cap = params.require("vetoes.seed_stability.max_ir_range")
    assert veto_seed_stability(ctx(seed_irs={1: 0.30, 2: 0.36, 3: 0.33}), params).passed
    assert not veto_seed_stability(ctx(seed_irs={1: 0.10, 2: 0.55}), params).passed
    assert veto_seed_stability(ctx(seed_irs={1: 0.20, 2: 0.20 + cap}), params).passed
    assert not veto_seed_stability(ctx(seed_irs={1: 0.20, 2: 0.20 + cap + 1e-6}), params).passed


def test_seed_stability_needs_at_least_two_seeds(params):
    assert not veto_seed_stability(ctx(seed_irs={1: 0.30}), params).passed


# --- 8. multiple_testing -----------------------------------------------------


# decisions/0043: the verdict carries the procedure, g and the shuffle count k.
# The context key stays `romano_wolf` for every procedure.
# decisions/0045: the verdict also carries n_tests (>= 8 here, so g = 2) and standardise.
GFWER = {
    "procedure": "romano_wolf_gfwer",
    "g": 2,
    "n_shuffles": 100,
    "n_tests": 120,
    "standardise": True,
}


def test_multiple_testing_passes_when_the_stepdown_rejects(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, "n_tests": 120, **GFWER}
    assert veto_multiple_testing(ctx(romano_wolf=rw), params).passed


def test_multiple_testing_fails_when_the_stepdown_does_not_reject(params):
    rw = {"rejected": False, "fwer_alpha": 0.05, "n_tests": 120, **GFWER}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "did not reject" in v.detail


def test_multiple_testing_rejects_a_verdict_from_a_looser_alpha(params):
    """The boundary that matters: a stepdown run at 10% is not this test."""
    rw = {"rejected": True, "fwer_alpha": 0.10, **GFWER}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "0.1" in v.detail


def test_multiple_testing_rejects_a_verdict_from_another_procedure(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, "procedure": "bonferroni"}
    assert not veto_multiple_testing(ctx(romano_wolf=rw), params).passed


def test_multiple_testing_rejects_the_retired_single_fwer_verdict(params):
    """A g = 1 `romano_wolf` verdict is not the test params now require."""
    rw = {
        "rejected": True,
        "fwer_alpha": 0.05,
        "procedure": "romano_wolf",
        "g": 1,
        "n_shuffles": 100,
    }
    assert not veto_multiple_testing(ctx(romano_wolf=rw), params).passed


def test_multiple_testing_without_input_fails_closed(params):
    assert not veto_multiple_testing(ctx(), params).passed


def test_multiple_testing_fails_on_the_wrong_g(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, **{**GFWER, "g": 3}}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "g=3" in v.detail and "g=2" in v.detail


def test_multiple_testing_fails_on_too_few_shuffles(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, **{**GFWER, "n_shuffles": 99}}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "99" in v.detail and "100" in v.detail


def test_multiple_testing_fails_closed_when_g_is_missing(params):
    rw = {"rejected": True, "fwer_alpha": 0.05, **{k: x for k, x in GFWER.items() if k != "g"}}
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "romano_wolf.g" in v.detail


def test_multiple_testing_fails_closed_when_n_shuffles_is_missing(params):
    rw = {
        "rejected": True,
        "fwer_alpha": 0.05,
        **{k: x for k, x in GFWER.items() if k != "n_shuffles"},
    }
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "romano_wolf.n_shuffles" in v.detail


# --- decisions/0045: small searches are gated at g = 1 -------------------------


def test_the_veto_passes_a_single_test_verdict_at_g1_and_fails_it_at_g2(params):
    one = {"rejected": True, "fwer_alpha": 0.05, **{**GFWER, "n_tests": 1}}
    assert veto_multiple_testing(ctx(romano_wolf={**one, "g": 1}), params).passed
    v = veto_multiple_testing(ctx(romano_wolf={**one, "g": 2}), params)
    assert not v.passed and "g=2" in v.detail and "g=1" in v.detail


def test_the_veto_switches_to_g2_at_the_small_search_floor(params):
    below = {"rejected": True, "fwer_alpha": 0.05, **{**GFWER, "n_tests": 7, "g": 1}}
    at = {"rejected": True, "fwer_alpha": 0.05, **{**GFWER, "n_tests": 8}}
    assert veto_multiple_testing(ctx(romano_wolf=below), params).passed
    assert veto_multiple_testing(ctx(romano_wolf=at), params).passed
    assert not veto_multiple_testing(ctx(romano_wolf={**at, "g": 1}), params).passed


def test_the_veto_fails_a_verdict_with_no_n_tests(params):
    rw = {
        "rejected": True,
        "fwer_alpha": 0.05,
        **{k: x for k, x in GFWER.items() if k != "n_tests"},
    }
    v = veto_multiple_testing(ctx(romano_wolf=rw), params)
    assert not v.passed and "romano_wolf.n_tests" in v.detail


def test_the_veto_fails_a_verdict_with_no_standardise_or_standardise_false(params):
    base = {"rejected": True, "fwer_alpha": 0.05, **GFWER}
    missing = {k: x for k, x in base.items() if k != "standardise"}
    v = veto_multiple_testing(ctx(romano_wolf=missing), params)
    assert not v.passed and "romano_wolf.standardise" in v.detail
    v = veto_multiple_testing(ctx(romano_wolf={**base, "standardise": False}), params)
    assert not v.passed and "standardise" in v.detail


# --- 9. direction -----------------------------------------------------------


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
        active_returns=_active_with_bias({2010: 0.95, 2011: 1.02, 2012: 0.98}),
        te_ex_ante=pd.Series(EX_ANTE, index=CAL_DATES),
        weights=weights_with(25),
        signal_availability=availability(0.95, 0.97),
        estimation_universe=None,
        observation_usage=pd.DataFrame(
            {
                "series_id": ["x"],
                "period_end": [pd.Timestamp("2010-01-31")],
                "knowledge_date": [pd.Timestamp("2010-03-01")],
                "used_on_date": [pd.Timestamp("2010-03-05")],
            }
        ),
        parameter_usage=honest_parameters(),
        return_contributions=contributions_for(panel, ids, +30),
        series_meta=panel.meta,
        seed_irs={1: 0.30, 2: 0.34},
        romano_wolf={
            "rejected": True,
            "fwer_alpha": 0.05,
            "n_tests": 90,
            **GFWER,
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
    assert len(verdicts) == 9
    assert all(v.passed for v in verdicts.values())


def test_apply_vetoes_records_every_verdict_not_only_the_failure(panel, params):
    cap = int(params.require("vetoes.positions.max_nonzero"))
    c = full_context(
        panel, cash_weights=pd.Series(0.35, index=DATES), weights=weights_with(cap + 1)
    )
    verdicts, failure = apply_vetoes(c, params)
    assert len(verdicts) == 9
    failed = {k for k, v in verdicts.items() if not v.passed}
    assert failed == {"cash", "positions"}, "both breaches must be visible, not only the first"
    assert failure == "cash", "first failure follows the configured order"


def test_apply_vetoes_returns_first_failure_in_configured_order(panel, params):
    c = full_context(
        panel,
        cash_weights=pd.Series(0.35, index=DATES),
        observation_usage=pd.DataFrame(
            {
                "series_id": ["x"],
                "period_end": [pd.Timestamp("2010-01-31")],
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
    assert len(rows.loc[0, "verdicts"]) == 9


def test_a_crashing_veto_fails_rather_than_passing(panel, params, monkeypatch):
    from vetoes import registry

    def explode(ctx, params=None):
        raise RuntimeError("boom")

    monkeypatch.setitem(registry.VETOES, "cash", explode)
    verdicts, failure = registry.apply_vetoes(full_context(panel), params)
    assert not verdicts["cash"].passed
    assert "RuntimeError" in verdicts["cash"].detail
    assert failure == "cash"


def test_first_failure_is_none_when_all_pass():
    from signal_lab.results.store import Verdict

    assert first_failure({"a": Verdict(True), "b": Verdict(True)}, ["a", "b"]) is None
