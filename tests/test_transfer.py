"""The transfer coefficient and the alpha migration it needs. decisions/0033."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from signal_lab.audit import transfer as tr
from signal_lab.harness.engine import constant_exposures, run_walk_forward


def _spd(n: int, seed: int = 0) -> np.ndarray:
    m = np.random.default_rng(seed).normal(size=(n, n))
    return m @ m.T / n + np.eye(n) * 0.5


def test_the_book_proportional_to_the_unconstrained_optimum_transfers_fully():
    omega = _spd(8)
    a = np.random.default_rng(1).normal(size=8)
    w_star = np.linalg.solve(omega, a)
    got = tr.coefficients(a, 3.0 * w_star, omega)
    assert got["full"] == pytest.approx(1.0)
    assert got["alignment"] == pytest.approx(1.0), "B is 1 if and only if w is proportional to w*"


def test_the_full_matrix_form_is_a_cosine_so_never_above_one_and_can_fall_below_zero():
    omega = _spd(10, seed=3)
    rng = np.random.default_rng(4)
    a = rng.normal(size=10)
    for _ in range(50):
        w = rng.normal(size=10)
        assert abs(tr.coefficients(a, w, omega)["full"]) <= 1.0 + 1e-12
    assert tr.coefficients(a, -np.linalg.solve(omega, a), omega)["full"] == pytest.approx(-1.0)


def test_with_no_correlations_the_three_forms_agree():
    omega = np.diag([0.5, 1.0, 2.0, 4.0, 1.5])
    rng = np.random.default_rng(5)
    a, w = rng.normal(size=5), rng.normal(size=5)
    got = tr.coefficients(a, w, omega)
    s = np.sqrt(np.diag(omega))
    # With Omega diagonal, a'w / (sqrt(a' Omega^-1 a) sqrt(w' Omega w)) is the
    # cosine of a/s and w*s, which is what the diagonal form correlates.
    cosine = float((a / s) @ (w * s)) / (np.linalg.norm(a / s) * np.linalg.norm(w * s))
    assert got["full"] == pytest.approx(cosine)
    assert got["condition"] == pytest.approx(4.0 / 0.5)


def test_the_active_covariance_is_the_solvers_active_variance():
    """w' Omega w must equal x' Sigma x for the solver's x = S w - b, or TC measures another book."""
    ids = ["A", "B", "C", "L1", "L2"]
    sigma = pd.DataFrame(_spd(5, seed=7), index=ids, columns=ids)
    hold, legs = ["A", "B", "C"], ["L1", "L2"]
    leg_w = pd.Series([0.5, 0.5], index=legs)
    omega = tr.active_covariance(sigma, hold, legs, leg_w)
    w = np.array([0.2, 0.5, 0.3])  # fully invested
    x = np.zeros(5)
    x[:3] = w
    x[3:] -= 0.5
    assert float(w @ omega @ w) == pytest.approx(float(x @ sigma.to_numpy() @ x))


def test_a_zero_alpha_book_has_no_full_reading_rather_than_a_wrong_one():
    omega = _spd(6)
    got = tr.coefficients(np.zeros(6), np.full(6, 1 / 6), omega)
    assert np.isnan(got["full"]) and np.isnan(got["diagonal"]) and np.isnan(got["alignment"])
    assert np.isfinite(got["condition"])


def test_a_singular_omega_is_reported_not_inverted():
    omega = np.ones((4, 4))  # rank one
    got = tr.coefficients(np.arange(4.0), np.full(4, 0.25), omega)
    assert got["condition"] > 1e12 or not np.isfinite(got["condition"])


# --- the migration: a rule MAY expose alpha() -------------------------------------


class _RuleWithAlpha:
    def __init__(self, ids):
        self.ids = list(ids)
        self.seen: list[pd.Timestamp] = []

    def __call__(self, date, _panel, drifted=None):
        self.seen.append(pd.Timestamp(date))
        return pd.Series(1.0 / len(self.ids), index=self.ids)

    def alpha(self):
        return pd.DataFrame(0.01, index=pd.DatetimeIndex(self.seen), columns=self.ids)


def _tiny(periods=8):
    dates = pd.date_range("2012-01-06", periods=periods, freq="W-FRI")
    ids = ["A", "B"]
    returns = pd.DataFrame(0.001, index=dates, columns=ids)
    from signal_lab.loaders.base import ReturnPanel

    return ReturnPanel(levels=(1.0 + returns).cumprod(), returns=returns, meta={}), dates, ids


def _run(rule):
    panel, dates, ids = _tiny()
    return run_walk_forward(
        panel,
        rule,
        pd.Series(0.0005, index=dates),
        constant_exposures(pd.DataFrame(0.0, index=ids, columns=["f0"])),
    )


def test_a_rule_that_exposes_its_alpha_puts_it_on_the_path():
    path = _run(_RuleWithAlpha(["A", "B"]))
    assert path.alpha is not None
    assert list(path.alpha.columns) == ["A", "B"]
    assert path.alpha.index.is_monotonic_increasing


def test_a_rule_without_alpha_leaves_the_transfer_coefficient_unevaluated_not_defaulted():
    ids = ["A", "B"]

    def rule(date, _panel, drifted=None):
        return pd.Series(1.0 / len(ids), index=ids)

    path = _run(rule)
    assert path.alpha is None
    row = tr.path_transfer(path, SimpleNamespace(), SimpleNamespace())
    assert row["transfer_n_dates"] == 0
    assert all(np.isnan(row[k]) for k in tr.ROW_KEYS if k != "transfer_n_dates")


def test_a_non_callable_alpha_attribute_is_not_mistaken_for_the_method():
    class Rule:
        alpha = pd.Series([1.0])  # an attribute that happens to share the name

        def __call__(self, date, _panel, drifted=None):
            return pd.Series([0.5, 0.5], index=["A", "B"])

    assert _run(Rule()).alpha is None


def test_to_run_context_carries_alpha():
    from signal_lab.harness.engine import to_run_context

    rule = _RuleWithAlpha(["A", "B"])
    panel, dates, ids = _tiny()
    path = run_walk_forward(
        panel,
        rule,
        pd.Series(0.0005, index=dates),
        constant_exposures(pd.DataFrame(0.0, index=ids, columns=["f0"])),
    )
    assert to_run_context(path, "R-test", panel).alpha is not None


# --- the breadth read off the constrained ladder ----------------------------------


def _ladder(with_tc: bool) -> pd.DataFrame:
    rows = []
    for ic in (0.05, 0.10, 0.20):
        row = {"tag": "base", "horizon": 13, "ic": ic, "seed": 0, "net_ir": 2.0 * ic}
        if with_tc:
            row["transfer_coefficient"] = 0.5
        rows.append(row)
    return pd.DataFrame(rows)


def test_ladder_breadth_divides_the_slope_by_the_measured_tc():
    from signal_lab.audit.ladder import ladder_breadth

    out = ladder_breadth(_ladder(with_tc=True)).iloc[0]
    assert out["ir_per_unit_ic"] == pytest.approx(2.0)
    assert out["ladder_breadth"] == pytest.approx((2.0 / 0.5) ** 2)


def test_ladder_breadth_is_blank_where_no_tc_was_measured():
    from signal_lab.audit.ladder import ladder_breadth

    assert np.isnan(ladder_breadth(_ladder(with_tc=False)).iloc[0]["ladder_breadth"])
