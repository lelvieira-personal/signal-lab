"""Shared fixtures. The synthetic panel is expensive to build, so it is session-scoped."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "src"), str(REPO_ROOT)]


@pytest.fixture(scope="session")
def params():
    from signal_lab.params import get_params

    return get_params()


@pytest.fixture(scope="session")
def panel(params):
    from signal_lab.loaders.synthetic import SyntheticLoader

    return SyntheticLoader(params).load_returns()


@pytest.fixture(scope="session")
def macro(params):
    from signal_lab.loaders.synthetic import SyntheticLoader

    return SyntheticLoader(params).load_macro()


@pytest.fixture(scope="session")
def analytics(params):
    from signal_lab.loaders.synthetic import SyntheticLoader

    return SyntheticLoader(params).load_analytics()


@pytest.fixture
def store(tmp_path):
    from signal_lab.results.store import ResultsStore

    return ResultsStore(tmp_path / "runs.db", tmp_path / "artifacts")


@pytest.fixture(scope="session")
def planted(panel):
    """
    A planted weight path plus its exact benchmark and ground truth.

    Session-scoped because building it runs the engine once over the full
    synthetic panel; five tests sharing one build is the difference between a
    fast suite and a slow one.
    """
    from signal_lab.loaders.synthetic import plant_weight_path

    rule, benchmark, truth = plant_weight_path(panel, target_ir=0.5, target_te=0.04)
    return rule, benchmark, truth


@pytest.fixture(scope="session")
def planted_path(panel, planted):
    import pandas as pd

    from signal_lab.harness.engine import constant_exposures, run_walk_forward

    rule, benchmark, _ = planted
    ids = rule(panel.returns.index[0], panel).index
    exposures = constant_exposures(pd.DataFrame(0.0, index=ids, columns=["f0"]))
    return run_walk_forward(panel, rule, benchmark, exposures)
