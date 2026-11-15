#!/usr/bin/env python3
"""
The pilot's null, measured before the owner rules the thresholds: HANDOFF task 98 step 1
(decisions/0059 G, decisions/proposed/0072). A diagnostic: it measures and fixes nothing, and
runs no solve.

For each expression, the planted IC 0 score is built with the pilot's own functions and seeds
(`audit.pilot.baseline_ic_by_column`, which is `plant_axis_signal` and `realised_ic` as the
pilot's rows use them), first with the baseline twin's own shuffle, reproducing task 94's
`realised_ic_by_column` for seeds 0 to 4 from its `cells.csv` to 1e-9, then with 40 other draws
of the same block shuffle per seed (`pilot.null_shuffle_rng`), 200 per expression. Reported:
mean, SD, the 5% and 95% points, 1/sqrt(B x K) beside the SD (B the non-overlapping 13-week
blocks in the scored window, K the columns), each seed's mean and SD over its draws, and the
reading of step 1 (the mean within 3 x SD/sqrt(200) of 0, or not).

Writes `results/pilot_null/ic_report.md` and `ic_summary.json`: derived numbers from planted
scores only, no vendor value, nothing in the results store. Exit 4 if the reproduction fails.

    python scripts/pilot_null_probe.py      # make pilot-null
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import _bootstrap

THREADS = _bootstrap.require_one_thread()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from signal_lab.audit import pilot  # noqa: E402

OUT_DIR = Path("results/pilot_null")
AUDIT_DIR = Path("results/audit")
TASK94_RUN = "A-20261114-030208"
REPRO_TOL = 1e-9


def _factor(inputs, expression: str) -> pd.DataFrame:
    return inputs.duration_factor if expression == "directional" else inputs.region_factor


def ic_step(inputs, params, task94: pd.DataFrame) -> tuple[dict[str, Any], list[str], bool]:
    summary: dict[str, Any] = {
        "task94_run": TASK94_RUN,
        "seeds": list(pilot.NULL_PROBE_SEEDS),
        "draws": pilot.NULL_PROBE_DRAWS,
    }
    md = [
        "# Step 1: the IC 0 baseline's realised IC under the null (no solves)",
        "",
        f"Planted IC 0, h {pilot.PILOT_HORIZON}, seeds {list(pilot.NULL_PROBE_SEEDS)}, "
        f"{pilot.NULL_PROBE_DRAWS} block-shuffle draws per seed (the twin's function and block). "
        "`realised_ic_by_column` as the pilot's rows compute it. HANDOFF task 98.",
        "",
    ]
    reproduced = True
    for expression in pilot.AXIS_OF_EXPRESSION:
        factor = _factor(inputs, expression)
        repro = []
        for seed in pilot.NULL_PROBE_SEEDS:
            key = pilot.PilotCell(expression, 0.0, seed, baseline=True).key()
            recorded = task94.loc[task94["key"] == key, "realised_ic_by_column"]
            got = pilot.baseline_ic_by_column(factor, expression, seed, params)
            want = float(recorded.iloc[0]) if len(recorded) == 1 else float("nan")
            gap = abs(got - want)
            ok = bool(np.isfinite(gap) and gap <= REPRO_TOL)
            reproduced &= ok
            repro.append({"key": key, "task94": want, "probe": got, "gap": gap, "ok": ok})
        draws: list[float] = []
        per_seed = []
        for seed in pilot.NULL_PROBE_SEEDS:
            vals = [
                pilot.baseline_ic_by_column(
                    factor, expression, seed, params, shuffle_rng=pilot.null_shuffle_rng(seed, d)
                )
                for d in range(pilot.NULL_PROBE_DRAWS)
            ]
            draws += vals
            per_seed.append(
                {"seed": seed, "mean": float(np.mean(vals)), "sd": float(np.std(vals, ddof=1))}
            )
        x = np.asarray(draws, dtype=float)
        n = len(x)
        mean, sd = float(x.mean()), float(x.std(ddof=1))
        blocks, k = pilot.scored_blocks(factor), int(factor.shape[1])
        envelope = 1.0 / np.sqrt(blocks * k)
        band = 3.0 * sd / np.sqrt(n)
        within = abs(mean) <= band
        seed_means = np.asarray([p["mean"] for p in per_seed])
        s = {
            "reproduction": repro,
            "n": n,
            "mean": mean,
            "sd": sd,
            "p05": float(np.quantile(x, 0.05)),
            "p95": float(np.quantile(x, 0.95)),
            "blocks_B": blocks,
            "columns_K": k,
            "one_over_sqrt_BK": float(envelope),
            "three_sd_over_sqrt_n": float(band),
            "mean_within_band": bool(within),
            "per_seed": per_seed,
            "sd_of_seed_means": float(seed_means.std(ddof=1)),
            "mean_within_sd_draws_sd": float(np.mean([p["sd"] for p in per_seed])),
        }
        summary[expression] = s
        md += [
            f"## {expression} ({pilot.AXIS_OF_EXPRESSION[expression]})",
            "",
            "Reproduction of task 94's IC 0 baseline (`realised_ic_by_column`, tolerance 1e-9):",
            "",
            "| key | task 94 | probe | gap |",
            "|---|---|---|---|",
            *[
                f"| {r['key']} | {r['task94']:.12f} | {r['probe']:.12f} | {r['gap']:.1e} |"
                for r in repro
            ],
            "",
            f"| n | mean | SD | 1/sqrt(BxK) (B={blocks}, K={k}) | p05 | p95 | 3 SD/sqrt(n) | "
            "mean within it |",
            "|---|---|---|---|---|---|---|---|",
            f"| {n} | {mean:+.4f} | {sd:.4f} | {envelope:.4f} | {s['p05']:+.4f} | "
            f"{s['p95']:+.4f} | {band:.4f} | {'yes' if within else 'NO'} |",
            "",
            "Per seed over its draws (the noise draw is the seed's; only the shuffle changes):",
            "",
            "| seed | mean | SD |",
            "|---|---|---|",
            *[f"| {p['seed']} | {p['mean']:+.4f} | {p['sd']:.4f} |" for p in per_seed],
            "",
            f"SD of the five seed means {s['sd_of_seed_means']:.4f}; mean within-seed SD "
            f"{s['mean_within_sd_draws_sd']:.4f}.",
            "",
        ]
    holds = all(summary[e]["mean_within_band"] for e in pilot.AXIS_OF_EXPRESSION)
    summary["reproduced"] = bool(reproduced)
    summary["mean_within_band_both"] = bool(holds)
    md += [
        "## Reading (task 98 step 1's rule)",
        "",
        f"Reproduction of task 94's values: {'held' if reproduced else 'FAILED'}. "
        + (
            "The mean is within 3 x SD/sqrt(200) of 0 in both expressions: the shuffle keeps no "
            "truth, and the twins' realised IC is their noise (a power property)."
            if holds
            else "The mean is NOT within 3 x SD/sqrt(200) of 0 in at least one expression: "
            "task 98 step 1's stop branch. Cowork rules from this report."
        ),
        "",
    ]
    return summary, md, reproduced


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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args(argv)

    from signal_lab.params import get_params

    params = get_params()
    started = time.time()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print("pilot-null: building the pilot's inputs", flush=True)
    inputs = _inputs(params)
    task94 = pd.read_csv(AUDIT_DIR / TASK94_RUN / "cells.csv")
    summary, md, reproduced = ic_step(inputs, params, task94)
    summary["seconds"] = round(time.time() - started, 1)
    summary["threads"] = THREADS
    (out / "ic_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "ic_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"pilot-null: wrote {out}/ic_report.md and ic_summary.json in {summary['seconds']} s")
    return 0 if reproduced else 4


if __name__ == "__main__":
    sys.exit(main())
