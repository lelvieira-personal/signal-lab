#!/usr/bin/env python3
"""
The JPMaQS pull. HANDOFF task 44. THE OWNER RUNS THIS, in their own shell:

    set -a; source .env; set +a; make jpmaqs-pull

Downloads value, grading and eop_lag for the tickers in `data/jpmaqs/request.txt`,
from `data_sources.sources.jpmaqs.start_date` to the last calendar day before
`holdout_start`, and writes one raw pull:

    data/raw/jpmaqs/<pull_id>/qdf.parquet
    data/raw/jpmaqs/<pull_id>/pull_manifest.json

`<pull_id>` is `P-<UTC stamp>` and an existing pull is never overwritten. It
does not touch `params/` and it does not build a snapshot. It prints shapes,
counts and date ranges only -- never a value.

Refuses (non-zero exit, nothing written) if a requested ticker or a metric is
missing from the result, or if the result reaches the holdout.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime, timedelta
from importlib import metadata
from pathlib import Path

import _bootstrap  # noqa: F401


def default_client(params):
    """The vendor client as a context manager. Credentials stay inside the loader."""
    from signal_lab.loaders.jpmaqs import JPMaQSLoader

    loader = JPMaQSLoader(params)
    client_id, client_secret = loader.credentials()  # never printed
    from macrosynergy.download import JPMaQSDownload

    return JPMaQSDownload(
        client_id=client_id,
        client_secret=client_secret,
        proxy=loader.proxies(),
        check_connection=True,
    )


def package_version() -> str:
    try:
        return metadata.version("macrosynergy")
    except metadata.PackageNotFoundError:
        return "unknown"


def pull(
    params,
    tickers: list[str],
    out_root: Path,
    client_factory=default_client,
    now: datetime | None = None,
) -> int:
    import pandas as pd

    from signal_lab.loaders.holdout import holdout_start
    from signal_lab.loaders.jpmaqs import PULL_MANIFEST_NAME, QDF_NAME, file_sha256

    metrics = list(params.get("data_sources.sources.jpmaqs.required_metrics"))
    start_date = str(params.require("data_sources.sources.jpmaqs.start_date"))
    end_date = (holdout_start(params) - timedelta(days=1)).date().isoformat()
    now = now or datetime.now(UTC)
    pull_id = "P-" + now.strftime("%Y%m%dT%H%M%SZ")
    out = out_root / pull_id
    if out.exists():
        print(f"{out} exists; a pull is never overwritten.", file=sys.stderr)
        return 1

    print(
        f"{len(tickers)} tickers, metrics {metrics}, {start_date} to {end_date} "
        f"(the day before the holdout). Connecting...",
        flush=True,
    )
    try:
        with client_factory(params) as dq:
            qdf = dq.download(
                tickers=tickers,
                metrics=metrics,
                start_date=start_date,
                end_date=end_date,
                show_progress=False,
            )
    except Exception as exc:  # noqa: BLE001 -- report and stop; nothing is written
        print(f"download failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    problems = []
    if qdf is None or len(qdf) == 0:
        print("the download returned no rows; nothing written.", file=sys.stderr)
        return 1
    absent_cols = [c for c in ("cid", "xcat", "real_date", *metrics) if c not in qdf.columns]
    if absent_cols:
        problems.append(f"column(s) missing from the result: {absent_cols}")
    else:
        present = set(qdf["cid"].astype(str) + "_" + qdf["xcat"].astype(str))
        missing = sorted(set(tickers) - present)
        if missing:
            problems.append(
                f"{len(missing)} requested ticker(s) missing from the result: {missing}"
            )
        # A metric that is entirely empty for a ticker is as good as missing.
        for m in metrics:
            empty = sorted(
                t
                for t, g in qdf.groupby(qdf["cid"].astype(str) + "_" + qdf["xcat"].astype(str))
                if t in tickers and g[m].isna().all()
            )
            if empty:
                problems.append(f"metric {m!r} is empty for {len(empty)} ticker(s): {empty}")
        reached = pd.to_datetime(qdf["real_date"]).max()
        if reached >= holdout_start(params):
            problems.append(
                f"the result reaches {reached.date()}, on or after the holdout; nothing "
                f"on or after {holdout_start(params).date()} may be stored"
            )
    if problems:
        for pr in problems:
            print(f"REFUSED: {pr}", file=sys.stderr)
        print("nothing written.", file=sys.stderr)
        return 1

    qdf = qdf[["cid", "xcat", "real_date", *metrics]].copy()
    qdf["real_date"] = pd.to_datetime(qdf["real_date"])
    ticker = qdf["cid"].astype(str) + "_" + qdf["xcat"].astype(str)
    rows_per_ticker = {t: int(n) for t, n in ticker.value_counts().sort_index().items()}

    out.mkdir(parents=True)
    try:
        qdf.to_parquet(out / QDF_NAME, index=False)
        manifest = {
            "pull_id": pull_id,
            "call_shape": "tickers=",
            "tickers": sorted(tickers),
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
            "macrosynergy_version": package_version(),
            "n_rows": int(len(qdf)),
            "first_real_date": str(qdf["real_date"].min().date()),
            "last_real_date": str(qdf["real_date"].max().date()),
            "rows_per_ticker": rows_per_ticker,
            "sha256": file_sha256(out / QDF_NAME),
        }
        (out / PULL_MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception:
        shutil.rmtree(out, ignore_errors=True)
        raise

    print(
        f"wrote {out}: {manifest['n_rows']} rows, {len(rows_per_ticker)} tickers, "
        f"real_date {manifest['first_real_date']} to {manifest['last_real_date']}, "
        f"macrosynergy {manifest['macrosynergy_version']}, call shape {manifest['call_shape']}."
    )
    return 0


def main(argv=None, client_factory=default_client) -> int:
    from signal_lab.loaders.jpmaqs import RAW_ROOT, REQUEST_TXT, read_request_tickers
    from signal_lab.params import get_params

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", default=str(REQUEST_TXT))
    parser.add_argument("--out-root", default=str(RAW_ROOT))
    args = parser.parse_args(argv)
    tickers = read_request_tickers(args.request)
    return pull(get_params(), tickers, Path(args.out_root), client_factory)


if __name__ == "__main__":
    sys.exit(main())
