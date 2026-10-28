"""
The Japan government family (HANDOFF task 76, decisions/0066), on a synthetic workbook written
here with hand-made numbers. Nothing reads data/raw/.
"""

from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_characteristics  # noqa: E402
from fixtures import bloomberg_fixture  # noqa: E402

from signal_lab.loaders import fx  # noqa: E402
from signal_lab.loaders import japan_govt as japan  # noqa: E402
from signal_lab.loaders.bloomberg import BloombergLoader  # noqa: E402
from signal_lab.loaders.holdout import holdout_start  # noqa: E402
from signal_lab.loaders.invariants import InvariantViolation  # noqa: E402

TICKERS = ["I29064JP", "I29065JP", "I29066JP", "I29067JP", "I29068JP"]
MARKERS = ["#N/A"]
LEVEL_ROWS = (
    "bbg_japan_govt.xlsx,levels,wide_single_date,PX_LAST,JPY,returns_japan_govt,1,2\n"
    "bbg_japan_govt.xlsx,analytics,long_date_ticker,various,n/a,analytics_japan_govt,1,2\n"
)


def _header(ccy="JPY", tickers=TICKERS):
    return ["date", *[f"{t}_local_{ccy}" for t in tickers]]


def _rows(dates, tickers=TICKERS, value=lambda i, j: 100.0 + i + 0.5 * j):
    return [
        tuple([d.to_pydatetime(), *[value(i, j) for j in range(len(tickers))]])
        for i, d in enumerate(dates)
    ]


# --- the reader ------------------------------------------------------------------------------


def test_a_suffix_other_than_jpy_is_refused():
    rows = [tuple(_header(ccy="USD")), *_rows(pd.bdate_range("2013-01-31", periods=3))]
    with pytest.raises(InvariantViolation, match="quoted in USD"):
        japan.levels_from_rows(rows, MARKERS, TICKERS)


def test_a_ticker_outside_the_universe_is_refused():
    other = [*TICKERS[:4], "I29099JP"]
    rows = [tuple(_header(tickers=other)), *_rows(pd.bdate_range("2013-01-31", periods=3), other)]
    with pytest.raises(InvariantViolation, match="not the universe's"):
        japan.levels_from_rows(rows, MARKERS, TICKERS)


def test_an_unknown_analytics_ticker_and_a_repeated_row_are_refused():
    d = pd.Timestamp("2013-01-31").to_pydatetime()
    head = tuple(japan.ANALYTICS_COLUMNS)
    with pytest.raises(InvariantViolation, match="outside"):
        japan.analytics_from_rows([head, (d, "ZZZ", "n", 1.0, 2.0)], MARKERS, TICKERS)
    row = (d, TICKERS[0], "n", 1.0, 2.0)
    with pytest.raises(InvariantViolation, match="repeated"):
        japan.analytics_from_rows([head, row, row], MARKERS, TICKERS)


def test_the_daily_start_is_found_after_a_sparse_run_in():
    monthly = list(pd.date_range("2012-06-30", periods=6, freq="ME"))
    daily = list(pd.bdate_range("2013-01-31", periods=60))
    rows = [tuple(_header()), *_rows(monthly + daily)]
    levels, _ = japan.levels_from_rows(rows, MARKERS, TICKERS)
    starts = japan.true_daily_starts(levels, pd.Timestamp("2020-01-01"))
    assert set(starts.values()) == {daily[0]}


def test_a_missing_marker_is_nan_not_zero():
    d = list(pd.bdate_range("2013-01-31", periods=3))
    rows = [tuple(_header()), *_rows(d)]
    rows[2] = (rows[2][0], "#N/A", *rows[2][2:])
    levels, _ = japan.levels_from_rows(rows, MARKERS, TICKERS)
    assert pd.isna(levels.iloc[1, 0]) and not (levels.fillna(1.0) == 0).any().any()


def test_a_ticker_with_no_daily_start_is_refused():
    rows = [tuple(_header()), *_rows(pd.bdate_range("2013-01-31", periods=5))]
    levels, _ = japan.levels_from_rows(rows, MARKERS, TICKERS)
    with pytest.raises(InvariantViolation, match="no true daily start"):
        japan.true_daily_starts(levels, pd.Timestamp("2020-01-01"))


# --- the loader ------------------------------------------------------------------------------


def _write_japan(path, level_dates, analytics_dates):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "levels"
    ws.append(_header())
    for r in _rows(level_dates):
        ws.append(list(r))
    an = wb.create_sheet("analytics")
    an.append(list(japan.ANALYTICS_COLUMNS))
    for i, d in enumerate(analytics_dates):
        for j, t in enumerate(TICKERS):
            an.append([d.to_pydatetime(), t, "name", 5.0 + 0.01 * i + j, 0.5 + 0.001 * i])
    wb.save(path)


def _universe_rows(path):
    """Append the five rows to the fixture's universe table, as task 74 did to the real one."""
    with path.open(newline="", encoding="utf-8") as fh:
        fields = csv.DictReader(fh).fieldnames
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        for t in TICKERS:
            w.writerow(
                {
                    "ticker": t,
                    "name": f"{t} name",
                    "section": "3. International Government Bonds",
                    "first_daily": "2013-01-31",
                    "tier": "",
                    "hedged": False,
                    "investable": True,
                    "cost_bucket": "mid",
                    "reporting_class": "Ex-USD Bonds",
                    "source_file": japan.SOURCE_FILE,
                }
            )


def _fixture(tmp_path, with_japan, level_dates=None):
    built = bloomberg_fixture.build(tmp_path)
    if with_japan:
        level_dates = level_dates or list(pd.bdate_range("2012-11-30", "2020-02-28"))
        analytics_dates = list(pd.bdate_range("2013-01-31", "2020-02-28"))
        _write_japan(
            built["root"] / "data" / "raw" / "bbg_japan_govt.xlsx", level_dates, analytics_dates
        )
        _universe_rows(built["universe"] / "investable_universe.csv")
        with (built["universe"] / "raw_manifest.csv").open("a", newline="", encoding="utf-8") as fh:
            fh.write(LEVEL_ROWS)
    return built


@pytest.fixture
def pin(monkeypatch):
    def _pin(built):
        monkeypatch.setattr(fx, "SHA256_PREFIX", fx.file_sha256(built["fx"])[:16])
        if (built["root"] / "data" / "raw" / "bbg_japan_govt.xlsx").exists():
            sha = japan.file_sha256(built["root"] / "data" / "raw" / "bbg_japan_govt.xlsx")
            monkeypatch.setattr(japan, "SHA256_PREFIX", sha[:16])

    return _pin


def _loader(built, params):
    return BloombergLoader(
        params, raw_dir=built["root"] / "data" / "raw", universe_dir=built["universe"]
    )


def test_a_manifest_without_the_two_roles_gives_the_panel_it_gave_before(tmp_path, params, pin):
    built = _fixture(tmp_path, with_japan=False)
    pin(built)
    loader = _loader(built, params)
    panel = loader.load_returns()
    assert not set(TICKERS) & set(panel.levels.columns)
    assert "japan_govt" not in loader.report


def test_the_five_appear_converted_with_the_tradable_only_tier(tmp_path, params, pin):
    built = _fixture(tmp_path, with_japan=True)
    pin(built)
    loader = _loader(built, params)
    panel = loader.load_returns()
    assert set(TICKERS) <= set(panel.levels.columns)

    # one level times one rate, by hand: the level of row i is 100 + i + 0.5 j, the fixture's
    # USDJPY on day n since 2000-01-01 is 110 - 0.001 n, and USD per yen is its inverse
    day = pd.Timestamp("2013-02-04")
    dates = list(pd.bdate_range("2012-11-30", "2020-02-28"))
    i = dates.index(day)
    n = (day.date() - dt.date(2000, 1, 1)).days
    for j, t in enumerate(TICKERS):
        expected = (100.0 + i + 0.5 * j) / (110.0 - 0.001 * n)
        assert panel.levels.loc[day, t] == pytest.approx(expected, rel=1e-9)

    for t in TICKERS:
        m = panel.meta[t]
        assert m.tier == "tradable-only" and m.true_daily_start == pd.Timestamp("2012-11-30")
        assert m.currency == "USD" and m.quote_currency == "JPY"
        assert panel.levels[t].index.max() < holdout_start(params)
        before = panel.levels.index < m.true_daily_start
        assert panel.levels.loc[before, t].isna().all()

    report = loader.report["japan_govt"]
    assert report["level_rows_on_or_after_holdout"] > 0  # the file's rows, counted and cut
    assert set(report["tickers"]) == set(TICKERS)
    assert all(v["tier"] == "tradable-only" for v in report["tickers"].values())


def test_a_row_on_or_after_the_holdout_never_reaches_the_panel(tmp_path, params, pin):
    built = _fixture(tmp_path, with_japan=True)
    pin(built)
    panel = _loader(built, params).load_returns()
    assert panel.levels.index.max() < holdout_start(params)
    assert panel.returns.index.max() < holdout_start(params)


def test_the_analytics_map_to_the_two_fields_and_to_no_oas(tmp_path, params, pin):
    built = _fixture(tmp_path, with_japan=True)
    pin(built)
    loader = _loader(built, params)
    analytics = loader.load_analytics()
    for field in ("INDEX_OAD_TSY", "INDEX_YIELD_TO_WORST"):
        assert set(TICKERS) <= set(analytics.fields[field].columns)
        assert analytics.fields[field].index.max() < holdout_start(params)
    for field, frame in analytics.fields.items():
        if field.startswith("INDEX_OAS"):
            assert not set(TICKERS) & set(frame.columns)
    assert loader.report["analytics"]["japan_govt"]["tickers"] == sorted(TICKERS)


def test_a_file_that_is_not_the_one_expected_is_refused(tmp_path, params, pin):
    built = _fixture(tmp_path, with_japan=True)
    pin(built)
    japan_pin = japan.SHA256_PREFIX
    assert japan_pin != "dfdf8ed9a39c5da1"  # the pin is the synthetic file's, for this test
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(japan, "SHA256_PREFIX", "0000000000000000")
        with pytest.raises(japan.RawFileChanged):
            _loader(built, params).load_returns()


def test_a_ticker_and_field_in_both_analytics_files_is_refused(tmp_path, params, pin):
    built = _fixture(tmp_path, with_japan=True)
    pin(built)
    loader = _loader(built, params)
    by_field = {"INDEX_OAD_TSY": {TICKERS[0]: pd.Series([1.0], index=[pd.Timestamp("2014-01-02")])}}
    with pytest.raises(InvariantViolation, match="both analytics files"):
        loader._merge_japan_analytics(by_field, {}, MARKERS, loader.params)


# --- the store comparison of scripts/build_characteristics.py ---------------------------------


def _frames(extra=()):
    d = pd.Timestamp("2014-01-03")
    loadings = pd.DataFrame(
        {"instrument": ["A", "A"], "date": [d, d], "factor": ["f1", "f2"], "loading": [0.5, 1.5],
         "se": [0.1, 0.2]}
    )  # fmt: skip
    measured = pd.DataFrame(
        {"instrument": ["B", *extra], "date": [d] * (1 + len(extra)),
         "duration": [4.0] * (1 + len(extra)), "kind": ["measured"] * (1 + len(extra))}
    )  # fmt: skip
    inst = pd.DataFrame({"instrument": ["A", "B", *extra]})
    return {"loadings": loadings, "measured": measured, "instruments": inst}


def _compare(new, **hashes):
    old_m = {"factors_hash": "f", "weekly_returns_hash": "w"}
    new_m = {"factors_hash": "f", "weekly_returns_hash": "w", **hashes}
    return build_characteristics.compare_with_superseded(_frames(), new, old_m, new_m, ["J1"])


def test_a_store_that_only_adds_the_five_passes_the_comparison():
    out = _compare(_frames(extra=["J1"]))
    assert out["failures"] == [] and out["loadings"]["unmatched"] == 0
    assert out["measured"]["cells_compared"] == 1 and out["new_instruments"] == ["J1"]


def test_a_moved_loading_a_loading_row_for_a_new_instrument_or_a_hash_stops_it():
    new = _frames(extra=["J1"])
    new["loadings"].loc[0, "loading"] = 0.5000001
    assert any("loading differs" in f for f in _compare(new)["failures"])
    new = _frames(extra=["J1"])
    row = {
        "instrument": "J1",
        "date": pd.Timestamp("2014-01-03"),
        "factor": "f1",
        "loading": 1.0,
        "se": 1.0,
    }
    new["loadings"] = pd.concat([new["loadings"], pd.DataFrame([row])], ignore_index=True)
    assert any("new instrument has a loading row" in f for f in _compare(new)["failures"])
    assert any(
        "weekly_returns_hash" in f
        for f in _compare(_frames(extra=["J1"]), weekly_returns_hash="x")["failures"]
    )
    assert any("not the expected" in f for f in _compare(_frames(extra=["J1", "J2"]))["failures"])
