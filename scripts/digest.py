#!/usr/bin/env python3
"""
Write the morning digest. SUBSTRATE sections 13 and 14.

    python scripts/digest.py -o results/digest.md

A short markdown summary of the last cycle: what ran, what died and why, what is
blocked on data, and what it cost. The owner touchpoints in SUBSTRATE section 13
are the digest, decisions/proposed/, data/requests/ and the leaderboard, so the
digest points at the other three rather than duplicating them.

Gross IR does not appear here, for the same reason it is never plotted.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap  # noqa: F401


def build_digest(store, params, registry, requests_dir: Path) -> str:
    runs = store.list_runs()
    summary = store.summary()
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Signal Lab — digest",
        "",
        f"Generated {now} · params {params.params_version} · `{params.params_hash[:12]}`",
        "",
    ]

    if runs.empty:
        lines += [
            "## No runs recorded",
            "",
            "The results store is empty. Expected until the walk-forward engine lands in phase 1.",
            "",
        ]
    else:
        last_ts = runs["ts"].max()
        cycle = runs[runs["ts"] >= last_ts[:10]]
        by_status = cycle["status"].value_counts().to_dict()
        lines += [
            "## Last cycle",
            "",
            f"- Runs recorded: **{len(cycle)}** (store total {summary['n_runs']})",
            f"- By status: {', '.join(f'{k} {v}' for k, v in sorted(by_status.items()))}",
            f"- Killed: **{int(cycle['killed_by'].notna().sum())}**",
            f"- Tokens: {summary['cost_tokens'] or 0:,}"
            + (
                f" · cost ${summary['cost_usd']:.2f}"
                if summary["cost_usd"]
                else " · cost not priced"
            ),
            "",
        ]

        killed = cycle[cycle["killed_by"].notna()]
        if not killed.empty:
            lines += [
                "### What died and why",
                "",
                "| Run | Hypothesis | Family | Stopped by |",
                "|---|---|---|---|",
            ]
            for _, r in killed.iterrows():
                lines.append(
                    f"| `{r['run_id']}` | {r['hypothesis_id'] or ''} | {r['family'] or ''} "
                    f"| {r['killed_by']} |"
                )
            lines.append("")

        survivors = cycle[cycle["passed"]] if "passed" in cycle else cycle.head(0)
        if survivors.empty:
            lines += ["### Survivors", "", "None this cycle.", ""]
        else:
            lines += [
                "### Survivors, by the pre-registered objective",
                "",
                "| Run | Family | Net IR |",
                "|---|---|---|",
            ]
            ordered = (
                survivors.sort_values("net_ir", ascending=False)
                if "net_ir" in survivors
                else survivors
            )
            for _, r in ordered.iterrows():
                ir = r.get("net_ir")
                lines.append(
                    f"| `{r['run_id']}` | {r['family'] or ''} | {'—' if ir is None else f'{ir:.2f}'} |"
                )
            lines.append("")

    # --- the other owner touchpoints ---
    pending, rejected = registry.load_tolerant("pending")
    lines += [
        "## Hypothesis registry",
        "",
        f"- pending: **{len(pending)}** valid"
        + (f", {len(rejected)} rejected by the validator" if rejected else ""),
        f"- running: {len(registry.paths('running'))} · done: {len(registry.paths('done'))}",
        "",
    ]
    if rejected:
        for path, reason in rejected:
            lines.append(f"  - `{path.name}` — {reason}")
        lines.append("")

    requests = sorted(p.name for p in Path(requests_dir).glob("*.yaml"))
    lines += ["## Waiting on the owner", ""]
    lines.append(
        f"- `data/requests/`: **{len(requests)}** open data request(s)"
        + (f" — {', '.join(requests[:8])}" if requests else "")
    )
    proposed = sorted(
        p.name for p in (Path(params.params_dir).parent / "decisions" / "proposed").glob("*.md")
    )
    lines.append(f"- `decisions/proposed/`: **{len(proposed)}** open question(s)")
    if proposed:
        for name in proposed:
            lines.append(f"  - {name}")
    lines += [
        "",
        "## Where to look",
        "",
        "- Leaderboard: `python render/static_report.py -o leaderboard.html`",
        "- Constitution: `SUBSTRATE.md`",
        "- Status: `STATUS.md`",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    from signal_lab.harness.hypotheses import REQUESTS_DIR, HypothesisRegistry
    from signal_lab.params import get_params
    from signal_lab.results.store import ResultsStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--out", default="results/digest.md")
    parser.add_argument("--db", default=None)
    args = parser.parse_args(argv)

    params = get_params()
    store = ResultsStore(args.db) if args.db else ResultsStore()
    registry = HypothesisRegistry(store=store, params=params)

    text = build_digest(store, params, registry, REQUESTS_DIR)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
