#!/usr/bin/env python3
"""
Freeze a raw JPMaQS pull as a macro snapshot. HANDOFF task 44, part B.

    make macro-snapshot [MACRO_SNAPSHOT=jpmaqs-macro-v1] [PULL_ID=P-...]

Separate from the Bloomberg return snapshot, which is immutable and cited by
every audit run. Never overwrites. Prints counts only.
"""

from __future__ import annotations

import argparse
import sys

import _bootstrap  # noqa: F401


def main(argv=None) -> int:
    from signal_lab.harness.snapshot import build_macro_snapshot
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", default="jpmaqs-macro-v1", help="macro snapshot id")
    parser.add_argument("--pull-id", default=None, help="a raw pull; default the newest")
    parser.add_argument("--snapshots-dir", default=None)
    parser.add_argument("--raw-root", default=None)
    args = parser.parse_args(argv)

    snap = build_macro_snapshot(
        args.id,
        pull_id=args.pull_id or None,
        params=get_params(),
        snapshots_dir=args.snapshots_dir,
        raw_root=args.raw_root,
    )
    c = snap.manifest["counts"]
    print(
        f"snapshot {snap.snapshot_id} <- pull {snap.manifest['pull_id']}\n"
        f"  hash {snap.data_snapshot_hash}\n"
        f"  {c['n_tickers']} tickers; rows raw {c['rows_raw']}, no value {c['rows_no_value']}, "
        f"dropped by grade {c['rows_grade_excluded']}, before compression "
        f"{c['rows_kept_before_compression']}, after {c['rows_after_compression']}; "
        f"cross-product series dropped {c['cross_product_series_dropped']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
