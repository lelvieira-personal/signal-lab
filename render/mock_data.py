"""
SYNTHETIC DATA ONLY -- for UI layout review.

Every number produced here is generated from a fixed random seed.
None of it comes from real market data, real signals, or real backtests.
This module exists purely so the render layer has something shaped like
real results to draw. Delete it once the harness writes to results/runs.db.
"""

import numpy as np
import pandas as pd

SEED = 20260905
RNG = np.random.default_rng(SEED)


def _window():
    """The development window comes from params, never from a literal here."""
    try:
        from signal_lab.params import get_params

        p = get_params()
        return str(p.require("data.windows.dev_start")), str(p.require("data.windows.dev_end"))
    except Exception:  # noqa: BLE001 - the mock must render even with no params
        return "2001-01-05", "2019-12-27"


DEV_START, DEV_END = _window()

# SUBSTRATE section 6, all eleven.
SIGNAL_FAMILIES = [
    "growth",
    "inflation",
    "policy_rates",
    "credit_conditions",
    "liquidity",
    "terms_of_trade",
    "spreads_curve",
    "volatility_stress",
    "trend",
    "carry",
    "valuation",
]

AGGREGATIONS = [
    "shrunk z-score mean",
    "entropy-weighted",
    "BL view vector",
    "equal-weight family",
    "rank-IC weighted",
]

# All ten of SUBSTRATE section 10. The labels are only for the mock; the live
# report reads them from params via views.veto_legend().
VETOES = [
    ("turnover", "Annualised turnover \u2264 400% \u2014 a backstop, not a budget"),
    ("cash", "Max cash weight \u2264 20%"),
    ("tracking_error", "Trailing-3y tracking error \u2264 6.0%"),
    ("positions", "Non-zero holdings \u2264 30"),
    ("coverage", "Signal coverage \u2265 80% of universe on \u2265 90% of dates"),
    ("lookahead", "Bitemporal check: no future vintages"),
    ("frequency", "No return before a series' true daily start"),
    ("seed_stability", "IR range across resampling seeds \u2264 0.15"),
    ("multiple_testing", "Survives Romano-Wolf stepdown at FWER 5%"),
    ("direction", "Realised sign matches the pre-registered direction"),
]


def weekly_index(start, end):
    return pd.date_range(start, end, freq="W-FRI")


def _run_series(dates, ir, te, seed):
    """Active (excess vs 50/50) weekly return series with a target IR and TE."""
    rng = np.random.default_rng(seed)
    n = len(dates)
    wk_te = te / np.sqrt(52)
    # fat-ish tails plus mild autocorrelation, so drawdowns look plausible
    raw = rng.standard_t(df=6, size=n) / np.sqrt(6 / 4)
    raw = pd.Series(raw).ewm(alpha=0.6).mean().to_numpy()
    raw = (raw - raw.mean()) / raw.std()
    return pd.Series(raw * wk_te + ir * te / 52, index=dates)


def build_runs():
    """One row per experiment. Mix of survivors and veto failures."""
    rows = []
    dates = weekly_index(DEV_START, DEV_END)
    for i in range(28):
        fam = SIGNAL_FAMILIES[i % len(SIGNAL_FAMILIES)]
        agg = AGGREGATIONS[(i * 3) % len(AGGREGATIONS)]
        rng = np.random.default_rng(SEED + i)

        ir = float(np.clip(rng.normal(0.22, 0.30), -0.55, 0.95))
        te = float(np.clip(rng.normal(4.2, 1.4), 1.6, 8.5))
        turnover = float(np.clip(rng.normal(128, 40), 45, 260))
        max_cash = float(np.clip(rng.normal(11, 7), 0, 34))
        coverage = float(np.clip(rng.normal(0.91, 0.09), 0.55, 1.0))
        seed_range = float(np.clip(rng.normal(0.09, 0.06), 0.01, 0.34))
        max_active_dd = float(np.clip(rng.normal(16.0, 6.0), 3.0, 42.0))
        cost_drag = float(np.clip(rng.normal(0.22, 0.08), 0.05, 0.55))
        lookahead_ok = rng.random() > 0.07
        n_positions = int(rng.integers(18, 33))
        null_pct = float(np.clip(rng.normal(0.72, 0.20), 0.01, 0.999))
        ess_cycles = float(rng.integers(3, 14))

        verdicts = {
            "lookahead": bool(lookahead_ok),
            "frequency": bool(rng.random() > 0.04),
            "coverage": coverage >= 0.80,
            "turnover": turnover <= 150,
            "cash": max_cash <= 20,
            "tracking_error": te <= 6.0,
            "positions": n_positions <= 30,
            "seed_stability": seed_range <= 0.15,
            "multiple_testing": bool(rng.random() > 0.55),
            "direction": bool(rng.random() > 0.18),
        }
        passed = all(verdicts.values())

        rows.append(
            {
                "run_id": f"R-{2026}{i:03d}",
                "family": fam,
                "aggregation": agg,
                "net_ir": round(ir, 2),
                "te": round(te, 1),
                "turnover": round(turnover),
                "max_cash": round(max_cash, 1),
                "coverage": round(coverage, 2),
                "seed_range": round(seed_range, 2),
                "max_active_drawdown": round(max_active_dd, 1),
                "cost_drag": round(cost_drag, 2),
                "n_positions": n_positions,
                "null_pct": round(null_pct, 3),
                "ess_cycles": ess_cycles,
                "status": "completed",
                "killed_by": None,
                "verdicts": verdicts,
                "passed": passed,
                "series": _run_series(dates, ir, te / 100, SEED + 500 + i),
            }
        )

    runs = sorted(rows, key=lambda r: (-r["passed"], -r["net_ir"]))
    return runs, dates


def build_detail(run, dates):
    """Everything the run-detail view needs, for a single run."""
    rng = np.random.default_rng(SEED + 99)
    active = run["series"]

    bench_wk = pd.Series(
        rng.standard_t(df=5, size=len(dates)) / np.sqrt(5 / 3) * (0.095 / np.sqrt(52)) + 0.055 / 52,
        index=dates,
    )
    strat_wk = bench_wk + active

    cum_strat = (1 + strat_wk).cumprod()
    cum_bench = (1 + bench_wk).cumprod()

    cum_active = (1 + active).cumprod()
    dd = cum_active / cum_active.cummax() - 1

    roll_excess = active.rolling(52).sum()
    roll_te = active.rolling(52).std() * np.sqrt(52) * 100

    turnover_wk = pd.Series(np.clip(rng.gamma(2.2, 0.9, len(dates)), 0.1, None), index=dates)
    turnover_wk = turnover_wk / turnover_wk.sum() * (run["turnover"] / 100) * (len(dates) / 52)
    cost_wk = turnover_wk * 0.0006  # 6bp per unit turnover, placeholder
    cum_cost = cost_wk.cumsum() * 100

    axes = ["Duration", "Credit", "Region", "Sector", "Style", "FX", "Cash"]
    base = np.array([0.9, 0.7, 1.1, 0.8, 1.0, 0.4, 0.5])
    w = np.zeros((len(dates), len(axes)))
    for j in range(len(axes)):
        s = pd.Series(rng.normal(0, 1, len(dates))).ewm(span=26).mean()
        w[:, j] = (s / s.std()).to_numpy() * base[j] * 3.0
    active_weights = pd.DataFrame(w, index=dates, columns=axes)

    risk_axes = [
        "Duration",
        "Credit spread",
        "Equity region",
        "Sector",
        "Style",
        "FX",
        "Idiosyncratic",
    ]
    risk_contrib = np.array([1.42, 0.88, 1.05, 0.61, 0.74, 0.22, 0.38])
    risk_contrib = risk_contrib / risk_contrib.sum() * run["te"]

    ic_mean = {f: float(np.clip(rng.normal(0.035, 0.028), -0.03, 0.11)) for f in SIGNAL_FAMILIES}
    ic_se = {f: float(np.clip(rng.normal(0.019, 0.005), 0.008, 0.035)) for f in SIGNAL_FAMILIES}

    null_max_ir = rng.normal(0.41, 0.13, 4000)

    return {
        "dates": dates,
        "cum_strat": cum_strat,
        "cum_bench": cum_bench,
        "drawdown": dd,
        "roll_excess": roll_excess,
        "roll_te": roll_te,
        "turnover_wk": turnover_wk,
        "cum_cost": cum_cost,
        "active_weights": active_weights,
        "risk_axes": risk_axes,
        "risk_contrib": risk_contrib,
        "ic_mean": ic_mean,
        "ic_se": ic_se,
        "null_max_ir": null_max_ir,
    }
