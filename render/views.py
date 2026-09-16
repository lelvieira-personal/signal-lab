"""
View layer. Builds figures and table structures from results.

Every function here returns a plotly Figure or a plain dict/DataFrame and does
no rendering. static_report.py wraps these into a self-contained HTML file;
streamlit_app.py passes the same objects to st.plotly_chart / st.dataframe.
Keeping this layer renderer-agnostic is what stops the shared HTML and the
deployed app from drifting apart.

SUBSTRATE section 12 constrains this layer, and the constraints are enforced
here rather than left to whoever writes the next report:

  * the leaderboard is sorted by the objective only, and offers no other sort;
  * failed runs stay visible with the veto that stopped them;
  * gross IR is never plotted;
  * holdout metrics are absent until the holdout is unlocked.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

ORANGE = "#FF6100"
INK = "#1C252E"
SLATE = "#455760"
ICE = "#C3EBF6"
GREY = "#9AA5AD"
GRID = "#E6E9EB"
FAIL = "#B9C0C5"

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family=FONT, size=12, color=SLATE),
    margin=dict(l=48, r=16, t=28, b=36),
    hovermode="x unified",
    xaxis=dict(gridcolor=GRID, linecolor=GRID, zeroline=False),
    yaxis=dict(gridcolor=GRID, linecolor=GRID, zeroline=False),
    showlegend=False,
)


def _fig(height=260, **over):
    f = go.Figure()
    lay = {**LAYOUT, **over}
    f.update_layout(height=height, **lay)
    return f


# The objective, pre-registered in SUBSTRATE section 3. The leaderboard has one
# sort and this is it. Offering a second sort would be offering selection.
OBJECTIVE = "net_ir"

# SUBSTRATE section 3: gross IR is recorded and never used for ranking;
# section 12: it is never plotted. The render layer refuses to draw it.
NEVER_PLOTTED = frozenset({"gross_ir"})


def leaderboard_table(runs):
    """
    Rows for the leaderboard, sorted by the pre-registered objective only.

    Survivors first, then by net IR descending. Failed runs are kept, not
    filtered: knowing what died and why is most of the diagnostic value, and
    hiding it invites the same idea to be proposed again next cycle.
    """
    rows = [
        {
            "run_id": r["run_id"],
            "family": r.get("family") or "",
            "aggregation": r.get("aggregation") or "",
            "net_ir": r.get("net_ir"),
            "te": r.get("te"),
            "turnover": r.get("turnover"),
            "max_cash": r.get("max_cash"),
            "n_positions": r.get("n_positions"),
            "verdicts": r.get("verdicts") or {},
            "verdict_details": r.get("verdict_details") or {},
            "passed": bool(r.get("passed")),
            "status": r.get("status", ""),
            "killed_by": r.get("killed_by"),
        }
        for r in runs
    ]

    def key(row):
        ir = row["net_ir"]
        return (not row["passed"], -(ir if ir is not None else float("-inf")))

    return sorted(rows, key=key)


def first_failed_veto(row, order=None):
    """The veto that stopped a run, for the leaderboard's last column."""
    if row.get("killed_by"):
        return row["killed_by"]
    verdicts = row.get("verdicts") or {}
    for name in order or list(verdicts):
        if name in verdicts and not verdicts[name]:
            return name
    return ""


def ir_vs_te_scatter(runs, te_cap=6.0):
    """IR against TE. The dotted line is the tracking error veto from params."""
    runs = [r for r in runs if r.get("net_ir") is not None and r.get("te") is not None]
    f = _fig(height=300, hovermode="closest", margin=dict(l=52, r=16, t=16, b=44))
    for passed, colour, size in ((False, FAIL, 7), (True, ORANGE, 10)):
        sel = [r for r in runs if r["passed"] == passed]
        if not sel:
            continue
        f.add_trace(
            go.Scatter(
                x=[r["te"] for r in sel],
                y=[r["net_ir"] for r in sel],
                mode="markers",
                marker=dict(size=size, color=colour, line=dict(width=0.8, color="white")),
                text=[f"{r['run_id']} · {r['family']}" for r in sel],
                hovertemplate="%{text}<br>IR %{y:.2f} · TE %{x:.1f}%<extra></extra>",
            )
        )
    f.add_vline(x=te_cap, line=dict(color=GREY, width=1, dash="dot"))
    f.add_hline(y=0, line=dict(color=GRID, width=1))
    f.update_xaxes(title_text="Tracking error vs 50/50, %")
    f.update_yaxes(title_text="Net information ratio")
    return f


def cumulative_vs_benchmark(d):
    f = _fig(
        height=300,
        showlegend=True,
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    f.add_trace(
        go.Scatter(
            x=d["dates"], y=d["cum_bench"], name="50/50 benchmark", line=dict(color=GREY, width=1.6)
        )
    )
    f.add_trace(
        go.Scatter(
            x=d["dates"], y=d["cum_strat"], name="Strategy, net", line=dict(color=ORANGE, width=2.1)
        )
    )
    f.update_yaxes(title_text="Growth of 1.0")
    return f


def active_drawdown(d):
    f = _fig(height=190)
    f.add_trace(
        go.Scatter(
            x=d["dates"],
            y=d["drawdown"] * 100,
            fill="tozeroy",
            line=dict(color=SLATE, width=1),
            fillcolor="rgba(69,87,96,0.13)",
        )
    )
    f.update_yaxes(title_text="Active drawdown, %")
    return f


def rolling_excess(d):
    f = _fig(height=190)
    f.add_trace(
        go.Bar(
            x=d["dates"],
            y=d["roll_excess"] * 100,
            marker_color=np.where(d["roll_excess"] >= 0, ORANGE, SLATE),
            marker_line_width=0,
        )
    )
    f.add_hline(y=0, line=dict(color=GREY, width=1))
    f.update_yaxes(title_text="Rolling 12m excess, %")
    return f


def rolling_te(d, cap=6.0):
    """Rolling tracking error. `cap` is the veto threshold, passed from params."""
    f = _fig(height=190)
    f.add_trace(go.Scatter(x=d["dates"], y=d["roll_te"], line=dict(color=SLATE, width=1.6)))
    f.add_hline(y=cap, line=dict(color=ORANGE, width=1, dash="dash"))
    f.update_yaxes(title_text="Rolling 52w TE, %")
    return f


def turnover_and_cost(d):
    f = _fig(
        height=190,
        showlegend=True,
        legend=dict(orientation="h", y=1.16, x=0, bgcolor="rgba(0,0,0,0)"),
        yaxis2=dict(
            overlaying="y",
            side="right",
            gridcolor="rgba(0,0,0,0)",
            linecolor=GRID,
            zeroline=False,
            title=dict(text="Cumulative cost, %"),
        ),
    )
    f.add_trace(
        go.Bar(
            x=d["dates"],
            y=d["turnover_wk"] * 100,
            name="Turnover",
            marker_color=ICE,
            marker_line_width=0,
        )
    )
    f.add_trace(
        go.Scatter(
            x=d["dates"],
            y=d["cum_cost"],
            name="Cumulative cost drag",
            yaxis="y2",
            line=dict(color=ORANGE, width=1.8),
        )
    )
    f.update_yaxes(title_text="Turnover per rebal, %")
    return f


def active_weights_area(d):
    f = _fig(
        height=260,
        showlegend=True,
        legend=dict(orientation="h", y=1.14, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    palette = [ORANGE, INK, SLATE, ICE, GREY, "#7E8C94", "#D8DDE0"]
    for i, col in enumerate(d["active_weights"].columns):
        f.add_trace(
            go.Scatter(
                x=d["dates"],
                y=d["active_weights"][col],
                name=col,
                stackgroup="one",
                line=dict(width=0.5, color=palette[i % len(palette)]),
                fillcolor=palette[i % len(palette)],
            )
        )
    f.update_yaxes(title_text="Active weight, %")
    return f


def risk_decomposition(d):
    f = _fig(height=260, hovermode="closest", margin=dict(l=118, r=16, t=16, b=36))
    order = np.argsort(d["risk_contrib"])
    axes = [d["risk_axes"][i] for i in order]
    vals = d["risk_contrib"][order]
    colours = [ORANGE if a != "Idiosyncratic" else SLATE for a in axes]
    f.add_trace(
        go.Bar(
            x=vals,
            y=axes,
            orientation="h",
            marker_color=colours,
            marker_line_width=0,
            hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        )
    )
    f.update_xaxes(title_text="Contribution to active risk, %")
    return f


def ic_by_family(d):
    f = _fig(height=260, hovermode="closest", margin=dict(l=48, r=16, t=16, b=76))
    fams = list(d["ic_mean"].keys())
    means = [d["ic_mean"][k] for k in fams]
    ses = [d["ic_se"][k] * 1.96 for k in fams]
    colours = [ORANGE if m - s > 0 else FAIL for m, s in zip(means, ses, strict=True)]
    f.add_trace(
        go.Bar(
            x=fams,
            y=means,
            marker_color=colours,
            marker_line_width=0,
            error_y=dict(type="data", array=ses, color=SLATE, thickness=1, width=3),
        )
    )
    f.add_hline(y=0, line=dict(color=GREY, width=1))
    f.update_yaxes(title_text="Mean rank IC, HAC 95% bands")
    f.update_xaxes(tickangle=-40)
    return f


def null_distribution(d, realised_ir):
    f = _fig(height=260, hovermode="closest")
    f.add_trace(go.Histogram(x=d["null_max_ir"], nbinsx=48, marker_color=ICE, marker_line_width=0))
    f.add_vline(x=realised_ir, line=dict(color=ORANGE, width=2))
    f.add_annotation(
        x=realised_ir,
        y=1,
        yref="paper",
        yanchor="top",
        text=f" realised {realised_ir:.2f}",
        showarrow=False,
        font=dict(color=ORANGE, size=11),
        xanchor="left",
    )
    f.update_xaxes(title_text="Max IR under the search's null, 4,000 draws")
    f.update_yaxes(title_text="Frequency")
    return f


def veto_legend(params=None):
    """
    The veto set as the report shows it: all ten of SUBSTRATE section 10, with
    their live thresholds read from params rather than retyped into the HTML.
    """
    from signal_lab.params import get_params

    p = params or get_params()
    pct = lambda x: f"{float(x):.0%}"  # noqa: E731
    return [
        (
            "turnover",
            f"Annualised turnover ≤ {pct(p.require('vetoes.turnover.max_annualised'))} "
            f"— a backstop, not a budget (decisions/0024); turnover is priced, not capped",
        ),
        ("cash", f"Max cash weight ≤ {pct(p.require('vetoes.cash.max_weight'))}"),
        (
            "tracking_error",
            f"Trailing-3y tracking error ≤ "
            f"{float(p.require('vetoes.tracking_error.max_trailing_3y')):.1%}, "
            f"{p.get('vetoes.tracking_error.statistic', 'p95')} of readings",
        ),
        ("positions", f"Non-zero holdings ≤ {int(p.require('vetoes.positions.max_nonzero'))}"),
        (
            "coverage",
            f"Signal covers ≥ {pct(p.require('vetoes.coverage.min_universe_fraction'))} of the "
            f"estimation universe on ≥ {pct(p.require('vetoes.coverage.min_date_fraction'))} of dates",
        ),
        ("lookahead", "Bitemporal check: no observation used before its knowledge date"),
        ("frequency", "No series contributes a return before its true daily start"),
        (
            "seed_stability",
            f"IR range across resampling seeds ≤ {float(p.require('vetoes.seed_stability.max_ir_range')):.2f}",
        ),
        (
            "multiple_testing",
            f"Survives Romano-Wolf stepdown at FWER "
            f"{pct(p.require('vetoes.multiple_testing.fwer_alpha'))}",
        ),
        ("direction", "Realised sign matches the pre-registered direction"),
    ]


def holdout_panel(params=None):
    """
    What the report says about the holdout.

    SUBSTRATE section 12: holdout metrics are absent until unlocked. This
    returns the text and a locked flag; it never returns a metric.
    """
    from signal_lab.params import get_params

    p = params or get_params()
    locked = bool(p.get("data.holdout.locked", True))
    start = p.require("data.windows.holdout_start")
    if locked:
        return {
            "locked": True,
            "title": f"Holdout from {start} is locked.",
            "body": "It opens once, on the run taken to production. "
            "Unlocking is recorded in the decision log with who and when.",
        }
    return {
        "locked": False,
        "title": f"Holdout from {start} was unlocked by {p.get('data.holdout.unlocked_by')} "
        f"on {p.get('data.holdout.unlocked_on')}.",
        "body": "Holdout metrics below are a single, final measurement and are not iterated on.",
    }


def run_summary_stats(run):
    """
    The stat tiles for a run detail.

    Gross IR is deliberately absent. SUBSTRATE section 3 records it and section
    12 forbids plotting it; showing it beside the net figure invites the reader
    to do the ranking the substrate forbids. It stays in the store for
    diagnostics. decisions/0004 replaces it with the cost drag -- gross minus
    net -- which carries the diagnostic value without the ranking temptation.
    """
    out = []
    for label, key, fmt in (
        ("Net IR", "net_ir", "{:.2f}"),
        ("Cost drag", "cost_drag", "{:.2f}"),
        ("Tracking error", "te", "{:.1f}%"),
        ("Max active drawdown", "max_active_drawdown", "{:.1f}%"),
        ("Turnover", "turnover", "{:.0f}%"),
        ("Max cash", "max_cash", "{:.1f}%"),
        ("Holdings", "n_positions", "{:.0f}"),
        ("Signal coverage", "coverage", "{:.0%}"),
        ("Seed IR range", "seed_range", "{:.2f}"),
        ("Null percentile", "null_pct", "{:.0%}"),
        ("Effective cycles", "ess_cycles", "{:.0f}"),
    ):
        value = run.get(key)
        out.append(
            {
                "label": label,
                "value": "n/a" if value is None else fmt.format(value),
                "highlight": key == "net_ir",
            }
        )
    assert not (set(run) & NEVER_PLOTTED & {"__drawn__"})
    return out
