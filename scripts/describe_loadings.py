#!/usr/bin/env python3
"""
Descriptions of one loading-estimator run (HANDOFF task 48, decisions/0046 addendum of 2026-10-03).

    make describe-loadings                 # stability of each estimator's loadings
    make describe-fit                      # how well the loadings predict at all
    make describe-loadings RUN=M-...       # another run

DESCRIPTIONS MADE AFTER THE RESULTS WERE SEEN. Nothing here is a test; nothing changes a
verdict. The stability description reads only the run's `loadings.parquet`. The fit
description needs the weekly returns and factors, which it rebuilds through the same loader
the run used (hash-checked against the run's `summary.json`) and never prints.

Writes into the run's directory: stability.md and stability.json; fit.md, fit.json and
predicted_vs_actual.html. The HTML holds weekly returns, which are vendor data: it is
git-ignored and is never summarised anywhere.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO_ROOT / "results" / "measurement"
RUN_OF_RECORD = "M-20261003T181155Z"
DISCLAIMER = (
    "**A description made after the results were seen. It is not a test and it changes no "
    "verdict, whichever way it reads.**"
)
STORED = (
    "Compared as stored: `mean_reverting_dlm_own_mean` stores its one-step FORECAST of the "
    "loading for week t+1, the others a filtered or fitted value at t. The exposure matrix "
    "would be handed what is stored, so that is what is compared."
)
# Named in HANDOFF task 48 before any was looked at. One not in the scored set is said so, not replaced.
NAMED = (
    "SPXT",
    "MXUS0UT",
    "M1EF",
    "NDDUJN",
    "LF98TRUU",
    "LUACTRUU",
    "LT09TRUU",
    "LUTLTRUU",
    "I20344US",
    "BCOMGCTR",
    "ENXG",
    "LUMSTRUU",
)
GREY, ORANGE, INK, FAINT = "#8A8A8A", "#FF6100", "#333333", "#D9D9D9"
MR = "mean_reverting_dlm_own_mean"


def md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
        *("| " + " | ".join(r) + " |" for r in rows),
    ]


def f(x, nd=3) -> str:
    return "-" if x is None or (isinstance(x, float) and x != x) else f"{x:.{nd}f}"


# --- stability --------------------------------------------------------------------------------


def run_stability(run_dir: Path, summary: dict) -> None:
    from signal_lab.measurement import describe

    estimators = summary["estimators"]
    long = pd.read_parquet(run_dir / "loadings.parquet")
    res = describe.stability(long, estimators)
    (run_dir / "stability.json").write_text(
        json.dumps(res, indent=2, default=float), encoding="utf-8"
    )
    lines = [
        f"# Stability of the loadings, {summary['run_id']}",
        "",
        DISCLAIMER,
        "",
        STORED,
        "",
        f"Cells: {res['cells']} instrument-weeks at which every estimator has a loading. A "
        "change counts when both dates are such cells. Ratios are to rolling OLS (1.00 is as "
        "stable as OLS); an absolute mean is the mean over instruments of the mean over weeks "
        "of the absolute change, in loading units.",
        "",
        "## Summary: mean of each ratio across the six factors",
        "",
        *md_table(
            ["estimator", "weekly", "weekly 2008-09", "annual", "annual 2008-09", "rank agreement"],
            [
                [
                    e,
                    f(s["weekly_change_ratio"], 2),
                    f(s["weekly_change_2008_2009_ratio"], 2),
                    f(s["annual_change_ratio"], 2),
                    f(s["annual_change_2008_2009_ratio"], 2),
                    f(s["rank_agreement"], 3),
                ]
                for e, s in res["summary"].items()
            ],
        ),
    ]
    for label, title in (
        ("weekly_change", "Weekly change, ratio to rolling OLS"),
        ("weekly_change_2008_2009", "Weekly change in 2008-2009, ratio to rolling OLS"),
        ("annual_change", "Annual change, ratio to rolling OLS"),
        ("annual_change_2008_2009", "Annual change in 2008-2009, ratio to rolling OLS"),
        (
            "rank_agreement",
            "Rank agreement with rolling OLS (median weekly cross-sectional Spearman)",
        ),
    ):
        block = res[label] if label == "rank_agreement" else res[label]["ratio"]
        lines += [
            "",
            f"## {title}",
            "",
            *md_table(
                ["estimator", *res["factors"]],
                [[e, *(f(block[e][k], 2) for k in res["factors"])] for e in estimators],
            ),
        ]
    lines += [
        "",
        "## Weekly change, absolute (loading units)",
        "",
        *md_table(
            ["estimator", *res["factors"]],
            [
                [e, *(f(res["weekly_change"]["abs"][e][k], 4) for k in res["factors"])]
                for e in estimators
            ],
        ),
        "",
    ]
    (run_dir / "stability.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {run_dir / 'stability.md'}")


# --- fit --------------------------------------------------------------------------------------


def rebuild_inputs(summary: dict):
    """The weekly returns and factors the run scored, rebuilt by the run's own code and hash-checked."""
    import run_measurement as RM

    from signal_lab.params import get_params

    params = get_params()
    panel, _analytics, ff, universe_rows, flags = RM.load_inputs(params)
    ids, classes = RM.select_instruments(panel, universe_rows, flags)
    excluded = set(summary["excluded_classes"])
    keep = [i for i, c in enumerate(classes) if c not in excluded]
    ids, classes = [ids[i] for i in keep], [classes[i] for i in keep]
    weekly = RM.weekly_inputs(panel, ids, ff)
    for key, frame in (("weekly_returns_hash", weekly), ("factors_hash", ff.frame)):
        if RM._frame_hash(frame) != summary["hashes"][key]:
            raise SystemExit(
                f"STOP: {key} differs from the run's summary.json; the inputs are not the run's"
            )
    return ids, classes, weekly, ff


def beta_arrays(long: pd.DataFrame, estimators, ids, weeks, factors) -> dict[str, np.ndarray]:
    t_idx = weeks.get_indexer(long["date"])
    i_idx = pd.Index(ids).get_indexer(long["instrument"])
    k_idx = pd.Index(factors).get_indexer(long["factor"])
    out = {}
    for name in estimators:
        sel = (long["estimator"] == name).to_numpy()
        a = np.full((len(weeks), len(ids), len(factors)), np.nan)
        a[t_idx[sel], i_idx[sel], k_idx[sel]] = long["loading"].to_numpy()[sel]
        out[name] = a
    return out


def run_fit(run_dir: Path, summary: dict) -> None:
    from signal_lab.measurement import describe, fidelity

    estimators = summary["estimators"]
    ids, classes, weekly, ff = rebuild_inputs(summary)
    weeks, factors = ff.frame.index, list(ff.frame.columns)
    R, F = weekly.to_numpy(dtype=float), ff.frame.to_numpy(dtype=float)
    long = pd.read_parquet(run_dir / "loadings.parquet")
    if set(long["instrument"]) != set(ids):
        raise SystemExit("STOP: the loadings' instruments are not the run's scored instruments")
    betas = beta_arrays(long, estimators, ids, weeks, factors)
    scale = fidelity.robust_scale(R)

    # The score's slices, rebuilt as fidelity.score builds them, over the weeks it scored.
    have = np.ones(R.shape, dtype=bool)
    for b in betas.values():
        have &= np.isfinite(b).all(axis=2)
    mask = describe.scored_cells(have, R, F, scale)
    scored_weeks = weeks[mask.any(axis=1)]
    sd = ff.frame.std()
    move = np.sqrt(((ff.frame.reindex(scored_weeks) / sd) ** 2).sum(axis=1))
    stress = move >= move.quantile(1 - fidelity.TOP_DECILE)
    slices = {
        "top_decile_factor_moves": np.isin(weeks, stress.index[stress.to_numpy()]),
        **{
            label: np.asarray((weeks.year >= lo) & (weeks.year <= hi))
            for label, lo, hi in fidelity.SUBPERIODS
        },
    }
    res = describe.fit_metrics(R, F, betas, scale, classes, ids, weeks, slices, mask=mask)

    # Proof that this is "exactly as the score uses it": the score's own mean Huber loss.
    worst = 0.0
    for name in estimators:
        ref = summary["score"]["estimators"][name]["mean_huber_loss"]
        worst = max(worst, abs(res["estimators"][name]["mean_huber_loss"] - ref))
    res["reproduces_scores_mean_huber_loss"] = {"max_abs_difference": worst, "cells": res["cells"]}
    if res["cells"] != summary["score"]["n_cells_scored"] or worst > 1e-9:
        raise SystemExit(
            f"STOP: the cells or the mean Huber loss differ from the score's "
            f"({res['cells']} against {summary['score']['n_cells_scored']}; max difference {worst:.2e})"
        )

    scored_ids = {s for i, s in enumerate(ids) if mask[:, i].any()}
    res["named_instruments"] = {
        "in_scored_set": [s for s in NAMED if s in scored_ids],
        "not_in_scored_set": [s for s in NAMED if s not in scored_ids],
    }
    (run_dir / "fit.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    write_fit_md(run_dir, summary, res, estimators, factors)
    write_html(run_dir / "predicted_vs_actual.html", res, R, F, betas, mask, ids, weeks, classes)
    print(f"wrote {run_dir / 'fit.md'}, fit.json and predicted_vs_actual.html")
    print(f"scored cells {res['cells']}; mean Huber loss reproduced to {worst:.1e}")
    print(
        "named instruments not in the scored set:",
        res["named_instruments"]["not_in_scored_set"] or "none",
    )


def write_fit_md(run_dir: Path, summary: dict, res: dict, estimators, factors) -> None:
    ests = res["estimators"]
    classes = sorted(ests[estimators[0]]["by_class"])
    lines = [
        f"# Absolute fit of the loadings, {summary['run_id']}",
        "",
        DISCLAIMER,
        "",
        STORED,
        "",
        f"{res['cells']} scored cells (the score's: every estimator has a loading at week t, "
        f"week t+1 is observed, the volatility scale is known). `p = b_t' f_(t+1)` with no "
        f"intercept, `r` the week t+1 return. Mean Huber loss reproduces the run's "
        f"`summary.json` to {res['reproduces_scores_mean_huber_loss']['max_abs_difference']:.1e}.",
        "",
        "`r2_oos = 1 - sum (r-p)^2 / sum r^2`; `huber_skill = 1 - loss / loss_zero`, the score's "
        "Huber loss on volatility-scaled errors against `p = 0`. Both are against a loading of "
        "zero. `r2_oos` is in raw returns, so high-volatility instruments weigh most; "
        "`huber_skill` is scaled by each instrument's own volatility.",
        "",
    ]
    for metric in ("r2_oos", "huber_skill"):
        lines += [f"## {metric}, pooled, by class and in the four slices", ""]
        cols = ["pooled", *classes, *ests[estimators[0]]["slices"]]
        rows = []
        for e in estimators:
            v = ests[e]
            vals = [v["pooled"], *(v["by_class"][c] for c in classes), *v["slices"].values()]
            rows.append([e, *(f(x[metric], 4) for x in vals)])
        lines += md_table(["estimator", *cols], rows) + [""]
    lines += [
        "## ts_corr: per instrument, correlation of p and r over its scored weeks",
        "",
        "Instruments with at least 26 scored weeks. Median (q1, q3) by class.",
        "",
        *md_table(
            ["estimator", "pooled", *classes],
            [
                [
                    e,
                    *(
                        f"{f(q['median'], 3)} ({f(q['q1'], 3)}, {f(q['q3'], 3)})"
                        for q in (
                            ests[e]["ts_corr"]["pooled"],
                            *(ests[e]["ts_corr"]["by_class"][c] for c in classes),
                        )
                    ),
                ]
                for e in estimators
            ],
        ),
        "",
        "The ten lowest instruments, by ticker (ts_corr):",
        "",
    ]
    for e in estimators:
        lines.append(
            f"- {e}: " + ", ".join(f"{s} {v:.3f}" for s, v in ests[e]["ts_corr"]["lowest_ten"])
        )
    lines += [
        "",
        "## xs_corr: per week, Spearman of p and r across instruments",
        "",
        "**Conditional on the realised factor moves, not a forecast IC.** The loadings forecast "
        "sensitivities, not returns: `p` uses the factors of the week being predicted.",
        "",
        *md_table(
            ["estimator", "mean", "sd", "share of weeks above zero", "weeks"],
            [
                [e, f(x["mean"], 3), f(x["sd"], 3), f(x["share_above_zero"], 3), str(x["weeks"])]
                for e in estimators
                for x in (ests[e]["xs_corr"],)
            ],
        ),
        "",
        "## factor_share: each factor's share of the predicted variation, sum p b_k f_k / sum p^2",
        "",
        "The six shares sum to 1.",
        "",
    ]
    for e in estimators:
        fs = ests[e]["factor_share"]
        lines += [
            f"**{e}**",
            "",
            *md_table(
                ["class", *factors, "sum"],
                [[k, *(f(x, 3) for x in v), f(sum(v), 3)] for k, v in fs.items() if v is not None],
            ),
            "",
        ]
    ni = res["named_instruments"]
    lines += [
        "## The named instruments for `predicted_vs_actual.html`",
        "",
        f"In the scored set: {', '.join(ni['in_scored_set']) or 'none'}.",
        f"Not in the scored set (not substituted): {', '.join(ni['not_in_scored_set']) or 'none'}.",
        "",
    ]
    (run_dir / "fit.md").write_text("\n".join(lines), encoding="utf-8")


# --- the examples -----------------------------------------------------------------------------

PW, PH, PAD = 380, 260, 44


def _scale(lo, hi, a, b):
    span = (hi - lo) or 1.0
    return lambda v: a + (v - lo) / span * (b - a)


def _ticks(lo, hi, n=3) -> list[float]:
    return list(np.linspace(lo, hi, n))


def _frame(title: str, xlabel: str, ylabel: str, xs, ys, body: str, xfmt, yfmt) -> str:
    x0, x1, y0, y1 = PAD, PW - 10, 22, PH - PAD
    parts = [
        f'<svg viewBox="0 0 {PW} {PH}" width="{PW}" height="{PH}" role="img" aria-label="{title}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="system-ui, sans-serif" font-size="10">',
        f'<rect width="{PW}" height="{PH}" fill="#FFFFFF"/>',
        f'<text x="{x0}" y="13" fill="{INK}" font-size="11">{title}</text>',
    ]
    for t in _ticks(*xs):
        parts.append(
            f'<line x1="{xs_px(t, xs, x0, x1):.1f}" x2="{xs_px(t, xs, x0, x1):.1f}" y1="{y0}" y2="{y1}" stroke="{FAINT}" stroke-width="0.5"/>'
        )
        parts.append(
            f'<text x="{xs_px(t, xs, x0, x1):.1f}" y="{y1 + 12}" fill="{GREY}" text-anchor="middle">{xfmt(t)}</text>'
        )
    for t in _ticks(*ys):
        py = _scale(ys[0], ys[1], y1, y0)(t)
        parts.append(
            f'<line x1="{x0}" x2="{x1}" y1="{py:.1f}" y2="{py:.1f}" stroke="{FAINT}" stroke-width="0.5"/>'
        )
        parts.append(
            f'<text x="{x0 - 4}" y="{py + 3:.1f}" fill="{GREY}" text-anchor="end">{yfmt(t)}</text>'
        )
    parts += [
        body,
        f'<text x="{(x0 + x1) / 2}" y="{PH - 6}" fill="{INK}" text-anchor="middle">{xlabel}</text>',
        f'<text x="10" y="{(y0 + y1) / 2}" fill="{INK}" text-anchor="middle" transform="rotate(-90 10 {(y0 + y1) / 2})">{ylabel}</text>',
        "</svg>",
    ]
    return "\n".join(parts)


def xs_px(v, rng, a, b):
    return _scale(rng[0], rng[1], a, b)(v)


def write_html(path: Path, res, R, F, betas, mask, ids, weeks, classes) -> None:
    from signal_lab.measurement import describe

    pairs = (("rolling_ols", GREY, "rolling OLS"), (MR, ORANGE, "mean-reverting (own mean)"))
    P = {name: describe.predictions(betas[name], F)[0] for name, _, _ in pairs}
    cards = []
    for sid in NAMED:
        if sid not in ids or not mask[:, ids.index(sid)].any():
            cards.append(
                f"<section><h2>{sid}</h2><p>Not in the scored set. Not substituted.</p></section>"
            )
            continue
        i = ids.index(sid)
        m = mask[:, i]
        r = R[m, i]
        allp = np.concatenate([P[n][m, i] for n, _, _ in pairs])
        px = (float(allp.min()), float(allp.max()))
        ry = (float(r.min()), float(r.max()))
        lo = min(px[0], ry[0])
        hi = max(px[1], ry[1])
        pad = 0.05 * (hi - lo or 1.0)
        rng = (lo - pad, hi + pad)  # one range on both axes so the 45-degree line is the diagonal
        x0, x1, y0, y1 = PAD, PW - 10, 22, PH - PAD
        sx, sy = _scale(*rng, x0, x1), _scale(*rng, y1, y0)
        body = [
            f'<line x1="{sx(rng[0]):.1f}" y1="{sy(rng[0]):.1f}" x2="{sx(rng[1]):.1f}" y2="{sy(rng[1]):.1f}" stroke="{INK}" stroke-width="0.6" stroke-dasharray="3 3"/>'
        ]
        for name, colour, _label in pairs:
            p = P[name][m, i]
            op = "0.55" if name == MR else "0.5"
            body += [
                f'<circle cx="{sx(a):.1f}" cy="{sy(b):.1f}" r="2" fill="{colour}" fill-opacity="{op}"/>'
                for a, b in zip(p, r, strict=True)
            ]
        scatter = _frame(
            f"{sid}: predicted p against actual r",
            "predicted p",
            "actual r",
            rng,
            rng,
            "\n".join(body),
            lambda v: f"{v:.1%}",
            lambda v: f"{v:.1%}",
        )
        lines = []
        allc = []
        for name, colour, label in pairs:
            c = describe.rolling_corr(P[name][m, i], r)
            allc.append(c)
            lines.append((name, colour, label, c))
        n = int(m.sum())
        fin = (
            np.concatenate([c[np.isfinite(c)] for c in allc])
            if any(np.isfinite(c).any() for c in allc)
            else np.array([-1.0, 1.0])
        )
        cr = (min(-0.2, float(fin.min())), max(0.2, float(fin.max())))
        wk = weeks[m]
        tx = _scale(0, max(n - 1, 1), x0, x1)
        cy = _scale(*cr, y1, y0)
        body2 = [
            f'<line x1="{x0}" x2="{x1}" y1="{cy(0):.1f}" y2="{cy(0):.1f}" stroke="{INK}" stroke-width="0.6"/>'
        ]
        for _name, colour, label, c in lines:
            pts = " ".join(f"{tx(k):.1f},{cy(v):.1f}" for k, v in enumerate(c) if np.isfinite(v))
            if pts:
                body2.append(
                    f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="1.6"><title>{label}</title></polyline>'
                )
        roll = _frame(
            f"{sid}: {describe.ROLLING_CORR_WEEKS}-week rolling correlation of p and r",
            f"scored weeks, {wk[0].year} to {wk[-1].year}",
            "correlation",
            (0, max(n - 1, 1)),
            cr,
            "\n".join(body2),
            lambda v: f"{int(v)}",
            lambda v: f"{v:.2f}",
        )
        cards.append(
            f"<section><h2>{sid} <small>({classes[i]})</small></h2><div class=row>{scatter}{roll}</div></section>"
        )
    legend = "".join(f'<span><i style="background:{c}"></i>{lab}</span>' for _, c, lab in pairs)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Predicted against actual</title>
<style>
body{{background:#fff;color:{INK};font-family:system-ui,sans-serif;margin:16px;max-width:900px}}
h1{{font-size:18px}} h2{{font-size:14px;margin:18px 0 4px}} small{{color:{GREY};font-weight:normal}}
.row{{display:flex;flex-wrap:wrap;gap:8px}} .legend span{{margin-right:16px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:5px;margin-right:5px}}
p{{font-size:13px;max-width:70ch}}
</style></head><body>
<h1>Predicted against actual, rolling OLS and mean-reverting (own mean)</h1>
<p><b>A description made after the results were seen; not a test.</b> Each point is one scored week
of one instrument: the loading stored at t applied to the factor moves of week t+1 (no intercept)
against that week's return. The dashed line is p = r. This file holds weekly returns, which are
vendor data: it stays on this machine and is not committed.</p>
<p class="legend">{legend}</p>
{"".join(cards)}
</body></html>
"""
    path.write_text(html, encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("what", choices=("stability", "fit", "both"))
    parser.add_argument("--run", default=RUN_OF_RECORD)
    parser.add_argument("--out-root", default=str(OUT_ROOT))
    args = parser.parse_args(argv)
    run_dir = Path(args.out_root) / args.run
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    if args.what in ("stability", "both"):
        run_stability(run_dir, summary)
    if args.what in ("fit", "both"):
        run_fit(run_dir, summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
