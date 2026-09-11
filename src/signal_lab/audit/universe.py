"""
Assemble the audit universe from a backend.

Two sources, one shape. `bloomberg_universe` is the real one: the investable
universe from `data/universe/investable_universe.csv`, the benchmark legs from
`BloombergLoader.load_benchmark`, and the development window.
`synthetic_universe` is the validation one, where the planted IC is known
exactly and the audit must recover it before anyone reads a real number.

One deliberate difference between them, and it is not cosmetic.
`loaders.synthetic.make_benchmark` builds a benchmark that is NOT a combination
of panel members -- on purpose, so a planted strategy cannot beat it by holding
it. That is right for phase 1's accounting test and wrong for the audit, which
asks what tracking error a book can achieve against the benchmark: against an
unspannable benchmark the answer is "none of it", the budget is infeasible at
every rebalance, and the ladder measures the synthetic generator rather than
the pipeline. So the synthetic audit builds its legs as equal-weighted averages
of the panel's equity and fixed-income sections, which is spannable by
construction. The real legs (`NDUEACWF`, `LEGATRUU`) are near-spanned by a
universe of global equity and aggregate bond indices, and
`ShrunkCovariance.legs` reports the replication R^2 at every rebalance, so if
that assumption fails on real data it is visible rather than assumed.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from signal_lab.audit.ladder import AuditUniverse, build_universe
from signal_lab.loaders.base import ReturnPanel
from signal_lab.params import Params, get_params

REPO_ROOT = Path(__file__).resolve().parents[3]
UNIVERSE_CSV = REPO_ROOT / "data" / "universe" / "investable_universe.csv"

# Sections of the synthetic panel, by leg. `loaders.synthetic.SECTIONS` numbers
# them; 6-11 are equity, 2-5 fixed income, 1 cash, 15 real assets.
SYNTHETIC_EQUITY_SECTIONS = ("6.", "7.", "8.", "9.", "10", "11")
SYNTHETIC_BOND_SECTIONS = ("2.", "3.", "4.", "5.")


def _development_window(panel: ReturnPanel, params: Params) -> ReturnPanel:
    """Clip a panel to `DEV_START`..`DEV_END`. The holdout is already refused
    by the loader; this is the other end."""
    start = pd.Timestamp(params.require("data.windows.dev_start"))
    end = pd.Timestamp(params.require("data.windows.dev_end"))
    mask = (panel.returns.index >= start) & (panel.returns.index <= end)
    index = panel.returns.index[mask]
    return ReturnPanel(
        levels=panel.levels.reindex(index),
        returns=panel.returns.reindex(index),
        meta=panel.meta,
        splices=panel.splices,
        snapshot_id=panel.snapshot_id,
        source=panel.source,
    )


def read_investable_flags(path: Path | str | None = None) -> dict[str, bool]:
    """`ticker -> investable` from the universe table. Missing file: empty map."""
    path = Path(path or UNIVERSE_CSV)
    if not path.exists():
        return {}
    flags: dict[str, bool] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ticker = row.get("ticker")
            if ticker:
                flags[ticker] = str(row.get("investable", "True")).strip().lower() == "true"
    return flags


def synthetic_universe(
    params: Params | None = None,
    seed: int | None = None,
    start: str | pd.Timestamp | None = None,
) -> AuditUniverse:
    """The validation universe: a synthetic panel with spannable benchmark legs."""
    from signal_lab.loaders.synthetic import SyntheticLoader

    params = params or get_params()
    panel = _development_window(SyntheticLoader(params, seed=seed).load_returns(), params)
    if start is not None:
        index = panel.returns.index[panel.returns.index >= pd.Timestamp(start)]
        panel = ReturnPanel(
            levels=panel.levels.reindex(index),
            returns=panel.returns.reindex(index),
            meta=panel.meta,
            splices=panel.splices,
            snapshot_id=panel.snapshot_id,
            source=panel.source,
        )

    def members(prefixes):
        return [
            s
            for s in panel.returns.columns
            if not panel.meta[s].hedged and str(panel.meta[s].section)[:2] in prefixes
        ]

    equity, bonds = members(SYNTHETIC_EQUITY_SECTIONS), members(SYNTHETIC_BOND_SECTIONS)
    if not equity or not bonds:
        raise ValueError("the synthetic panel has no equity or no fixed-income section")
    legs = pd.DataFrame(
        {
            "SYN_EQ": panel.returns[equity].mean(axis=1),
            "SYN_BD": panel.returns[bonds].mean(axis=1),
        }
    )
    weights = pd.Series(
        dict(
            zip(
                ("SYN_EQ", "SYN_BD"),
                params.get("constraints.benchmark.weights", [0.5, 0.5]),
                strict=True,
            )
        )
    )
    return build_universe(panel, legs, weights, params)


def bloomberg_universe(params: Params | None = None) -> AuditUniverse:
    """The real universe: investable Bloomberg series against the 50/50 legs."""
    from signal_lab.loaders.bloomberg import BloombergLoader

    params = params or get_params()
    loader = BloombergLoader(params)
    panel = _development_window(loader.load_returns(), params)
    bench = _development_window(loader.load_benchmark(), params)

    equity = str(params.require("constraints.benchmark.equity"))
    bond = str(params.require("constraints.benchmark.bond"))
    missing = [t for t in (equity, bond) if t not in bench.returns.columns]
    if missing:
        raise ValueError(f"the benchmark panel has no {missing}; check the Bloomberg pull")
    legs = bench.returns[[equity, bond]]
    weights = pd.Series(
        dict(
            zip(
                (equity, bond), params.get("constraints.benchmark.weights", [0.5, 0.5]), strict=True
            )
        )
    )
    return build_universe(panel, legs, weights, params, investable=read_investable_flags())


def get_universe(
    source: str = "synthetic", params: Params | None = None, **kwargs
) -> AuditUniverse:
    if source == "synthetic":
        return synthetic_universe(params, **kwargs)
    if source == "bloomberg":
        return bloomberg_universe(params, **kwargs)
    raise ValueError(f"unknown audit source {source!r}")
