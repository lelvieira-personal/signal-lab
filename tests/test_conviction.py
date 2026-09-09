"""
Conviction measures, and the conviction-scaled tracking-error penalty.

SUBSTRATE section 4; decisions/0019. The owner's worked example is the anchor:
a three-state regime model at [0.40, 0.30, 0.30] has barely decided anything,
one at [0.70, 0.20, 0.10] has.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from signal_lab.harness.conviction import (
    conviction_comparison,
    conviction_series,
    dispersion_conviction,
    entropy_conviction,
    max_probability_conviction,
)
from signal_lab.harness.objective import (
    ObjectiveNotConfigured,
    te_coefficient,
    tracking_error_penalty,
)
from signal_lab.params import PARAM_FILES, load_params

WEAK = [0.40, 0.30, 0.30]
STRONG = [0.70, 0.20, 0.10]
UNIFORM = [1 / 3, 1 / 3, 1 / 3]

MEASURES = (entropy_conviction, max_probability_conviction)


def with_te_coefficients(tmp_path, params, low, high):
    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "constraints.yaml"
    target.write_text(
        target.read_text()
        .replace("coefficient_low_conviction: null", f"coefficient_low_conviction: {low}")
        .replace("coefficient_high_conviction: null", f"coefficient_high_conviction: {high}")
    )
    return load_params(tmp_path)


# --- the measures ------------------------------------------------------------


@pytest.mark.parametrize("measure", MEASURES)
def test_the_owners_example_orders_correctly(measure):
    assert measure(WEAK) < measure(STRONG)


@pytest.mark.parametrize("measure", MEASURES)
def test_uniform_is_zero_and_certainty_is_one(measure):
    assert measure(UNIFORM) == pytest.approx(0.0, abs=1e-9)
    assert measure([1.0, 0.0, 0.0]) == pytest.approx(1.0)


@pytest.mark.parametrize("measure", MEASURES)
def test_conviction_is_direction_agnostic(measure):
    """
    A confident risk-off call is as convicted as a confident risk-on one.
    Conviction sizes the tilt; the view sets its sign. Collapsing the two would
    make [0.1, 0.2, 0.7] look like weak enthusiasm rather than strong pessimism.
    """
    assert measure([0.7, 0.2, 0.1]) == pytest.approx(measure([0.1, 0.2, 0.7]))


@pytest.mark.parametrize("measure", MEASURES)
def test_conviction_is_bounded(measure):
    for vector in (UNIFORM, WEAK, STRONG, [0.95, 0.03, 0.02], [1.0, 0.0, 0.0]):
        assert 0.0 <= measure(vector) <= 1.0


@pytest.mark.parametrize("measure", MEASURES)
def test_unnormalised_input_is_normalised_not_rejected(measure):
    assert measure([70, 20, 10]) == pytest.approx(measure(STRONG))


def test_entropy_registers_ruling_a_state_out_and_max_probability_barely_does():
    """
    The substantive difference between the two. [0.45, 0.45, 0.10] has decided
    something -- the third state is out -- without picking a winner. Entropy
    sees it; the modal measure almost cannot, because the mode barely moved.
    """
    split = [0.45, 0.45, 0.10]
    assert entropy_conviction(split) > entropy_conviction(WEAK) * 5
    assert max_probability_conviction(split) < max_probability_conviction(WEAK) * 2


def test_entropy_discriminates_far_harder_at_the_weak_end():
    """
    Calibration, recorded as a test because it decides how much a weak signal is
    allowed to move the book: ~30x between the owner's two examples on entropy,
    ~5x on the modal measure. decisions/0019.
    """
    e = entropy_conviction(STRONG) / entropy_conviction(WEAK)
    m = max_probability_conviction(STRONG) / max_probability_conviction(WEAK)
    assert e > 20 and m < 10


@pytest.mark.parametrize("bad", [[], [1.0], [-0.1, 0.6, 0.5], [0.0, 0.0, 0.0]])
def test_malformed_probability_vectors_are_refused(bad):
    with pytest.raises(ValueError):
        entropy_conviction(bad)


def test_conviction_series_applies_row_wise():
    frame = pd.DataFrame([UNIFORM, WEAK, STRONG], index=pd.date_range("2010-01-01", periods=3))
    out = conviction_series(frame, "entropy")
    assert out.is_monotonic_increasing
    with pytest.raises(ValueError, match="unknown conviction method"):
        conviction_series(frame, "vibes")


def test_dispersion_is_a_different_quantity_from_certainty():
    """
    SUBSTRATE section 4 says "conviction dispersion"; the owner's example is
    about certainty. They are not the same measurement and can disagree, which
    is why decisions/0019 asks which one the penalty reads.
    """
    tight = pd.Series([0.1, -0.1, 0.05, -0.05])
    wide = pd.Series([2.5, -2.0, 1.8, -2.2])
    assert dispersion_conviction(tight) < dispersion_conviction(wide)
    assert entropy_conviction(STRONG) > 0, "certainty is high here regardless of any dispersion"


def test_the_comparison_table_covers_both_measures():
    table = conviction_comparison({"weak": WEAK, "strong": STRONG})
    assert list(table.columns) == ["entropy", "max_probability"]
    assert (table.loc["strong"] > table.loc["weak"]).all()


# --- the conviction-scaled penalty -------------------------------------------


def test_the_te_penalty_refuses_while_the_coefficients_are_unset(params):
    with pytest.raises(ObjectiveNotConfigured, match="conviction"):
        tracking_error_penalty(0.08, entropy_conviction(STRONG), params)


def test_te_is_dearer_at_low_conviction_than_at_high(tmp_path, params):
    configured = with_te_coefficients(tmp_path, params, low=8.0, high=2.0)
    assert te_coefficient(0.0, configured) == pytest.approx(8.0)
    assert te_coefficient(1.0, configured) == pytest.approx(2.0)
    assert te_coefficient(0.5, configured) == pytest.approx(5.0)

    weak_cost = tracking_error_penalty(0.08, entropy_conviction(WEAK), configured)
    strong_cost = tracking_error_penalty(0.08, entropy_conviction(STRONG), configured)
    assert weak_cost > strong_cost, "section 4: TE is cheap when conviction is high"


def test_the_coefficient_never_reaches_zero_however_confident(tmp_path, params):
    """
    The bound that matters. An overfit regime model reporting a spurious
    [0.99, 0.005, 0.005] must not be able to buy unlimited tracking error.
    """
    configured = with_te_coefficients(tmp_path, params, low=8.0, high=2.0)
    overconfident = entropy_conviction([0.99, 0.005, 0.005])
    assert overconfident > 0.9
    assert te_coefficient(overconfident, configured) >= 2.0


def test_the_penalty_is_one_sided_above_the_ceiling(tmp_path, params):
    configured = with_te_coefficients(tmp_path, params, low=8.0, high=2.0)
    cap = float(configured.require("constraints.tracking_error.max_trailing_3y"))
    assert tracking_error_penalty(cap * 0.5, 0.5, configured) == 0.0
    assert tracking_error_penalty(cap, 0.5, configured) == 0.0
    assert tracking_error_penalty(cap * 1.5, 0.5, configured) > 0.0


def test_a_forgotten_conviction_defaults_to_the_dear_end(tmp_path, params):
    """Forgetting the argument must penalise, not exempt."""
    configured = with_te_coefficients(tmp_path, params, low=8.0, high=2.0)
    assert tracking_error_penalty(0.09, params=configured) == pytest.approx(
        tracking_error_penalty(0.09, 0.0, configured)
    )


def test_inverted_coefficients_are_refused(tmp_path, params):
    """high > low would make TE dearer when the model is sure, inverting section 4."""
    inverted = with_te_coefficients(tmp_path, params, low=2.0, high=8.0)
    with pytest.raises(ObjectiveNotConfigured, match="CHEAPER"):
        te_coefficient(0.5, inverted)


def test_conviction_outside_the_unit_interval_is_clipped(tmp_path, params):
    configured = with_te_coefficients(tmp_path, params, low=8.0, high=2.0)
    assert te_coefficient(-5.0, configured) == pytest.approx(8.0)
    assert te_coefficient(np.inf, configured) == pytest.approx(2.0)
