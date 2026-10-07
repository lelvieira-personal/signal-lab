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
STORE_ID = "huber6-v1"
TOLERANCE = 1e-6
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
    The estimator test's own numbers for huber_m, from this build's loadings, on the cells the
    test scored (Cash out). Uses the test's functions, not new ones.
    """
    from signal_lab.characteristics import build
    from signal_lab.measurement import describe, fidelity
    from signal_lab.measurement.factors import FACTOR_NAMES

    keep = [i for i, c in enumerate(classes) if c != "Cash"]
    Rk, ck, idk = R[:, keep], [classes[i] for i in keep], [ids[i] for i in keep]
    paths = build.estimate_paths(Rk, F)
    beta = np.stack([p.beta for p in paths], axis=1)  # (T, N, K)
    scale = fidelity.robust_scale(Rk)

    # The test scored a cell only where EVERY estimator had a loading. That set is read from
    # the run of record's stored loadings (presence only); nothing else is taken from them
    # except the Huber loadings, which are compared with this build's.
    summary = json.loads((reference_dir / "summary.json").read_text(encoding="utf-8"))
    stored = pd.read_parquet(reference_dir / "loadings.parquet")
    if set(stored["instrument"]) != set(idk):
        raise SystemExit("STOP: the run of record's instruments are not this build's (Cash out)")
    factors = list(FACTOR_NAMES)
    t_idx = weeks.get_indexer(stored["date"])
    i_idx = pd.Index(idk).get_indexer(stored["instrument"])
    k_idx = pd.Index(factors).get_indexer(stored["factor"])
    have = np.ones(Rk.shape, dtype=bool)
    stored_huber = np.full(beta.shape, np.nan)
    for name in summary["estimators"]:
        sel = (stored["estimator"] == name).to_numpy()
        a_ = np.full(beta.shape, np.nan)
        a_[t_idx[sel], i_idx[sel], k_idx[sel]] = stored["loading"].to_numpy()[sel]
        have &= np.isfinite(a_).all(axis=2)
        if name == "huber_m":
            stored_huber = a_
    both = np.isfinite(beta) & np.isfinite(stored_huber)
    loading_diff = float(np.abs(beta[both] - stored_huber[both]).max()) if both.any() else None
    mask = describe.scored_cells(have & np.isfinite(beta).all(axis=2), Rk, F, scale)
    res = describe.fit_metrics(Rk, F, {"huber_m": beta}, scale, ck, idk, weeks, {}, mask=mask)
    ref = json.loads((reference_dir / "fit.json").read_text(encoding="utf-8"))
    ref_h = ref["estimators"]["huber_m"]
    got = res["estimators"]["huber_m"]
    out = {
        "cells": res["cells"],
        "max_abs_loading_difference_to_stored_huber": loading_diff,
        "reference_cells": ref["cells"],
        "r2_oos": got["pooled"]["r2_oos"],
        "reference_r2_oos": ref_h["pooled"]["r2_oos"],
        "mean_huber_loss": got["mean_huber_loss"],
        "reference_mean_huber_loss": ref_h["mean_huber_loss"],
    }
    out["r2_oos_difference"] = abs(out["r2_oos"] - out["reference_r2_oos"])
    out["mean_huber_loss_difference"] = abs(
        out["mean_huber_loss"] - out["reference_mean_huber_loss"]
    )
    return out


def checks_text(manifest: dict, check: dict) -> dict[str, str]:
    return {
        "reproduces the estimator test": (
            f"{check['cells']} cells; pooled r2_oos differs from "
            f"`{manifest['run_of_record']}/fit.json` by {check['r2_oos_difference']:.2e} and mean "
            f"Huber loss by {check['mean_huber_loss_difference']:.2e} (tolerance {TOLERANCE:g})"
        ),
        "no lookahead": "`assert_no_lookahead` passed on every instrument's path",
        "inputs": "weekly returns (Cash out) and factors hash-equal to the run of record: "
        f"{manifest['inputs_equal_run_of_record']}",
    }


def main(argv=None) -> int:
    import run_measurement as RM

    from signal_lab.characteristics import build, report, store
    from signal_lab.measurement.estimators import HUBER_C, MAD_TO_SD, MIN_OBS, WINDOW
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-id", default=STORE_ID)
    parser.add_argument("--root", default=str(store.STORE_ROOT))
    parser.add_argument("--report-root", default=str(REPO_ROOT / "results" / "characteristics"))
    parser.add_argument("--reference-run", default=REFERENCE_RUN)
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
    panel, analytics, ff, universe_rows, flags = RM.load_inputs(params)
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
    ref_summary = json.loads((ref_dir / "summary.json").read_text(encoding="utf-8"))
    no_cash = [i for i, c in enumerate(classes) if c != "Cash"]
    weekly_hash_ex_cash = RM._frame_hash(weekly.iloc[:, no_cash])
    inputs_match = (
        weekly_hash_ex_cash == ref_summary["hashes"]["weekly_returns_hash"]
        and RM._frame_hash(ff.frame) == ref_summary["hashes"]["factors_hash"]
    )
    print(f"inputs equal the run of record's (Cash out): {inputs_match}")

    check = reproduce_the_test(R, F, classes, ids, weeks, ref_dir)
    print(
        f"reproduction: {check['cells']} cells (the test's {check['reference_cells']}); "
        f"r2_oos {check['r2_oos']:.6f} against {check['reference_r2_oos']:.6f} "
        f"(difference {check['r2_oos_difference']:.2e}); mean Huber loss "
        f"{check['mean_huber_loss']:.6f} against {check['reference_mean_huber_loss']:.6f} "
        f"(difference {check['mean_huber_loss_difference']:.2e})"
    )
    if (
        check["cells"] != check["reference_cells"]
        or check["r2_oos_difference"] > TOLERANCE
        or check["mean_huber_loss_difference"] > TOLERANCE
    ):
        print(f"STOP: the build does not reproduce the test to {TOLERANCE:g}.", file=sys.stderr)
        return 4

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
        "handoff_task": 51,
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
        "weekly_returns_hash_ex_cash": weekly_hash_ex_cash,
        "factors_hash": RM._frame_hash(ff.frame),
        "inputs_equal_run_of_record": bool(inputs_match),
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
    out = store.write_store(args.store_id, frames, manifest, args.root)
    loaded = store.load_store(args.store_id, args.root)  # re-hash: the round trip must hold
    print(f"wrote {out} (directory hash {loaded.manifest['directory_hash'][:16]})")

    rep_dir = Path(args.report_root) / args.store_id
    rep_dir.mkdir(parents=True, exist_ok=True)
    checks = checks_text(manifest, check)
    (rep_dir / "report.md").write_text(report.build_report(loaded, checks), encoding="utf-8")
    print(f"wrote {rep_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
