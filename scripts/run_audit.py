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


def main(argv=None) -> int:
    import pandas as pd

    from signal_lab.audit.breadth import effective_breadth
    from signal_lab.audit.ladder import grid_cells, run_cell
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
    cells = grid_cells(params, args.lean)
    if not args.quiet:
        print(
            f"ruler audit {run_id}: {args.source}, {len(universe.holdable)} holdable series, "
            f"{len(universe.audit_dates())} rebalances from {universe.first_audit_date.date()}, "
            f"{len(cells)} cells",
            flush=True,
        )

    rows = []
    for i, cell in enumerate(cells, start=1):
        row, _ = run_cell(universe, cell, params, args.solver)
        rows.append(row)
        if not args.quiet:
            print(
                f"  [{i:>3}/{len(cells)}] {cell.key():<34} net IR {row['net_ir']:+.3f}  "
                f"TE p95 {row['te_p95']:.1%}  turnover {row['turnover_annual']:.0%}  "
                f"{row['seconds']:.1f}s",
                flush=True,
            )
    table = pd.DataFrame(rows)

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
        print((out / "ruler.md").read_text(encoding="utf-8").split("## Required IC")[1][:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
