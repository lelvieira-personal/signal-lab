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

HANDOFF task 99 step 1 (decisions/0073), `--part task99`: (a) the seed as the unit, the twin's own
draw for seeds 0 to 14 with z against 1/sqrt(B x K)/sqrt(15); (b) the block shuffle's correlation
with the real truth over 200 independent draws; (c) the live cell and the twin under three noise
designs, report only. Writes `seed_report.md` and `seed_summary.json`.

    python scripts/pilot_null_probe.py                 # make pilot-null
    python scripts/pilot_null_probe.py --part task99   # make pilot-null ARGS="--part task99"
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


# ---------------------------------------------------------------------------------------------
# HANDOFF task 99 step 1 (decisions/0073): the seed as the unit, the shuffle tested directly,
# and the owner's question of decisions/proposed/0072's addendum of 2026-11-15 (report only).
# `--part task99`; writes `seed_report.md` and `seed_summary.json`. No solves, no src/ change.
# ---------------------------------------------------------------------------------------------

SEED_UNIT_SEEDS = tuple(range(15))
SHUFFLE_DRAWS = 200
SHUFFLE_SEED = 0
VARIANT_ICS = (0.0, 0.35)
VARIANTS = ("k", "m", "n")
VARIANT_NAMES = {
    "k": "as built (twin's noise orthogonal to the shuffled truth)",
    "m": "twin's noise orthogonal to the shuffled and the real truth",
    "n": "no orthogonalisation in either cell",
}
STOP_SHUFFLE_MEAN = 0.05
STOP_Z = 3.0


def column_mean_corr(a: pd.DataFrame, b: pd.DataFrame) -> float:
    """The mean over columns of each column's correlation over dates, on the dates both carry:
    `realised_ic`'s `by_column_mean`, for two frames."""
    per = []
    for column in a.columns:
        both = pd.concat([a[column], b[column]], axis=1).dropna()
        if len(both) > 2 and both.iloc[:, 0].std() > 0 and both.iloc[:, 1].std() > 0:
            per.append(float(np.corrcoef(both.iloc[:, 0], both.iloc[:, 1])[0, 1]))
    return float(np.mean(per)) if per else float("nan")


def shuffle_correlation(truth: pd.DataFrame, rng, shuffle=None, block: int | None = None) -> float:
    """Step 1 (b): the correlation of `block_shuffle_rows(truth, BASELINE_BLOCK, rng)` with the
    real truth, averaged over columns (truth only, no noise)."""
    from signal_lab.audit.signals import BASELINE_BLOCK
    from signal_lab.stats.blocks import block_shuffle_rows

    shuffle = block_shuffle_rows if shuffle is None else shuffle
    block = BASELINE_BLOCK if block is None else block
    return column_mean_corr(shuffle(truth, block, rng), truth)


def orthogonalise(e: np.ndarray, regressors: list[np.ndarray]) -> np.ndarray:
    """`e` centred, less its least-squares projection on the centred `regressors`."""
    ec = e - e.mean()
    if not regressors:
        return ec
    x = np.column_stack([r - r.mean() for r in regressors])
    beta, *_ = np.linalg.lstsq(x, ec, rcond=None)
    return ec - x @ beta


def plant_variant(factor, ic, seed, expression, params, baseline, variant, horizon=None):
    """`plant_axis_signal`, re-stated in the probe with the noise's orthogonalisation as a switch
    (step 1 (c), no src/ change): (k) as built, against what the cell blends from; (m) as (k) for
    the live cell, against the shuffled AND the real truth for the twin; (n) none in either cell
    (the centred AR(1) draw, scaled to the column's truth SD as the build scales it). Everything
    else (the truth, the shuffle stream, the noise draw, the scaling, the blend) is the build's;
    `variant="k"` reproduces `plant_axis_signal` (checked at run time and in the tests)."""
    from signal_lab.audit.axis_signals import AxisPlant, plant_axis_signal
    from signal_lab.audit.signals import BASELINE_BLOCK, _ar1_noise
    from signal_lab.stats.blocks import baseline_rng, block_shuffle_rows

    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    horizon = pilot.PILOT_HORIZON if horizon is None else int(horizon)
    # the truth exactly as the build makes it: take it from the build itself
    ref = plant_axis_signal(factor, 0.0, horizon, seed, expression, params)
    truth = ref.truth
    blend = truth
    if baseline:
        shuffled = block_shuffle_rows(truth, BASELINE_BLOCK, baseline_rng(seed))
        blend = shuffled.where(truth.notna()).fillna(0.0).where(truth.notna())
    rng = np.random.default_rng(seed)
    phi = (horizon - 1) / horizon
    raw = _ar1_noise(len(truth.index), truth.shape[1], phi, rng)
    noise = pd.DataFrame(raw, index=truth.index, columns=truth.columns).where(truth.notna())
    for column in truth.columns:
        y, e, t = blend[column], noise[column], truth[column]
        ok = y.notna() & e.notna() & t.notna()
        yv, ev, tv = y[ok].to_numpy(float), e[ok].to_numpy(float), t[ok].to_numpy(float)
        if len(yv) < 3 or float(np.dot(yv - yv.mean(), yv - yv.mean())) <= 0.0:
            continue
        if variant == "n":
            regs: list[np.ndarray] = []
        elif variant == "m" and baseline:
            regs = [yv, tv]
        else:
            regs = [yv]
        resid = orthogonalise(ev, regs)
        sd = float(resid.std())
        if sd > 0.0:
            noise.loc[ok[ok].index, column] = resid / sd * float(yv.std())
    noise = noise.where(blend.notna())
    score = ic * blend + np.sqrt(1.0 - ic * ic) * noise
    return AxisPlant(
        ic=float(ic),
        horizon=horizon,
        seed=int(seed),
        expression=expression,
        score=score,
        truth=truth,
        blend_truth=blend,
        baseline=bool(baseline),
    )


def _mean_sd(values) -> tuple[float, float]:
    x = np.asarray(values, dtype=float)
    return float(x.mean()), float(x.std(ddof=1))


def task99_step(inputs, params, task94: pd.DataFrame) -> tuple[dict[str, Any], list[str], bool]:
    from signal_lab.audit.axis_signals import plant_axis_signal, realised_ic
    from signal_lab.audit.signals import BASELINE_BLOCK

    summary: dict[str, Any] = {
        "task94_run": TASK94_RUN,
        "seeds": list(SEED_UNIT_SEEDS),
        "shuffle_draws": SHUFFLE_DRAWS,
        "variant_ics": list(VARIANT_ICS),
    }
    md = [
        "# Task 99 step 1: the pilot's null with the seed as the unit, and the shuffle itself",
        "",
        f"Planted h {pilot.PILOT_HORIZON}; seeds {SEED_UNIT_SEEDS[0]} to {SEED_UNIT_SEEDS[-1]}; "
        f"block {BASELINE_BLOCK} weeks. `realised_ic_by_column` as the pilot's rows compute it. "
        "HANDOFF task 99, decisions/0073. No solves.",
        "",
    ]
    reproduced = True
    stop = False
    for expression in pilot.AXIS_OF_EXPRESSION:
        factor = _factor(inputs, expression)
        blocks, k = pilot.scored_blocks(factor), int(factor.shape[1])
        s: dict[str, Any] = {"blocks_B": blocks, "columns_K": k}
        # (a) the twin's own draw, seed by seed
        values, repro = [], []
        for seed in SEED_UNIT_SEEDS:
            got = pilot.baseline_ic_by_column(factor, expression, seed, params)
            values.append(got)
            if seed in pilot.NULL_PROBE_SEEDS:
                key = pilot.PilotCell(expression, 0.0, seed, baseline=True).key()
                rec = task94.loc[task94["key"] == key, "realised_ic_by_column"]
                want = float(rec.iloc[0]) if len(rec) == 1 else float("nan")
                gap = abs(got - want)
                ok = bool(np.isfinite(gap) and gap <= REPRO_TOL)
                reproduced &= ok
                repro.append({"seed": seed, "task94": want, "probe": got, "gap": gap, "ok": ok})
        mean, sd = _mean_sd(values)
        se = 1.0 / np.sqrt(blocks * k) / np.sqrt(len(values))
        z = mean / se
        s["seed_unit"] = {
            "values": [{"seed": n, "ic": v} for n, v in zip(SEED_UNIT_SEEDS, values, strict=True)],
            "reproduction": repro,
            "n": len(values),
            "mean": mean,
            "sd": sd,
            "theoretical_se": float(se),
            "z": float(z),
            "beyond_3": bool(abs(z) > STOP_Z),
        }
        # (b) the shuffle itself, truth only
        truth = plant_axis_signal(factor, 0.0, pilot.PILOT_HORIZON, 0, expression, params).truth
        corr = [
            shuffle_correlation(truth, pilot.null_shuffle_rng(SHUFFLE_SEED, d))
            for d in range(SHUFFLE_DRAWS)
        ]
        cm, csd = _mean_sd(corr)
        band = 3.0 * csd / np.sqrt(SHUFFLE_DRAWS)
        n_blocks = int(np.ceil(len(truth) / BASELINE_BLOCK))
        s["shuffle"] = {
            "n": SHUFFLE_DRAWS,
            "mean": cm,
            "sd": csd,
            "three_sd_over_sqrt_n": float(band),
            "n_blocks": n_blocks,
            "one_over_n_blocks": 1.0 / n_blocks,
            "rows": len(truth),
            "triggers": bool(cm > STOP_SHUFFLE_MEAN and abs(cm) > band),
        }
        # (c) the twin's design, report only
        check = plant_variant(factor, 0.35, 0, expression, params, True, "k").score
        built = plant_axis_signal(factor, 0.35, pilot.PILOT_HORIZON, 0, expression, params, True)
        gap_k = float(np.nanmax(np.abs((check - built.score).to_numpy(float))))
        s["variant_k_reproduces_build"] = gap_k
        if not gap_k <= 1e-12:
            reproduced = False
        table = {}
        for ic in VARIANT_ICS:
            for variant in VARIANTS:
                live, twin = [], []
                for seed in SEED_UNIT_SEEDS:
                    lp = plant_variant(factor, ic, seed, expression, params, False, variant)
                    tp = plant_variant(factor, ic, seed, expression, params, True, variant)
                    live.append(realised_ic(lp)["by_column_mean"])
                    twin.append(realised_ic(tp)["by_column_mean"])
                diff = np.asarray(live) - np.asarray(twin)
                table[f"ic{ic:.2f}_{variant}"] = {
                    "ic": ic,
                    "variant": variant,
                    "live": _mean_sd(live),
                    "twin": _mean_sd(twin),
                    "live_minus_twin": _mean_sd(diff),
                }
        s["variants"] = table
        stop |= s["seed_unit"]["beyond_3"] or s["shuffle"]["triggers"]
        summary[expression] = s

        su, sh = s["seed_unit"], s["shuffle"]
        md += [
            f"## {expression} ({pilot.AXIS_OF_EXPRESSION[expression]}), B {blocks}, K {k}",
            "",
            "### (a) The seed as the unit: each seed's twin, its own draw (`baseline_rng(seed)`)",
            "",
            "| seed | " + " | ".join(str(x) for x in SEED_UNIT_SEEDS) + " |",
            "|---|" + "---|" * len(SEED_UNIT_SEEDS),
            "| IC | " + " | ".join(f"{v:+.3f}" for v in values) + " |",
            "",
            "Reproduction of task 94 (seeds 0 to 4, tolerance 1e-9): max gap "
            f"{max(r['gap'] for r in repro):.1e}, {'held' if all(r['ok'] for r in repro) else 'FAILED'}.",
            "",
            "| n | mean | SD | SE = 1/sqrt(BxK)/sqrt(n) | z = mean/SE | abs(z) > 3 |",
            "|---|---|---|---|---|---|",
            f"| {su['n']} | {mean:+.4f} | {sd:.4f} | {se:.4f} | {z:+.2f} | "
            f"{'YES' if su['beyond_3'] else 'no'} |",
            "",
            f"### (b) The shuffle itself: corr(block_shuffle_rows(truth), truth), "
            f"`null_shuffle_rng({SHUFFLE_SEED}, d)`, d 0 to {SHUFFLE_DRAWS - 1}",
            "",
            "| n | mean | SD | 3 SD/sqrt(n) | 1/(blocks) | blocks (rows) | mean > 0.05 and beyond band |",
            "|---|---|---|---|---|---|---|",
            f"| {sh['n']} | {cm:+.4f} | {csd:.4f} | {band:.4f} | {1.0 / n_blocks:.4f} | "
            f"{n_blocks} ({len(truth)}) | {'YES' if sh['triggers'] else 'no'} |",
            "",
            "### (c) The twin's design (report only; the owner's, decisions/proposed/0072)",
            "",
            f"Mean (SD) over {len(SEED_UNIT_SEEDS)} seeds of `realised_ic_by_column`. Variant (k) "
            f"reproduces `plant_axis_signal` to {gap_k:.1e}.",
            "",
            "| IC | variant | live | twin | live - twin |",
            "|---|---|---|---|---|",
            *[
                f"| {r['ic']:.2f} | ({r['variant']}) {VARIANT_NAMES[r['variant']]} | "
                f"{r['live'][0]:+.4f} ({r['live'][1]:.4f}) | {r['twin'][0]:+.4f} ({r['twin'][1]:.4f}) | "
                f"{r['live_minus_twin'][0]:+.4f} ({r['live_minus_twin'][1]:.4f}) |"
                for r in table.values()
            ],
            "",
        ]
    summary["reproduced"] = bool(reproduced)
    summary["stop_branch"] = bool(stop)
    md += [
        "## Reading (task 99 step 1's stop branch, decisions/0073's reversal)",
        "",
        f"Reproduction: {'held' if reproduced else 'FAILED'}. "
        + (
            "STOP BRANCH: (b)'s mean is above 0.05 and beyond 3 SD/sqrt(200), or abs(z) in (a) "
            "is above 3, in at least one expression."
            if stop
            else "Not the stop branch: in both expressions (b)'s mean is not both above 0.05 and "
            "beyond 3 SD/sqrt(200), and abs(z) in (a) is at most 3."
        ),
        "",
    ]
    return summary, md, reproduced


# ---------------------------------------------------------------------------------------------
# HANDOFF task 99 step 2 (task 98's step 2): the report on the null grid, pooled with task 94's
# IC 0 rows. `--part report --null-run <run_id>`; writes `report.md` and `summary.json`.
# ---------------------------------------------------------------------------------------------

SIGN_SHARE = 2.0 / 3.0
EXPLAINED_SHARE = 2.0 / 3.0


def _stats(x: pd.Series) -> dict[str, float]:
    x = x.astype(float).dropna()
    return {
        "n": int(len(x)),
        "mean": float(x.mean()),
        "sd": float(x.std(ddof=1)) if len(x) > 1 else float("nan"),
        "min": float(x.min()),
        "max": float(x.max()),
    }


def null_report(
    task94: pd.DataFrame, null: pd.DataFrame, target: float, seed_ic: dict[str, dict[int, float]]
) -> tuple[dict[str, Any], list[str]]:
    """Per expression: task 94's IC 0 rows (seeds 0-4, prior x1) pooled with the null grid's."""
    old = task94[(task94["ic"] == 0.0) & (task94["ic_prior_multiplier"] == 1.0)].copy()
    old["source"] = TASK94_RUN
    zero_mask = null["zero_scores"].astype(bool)
    zero = null[zero_mask]
    new = null[~zero_mask].copy()
    new["source"] = "null grid"
    common = [c for c in old.columns if c in new.columns]
    pooled = pd.concat([old[common], new], ignore_index=True)
    factor_names = [
        c[len("fx_") : -len("_explained_annual")]
        for c in null.columns
        if c.startswith("fx_") and c.endswith("_explained_annual") and c != "fx_explained_annual"
    ]
    summary: dict[str, Any] = {"target_net_ir": target, "factors": factor_names}
    md = [
        "# Task 99 step 2: the pilot's null over ten more seeds, and the zero-view floor",
        "",
        f"IC 0, h 13, the decisions/0070 defaults. Pooled: task 94's IC 0 rows (`{TASK94_RUN}`, "
        "seeds 0 to 4) and the null grid's (seeds 5 to 14). Bar 1's `target_net_ir` "
        f"{target:.2f} (params/audit.yaml), read as a share only; no verdict. HANDOFF task 99.",
        "",
    ]
    readings = {}
    for expression in pilot.AXIS_OF_EXPRESSION:
        p = pooled[pooled["expression"] == expression]
        live = p[~p["baseline"].astype(bool)]
        twins = p[p["baseline"].astype(bool)]
        n_live = int(len(live))
        hit = live["net_ir"] >= target
        pos = live["net_ir_excess"] > 0
        z = zero[zero["expression"] == expression]
        zr = z.iloc[0] if len(z) else None
        # the attribution: the null grid's live IC 0 runs (task 94's rows carry no fx_ columns)
        nl = new[(new["expression"] == expression) & ~new["baseline"].astype(bool)]
        active_mean = float(nl["active_return_annual"].mean())
        fac = []
        sign_ok_explained = 0.0
        for name in factor_names:
            contrib = nl[f"fx_{name}_explained_annual"].astype(float)
            m = float(contrib.mean())
            same = int((np.sign(contrib) == np.sign(m)).sum())
            holds = same >= SIGN_SHARE * len(contrib)
            if holds:
                sign_ok_explained += m
            fac.append(
                {
                    "factor": name,
                    "exposure_mean": float(nl[f"fx_{name}_exposure_mean"].mean()),
                    "explained_mean": m,
                    "seeds_with_sign_of_mean": same,
                    "seeds": int(len(contrib)),
                    "sign_holds": bool(holds),
                }
            )
        unexplained = float(nl["fx_unexplained_annual"].mean())
        share = sign_ok_explained / active_mean if active_mean != 0 else float("nan")
        zero_ir = float(zr["net_ir"]) if zr is not None else float("nan")
        premium = bool(zero_ir <= 0.0 and active_mean > 0 and share >= EXPLAINED_SHARE)
        ic_check = [
            abs(float(r["realised_ic_by_column"]) - seed_ic[expression][int(r["seed"])])
            for _, r in new[
                (new["expression"] == expression) & new["baseline"].astype(bool)
            ].iterrows()
            if int(r["seed"]) in seed_ic.get(expression, {})
        ]
        s = {
            "n_live": n_live,
            "n_twins": int(len(twins)),
            "net_ir": _stats(live["net_ir"]),
            "net_ir_excess": _stats(live["net_ir_excess"]),
            "share_net_ir_ge_target": float(hit.mean()),
            "share_excess_gt_0": float(pos.mean()),
            "share_both": float((hit & pos).mean()),
            "twins_share_net_ir_ge_target": float((twins["net_ir"] >= target).mean()),
            "twins_net_ir": _stats(twins["net_ir"]),
            "zero_score": None
            if zr is None
            else {
                "key": str(zr["key"]),
                "net_ir": zero_ir,
                "active_return_annual": float(zr["active_return_annual"]),
                "cost_drag_annual": float(zr["cost_drag_annual"]),
                "turnover_annual": float(zr["turnover_annual"]),
                "legacy": bool(zr["legacy"]),
            },
            "attribution_runs": int(len(nl)),
            "active_return_annual_mean": active_mean,
            "factors": fac,
            "unexplained_annual_mean": unexplained,
            "explained_by_sign_holding_factors": sign_ok_explained,
            "explained_share_by_sign_holding_factors": float(share),
            "real_premium": premium,
            "twin_ic_matches_step1_max_gap": float(max(ic_check)) if ic_check else float("nan"),
        }
        summary[expression] = s
        readings[expression] = premium
        ni, ex = s["net_ir"], s["net_ir_excess"]
        zs = s["zero_score"] or {}
        md += [
            f"## {expression} ({pilot.AXIS_OF_EXPRESSION[expression]})",
            "",
            "| | n | mean | SD | min | max |",
            "|---|---|---|---|---|---|",
            f"| net IR, IC 0 live | {ni['n']} | {ni['mean']:+.3f} | {ni['sd']:.3f} | "
            f"{ni['min']:+.3f} | {ni['max']:+.3f} |",
            f"| net_ir_excess | {ex['n']} | {ex['mean']:+.3f} | {ex['sd']:.3f} | "
            f"{ex['min']:+.3f} | {ex['max']:+.3f} |",
            f"| net IR, baseline twins | {s['twins_net_ir']['n']} | "
            f"{s['twins_net_ir']['mean']:+.3f} | {s['twins_net_ir']['sd']:.3f} | "
            f"{s['twins_net_ir']['min']:+.3f} | {s['twins_net_ir']['max']:+.3f} |",
            "",
            f"Shares over the {n_live} IC 0 live runs: net IR >= {target:.2f} "
            f"{s['share_net_ir_ge_target']:.0%}; excess > 0 {s['share_excess_gt_0']:.0%}; both "
            f"{s['share_both']:.0%}. Over the {s['n_twins']} baseline twins: net IR >= "
            f"{target:.2f} {s['twins_share_net_ir_ge_target']:.0%}.",
            "",
            f"Zero-score run (`{zs.get('key', '')}`; the no-view arm keeps its own arguments, "
            f"legacy {zs.get('legacy')}): net IR {zs.get('net_ir', float('nan')):+.3f}, active "
            f"return {zs.get('active_return_annual', float('nan')):+.4f} a year, cost drag "
            f"{zs.get('cost_drag_annual', float('nan')):.4f}, turnover "
            f"{zs.get('turnover_annual', float('nan')):.0%}.",
            "",
            f"Factor attribution, the null grid's {len(nl)} IC 0 live runs (seeds 5 to 14; "
            "exposure at t times the factor's move t to t+1, annualised; task 94's rows carry "
            f"none). Mean active return {active_mean:+.4f} a year.",
            "",
            "| factor | mean active exposure | explained a year | seeds with the mean's sign |",
            "|---|---|---|---|",
            *[
                f"| {f['factor']} | {f['exposure_mean']:+.4f} | {f['explained_mean']:+.4f} | "
                f"{f['seeds_with_sign_of_mean']}/{f['seeds']} |"
                for f in fac
            ],
            f"| unexplained | | {unexplained:+.4f} | |",
            "",
            f"Explained by factors whose sign holds on at least two-thirds of the seeds: "
            f"{sign_ok_explained:+.4f}, {share:.0%} of the mean active return. The twins' "
            "`realised_ic_by_column` matches step 1 (a) seed by seed to "
            f"{s['twin_ic_matches_step1_max_gap']:.1e}.",
            "",
        ]
    summary["readings_real_premium"] = readings
    md += [
        "## Reading, with its basis (reported, not a stop)",
        "",
        "Rule (task 98 step 2): a real premium if the zero-score run's net IR is at most 0 and the "
        "IC 0 runs' mean active return is at least two-thirds explained by factor exposures whose "
        "sign holds on at least two-thirds of the seeds; otherwise say what is unexplained.",
        "",
        *[
            f"- {e}: {'a real premium under the rule' if v else 'not shown to be a real premium under the rule'} "
            f"(zero-score net IR {summary[e]['zero_score']['net_ir']:+.3f}; "
            f"{summary[e]['explained_share_by_sign_holding_factors']:.0%} explained by "
            f"sign-holding factors; unexplained {summary[e]['unexplained_annual_mean']:+.4f} a year)."
            for e, v in readings.items()
        ],
        "",
    ]
    return summary, md


# ---------------------------------------------------------------------------------------------
# HANDOFF task 100 (decisions/0072, decisions/0074). Step 1, `--part accept-check`: the
# reviewer's re-run of the 0072 addendum's table from task 94's and task 99's cells. Step 3,
# `--part accept-report --accept-run <id>`: the acceptance grid's report. Arithmetic only, no
# solves, no acceptance (the acceptance is Cowork's review). Both write under results/pilot_accept/.
# ---------------------------------------------------------------------------------------------

ACCEPT_DIR = Path("results/pilot_accept")
NULL_RUN = "A-20261115-105504"  # task 99's null grid
A2_T = 2.0  # decisions/0072 (a2): slope t >= 2
A2_GAP = 0.10  # decisions/0072 (a2): mean excess at IC 0.35 minus at IC 0 >= 0.10
B1_SHARE = 0.10  # decisions/0072 (b1): at most 10%
GAP_HIGH_IC = 0.35


def ols_slope(x, y) -> dict[str, float]:
    """OLS of y on a constant and x: the slope, its classical standard error and t, and n."""
    xv, yv = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    n = len(xv)
    xc = xv - xv.mean()
    sxx = float(np.dot(xc, xc))
    slope = float(np.dot(xc, yv - yv.mean()) / sxx)
    resid = yv - yv.mean() - slope * xc
    se = float(np.sqrt(np.dot(resid, resid) / (n - 2) / sxx))
    return {"n": int(n), "slope": slope, "se": se, "t": slope / se if se > 0 else float("nan")}


def live_pairs(table: pd.DataFrame) -> pd.DataFrame:
    """The live rows that carry an excess: `IC_prior` x1, no zero-score row, each with its twin
    (`with_excess` applied if the table has no `net_ir_excess` yet)."""
    t = table if "net_ir_excess" in table.columns else pilot.with_excess(table)
    keep = (t["ic_prior_multiplier"].astype(float) == 1.0) & ~t["baseline"].astype(bool)
    if "zero_scores" in t.columns:
        keep &= ~t["zero_scores"].astype(bool)
    out = t[keep].copy()
    return out[out["net_ir_excess"].notna()]


def a2_b1(live: pd.DataFrame, target: float) -> dict[str, Any]:
    """(a2)'s slope, t and gap and (b1)'s count over a set of live rows (one expression)."""
    fit = ols_slope(live["ic"], live["net_ir_excess"])
    by_ic = live.groupby("ic")["net_ir_excess"].mean()
    gap = float(by_ic.get(GAP_HIGH_IC, np.nan) - by_ic.get(0.0, np.nan))
    ic0 = live[live["ic"] == 0.0]
    both = (ic0["net_ir"] >= target) & (ic0["net_ir_excess"] > 0)
    n0 = int(len(ic0))
    return {
        **fit,
        "gap": gap,
        "b1_n": n0,
        "b1_count": int(both.sum()),
        "b1_share": float(both.mean()) if n0 else float("nan"),
    }


def accept_check(task94: pd.DataFrame, null: pd.DataFrame, target: float) -> dict[str, Any]:
    """Step 1: per expression, (a2) and (b1) on the grid's 25 runs and on the 35 pooled."""
    grid = live_pairs(task94)
    nul = live_pairs(null)
    nul = nul[nul["ic"] == 0.0]
    out: dict[str, Any] = {}
    for expression in pilot.AXIS_OF_EXPRESSION:
        g = grid[grid["expression"] == expression]
        p = pd.concat([g, nul[nul["expression"] == expression]], ignore_index=True)
        out[expression] = {"grid": a2_b1(g, target), "pooled": a2_b1(p, target)}
    return out


# the 0072 addendum of 2026-11-15, as written: (slope, t) grid and pooled, gap grid / pooled, b1
ADDENDUM = {
    "cross_sectional": {
        "grid": (0.88, 6.17),
        "pooled": (0.84, 7.28),
        "gap": (0.326, 0.295),
        "b1": 1,
    },
    "directional": {"grid": (0.29, 1.86), "pooled": (0.33, 2.50), "gap": (0.102, 0.120), "b1": 4},
}
TOL_SLOPE, TOL_T, TOL_COUNT = 0.01, 0.05, 1


def compare_addendum(check: dict[str, Any]) -> list[dict[str, Any]]:
    """Each figure beside the addendum's, and whether it is within the task's tolerance. The
    addendum prints the slope to two decimals and the gap to three, so a slope is compared at
    its printed precision plus the tolerance, and a gap at the slope's tolerance."""
    rows = []
    for e, a in ADDENDUM.items():
        c = check[e]
        for part in ("grid", "pooled"):
            rows.append(
                {
                    "expression": e,
                    "figure": f"slope ({part})",
                    "addendum": a[part][0],
                    "check": c[part]["slope"],
                    "tol": TOL_SLOPE + 0.005,
                }
            )
            rows.append(
                {
                    "expression": e,
                    "figure": f"t ({part})",
                    "addendum": a[part][1],
                    "check": c[part]["t"],
                    "tol": TOL_T + 0.005,
                }
            )
        for j, part in enumerate(("grid", "pooled")):
            rows.append(
                {
                    "expression": e,
                    "figure": f"gap ({part})",
                    "addendum": a["gap"][j],
                    "check": c[part]["gap"],
                    "tol": TOL_SLOPE + 0.0005,
                }
            )
        rows.append(
            {
                "expression": e,
                "figure": "b1 count (15)",
                "addendum": a["b1"],
                "check": c["pooled"]["b1_count"],
                "tol": TOL_COUNT,
            }
        )
    for r in rows:
        r["within"] = bool(abs(float(r["check"]) - float(r["addendum"])) <= r["tol"])
    return rows


def accept_check_md(check: dict[str, Any], rows: list[dict[str, Any]], target: float) -> list[str]:
    md = [
        "# Task 100 step 1: the 0072 addendum's table, re-run by the reviewer",
        "",
        f"From `results/audit/{TASK94_RUN}/cells.csv` (the grid, 25 runs an expression) and "
        f"`results/audit/{NULL_RUN}/cells.csv` (the null grid's IC 0 runs, 10 an expression). "
        "Excess = live `net_ir` minus its twin's; `IC_prior` x1; zero-score rows left out. OLS "
        f"with a constant, classical SE. (b1): IC 0 runs with net IR >= {target:.2f} and excess > 0.",
        "",
        "| | region cross-sectional | duration directional |",
        "|---|---|---|",
    ]
    x, d = check["cross_sectional"], check["directional"]
    md += [
        f"| (a2) slope, t: the grid's runs (n {x['grid']['n']} / {d['grid']['n']}) | "
        f"{x['grid']['slope']:.4f}, t {x['grid']['t']:.3f} | {d['grid']['slope']:.4f}, t {d['grid']['t']:.3f} |",
        f"| same, pooled (n {x['pooled']['n']} / {d['pooled']['n']}) | "
        f"{x['pooled']['slope']:.4f}, t {x['pooled']['t']:.3f} | {d['pooled']['slope']:.4f}, t {d['pooled']['t']:.3f} |",
        f"| (a2) gap, grid / pooled | {x['grid']['gap']:.4f} / {x['pooled']['gap']:.4f} | "
        f"{d['grid']['gap']:.4f} / {d['pooled']['gap']:.4f} |",
        f"| (b1) count of {x['pooled']['b1_n']} / {d['pooled']['b1_n']} | "
        f"{x['pooled']['b1_count']} ({x['pooled']['b1_share']:.1%}) | {d['pooled']['b1_count']} ({d['pooled']['b1_share']:.1%}) |",
        "",
        "Beside the addendum (tolerance: 0.01 a slope or gap, 0.05 a t, one run a count; the "
        "addendum's printed rounding added):",
        "",
        "| expression | figure | addendum | check | within |",
        "|---|---|---|---|---|",
        *[
            f"| {r['expression']} | {r['figure']} | {r['addendum']} | {float(r['check']):.4f} | "
            f"{'yes' if r['within'] else 'NO'} |"
            for r in rows
        ],
        "",
        f"All within: {'yes' if all(r['within'] for r in rows) else 'NO'}.",
        "",
    ]
    return md


def accept_report(table: pd.DataFrame, target: float) -> tuple[dict[str, Any], list[str]]:
    """Step 3: the acceptance grid's report (region cross-sectional, seeds 15 to 29)."""
    t = pilot.with_excess(table) if "net_ir_excess" not in table.columns else table
    live = live_pairs(t)
    twins = t[t["baseline"].astype(bool)]
    per_ic = []
    for ic in sorted(t["ic"].astype(float).unique()):
        lv = live[live["ic"] == ic]
        tw = twins[twins["ic"] == ic]
        per_ic.append(
            {
                "ic": float(ic),
                "net_ir": _stats(lv["net_ir"]),
                "net_ir_excess": _stats(lv["net_ir_excess"]),
                "realised_ic_live": _stats(lv["realised_ic_by_column"]),
                "realised_ic_twin": _stats(tw["realised_ic_by_column"]),
            }
        )
    fit = a2_b1(live, target)
    twin_share = float((twins["net_ir"] >= target).mean())
    a2 = bool(fit["t"] >= A2_T and fit["gap"] >= A2_GAP)
    b1 = bool(fit["b1_share"] <= B1_SHARE)
    summary = {
        "target_net_ir": target,
        "n_runs": int(len(t)),
        "n_pairs": int(len(live)),
        "seeds": sorted(int(s) for s in t["seed"].unique()),
        "per_ic": per_ic,
        "slope": fit["slope"],
        "slope_se": fit["se"],
        "slope_t": fit["t"],
        "gap": fit["gap"],
        "b1_n": fit["b1_n"],
        "b1_count": fit["b1_count"],
        "b1_share": fit["b1_share"],
        "twins_share_net_ir_ge_target": twin_share,
        "lookahead_passed_all": bool(t["lookahead_passed"].astype(bool).all()),
        "arithmetic": {
            "a2_t_ge_2": bool(fit["t"] >= A2_T),
            "a2_gap_ge_0.10": bool(fit["gap"] >= A2_GAP),
            "a2_met": a2,
            "b1_le_10pct": b1,
        },
    }

    def row(name: str, s: dict[str, float]) -> str:
        return (
            f"| {name} | {s['n']} | {s['mean']:+.4f} | {s['sd']:.4f} | {s['min']:+.4f} | "
            f"{s['max']:+.4f} |"
        )

    md = [
        "# Task 100 step 3: the pilot's acceptance run, region cross-sectional, seeds 15 to 29",
        "",
        "decisions/0074 (delegated), judged by decisions/0072's (a2) and (b1) as arithmetic only; "
        "the acceptance itself is Cowork's review. Planted data, the decisions/0070 defaults, h 13, "
        f"`IC_prior` x1. {summary['n_runs']} runs, {summary['n_pairs']} live/twin pairs. Lookahead "
        f"passed on every run: {'yes' if summary['lookahead_passed_all'] else 'NO'}.",
        "",
        "## Per planted IC",
        "",
        "| IC | quantity | n | mean | SD | min | max |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in per_ic:
        for name, key in (
            ("net IR", "net_ir"),
            ("net_ir_excess", "net_ir_excess"),
            ("realised IC, live", "realised_ic_live"),
            ("realised IC, twin", "realised_ic_twin"),
        ):
            md.append(f"| {p['ic']:.2f} " + row(name, p[key]))
    md += [
        "",
        "## The bars, as arithmetic",
        "",
        f"- OLS slope of excess on planted IC over the {summary['n_pairs']} pairs: "
        f"{fit['slope']:.4f} (SE {fit['se']:.4f}), t {fit['t']:.3f}. (a2) t >= 2: "
        f"{'meets' if summary['arithmetic']['a2_t_ge_2'] else 'does not meet'}.",
        f"- Gap, mean excess at IC 0.35 minus at IC 0: {fit['gap']:+.4f}. (a2) gap >= 0.10: "
        f"{'meets' if summary['arithmetic']['a2_gap_ge_0.10'] else 'does not meet'}.",
        f"- IC 0 pairs with net IR >= {target:.2f} and excess > 0: {fit['b1_count']} of "
        f"{fit['b1_n']} ({fit['b1_share']:.1%}). (b1) <= 10%: "
        f"{'meets' if b1 else 'does not meet'}.",
        f"- Baseline twins with net IR >= {target:.2f}: {twin_share:.1%} of {len(twins)}.",
        "",
    ]
    return summary, md


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
    ap.add_argument(
        "--part",
        choices=("task98", "task99", "report", "accept-check", "accept-report"),
        default="task98",
        help="task98: 40 shuffles a seed, seeds 0-4 (ic_report.md); task99: the seed as the "
        "unit over seeds 0-14, the shuffle itself, the twin's design (seed_report.md); report: "
        "the null grid's report (report.md, summary.json; needs --null-run)",
    )
    ap.add_argument("--null-run", default=None, help="the phase2-pilot-null run id (--part report)")
    ap.add_argument(
        "--accept-run", default=None, help="the phase2-pilot-accept run id (--part accept-report)"
    )
    args = ap.parse_args(argv)

    from signal_lab.params import get_params

    params = get_params()
    started = time.time()
    if args.part in ("accept-check", "accept-report"):
        out = Path(args.out) if args.out != str(OUT_DIR) else ACCEPT_DIR
        out.mkdir(parents=True, exist_ok=True)
        target = float(params.require("audit.target_net_ir"))
        if args.part == "accept-check":
            task94 = pd.read_csv(AUDIT_DIR / TASK94_RUN / "cells.csv")
            null = pd.read_csv(AUDIT_DIR / NULL_RUN / "cells.csv")
            check = accept_check(task94, null, target)
            rows = compare_addendum(check)
            md = accept_check_md(check, rows, target)
            ok = all(r["within"] for r in rows)
            payload = {
                "task94_run": TASK94_RUN,
                "null_run": NULL_RUN,
                "target_net_ir": target,
                "check": check,
                "beside_addendum": rows,
                "all_within": ok,
            }
            (out / "accept_check.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            (out / "accept_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
            print("\n".join(md))
            print(f"pilot-null: wrote {out}/accept_check.md and accept_check.json")
            return 0 if ok else 5
        if not args.accept_run:
            print("pilot-null: --part accept-report needs --accept-run", file=sys.stderr)
            return 2
        table = pd.read_csv(AUDIT_DIR / args.accept_run / "cells.csv")
        summary, md = accept_report(table, target)
        summary["accept_run"] = args.accept_run
        summary["seconds_per_run_mean"] = float(table["seconds"].mean())
        summary["seconds_total_runs"] = float(table["seconds"].sum())
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )
        (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print("\n".join(md))
        print(f"pilot-null: wrote {out}/report.md and summary.json")
        return 0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.part == "report":
        if not args.null_run:
            print("pilot-null: --part report needs --null-run", file=sys.stderr)
            return 2
        task94 = pilot.with_excess(pd.read_csv(AUDIT_DIR / TASK94_RUN / "cells.csv"))
        null = pd.read_csv(AUDIT_DIR / args.null_run / "cells.csv")
        step1 = json.loads((out / "seed_summary.json").read_text(encoding="utf-8"))
        seed_ic = {
            e: {int(v["seed"]): float(v["ic"]) for v in step1[e]["seed_unit"]["values"]}
            for e in pilot.AXIS_OF_EXPRESSION
        }
        target = float(params.require("audit.target_net_ir"))
        summary, md = null_report(task94, null, target, seed_ic)
        summary["null_run"] = args.null_run
        summary["task94_run"] = TASK94_RUN
        summary["seconds"] = round(time.time() - started, 1)
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )
        (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print("\n".join(md))
        print(f"pilot-null: wrote {out}/report.md and summary.json")
        return 0
    print("pilot-null: building the pilot's inputs", flush=True)
    inputs = _inputs(params)
    task94 = pd.read_csv(AUDIT_DIR / TASK94_RUN / "cells.csv")
    step, stem = (ic_step, "ic") if args.part == "task98" else (task99_step, "seed")
    summary, md, reproduced = step(inputs, params, task94)
    summary["seconds"] = round(time.time() - started, 1)
    summary["threads"] = THREADS
    (out / f"{stem}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / f"{stem}_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(
        f"pilot-null: wrote {out}/{stem}_report.md and {stem}_summary.json in {summary['seconds']} s"
    )
    return 0 if reproduced else 4


if __name__ == "__main__":
    sys.exit(main())
