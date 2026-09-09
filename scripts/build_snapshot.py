#!/usr/bin/env python3
"""
Hash and freeze a panel.

    python scripts/build_snapshot.py --id synthetic-v1
    python scripts/build_snapshot.py --id synthetic-v1 --verify

Phase 0 builds from the synthetic backend only. The real backends raise a clear
"lands in phase 2" rather than producing an empty panel.
"""

from __future__ import annotations

import argparse
import sys

import _bootstrap  # noqa: F401


def main(argv=None) -> int:
    from signal_lab.harness.snapshot import build_snapshot, load_snapshot, verify_snapshot
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", default="synthetic-v1", help="snapshot id")
    parser.add_argument("--source", default="synthetic", choices=["synthetic", "bloomberg", "fred"])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--snapshots-dir", default=None, help="override data/snapshots/")
    parser.add_argument("--overwrite", action="store_true", help="rebuild an existing snapshot id")
    parser.add_argument(
        "--verify", action="store_true", help="re-hash an existing snapshot instead"
    )
    args = parser.parse_args(argv)

    params = get_params()

    if args.verify:
        snap = load_snapshot(args.id, args.snapshots_dir)
        ok, detail = verify_snapshot(snap)
        print(f"{'OK  ' if ok else 'FAIL'} {detail}")
        return 0 if ok else 1

    try:
        snap = build_snapshot(
            args.id,
            args.source,
            params,
            snapshots_dir=args.snapshots_dir,
            seed=args.seed,
            overwrite=args.overwrite,
        )
    except NotImplementedError as exc:
        print(f"cannot build: {exc}", file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 3

    m = snap.manifest
    print(f"snapshot          {snap.snapshot_id}")
    print(f"source            {m['source']}")
    print(f"data_snapshot_hash {snap.data_snapshot_hash}")
    print(f"params            {m['params_version']} · {m['params_hash'][:12]}")
    print(f"dates             {m['first_date']} to {m['last_date']}")
    print(f"series            {m['n_series']}  tiers {m['tiers']}")
    print(f"macro series      {len(m['macro_ids'])}")
    print(f"analytics fields  {m['analytics_fields']}")
    print(f"hedged            {len(m['hedged_ids'])}")
    print(f"splices applied   {len(m['splices'])}")
    print(f"path              {snap.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
