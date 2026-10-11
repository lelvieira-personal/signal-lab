"""
Every return in dollars (HANDOFF task 53, decisions/0053), on a synthetic FX workbook built in a
temp folder. Nothing reads data/raw/.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import openpyxl
import pandas as pd
import pytest

from signal_lab.loaders import fx
from signal_lab.loaders.base import SeriesMeta
from signal_lab.loaders.bloomberg import BloombergLoader
from signal_lab.loaders.holdout import holdout_start
from signal_lab.loaders.invariants import InvariantViolation

MARKERS = ["#N/A", "N/A", "#N/A N/A"]
HEADER = ["file", "sheet", "layout", "field", "currency", "role", "header_rows", "first_data_row"]
FX_ROW = "fx.xlsx,FX_Spot_USD,wide_single_date,PX_LAST,per_quote_convention_table,fx_spot,1,2\n"


def _rows(columns, data):
    """Sheet rows: a header, then (date, *values) tuples."""
    return [("Date", *columns), *data]


def _write_fx(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FX_Spot_USD"
    for r in rows:
        ws.append(list(r))
    wb.save(path)


def _meta(ticker, ccy, start="2001-01-02"):
    return SeriesMeta(ticker, pd.Timestamp(start), "backbone", currency=ccy)


# --- the reader and the convention table --------------------------------------------------


def test_a_usd_per_unit_quote_multiplies():
    """A EUR level of 100 at EURUSD 1.25 is 125 USD."""
    cut = pd.Timestamp("2020-01-01")
    rates = fx.rows_to_usd_per_unit(
        _rows(["EURUSD"], [(dt.datetime(2005, 1, 3), 1.25)]), MARKERS, cut
    )
    levels = pd.DataFrame({"E": [100.0]}, index=pd.DatetimeIndex(["2005-01-03"]))
    out = fx.convert_levels(levels, {"E": "EUR"}, rates)
    assert out["E"].iloc[0] == pytest.approx(125.0)


def test_a_units_per_usd_quote_divides():
    """A JPY level of 100 at USDJPY 100 is 1 USD."""
    cut = pd.Timestamp("2020-01-01")
    rates = fx.rows_to_usd_per_unit(
        _rows(["USDJPY"], [(dt.datetime(2005, 1, 3), 100.0)]), MARKERS, cut
    )
    levels = pd.DataFrame({"J": [100.0]}, index=pd.DatetimeIndex(["2005-01-03"]))
    assert fx.convert_levels(levels, {"J": "JPY"}, rates)["J"].iloc[0] == pytest.approx(1.0)


def test_the_convention_table_fixes_the_direction_of_every_column():
    mult = {c for c, (_ccy, how) in fx.QUOTE_CONVENTION.items() if how == fx.MULTIPLY}
    assert mult == {"EURUSD", "GBPUSD"}
    div = {c for c, (_ccy, how) in fx.QUOTE_CONVENTION.items() if how == fx.DIVIDE}
    assert div == {"USDCAD", "USDHKD", "USDINR", "USDKRW", "USDTWD", "USDJPY"}


def test_an_unknown_column_is_refused():
    with pytest.raises(InvariantViolation, match="not in the quote-convention table"):
        fx.rows_to_usd_per_unit(
            _rows(["EURUSD", "CHFUSD"], [(dt.datetime(2005, 1, 3), 1.2, 1.1)]),
            MARKERS,
            pd.Timestamp("2020-01-01"),
        )


def test_the_reader_cuts_at_the_holdout(params):
    cut = holdout_start(params)
    rows = _rows(
        ["EURUSD"],
        [
            (dt.datetime(2019, 12, 31), 1.1),
            (dt.datetime(2020, 1, 1), 1.2),
            (dt.datetime(2026, 10, 9), 1.3),
        ],
    )
    rates = fx.rows_to_usd_per_unit(rows, MARKERS, cut)
    assert rates.index.max() == pd.Timestamp("2019-12-31")
    assert len(rates) == 1


def test_blank_and_marker_are_missing_not_zero():
    rates = fx.rows_to_usd_per_unit(
        _rows(
            ["EURUSD", "USDJPY"],
            [
                (dt.datetime(2005, 1, 3), None, 100.0),
                (dt.datetime(2005, 1, 4), "#N/A", ""),
                (dt.datetime(2005, 1, 5), 1.25, 125.0),
            ],
        ),
        MARKERS,
        pd.Timestamp("2020-01-01"),
    )
    assert rates["EUR"].isna().tolist() == [True, True, False]
    assert rates["JPY"].isna().tolist() == [False, True, False]
    assert not bool((rates.fillna(1.0) == 0).to_numpy().any())


def test_a_rate_that_is_not_positive_is_refused():
    with pytest.raises(InvariantViolation, match="zero or negative"):
        fx.rows_to_usd_per_unit(
            _rows(["USDJPY"], [(dt.datetime(2005, 1, 3), 0.0)]), MARKERS, pd.Timestamp("2020-01-01")
        )


# --- no carrying ----------------------------------------------------------------------------


def test_a_date_without_a_rate_has_no_usd_level():
    """The previous day's rate is not carried over a gap."""
    rates = fx.rows_to_usd_per_unit(
        _rows(
            ["EURUSD"],
            [(dt.datetime(2005, 1, 3), 1.25), (dt.datetime(2005, 1, 5), 1.25)],
        ),
        MARKERS,
        pd.Timestamp("2020-01-01"),
    )
    idx = pd.DatetimeIndex(["2005-01-03", "2005-01-04", "2005-01-05"])
    levels = pd.DataFrame({"E": [100.0, 101.0, 102.0]}, index=idx)
    out = fx.convert_levels(levels, {"E": "EUR"}, rates)
    assert out["E"].isna().tolist() == [False, True, False]
    assert fx.dates_without_rate(
        levels["E"], rates["EUR"], pd.Timestamp("2001-01-02"), pd.Timestamp("2020-01-01")
    ) == ["2005-01-04"]


# --- the guard ------------------------------------------------------------------------------


def test_an_unconverted_non_usd_series_is_refused():
    with pytest.raises(InvariantViolation, match="CHF"):
        fx.plan({"A": "USD", "B": "CHF"})


def test_a_blank_quote_currency_is_reported_not_refused():
    convert, blank = fx.plan({"A": None, "B": "#N/A", "C": "", "D": "USD", "E": "EUR"})
    assert blank == ["A", "B", "C"]
    assert convert == {"E": "EUR"}


def test_a_series_already_converted_at_construction_is_exempt():
    convert, blank = fx.plan({"X": "EUR"}, exempt={"X"})
    assert convert == {} and blank == []


# --- the loader ---------------------------------------------------------------------------


@pytest.fixture
def fx_loader(tmp_path, params, monkeypatch):
    def make(with_row=True, with_file=True):
        universe = tmp_path / "universe"
        universe.mkdir(exist_ok=True)
        (universe / "raw_manifest.csv").write_text(
            ",".join(HEADER) + "\n" + (FX_ROW if with_row else "")
        )
        raw = tmp_path / "raw"
        raw.mkdir(exist_ok=True)
        if with_file:
            path = raw / "fx.xlsx"
            days = pd.bdate_range("2005-01-03", "2021-01-29")
            data = [(d.to_pydatetime(), 1.25, 100.0) for d in days]
            data = [r for r in data if r[0].date() != dt.date(2005, 1, 5)]
            _write_fx(path, _rows(["EURUSD", "USDJPY"], data))
            monkeypatch.setattr(fx, "SHA256_PREFIX", fx.file_sha256(path)[:16])
        return BloombergLoader(params, raw_dir=raw, universe_dir=universe)

    return make


def _levels():
    idx = pd.bdate_range("2005-01-03", "2005-01-07")
    return pd.DataFrame(
        {"E": [100.0] * 5, "J": [100.0] * 5, "U": [50.0] * 5, "B": [10.0] * 5}, index=idx
    )


def _metas():
    return {
        "E": _meta("E", "EUR"),
        "J": _meta("J", "JPY"),
        "U": _meta("U", "USD"),
        "B": _meta("B", ""),
    }


def test_the_loader_converts_and_records(fx_loader):
    loader = fx_loader()
    out, meta, rep = loader._to_usd(_levels(), _metas(), exempt=frozenset())
    assert out["E"].iloc[0] == pytest.approx(125.0)
    assert out["J"].iloc[0] == pytest.approx(1.0)
    assert out["U"].tolist() == [50.0] * 5
    assert meta["E"].currency == "USD" and meta["E"].quote_currency == "EUR"
    assert meta["U"].quote_currency is None
    assert rep["converted"]["E"]["column"] == "EURUSD"
    assert rep["converted"]["E"]["dates_dropped"] == ["2005-01-05"]
    assert rep["blank_quote_currency"] == ["B"]
    assert meta["B"].currency == "USD"
    assert np.isnan(out["E"].iloc[2])


def test_the_converted_series_follows_the_gap_without_carrying(fx_loader):
    loader = fx_loader()
    out, _meta_out, _rep = loader._to_usd(_levels(), _metas(), exempt=frozenset())
    assert out["E"].isna().tolist() == [False, False, True, False, False]


def test_a_fixture_without_the_fx_file_loads_when_no_series_needs_it(fx_loader):
    loader = fx_loader(with_row=False, with_file=False)
    levels = _levels()[["U", "B"]]
    metas = {k: v for k, v in _metas().items() if k in levels.columns}
    out, _meta_out, rep = loader._to_usd(levels, metas, exempt=frozenset())
    assert out.equals(levels)
    assert rep["converted"] == {}


def test_a_series_that_needs_conversion_is_refused_without_a_manifest_row(fx_loader):
    loader = fx_loader(with_row=False, with_file=False)
    with pytest.raises(InvariantViolation, match="fx_spot"):
        loader._to_usd(_levels(), _metas(), exempt=frozenset())


def test_a_file_that_is_not_the_one_expected_is_refused(fx_loader, monkeypatch):
    from signal_lab.loaders.exusd_analytics import RawFileChanged

    loader = fx_loader()
    monkeypatch.setattr(fx, "SHA256_PREFIX", "0000000000000000")
    with pytest.raises(RawFileChanged):
        loader._to_usd(_levels(), _metas(), exempt=frozenset())


def test_an_unconvertible_series_stops_the_load(fx_loader):
    loader = fx_loader()
    metas = _metas()
    metas["E"] = _meta("E", "CHF")
    with pytest.raises(InvariantViolation, match="CHF"):
        loader._to_usd(_levels(), metas, exempt=frozenset())


def test_nothing_on_or_after_the_holdout_is_converted(fx_loader):
    loader = fx_loader()
    idx = pd.bdate_range("2019-12-26", "2020-01-08")
    levels = pd.DataFrame({"E": 100.0}, index=idx)
    out, _m, _r = loader._to_usd(levels, {"E": _meta("E", "EUR")}, exempt=frozenset())
    assert out["E"].loc[idx < pd.Timestamp("2020-01-01")].notna().all()
    assert out["E"].loc[idx >= pd.Timestamp("2020-01-01")].isna().all()
