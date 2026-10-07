"""
The ex-USD analytics file (HANDOFF task 52, decisions/0052), on a synthetic long-form workbook
built in a temp folder. Nothing reads data/raw/.
"""

from __future__ import annotations

import numpy as np
import openpyxl
import pandas as pd
import pytest

from signal_lab.loaders import exusd_analytics as exusd
from signal_lab.loaders.bloomberg import BloombergLoader
from signal_lab.loaders.holdout import holdout_start
from signal_lab.loaders.invariants import InvariantViolation

MANIFEST = "file,sheet,layout,field,currency,role,header_rows,first_data_row\n"
ROW = "x.xlsx,BBG Values,long_date_ticker,various,n/a,analytics_exusd,1,2\n"


def _daily(start, n):
    return list(pd.bdate_range(start, periods=n))


def _month_ends(n, end="2005-12-31"):
    return list(pd.date_range(end=end, periods=n, freq="BME"))


def _rows(ticker, dates, oas_field="INDEX_OAS_TSY", oas=True):
    out = []
    for i, d in enumerate(dates):
        out.append(
            (
                d.to_pydatetime(),
                ticker,
                "name",
                5.0 + i * 1e-3,
                2.0,
                0.5 if oas else "#N/A",
                oas_field,
            )
        )
    return out


def _write(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BBG Values"
    ws.append(list(exusd.COLUMNS))
    for r in rows:
        ws.append(list(r))
    wb.save(path)


def _loader(tmp_path, params, rows, with_row=True):
    universe = tmp_path / "universe"
    universe.mkdir(exist_ok=True)
    (universe / "raw_manifest.csv").write_text(MANIFEST + (ROW if with_row else ""))
    raw = tmp_path / "raw"
    raw.mkdir(exist_ok=True)
    _write(raw / "x.xlsx", rows)
    return BloombergLoader(params, raw_dir=raw, universe_dir=universe)


@pytest.fixture
def pin(monkeypatch, tmp_path):
    """Accept the synthetic file's own hash, as the real one is accepted by its prefix."""

    def _pin(loader):
        sha = exusd.file_sha256(loader.raw_dir / "x.xlsx")
        monkeypatch.setattr(exusd, "SHA256_PREFIX", sha[:16])

    return _pin


def _merge(loader, by_field=None):
    by_field = {} if by_field is None else by_field
    meta: dict = {}
    report = loader._merge_exusd_analytics(by_field, meta, ["#N/A"], loader.params)
    return by_field, meta, report


def test_the_field_map_keeps_a_swap_spread_out_of_the_treasury_field(tmp_path, params, pin):
    d = _daily("2004-01-05", 60)
    rows = _rows("TSY1", d) + _rows("SWP1", d, oas_field="INDEX_OAS_SWAP")
    loader = _loader(tmp_path, params, rows)
    pin(loader)
    by_field, meta, report = _merge(loader)
    assert set(by_field) == {
        "INDEX_OAD_TSY",
        "INDEX_YIELD_TO_WORST",
        "INDEX_OAS_TSY",
        "INDEX_OAS_SWAP",
    }
    assert set(by_field["INDEX_OAS_TSY"]) == {"TSY1"}
    assert set(by_field["INDEX_OAS_SWAP"]) == {"SWP1"}
    assert set(by_field["INDEX_OAD_TSY"]) == {"TSY1", "SWP1"}
    assert set(meta) == {"TSY1", "SWP1"} and report["tickers"] == ["SWP1", "TSY1"]


def test_an_oas_field_that_is_not_known_is_refused():
    long = pd.DataFrame(
        {
            "ticker": ["T"],
            "oas": [0.5],
            "oas_field": ["INDEX_OAS_OTHER"],
            "date": [pd.Timestamp("2004-01-05")],
        }
    )
    with pytest.raises(InvariantViolation, match="oas_field"):
        exusd.oas_field_by_ticker(long)


def test_a_monthly_run_in_is_truncated_at_the_daily_start(tmp_path, params, pin):
    monthly = _month_ends(6)
    daily = _daily(
        "2006-01-16", 80
    )  # first daily date is more than 5 days after the last month-end
    loader = _loader(tmp_path, params, _rows("T", monthly + daily))
    pin(loader)
    by_field, meta, _ = _merge(loader)
    s = by_field["INDEX_OAD_TSY"]["T"]
    assert s.dropna().index.min() == daily[0]
    assert s[s.index < daily[0]].isna().all() and s.index.min() == monthly[0]
    assert meta["T"].true_daily_start == daily[0]


def test_nothing_on_or_after_the_holdout_is_loaded(tmp_path, params, pin):
    d = _daily("2019-06-03", 400)  # runs past 2020-01-01
    assert d[-1] >= holdout_start(params)
    loader = _loader(tmp_path, params, _rows("T", d))
    pin(loader)
    by_field, _, _ = _merge(loader)
    for cols in by_field.values():
        for s in cols.values():
            assert s.index.max() < holdout_start(params)


def test_a_ticker_and_field_in_both_files_is_refused(tmp_path, params, pin):
    loader = _loader(tmp_path, params, _rows("T", _daily("2004-01-05", 60)))
    pin(loader)
    existing = {"INDEX_OAD_TSY": {"T": pd.Series([1.0], index=[pd.Timestamp("2004-01-05")])}}
    with pytest.raises(InvariantViolation, match="both analytics files"):
        _merge(loader, existing)


def test_a_file_that_is_not_the_one_expected_is_refused(tmp_path, params):
    loader = _loader(tmp_path, params, _rows("T", _daily("2004-01-05", 60)))
    with pytest.raises(exusd.RawFileChanged):
        _merge(loader)


def test_a_raw_directory_without_the_manifest_row_loads_as_before(tmp_path, params):
    loader = _loader(tmp_path, params, [], with_row=False)
    assert _merge(loader)[2] is None


def test_the_row_makes_the_file_required(tmp_path, params):
    loader = _loader(tmp_path, params, _rows("T", _daily("2004-01-05", 60)))
    (loader.raw_dir / "x.xlsx").unlink()
    with pytest.raises(FileNotFoundError):
        _merge(loader)


def test_the_missing_marker_is_missing_not_zero(tmp_path, params, pin):
    d = _daily("2004-01-05", 60)
    loader = _loader(tmp_path, params, _rows("T", d, oas=False))
    pin(loader)
    by_field, _, _ = _merge(loader)
    assert "INDEX_OAS_TSY" not in by_field  # no OAS observation, so no daily start
    assert not (by_field["INDEX_OAD_TSY"]["T"].dropna() == 0).any()


# --- the daily-start rule ---------------------------------------------------------------------


def _dates(gaps_days):
    return pd.DatetimeIndex(
        pd.Timestamp("2004-01-05") + pd.to_timedelta(np.cumsum([0, *gaps_days]), unit="D")
    )


def test_the_rule_needs_twenty_following_observations_within_five_days():
    assert exusd.true_daily_start(_dates([5] * 20)) == pd.Timestamp("2004-01-05")  # exactly 5 is in
    assert exusd.true_daily_start(_dates([5] * 19)) is None  # only 19 follow
    assert exusd.true_daily_start(_dates([6] + [1] * 20)) == pd.Timestamp(
        "2004-01-11"
    )  # a 6-day gap is out
    assert exusd.true_daily_start(_dates([1] * 3 + [6] + [1] * 25)) == pd.Timestamp("2004-01-14")
