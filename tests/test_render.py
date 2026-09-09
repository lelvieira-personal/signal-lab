"""
The render layer, and the SUBSTRATE section 12 constraints on it.

The constraints are tested rather than trusted: "gross IR is never plotted" is
the kind of rule that survives exactly as long as nobody adds a chart.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "render")]

import views as v  # noqa: E402


def test_veto_legend_covers_every_veto_and_reads_params(params):
    legend = v.veto_legend(params)
    from vetoes import VETOES

    assert {name for name, _ in legend} == set(VETOES)
    assert "150%" in dict(legend)["turnover"]
    assert "6.0%" in dict(legend)["tracking_error"]
    assert "p95" in dict(legend)["tracking_error"]
    assert "18.0%" in dict(legend)["active_drawdown"]


def test_leaderboard_puts_survivors_first_then_objective():
    runs = [
        {"run_id": "A", "net_ir": 0.10, "passed": True, "verdicts": {}},
        {"run_id": "B", "net_ir": 0.90, "passed": False, "verdicts": {"turnover": False}},
        {"run_id": "C", "net_ir": 0.40, "passed": True, "verdicts": {}},
    ]
    rows = v.leaderboard_table(runs)
    assert [r["run_id"] for r in rows] == ["C", "A", "B"]


def test_failed_runs_stay_visible_with_their_veto():
    """SUBSTRATE section 12: failed runs stay visible with the veto that stopped them."""
    runs = [
        {
            "run_id": "B",
            "net_ir": 0.9,
            "passed": False,
            "verdicts": {"lookahead": True, "turnover": False, "cash": False},
        }
    ]
    rows = v.leaderboard_table(runs)
    assert len(rows) == 1, "a failed run is not filtered out"
    assert v.first_failed_veto(rows[0], ["lookahead", "turnover", "cash"]) == "turnover"


def test_runs_with_no_metrics_do_not_crash_the_table():
    rows = v.leaderboard_table([{"run_id": "X", "passed": False, "verdicts": {}}])
    assert rows[0]["net_ir"] is None


def test_run_summary_stats_show_cost_drag_never_gross_ir():
    """decisions/0004: the drag carries the diagnostic, gross carries the temptation."""
    stats = v.run_summary_stats({"net_ir": 0.31, "gross_ir": 0.55, "te": 4.2, "cost_drag": 0.24})
    labels = {s["label"].lower() for s in stats}
    assert not any("gross" in label for label in labels)
    assert "cost drag" in labels


def test_holdout_panel_reports_locked_and_shows_no_metric(params):
    panel = v.holdout_panel(params)
    assert panel["locked"] is True
    assert "2020-01-01" in panel["title"]
    assert not re.search(r"\d\.\d\d", panel["body"]), "no metric appears while locked"


# --- the reports themselves --------------------------------------------------


def test_synthetic_report_renders(tmp_path, params):
    from static_report import build

    out = build(tmp_path / "syn.html", synthetic=True, params=params)
    html = Path(out).read_text(encoding="utf-8")
    assert "Synthetic data." in html, "a mock report must announce itself"
    assert "Leaderboard" in html
    assert "Holdout" in html and "locked" in html
    assert params.params_hash[:12] in html, "the report states which params produced it"


def test_synthetic_report_shows_all_ten_vetoes(tmp_path, params):
    from static_report import build

    html = Path(build(tmp_path / "syn.html", synthetic=True, params=params)).read_text("utf-8")
    from vetoes import VETOES

    for name in VETOES:
        assert name in html, f"veto {name} is not shown on the report"


def test_synthetic_report_never_plots_gross_ir(tmp_path, params):
    """
    The rule that is easiest to break by accident.

    Checked against the whole rendered document, chart JSON included, because a
    plotly trace named "Gross IR" would not appear anywhere else.
    """
    from static_report import build

    html = Path(build(tmp_path / "syn.html", synthetic=True, params=params)).read_text("utf-8")
    assert "gross_ir" not in html.lower().replace("gross is recorded", "")
    assert "Gross IR<" not in html


def test_empty_store_renders_a_report_rather_than_failing(tmp_path, params):
    from static_report import build

    out = build(
        tmp_path / "empty.html", synthetic=False, db_path=tmp_path / "empty.db", params=params
    )
    html = Path(out).read_text(encoding="utf-8")
    assert "No runs recorded" in html
    assert "Veto set" in html, "the veto set is live even with no runs"


def test_report_from_a_store_with_runs(tmp_path, params, store):
    from static_report import build

    from signal_lab.results.store import Verdict

    for i, (ir, ok) in enumerate([(0.42, True), (0.61, False)]):
        rid = f"R-{i}"
        store.record_run(
            rid,
            status="completed",
            data_snapshot_hash="h",
            family="trend",
            aggregation="shrunk z-score mean",
            params=params,
        )
        store.record_metrics(
            rid, {"net_ir": ir, "te": 4.1, "turnover": 120, "max_cash": 8.0, "n_positions": 24}
        )
        store.record_verdicts(
            rid,
            {
                name: Verdict(ok or name != "turnover", "detail")
                for name in ("turnover", "cash", "lookahead")
            },
        )

    out = build(tmp_path / "store.html", synthetic=False, db_path=store.db_path, params=params)
    html = Path(out).read_text(encoding="utf-8")
    assert "R-0" in html and "R-1" in html
    assert "Synthetic data." not in html, "a store-backed report must not claim to be a mock"
    assert "0.42" in html


def test_streamlit_app_imports_the_same_views():
    """
    The app must not grow its own figure code, or the two renderers drift.
    """
    source = (REPO_ROOT / "render" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "import views as v" in source
    assert "plotly.graph_objects" not in source, "figures belong in views.py"
    assert "go.Figure" not in source


def test_streamlit_app_offers_no_sort_control():
    """SUBSTRATE section 12: the leaderboard has one sort, the objective."""
    source = (REPO_ROOT / "render" / "streamlit_app.py").read_text(encoding="utf-8")
    for control in ("st.selectbox", "st.radio", "sort_by", "column_order"):
        assert control not in source, f"{control} would let a reader re-rank the leaderboard"


def test_deploy_stub_exists_and_lists_open_questions():
    text = (REPO_ROOT / "DEPLOY.md").read_text(encoding="utf-8")
    assert "confirm" in text.lower()
    assert "Entrypoint" in text
