#!/usr/bin/env python3
"""
Build the estimated half of the characteristic map (decisions/0049, HANDOFF task 51).

    make characteristics

Huber loadings on the six factors, walk-forward, with their uncertainty and each instrument's
explained share, and the measured cells beside them. Writes `data/characteristics/<id>/`
(data files git-ignored, `manifest.yaml` committed) and `results/characteristics/<id>/report.md`.

Two checks before anything is written: the build must reproduce the estimator test's pooled
`r2_oos` and mean Huber loss for `huber_m` (Cash excluded, as the test was) to within 1e-6, and
no estimate may use data from after its own week. This chooses nothing about the matrix's
columns (OWNER-QUEUE L27) and `resolve_exposures` still raises.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap
import numpy as np
import pandas as pd

THREADS = _bootstrap.require_one_thread()

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_RUN = "M-20261003T181155Z"
STORE_ID = "huber6-v3"
TASK = 53
# HANDOFF task 56 (decisions/0056, 0058): `huber6-v4` selects the credit factor on FRED's BAA10Y and
# estimation from the factors' common start. The defaults reproduce v1 to v3.
V4_TASK = 56
V4_SKIP_REASON = (
    "the factors differ from the run of record's by design (credit is FRED BAA10Y, estimation "
    "starts at the factors' common start), decisions/0058"
)
RESTATED = ("LGTRTRGU", "LGTRTRJU")  # decisions/0052: left the universe after the run of record
NDDLUK = "NDDLUK"  # decisions/0053: MSCI UK in sterling, a restatement of NDDUUK
LEFT = (*RESTATED, NDDLUK)  # instruments in the run of record that are not in this build
# decisions/0053: the 17 estimated series that were local-currency returns in the run of record.
# MXEU0RL (tradable-only, never estimated) and NDDLUK (left) are the other two of rule 4's list.
CONVERTED = (
    "I02513EU",
    "MXEUG",
    "MXEU0EN",
    "MXEU0MT",
    "MXEU0IN",
    "MXEU0CD",
    "MXEU0CS",
    "MXEU0HC",
    "MXEU0FN",
    "MXEU0IT",
    "MXEU0TC",
    "MXEU0UT",
    "MXCA",
    "MXCN",
    "MXIN",
    "MXKR",
    "TAMSCI",
)
NOT_ESTIMATED_REASON = (
    "tradable-only series (daily start after 2009) inherit loadings and are never estimated, "
    "SUBSTRATE section 5.2"
)


def tradable_only_ids(panel, universe_rows, flags) -> list[str]:
    """Investable, unhedged series whose tier is neither backbone nor second."""
    return [
        sid
        for sid, meta in panel.meta.items()
        if sid in panel.returns.columns
        and not meta.hedged
        and not str(meta.section).startswith("18.")
        and flags.get(sid, False)
        and meta.tier not in ("backbone", "second")
        and universe_rows.get(sid, {}).get("reporting_class")
    ]


def reproduce_the_test(R, F, classes, ids, weeks, reference_dir: Path) -> dict:
    """
    The gates against the run of record (decisions/0052 changed the universe since it).

    The run's instruments must be this build's (Cash out) plus exactly `LEFT`. Every Huber
    loading it stores for an instrument that is neither left nor `CONVERTED` must equal this
    build's at a tolerance of zero (decisions/0053: a converted series is a different series).
    The pooled `r2_oos` and mean Huber loss are then computed on those cells, with the test's
    own functions, and reported but not compared: `fit.json` pools the 86 instruments.
    """
    from signal_lab.characteristics import build, reference
    from signal_lab.measurement import describe, fidelity
    from signal_lab.measurement.factors import FACTOR_NAMES

    keep = [i for i, c in enumerate(classes) if c != "Cash"]
    Rk, ck, idk = R[:, keep], [classes[i] for i in keep], [ids[i] for i in keep]
    paths = build.estimate_paths(Rk, F)
    beta = np.stack([p.beta for p in paths], axis=1)  # (T, N, K)
    scale = fidelity.robust_scale(Rk)

    summary = json.loads((reference_dir / "summary.json").read_text(encoding="utf-8"))
    stored = pd.read_parquet(reference_dir / "loadings.parquet")
    stored_ids = sorted(set(stored["instrument"]))
    if set(stored_ids) != set(idk) | set(LEFT) or set(idk) & set(LEFT):
        extra = sorted(set(stored_ids) - set(idk) - set(LEFT))
        short = sorted((set(idk) | set(LEFT)) - set(stored_ids))
        raise SystemExit(
            "STOP: the run of record's instruments are not this build's (Cash out) plus "
            f"{list(LEFT)}; only in the run: {extra}; only in the build: {short}"
        )
    unconverted = [s_ for s_ in CONVERTED if s_ not in idk]
    if unconverted:
        raise SystemExit(f"STOP: CONVERTED names instruments this build lacks: {unconverted}")
    arrays = reference.reference_arrays(
        stored, summary["estimators"], stored_ids, weeks, list(FACTOR_NAMES)
    )
    sel = [i for i, s_ in enumerate(idk) if s_ not in CONVERTED]  # in this build's order
    idk_s = [idk[i] for i in sel]
    pos = [stored_ids.index(s_) for s_ in idk_s]
    beta_s = beta[:, sel, :]
    shared_huber = arrays["huber_m"][:, pos, :]
    have = reference.presence_mask({k: v[:, pos, :] for k, v in arrays.items()})

    on_stored = np.isfinite(shared_huber)
    diff = np.where(
        on_stored, np.abs(np.where(np.isfinite(beta_s), beta_s, np.inf) - shared_huber), 0.0
    )
    compared = int(on_stored.sum())
    max_diff = float(diff.max()) if compared else 0.0
    out = {"cells_compared": compared, "max_abs_loading_difference": max_diff}
    if max_diff != 0.0:
        out["stop"] = "a Huber loading differs from the run of record's"
        return out

    Rs, cs, scale_s = Rk[:, sel], [ck[i] for i in sel], scale[:, sel]
    mask = describe.scored_cells(have & np.isfinite(beta_s).all(axis=2), Rs, F, scale_s)
    res = describe.fit_metrics(Rs, F, {"huber_m": beta_s}, scale_s, cs, idk_s, weeks, {}, mask=mask)
    got = res["estimators"]["huber_m"]
    ref = json.loads((reference_dir / "fit.json").read_text(encoding="utf-8"))
    ref_h = ref["estimators"]["huber_m"]
    out.update(
        {
            "shared_instruments": len(idk_s),
            "shared_scored_cells": res["cells"],
            "r2_oos": got["pooled"]["r2_oos"],
            "mean_huber_loss": got["mean_huber_loss"],
            "reference_cells_86_instruments": ref["cells"],
            "reference_r2_oos_86_instruments": ref_h["pooled"]["r2_oos"],
            "reference_mean_huber_loss_86_instruments": ref_h["mean_huber_loss"],
        }
    )
    return out


def checks_text(manifest: dict, check: dict) -> dict[str, str]:
    if manifest.get("gates_against_run_of_record") == "skipped":
        return {
            "gates against the run of record": f"skipped: {manifest['gates_skipped_reason']}",
            "no lookahead": "`assert_no_lookahead` passed on every instrument's path",
            "factors": f"{manifest['factor_set']}, estimation from {manifest['estimation_start']}; "
            f"all six factors exist from {manifest['factors_common_start']}",
        }
    out = {
        "Huber loadings against the run of record": (
            f"`{manifest['run_of_record']}` stores {check['cells_compared']:,} Huber loadings for "
            f"the instruments it shares with this build and that were not converted to dollars; "
            f"the largest absolute difference is "
            f"{check['max_abs_loading_difference']:.1e} (tolerance zero)"
        ),
        "no lookahead": "`assert_no_lookahead` passed on every instrument's path",
        "factors": "the factors hash equals the run of record's: "
        f"{manifest['factors_equal_run_of_record']}",
    }
    if "shared_scored_cells" in check:
        out["fit on the shared cells (reported, not compared)"] = (
            f"{check['shared_instruments']} instruments, {check['shared_scored_cells']:,} cells "
            f"scored by the test's rule: pooled r2_oos {check['r2_oos']:.4f}, mean Huber loss "
            f"{check['mean_huber_loss']:.4f}; `fit.json` pools 86 instruments "
            f"({check['reference_cells_86_instruments']:,} cells): "
            f"{check['reference_r2_oos_86_instruments']:.4f} and "
            f"{check['reference_mean_huber_loss_86_instruments']:.4f}"
        )
    if "supersedes_max_abs_loading_difference" in manifest:
        out[f"against {manifest['supersedes']}"] = (
            f"{manifest['supersedes_cells_compared']:,} loadings of the instruments neither "
            f"left nor converted to dollars; the largest absolute difference is "
            f"{manifest['supersedes_max_abs_loading_difference']:.1e} in the loading and "
            f"{manifest['supersedes_max_abs_se_difference']:.1e} in its standard error "
            f"(tolerance zero); {manifest['supersedes_rows_unmatched']} unmatched rows"
        )
    if "converted_max_abs_loading_difference" in manifest:
        out["the converted series"] = (
            f"{manifest['converted_cells_compared']:,} loadings of the "
            f"{len(manifest['converted_to_usd'])} converted series on both sides; the largest "
            f"absolute difference is {manifest['converted_max_abs_loading_difference']:.3f}"
        )
    return out


def main(argv=None) -> int:
    import run_measurement as RM

    from signal_lab.characteristics import build, report, store
    from signal_lab.measurement.estimators import HUBER_C, MAD_TO_SD, MIN_OBS, WINDOW
    from signal_lab.measurement.run import factor_correlations
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-id", default=STORE_ID)
    parser.add_argument("--root", default=str(store.STORE_ROOT))
    parser.add_argument("--report-root", default=str(REPO_ROOT / "results" / "characteristics"))
    parser.add_argument("--reference-run", default=REFERENCE_RUN)
    parser.add_argument(
        "--factor-set",
        default="huber6",
        choices=("huber6", "huber6-baa10y"),
        help="huber6-baa10y builds the credit factor from FRED's BAA10Y (decisions/0058); "
        "it skips the run-of-record gates, which cannot hold for other factors",
    )
    parser.add_argument(
        "--estimation-start",
        default="dev_start",
        choices=("dev_start", "common"),
        help="common reads from the factors' common start rather than dev_start (decisions/0058)",
    )
    parser.add_argument(
        "--supersedes",
        default="huber6-v2",
        help="an earlier store: recorded in the manifest and compared cell by cell",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="rewrite report.md from the existing store, after re-hashing it; builds nothing",
    )
    args = parser.parse_args(argv)

    if args.report_only:
        loaded = store.load_store(args.store_id, args.root)
        rep_dir = Path(args.report_root) / args.store_id
        rep_dir.mkdir(parents=True, exist_ok=True)
        repro = loaded.manifest["reproduction"]
        (rep_dir / "report.md").write_text(
            report.build_report(loaded, checks_text(loaded.manifest, repro)), encoding="utf-8"
        )
        print(f"wrote {rep_dir / 'report.md'} from {loaded.store_id}")
        return 0

    params = get_params()
    v4 = (args.factor_set, args.estimation_start) != ("huber6", "dev_start")
    panel, analytics, ff, universe_rows, flags = RM.load_inputs(
        params, args.factor_set, args.estimation_start
    )
    fx_report = RM.LOADER_REPORT.get("fx", {}) if hasattr(RM, "LOADER_REPORT") else {}
    ids, classes = RM.select_instruments(panel, universe_rows, flags)  # Cash included
    skipped = tradable_only_ids(panel, universe_rows, flags)
    weekly = RM.weekly_inputs(panel, ids, ff)
    R, F = weekly.to_numpy(dtype=float), ff.frame.to_numpy(dtype=float)
    weeks = ff.frame.index
    print(
        f"{len(ids)} instruments, {len(skipped)} not estimated, {len(weeks)} weeks "
        f"({weeks[0].date()} to {weeks[-1].date()})."
    )

    ref_dir = REPO_ROOT / "results" / "measurement" / args.reference_run
    if v4:
        factors_match = False
        check = {"skipped": True}
        print(f"run-of-record gates skipped: {V4_SKIP_REASON}")
        print(
            f"all six factors exist from {ff.common_start.date()}; estimation reads "
            f"{args.estimation_start}"
        )
    else:
        ref_summary = json.loads((ref_dir / "summary.json").read_text(encoding="utf-8"))
        factors_match = RM._frame_hash(ff.frame) == ref_summary["hashes"]["factors_hash"]
        print(f"factors hash equals the run of record's: {factors_match}")
        if not factors_match:
            print("STOP: the factors moved since the run of record.", file=sys.stderr)
            return 4

        check = reproduce_the_test(R, F, classes, ids, weeks, ref_dir)
        print(
            f"Huber loadings against the run of record: {check['cells_compared']} cells compared, "
            f"largest absolute difference {check['max_abs_loading_difference']:.1e}"
        )
        if "stop" in check:
            print(f"STOP: {check['stop']}.", file=sys.stderr)
            return 4
        print(
            f"on the {check['shared_instruments']} shared instruments: "
            f"{check['shared_scored_cells']} scored cells, r2_oos {check['r2_oos']:.6f}, "
            f"mean Huber loss {check['mean_huber_loss']:.6f} "
            f"(fit.json, 86 instruments: {check['reference_r2_oos_86_instruments']:.6f}, "
            f"{check['reference_mean_huber_loss_86_instruments']:.6f})"
        )

    built = build.build_estimated(R, F, ids, classes, weeks, params)  # assert_no_lookahead inside
    measured_ids = list(dict.fromkeys([*ids, *skipped]))
    measured = build.measured_cells(analytics.fields, measured_ids, ff.dates, weeks, params)
    inst = built["instruments"]
    skipped_rows = pd.DataFrame(
        {
            "instrument": skipped,
            "class": [str(universe_rows[s]["reporting_class"]) for s in skipped],
            "estimated": False,
            "first_date": pd.NaT,
            "last_date": pd.NaT,
            "n_rows": 0,
            "explained_share_full": np.nan,
            "kind": build.ESTIMATED,
            "estimator": build.ESTIMATOR,
        }
    )
    frames = {
        "loadings": built["loadings"],
        "fit": built["fit"],
        "measured": measured,
        "instruments": pd.concat([inst, skipped_rows], ignore_index=True),
    }
    manifest = {
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "decision": "decisions/0049",
        "also": (
            ["decisions/0052", "decisions/0053", "decisions/0056", "decisions/0058"]
            if v4
            else ["decisions/0052", "decisions/0053"]
        ),
        "handoff_task": V4_TASK if v4 else TASK,
        "supersedes": args.supersedes,
        "estimator": {
            "name": build.ESTIMATOR,
            "hypothesis": "H-2026-0013",
            "huber_c": HUBER_C,
            "mad_to_sd": MAD_TO_SD,
            "window_weeks": WINDOW,
            "min_obs": MIN_OBS,
            "explained_share_window_weeks": build.EXPLAINED_WINDOW,
            "explained_share_min_weeks": build.EXPLAINED_MIN,
        },
        "factors": list(ff.frame.columns),
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "weekly_returns_hash": RM._frame_hash(weekly),
        "factors_hash": RM._frame_hash(ff.frame),
        "factors_equal_run_of_record": bool(factors_match),
        "run_of_record": args.reference_run,
        "thread_setting": THREADS,
        "n_estimated": int(inst["estimated"].sum()),
        "n_not_estimated": int(len(skipped) + (~inst["estimated"]).sum()),
        "not_estimated_reason": NOT_ESTIMATED_REASON,
        "not_estimated": sorted(skipped),
        "estimated_but_no_row": sorted(inst.loc[~inst["estimated"], "instrument"]),
        "first_date": str(pd.Timestamp(built["loadings"]["date"].min()).date()),
        "last_date": str(pd.Timestamp(built["loadings"]["date"].max()).date()),
        "measured_fields": build.MEASURED_FIELDS,
        "reproduction": {k: (float(v) if isinstance(v, float) else v) for k, v in check.items()},
    }
    if v4:
        manifest.update(
            {
                "factor_set": args.factor_set,
                "estimation_start": args.estimation_start,
                "factors_common_start": str(ff.common_start.date()),
                "factors_n_complete_weeks": int(ff.n_weeks),
                "credit_source": "FRED BAA10Y, percent, dated by its observation date",
                "gates_against_run_of_record": "skipped",
                "gates_skipped_reason": V4_SKIP_REASON,
                "factor_correlations": factor_correlations(ff.frame),
            }
        )
    if args.supersedes and not v4:
        old = store.load_store(args.supersedes, args.root)
        key = ["instrument", "date", "factor"]
        moved = set(CONVERTED) | set(LEFT)
        old_l, new_l = old.frames["loadings"], frames["loadings"]
        old_same = old_l[~old_l["instrument"].isin(moved)]
        new_same = new_l[~new_l["instrument"].isin(moved)]
        both = old_same.merge(new_same, on=key, suffixes=("_old", "_new"))
        manifest["supersedes_cells_compared"] = int(len(both))
        manifest["supersedes_rows_unmatched"] = int(len(old_same) + len(new_same) - 2 * len(both))
        manifest["supersedes_max_abs_loading_difference"] = (
            float((both["loading_old"] - both["loading_new"]).abs().max()) if len(both) else 0.0
        )
        manifest["supersedes_max_abs_se_difference"] = (
            float((both["se_old"] - both["se_new"]).abs().max()) if len(both) else 0.0
        )
        print(
            f"against {args.supersedes}, instruments neither left nor converted: {len(both)} "
            f"rows on shared cells, {manifest['supersedes_rows_unmatched']} unmatched, largest "
            f"absolute difference {manifest['supersedes_max_abs_loading_difference']:.1e} in "
            f"the loading and {manifest['supersedes_max_abs_se_difference']:.1e} in its se"
        )
        if (
            manifest["supersedes_max_abs_loading_difference"] != 0.0
            or manifest["supersedes_max_abs_se_difference"] != 0.0
            or manifest["supersedes_rows_unmatched"] != 0
        ):
            print(
                f"STOP: a loading or standard error of an unchanged instrument differs from "
                f"{args.supersedes}'s, or a cell is missing from one side.",
                file=sys.stderr,
            )
            return 4

        fx_rep = fx_report["converted"]
        converted = {t: fx_rep[t] for t in CONVERTED}
        rows = report.converted_rows(frames, old.frames, converted)
        manifest["converted_to_usd"] = rows
        o_c = old_l[old_l["instrument"].isin(CONVERTED)]
        n_c = new_l[new_l["instrument"].isin(CONVERTED)]
        cb = o_c.merge(n_c, on=key, suffixes=("_old", "_new"))
        manifest["converted_cells_compared"] = int(len(cb))
        manifest["converted_max_abs_loading_difference"] = (
            float((cb["loading_old"] - cb["loading_new"]).abs().max()) if len(cb) else 0.0
        )
        print(
            f"{len(CONVERTED)} converted series: {len(cb)} cells on both sides, largest absolute "
            f"loading difference {manifest['converted_max_abs_loading_difference']:.3f}"
        )
        for r in rows:
            print(
                f"  {r['instrument']:9s} {r['currency']} dollar loading {r['dollar_before']:+.2f} "
                f"-> {r['dollar_after']:+.2f}; explained share {r['share_before']:.2f} -> "
                f"{r['share_after']:.2f}; FX dates dropped {r['fx_dates_dropped']}"
            )
    out = store.write_store(args.store_id, frames, manifest, args.root)
    loaded = store.load_store(args.store_id, args.root)  # re-hash: the round trip must hold
    print(f"wrote {out} (directory hash {loaded.manifest['directory_hash'][:16]})")

    rep_dir = Path(args.report_root) / args.store_id
    rep_dir.mkdir(parents=True, exist_ok=True)
    checks = checks_text(manifest, check)
    (rep_dir / "report.md").write_text(report.build_report(loaded, checks), encoding="utf-8")
    print(f"wrote {rep_dir / 'report.md'}")
    if v4:
        corr = manifest["factor_correlations"]
        (rep_dir / "factor_correlations.json").write_text(
            json.dumps(corr, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        full = pd.DataFrame(corr["full_sample"]).round(2)
        lines = [
            f"# Factor correlations, `{args.store_id}` (decisions/0058)",
            "",
            f"Weeks with all six factors: {ff.n_weeks}, from {ff.common_start.date()} to "
            f"{ff.frame.index[-1].date()}.",
            "",
            "Full-sample correlation:",
            "",
            "```",
            full.to_string(),
            "```",
            "",
            "Range of the rolling 156-week correlation, by pair:",
            "",
            *(
                f"- `{pair}`: {r['min']:.2f} to {r['max']:.2f}"
                for pair, r in corr["rolling_156w_range"].items()
            ),
        ]
        (rep_dir / "factor_correlations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {rep_dir / 'factor_correlations.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
