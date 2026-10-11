"""
The report of a characteristics store (HANDOFF task 51): counts, dates and aggregates only.
No instrument-week value is printed; the per-instrument rows of the estimated-against-measured
table are medians over weeks, which is the table OWNER-QUEUE L27 asks for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.characteristics.store import Store

FIRST_LINE = (
    "Built from `decisions/0049`. It chooses nothing about the matrix's columns (OWNER-QUEUE L27)."
)
BOND_FACTORS = ("real_yield", "inflation", "credit")


def _f(x, nd=3) -> str:
    return "-" if x is None or (isinstance(x, float) and x != x) else f"{x:.{nd}f}"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
        *("| " + " | ".join(r) + " |" for r in rows),
    ]


BOND_CLASSES = (
    "Treasuries",
    "Long Treasuries",
    "TIPS",
    "MBS",
    "IG Corporates",
    "HY Corporates",
    "EM Sovereign Bonds",
    "EM Corporate Bonds",
    "Ex-USD Bonds",
)
PERIODS = (("2002-08", 2002, 2008), ("2009-15", 2009, 2015), ("2016-19", 2016, 2019))
SPREAD_REFERENCE = "LUACTRUU"
# Duration times spread is meaningless where the spread over Treasuries is near zero: the ratio
# divides by it (task 52 printed -39 and 15). Left out by class, and four government ex-USD indices.
DTS_EXCLUDED_CLASSES = ("Treasuries", "Long Treasuries", "TIPS")
DTS_EXCLUDED_INSTRUMENTS = ("I02513EU", "I02913JP", "I12823GB", "LET1TREU")


def bond_frame(store: Store) -> pd.DataFrame:
    """
    One row per instrument-week of the estimated bond-class instruments: the three bond loadings
    with `oad` and `oas` beside them (NaN where not measured). Instruments in `BOND_CLASSES` only.
    """
    inst = store.frames["instruments"]
    ids = inst.loc[inst["estimated"] & inst["class"].isin(BOND_CLASSES), "instrument"]
    load = store.frames["loadings"]
    load = load[load["instrument"].isin(set(ids)) & load["factor"].isin(BOND_FACTORS)]
    wide = load.pivot_table(index=["instrument", "date"], columns="factor", values="loading")
    meas = store.frames["measured"].set_index(["instrument", "date"])[["oad", "oas"]]
    out = wide.join(meas, how="left").reset_index()
    klass = dict(zip(inst["instrument"], inst["class"], strict=True))
    out["class"] = out["instrument"].map(klass)
    return out


def _pctl(x: pd.Series, q: float) -> float:
    return float(np.nanpercentile(x.to_numpy(), q)) if len(x) else float("nan")


def estimated_against_measured(store: Store) -> pd.DataFrame:
    """
    One row per estimated bond-class instrument. Medians and their ratio are over the weeks with
    both a loading and a measured duration; the weekly ratio `loading_t / -oad_t` is summarised
    by its median and 10th and 90th percentiles for real yield and inflation. Instruments with
    no measured duration have NaN there.
    """
    df = bond_frame(store)
    rows = []
    for sid, g in df.groupby("instrument", sort=False):
        both = g[g["oad"].notna() & (g["oad"] > 0)]
        row = {
            "instrument": sid,
            "reporting_class": g["class"].iloc[0],
            "weeks": int(len(g)),
            "weeks_measured": int(len(both)),
        }
        if len(both):
            minus_oad = -float(both["oad"].median())
            row["minus_oad"] = minus_oad
            for fac in BOND_FACTORS:
                v = float(both[fac].median())
                row[fac] = v
                row[f"{fac}_ratio"] = v / minus_oad
            for fac in ("real_yield", "inflation"):
                w = both[fac] / -both["oad"]
                row[f"{fac}_weekly_median"] = float(w.median())
                row[f"{fac}_weekly_p10"] = _pctl(w, 10)
                row[f"{fac}_weekly_p90"] = _pctl(w, 90)
        rows.append(row)
    return pd.DataFrame(rows)


def ratio_by_period(store: Store) -> pd.DataFrame:
    """Median weekly ratio of real yield and of inflation loading to -OAD, per period."""
    df = bond_frame(store)
    df = df[df["oad"].notna() & (df["oad"] > 0)]
    rows = []
    for sid, g in df.groupby("instrument", sort=False):
        row = {"instrument": sid, "reporting_class": g["class"].iloc[0]}
        for fac in ("real_yield", "inflation"):
            w = g[fac] / -g["oad"]
            for label, lo, hi in PERIODS:
                sel = w[(g["date"].dt.year >= lo) & (g["date"].dt.year <= hi)]
                row[f"{fac}_{label}"] = float(sel.median()) if len(sel) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def measured_coverage(store: Store) -> pd.DataFrame:
    """
    Per estimated bond-class instrument: the first measured week; the weeks with a loading and no
    measured duration; and the empty weeks inside the measured span, counted on the weekly
    calendar the store's loadings use.
    """
    df = bond_frame(store)
    calendar = pd.DatetimeIndex(sorted(store.frames["loadings"]["date"].unique()))
    rows = []
    for sid, g in df.groupby("instrument", sort=False):
        measured = g.loc[g["oad"].notna(), "date"]
        row = {
            "instrument": sid,
            "reporting_class": g["class"].iloc[0],
            "first_measured": measured.min() if len(measured) else pd.NaT,
            "loading_no_duration": int(g["oad"].isna().sum()),
        }
        if len(measured):
            span = calendar[(calendar >= measured.min()) & (calendar <= measured.max())]
            row["empty_inside"] = int(len(span) - len(set(measured) & set(span)))
        rows.append(row)
    return pd.DataFrame(rows)


def duration_times_spread(store: Store) -> pd.DataFrame:
    """
    For each instrument with an `INDEX_OAS_TSY`: the weekly median of the credit loading over
    `-OAD * OAS / OAS of LUACTRUU`, over the weeks all of it is observed.
    """
    df = bond_frame(store)
    ref = df.loc[df["instrument"] == SPREAD_REFERENCE].set_index("date")["oas"]
    rows = []
    for sid, g in df.groupby("instrument", sort=False):
        if sid in DTS_EXCLUDED_INSTRUMENTS or g["class"].iloc[0] in DTS_EXCLUDED_CLASSES:
            continue
        g = g.assign(ref=g["date"].map(ref))
        ok = g[(g["oad"] > 0) & (g["oas"] > 0) & (g["ref"] > 0)]
        if not len(ok):
            continue
        ratio = ok["credit"] / (-ok["oad"] * ok["oas"] / ok["ref"])
        rows.append(
            {
                "instrument": sid,
                "reporting_class": g["class"].iloc[0],
                "weeks": int(len(ok)),
                "credit_over_duration_times_spread": float(ratio.median()),
            }
        )
    return pd.DataFrame(rows)


def bond_sections(store: Store) -> list[str]:
    table = estimated_against_measured(store)
    n_meas = int((table["weeks_measured"] > 0).sum())
    lines = [
        "",
        f"## Estimated against measured, {n_meas} of {len(table)} estimated bond-class "
        "instruments have a measured duration",
        "",
        "Medians and their ratio are over the weeks with both a loading and a measured "
        "`INDEX_OAD_TSY`; `-OAD` is minus its median over those weeks. A ratio of 1 means the "
        "loading equals minus the measured duration. *weekly* is the median of the weekly "
        "`loading / -OAD` with its 10th and 90th percentiles. A dash is an instrument with no "
        "measured duration. Not merged: the two stay separate in the store (`decisions/0015`).",
        "",
    ]

    def band(r, fac):
        m = r.get(f"{fac}_weekly_median")
        if m is None or m != m:
            return "-"
        return f"{m:.2f} [{r[f'{fac}_weekly_p10']:.2f}, {r[f'{fac}_weekly_p90']:.2f}]"

    rows = []
    for _, r in table.sort_values(["reporting_class", "instrument"]).iterrows():
        meas = r["weeks_measured"] > 0
        rows.append(
            [
                r["instrument"],
                r["reporting_class"],
                str(r["weeks"]),
                str(r["weeks_measured"]),
                _f(r.get("real_yield")) if meas else "-",
                _f(r.get("inflation")) if meas else "-",
                _f(r.get("credit")) if meas else "-",
                _f(r.get("minus_oad"), 2) if meas else "-",
                _f(r.get("real_yield_ratio"), 2) if meas else "-",
                _f(r.get("inflation_ratio"), 2) if meas else "-",
                _f(r.get("credit_ratio"), 2) if meas else "-",
                band(r, "real_yield") if meas else "-",
                band(r, "inflation") if meas else "-",
            ]
        )
    lines += _table(
        [
            "instrument",
            "class",
            "weeks",
            "weeks measured",
            "real yield",
            "inflation",
            "credit",
            "-OAD",
            "ratio real yield",
            "ratio inflation",
            "ratio credit",
            "weekly real yield",
            "weekly inflation",
        ],
        rows,
    )
    per = ratio_by_period(store)
    lines += [
        "",
        "## By period, median weekly ratio of the loading to -OAD",
        "",
        *_table(
            [
                "instrument",
                "class",
                *(f"real yield {p[0]}" for p in PERIODS),
                *(f"inflation {p[0]}" for p in PERIODS),
            ],
            [
                [
                    r["instrument"],
                    r["reporting_class"],
                    *(_f(r[f"real_yield_{p[0]}"], 2) for p in PERIODS),
                    *(_f(r[f"inflation_{p[0]}"], 2) for p in PERIODS),
                ]
                for _, r in per.sort_values(["reporting_class", "instrument"]).iterrows()
            ],
        ),
    ]
    cov = measured_coverage(store)
    lines += [
        "",
        "## Measured coverage",
        "",
        "First week with a measured duration; weeks with a loading and no measured duration; "
        "empty weeks inside the measured span (a week between the first and last measured week "
        "with no observation).",
        "",
        *_table(
            ["instrument", "class", "first measured week", "loading, no duration", "empty inside"],
            [
                [
                    r["instrument"],
                    r["reporting_class"],
                    "-" if pd.isna(r["first_measured"]) else str(r["first_measured"].date()),
                    str(r["loading_no_duration"]),
                    "-" if pd.isna(r.get("empty_inside")) else str(int(r["empty_inside"])),
                ]
                for _, r in cov.sort_values(["reporting_class", "instrument"]).iterrows()
            ],
        ),
    ]
    dts = duration_times_spread(store)
    lines += [
        "",
        "## Duration times spread",
        "",
        "For each instrument with an `INDEX_OAS_TSY`: the median over weeks of the credit loading "
        f"over `-OAD x OAS / OAS of {SPREAD_REFERENCE}`. 1 means the credit loading is duration "
        "times spread, scaled to the reference. **Left out:** the "
        f"{', '.join(DTS_EXCLUDED_CLASSES)} classes and the government ex-USD indices "
        f"{', '.join(f'`{t}`' for t in DTS_EXCLUDED_INSTRUMENTS)}. Their spread over Treasuries "
        "is near zero, so the ratio divides by almost nothing and means nothing.",
        "",
        *_table(
            ["instrument", "class", "weeks", "credit loading over duration x spread"],
            [
                [
                    r["instrument"],
                    r["reporting_class"],
                    str(r["weeks"]),
                    _f(r["credit_over_duration_times_spread"], 2),
                ]
                for _, r in dts.sort_values(["reporting_class", "instrument"]).iterrows()
            ],
        ),
    ]
    return lines


def converted_rows(new: dict, old: dict, converted: dict[str, dict]) -> list[dict]:
    """
    Per series converted to dollars (decisions/0053): the median over weeks of its dollar
    loading and of its explained share in the earlier store and in this one.

    `new` and `old` are store frames; `converted` maps a ticker to `{"currency", "column",
    "n_dates_dropped"}`. A series absent from a store has NaN there.
    """

    def med(frames, sid, factor=None):
        if factor is None:
            g = frames["fit"]
            g = g[g["instrument"] == sid]["explained_share"]
        else:
            g = frames["loadings"]
            g = g[(g["instrument"] == sid) & (g["factor"] == factor)]["loading"]
        g = g.dropna()
        return float(g.median()) if len(g) else float("nan")

    rows = []
    for sid, c in sorted(converted.items()):
        load = new["loadings"]
        weeks = load[(load["instrument"] == sid) & (load["factor"] == "dollar")]["date"].nunique()
        rows.append(
            {
                "instrument": sid,
                "currency": c["currency"],
                "column": c["column"],
                "weeks": int(weeks),
                "dollar_before": med(old, sid, "dollar"),
                "share_before": med(old, sid),
                "dollar_after": med(new, sid, "dollar"),
                "share_after": med(new, sid),
                "fx_dates_dropped": int(c["n_dates_dropped"]),
            }
        )
    return rows


def converted_section(store: Store) -> list[str]:
    rows = store.manifest.get("converted_to_usd")
    if not rows:
        return []
    return [
        "",
        "## Converted to dollars (`decisions/0053`)",
        "",
        "Series delivered in their quote currency, converted in the loader with Bloomberg generic "
        f"spot on the same date. *before* is `{store.manifest.get('supersedes', '-')}`, *after* "
        "this store. Medians over weeks of the dollar loading and of the explained share. "
        "*FX dates dropped* are dates, from each series' true daily start to the holdout, with a "
        "local level and no rate: they have no dollar level and nothing is carried.",
        "",
        *_table(
            [
                "instrument",
                "currency",
                "FX column",
                "weeks",
                "dollar loading before",
                "dollar loading after",
                "explained share before",
                "explained share after",
                "FX dates dropped",
            ],
            [
                [
                    r["instrument"],
                    r["currency"],
                    r["column"],
                    str(r["weeks"]),
                    _f(r["dollar_before"], 2),
                    _f(r["dollar_after"], 2),
                    _f(r["share_before"], 2),
                    _f(r["share_after"], 2),
                    str(r["fx_dates_dropped"]),
                ]
                for r in rows
            ],
        ),
    ]


def build_report(store: Store, checks: dict[str, str] | None = None) -> str:
    m = store.manifest
    load, fit, inst = store.frames["loadings"], store.frames["fit"], store.frames["instruments"]
    est = inst[inst["estimated"]]
    lines = [
        FIRST_LINE,
        "",
        f"# Characteristics store `{store.store_id}`",
        "",
        f"- Estimator `{m['estimator']['name']}` ({m['estimator']['hypothesis']}): "
        f"c = {m['estimator']['huber_c']}, MAD scale, {m['estimator']['window_weeks']} weeks, "
        f"at least {m['estimator']['min_obs']} valid weeks, sandwich covariance, all six factors "
        f"in one regression, walk-forward. Factors: {', '.join(m['factors'])}.",
        f"- Dates: {m['first_date']} to {m['last_date']}; development window only.",
        f"- Instruments: {m['n_estimated']} estimated, {m['n_not_estimated']} not "
        f"({m['not_estimated_reason']}).",
        f"- Rows: {', '.join(f'{k} {v:,}' for k, v in m['row_counts'].items())}.",
        f"- Hashes: directory `{m['directory_hash'][:16]}`, params `{m['params_hash'][:16]}`, "
        f"weekly returns `{m['weekly_returns_hash'][:16]}`, factors `{m['factors_hash'][:16]}`. "
        f"Threads (OMP/OPENBLAS/MKL) "
        f"{'/'.join(str(v) for v in m['thread_setting'].values())}.",
        "",
        "## Instruments estimated, by reporting class",
        "",
        *_table(
            ["class", "instruments", "first week with loadings"],
            [
                [k, str(len(g)), str(pd.Timestamp(g["first_date"].min()).date())]
                for k, g in est.groupby("class")
            ],
        ),
        "",
        "## Explained share, by reporting class",
        "",
        "Out of sample: `1 - sum (r - p)^2 / sum r^2`, `p` this week's factors times last week's "
        "loadings, no intercept. *Full sample* is over every week an instrument has; *last week* "
        f"is the 156 weeks ending {m['last_date']} (instruments with a value there). Medians over "
        "instruments. It may be negative.",
        "",
    ]
    last = fit[fit["date"] == pd.Timestamp(m["last_date"])].set_index("instrument")[
        "explained_share"
    ]
    rows = []
    for k, g in est.groupby("class"):
        at_last = last.reindex(g["instrument"]).dropna()
        low = at_last.idxmin() if len(at_last) else None
        rows.append(
            [
                k,
                _f(float(np.nanmedian(g["explained_share_full"])))
                if g["explained_share_full"].notna().any()
                else "-",
                _f(float(at_last.median())) if len(at_last) else "-",
                str(len(at_last)),
                f"{low} {at_last.min():.3f}" if low is not None else "-",
                str(int((at_last < 0.5).sum())),
            ]
        )
    lines += _table(
        ["class", "full sample", "last week", "n at last week", "lowest at last week", "below 0.5"],
        rows,
    )
    lines += [
        "",
        "Commodities' share is an identity, not a finding: the commodities factor is that index "
        "less cash, so the regression recovers it exactly.",
    ]

    lines += [
        "",
        "## Standard error against loading",
        "",
        f"Median over instruments of `se / |loading|` at {m['last_date']}, by factor and class. "
        "Large where a class has little exposure to a factor.",
        "",
    ]
    at = load[load["date"] == pd.Timestamp(m["last_date"])].copy()
    at["ratio"] = at["se"] / at["loading"].abs()
    at = at.merge(inst[["instrument", "class"]], on="instrument")
    piv = at.pivot_table(index="class", columns="factor", values="ratio", aggfunc="median")
    factors = list(m["factors"])
    lines += _table(
        ["class", *factors],
        [
            [k, *(_f(float(piv.loc[k, f]), 2) if f in piv.columns else "-" for f in factors)]
            for k in piv.index
        ],
    )

    lines += converted_section(store)
    lines += bond_sections(store)
    if checks:
        lines += ["", "## Checks the build made on itself", ""]
        lines += [f"- {k}: {v}" for k, v in checks.items()]
    return "\n".join(lines) + "\n"
