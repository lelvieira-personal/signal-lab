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
        choices=("task98", "task99", "report"),
        default="task98",
        help="task98: 40 shuffles a seed, seeds 0-4 (ic_report.md); task99: the seed as the "
        "unit over seeds 0-14, the shuffle itself, the twin's design (seed_report.md); report: "
        "the null grid's report (report.md, summary.json; needs --null-run)",
    )
    ap.add_argument("--null-run", default=None, help="the phase2-pilot-null run id (--part report)")
    args = ap.parse_args(argv)

    from signal_lab.params import get_params

    params = get_params()
    started = time.time()
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
