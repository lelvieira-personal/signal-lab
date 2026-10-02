"""
The JPMaQS loader (HANDOFF task 44): raw pull -> VintagePanel -> macro snapshot.

Every frame here is synthetic and shaped like the vendor's long frame. Nothing
reads data/raw/ and nothing makes a network call.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "scripts")]

import jpmaqs_coverage  # noqa: E402
import jpmaqs_pull  # noqa: E402

from signal_lab.harness.snapshot import (  # noqa: E402
    build_macro_snapshot,
    load_snapshot,
    verify_snapshot,
)
from signal_lab.loaders.holdout import HoldoutViolation  # noqa: E402
from signal_lab.loaders.jpmaqs import (  # noqa: E402
    JPMaQSLoader,
    LoaderNotImplemented,
    RawPullMissing,
    build_macro_panel,
    compress_to_change_points,
    file_sha256,
    filter_panel,
    qdf_to_vintage_frame,
)

T1 = "USD_FAKEGDP_NSA"
T2 = "DEM_FAKECPI_SA"  # a legacy euro prefix
EXTRA = "ZZZ_FAKEEXTRA_NSA"  # cross-product leftover, never requested


def _qdf(ticker: str, days, values, gradings=None, lags=None, period_ends=None) -> pd.DataFrame:
    """
    The vendor's information-state frame. `eop_lag` grows day by day while a
    vintage stands, so a vintage is best described by its period_end; pass
    `period_ends` and the lag is `real_date - period_end` in days.
    """
    cid, xcat = ticker.split("_", 1)
    n = len(days)
    if period_ends is not None:
        lags = list(
            (pd.to_datetime(list(days)) - pd.to_datetime(list(period_ends))).days.astype(float)
        )
    return pd.DataFrame(
        {
            "real_date": pd.to_datetime(list(days)),
            "cid": cid,
            "xcat": xcat,
            "value": values,
            "grading": gradings if gradings is not None else [1.0] * n,
            "eop_lag": lags if lags is not None else [10.0] * n,
        }
    )


def _daily(start="2010-01-04", n=12):
    return pd.bdate_range(start, periods=n)


def _two_series() -> pd.DataFrame:
    """T1 repeats one vintage, then a new period, then a revision of it."""
    d = _daily()
    v1 = [1.0] * 4 + [2.0] * 4 + [2.5] * 4  # change points at day 0, 4, 8
    pe1 = [d[0] - pd.Timedelta(days=30)] * 4 + [d[4] - pd.Timedelta(days=3)] * 8
    pe2 = [d[0] - pd.Timedelta(days=30)] * 12
    return pd.concat(
        [
            _qdf(T1, d, v1, period_ends=pe1),
            _qdf(T2, d, [5.0] * 12, period_ends=pe2),
            _qdf(EXTRA, d, [9.0] * 12),
        ],
        ignore_index=True,
    )


# --- the conversion -----------------------------------------------------------


def test_the_conversion_inverts_the_naming():
    d = _daily(n=3)
    out = qdf_to_vintage_frame(_qdf(T1, d, [1.0, 1.0, 2.0], lags=[10.0, 10.0, 4.0]))
    assert list(out["series_id"].unique()) == [T1]
    assert (out["knowledge_date"] == pd.DatetimeIndex(d)).all()
    assert (out["period_end"] == pd.DatetimeIndex(d) - pd.to_timedelta([10, 10, 4], unit="D")).all()
    assert (out["period_end"] <= out["knowledge_date"]).all()


def test_a_revision_is_a_new_row_with_the_same_period_end():
    # Day 0 publishes period P; day 5 republishes the same period with a new value:
    # real_date - eop_lag is the same date on both.
    days = pd.to_datetime(["2010-02-01", "2010-02-08"])
    lags = [20.0, 27.0]
    out = qdf_to_vintage_frame(_qdf(T1, days, [1.0, 1.4], lags=lags))
    assert out["period_end"].nunique() == 1
    assert list(out["knowledge_date"]) == list(days)
    panel, _ = build_macro_panel(_qdf(T1, days, [1.0, 1.4], lags=lags), [T1])
    assert panel.as_of("2010-02-03").iloc[0, 0] == 1.0
    assert panel.as_of("2010-02-08").iloc[0, 0] == 1.4


def test_every_row_has_period_end_on_or_before_knowledge_date():
    panel, _ = build_macro_panel(_two_series(), [T1, T2])
    assert (panel.frame["period_end"] <= panel.frame["knowledge_date"]).all()


@pytest.mark.parametrize("drop", ["value", "grading", "eop_lag"])
def test_a_missing_metric_column_is_refused(drop):
    with pytest.raises(ValueError, match=drop):
        qdf_to_vintage_frame(_qdf(T1, _daily(n=3), [1.0] * 3).drop(columns=drop))


@pytest.mark.parametrize("bad", [-1.0, np.nan, np.inf])
def test_a_bad_eop_lag_on_a_valued_row_is_refused(bad):
    with pytest.raises(ValueError, match="eop_lag"):
        qdf_to_vintage_frame(_qdf(T1, _daily(n=3), [1.0] * 3, lags=[10.0, bad, 10.0]))


def test_a_missing_grading_on_a_valued_row_is_refused():
    with pytest.raises(ValueError, match="grading"):
        qdf_to_vintage_frame(_qdf(T1, _daily(n=3), [1.0] * 3, gradings=[1.0, np.nan, 1.0]))


def test_rows_with_no_value_are_dropped_and_counted_and_may_have_bad_metrics():
    q = _qdf(T1, _daily(n=4), [1.0, np.nan, np.nan, 2.0], lags=[10.0, np.nan, -5.0, 10.0])
    q.loc[1, "grading"] = np.nan
    assert len(qdf_to_vintage_frame(q)) == 2  # the no-value rows are not observations
    _, counts = build_macro_panel(q, [T1])
    assert counts["per_ticker"][T1]["rows_no_value"] == 2
    assert counts["rows_raw"] == 4


# --- filter_panel -------------------------------------------------------------


def test_filter_panel_drops_extras_and_counts_them():
    kept, dropped = filter_panel(_two_series(), [T1, T2])
    assert set(kept["cid"] + "_" + kept["xcat"]) == {T1, T2}
    assert dropped == 1


def test_filter_panel_raises_on_a_missing_ticker():
    with pytest.raises(ValueError, match="FAKEMISSING"):
        filter_panel(_two_series(), [T1, "USD_FAKEMISSING_NSA"])


# --- compression --------------------------------------------------------------


def test_compression_keeps_only_change_points():
    full = qdf_to_vintage_frame(_two_series().query("cid == 'USD'"))
    small = compress_to_change_points(full)
    assert len(full) == 12 and len(small) == 3


def test_compression_changes_no_as_of_answer():
    rng = np.random.default_rng(7)
    d = pd.bdate_range("2010-01-04", periods=120)
    # Piecewise-constant vintages with occasional revisions and a grade change.
    values = np.repeat(rng.normal(size=20), 6)
    first_days = d[::6]
    pe = np.repeat(first_days - pd.to_timedelta(rng.integers(1, 40, size=20), unit="D"), 6)
    grades = np.repeat(rng.choice([1.0, 2.0], size=20), 6)
    full = qdf_to_vintage_frame(_qdf(T1, d, values, gradings=grades, period_ends=pe))
    from signal_lab.loaders.base import VintagePanel

    meta = {}
    a = VintagePanel(full, meta)
    b = VintagePanel(compress_to_change_points(full), meta)
    assert len(b.frame) < len(a.frame)
    for kd in pd.date_range("2009-12-01", "2010-08-01", freq="9D"):
        pd.testing.assert_frame_equal(a.as_of(kd), b.as_of(kd))


# --- the grade filter ---------------------------------------------------------


def test_grade_three_is_excluded_and_counted_per_ticker(params):
    d = _daily(n=6)
    q = _qdf(T1, d, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], gradings=[1.0, 2.0, 3.0, 3.0, 2.5, 1.0])
    panel, counts = build_macro_panel(q, [T1], params)
    c = counts["per_ticker"][T1]
    assert c["rows_grade_excluded"] == 2
    assert c["grading_counts"] == {"1.0": 2, "2.0": 1, "2.5": 1, "3.0": 2}  # fractional shown
    assert 3.0 not in set(panel.frame["grading"])
    assert 2.5 in set(panel.frame["grading"])  # no invented threshold


def test_any_other_grade_rule_is_not_implemented(params, monkeypatch):
    monkeypatch.setitem(params.as_dict()["data"]["jpmaqs"], "grade_3", "downweight")
    with pytest.raises(LoaderNotImplemented):
        build_macro_panel(_two_series(), [T1, T2], params)


# --- legacy prefixes ----------------------------------------------------------


def test_a_legacy_prefix_maps_in_the_meta_and_not_in_the_id(params):
    panel, _ = build_macro_panel(_two_series(), [T1, T2], params)
    assert T2 in panel.frame["series_id"].unique()
    assert panel.meta[T2].region == "DEU"
    assert panel.meta[T1].region == "USD"
    assert panel.source == "jpmaqs"


# --- the holdout --------------------------------------------------------------


@pytest.mark.holdout
def test_a_pull_that_reaches_the_holdout_raises_and_is_not_clipped(params):
    d = pd.to_datetime(["2019-12-30", "2020-01-02"])
    with pytest.raises(HoldoutViolation):
        build_macro_panel(_qdf(T1, d, [1.0, 2.0]), [T1], params)


@pytest.mark.holdout
def test_the_pull_never_requests_the_holdout(params, tmp_path):
    calls = []
    jpmaqs_pull.pull(params, [T1], tmp_path, _FakeFactory(_qdf(T1, _daily(), [1.0] * 12), calls))
    assert calls[0]["end_date"] == "2019-12-31"
    assert calls[0]["metrics"] == ["value", "grading", "eop_lag"]
    assert calls[0]["tickers"] == [T1]


# --- the pull script, with a fake vendor client -------------------------------


class _FakeFactory:
    def __init__(self, qdf, calls):
        self.qdf, self.calls = qdf, calls

    def __call__(self, params):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def download(self, **kwargs):
        self.calls.append(kwargs)
        return self.qdf


NOW = datetime(2026, 10, 2, 9, 0, 0, tzinfo=UTC)


def _pull(params, tmp_path, qdf, tickers):
    return jpmaqs_pull.pull(params, tickers, tmp_path, _FakeFactory(qdf, []), now=NOW)


def test_a_good_pull_writes_the_parquet_and_the_manifest(params, tmp_path, capsys):
    q = _two_series()
    q = q[q["cid"] != "ZZZ"]
    assert _pull(params, tmp_path, q, [T1, T2]) == 0
    out = tmp_path / "P-20261002T090000Z"
    manifest = json.loads((out / "pull_manifest.json").read_text())
    assert manifest["tickers"] == [T2, T1] or sorted(manifest["tickers"]) == sorted([T1, T2])
    assert manifest["sha256"] == file_sha256(out / "qdf.parquet")
    assert manifest["call_shape"] == "tickers="
    assert manifest["rows_per_ticker"][T1] == 12
    printed = capsys.readouterr().out
    assert "wrote" in printed and "rows" in printed


def test_a_pull_is_never_overwritten(params, tmp_path):
    q = _two_series()
    q = q[q["cid"] != "ZZZ"]
    assert _pull(params, tmp_path, q, [T1, T2]) == 0
    assert _pull(params, tmp_path, q, [T1, T2]) == 1


def test_a_pull_missing_a_ticker_writes_nothing(params, tmp_path):
    q = _qdf(T1, _daily(), [1.0] * 12)
    assert _pull(params, tmp_path, q, [T1, T2]) == 1
    assert list(tmp_path.iterdir()) == []


def test_a_pull_missing_a_metric_writes_nothing(params, tmp_path):
    q = _qdf(T1, _daily(), [1.0] * 12).drop(columns="eop_lag")
    assert _pull(params, tmp_path, q, [T1]) == 1
    assert list(tmp_path.iterdir()) == []


def test_a_pull_with_an_empty_metric_writes_nothing(params, tmp_path):
    q = _qdf(T1, _daily(), [1.0] * 12, gradings=[np.nan] * 12)
    assert _pull(params, tmp_path, q, [T1]) == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.holdout
def test_a_pull_that_reaches_the_holdout_writes_nothing(params, tmp_path):
    q = _qdf(T1, pd.to_datetime(["2019-12-30", "2020-01-02"]), [1.0, 2.0])
    assert _pull(params, tmp_path, q, [T1]) == 1
    assert list(tmp_path.iterdir()) == []


def test_a_failed_download_writes_nothing(params, tmp_path):
    class Boom(_FakeFactory):
        def download(self, **kw):
            raise ConnectionError("no route")

    assert jpmaqs_pull.pull(params, [T1], tmp_path, Boom(None, []), now=NOW) == 1
    assert list(tmp_path.iterdir()) == []


# --- load_macro and the macro snapshot, on a tmp_path raw directory -----------


@pytest.fixture
def raw_root(params, tmp_path):
    root = tmp_path / "raw"
    q = _two_series()
    assert jpmaqs_pull.pull(params, [T1, T2], root, _FakeFactory(q, []), now=NOW) == 0
    return root


def test_load_macro_reads_the_newest_pull_and_filters_to_the_manifest(params, raw_root):
    panel = JPMaQSLoader(params, raw_root=raw_root).load_macro("m1")
    assert set(panel.frame["series_id"]) == {T1, T2}
    assert panel.snapshot_id == "m1" and panel.source == "jpmaqs"


def test_load_macro_without_a_raw_pull_says_how_to_make_one(params, tmp_path):
    with pytest.raises(RawPullMissing, match="make jpmaqs-pull"):
        JPMaQSLoader(params, raw_root=tmp_path / "nothing").load_macro()
    (tmp_path / "empty").mkdir()
    with pytest.raises(RawPullMissing, match="make jpmaqs-pull"):
        JPMaQSLoader(params, raw_root=tmp_path / "empty").load_macro()
    with pytest.raises(RawPullMissing, match="P-nope"):
        JPMaQSLoader(params, raw_root=tmp_path / "empty").load_macro(pull_id="P-nope")


def test_a_raw_file_changed_after_the_pull_is_refused(params, raw_root):
    pull_dir = next(raw_root.iterdir())
    q = pd.read_parquet(pull_dir / "qdf.parquet")
    q["value"] = q["value"] + 1.0
    q.to_parquet(pull_dir / "qdf.parquet", index=False)
    with pytest.raises(RuntimeError, match="sha256"):
        JPMaQSLoader(params, raw_root=raw_root).load_macro()


def test_a_macro_snapshot_is_built_hashed_and_immutable(params, raw_root, tmp_path):
    snaps = tmp_path / "snaps"
    snap = build_macro_snapshot(
        "jpmaqs-macro-test", params=params, snapshots_dir=snaps, raw_root=raw_root
    )
    assert (snap.path / "macro.parquet").exists()
    assert snap.manifest["macro_ids"] == sorted([T1, T2])
    assert snap.manifest["pull_id"] == "P-20261002T090000Z"
    assert snap.manifest["params_hash"] == params.params_hash
    assert snap.manifest["counts"]["n_tickers"] == 2
    assert snap.manifest["counts"]["rows_after_compression"] < snap.manifest["counts"]["rows_raw"]
    ok, _ = verify_snapshot(load_snapshot("jpmaqs-macro-test", snaps))
    assert ok
    with pytest.raises(FileExistsError):
        build_macro_snapshot(
            "jpmaqs-macro-test", params=params, snapshots_dir=snaps, raw_root=raw_root
        )


def test_a_missing_raw_pull_leaves_no_snapshot_directory(params, tmp_path):
    snaps = tmp_path / "snaps"
    with pytest.raises(RawPullMissing):
        build_macro_snapshot("m", params=params, snapshots_dir=snaps, raw_root=tmp_path / "none")
    assert not (snaps / "m").exists()


# --- the coverage report ------------------------------------------------------


def test_the_coverage_report_has_dates_and_counts_and_no_values(params, raw_root, tmp_path):
    snaps = tmp_path / "snaps"
    snap = build_macro_snapshot("m", params=params, snapshots_dir=snaps, raw_root=raw_root)
    rows = jpmaqs_coverage.coverage_rows(snap, {T1: ["H-TEST-0001"]})
    by = {r["ticker"]: r for r in rows}
    assert by[T1]["hypotheses"] == "H-TEST-0001"
    assert by[T1]["n_vintages"] == 3 and by[T1]["n_periods"] == 2  # a revision shares its period
    assert by[T1]["starts_by_dev_start"] is False  # 2010 start, after 2001-01-05
    assert by[T1]["gradings"] == "1.0:12"
    assert by[T1]["eop_lag_1_31"] + by[T1]["eop_lag_32_92"] == 12
    csv_path, md_path = jpmaqs_coverage.write_reports(rows, snap, tmp_path / "out")
    header = csv_path.read_text().splitlines()[0].split(",")
    assert "value" not in header
    assert md_path.exists()
