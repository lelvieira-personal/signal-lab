"""
JPMaQS / Macrosynergy backend. Phase 3 (SUBSTRATE sections 5.6 and 16).

The download is `scripts/jpmaqs_pull.py` (the owner runs it; it writes one raw
pull under `data/raw/jpmaqs/<pull_id>/`). This module turns a raw pull into a
`VintagePanel`, because the parts that are easy to get wrong are the
conventions, not the HTTP call.

Three conventions, all of which will silently corrupt a panel if mishandled:

1.  A JPMaQS ticker is `{cid}_{xcat}` -- a three-character cross-section id, an
    underscore, then the extended category. `USD_INTRGDP_NSA_P1M1ML12_D1M1ML3`
    is cid `USD` and xcat `INTRGDP_NSA_P1M1ML12_D1M1ML3`. The download API takes
    cids and xcats as separate lists and returns their cross product, so a set
    of requested tickers has to be split, downloaded, and filtered back down.

2.  JPMaQS `real_date` is "the date of the information state as observed by the
    markets" -- the KNOWLEDGE date. This lab's VintagePanel calls the period the
    number describes `period_end`. The two vocabularies invert; see
    decisions/0014 and the note in loaders/base.py.

3.  Every ticker must carry `value`, `grading` and `eop_lag` (SUBSTRATE 5.6).
    Without `grading` the grade filter cannot run; without `eop_lag` the period
    cannot be recovered from the knowledge date, and the result is a panel that
    looks point-in-time and is not.

SUBSTRATE section 5.6 also makes this module the gate on the whole search:
until the macro block is in the snapshot, no signal search runs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel, SeriesMeta, VintagePanel
from signal_lab.loaders.bloomberg import LoaderNotImplemented
from signal_lab.loaders.env import check_secret
from signal_lab.loaders.holdout import enforce_holdout, holdout_start
from signal_lab.params import Params, get_params

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_ROOT = REPO_ROOT / "data" / "raw" / "jpmaqs"
REQUEST_TXT = REPO_ROOT / "data" / "jpmaqs" / "request.txt"
QDF_NAME = "qdf.parquet"
PULL_MANIFEST_NAME = "pull_manifest.json"

QDF_COLUMNS = ("cid", "xcat", "real_date", "value", "grading", "eop_lag")
# eop_lag buckets for the coverage report, in days: (label, low, high inclusive).
EOP_LAG_BUCKETS = (("0", 0, 0), ("1-31", 1, 31), ("32-92", 32, 92), (">92", 93, None))
# decisions/0047: a negative eop_lag is a period that ends after the number is known.
# Counted in three buckets (days), and the third must be empty for anything to be built.
NEGATIVE_LAG_BUCKETS = ("-1..-31", "-32..-92", "below -92")
NEGATIVE_LAG_CHECKPOINT_DAYS = -92


class NegativeLagCheckpoint(ValueError):
    """decisions/0047 section 3: a valued row's period ends more than 92 days after it is known."""


# cid is exactly three characters, then the xcat. Anchored so a Bloomberg
# ticker (LUACTRUU, MXUS0EN) cannot match by accident.
TICKER_RE = re.compile(r"^(?P<cid>[A-Z]{3})_(?P<xcat>[A-Z0-9][A-Z0-9_]*)$")


class JPMaQSTickerError(ValueError):
    """A ticker that is not in {cid}_{xcat} form."""


def split_ticker(ticker: str) -> tuple[str, str]:
    """`USD_CPIH_SJA_P3M3ML3AR` -> `('USD', 'CPIH_SJA_P3M3ML3AR')`."""
    m = TICKER_RE.match(ticker)
    if not m:
        raise JPMaQSTickerError(
            f"{ticker!r} is not a JPMaQS ticker; expected a 3-character cid, an "
            f"underscore, then the xcat, e.g. USD_CPIH_SJA_P3M3ML3AR"
        )
    return m.group("cid"), m.group("xcat")


def is_jpmaqs_ticker(ticker: str) -> bool:
    return bool(TICKER_RE.match(ticker))


def split_tickers(tickers: list[str]) -> tuple[list[str], list[str]]:
    """
    Split a set of tickers into the cids and xcats to request.

    The API returns the cross product, which is usually larger than what was
    asked for -- four cids and three xcats is twelve series for a request that
    named five. That is the efficient shape (one call rather than five) but the
    caller must filter the result back down to the tickers actually requested,
    or the panel silently gains series no hypothesis registered. `filter_panel`
    below does that.
    """
    cids, xcats = set(), set()
    for t in tickers:
        cid, xcat = split_ticker(t)
        cids.add(cid)
        xcats.add(xcat)
    return sorted(cids), sorted(xcats)


def cross_product_size(tickers: list[str]) -> tuple[int, int]:
    """(requested, downloaded) counts, for the request file and the digest."""
    cids, xcats = split_tickers(tickers)
    return len(tickers), len(cids) * len(xcats)


# --- raw pull -> VintagePanel ------------------------------------------------


class RawPullMissing(FileNotFoundError):
    """No raw JPMaQS pull to load."""


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_request_tickers(path: Path | str = REQUEST_TXT) -> list[str]:
    """The pull list: one ticker per line, `#` comments and blank lines ignored."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    tickers = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    for t in tickers:
        split_ticker(t)
    if len(set(tickers)) != len(tickers):
        raise ValueError(f"{path} lists a ticker twice")
    return tickers


def find_pull(raw_root: Path | str, pull_id: str | None = None) -> Path:
    """The named pull, or the newest one. A missing pull is an error, never an empty panel."""
    root = Path(raw_root)
    hint = "run `make jpmaqs-pull` (the owner runs it; it needs the vendor credentials)"
    if pull_id is not None:
        pull_dir = root / pull_id
        if not (pull_dir / QDF_NAME).exists() or not (pull_dir / PULL_MANIFEST_NAME).exists():
            raise RawPullMissing(f"no raw JPMaQS pull {pull_id!r} under {root}; {hint}")
        return pull_dir
    candidates = (
        sorted(
            d.name
            for d in root.iterdir()
            if d.is_dir()
            and d.name.startswith("P-")
            and (d / QDF_NAME).exists()
            and (d / PULL_MANIFEST_NAME).exists()
        )
        if root.exists()
        else []
    )
    if not candidates:
        raise RawPullMissing(f"no raw JPMaQS pull under {root}; {hint}")
    return root / candidates[-1]


def filter_panel(frame: pd.DataFrame, tickers: list[str]) -> tuple[pd.DataFrame, int]:
    """
    Keep exactly the requested tickers of a long frame with `cid` and `xcat`.

    The download API returns the cross product of the requested cids and xcats,
    so a pull made that way carries series no hypothesis registered. Raises if a
    requested ticker is absent, because a silently thinner panel is a `coverage`
    failure nobody sees. Returns the filtered frame and the number of series
    (distinct tickers) dropped.
    """
    for c in ("cid", "xcat"):
        if c not in frame.columns:
            raise ValueError(f"frame has no {c!r} column")
    ticker = frame["cid"].astype(str) + "_" + frame["xcat"].astype(str)
    present = set(ticker.unique())
    missing = sorted(set(tickers) - present)
    if missing:
        raise ValueError(f"{len(missing)} requested ticker(s) absent from the frame: {missing}")
    keep = ticker.isin(set(tickers))
    return frame.loc[keep].copy(), len(present) - len(set(tickers))


def negative_lag_buckets(lag: pd.Series, ticker: pd.Series) -> dict[str, dict[str, int]]:
    """Valued rows with a negative `eop_lag`, per ticker, in the three buckets of decisions/0047."""
    neg = lag < 0
    out: dict[str, dict[str, int]] = {}
    for t, lags in lag[neg].groupby(ticker[neg]):
        out[str(t)] = {
            NEGATIVE_LAG_BUCKETS[0]: int((lags >= -31).sum()),
            NEGATIVE_LAG_BUCKETS[1]: int(((lags < -31) & (lags >= -92)).sum()),
            NEGATIVE_LAG_BUCKETS[2]: int((lags < -92).sum()),
        }
    return out


def _bucket_counts(lags: pd.Series) -> dict[str, int]:
    out = {}
    for label, lo, hi in EOP_LAG_BUCKETS:
        mask = lags >= lo if hi is None else (lags >= lo) & (lags <= hi)
        out[label] = int(mask.sum())
    return out


def qdf_to_vintage_frame(qdf: pd.DataFrame) -> pd.DataFrame:
    """
    The vendor's long frame -> VintagePanel rows, uncompressed. Pure; no I/O.

    `series_id = cid_xcat`, `knowledge_date = real_date`,
    `period_end = real_date - eop_lag days` (decisions/0014). Rows with no value
    are dropped (a day on which nothing was published is not an observation);
    the caller counts them. Refuses, rather than repairs, a frame missing a
    metric column, or a valued row whose `eop_lag` is non-finite or whose
    `grading` is missing. A NEGATIVE `eop_lag` is allowed (decisions/0047: the
    period ends after the number is known) up to the checkpoint: a valued row
    with an `eop_lag` below -92 days raises `NegativeLagCheckpoint` and nothing
    is built.
    """
    missing = [c for c in QDF_COLUMNS if c not in qdf.columns]
    if missing:
        raise ValueError(
            f"the JPMaQS frame is missing column(s) {missing}; value, grading and eop_lag "
            f"are all required (SUBSTRATE section 5.6)"
        )
    valued = qdf.loc[qdf["value"].notna()]
    lag = pd.to_numeric(valued["eop_lag"], errors="coerce")
    bad_lag = ~np.isfinite(lag)
    if bool(bad_lag.any()):
        raise ValueError(
            f"{int(bad_lag.sum())} valued row(s) have a non-finite eop_lag; "
            f"the period cannot be recovered from them"
        )
    deep = lag < NEGATIVE_LAG_CHECKPOINT_DAYS
    if bool(deep.any()):
        ticker = valued["cid"].astype(str) + "_" + valued["xcat"].astype(str)
        by_ticker = negative_lag_buckets(lag, ticker)
        raise NegativeLagCheckpoint(
            f"{int(deep.sum())} valued row(s) have an eop_lag below {NEGATIVE_LAG_CHECKPOINT_DAYS} "
            f"days (decisions/0047 section 3); nothing is built. Negative-lag rows by ticker "
            f"and bucket: {by_ticker}"
        )
    if bool(valued["grading"].isna().any()):
        raise ValueError(
            f"{int(valued['grading'].isna().sum())} valued row(s) have no grading; the grade "
            f"filter cannot run on them"
        )
    knowledge = pd.to_datetime(valued["real_date"]).dt.normalize()
    out = pd.DataFrame(
        {
            "series_id": valued["cid"].astype(str) + "_" + valued["xcat"].astype(str),
            "period_end": (knowledge - pd.to_timedelta(lag, unit="D")).dt.normalize(),
            "knowledge_date": knowledge,
            "value": valued["value"].astype("float64"),
            "grading": valued["grading"].astype("float64"),
            "eop_lag": lag.astype("float64"),
        }
    )
    return out.sort_values(["series_id", "knowledge_date"], kind="stable").reset_index(drop=True)


def compress_to_change_points(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Keep a row only when (period_end, value, grading) differs from the previous
    row of the same series. The information-state series repeats the same vintage
    every day; `VintagePanel.as_of` needs only the first day each was known.
    """
    f = frame.sort_values(["series_id", "knowledge_date"], kind="stable")
    key = f[["period_end", "value", "grading"]]
    changed = (key != key.groupby(f["series_id"]).shift(1)).any(axis=1)
    first = ~f["series_id"].duplicated()
    return f.loc[changed | first].reset_index(drop=True)


def legacy_meta(series_id: str, first_known: pd.Timestamp, params: Params) -> SeriesMeta:
    """
    Meta for a macro series. A legacy euro prefix (`DEM_`, ...) maps to a country
    here, in the meta; the `series_id` keeps the vendor's name because hypotheses
    register the vendor's name.
    """
    prefix_map = params.get("data.jpmaqs.legacy_euro_prefix_map", {}) or {}
    region = series_id.split("_", 1)[0]
    for prefix, country in prefix_map.items():
        if series_id.startswith(prefix):
            region = country
            break
    return SeriesMeta(
        series_id=series_id,
        true_daily_start=pd.Timestamp(first_known),
        tier="backbone",
        section="macro",
        region=region,
    )


def build_macro_panel(
    qdf: pd.DataFrame,
    tickers: list[str],
    params: Params | None = None,
    snapshot_id: str = "jpmaqs-v1",
) -> tuple[VintagePanel, dict[str, Any]]:
    """
    Steps: filter to the requested tickers, drop and count no-value rows, convert,
    apply the grade filter, compress to change points, enforce the holdout.

    Counts are per ticker and are counts only -- no vendor value appears in them,
    except the distinct grading values the owner asked to see.
    """
    params = params or get_params()
    grade_rule = params.get("data.jpmaqs.grade_3", "exclude")
    if grade_rule != "exclude":
        raise LoaderNotImplemented(
            f"data.jpmaqs.grade_3 = {grade_rule!r} is not implemented; only 'exclude' is"
        )

    # Holdout first, on the raw dates: if the pull reaches it, something is wrong.
    if "real_date" in qdf.columns:
        enforce_holdout(pd.to_datetime(qdf["real_date"]), params, what="jpmaqs raw pull real_date")

    qdf, n_dropped_series = filter_panel(qdf, tickers)
    ticker = qdf["cid"].astype(str) + "_" + qdf["xcat"].astype(str)
    raw_rows = ticker.value_counts()
    no_value = ticker[qdf["value"].isna()].value_counts()

    full = qdf_to_vintage_frame(qdf)
    grading_counts = {
        sid: {str(k): int(v) for k, v in g["grading"].value_counts().sort_index().items()}
        for sid, g in full.groupby("series_id")
    }
    excluded_mask = full["grading"] >= 3
    excluded = full.loc[excluded_mask, "series_id"].value_counts()
    kept = full.loc[~excluded_mask].reset_index(drop=True)
    eop_buckets = {sid: _bucket_counts(g["eop_lag"]) for sid, g in kept.groupby("series_id")}
    compressed = compress_to_change_points(kept)

    # decisions/0047: the holdout binds on the knowledge date. A period may end after it
    # is known, so period_end is NOT checked; it is recorded in the manifest instead.
    enforce_holdout(compressed["knowledge_date"], params, what="jpmaqs macro knowledge_date")

    first_known = compressed.groupby("series_id")["knowledge_date"].min()
    meta = {sid: legacy_meta(sid, first_known[sid], params) for sid in sorted(first_known.index)}
    panel = VintagePanel(
        compressed,
        meta,
        snapshot_id=snapshot_id,
        source="jpmaqs",
        period_may_follow_knowledge=True,
    )
    neg_buckets = negative_lag_buckets(full["eop_lag"], full["series_id"])
    holdout = holdout_start(params)

    per_ticker = {}
    for t in sorted(tickers):
        per_ticker[t] = {
            "rows_raw": int(raw_rows.get(t, 0)),
            "rows_no_value": int(no_value.get(t, 0)),
            "rows_grade_excluded": int(excluded.get(t, 0)),
            "rows_kept_before_compression": int((kept["series_id"] == t).sum()),
            "rows_after_compression": int((compressed["series_id"] == t).sum()),
            "grading_counts": grading_counts.get(t, {}),
            "eop_lag_buckets": eop_buckets.get(t, {label: 0 for label, _, _ in EOP_LAG_BUCKETS}),
            "negative_lag_buckets": neg_buckets.get(t, dict.fromkeys(NEGATIVE_LAG_BUCKETS, 0)),
        }
    counts = {
        "n_tickers": len(tickers),
        "cross_product_series_dropped": n_dropped_series,
        "rows_raw": int(sum(v["rows_raw"] for v in per_ticker.values())),
        "rows_no_value": int(sum(v["rows_no_value"] for v in per_ticker.values())),
        "rows_grade_excluded": int(sum(v["rows_grade_excluded"] for v in per_ticker.values())),
        "rows_kept_before_compression": int(len(kept)),
        "rows_after_compression": int(len(compressed)),
        "negative_lag_rows": int(
            sum(sum(v["negative_lag_buckets"].values()) for v in per_ticker.values())
        ),
        "max_period_end": str(compressed["period_end"].max().date()),
        "rows_with_period_end_in_holdout": int((compressed["period_end"] >= holdout).sum()),
        "per_ticker": per_ticker,
    }
    return panel, counts


class JPMaQSLoader:
    source = "jpmaqs"
    phase = 3

    def __init__(self, params: Params | None = None, raw_root: Path | str | None = None):
        self.params = params or get_params()
        self.raw_root = Path(raw_root) if raw_root else RAW_ROOT

    # --- credentials -------------------------------------------------------

    def credentials(self) -> tuple[str, str]:
        keys = self.params.get("data_sources.sources.jpmaqs.env_keys", [])
        values = [os.environ.get(k) for k in keys]
        missing = [k for k, v in zip(keys, values, strict=True) if not v]
        if missing:
            raise RuntimeError(
                f"{missing} not set. Secrets come from environment variables only; "
                f"nothing key-shaped is committed."
            )
        for k, v in zip(keys, values, strict=True):
            check_secret(k, v)
        return values[0], values[1]

    def proxies(self) -> dict[str, str] | None:
        """
        Corporate proxy, or None.

        The owner's production helper builds
        `http://{os.getlogin()}:{PROXY_PWD}@proxynew.itau:8080` from `.env`.
        That host resolves on the corporate network and not elsewhere, so the
        proxy is optional here and off by default: this lab runs on a personal
        machine. Set `proxy.enabled: true` in params/data_sources.yaml when
        running somewhere the host resolves.
        """
        cfg = self.params.get("data_sources.sources.jpmaqs.proxy", {}) or {}
        if not cfg.get("enabled", False):
            return None
        pwd = os.environ.get(cfg.get("password_env", "PROXY_PWD"))
        if not pwd:
            raise RuntimeError(f"{cfg.get('password_env')} not set but proxy.enabled is true")
        check_secret(cfg.get("password_env", "PROXY_PWD"), pwd)
        user = os.getlogin()
        url = f"http://{user}:{pwd}@{cfg['host']}:{cfg.get('port', 8080)}"
        return {"http": url, "https": url}

    def required_metrics(self) -> list[str]:
        return list(self.params.get("data_sources.sources.jpmaqs.required_metrics", []))

    # --- the interface -----------------------------------------------------

    def load_returns(self, snapshot_id: str) -> ReturnPanel:
        raise LoaderNotImplemented("JPMaQS is a macro source, not a return source")

    def load_analytics(self, snapshot_id: str) -> AnalyticsPanel:
        raise LoaderNotImplemented("JPMaQS is a macro source, not an analytics source")

    def load_macro(
        self, snapshot_id: str = "jpmaqs-v1", pull_id: str | None = None
    ) -> VintagePanel:
        return self.load_macro_with_counts(snapshot_id, pull_id)[0]

    def load_macro_with_counts(
        self, snapshot_id: str = "jpmaqs-v1", pull_id: str | None = None
    ) -> tuple[VintagePanel, dict[str, Any]]:
        """
        One raw pull -> a VintagePanel, plus the counts the snapshot manifest and
        the coverage report need. `pull_id=None` takes the newest pull.
        """
        pull_dir = find_pull(self.raw_root, pull_id)
        manifest = json.loads((pull_dir / PULL_MANIFEST_NAME).read_text(encoding="utf-8"))
        qdf_path = pull_dir / QDF_NAME
        actual = file_sha256(qdf_path)
        if actual != manifest.get("sha256"):
            raise RuntimeError(
                f"{qdf_path} does not match the sha256 in its pull manifest; the raw pull "
                f"has changed since it was written. Refusing to load it."
            )
        qdf = pd.read_parquet(qdf_path)
        panel, counts = build_macro_panel(
            qdf, list(manifest["tickers"]), self.params, snapshot_id=snapshot_id
        )
        counts["pull_id"] = pull_dir.name
        counts["raw_sha256"] = actual
        return panel, counts


def search_is_open(params: Params | None = None) -> tuple[bool, str]:
    """
    Whether the signal search may run at all.

    SUBSTRATE section 5.6: the search opens only when the full signal set is in.
    A leaderboard built on price signals alone would tacitly decide what works
    before the macro block is tested, so this is a gate rather than a warning.
    Holding credentials is not holding data: only `status: loaded` opens it.
    """
    params = params or get_params()
    status = params.get("data.jpmaqs.status", "pending")
    gated = bool(params.get("data.jpmaqs.search_opens_only_when_loaded", True))
    if gated and status != "loaded":
        return False, (
            f"JPMaQS status is {status!r}. SUBSTRATE section 5.6: no signal search "
            f"runs until the macro block is in."
        )
    return True, "macro block present"
