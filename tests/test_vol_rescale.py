"""
The volatility overlay: fast volatilities on the slow correlation.

`results/audit/_probe/TE-20260917-bbg1` measured a 156-week equal-weighted
covariance failing to see a volatility spike -- an audit book's ex-ante TE went
5.2% -> 6.0% -> 6.0% across 2007-2009 while its realised active volatility went
6.6% -> 12.2% -> 3.7%. `rescale_volatility` is the opt-in response.

The first test is the one that matters: the default path has to be unchanged,
because every number in every run before 2026-09-17 was produced by it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.audit.ladder import AuditCell
from signal_lab.portfolio.covariance import (
    ewma_weights,
    ledoit_wolf,
    rescale_volatility,
    trailing_covariance,
)


def _panel(periods: int = 200, series: int = 6, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    common = rng.normal(0.0, 0.01, size=(periods, 1))
    idiosyncratic = rng.normal(0.0, 0.005, size=(periods, series))
    values = common + idiosyncratic
    index = pd.date_range("2010-01-01", periods=periods, freq="W-FRI")
    return pd.DataFrame(values, index=index, columns=[f"S{i}" for i in range(series)])


def test_default_trailing_covariance_is_byte_identical() -> None:
    """No halflife means the estimate every earlier run used, to the bit."""
    frame = _panel()
    before = trailing_covariance(frame, frame.index[-1], window=156)
    after = trailing_covariance(frame, frame.index[-1], window=156, vol_halflife=None)
    assert before.matrix.to_numpy().tobytes() == after.matrix.to_numpy().tobytes()
    assert before.shrinkage == after.shrinkage


def test_default_cell_has_no_halflife_and_an_unchanged_key() -> None:
    """A cell key written before this existed still names the same cell.

    HANDOFF task 42 (decisions/0042): the DEFAULT now follows params, which carry
    the 26-week scalar overlay, so it is `vol_halflife=None` -- explicit "no
    overlay" -- that keeps every pre-task-42 key."""
    cell = AuditCell(ic=0.05, horizon=13, seed=0, vol_halflife=None, shadow_form="trailing")
    assert cell.vol_halflife is None
    assert cell.key() == "ic0.05_h13_s0_c1.0_tnone_rnone"
    assert "_vhl26" in AuditCell(ic=0.05, horizon=13, seed=0, vol_halflife=26).key()


def test_rescale_leaves_the_correlation_exactly_alone() -> None:
    """The whole point: one channel moves. The correlation is not it."""
    frame = _panel()
    cov = ledoit_wolf(frame)
    rescaled = rescale_volatility(cov, frame, halflife=26)
    np.testing.assert_allclose(
        rescaled.correlation().to_numpy(), cov.correlation().to_numpy(), atol=1e-12
    )
    assert rescaled.shrinkage == cov.shrinkage
    assert rescaled.n_observations == cov.n_observations


def test_rescale_puts_the_exponentially_weighted_volatility_on_the_diagonal() -> None:
    frame = _panel()
    cov = ledoit_wolf(frame)
    halflife = 26.0
    rescaled = rescale_volatility(cov, frame, halflife=halflife)
    w = ewma_weights(len(frame), halflife)
    x = frame.to_numpy(dtype=float)
    expected = w @ (x - w @ x) ** 2
    np.testing.assert_allclose(np.diag(rescaled.matrix.to_numpy()), expected, rtol=1e-10)


def test_a_long_halflife_converges_on_the_equal_weighted_estimate() -> None:
    """A sanity check on the direction of the knob, not a property of the panel."""
    frame = _panel()
    cov = ledoit_wolf(frame)
    slow = rescale_volatility(cov, frame, halflife=1e6)
    # Not exact: with a halflife this long the decay factor is 1 - 7e-7 and the
    # weights differ from 1/n in the last few digits.
    np.testing.assert_allclose(
        np.diag(slow.matrix.to_numpy()), np.diag(cov.matrix.to_numpy()), rtol=1e-5
    )


def test_a_short_halflife_tracks_a_volatility_spike_the_window_cannot_see() -> None:
    """The defect the probe measured, reproduced small and then fixed."""
    frame = _panel(periods=200, series=4, seed=3)
    frame.iloc[-10:] *= 5.0  # a spike in the last ten weeks of a 200-week window
    cov = ledoit_wolf(frame)
    fast = rescale_volatility(cov, frame, halflife=8)
    calm = np.sqrt(np.diag(ledoit_wolf(frame.iloc[:-10]).matrix.to_numpy()))
    slow_sd = np.sqrt(np.diag(cov.matrix.to_numpy()))
    fast_sd = np.sqrt(np.diag(fast.matrix.to_numpy()))
    # The equal-weighted window barely moves off the calm level; the overlay does.
    assert (slow_sd / calm).max() < 2.0
    assert (fast_sd / calm).min() > 2.5


def test_a_non_positive_halflife_is_refused() -> None:
    with pytest.raises(ValueError, match="halflife must be positive"):
        ewma_weights(10, 0.0)


def test_weights_sum_to_one_and_favour_the_newest_observation() -> None:
    w = ewma_weights(100, 10.0)
    assert w.sum() == pytest.approx(1.0)
    assert w[-1] > w[0]
    assert w[-1] / w[-11] == pytest.approx(2.0)  # ten back is half the weight
