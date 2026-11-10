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
import os
import sys
import time

import _bootstrap

THREADS = _bootstrap.require_one_thread()


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


def _halflife_preflight(cells, universe, params, out_root):
    """
    HANDOFF task 35: the `vol_halflife=None` h13 arm is the identity check
    against `POWER_LIVE_RUN`'s live cell at every (ic, seed) the grid runs.
    Checked before any cell so a mismatch costs seconds, not 5.5-6 hours.
    Returns the reason to stop, or None.
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


def _parse_halflife_deadline(raw: str | None) -> float | None:
    """`HALFLIFE_DEADLINE` (task 35's amendment), an ISO timestamp with its
    offset, as a unix timestamp -- or None if unset."""
    if not raw:
        return None
    from datetime import datetime

    return datetime.fromisoformat(raw).timestamp()


def _halflife_should_stop(now_ts: float, deadline_ts: float | None, durations: list) -> bool:
    """
    True if starting another cell risks missing `deadline_ts`: now plus 1.5x
    the median cell duration so far (120s before the first cell) would pass
    it. `deadline_ts=None` (the variable unset) never stops early.
    """
    if deadline_ts is None:
        return False
    median = sorted(durations)[len(durations) // 2] if durations else 120.0
    return now_ts + 1.5 * median > deadline_ts


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


def _halflife_by_cell(table, universe, params, out_root):
    """
    HANDOFF task 35 (OWNER-QUEUE B1, L13). Four pieces, built to tolerate a
    deadline-truncated `table` (including zero rows):
    - the h13 `vol_halflife=None` arm checked cell by cell against
      `POWER_LIVE_RUN`'s live twin (the identity check the receipt must stop
      and report on if it fails);
    - per (horizon, halflife) summary statistics, pooled over both ICs and
      separately per IC;
    - the paired net-IR delta of each halflife arm against the `None` control,
      by (ic, seed, horizon), aggregated over seed;
    - every cell flagged for `inaccurate_share > 0.01` or `infeasible_te_share
      > 0`.
    """
    import json
    from pathlib import Path

    import pandas as pd

    from signal_lab.audit.ladder import POWER_LIVE_RUN

    empty_cols = [
        "horizon",
        "halflife_label",
        "n",
        "n_risk_calibration_fails",
        "bias_worst_annual_median",
        "bias_worst_annual_max",
        "n_worst_year_2008",
        "bias_stat_median",
        "te_p95_median",
        "te_p95_to_budget_median",
        "net_ir_median",
        "net_ir_min",
        "net_ir_max",
        "turnover_annual_median",
        "cost_drag_median",
    ]

    hashes = {"live_run": POWER_LIVE_RUN, "found": Path(out_root, POWER_LIVE_RUN).exists()}
    if hashes["found"]:
        live_summary = json.loads(
            (Path(out_root) / POWER_LIVE_RUN / "summary.json").read_text(encoding="utf-8")
        )
        hashes["panel_hash_match"] = live_summary.get("panel_hash") == universe.panel_hash()
        hashes["params_hash_match"] = live_summary.get("params_hash") == params.params_hash

    if table.empty:
        empty = pd.DataFrame(columns=empty_cols)
        flagged_cols = [
            "ic",
            "horizon",
            "seed",
            "vol_halflife",
            "inaccurate_share",
            "infeasible_te_share",
        ]
        return hashes, None, empty, empty, pd.DataFrame(), pd.DataFrame(columns=flagged_cols)

    identity = None
    if hashes["found"]:
        knee = _read_cells(Path(out_root) / POWER_LIVE_RUN)
        knee_live = knee[~knee["baseline"].astype(bool) & (knee["tag"] == "base")]
        none_h13 = table[(table["horizon"] == 13) & table["vol_halflife"].isna()]
        rows = []
        for _, row in none_h13.iterrows():
            match = knee_live[
                (knee_live["ic"].round(6) == round(float(row["ic"]), 6))
                & (knee_live["seed"] == row["seed"])
            ]
            rows.append(
                {
                    "ic": float(row["ic"]),
                    "seed": int(row["seed"]),
                    "halflife_net_ir": float(row["net_ir"]),
                    "knee_net_ir": (
                        float(match["net_ir"].iloc[0]) if len(match) == 1 else float("nan")
                    ),
                    "found": len(match) == 1,
                }
            )
        identity = pd.DataFrame(rows)
        if len(identity):
            identity["diff"] = identity["halflife_net_ir"] - identity["knee_net_ir"]

    work = table.copy()
    work["halflife_label"] = work["vol_halflife"].map(lambda x: "none" if pd.isna(x) else str(x))

    def _summary(extra_keys):
        keys = ["horizon", "halflife_label", *extra_keys]
        return (
            work.groupby(keys)
            .agg(
                n=("seed", "count"),
                n_risk_calibration_fails=(
                    "veto_detail",
                    lambda s: int(s.fillna("").str.contains("risk_calibration").sum()),
                ),
                bias_worst_annual_median=("bias_worst_annual", "median"),
                bias_worst_annual_max=("bias_worst_annual", "max"),
                n_worst_year_2008=("bias_worst_year", lambda s: int((s == 2008).sum())),
                bias_stat_median=("bias_stat", "median"),
                te_p95_median=("te_p95", "median"),
                te_p95_to_budget_median=("te_p95_to_budget", "median"),
                net_ir_median=("net_ir", "median"),
                net_ir_min=("net_ir", "min"),
                net_ir_max=("net_ir", "max"),
                turnover_annual_median=("turnover_annual", "median"),
                cost_drag_median=("cost_drag_annual", "median"),
            )
            .reset_index()
        )

    by_horizon_halflife = _summary([])
    by_horizon_halflife_ic = _summary(["ic"])

    work["hl_key"] = work["vol_halflife"].astype(float).fillna(-1.0)
    pivot = work.pivot_table(index=["ic", "seed", "horizon"], columns="hl_key", values="net_ir")
    paired_rows = []
    if -1.0 in pivot.columns:
        for (ic, horizon), grp in pivot.groupby(["ic", "horizon"]):
            for hl in (13.0, 26.0, 52.0):
                if hl not in grp.columns:
                    continue
                diff = (grp[hl] - grp[-1.0]).dropna()
                if not len(diff):
                    continue
                paired_rows.append(
                    {
                        "ic": float(ic),
                        "horizon": int(horizon),
                        "halflife": hl,
                        "n": int(len(diff)),
                        "mean_diff": float(diff.mean()),
                        "sd_diff": float(diff.std(ddof=1)) if len(diff) > 1 else float("nan"),
                        "n_positive": int((diff > 0).sum()),
                    }
                )
    paired = pd.DataFrame(paired_rows)

    flagged = table[(table["inaccurate_share"] > 0.01) | (table["infeasible_te_share"] > 0)][
        ["ic", "horizon", "seed", "vol_halflife", "inaccurate_share", "infeasible_te_share"]
    ]

    return hashes, identity, by_horizon_halflife, by_horizon_halflife_ic, paired, flagged


def _write_halflife_run(
    args, params, universe, table, run_id, out_root, started, n_cells_total, partial
):
    """
    HANDOFF task 35. Writes `cells.csv` and a summary with the receipt's
    required analytics from whatever cells finished -- the full 240 or a
    deadline-truncated subset (possibly zero). `partial` marks the run
    PARTIAL and records the per-horizon cell count, so the receipt can say
    which horizons are complete.
    """
    import json
    from pathlib import Path

    out = Path(out_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "cells.csv", index=False)

    hashes, identity, by_hh, by_hh_ic, paired, flagged = _halflife_by_cell(
        table, universe, params, out_root
    )
    per_horizon = (
        {int(k): int(v) for k, v in table.groupby("horizon").size().to_dict().items()}
        if len(table)
        else {}
    )
    summary = {
        "run_id": run_id,
        "kind": "halflife",
        "grid": args.grid,
        "status": "PARTIAL" if partial else "COMPLETE",
        "source": args.source,
        "snapshot_id": universe.panel.snapshot_id,
        "panel_hash": universe.panel_hash(),
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "thread_setting": THREADS,
        "generated_at": pd_now(),
        "n_cells": len(table),
        "n_cells_total": n_cells_total,
        "per_horizon_cell_count": per_horizon,
        "solver": str(table["solver"].iloc[0]) if len(table) else None,
        "seconds": round(time.time() - started, 1),
        "halflife_live_run": hashes,
        "halflife_h13_identity": (
            identity.to_dict(orient="records") if identity is not None else None
        ),
        "halflife_by_horizon_halflife": by_hh.to_dict(orient="records"),
        "halflife_by_horizon_halflife_ic": by_hh_ic.to_dict(orient="records"),
        "halflife_paired_by_ic_seed_horizon": paired.to_dict(orient="records"),
        "halflife_flagged_cells": flagged.to_dict(orient="records"),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )
    if not args.quiet:
        print(f"status: {summary['status']}  n_cells={len(table)}/{n_cells_total}")
        print(f"per-horizon cell count: {per_horizon}")
        print(hashes)
        if identity is not None and len(identity):
            print("h13 vol_halflife=None arm vs POWER_LIVE_RUN's live twin:")
            print(identity.to_string(index=False))
            print(f"max |diff| = {identity['diff'].abs().max():.6g}")
        if len(by_hh):
            print(by_hh.to_string(index=False))
        if len(paired):
            print(paired.to_string(index=False))
        if len(flagged):
            print("FLAGGED cells (inaccurate_share > 0.01 or infeasible_te_share > 0):")
            print(flagged.to_string(index=False))
        print(f"\nwrote {out}/  ({summary['seconds']:.0f}s)")
    return 0


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
        "thread_setting": THREADS,
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


def _md_table(frame) -> str:
    """A plain markdown table (no tabulate dependency); floats to three decimals."""

    def cell(value) -> str:
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value)

    head = "| " + " | ".join(map(str, frame.columns)) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([head, rule, *body])


def _pilot_report(summary: dict, table, by_cell) -> str:
    """report.md for a phase-2 pilot run: the table of decisions/0059 G, no pass or fail."""
    lines = [
        f"# Phase-2 pilot {summary['run_id']} ({summary['grid']})",
        "",
        "decisions/0059 G and its addendum of 2026-11-10; HANDOFF task 90. Planted at the axis "
        "level, h = 13, on the development window. **No pass or fail:** the thresholds are the "
        "owner's (decisions/0069 item 2).",
        "",
        f"- source `{summary['source']}`, snapshot `{summary['snapshot_id']}`, panel hash "
        f"`{summary['panel_hash'][:16]}...`",
        f"- params `{summary['params_version']}` (`{summary['params_hash'][:16]}...`), store "
        f"`{summary['store_id']}`, factor set `{summary['factor_set']}` from "
        f"`{summary['estimation_start']}`",
        f"- {summary['n_runs']} runs, {summary['seconds']:.0f} s; per run mean "
        f"{summary['seconds_per_run_mean']:.0f} s, max {summary['seconds_per_run_max']:.0f} s",
        f"- lookahead veto passed on {summary['lookahead_passed']} of {summary['n_runs']} runs",
        "",
        "`excess_positive_share` is the share of seeds whose net IR beats its baseline twin "
        "(the first half of bar 2; the stepdown is not run here). At IC 0 it reads as the "
        "false-pass rate of that half.",
        "",
        "## By expression, planted IC and IC_prior multiplier (means over seeds)",
        "",
        _md_table(by_cell),
        "",
        "## Every run",
        "",
        _md_table(table[PILOT_REPORT_COLUMNS]),
        "",
    ]
    return "\n".join(lines)


PILOT_REPORT_COLUMNS = [
    "key",
    "net_ir",
    "baseline_net_ir",
    "net_ir_excess",
    "transfer",
    "equity_tracking_variance_share",
    "turnover_annual",
    "bias_stat",
    "inaccurate_share",
    "infeasible_te_share",
    "realised_ic_by_column",
    "lookahead_passed",
    "seconds",
]


def _run_phase2_pilot(args, params, run_id: str, out_root: str) -> int:
    """
    `--grid phase2-pilot` / `phase2-pilot-smoke` (HANDOFF task 90, decisions/0059 G and its
    addendum of 2026-11-10). Bloomberg only: the pilot reads the pinned exposure store, and the
    factors are rebuilt with the store's own factor set and estimation start.
    """
    import csv
    import json
    from pathlib import Path

    import pandas as pd
    import run_measurement as RM

    from signal_lab.audit import pilot
    from signal_lab.audit.universe import get_universe
    from signal_lab.characteristics.exposures import ExposureMap
    from vetoes.rules import veto_lookahead

    if args.source != "bloomberg":
        print(
            "the phase-2 pilot runs on --source bloomberg only (it reads the store)",
            file=sys.stderr,
        )
        return 2
    started = time.time()
    universe = get_universe("bloomberg", params)
    exposures = ExposureMap.from_params(params)
    manifest = exposures.store.manifest
    factor_set = str(manifest.get("factor_set", "huber6"))
    estimation_start = str(manifest.get("estimation_start", "dev_start"))
    _, _, ff, _, _ = RM.load_inputs(params, factor_set, estimation_start)
    inputs = pilot.build_inputs(universe, exposures, ff.frame, params)
    if args.grid == pilot.PILOT_DIAG_GRID:
        meta = {
            "snapshot_id": universe.panel.snapshot_id,
            "panel_hash": universe.panel_hash(),
            "factor_set": factor_set,
            "estimation_start": estimation_start,
            "prep_seconds": round(time.time() - started, 1),
        }
        return _run_pilot_diag(args, params, run_id, out_root, inputs, meta, veto_lookahead)
    cells = pilot.pilot_cells(args.grid)
    prep_seconds = time.time() - started
    if not args.quiet:
        print(
            f"phase-2 pilot {run_id}: {args.grid}, {len(cells)} runs, {len(universe.holdable)} "
            f"holdable series, store {params.get('data.characteristics.store_id')}, factors "
            f"{factor_set} from {estimation_start}; inputs {inputs.notes}; prepared in "
            f"{prep_seconds:.0f}s",
            flush=True,
        )

    out = Path(out_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    failure = None
    with open(out / "cells.partial.csv", "w", newline="", encoding="utf-8") as fh:
        writer = None
        for i, cell in enumerate(cells, start=1):
            try:
                row, _, _ = pilot.run_pilot_cell(
                    inputs, cell, params, lookahead_veto=veto_lookahead, solver=args.solver
                )
            except Exception as exc:  # report which run and stop (HANDOFF task 90 step 4)
                failure = f"{cell.key()}: {type(exc).__name__}: {exc}"
                print(f"phase-2 pilot STOPPED at run {i}/{len(cells)}: {failure}", file=sys.stderr)
                break
            rows.append(row)
            if writer is None:
                writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
                writer.writeheader()
            writer.writerow(row)
            fh.flush()
            if not args.quiet:
                print(
                    f"  [{i:>3}/{len(cells)}] {cell.key():<40} net IR {row['net_ir']:+.3f}  "
                    f"turnover {row['turnover_annual']:.0%}  transfer {row['transfer']:+.2f}  "
                    f"lookahead {'ok' if row['lookahead_passed'] else 'FAIL'}  "
                    f"{row['seconds']:.0f}s",
                    flush=True,
                )
    if not rows:
        return 3
    table = pilot.with_excess(pd.DataFrame(rows))
    by_cell = pilot.summarise(pd.DataFrame(rows))
    table.to_csv(out / "cells.csv", index=False)
    summary = {
        "run_id": run_id,
        "kind": "phase2-pilot",
        "grid": args.grid,
        "source": args.source,
        "snapshot_id": universe.panel.snapshot_id,
        "panel_hash": universe.panel_hash(),
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "store_id": params.get("data.characteristics.store_id"),
        "factor_set": factor_set,
        "estimation_start": estimation_start,
        "thread_setting": THREADS,
        "generated_at": pd_now(),
        "n_cells_planned": len(cells),
        "n_runs": len(table),
        "complete": failure is None,
        "failure": failure,
        "prep_seconds": round(prep_seconds, 1),
        "seconds": round(time.time() - started, 1),
        "seconds_per_run_mean": float(table["seconds"].mean()),
        "seconds_per_run_max": float(table["seconds"].max()),
        "lookahead_passed": int(table["lookahead_passed"].sum()),
        "inputs": inputs.notes,
        "by_cell": by_cell.to_dict(orient="records"),
        "runs": table.to_dict(orient="records"),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    (out / "report.md").write_text(_pilot_report(summary, table, by_cell), encoding="utf-8")
    if not args.quiet:
        print(by_cell.to_string(index=False))
        print(f"\nwrote {out}/  ({summary['seconds']:.0f}s)")
    return 0 if failure is None else 3


def _run_pilot_diag(args, params, run_id, out_root, inputs, meta, lookahead_veto) -> int:
    """
    `--grid phase2-pilot-diag` (HANDOFF task 91): why the pilot's views barely move the book.
    Fourteen runs through `run_pilot_cell` (`pilot.diag_cells`), then the tables (a) to (d) and
    the one-date hand check (e). Derived numbers only; nothing is judged.
    """
    import json
    from pathlib import Path

    import numpy as np
    import pandas as pd

    from signal_lab.audit import pilot
    from signal_lab.characteristics.exposures import REGION_COLUMNS
    from signal_lab.measurement.factors import FACTOR_NAMES

    started = time.time()
    cells = pilot.diag_cells()
    out = Path(out_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    rows, kept, failure = [], {}, None
    for i, cell in enumerate(cells, start=1):
        keep: dict = {}
        try:
            row, rule, path = pilot.run_pilot_cell(
                inputs, cell, params, lookahead_veto=lookahead_veto, solver=args.solver, keep=keep
            )
        except Exception as exc:  # report which run and stop
            failure = f"{cell.key()}: {type(exc).__name__}: {exc}"
            print(f"phase-2 diag STOPPED at run {i}/{len(cells)}: {failure}", file=sys.stderr)
            break
        row["te_realised"] = float(path.active_returns.std() * np.sqrt(rule.ppy))
        rows.append(row)
        live_1x = not cell.frictionless and cell.ic == pilot.DIAG_IC
        if cell.zero_scores:
            kept[("noview", cell.expression)] = (rule, path, keep)
        elif live_1x and cell.prior_multiplier == 1.0:
            kept[("ic35", cell.expression)] = (rule, path, keep)
        if not args.quiet:
            print(
                f"  [{i:>2}/{len(cells)}] {cell.key():<44} net IR {row['net_ir']:+.3f}  "
                f"gross IR {row['gross_ir']:+.3f}  turnover {row['turnover_annual']:.0%}  "
                f"transfer {row['transfer']:+.2f}  TE {row['te_ex_ante_mean']:.2%}  "
                f"{row['seconds']:.0f}s",
                flush=True,
            )
    table = pd.DataFrame(rows)
    table.to_csv(out / "cells.csv", index=False)
    if failure is not None:
        (out / "failure.txt").write_text(failure + "\n", encoding="utf-8")
        return 3

    common = ["expression", "net_ir", "transfer", "turnover_annual", "te_ex_ante_mean"]
    common += ["te_realised"]
    noview = table[table["zero_scores"].astype(bool)]
    sized = table[
        ~table["zero_scores"].astype(bool)
        & ~table["frictionless"].astype(bool)
        & (table["ic"] == pilot.DIAG_IC)
    ]
    friction = table[table["frictionless"].astype(bool)]
    table_a = noview[["expression", "net_ir", "te_ex_ante_mean", "te_realised", "te_p95"]]
    table_a = table_a.assign(turnover_annual=noview["turnover_annual"])
    table_b = sized[["ic_prior_multiplier", "ic_prior", *common]]
    table_c = friction[["ic", "gross_ir", *common]]

    exposure_cols = [*FACTOR_NAMES, *REGION_COLUMNS]
    a_exposure, a_variance = {}, {}
    for expression in pilot.AXIS_OF_EXPRESSION:
        reports = kept[("noview", expression)][2]["reports"]
        ae = reports["active_exposure"].astype(float)
        first = [c for c in exposure_cols if c in ae.columns]
        a_exposure[expression] = ae[first + [c for c in ae.columns if c not in first]].mean()
        a_variance[expression] = reports["tracking_variance"].astype(float).mean()
    a_exposure = pd.DataFrame(a_exposure).reset_index(names="column")
    a_variance = pd.DataFrame(a_variance).reset_index(names="factor")

    d_rows, d_detail = [], {}
    for expression in pilot.AXIS_OF_EXPRESSION:
        rule, _, keep = kept[("ic35", expression)]
        arith = pilot.alpha_arithmetic(rule, keep["costs"]).astype(
            {
                c: float
                for c in (
                    "max_abs_alpha_annual_bp",
                    "max_abs_alpha_horizon_bp",
                    "half_spread_bp",
                    "shadow_marginal_bp",
                    "round_trip_bp",
                )
            }
        )
        d_detail[expression] = arith
        d_rows.append(
            {
                "expression": expression,
                "dates": len(arith),
                "alpha_annual_bp_median": arith["max_abs_alpha_annual_bp"].median(),
                "alpha_annual_bp_p90": arith["max_abs_alpha_annual_bp"].quantile(0.9),
                "alpha_13w_bp_median": arith["max_abs_alpha_horizon_bp"].median(),
                "alpha_13w_bp_p90": arith["max_abs_alpha_horizon_bp"].quantile(0.9),
                "round_trip_bp_median": arith["round_trip_bp"].median(),
                "round_trip_bp_p90": arith["round_trip_bp"].quantile(0.9),
                "shadow_marginal_bp_median": arith["shadow_marginal_bp"].median(),
                "share_13w_alpha_above_round_trip": float(
                    (arith["max_abs_alpha_horizon_bp"] > arith["round_trip_bp"]).mean()
                ),
                "most_frequent_top_instrument": str(arith["instrument"].mode().iloc[0]),
            }
        )
    table_d = pd.DataFrame(d_rows)

    rule_xs = kept[("ic35", "cross_sectional")][0]
    rule_nv = kept[("noview", "cross_sectional")][0]
    dates = sorted(rule_xs.books)
    mid = dates[len(dates) // 2]
    hc = pilot.hand_check(rule_xs, mid, params)
    w_view = rule_xs.books[mid]["weights"].astype(float)
    w_none = rule_nv.books[mid]["weights"].astype(float)
    e_inst = hc["by_instrument"].copy()
    ids = sorted(set(e_inst.index) | set(w_view.index) | set(w_none.index))
    e_inst = e_inst.reindex(ids)
    e_inst["w_view"] = w_view.reindex(ids).fillna(0.0)
    e_inst["w_noview"] = w_none.reindex(ids).fillna(0.0)
    e_inst["w_diff"] = e_inst["w_view"] - e_inst["w_noview"]
    e_inst = e_inst[
        (e_inst["alpha_rule"].abs() > 0) | (e_inst[["w_view", "w_noview"]].abs() > 0).any(axis=1)
    ]
    e_summary = {
        "date": str(pd.Timestamp(mid).date()),
        "max_gap_z": hc["max_gap_z"],
        "max_gap_view": hc["max_gap_view"],
        "max_gap_alpha": hc["max_gap_alpha"],
        "sum_abs_weight_diff_vs_noview": float(e_inst["w_diff"].abs().sum()),
    }

    def recs(frame):
        return json.loads(frame.to_json(orient="records", default_handler=str))

    summary = {
        "run_id": run_id,
        "kind": "phase2-pilot-diag",
        "grid": pilot.PILOT_DIAG_GRID,
        "source": args.source,
        **meta,
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "store_id": params.get("data.characteristics.store_id"),
        "thread_setting": THREADS,
        "generated_at": pd_now(),
        "n_runs": len(table),
        "seconds": round(time.time() - started + meta["prep_seconds"], 1),
        "seconds_per_run_mean": float(table["seconds"].mean()),
        "lookahead_passed": int(table["lookahead_passed"].sum()),
        "inputs": inputs.notes,
        "a_no_view": recs(table_a),
        "a_active_exposure_mean": recs(a_exposure),
        "a_tracking_variance_share_mean": recs(a_variance),
        "b_view_size": recs(table_b),
        "c_no_friction": recs(table_c),
        "d_arithmetic": recs(table_d),
        "e_hand_check": e_summary,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    for expression, frame in d_detail.items():
        frame.to_csv(out / f"d_arithmetic_{expression}.csv", index_label="date")
    hc["by_region"].to_csv(out / "e_by_region.csv", index_label="region")
    e_inst.to_csv(out / "e_by_instrument.csv", index_label="instrument")

    lines = [
        f"# Phase-2 pilot diagnostics {run_id} (HANDOFF task 91)",
        "",
        "Seed 0, h = 13, through `run_pilot_cell`. Derived numbers only. **Nothing judged:** "
        "thresholds, `IC_prior`, costs and constraints are the owner's (decisions/0069 item 2).",
        "",
        f"- snapshot `{meta['snapshot_id']}`, params `{params.params_version}`, store "
        f"`{summary['store_id']}`; {len(table)} runs, {summary['seconds']:.0f} s; lookahead "
        f"passed on {summary['lookahead_passed']}",
        "",
        "## (a) The no-view book",
        "",
        _md_table(table_a),
        "",
        "Active exposure, mean over rebalances:",
        "",
        _md_table(a_exposure),
        "",
        "Share of ex-ante tracking variance, mean over rebalances:",
        "",
        _md_table(a_variance),
        "",
        "## (b) The size of the view (planted IC 0.35)",
        "",
        _md_table(table_b),
        "",
        "## (c) No friction (half-spread x0, shadow coefficient 0; read `gross_ir`)",
        "",
        _md_table(table_c),
        "",
        "## (d) The arithmetic (IC 0.35, IC_prior x1; bp)",
        "",
        _md_table(table_d),
        "",
        f"## (e) One date by hand: {e_summary['date']} (region, IC 0.35, x1)",
        "",
        f"Largest gaps, rule against hand: z {e_summary['max_gap_z']:.3g}, view "
        f"{e_summary['max_gap_view']:.3g}, alpha {e_summary['max_gap_alpha']:.3g}; "
        f"sum |w - w_noview| {e_summary['sum_abs_weight_diff_vs_noview']:.4f}.",
        "",
        _md_table(hc["by_region"].reset_index(names="region")),
        "",
        _md_table(e_inst.reset_index(names="instrument")),
        "",
    ]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    if not args.quiet:
        print("\n".join(lines))
        print(f"\nwrote {out}/  ({summary['seconds']:.0f}s)")
    return 0


def _write_cell_artifacts(artifacts_root, run_id: str, cell, path, params=None) -> int:
    """
    Weights, alpha and the rebalance-date index for one cell, as parquet
    (decisions/0035 s5). `results/artifacts/` is where `STATUS.md` already
    says these live and where the results store's own `write_artifact` puts
    them; the audit writes here directly since it does not go through the
    store. Returns the bytes written, so the caller can report the disk cost.
    """
    from pathlib import Path

    out = Path(artifacts_root) / run_id / cell.key(params)
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
        HALFLIFE_GRID,
        KNEE_GRID,
        POWER10_GRID,
        POWER_GRID,
        baseline_cells,
        friction_cells,
        friction_created_cells,
        grid_cells,
        halflife_cells,
        knee_cells,
        power10_cells,
        power_cells,
        run_cell,
    )
    from signal_lab.audit.pilot import PILOT_DIAG_GRID, PILOT_GRIDS
    from signal_lab.audit.report import run_id_now, write_outputs

    pilot_grids = (*PILOT_GRIDS, PILOT_DIAG_GRID)
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
        choices=[*AUDIT_GRIDS, *pilot_grids],
        help="run only the block-shuffled baseline cells of decisions/0036: "
        "baseline-pilot (h13) or baseline (every horizon); or knee, the live and "
        "baseline cells at the IC rungs between 0.20 and the oracle (h13); or power, "
        "20 score-shuffle baselines per knee rung and seed (HANDOFF task 25); or "
        "power10, 20 span-limited score shuffles at IC 0.70 for seeds 0-9 (task 30); or "
        "friction, live cells only at the shadow-cost coefficient 10/20/40 bp (task 32); or "
        "friction_created, the same 60 cells priced with the created-turnover shadow "
        "instead of trailing (task 36, decisions/0040); or "
        "halflife, live cells at horizons 4/13/26, IC 0.35/0.70, seeds 0-9, vol_halflife "
        "None/13/26/52 -- 240 cells, respects HALFLIFE_DEADLINE (task 35, OWNER-QUEUE B1/L13)",
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
    if args.grid in pilot_grids:
        return _run_phase2_pilot(args, params, run_id, out_root)

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
    elif args.grid == HALFLIFE_GRID:
        cells = halflife_cells(params)
        problem = _halflife_preflight(
            cells, universe, params, args.out or params.get("audit.output_dir", "results/audit")
        )
        if problem:
            print(f"halflife STOPPED before any cell: {problem}", file=sys.stderr)
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

    if args.grid == HALFLIFE_GRID:
        # task 35's amendment: checkpoint every finished cell to
        # cells.partial.csv (a kill loses at most one cell), and stop cleanly
        # before a cell that would likely miss HALFLIFE_DEADLINE.
        import csv

        out = Path(out_root) / run_id
        out.mkdir(parents=True, exist_ok=True)
        deadline_ts = _parse_halflife_deadline(os.environ.get("HALFLIFE_DEADLINE"))
        durations: list[float] = []
        partial_file = None
        partial_writer = None
        stopped_early = False
        try:
            for i, cell in enumerate(cells, start=1):
                if _halflife_should_stop(time.time(), deadline_ts, durations):
                    stopped_early = True
                    if not args.quiet:
                        print(
                            f"halflife: stopping before cell {i}/{len(cells)} -- "
                            f"HALFLIFE_DEADLINE would be missed",
                            flush=True,
                        )
                    break
                t_cell = time.time()
                row, path = run_cell(universe, cell, params, args.solver)
                durations.append(time.time() - t_cell)
                rows.append(row)
                if cell.tag == "base":
                    artifact_bytes += _write_cell_artifacts(
                        artifacts_root, run_id, cell, path, params
                    )
                if partial_writer is None:
                    partial_file = open(
                        out / "cells.partial.csv", "w", newline="", encoding="utf-8"
                    )
                    partial_writer = csv.DictWriter(partial_file, fieldnames=list(row.keys()))
                    partial_writer.writeheader()
                partial_writer.writerow(row)
                partial_file.flush()
                if not args.quiet:
                    print(
                        f"  [{i:>3}/{len(cells)}] {cell.key(params):<34} net IR {row['net_ir']:+.3f}  "
                        f"TE p95 {row['te_p95']:.1%}  turnover {row['turnover_annual']:.0%}  "
                        f"inaccurate {row['inaccurate_share']:.1%}  {row['seconds']:.1f}s",
                        flush=True,
                    )
        finally:
            if partial_file is not None:
                partial_file.close()
        table = pd.DataFrame(rows)
        if artifact_bytes and not args.quiet:
            print(f"artifacts: {artifact_bytes / 1e6:.1f} MB under {artifacts_root}/{run_id}/")
        return _write_halflife_run(
            args, params, universe, table, run_id, out_root, started, len(cells), stopped_early
        )

    for i, cell in enumerate(cells, start=1):
        row, path = run_cell(universe, cell, params, args.solver)
        rows.append(row)
        if cell.tag == "base":
            # decisions/0035 s5: base cells at minimum, so the next measurement
            # bug is a re-derivation instead of another multi-hour re-run.
            artifact_bytes += _write_cell_artifacts(artifacts_root, run_id, cell, path, params)
        if not args.quiet:
            print(
                f"  [{i:>3}/{len(cells)}] {cell.key(params):<34} net IR {row['net_ir']:+.3f}  "
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
        "thread_setting": THREADS,
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
