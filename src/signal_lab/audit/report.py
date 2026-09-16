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
from signal_lab.audit.ladder import required_ic

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
    sub = table[table["tag"] == tag]
    if sub.empty:
        return pd.DataFrame()
    lo = sub.pivot_table(index="ic", columns="horizon", values=value, aggfunc="min")
    hi = sub.pivot_table(index="ic", columns="horizon", values=value, aggfunc="max")
    return hi - lo


CALIBRATION_COLUMNS = ("bias_stat", "te_realised_to_ex_ante", "te_p95_to_budget")


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
    return out


def summarise(
    table: pd.DataFrame,
    breadth: Breadth,
    target: float,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Everything the markdown and HTML render, as plain objects."""
    stress_h = int(meta.get("stress_horizon") or table["horizon"].median())
    if stress_h not in set(table["horizon"]):
        stress_h = int(sorted(table["horizon"].unique())[len(table["horizon"].unique()) // 2])
    req = required_ic(table, target)
    req_surviving = required_ic(table, target, surviving_only=True)
    implied = {
        int(h): breadth.implied_ic(target, int(h)) for h in sorted(table["horizon"].unique())
    }
    for i, row in req.iterrows():
        h = int(row["horizon"])
        req.loc[i, "flam_implied_ic"] = implied.get(h, float("nan"))
        req.loc[i, "effective_breadth"] = breadth.effective_breadth(h)
    return {
        "meta": meta,
        "target_net_ir": target,
        "breadth": {
            "n_series": breadth.n_series,
            "effective_bets_total": breadth.effective_bets_total,
            "effective_bets_active": breadth.effective_bets_active,
            "decisions_per_year": {int(k): v for k, v in breadth.decisions_per_year.items()},
        },
        "required_ic": req.to_dict(orient="records"),
        "ladder_net_ir": _pivot(table, "base").to_dict(),
        "ladder_seed_range": _pivot_range(table, "base").to_dict(),
        "oracle_net_ir": _pivot(table, "oracle").to_dict(),
        "required_ic_surviving": req_surviving.to_dict(orient="records"),
        "risk_calibration": _calibration(table),
        "stress_horizon": stress_h,
        "n_cells_failing_vetoes": int((~table["passes_portfolio_vetoes"]).sum())
        if "passes_portfolio_vetoes" in table.columns
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
        "| horizon (weeks) | required IC (ladder) | FLAM-implied IC (TC = 1) | effective breadth | note |",
        "|---|---|---|---|---|",
    ]
    for r in summary["required_ic"]:
        out.append(
            f"| {r['horizon']} | {_fmt(r['required_ic'], 3)} | {_fmt(r.get('flam_implied_ic'), 3)} | "
            f"{_fmt(r.get('effective_breadth'), 1)} | {r['note']} |"
        )
    out += [
        "",
        "The gap between the ladder's required IC and the fundamental law's is the price "
        "of long-only, the cash and position caps, the turnover cap and covariance error, "
        "measured rather than assumed.",
        "",
        "### Required IC among cells that would survive the portfolio vetoes",
        "",
        "The table above asks only whether a cell clears the bar on net IR. A cell that "
        "clears it while breaching the tracking-error veto would be "
        "killed in phase 3, so the bar above is optimistic. This one counts only cells "
        "that pass all four portfolio vetoes at their real thresholds. Where the two "
        "disagree, the SECOND is the bar.",
        "",
    ]
    if summary.get("required_ic_surviving"):
        out += [
            "| horizon (weeks) | required IC (surviving cells) | note |",
            "|---|---|---|",
        ]
        for r in summary["required_ic_surviving"]:
            out.append(f"| {r['horizon']} | {_fmt(r['required_ic'], 3)} | {r['note']} |")
    else:
        out.append(
            "_No cell passed all four portfolio vetoes._ On a short window this is expected "
            "and not a finding: a trailing-3y tracking error has no reading until 156 "
            "rebalances have passed, and SUBSTRATE section 10 fails a veto whose input is "
            "absent. See `veto_detail` in `cells.csv`."
        )
    n_fail = summary.get("n_cells_failing_vetoes")
    if n_fail is not None:
        out.append("")
        out.append(f"{n_fail} of {len(table)} cells fail at least one portfolio veto.")
    out += [
        "",
        "## The ladder — mean net IR over seeds (rows: IC, columns: horizon)",
        "",
        _md_table(_pivot(table, "base"), 2, "IC \\ h"),
        "",
        "Seed range (max − min) per cell:",
        "",
        _md_table(_pivot_range(table, "base"), 2, "IC \\ h"),
        "",
    ]
    out += _md_calibration(summary.get("risk_calibration") or {})
    out += [
        "## Oracle (IC = 1) — a ceiling, not the ruler",
        "",
        _md_table(_pivot(table, "oracle"), 2, "IC \\ h"),
        "",
        f"## Cost stress — net IR by half-spread multiplier (horizon {summary['stress_horizon']}w)",
        "",
    ]
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
    "Measured, gates nothing (decisions/0027). Does the risk each book was sized to "
    "match the risk it ran? `bias` is the standard deviation of each period's active "
    "return over the ex-ante TE of the book that earned it: 1.00 is a calibrated "
    "risk model. `TE p95 / budget` is the statistic the tracking-error veto reads, "
    "over the budget the solver aimed at: above 1.00 the veto fires on a book that "
    "did what it was told."
)


def _frame(pivot: dict) -> pd.DataFrame:
    return pd.DataFrame(pivot) if pivot else pd.DataFrame()


def _md_calibration(cal: dict[str, Any]) -> list[str]:
    if not cal:
        return []
    out = ["## Risk calibration — ex ante against realised", "", CALIBRATION_INTRO, ""]
    if "bias_stat" in cal:
        band = cal.get("bias_band_median", float("nan"))
        out += [
            f"Bias statistic (1.00 is calibrated; approximate 95% band ±{_fmt(band, 3)}):",
            "",
            _md_table(_frame(cal["bias_stat"]), 2, "IC \\ h"),
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
            "Trailing-3y TE p95 / budget (the veto's reading):",
            "",
            _md_table(_frame(cal["te_p95_to_budget"]), 2, "IC \\ h"),
            "",
        ]
    return out


def _html_calibration(cal: dict[str, Any]) -> str:
    if not cal:
        return ""
    parts = [
        "<h2>Risk calibration — ex ante against realised</h2>",
        f"<p class='muted'>{CALIBRATION_INTRO.replace('`', '')}</p>",
    ]
    labels = {
        "bias_stat": "Bias statistic (approximate 95% band ±"
        + _fmt(cal.get("bias_band_median", float("nan")), 3)
        + ")",
        "te_realised_to_ex_ante": "Realised active volatility / mean ex-ante TE",
        "te_p95_to_budget": "Trailing-3y TE p95 / budget",
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
        f"{_fmt(r['required_ic'], 3)}</td><td>{_fmt(r.get('flam_implied_ic'), 3)}</td>"
        f"<td>{_fmt(r.get('effective_breadth'), 1)}</td><td style='text-align:left'>{r['note']}</td></tr>"
        for r in summary["required_ic"]
    )
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
            f"<tr><th>{r['horizon']}</th><td class='hit'>{_fmt(r['required_ic'], 3)}</td>"
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
            "<p class='muted'><b>No cell passed all four portfolio vetoes.</b> On a short window "
            "this is expected and not a finding: a trailing-3y tracking error has no reading "
            "until 156 rebalances have passed, and a veto whose input is absent fails. See "
            "<code>veto_detail</code> in cells.csv.</p>"
        )
    ic_h = "IC \\ h"
    ladder_html = _html_table(_pivot(table, "base"), 2, ic_h, target)
    range_html = _html_table(_pivot_range(table, "base"), 2, ic_h)
    oracle_html = _html_table(_pivot(table, "oracle"), 2, ic_h)
    calibration_html = _html_calibration(summary.get("risk_calibration") or {})
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
<table><thead><tr><th>horizon (weeks)</th><th>required IC (ladder)</th><th>FLAM-implied IC (TC=1)</th><th>effective breadth</th><th>note</th></tr></thead>
<tbody>{req_rows}</tbody></table>
<p class="muted">Independent decisions a year by horizon: {decisions}.
The gap between the two IC columns is the price of the constraints and of covariance error.</p>
<h2>The ladder — mean net IR over seeds</h2>
{ladder_html}
<p class="muted">Orange: at or above the bar. Seed range per cell:</p>
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
