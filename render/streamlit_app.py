"""
Streamlit renderer. Same views, same sources, same constraints.

    streamlit run render/streamlit_app.py -- --synthetic

This file contains no figure code. Every chart comes from views.py and every
row from sources.py, which is what stops the shared HTML and the deployed app
from drifting apart. If a chart needs changing it changes in views.py and both
renderers get it.

SUBSTRATE section 12 applies here exactly as it does to the static report: one
sort, failures visible with their veto, gross IR never plotted, no holdout
metrics until unlocked. There is deliberately no sort control on the table.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "src"), str(REPO_ROOT), str(REPO_ROOT / "render")]

import views as v  # noqa: E402
from sources import get_source  # noqa: E402


def parse_args(argv=None):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--db", default=None)
    known, _ = parser.parse_known_args(argv if argv is not None else sys.argv[1:])
    return known


def main() -> None:
    import streamlit as st

    from signal_lab.params import get_params

    args = parse_args()
    params = get_params()
    st.set_page_config(page_title="Signal Lab", layout="wide")

    source = get_source(
        synthetic=args.synthetic, **({"db_path": args.db} if args.db and not args.synthetic else {})
    )
    data = source.load()

    st.title("Signal Lab — run browser")
    st.caption(
        f"Read-only browser over {data.label}. Nothing here changes a portfolio. "
        f"Params {params.params_version} · {params.params_hash[:12]}"
    )

    if data.is_synthetic:
        st.warning(
            "Synthetic data. Every number below is generated from a fixed seed so the "
            "layout can be reviewed. No market data, no signals, no backtest, no result.",
            icon="⚠️",
        )

    cols = st.columns(5)
    cols[0].metric("Experiments", data.n_runs)
    cols[1].metric("Survived all vetoes", data.n_passed)
    cols[2].metric("Development window", f"{data.dev_start} → {data.dev_end}")
    holdout = v.holdout_panel(params)
    cols[3].metric("Holdout", "locked" if holdout["locked"] else "unlocked")
    cols[4].metric("Rebalance", f"Weekly, {params.get('constraints.rebalance.day', 'FRI')}")

    st.subheader("Veto set")
    st.caption(
        "Fixed before the cycle ran, read live from params/vetoes.yaml. "
        "None of these are advisory and none is tuned per run."
    )
    for name, label in v.veto_legend(params):
        st.markdown(f"- **{name}** — {label}")

    if not data.runs:
        st.info("No runs recorded yet. The results store is empty.")
        st.markdown(f"**{holdout['title']}** {holdout['body']}")
        return

    te_cap = float(params.require("vetoes.tracking_error.max_trailing_3y")) * 100

    st.subheader("Leaderboard")
    st.caption(
        "Survivors first, then by the pre-registered objective. There is no other sort: "
        "sorting by anything else is selection."
    )
    rows = v.leaderboard_table(data.runs)
    order = [name for name, _ in v.veto_legend(params)]
    table = [
        {
            "Run": r["run_id"],
            "Signal family": r["family"],
            "Aggregation": r["aggregation"],
            "Net IR": r["net_ir"],
            "TE %": r["te"],
            "Turnover %": r["turnover"],
            "Max cash %": r["max_cash"],
            "Holdings": r["n_positions"],
            "Stopped by": "" if r["passed"] else v.first_failed_veto(r, order),
        }
        for r in rows
    ]
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.plotly_chart(v.ir_vs_te_scatter(data.runs, te_cap=te_cap), use_container_width=True)

    detail = data.detail
    if not detail or "dates" not in detail:
        st.info("No run detail to show yet: the champion run has no artifacts.")
        st.markdown(f"**{holdout['title']}** {holdout['body']}")
        return

    champ = data.champion
    st.subheader(f"Run detail — {champ['run_id']}")
    stat_cols = st.columns(5)
    for i, stat in enumerate(v.run_summary_stats(champ)[:5]):
        stat_cols[i].metric(stat["label"], stat["value"])

    st.plotly_chart(v.cumulative_vs_benchmark(detail), use_container_width=True)
    left, right = st.columns(2)
    left.plotly_chart(v.rolling_excess(detail), use_container_width=True)
    right.plotly_chart(v.active_drawdown(detail), use_container_width=True)
    left.plotly_chart(v.rolling_te(detail, cap=te_cap), use_container_width=True)
    right.plotly_chart(v.turnover_and_cost(detail), use_container_width=True)
    left.plotly_chart(v.active_weights_area(detail), use_container_width=True)
    right.plotly_chart(v.risk_decomposition(detail), use_container_width=True)
    left.plotly_chart(v.ic_by_family(detail), use_container_width=True)
    right.plotly_chart(v.null_distribution(detail, champ["net_ir"]), use_container_width=True)

    st.markdown(f"**{holdout['title']}** {holdout['body']}")


if __name__ == "__main__":
    main()
