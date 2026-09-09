"""
Bloomberg backend. Phase 2 (SUBSTRATE section 16). Not implemented.

The shape is fixed here so phase 2 is a filling-in rather than a design: the
workbook layout is described in data/universe/raw_manifest.csv, the invariants
it must satisfy are in loaders/invariants.py, and the panel types it must return
are in loaders/base.py.

Deliberately raises rather than returning an empty panel. An empty panel would
propagate as "no coverage" and be reported as a coverage veto failure, which
would be a wrong diagnosis of a missing implementation.
"""

from __future__ import annotations

from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel, VintagePanel
from signal_lab.params import Params, get_params


class LoaderNotImplemented(NotImplementedError):
    """A real-data backend that phase 0 does not ship."""


class BloombergLoader:
    source = "bloomberg"
    phase = 2

    # What phase 2 must build, kept next to the stub so it is not re-derived.
    TODO = (
        "read the sheets in data/universe/raw_manifest.csv (TR Levels, TR Levels "
        "Hedged, TR Levels Candidates, TR Benchmarks, TR Analytics); apply "
        "invariants 1-7; assign tiers from bbg_index_coverage.csv; carry the "
        "hedged ids from params/data.yaml; log every splice",
    )

    def __init__(self, params: Params | None = None):
        self.params = params or get_params()

    def load_returns(self, snapshot_id: str) -> ReturnPanel:
        raise LoaderNotImplemented("Bloomberg returns loader lands in phase 2")

    def load_analytics(self, snapshot_id: str) -> AnalyticsPanel:
        raise LoaderNotImplemented("Bloomberg analytics loader lands in phase 2")

    def load_macro(self, snapshot_id: str) -> VintagePanel:
        raise LoaderNotImplemented("Bloomberg is not a macro vintage source; see jpmaqs")
