"""
The characteristics builder and store (HANDOFF task 51, decisions/0049), on synthetic data only.
Nothing reads data/raw/, data/snapshots/ or the vendor's panels.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from signal_lab.characteristics import build, report, store
from signal_lab.harness.experiment import ExposureMatrixMissing, resolve_exposures
from signal_lab.loaders.holdout import HoldoutViolation, holdout_start
from signal_lab.measurement.factors import FACTOR_NAMES

REPO_ROOT = Path(__file__).resolve().parents[1]
K = len(FACTOR_NAMES)
TRUE = np.array([0.8, -3.0, -1.5, -2.0, 0.2, 0.1])


def _weeks(n=300, start="2005-01-07"):
    return pd.date_range(start, periods=n, freq="W-FRI")


def _factors(n, seed=1):
    return np.random.default_rng(seed).normal(0.0, 0.01, size=(n, K))


def _returns(F, noise=1e-4, seed=2):
    """Three instruments: constant true loadings, the same with noise, and unrelated to F."""
    rng = np.random.default_rng(seed)
    n = len(F)
    a = F @ TRUE + rng.normal(0, 1e-6, n)
    b = F @ TRUE + rng.normal(0, noise, n)
    c = rng.normal(0, 0.01, n)
    return np.column_stack([a, b, c])


def _build(R, F, weeks, ids=("A", "B", "C")):
    return build.build_estimated(R, F, list(ids), ["x"] * len(ids), weeks)


def _fit(built, sid):
    f = built["fit"]
    return f[f["instrument"] == sid].set_index("date")


def test_constant_true_loadings_are_recovered_and_explained_share_is_near_one():
    F, weeks = _factors(300), _weeks()
    built = _build(_returns(F), F, weeks)
    last = built["loadings"]
    last = last[(last["instrument"] == "B") & (last["date"] == weeks[-1])].set_index("factor")
    assert np.allclose(last.loc[list(FACTOR_NAMES), "loading"].to_numpy(), TRUE, atol=0.05)
    assert (last["kind"] == "estimated").all() and (last["estimator"] == "huber_m").all()
    assert (last["se"] > 0).all()
    assert _fit(built, "A")["explained_share"].iloc[-1] > 0.999
    assert _fit(built, "B")["explained_share"].iloc[-1] > 0.95


def test_an_instrument_unrelated_to_the_factors_explains_about_nothing():
    F, weeks = _factors(300), _weeks()
    share = _fit(_build(_returns(F), F, weeks), "C")["explained_share"].dropna()
    assert abs(share.iloc[-1]) < 0.2 and share.max() < 0.3


def test_explained_share_needs_52_weeks_and_is_not_clipped():
    F = _factors(300)
    r = F @ TRUE
    beta = np.tile(TRUE, (300, 1))
    beta[:104] = np.nan  # no loading before week 104
    share = build.explained_share(r, F, beta)
    assert np.isnan(share[:155]).all()  # 52 predicted weeks first exist at 104 + 52 = 156 - 1
    assert np.isfinite(share[156:]).all() and share[200] > 0.999
    wrong = np.tile(-TRUE * 3, (300, 1))  # a wrong loading is worse than no loading
    assert build.explained_share(r, F, wrong)[250] < 0


def test_changing_every_observation_after_t_leaves_every_row_at_or_before_t_unchanged():
    F, weeks = _factors(300), _weeks()
    R = _returns(F)
    t0 = 220
    base = _build(R, F, weeks)
    R2, F2 = R.copy(), F.copy()
    rng = np.random.default_rng(99)
    R2[t0 + 1 :] = rng.normal(0, 0.05, R2[t0 + 1 :].shape)
    F2[t0 + 1 :] = rng.normal(0, 0.05, F2[t0 + 1 :].shape)
    other = _build(R2, F2, weeks)
    for name in ("loadings", "fit"):
        a = base[name][base[name]["date"] <= weeks[t0]].reset_index(drop=True)
        b = other[name][other[name]["date"] <= weeks[t0]].reset_index(drop=True)
        assert len(a) > 0
        pd.testing.assert_frame_equal(a, b, check_exact=True)  # bit for bit, share included
    fit = base["fit"]
    assert (fit["last_data_date"] <= fit["date"]).all()


def test_the_measured_value_is_the_last_one_on_or_before_the_date_never_a_later_one():
    fridays = pd.date_range("2010-01-08", periods=6, freq="W-FRI")
    daily = pd.bdate_range("2010-01-04", fridays[-1] + pd.Timedelta(3, "D"))
    oad = pd.Series(np.arange(len(daily), dtype=float), index=daily)
    oad.loc[fridays[2] - pd.Timedelta(4, "D") : fridays[2]] = np.nan  # an empty week
    fields = {
        "INDEX_OAD_TSY": pd.DataFrame({"X": oad}),
        "INDEX_OAS_TSY": pd.DataFrame({"X": oad * 0 + 1.0}),
    }
    out = build.measured_cells(fields, ["X", "NO_SUCH"], fridays, fridays[1:])
    assert (out["kind"] == "measured").all() and set(out["instrument"]) == {"X"}
    got = out.set_index("date")["oad"]
    for d, v in got.items():
        assert v == oad.loc[:d].iloc[-1], "a later observation was used"
    assert fridays[2] not in got.index or np.isnan(got.get(fridays[2], np.nan))  # not carried


def _store_inputs(tmp_path):
    F, weeks = _factors(300), _weeks()
    built = _build(_returns(F), F, weeks)
    frames = {
        "loadings": built["loadings"],
        "fit": built["fit"],
        "measured": pd.DataFrame(
            {
                "instrument": ["A"],
                "date": [weeks[-1]],
                "oad": [5.0],
                "oas": [np.nan],
                "kind": ["measured"],
            }
        ),
        "instruments": built["instruments"],
    }
    return frames, {"first_date": str(weeks[0].date()), "last_date": str(weeks[-1].date())}


def test_a_store_round_trips_and_is_immutable(tmp_path):
    frames, manifest = _store_inputs(tmp_path)
    path = store.write_store("t1", frames, manifest, tmp_path)
    loaded = store.load_store("t1", tmp_path)
    assert loaded.manifest["row_counts"]["loadings"] == len(frames["loadings"])
    assert (path / "manifest.yaml").exists()
    with pytest.raises(FileExistsError):
        store.write_store("t1", frames, manifest, tmp_path)


def test_a_store_that_is_edited_after_it_is_written_is_refused(tmp_path):
    frames, manifest = _store_inputs(tmp_path)
    path = store.write_store("t2", frames, manifest, tmp_path)
    edited = pd.read_parquet(path / "loadings.parquet")
    edited.loc[0, "loading"] += 1e-9
    edited.to_parquet(path / "loadings.parquet", index=False)
    with pytest.raises(store.StoreChanged):
        store.load_store("t2", tmp_path)


def test_the_report_opens_with_its_disclaimer_and_tabulates_measured_against_estimated(tmp_path):
    F, weeks = _factors(300), _weeks()
    built = _build(_returns(F), F, weeks)
    meas = pd.DataFrame(
        {
            "instrument": "A",
            "date": weeks,
            "oad": 3.0,
            "oas": np.nan,
            "kind": "measured",
        }
    )
    frames = {
        "loadings": built["loadings"],
        "fit": built["fit"],
        "measured": meas,
        "instruments": built["instruments"],
    }
    manifest = {
        "estimator": {
            "name": "huber_m",
            "hypothesis": "H-2026-0013",
            "huber_c": 1.345,
            "window_weeks": 156,
            "min_obs": 104,
        },
        "factors": list(FACTOR_NAMES),
        "first_date": str(weeks[0].date()),
        "last_date": str(weeks[-1].date()),
        "n_estimated": 3,
        "n_not_estimated": 0,
        "not_estimated_reason": "none",
        "params_hash": "p" * 64,
        "weekly_returns_hash": "w" * 64,
        "factors_hash": "f" * 64,
        "thread_setting": {"OMP_NUM_THREADS": "1"},
    }
    store.write_store("t3", frames, manifest, tmp_path)
    loaded = store.load_store("t3", tmp_path)
    table = report.estimated_against_measured(loaded)
    row = table.iloc[0]
    assert row["instrument"] == "A" and row["minus_oad"] == -3.0
    assert row["real_yield"] == pytest.approx(TRUE[1], abs=0.05)
    assert row["real_yield_ratio"] == pytest.approx(TRUE[1] / -3.0, abs=0.02)
    text = report.build_report(loaded)
    assert text.startswith("Built from `decisions/0049`. It chooses nothing about the matrix's")


def test_the_exposure_matrix_still_does_not_exist():
    with pytest.raises(ExposureMatrixMissing):
        resolve_exposures(None)


@pytest.mark.holdout
def test_the_builder_raises_on_a_week_in_the_holdout():
    F = _factors(300)
    weeks = pd.date_range("2017-01-06", periods=300, freq="W-FRI")  # runs past 2020-01-01
    assert weeks[-1] >= holdout_start()
    with pytest.raises(HoldoutViolation):
        _build(_returns(F), F, weeks)
    with pytest.raises(HoldoutViolation):
        build.measured_cells({}, [], weeks, weeks)


@pytest.mark.holdout
def test_a_built_stores_last_date_is_before_the_holdout():
    manifests = sorted((REPO_ROOT / "data" / "characteristics").glob("*/manifest.yaml"))
    for path in manifests:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert pd.Timestamp(doc["last_date"]) < holdout_start(), path.parent.name
