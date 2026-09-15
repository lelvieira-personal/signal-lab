"""
Loaders. One interface (PanelLoader), several backends.

Phase 2 ships the Bloomberg backend alongside the synthetic one. FRED and JPMaQS
are still stubs that raise, so the harness stays wired against the real names and
an unbuilt backend fails with a clear "lands in phase N" rather than an import
error or, worse, a silently empty panel that would be reported as a coverage
veto failure.
"""

from signal_lab.loaders.base import (
    AnalyticsPanel,
    PanelLoader,
    ReturnPanel,
    SeriesMeta,
    SpliceRecord,
    VintagePanel,
)
from signal_lab.loaders.holdout import HoldoutViolation, enforce_holdout, holdout_start
from signal_lab.loaders.invariants import InvariantViolation, SpliceRefused
from signal_lab.loaders.synthetic import SyntheticLoader, plant

__all__ = [
    "AnalyticsPanel",
    "HoldoutViolation",
    "InvariantViolation",
    "PanelLoader",
    "ReturnPanel",
    "SeriesMeta",
    "SpliceRecord",
    "SpliceRefused",
    "SyntheticLoader",
    "VintagePanel",
    "enforce_holdout",
    "get_loader",
    "holdout_start",
    "plant",
]


def get_loader(source: str = "synthetic", **kwargs) -> PanelLoader:
    """Backend by name. Unknown names fail loudly rather than defaulting."""
    if source == "synthetic":
        return SyntheticLoader(**kwargs)
    if source == "bloomberg":
        from signal_lab.loaders.bloomberg import BloombergLoader

        return BloombergLoader(**kwargs)
    if source == "fred":
        from signal_lab.loaders.fred import FredLoader

        return FredLoader(**kwargs)
    if source == "jpmaqs":
        from signal_lab.loaders.jpmaqs import JPMaQSLoader

        return JPMaQSLoader(**kwargs)
    raise ValueError(f"unknown loader source {source!r}")
