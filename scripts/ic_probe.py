#!/usr/bin/env python3
"""
The standardisation probe: what does the ruler's IC label buy on real data?

The first Bloomberg ruler audit (A-20260917-020949, 3 seeds) came back with a
ladder that barely responds to IC -- mean net IR 0.35 at IC 0.02 and 0.37 at
IC 0.20 at h=4 -- while the IC = 1 oracle responded normally (1.93). Three
explanations fit that, and this probe separates them before eight hours go into
a ten-seed rerun of the same measurement:

  A. THE LABEL. The planted IC is a POOLED correlation, and the truth it is
     planted against (forward active return per unit of risk, benchmark not
     removed cross-sectionally) carries a common, same-sign component. A book
     spends the cross-section. If most of the truth's variance is common, an
     IC 0.20 rung hands the book far less than 0.20 of usable forecast.
     Measured here by `common_share` and by three readings of the realised IC.

  B. THE METRIC. `realised_ic_cross_sectional` is a per-date RANK correlation,
     which removes the common component by construction, so a low value is
     partly an artefact of the reading rather than a fact about the signal.
     Measured here by the Pearson readings beside it.

  C. THE COVARIANCE. The frictionless book is inv(Sigma) alpha, and on 95 real
     series its bias statistic ran 1.33 to 1.56 against 1.21 on the synthetic
     panel: it takes 33 to 56 per cent more risk than it is sized for. That
     alone flattens IR. Measured here by running the frictionless ladder in
     both standardisation modes and reading the slope and the bias together.

What it does, in three stages, cheapest first:

  1. PANEL DIAGNOSTICS, no solver, seconds. The truth's common share by
     horizon, and the realised IC of a planted signal read four ways, in both
     standardisation modes.
  2. THE FRICTIONLESS LADDER, both modes, every IC and horizon, `--seeds`
     seeds. A linear solve a week: the whole family is minutes, and it is where
     the anomaly is sharpest (IR is not supposed to be flat in IC here).
  3. BASE CELLS, optional (`--with-base`), both modes, at one horizon and two
     ICs. The constrained book through the real solver, engine and cost model,
     to confirm stage 2 carries into the mandate. About 90 s a cell.

Writes `results/audit/_probe/<stamp>/` -- probe.md, cells.csv, diagnostics.json
-- and nothing to the results store. Like the audit, the planted signal is a
lookahead by construction: this is a measurement of the ruler, not a run, and
it never reaches the leaderboard (SUBSTRATE sections 2 and 10).

    python scripts/ic_probe.py --source bloomberg                  # stages 1-2
    python scripts/ic_probe.py --source bloomberg --with-base      # stages 1-3

It is also RESUMABLE, which is what lets a short-lived shell run it in pieces
(Cowork's local sandbox kills a process when the call returns, so no single
step may outlive one call). Each stage appends to `cells.jsonl` in the run
directory and can be run on its own; `--stage report` assembles what is there.

    python scripts/ic_probe.py --source bloomberg --stage 1 --run-id P-x
    python scripts/ic_probe.py --source bloomberg --stage 2 --chunk 1/8 --run-id P-x
    ...
    python scripts/ic_probe.py --source bloomberg --stage 3 --run-id P-x
    python scripts/ic_probe.py --stage report --run-id P-x

`--universe-cache` pickles the assembled universe outside the repo so each
piece reloads it in a second instead of re-reading the workbook. The cache is
derived vendor data: keep it off the repo and off any shared path.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import _bootstrap  # noqa: F401


def _fmt(x: float, nd: int = 3) -> str:
    return "—" if x != x else f"{x:.{nd}f}"


def _plain(value):
    """JSON-safe: numpy scalars, timestamps and NaN out of a cell row."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return str(value)
    return None if as_float != as_float else as_float


def _universe(args, params, kwargs, get_universe, say=None):
    """The audit universe, from `--universe-cache` when it is there.

    Assembling it re-reads the vendor workbook, which is the expensive part of a
    short call. The pickle is derived vendor data: it belongs outside the repo.
    """
    import pickle

    cache = Path(args.universe_cache) if args.universe_cache else None
    if cache and cache.exists():
        with cache.open("rb") as fh:
            return pickle.load(fh)  # noqa: S301 -- our own file, written below
    universe = get_universe(args.source, params, **kwargs)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        with cache.open("wb") as fh:
            pickle.dump(universe, fh, protocol=5)
        if say:
            say(f"universe cached at {cache}")
    return universe


def main(argv=None) -> int:
    import pandas as pd

    from signal_lab.audit.ladder import FRICTIONLESS, AuditCell, empirical_breadth, run_cell
    from signal_lab.audit.report import run_id_now
    from signal_lab.audit.signals import (
        CROSS_SECTIONAL,
        POOLED,
        plant_signal,
        realised_ic,
        truth_decomposition,
    )
    from signal_lab.audit.universe import get_universe
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="bloomberg", choices=["synthetic", "bloomberg"])
    parser.add_argument("--seeds", type=int, default=10, help="seeds per frictionless cell")
    parser.add_argument("--with-base", action="store_true", help="stage 3: constrained cells")
    parser.add_argument("--base-horizon", type=int, default=13)
    parser.add_argument("--base-ics", default="0.05,0.20")
    parser.add_argument("--base-seeds", type=int, default=3)
    parser.add_argument("--out", default=None, help="override results/audit/_probe")
    parser.add_argument(
        "--stage",
        default="all",
        choices=["all", "1", "2", "3", "report"],
        help="run one stage into a run directory, or assemble the report from what is there",
    )
    parser.add_argument("--chunk", default=None, help="stage 2 only: i/n, run the i-th slice")
    parser.add_argument(
        "--universe-cache",
        default=None,
        help="pickle the assembled universe here and reuse it; keep it outside the repo",
    )
    parser.add_argument("--run-id", default=None, help="write into (or resume) this run directory")
    parser.add_argument("--start", default=None, help="synthetic only: clip the panel, for tests")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    params = get_params()
    ic_grid = [float(x) for x in params.require("audit.ic_grid")]
    horizons = [int(h) for h in params.require("audit.horizon_weeks")]
    modes = [POOLED, CROSS_SECTIONAL]
    run_id = args.run_id or run_id_now().replace("A-", "P-")
    out = Path(args.out or "results/audit/_probe") / run_id
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stage = args.stage
    cells_jsonl = out / "cells.jsonl"

    def append_rows(new_rows: list[dict]) -> None:
        with cells_jsonl.open("a", encoding="utf-8") as fh:
            for row in new_rows:
                fh.write(json.dumps({k: _plain(v) for k, v in row.items()}) + "\n")

    def load_rows() -> pd.DataFrame:
        if not cells_jsonl.exists():
            return pd.DataFrame()
        seen, kept = set(), []
        for line in cells_jsonl.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["key"] not in seen:  # a re-run chunk replaces nothing; first wins
                seen.add(row["key"])
                kept.append(row)
        return pd.DataFrame(kept)

    universe = None
    if stage != "report":
        kwargs = {"start": args.start} if (args.source == "synthetic" and args.start) else {}
        universe = _universe(
            args, params, kwargs, get_universe, say=print if not args.quiet else None
        )
    weekly = None if universe is None else universe.weekly[universe.holdable]
    say = (lambda *a: None) if args.quiet else (lambda *a: print(*a, flush=True))
    if universe is not None:
        say(
            f"probe {run_id}: {args.source}, {len(universe.holdable)} series, "
            f"{len(universe.audit_dates())} rebalances, seeds {args.seeds}"
        )

    # --- stage 1: the panel, no solver ------------------------------------
    diagnostics: list[dict] = []
    if stage in ("all", "1"):
        say("\nstage 1: panel diagnostics")
    horizons_stage1 = horizons if stage in ("all", "1") else []
    for horizon in horizons_stage1:
        for mode in modes:
            for ic in ic_grid:
                signal = plant_signal(
                    weekly,
                    universe.benchmark_weekly,
                    ic=ic,
                    horizon=horizon,
                    seed=0,
                    vol_window=universe.window,
                    standardise=mode,
                )
                row = {"horizon": horizon, "standardise": mode, "ic": ic}
                row.update({f"ic_{k}": v for k, v in realised_ic(signal).items()})
                row.update(truth_decomposition(signal))
                diagnostics.append(row)
                say(
                    f"  h{horizon:>2} {mode:<16} ic {ic:.2f}  "
                    f"pooled {_fmt(row['ic_pooled'])}  "
                    f"xs-pearson {_fmt(row['ic_cross_sectional_pearson'])}  "
                    f"xs-demeaned {_fmt(row['ic_cross_sectional_demeaned'])}  "
                    f"xs-rank {_fmt(row['ic_cross_sectional'])}  "
                    f"common share {_fmt(row['common_share'], 2)}"
                )
    if diagnostics:
        (out / "diagnostics.json").write_text(
            json.dumps([{k: _plain(v) for k, v in r.items()} for r in diagnostics], indent=2),
            encoding="utf-8",
        )
    diag = (
        pd.DataFrame(diagnostics)
        if diagnostics
        else (
            pd.read_json(out / "diagnostics.json")
            if (out / "diagnostics.json").exists()
            else pd.DataFrame()
        )
    )

    # --- stage 2: the frictionless ladder, both modes ----------------------
    rows: list[dict] = []
    if stage in ("all", "2"):
        cells = [
            AuditCell(ic=ic, horizon=h, seed=s, tag=FRICTIONLESS, standardise=mode)
            for mode in modes
            for h in horizons
            for ic in ic_grid
            for s in range(args.seeds)
        ]
        if args.chunk:
            i_chunk, n_chunk = (int(x) for x in args.chunk.split("/"))
            cells = [c for j, c in enumerate(cells) if j % n_chunk == i_chunk - 1]
            say(f"\nstage 2 [chunk {i_chunk}/{n_chunk}]: {len(cells)} frictionless cells")
        else:
            say(f"\nstage 2: {len(cells)} frictionless cells")
        for i, cell in enumerate(cells, start=1):
            row, _ = run_cell(universe, cell, params)
            row["standardise"] = cell.standardise
            rows.append(row)
            if i % 20 == 0 or i == len(cells):
                say(f"  [{i:>4}/{len(cells)}] {cell.key()}  net IR {row['net_ir']:+.3f}")
        append_rows(rows)

    # --- stage 3: base cells, optional ------------------------------------
    if args.with_base or stage == "3":
        base_ics = [float(x) for x in args.base_ics.split(",")]
        base_cells = [
            AuditCell(ic=ic, horizon=args.base_horizon, seed=s, standardise=mode)
            for mode in modes
            for ic in base_ics
            for s in range(args.base_seeds)
        ]
        say(f"\nstage 3: {len(base_cells)} base cells (h{args.base_horizon})")
        for i, cell in enumerate(base_cells, start=1):
            row, _ = run_cell(universe, cell, params)
            row["standardise"] = cell.standardise
            rows.append(row)
            say(
                f"  [{i:>2}/{len(base_cells)}] {cell.key()}  net IR {row['net_ir']:+.3f}  "
                f"TE p95 {row['te_p95']:.1%}  {row['seconds']:.0f}s"
            )
            append_rows([row])

    if stage not in ("all", "report"):
        say(f"\nstage {stage} done -> {out}/cells.jsonl  ({time.time() - started:.0f}s)")
        return 0

    table = load_rows() if cells_jsonl.exists() else pd.DataFrame(rows)
    if table.empty:
        say("nothing to report yet: run stages 1-3 first")
        return 1
    table.to_csv(out / "cells.csv", index=False)

    # --- the report --------------------------------------------------------
    panel = (
        f"{len(universe.holdable)} series, {len(universe.audit_dates())} rebalances, "
        if universe is not None
        else ""
    )
    lines = [
        f"# Standardisation probe — {run_id}",
        "",
        f"Source **{args.source}**, {panel}params `{params.params_version}`, "
        f"{args.seeds} seeds per frictionless cell.",
        "",
        "> Planted signals are forward returns with noise: a lookahead by construction. "
        "This measures the ruler, not a strategy.",
        "",
        "## 1. What kind of information the truth is",
        "",
        "`common share` is the share of the truth's variance that moves every instrument "
        "the same way on a date — the part a long-only book can express only by moving "
        "between asset classes and cash. The rest is selection.",
        "",
        "| horizon | common share |",
        "|---|---|",
    ]
    for h in horizons if not diag.empty else []:
        sub = diag[(diag["horizon"] == h) & (diag["standardise"] == POOLED)]
        lines.append(f"| {h} | {_fmt(float(sub['common_share'].mean()), 2)} |")
    lines += [
        "",
        "## 2. The IC, read four ways",
        "",
        "`pooled` is what the construction targets. `xs pearson` is the per-date "
        "correlation on levels, `xs demeaned` removes each date's mean from both series "
        "(what a book with no net exposure can spend), `xs rank` is the audit's existing "
        "reading. A gap between `pooled` and `xs demeaned` is the label overstating what "
        "the book receives.",
        "",
        "| mode | horizon | planted IC | pooled | xs pearson | xs demeaned | xs rank |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in diag.iterrows() if not diag.empty else []:
        lines.append(
            f"| {r['standardise']} | {int(r['horizon'])} | {r['ic']:.2f} | "
            f"{_fmt(r['ic_pooled'])} | {_fmt(r['ic_cross_sectional_pearson'])} | "
            f"{_fmt(r['ic_cross_sectional_demeaned'])} | {_fmt(r['ic_cross_sectional'])} |"
        )

    lines += ["", "## 3. The frictionless ladder in both modes", ""]
    fric = table[table["tag"] == FRICTIONLESS]
    for mode in modes:
        sub = fric[fric["standardise"] == mode]
        breadth = empirical_breadth(sub)
        lines += [
            f"### {mode}",
            "",
            "| IC \\ h | " + " | ".join(str(h) for h in horizons) + " |",
            "|---" * (len(horizons) + 1) + "|",
        ]
        for ic in ic_grid:
            cellsr = [
                _fmt(float(sub[(sub["ic"] == ic) & (sub["horizon"] == h)]["net_ir"].mean()), 2)
                for h in horizons
            ]
            lines.append(f"| {ic:.2f} | " + " | ".join(cellsr) + " |")
        lines += [
            "",
            "| horizon | IR per unit IC | empirical breadth | bias statistic | seed sd of IR |",
            "|---|---|---|---|---|",
        ]
        for h in horizons:
            b = breadth[breadth["horizon"] == h]
            g = sub[sub["horizon"] == h]
            lines.append(
                f"| {h} | {_fmt(float(b['ir_per_unit_ic'].iloc[0]), 2) if len(b) else '—'} | "
                f"{_fmt(float(b['empirical_breadth'].iloc[0]), 1) if len(b) else '—'} | "
                f"{_fmt(float(g['bias_stat'].mean()), 2)} | "
                f"{_fmt(float(g.groupby('ic')['net_ir'].std().mean()), 2)} |"
            )
        lines.append("")

    base = table[table["tag"] == "base"]
    if len(base):
        lines += [
            "## 4. Base cells — the constrained book",
            "",
            "| mode | IC | horizon | mean net IR | seed sd | TE p95/budget | bias |",
            "|---|---|---|---|---|---|---|",
        ]
        for mode in modes:
            sub = base[base["standardise"] == mode]
            for (ic, h), g in sub.groupby(["ic", "horizon"]):
                lines.append(
                    f"| {mode} | {ic:.2f} | {int(h)} | {_fmt(float(g['net_ir'].mean()), 2)} | "
                    f"{_fmt(float(g['net_ir'].std()), 2)} | "
                    f"{_fmt(float(g['te_p95_to_budget'].mean()), 2)} | "
                    f"{_fmt(float(g['bias_stat'].mean()), 2)} |"
                )
        lines.append("")

    lines += [
        "## How to read this",
        "",
        "- If `common share` is large and `xs demeaned` is far below `pooled`, the ladder's "
        "IC label is not what the book receives (explanation A). The fix is a decision about "
        "what the rung means, not a bug fix.",
        "- If `xs rank` is far below `xs pearson` but `xs demeaned` tracks `pooled`, the old "
        "reading was the artefact (explanation B).",
        "- If both modes give a flat ladder while the bias statistic sits well above 1.00, the "
        "covariance is eating the signal before the constraints ever see it (explanation C).",
        "- Seed sd beside each slope says whether any of it is resolvable at this seed count.",
        "",
        f"Run time {time.time() - started:.0f} s. Cells in `cells.csv`, "
        "stage-1 detail in `diagnostics.json`.",
        "",
    ]
    (out / "probe.md").write_text("\n".join(lines), encoding="utf-8")
    say(f"\nwrote {out}/  ({time.time() - started:.0f}s)")
    if not args.quiet:
        print("\n" + "\n".join(lines[: lines.index("## 3. The frictionless ladder in both modes")]))
    json.dump(
        {
            "run_id": run_id,
            "source": args.source,
            "seeds": args.seeds,
            "n_cells": int(len(table)),
            "seconds": round(time.time() - started, 1),
            "params_version": params.params_version,
            "panel_hash": universe.panel_hash() if universe is not None else None,
        },
        (out / "meta.json").open("w", encoding="utf-8"),
        indent=2,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
