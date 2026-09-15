"""
A workbook shaped like the vendor pull, with planted properties and no vendor data.

The real workbook is 71 MB of licensed Bloomberg data that stays on the owner's
machine, so the loader cannot be tested against it in CI or by anyone without
their own entitlement. This builds a small one with the same sheet names, the
same header-row structure and the same pathologies -- month-end history before a
daily era, `#N/A` for non-trading days, a replacement series on a different level
scale, per-metric analytics starts, observations past the holdout -- so that
every invariant has something real to catch.

The planted properties are asserted in `tests/test_bloomberg_loader.py`. If this
file and that one ever disagree, the fixture is wrong: the fixture describes what
the loader must survive, not what it currently does.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import openpyxl

NA = "#N/A"

# --- the planted panel --------------------------------------------------------

START = dt.date(2000, 1, 1)
END = dt.date(2021, 6, 30)  # deliberately past HOLDOUT_START (2020-01-01)

# ticker -> (section, first daily date, frequency flag, base level, sparse era)
SERIES = {
    # daily from inception, backbone
    "SPXT": ("6. Equity Regions - US", dt.date(2000, 1, 3), "Daily from inception", 1000.0, 0),
    # MONTH-END until 2003, then daily. The trap invariant 2 exists for.
    "LUACTRUU": (
        "5. Credit",
        dt.date(2003, 1, 1),
        "MONTHLY THEN DAILY - daily from 2003-01-01",
        1500.0,
        36,
    ),
    # the splice target: short daily history, large level scale
    "LT13TRUU": (
        "2. US Treasury Maturity Buckets",
        dt.date(2010, 1, 4),
        "MONTHLY THEN DAILY - daily from 2010-01-04",
        1800.0,
        120,
    ),
    # net of withholding (NDDU prefix), daily from inception
    "NDDUJN": (
        "7. Equity Regions - Developed ex-US",
        dt.date(2000, 1, 3),
        "Daily from inception",
        900.0,
        0,
    ),
    # already USD-hedged inside the base tab
    "H09122US": (
        "3. International Government Bonds",
        dt.date(2005, 6, 1),
        "MONTHLY THEN DAILY - daily from 2005-06-01",
        1200.0,
        64,
    ),
    # price index masquerading in a total-return panel
    "SPBDALB": ("5. Credit", dt.date(2007, 4, 2), "MONTHLY THEN DAILY - daily from 2007-04-02", 95.0, 87),
}

# the replacement candidate: much longer daily history, unrelated level scale
CANDIDATE = ("G3OC", "16. Replacement Candidate (separate tab)", dt.date(2001, 1, 2), 240.0)

BENCHMARKS = {
    "LEGATRUU": ("18. Benchmark (separate tab)", dt.date(2000, 1, 3), 250.0),
    "NDUEACWF": ("18. Benchmark (separate tab)", dt.date(2000, 1, 3), 180.0),
    "SBWGU": ("18. Benchmark (separate tab)", dt.date(2000, 1, 3), 400.0),
    "MXWO": ("18. Benchmark (separate tab)", dt.date(2000, 1, 3), 1100.0),
}

# analytics: (full ticker, field, metric, group, first daily date)
ANALYTICS = [
    ("LUACTRUU Index", "INDEX_OAS_TSY", "OAS to Treasury (%) x100 for bps", "1. Path1 analytics on TR ticker", dt.date(2004, 10, 1)),
    ("LUACTRUU Index", "INDEX_YIELD_TO_WORST", "Yield to worst (%)", "1. Path1 analytics on TR ticker", dt.date(2001, 6, 4)),
    ("LUACTRUU Index", "INDEX_OAD_TSY", "Effective duration (yrs)", "1. Path1 analytics on TR ticker", dt.date(2001, 8, 1)),
    # OAS on a Treasury bucket: zero by construction, dropped by params
    ("LT13TRUU Index", "INDEX_OAS_TSY", "OAS to Treasury (%) x100 for bps", "1. Path1 analytics on TR ticker", dt.date(2005, 1, 3)),
    ("LT13TRUU Index", "INDEX_YIELD_TO_WORST", "Yield to worst (%)", "1. Path1 analytics on TR ticker", dt.date(2002, 1, 2)),
    ("MOVE Index", "PX_LAST", "Level", "3. Vol / financial conditions", dt.date(2000, 1, 3)),
]

EXUSD = {
    "LET1TREU": (dt.date(2000, 1, 3), 130.0, "EUR"),
    "LG38TRUU": (dt.date(2001, 1, 2), 175.0, "USD"),
}


def _calendar(start: dt.date, end: dt.date) -> list[dt.date]:
    out, day = [], start
    while day <= end:
        out.append(day)
        day += dt.timedelta(days=1)
    return out


def _level(base: float, i: int) -> float:
    """A smooth, strictly positive path. Deterministic, no randomness, no vendor values."""
    return round(base * (1.0 + 0.0002 * i + 0.01 * ((i % 17) / 17.0)), 6)


def _month_ends(days: list[dt.date], before: dt.date) -> set[dt.date]:
    ends = set()
    for a, b in zip(days, days[1:], strict=False):
        if a < before and a.month != b.month:
            ends.add(a)
    return ends


def _observed(day: dt.date, first_daily: dt.date, sparse: set[dt.date]) -> bool:
    if day >= first_daily:
        return day.weekday() < 5
    return day in sparse


def build(target_dir: Path) -> dict[str, Path]:
    """
    Write the fixture workbook, the ex-USD csv and the universe tables.

    Returns the paths, so a test can point a BloombergLoader at a tmp_path and
    get a panel without touching `data/raw/`.
    """
    target = Path(target_dir)
    raw = target / "data" / "raw" / "bloomberg"
    raw.mkdir(parents=True, exist_ok=True)
    universe = target / "data" / "universe"
    universe.mkdir(parents=True, exist_ok=True)

    days = _calendar(START, END)
    wb = openpyxl.Workbook()

    # --- Index Map -----------------------------------------------------------
    im = wb.active
    im.title = "Index Map"
    im.append(
        [
            "Ticker", "Bloomberg Security Name", "Section", "Tier", "Splice Flag (Y/N)",
            "Splice Date", "Notes", "First data date", "Frequency flag", "First daily year",
            "First daily date", "Sparse-era obs (pre-daily)", "Peak obs/yr", "First daily month",
            "Currency hedge", "Hedge pair (counterpart)", "Hedge pair note",
            "Long name (Bloomberg LONG_COMP_NAME)", "Quote ccy", "Replacement candidate",
            "Replacement note", None, "Source-declared USD-hedged tickers (from user list)",
            "Analytics metric", "Bloomberg field", "Full Bloomberg ticker",
        ]
    )

    def imrow(ticker, section, first_daily, flag, sparse, ccy="USD", metric=None, field=None, full=None):
        row = [None] * 26
        row[0] = ticker
        row[1] = f"{ticker} name"
        row[2] = section
        row[7] = str(START)
        row[8] = flag
        row[9] = str(first_daily.year)
        row[10] = str(first_daily)
        row[11] = str(sparse)
        row[12] = "261"
        row[17] = f"{ticker} long name"
        row[18] = ccy
        row[23] = metric
        row[24] = field
        row[25] = full
        im.append(row)

    for ticker, (section, first_daily, flag, _base, sparse) in SERIES.items():
        imrow(ticker, section, first_daily, flag, sparse)
    imrow(CANDIDATE[0], CANDIDATE[1], CANDIDATE[2], "MONTHLY THEN DAILY - daily from 2001-01-02", 24)
    for ticker, (section, first_daily, _b) in BENCHMARKS.items():
        imrow(ticker, section, first_daily, "Daily from inception", 0)
    for full, field, metric, group, first_daily in ANALYTICS:
        imrow(
            full.split()[0], f"17. Analytics / non-investable ({group.split('. ')[1]})",
            first_daily, "Daily from inception", 0, metric=metric, field=field, full=full,
        )

    # --- Loader Notes --------------------------------------------------------
    ln = wb.create_sheet("Loader Notes")
    ln.append(["Loader Notes - TR Levels", None])
    ln.append(["Field", "TOT_RETURN_INDEX_GROSS_DVDS"])
    ln.append(["Overrides", "Per=D, Fill=NA, Days=A"])

    # --- TR Levels -----------------------------------------------------------
    tr = wb.create_sheet("TR Levels")
    tickers = list(SERIES)
    sparse_sets = {
        t: _month_ends(days, SERIES[t][1]) if SERIES[t][4] else set() for t in tickers
    }
    tr.append(["Date", *tickers, None, "FLAG", "FLAG", "FLAG"])
    tr.append(["Security name", *[f"{t} name" for t in tickers], None, None, None, None])
    tr.append(["Tier", *[None] * len(tickers), None, None, None, None])
    tr.append(["Splice flag", *[None] * len(tickers), None, None, None, None])
    for i, day in enumerate(days):
        row = [day]
        for t in tickers:
            _s, first_daily, _f, base, _sp = SERIES[t]
            row.append(_level(base, i) if _observed(day, first_daily, sparse_sets[t]) else NA)
        row += [None, 1 if day.weekday() < 5 else 0, 0, 0]
        tr.append(row)

    # --- TR Levels Candidates ------------------------------------------------
    cand = wb.create_sheet("TR Levels Candidates")
    c_ticker, _c_section, c_first, c_base = CANDIDATE
    c_sparse = _month_ends(days, c_first)
    cand.append(["Date", c_ticker, None, "Metadata probe"])
    cand.append(["Index name", f"{c_ticker} long name", None, None])
    cand.append(["Purpose", "Candidate with longer daily history", None, None])
    cand.append(["Replaces / compares to", "LT13TRUU", None, None])
    for i, day in enumerate(days):
        observed = _observed(day, c_first, c_sparse)
        cand.append([day, _level(c_base, i) if observed else NA, None, None])

    # --- TR Levels Hedged ----------------------------------------------------
    hedged = wb.create_sheet("TR Levels Hedged")
    hedged.append(["Date", "LGTRTRUH"])
    hedged.append(["Index name", "Global Agg Treasuries hedged"])
    hedged.append(["Hedge axis", "Global ex-US Govt"])
    hedged.append(["Unhedged counterpart", "none in universe"])
    for i, day in enumerate(days):
        hedged.append([day, _level(500.0, i) if day.weekday() < 5 else NA])

    # --- TR Analytics --------------------------------------------------------
    an = wb.create_sheet("TR Analytics")
    an.append(["Date", *[a[0] for a in ANALYTICS]])
    an.append(["Field", *[a[1] for a in ANALYTICS]])
    an.append(["Metric", *[a[2] for a in ANALYTICS]])
    an.append(["Group", *[a[3] for a in ANALYTICS]])
    for i, day in enumerate(days):
        row = [day]
        for _full, _field, _metric, _group, first_daily in ANALYTICS:
            row.append(round(1.0 + 0.001 * i, 6) if _observed(day, first_daily, set()) else NA)
        an.append(row)

    # --- TR Benchmarks -------------------------------------------------------
    bm = wb.create_sheet("TR Benchmarks")
    bnames = list(BENCHMARKS)
    bm.append(["Date", *bnames, "FLAG", "FLAG"])
    bm.append(["Security name", *[f"{b} name" for b in bnames], None, None])
    bm.append(["Long name (LONG_COMP_NAME)", *[f"{b} long" for b in bnames], None, None])
    bm.append(["Role", *["Benchmark" for _ in bnames], None, None])
    for i, day in enumerate(days):
        row = [day]
        for b in bnames:
            _sec, first_daily, base = BENCHMARKS[b]
            row.append(_level(base, i) if _observed(day, first_daily, set()) else NA)
        row += [1 if day.weekday() < 5 else 0, 0]
        bm.append(row)

    workbook = raw / "bbg_data_values_only.xlsx"
    wb.save(workbook)

    # --- ex-USD csv ----------------------------------------------------------
    csv_path = raw / "bbg_exusd_bonds_usd_unhedged.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        header = [""]
        for t, (_fd, _b, ccy) in EXUSD.items():
            header += [f"{t}_local_{ccy}", f"{t}_USD_unhedged", f"{t}_fx_USDper{ccy}"]
        w.writerow(header)
        for i, day in enumerate(days):
            if day.weekday() >= 5:
                continue
            row = [day.isoformat()]
            for _t, (first_daily, base, _ccy) in EXUSD.items():
                if day < first_daily or i % 61 == 0:  # planted FX-fix gaps, left as gaps
                    row += ["", "", ""]
                else:
                    row += [_level(base, i), _level(base * 1.1, i), 1.1]
            w.writerow(row)

    _write_universe_tables(universe, workbook.name, csv_path.name)
    return {"workbook": workbook, "exusd": csv_path, "universe": universe, "root": target}


def _write_universe_tables(universe: Path, workbook_name: str, exusd_name: str) -> None:
    """The manifest, the investable universe and the ex-USD coverage table."""
    with (universe / "raw_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["file", "sheet", "layout", "field", "currency", "role", "header_rows", "first_data_row"]
        )
        rows = [
            (workbook_name, "Index Map", "table", "n/a", "n/a", "index_map", 1, 2),
            (workbook_name, "TR Levels", "wide_single_date", "TOT_RETURN_INDEX_GROSS_DVDS", "USD", "returns", 4, 5),
            (workbook_name, "TR Levels Hedged", "wide_single_date", "TOT_RETURN_INDEX_GROSS_DVDS", "USD_hedged", "returns_hedged", 4, 5),
            (workbook_name, "TR Levels Candidates", "wide_single_date", "TOT_RETURN_INDEX_GROSS_DVDS", "USD", "returns_substitutes", 4, 5),
            (workbook_name, "TR Benchmarks", "wide_single_date", "TOT_RETURN_INDEX_GROSS_DVDS", "USD", "benchmark", 4, 5),
            (workbook_name, "TR Analytics", "wide_ticker_field_header", "various", "n/a", "analytics", 4, 5),
            (exusd_name, "", "paired_date_value", "PX_LAST", "local_or_USD", "returns_ex_usd", 1, 2),
        ]
        w.writerows(rows)

    hedged = {"H09122US"}
    not_investable = hedged | {"SPBDALB"}
    with (universe / "investable_universe.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "ticker", "name", "section", "first_daily", "tier", "hedged",
                "investable", "cost_bucket", "reporting_class", "source_file",
            ],
        )
        w.writeheader()
        for ticker, (section, first_daily, _flag, _base, _sparse) in SERIES.items():
            tier = (
                "backbone" if first_daily.year <= 2001
                else "second" if first_daily.year <= 2009
                else "tradable-only"
            )
            w.writerow(
                {
                    "ticker": ticker, "name": f"{ticker} name", "section": section,
                    "first_daily": first_daily, "tier": tier,
                    "hedged": ticker in hedged, "investable": ticker not in not_investable,
                    "cost_bucket": "mid", "reporting_class": "Test",
                    "source_file": "fixture",
                }
            )
        for ticker, (first_daily, _base, _ccy) in EXUSD.items():
            w.writerow(
                {
                    "ticker": ticker, "name": f"{ticker} name",
                    "section": "3. International Government Bonds",
                    "first_daily": first_daily, "tier": "", "hedged": False,
                    "investable": True, "cost_bucket": "mid",
                    "reporting_class": "Ex-USD Bonds", "source_file": "fixture",
                }
            )

    with (universe / "bbg_exusd_bonds_coverage.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "name", "local_ccy", "usd_series_daily_start", "construction"])
        for ticker, (first_daily, _base, ccy) in EXUSD.items():
            w.writerow([ticker, f"{ticker} name", ccy, first_daily, "fixture"])


if __name__ == "__main__":  # pragma: no cover - convenience
    import sys

    built = build(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    for key, value in built.items():
        print(f"{key:<10} {value}")
