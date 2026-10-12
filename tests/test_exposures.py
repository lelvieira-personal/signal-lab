"""
The exposure map (HANDOFF tasks 54 and 55, decisions/0050, 0054 and 0055), on a synthetic store
written with `write_store` in a temp folder and a synthetic label map. Nothing reads data/raw/,
data/snapshots/ or the real store. The real label map is tested in test_label_map.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from signal_lab.characteristics import exposures, store
from signal_lab.characteristics.exposures import ExposureMap, LabelMapMissing
from signal_lab.harness.engine import (
    NoExposureRow,
    constant_exposures,
    run_walk_forward,
)
from signal_lab.harness.experiment import ExposureMatrixMissing, resolve_exposures
from signal_lab.harness.hypotheses import TARGET_AXES
from signal_lab.loaders.base import ReturnPanel, SeriesMeta
from signal_lab.measurement.factors import FACTOR_NAMES

WEEKS = pd.date_range("2010-01-08", periods=6, freq="W-FRI")
# instrument -> reporting class
CLASSES = {
    "TSY": "Treasuries",
    "EQ": "US Equities",
    "CSH": "Cash",
    "IG": "IG Corporates",
    "HY": "HY Corporates",
}
STORE_ID = "synthetic-v1"

# The synthetic label map says what each synthetic instrument is, whatever the store's class says:
# TSY a US bond, EQ a US equity, CSH cash, IG a Global equity, HY a commodity.
LABEL_HEADER = (
    "ticker,asset_group,reporting_class,region,region_view,curve_currency,rating_class,"
    "market_label,curve,rating,hy_bucket,market"
)
LABEL_ROWS = {
    "TSY": "TSY,bond,Treasuries,US,no,USD,Government,DM,USD,Government,,DM",
    "EQ": "EQ,equity,US Equities,US,yes,,,,,,,",
    "CSH": "CSH,cash,Cash,US,no,USD,Government (bills),DM,USD,Government,,DM",
    "IG": "IG,equity,DM ex-US Equities,Global,no,,,,,,,",
    "HY": "HY,commodity,Commodities,Commodities,no,,,,,,,",
}


def write_label_map(path, rows=None):
    rows = LABEL_ROWS if rows is None else rows
    path.write_text("\n".join([LABEL_HEADER, *rows.values()]) + "\n", encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def synthetic_label_map(tmp_path_factory, monkeypatch):
    path = write_label_map(tmp_path_factory.mktemp("labels") / "label_map.csv")
    monkeypatch.setattr(exposures, "LABEL_MAP_PATH", path)
    return path


class FakeParams:
    """Only `.get`, which is all `ExposureMap.from_params` uses."""

    def __init__(self, store_id=STORE_ID, directory_hash=None):
        self.values = {
            "data.characteristics.store_id": store_id,
            "data.characteristics.directory_hash": directory_hash,
        }

    def get(self, dotted, default=None):
        return self.values.get(dotted, default)


def _frames(fitted_late=False):
    rows, fit, meas = [], [], []
    for w_i, week in enumerate(WEEKS):
        for i_i, inst in enumerate(CLASSES):
            for f_i, factor in enumerate(FACTOR_NAMES):
                rows.append(
                    {
                        "instrument": inst,
                        "date": week,
                        "factor": factor,
                        "loading": 0.1 * (f_i + 1) + 0.01 * i_i + 0.001 * w_i,
                        "se": 0.05,
                        "kind": "estimated",
                        "estimator": "huber_m",
                    }
                )
            fit.append(
                {
                    "instrument": inst,
                    "date": week,
                    "resid_var": 1.0,
                    "n_valid_weeks": 150,
                    "last_data_date": week + pd.Timedelta(days=7 if fitted_late else 0),
                    "explained_share": 0.5 + 0.01 * i_i,
                    "kind": "estimated",
                    "estimator": "huber_m",
                }
            )
    # TSY has a measured duration in weeks 0 and 1 only; EQ has one in every week (never read);
    # IG has one in week 0 only (an earlier week must not be carried).
    for w_i, week in enumerate(WEEKS):
        if w_i <= 1:
            meas.append({"instrument": "TSY", "date": week, "oad": 5.0 + w_i, "oas": np.nan})
        meas.append({"instrument": "EQ", "date": week, "oad": 9.0, "oas": np.nan})
        if w_i == 0:
            meas.append({"instrument": "IG", "date": week, "oad": 7.0, "oas": 1.0})
    measured = pd.DataFrame(meas)
    measured["kind"] = "measured"
    inst = pd.DataFrame(
        {
            "instrument": list(CLASSES),
            "class": list(CLASSES.values()),
            "estimated": True,
            "first_date": WEEKS[0],
            "last_date": WEEKS[-1],
            "n_rows": len(WEEKS),
            "explained_share_full": 0.5,
            "kind": "estimated",
            "estimator": "huber_m",
        }
    )
    return {
        "loadings": pd.DataFrame(rows),
        "fit": pd.DataFrame(fit),
        "measured": measured,
        "instruments": inst,
    }


def _write(tmp_path, name=STORE_ID, **kw):
    manifest = {
        "factors": list(FACTOR_NAMES),
        "first_date": str(WEEKS[0].date()),
        "last_date": str(WEEKS[-1].date()),
    }
    store.write_store(name, _frames(**kw), manifest, tmp_path)
    return store.load_store(name, tmp_path).manifest["directory_hash"]


@pytest.fixture
def emap(tmp_path):
    digest = _write(tmp_path)
    return ExposureMap.from_params(FakeParams(directory_hash=digest), tmp_path)


# --- which store ----------------------------------------------------------------------------


def test_the_store_params_names_is_the_one_read(tmp_path):
    digest = _write(tmp_path)
    _write(tmp_path, name="other-v1")
    got = resolve_exposures(None, FakeParams(directory_hash=digest), root=tmp_path)
    assert got.store.store_id == STORE_ID


def test_a_wrong_hash_is_refused(tmp_path):
    _write(tmp_path)
    with pytest.raises(ExposureMatrixMissing, match="characteristic map"):
        resolve_exposures(None, FakeParams(directory_hash="0" * 64), root=tmp_path)


def test_a_store_that_is_not_there_and_params_that_name_none_are_refused(tmp_path):
    with pytest.raises(ExposureMatrixMissing, match="characteristic map"):
        resolve_exposures(None, FakeParams(directory_hash="0" * 64), root=tmp_path)
    with pytest.raises(ExposureMatrixMissing, match="names no store"):
        resolve_exposures(None, FakeParams(store_id=None), root=tmp_path)


def test_the_real_params_name_a_store_and_a_missing_root_raises(params, tmp_path):
    with pytest.raises(ExposureMatrixMissing):
        resolve_exposures(None, params, root=tmp_path)


# --- which week -----------------------------------------------------------------------------


def test_a_friday_reads_its_own_week_and_the_tuesday_after_reads_the_friday_before(emap):
    friday = WEEKS[2]
    assert emap.store_week(friday) == friday
    assert emap.store_week(friday + pd.Timedelta(days=4)) == friday
    assert emap.store_week(friday + pd.Timedelta(days=6)) == friday


def test_a_date_seven_days_after_the_last_week_or_before_the_first_raises(emap):
    with pytest.raises(ExposureMatrixMissing, match="more than six days"):
        emap.at(WEEKS[-1] + pd.Timedelta(days=7))
    with pytest.raises(ExposureMatrixMissing, match="on or before"):
        emap.at(WEEKS[0] - pd.Timedelta(days=1))
    with pytest.raises(ExposureMatrixMissing, match="2010-01-08 to 2010-02-12"):
        emap.at(WEEKS[0] - pd.Timedelta(days=3))


# --- the axes -------------------------------------------------------------------------------


def test_duration_reads_oad_for_a_treasury_and_marks_it_measured(emap):
    frame = emap.at(WEEKS[0])
    assert frame.loc["TSY", "axis_duration"] == 5.0
    assert frame.loc["TSY", "axis_duration_provenance"] == "measured"
    assert frame.loc["TSY", "oad"] == 5.0
    assert frame.loc["IG", "axis_duration"] == 7.0 and frame.loc["IG", "oas"] == 1.0


def test_a_missing_oad_falls_back_to_minus_real_yield_and_is_marked_estimated(emap):
    frame = emap.at(WEEKS[2])  # TSY has no oad that week
    assert np.isnan(frame.loc["TSY", "oad"])
    assert frame.loc["TSY", "axis_duration"] == pytest.approx(-frame.loc["TSY", "real_yield"])
    assert frame.loc["TSY", "axis_duration_provenance"] == "estimated"


def test_an_equity_reads_minus_real_yield_even_when_an_oad_is_present(emap):
    frame = emap.at(WEEKS[0])
    assert frame.loc["EQ", "oad"] == 9.0
    assert frame.loc["EQ", "axis_duration"] == pytest.approx(-frame.loc["EQ", "real_yield"])
    assert frame.loc["EQ", "axis_duration_provenance"] == "estimated"


def test_oad_from_an_earlier_week_is_never_used(emap):
    # IG has an oad in week 0 only. Weeks 1 to 5 read the loading, and a Tuesday after week 0
    # reads week 0's own measured value, never a later week's.
    for week in WEEKS[1:]:
        frame = emap.at(week)
        assert np.isnan(frame.loc["IG", "oad"])
        assert frame.loc["IG", "axis_duration"] == pytest.approx(-frame.loc["IG", "real_yield"])
    assert emap.at(WEEKS[1] + pd.Timedelta(days=4)).loc["TSY", "axis_duration"] == 6.0


def test_real_nominal_credit_and_cash_axes_and_their_signs(emap):
    frame = emap.at(WEEKS[1])
    assert (frame["axis_real_nominal"] == -frame["inflation"]).all()
    assert (frame["axis_credit"] == -frame["credit"]).all()
    assert frame["axis_cash"].to_dict() == {"TSY": 0.0, "EQ": 0.0, "CSH": 1.0, "IG": 0.0, "HY": 0.0}
    assert (frame["axis_real_nominal"] < 0).all(), "a positive inflation loading reads negative"
    assert emap.axis("credit", WEEKS[1]).name == "credit"
    assert emap.axis("duration", WEEKS[0])["TSY"] == 5.0


def test_the_frame_has_the_factors_their_ses_the_measured_block_and_the_provenance(emap):
    frame = emap.at(WEEKS[0])
    for f in FACTOR_NAMES:
        assert f in frame.columns and f"{f}_se" in frame.columns
    for c in ("oad", "oas", "explained_share", "axis_duration_provenance", "reporting_class"):
        assert c in frame.columns
    assert set(frame.index) == set(CLASSES)


def test_sector_and_style_raise_naming_decisions_0054_and_anything_else_is_a_value_error(emap):
    for name in ("sector", "style"):
        assert name in TARGET_AXES
        with pytest.raises(LabelMapMissing, match="decisions/0054 item 8") as exc:
            emap.axis(name, WEEKS[0])
        assert isinstance(exc.value, ExposureMatrixMissing)
    with pytest.raises(ValueError, match="unknown axis"):
        emap.axis("momentum", WEEKS[0])


def test_the_rule_has_the_six_factors_four_axes_and_seven_regions_and_no_missing_value(emap):
    rule = emap(WEEKS[2])
    assert list(rule.columns) == [
        *FACTOR_NAMES,
        "axis_duration",
        "axis_real_nominal",
        "axis_credit",
        "axis_cash",
        "region_us",
        "region_dev_europe",
        "region_japan",
        "region_apac_ex_japan",
        "region_canada",
        "region_em",
        "region_global",
    ]
    assert not rule.isna().any().any()
    assert emap.requires_row is True


# --- the usage log --------------------------------------------------------------------------


def test_the_usage_log_has_one_row_per_instrument_and_date_fitted_through_the_week(emap):
    for week in WEEKS[:3]:
        emap.at(week)
        emap.at(week)  # a repeat adds nothing
    emap.at(WEEKS[2] + pd.Timedelta(days=4))
    log = emap.usage()
    assert len(log) == len(CLASSES) * 4
    assert set(log["parameter"]) == {"loadings"}
    fridays = log[log["used_on_date"].isin(WEEKS)]
    assert (fridays["fitted_through"] == fridays["used_on_date"]).all()
    tuesday = log[~log["used_on_date"].isin(WEEKS)]
    assert ((tuesday["used_on_date"] - tuesday["fitted_through"]).dt.days == 4).all()
    assert len(log[log.duplicated(["instrument", "used_on_date"])]) == 0


def test_an_honest_store_passes_the_lookahead_veto_and_one_fitted_late_fails(tmp_path, params):
    from signal_lab.harness.run_context import RunContext
    from vetoes.rules import veto_lookahead

    obs = pd.DataFrame(
        {
            "series_id": ["x"],
            "period_end": [pd.Timestamp("2010-01-31")],
            "knowledge_date": [pd.Timestamp("2010-03-01")],
            "used_on_date": [pd.Timestamp("2010-03-05")],
        }
    )
    honest_dir, late_dir = tmp_path / "honest", tmp_path / "late"
    honest_dir.mkdir()
    late_dir.mkdir()
    verdicts = {}
    for label, root, late in (("honest", honest_dir, False), ("late", late_dir, True)):
        digest = _write(root, fitted_late=late)
        m = ExposureMap.from_params(FakeParams(directory_hash=digest), root)
        for week in WEEKS:
            m(week)
        ctx = RunContext(run_id="R", observation_usage=obs, parameter_usage=m.usage())
        verdicts[label] = veto_lookahead(ctx, params)
    assert verdicts["honest"].passed
    assert not verdicts["late"].passed and "fitted past the date" in verdicts["late"].detail


def test_the_run_context_gets_the_usage_and_a_constant_matrix_gets_none(emap):
    from signal_lab.harness.experiment import ExperimentResult, attach_parameter_usage
    from signal_lab.harness.run_context import RunContext

    emap(WEEKS[0])

    def fresh():
        return ExperimentResult(RunContext(run_id="R"), None, {}, {})

    got = attach_parameter_usage(fresh(), emap)
    assert {"fitted_through", "used_on_date"} <= set(got.run_context.parameter_usage.columns)
    assert len(got.run_context.parameter_usage) == len(CLASSES)
    const = constant_exposures(pd.DataFrame(0.0, index=["A"], columns=["f0"]))
    assert attach_parameter_usage(fresh(), const).run_context.parameter_usage is None


# --- no row, no holding ---------------------------------------------------------------------


def _panel(ids=("TSY", "EQ"), days=25):
    index = pd.bdate_range("2015-01-01", periods=days)
    returns = pd.DataFrame(0.0, index=index, columns=list(ids))
    meta = {c: SeriesMeta(series_id=c, true_daily_start=index[0], tier="backbone") for c in ids}
    levels = (1.0 + returns).cumprod() * 100.0
    return ReturnPanel(levels=levels, returns=returns, meta=meta, snapshot_id="tiny")


class _RowsFor:
    """A rule with the marker that covers only some instruments."""

    requires_row = True

    def __init__(self, ids):
        self.frame = pd.DataFrame(0.0, index=list(ids), columns=["f0"])

    def __call__(self, _date):
        return self.frame


def test_the_engine_refuses_a_weight_on_an_instrument_without_a_row_when_the_rule_says_so():
    panel = _panel()
    weights = pd.Series({"TSY": 0.5, "EQ": 0.5})
    with pytest.raises(NoExposureRow, match="EQ"):
        run_walk_forward(
            panel,
            lambda _d, _p: weights.copy(),
            pd.Series(0.0, index=panel.returns.index),
            _RowsFor(["TSY"]),
        )
    # a zero weight on an instrument with no row is not a holding
    ok = pd.Series({"TSY": 1.0, "EQ": 0.0})
    path = run_walk_forward(
        panel,
        lambda _d, _p: ok.copy(),
        pd.Series(0.0, index=panel.returns.index),
        _RowsFor(["TSY"]),
    )
    assert len(path.dates) > 0


def test_a_constant_matrix_does_not_carry_the_marker_and_nothing_changes():
    panel = _panel()
    rule = constant_exposures(pd.DataFrame(0.0, index=["TSY"], columns=["f0"]))
    assert not getattr(rule, "requires_row", False)
    weights = pd.Series({"TSY": 0.5, "EQ": 0.5})
    path = run_walk_forward(
        panel, lambda _d, _p: weights.copy(), pd.Series(0.0, index=panel.returns.index), rule
    )
    assert len(path.dates) > 0


# --- the label map (HANDOFF task 55) --------------------------------------------------------


def test_the_region_axis_is_a_frame_of_the_six_view_regions_and_only_an_equity_with_a_view_reads_1(
    emap,
):
    frame = emap.axis("region", WEEKS[1])
    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == [
        "US",
        "Developed Europe",
        "Japan",
        "APAC ex-Japan",
        "Canada",
        "EM",
    ]
    assert frame.loc["EQ"].to_dict() == {
        "US": 1.0,
        "Developed Europe": 0.0,
        "Japan": 0.0,
        "APAC ex-Japan": 0.0,
        "Canada": 0.0,
        "EM": 0.0,
    }
    for none in ("IG", "TSY", "CSH", "HY"):  # a Global equity, a bond, cash, a commodity
        assert (frame.loc[none] == 0.0).all(), none


def test_the_region_reporting_columns_keep_a_bond_its_region_and_every_row_sums_to_0_or_1(emap):
    rule = emap(WEEKS[1])
    cols = [c for c in rule.columns if c.startswith("region_")]
    assert len(cols) == 7
    assert rule.loc["TSY", "region_us"] == 1.0  # a bond keeps a region for reporting
    assert rule.loc["IG", "region_global"] == 1.0
    assert (rule.loc["HY", cols] == 0.0).all()  # commodities read 0 in all seven
    assert set(rule[cols].sum(axis=1)) <= {0.0, 1.0}


def test_at_carries_the_label_columns_as_strings_blank_where_the_map_is_blank(emap):
    frame = emap.at(WEEKS[0])
    assert frame.loc["TSY", "curve"] == "USD" and frame.loc["TSY", "rating"] == "Government"
    assert frame.loc["TSY", "market"] == "DM" and frame.loc["TSY", "region"] == "US"
    assert frame.loc["EQ", "curve"] == "" and frame.loc["EQ", "market_label"] == ""
    for col in exposures.LABEL_COLUMNS:
        assert frame[col].map(type).eq(str).all(), col
    assert "view_US" not in frame.columns


def test_a_store_instrument_without_a_label_row_and_a_label_row_without_one_both_raise(
    tmp_path, synthetic_label_map
):
    digest = _write(tmp_path)
    fewer = {k: v for k, v in LABEL_ROWS.items() if k != "HY"}
    path = write_label_map(tmp_path / "fewer.csv", fewer)
    with pytest.raises(LabelMapMissing, match=r"in the store only \['HY'\]"):
        ExposureMap.from_params(FakeParams(directory_hash=digest), tmp_path, label_map=path)
    more = {**LABEL_ROWS, "EXTRA": "EXTRA,equity,US Equities,US,yes,,,,,,,"}
    path = write_label_map(tmp_path / "more.csv", more)
    with pytest.raises(LabelMapMissing, match=r"in the label map only \['EXTRA'\]"):
        ExposureMap.from_params(FakeParams(directory_hash=digest), tmp_path, label_map=path)


def test_a_missing_label_map_file_raises(tmp_path):
    digest = _write(tmp_path)
    with pytest.raises(LabelMapMissing, match="no label map"):
        ExposureMap.from_params(
            FakeParams(directory_hash=digest), tmp_path, label_map=tmp_path / "nope.csv"
        )
