"""
The standardisation mode of the planted truth (the probe of 2026-09-17).

Two claims are worth locking down. The default mode is the one every audit
before the probe ran, so it must be unchanged to the last bit -- otherwise the
probe's comparison is against a moving baseline. And the cross-sectional mode
must do what it says: no common component left, and a planted IC that still
comes back as the planted IC.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.audit.ladder import FRICTIONLESS, AuditCell
from signal_lab.audit.signals import (
    CROSS_SECTIONAL,
    POOLED,
    plant_signal,
    realised_ic,
    truth_decomposition,
)


def _panel(n_periods: int = 320, n_ids: int = 12, seed: int = 7) -> tuple[pd.DataFrame, pd.Series]:
    """A weekly panel with a deliberate common factor, so the two modes differ."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2005-01-07", periods=n_periods, freq="W-FRI")
    common = rng.normal(0.0, 0.010, size=(n_periods, 1))
    idio = rng.normal(0.0, 0.006, size=(n_periods, n_ids))
    weekly = pd.DataFrame(common + idio, index=dates, columns=[f"S{i:02d}" for i in range(n_ids)])
    benchmark = weekly.mean(axis=1)
    return weekly, benchmark


def _plant(mode: str, ic: float = 0.10, horizon: int = 13):
    weekly, benchmark = _panel()
    return plant_signal(
        weekly, benchmark, ic=ic, horizon=horizon, seed=3, vol_window=52, standardise=mode
    )


def test_the_default_mode_is_pooled_and_unchanged():
    weekly, benchmark = _panel()
    kwargs = {"ic": 0.10, "horizon": 13, "seed": 3, "vol_window": 52}
    default = plant_signal(weekly, benchmark, **kwargs)
    explicit = plant_signal(weekly, benchmark, standardise=POOLED, **kwargs)
    assert default.standardise == POOLED
    pd.testing.assert_frame_equal(default.score, explicit.score)
    pd.testing.assert_frame_equal(default.alpha, explicit.alpha)


def test_an_unknown_mode_is_refused():
    weekly, benchmark = _panel()
    with pytest.raises(ValueError, match="standardise must be one of"):
        plant_signal(
            weekly, benchmark, ic=0.1, horizon=13, seed=0, vol_window=52, standardise="per_date"
        )


def test_the_cross_sectional_mode_removes_the_common_component():
    pooled = _plant(POOLED)
    cross = _plant(CROSS_SECTIONAL)
    assert truth_decomposition(cross)["common_share"] < 1e-6
    # The panel has a real common factor, so the default mode keeps something.
    assert truth_decomposition(pooled)["common_share"] > truth_decomposition(cross)["common_share"]


def test_both_modes_deliver_the_planted_pooled_ic():
    for mode in (POOLED, CROSS_SECTIONAL):
        planted = _plant(mode, ic=0.10)
        assert realised_ic(planted)["pooled"] == pytest.approx(0.10, abs=5e-3)


def test_the_cross_sectional_mode_raises_the_usable_reading():
    """What the probe is for: the part of the signal a market-neutral book can spend."""
    pooled = realised_ic(_plant(POOLED))["cross_sectional_demeaned"]
    cross = realised_ic(_plant(CROSS_SECTIONAL))["cross_sectional_demeaned"]
    assert cross > pooled


def test_realised_ic_reports_four_readings():
    readings = realised_ic(_plant(POOLED))
    for key in ("pooled", "cross_sectional", "cross_sectional_pearson", "cross_sectional_demeaned"):
        assert -1.0 <= readings[key] <= 1.0


def test_the_cell_key_is_unchanged_in_the_default_mode():
    assert AuditCell(ic=0.1, horizon=13, seed=0).key() == "ic0.10_h13_s0_c1.0_tnone_rnone"
    assert (
        AuditCell(ic=0.1, horizon=13, seed=0, standardise=CROSS_SECTIONAL)
        .key()
        .endswith("_cross_sectional")
    )
    assert AuditCell(ic=0.1, horizon=13, seed=0, tag=FRICTIONLESS).key().endswith("_frictionless")
