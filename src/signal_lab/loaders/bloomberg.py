"""
Bloomberg backend. SUBSTRATE section 16, phase 2.

Reads the vendor pull in `data/raw/` into the panel types in `base.py`, under
the seven loader invariants of SUBSTRATE section 5.1. The invariants themselves
live in `invariants.py` and are shared with every other backend; this module's
job is to get the workbook into a frame those functions can police, in an order
that does not defeat them.

Layout comes from `data/universe/raw_manifest.csv` rather than from constants
here, and the per-series true daily start comes from the workbook's own
`Index Map` sheet, which SUBSTRATE section 5.1.2 names as the authority.

THE ORDER OF OPERATIONS IS LOAD-BEARING, and differs from the synthetic
backend's on purpose:

    missing markers -> business days -> truncate at true daily start
    -> splice -> hedge and withholding flags -> cut the holdout -> returns

Truncation runs BEFORE the splice. Both `LT13TRUU` and its replacement `G3OC`
begin as month-end series and only later go daily, so splicing first would fill
the target's early gap with the source's month-end era and truncation would then
blank the result, silently undoing the splice and leaving the panel exactly as
short as before. Truncating first blanks both sparse eras, and the splice then
fills daily history with daily history, which is the only join SUBSTRATE
section 2 permits.

Returns are computed LAST, after the holdout cut, so that no return anywhere in
the panel is ever computed across the holdout boundary.
"""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

from signal_lab.loaders.base import (
    AnalyticsPanel,
    ReturnPanel,
    SeriesMeta,
    SpliceRecord,
    VintagePanel,
)
from signal_lab.loaders.holdout import enforce_holdout, holdout_start
from signal_lab.loaders.invariants import (
    InvariantViolation,
    apply_splices,
    filter_business_days,
    flag_net_of_withholding,
    propagate_hedge_flags,
    returns_from_prior_observation,
    to_missing,
    truncate_at_daily_start,
)
from signal_lab.params import Params, get_params

REPO_ROOT = Path(__file__).resolve().parents[3]


class LoaderNotImplemented(NotImplementedError):
    """A real-data backend that this phase does not ship."""


class RawDataMissing(FileNotFoundError):
    """A file named in the manifest is not in data/raw/."""


# --- the workbook's own vocabulary -------------------------------------------

# Index Map columns, by header text rather than by letter: a column inserted in
# the workbook would silently shift every letter-based read, and this sheet is
# maintained by hand.
INDEX_MAP_COLUMNS = {
    "ticker": "Ticker",
    "name": "Bloomberg Security Name",
    "section": "Section",
    "first_any": "First data date",
    "frequency_flag": "Frequency flag",
    "first_daily": "First daily date",
    "sparse_obs": "Sparse-era obs (pre-daily)",
    "hedge": "Currency hedge",
    "long_name": "Long name (Bloomberg LONG_COMP_NAME)",
    "currency": "Quote ccy",
    "metric": "Analytics metric",
    "field": "Bloomberg field",
    "full_ticker": "Full Bloomberg ticker",
}

# Section 17 is the analytics inventory; 15-hedged, 16 and 18 are the overlay,
# the replacement candidate and the benchmarks, each on its own tab.
ANALYTICS_SECTION_PREFIX = "17."
HEDGED_OVERLAY_SECTION = "15. USD-Hedged Overlay (separate tab)"
CANDIDATE_SECTION_PREFIX = "16."
BENCHMARK_SECTION_PREFIX = "18."

# Columns on TR Levels that are spreadsheet bookkeeping, not series. The loader
# recomputes what they encode (`filter_business_days`, plus a coverage count)
# rather than trusting a formula it cannot see.
FLAG_HEADER = "FLAG"

BENCHMARK_CORE = ("LEGATRUU", "NDUEACWF")
BENCHMARK_PROXIES = ("SBWGU", "MXWO")


def _norm(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_timestamp(value: Any) -> pd.Timestamp | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        ts = pd.Timestamp(value)
    except (ValueError, TypeError):
        return None
    return None if pd.isna(ts) else ts.normalize()


# --- reading the workbook -----------------------------------------------------


def read_manifest(universe_dir: Path) -> list[dict[str, str]]:
    """The raw layout table. Which file, which sheet, how many header rows."""
    path = Path(universe_dir) / "raw_manifest.csv"
    if not path.exists():
        raise RawDataMissing(f"no raw manifest at {path}")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def _sheet_rows(path: Path, sheet: str) -> list[tuple]:
    """
    Every row of one sheet, streamed.

    read_only keeps a 71 MB workbook off the heap; values_only skips building a
    Cell object per observation, which on a 20,700 x 102 grid is the difference
    between seconds and minutes.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet not in wb.sheetnames:
            raise RawDataMissing(f"{path.name} has no sheet {sheet!r}; has {wb.sheetnames}")
        return list(wb[sheet].iter_rows(values_only=True))
    finally:
        wb.close()


def read_index_map(path: Path, sheet: str = "Index Map") -> pd.DataFrame:
    """
    The workbook's own inventory, as a frame keyed by full ticker.

    SUBSTRATE section 5.1.2 makes the "First daily date" column the authority on
    where each series' daily history begins. It is a month-granular measurement
    -- the first calendar month holding at least fifteen observations, with a
    guard for a partial first month -- and it is the number the loader truncates
    on. Nothing here recomputes it; recomputing it would mean this module and
    the workbook could disagree.
    """
    rows = _sheet_rows(path, sheet)
    if not rows:
        raise InvariantViolation(f"{sheet} is empty")
    header = [_norm(c) for c in rows[0]]
    missing = [c for c in INDEX_MAP_COLUMNS.values() if c not in header]
    if missing:
        raise InvariantViolation(f"{sheet} is missing column(s) {missing}")
    pos = {key: header.index(col) for key, col in INDEX_MAP_COLUMNS.items()}

    records = []
    for row in rows[1:]:
        ticker = _norm(row[pos["ticker"]]) if pos["ticker"] < len(row) else None
        if not ticker:
            continue
        rec = {key: (_norm(row[i]) if i < len(row) else None) for key, i in pos.items()}
        rec["first_daily"] = _as_timestamp(rec["first_daily"])
        rec["first_any"] = _as_timestamp(rec["first_any"])
        records.append(rec)

    frame = pd.DataFrame.from_records(records)
    # Rows 110-199 hold one row per analytics ticker/metric pair, so `ticker`
    # repeats up to three times there. The workbook says to key on ticker plus
    # metric; `full_ticker` carries the Bloomberg name and is unique per row
    # only in combination with the field, so both are kept and neither is used
    # as an index on its own.
    return frame


def read_wide_sheet(
    path: Path, sheet: str, header_rows: int, first_data_row: int
) -> tuple[pd.DataFrame, list[list[str | None]]]:
    """
    A date-in-column-A grid into a frame, plus its header block.

    Returns raw cell values -- `#N/A` arrives as the string it is. Mapping it to
    NaN is `to_missing`'s job and happens once, centrally, so that no backend
    can quietly decide a missing observation is a zero.
    """
    rows = _sheet_rows(path, sheet)
    if len(rows) < first_data_row:
        raise InvariantViolation(f"{sheet} has {len(rows)} rows, expected data at {first_data_row}")

    header = [[_norm(c) for c in rows[i]] for i in range(header_rows)]
    width = max(len(r) for r in rows[:header_rows])
    header = [h + [None] * (width - len(h)) for h in header]

    dates: list[pd.Timestamp] = []
    values: list[list[Any]] = []
    for row in rows[first_data_row - 1 :]:
        if not row:
            continue
        ts = _as_timestamp(row[0])
        if ts is None:
            continue
        dates.append(ts)
        padded = list(row[:width]) + [None] * (width - len(row))
        values.append(padded[1:])

    frame = pd.DataFrame(values, index=pd.DatetimeIndex(dates, name="date"))
    return frame, header


def _series_columns(header: list[list[str | None]]) -> dict[str, int]:
    """
    Ticker -> positional index, for a wide sheet whose first header row is the
    ticker. Bookkeeping columns (`FLAG`) and blanks end the block.
    """
    out: dict[str, int] = {}
    for i, ticker in enumerate(header[0][1:]):
        if ticker is None or ticker.upper() == FLAG_HEADER:
            continue
        if ticker in out:
            raise InvariantViolation(f"ticker {ticker!r} appears twice in the header")
        out[ticker] = i
    return out


def _named_frame(frame: pd.DataFrame, columns: dict[str, int]) -> pd.DataFrame:
    out = frame.iloc[:, list(columns.values())].copy()
    out.columns = list(columns)
    return out


def read_exusd_csv(path: Path) -> pd.DataFrame:
    """
    The unhedged-USD international bond panel.

    Each ticker appears three times -- local level, USD-unhedged level, and the
    FX rate used to convert. Only the USD-unhedged column is a return series in
    this panel's currency; the other two are the workings. The days where no
    FRED fix existed were dropped at construction rather than interpolated, so
    the gaps are genuine missing observations and stay NaN.
    """
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.DatetimeIndex(frame.index, name="date")
    suffix = "_USD_unhedged"
    cols = {c[: -len(suffix)]: c for c in frame.columns if c.endswith(suffix)}
    if not cols:
        raise InvariantViolation(f"{path.name} has no *{suffix} columns; got {list(frame.columns)}")
    out = frame[list(cols.values())].copy()
    out.columns = list(cols)
    return out


# --- metadata -----------------------------------------------------------------


def read_universe(universe_dir: Path) -> dict[str, dict[str, str]]:
    """`investable_universe.csv`, keyed by ticker. Tier and cost bucket live here."""
    path = Path(universe_dir) / "investable_universe.csv"
    if not path.exists():
        raise RawDataMissing(f"no investable universe at {path}")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {r["ticker"]: r for r in csv.DictReader(fh)}


def _tier_from_start(start: pd.Timestamp, params: Params) -> str:
    """
    SUBSTRATE section 5.2, applied only where the universe table is silent.

    The five ex-USD series carry an empty tier in `investable_universe.csv`
    because `scripts/build_universe.py` defers them to the loader by design.
    Every other series takes the tier the table gives it: section 5.2 says the
    loader reads tier assignment and agents do not override it.
    """
    backbone_to = pd.Timestamp(params.get("data.tiers.backbone.daily_start_on_or_before"))
    second_to = pd.Timestamp(params.get("data.tiers.second.daily_start_to"))
    if start <= backbone_to:
        return "backbone"
    if start <= second_to:
        return "second"
    return "tradable-only"


def build_series_meta(
    tickers: list[str],
    index_map: pd.DataFrame,
    universe: dict[str, dict[str, str]],
    params: Params,
    exusd_starts: dict[str, pd.Timestamp] | None = None,
) -> dict[str, SeriesMeta]:
    """
    One SeriesMeta per series, from the Index Map and the universe table.

    A series with no true daily start is REFUSED rather than defaulted. Invariant
    2 is the whole defence against month-end observations entering a daily panel,
    and a default start of "the beginning of the data" would disable it silently
    for exactly the series whose history is most ragged.

    `region` is set to the series' Section. That is a conservative placeholder,
    not a region map: `cross_region_covariance` treats any pair with differing
    region labels as non-synchronous and estimates it on 2-day overlapping
    returns, so using Section means more pairs get the overlap treatment than
    strictly need it, never fewer. SUBSTRATE section 5.1.7 forbids the error in
    the other direction. A real region map is an owner decision and is noted in
    the loader report rather than invented here.
    """
    exusd_starts = exusd_starts or {}
    by_ticker = {
        r["ticker"]: r
        for _, r in index_map.iterrows()
        if not str(r.get("section") or "").startswith(ANALYTICS_SECTION_PREFIX)
    }

    net_prefixes = list(params.get("data.net_of_withholding.prefixes", []))
    meta: dict[str, SeriesMeta] = {}
    for ticker in tickers:
        row = by_ticker.get(ticker, {})
        uni = universe.get(ticker, {})

        start = row.get("first_daily") if row is not None else None
        if start is None or pd.isna(start):
            start = exusd_starts.get(ticker)
        if start is None or pd.isna(start):
            raise InvariantViolation(
                f"{ticker} has no true daily start in the Index Map and none in the "
                f"ex-USD coverage table. SUBSTRATE section 5.1.2 truncates every "
                f"series at that date; defaulting it would disable the frequency "
                f"veto for this series."
            )
        start = pd.Timestamp(start)

        tier = (uni.get("tier") or "").strip() or _tier_from_start(start, params)
        section = (
            (row.get("section") if row is not None else None)
            or uni.get("section")
            or "unclassified"
        )
        sparse = row.get("sparse_obs") if row is not None else None
        month_end_before = start if sparse not in (None, "", "0") else None

        meta[ticker] = SeriesMeta(
            series_id=ticker,
            true_daily_start=start,
            tier=tier,  # type: ignore[arg-type]
            hedged=str(uni.get("hedged", "False")).lower() == "true",
            gross=not any(ticker.startswith(p) for p in net_prefixes),
            section=section,
            cost_bucket=(uni.get("cost_bucket") or "high"),
            month_end_only_before=month_end_before,
            region=section,
            currency=(row.get("currency") if row is not None else None) or "USD",
        )
    return meta


# --- the loader ---------------------------------------------------------------


class BloombergLoader:
    """
    Index total returns and index analytics, from the vendor workbook.

    The pulled field is `TOT_RETURN_INDEX_GROSS_DVDS` -- a cumulative gross
    total-return index level, not a price index -- with `Fill=NA`, so a
    non-trading day is `#N/A` rather than a repeat of the previous level. That
    is what makes invariant 1 enforceable: there is nothing to un-fill.
    """

    source = "bloomberg"
    phase = 2

    def __init__(
        self,
        params: Params | None = None,
        raw_dir: Path | str | None = None,
        universe_dir: Path | str | None = None,
    ):
        self.params = params or get_params()
        self.raw_dir = Path(raw_dir) if raw_dir else REPO_ROOT / "data" / "raw"
        self.universe_dir = Path(universe_dir) if universe_dir else REPO_ROOT / "data" / "universe"
        self._manifest: list[dict[str, str]] | None = None
        self.report: dict[str, Any] = {}

    # -- manifest plumbing ----------------------------------------------------

    def manifest(self) -> list[dict[str, str]]:
        if self._manifest is None:
            self._manifest = read_manifest(self.universe_dir)
        return self._manifest

    def _entry(self, role: str) -> dict[str, str]:
        for row in self.manifest():
            if row.get("role") == role:
                return row
        raise RawDataMissing(f"raw_manifest.csv has no row with role {role!r}")

    def _path(self, entry: dict[str, str]) -> Path:
        candidates = [
            self.raw_dir / entry["file"],
            self.raw_dir / "bloomberg" / entry["file"],
            self.raw_dir / "fred" / entry["file"],
        ]
        for path in candidates:
            if path.exists():
                return path
        raise RawDataMissing(
            f"{entry['file']} is not under {self.raw_dir}. The vendor pull is not "
            f"committed; see the project notes for where it lives."
        )

    def _read_role(self, role: str) -> tuple[pd.DataFrame, list[list[str | None]]]:
        entry = self._entry(role)
        return read_wide_sheet(
            self._path(entry),
            entry["sheet"],
            int(entry.get("header_rows", 4)),
            int(entry.get("first_data_row", 5)),
        )

    # -- returns --------------------------------------------------------------

    def load_returns(self, snapshot_id: str = "bloomberg-v1") -> ReturnPanel:
        params = self.params
        markers = list(params.get("data.calendar.missing_markers", []))

        levels_raw, header = self._read_role("returns")
        series_cols = _series_columns(header)
        levels = _named_frame(levels_raw, series_cols)

        # The replacement candidate rides along as a column so that it is
        # truncated at its own daily start like everything else, and is dropped
        # once the splice has consumed it. G3OC has a monthly-to-daily break of
        # its own (1986-11-03); splicing from its month-end era would breach
        # invariant 2 as surely as splicing from the target's.
        splice_specs = list(params.get("data.splices", []))
        wanted_sources = {
            spec.get("source")
            for spec in splice_specs
            if spec.get("active", False) and spec.get("source")
        }
        candidates, cand_header = self._read_role("returns_substitutes")
        # Only the columns named as a splice source. The candidates tab also
        # carries probe scaffolding -- "Metadata probe", per-month observation
        # counts, a comparison block -- whose headers are prose, and one of which
        # repeats. Taking the whole header row would drag those in as series.
        cand_cols = {
            ticker: i for i, ticker in enumerate(cand_header[0][1:]) if ticker in wanted_sources
        }
        missing_sources = sorted(wanted_sources - set(cand_cols))
        candidates = _named_frame(candidates, cand_cols)

        exusd = read_exusd_csv(self._path(self._entry("returns_ex_usd")))

        combined = pd.concat(
            [levels, candidates[[c for c in candidates.columns if c not in levels.columns]]],
            axis=1,
        )
        combined = combined.join(exusd, how="outer")

        # 1. markers to NaN, never to zero. Then business days only.
        combined = to_missing(combined, markers)
        combined = filter_business_days(combined)

        index_map = read_index_map(
            self._path(self._entry("index_map")), self._entry("index_map")["sheet"]
        )
        universe = read_universe(self.universe_dir)
        exusd_starts = self._exusd_starts()
        meta = build_series_meta(list(combined.columns), index_map, universe, params, exusd_starts)

        # 2. truncate at the true daily start, per series.
        before_truncation = combined
        combined = truncate_at_daily_start(combined, meta)

        # 5. splices, applied to daily history only, each one logged.
        combined, meta, records = apply_splices(combined, splice_specs, meta)
        skipped = self._skipped_splices(splice_specs, records, combined.columns)

        # A spliced series carries daily history from its source's start, so its
        # tier is recomputed from the start the splice gave it. SUBSTRATE
        # section 5.2 tells the loader to read tier assignment rather than
        # choose it, and this is not a choice: the coverage table was built
        # before the splice and cannot know that `LT13TRUU` now has daily
        # history back to G3OC's start. Leaving the old tier would bar from
        # estimation a series that demonstrably has the history. Every change is
        # reported.
        retiered = []
        for target in {r.target for r in records}:
            if target not in meta:
                continue
            was = meta[target].tier
            now = _tier_from_start(meta[target].true_daily_start, params)
            if now != was:
                meta[target] = replace(meta[target], tier=now)  # type: ignore[arg-type]
                retiered.append(
                    {
                        "series": target,
                        "from": was,
                        "to": now,
                        "spliced_daily_start": str(meta[target].true_daily_start.date()),
                    }
                )

        # 4 and 6. flags carried, never corrected.
        meta = flag_net_of_withholding(
            meta, list(params.get("data.net_of_withholding.prefixes", []))
        )
        meta = propagate_hedge_flags(meta, [s for s, m in meta.items() if m.hedged])

        # The candidate is not a member of the universe; it existed to be
        # spliced. Dropping it here keeps it out of the estimation universe and
        # off every downstream report.
        keep = [c for c in combined.columns if c in universe]
        dropped = sorted(set(combined.columns) - set(keep))
        combined = combined[keep]
        meta = {k: v for k, v in meta.items() if k in keep}

        # The holdout, cut before returns are computed so that no return spans
        # the boundary. There is no bypass; this removes rows, it does not serve
        # them.
        start = holdout_start(params)
        combined = combined.loc[combined.index < start]

        returns = returns_from_prior_observation(combined)

        panel = ReturnPanel(
            levels=combined,
            returns=returns,
            meta=meta,
            splices=records,
            snapshot_id=snapshot_id,
            source=self.source,
        )
        enforce_holdout(panel.levels, params, what="bloomberg load_returns levels")
        enforce_holdout(panel.returns, params, what="bloomberg load_returns returns")

        self.report = {
            "n_series": len(keep),
            "dropped_after_splice": dropped,
            "splices_applied": [r.as_row() for r in records],
            "splices_skipped": skipped,
            "splice_sources_not_in_candidates": missing_sources,
            "retiered_by_splice": retiered,
            "first_date": str(combined.index.min().date()) if len(combined) else None,
            "last_date": str(combined.index.max().date()) if len(combined) else None,
            "n_rows": int(len(combined)),
            "rows_before_business_day_filter": int(len(before_truncation)),
            "tiers": pd.Series([m.tier for m in meta.values()]).value_counts().to_dict(),
            "hedged": sorted(s for s, m in meta.items() if m.hedged),
            "net_of_withholding": sorted(s for s, m in meta.items() if not m.gross),
            "region_source": "Section (conservative placeholder; see build_series_meta)",
        }
        return panel

    def _exusd_starts(self) -> dict[str, pd.Timestamp]:
        path = self.universe_dir / "bbg_exusd_bonds_coverage.csv"
        if not path.exists():
            return {}
        with path.open(newline="", encoding="utf-8-sig") as fh:
            return {
                r["ticker"]: pd.Timestamp(r["usd_series_daily_start"])
                for r in csv.DictReader(fh)
                if r.get("usd_series_daily_start")
            }

    @staticmethod
    def _skipped_splices(
        specs: list[dict], applied: list[SpliceRecord], columns
    ) -> list[dict[str, Any]]:
        """
        Every splice that did not happen, with the reason.

        Reported rather than silent: a splice that quietly did nothing is
        indistinguishable, downstream, from one that was never configured.
        """
        done = {(r.target, r.source) for r in applied}
        out = []
        for spec in specs:
            target, source = spec.get("target"), spec.get("source")
            if (target, source) in done:
                continue
            if not spec.get("active", False):
                reason = spec.get("blocked") or "inactive in params/data.yaml"
            elif not source:
                reason = "no source named"
            elif target not in columns:
                reason = f"target {target} not in the panel"
            elif source not in columns:
                reason = f"source {source} not in the panel"
            else:
                reason = "target had no missing observation the source could fill"
            out.append({"target": target, "source": source, "reason": reason})
        return out

    # -- analytics ------------------------------------------------------------

    def load_analytics(self, snapshot_id: str = "bloomberg-v1") -> AnalyticsPanel:
        """
        Index OAS, yield-to-worst and effective duration, one frame per field.

        Each metric is truncated at ITS OWN true daily start, not at the return
        series'. They differ, often by years: `LT01TRUU` has yield-to-worst daily
        from 1997-06-02, effective duration from 1997-08-01, and OAS only from
        2002-10-01. Truncating all three at the return series' start would admit
        five years of month-end OAS into a daily panel.

        OAS is left in the unit Bloomberg returns it in, which is PERCENT and not
        basis points despite the field documentation -- `LUACTRUU` reads 0.7918
        against a quoted 80bp. Converting here would hide the discrepancy; the
        unit is recorded on the panel instead, and whatever consumes it converts
        knowingly.
        """
        params = self.params
        markers = list(params.get("data.calendar.missing_markers", []))

        raw, header = self._read_role("analytics")
        index_map = read_index_map(
            self._path(self._entry("index_map")), self._entry("index_map")["sheet"]
        )
        analytics_rows = index_map[
            index_map["section"].astype(str).str.startswith(ANALYTICS_SECTION_PREFIX)
        ]
        # Ticker alone is not unique here -- each TR index appears once per
        # metric -- so the key is the full Bloomberg ticker plus the field.
        starts: dict[tuple[str, str], pd.Timestamp] = {}
        for _, row in analytics_rows.iterrows():
            full = row.get("full_ticker") or row.get("ticker")
            field = row.get("field")
            when = row.get("first_daily")
            if full and field and when is not None and not pd.isna(when):
                starts[(str(full), str(field))] = pd.Timestamp(when)

        tickers, fields = header[0][1:], header[1][1:]
        drop_treasury_oas = bool(params.get("data.analytics.drop_oas_on_treasury_buckets", True))
        treasury = self._treasury_tickers(index_map)

        by_field: dict[str, dict[str, pd.Series]] = {}
        meta: dict[str, SeriesMeta] = {}
        dropped: list[str] = []
        missing_start: list[str] = []

        raw = to_missing(raw, markers)
        raw = filter_business_days(raw)

        for i, (full_ticker, field) in enumerate(zip(tickers, fields, strict=False)):
            if not full_ticker or not field:
                continue
            ticker = full_ticker.split()[0]
            if drop_treasury_oas and field == "INDEX_OAS_TSY" and ticker in treasury:
                # Zero by construction on a Treasury index, and Bloomberg returns
                # a small negative number rather than zero. SUBSTRATE section 5.3
                # drops it; the yield-to-worst companion is the usable series.
                dropped.append(f"{ticker}|{field}")
                continue
            start = starts.get((full_ticker, field))
            if start is None:
                missing_start.append(f"{full_ticker}|{field}")
                continue
            column = raw.iloc[:, i].copy()
            column[column.index < start] = pd.NA
            by_field.setdefault(field, {})[ticker] = pd.to_numeric(column, errors="coerce")
            meta.setdefault(
                ticker,
                SeriesMeta(
                    series_id=ticker,
                    true_daily_start=start,
                    tier=_tier_from_start(start, params),  # type: ignore[arg-type]
                    section="17. Analytics",
                    region="17. Analytics",
                ),
            )
            if start < meta[ticker].true_daily_start:
                meta[ticker] = replace(meta[ticker], true_daily_start=start)

        cut = holdout_start(params)
        frames = {
            field: pd.DataFrame(cols).loc[lambda f: f.index < cut]
            for field, cols in by_field.items()
        }
        for frame in frames.values():
            enforce_holdout(frame, params, what="bloomberg load_analytics")

        self.report.setdefault("analytics", {})
        self.report["analytics"] = {
            "fields": sorted(frames),
            "n_series_per_field": {k: int(v.shape[1]) for k, v in frames.items()},
            "dropped_treasury_oas": sorted(dropped),
            "no_daily_start_in_index_map": sorted(missing_start),
            "oas_unit": "percent (multiply by 100 for basis points)",
        }
        return AnalyticsPanel(fields=frames, meta=meta, snapshot_id=snapshot_id, source=self.source)

    @staticmethod
    def _treasury_tickers(index_map: pd.DataFrame) -> set[str]:
        """Tickers in the Treasury maturity-bucket and inflation-linked sections."""
        mask = (
            index_map["section"]
            .astype(str)
            .str.startswith(("2. US Treasury Maturity Buckets", "1. Risk-Free / Cash"))
        )
        return set(index_map.loc[mask, "ticker"].astype(str))

    # -- benchmark ------------------------------------------------------------

    def load_benchmark(self, snapshot_id: str = "bloomberg-v1") -> ReturnPanel:
        """
        The 50/50 benchmark legs, as their own panel.

        `NDUEACWF` is daily from its 1998-12-31 inception; `LEGATRUU` starts in
        1990 but is MONTH-END ONLY until 1998-12-31, with 109 sparse-era
        observations. Those are truncated like any other pre-daily history.

        SUBSTRATE section 5.5 extends the pair before 1999 with `MXWO` and
        `SBWGU`. That extension is not applied here: `DEV_START` is 2001-01-05,
        so the core pair covers the whole development window and the blend would
        be dead history built from a different exposure -- sovereign-only bonds
        and developed-only equity, gross of dividend tax rather than net. The
        proxies are loaded and flagged so the blend can be built deliberately if
        the window ever moves, which is the point at which it needs a decision.
        """
        params = self.params
        raw, header = self._read_role("benchmark")
        cols = _series_columns(header)
        wanted = {t: i for t, i in cols.items() if t in BENCHMARK_CORE + BENCHMARK_PROXIES}
        levels = _named_frame(raw, wanted)
        levels = to_missing(levels, list(params.get("data.calendar.missing_markers", [])))
        levels = filter_business_days(levels)

        index_map = read_index_map(
            self._path(self._entry("index_map")), self._entry("index_map")["sheet"]
        )
        rows = {str(r["ticker"]): r for _, r in index_map.iterrows()}
        meta = {}
        for ticker in levels.columns:
            row = rows.get(ticker, {})
            start = row.get("first_daily")
            if start is None or pd.isna(start):
                raise InvariantViolation(
                    f"benchmark leg {ticker} has no true daily start in the Index Map"
                )
            meta[ticker] = SeriesMeta(
                series_id=ticker,
                true_daily_start=pd.Timestamp(start),
                tier="backbone",
                gross=ticker not in ("NDUEACWF",),
                section="18. Benchmark",
                cost_bucket="low",
                region="18. Benchmark",
            )
        levels = truncate_at_daily_start(levels, meta)
        levels = levels.loc[levels.index < holdout_start(params)]

        panel = ReturnPanel(
            levels=levels,
            returns=returns_from_prior_observation(levels),
            meta=meta,
            snapshot_id=snapshot_id,
            source=self.source,
        )
        enforce_holdout(panel.returns, params, what="bloomberg load_benchmark")
        return panel

    def load_macro(self, snapshot_id: str = "bloomberg-v1") -> VintagePanel:
        raise LoaderNotImplemented(
            "Bloomberg is not a point-in-time macro source; vintages come from JPMaQS"
        )
