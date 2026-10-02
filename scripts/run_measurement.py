#!/usr/bin/env python3
"""
The loading-estimator test of decisions/0046 (HANDOFF task 45).

    make measurement-loadings            # time it first; stop if it projects past 3 h
    make measurement-loadings ARGS=--time-only

Six weekly factors, the rolling-OLS incumbent and four candidates (H-2026-0013 to
0016), every investable backbone and second-tier instrument, development window
only. A MEASUREMENT test: no portfolio, no net IR, no signal. It chooses nothing;
the report is numbers, and adopting an estimator is the owner's decision.

Writes `results/measurement/M-<stamp>/`:
  summary.json    hashes, sample, per estimator the statistic, adjusted p, gate, bias, slices
  loadings.parquet  instrument, date, estimator, factor, loading, se   (git-ignored data)
  report.md       the same, readable, plus the factor correlations and the
                  measured-against-estimated check of decisions/0046 section 1

Factor series are vendor data and are never written here; loadings, losses and
correlations are model output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap  # noqa: F401
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO_ROOT / "results" / "measurement"
HYPOTHESES = ("H-2026-0013", "H-2026-0014", "H-2026-0015", "H-2026-0016")
BY_HYPOTHESIS = dict(
    zip(
        HYPOTHESES,
        (
            "huber_m",
            "theil_goldberger_peer_prior",
            "hmm2_regime_conditional",
            "kalman_dlm_discount",
        ),
        strict=True,
    )
)
MAX_SECONDS = 3 * 3600
TREASURY_CLASSES = ("Treasuries", "Long Treasuries")
CREDIT_CLASSES = ("IG Corporates",)


def _frame_hash(*frames: pd.DataFrame) -> str:
    h = hashlib.sha256()
    for f in frames:
        h.update(",".join(map(str, f.columns)).encode())
        h.update(np.ascontiguousarray(f.fillna(-999.0).to_numpy(dtype=float)).tobytes())
    return h.hexdigest()


def load_inputs(params):
    from signal_lab.audit.universe import _development_window, read_investable_flags
    from signal_lab.loaders.bloomberg import BloombergLoader, read_universe
    from signal_lab.measurement.factors import build_factors

    loader = BloombergLoader(params)
    panel = loader.load_returns()
    bench = loader.load_benchmark()
    analytics = loader.load_analytics()
    ff = build_factors(panel, bench, analytics, params)
    start = pd.Timestamp(params.require("data.windows.dev_start"))
    end = pd.Timestamp(params.require("data.windows.dev_end"))
    ff.frame = ff.frame.loc[(ff.frame.index >= start) & (ff.frame.index <= end)]
    complete = ff.frame.notna().all(axis=1)
    ff.common_start = pd.Timestamp(complete[complete].index[0])
    ff.n_weeks = int(complete.sum())
    dev_panel = _development_window(panel, params)
    universe_rows = read_universe(loader.universe_dir)
    flags = read_investable_flags()
    return dev_panel, analytics, ff, universe_rows, flags


def select_instruments(panel, universe_rows, flags) -> tuple[list[str], list[str]]:
    """Investable, unhedged, backbone and second tier; never a benchmark leg."""
    ids, classes = [], []
    for sid, meta in panel.meta.items():
        row = universe_rows.get(sid, {})
        if (
            sid in panel.returns.columns
            and not meta.hedged
            and not str(meta.section).startswith("18.")
            and flags.get(sid, False)
            and meta.tier in ("backbone", "second")
            and row.get("reporting_class")
        ):
            ids.append(sid)
            classes.append(str(row["reporting_class"]))
    return ids, classes


def weekly_inputs(panel, ids, ff):
    from signal_lab.portfolio.covariance import period_returns

    weekly = period_returns(panel.returns[ids], ff.dates).reindex(ff.frame.index)
    return weekly


def check_table(analytics, ids, classes, paths, weeks, ff) -> list[dict]:
    """
    The built-in sanity check of decisions/0046 section 1: a Treasury bucket's real-yield
    loading should sit near minus its measured OAD, and an IG corporate index's credit
    loading near minus its duration. Medians over the weeks scored. Not a score.
    """
    from signal_lab.measurement.factors import weekly_levels

    if "INDEX_OAD_TSY" not in analytics.fields:
        return []
    oad = analytics.fields["INDEX_OAD_TSY"]
    factors = list(ff.frame.columns)
    rows = []
    for i, (sid, klass) in enumerate(zip(ids, classes, strict=True)):
        if klass in TREASURY_CLASSES:
            factor = "real_yield"
        elif klass in CREDIT_CLASSES:
            factor = "credit"
        else:
            continue
        if sid not in oad.columns:
            continue
        k = factors.index(factor)
        measured = -weekly_levels(oad[sid], ff.dates).reindex(weeks)
        row = {"instrument": sid, "class": klass, "factor": factor}
        for name, plist in paths.items():
            p = plist[i]
            sel = np.flatnonzero(p.has())
            row[name] = float(np.nanmedian(p.beta[sel, k])) if len(sel) else None
        sel = np.flatnonzero(paths["rolling_ols"][i].has())
        row["minus_measured_oad"] = (
            float(np.nanmedian(measured.to_numpy()[sel])) if len(sel) else None
        )
        rows.append(row)
    return rows


def write_report(out: Path, summary: dict, corr: dict, checks: list[dict]) -> None:
    est = summary["score"]["estimators"]
    lines = [
        f"# Loading-estimator test, {summary['run_id']}",
        "",
        *(
            [
                f"**SENSITIVITY RUN, not the registered test.** Excludes reporting class "
                f"{summary['excluded_classes']}. No hypothesis was moved by this run; the "
                f"registered run is the one without exclusions.",
                "",
            ]
            if summary["sensitivity"]
            else []
        ),
        "A measurement run (decisions/0016, decisions/0046): out-of-sample loading fidelity "
        "against rolling OLS. No portfolio, no net IR. **The run chooses nothing**; adoption "
        "is the owner's decision.",
        "",
        f"- Sample: {summary['sample']['common_start']} to {summary['sample']['last_week']}; "
        f"{summary['sample']['n_weeks_all_factors']} weeks with all six factors; "
        f"{summary['score']['n_weeks_scored']} weeks and {summary['sample']['n_instruments']} "
        f"instruments scored ({summary['score']['n_cells_scored']} instrument-weeks).",
        f"- Units: {summary['units']}",
        f"- Gate: `{summary['score']['gate']['procedure']}`, alpha {summary['score']['gate']['fwer_alpha']}, "
        f"g = {summary['score']['gate']['g']}, {summary['score']['gate']['n_tests']} candidates, "
        f"{summary['score']['gate']['n_shuffles']} centred block-bootstrap draws "
        f"({summary['score']['gate']['block_weeks']}-week blocks).",
        f"- Hashes: params `{summary['hashes']['params_hash'][:16]}`, returns "
        f"`{summary['hashes']['weekly_returns_hash'][:16]}`, factors "
        f"`{summary['hashes']['factors_hash'][:16]}`.",
        "",
        "## Estimators",
        "",
        "Statistic: mean over weeks of the cross-sectional mean of (incumbent loss - candidate "
        "loss), Huber loss on volatility-scaled errors; positive is better than rolling OLS.",
        "",
        "| estimator | statistic | adj. p | gate | worst-year bias | year | bias check | "
        "top-decile moves | 2004-07 | 2008-09 | 2010-19 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, e in est.items():
        if "statistic" in e:
            s = e["slices"]
            lines.append(
                f"| {name} | {e['statistic']:.3e} | {e['p_adjusted']:.3f} | "
                f"{'pass' if e['gate_passed'] else 'fail'} | {e['worst_annual_bias']:.2f} | "
                f"{e['worst_year']} | {'pass' if e['bias_ok'] else 'fail'} | "
                f"{s['top_decile_factor_moves']:.2e} | {s['2004-2007']:.2e} | "
                f"{s['2008-2009']:.2e} | {s['2010-2019']:.2e} |"
            )
        else:
            lines.append(
                f"| {name} (incumbent) | - | - | - | {e['worst_annual_bias']:.2f} | "
                f"{e['worst_year']} | {'pass' if e['bias_ok'] else 'fail'} | - | - | - | - |"
            )
    lines += [
        "",
        f"Bias ceiling: {summary['bias_ceiling']} (`vetoes.risk_calibration.max_worst_annual_bias`).",
        "",
        "## Verdicts recorded",
        "",
    ]
    for hid, v in summary["verdicts"].items():
        lines.append(f"- {hid} ({BY_HYPOTHESIS[hid]}): {v}")
    lines += [
        "",
        "## HMM regime stability across restarts",
        "",
        "```json",
        json.dumps(summary["hmm_stability"], indent=2),
        "```",
        "",
        "## Factor correlations",
        "",
        "Full sample:",
        "",
        pd.DataFrame(corr["full_sample"]).round(2).to_markdown()
        if hasattr(pd.DataFrame, "to_markdown") and _has_tabulate()
        else "```\n" + pd.DataFrame(corr["full_sample"]).round(2).to_string() + "\n```",
        "",
        "Range of the rolling 156-week correlation, by pair:",
        "",
    ]
    for pair, r in corr["rolling_156w_range"].items():
        lines.append(f"- {pair}: {r['min']:.2f} to {r['max']:.2f}")
    lines += ["", "## Measured against estimated (decisions/0046 section 1)", ""]
    if checks:
        cols = ["instrument", "class", "factor", "minus_measured_oad", *summary["estimators"]]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * len(cols))
        for r in checks:
            lines.append(
                "| "
                + " | ".join(
                    f"{r[c]:.2f}" if isinstance(r.get(c), float) else str(r.get(c)) for c in cols
                )
                + " |"
            )
        lines += ["", "Median over the weeks scored. A check on the harness, not a score."]
    else:
        lines.append("INDEX_OAD_TSY is not in the analytics panel; the check could not be made.")
    lines += [
        "",
        "## Known limitation",
        "",
        "Asian and European closes lead the US close by part of a day, which biases a weekly "
        "beta slightly toward zero. Reported, not corrected, in this first test.",
        "",
    ]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
    except ImportError:
        return False
    return True


def main(argv=None) -> int:
    from signal_lab.harness.hypotheses import HypothesisRegistry
    from signal_lab.measurement import estimators as E
    from signal_lab.measurement import fidelity, run
    from signal_lab.params import get_params
    from signal_lab.results.store import ResultsStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--time-only", action="store_true", help="time ten instruments, project, stop"
    )
    parser.add_argument("--time-limit", type=float, default=MAX_SECONDS, help="projected seconds")
    parser.add_argument("--out-root", default=str(OUT_ROOT))
    parser.add_argument("--no-registry", action="store_true", help="do not move hypotheses")
    parser.add_argument(
        "--exclude-class",
        action="append",
        default=[],
        help="a SENSITIVITY run without a reporting class; never moves hypotheses",
    )
    args = parser.parse_args(argv)

    params = get_params()
    started = time.time()
    panel, analytics, ff, universe_rows, flags = load_inputs(params)
    ids, classes = select_instruments(panel, universe_rows, flags)
    sensitivity = bool(args.exclude_class)
    if sensitivity:
        keep = [i for i, c in enumerate(classes) if c not in args.exclude_class]
        ids, classes = [ids[i] for i in keep], [classes[i] for i in keep]
        args.no_registry = True  # a sensitivity run is not the registered test
    weekly = weekly_inputs(panel, ids, ff)
    R, F = weekly.to_numpy(dtype=float), ff.frame.to_numpy(dtype=float)
    weeks = ff.frame.index
    print(
        f"{len(ids)} instruments, {len(weeks)} weeks ({weeks[0].date()} to {weeks[-1].date()}), "
        f"{ff.n_weeks} with all six factors from {ff.common_start.date()}; "
        f"credit read as {ff.units['credit']}."
    )

    proj = run.project_runtime(R, F, classes)
    print(
        f"timing: HMM {proj['hmm_seconds_per_fit']:.2f}s a fit x {int(proj['hmm_fits'])} fits, "
        f"{proj['seconds_per_instrument']:.1f}s an instrument x {len(ids)}; projected "
        f"{proj['projected_seconds'] / 3600:.2f} h."
    )
    if args.time_only:
        return 0
    if proj["projected_seconds"] > args.time_limit:
        print(
            f"STOP: the full run projects to {proj['projected_seconds'] / 3600:.2f} h, past the "
            f"{args.time_limit / 3600:.1f} h limit. Nothing was run.",
            file=sys.stderr,
        )
        return 3

    registry = None
    if not args.no_registry:
        registry = HypothesisRegistry(store=ResultsStore())
    run_id = "M-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ("-sens" if sensitivity else "")
    out = Path(args.out_root) / run_id
    if out.exists():
        print(f"{out} exists; never overwritten", file=sys.stderr)
        return 1
    if registry is not None:
        for hid in HYPOTHESES:
            registry.move(hid, "running", run_id=run_id, detail="HANDOFF task 45")

    print("fitting the regime model (one HMM a week)...", flush=True)
    regimes = E.regime_path(F)
    print(f"  {len(regimes.rows)} fits in {time.time() - started:.0f}s; estimating...", flush=True)
    paths = run.estimate_all(R, F, classes, regimes)
    print(f"  estimated at {time.time() - started:.0f}s; scoring...", flush=True)

    ev = fidelity.evaluate(R, F, paths, run.ALL_NAMES, weeks)
    score = fidelity.score(ev, ff.frame, params)
    verdicts = {hid: score["estimators"][name]["verdict"] for hid, name in BY_HYPOTHESIS.items()}
    corr = run.factor_correlations(ff.frame)
    checks = check_table(analytics, ids, classes, paths, weeks, ff)

    out.mkdir(parents=True)
    long = run.loadings_long(paths, ids, weeks, list(ff.frame.columns))
    long.to_parquet(out / "loadings.parquet", index=False)
    summary = {
        "run_id": run_id,
        "decision": "decisions/0046",
        "sensitivity": sensitivity,
        "excluded_classes": list(args.exclude_class),
        "hashes": {
            "params_hash": params.params_hash,
            "params_version": params.params_version,
            "weekly_returns_hash": _frame_hash(weekly),
            "factors_hash": _frame_hash(ff.frame),
        },
        "sample": {
            "common_start": str(ff.common_start.date()),
            "last_week": str(weeks[-1].date()),
            "n_weeks_all_factors": ff.n_weeks,
            "n_instruments": len(ids),
        },
        "units": ff.units,
        "estimators": run.ALL_NAMES,
        "bias_ceiling": float(params.require("vetoes.risk_calibration.max_worst_annual_bias")),
        "score": score,
        "verdicts": verdicts,
        "hmm_stability": run.hmm_stability(regimes),
        "factor_correlations": corr,
        "projection": proj,
        "runtime_seconds": time.time() - started,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )
    write_report(out, summary, corr, checks)

    if registry is not None:
        for hid, verdict in verdicts.items():
            registry.move(hid, "done", run_id=run_id, detail="HANDOFF task 45", verdict=verdict)
    print(f"wrote {out} in {time.time() - started:.0f}s")
    for name, e in score["estimators"].items():
        if "statistic" in e:
            print(
                f"  {name}: stat {e['statistic']:.3e}, adj p {e['p_adjusted']:.3f}, gate "
                f"{'pass' if e['gate_passed'] else 'fail'}, bias {e['worst_annual_bias']:.2f} "
                f"{'ok' if e['bias_ok'] else 'FAIL'} -> {e['verdict']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
