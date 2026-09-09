"""
The holdout lock. SUBSTRATE sections 2 and 3.

Marked `holdout` so `make check` can run these explicitly and by name, rather
than trusting that they were somewhere in the suite.
"""

from __future__ import annotations

import pandas as pd
import pytest

from signal_lab.loaders.holdout import (
    HoldoutViolation,
    clip_to_development,
    enforce_holdout,
    holdout_start,
)

pytestmark = pytest.mark.holdout


def test_holdout_start_is_2020(params):
    assert holdout_start(params) == pd.Timestamp("2020-01-01")


def test_raises_on_a_single_holdout_date(params):
    with pytest.raises(HoldoutViolation, match="HOLDOUT_START"):
        enforce_holdout([pd.Timestamp("2020-01-02")], params)


def test_raises_on_a_frame_whose_index_reaches_the_holdout(params):
    frame = pd.DataFrame({"x": [1.0, 2.0]}, index=pd.to_datetime(["2019-12-27", "2020-01-02"]))
    with pytest.raises(HoldoutViolation):
        enforce_holdout(frame, params)


def test_boundary_the_day_before_passes_and_the_day_itself_raises(params):
    enforce_holdout([pd.Timestamp("2019-12-31")], params)  # must not raise
    with pytest.raises(HoldoutViolation):
        enforce_holdout([pd.Timestamp("2020-01-01")], params)


def test_empty_input_passes(params):
    enforce_holdout([], params)
    enforce_holdout(pd.DatetimeIndex([]), params)


def test_series_of_dates_is_checked(params):
    s = pd.Series(pd.to_datetime(["2018-06-01", "2021-06-01"]))
    with pytest.raises(HoldoutViolation):
        enforce_holdout(s, params)


def test_there_is_no_bypass_argument():
    """
    SUBSTRATE section 2: 'The loader refuses these dates; do not work around it.'

    A keyword like force= or allow_holdout= would be exactly that workaround, so
    its absence is asserted rather than left to reviewer vigilance.
    """
    import inspect

    from signal_lab.loaders import holdout as module

    forbidden = {"force", "bypass", "allow_holdout", "unlock", "override", "unsafe"}
    for name, fn in vars(module).items():
        if not callable(fn) or not hasattr(fn, "__code__"):
            continue
        args = set(inspect.signature(fn).parameters)
        assert not (args & forbidden), f"{name} exposes a holdout bypass: {args & forbidden}"


def test_synthetic_panel_never_reaches_the_holdout(panel, params):
    assert panel.returns.index.max() < holdout_start(params)
    enforce_holdout(panel.returns, params)


def test_macro_panel_never_reaches_the_holdout(macro, params):
    enforce_holdout(macro.frame["knowledge_date"], params)
    enforce_holdout(macro.frame["real_date"], params)


def test_unlocking_requires_a_named_owner_and_a_date(params, tmp_path):
    """An unlock that does not say who and when is not an unlock."""
    import shutil
    from pathlib import Path

    from signal_lab.params import PARAM_FILES, load_params

    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    data = tmp_path / "data.yaml"
    data.write_text(data.read_text().replace("locked: true", "locked: false"))
    loosened = load_params(tmp_path)
    with pytest.raises(HoldoutViolation, match="unlocked_by"):
        enforce_holdout([pd.Timestamp("2021-01-04")], loosened)


def test_clip_to_development_removes_rather_than_serves(panel, params):
    clipped = clip_to_development(panel.returns, params)
    assert clipped.index.min() >= pd.Timestamp(params.require("data.windows.dev_start"))
    assert clipped.index.max() <= pd.Timestamp(params.require("data.windows.dev_end"))
