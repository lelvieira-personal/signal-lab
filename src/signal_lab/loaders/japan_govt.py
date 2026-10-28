"""
The Japan government family (decisions/0063, 0066, HANDOFF task 76): `bbg_japan_govt.xlsx`, five
indices `I29064JP` to `I29068JP` delivered in yen.

Two sheets. `levels` is wide, `date` plus one `<ticker>_local_<CCY>` column per ticker (`PX_LAST`);
every `CCY` must be `JPY`, and the loader converts the levels with Bloomberg's close like every
other series (decisions/0053, 0056). `analytics` is long, `date, ticker, index_name, oad_tsy,
yield_to_worst`, with no OAS column. Pure functions on rows and frames, in the shape of
`exusd_analytics`; `BloombergLoader` reads the sheets and merges what comes back.

The tickers are the universe rows whose `source_file` is this file, read from the table and not
listed a second time here. The true daily start is the rule the ex-USD analytics already use
(`exusd_analytics.true_daily_start`), applied to the observed dates before the holdout; the Index
Map has no row for these series.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.loaders import exusd_analytics as exusd
from signal_lab.loaders.exusd_analytics import RawFileChanged, file_sha256
from signal_lab.loaders.holdout import holdout_start
from signal_lab.loaders.invariants import (
    InvariantViolation,
    filter_business_days,
    to_missing,
)
from signal_lab.params import Params

ROLE_LEVELS = "returns_japan_govt"
ROLE_ANALYTICS = "analytics_japan_govt"
SOURCE_FILE = "bbg_japan_govt.xlsx"
SHA256_PREFIX = "dfdf8ed9a39c5da1"
CURRENCY = "JPY"
ANALYTICS_COLUMNS = ("date", "ticker", "index_name", "oad_tsy", "yield_to_worst")
VALUE_FIELDS = {"oad_tsy": "INDEX_OAD_TSY", "yield_to_worst": "INDEX_YIELD_TO_WORST"}

__all__ = ["RawFileChanged", "file_sha256"]


def check_file(path: Path) -> str:
    """The file's sha256, after checking it begins with the expected prefix."""
    digest = file_sha256(path)
    if not digest.startswith(SHA256_PREFIX):
        raise RawFileChanged(
            f"{Path(path).name} hashes to {digest[:16]}..., not {SHA256_PREFIX}...; the loader "
            f"was written against another file. Stop and tell the owner."
        )
    return digest


def tickers_in_universe(universe: dict[str, dict[str, str]]) -> list[str]:
    """The universe rows that name this file as their source, in table order."""
    return [t for t, r in universe.items() if (r.get("source_file") or "").strip() == SOURCE_FILE]


def levels_from_rows(
    rows: list[tuple], markers: list[str], tickers: list[str]
) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    The wide sheet (header first) into a frame of levels by ticker, and the quote currency of
    each column. Missing markers become NaN, business days only. The columns must be exactly
    `tickers`, each `<ticker>_local_JPY`. Rows on or after the holdout are kept here and counted
    by the caller; the loader's holdout cut removes them.
    """
    header = tuple(str(c).strip() if c is not None else "" for c in rows[0])
    if not header or header[0] != "date":
        raise InvariantViolation(f"Japan levels header is {header}, expected `date` first")
    quote: dict[str, str] = {}
    positions: dict[str, int] = {}
    for i, name in enumerate(header[1:], start=1):
        if not name:
            continue
        ticker, sep, ccy = name.partition("_local_")
        if not sep:
            raise InvariantViolation(f"Japan levels column {name!r} is not <ticker>_local_<CCY>")
        if ccy != CURRENCY:
            raise InvariantViolation(
                f"{ticker}: the column {name!r} is quoted in {ccy}, not {CURRENCY}. A series whose "
                f"quote currency differs from its sheet's is refused (decisions/0053)."
            )
        if ticker in positions:
            raise InvariantViolation(f"Japan levels ticker {ticker!r} appears twice")
        positions[ticker], quote[ticker] = i, ccy
    if set(positions) != set(tickers):
        raise InvariantViolation(
            f"Japan levels tickers {sorted(positions)} are not the universe's {sorted(tickers)}"
        )
    dates, body = [], []
    for r in rows[1:]:
        if not r or r[0] is None:
            continue
        dates.append(pd.Timestamp(r[0]).normalize())
        body.append([r[positions[t]] if positions[t] < len(r) else None for t in tickers])
    frame = pd.DataFrame(body, index=pd.DatetimeIndex(dates, name="date"), columns=list(tickers))
    if frame.index.duplicated().any():
        raise InvariantViolation("Japan levels has a repeated date")
    frame = to_missing(frame, markers)
    return filter_business_days(frame), quote


def true_daily_starts(levels: pd.DataFrame, cut: pd.Timestamp) -> dict[str, pd.Timestamp]:
    """Per ticker, the true daily start of the observed levels before the holdout."""
    out: dict[str, pd.Timestamp] = {}
    for ticker in levels.columns:
        obs = levels[ticker].dropna()
        start = exusd.true_daily_start(obs.index[obs.index < cut])
        if start is None:
            raise InvariantViolation(f"{ticker} has no true daily start in {SOURCE_FILE}")
        out[str(ticker)] = start
    return out


def analytics_from_rows(rows: list[tuple], markers: list[str], tickers: list[str]) -> pd.DataFrame:
    """The long sheet (header first) into a frame: markers to NaN, business days only."""
    header = tuple(str(c).strip() if c is not None else "" for c in rows[0])
    if header[: len(ANALYTICS_COLUMNS)] != ANALYTICS_COLUMNS:
        raise InvariantViolation(
            f"Japan analytics header is {header}, expected {ANALYTICS_COLUMNS}"
        )
    body = [r[: len(ANALYTICS_COLUMNS)] for r in rows[1:] if r and r[0] is not None]
    frame = pd.DataFrame(body, columns=list(ANALYTICS_COLUMNS))
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    frame["ticker"] = frame["ticker"].astype(str).str.strip()
    unknown = sorted(set(frame["ticker"]) - set(tickers))
    if unknown:
        raise InvariantViolation(f"Japan analytics has tickers {unknown} outside {sorted(tickers)}")
    if frame.duplicated(["date", "ticker"]).any():
        raise InvariantViolation("Japan analytics has a repeated (date, ticker) row")
    values = to_missing(frame[list(VALUE_FIELDS)], markers)
    frame[list(values.columns)] = values
    frame = frame.set_index("date", drop=False)
    return filter_business_days(frame).reset_index(drop=True)


def split_by_field(
    long: pd.DataFrame, params: Params
) -> tuple[dict[str, dict[str, pd.Series]], dict[tuple[str, str], pd.Timestamp]]:
    """
    `by_field[field][ticker]` series, daily from each field's own start and before the holdout,
    and the starts by `(ticker, field)`. A ticker and field with no daily start is left out.
    """
    cut = holdout_start(params)
    long = long[long["date"] < cut]
    by_field: dict[str, dict[str, pd.Series]] = {}
    starts: dict[tuple[str, str], pd.Timestamp] = {}
    for ticker, g in long.groupby("ticker"):
        ticker = str(ticker)
        g = g.set_index("date").sort_index()
        for col, field in VALUE_FIELDS.items():
            s = g[col].astype(float)
            start = exusd.true_daily_start(s.dropna().index)
            if start is None:
                continue
            s = s.copy()
            s[s.index < start] = np.nan
            by_field.setdefault(field, {})[ticker] = s
            starts[(ticker, field)] = start
    return by_field, starts


def describe_analytics(
    by_field: dict[str, dict[str, pd.Series]],
    starts: dict[tuple[str, str], pd.Timestamp],
    long: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "rows": int(len(long)),
        "tickers": sorted(long["ticker"].unique()),
        "n_series_per_field": {k: len(v) for k, v in sorted(by_field.items())},
        "starts": {f"{t}|{f}": str(s.date()) for (t, f), s in sorted(starts.items())},
    }
