"""
Renders the views into a single self-contained HTML file.

plotly.js is inlined in the first figure and referenced thereafter, so the
output opens from an email attachment or a shared drive with no server and
no network. A Streamlit renderer would import the same views module and
call st.plotly_chart on the same figure objects.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from plotly.io import to_html

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "src"), str(REPO_ROOT), str(REPO_ROOT / "render")]

import views as v  # noqa: E402
from sources import get_source  # noqa: E402

ORANGE, INK, SLATE, ICE = v.ORANGE, v.INK, v.SLATE, v.ICE

CSS = f"""
:root {{
  --orange:{ORANGE}; --ink:{INK}; --slate:{SLATE}; --ice:{ICE};
  --rule:#E6E9EB; --mute:#8A959C; --fail:#B9C0C5;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:#fff; color:var(--ink);
  font-family:{v.FONT}; font-size:14px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:1180px; margin:0 auto; padding:40px 32px 88px; }}

header {{ border-bottom:2px solid var(--ink); padding-bottom:18px; margin-bottom:6px; }}
h1 {{ font-size:23px; font-weight:600; margin:0 0 4px; letter-spacing:-0.01em; }}
.sub {{ color:var(--slate); font-size:13px; margin:0; }}
.meta {{ display:flex; gap:34px; flex-wrap:wrap; margin-top:16px; }}
.meta div {{ font-size:12.5px; color:var(--slate); }}
.meta b {{ display:block; color:var(--ink); font-weight:600; font-size:14px;
           font-variant-numeric:tabular-nums; }}

.notice {{
  background:#FFF4EC; border-left:3px solid var(--orange);
  padding:11px 14px; margin:22px 0 0; font-size:13px; color:var(--slate);
}}
.notice b {{ color:var(--ink); }}

h2 {{ font-size:16px; font-weight:600; margin:44px 0 3px; }}
h2 .n {{ color:var(--mute); font-weight:400; margin-right:9px; }}
.lede {{ color:var(--slate); font-size:13px; margin:0 0 16px; max-width:74ch; }}

table {{ width:100%; border-collapse:collapse; font-size:13px;
         font-variant-numeric:tabular-nums; }}
thead th {{
  text-align:left; font-weight:600; font-size:12px; color:var(--slate);
  border-bottom:1px solid var(--ink); padding:8px 10px 7px; white-space:nowrap;
}}
thead th.num, td.num {{ text-align:right; }}
tbody td {{ border-bottom:1px solid var(--rule); padding:8px 10px; }}
tbody tr.killed {{ color:var(--fail); }}
tbody tr.killed .id {{ color:var(--fail); }}
tbody tr.lead td {{ background:#FFF7F1; }}
tbody tr:hover td {{ background:#F7F9FA; }}
tbody tr.lead:hover td {{ background:#FFF1E6; }}
.id {{ font-weight:600; color:var(--ink); }}
.agg {{ color:var(--slate); }}
.ir-strong {{ color:var(--orange); font-weight:600; }}

.dots {{ display:flex; gap:4px; }}
.dot {{ width:9px; height:9px; border-radius:50%; background:#DCE1E4; }}
.dot.ok {{ background:var(--ice); }}
.dot.bad {{ background:var(--orange); }}
.why {{ font-size:12px; color:var(--slate); }}

.legend {{ margin-top:14px; font-size:12px; color:var(--slate); }}
.legend span {{ margin-right:18px; white-space:nowrap; }}
.legend i {{ display:inline-block; width:9px; height:9px; border-radius:50%;
             margin-right:5px; vertical-align:baseline; }}

.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:26px; }}
.panel {{ border:1px solid var(--rule); padding:14px 14px 6px; }}
.panel h3 {{ font-size:13px; font-weight:600; margin:0 0 2px; }}
.panel p {{ font-size:12px; color:var(--slate); margin:0 0 6px; }}

.runhead {{ display:flex; align-items:baseline; gap:16px; flex-wrap:wrap;
            border-bottom:1px solid var(--rule); padding-bottom:12px; margin-bottom:18px; }}
.runhead .rid {{ font-size:17px; font-weight:600; }}
.runhead .tag {{ font-size:12px; color:var(--slate); }}
.stats {{ display:flex; gap:30px; flex-wrap:wrap; margin:0 0 20px; }}
.stats div {{ font-size:12px; color:var(--slate); }}
.stats b {{ display:block; font-size:19px; font-weight:600; color:var(--ink);
            font-variant-numeric:tabular-nums; }}
.stats b.hl {{ color:var(--orange); }}

.locked {{ border:1px dashed #C9D0D4; padding:22px; text-align:center;
           color:var(--mute); font-size:13px; margin-top:26px; }}
.locked b {{ color:var(--slate); }}

footer {{ margin-top:56px; padding-top:16px; border-top:1px solid var(--rule);
          font-size:12px; color:var(--mute); }}

@media (max-width:820px) {{
  .grid2 {{ grid-template-columns:1fr; }}
  .wrap {{ padding:26px 18px 60px; }}
}}
"""


def _plot(fig, first=False):
    return to_html(
        fig,
        include_plotlyjs=("inline" if first else False),
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
    )


def _veto_dots(verdicts):
    cells = "".join(
        f'<span class="dot {"ok" if ok else "bad"}" title="{key}"></span>'
        for key, ok in verdicts.items()
    )
    return f'<div class="dots">{cells}</div>'


def _first_failure(verdicts, order=None):
    """The veto that stopped a run. Failed runs keep their reason on the table."""
    for k in order or list(verdicts):
        if k in verdicts and not verdicts[k]:
            return k
    return ""


def leaderboard_html(rows, order=None):
    body = io.StringIO()
    lead_id = next((r["run_id"] for r in rows if r["passed"]), None)
    for r in rows:
        cls = []
        if not r["passed"]:
            cls.append("killed")
        if r["run_id"] == lead_id:
            cls.append("lead")
        ir = r.get("net_ir")
        ir_cls = "ir-strong" if r["passed"] and ir is not None and ir >= 0.45 else ""
        body.write(f"""
<tr class="{" ".join(cls)}">
  <td class="id">{r["run_id"]}</td>
  <td>{r["family"]}</td>
  <td class="agg">{r["aggregation"]}</td>
  <td class="num {ir_cls}">{_num(ir, "{:.2f}")}</td>
  <td class="num">{_num(r.get("te"), "{:.1f}")}</td>
  <td class="num">{_num(r.get("turnover"), "{:.0f}")}</td>
  <td class="num">{_num(r.get("max_cash"), "{:.1f}")}</td>
  <td class="num">{_num(r.get("n_positions"), "{:.0f}")}</td>
  <td>{_veto_dots(r["verdicts"])}</td>
  <td class="why">{"" if r["passed"] else _first_failure(r["verdicts"], order)}</td>
</tr>""")
    return f"""
<table>
  <thead><tr>
    <th>Run</th><th>Signal family</th><th>Aggregation</th>
    <th class="num">Net IR</th><th class="num">TE %</th>
    <th class="num">Turnover %</th><th class="num">Max cash %</th>
    <th class="num">Holdings</th><th>Vetoes</th><th>Stopped by</th>
  </tr></thead>
  <tbody>{body.getvalue()}</tbody>
</table>
<div class="legend">
  <span><i style="background:var(--ice)"></i>veto passed</span>
  <span><i style="background:var(--orange)"></i>veto failed</span>
  <span>Order is the pre-registered objective. Sorting by anything else is
        selection, so the table doesn't offer it.</span>
</div>"""


def _num(value, fmt="{:.2f}"):
    """Render a number, or an em dash where the harness has not produced one."""
    return "—" if value is None else fmt.format(value)


def _empty_report(data, params, path):
    """
    The report for a lab with no runs.

    An empty leaderboard is the correct picture of phase 0, and saying so beats
    rendering nothing or, worse, falling back to the mock without a banner.
    """
    holdout = v.holdout_panel(params)
    vetoes = "".join(f"<li><b>{name}</b> — {label}</li>" for name, label in v.veto_legend(params))
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signal Lab — run browser</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<header>
  <h1>Signal Lab — run browser</h1>
  <p class="sub">Read-only browser over the results store. Nothing here changes a portfolio.</p>
  <div class="meta">
    <div>Experiments<b>0</b></div>
    <div>Survived all vetoes<b>0</b></div>
    <div>Development window<b>{data.dev_start} to {data.dev_end}</b></div>
    <div>Holdout<b>{"locked" if holdout["locked"] else "unlocked"}</b></div>
    <div>Params version<b>{params.params_version}</b></div>
    <div>Params hash<b>{params.params_hash[:12]}</b></div>
  </div>
</header>
<div class="notice"><b>No runs recorded.</b> The results store is empty. This is the
  expected state until the walk-forward engine lands in phase 1; the veto set below is
  already live and is read from <code>params/vetoes.yaml</code>.</div>
<h2><span class="n">1</span>Veto set</h2>
<p class="lede">Fixed before any cycle runs. A run failing any one is killed with the
  reason logged; none of these are advisory, and none is tuned per run.</p>
<ol style="font-size:13px;color:var(--slate);padding-left:20px;line-height:1.9">{vetoes}</ol>
<div class="locked"><b>{holdout["title"]}</b><br>{holdout["body"]}</div>
<footer>Signal Lab · params {params.params_version} ({params.params_hash[:12]}) ·
  rendered from views.py, which streamlit_app.py also imports.</footer>
</div></body></html>"""
    Path(path).write_text(html, encoding="utf-8")
    return str(path)


def build(path="leaderboard.html", synthetic=False, db_path=None, params=None):
    """
    Render the report.

    `synthetic=True` regenerates the mock so the layout can be reviewed with no
    runs present. The synthetic banner is not optional: a mock report that could
    pass for a real one is a hazard, not a convenience.
    """
    from signal_lab.params import get_params

    params = params or get_params()
    source = get_source(
        synthetic=synthetic, **({"db_path": db_path} if db_path and not synthetic else {})
    )
    data = source.load()

    if not data.runs:
        return _empty_report(data, params, path)

    order = [name for name, _ in v.veto_legend(params)]
    rows = v.leaderboard_table(data.runs)
    champ = data.champion
    detail = data.detail
    holdout = v.holdout_panel(params)
    te_cap = float(params.require("vetoes.tracking_error.max_trailing_3y")) * 100

    veto_list = "".join(
        f"<li><b>{name}</b> — {label}</li>" for name, label in v.veto_legend(params)
    )

    figs = [_plot(v.ir_vs_te_scatter(data.runs, te_cap=te_cap), first=True)]
    have_detail = bool(detail) and "dates" in (detail or {})
    if have_detail:
        figs += [
            _plot(v.cumulative_vs_benchmark(detail)),
            _plot(v.rolling_excess(detail)),
            _plot(v.active_drawdown(detail)),
            _plot(v.rolling_te(detail, cap=te_cap)),
            _plot(v.turnover_and_cost(detail)),
            _plot(v.active_weights_area(detail)),
            _plot(v.risk_decomposition(detail)),
            _plot(v.ic_by_family(detail)),
            _plot(v.null_distribution(detail, champ["net_ir"])),
        ]

    banner = ""
    if data.is_synthetic:
        banner = """<div class="notice"><b>Synthetic data.</b> Every number and chart below is
  randomly generated from a fixed seed so the layout can be reviewed. No market data,
  no signals, no backtest, no result.</div>"""
    elif data.notes:
        banner = f"""<div class="notice">{" ".join(data.notes)}</div>"""

    detail_section = ""
    if have_detail and champ:
        stats = "".join(
            f"<div>{s['label']}<b{' class="hl"' if s['highlight'] else ''}>{s['value']}</b></div>"
            for s in v.run_summary_stats(champ)
        )
        detail_section = f"""
<h2><span class="n">2</span>Run detail</h2>
<div class="runhead">
  <span class="rid">{champ["run_id"]}</span>
  <span class="tag">{champ.get("family", "")} · {champ.get("aggregation", "")} ·
        {_num(champ.get("n_positions"), "{:.0f}")} holdings</span>
</div>
<div class="stats">{stats}</div>
<div class="panel" style="margin-bottom:26px">
  <h3>Net of costs vs the 50/50 benchmark</h3>
  <p>Gross is recorded for diagnostics and never plotted — only the net line is the
     deliverable (SUBSTRATE sections 3 and 12).</p>
  {figs[1]}
</div>
<div class="grid2">
  <div class="panel"><h3>Rolling 12-month excess return</h3>
    <p>How long the strategy can stay behind.</p>{figs[2]}</div>
  <div class="panel"><h3>Active drawdown</h3>
    <p>Peak-to-trough on the excess return stream.</p>{figs[3]}</div>
  <div class="panel"><h3>Rolling tracking error</h3>
    <p>Dashed line is the {te_cap:.1f}% veto threshold from params.</p>{figs[4]}</div>
  <div class="panel"><h3>Turnover and cumulative cost</h3>
    <p>Cost drag as its own series, not buried in the return.</p>{figs[5]}</div>
</div>

<h2><span class="n">3</span>What the portfolio is actually doing</h2>
<p class="lede">Positions are ETFs, but the decisions are exposures. These two views are
  where the claim that the holdings tackle distinct risks gets checked, or falsified.</p>
<div class="grid2">
  <div class="panel"><h3>Active weight by risk axis</h3>
    <p>Aggregated from instrument weights through the characteristic map.</p>{figs[6]}</div>
  <div class="panel"><h3>Active risk decomposition</h3>
    <p>A large idiosyncratic share means the exposures aren't the story.</p>{figs[7]}</div>
</div>

<h2><span class="n">4</span>Is the result real?</h2>
<p class="lede">The search tested many signals, so the best IR is a maximum over many
  draws. Romano-Wolf stepdown is the gate; these two panels are the intuition.</p>
<div class="grid2">
  <div class="panel"><h3>Rank IC by signal family</h3>
    <p>HAC bands account for overlapping weekly observations. Grey where the band
       spans zero.</p>{figs[8]}</div>
  <div class="panel"><h3>Realised IR against the search null</h3>
    <p>Block bootstrap on shuffled signals, same search width. Reported for intuition;
       the stepdown is the gate.</p>{figs[9]}</div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signal Lab — run browser</title>
<style>{CSS}</style></head>
<body><div class="wrap">

<header>
  <h1>Signal Lab — run browser</h1>
  <p class="sub">Read-only browser over {data.label}. Nothing here changes a portfolio.</p>
  <div class="meta">
    <div>Experiments<b>{data.n_runs}</b></div>
    <div>Survived all vetoes<b>{data.n_passed}</b></div>
    <div>Development window<b>{data.dev_start} to {data.dev_end}</b></div>
    <div>Holdout<b>{"locked" if holdout["locked"] else "unlocked"}</b></div>
    <div>Rebalance<b>Weekly, {params.get("constraints.rebalance.day", "FRI")}</b></div>
    <div>Params<b>{params.params_version} · {params.params_hash[:12]}</b></div>
  </div>
</header>

{banner}

<h2><span class="n">1</span>Leaderboard</h2>
<p class="lede">All {data.n_runs} experiments, survivors first. Failures stay visible with
  the veto that stopped them — knowing what died and why is most of the diagnostic value,
  and hiding it invites the same idea to be proposed again next cycle.</p>
{leaderboard_html(rows, order)}

<div class="grid2" style="margin-top:30px">
  <div class="panel">
    <h3>Where the survivors sit</h3>
    <p>Dotted line is the {te_cap:.1f}% tracking error veto.</p>
    {figs[0]}
  </div>
  <div class="panel">
    <h3>Veto set</h3>
    <p>Fixed before the cycle ran, read live from params/vetoes.yaml. A run failing any
       one is killed with the reason logged; none of these are advisory.</p>
    <ol style="font-size:12.5px;color:var(--slate);padding-left:20px;margin:8px 0 0;
               line-height:1.75">{veto_list}</ol>
  </div>
</div>

{detail_section}

<div class="locked"><b>{holdout["title"]}</b><br>{holdout["body"]}</div>

<footer>
  Signal Lab · {data.label} · params {params.params_version} ({params.params_hash[:12]}) ·
  rendered from views.py, which streamlit_app.py also imports.
</footer>

</div></body></html>"""

    Path(path).write_text(html, encoding="utf-8")
    return str(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render the Signal Lab run browser.")
    parser.add_argument("-o", "--out", default="leaderboard.html", help="output HTML path")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="regenerate the mock so the report can be built with no runs present",
    )
    parser.add_argument("--db", default=None, help="results store path (default results/runs.db)")
    args = parser.parse_args(argv)
    out = build(args.out, synthetic=args.synthetic, db_path=args.db)
    print(out)
    return out


if __name__ == "__main__":
    main()
