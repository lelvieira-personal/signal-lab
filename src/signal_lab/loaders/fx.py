"""
Every return is in dollars (decisions/0053, SUBSTRATE section 5.1 invariant 8, HANDOFF task 53).

A series delivered in another currency is converted on the same date with
`data/raw/bloomberg/bbg_curncy_hist.xlsx`, sheet `FX_Spot_USD`, Bloomberg generic spot
(`<CCY> Curncy` `PX_LAST`). It is not the WM 4pm London fix.

The quote convention is an explicit table, never inferred from a column name by a string rule.
`EURUSD` and `GBPUSD` are USD per unit and multiply. The six `USDxxx` columns are units per USD
and divide. A column that is not in the table is refused.

Pure functions on rows and frames; `BloombergLoader.load_returns` reads the sheet and applies
them. Nothing is carried: a date with a local level and no FX rate has no USD level that day.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from signal_lab.loaders.exusd_analytics import RawFileChanged, file_sha256
from signal_lab.loaders.invariants import InvariantViolation, to_missing

ROLE = "fx_spot"
SHA256_PREFIX = "1d6fbb63e8a33e2e"
DATE_HEADER = "Date"

MULTIPLY = "usd_per_unit"
DIVIDE = "units_per_usd"

# column -> (currency, how the quote reads). The only place the direction is decided.
QUOTE_CONVENTION: dict[str, tuple[str, str]] = {
    "EURUSD": ("EUR", MULTIPLY),
    "GBPUSD": ("GBP", MULTIPLY),
    "USDCAD": ("CAD", DIVIDE),
    "USDHKD": ("HKD", DIVIDE),
    "USDINR": ("INR", DIVIDE),
    "USDKRW": ("KRW", DIVIDE),
    "USDTWD": ("TWD", DIVIDE),
    "USDJPY": ("JPY", DIVIDE),
}
CURRENCY_COLUMN: dict[str, str] = {ccy: col for col, (ccy, _how) in QUOTE_CONVENTION.items()}

BASE_CURRENCY = "USD"
# What a blank quote currency looks like once read; reported, never refused.
BLANK_QUOTE = {"", "#N/A", "N/A", "NAN", "NONE"}


def check_file(path) -> str:
    """The file's sha256, after checking it begins with the expected prefix."""
    digest = file_sha256(path)
    if not digest.startswith(SHA256_PREFIX):
        raise RawFileChanged(
            f"{getattr(path, 'name', path)} hashes to {digest[:16]}..., not {SHA256_PREFIX}...; "
            f"the loader was written against another file. Stop and tell the owner."
        )
    return digest


def rows_to_usd_per_unit(rows: list[tuple], markers: list[str], cut: pd.Timestamp) -> pd.DataFrame:
    """
    Sheet rows (header first) into USD per unit of each currency, dates before `cut` only.

    Missing markers and blanks are NaN, never zero. A column outside the convention table is
    refused. A non-positive rate is refused: dividing by it, or multiplying by it, would make a
    level that is zero or negative.
    """
    if not rows:
        raise InvariantViolation("the FX sheet is empty")
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    if not header or header[0] != DATE_HEADER:
        raise InvariantViolation(f"the FX sheet's first column is {header[:1]}, expected 'Date'")
    columns = [c for c in header[1:] if c]
    unknown = [c for c in columns if c not in QUOTE_CONVENTION]
    if unknown:
        raise InvariantViolation(
            f"FX column(s) {unknown} are not in the quote-convention table "
            f"{sorted(QUOTE_CONVENTION)}. The direction is never inferred (decisions/0053)."
        )
    if len(set(columns)) != len(columns):
        raise InvariantViolation(f"the FX sheet repeats a column: {columns}")

    dates: list[pd.Timestamp] = []
    values: list[list[Any]] = []
    for row in rows[1:]:
        if not row or row[0] is None:
            continue
        try:
            ts = pd.Timestamp(row[0])
        except (ValueError, TypeError):
            continue
        if pd.isna(ts):
            continue
        ts = ts.normalize()
        if ts >= cut:
            continue
        dates.append(ts)
        vals = list(row[1 : len(header)])
        values.append(vals + [None] * (len(header) - 1 - len(vals)))
    if len(set(dates)) != len(dates):
        raise InvariantViolation("the FX sheet repeats a date")

    frame = pd.DataFrame(values, index=pd.DatetimeIndex(dates, name="date"), columns=header[1:])
    frame = frame[columns].sort_index()
    frame = to_missing(frame, markers)
    if bool((frame <= 0).to_numpy().any()):
        raise InvariantViolation("the FX sheet holds a rate that is zero or negative")

    out = {}
    for col in columns:
        ccy, how = QUOTE_CONVENTION[col]
        out[ccy] = frame[col] if how == MULTIPLY else 1.0 / frame[col]
    return pd.DataFrame(out, index=frame.index)


def describe_rates(rates: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Rows and first date per currency. Counts and dates, no rates."""
    out = {}
    for ccy in rates.columns:
        col = rates[ccy].dropna()
        out[ccy] = {
            "column": CURRENCY_COLUMN[ccy],
            "rows": int(len(col)),
            "first_date": str(col.index.min().date()) if len(col) else None,
        }
    return out


def classify(quote: str | None) -> str | None:
    """The normalised quote currency, or None when it is blank."""
    text = (quote or "").strip().upper()
    return None if text in BLANK_QUOTE else text


def plan(
    quote_currency: dict[str, str | None], exempt: set[str] | frozenset[str] = frozenset()
) -> tuple[dict[str, str], list[str]]:
    """
    The guard (decisions/0053 rule 5).

    Returns (ticker -> currency to convert, tickers with a blank quote currency). A series whose
    quote currency is neither USD nor in the convention table stops the load. `exempt` are
    series already converted at construction (the ex-USD CSV).
    """
    convert: dict[str, str] = {}
    blank: list[str] = []
    refused: dict[str, str] = {}
    for ticker, raw in quote_currency.items():
        if ticker in exempt:
            continue
        ccy = classify(raw)
        if ccy is None:
            blank.append(ticker)
        elif ccy == BASE_CURRENCY:
            continue
        elif ccy in CURRENCY_COLUMN:
            convert[ticker] = ccy
        else:
            refused[ticker] = ccy
    if refused:
        raise InvariantViolation(
            f"return series quoted in a currency the lab cannot convert: {refused}. "
            f"SUBSTRATE section 5.1 invariant 8 refuses a non-USD series that is not converted."
        )
    return convert, sorted(blank)


def convert_levels(
    levels: pd.DataFrame, convert: dict[str, str], rates: pd.DataFrame
) -> pd.DataFrame:
    """
    USD level = local level x USD per unit, on the same date. A date without a rate is NaN.

    The rates are reindexed onto the level's dates and never filled.
    """
    out = levels.copy()
    for ticker, ccy in convert.items():
        if ccy not in rates.columns:
            raise InvariantViolation(f"{ticker} is quoted in {ccy}, which the FX file lacks")
        rate = rates[ccy].reindex(levels.index)
        out[ticker] = levels[ticker].astype(float) * rate.astype(float)
    return out


def dates_without_rate(
    local: pd.Series, rate: pd.Series, start: pd.Timestamp, cut: pd.Timestamp
) -> list[str]:
    """Dates in [start, cut) with a local level and no rate: the days that lose their level."""
    idx = local.index
    mask = local.notna().to_numpy() & ~np.asarray(rate.reindex(idx).notna())
    mask &= np.asarray((idx >= start) & (idx < cut))
    return [str(d.date()) for d in idx[mask]]
