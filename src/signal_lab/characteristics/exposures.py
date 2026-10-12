"""
The exposure map: a characteristics store read as of a date (decisions/0050, 0055; HANDOFF tasks 54, 55).

`resolve_exposures` returns an `ExposureMap` built from the store `params/` names
(`data.characteristics.store_id` and `directory_hash`), and from no other. A run on date `d` reads
the store's latest week on or before `d`, and only if that week is within six days of `d`; nothing
older is carried. The map is also the engine's `ExposureRule`: calling it with a date gives the
six factors and the four axes of each instrument that has a row that week, with no missing value.

Axes (decisions/0050 and its addendum of 2026-10-10):

    duration       oad that week for Treasuries, Long Treasuries, IG Corporates and TIPS when it
                   is not missing (provenance `measured`); minus the real-yield loading otherwise
                   (`estimated`)
    real_nominal   minus the inflation loading
    credit         minus the credit loading
    cash           1 for the Cash reporting class, 0 otherwise

Labels (decisions/0054, 0057; HANDOFF task 55) come from `data/universe/label_map.csv`, the owner's
map, not from the store. They are carried on `at(date)` as strings and no axis reads a bond label.
`region` is the one label axis built: `axis("region", date)` is a frame, one 0/1 column per region
a view can name, where the other axes are series, because a region view is one view per region.
Sector and style raise `LabelMapMissing` (decisions/0054 item 8).

No row, no holding (decisions/0055): `requires_row` tells the engine to refuse a weight on an
instrument that has no row on a rebalance date. The eight tradable-only instruments never have
one.

Every `at(date)` also records, per instrument, which week's loadings were used on which date and
the date those loadings were fitted through (the store's `last_data_date`). `usage()` returns that
log as the `parameter_usage` table that `veto_lookahead` reads.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from signal_lab.characteristics import store as store_mod
from signal_lab.harness.experiment import ExposureMatrixMissing
from signal_lab.harness.hypotheses import TARGET_AXES
from signal_lab.params import Params, get_params

MEASURED_DURATION_CLASSES = ("Treasuries", "Long Treasuries", "IG Corporates", "TIPS")
LABEL_MAP_PATH = Path(__file__).resolve().parents[3] / "data" / "universe" / "label_map.csv"
UNBUILT_LABEL_AXES = ("sector", "style")
LABEL_COLUMNS = (
    "region",
    "curve_currency",
    "rating_class",
    "market_label",
    "curve",
    "rating",
    "hy_bucket",
    "market",
)
# The regions a view can name (decisions/0054 item 9) and the seven a report shows, Global included.
VIEW_REGIONS = ("US", "Developed Europe", "Japan", "APAC ex-Japan", "Canada", "EM")
REPORT_REGIONS = {
    "US": "region_us",
    "Developed Europe": "region_dev_europe",
    "Japan": "region_japan",
    "APAC ex-Japan": "region_apac_ex_japan",
    "Canada": "region_canada",
    "EM": "region_em",
    "Global": "region_global",
}
REGION_COLUMNS = tuple(REPORT_REGIONS.values())
MAX_STALENESS = pd.Timedelta(days=6)
AXIS_COLUMNS = ("axis_duration", "axis_real_nominal", "axis_credit", "axis_cash")
USAGE_COLUMNS = ("instrument", "parameter", "store_week", "fitted_through", "used_on_date")

_AXIS_OF = {
    "duration": "axis_duration",
    "real_nominal": "axis_real_nominal",
    "credit": "axis_credit",
    "cash": "axis_cash",
}


class LabelMapMissing(ExposureMatrixMissing):
    """Sector and style have no label map (decisions/0054 item 8), or the region map is unusable."""


def load_label_map(path: Path | str | None = None) -> pd.DataFrame:
    """The label map indexed by ticker, every cell a string and a blank cell ''."""
    path = Path(path) if path is not None else LABEL_MAP_PATH
    if not path.exists():
        raise LabelMapMissing(f"no label map at {path} (decisions/0054)")
    return pd.read_csv(path, dtype=str, keep_default_na=False).set_index("ticker")


class ExposureMap:
    """A store's weeks as exposures. See the module docstring."""

    requires_row = True

    def __init__(self, loaded: store_mod.Store, label_map: Path | str | None = None):
        self.store = loaded
        self.factors: list[str] = list(loaded.manifest["factors"])
        f = loaded.frames
        load = f["loadings"].pivot_table(
            index=["date", "instrument"], columns="factor", values="loading"
        )[self.factors]
        se = f["loadings"].pivot_table(index=["date", "instrument"], columns="factor", values="se")[
            self.factors
        ]
        se.columns = [f"{c}_se" for c in self.factors]
        fit = f["fit"].set_index(["date", "instrument"])[["explained_share", "last_data_date"]]
        meas = f["measured"].set_index(["date", "instrument"])[["oad", "oas"]]
        klass = dict(zip(f["instruments"]["instrument"], f["instruments"]["class"], strict=True))

        wide = load.join(se).join(fit, how="left").join(meas, how="left")
        wide["reporting_class"] = [klass.get(i) for i in wide.index.get_level_values("instrument")]
        labels = load_label_map(label_map)
        # The store also lists the tradable-only instruments, with no row (decisions/0055); the
        # label map has a row for exactly the instruments that have one.
        held = set(wide.index.get_level_values("instrument"))
        labelled = set(labels.index)
        if held != labelled:
            raise LabelMapMissing(
                "the store and the label map name different instruments: "
                f"in the store only {sorted(held - labelled)}, "
                f"in the label map only {sorted(labelled - held)} (decisions/0054)"
            )
        self._labels = labels
        self._wide = wide.sort_index()
        self.weeks = pd.DatetimeIndex(sorted(self._wide.index.get_level_values("date").unique()))
        self._cache: dict[pd.Timestamp, pd.DataFrame] = {}
        self._usage: list[pd.DataFrame] = []

    # -- construction ---------------------------------------------------------------------

    @classmethod
    def from_params(
        cls,
        params: Params | None = None,
        root: Path | str | None = None,
        label_map: Path | str | None = None,
    ) -> ExposureMap:
        """The store `data.characteristics` names, refused if it is not that store."""
        params = params or get_params()
        store_id = params.get("data.characteristics.store_id", None)
        want = params.get("data.characteristics.directory_hash", None)
        if not store_id or not want:
            raise ExposureMatrixMissing(
                "params/ names no store for the characteristic map "
                "(data.characteristics.store_id and directory_hash; decisions/0055)"
            )
        root = Path(root) if root is not None else store_mod.STORE_ROOT
        try:
            loaded = store_mod.load_store(store_id, root)
        except FileNotFoundError as exc:
            raise ExposureMatrixMissing(
                f"no characteristic map: store {store_id!r} is not under {root}; "
                f"params/ names it (decisions/0055)"
            ) from exc
        have = loaded.manifest.get("directory_hash")
        if have != want:
            raise ExposureMatrixMissing(
                f"characteristic map {store_id!r} hashes to {str(have)[:16]}..., params/ names "
                f"{str(want)[:16]}...; a store of the same id with other contents is refused "
                f"(decisions/0055)"
            )
        return cls(loaded, label_map)

    # -- reading a date -------------------------------------------------------------------

    def store_week(self, date) -> pd.Timestamp:
        """The latest store week on or before `date`, within six days of it."""
        date = pd.Timestamp(date).normalize()
        pos = self.weeks.searchsorted(date, side="right") - 1
        span = f"{self.weeks[0].date()} to {self.weeks[-1].date()}"
        if pos < 0:
            raise ExposureMatrixMissing(
                f"no characteristic map week on or before {date.date()}; the store holds {span}"
            )
        week = self.weeks[pos]
        if date - week > MAX_STALENESS:
            raise ExposureMatrixMissing(
                f"the latest characteristic map week before {date.date()} is {week.date()}, "
                f"more than six days earlier; the store holds {span}. Nothing older is carried."
            )
        return week

    def _week_frame(self, week: pd.Timestamp) -> pd.DataFrame:
        if week not in self._cache:
            w = self._wide.xs(week, level="date").copy()
            klass = w["reporting_class"]
            measured = klass.isin(MEASURED_DURATION_CLASSES) & w["oad"].notna()
            w["axis_duration"] = (-w["real_yield"]).where(~measured, w["oad"])
            w["axis_duration_provenance"] = measured.map({True: "measured", False: "estimated"})
            w["axis_real_nominal"] = -w["inflation"]
            w["axis_credit"] = -w["credit"]
            w["axis_cash"] = (klass == "Cash").astype(float)
            labels = self._labels.reindex(w.index)[list(LABEL_COLUMNS)]
            for col in LABEL_COLUMNS:
                w[col] = labels[col].to_numpy()
            for region, col in REPORT_REGIONS.items():
                w[col] = (w["region"] == region).astype(float)
            view = self._labels.reindex(w.index)["region_view"].eq("yes")
            for region in VIEW_REGIONS:
                w[f"view_{region}"] = ((w["region"] == region) & view).astype(float)
            self._cache[week] = w
        return self._cache[week]

    def at(self, date) -> pd.DataFrame:
        """
        One row per instrument that has a row in the store week `date` reads: the six factors
        and their standard errors, `oad` and `oas` (missing where the store has none), the four
        axes, `axis_duration_provenance`, `explained_share`, `reporting_class`, the label
        columns (strings, blank where the map is blank) and the seven `region_*` reporting
        columns. Records the usage of its loadings.
        """
        date = pd.Timestamp(date).normalize()
        week = self.store_week(date)
        frame = self._week_frame(week)
        self._usage.append(
            pd.DataFrame(
                {
                    "instrument": frame.index.astype(str),
                    "parameter": "loadings",
                    "store_week": week,
                    "fitted_through": frame["last_data_date"].to_numpy(),
                    "used_on_date": date,
                }
            )
        )
        helpers = [f"view_{r}" for r in VIEW_REGIONS]
        return frame.drop(columns=["last_data_date", *helpers])

    def axis(self, name: str, date) -> pd.Series | pd.DataFrame:
        """
        One axis over the instruments that have a row. Every axis is a series except `region`,
        which is a frame with one 0/1 column per view region (US, Developed Europe, Japan, APAC
        ex-Japan, Canada, EM): a region view is one view per region, so it needs a column each.
        An instrument reads 1 only where the map's `region_view` is `yes`, which is equities
        only (decisions/0054 items 9 and 10); Global has no column and no view.
        """
        if name in UNBUILT_LABEL_AXES:
            raise LabelMapMissing(f"the {name} axis has no label map yet (decisions/0054 item 8)")
        if name not in TARGET_AXES:
            raise ValueError(f"unknown axis {name!r}; valid names are {TARGET_AXES}")
        if name == "region":
            week = self.store_week(pd.Timestamp(date).normalize())
            self.at(date)  # records the usage
            out = self._week_frame(week)[[f"view_{r}" for r in VIEW_REGIONS]]
            out.columns = list(VIEW_REGIONS)
            return out
        col = _AXIS_OF[name]
        return self.at(date)[col].rename(name)

    def __call__(self, date) -> pd.DataFrame:
        """
        The engine's ExposureRule: the six factors, the four axes and the seven region reporting
        columns, no missing value.
        """
        frame = self.at(date)
        cols = [*self.factors, *AXIS_COLUMNS, *REGION_COLUMNS]
        return frame[cols].dropna()

    # -- the usage log --------------------------------------------------------------------

    def usage(self) -> pd.DataFrame:
        """`parameter_usage`: what every `at(date)` read, without duplicates."""
        if not self._usage:
            return pd.DataFrame(columns=list(USAGE_COLUMNS))
        out = pd.concat(self._usage, ignore_index=True).drop_duplicates()
        return out[list(USAGE_COLUMNS)].reset_index(drop=True)
