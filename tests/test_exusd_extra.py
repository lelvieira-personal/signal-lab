"""
The Euro Treasury and UK Gilt bands and the euro linkers (HANDOFF task 89, decisions/0068), on a
synthetic workbook written here with hand-made numbers. Nothing reads data/raw/.
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

from signal_lab.loaders import exusd_extra as extra  # noqa: E402
from signal_lab.loaders import fx  # noqa: E402
from signal_lab.loaders.bloomberg import BloombergLoader  # noqa: E402
from signal_lab.loaders.holdout import holdout_start  # noqa: E402
from signal_lab.loaders.invariants import InvariantViolation  # noqa: E402

# ticker, currency, investable
ROWS = (
    ("LEATTREU", "EUR", False),
    ("LET3TREU", "EUR", True),
    ("I08043GB", "GBP", True),
    ("BEIG1T", "EUR", True),
)
TICKERS = [t for t, _, _ in ROWS]
NOMINAL = ["LEATTREU", "LET3TREU", "I08043GB"]
MARKERS = ["#N/A"]
MANIFEST_ROWS = (
    "bbg_exusd_bonds_extra.xlsx,levels,wide_single_date,PX_LAST,EUR_or_GBP,returns_exusd_extra,1,2\n"
    "bbg_exusd_bonds_extra.xlsx,analytics,long_date_ticker,various,n/a,analytics_exusd_extra,1,2\n"
    "bbg_exusd_bonds_extra.xlsx,linker_fields,table,n/a,n/a,linker_fields_exusd_extra,1,2\n"
)
ANALYTICS_HEAD = ("date", "ticker", "index_name", "oad_tsy", "yield_to_worst", "oas", "oas_field")


def _header(rows=ROWS, ccy=None):
    return ["date", *[f"{t}_local_{ccy or c}" for t, c, _ in rows]]


def _levels(dates, n=None):
    n = len(ROWS) if n is None else n
    return [
        tuple([d.to_pydatetime(), *[100.0 + i + 0.5 * j for j in range(n)]])
        for i, d in enumerate(dates)
    ]


# --- the reader ------------------------------------------------------------------------------


def test_a_currency_other_than_eur_or_gbp_is_refused():
    rows = [tuple(_header(ccy="JPY")), *_levels(pd.bdate_range("2003-01-02", periods=3))]
    with pytest.raises(InvariantViolation, match="quoted in JPY"):
        extra.levels_from_rows(rows, MARKERS, TICKERS)


def test_a_ticker_outside_the_universe_is_refused():
    other = (*ROWS[:3], ("ZZZ", "EUR", True))
    rows = [tuple(_header(other)), *_levels(pd.bdate_range("2003-01-02", periods=3))]
    with pytest.raises(InvariantViolation, match="not the universe's"):
        extra.levels_from_rows(rows, MARKERS, TICKERS)


def test_the_daily_start_is_found_after_a_sparse_run_in_and_a_marker_is_nan():
    monthly = list(pd.date_range("2002-06-30", periods=6, freq="ME"))
    daily = list(pd.bdate_range("2003-01-02", periods=60))
    rows = [tuple(_header()), *_levels(monthly + daily)]
    rows[-1] = (rows[-1][0], "#N/A", *rows[-1][2:])
    levels, quote = extra.levels_from_rows(rows, MARKERS, TICKERS)
    assert quote == {t: c for t, c, _ in ROWS}
    assert pd.isna(levels.iloc[-1, 0]) and not (levels.fillna(1.0) == 0).any().any()
    starts = extra.true_daily_starts(levels, pd.Timestamp("2020-01-01"))
    assert set(starts.values()) == {daily[0]}


def test_an_unknown_analytics_ticker_is_refused():
    d = pd.Timestamp("2003-01-02").to_pydatetime()
    with pytest.raises(InvariantViolation, match="outside"):
        extra.analytics_from_rows(
            [ANALYTICS_HEAD, (d, "ZZZ", "n", 1.0, 2.0, None, None)], MARKERS, TICKERS
        )


def test_the_linker_flags_read_only_the_is_number_columns():
    head = ("mnemonic", "BEIG1T_result", "BEIG3T_result", "BEIG1T_is_number", "BEIG3T_is_number")
    rows = [
        head,
        ("INDEX_REAL_DURATION", "x", 7.5, False, "TRUE"),
        ("NOTE", None, None, None, None),
    ]
    flags = extra.linker_flags(rows)
    assert flags["BEIG1T"]["INDEX_REAL_DURATION"] is False
    assert flags["BEIG3T"]["INDEX_REAL_DURATION"] is True
    assert flags["BEIG1T"]["NOTE"] is None
    with pytest.raises(InvariantViolation, match="linker_fields header"):
        extra.linker_flags([("mnemonic", "BEIG1T_result"), ("X", 1)])


# --- the loader ------------------------------------------------------------------------------


def _write(path, level_dates, analytics_dates):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "levels"
    ws.append(_header())
    for r in _levels(level_dates):
        ws.append(list(r))
    an = wb.create_sheet("analytics")
    an.append(list(ANALYTICS_HEAD))
    for d in analytics_dates:
        for j, t in enumerate(NOMINAL):
            an.append([d.to_pydatetime(), t, f"{t} band", 5.0 + j, 2.0, 0.1, "INDEX_OAS_TSY"])
    lf = wb.create_sheet("linker_fields")
    lf.append(
        ["mnemonic", "BEIG1T_result", "BEIG3T_result", "BEIG1T_is_number", "BEIG3T_is_number"]
    )
    lf.append(["INDEX_REAL_DURATION", "#N/A", "#N/A", False, False])
    wb.save(path)


def _fixture(tmp_path, with_extra):
    built = bloomberg_fixture.build(tmp_path)
    if with_extra:
        dates = list(pd.bdate_range("2002-11-29", "2020-02-28"))
        _write(built["root"] / "data" / "raw" / extra.SOURCE_FILE, dates, dates)
        path = built["universe"] / "investable_universe.csv"
        with path.open(newline="", encoding="utf-8") as fh:
            fields = csv.DictReader(fh).fieldnames
        with path.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            for t, _, investable in ROWS:
                w.writerow(
                    {
                        "ticker": t,
                        "name": f"{t} name",
                        "section": "3. International Government Bonds",
                        "first_daily": "2002-11-29",
                        "tier": "",
                        "hedged": False,
                        "investable": investable,
                        "cost_bucket": "mid",
                        "reporting_class": "Ex-USD Bonds",
                        "source_file": extra.SOURCE_FILE,
                    }
                )
        with (built["universe"] / "raw_manifest.csv").open("a", newline="", encoding="utf-8") as fh:
            fh.write(MANIFEST_ROWS)
    return built


@pytest.fixture
def pin(monkeypatch):
    def _pin(built):
        monkeypatch.setattr(fx, "SHA256_PREFIX", fx.file_sha256(built["fx"])[:16])
        path = built["root"] / "data" / "raw" / extra.SOURCE_FILE
        if path.exists():
            monkeypatch.setattr(extra, "SHA256_PREFIX", extra.file_sha256(path)[:16])

    return _pin


def _loader(built, params):
    return BloombergLoader(
        params, raw_dir=built["root"] / "data" / "raw", universe_dir=built["universe"]
    )


def test_a_manifest_without_the_roles_gives_the_panel_it_gave_before(tmp_path, params, pin):
    built = _fixture(tmp_path, with_extra=False)
    pin(built)
    loader = _loader(built, params)
    panel = loader.load_returns()
    assert not set(TICKERS) & set(panel.levels.columns)
    assert "exusd_extra" not in loader.report


def test_the_rows_appear_in_dollars_with_their_tier_and_before_the_holdout(tmp_path, params, pin):
    built = _fixture(tmp_path, with_extra=True)
    pin(built)
    loader = _loader(built, params)
    panel = loader.load_returns()
    assert set(TICKERS) <= set(panel.levels.columns)  # the reference series is in the panel too

    # one level times one rate, by hand: row i is 100 + i + 0.5 j; the fixture's EURUSD on day n
    # since 2000-01-01 is 1.10 + 0.0001 n and GBPUSD 1.30 + 0.0001 n, both dollars per unit
    day = pd.Timestamp("2003-02-04")
    i = list(pd.bdate_range("2002-11-29", "2020-02-28")).index(day)
    n = (day.date() - dt.date(2000, 1, 1)).days
    for j, (t, ccy, _) in enumerate(ROWS):
        rate = (1.10 if ccy == "EUR" else 1.30) + 0.0001 * n
        assert panel.levels.loc[day, t] == pytest.approx((100.0 + i + 0.5 * j) * rate, rel=1e-9)

    for t, ccy, _ in ROWS:
        m = panel.meta[t]
        assert m.tier == "second" and m.true_daily_start == pd.Timestamp("2002-11-29")
        assert m.currency == "USD" and m.quote_currency == ccy
    assert panel.levels.index.max() < holdout_start(params)
    assert panel.returns.index.max() < holdout_start(params)

    report = loader.report["exusd_extra"]
    assert report["level_rows_on_or_after_holdout"] > 0  # the file's rows, counted and cut
    assert set(report["tickers"]) == set(TICKERS)
    assert report["tickers"]["LEATTREU"]["investable"] is False
    assert report["tickers"]["LET3TREU"]["investable"] is True


def test_the_analytics_merge_and_the_linkers_are_counted(tmp_path, params, pin):
    built = _fixture(tmp_path, with_extra=True)
    pin(built)
    loader = _loader(built, params)
    analytics = loader.load_analytics()
    for field in ("INDEX_OAD_TSY", "INDEX_YIELD_TO_WORST", "INDEX_OAS_TSY"):
        assert set(NOMINAL) <= set(analytics.fields[field].columns)
        assert analytics.fields[field].index.max() < holdout_start(params)
    rep = loader.report["analytics"]["exusd_extra"]
    assert rep["linker_dates_numeric"]["BEIG1T"] == {"oad_tsy": 0, "yield_to_worst": 0, "oas": 0}
    assert rep["linker_fields_is_number"]["BEIG1T"] == {"INDEX_REAL_DURATION": False}
    assert rep["index_names"]["LET3TREU"] == "LET3TREU band"


def test_a_file_that_is_not_the_one_expected_is_refused(tmp_path, params, pin):
    built = _fixture(tmp_path, with_extra=True)
    pin(built)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(extra, "SHA256_PREFIX", "0000000000000000")
        with pytest.raises(extra.RawFileChanged):
            _loader(built, params).load_returns()


# --- the store comparison, task 89's form ------------------------------------------------------


def _frames(instruments, loaded):
    d = pd.Timestamp("2014-01-03")
    loadings = pd.DataFrame(
        [{"instrument": i, "date": d, "factor": "f1", "loading": 0.5, "se": 0.1} for i in loaded]
    )
    measured = pd.DataFrame(
        {"instrument": instruments, "date": [d] * len(instruments), "duration": 4.0, "kind": "m"}
    )
    return {
        "loadings": loadings,
        "measured": measured,
        "instruments": pd.DataFrame({"instrument": instruments}),
    }


def test_a_store_that_adds_estimated_rows_and_retires_a_reference_series_passes():
    old = _frames(["A", "G"], ["A", "G"])
    new = _frames(["A", "N"], ["A", "N"])
    old_m = {"factors_hash": "f", "weekly_returns_hash": "w"}
    new_m = {"factors_hash": "f", "weekly_returns_hash": "x"}
    cmp = build_characteristics.compare_with_superseded
    out = cmp(old, new, old_m, new_m, ["N"], expected_removed=["G"], new_may_be_estimated=True)
    assert out["failures"] == [] and out["new_instruments_estimated"] == ["N"]
    assert out["removed_instruments"] == ["G"]
    # task 76's defaults still refuse each of the three
    failures = cmp(old, new, old_m, new_m, ["N"])["failures"]
    assert any("only in the old store" in f for f in failures)
    assert any("new instrument has a loading row" in f for f in failures)
    assert any("weekly_returns_hash" in f for f in failures)
    # a new instrument with no analytics may lack a measured row only where excused
    bare = _frames(["A", "N"], ["A", "N"])
    bare["measured"] = bare["measured"][bare["measured"]["instrument"] != "N"]
    no_row = cmp(old, bare, old_m, new_m, ["N"], ["G"], True)["failures"]
    assert any("measured: no row for ['N']" in f for f in no_row)
    excused = cmp(old, bare, old_m, new_m, ["N"], ["G"], True, may_lack_measured=["N"])
    assert excused["failures"] == [] and excused["new_instruments_without_measured_rows"] == ["N"]
    # the factors hash is still required equal
    moved = cmp(old, new, old_m, {**new_m, "factors_hash": "g"}, ["N"], ["G"], True)["failures"]
    assert any("factors_hash" in f for f in moved)
