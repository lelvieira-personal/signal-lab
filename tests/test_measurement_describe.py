"""
The descriptions of HANDOFF task 48, on synthetic frames with a planted truth.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.measurement import describe

FACTORS = ["f1", "f2"]


def _long(paths: dict[str, np.ndarray], weeks: pd.DatetimeIndex) -> pd.DataFrame:
    """paths[name] is (T, N, K)."""
    rows = []
    for name, b in paths.items():
        T, N, K = b.shape
        for i in range(N):
            for k in range(K):
                rows.append(
                    pd.DataFrame(
                        {
                            "instrument": f"I{i}",
                            "date": weeks,
                            "estimator": name,
                            "factor": FACTORS[k],
                            "loading": b[:, i, k],
                            "se": 0.1,
                        }
                    )
                )
    return pd.concat(rows, ignore_index=True)


def _weeks(n):
    return pd.date_range("2005-01-07", periods=n, freq="W-FRI")


def test_a_constant_loading_changes_by_zero():
    n, N = 120, 8
    base = np.random.default_rng(0).normal(size=(1, N, 2))
    b = np.repeat(base, n, axis=0)
    res = describe.stability(_long({"a": b, "b": b + 0.1}, _weeks(n)), ["a", "b"])
    for label in ("weekly_change", "annual_change"):
        for e in ("a", "b"):
            assert all(v == 0 for v in res[label]["abs"][e].values())


def test_a_planted_step_is_returned():
    n, N, step = 120, 8, 0.03
    walk = np.cumsum(np.full((n, N, 2), step), axis=0)
    other = np.cumsum(np.full((n, N, 2), 2 * step), axis=0)
    res = describe.stability(_long({"ols": walk, "x": other}, _weeks(n)), ["ols", "x"])
    assert np.allclose(list(res["weekly_change"]["abs"]["ols"].values()), step)
    assert np.allclose(list(res["annual_change"]["abs"]["ols"].values()), 52 * step)
    assert np.allclose(list(res["weekly_change"]["ratio"]["x"].values()), 2.0)
    assert np.isclose(res["summary"]["x"]["annual_change_ratio"], 2.0)


def test_two_identical_estimators_have_ratio_one_and_rank_agreement_one():
    n, N = 120, 12
    b = np.random.default_rng(1).normal(size=(n, N, 2)).cumsum(axis=0)
    res = describe.stability(_long({"ols": b, "same": b.copy()}, _weeks(n)), ["ols", "same"])
    assert np.allclose(list(res["weekly_change"]["ratio"]["same"].values()), 1.0)
    assert np.allclose(list(res["rank_agreement"]["same"].values()), 1.0)
    assert np.isclose(res["summary"]["same"]["rank_agreement"], 1.0)


def test_only_cells_where_every_estimator_has_a_loading_count():
    n, N = 120, 6
    b = np.random.default_rng(2).normal(size=(n, N, 2))
    late = b.copy()
    late[:60] = np.nan  # the second estimator starts at week 60
    res = describe.stability(_long({"ols": b, "late": late}, _weeks(n)), ["ols", "late"])
    assert res["cells"] == (n - 60) * N


def _fit_inputs(noise=0.0, seed=4, T=200, N=10, K=3):
    rng = np.random.default_rng(seed)
    F = rng.normal(size=(T, K)) * 0.01
    B = rng.normal(size=(1, N, K)) * 2 + np.zeros((T, N, K))
    R = np.full((T, N), np.nan)
    R[1:] = np.einsum("tnk,tk->tn", B[:-1], F[1:]) + noise * rng.normal(size=(T - 1, N))
    return R, F, B, np.full((T, N), 0.01)


def _metrics(R, F, betas, scale):
    N = R.shape[1]
    weeks = _weeks(len(R))
    slices = {"all": np.ones(len(R), dtype=bool)}
    return describe.fit_metrics(
        R,
        F,
        betas,
        scale,
        ["c1"] * (N // 2) + ["c2"] * (N - N // 2),
        [f"I{i}" for i in range(N)],
        weeks,
        slices,
    )


def test_true_loadings_with_no_noise_give_r2_one():
    R, F, B, scale = _fit_inputs()
    res = _metrics(R, F, {"truth": B}, scale)["estimators"]["truth"]
    assert np.isclose(res["pooled"]["r2_oos"], 1.0)
    assert np.isclose(res["pooled"]["huber_skill"], 1.0)
    assert np.isclose(res["xs_corr"]["mean"], 1.0)


def test_zero_loadings_give_zero_r2_and_zero_huber_skill():
    R, F, B, scale = _fit_inputs(noise=0.005)
    res = _metrics(R, F, {"zero": np.zeros_like(B)}, scale)["estimators"]["zero"]
    assert res["pooled"]["r2_oos"] == 0.0
    assert res["pooled"]["huber_skill"] == 0.0
    assert res["slices"]["all"]["r2_oos"] == 0.0


def test_factor_share_sums_to_one():
    R, F, B, scale = _fit_inputs(noise=0.005)
    res = _metrics(R, F, {"truth": B}, scale)["estimators"]["truth"]
    for key, shares in res["factor_share"].items():
        assert np.isclose(sum(shares), 1.0), key


def test_a_cell_without_a_loading_is_not_scored():
    R, F, B, scale = _fit_inputs()
    B2 = B.copy()
    B2[:100] = np.nan
    res = _metrics(R, F, {"late": B2, "full": B}, scale)
    assert res["cells"] == (len(R) - 1 - 100) * R.shape[1]
