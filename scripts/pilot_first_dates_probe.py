#!/usr/bin/env python3
"""
Why the decisions/0070 pilot runs trade nothing on their first recorded rebalance, and why a
run takes about 270 s (HANDOFF task 95; decisions/0070, decisions/0059 G). A diagnostic: it
measures and fixes nothing.

Step 1, the first dates. Three arms, planted IC 0.35, h 13, seed 0, duration directional and
region cross-sectional, each run through `audit.pilot.run_pilot_cell` (so the rule, the engine
and the costs are exactly the pilot's):

  default   the 0070 defaults (the solve sees half-spread / h, the first book is the no-view book)
  A         the legacy objective with task 92's (A) switch (half-spread / 13 through
            `AmortisedCosts`, the first book built free with the view)
  C         task 92's (C) switch alone (full half-spread, the first book the no-view book)

The probe instruments, from outside `src/`, three names for the duration of a run:
`RebalanceStep.step` (what the solve is handed: the alpha, the divisor on the half-spread, the
first-call branch), `portfolio.rebalance.solve` (the traded notional and its seconds) and
`portfolio.long_only._run` (the inner solves the position cap adds). Nothing is changed: each
wrapper calls the original and returns its result untouched.

Step 2, timing. The four live default cells (both expressions, IC 0 and 0.35), one after
another, then the same four under the legacy objective with the (A) switch; for each, wall
seconds, `/proc/loadavg` at start and end, solves and seconds inside them.

HANDOFF task 96 (decisions/0070 addendum of 2026-11-13, decisions/0040) adds, per date:
`shadow_marginal_bps_at_0`, the marginal created-turnover shadow at zero trade from the step's
own `created_marginal_quadratic` (`2 a max(0, b)`, in bp, read before the solve; NaN on the
first date, whose book is built at a cost of 0); `best_pair_net_bps`, on the drifted book the
largest `(alpha_i - c_i) - (alpha_j + c_j)` over a holdable i and a held j (`w0_j > 0`, j != i)
with `c` the half-spread vector the solve receives, and the same less twice the shadow; and the
drifted book's weight on instruments that are not in the step's holdable set (the solve's `w0`
is the drifted book reindexed to it). A fourth arm, `shadow0`, is the defaults with an
in-memory copy of `Params` whose `constraints.turnover.penalty.coefficient` is 0.

Writes `results/pilot_first_dates/report.md` and `summary.json`: dates, norms, counts and
seconds from planted runs only; no vendor value, nothing in the results store. A run keeps what
an earlier task wrote there: its own summary goes under the key `--tag` names and its report
section replaces only that tag's section.

    python scripts/pilot_first_dates_probe.py            # both steps (make pilot-first-dates)
    python scripts/pilot_first_dates_probe.py --step 1   # the first dates only
    python scripts/pilot_first_dates_probe.py --step 1 --arms default,shadow0   # task 96
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import _bootstrap

THREADS = _bootstrap.require_one_thread()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from signal_lab.audit import pilot  # noqa: E402
from signal_lab.portfolio import long_only as long_only_mod  # noqa: E402
from signal_lab.portfolio import rebalance as rebalance_mod  # noqa: E402

TRADE_THRESHOLD = 1e-4
N_DATES = 30
OUT_DIR = Path("results/pilot_first_dates")

ARMS = ("default", "A", "C")
KNOWN_ARMS = ("default", "A", "C", "legacy", "shadow0")
BPS = 1e-4


def with_shadow_coefficient(params, value: float):
    """An in-memory copy of `params` with `constraints.turnover.penalty.coefficient` set to
    `value` (as `pilot.with_ic_prior` copies `IC_prior`); nothing under `params/` is edited."""
    constraints = copy.deepcopy(params.constraints)
    constraints.setdefault("turnover", {}).setdefault("penalty", {})["coefficient"] = float(value)
    return dataclasses.replace(params, constraints=constraints)


def arm_params(arm: str, params):
    """The params an arm runs on: `shadow0` zeroes the created-turnover shadow's coefficient."""
    return with_shadow_coefficient(params, 0.0) if arm == "shadow0" else params


def arm_cell(arm: str, expression: str, ic: float = pilot.DIAG_IC, seed: int = 0):
    """The pilot cell of each arm (task 92's switches imply the legacy objective). `shadow0`
    is the default cell; its difference is in `arm_params`."""
    if arm in ("default", "shadow0"):
        return pilot.PilotCell(expression, ic, seed)
    if arm == "A":
        return pilot.PilotCell(expression, ic, seed, amortise=True)
    if arm == "C":
        return pilot.PilotCell(expression, ic, seed, start_noview=True)
    if arm == "legacy":
        return pilot.PilotCell(expression, ic, seed, legacy=True)
    raise ValueError(f"unknown arm {arm!r}")


class Recorder:
    """What the instrumented names saw during one run."""

    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []
        self.solve_seconds = 0.0
        self.n_solves = 0
        self.inner_solves = 0
        self.inner_seconds = 0.0
        self.positions_capped = 0


def _l2(values) -> float:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    return float(np.sqrt((x * x).sum())) if len(x) else 0.0


def _nonzero(values) -> int:
    x = np.asarray(values, dtype=float)
    return int((np.isfinite(x) & (np.abs(x) > 0)).sum())


def best_pair_net(alpha: pd.Series, w0: pd.Series, cost: pd.Series) -> tuple[float, str]:
    """On the book the solve starts from: the largest `(alpha_i - c_i) - (alpha_j + c_j)` over
    a holdable i and a held j (`w0_j > 0`, j != i), in return units, and the pair `i/j`. Any
    holdable id is buyable: `LongOnlySpec` carries no per-instrument upper bound (the cash cap
    is aggregate). NaN when nothing is held."""
    ids = list(w0.index)
    a = alpha.reindex(ids).fillna(0.0).to_numpy(dtype=float)
    c = pd.Series(cost).reindex(ids).fillna(0.0).to_numpy(dtype=float)
    held = w0.to_numpy(dtype=float) > 0
    if not held.any():
        return float("nan"), ""
    buy = a - c
    sell = a + c
    gain = buy[:, None] - sell[None, :]
    gain[:, ~held] = -np.inf
    np.fill_diagonal(gain, -np.inf)
    k = int(np.argmax(gain))
    i, j = divmod(k, len(ids))
    return float(gain[i, j]), f"{ids[i]}/{ids[j]}"


@contextlib.contextmanager
def instrument():
    """Wrap `RebalanceStep.step`, `rebalance.solve` and `long_only._run`; restore on exit."""
    rec = Recorder()
    real_step = rebalance_mod.RebalanceStep.step
    real_solve = rebalance_mod.solve
    real_run = long_only_mod._run
    last: dict[str, Any] = {}

    def solve(*args, **kwargs):
        t0 = time.perf_counter()
        sol = real_solve(*args, **kwargs)
        rec.solve_seconds += time.perf_counter() - t0
        rec.n_solves += 1
        rec.positions_capped += int(bool(sol.positions_capped))
        last["turnover"] = float(sol.turnover)
        a_in = args[0] if len(args) > 0 else kwargs.get("alpha")
        w0_in = args[2] if len(args) > 2 else kwargs.get("w0")
        cost_in = args[3] if len(args) > 3 else kwargs.get("cost")
        last["cost"] = cost_in
        last["hold"] = list(w0_in.index)
        last["best_pair"] = best_pair_net(pd.Series(a_in), w0_in, pd.Series(cost_in))
        return sol

    def run(*args, **kwargs):
        t0 = time.perf_counter()
        out = real_run(*args, **kwargs)
        rec.inner_seconds += time.perf_counter() - t0
        rec.inner_solves += 1
        return out

    def step(self, date, alpha, drifted=None):
        first = drifted is None
        no_view_branch = first and (
            bool(getattr(self, "first_book_from_no_view", False))
            or isinstance(self, pilot.FromNoViewRule)
        )
        date = pd.Timestamp(date)
        entry: dict[str, Any] = {"date": date, "first": first, "first_call_branch": no_view_branch}
        scores = getattr(self, "scores", None)
        z = getattr(self, "z", None)
        if isinstance(scores, pd.DataFrame) and date in scores.index:
            entry["n_raw_scores_nonzero"] = _nonzero(scores.loc[date].to_numpy())
            entry["raw_scores_l2"] = _l2(scores.loc[date].to_numpy())
        if isinstance(z, pd.DataFrame) and date in z.index:
            entry["n_z_nonzero"] = _nonzero(z.loc[date].to_numpy())
            entry["z_l2"] = _l2(z.loc[date].to_numpy())
        a = alpha.astype(float)
        entry["alpha_l2"] = _l2(a.to_numpy())
        entry["alpha_max_abs"] = float(a.abs().max()) if len(a) else 0.0
        entry["alpha_argmax"] = str(a.abs().idxmax()) if len(a) and a.abs().max() > 0 else ""
        wrapper_div = float(getattr(self.costs, "divisor", 1.0))
        horizon_div = float(self.cost_horizon) if self.cost_horizon is not None else 1.0
        # the first book is built, not traded: the solve sees a cost of 0 (`step`, `first`)
        entry["half_spread_divisor"] = float("inf") if first else wrapper_div * horizon_div
        # HANDOFF task 96: the marginal created shadow at zero trade, from the step's own
        # history and coefficient, read before the solve (the solve appends to the log)
        entry["shadow_form"] = str(self.shadow_form)
        if first:
            entry["shadow_marginal_bps_at_0"] = float("nan")
            entry["prefilled_P"] = float("nan")
        elif self.shadow_form == "created":
            a_coef, b_coef = self._shadow_quadratic_coeffs()
            entry["shadow_marginal_bps_at_0"] = 2.0 * a_coef * max(0.0, b_coef) / BPS
            entry["prefilled_P"] = float(self._prefilled_P())
        else:
            entry["shadow_marginal_bps_at_0"] = float(self._shadow()) / BPS
            entry["prefilled_P"] = float("nan")
        last.pop("best_pair", None)
        weights = real_step(self, date, alpha, drifted)
        entry["solve_turnover"] = last.get("turnover", float("nan"))
        pair_gain, pair = last.get("best_pair", (float("nan"), ""))
        entry["best_pair_net_bps"] = pair_gain / BPS
        entry["best_pair_net_less_shadow_bps"] = (
            entry["best_pair_net_bps"] - 2.0 * entry["shadow_marginal_bps_at_0"]
        )
        entry["best_pair"] = pair
        if drifted is not None:
            hold = set(last.get("hold", []))
            d = drifted.astype(float)
            out = {k: float(v) for k, v in d.items() if k not in hold and abs(v) > 1e-12}
            entry["left_holdable"] = out
            entry["left_holdable_weight"] = float(sum(out.values()))
        cost = last.get("cost")
        if cost is not None and len(a) and entry["alpha_argmax"]:
            entry["solve_cost_at_argmax"] = float(
                pd.Series(cost).get(entry["alpha_argmax"], np.nan)
            )
        if drifted is not None:
            w = weights.astype(float)
            d = drifted.astype(float)
            ids = sorted(set(w.index) | set(d.index))
            delta = w.reindex(ids).fillna(0.0) - d.reindex(ids).fillna(0.0)
            top = delta.abs().sort_values(ascending=False).head(5)
            entry["top_trades"] = {k: float(delta[k]) for k in top.index if abs(delta[k]) > 1e-6}
            entry["entered_holdable"] = sorted(set(w.index) - set(d.index))
        rec.steps.append(entry)
        return weights

    rebalance_mod.RebalanceStep.step = step
    rebalance_mod.solve = solve
    long_only_mod._run = run
    try:
        yield rec
    finally:
        rebalance_mod.RebalanceStep.step = real_step
        rebalance_mod.solve = real_solve
        long_only_mod._run = real_run


def first_dates_table(rec: Recorder, path: Any, n: int = N_DATES) -> pd.DataFrame:
    """One row per rebalance date: what the rule read and handed the solve, and what the engine
    recorded. The engine records no turnover row for the first date (the book is built)."""
    steps = pd.DataFrame(rec.steps).set_index("date")
    traded = path.turnover.astype(float)
    steps["engine_traded_notional"] = traded.reindex(steps.index)
    steps.insert(0, "index", range(len(steps)))
    return steps.head(n)


def first_trade(table: pd.DataFrame, threshold: float = TRADE_THRESHOLD) -> dict[str, Any] | None:
    """The first date where the engine's traded notional passes `threshold`."""
    hit = table[table["engine_traded_notional"] > threshold]
    if hit.empty:
        return None
    date = hit.index[0]
    return {"date": str(pd.Timestamp(date).date()), "index": int(hit.loc[date, "index"])}


def first_alpha(table: pd.DataFrame, costs: Any, h: int) -> dict[str, Any] | None:
    """The first date with a nonzero alpha: its largest |alpha_i| beside half-spread_i / h."""
    hit = table[table["alpha_max_abs"] > 0]
    if hit.empty:
        return None
    date = hit.index[0]
    inst = str(hit.loc[date, "alpha_argmax"])
    half = float(costs.half_spread_vector([inst]).iloc[0])
    return {
        "date": str(pd.Timestamp(date).date()),
        "index": int(hit.loc[date, "index"]),
        "instrument": inst,
        "max_abs_alpha": float(hit.loc[date, "alpha_max_abs"]),
        "half_spread": half,
        "half_spread_over_h": half / h,
        "ratio_alpha_to_half_spread_over_h": float(hit.loc[date, "alpha_max_abs"]) / (half / h),
    }


def loadavg() -> str:
    try:
        return Path("/proc/loadavg").read_text().strip()
    except OSError:
        return "n/a"


def probe_cell(inputs, cell, params, lookahead_veto, solver=None, n=N_DATES) -> dict[str, Any]:
    """One instrumented pilot run: the first-dates table and the timing."""
    load_start = loadavg()
    t0 = time.perf_counter()
    keep: dict[str, Any] = {}
    with instrument() as rec:
        row, rule, path = pilot.run_pilot_cell(
            inputs, cell, params, lookahead_veto=lookahead_veto, solver=solver, keep=keep
        )
    wall = time.perf_counter() - t0
    table = first_dates_table(rec, path, n)
    return {
        "cell": cell,
        "row": row,
        "rule": rule,
        "path": path,
        "table": table,
        "first_trade": first_trade(table),
        "first_alpha": first_alpha(table, keep["costs"], cell.horizon),
        "timing": {
            "key": cell.key(),
            "wall_seconds": wall,
            "load_start": load_start,
            "load_end": loadavg(),
            "n_rebalances": int(len(rec.steps)),
            "n_solves": rec.n_solves,
            "solve_seconds": rec.solve_seconds,
            "seconds_per_solve": rec.solve_seconds / rec.n_solves if rec.n_solves else math.nan,
            "inner_solves": rec.inner_solves,
            "inner_seconds": rec.inner_seconds,
            "positions_capped": rec.positions_capped,
            "seconds_outside_solves": wall - rec.solve_seconds,
            "lookahead_passed": bool(row["lookahead_passed"]),
            "turnover_annual": float(row["turnover_annual"]),
        },
    }


# -- the run on the pilot's inputs ----------------------------------------------------------


def _inputs(params):
    import run_measurement as RM

    from signal_lab.audit.universe import get_universe
    from signal_lab.characteristics.exposures import ExposureMap

    universe = get_universe("bloomberg", params)
    exposures = ExposureMap.from_params(params)
    manifest = exposures.store.manifest
    factor_set = str(manifest.get("factor_set", "huber6"))
    estimation_start = str(manifest.get("estimation_start", "dev_start"))
    _, _, ff, _, _ = RM.load_inputs(params, factor_set, estimation_start)
    return pilot.build_inputs(universe, exposures, ff.frame, params)


TABLE_COLUMNS = [
    "index",
    "first",
    "first_call_branch",
    "n_z_nonzero",
    "z_l2",
    "n_raw_scores_nonzero",
    "alpha_l2",
    "alpha_max_abs",
    "half_spread_divisor",
    "shadow_marginal_bps_at_0",
    "best_pair_net_bps",
    "best_pair_net_less_shadow_bps",
    "left_holdable_weight",
    "solve_turnover",
    "engine_traded_notional",
]


def _fmt(value) -> str:
    if isinstance(value, bool | np.bool_):
        return "T" if value else "F"
    if isinstance(value, float | np.floating):
        if not np.isfinite(value):
            return "inf" if value == np.inf else "nan"
        return f"{value:.3g}"
    return str(value)


def _md(frame: pd.DataFrame) -> str:
    cols = ["date", *frame.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in frame.iterrows():
        cells = [str(pd.Timestamp(idx).date())] + [_fmt(row[c]) for c in frame.columns]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for idx, row in frame.iterrows():
        rec = {"date": str(pd.Timestamp(idx).date())}
        for c, v in row.items():
            if isinstance(v, np.bool_ | bool):
                rec[c] = bool(v)
            elif isinstance(v, np.integer):
                rec[c] = int(v)
            elif isinstance(v, float | np.floating):
                rec[c] = float(v) if np.isfinite(v) else str(v)
            else:
                rec[c] = v
        out.append(rec)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--step", choices=["1", "2", "all"], default="all")
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument(
        "--arms",
        default=",".join(ARMS),
        help=f"step 1's arms, comma-separated, from {', '.join(KNOWN_ARMS)}",
    )
    ap.add_argument("--tag", default="task96", help="the key this run's results are kept under")
    args = ap.parse_args(argv)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    unknown = [a for a in arms if a not in KNOWN_ARMS]
    if unknown:
        ap.error(f"unknown arm(s) {unknown}; known: {KNOWN_ARMS}")

    from signal_lab.params import get_params
    from vetoes.rules import veto_lookahead

    params = get_params()
    started = time.time()
    print(f"pilot-first-dates: building the pilot's inputs (load {loadavg()})", flush=True)
    inputs = _inputs(params)
    prep = time.time() - started
    print(f"  inputs ready in {prep:.0f} s; {inputs.notes}", flush=True)

    summary: dict[str, Any] = {
        "task": f"HANDOFF {args.tag}",
        "threads": THREADS,
        "prep_seconds": round(prep, 1),
        "trade_threshold": TRADE_THRESHOLD,
        "arms": arms,
        "step1": {},
        "step2": [],
    }
    md: list[str] = [
        f"# {SECTION_MARK}{args.tag}: pilot first dates",
        "",
        f"Arms {', '.join(arms)}. `shadow_marginal_bps_at_0` is the marginal created-turnover "
        "shadow at zero trade, per unit of traded notional (each leg), from the step's own "
        "`created_marginal_quadratic`, NaN on the first date. `best_pair_net_bps` is the best "
        "(alpha_i - c_i) - (alpha_j + c_j) over a holdable i and a held j on the drifted book, "
        "c the half-spread the solve receives; `_less_shadow` takes twice the shadow off. "
        "`left_holdable_weight` is the drifted book's weight on instruments outside the step's "
        "holdable set (the solve's `w0` leaves them out; the engine sells them).",
        "",
        "Planted runs through `run_pilot_cell`, seed 0, h 13. Derived numbers only: dates, norms, "
        "counts, seconds. `half_spread_divisor` is inf on the first date (the first book is built "
        "at a cost of 0). `engine_traded_notional` is the engine's recorded turnover (no row for "
        "the first date). `n_z_nonzero`/`z_l2` are the standardised scores the rule turns into "
        "views; `n_raw_scores_nonzero` the planted raw scores at the date.",
        "",
    ]

    if args.step in ("1", "all"):
        md += ["## Step 1: the first dates (IC 0.35)", ""]
        for expression in pilot.AXIS_OF_EXPRESSION:
            for arm in arms:
                cell = arm_cell(arm, expression)
                print(f"  step 1: {cell.key()} ({arm})", flush=True)
                res = probe_cell(inputs, cell, arm_params(arm, params), veto_lookahead)
                table = res["table"]
                a_trade = res["first_trade"]
                key = f"{expression}/{arm}"
                second = table.iloc[1] if len(table) > 1 else None
                summary["step1"][key] = {
                    "cell": cell.key(),
                    "first_trade": a_trade,
                    "first_alpha": res["first_alpha"],
                    "date2_top_trades": second.get("top_trades") if second is not None else None,
                    "date2_entered_holdable": second.get("entered_holdable")
                    if second is not None
                    else None,
                    "left_holdable_by_index": {
                        int(r["index"]): r["left_holdable"]
                        for _, r in table.iterrows()
                        if isinstance(r.get("left_holdable"), dict) and r["left_holdable"]
                    },
                    "best_pair_by_index": {
                        int(r["index"]): r["best_pair"]
                        for _, r in table.head(15).iterrows()
                        if r.get("best_pair")
                    },
                    "table": _records(table[[c for c in TABLE_COLUMNS if c in table.columns]]),
                    "timing": res["timing"],
                }
                md += [
                    f"### {expression}, arm {arm} (`{cell.key()}`)",
                    "",
                    f"First traded notional > {TRADE_THRESHOLD:g}: {a_trade}. "
                    f"First nonzero alpha: {res['first_alpha']}.",
                    "",
                    f"Date 2 largest trades: {summary['step1'][key]['date2_top_trades']}; "
                    f"instruments entering: {summary['step1'][key]['date2_entered_holdable']}.",
                    "",
                    "Drifted weight outside the holdable set, by index: "
                    f"{summary['step1'][key]['left_holdable_by_index']}. "
                    f"Best pair (buy/sell), by index: {summary['step1'][key]['best_pair_by_index']}.",
                    "",
                    _md(table[[c for c in TABLE_COLUMNS if c in table.columns]]),
                    "",
                ]
                print(f"    first trade {a_trade}; first alpha {res['first_alpha']}", flush=True)

    if args.step in ("2", "all"):
        md += [
            "## Step 2: timing, one run after another",
            "",
            "| key | arm | wall s | load start | load end | solves | solve s | s/solve | inner "
            "solves | capped | outside solves s |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for arm in ("default", "A"):
            for expression in pilot.AXIS_OF_EXPRESSION:
                for ic in (0.0, pilot.DIAG_IC):
                    cell = arm_cell(arm, expression, ic)
                    print(f"  step 2: {cell.key()} ({arm})", flush=True)
                    res = probe_cell(inputs, cell, params, veto_lookahead)
                    t = dict(res["timing"], arm=arm)
                    summary["step2"].append(t)
                    md.append(
                        f"| {t['key']} | {arm} | {t['wall_seconds']:.0f} | {t['load_start']} | "
                        f"{t['load_end']} | {t['n_solves']} | {t['solve_seconds']:.0f} | "
                        f"{t['seconds_per_solve']:.3f} | {t['inner_solves']} | "
                        f"{t['positions_capped']} | {t['seconds_outside_solves']:.0f} |"
                    )
                    print(
                        f"    {t['wall_seconds']:.0f} s, {t['n_solves']} solves, "
                        f"{t['solve_seconds']:.0f} s in them, inner {t['inner_solves']}, "
                        f"load {t['load_start']} -> {t['load_end']}",
                        flush=True,
                    )
        md.append("")

    summary["seconds"] = round(time.time() - started, 1)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    merged = merge_summary(out / "summary.json", args.tag, summary)
    (out / "summary.json").write_text(json.dumps(merged, indent=2, default=str), encoding="utf-8")
    report = merge_report(out / "report.md", args.tag, "\n".join(md) + "\n")
    (out / "report.md").write_text(report, encoding="utf-8")
    print(f"pilot-first-dates: wrote {out}/report.md and summary.json in {summary['seconds']} s")
    return 0


SECTION_MARK = "Probe run "


def merge_summary(path: Path, tag: str, summary: dict[str, Any]) -> dict[str, Any]:
    """Keep what an earlier run wrote: task 95's flat summary moves under `task95`, and this
    run's summary replaces only its own tag's key."""
    existing: dict[str, Any] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if "task" in existing and "step1" in existing:
            old_tag = str(existing["task"]).replace("HANDOFF ", "").replace(" ", "")
            existing = {old_tag: existing}
    existing[tag] = summary
    return existing


def merge_report(path: Path, tag: str, section: str) -> str:
    """Keep the earlier report and replace only this tag's section (from its heading on, up to
    the next probe-run heading)."""
    if not path.exists():
        return section
    text = path.read_text(encoding="utf-8")
    head = f"# {SECTION_MARK}{tag}:"
    start = text.find(head)
    if start < 0:
        return text.rstrip("\n") + "\n\n" + section
    nxt = text.find(f"\n# {SECTION_MARK}", start + len(head))
    rest = "" if nxt < 0 else text[nxt + 1 :]
    return text[:start] + section + ("\n" + rest if rest else "")


if __name__ == "__main__":
    sys.exit(main())
