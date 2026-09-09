"""
Panel types and the loader interface.

One interface, three panels, several backends. A backend is chosen by snapshot
id; the harness never knows whether it is holding a synthetic panel or a
Bloomberg one, which is the point: phase 1 validates the engine against planted
synthetic properties using exactly the code path phase 2 will use for real data.

Every panel carries per-series metadata (true daily start, tier, hedge flag,
gross/net flag, splice record) because the loader invariants in SUBSTRATE
section 5.1 and the `frequency` and `lookahead` vetoes cannot be evaluated
without it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal, Protocol

import pandas as pd

Tier = Literal["backbone", "second", "tradable-only"]


@dataclass(frozen=True)
class SpliceRecord:
    """
    A logged substitution. SUBSTRATE section 5.1.5.

    Splices are applied in the loader and recorded, never done silently and
    never used to join a month-end history onto a daily one.
    """

    target: str
    source: str
    reason: str
    splice_date: date | None = None
    n_observations_taken: int = 0

    def as_row(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "source": self.source,
            "reason": self.reason,
            "splice_date": self.splice_date,
            "n_observations_taken": self.n_observations_taken,
        }


@dataclass(frozen=True)
class SeriesMeta:
    """Per-series metadata. Immutable: the loader assigns it, agents read it."""

    series_id: str
    true_daily_start: pd.Timestamp
    tier: Tier
    hedged: bool = False
    gross: bool = True  # False = net of withholding tax (NDDU / M1 MSCI series)
    section: str = "unclassified"
    cost_bucket: str = "high"  # conservative default, params/costs.yaml
    month_end_only_before: pd.Timestamp | None = None
    splice: SpliceRecord | None = None
    region: str | None = None
    currency: str = "USD"

    def contributes_from(self) -> pd.Timestamp:
        """
        The first date this series may contribute a daily return.

        This is the `frequency` veto's reference point: a return dated before it
        would have been built from month-end observations spliced into a daily
        panel, which SUBSTRATE section 2 forbids.
        """
        return self.true_daily_start


@dataclass
class ReturnPanel:
    """Daily total-return levels and the returns derived from them."""

    levels: pd.DataFrame  # dates x series_id, NaN where not observed
    returns: pd.DataFrame  # dates x series_id, NaN where not computable
    meta: dict[str, SeriesMeta]
    splices: list[SpliceRecord] = field(default_factory=list)
    snapshot_id: str = "unknown"
    source: str = "unknown"

    @property
    def series_ids(self) -> list[str]:
        return list(self.returns.columns)

    def hedged_ids(self) -> list[str]:
        return [s for s, m in self.meta.items() if m.hedged]

    def unhedged_ids(self) -> list[str]:
        return [s for s, m in self.meta.items() if not m.hedged]

    def by_tier(self, tier: Tier) -> list[str]:
        return [s for s, m in self.meta.items() if m.tier == tier]

    def estimation_universe(self) -> list[str]:
        """
        Series a signal may be estimated on. SUBSTRATE section 5.2:
        tradable-only series are never used to estimate a signal.
        """
        return [s for s, m in self.meta.items() if m.tier in ("backbone", "second")]

    def daily_starts(self) -> dict[str, pd.Timestamp]:
        return {s: m.true_daily_start for s, m in self.meta.items()}

    def meta_frame(self) -> pd.DataFrame:
        rows = []
        for s, m in self.meta.items():
            rows.append(
                {
                    "series_id": s,
                    "true_daily_start": m.true_daily_start,
                    "tier": m.tier,
                    "hedged": m.hedged,
                    "gross": m.gross,
                    "section": m.section,
                    "cost_bucket": m.cost_bucket,
                    "month_end_only_before": m.month_end_only_before,
                    "region": m.region,
                    "currency": m.currency,
                    "spliced_from": m.splice.source if m.splice else None,
                }
            )
        return pd.DataFrame(rows).set_index("series_id").sort_index()


@dataclass
class AnalyticsPanel:
    """
    Index characteristics: OAS, yield-to-worst, effective duration.

    One frame per field, dates x series_id. Shares the ReturnPanel's metadata
    conventions so the frequency veto applies to analytics too.
    """

    fields: dict[str, pd.DataFrame]
    meta: dict[str, SeriesMeta]
    snapshot_id: str = "unknown"
    source: str = "unknown"

    @property
    def field_names(self) -> list[str]:
        return sorted(self.fields)

    def field(self, name: str) -> pd.DataFrame:
        if name not in self.fields:
            raise KeyError(f"no analytics field {name!r}; have {self.field_names}")
        return self.fields[name]


@dataclass
class VintagePanel:
    """
    Bitemporal macro data. SUBSTRATE section 5.6.

    Long format, one row per (series_id, period_end, knowledge_date).
    `period_end` is the last date of the period the number describes;
    `knowledge_date` is when it could first have been known. A revision is a new
    row with the same period_end and a later knowledge_date, never an overwrite.

    NAMING, DELIBERATE: these fields were called `real_date` and
    `knowledge_date` until the JPMaQS access details arrived. JPMaQS also has a
    column called `real_date`, and it means the OPPOSITE end of the pair -- "the
    date of the information state as observed by the markets", i.e. what this
    class calls `knowledge_date`. Two columns with the same name and inverted
    meanings, joined by a loader, is a lookahead bug that no test would catch
    because the panel would look perfectly well-formed. The field is therefore
    `period_end`, which is also what JPMaQS lets you recover:

        period_end     = jpmaqs.real_date - jpmaqs.eop_lag days
        knowledge_date = jpmaqs.real_date

    See decisions/0014.

    `as_of` is the only sanctioned way to read it. Reading `frame` directly and
    filtering by period_end is exactly the lookahead the veto exists to catch.
    """

    frame: pd.DataFrame  # series_id, period_end, knowledge_date, value, grading, eop_lag
    meta: dict[str, SeriesMeta]
    snapshot_id: str = "unknown"
    source: str = "unknown"

    REQUIRED_COLUMNS = ("series_id", "period_end", "knowledge_date", "value")

    def __post_init__(self) -> None:
        missing = [c for c in self.REQUIRED_COLUMNS if c not in self.frame.columns]
        if missing:
            raise ValueError(f"VintagePanel is missing columns {missing}")
        bad = self.frame["knowledge_date"] < self.frame["period_end"]
        if bool(bad.any()):
            raise ValueError(
                f"{int(bad.sum())} observation(s) have knowledge_date before "
                f"period_end, which would be knowing a number before the period it "
                f"describes has ended"
            )

    def as_of(self, knowledge_date, series_ids: list[str] | None = None) -> pd.DataFrame:
        """
        What was knowable at `knowledge_date`, wide: period_end x series_id.

        For each series and period_end, the latest vintage published on or before
        knowledge_date. Rows whose first vintage came later are absent, not
        filled: a number nobody had is not zero and is not the previous number.
        """
        kd = pd.Timestamp(knowledge_date)
        sub = self.frame[self.frame["knowledge_date"] <= kd]
        if series_ids is not None:
            sub = sub[sub["series_id"].isin(series_ids)]
        if sub.empty:
            return pd.DataFrame(index=pd.DatetimeIndex([], name="period_end"))
        sub = sub.sort_values(["series_id", "period_end", "knowledge_date"])
        latest = sub.groupby(["series_id", "period_end"], as_index=False).last()
        wide = latest.pivot(index="period_end", columns="series_id", values="value")
        wide.index = pd.DatetimeIndex(wide.index, name="period_end")
        wide.columns.name = None
        return wide.sort_index()

    def latest_value_as_of(self, knowledge_date, series_id: str) -> float | None:
        """The most recent observation of one series knowable at that date."""
        wide = self.as_of(knowledge_date, [series_id])
        if wide.empty or series_id not in wide.columns:
            return None
        col = wide[series_id].dropna()
        return None if col.empty else float(col.iloc[-1])

    def usage_log(self, knowledge_date, series_ids: list[str] | None = None) -> pd.DataFrame:
        """
        The observations `as_of` would return, with the date they were used on.

        This is what the `lookahead` veto reads. Producing it here rather than
        asking each signal to report its own usage means a signal cannot fail to
        declare a peek.
        """
        kd = pd.Timestamp(knowledge_date)
        sub = self.frame[self.frame["knowledge_date"] <= kd]
        if series_ids is not None:
            sub = sub[sub["series_id"].isin(series_ids)]
        out = sub[["series_id", "period_end", "knowledge_date"]].copy()
        out["used_on_date"] = kd
        return out.reset_index(drop=True)

    def grades(self) -> pd.Series:
        if "grading" not in self.frame.columns:
            return pd.Series(dtype="float64")
        return self.frame["grading"]


class PanelLoader(Protocol):
    """
    The single loader interface. Bloomberg, FRED, JPMaQS and the synthetic
    backend all satisfy it, so the harness is written once.
    """

    def load_returns(self, snapshot_id: str) -> ReturnPanel: ...

    def load_analytics(self, snapshot_id: str) -> AnalyticsPanel: ...

    def load_macro(self, snapshot_id: str) -> VintagePanel: ...
