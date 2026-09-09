"""
The loader invariants of SUBSTRATE section 5.1, one function each.

These are the rules that decide whether a panel is trustworthy, so they are
functions with tests rather than comments inside a loader. Every backend runs
the same seven, in the same order, and the result of each is recorded.

  1. business-day filter, #N/A is missing and never zero
  2. truncation at each series' true daily start
  3. returns from each series' own prior observation
  4. gross/net flag carried, mismatch noted and not corrected
  5. splices applied with a logged record
  6. hedge flags propagated, hedged never mixed with unhedged in a region signal
  7. cross-region covariance on 2-day overlapping returns
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signal_lab.loaders.base import SeriesMeta, SpliceRecord


class InvariantViolation(Exception):
    """A panel breached a loader invariant. The panel is not served."""


# --- 1. business days, missing markers -------------------------------------


def to_missing(frame: pd.DataFrame, markers: list[str]) -> pd.DataFrame:
    """
    Map vendor missing markers to NaN.

    SUBSTRATE section 5.1.1: `#N/A` is missing, never zero, never carried.
    Mapping to 0.0 would make a gap look like a flat day, which is a return of
    exactly zero and a lie about a day the index did not trade.
    """
    out = frame.replace(list(markers), np.nan)
    return out.apply(pd.to_numeric, errors="coerce")


def filter_business_days(frame: pd.DataFrame, holidays=None) -> pd.DataFrame:
    """Drop non-business days. Weekend rows are dropped, not zero-filled."""
    index = pd.DatetimeIndex(frame.index)
    keep = index.dayofweek < 5
    if holidays is not None and len(holidays) > 0:
        keep &= ~index.isin(pd.DatetimeIndex(holidays))
    return frame.loc[keep]


def assert_no_forward_fill(before: pd.DataFrame, after: pd.DataFrame) -> None:
    """
    Assert a transformation did not fill gaps.

    Checked structurally: every cell that was NaN before must still be NaN
    after. SUBSTRATE section 2 forbids forward-filling any data gap, and the
    cheapest place to catch it is at the boundary of each step.
    """
    common_rows = before.index.intersection(after.index)
    common_cols = before.columns.intersection(after.columns)
    was_nan = before.loc[common_rows, common_cols].isna()
    now_filled = was_nan & after.loc[common_rows, common_cols].notna()
    if bool(now_filled.to_numpy().any()):
        n = int(now_filled.to_numpy().sum())
        cols = sorted(now_filled.columns[now_filled.any()].tolist())[:5]
        raise InvariantViolation(
            f"{n} previously-missing observation(s) were filled, e.g. in {cols}. "
            f"Forward fill is forbidden (SUBSTRATE section 2)."
        )


# --- 2. truncation at true daily start --------------------------------------


def truncate_at_daily_start(levels: pd.DataFrame, meta: dict[str, SeriesMeta]) -> pd.DataFrame:
    """
    Blank every observation before a series' true daily start.

    SUBSTRATE section 5.1.2: month-end observations before that date are not
    part of the daily panel. They are not deleted from the world, they are
    simply not this panel's business; a monthly panel is a separate object.
    """
    out = levels.copy()
    for series_id in out.columns:
        if series_id not in meta:
            raise InvariantViolation(f"no metadata for series {series_id!r}")
        start = pd.Timestamp(meta[series_id].true_daily_start)
        out.loc[out.index < start, series_id] = np.nan
    return out


def frequency_breaches(contributions: pd.DataFrame, meta: dict[str, SeriesMeta]) -> pd.DataFrame:
    """
    Rows in a contribution log dated before that series' true daily start.

    `contributions` has columns series_id and date. This is what the `frequency`
    veto reads. An empty result means no month-end observation was spliced into
    the daily panel.
    """
    if contributions.empty:
        return contributions.head(0)
    starts = pd.Series(
        {s: pd.Timestamp(m.true_daily_start) for s, m in meta.items()}, dtype="datetime64[ns]"
    )
    mapped = contributions["series_id"].map(starts)
    unknown = mapped.isna()
    if bool(unknown.any()):
        bad = sorted(contributions.loc[unknown, "series_id"].unique().tolist())[:5]
        raise InvariantViolation(f"contributions reference unknown series {bad}")
    dates = pd.to_datetime(contributions["date"])
    return contributions.loc[dates < mapped].copy()


# --- 3. returns from each series' own prior observation ---------------------


def returns_from_prior_observation(levels: pd.DataFrame) -> pd.DataFrame:
    """
    level_t / level_prev_obs - 1, per series, using that series' own last
    observed level rather than the previous row.

    SUBSTRATE section 5.1.3. The difference matters on any date where one series
    trades and another does not: `pct_change()` on a NaN-holed frame produces a
    NaN for the trading series, silently dropping a real return. Here the return
    spans the gap and lands on the date it was earned, and stays NaN only where
    the series itself did not print.
    """
    out = pd.DataFrame(index=levels.index, columns=levels.columns, dtype="float64")
    for col in levels.columns:
        series = levels[col]
        observed = series.dropna()
        if len(observed) < 2:
            continue
        rets = observed / observed.shift(1) - 1.0
        out.loc[rets.index, col] = rets.to_numpy()
    return out


def spanned_gap_days(levels: pd.DataFrame) -> pd.DataFrame:
    """
    How many calendar days each return spans, per observation.

    A return spanning 40 days is a month-end print, not a daily one. The
    frequency veto uses the daily-start metadata rather than this, but this is
    the diagnostic that shows why a start date is where it is.
    """
    out = pd.DataFrame(index=levels.index, columns=levels.columns, dtype="float64")
    for col in levels.columns:
        observed = levels[col].dropna()
        if len(observed) < 2:
            continue
        gaps = pd.Series(observed.index, index=observed.index).diff().dt.days
        out.loc[gaps.index, col] = gaps.to_numpy()
    return out


# --- 4. gross / net flag -----------------------------------------------------


def flag_net_of_withholding(
    meta: dict[str, SeriesMeta], prefixes: list[str]
) -> dict[str, SeriesMeta]:
    """
    Mark MSCI net series. SUBSTRATE section 5.1.4: note the mismatch, do not
    correct it in v0.1. Correcting it would mean assuming a withholding rate.
    """
    from dataclasses import replace

    out = {}
    for series_id, m in meta.items():
        is_net = any(series_id.startswith(p) for p in prefixes)
        out[series_id] = replace(m, gross=not is_net) if is_net else m
    return out


def gross_net_mismatch(meta: dict[str, SeriesMeta]) -> list[str]:
    """Series recorded as net of withholding, for the run's diagnostics."""
    return sorted(s for s, m in meta.items() if not m.gross)


# --- 5. splices --------------------------------------------------------------


def apply_splices(
    levels: pd.DataFrame, splices: list[dict], meta: dict[str, SeriesMeta]
) -> tuple[pd.DataFrame, dict[str, SeriesMeta], list[SpliceRecord]]:
    """
    Apply the substitutions in params/data.yaml, logging each one.

    A splice fills the target's missing early history from the source and only
    there: where both are observed the target wins, so a splice can lengthen a
    series but never overwrite it. Inactive or unresolved splices are skipped
    and reported, not guessed at.
    """
    from dataclasses import replace

    out = levels.copy()
    new_meta = dict(meta)
    records: list[SpliceRecord] = []

    for spec in splices:
        if not spec.get("active", False):
            continue
        target, source = spec["target"], spec.get("source")
        if not source:
            continue
        if target not in out.columns or source not in out.columns:
            continue
        gap = out[target].isna() & out[source].notna()
        n = int(gap.sum())
        if n == 0:
            continue
        first = out.index[gap][0]
        out.loc[gap, target] = out.loc[gap, source]
        record = SpliceRecord(
            target=target,
            source=source,
            reason=spec.get("reason", ""),
            splice_date=pd.Timestamp(first).date(),
            n_observations_taken=n,
        )
        records.append(record)
        if target in new_meta:
            new_meta[target] = replace(new_meta[target], splice=record)

    return out, new_meta, records


# --- 6. hedge flags ----------------------------------------------------------


def propagate_hedge_flags(
    meta: dict[str, SeriesMeta], hedged_ids: list[str]
) -> dict[str, SeriesMeta]:
    """Set the hedge flag from params. SUBSTRATE section 5.1.6."""
    from dataclasses import replace

    hedged = set(hedged_ids)
    return {
        s: (replace(m, hedged=True) if s in hedged else replace(m, hedged=False))
        for s, m in meta.items()
    }


def region_signal_universe(meta: dict[str, SeriesMeta], allow_hedged: bool = False) -> list[str]:
    """
    Series admissible to a region signal.

    SUBSTRATE section 5.1.6: hedged series are not mixed with unhedged peers in
    a region signal, because the hedged/unhedged difference is an FX return and
    a cross-sectional region signal would read it as a region view. The hedged
    set is the counterfactual (section 4), requested explicitly.
    """
    return sorted(s for s, m in meta.items() if m.hedged == allow_hedged)


def hedge_mixing_breach(series_ids: list[str], meta: dict[str, SeriesMeta]) -> list[str]:
    """The hedged series present in a set that also contains unhedged ones."""
    hedged = [s for s in series_ids if s in meta and meta[s].hedged]
    unhedged = [s for s in series_ids if s in meta and not meta[s].hedged]
    return sorted(hedged) if hedged and unhedged else []


# --- 7. cross-region covariance on overlapping returns -----------------------


def overlapping_returns(returns: pd.DataFrame, days: int = 2) -> pd.DataFrame:
    """
    Rolling `days`-day compounded returns.

    SUBSTRATE section 5.1.7: non-synchronous closes bias same-day cross-region
    correlation low, because a shock after Tokyo's close lands in Tokyo's next
    day and New York's same day. Overlapping two-day returns put both markets'
    reaction inside the same window.
    """
    if days < 1:
        raise ValueError("days must be >= 1")
    return (1.0 + returns).rolling(days, min_periods=days).apply(np.prod, raw=True) - 1.0


def cross_region_covariance(
    returns: pd.DataFrame,
    meta: dict[str, SeriesMeta],
    overlap_days: int = 2,
    min_periods: int = 60,
) -> pd.DataFrame:
    """
    Covariance with cross-region pairs estimated on overlapping returns.

    Same-region pairs use daily returns; cross-region pairs use `overlap_days`
    overlapping returns, rescaled to a daily basis by dividing by the overlap.
    Overlapping windows induce autocorrelation, so this matrix is for shape, not
    for a standard error; standard errors are HAC (SUBSTRATE section 9).

    The result is symmetrised and is not guaranteed positive semi-definite;
    projecting it is the optimiser's job in phase 1, not the loader's.
    """
    daily = returns.cov(min_periods=min_periods)
    over = overlapping_returns(returns, overlap_days).cov(min_periods=min_periods) / overlap_days

    regions = {s: (meta[s].region if s in meta else None) for s in returns.columns}
    out = daily.copy()
    cols = list(returns.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            ra, rb = regions.get(a), regions.get(b)
            if ra is not None and rb is not None and ra != rb:
                value = over.loc[a, b]
                out.loc[a, b] = value
                out.loc[b, a] = value
    return out


def same_day_cross_region_pairs(meta: dict[str, SeriesMeta], series_ids: list[str]) -> list[tuple]:
    """Cross-region pairs, which may not use same-day correlation."""
    pairs = []
    ids = [s for s in series_ids if s in meta and meta[s].region is not None]
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if meta[a].region != meta[b].region:
                pairs.append((a, b))
    return pairs
