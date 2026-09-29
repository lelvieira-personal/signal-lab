#!/usr/bin/env python3
"""
Run the ruler audit. decisions/0023, phase 2.5.

    python scripts/run_audit.py --source synthetic --lean     # the validation run
    python scripts/run_audit.py --source bloomberg            # the real one

Writes `results/audit/<run_id>/` -- cells.csv, summary.json, breadth.json,
ruler.md, ruler.html -- and nothing to the results store. The planted signals
are forward returns with noise, a lookahead by construction, so an audit path
is not a run and never reaches the leaderboard (SUBSTRATE sections 2 and 10).
"""

from __future__ import annotations

import argparse
import sys
import time

import _bootstrap  # noqa: F401


def _read_cells(run_dir):
    """
    A run's cells.csv. Runs before HANDOFF task 25 have no `shuffle` column; every
    baseline in them is a truth shuffle, so the column is filled in as that.
    """
    import pandas as pd

    cells = pd.read_csv(run_dir / "cells.csv")
    if "shuffle" not in cells.columns:
        cells["shuffle"] = ""
    return cells


def _power_by_cell(table, universe, params, out_root):
    """
    HANDOFF task 25: per (horizon, ic, seed), the live net IR from the knee run,
    the mean and sd of the score-shuffled net IRs, and the live IR's rank among
    all of them (1 = highest). The live run's hashes are compared with this
    run's, because a rank against a live IR from another panel or other params
    means nothing.
    """
    import json
    from pathlib import Path

    import pandas as pd

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    live_dir = Path(out_root) / POWER_LIVE_RUN
    hashes = {"live_run": POWER_LIVE_RUN, "found": live_dir.exists()}
    live = None
    if live_dir.exists():
        live_summary = json.loads((live_dir / "summary.json").read_text(encoding="utf-8"))
        hashes["panel_hash_match"] = live_summary.get("panel_hash") == universe.panel_hash()
        hashes["params_hash_match"] = live_summary.get("params_hash") == params.params_hash
        cells = _read_cells(live_dir)
        live = cells[~cells["baseline"].astype(bool) & (cells["tag"] == "base")]
        truth_twin = cells[
            cells["baseline"].astype(bool) & cells["shuffle"].fillna("").isin(["", "truth"])
        ]
    rows = []
    for (h, ic, seed), grp in table.groupby(["horizon", "ic", "seed"]):
        shuffled = grp["net_ir"].astype(float)
        row = {
            "horizon": int(h),
            "ic": float(ic),
            "seed": int(seed),
            "n_perms": int(len(shuffled)),
            "shuffled_mean": float(shuffled.mean()),
            "shuffled_sd": float(shuffled.std(ddof=1)),
            "live_net_ir": float("nan"),
            "truth_twin_net_ir": float("nan"),
            "live_rank": None,
            "of": int(len(shuffled)) + 1,
        }
        if live is not None:
            match = live[
                (live["horizon"] == h)
                & (live["ic"].round(6) == round(float(ic), 6))
                & (live["seed"] == seed)
            ]
            if len(match) == 1:
                value = float(match["net_ir"].iloc[0])
                row["live_net_ir"] = value
                row["live_rank"] = 1 + int((shuffled > value).sum())
            twin = truth_twin[
                (truth_twin["horizon"] == h)
                & (truth_twin["ic"].round(6) == round(float(ic), 6))
                & (truth_twin["seed"] == seed)
            ]
            if len(twin) == 1:
                row["truth_twin_net_ir"] = float(twin["net_ir"].iloc[0])
        rows.append(row)
    return hashes, pd.DataFrame(rows)


def _power10_preflight(cells, universe, params, out_root):
    """
    HANDOFF task 30: the grid's live and truth-shuffle twins are the knee run's, so
    every seed and rung must be there and its hashes must match this run's. Checked
    before any cell so a mismatch costs seconds, not six hours. Returns the reason
    to stop, or None.
    """
    import json
    from pathlib import Path

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    live_dir = Path(out_root) / POWER_LIVE_RUN
    if not live_dir.exists():
        return f"{live_dir} not found"
    live_summary = json.loads((live_dir / "summary.json").read_text(encoding="utf-8"))
    if live_summary.get("panel_hash") != universe.panel_hash():
        return f"panel_hash differs from {POWER_LIVE_RUN}"
    if live_summary.get("params_hash") != params.params_hash:
        return f"params_hash differs from {POWER_LIVE_RUN}"
    table = _read_cells(live_dir)
    for ic, seed in sorted({(c.ic, c.seed) for c in cells}):
        at = (
            (table["horizon"] == 13)
            & (table["ic"].round(6) == round(ic, 6))
            & (table["seed"] == seed)
        )
        live = at & ~table["baseline"].astype(bool) & (table["tag"] == "base")
        twin = at & table["baseline"].astype(bool) & table["shuffle"].fillna("").isin(["", "truth"])
        if live.sum() != 1 or twin.sum() != 1:
            return f"{POWER_LIVE_RUN} lacks the live or truth-twin cell at ic={ic}, seed={seed}"
    return None


def _friction_preflight(cells, universe, params, out_root):
    """
    HANDOFF task 32: the 10 bp arm's identity check needs `POWER_LIVE_RUN`'s live
    cell at every (ic, seed) the friction grid runs. Checked before any cell so a
    mismatch costs seconds, not the better part of two hours. Returns the reason
    to stop, or None.
    """
    import json
    from pathlib import Path

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    live_dir = Path(out_root) / POWER_LIVE_RUN
    if not live_dir.exists():
        return f"{live_dir} not found"
    live_summary = json.loads((live_dir / "summary.json").read_text(encoding="utf-8"))
    if live_summary.get("panel_hash") != universe.panel_hash():
        return f"panel_hash differs from {POWER_LIVE_RUN}"
    if live_summary.get("params_hash") != params.params_hash:
        return f"params_hash differs from {POWER_LIVE_RUN}"
    table = _read_cells(live_dir)
    for ic, seed in sorted({(c.ic, c.seed) for c in cells}):
        at = (
            (table["horizon"] == 13)
            & (table["ic"].round(6) == round(ic, 6))
            & (table["seed"] == seed)
        )
        live = at & ~table["baseline"].astype(bool) & (table["tag"] == "base")
        if live.sum() != 1:
            return f"{POWER_LIVE_RUN} lacks the live cell at ic={ic}, seed={seed}"
    return None


def _friction_by_cell(table, universe, params, out_root):
    """
    HANDOFF task 32. Three pieces: the 10 bp arm checked cell by cell against
    `POWER_LIVE_RUN`'s live twin; median and range over seeds per (ic,
    shadow_coefficient); and, paired by seed, the 20 bp and 40 bp arms' net IR
    less the 10 bp arm's.
    """
    import json
    from pathlib import Path

    import pandas as pd

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    live_dir = Path(out_root) / POWER_LIVE_RUN
    hashes = {"live_run": POWER_LIVE_RUN, "found": live_dir.exists()}
    ten_bp = None
    if live_dir.exists():
        live_summary = json.loads((live_dir / "summary.json").read_text(encoding="utf-8"))
        hashes["panel_hash_match"] = live_summary.get("panel_hash") == universe.panel_hash()
        hashes["params_hash_match"] = live_summary.get("params_hash") == params.params_hash
        cells = _read_cells(live_dir)
        live = cells[~cells["baseline"].astype(bool) & (cells["tag"] == "base")]
        rows = []
        for _, row in table[table["shadow_coefficient"] == 10.0].iterrows():
            match = live[
                (live["horizon"] == row["horizon"])
                & (live["ic"].round(6) == round(float(row["ic"]), 6))
                & (live["seed"] == row["seed"])
            ]
            rows.append(
                {
                    "ic": float(row["ic"]),
                    "seed": int(row["seed"]),
                    "friction_net_ir": float(row["net_ir"]),
                    "knee_net_ir": float(match["net_ir"].iloc[0])
                    if len(match) == 1
                    else float("nan"),
                    "found": len(match) == 1,
                }
            )
        ten_bp = pd.DataFrame(rows)
        ten_bp["diff"] = ten_bp["friction_net_ir"] - ten_bp["knee_net_ir"]

    by_arm = (
        table.groupby(["ic", "shadow_coefficient"])
        .agg(
            n=("seed", "count"),
            net_ir_median=("net_ir", "median"),
            net_ir_min=("net_ir", "min"),
            net_ir_max=("net_ir", "max"),
            cost_drag_median=("cost_drag_annual", "median"),
            cost_drag_min=("cost_drag_annual", "min"),
            cost_drag_max=("cost_drag_annual", "max"),
            turnover_annual_median=("turnover_annual", "median"),
            turnover_annual_min=("turnover_annual", "min"),
            turnover_annual_max=("turnover_annual", "max"),
            turnover_rolling_median=("turnover_max_rolling_1y", "median"),
            turnover_rolling_min=("turnover_max_rolling_1y", "min"),
            turnover_rolling_max=("turnover_max_rolling_1y", "max"),
            te_p95_median=("te_p95", "median"),
            te_p95_min=("te_p95", "min"),
            te_p95_max=("te_p95", "max"),
            realised_ic_median=("realised_ic_pooled", "median"),
            realised_ic_min=("realised_ic_pooled", "min"),
            realised_ic_max=("realised_ic_pooled", "max"),
            n_annual_above_200=("turnover_annual", lambda s: int((s > 2.0).sum())),
            n_rolling_above_200=("turnover_max_rolling_1y", lambda s: int((s > 2.0).sum())),
            n_risk_calibration_fails=(
                "veto_detail",
                lambda s: int(s.fillna("").str.contains("risk_calibration").sum()),
            ),
        )
        .reset_index()
    )

    pivot = table.pivot_table(index=["ic", "seed"], columns="shadow_coefficient", values="net_ir")
    paired_rows = []
    for ic, grp in pivot.groupby("ic"):
        for coef in (20.0, 40.0):
            if coef not in grp.columns or 10.0 not in grp.columns:
                continue
            diff = (grp[coef] - grp[10.0]).dropna()
            paired_rows.append(
                {
                    "ic": float(ic),
                    "coefficient": coef,
                    "n": int(len(diff)),
                    "mean_diff": float(diff.mean()),
                    "sd_diff": float(diff.std(ddof=1)) if len(diff) > 1 else float("nan"),
                    "n_positive": int((diff > 0).sum()),
                }
            )
    paired = pd.DataFrame(paired_rows)
    return hashes, ten_bp, by_arm, paired


def _friction_created_preflight(cells, universe, params, out_root):
    """
    HANDOFF task 36: the control is `FRICTION_LIVE_RUN` (task 32's grid, the
    `trailing` form), matched by (ic, seed, shadow_coefficient) -- not the knee
    run, which never carries a `shadow_coefficient` override. Checked before any
    cell so a mismatch costs seconds, not the 1.5-2.5h the grid budgets.
    """
    import json
    from pathlib import Path

    from signal_lab.audit.ladder import FRICTION_LIVE_RUN

    live_dir = Path(out_root) / FRICTION_LIVE_RUN
    if not live_dir.exists():
        return f"{live_dir} not found"
    live_summary = json.loads((live_dir / "summary.json").read_text(encoding="utf-8"))
    if live_summary.get("panel_hash") != universe.panel_hash():
        return f"panel_hash differs from {FRICTION_LIVE_RUN}"
    if live_summary.get("params_hash") != params.params_hash:
        return f"params_hash differs from {FRICTION_LIVE_RUN}"
    table = _read_cells(live_dir)
    for ic, seed, coef in sorted({(c.ic, c.seed, c.shadow_coefficient) for c in cells}):
        at = (
            (table["horizon"] == 13)
            & (table["ic"].round(6) == round(ic, 6))
            & (table["seed"] == seed)
            & (table["shadow_coefficient"].astype(float).round(6) == round(coef, 6))
        )
        live = at & ~table["baseline"].astype(bool) & (table["tag"] == "base")
        if live.sum() != 1:
            return f"{FRICTION_LIVE_RUN} lacks the trailing cell at ic={ic}, seed={seed}, coefficient={coef}"
    return None


def _column_or_nan(frame, name):
    import numpy as np

    return frame[name].astype(float) if name in frame.columns else np.full(len(frame), np.nan)


def _friction_created_by_cell(table, universe, params, out_root):
    """
    HANDOFF task 36. The `created` grid's 60 cells against `FRICTION_LIVE_RUN`'s
    `trailing` control at the same (ic, seed, shadow_coefficient): a cell-by-cell
    merge (not every control column exists in that older run -- see
    `_column_or_nan` -- because `gross_ir` and the autocorrelation and
    `shadow_paid_bps` columns are new in this task), summary by arm for both
    forms, and the paired created-minus-trailing differences.
    """
    import json
    from pathlib import Path

    import pandas as pd

    from signal_lab.audit.ladder import FRICTION_LIVE_RUN

    live_dir = Path(out_root) / FRICTION_LIVE_RUN
    hashes = {"live_run": FRICTION_LIVE_RUN, "found": live_dir.exists()}
    trailing = None
    if live_dir.exists():
        live_summary = json.loads((live_dir / "summary.json").read_text(encoding="utf-8"))
        hashes["panel_hash_match"] = live_summary.get("panel_hash") == universe.panel_hash()
        hashes["params_hash_match"] = live_summary.get("params_hash") == params.params_hash
        cells = _read_cells(live_dir)
        trailing = cells[~cells["baseline"].astype(bool) & (cells["tag"] == "base")].copy()

    metrics = [
        "net_ir",
        "gross_ir",
        "cost_drag_annual",
        "turnover_annual",
        "turnover_p95_rolling_1y",
        "turnover_max_rolling_1y",
        "turnover_per_rebalance_max",
        "turnover_autocorr_lag52",
        "turnover_autocorr_lag53",
        "shadow_bps_mean",
        "shadow_paid_bps_mean",
        "te_p95",
        "realised_ic_pooled",
    ]

    def _by_arm(frame):
        out = frame.copy()
        for m in metrics:
            out[m] = _column_or_nan(out, m)
        agg = {}
        for m in metrics:
            agg[f"{m}_median"] = (m, "median")
            agg[f"{m}_min"] = (m, "min")
            agg[f"{m}_max"] = (m, "max")
        agg["n"] = ("seed", "count")
        agg["n_annual_above_200"] = ("turnover_annual", lambda s: int((s > 2.0).sum()))
        agg["n_rolling_above_200"] = ("turnover_max_rolling_1y", lambda s: int((s > 2.0).sum()))
        agg["n_week_above_150"] = ("turnover_per_rebalance_max", lambda s: int((s > 1.5).sum()))
        agg["n_week_above_195"] = ("turnover_per_rebalance_max", lambda s: int((s > 1.95).sum()))
        agg["n_risk_calibration_fails"] = (
            "veto_detail",
            lambda s: int(s.fillna("").str.contains("risk_calibration").sum()),
        )
        agg["inaccurate_share_max"] = ("inaccurate_share", "max")
        agg["infeasible_te_share_max"] = ("infeasible_te_share", "max")
        agg["n_not_clarabel"] = ("solvers_used", lambda s: int((s.fillna("") != "CLARABEL").sum()))
        return out.groupby(["ic", "shadow_coefficient"]).agg(**agg).reset_index()

    by_arm_created = _by_arm(table)
    by_arm_trailing = _by_arm(trailing) if trailing is not None else None

    paired_rows = []
    if trailing is not None:
        keys = ["ic", "seed", "shadow_coefficient"]
        merged = table.merge(
            trailing[[*keys, "net_ir", "turnover_annual", "turnover_per_rebalance_max"]],
            on=keys,
            suffixes=("_created", "_trailing"),
            how="inner",
        )
        for (ic, coef), grp in merged.groupby(["ic", "shadow_coefficient"]):
            row = {"ic": float(ic), "coefficient": float(coef), "n": int(len(grp))}
            for m in ("net_ir", "turnover_annual", "turnover_per_rebalance_max"):
                diff = grp[f"{m}_created"] - grp[f"{m}_trailing"]
                row[f"{m}_mean_diff"] = float(diff.mean())
                row[f"{m}_sd_diff"] = float(diff.std(ddof=1)) if len(diff) > 1 else float("nan")
                row[f"{m}_n_positive"] = int((diff > 0).sum())
            paired_rows.append(row)
    paired = pd.DataFrame(paired_rows)
    return hashes, by_arm_created, by_arm_trailing, paired


def _write_baseline_run(args, params, universe, table, run_id, out_root, started) -> int:
    """
    A baseline-only run has no base cells, oracle or twin, so the ruler report has
    nothing to say and would fail on it. Write what the run is FOR: the cells, the
    hashes that decide whether a contrast against A-20260919-155557 is valid, and
    the baseline net IR by rung with its seed range (decisions/0036).
    """
    import json
    from pathlib import Path

    out = Path(out_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "cells.csv", index=False)
    is_base = table["baseline"].astype(bool)
    by_rung = (
        table[is_base]
        .groupby(["horizon", "ic"])["net_ir"]
        .agg(mean="mean", min="min", max="max", n="count")
        .reset_index()
    )
    paired = None
    if (~is_base).any() and args.grid not in ("friction", "friction_created"):
        # A run with live cells beside their baselines (the knee grid): the
        # statistic is the seed-paired excess, not either level (SUBSTRATE s3, bar 2).
        from signal_lab.audit.ladder import net_ir_excess

        live = table[~is_base].assign(excess=lambda t: net_ir_excess(table)[t.index])
        grouped = live.groupby(["horizon", "ic"])
        paired = grouped["net_ir"].agg(live_mean="mean", live_min="min", live_max="max")
        paired["baseline_mean"] = by_rung.set_index(["horizon", "ic"])["mean"]
        paired["excess_mean"] = grouped["excess"].mean()
        paired["excess_se"] = grouped["excess"].std(ddof=1) / grouped["excess"].count() ** 0.5
        paired["n"] = grouped["excess"].count()
        paired = paired.reset_index()
    summary = {
        "run_id": run_id,
        "kind": "baseline",
        "grid": args.grid,
        "source": args.source,
        "snapshot_id": universe.panel.snapshot_id,
        "panel_hash": universe.panel_hash(),
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "generated_at": pd_now(),
        "n_cells": len(table),
        "solver": str(table["solver"].iloc[0]),
        "seconds": round(time.time() - started, 1),
        "baseline_net_ir_by_rung": by_rung.to_dict(orient="records"),
    }
    if paired is not None:
        summary["paired_by_rung"] = paired.to_dict(orient="records")
    power = None
    if args.grid in ("power", "power10"):
        hashes, power = _power_by_cell(table, universe, params, out_root)
        summary["power_live_run"] = hashes
        summary["power_by_cell"] = power.to_dict(orient="records")
    friction = None
    if args.grid == "friction":
        hashes, ten_bp, by_arm, paired_seeds = _friction_by_cell(table, universe, params, out_root)
        summary["friction_live_run"] = hashes
        summary["friction_ten_bp_arm"] = ten_bp.to_dict(orient="records")
        summary["friction_by_arm"] = by_arm.to_dict(orient="records")
        summary["friction_paired_by_seed"] = paired_seeds.to_dict(orient="records")
        friction = (ten_bp, by_arm, paired_seeds)
    friction_created = None
    if args.grid == "friction_created":
        hashes, by_arm_created, by_arm_trailing, paired_seeds = _friction_created_by_cell(
            table, universe, params, out_root
        )
        summary["friction_created_live_run"] = hashes
        summary["friction_created_by_arm"] = by_arm_created.to_dict(orient="records")
        if by_arm_trailing is not None:
            summary["friction_trailing_by_arm"] = by_arm_trailing.to_dict(orient="records")
        summary["friction_created_paired_by_seed"] = paired_seeds.to_dict(orient="records")
        friction_created = (hashes, by_arm_created, by_arm_trailing, paired_seeds)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )
    if not args.quiet:
        if args.grid not in ("friction", "friction_created"):
            print(by_rung.to_string(index=False))
        if paired is not None:
            print(paired.to_string(index=False))
        if power is not None:
            print(summary["power_live_run"])
            print(power.to_string(index=False))
        if friction is not None:
            ten_bp, by_arm, paired_seeds = friction
            print(summary["friction_live_run"])
            print("10 bp arm vs the knee run's live twin:")
            print(ten_bp.to_string(index=False))
            print(f"max |diff| = {ten_bp['diff'].abs().max():.6g}")
            print(by_arm.to_string(index=False))
            print(paired_seeds.to_string(index=False))
        if friction_created is not None:
            hashes, by_arm_created, by_arm_trailing, paired_seeds = friction_created
            print(hashes)
            print("created form, by arm:")
            print(by_arm_created.to_string(index=False))
            if by_arm_trailing is not None:
                print("trailing form control (FRICTION_LIVE_RUN), by arm:")
                print(by_arm_trailing.to_string(index=False))
            print("paired created-minus-trailing, by (ic, seed, coefficient):")
            print(paired_seeds.to_string(index=False))
        print(f"\nwrote {out}/  ({summary['seconds']:.0f}s)")
    return 0


def pd_now() -> str:
    import pandas as pd

    return pd.Timestamp.now("UTC").isoformat(timespec="seconds")


def _write_cell_artifacts(artifacts_root, run_id: str, cell, path) -> int:
    """
    Weights, alpha and the rebalance-date index for one cell, as parquet
    (decisions/0035 s5). `results/artifacts/` is where `STATUS.md` already
    says these live and where the results store's own `write_artifact` puts
    them; the audit writes here directly since it does not go through the
    store. Returns the bytes written, so the caller can report the disk cost.
    """
    from pathlib import Path

    out = Path(artifacts_root) / run_id / cell.key()
    out.mkdir(parents=True, exist_ok=True)
    written = 0
    weights = path.weights.reset_index(names="date")
    weights.to_parquet(out / "weights.parquet", index=False)
    written += (out / "weights.parquet").stat().st_size
    if path.alpha is not None and len(path.alpha):
        alpha = path.alpha.reset_index(names="date")
        alpha.to_parquet(out / "alpha.parquet", index=False)
        written += (out / "alpha.parquet").stat().st_size
    return written


def main(argv=None) -> int:
    import pandas as pd

    from signal_lab.audit.breadth import effective_breadth
    from signal_lab.audit.ladder import (
        AUDIT_GRIDS,
        FRICTION_CREATED_GRID,
        FRICTION_GRID,
        KNEE_GRID,
        POWER10_GRID,
        POWER_GRID,
        baseline_cells,
        friction_cells,
        friction_created_cells,
        grid_cells,
        knee_cells,
        power10_cells,
        power_cells,
        run_cell,
    )
    from signal_lab.audit.report import run_id_now, write_outputs
    from signal_lab.audit.universe import get_universe
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="synthetic", choices=["synthetic", "bloomberg"])
    parser.add_argument(
        "--lean",
        action="store_true",
        help="two ICs, two horizons, one seed, no stress cells -- shape and runtime, not the bar",
    )
    parser.add_argument(
        "--grid",
        default=None,
        choices=list(AUDIT_GRIDS),
        help="run only the block-shuffled baseline cells of decisions/0036: "
        "baseline-pilot (h13) or baseline (every horizon); or knee, the live and "
        "baseline cells at the IC rungs between 0.20 and the oracle (h13); or power, "
        "20 score-shuffle baselines per knee rung and seed (HANDOFF task 25); or "
        "power10, 20 span-limited score shuffles at IC 0.70 for seeds 0-9 (task 30); or "
        "friction, live cells only at the shadow-cost coefficient 10/20/40 bp (task 32); or "
        "friction_created, the same 60 cells priced with the created-turnover shadow "
        "instead of trailing (task 36, decisions/0040)",
    )
    parser.add_argument("--solver", default=None, help="auto | cvxpy | scipy (default: params)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--out", default=None, help="override results/audit/")
    parser.add_argument("--start", default=None, help="synthetic only: clip the panel, for tests")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    params = get_params()
    target = float(params.require("audit.target_net_ir"))
    run_id = args.run_id or run_id_now()
    out_root = args.out or params.get("audit.output_dir", "results/audit")
    kwargs = {"start": args.start} if (args.source == "synthetic" and args.start) else {}

    started = time.time()
    universe = get_universe(args.source, params, **kwargs)
    if args.grid == KNEE_GRID:
        cells = knee_cells(params)
    elif args.grid == POWER_GRID:
        cells = power_cells(params)
    elif args.grid == POWER10_GRID:
        cells = power10_cells(params)
        problem = _power10_preflight(
            cells, universe, params, args.out or params.get("audit.output_dir", "results/audit")
        )
        if problem:
            print(f"power10 STOPPED before any cell: {problem}", file=sys.stderr)
            return 2
    elif args.grid == FRICTION_GRID:
        cells = friction_cells(params)
        problem = _friction_preflight(
            cells, universe, params, args.out or params.get("audit.output_dir", "results/audit")
        )
        if problem:
            print(f"friction STOPPED before any cell: {problem}", file=sys.stderr)
            return 2
    elif args.grid == FRICTION_CREATED_GRID:
        cells = friction_created_cells(params)
        problem = _friction_created_preflight(
            cells, universe, params, args.out or params.get("audit.output_dir", "results/audit")
        )
        if problem:
            print(f"friction_created STOPPED before any cell: {problem}", file=sys.stderr)
            return 2
    elif args.grid:
        cells = baseline_cells(params, args.grid)
    else:
        cells = grid_cells(params, args.lean)
    if not args.quiet:
        print(
            f"ruler audit {run_id}: {args.source}, {len(universe.holdable)} holdable series, "
            f"{len(universe.audit_dates())} rebalances from {universe.first_audit_date.date()}, "
            f"{len(cells)} cells",
            flush=True,
        )

    from pathlib import Path

    artifacts_root = Path(out_root).parent / "artifacts"
    artifact_bytes = 0
    rows = []
    for i, cell in enumerate(cells, start=1):
        row, path = run_cell(universe, cell, params, args.solver)
        rows.append(row)
        if cell.tag == "base":
            # decisions/0035 s5: base cells at minimum, so the next measurement
            # bug is a re-derivation instead of another multi-hour re-run.
            artifact_bytes += _write_cell_artifacts(artifacts_root, run_id, cell, path)
        if not args.quiet:
            print(
                f"  [{i:>3}/{len(cells)}] {cell.key():<34} net IR {row['net_ir']:+.3f}  "
                f"TE p95 {row['te_p95']:.1%}  turnover {row['turnover_annual']:.0%}  "
                f"inaccurate {row['inaccurate_share']:.1%}  {row['seconds']:.1f}s",
                flush=True,
            )
    table = pd.DataFrame(rows)
    if artifact_bytes and not args.quiet:
        print(f"artifacts: {artifact_bytes / 1e6:.1f} MB under {artifacts_root}/{run_id}/")

    if args.grid:
        return _write_baseline_run(args, params, universe, table, run_id, out_root, started)

    phi = table.groupby("horizon")["signal_phi"].mean().to_dict()
    breadth = effective_breadth(
        universe.weekly[universe.holdable],
        universe.benchmark_weekly,
        sorted({int(c.horizon) for c in cells}),
        signal_phi={int(k): float(v) for k, v in phi.items()},
        periods_per_year=float(params.get("costs.application.weeks_per_year", 52)),
    )

    meta = {
        "run_id": run_id,
        "source": args.source,
        "snapshot_id": universe.panel.snapshot_id,
        "panel_hash": universe.panel_hash(),
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "generated_at": pd.Timestamp.now("UTC").isoformat(timespec="seconds"),
        "te_budget": float(params.require("constraints.tracking_error.max_trailing_3y")),
        "first_date": str(table["first_date"].iloc[0]),
        "last_date": str(table["last_date"].iloc[0]),
        "n_rebalances": int(table["n_rebalances"].iloc[0]),
        "solver": str(table["solver"].iloc[0]),
        "stress_horizon": int(params.get("audit.stress_horizon_weeks", 13)),
        "lean": bool(args.lean),
        "n_cells": len(cells),
        "seconds": round(time.time() - started, 1),
    }
    out = write_outputs(f"{out_root}/{run_id}", table, breadth, target, meta)
    if not args.quiet:
        print(f"\nwrote {out}/  ({meta['seconds']:.0f}s)")
        text = (out / "ruler.md").read_text(encoding="utf-8")
        start = text.find("## Required IC")
        end = text.find("\n## ", start + 1)
        print(text[start : end if end > 0 else None] if start >= 0 else text[:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
