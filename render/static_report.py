"""
Renders the views into a single self-contained HTML file.

plotly.js is inlined in the first figure and referenced thereafter, so the
output opens from an email attachment or a shared drive with no server and
no network. A Streamlit renderer would import the same views module and
call st.plotly_chart on the same figure objects.
"""

import io
from plotly.io import to_html

import mock_data as md
import views as v

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
    return to_html(fig, include_plotlyjs=("inline" if first else False),
                   full_html=False, config={"displayModeBar": False,
                                            "responsive": True})


def _veto_dots(verdicts):
    cells = "".join(
        f'<span class="dot {"ok" if ok else "bad"}" title="{key}"></span>'
        for key, ok in verdicts.items())
    return f'<div class="dots">{cells}</div>'


def _first_failure(verdicts):
    labels = dict(md.VETOES)
    for k, ok in verdicts.items():
        if not ok:
            return labels[k].split(":")[0].split("\u2264")[0].strip()
    return ""


def leaderboard_html(rows):
    body = io.StringIO()
    lead_id = next((r["run_id"] for r in rows if r["passed"]), None)
    for r in rows:
        cls = []
        if not r["passed"]:
            cls.append("killed")
        if r["run_id"] == lead_id:
            cls.append("lead")
        ir_cls = "ir-strong" if r["passed"] and r["net_ir"] >= 0.45 else ""
        body.write(f"""
<tr class="{' '.join(cls)}">
  <td class="id">{r['run_id']}</td>
  <td>{r['family']}</td>
  <td class="agg">{r['aggregation']}</td>
  <td class="num {ir_cls}">{r['net_ir']:.2f}</td>
  <td class="num">{r['te']:.1f}</td>
  <td class="num">{r['turnover']}</td>
  <td class="num">{r['max_cash']:.1f}</td>
  <td class="num">{r['n_positions']}</td>
  <td>{_veto_dots(r['verdicts'])}</td>
  <td class="why">{'' if r['passed'] else _first_failure(r['verdicts'])}</td>
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


def build(path="leaderboard_mock.html"):
    runs, dates = md.build_runs()
    rows = v.leaderboard_table(runs)
    champ = next(r for r in runs if r["passed"])
    d = md.build_detail(champ, dates)

    n_pass = sum(r["passed"] for r in runs)
    veto_list = "".join(f"<li>{label}</li>" for _, label in md.VETOES)

    figs = [
        _plot(v.ir_vs_te_scatter(runs), first=True),
        _plot(v.cumulative_vs_benchmark(d)),
        _plot(v.rolling_excess(d)),
        _plot(v.active_drawdown(d)),
        _plot(v.rolling_te(d)),
        _plot(v.turnover_and_cost(d)),
        _plot(v.active_weights_area(d)),
        _plot(v.risk_decomposition(d)),
        _plot(v.ic_by_family(d)),
        _plot(v.null_distribution(d, champ["net_ir"])),
    ]

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Research OS — run browser (mock)</title>
<style>{CSS}</style></head>
<body><div class="wrap">

<header>
  <h1>Research OS — signal search, cycle 2026-W36</h1>
  <p class="sub">Read-only browser over a completed agentic run. Nothing here
     changes a portfolio.</p>
  <div class="meta">
    <div>Experiments<b>{len(runs)}</b></div>
    <div>Survived all vetoes<b>{n_pass}</b></div>
    <div>Development window<b>2007–2019</b></div>
    <div>Holdout<b>locked</b></div>
    <div>Rebalance<b>Weekly, Friday</b></div>
    <div>Universe<b>30 ETFs</b></div>
  </div>
</header>

<div class="notice">
  <b>Synthetic data.</b> Every number and chart below is randomly generated
  from a fixed seed so the layout can be reviewed. No market data, no signals,
  no backtest.
</div>

<h2><span class="n">1</span>Leaderboard</h2>
<p class="lede">All {len(runs)} experiments, survivors first. Failures stay
  visible with the veto that stopped them — knowing what died and why is most
  of the diagnostic value, and hiding it invites the same idea to be proposed
  again next cycle.</p>
{leaderboard_html(rows)}

<div class="grid2" style="margin-top:30px">
  <div class="panel">
    <h3>Where the survivors sit</h3>
    <p>Dotted line is the 6% tracking error veto.</p>
    {figs[0]}
  </div>
  <div class="panel">
    <h3>Veto set</h3>
    <p>Fixed before the cycle ran. A run failing any one is killed with the
       reason logged; none of these are advisory.</p>
    <ol style="font-size:13px;color:var(--slate);padding-left:20px;margin:8px 0 0;
               line-height:1.85">{veto_list}</ol>
  </div>
</div>

<h2><span class="n">2</span>Run detail</h2>
<div class="runhead">
  <span class="rid">{champ['run_id']}</span>
  <span class="tag">{champ['family']} · {champ['aggregation']} ·
        {champ['n_positions']} holdings</span>
</div>

<div class="stats">
  <div>Net IR<b class="hl">{champ['net_ir']:.2f}</b></div>
  <div>Gross IR<b>{champ['gross_ir']:.2f}</b></div>
  <div>Tracking error<b>{champ['te']:.1f}%</b></div>
  <div>Turnover<b>{champ['turnover']}%</b></div>
  <div>Max cash<b>{champ['max_cash']:.1f}%</b></div>
  <div>Signal coverage<b>{champ['coverage']:.0%}</b></div>
  <div>Seed IR range<b>{champ['seed_range']:.2f}</b></div>
</div>

<div class="panel" style="margin-bottom:26px">
  <h3>Net of costs vs the 50/50 benchmark</h3>
  <p>Gross is recorded but never plotted — only the net line is the deliverable.</p>
  {figs[1]}
</div>

<div class="grid2">
  <div class="panel"><h3>Rolling 12-month excess return</h3>
    <p>How long the strategy can stay behind.</p>{figs[2]}</div>
  <div class="panel"><h3>Active drawdown</h3>
    <p>Peak-to-trough on the excess return stream.</p>{figs[3]}</div>
  <div class="panel"><h3>Rolling tracking error</h3>
    <p>Dashed line is the 6% veto threshold.</p>{figs[4]}</div>
  <div class="panel"><h3>Turnover and cumulative cost</h3>
    <p>Cost drag as its own series, not buried in the return.</p>{figs[5]}</div>
</div>

<h2><span class="n">3</span>What the portfolio is actually doing</h2>
<p class="lede">Positions are ETFs, but the decisions are exposures. These two
  views are where the claim that 30 holdings tackle distinct risks gets checked
  — or falsified.</p>
<div class="grid2">
  <div class="panel"><h3>Active weight by risk axis</h3>
    <p>Aggregated from instrument weights through the characteristic map.</p>
    {figs[6]}</div>
  <div class="panel"><h3>Active risk decomposition</h3>
    <p>A large idiosyncratic share means the exposures aren't the story.</p>
    {figs[7]}</div>
</div>

<h2><span class="n">4</span>Is the result real?</h2>
<p class="lede">The search tested many signals, so the best IR is a maximum
  over many draws. These two panels are the check on that.</p>
<div class="grid2">
  <div class="panel"><h3>Rank IC by signal family</h3>
    <p>HAC bands account for overlapping weekly observations. Grey where the
       band spans zero.</p>{figs[8]}</div>
  <div class="panel"><h3>Realised IR against the search null</h3>
    <p>Block bootstrap on shuffled signals, same search width.</p>
    {figs[9]}</div>
</div>

<div class="locked">
  <b>Holdout 2020–2026 is locked.</b> It opens once, on the run you take to
  production. Unlocking is recorded in the decision log with who and when.
</div>

<footer>
  Research OS mock · synthetic data, fixed seed 20260905 · rendered from
  views.py, which the Streamlit app also imports.
</footer>

</div></body></html>"""

    with open(path, "w") as fh:
        fh.write(html)
    return path


if __name__ == "__main__":
    print(build())
