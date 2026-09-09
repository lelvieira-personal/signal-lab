"""params/ is the single source of every threshold, and it is hashed."""

from __future__ import annotations

import re

import pytest

from signal_lab.params import (
    PARAM_FILES,
    ParamNotConfigured,
    ParamsError,
    hash_params_dir,
    load_params,
)


def test_all_param_files_present_and_versions_agree(params):
    assert params.params_version
    assert len(params.params_hash) == 64


def test_hash_is_content_addressed_and_changes_with_content(tmp_path, params):
    import shutil
    from pathlib import Path

    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    assert hash_params_dir(tmp_path) == params.params_hash

    target = tmp_path / "vetoes.yaml"
    target.write_text(target.read_text() + "\n# a comment changes the bytes\n")
    assert hash_params_dir(tmp_path) != params.params_hash


def test_missing_param_file_is_an_error(tmp_path, params):
    import shutil
    from pathlib import Path

    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    (tmp_path / "costs.yaml").unlink()
    with pytest.raises(ParamsError):
        load_params(tmp_path)


def test_version_disagreement_is_refused(tmp_path, params):
    import shutil
    from pathlib import Path

    src = Path(params.params_dir)
    for name in PARAM_FILES:
        shutil.copy(src / name, tmp_path / name)
    target = tmp_path / "costs.yaml"
    # Version-agnostic: rewrite whatever version is there, so this test does not
    # need editing every time params_version is bumped.
    target.write_text(
        re.sub(r'params_version: "[^"]+"', 'params_version: "9.9.9"', target.read_text(), count=1)
    )
    with pytest.raises(ParamsError, match="disagrees"):
        load_params(tmp_path)


def test_require_refuses_a_null_threshold(params):
    """
    SUBSTRATE forbids inventing thresholds; unset means refuse, not default.

    Every ceiling is now set (decisions/0007), so this is asserted against
    parameters the owner deliberately left null: the conviction-scaled TE
    penalty coefficients, whose functional form is settled (decisions/0019) but
    whose endpoints cannot sensibly be chosen before there is a candidate model.
    """
    for endpoint in ("coefficient_low_conviction", "coefficient_high_conviction"):
        path = f"constraints.tracking_error.penalty.{endpoint}"
        assert params.get(path) is None
        with pytest.raises(ParamNotConfigured):
            params.require(path)


def test_unknown_path_raises_but_default_is_honoured(params):
    with pytest.raises(ParamsError):
        params.get("vetoes.no_such_veto.threshold")
    assert params.get("vetoes.no_such_veto.threshold", 1.23) == 1.23


def test_every_substrate_threshold_is_in_params(params):
    """The section 10 table, read back out of params rather than out of code."""
    assert params.require("vetoes.turnover.max_annualised") == 1.50
    assert params.require("vetoes.cash.max_weight") == 0.20
    assert params.require("vetoes.tracking_error.max_trailing_3y") == 0.060
    assert params.require("vetoes.positions.max_nonzero") == 30
    assert params.require("vetoes.coverage.min_universe_fraction") == 0.80
    assert params.require("vetoes.coverage.min_date_fraction") == 0.90
    assert params.require("vetoes.seed_stability.max_ir_range") == 0.15
    assert params.require("vetoes.active_drawdown.te_multiple") == 3.0
    assert params.require("vetoes.tracking_error.statistic") == "p95"
    assert params.require("vetoes.multiple_testing.fwer_alpha") == 0.05
    assert params.require("data.windows.holdout_start") == "2020-01-01"
    assert params.require("costs.buckets.low.half_spread_bps") == 5
    assert params.require("costs.buckets.high.annual_fee_tracking_bps") == 35
