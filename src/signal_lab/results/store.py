"""
The results store: append-only SQLite plus parquet artifacts.

Every run records the params version, the params hash, the data snapshot hash
and the seed, so any row on the leaderboard can be traced back to the exact
configuration and panel that produced it. That is the whole point of the store;
a metric with no provenance is an anecdote.

Append-only is enforced by database triggers (see schema.sql), not by this
module being careful. Writing the same run twice raises rather than overwriting.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from signal_lab.params import Params, get_params

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = REPO_ROOT / "results" / "runs.db"
DEFAULT_ARTIFACTS = REPO_ROOT / "results" / "artifacts"
SCHEMA = Path(__file__).with_name("schema.sql")


class StoreError(Exception):
    """A write the store refuses, including any attempt to rewrite history."""


@dataclass(frozen=True)
class Verdict:
    """
    The result of one veto. SUBSTRATE section 10.

    `detail` is required in spirit even when passing: "turnover 112% of a 150%
    ceiling" tells the reader how close the run was, which a bare True does not.
    """

    passed: bool
    detail: str = ""
    veto: str = ""

    def as_row(self, veto: str | None = None) -> dict[str, Any]:
        return {"veto": veto or self.veto, "passed": int(self.passed), "detail": self.detail}


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class ResultsStore:
    """
    Append-only run history.

    Usage:
        store = ResultsStore()
        store.record_run(run_id, hypothesis_id=..., status="completed", ...)
        store.record_verdicts(run_id, {"turnover": Verdict(True, "112% of 150%")})
        store.record_metrics(run_id, {"net_ir": 0.31})
        store.write_artifact(run_id, "weights", weights_frame)
    """

    def __init__(
        self,
        db_path: Path | str = DEFAULT_DB,
        artifacts_dir: Path | str = DEFAULT_ARTIFACTS,
        params: Params | None = None,
    ):
        self.db_path = Path(db_path)
        self.artifacts_dir = Path(artifacts_dir)
        self.params = params
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # --- plumbing -----------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    # --- writes -------------------------------------------------------------

    def record_run(
        self,
        run_id: str,
        *,
        status: str,
        data_snapshot_hash: str,
        hypothesis_id: str | None = None,
        family: str | None = None,
        aggregation: str | None = None,
        seed: int | None = None,
        killed_by: str | None = None,
        cost_tokens: int | None = None,
        cost_usd: float | None = None,
        params: Params | None = None,
        ts: str | None = None,
    ) -> str:
        """
        Insert one run. Raises if the run_id already exists: a run is a fact,
        and a fact is not amended in place.
        """
        params = params or self.params or get_params()
        row = (
            run_id,
            ts or utc_now(),
            hypothesis_id,
            family,
            aggregation,
            params.params_version,
            params.params_hash,
            data_snapshot_hash,
            seed,
            status,
            killed_by,
            cost_tokens,
            cost_usd,
        )
        try:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO runs (run_id, ts, hypothesis_id, family, aggregation, "
                    "params_version, params_hash, data_snapshot_hash, seed, status, "
                    "killed_by, cost_tokens, cost_usd) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    row,
                )
        except sqlite3.IntegrityError as exc:
            raise StoreError(f"run {run_id!r} already recorded; the store is append-only") from exc
        return run_id

    def record_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        """
        Insert metrics for a run.

        Gross IR is welcome here: SUBSTRATE section 3 records it and only forbids
        ranking on it, and section 12 forbids plotting it. The render layer, not
        the store, enforces that.
        """
        self._require_run(run_id)
        rows = [
            (run_id, name, None if value is None else float(value))
            for name, value in metrics.items()
        ]
        try:
            with self.connect() as conn:
                conn.executemany("INSERT INTO metrics (run_id, name, value) VALUES (?,?,?)", rows)
        except sqlite3.IntegrityError as exc:
            raise StoreError(f"metric already recorded for run {run_id!r}") from exc

    def record_verdicts(self, run_id: str, verdicts: dict[str, Verdict]) -> None:
        """Insert every veto verdict for a run, passes as well as failures."""
        self._require_run(run_id)
        rows = [(run_id, name, int(v.passed), v.detail) for name, v in verdicts.items()]
        try:
            with self.connect() as conn:
                conn.executemany(
                    "INSERT INTO verdicts (run_id, veto, passed, detail) VALUES (?,?,?,?)", rows
                )
        except sqlite3.IntegrityError as exc:
            raise StoreError(f"verdict already recorded for run {run_id!r}") from exc

    def record_transition(
        self,
        hypothesis_id: str,
        from_state: str,
        to_state: str,
        run_id: str | None = None,
        detail: str = "",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO hypothesis_transitions (ts, hypothesis_id, from_state, to_state, "
                "run_id, detail) VALUES (?,?,?,?,?,?)",
                (utc_now(), hypothesis_id, from_state, to_state, run_id, detail),
            )

    def _require_run(self, run_id: str) -> None:
        with self.connect() as conn:
            found = conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if not found:
            raise StoreError(f"no such run {run_id!r}; record_run first")

    # --- artifacts ----------------------------------------------------------

    def artifact_dir(self, run_id: str) -> Path:
        path = self.artifacts_dir / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_artifact(self, run_id: str, name: str, frame: pd.DataFrame) -> Path:
        """
        Write one artifact as parquet. Artifacts are not committed to git;
        they are regenerable from the run's params and snapshot hash.
        """
        path = self.artifact_dir(run_id) / f"{name}.parquet"
        out = frame.copy()
        if not isinstance(out.index, pd.RangeIndex):
            out = out.reset_index()
        out.columns = [str(c) for c in out.columns]
        out.to_parquet(path, index=False)
        return path

    def load_artifacts(self, run_id: str) -> dict[str, pd.DataFrame]:
        """Every artifact for a run, keyed by name. Empty dict if there are none."""
        path = self.artifacts_dir / run_id
        if not path.exists():
            return {}
        return {f.stem: pd.read_parquet(f) for f in sorted(path.glob("*.parquet"))}

    # --- reads --------------------------------------------------------------

    def list_runs(
        self,
        hypothesis_id: str | None = None,
        status: str | None = None,
        since: str | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Runs with their metrics and verdicts attached.

        Deliberately returns runs in insertion order, not sorted by any metric.
        Sorting is the render layer's job and SUBSTRATE section 12 allows exactly
        one sort: the pre-registered objective. A store that offered `order_by`
        would be offering selection.
        """
        clauses, args = [], []
        if hypothesis_id:
            clauses.append("hypothesis_id = ?")
            args.append(hypothesis_id)
        if status:
            clauses.append("status = ?")
            args.append(status)
        if since:
            clauses.append("ts >= ?")
            args.append(since)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM runs{where} ORDER BY ts, run_id"
        if limit:
            sql += f" LIMIT {int(limit)}"

        with self.connect() as conn:
            runs = pd.read_sql_query(sql, conn, params=args)
            metrics = pd.read_sql_query("SELECT * FROM metrics", conn)
            verdicts = pd.read_sql_query("SELECT * FROM verdicts", conn)

        if runs.empty:
            return runs

        wide = (
            metrics.pivot(index="run_id", columns="name", values="value")
            if not metrics.empty
            else pd.DataFrame(index=pd.Index([], name="run_id"))
        )
        runs = runs.merge(wide, left_on="run_id", right_index=True, how="left")

        if verdicts.empty:
            runs["verdicts"] = [{} for _ in range(len(runs))]
            runs["verdict_details"] = [{} for _ in range(len(runs))]
        else:
            passed_map = {
                rid: dict(zip(g["veto"], g["passed"].astype(bool), strict=True))
                for rid, g in verdicts.groupby("run_id")
            }
            detail_map = {
                rid: dict(zip(g["veto"], g["detail"].fillna(""), strict=True))
                for rid, g in verdicts.groupby("run_id")
            }
            runs["verdicts"] = runs["run_id"].map(lambda r: passed_map.get(r, {}))
            runs["verdict_details"] = runs["run_id"].map(lambda r: detail_map.get(r, {}))

        runs["passed"] = runs["verdicts"].map(lambda d: bool(d) and all(d.values()))
        return runs

    def transitions(self, hypothesis_id: str | None = None) -> pd.DataFrame:
        sql = "SELECT * FROM hypothesis_transitions"
        args: list[Any] = []
        if hypothesis_id:
            sql += " WHERE hypothesis_id = ?"
            args.append(hypothesis_id)
        sql += " ORDER BY id"
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=args)

    def summary(self) -> dict[str, Any]:
        with self.connect() as conn:
            n_runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            n_killed = conn.execute(
                "SELECT COUNT(*) FROM runs WHERE killed_by IS NOT NULL"
            ).fetchone()[0]
            tokens = conn.execute("SELECT COALESCE(SUM(cost_tokens),0) FROM runs").fetchone()[0]
            usd = conn.execute("SELECT SUM(cost_usd) FROM runs").fetchone()[0]
            last = conn.execute("SELECT MAX(ts) FROM runs").fetchone()[0]
        return {
            "n_runs": n_runs,
            "n_killed": n_killed,
            "cost_tokens": tokens,
            "cost_usd": usd,
            "last_run_ts": last,
        }


def new_run_id(prefix: str = "R", when: datetime | None = None, suffix: str = "") -> str:
    """A sortable run id. Collisions raise at insert; they are not resolved silently."""
    when = when or datetime.now(UTC)
    stamp = when.strftime("%Y%m%dT%H%M%S")
    return f"{prefix}-{stamp}{('-' + suffix) if suffix else ''}"


def dumps(obj: Iterable | dict) -> str:
    return json.dumps(obj, default=str, sort_keys=True)
