"""
The implied-vol file (HANDOFF task 59, decisions/0061), on synthetic blocks only. Nothing reads
data/raw/.
"""

from __future__ import annotations

import openpyxl
import pandas as pd
import pytest

from signal_lab.loaders import impvol
from signal_lab.loaders.holdout import holdout_start
from signal_lab.loaders.invariants import InvariantViolation
from signal_lab.loaders.jpmaqs import TICKER_RE

OVR = "IVOL_MATURITY=MATURITY_90D"


def _sheet(blocks):
    """Rows for `blocks = [(series_id, security, field, [(date, value), ...]), ...]`."""
    n = max(len(b[3]) for b in blocks)
    rows = [[], [], [], []] + [[] for _ in range(n)]
    for sid, sec, field, obs in blocks:
        for r, v in zip(rows[:4], (sid, sec, field, OVR), strict=True):
            r.extend([v, None, None])
        for i in range(n):
            d, v = obs[i] if i < len(obs) else (None, None)
            rows[4 + i].extend([d, v, None])
    return [tuple(r[:-1]) for r in rows]  # the final blank column is not delivered


def _fridays(start, n):
    return list(pd.date_range(start, periods=n, freq="W-FRI"))


def _obs(dates, values):
    return [(d.to_pydatetime(), v) for d, v in zip(dates, values, strict=True)]


def test_the_block_layout_is_read_back(params):
    fr = _fridays("2010-01-01", 3)
    rows = _sheet([("SPX_IV3M_25DP", "SPX Index", "IVOL_DELTA", _obs(fr, [20.0, 21.0, 22.0]))])
    out = impvol.read_blocks(rows, "IV_Weekly_v")
    assert list(out.columns) == list(impvol.LONG_COLUMNS)
    assert out["series_id"].unique().tolist() == ["SPX Index|IV3M_25DP"]
    assert out["workbook_series_id"].unique().tolist() == ["SPX_IV3M_25DP"]
    assert out["overrides"].unique().tolist() == [OVR]
    assert out["value"].tolist() == [20.0, 21.0, 22.0]


def test_a_text_value_is_refused_with_its_series_named():
    rows = _sheet(
        [
            (
                "EZU_IV3M_10DP",
                "EZU US Equity",
                "IVOL_DELTA",
                [(pd.Timestamp("2010-01-01"), "#N/A N/A")],
            )
        ]
    )
    with pytest.raises(InvariantViolation, match="EZU_IV3M_10DP"):
        impvol.read_blocks(rows, "IV_Weekly_v")


def test_an_empty_header_cell_is_refused():
    rows = _sheet([("EZU_IV3M_10DP", "", "IVOL_DELTA", [(pd.Timestamp("2010-01-01"), 1.0)])])
    with pytest.raises(InvariantViolation, match="EZU_IV3M_10DP"):
        impvol.read_blocks(rows, "IV_Weekly_v")


def test_lab_ids_never_look_like_a_jpmaqs_ticker_but_the_workbook_ids_do():
    assert TICKER_RE.match("SPX_IV3M_10DP")
    for wid, sec in [
        ("SPX_IV3M_10DP", "SPX Index"),
        ("XAUUSD_IV3M_25R", "XAUUSD25R3M BGN Curncy"),
        ("EZU_IV3M_M100", "EZU US Equity"),
        ("SKEW", "SKEW Index"),
    ]:
        assert not TICKER_RE.match(impvol.lab_id(wid, sec))
    assert impvol.lab_id("SKEW", "SKEW Index") == "SKEW Index|PX_LAST"
    assert impvol.lab_id("XAUUSD_IV3M_25R", "XAUUSD25R3M BGN Curncy") == (
        "XAUUSD25R3M BGN Curncy|IV3M_25R"
    )
    with pytest.raises(InvariantViolation):
        impvol.lab_id("FOO_BAR", "FOO Index")


def test_two_blocks_with_one_lab_id_are_refused():
    obs = [(pd.Timestamp("2010-01-01"), 1.0)]
    rows = _sheet(
        [
            ("SPX_IV3M_10DP", "SPX Index", "IVOL_DELTA", obs),
            ("SPX_IV3M_10DP", "SPX Index", "IVOL_DELTA", obs),
        ]
    )
    with pytest.raises(InvariantViolation, match="share the lab id"):
        impvol.read_blocks(rows, "IV_Weekly_v")


def test_a_weekly_date_that_is_not_a_friday_is_refused(params):
    rows = _sheet(
        [("EWJ_IV3M_10DP", "EWJ US Equity", "IVOL_DELTA", [(pd.Timestamp("2010-01-06"), 1.0)])]
    )
    with pytest.raises(InvariantViolation, match="Friday"):
        impvol.to_fridays(impvol.read_blocks(rows, "IV_Weekly_v"), "weekly", params)


def test_daily_becomes_weekly_by_the_last_day_and_the_holdout_week_goes_whole(params):
    cut = holdout_start(params)
    assert cut == pd.Timestamp("2020-01-01")
    days = list(pd.bdate_range("2019-12-23", "2020-01-03"))  # two weeks; the second ends 01-03
    vals = [float(i) for i in range(len(days))]
    rows = _sheet([("SPX_IV3M_M100", "SPX Index", "IVOL_MONEYNESS", _obs(days, vals))])
    out = impvol.to_fridays(impvol.read_blocks(rows, "IV_Daily_v"), "daily", params)
    assert out["date"].tolist() == [pd.Timestamp("2019-12-27")]
    assert out["value"].tolist() == [4.0]  # Friday 12-27 is the fifth day, the last of its week


def test_daily_takes_the_last_observation_even_when_friday_is_missing(params):
    days = [pd.Timestamp("2010-03-01"), pd.Timestamp("2010-03-02"), pd.Timestamp("2010-03-04")]
    rows = _sheet([("SPX_IV3M_M100", "SPX Index", "IVOL_MONEYNESS", _obs(days, [1.0, 2.0, 3.0]))])
    out = impvol.to_fridays(impvol.read_blocks(rows, "IV_Daily_v"), "daily", params)
    assert out["date"].tolist() == [pd.Timestamp("2010-03-05")]
    assert out["value"].tolist() == [3.0]


def _panel(values):
    fr = _fridays("2010-01-01", len(values))
    rows = _sheet([("XAUUSD_IV3M_25R", "XAUUSD25R3M BGN Curncy", "PX_LAST", _obs(fr, values))])
    return impvol.drop_stale(impvol.read_blocks(rows, "IV_Weekly_v"))


def test_a_run_of_five_identical_weeks_is_kept_whole():
    panel = _panel([1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 3.0])
    assert len(panel.long) == 7
    assert panel.stale.empty


def test_a_run_of_six_keeps_one_and_removes_five():
    panel = _panel([1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 3.0])
    assert len(panel.long) == 3
    assert len(panel.stale) == 5
    assert panel.long["value"].tolist() == [1.0, 2.0, 3.0]
    assert panel.stale["date"].min() == pd.Timestamp("2010-01-15")


def test_a_missing_friday_ends_a_run():
    fr = _fridays("2010-01-01", 8)
    fr = fr[:3] + fr[4:]  # one Friday absent inside a run of eight equal values
    rows = _sheet([("XAUUSD_IV3M_25R", "XAUUSD25R3M BGN Curncy", "PX_LAST", _obs(fr, [2.0] * 7))])
    panel = impvol.drop_stale(impvol.read_blocks(rows, "IV_Weekly_v"))
    assert panel.stale.empty


def _write(path, weekly, daily):
    wb = openpyxl.Workbook()
    for title, rows in ((impvol.WEEKLY_SHEET, weekly), (impvol.DAILY_SHEET, daily)):
        ws = wb.create_sheet(title) if wb.active.title != "Sheet" else wb.active
        ws.title = title
        for r in rows:
            ws.append(list(r))
    wb.save(path)


def test_a_file_with_the_wrong_hash_is_refused(tmp_path, params):
    fr = _fridays("2010-01-01", 2)
    weekly = _sheet([("EWJ_IV3M_10DP", "EWJ US Equity", "IVOL_DELTA", _obs(fr, [1.0, 2.0]))])
    path = tmp_path / "x.xlsx"
    _write(path, weekly, weekly)
    with pytest.raises(impvol.RawFileChanged):
        impvol.load_impvol(path, params)


def test_nothing_on_or_after_the_holdout_is_in_the_output(tmp_path, params, monkeypatch):
    fr = list(pd.date_range("2019-11-29", "2020-01-31", freq="W-FRI"))
    weekly = _sheet([("EWJ_IV3M_10DP", "EWJ US Equity", "IVOL_DELTA", _obs(fr, range(len(fr))))])
    days = list(pd.bdate_range("2019-12-23", "2020-01-10"))
    daily = _sheet([("SPX_IV3M_M100", "SPX Index", "IVOL_MONEYNESS", _obs(days, range(len(days))))])
    path = tmp_path / "x.xlsx"
    _write(path, weekly, daily)
    monkeypatch.setattr(impvol, "check_file", lambda p: "synthetic")
    panel = impvol.load_impvol(path, params)
    assert panel.long["date"].max() < holdout_start(params)
    assert panel.long["date"].max() == pd.Timestamp("2019-12-27")
    assert set(panel.long["sheet"]) == {impvol.WEEKLY_SHEET, impvol.DAILY_SHEET}
