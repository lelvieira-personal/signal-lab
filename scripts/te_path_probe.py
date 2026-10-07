#!/usr/bin/env python3
"""
Where does the trailing-3y TE overrun live in time, and why?

`decisions/0027` section 2 left the TE budget / TE veto question open and the
first Bloomberg audit (A-20260917-020949) forced it: 40 of 48 base cells fail
the TE veto, `te_p95_to_budget` median 1.13 and max 1.43, while the SAME cells
report a bias statistic of 0.92 to 1.01 -- a risk model that looks calibrated.

Those two facts are consistent in two ways, and the honest fix differs:

  ESTIMATOR   a trailing-3y p95 is the upper tail of a noisy statistic and the
              overruns are scattered through the sample. Then the veto gates
              sampling error, which is the structure `decisions/0026` removed
              for drawdown, and the ex-ante budget plus the bias statistic is
              the replacement.

  CLUSTERING  active vol clusters, the overruns sit in one or two episodes, and
              a full-sample bias of 1.00 is the average of a hot stretch and a
              cold one. Then the overrun is a real property of the book in
              stress and retiring the veto hides it.

A full-sample bias statistic cannot tell these apart, because it is one number
over 16 years. This walks the same quantities through time instead.

Two readings, both per rebalance date:

  --mode realised   `path.tracking_error()`, the rolling 156-week annualised
                    std of active returns that the veto takes its p95 from.
                    Uses `run_cell`, which already returns the path, so nothing
                    in `src/` changes.

  --mode exante     adds `te_ex_ante` and the shrinkage intensity from
                    `rule.diagnostics`, which `run_cell` does not return. This
                    replicates `run_cell`'s body to keep the rule alive. With
                    both series the bias statistic -- std(r_t / sigma_ex_ante)
                    -- can be cut by period instead of read once.

Writes one CSV a cell plus `summary.md` under
`results/audit/_probe/<run-id>/`, and nothing to the results store: like the
audit, the planted signal is a lookahead by construction, so this is a
measurement of the ruler and never reaches the leaderboard (SUBSTRATE
sections 2 and 10).

Resumable -- a cell whose CSV is already there is skipped -- so a short-lived
shell can walk the list in pieces. `--cache` pickles the assembled universe
outside the repo so each piece reloads it in a second instead of re-reading the
vendor workbook; the cache is derived vendor data and belongs off the repo.

    python scripts/te_path_probe.py --mode exante --cells 0.05:13:0,0.20:13:0
    python scripts/te_path_probe.py --report --run-id TE-20260917-bbg1
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

REPO = Path(__file__).resolve().parent.parent
GFC_FIRST, GFC_LAST = "2008-01-01", "2009-12-31"
# A trailing-3y window ENDING in this span contains some of 2008-09.
WINDOW_TOUCHING_GFC = ("2008-01-01", "2012-12-31")


def _universe(cache: Path, source: str, params):
    """The audit universe, from the pickle when it is there."""
    from signal_lab.audit.universe import get_universe

    if cache.exists():
        with cache.open("rb") as fh:
            return pickle.load(fh)  # noqa: S301 -- our own file, written below
    universe = get_universe(source, params)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with cache.open("wb") as fh:
        pickle.dump(universe, fh, protocol=5)
    return universe


def _cell_realised(universe, cell, params):
    """`run_cell` already hands back the path; the TE series is on it."""
    import pandas as pd

    from signal_lab.audit.ladder import run_cell

    row, path = run_cell(universe, cell, params)
    frame = pd.DataFrame(
        {
            "te_trailing_3y": path.tracking_error(),
            "active_return": path.active_returns,
        }
    )
    return row, frame


def _cell_exante(universe, cell, params):
    """`run_cell`'s body, kept open so `rule.diagnostics` survives it."""
    import pandas as pd

    from signal_lab.audit.ladder import (
        _OptimiserRule,
        _plant,
        audit_cost_model,
        risk_calibration,
    )
    from signal_lab.harness.engine import constant_exposures, run_walk_forward

    solver = str(params.get("audit.solver", "auto"))
    signal = _plant(universe, cell)
    rule = _OptimiserRule(universe, signal, cell, params, solver)
    exposures = constant_exposures(pd.DataFrame(0.0, index=universe.holdable, columns=["f0"]))
    path = run_walk_forward(
        universe.engine_panel(),
        rule,
        universe.benchmark_weekly,
        exposures,
        cost_model=audit_cost_model(universe, params, cell.cost_multiplier),
        params=params,
        rebalance_day=str(params.get("audit.rebalance_day", "FRI")),
        cash_instrument=universe.cash[0] if len(universe.cash) == 1 else None,
    )
    diag = pd.DataFrame(rule.diagnostics).set_index("date")
    te = path.tracking_error()
    frame = pd.DataFrame(
        {
            "te_ex_ante": diag["te_ex_ante"],
            "te_trailing_3y": te.reindex(diag.index),
            "active_return": path.active_returns.reindex(diag.index),
            "shrinkage": diag["shrinkage"],
        }
    )
    budget = float(params.require("constraints.tracking_error.max_trailing_3y"))
    row = {
        "net_ir": path.information_ratio(),
        "te_p95": float(te.dropna().quantile(0.95)),
        "te_ex_ante_mean": float(diag["te_ex_ante"].mean()),
    }
    row.update(
        risk_calibration(
            path.active_returns,
            diag["te_ex_ante"],
            rule.ppy,
            budget,
            te_p95=row["te_p95"],
            active_vol=float(path.active_returns.std() * (rule.ppy**0.5)),
            ex_ante_mean=row["te_ex_ante_mean"],
        )
    )
    return row, frame


def _md(frame) -> str:
    """A markdown table without pulling `tabulate` into the locked env."""
    head = [str(frame.index.name or "")] + [str(c) for c in frame.columns]
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for idx, row in frame.iterrows():
        cells = [str(idx)] + [
            "" if v != v else (f"{v:g}" if isinstance(v, float) else str(v)) for v in row
        ]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def report(out: Path, budget: float) -> str:
    """Split the overrun by period, which is the whole point of the probe."""
    import numpy as np
    import pandas as pd

    lines: list[str] = []
    rows, years = [], {}
    for path in sorted(out.glob("ic*.csv")):
        name = path.stem
        d = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
        te = d["te_trailing_3y"].dropna()
        touching = (te.index >= WINDOW_TOUCHING_GFC[0]) & (te.index <= WINDOW_TOUCHING_GFC[1])
        clean = te[~touching]
        entry = {
            "cell": name,
            "p95_all": te.quantile(0.95),
            "p95_no_gfc": clean.quantile(0.95),
            "share_over_all": (te > budget).mean(),
            "share_over_no_gfc": (clean > budget).mean(),
            "peak": str(te.idxmax().date()),
        }
        if "te_ex_ante" in d:
            sigma = d["te_ex_ante"].shift(1)
            ok = sigma.notna() & d["active_return"].notna() & (sigma > 1e-4)
            z = d.loc[ok, "active_return"] / (sigma[ok] / np.sqrt(52.0))
            entry["bias_full"] = z.std()
            by = z.groupby(z.index.year).std()
            entry["bias_2008"] = by.get(2008, float("nan"))
            entry["bias_2010_14"] = by.loc[2010:2014].mean()
            years[name] = pd.DataFrame(
                {
                    "bias": by,
                    "realised_vol": d.loc[ok, "active_return"].groupby(d.loc[ok].index.year).std()
                    * np.sqrt(52.0),
                    "ex_ante": sigma[ok].groupby(sigma[ok].index.year).mean(),
                    "shrinkage": d.loc[ok, "shrinkage"].groupby(d.loc[ok].index.year).mean(),
                }
            )
        rows.append(entry)
        years.setdefault(name, None)

    frame = pd.DataFrame(rows).set_index("cell")
    frame.index.name = "cell"
    lines.append(f"# TE path probe -- budget {budget:.3f}\n")
    lines.append(
        "`p95_no_gfc` drops every trailing-3y window that contains any of "
        f"{GFC_FIRST[:7]}..{GFC_LAST[:7]}, i.e. every window ending in "
        f"{WINDOW_TOUCHING_GFC[0][:7]}..{WINDOW_TOUCHING_GFC[1][:7]}.\n"
    )
    lines.append("## Per cell\n")
    lines.append(_md(frame.round(4)))
    for name, table in years.items():
        if table is None:
            continue
        lines.append(f"\n## {name} -- by year\n")
        lines.append(_md(table.round(3)))
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("realised", "exante"), default="exante")
    ap.add_argument("--source", default="bloomberg")
    ap.add_argument("--run-id", default="TE-" + time.strftime("%Y%m%d"))
    ap.add_argument("--cache", default="/tmp/universe_bloomberg.pkl")
    ap.add_argument("--cells", default="", help="ic:horizon:seed,ic:horizon:seed,...")
    ap.add_argument(
        "--vol-halflife",
        type=float,
        default=None,
        help="weeks; volatilities exponentially weighted, correlation keeps the window",
    )
    ap.add_argument(
        "--vol-overlay",
        choices=("per_series", "scalar"),
        default="per_series",
        help="per_series moves composition too; scalar moves only the risk level",
    )
    ap.add_argument("--build-cache-only", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args(argv)

    from signal_lab.audit.ladder import AuditCell
    from signal_lab.params import get_params

    params = get_params()
    budget = float(params.require("constraints.tracking_error.max_trailing_3y"))
    out = REPO / "results" / "audit" / "_probe" / args.run_id
    out.mkdir(parents=True, exist_ok=True)

    if args.report:
        text = report(out, budget)
        (out / "summary.md").write_text(text, encoding="utf-8")
        print(text)
        return 0

    universe = _universe(Path(args.cache), args.source, params)
    if args.build_cache_only:
        print("universe cached", flush=True)
        return 0

    runner = _cell_exante if args.mode == "exante" else _cell_realised
    for spec in [s for s in args.cells.split(",") if s.strip()]:
        ic_s, h_s, seed_s = spec.split(":")
        cell = AuditCell(
            ic=float(ic_s),
            horizon=int(h_s),
            seed=int(seed_s),
            vol_halflife=args.vol_halflife,
            vol_overlay=args.vol_overlay,
        )
        name = f"ic{float(ic_s):g}_h{int(h_s)}_s{int(seed_s)}"
        if args.vol_halflife is not None:
            name = f"{name}_vhl{args.vol_halflife:g}"
            if args.vol_overlay != "per_series":
                name = f"{name}{args.vol_overlay}"
        dest = out / f"{name}.csv"
        if dest.exists():
            print(f"{name}: already there", flush=True)
            continue
        started = time.time()
        row, frame = runner(universe, cell, params)
        frame.index.name = "date"
        frame.to_csv(dest)
        te = frame["te_trailing_3y"].dropna()
        print(
            f"{name}: {time.time() - started:.0f}s net_ir={row['net_ir']:.3f} "
            f"te_p95={row['te_p95']:.4f} bias={row['bias_stat']:.3f} "
            f"share_over_budget={(te > budget).mean():.3f}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
