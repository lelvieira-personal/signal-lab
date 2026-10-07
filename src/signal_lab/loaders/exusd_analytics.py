"""
The ex-USD bond analytics file (decisions/0052, HANDOFF task 52): one long sheet, a row per
date and ticker, `date, ticker, index_name, oad_tsy, yield_to_worst, oas, oas_field`.

Pure functions on rows and frames; `BloombergLoader.load_analytics` reads the sheet and merges
what comes back into the `AnalyticsPanel`. Values stay as delivered: no unit is converted and
the Treasury-OAS drop is not extended to foreign government indices.

Field map: `oad_tsy` is `INDEX_OAD_TSY`, `yield_to_worst` is `INDEX_YIELD_TO_WORST`, and `oas`
goes to the field its own row names (`oas_field`): `INDEX_OAS_TSY` or `INDEX_OAS_SWAP`. A swap
spread must never land in `INDEX_OAS_TSY`, so the field comes from the row and anything else
is refused.

True daily start. The Index Map has no row for these series, so it is derived by one rule: the
first observation from which each of the next 20 observations follows within 5 calendar days.
Anything before it is a sparse (monthly or irregular) run-in and is not part of a daily panel
(SUBSTRATE section 5.1.2). Observations on or after the holdout are dropped before the rule
runs, so the rule never sees them.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.loaders.holdout import holdout_start
from signal_lab.loaders.invariants import (
    InvariantViolation,
    filter_business_days,
    to_missing,
)
from signal_lab.params import Params

ROLE = "analytics_exusd"
SHA256_PREFIX = "a76df50225f99128"
COLUMNS = ("date", "ticker", "index_name", "oad_tsy", "yield_to_worst", "oas", "oas_field")
VALUE_FIELDS = {"oad_tsy": "INDEX_OAD_TSY", "yield_to_worst": "INDEX_YIELD_TO_WORST"}
OAS_FIELDS = ("INDEX_OAS_TSY", "INDEX_OAS_SWAP")
RUN_LENGTH = 20
MAX_GAP_DAYS = 5


class RawFileChanged(RuntimeError):
    """The file on disk is not the one this loader was written against."""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_file(path: Path) -> str:
    """The file's sha256, after checking it begins with the expected prefix."""
    digest = file_sha256(path)
    if not digest.startswith(SHA256_PREFIX):
        raise RawFileChanged(
            f"{Path(path).name} hashes to {digest[:16]}..., not {SHA256_PREFIX}...; the loader "
            f"was written against another file. Stop and tell the owner."
        )
    return digest


def rows_to_long(rows: list[tuple], markers: list[str]) -> pd.DataFrame:
    """Sheet rows (header first) into a frame: missing markers to NaN, business days only."""
    header = tuple(str(c).strip() if c is not None else "" for c in rows[0])
    if header[: len(COLUMNS)] != COLUMNS:
        raise InvariantViolation(f"ex-USD analytics header is {header}, expected {COLUMNS}")
    body = [r[: len(COLUMNS)] for r in rows[1:] if r and r[0] is not None]
    frame = pd.DataFrame(body, columns=list(COLUMNS))
    frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
    frame["ticker"] = frame["ticker"].astype(str).str.strip()
    frame["oas_field"] = frame["oas_field"].map(
        lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v).strip()
    )
    if frame.duplicated(["date", "ticker"]).any():
        raise InvariantViolation("ex-USD analytics has a repeated (date, ticker) row")
    values = to_missing(frame[list(VALUE_FIELDS) + ["oas"]], markers)
    frame[list(values.columns)] = values
    frame = frame.set_index("date", drop=False)
    keep = filter_business_days(frame)
    return keep.reset_index(drop=True)


def oas_field_by_ticker(long: pd.DataFrame) -> dict[str, str]:
    """The field each ticker's OAS belongs to, from its own rows; mixed or unknown is refused."""
    out: dict[str, str] = {}
    for ticker, g in long.groupby("ticker"):
        named = {v for v in g["oas_field"].dropna()}
        if not named:
            if g["oas"].notna().any():
                raise InvariantViolation(f"{ticker}: OAS values but no oas_field")
            continue
        if len(named) > 1 or not named <= set(OAS_FIELDS):
            raise InvariantViolation(
                f"{ticker}: oas_field {sorted(named)} is not one of {OAS_FIELDS}"
            )
        out[str(ticker)] = named.pop()
    return out


def true_daily_start(dates: pd.DatetimeIndex) -> pd.Timestamp | None:
    """
    First observation from which each of the next 20 observations follows within 5 calendar
    days, or None when there is none. `dates` are the observed dates of one ticker and field.
    """
    d = pd.DatetimeIndex(sorted(set(dates)))
    n = len(d)
    if n <= RUN_LENGTH:
        return None
    bad = np.asarray((d[1:] - d[:-1]).days > MAX_GAP_DAYS, dtype=int)
    csum = np.concatenate([[0], np.cumsum(bad)])
    for i in range(n - RUN_LENGTH):
        if csum[i + RUN_LENGTH] - csum[i] == 0:  # gaps i .. i+19: the next 20 observations
            return d[i]
    return None


def split_by_field(
    long: pd.DataFrame, params: Params
) -> tuple[dict[str, dict[str, pd.Series]], dict[tuple[str, str], pd.Timestamp], pd.DataFrame]:
    """
    `by_field[field][ticker]` series (daily from each field's own start, before the holdout),
    the starts by `(ticker, field)`, and the coverage table. A ticker and field with no daily
    start is excluded and listed in the table with an empty `first_daily`.
    """
    cut = holdout_start(params)
    long = long[long["date"] < cut]
    oas_field = oas_field_by_ticker(long)
    by_field: dict[str, dict[str, pd.Series]] = {}
    starts: dict[tuple[str, str], pd.Timestamp] = {}
    rows = []
    for ticker, g in long.groupby("ticker"):
        ticker = str(ticker)
        g = g.set_index("date").sort_index()
        columns = {col: field for col, field in VALUE_FIELDS.items()}
        if ticker in oas_field:
            columns["oas"] = oas_field[ticker]
        for col, field in columns.items():
            s = g[col].astype(float)
            obs = s.dropna()
            start = true_daily_start(obs.index)
            rows.append(
                {
                    "ticker_field": f"{ticker}|{field}",
                    "first_any": str(obs.index.min().date()) if len(obs) else "",
                    "first_daily": str(start.date()) if start is not None else "",
                    "n_before_holdout": int(len(obs)),
                }
            )
            if start is None:
                continue
            s = s.copy()
            s[s.index < start] = np.nan
            by_field.setdefault(field, {})[ticker] = s
            starts[(ticker, field)] = start
    return by_field, starts, pd.DataFrame(rows)


def describe(
    by_field: dict[str, dict[str, pd.Series]], long: pd.DataFrame, sha: str
) -> dict[str, Any]:
    return {
        "sha256": sha,
        "rows": int(len(long)),
        "tickers": sorted(long["ticker"].unique()),
        "n_series_per_field": {k: len(v) for k, v in sorted(by_field.items())},
    }
