"""
Write the audit's outputs: the cell table, the required-IC table, the breadth
numbers, a markdown summary and a self-contained HTML page.

Under `results/audit/<run_id>/`, never in the results store (decisions/0023).
Every file carries the panel hash and the params hash so a table produced on
the synthetic snapshot cannot be mistaken for one produced on Bloomberg data.
The HTML uses no external resource: grey palette, one orange, nothing loaded.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from signal_lab.audit.breadth import Breadth
from signal_lab.audit.ladder import (
    FRICTIONLESS,
    empirical_breadth,
    ladder_breadth,
    required_ic,
    transfer_ratio,
)

ORANGE = "#FF6100"
GREY = ["#1C252E", "#455760", "#6B7A86", "#9AA5AE", "#C9D0D6", "#E9ECEF", "#F6F7F8"]


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if np.isnan(value):
            return "—"
        if np.isinf(value):
            return "∞"
        return f"{value:.{digits}f}"
    return str(value)


def _pivot(table: pd.DataFrame, tag: str, value: str = "net_ir") -> pd.DataFrame:
    sub = table[table["tag"] == tag]
    if sub.empty:
        return pd.DataFrame()
    return sub.pivot_table(index="ic", columns="horizon", values=value, aggfunc="mean")


def _pivot_range(table: pd.DataFrame, tag: str, value: str = "net_ir") -> pd.DataFrame:
    """Max minus min over seeds; NaN (printed "—") where only one seed ran."""
    sub = table[table["tag"] == tag]
    if sub.empty:
        return pd.DataFrame()
    lo = sub.pivot_table(index="ic", columns="horizon", values=value, aggfunc="min")
    hi = sub.pivot_table(index="ic", columns="horizon", values=value, aggfunc="max")
    n = sub.pivot_table(index="ic", columns="horizon", values=value, aggfunc="count")
    return (hi - lo).where(n > 1)


def _required(r: dict[str, Any]) -> str:
    """A required IC as the report prints it: a bound stays a bound."""
    shown = r.get("display")
    if isinstance(shown, str) and shown:
        return shown
    return _fmt(r.get("required_ic"), 3)


READING_THE_CHAIN = (
    "Implied IC is printed twice because its meaning changed (decisions/0033). At "
    "TC = 1 it is what every earlier audit printed, and assumes the long-only "
    "constraint, the caps and the shadow cost lose nothing. At the measured TC it "
    "prices them. Empirical breadth is read off the constrained ladder: net IR per "
    "unit IC divided by the measured TC, squared, so it is net of costs and blank "
    "where no TC was measured. The frictionless twin's breadth, its FLAM comparison "
    "and the base-over-frictionless ratio are not shown (decisions/0029 s1): they "
    "measure the covariance estimate rather than the constraints. The raw columns "
    "remain in `cells.csv` and `summary.json`."
)


def _stress_note(summary: dict[str, Any]) -> list[str]:
    used, asked = summary.get("stress_horizon"), summary.get("stress_horizon_requested")
    if asked is None or used == asked:
        return []
    return [
        f"_The stress horizon in params is {asked}w, which this grid did not run; "
        f"the tables below use {used}w and hold base cells only unless stress cells ran._",
        "",
    ]


COVARIANCE_NOTE = (
    "The frictionless twin is kept as a diagnostic of the covariance estimate "
    "(decisions/0029 s3). It inverts the same shrunk covariance the constrained book "
    "is built from with nothing holding the weights down, so a bias statistic above "
    "one is estimation error the long-only constraint was absorbing "
    "(Jagannathan and Ma, 2003), not a price of the constraints."
)

TC_NOTE = (
    "Transfer coefficient (decisions/0033, corrected by decisions/0035 s4), from the "
    "alpha each book was solved against and its ACTIVE weight, `w - w_baseline`, with "
    "nothing re-solved unconstrained. `w_baseline` is the long-only NNLS tracking "
    "portfolio for the benchmark (s4a) -- the book with no view -- because the "
    "benchmark legs are not holdable and `w` itself is dominated by replicating them. "
    "**Full matrix** is the reported TC: a'w_active / [sqrt(a' Omega^-1 a) "
    "sqrt(w_active' Omega w_active)] on the active covariance (Clarke, de Silva and "
    "Thorley 2006, eq. 23, with w_active in place of w throughout). **Diagonal** is the "
    "form comparable to the published 0.3 to 0.8 range and ignores correlations. "
    "**Alignment** is corr(a, Omega w_active), which needs no inverse and is a control, "
    "not a level. Omega's condition number is printed beside them because the "
    "full-matrix form inverts it. Published: 0.671 full and 0.620 diagonal for a "
    "long-only capped 21-country book (Clarke, de Silva and Thorley 2006). It gates "
    "nothing. NNLS r2 per leg (s4a) is the replication quality w_baseline is built on; "
    "a degraded r2 means the corrected TC is measured against a poor baseline."
)

IC_NOTE = (
    "Realised IC on the base cells, four readings of the same planted signal. The "
    "cross-sectional rank reading understates a heavy-tailed signal several-fold "
    "(decisions/0029 s5), so the per-date Pearson reading is printed beside it."
)


def _by_horizon(table: pd.DataFrame, columns: dict[str, str], tag: str = "base") -> pd.DataFrame:
    """Median over the cells of each horizon, one named column per reading."""
    sub = table[table["tag"] == tag] if "tag" in table.columns else table.iloc[0:0]
    present = {c: label for c, label in columns.items() if c in sub.columns}
    if sub.empty or not present:
        return pd.DataFrame()
    frame = (
        sub.assign(**{c: pd.to_numeric(sub[c], errors="coerce") for c in present})
        .groupby("horizon")[list(present)]
        .median()
    )
    return frame.rename(columns=present)


def _transfer_frame(table: pd.DataFrame) -> pd.DataFrame:
    # decisions/0035 s4a: the NNLS replication quality the corrected TC is now
    # measured against, per leg. Column names carry the leg id, which varies by
    # universe, so they are found rather than named.
    leg_cols = {
        c: f"NNLS r2 ({c[len('nnls_r2_') :]})" for c in table.columns if c.startswith("nnls_r2_")
    }
    return _by_horizon(
        table,
        {
            "transfer_coefficient": "TC, full matrix (reported), active weight",
            "transfer_coefficient_diagonal": "TC, diagonal",
            "transfer_coefficient_alignment": "alignment (control)",
            "omega_condition_median": "Omega condition number",
            **leg_cols,
        },
    )


def _ic_frame(table: pd.DataFrame) -> pd.DataFrame:
    sub = table[table["tag"] == "base"] if "tag" in table.columns else table.iloc[0:0]
    cols = {
        "realised_ic_pooled": "pooled",
        "realised_ic_cross_sectional_pearson": "per-date Pearson",
        "realised_ic_cross_sectional_demeaned": "per-date demeaned",
        "realised_ic_cross_sectional": "per-date rank",
    }
    present = {c: v for c, v in cols.items() if c in sub.columns}
    if sub.empty or not present:
        return pd.DataFrame()
    frame = sub.groupby(["ic", "horizon"])[list(present)].mean().rename(columns=present)
    frame.index = [f"{ic:g} / h{int(h)}" for ic, h in frame.index]
    return frame


def _covariance_frame(table: pd.DataFrame) -> pd.DataFrame:
    """Bias statistic by horizon, constrained book against its frictionless twin."""
    if "bias_stat" not in table.columns or "tag" not in table.columns:
        return pd.DataFrame()
    base = _by_horizon(table, {"bias_stat": "long-only book"}, "base")
    fric = _by_horizon(table, {"bias_stat": "frictionless twin"}, FRICTIONLESS)
    if base.empty or fric.empty:
        return pd.DataFrame()
    return base.join(fric)


def _md_diagnostics(summary: dict[str, Any]) -> list[str]:
    out: list[str] = []
    tc = _frame(summary.get("transfer_by_horizon") or {})
    if not tc.empty:
        out += ["## Transfer coefficient", "", TC_NOTE, "", _md_table(tc, 3, "horizon"), ""]
    ic = _frame(summary.get("ic_readings") or {})
    if not ic.empty:
        out += ["## Realised IC — four readings", "", IC_NOTE, "", _md_table(ic, 3, "IC / h"), ""]
    cov = _frame(summary.get("covariance_diagnostic") or {})
    if not cov.empty:
        out += [
            "## Covariance-error diagnostic — bias statistic, constrained against frictionless",
            "",
            COVARIANCE_NOTE,
            "",
            _md_table(cov, 2, "horizon"),
            "",
        ]
    return out


TURNOVER_HIGHLIGHT_LIST_CAP = 40


def _turnover_highlight(table: pd.DataFrame, params: Any = None) -> dict[str, Any]:
    """
    Which judged cells ran above the turnover highlight (decisions/0038): a
    count for the grid and the cells themselves. A REPORTING flag -- it gates
    nothing -- read from the `turnover_highlight` column `run_cell` records. A
    table from before that column existed has no reading, and says so rather
    than reporting zero.
    """
    from signal_lab.params import get_params

    p = params or get_params()
    cap = float(p.require("constraints.turnover.highlight_annualised"))
    judged = table[table["tag"] != FRICTIONLESS] if "tag" in table.columns else table
    out: dict[str, Any] = {"cap": cap, "n_cells": int(len(judged)), "recorded": False}
    if "turnover_highlight" not in judged.columns or judged.empty:
        return out
    flag = judged["turnover_highlight"].fillna(False).astype(bool)
    cols = [
        c
        for c in ("key", "turnover_annual", "turnover_p95_rolling_1y", "turnover_max_rolling_1y")
        if c in judged.columns
    ]
    hot = judged.loc[flag, cols]
    out.update(
        recorded=True,
        n_highlighted=int(flag.sum()),
        cells=hot.head(TURNOVER_HIGHLIGHT_LIST_CAP).to_dict(orient="records"),
        n_listed=int(min(len(hot), TURNOVER_HIGHLIGHT_LIST_CAP)),
    )
    return out


def _md_turnover_highlight(th: dict[str, Any]) -> list[str]:
    head = f"## Turnover — highlighted above {th['cap']:.0%} (disclosed, never a veto)"
    if not th.get("recorded"):
        return [head, "", "_No `turnover_highlight` column in this table; nothing to report._", ""]
    out = [
        head,
        "",
        f"▲ **{th['n_highlighted']} of {th['n_cells']}** cells ran above {th['cap']:.0%} on "
        "annual traded notional or on the rolling one-year p95 "
        "(`constraints.turnover.highlight_windows`). The rolling maximum is reported, not "
        "highlighted. decisions/0038.",
        "",
    ]
    if th["cells"]:
        out += [
            "| cell | annual | rolling 1y p95 | rolling 1y max |",
            "|---|---|---|---|",
        ]
        for r in th["cells"]:
            out.append(
                f"| ▲ `{r.get('key', '')}` | {_fmt(r.get('turnover_annual'), 2)} "
                f"| {_fmt(r.get('turnover_p95_rolling_1y'), 2)} "
                f"| {_fmt(r.get('turnover_max_rolling_1y'), 2)} |"
            )
        if th["n_highlighted"] > th["n_listed"]:
            out.append("")
            out.append(f"…and {th['n_highlighted'] - th['n_listed']} more, in `cells.csv`.")
        out.append("")
    return out


def _html_turnover_highlight(th: dict[str, Any]) -> str:
    if not th.get("recorded"):
        return "<p class='muted'>No <code>turnover_highlight</code> column in this table.</p>"
    parts = [
        f"<p><span class='accent'>▲</span> <b>{th['n_highlighted']} of {th['n_cells']}</b> cells "
        f"ran above {th['cap']:.0%} on annual traded notional or on the rolling one-year p95. "
        "The rolling maximum is reported, not highlighted. Disclosed, never a veto "
        "(decisions/0038).</p>"
    ]
    if th["cells"]:
        rows = "".join(
            f"<tr><th class='hit'>▲ <code>{r.get('key', '')}</code></th>"
            f"<td>{_fmt(r.get('turnover_annual'), 2)}</td>"
            f"<td>{_fmt(r.get('turnover_p95_rolling_1y'), 2)}</td>"
            f"<td>{_fmt(r.get('turnover_max_rolling_1y'), 2)}</td></tr>"
            for r in th["cells"]
        )
        parts.append(
            "<table><thead><tr><th>cell</th><th>annual</th><th>rolling 1y p95</th>"
            f"<th>rolling 1y max</th></tr></thead><tbody>{rows}</tbody></table>"
        )
        if th["n_highlighted"] > th["n_listed"]:
            parts.append(
                f"<p class='muted'>…and {th['n_highlighted'] - th['n_listed']} more, "
                "in <code>cells.csv</code>.</p>"
            )
    return "\n".join(parts)


CALIBRATION_COLUMNS = (
    "bias_worst_annual",
    "bias_stat",
    "left_tail_L",
    "te_realised_to_ex_ante",
    "te_p95_to_budget",
)


def _calibration(table: pd.DataFrame) -> dict[str, Any]:
    """The risk-calibration pivots over the base cells (decisions/0027)."""
    base = table[table["tag"] == "base"] if "tag" in table.columns else table.iloc[0:0]
    present = [c for c in CALIBRATION_COLUMNS if c in base.columns]
    if base.empty or not present:
        return {}
    out: dict[str, Any] = {c: _pivot(table, "base", c).to_dict() for c in present}
    if "bias_band" in base.columns:
        out["bias_band_median"] = float(base["bias_band"].median())
    if "bias_stat" in base.columns:
        out["bias_stat_median"] = float(base["bias_stat"].median())
    if "bias_worst_annual" in base.columns:
        worst = base["bias_worst_annual"].dropna()
        out["bias_worst_annual_median"] = float(worst.median()) if len(worst) else float("nan")
        out["bias_worst_annual_max"] = float(worst.max()) if len(worst) else float("nan")
    if "left_tail_L" in base.columns:
        left = pd.to_numeric(base["left_tail_L"], errors="coerce").dropna()
        if len(left):
            out["left_tail_L_median"] = float(left.median())
            out["left_tail_L_p05"] = float(left.quantile(0.05))
            out["left_tail_L_p95"] = float(left.quantile(0.95))
            out["left_tail_L_max"] = float(left.max())
    if "bias_worst_year" in base.columns:
        years = base["bias_worst_year"].dropna()
        if len(years):
            counts = years.astype(int).value_counts()
            out["bias_worst_year_mode"] = int(counts.index[0])
            out["bias_worst_year_share"] = float(counts.iloc[0] / len(years))
    if "te_p95" in base.columns:
        te = base["te_p95"].dropna()
        if len(te):
            out["te_p95_median"] = float(te.median())
            out["te_p95_max"] = float(te.max())
    return out


def summarise(
    table: pd.DataFrame,
    breadth: Breadth,
    target: float,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Everything the markdown and HTML render, as plain objects."""
    requested_h = int(meta.get("stress_horizon") or table["horizon"].median())
    stress_h = requested_h
    if stress_h not in set(table["horizon"]):
        stress_h = int(sorted(table["horizon"].unique())[len(table["horizon"].unique()) // 2])
    req = required_ic(table, target)
    req_surviving = required_ic(table, target, surviving_only=True)
    implied = {
        int(h): breadth.implied_ic(target, int(h)) for h in sorted(table["horizon"].unique())
    }
    empirical = (
        empirical_breadth(table).set_index("horizon")
        if "tag" in table.columns and (table["tag"] == FRICTIONLESS).any()
        else pd.DataFrame()
    )
    ladder = (
        ladder_breadth(table).set_index("horizon") if "tag" in table.columns else pd.DataFrame()
    )
    for i, row in req.iterrows():
        h = int(row["horizon"])
        tc = float(ladder["transfer_coefficient"].get(h, np.nan)) if len(ladder) else np.nan
        req.loc[i, "transfer_coefficient"] = tc
        req.loc[i, "implied_ic_measured_tc"] = (
            breadth.implied_ic(target, h, tc) if np.isfinite(tc) and tc > 0 else np.nan
        )
        req.loc[i, "ladder_breadth"] = (
            float(ladder["ladder_breadth"].get(h, np.nan)) if len(ladder) else np.nan
        )
        req.loc[i, "flam_implied_ic"] = implied.get(h, float("nan"))
        req.loc[i, "effective_breadth"] = breadth.effective_breadth(h)
        slope = float(empirical["ir_per_unit_ic"].get(h, np.nan)) if len(empirical) else np.nan
        req.loc[i, "empirical_breadth"] = (
            float(empirical["empirical_breadth"].get(h, np.nan)) if len(empirical) else np.nan
        )
        req.loc[i, "frictionless_ic"] = (
            target / slope if np.isfinite(slope) and slope > 0 else np.nan
        )
    judged = table[table["tag"] != FRICTIONLESS] if "tag" in table.columns else table
    return {
        "meta": meta,
        "target_net_ir": target,
        "breadth": {
            "n_series": breadth.n_series,
            "effective_bets_total": breadth.effective_bets_total,
            "effective_bets_active": breadth.effective_bets_active,
            "decisions_per_year": {int(k): v for k, v in breadth.decisions_per_year.items()},
            "signal_phi": {int(k): v for k, v in breadth.signal_phi.items()},
        },
        "frictionless_net_ir": _pivot(table, FRICTIONLESS).to_dict(),
        "transfer_ratio": transfer_ratio(table).to_dict() if "tag" in table.columns else {},
        "required_ic": req.to_dict(orient="records"),
        "ladder_net_ir": _pivot(table, "base").to_dict(),
        "ladder_seed_range": _pivot_range(table, "base").to_dict(),
        "oracle_net_ir": _pivot(table, "oracle").to_dict(),
        "required_ic_surviving": req_surviving.to_dict(orient="records"),
        "risk_calibration": _calibration(table),
        "turnover_highlight": _turnover_highlight(table),
        "transfer_by_horizon": _transfer_frame(table).to_dict(),
        "ic_readings": _ic_frame(table).to_dict(),
        "covariance_diagnostic": _covariance_frame(table).to_dict(),
        "stress_horizon": stress_h,
        "stress_horizon_requested": requested_h,
        "n_cells_judged": int(len(judged)),
        "n_cells_failing_vetoes": int((~judged["passes_portfolio_vetoes"].astype(bool)).sum())
        if "passes_portfolio_vetoes" in judged.columns
        else None,
        "cost_stress": _stress(table, "cost", stress_h)
        .groupby(["ic", "cost_multiplier"])["net_ir"]
        .mean()
        .reset_index()
        .to_dict(orient="records"),
        "turnover_curve": _stress(table, "turnover", stress_h)
        # `turnover_cap` is object dtype -- the "no cap" cell carries None --
        # and pandas 2.2 deprecated the silent downcast `fillna` performs on an
        # object column. Coerce first, so the column is float before the fill
        # and "no cap" groups under a real infinity rather than under NaN,
        # which would silently drop that row from the groupby.
        .assign(
            turnover_cap=lambda t: pd.to_numeric(t["turnover_cap"], errors="coerce").fillna(np.inf)
        )
        .groupby(["ic", "turnover_cap"])[["net_ir", "turnover_annual", "cost_drag_annual"]]
        .mean()
        .reset_index()
        .to_dict(orient="records"),
    }


def _stress(table: pd.DataFrame, tag: str, stress_h: int) -> pd.DataFrame:
    """
    The stress cells and the base cells they are measured against, at ONE
    horizon.

    Without the horizon filter the comparison is not a comparison: the stress
    cells run at a single horizon while the base cells span all four, so the
    1x-spread and 150%-cap columns were four-horizon averages and the rest were
    single-horizon. Part of every apparent cost or turnover effect was the
    horizon mix.
    """
    sub = table[table["tag"].isin(["base", tag]) & (table["horizon"] == stress_h)]
    return sub.copy()


# --- markdown -------------------------------------------------------------------


def _md_table(frame: pd.DataFrame, digits: int = 2, index_name: str = "") -> str:
    if frame.empty:
        return "_(no cells)_"
    cols = [index_name] + [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in frame.iterrows():
        lines.append("| " + " | ".join([_fmt(idx, digits)] + [_fmt(v, digits) for v in row]) + " |")
    return "\n".join(lines)


def to_markdown(summary: dict[str, Any], table: pd.DataFrame) -> str:
    m = summary["meta"]
    b = summary["breadth"]
    target = summary["target_net_ir"]
    out = [
        "# Ruler audit — decisions/0023",
        "",
        f"Source: **{m['source']}** (snapshot `{m['snapshot_id']}`), panel hash "
        f"`{m['panel_hash'][:16]}…`, params `{m['params_version']}` "
        f"(`{m['params_hash'][:16]}…`), run `{m['run_id']}`, {m['generated_at']}.",
        "",
        f"Window {m['first_date']} → {m['last_date']}, {m['n_rebalances']} rebalances, "
        f"TE budget {m['te_budget']:.1%}, target net IR **{target:.2f}**, solver `{m['solver']}`.",
        "",
        "> The signals are forward returns with noise: a lookahead by construction. "
        "Nothing here is a run, a result, or a candidate.",
        "",
        "## Effective breadth",
        "",
        f"{b['n_series']} series with enough history. Effective bets: "
        f"**{b['effective_bets_active']:.1f}** on active returns "
        f"({b['effective_bets_total']:.1f} on total returns). Independent decisions a year "
        "by signal horizon: "
        + ", ".join(f"h={h}: {v:.1f}" for h, v in b["decisions_per_year"].items())
        + ".",
        "",
        "## Required IC to clear the bar",
        "",
        "| horizon (weeks) | required IC (ladder, net) | implied IC, TC = 1 "
        "| implied IC, measured TC | measured TC | formula breadth "
        "| empirical breadth (ladder) | note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in summary["required_ic"]:
        out.append(
            f"| {r['horizon']} | {_required(r)} | {_fmt(r.get('flam_implied_ic'), 3)} "
            f"| {_fmt(r.get('implied_ic_measured_tc'), 3)} "
            f"| {_fmt(r.get('transfer_coefficient'), 3)} "
            f"| {_fmt(r.get('effective_breadth'), 1)} "
            f"| {_fmt(r.get('ladder_breadth'), 1)} | {r['note']} |"
        )
    out += ["", READING_THE_CHAIN, ""]
    out += _md_diagnostics(summary)
    out += [
        "",
        "### Required IC among cells that would survive the portfolio vetoes",
        "",
        "The table above asks only whether a cell clears the bar on net IR. A cell that "
        "clears it while breaching the tracking-error veto would be "
        "killed in phase 3, so the bar above is optimistic. This one counts only cells "
        "that pass all three portfolio vetoes at their real thresholds. Where the two "
        "disagree, the SECOND is the bar.",
        "",
    ]
    if summary.get("required_ic_surviving"):
        out += [
            "| horizon (weeks) | required IC (surviving cells) | note |",
            "|---|---|---|",
        ]
        for r in summary["required_ic_surviving"]:
            out.append(f"| {r['horizon']} | {_required(r)} | {r['note']} |")
    else:
        out.append(
            "_No cell passed all three portfolio vetoes._ On a short window this is expected "
            "and not a finding: a trailing-3y tracking error has no reading until 156 "
            "rebalances have passed, and SUBSTRATE section 10 fails a veto whose input is "
            "absent. See `veto_detail` in `cells.csv`."
        )
    n_fail = summary.get("n_cells_failing_vetoes")
    if n_fail is not None:
        out.append("")
        n_judged = summary.get("n_cells_judged", len(table))
        out.append(
            f"{n_fail} of {n_judged} cells fail at least one portfolio veto "
            "(frictionless cells have no mandate and are not judged)."
        )
    out += [
        "",
        "## The ladder — mean net IR over seeds (rows: IC, columns: horizon)",
        "",
        _md_table(_pivot(table, "base"), 2, "IC \\ h"),
        "",
        "Seed range (max − min) per cell; — where only one seed ran:",
        "",
        _md_table(_pivot_range(table, "base"), 2, "IC \\ h"),
        "",
    ]
    out += _md_calibration(summary.get("risk_calibration") or {}, m.get("te_budget"))
    out += [
        "## Oracle (IC = 1) — a ceiling, not the ruler",
        "",
        _md_table(_pivot(table, "oracle"), 2, "IC \\ h"),
        "",
        f"## Cost stress — net IR by half-spread multiplier (horizon {summary['stress_horizon']}w)",
        "",
    ]
    out += _stress_note(summary)
    cost = pd.DataFrame(summary["cost_stress"])
    if not cost.empty:
        piv = cost.pivot_table(index="ic", columns="cost_multiplier", values="net_ir")
        out.append(_md_table(piv, 2, "IC \\ ×spread"))
    out += [
        "",
        f"## Turnover-shortfall curve — net IR by annual turnover cap "
        f"(horizon {summary['stress_horizon']}w)",
        "",
    ]
    turn = pd.DataFrame(summary["turnover_curve"])
    if not turn.empty:
        piv = turn.pivot_table(index="ic", columns="turnover_cap", values="net_ir")
        piv.columns = ["uncapped" if np.isinf(c) else f"{c:.0%}" for c in piv.columns]
        out.append(_md_table(piv, 2, "IC \\ cap"))
        piv2 = turn.pivot_table(index="ic", columns="turnover_cap", values="turnover_annual")
        piv2.columns = ["uncapped" if np.isinf(c) else f"{c:.0%}" for c in piv2.columns]
        out += [
            "",
            "Realised annual turnover (traded notional) at each cap:",
            "",
            _md_table(piv2, 2, "IC \\ cap"),
        ]
    out += [""]
    out += _md_turnover_highlight(summary.get("turnover_highlight") or {"cap": 0.0})
    out += [
        "",
        "## Every cell",
        "",
        "See `cells.csv`. Columns: realised IC (pooled and cross-sectional), TE p95 and max, "
        "ex-ante TE, turnover, cost drag, active drawdown, and the share of rebalances on "
        "which each constraint bound or the budget was infeasible.",
        "",
    ]
    return "\n".join(out)


CALIBRATION_INTRO = (
    "Two different questions, and decisions/0030 separates them. HOW MUCH RISK the "
    "book ran is a characteristic and is disclosed: active volatility clusters, so a "
    "book honestly sized to the budget runs above it in a crisis and below it in a "
    "calm decade, and `TE p95 / budget` above 1.00 is a fact about the world rather "
    "than a fault. WHETHER IT RAN THE RISK IT WAS SIZED FOR is the gate. `bias` is "
    "the standard deviation of each period's active return over the ex-ante TE of "
    "the book that earned it: 1.00 is a calibrated risk model. The **worst annual** "
    "reading is what the risk_calibration veto takes; the full-sample reading is "
    "shown beside it and gates nothing, because it cannot tell a book running twice "
    "its sized risk for a year from one that is not."
)


def _disclosure_lines(cal: dict[str, Any], budget: float | None = None) -> list[str]:
    """The plain-language risk disclosure, for a reader who is not an author.

    decisions/0030 made the realised tracking error something the lab states
    rather than something it hides behind a veto, which only means anything if
    it is stated somewhere a person reads.
    """
    lines: list[str] = []
    if "te_p95_median" in cal:
        budget_text = f" against a {budget:.1%} ex-ante budget" if budget else ""
        lines.append(
            f"- Trailing-3y tracking error, 95th percentile: median "
            f"{cal['te_p95_median']:.2%} across base cells, worst "
            f"{cal['te_p95_max']:.2%}{budget_text}. Reported, not gated."
        )
    if "bias_worst_annual_median" in cal:
        lines.append(
            f"- Worst single year of risk-model bias: median "
            f"{cal['bias_worst_annual_median']:.2f}, worst "
            f"{cal['bias_worst_annual_max']:.2f}. This is what is gated."
        )
    if "bias_worst_year_mode" in cal:
        lines.append(
            f"- That worst year is {cal['bias_worst_year_mode']} in "
            f"{cal['bias_worst_year_share']:.0%} of base cells — the overrun is an "
            f"episode, not a drift."
        )
    if "left_tail_L_median" in cal:
        lines.append(
            f"- Left tail, L = |q05(z)| / 1.645 (1.00 when the risk model is right): "
            f"median {cal['left_tail_L_median']:.2f} across base cells, 5th to 95th "
            f"percentile {cal['left_tail_L_p05']:.2f} to {cal['left_tail_L_p95']:.2f}, "
            f"max {cal['left_tail_L_max']:.2f}. H-2026-0007's pre-registered check "
            f"(decisions/0031); reported, gates nothing."
        )
    if "bias_stat_median" in cal:
        lines.append(
            f"- Full-sample bias, for contrast: median "
            f"{cal['bias_stat_median']:.2f}. Averaging over the whole window hides "
            f"the episode above, which is why it is not the gate."
        )
    return lines


def _frame(pivot: dict) -> pd.DataFrame:
    return pd.DataFrame(pivot) if pivot else pd.DataFrame()


def _md_calibration(cal: dict[str, Any], budget: float | None = None) -> list[str]:
    if not cal:
        return []
    out = ["## Risk characteristics — ex ante against realised", "", CALIBRATION_INTRO, ""]
    disclosure = _disclosure_lines(cal, budget)
    if disclosure:
        out += ["### What this book does to risk", ""] + disclosure + [""]
    if "bias_worst_annual" in cal:
        out += [
            "Worst annual bias statistic (what risk_calibration gates on):",
            "",
            _md_table(_frame(cal["bias_worst_annual"]), 2, "IC \\ h"),
            "",
        ]
    if "bias_stat" in cal:
        band = cal.get("bias_band_median", float("nan"))
        out += [
            f"Bias statistic (1.00 is calibrated; approximate 95% band ±{_fmt(band, 3)}):",
            "",
            _md_table(_frame(cal["bias_stat"]), 2, "IC \\ h"),
            "",
        ]
    if "left_tail_L" in cal:
        out += [
            "Left-tail statistic L = |q05(z)| / 1.645 (1.00 is calibrated; "
            "decisions/0031, gates nothing):",
            "",
            _md_table(_frame(cal["left_tail_L"]), 2, "IC \\ h"),
            "",
        ]
    if "te_realised_to_ex_ante" in cal:
        out += [
            "Realised active volatility / mean ex-ante TE:",
            "",
            _md_table(_frame(cal["te_realised_to_ex_ante"]), 2, "IC \\ h"),
            "",
        ]
    if "te_p95_to_budget" in cal:
        out += [
            "Trailing-3y TE p95 / budget (disclosed, gates nothing):",
            "",
            _md_table(_frame(cal["te_p95_to_budget"]), 2, "IC \\ h"),
            "",
        ]
    return out


def _html_diagnostics(summary: dict[str, Any]) -> str:
    def plain(text: str) -> str:
        return text.replace("`", "").replace("**", "")

    parts: list[str] = []
    tc = _frame(summary.get("transfer_by_horizon") or {})
    if not tc.empty:
        parts += ["<h2>Transfer coefficient</h2>", f"<p class='muted'>{plain(TC_NOTE)}</p>"]
        parts.append(_html_table(tc, 3, "horizon"))
    ic = _frame(summary.get("ic_readings") or {})
    if not ic.empty:
        parts += ["<h2>Realised IC — four readings</h2>", f"<p class='muted'>{IC_NOTE}</p>"]
        parts.append(_html_table(ic, 3, "IC / h"))
    cov = _frame(summary.get("covariance_diagnostic") or {})
    if not cov.empty:
        parts += [
            "<h2>Covariance-error diagnostic — bias statistic, constrained against frictionless</h2>",
            f"<p class='muted'>{COVARIANCE_NOTE}</p>",
        ]
        parts.append(_html_table(cov, 2, "horizon"))
    return "\n".join(parts)


def _html_calibration(cal: dict[str, Any], budget: float | None = None) -> str:
    if not cal:
        return ""
    parts = [
        "<h2>Risk characteristics — ex ante against realised</h2>",
        f"<p class='muted'>{CALIBRATION_INTRO.replace('`', '').replace('**', '')}</p>",
    ]
    disclosure = _disclosure_lines(cal, budget)
    if disclosure:
        items = "".join(f"<li>{line.lstrip('- ')}</li>" for line in disclosure)
        parts.append(f"<h3>What this book does to risk</h3><ul>{items}</ul>")
    labels = {
        "bias_worst_annual": "Worst annual bias statistic (what risk_calibration gates on)",
        "bias_stat": "Full-sample bias statistic, which gates nothing (approximate 95% band ±"
        + _fmt(cal.get("bias_band_median", float("nan")), 3)
        + ")",
        "left_tail_L": "Left-tail statistic L = |q05(z)| / 1.645 (decisions/0031, gates nothing)",
        "te_realised_to_ex_ante": "Realised active volatility / mean ex-ante TE",
        "te_p95_to_budget": "Trailing-3y TE p95 / budget (disclosed, gates nothing)",
    }
    for key, label in labels.items():
        if key in cal:
            parts.append(f"<p class='muted'>{label}</p>")
            parts.append(_html_table(_frame(cal[key]), 2, "IC \\ h"))
    return "\n".join(parts)


# --- html -------------------------------------------------------------------------


def _html_table(
    frame: pd.DataFrame, digits: int, index_name: str, highlight: float | None = None
) -> str:
    if frame.empty:
        return "<p class='muted'>(no cells)</p>"
    head = "".join(f"<th>{c}</th>" for c in [index_name] + [str(c) for c in frame.columns])
    rows = []
    for idx, row in frame.iterrows():
        cells = [f"<th>{_fmt(idx, digits)}</th>"]
        for v in row:
            cls = ""
            if highlight is not None and isinstance(v, float) and np.isfinite(v) and v >= highlight:
                cls = " class='hit'"
            cells.append(f"<td{cls}>{_fmt(v, digits)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def to_html(summary: dict[str, Any], table: pd.DataFrame) -> str:
    m = summary["meta"]
    b = summary["breadth"]
    target = summary["target_net_ir"]
    css = f"""
    body {{ font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif; color: {GREY[0]};
           background: #fff; margin: 0; padding: 32px 24px; max-width: 1100px; }}
    h1 {{ font-size: 22px; margin: 0 0 4px; }} h2 {{ font-size: 15px; margin: 28px 0 8px;
           color: {GREY[1]}; text-transform: uppercase; letter-spacing: .06em; }}
    p, li {{ font-size: 14px; line-height: 1.5; }} .muted {{ color: {GREY[2]}; }}
    .banner {{ border-left: 4px solid {ORANGE}; background: {GREY[6]}; padding: 10px 14px; margin: 16px 0; }}
    table {{ border-collapse: collapse; font-size: 13px; margin: 8px 0 4px; }}
    th, td {{ border: 1px solid {GREY[4]}; padding: 5px 10px; text-align: right; }}
    th {{ background: {GREY[5]}; color: {GREY[1]}; font-weight: 600; }}
    td.hit {{ background: {ORANGE}; color: #fff; font-weight: 600; }}
    .kpis {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0; }}
    .kpi {{ background: {GREY[6]}; border: 1px solid {GREY[4]}; padding: 10px 14px; min-width: 150px; }}
    .kpi b {{ display: block; font-size: 20px; color: {GREY[0]}; }} .kpi span {{ font-size: 12px; color: {GREY[2]}; }}
    .accent {{ color: {ORANGE}; }} code {{ font-size: 12px; background: {GREY[6]}; padding: 1px 4px; }}
    """
    req_rows = "".join(
        f"<tr><th>{r['horizon']}</th><td class='{'hit' if np.isfinite(r['required_ic']) else ''}'>"
        f"{_required(r)}</td><td>{_fmt(r.get('flam_implied_ic'), 3)}</td>"
        f"<td>{_fmt(r.get('implied_ic_measured_tc'), 3)}</td>"
        f"<td>{_fmt(r.get('transfer_coefficient'), 3)}</td>"
        f"<td>{_fmt(r.get('effective_breadth'), 1)}</td>"
        f"<td>{_fmt(r.get('ladder_breadth'), 1)}</td>"
        f"<td style='text-align:left'>{r['note']}</td></tr>"
        for r in summary["required_ic"]
    )
    diagnostics_html = _html_diagnostics(summary)
    cost = pd.DataFrame(summary["cost_stress"])
    cost_html = (
        _html_table(
            cost.pivot_table(index="ic", columns="cost_multiplier", values="net_ir"),
            2,
            "IC \\ ×spread",
            target,
        )
        if not cost.empty
        else ""
    )
    turn = pd.DataFrame(summary["turnover_curve"])
    turn_html = ""
    if not turn.empty:
        piv = turn.pivot_table(index="ic", columns="turnover_cap", values="net_ir")
        piv.columns = ["uncapped" if np.isinf(c) else f"{c:.0%}" for c in piv.columns]
        turn_html = _html_table(piv, 2, "IC \\ cap", target)
    stress_h = summary["stress_horizon"]
    surviving = summary.get("required_ic_surviving") or []
    if surviving:
        rows = "".join(
            f"<tr><th>{r['horizon']}</th><td class='hit'>{_required(r)}</td>"
            f"<td style='text-align:left'>{r['note']}</td></tr>"
            for r in surviving
        )
        surviving_html = (
            "<p class='muted'>The table above asks only whether a cell clears the bar on net IR. "
            "A cell that clears it while breaching the tracking-error veto "
            "would be killed in phase 3. Where the two disagree, this one is the bar.</p>"
            "<table><thead><tr><th>horizon (weeks)</th><th>required IC (surviving cells)</th>"
            f"<th>note</th></tr></thead><tbody>{rows}</tbody></table>"
        )
    else:
        surviving_html = (
            "<p class='muted'><b>No cell passed all three portfolio vetoes.</b> On a short window "
            "this is expected and not a finding: a trailing-3y tracking error has no reading "
            "until 156 rebalances have passed, and a veto whose input is absent fails. See "
            "<code>veto_detail</code> in cells.csv.</p>"
        )
    ic_h = "IC \\ h"
    ladder_html = _html_table(_pivot(table, "base"), 2, ic_h, target)
    range_html = _html_table(_pivot_range(table, "base"), 2, ic_h)
    oracle_html = _html_table(_pivot(table, "oracle"), 2, ic_h)
    calibration_html = _html_calibration(summary.get("risk_calibration") or {}, m.get("te_budget"))
    decisions = ", ".join(f"h={h}: {v:.1f}" for h, v in b["decisions_per_year"].items())
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Ruler audit — {m["run_id"]}</title>
<style>{css}</style></head><body>
<h1>Ruler audit <span class="accent">·</span> decisions/0023</h1>
<p class="muted">{m["source"]} · snapshot <code>{m["snapshot_id"]}</code> · panel <code>{m["panel_hash"][:16]}…</code>
· params {m["params_version"]} <code>{m["params_hash"][:16]}…</code> · run <code>{m["run_id"]}</code> · {m["generated_at"]}</p>
<div class="banner"><b>Not a run.</b> The planted signals are forward returns with noise — a lookahead by construction.
This page measures the pipeline at the section 4 budget; nothing on it is a result about markets.</div>
<div class="kpis">
 <div class="kpi"><b>{target:.2f}</b><span>target net IR (the bar)</span></div>
 <div class="kpi"><b>{m["te_budget"]:.1%}</b><span>tracking-error budget</span></div>
 <div class="kpi"><b>{b["effective_bets_active"]:.1f}</b><span>effective bets, active ({b["n_series"]} series)</span></div>
 <div class="kpi"><b>{m["n_rebalances"]}</b><span>rebalances {m["first_date"]} → {m["last_date"]}</span></div>
</div>
<h2>Required IC to clear the bar</h2>
<table><thead><tr><th>horizon (weeks)</th><th>required IC (ladder, net)</th><th>implied IC, TC = 1</th><th>implied IC, measured TC</th><th>measured TC</th><th>formula breadth</th><th>empirical breadth (ladder)</th><th>note</th></tr></thead>
<tbody>{req_rows}</tbody></table>
<p class="muted">Decisions a year by horizon (52/h): {decisions}. {READING_THE_CHAIN}</p>
{diagnostics_html}
<h2>The ladder — mean net IR over seeds</h2>
{ladder_html}
<p class="muted">Orange: at or above the bar. Seed range per cell (— where only one seed ran):</p>
{range_html}
{calibration_html}
<h2>Oracle (IC = 1) — a ceiling, not the ruler</h2>
{oracle_html}
<h2>Required IC among cells that would survive the portfolio vetoes</h2>
{surviving_html}
<h2>Cost stress — net IR by half-spread multiplier (horizon {stress_h}w)</h2>
{cost_html}
<h2>Turnover-shortfall curve — net IR by annual turnover cap (horizon {stress_h}w)</h2>
{turn_html}
<h2>Turnover — highlighted above {summary.get("turnover_highlight", {}).get("cap", 0):.0%}</h2>
{_html_turnover_highlight(summary.get("turnover_highlight") or {})}
<p class="muted">Every cell, with realised IC, TE, turnover, cost drag, drawdown and binding shares, is in <code>cells.csv</code>.</p>
</body></html>"""


# --- files ----------------------------------------------------------------------


def write_outputs(
    out_dir: Path | str,
    table: pd.DataFrame,
    breadth: Breadth,
    target: float,
    meta: dict[str, Any],
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = summarise(table, breadth, target, meta)
    table.to_csv(out / "cells.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=_json_default), encoding="utf-8"
    )
    (out / "breadth.json").write_text(
        json.dumps(asdict(breadth), indent=2, default=_json_default), encoding="utf-8"
    )
    (out / "ruler.md").write_text(to_markdown(summary, table), encoding="utf-8")
    (out / "ruler.html").write_text(to_html(summary, table), encoding="utf-8")
    return out


def _json_default(value: Any):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return str(value)


def run_id_now() -> str:
    return datetime.now(UTC).strftime("A-%Y%m%d-%H%M%S")
