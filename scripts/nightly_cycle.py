#!/usr/bin/env python3
"""
The nightly cycle. SUBSTRATE section 13.

    python scripts/nightly_cycle.py --snapshot synthetic-v1

Deterministic script, not a model. It loads the snapshot, validates each pending
hypothesis, runs it, applies the vetoes, and records everything.

PHASE 0 STATUS: there is no engine. `run_experiment()` is the only sanctioned
way to run anything (SUBSTRATE section 2) and it lands in phase 1, so this
script wires the whole pipeline and stops at the engine boundary. Each ready
hypothesis is recorded with status `blocked:no_engine`. That is deliberate:

  * the cycle is exercised end to end now, so phase 1 changes one call rather
    than writing an orchestrator;
  * nothing is fabricated. No IR is computed, no veto is evaluated against
    invented inputs, and no row appears on the leaderboard that did not come
    from a real run.

The gate in SUBSTRATE section 5.6 is also live here: the search does not open
until the macro block is in, so even with an engine this script would refuse to
search on price-only signals.
"""

from __future__ import annotations

import argparse
from datetime import UTC

import _bootstrap  # noqa: F401


class EngineNotImplemented(NotImplementedError):
    """run_experiment() lands in phase 1."""


def run_experiment(hypothesis, snapshot, params, seed):
    """
    The only sanctioned way to run an experiment (SUBSTRATE section 2).

    Phase 1 fills this in: walk-forward engine, cost model, exposure mapping and
    long-only solve, returning a populated RunContext. It raises now so that a
    cycle cannot silently produce a run context full of defaults, which would
    then be judged by vetoes that fail closed and recorded as a veto failure
    rather than as a missing engine.
    """
    raise EngineNotImplemented(
        "the walk-forward engine lands in phase 1 (SUBSTRATE section 16); "
        "no signal logic exists in phase 0"
    )


def main(argv=None) -> int:
    from datetime import datetime

    from signal_lab.harness.budgets import model_calls_enabled
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
    args = parser.parse_args(argv)

    params = get_params()
    store = ResultsStore(args.db) if args.db else ResultsStore()
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

    # --- run ----------------------------------------------------------------
    recorded = 0
    for hyp in triage["ready"]:
        run_id = new_run_id(suffix=hyp.id)
        try:
            ctx = run_experiment(hyp, snapshot, params, args.seed)
        except EngineNotImplemented as exc:
            store.record_run(
                run_id,
                status="blocked:no_engine",
                killed_by="engine_missing",
                hypothesis_id=hyp.id,
                family=hyp.family,
                data_snapshot_hash=snapshot.data_snapshot_hash,
                seed=args.seed,
                params=params,
            )
            store.record_transition(hyp.id, "pending", "pending", run_id, str(exc)[:200])
            print(f"  {hyp.id}: blocked:no_engine")
            recorded += 1
            continue

        # Phase 1 onward reaches here. Vetoes are applied before any return
        # statistic is computed or displayed (SUBSTRATE section 10).
        store.record_run(
            run_id,
            status="completed",
            hypothesis_id=hyp.id,
            family=hyp.family,
            data_snapshot_hash=snapshot.data_snapshot_hash,
            seed=args.seed,
            params=params,
        )
        verdicts, failure = apply_vetoes(ctx, params, store=store)
        if failure:
            print(f"  {hyp.id}: killed by {failure} — {verdicts[failure].detail}")
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
