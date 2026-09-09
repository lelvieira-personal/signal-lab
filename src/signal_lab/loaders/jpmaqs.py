"""
JPMaQS / Macrosynergy backend. Phase 3 (SUBSTRATE sections 5.6 and 16).
Not implemented.

SUBSTRATE section 5.6 is explicit that until JPMaQS lands, no signal search
runs, and that price-only families are not tested in isolation first. This stub
is therefore also the gate: `search_is_open()` reads that rule from params so a
cycle cannot quietly open the search while the macro block is missing.
"""

from __future__ import annotations

from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel, VintagePanel
from signal_lab.loaders.bloomberg import LoaderNotImplemented
from signal_lab.params import Params, get_params


class JPMaQSLoader:
    source = "jpmaqs"
    phase = 3

    def __init__(self, params: Params | None = None):
        self.params = params or get_params()

    def load_returns(self, snapshot_id: str) -> ReturnPanel:
        raise LoaderNotImplemented("JPMaQS is a macro source, not a return source")

    def load_analytics(self, snapshot_id: str) -> AnalyticsPanel:
        raise LoaderNotImplemented("JPMaQS is a macro source, not an analytics source")

    def load_macro(self, snapshot_id: str) -> VintagePanel:
        raise LoaderNotImplemented("JPMaQS loader lands in phase 3")


def search_is_open(params: Params | None = None) -> tuple[bool, str]:
    """
    Whether the signal search may run at all.

    SUBSTRATE section 5.6: the search opens only when the full signal set is in.
    A leaderboard built on price signals alone would tacitly decide what works
    before the macro block is tested, so this is a gate rather than a warning.
    """
    params = params or get_params()
    status = params.get("data.jpmaqs.status", "pending")
    gated = bool(params.get("data.jpmaqs.search_opens_only_when_loaded", True))
    if gated and status != "loaded":
        return False, (
            f"JPMaQS status is {status!r}. SUBSTRATE section 5.6: no signal search "
            f"runs until the macro block is in."
        )
    return True, "macro block present"
