"""
Where the report gets its rows.

Two sources behind one interface:

  * StoreSource reads the results store. This is the real one.
  * SyntheticSource regenerates the mock (render/mock_data.py) so the report can
    be built and reviewed with no runs present, which is the whole of phase 0.

The `--synthetic` flag on static_report.py chooses between them. The flag exists
so that a report built from mock data cannot be mistaken for one built from
results: the synthetic source sets `is_synthetic`, and the report renders a
banner it is not possible to switch off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ReportData:
    """Everything a report needs, from either source."""

    runs: list[dict[str, Any]]
    detail: dict[str, Any] | None
    champion: dict[str, Any] | None
    is_synthetic: bool
    label: str
    dev_start: str
    dev_end: str
    n_runs: int = 0
    n_passed: int = 0
    notes: list[str] = field(default_factory=list)


class SyntheticSource:
    """The mock. Fixed seed, no market data, no signals, no backtest."""

    is_synthetic = True

    def __init__(self, params=None):
        from signal_lab.params import get_params

        self.params = params or get_params()

    def load(self) -> ReportData:
        import mock_data as md

        runs, dates = md.build_runs()
        champion = next((r for r in runs if r["passed"]), runs[0] if runs else None)
        detail = md.build_detail(champion, dates) if champion else None
        return ReportData(
            runs=runs,
            detail=detail,
            champion=champion,
            is_synthetic=True,
            label="synthetic mock, fixed seed",
            dev_start=str(self.params.require("data.windows.dev_start")),
            dev_end=str(self.params.require("data.windows.dev_end")),
            n_runs=len(runs),
            n_passed=sum(r["passed"] for r in runs),
            notes=[
                "Every number and chart is randomly generated from a fixed seed so the "
                "layout can be reviewed. No market data, no signals, no backtest."
            ],
        )


class StoreSource:
    """
    The results store.

    Returns an empty ReportData when there are no runs, rather than raising:
    an empty leaderboard is the correct picture of a lab that has not run
    anything, and the report says so.
    """

    is_synthetic = False

    def __init__(self, db_path=None, artifacts_dir=None, params=None):
        from signal_lab.params import get_params
        from signal_lab.results.store import DEFAULT_ARTIFACTS, DEFAULT_DB, ResultsStore

        self.params = params or get_params()
        self.store = ResultsStore(
            db_path or DEFAULT_DB, artifacts_dir or DEFAULT_ARTIFACTS, params=self.params
        )

    def load(self) -> ReportData:
        frame = self.store.list_runs()
        dev_start = str(self.params.require("data.windows.dev_start"))
        dev_end = str(self.params.require("data.windows.dev_end"))

        if frame.empty:
            return ReportData(
                runs=[],
                detail=None,
                champion=None,
                is_synthetic=False,
                label="results store",
                dev_start=dev_start,
                dev_end=dev_end,
                notes=["No runs recorded yet. The store is empty."],
            )

        # Validation runs exercise the harness on a planted path. They are not
        # results about markets and must never rank -- but they are reported in
        # the header, because "the pipeline was last proven on <date>" is worth
        # knowing and silently dropping rows is how a leaderboard starts lying.
        all_runs = frame.to_dict("records")
        validation = [r for r in all_runs if r.get("status") == "validation"]
        runs = [r for r in all_runs if r.get("status") != "validation"]
        for r in runs:
            r.setdefault("net_ir", None)
            r["passed"] = bool(r.get("passed"))

        passed = [r for r in runs if r["passed"] and r.get("net_ir") is not None]
        champion = max(passed, key=lambda r: r["net_ir"]) if passed else None
        detail = self._detail(champion) if champion else None

        return ReportData(
            runs=runs,
            detail=detail,
            champion=champion,
            is_synthetic=False,
            label="results store",
            dev_start=dev_start,
            dev_end=dev_end,
            n_runs=len(runs),
            n_passed=sum(r["passed"] for r in runs),
            notes=([] if champion else ["No run has survived the veto set yet."])
            + (
                [
                    f"Pipeline last validated {validation[-1]['ts'][:10]} on a planted "
                    f"synthetic path (IR recovery error "
                    f"{validation[-1].get('ir_recovery_error', float('nan')):.1e}). "
                    f"Validation runs are excluded from the leaderboard."
                ]
                if validation
                else []
            ),
        )

    def _detail(self, run: dict[str, Any]) -> dict[str, Any] | None:
        """
        Assemble a run detail from its parquet artifacts.

        Returns None when the artifacts are absent, and the report then renders
        the leaderboard alone rather than inventing a chart.
        """
        artifacts = self.store.load_artifacts(run["run_id"])
        if not artifacts:
            return None
        return {"artifacts": artifacts, "run": run}


def get_source(synthetic: bool = False, **kwargs):
    return SyntheticSource(**kwargs) if synthetic else StoreSource(**kwargs)
