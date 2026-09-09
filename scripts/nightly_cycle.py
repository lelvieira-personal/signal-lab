#!/usr/bin/env python3
"""
The nightly cycle. SUBSTRATE section 13.

    python scripts/nightly_cycle.py --snapshot synthetic-v1

Deterministic script, not a model. It loads the snapshot, validates each pending
hypothesis, runs it, applies the vetoes, and records everything.

PHASE 1 STATUS. The engine is built and validated; the links above it are not.
`run_experiment()` lives in `signal_lab.harness.experiment` and is the only
sanctioned way to run anything (SUBSTRATE section 2). It raises a precise
`ExperimentBlocked` subclass while a link is missing -- `blocked:no_signal_module`
rather than a vague "not implemented" -- so the digest names what to build next.

`--validate` drives a planted synthetic path through the built half of the chain
end to end: engine, costs, veto inputs, metrics, artifacts. Those runs are tagged
`validation` and excluded from the leaderboard, because a run that tests the
harness is not a result about markets and the planted IR was put there on
purpose.

The gate in SUBSTRATE section 5.6 is live here too: the search does not open
until the macro block is in, so even with signal modules this script would
refuse to search on price-only signals.
"""

from __future__ import annotations

import argparse
from datetime import UTC
from pathlib import Path

import _bootstrap  # noqa: F401


def _load_panel_and_benchmark(snapshot, params):
    """
    The snapshot's return panel and its benchmark.

    Phase 1 reads the synthetic backend. Phase 2 swaps in the Bloomberg loader
    and the real 50/50; nothing else in this script changes.
    """
    from signal_lab.loaders import get_loader
    from signal_lab.loaders.synthetic import make_benchmark

    loader = get_loader(snapshot.manifest.get("source", "synthetic"), params=params)
    panel = loader.load_returns(snapshot.snapshot_id)
    return panel, make_benchmark(panel, params)


def main(argv=None) -> int:
    from datetime import datetime

    from signal_lab.harness.budgets import model_calls_enabled
    from signal_lab.harness.experiment import (
        ExperimentBlocked,
        run_experiment,
        validate_pipeline,
    )
    from signal_lab.harness.hypotheses import HypothesisRegistry
    from signal_lab.harness.snapshot import load_snapshot, verify_snapshot
    from signal_lab.loaders.jpmaqs import search_is_open
    from signal_lab.params import get_params
    from signal_lab.results.store import ResultsStore, new_run_id
    from vetoes import apply_vetoes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="synthetic-v1")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--snapshots-dir", default=None, help="override data/snapshots/")
    parser.add_argument("--db", default=None)
    parser.add_argument("--dry-run", action="store_true", help="triage only, record nothing")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="also drive a planted synthetic path end to end through the built chain",
    )
    args = parser.parse_args(argv)

    params = get_params()
    # A run's database and its artifacts belong together: pointed at another
    # database, the cycle must not scatter parquet into the default directory,
    # or a results folder copied elsewhere arrives with rows whose artifacts are
    # missing and a default folder fills with artifacts nothing references.
    if args.db:
        db_path = Path(args.db)
        store = ResultsStore(db_path, db_path.parent / "artifacts")
    else:
        store = ResultsStore()
    cycle_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    print(f"cycle {cycle_id}")
    print(f"params {params.params_version} · {params.params_hash[:12]}")

    # --- load ---------------------------------------------------------------
    snapshot = load_snapshot(args.snapshot, args.snapshots_dir)
    ok, detail = verify_snapshot(snapshot)
    print(f"snapshot {snapshot.snapshot_id}: {detail}")
    if not ok:
        print("refusing to run on a snapshot that does not match its manifest")
        return 1

    # --- gates --------------------------------------------------------------
    search_open, search_detail = search_is_open(params)
    print(f"search gate: {'open' if search_open else 'CLOSED'} — {search_detail}")
    models_ok, models_detail = model_calls_enabled(params)
    print(f"model roles: {'enabled' if models_ok else 'disabled'} — {models_detail}")
    print("  deterministic steps (load, validate, veto, record) proceed regardless")

    # --- triage -------------------------------------------------------------
    registry = HypothesisRegistry(store=store, params=params)
    triage = registry.triage(snapshot.available_ids())
    print(
        f"pending: {len(triage['ready'])} ready, {len(triage['blocked'])} blocked:data, "
        f"{len(triage['rejected'])} rejected"
    )
    for path, reason in triage["rejected"]:
        print(f"  REJECTED {path.name}: {reason}")
    for hyp, check, request in triage["blocked"]:
        print(f"  BLOCKED  {hyp.id}: {len(check.missing)} series missing → {request.name}")

    if args.dry_run:
        print("dry run: nothing recorded")
        return 0

    # --- pipeline validation, if asked ---------------------------------------
    recorded = 0
    if args.validate:
        panel, benchmark = _load_panel_and_benchmark(snapshot, params)
        run_id = new_run_id(prefix="V", suffix="validate")
        result = validate_pipeline(panel, run_id, params)
        store.record_run(
            run_id,
            status=result.status,
            family="pipeline",
            aggregation="planted weight path",
            data_snapshot_hash=snapshot.data_snapshot_hash,
            seed=args.seed,
            params=params,
        )
        store.record_metrics(run_id, result.metrics)
        verdicts, failure = apply_vetoes(result.run_context, params, store=store)
        for name, frame in result.artifacts.items():
            store.write_artifact(run_id, name, frame)
        error = result.metrics.get("ir_recovery_error", float("nan"))
        print(
            f"validation {run_id}: planted IR {result.metrics['planted_ir']:.4f}, "
            f"recovered {result.metrics['net_ir']:.4f}, error {error:.2e}"
        )
        print(
            f"  vetoes: {sum(v.passed for v in verdicts.values())}/{len(verdicts)} passed"
            + (f", first failure {failure}" if failure else "")
        )
        print("  tagged 'validation'; excluded from the leaderboard")
        recorded += 1

    # --- run each ready hypothesis -------------------------------------------
    panel = benchmark = None
    for hyp in triage["ready"]:
        run_id = new_run_id(suffix=hyp.id)
        if panel is None:
            panel, benchmark = _load_panel_and_benchmark(snapshot, params)
        try:
            result = run_experiment(hyp, snapshot, panel, benchmark, params, args.seed)
        except ExperimentBlocked as exc:
            store.record_run(
                run_id,
                status=exc.status,
                killed_by=exc.status.removeprefix("blocked:"),
                hypothesis_id=hyp.id,
                family=hyp.family,
                data_snapshot_hash=snapshot.data_snapshot_hash,
                seed=args.seed,
                params=params,
            )
            store.record_transition(hyp.id, "pending", "pending", run_id, str(exc)[:200])
            print(f"  {hyp.id}: {exc.status}")
            recorded += 1
            continue

        store.record_run(
            run_id,
            status=result.status,
            hypothesis_id=hyp.id,
            family=hyp.family,
            data_snapshot_hash=snapshot.data_snapshot_hash,
            seed=args.seed,
            params=params,
        )
        # Vetoes before any return statistic is displayed (SUBSTRATE section 10).
        verdicts, failure = apply_vetoes(result.run_context, params, store=store)
        store.record_metrics(run_id, result.metrics)
        for name, frame in result.artifacts.items():
            store.write_artifact(run_id, name, frame)
        if failure:
            print(f"  {hyp.id}: killed by {failure} — {verdicts[failure].detail}")
        else:
            print(f"  {hyp.id}: survived all {len(verdicts)} vetoes")
        recorded += 1

    # --- blocked hypotheses are recorded too, so the digest can show them ----
    for hyp, _check, _request in triage["blocked"]:
        run_id = new_run_id(suffix=hyp.id)
        store.record_run(
            run_id,
            status="blocked:data",
            killed_by="coverage",
            hypothesis_id=hyp.id,
            family=hyp.family,
            data_snapshot_hash=snapshot.data_snapshot_hash,
            seed=args.seed,
            params=params,
        )
        recorded += 1

    print(f"recorded {recorded} run(s) into {store.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
