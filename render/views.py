"""
View layer. Builds figures and table structures from results.

Every function here returns a plotly Figure or a plain dict/DataFrame and
does no rendering. static_report.py wraps these into a self-contained HTML
file; a Streamlit app would pass the same objects to st.plotly_chart /
st.dataframe. Keeping this layer renderer-agnostic is what stops the shared
HTML and the deployed app from drifting apart.
"""

import numpy as np
import plotly.graph_objects as go

ORANGE = "#FF6100"
INK = "#1C252E"
SLATE = "#455760"
ICE = "#C3EBF6"
GREY = "#9AA5AD"
GRID = "#E6E9EB"
FAIL = "#B9C0C5"

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "'Helvetica Neue', Arial, sans-serif")

LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
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


def leaderboard_table(runs):
    """Rows for the leaderboard. Sorted by pre-registered objective only."""
    return [{
        "run_id": r["run_id"],
        "family": r["family"],
        "aggregation": r["aggregation"],
        "net_ir": r["net_ir"],
        "te": r["te"],
        "turnover": r["turnover"],
        "max_cash": r["max_cash"],
        "n_positions": r["n_positions"],
        "verdicts": r["verdicts"],
        "passed": r["passed"],
    } for r in runs]


def ir_vs_te_scatter(runs):
    f = _fig(height=300, hovermode="closest",
             margin=dict(l=52, r=16, t=16, b=44))
    for passed, colour, size in ((False, FAIL, 7), (True, ORANGE, 10)):
        sel = [r for r in runs if r["passed"] == passed]
        if not sel:
            continue
        f.add_trace(go.Scatter(
            x=[r["te"] for r in sel], y=[r["net_ir"] for r in sel],
            mode="markers",
            marker=dict(size=size, color=colour,
                        line=dict(width=0.8, color="white")),
            text=[f"{r['run_id']} · {r['family']}" for r in sel],
            hovertemplate="%{text}<br>IR %{y:.2f} · TE %{x:.1f}%<extra></extra>",
        ))
    f.add_vline(x=6.0, line=dict(color=GREY, width=1, dash="dot"))
    f.add_hline(y=0, line=dict(color=GRID, width=1))
    f.update_xaxes(title_text="Tracking error vs 50/50, %")
    f.update_yaxes(title_text="Net information ratio")
    return f


def cumulative_vs_benchmark(d):
    f = _fig(height=300, showlegend=True,
             legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"))
    f.add_trace(go.Scatter(x=d["dates"], y=d["cum_bench"], name="50/50 benchmark",
                           line=dict(color=GREY, width=1.6)))
    f.add_trace(go.Scatter(x=d["dates"], y=d["cum_strat"], name="Strategy, net",
                           line=dict(color=ORANGE, width=2.1)))
    f.update_yaxes(title_text="Growth of 1.0")
    return f


def active_drawdown(d):
    f = _fig(height=190)
    f.add_trace(go.Scatter(x=d["dates"], y=d["drawdown"] * 100,
                           fill="tozeroy", line=dict(color=SLATE, width=1),
                           fillcolor="rgba(69,87,96,0.13)"))
    f.update_yaxes(title_text="Active drawdown, %")
    return f


def rolling_excess(d):
    f = _fig(height=190)
    f.add_trace(go.Bar(x=d["dates"], y=d["roll_excess"] * 100,
                       marker_color=np.where(d["roll_excess"] >= 0, ORANGE, SLATE),
                       marker_line_width=0))
    f.add_hline(y=0, line=dict(color=GREY, width=1))
    f.update_yaxes(title_text="Rolling 12m excess, %")
    return f


def rolling_te(d, cap=6.0):
    f = _fig(height=190)
    f.add_trace(go.Scatter(x=d["dates"], y=d["roll_te"],
                           line=dict(color=SLATE, width=1.6)))
    f.add_hline(y=cap, line=dict(color=ORANGE, width=1, dash="dash"))
    f.update_yaxes(title_text="Rolling 52w TE, %")
    return f


def turnover_and_cost(d):
    f = _fig(height=190, showlegend=True,
             legend=dict(orientation="h", y=1.16, x=0, bgcolor="rgba(0,0,0,0)"),
             yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)",
                         linecolor=GRID, zeroline=False,
                         title=dict(text="Cumulative cost, %")))
    f.add_trace(go.Bar(x=d["dates"], y=d["turnover_wk"] * 100, name="Turnover",
                       marker_color=ICE, marker_line_width=0))
    f.add_trace(go.Scatter(x=d["dates"], y=d["cum_cost"], name="Cumulative cost drag",
                           yaxis="y2", line=dict(color=ORANGE, width=1.8)))
    f.update_yaxes(title_text="Turnover per rebal, %")
    return f


def active_weights_area(d):
    f = _fig(height=260, showlegend=True,
             legend=dict(orientation="h", y=1.14, x=0, bgcolor="rgba(0,0,0,0)"))
    palette = [ORANGE, INK, SLATE, ICE, GREY, "#7E8C94", "#D8DDE0"]
    for i, col in enumerate(d["active_weights"].columns):
        f.add_trace(go.Scatter(
            x=d["dates"], y=d["active_weights"][col], name=col,
            stackgroup="one", line=dict(width=0.5, color=palette[i % len(palette)]),
            fillcolor=palette[i % len(palette)]))
    f.update_yaxes(title_text="Active weight, %")
    return f


def risk_decomposition(d):
    f = _fig(height=260, hovermode="closest",
             margin=dict(l=118, r=16, t=16, b=36))
    order = np.argsort(d["risk_contrib"])
    axes = [d["risk_axes"][i] for i in order]
    vals = d["risk_contrib"][order]
    colours = [ORANGE if a != "Idiosyncratic" else SLATE for a in axes]
    f.add_trace(go.Bar(x=vals, y=axes, orientation="h",
                       marker_color=colours, marker_line_width=0,
                       hovertemplate="%{y}: %{x:.2f}%<extra></extra>"))
    f.update_xaxes(title_text="Contribution to active risk, %")
    return f


def ic_by_family(d):
    f = _fig(height=260, hovermode="closest",
             margin=dict(l=48, r=16, t=16, b=76))
    fams = list(d["ic_mean"].keys())
    means = [d["ic_mean"][k] for k in fams]
    ses = [d["ic_se"][k] * 1.96 for k in fams]
    colours = [ORANGE if m - s > 0 else FAIL for m, s in zip(means, ses)]
    f.add_trace(go.Bar(x=fams, y=means, marker_color=colours, marker_line_width=0,
                       error_y=dict(type="data", array=ses, color=SLATE,
                                    thickness=1, width=3)))
    f.add_hline(y=0, line=dict(color=GREY, width=1))
    f.update_yaxes(title_text="Mean rank IC, HAC 95% bands")
    f.update_xaxes(tickangle=-40)
    return f


def null_distribution(d, realised_ir):
    f = _fig(height=260, hovermode="closest")
    f.add_trace(go.Histogram(x=d["null_max_ir"], nbinsx=48,
                             marker_color=ICE, marker_line_width=0))
    f.add_vline(x=realised_ir, line=dict(color=ORANGE, width=2))
    f.add_annotation(x=realised_ir, y=1, yref="paper", yanchor="top",
                     text=f" realised {realised_ir:.2f}", showarrow=False,
                     font=dict(color=ORANGE, size=11), xanchor="left")
    f.update_xaxes(title_text="Max IR under the search's null, 4,000 draws")
    f.update_yaxes(title_text="Frequency")
    return f
