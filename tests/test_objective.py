"""
The optimiser's objective. SUBSTRATE sections 3, 4 and 8; decisions/0018.

The load-bearing test here is the last one: a shadow cost must never reach the
reported return.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from signal_lab.harness.objective import (
    BPS,
    ObjectiveNotConfigured,
    ObjectiveTerms,
    annual_turnover_penalty,
    is_configured,
    tracking_error_penalty,
    turnover_penalty,
)
from signal_lab.params import PARAM_FILES, load_params


def variant(tmp_path, params, old, new):
    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "constraints.yaml"
    target.write_text(target.read_text().replace(old, new))
    return load_params(tmp_path)


# --- the penalty is one-sided ------------------------------------------------


def test_no_penalty_at_or_below_the_target(params):
    assert annual_turnover_penalty(0.50, params) == 0.0
    assert annual_turnover_penalty(1.00, params) == 0.0, "the target itself is free"


def test_the_penalty_is_linear_in_the_excess(params):
    at_125 = annual_turnover_penalty(1.25, params)
    at_150 = annual_turnover_penalty(1.50, params)
    at_200 = annual_turnover_penalty(2.00, params)
    assert at_150 == pytest.approx(2 * at_125)
    assert at_200 == pytest.approx(4 * at_125)


def test_the_coefficient_is_read_from_params_in_basis_points(params):
    coefficient = float(params.require("constraints.turnover.penalty.coefficient"))
    assert annual_turnover_penalty(1.50, params) == pytest.approx(coefficient * BPS * 0.5)


def test_the_per_period_penalty_is_the_annual_one_divided_by_the_year(params):
    assert turnover_penalty(1.50, params, periods_per_year=52.0) == pytest.approx(
        annual_turnover_penalty(1.50, params) / 52.0
    )


def test_the_penalty_at_the_veto_ceiling_bites_without_dominating(params):
    """
    An arithmetic guard, not an opinion. The calibration in decisions/0018 is
    that the shadow cost should be a material fraction of the real spread on the
    same trading -- enough to trade one thing against another, not enough to
    dominate. Too small and the term is inert; too large and it stops being a
    soft constraint. Changing the coefficient fails this and forces a look.
    """
    penalty_bp = annual_turnover_penalty(1.50, params) * 1e4
    mid_spread_bp = 1.50 * float(params.require("costs.buckets.mid.half_spread_bps"))
    ratio = penalty_bp / mid_spread_bp

    assert penalty_bp == pytest.approx(5.0, abs=0.01)
    assert 0.15 < ratio < 0.75, (
        f"shadow cost is {ratio:.0%} of the real spread at the ceiling; under 15% "
        f"the optimiser ignores it, over 75% it is a hard constraint wearing a "
        f"penalty's clothes. See decisions/0018."
    )


def test_the_penalty_is_zero_at_target_and_grows_from_there(params):
    """The soft-constraint shape: free up to the target, then priced."""
    assert annual_turnover_penalty(0.99, params) == 0.0
    assert annual_turnover_penalty(1.01, params) > 0.0
    assert annual_turnover_penalty(1.50, params) < annual_turnover_penalty(1.51, params)


# --- refusing rather than defaulting ----------------------------------------


def test_an_unset_turnover_coefficient_refuses(tmp_path, params):
    unset = variant(tmp_path, params, "coefficient: 10.0", "coefficient: null")
    with pytest.raises(ObjectiveNotConfigured, match="turnover.penalty.coefficient"):
        annual_turnover_penalty(1.50, unset)


def test_an_unsupported_penalty_form_refuses(tmp_path, params):
    odd = variant(tmp_path, params, "form: linear", "form: cubic")
    with pytest.raises(ObjectiveNotConfigured, match="cubic"):
        annual_turnover_penalty(1.50, odd)


def test_the_tracking_error_penalty_still_refuses(params):
    """decisions/0003: SUBSTRATE section 4 requires it and states no coefficient."""
    with pytest.raises(ObjectiveNotConfigured, match="tracking_error"):
        tracking_error_penalty(0.08, params)


def test_the_objective_reports_what_is_still_missing(params):
    ok, reason = is_configured(params)
    assert not ok
    assert "tracking-error" in reason and "turnover" not in reason


# --- the separation that matters ---------------------------------------------


def test_a_shadow_cost_never_reaches_the_reported_return():
    """
    decisions/0018. The penalty shapes the weights; the leaderboard sees actual
    costs only. Otherwise two runs with different coefficients are not
    comparable, which is the one thing the leaderboard exists to be.
    """
    terms = ObjectiveTerms(net_return=0.0040, turnover_penalty=0.0003, te_penalty=0.0011)

    assert terms.reported_net_return == pytest.approx(0.0040)
    assert terms.total == pytest.approx(0.0040 - 0.0003 - 0.0011)
    assert terms.total < terms.reported_net_return
    assert terms.reported_net_return != terms.total, (
        "if these were ever equal the shadow costs would be ranking runs"
    )


def test_two_runs_with_different_penalties_report_the_same_return():
    """The comparability property, stated as a test rather than as a comment."""
    gentle = ObjectiveTerms(net_return=0.0040, turnover_penalty=0.0001, te_penalty=0.0)
    harsh = ObjectiveTerms(net_return=0.0040, turnover_penalty=0.0090, te_penalty=0.0)
    assert gentle.reported_net_return == harsh.reported_net_return
    assert gentle.total != harsh.total
