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
