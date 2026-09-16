"""
One function per veto in SUBSTRATE section 10, as amended by decisions/0003
(the tracking_error statistic loosened from the maximum to the 95th percentile)
and by decisions/0026 (active_drawdown removed: drawdown is a consequence of the
tracking-error budget, which decisions/0025 derives from the drawdown
tolerance). Ten vetoes.

Signature: veto(ctx: RunContext, params: Params | None) -> Verdict.
Thresholds are read from params/vetoes.yaml on every call, never cached and
never defaulted, so a run cannot be evaluated against a stale ceiling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.harness.run_context import MissingInput, RunContext
from signal_lab.loaders.invariants import frequency_breaches
from signal_lab.params import Params, get_params
from signal_lab.results.store import Verdict


def _p(params: Params | None) -> Params:
    return params or get_params()


def _missing(name: str, exc: MissingInput) -> Verdict:
    """
    The verdict for a veto that could not be evaluated.

    params/vetoes.yaml sets evaluation.on_missing_input: fail. This is not a
    technicality: an unevaluated constraint is an unenforced constraint, and a
    run that reaches the leaderboard with one is exactly the failure mode the
    veto set exists to prevent.
    """
    return Verdict(
        passed=False,
        veto=name,
        detail=f"cannot evaluate: missing input {exc}. Fail-closed per params/vetoes.yaml.",
    )


# The ceiling itself must pass (SUBSTRATE section 10), and a realised figure is
# a float aggregate -- a mean over 52 weeks, a percentile, a max -- so summation
# error can put a book that trades EXACTLY the ceiling a few ulps above it. At a
# 1.50 ceiling the arithmetic happened to land clean; at the 4.00 backstop
# decisions/0024 set, `4.00 / 52 * 52` does not. The tolerance is relative and
# 1e-9, which is nine orders of magnitude below any threshold in
# params/vetoes.yaml and cannot admit a breach anyone could measure. It is the
# same reading `audit.ladder.portfolio_veto_verdicts` already used, so the audit
# and the live veto set now agree at the boundary.
_REL_TOL = 1e-9


def _at_most(realised: float, cap: float) -> bool:
    """`realised <= cap`, at floating-point tolerance. See _REL_TOL."""
    return float(realised) <= float(cap) * (1.0 + _REL_TOL)


# --- 1. turnover -------------------------------------------------------------


def veto_turnover(ctx: RunContext, params: Params | None = None) -> Verdict:
    """Annualised one-way turnover against the ceiling in params."""
    cap = float(_p(params).require("vetoes.turnover.max_annualised"))
    try:
        realised = ctx.annualised_turnover()
    except MissingInput as exc:
        return _missing("turnover", exc)
    return Verdict(
        passed=_at_most(realised, cap),
        veto="turnover",
        detail=f"annualised turnover {realised:.1%} against a {cap:.0%} ceiling",
    )


# --- 2. cash -----------------------------------------------------------------


def veto_cash(ctx: RunContext, params: Params | None = None) -> Verdict:
    """Maximum cash weight over the run against the ceiling in params."""
    cap = float(_p(params).require("vetoes.cash.max_weight"))
    try:
        cash = ctx.require("cash_weights")
    except MissingInput as exc:
        return _missing("cash", exc)
    realised = float(pd.Series(cash).max())
    return Verdict(
        passed=_at_most(realised, cap),
        veto="cash",
        detail=f"max cash weight {realised:.1%} against a {cap:.0%} ceiling",
    )


# --- 3. tracking_error -------------------------------------------------------


def veto_tracking_error(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    Trailing-3y tracking error against the ceiling.

    params/vetoes.yaml sets `statistic: p95` -- the 95th percentile of trailing-3y
    readings. SUBSTRATE section 4 allows episodic excursions and section 10
    states a hard ceiling; the 95th percentile is what "episodic" has to mean if
    it means anything, since the maximum makes one bad quarter in nineteen years
    fatal. See decisions/0003.

    This is the lab's only ex-post risk gate. What the investor actually
    experienced -- the active drawdown -- is controlled ex ante instead, through
    the budget this ceiling enforces: decisions/0025 derives that budget FROM a
    drawdown tolerance, and decisions/0026 removed the separate realised-drawdown
    veto rather than charge the same risk twice.
    """
    p = _p(params)
    cap = float(p.require("vetoes.tracking_error.max_trailing_3y"))
    statistic = str(p.get("vetoes.tracking_error.statistic", "max"))
    try:
        te = pd.Series(ctx.require("te_trailing_3y")).dropna()
    except MissingInput as exc:
        return _missing("tracking_error", exc)
    if te.empty:
        return _missing("tracking_error", MissingInput("te_trailing_3y (all NaN)"))
    if statistic == "max":
        realised = float(te.max())
    elif statistic == "last":
        realised = float(te.iloc[-1])
    elif statistic.startswith("p"):
        realised = float(np.percentile(te.to_numpy(), float(statistic[1:])))
    else:
        return Verdict(
            passed=False,
            veto="tracking_error",
            detail=f"unknown tracking_error statistic {statistic!r} in params/vetoes.yaml",
        )
    return Verdict(
        passed=_at_most(realised, cap),
        veto="tracking_error",
        detail=(
            f"{statistic} trailing-3y TE {realised:.2%} against a {cap:.1%} ceiling "
            f"(worst reading {float(te.max()):.2%})"
        ),
    )


# --- 4. positions ------------------------------------------------------------


def veto_positions(ctx: RunContext, params: Params | None = None) -> Verdict:
    """Maximum count of non-zero instrument weights on any rebalance date."""
    cap = int(_p(params).require("vetoes.positions.max_nonzero"))
    try:
        weights = ctx.require("weights")
    except MissingInput as exc:
        return _missing("positions", exc)
    counts = (weights.abs() > 0).sum(axis=1)
    realised = int(counts.max())
    return Verdict(
        passed=realised <= cap,
        veto="positions",
        detail=f"max {realised} non-zero weights against a ceiling of {cap}",
    )


# --- 5. coverage -------------------------------------------------------------


def veto_coverage(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    Signal available for >= 80% of the estimation universe on >= 90% of dates.

    Coverage is measured on the estimation universe (SUBSTRATE section 5.2:
    tradable-only series are never used to estimate a signal), so a signal is
    not credited for covering instruments it may not learn from.
    """
    p = _p(params)
    min_universe = float(p.require("vetoes.coverage.min_universe_fraction"))
    min_dates = float(p.require("vetoes.coverage.min_date_fraction"))
    try:
        avail = ctx.require("signal_availability")
    except MissingInput as exc:
        return _missing("coverage", exc)

    universe = ctx.estimation_universe or list(avail.columns)
    cols = [c for c in universe if c in avail.columns]
    if not cols:
        return _missing("coverage", MissingInput("estimation_universe not present in availability"))

    per_date = avail[cols].astype(bool).mean(axis=1)
    date_fraction = float((per_date >= min_universe).mean())
    return Verdict(
        passed=date_fraction >= min_dates,
        veto="coverage",
        detail=(
            f"signal covered >= {min_universe:.0%} of {len(cols)} estimation series on "
            f"{date_fraction:.1%} of dates, needs {min_dates:.0%}"
        ),
    )


# --- 6. lookahead ------------------------------------------------------------


def veto_lookahead(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    Bitemporal check: no observation used before its knowledge date.

    `observation_usage` carries knowledge_date and used_on_date for every macro
    observation the run consumed. A single row with used_on_date earlier than
    knowledge_date is a peek at a number nobody had, and invalidates everything
    downstream, which is why this veto is evaluated first.
    """
    _p(params).require("vetoes.lookahead.strict")
    try:
        usage = ctx.require("observation_usage")
    except MissingInput as exc:
        return _missing("lookahead", exc)

    for col in ("knowledge_date", "used_on_date"):
        if col not in usage.columns:
            return _missing("lookahead", MissingInput(f"observation_usage.{col}"))

    known = pd.to_datetime(usage["knowledge_date"])
    used = pd.to_datetime(usage["used_on_date"])
    breaches = usage.loc[used < known]
    n = len(breaches)
    if n == 0:
        return Verdict(
            passed=True,
            veto="lookahead",
            detail=f"{len(usage)} observations, none used before its knowledge date",
        )
    worst = int((known - used).dt.days.max())
    series = sorted(breaches["series_id"].unique().tolist())[:5] if "series_id" in breaches else []
    return Verdict(
        passed=False,
        veto="lookahead",
        detail=(
            f"{n} observation(s) used before their knowledge date, worst by {worst} days"
            + (f", e.g. {series}" if series else "")
        ),
    )


# --- 7. frequency ------------------------------------------------------------


def veto_frequency(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    No series contributes a return before its true daily start.

    A return dated before that start was built from month-end observations
    spliced into a daily panel, which SUBSTRATE section 2 forbids outright. The
    breach is usually invisible in aggregate statistics and very visible here.
    """
    _p(params).require("vetoes.frequency.strict")
    try:
        contributions = ctx.require("return_contributions")
        meta = ctx.require("series_meta")
    except MissingInput as exc:
        return _missing("frequency", exc)

    for col in ("series_id", "date"):
        if col not in contributions.columns:
            return _missing("frequency", MissingInput(f"return_contributions.{col}"))

    breaches = frequency_breaches(contributions, meta)
    n = len(breaches)
    if n == 0:
        return Verdict(
            passed=True,
            veto="frequency",
            detail=(
                f"{len(contributions)} contributions across "
                f"{contributions['series_id'].nunique()} series, none before its daily start"
            ),
        )
    offenders = sorted(breaches["series_id"].unique().tolist())
    return Verdict(
        passed=False,
        veto="frequency",
        detail=(
            f"{n} return(s) dated before the series' true daily start across "
            f"{len(offenders)} series, e.g. {offenders[:5]}"
        ),
    )


# --- 8. seed_stability -------------------------------------------------------


def veto_seed_stability(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    IR range across resampling seeds. SUBSTRATE section 9.

    A result that moves materially when the resampling seed changes is a
    property of the draw, not of the signal.
    """
    cap = float(_p(params).require("vetoes.seed_stability.max_ir_range"))
    try:
        seed_irs = ctx.require("seed_irs")
    except MissingInput as exc:
        return _missing("seed_stability", exc)
    values = [float(v) for v in dict(seed_irs).values() if v is not None and not np.isnan(v)]
    if len(values) < 2:
        return _missing("seed_stability", MissingInput("seed_irs (needs >= 2 seeds)"))
    spread = float(max(values) - min(values))
    return Verdict(
        passed=_at_most(spread, cap),
        veto="seed_stability",
        detail=f"IR range {spread:.3f} across {len(values)} seeds against a {cap:.2f} ceiling",
    )


# --- 9. multiple_testing ------------------------------------------------------


def veto_multiple_testing(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    Survives Romano-Wolf stepdown at the family-wise error rate in params.

    This veto reads a verdict; it does not run the procedure. The stepdown lives
    in src/stats/ (phase 3) because it needs the joint distribution of every
    test statistic in the search, which is a property of the cycle rather than
    of one run. What the veto enforces here is that the verdict exists, was
    produced at the configured alpha, and rejected the null.

    The alpha is checked rather than trusted: a stepdown run at 10% and reported
    against a 5% ceiling would otherwise pass silently.
    """
    p = _p(params)
    alpha = float(p.require("vetoes.multiple_testing.fwer_alpha"))
    procedure = str(p.require("vetoes.multiple_testing.procedure"))
    try:
        result = dict(ctx.require("romano_wolf"))
    except MissingInput as exc:
        return _missing("multiple_testing", exc)

    if "rejected" not in result:
        return _missing("multiple_testing", MissingInput("romano_wolf.rejected"))

    reported_alpha = result.get("fwer_alpha")
    if reported_alpha is None or not np.isclose(float(reported_alpha), alpha):
        return Verdict(
            passed=False,
            veto="multiple_testing",
            detail=(
                f"stepdown reported at alpha {reported_alpha} but params require "
                f"{alpha}; a verdict at another level is not this test"
            ),
        )
    reported_procedure = str(result.get("procedure", procedure))
    if reported_procedure != procedure:
        return Verdict(
            passed=False,
            veto="multiple_testing",
            detail=f"verdict came from {reported_procedure!r}, params require {procedure!r}",
        )

    rejected = bool(result["rejected"])
    level = result.get("level", p.get("vetoes.multiple_testing.level", "family_then_within"))
    n_tests = result.get("n_tests", "unknown")
    return Verdict(
        passed=rejected,
        veto="multiple_testing",
        detail=(
            f"{procedure} at FWER {alpha:.0%} ({level}, {n_tests} tests): "
            f"{'rejected the null' if rejected else 'did not reject the null'}"
        ),
    )


# --- 10. direction ------------------------------------------------------------


def veto_direction(ctx: RunContext, params: Params | None = None) -> Verdict:
    """
    Realised sign matches the pre-registered direction.

    SUBSTRATE section 7: a hypothesis whose result contradicts its stated
    direction is recorded as a failure, not flipped. This veto is what makes
    that binding, and it is the reason pre-registration is worth the friction.
    """
    _p(params).require("vetoes.direction.strict")
    try:
        expected = str(ctx.require("preregistered_direction")).lower()
        realised = str(ctx.require("realised_direction")).lower()
    except MissingInput as exc:
        return _missing("direction", exc)

    valid = {"positive", "negative"}
    if expected not in valid:
        return Verdict(
            passed=False,
            veto="direction",
            detail=f"pre-registered direction {expected!r} is not one of {sorted(valid)}",
        )
    if realised not in valid | {"flat"}:
        return Verdict(
            passed=False,
            veto="direction",
            detail=f"realised direction {realised!r} is not interpretable",
        )
    return Verdict(
        passed=realised == expected,
        veto="direction",
        detail=f"pre-registered {expected}, realised {realised}",
    )
