"""
The Euro Treasury and UK Gilt bands and the euro linkers (decisions/0068, HANDOFF task 89):
`bbg_exusd_bonds_extra.xlsx`, fourteen indices delivered in euros and sterling.

Three sheets are read (task 58 described the file; nobody has read a value). `levels` is wide,
`date` plus one `<ticker>_local_<CCY>` column per ticker; every `CCY` must be `EUR` or `GBP`, and
the loader converts the levels with Bloomberg's close like every other series (decisions/0053,
0056). `analytics` is long, `date, ticker, index_name, oad_tsy, yield_to_worst, oas, oas_field`,
the header of the ex-USD analytics file, so `exusd_analytics.rows_to_long` and `split_by_field`
read it unchanged (the OAS goes to the field its own row names). `linker_fields` is the FLDS test
of the two linkers' fields: only its `mnemonic` and `<linker>_is_number` columns are read, never a
`_result`.

The tickers are the universe rows whose `source_file` is this file, read from the table and not
listed a second time here, in the shape of `japan_govt`. The true daily start is the ex-USD rule
(`exusd_analytics.true_daily_start`) on the observed dates before the holdout.

Reference series (decisions/0068 ruling 2 (b)): `LEATTREU` and `LSG1TRGU`, and `I12823GB` when the
loader report shows the Gilt bands covering 1 to 10 years start no later than it, are universe rows
with `investable` False. They are loaded into the panel like every row, so a signal or a check may
read them, and like every non-investable row they are never estimated and have no label-map row.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from signal_lab.loaders import exusd_analytics as exusd
from signal_lab.loaders.exusd_analytics import RawFileChanged, file_sha256
from signal_lab.loaders.invariants import (
    InvariantViolation,
    filter_business_days,
    to_missing,
)

ROLE_LEVELS = "returns_exusd_extra"
ROLE_ANALYTICS = "analytics_exusd_extra"
ROLE_LINKER_FIELDS = "linker_fields_exusd_extra"
SOURCE_FILE = "bbg_exusd_bonds_extra.xlsx"
SHA256_PREFIX = "7464927042b769de"  # HANDOFF task 58
CURRENCIES = ("EUR", "GBP")
LINKERS = ("BEIG1T", "BEIG3T")
LINKER_FIELDS_HEAD = (
    "mnemonic",
    *(f"{t}_result" for t in LINKERS),
    *(f"{t}_is_number" for t in LINKERS),
)

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
    `tickers`, each `<ticker>_local_EUR` or `<ticker>_local_GBP`. Rows on or after the holdout
    are kept here and counted by the caller; the loader's holdout cut removes them.
    """
    header = tuple(str(c).strip() if c is not None else "" for c in rows[0])
    if not header or header[0] != "date":
        raise InvariantViolation(f"{SOURCE_FILE} levels header is {header}, expected `date` first")
    quote: dict[str, str] = {}
    positions: dict[str, int] = {}
    for i, name in enumerate(header[1:], start=1):
        if not name:
            continue
        ticker, sep, ccy = name.partition("_local_")
        if not sep:
            raise InvariantViolation(
                f"{SOURCE_FILE} levels column {name!r} is not <ticker>_local_<CCY>"
            )
        if ccy not in CURRENCIES:
            raise InvariantViolation(
                f"{ticker}: the column {name!r} is quoted in {ccy}, not one of {CURRENCIES}. A "
                f"series whose quote currency differs from its sheet's is refused (decisions/0053)."
            )
        if ticker in positions:
            raise InvariantViolation(f"{SOURCE_FILE} levels ticker {ticker!r} appears twice")
        positions[ticker], quote[ticker] = i, ccy
    if set(positions) != set(tickers):
        raise InvariantViolation(
            f"{SOURCE_FILE} levels tickers {sorted(positions)} are not the universe's {sorted(tickers)}"
        )
    dates, body = [], []
    for r in rows[1:]:
        if not r or r[0] is None:
            continue
        dates.append(pd.Timestamp(r[0]).normalize())
        body.append([r[positions[t]] if positions[t] < len(r) else None for t in tickers])
    frame = pd.DataFrame(body, index=pd.DatetimeIndex(dates, name="date"), columns=list(tickers))
    if frame.index.duplicated().any():
        raise InvariantViolation(f"{SOURCE_FILE} levels has a repeated date")
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
    """The long sheet through the ex-USD reader; a ticker outside `tickers` is refused."""
    long = exusd.rows_to_long(rows, markers)
    unknown = sorted(set(long["ticker"]) - set(tickers))
    if unknown:
        raise InvariantViolation(
            f"{SOURCE_FILE} analytics has tickers {unknown} outside {sorted(tickers)}"
        )
    return long


def index_names(long: pd.DataFrame) -> dict[str, str]:
    """Each ticker's index name as the analytics rows give it (a label, not a value)."""
    out: dict[str, str] = {}
    for ticker, g in long.groupby("ticker"):
        names = sorted({str(v).strip() for v in g["index_name"].dropna() if str(v).strip()})
        out[str(ticker)] = " | ".join(names)
    return out


def _is_true(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().upper()
    if text in ("TRUE", "1", "YES"):
        return True
    if text in ("FALSE", "0", "NO", ""):
        return False
    return None


def linker_flags(rows: list[tuple]) -> dict[str, dict[str, bool | None]]:
    """
    `flags[linker][mnemonic]`: whether the FLDS test returned a number, from the `_is_number`
    columns only. The `_result` columns are never read.
    """
    header = tuple(str(c).strip() if c is not None else "" for c in rows[0])
    if header[: len(LINKER_FIELDS_HEAD)] != LINKER_FIELDS_HEAD:
        raise InvariantViolation(
            f"{SOURCE_FILE} linker_fields header is {header}, expected {LINKER_FIELDS_HEAD} first"
        )
    pos = {t: header.index(f"{t}_is_number") for t in LINKERS}
    flags: dict[str, dict[str, bool | None]] = {t: {} for t in LINKERS}
    for r in rows[1:]:
        if not r or r[0] is None or not str(r[0]).strip():
            continue
        mnemonic = str(r[0]).strip()
        for t, i in pos.items():
            flags[t][mnemonic] = _is_true(r[i] if i < len(r) else None)
    return flags


def linker_dates_numeric(long: pd.DataFrame) -> dict[str, dict[str, int]]:
    """Per linker and analytics column, the number of dates before the holdout with a number."""
    cols = [*exusd.VALUE_FIELDS, "oas"]
    out: dict[str, dict[str, int]] = {}
    for t in LINKERS:
        g = long[long["ticker"] == t]
        out[t] = {c: int(pd.to_numeric(g[c], errors="coerce").notna().sum()) for c in cols}
    return out
