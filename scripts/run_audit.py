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
    if (~is_base).any():
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
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )
    if not args.quiet:
        print(by_rung.to_string(index=False))
        if paired is not None:
            print(paired.to_string(index=False))
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
        KNEE_GRID,
        baseline_cells,
        grid_cells,
        knee_cells,
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
        "baseline cells at the IC rungs between 0.20 and the oracle (h13)",
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
