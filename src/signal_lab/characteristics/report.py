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


def estimated_against_measured(store: Store) -> pd.DataFrame:
    """One row per instrument with a measured duration: median loadings, minus median OAD, ratios."""
    load, meas, inst = (
        store.frames["loadings"],
        store.frames["measured"],
        store.frames["instruments"],
    )
    klass = dict(zip(inst["instrument"], inst["class"], strict=True))
    wide = load[load["factor"].isin(BOND_FACTORS)].pivot_table(
        index=["instrument", "date"], columns="factor", values="loading"
    )
    rows = []
    for sid, m in meas.dropna(subset=["oad"]).groupby("instrument"):
        if sid not in wide.index.get_level_values(0):
            continue
        w = wide.loc[sid]
        oad = m.set_index("date")["oad"].reindex(w.index).dropna()
        if oad.empty:
            continue
        minus_oad = -float(oad.median())
        row = {"instrument": sid, "reporting_class": klass.get(sid, ""), "weeks": int(len(w))}
        for fac in BOND_FACTORS:
            v = float(w[fac].median())
            row[fac] = v
            row[f"{fac}_ratio"] = v / minus_oad if minus_oad != 0 else float("nan")
        row["minus_oad"] = minus_oad
        rows.append(row)
    return pd.DataFrame(rows)


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
        rows.append(
            [
                k,
                _f(float(np.nanmedian(g["explained_share_full"])))
                if g["explained_share_full"].notna().any()
                else "-",
                _f(float(at_last.median())) if len(at_last) else "-",
                str(len(at_last)),
            ]
        )
    lines += _table(["class", "full sample", "last week", "n at last week"], rows)

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

    table = estimated_against_measured(store)
    lines += [
        "",
        "## Estimated against measured, every bond index",
        "",
        "The estimated loadings are medians over the weeks an instrument has them; `-OAD` is "
        "minus the median measured `INDEX_OAD_TSY` over the same weeks. A ratio of 1 means the "
        "regression's loading equals minus the measured duration. Not merged: the two stay "
        "separate in the store (`decisions/0015`).",
        "",
    ]
    if table.empty:
        lines.append("No instrument has a measured duration in this store.")
    else:
        lines += _table(
            [
                "instrument",
                "class",
                "weeks",
                "real yield",
                "inflation",
                "credit",
                "-OAD",
                "ratio real yield",
                "ratio inflation",
                "ratio credit",
            ],
            [
                [
                    r.instrument,
                    r.reporting_class,
                    str(r.weeks),
                    _f(r.real_yield),
                    _f(r.inflation),
                    _f(r.credit),
                    _f(r.minus_oad, 2),
                    _f(r.real_yield_ratio, 2),
                    _f(r.inflation_ratio, 2),
                    _f(r.credit_ratio, 2),
                ]
                for r in table.sort_values(["reporting_class", "instrument"]).itertuples()
            ],
        )
    if checks:
        lines += ["", "## Checks the build made on itself", ""]
        lines += [f"- {k}: {v}" for k, v in checks.items()]
    return "\n".join(lines) + "\n"
