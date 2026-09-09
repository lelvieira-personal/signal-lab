"""
FRED backend. Phase 2 (SUBSTRATE section 16). Not implemented.

Two rules already fixed and encoded in params/data.yaml, so phase 2 inherits
them rather than rediscovering them:

  * FRED's ICE BofA spread series start 2023-09 and are not used. Spreads come
    from Bloomberg (SUBSTRATE section 5.4).
  * FRED is not point-in-time. Its series are revised in place, so anything
    loaded from here is knowable only at its release, and the loader must
    construct knowledge dates rather than assume real_date == knowledge_date.

The API key comes from the FRED_API_KEY environment variable. No key is ever
written to params/ or committed.
"""

from __future__ import annotations

import os

from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel, VintagePanel
from signal_lab.loaders.bloomberg import LoaderNotImplemented
from signal_lab.params import Params, get_params


class FredLoader:
    source = "fred"
    phase = 2

    def __init__(self, params: Params | None = None):
        self.params = params or get_params()

    def api_key(self) -> str:
        key = os.environ.get("FRED_API_KEY")
        if not key:
            raise RuntimeError(
                "FRED_API_KEY is not set. Secrets come from environment variables "
                "only; nothing key-shaped is committed."
            )
        return key

    def excluded_prefixes(self) -> list[str]:
        return list(self.params.get("data.fred.exclude_series_prefixes", []))

    def load_returns(self, snapshot_id: str) -> ReturnPanel:
        raise LoaderNotImplemented("FRED provides levels and yields, not index total returns")

    def load_analytics(self, snapshot_id: str) -> AnalyticsPanel:
        raise LoaderNotImplemented("FRED analytics loader lands in phase 2")

    def load_macro(self, snapshot_id: str) -> VintagePanel:
        raise LoaderNotImplemented("FRED vintage loader lands in phase 2")
