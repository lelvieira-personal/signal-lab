#!/usr/bin/env python3
"""
The conversion's own check on real data (decisions/0053, HANDOFF task 53 step 3).

    make fx-check

`NDDLUK` is MSCI UK in sterling; `NDDUUK` is the same index in dollars. Converted `NDDLUK`
against `NDDUUK`, on weekly Friday closes from 2002-01-01 to 2019-12-27, shows how well the FX
file reproduces MSCI's own conversion. Four figures, then the same with the FX rate lagged one
business day. Writes `results/fx/conversion_check.md` and `.json`. Aggregates only: no level and
no rate is printed or written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

OUT_DIR = Path(__file__).resolve().parents[1] / "results" / "fx"
START, END = "2002-01-01", "2019-12-27"
LOCAL, DOLLAR, CCY = "NDDLUK", "NDDUUK", "GBP"
# Cowork's read of 2026-10-10 (decisions/0053), printed beside the measurement. Not a target.
COWORK = {"te_weekly_bp": 238.0, "te_4w_bp": 107.0, "autocorr_lag1": -0.51, "cum_gap_bp": -50.0}
TOL = {"te_weekly_bp": 5.0, "te_4w_bp": 5.0, "autocorr_lag1": 0.02, "cum_gap_bp": 5.0}


def _figures(conv, usd):
    import numpy as np
    import pandas as pd

    both = pd.concat({"c": conv, "u": usd}, axis=1).dropna()
    both = both.loc[(both.index >= START) & (both.index <= END)]
    fri = both.loc[both.index.dayofweek == 4]
    lr = np.log(fri).diff().dropna()
    diff = lr["c"] - lr["u"]
    te_w = float(diff.std(ddof=1) * np.sqrt(52) * 1e4)
    # 4-week: non-overlapping, every fourth Friday
    four = np.log(fri.iloc[::4]).diff().dropna()
    d4 = four["c"] - four["u"]
    te_4 = float(d4.std(ddof=1) * np.sqrt(13) * 1e4)
    # 4-week overlapping, for the record
    ov = np.log(fri).diff(4).dropna()
    dov = ov["c"] - ov["u"]
    te_4_ov = float(dov.std(ddof=1) * np.sqrt(13) * 1e4)
    ac = float(diff.autocorr(lag=1))
    cum = float(diff.sum() * 1e4)
    return {
        "n_weeks": int(len(diff)),
        "te_weekly_bp": te_w,
        "te_4w_bp": te_4,
        "te_4w_overlapping_bp": te_4_ov,
        "autocorr_lag1": ac,
        "cum_gap_bp": cum,
    }


# decisions/0053 addendum, HANDOFF task 54: the global aggregate restated in sterling and yen,
# converted, against the same aggregate in dollars. Cowork has no measurement of these.
GLOBAL_AGG = (("LGTRTRGU", "GBP"), ("LGTRTRJU", "JPY"))
BENCHMARK_LEG = "LEGATRUU"
STOP_ABOVE_BP = 1000.0


def main() -> int:
    from signal_lab.loaders.bloomberg import BloombergLoader
    from signal_lab.params import get_params

    loader = BloombergLoader(get_params())
    panel = loader.load_returns()
    rep = loader.report["fx"]
    if panel.meta[LOCAL].quote_currency != CCY:
        print(f"{LOCAL} was not converted from {CCY}; stopping", file=sys.stderr)
        return 1
    conv = panel.levels[LOCAL]
    usd = panel.levels[DOLLAR]

    rates, sha = loader._read_fx()
    rate = rates[CCY].reindex(conv.index)
    local = conv / rate  # exact where the rate exists; NaN where the level was dropped
    # the same local series, the rate of the previous business day
    lagged = local * rate.shift(1)

    same = _figures(conv, usd)
    lag = _figures(lagged, usd)
    result = {
        "pair": f"{LOCAL} converted ({CCY}) against {DOLLAR}",
        "window": [START, END],
        "fx_file_sha256_prefix": sha[:16],
        "same_day": same,
        "rate_lagged_one_business_day": lag,
        "cowork_read": COWORK,
        "n_dates_dropped": rep["converted"][LOCAL]["n_dates_dropped"],
    }

    bench = loader.load_benchmark().levels[BENCHMARK_LEG]
    pairs = {}
    for ticker, ccy in GLOBAL_AGG:
        if panel.meta[ticker].quote_currency != ccy:
            print(f"{ticker} was not converted from {ccy}; stopping", file=sys.stderr)
            return 1
        pairs[ticker] = {
            "currency": ccy,
            "against": BENCHMARK_LEG,
            "n_dates_dropped": rep["converted"][ticker]["n_dates_dropped"],
            **_figures(panel.levels[ticker], bench),
        }
    result["global_aggregate_same_day"] = pairs
    too_wide = {t: p["te_weekly_bp"] for t, p in pairs.items() if p["te_weekly_bp"] > STOP_ABOVE_BP}
    result["global_aggregate_above_1000bp"] = too_wide

    differs = {
        k: round(same[k] - COWORK[k], 3) for k in COWORK if abs(same[k] - COWORK[k]) > TOL[k]
    }
    better = same["te_weekly_bp"] < lag["te_weekly_bp"]
    result["differs_from_cowork_beyond_tolerance"] = differs
    result["same_day_is_the_better_alignment"] = bool(better)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "conversion_check.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# FX conversion check (decisions/0053, HANDOFF task 53)",
        "",
        f"`{LOCAL}` converted from {CCY} against `{DOLLAR}`, weekly Friday closes, "
        f"{START} to {END}. FX file sha256 `{sha[:16]}...`. Aggregates only.",
        "",
        "| Figure | Same day | Rate lagged one business day | Cowork's read |",
        "|---|---|---|---|",
    ]
    labels = {
        "te_weekly_bp": "Weekly tracking error (bp/yr)",
        "te_4w_bp": "4-week tracking error, non-overlapping (bp/yr)",
        "autocorr_lag1": "Lag-1 autocorrelation of the weekly difference",
        "cum_gap_bp": "Cumulative gap (bp)",
    }
    for k, label in labels.items():
        lines.append(f"| {label} | {same[k]:.2f} | {lag[k]:.2f} | {COWORK[k]} |")
    lines += [
        f"| 4-week tracking error, overlapping (bp/yr) | {same['te_4w_overlapping_bp']:.2f} "
        f"| {lag['te_4w_overlapping_bp']:.2f} | |",
        f"| Weeks | {same['n_weeks']} | {lag['n_weeks']} | |",
        "",
        f"- Same-day is the better alignment: **{better}**.",
        f"- Figures differing from Cowork's by more than the tolerance "
        f"(5 bp, 0.02): {differs or 'none'}.",
        f"- `{LOCAL}` dates dropped for want of an FX rate: {result['n_dates_dropped']}.",
        "",
        f"## The global aggregate restated, converted, against `{BENCHMARK_LEG}` (same day)",
        "",
        "| Series | Currency | Weekly TE (bp/yr) | Lag-1 autocorrelation | Cumulative gap (bp) "
        "| Weeks | FX dates dropped |",
        "|---|---|---|---|---|---|---|",
        *(
            f"| `{t}` | {p['currency']} | {p['te_weekly_bp']:.2f} | {p['autocorr_lag1']:.2f} "
            f"| {p['cum_gap_bp']:.2f} | {p['n_weeks']} | {p['n_dates_dropped']} |"
            for t, p in pairs.items()
        ),
        "",
        f"- Above {STOP_ABOVE_BP:.0f} bp/yr (the direction or the series would be wrong): "
        f"{too_wide or 'none'}.",
    ]
    (OUT_DIR / "conversion_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if too_wide:
        return 3
    return 0 if better else 2


if __name__ == "__main__":
    sys.exit(main())
