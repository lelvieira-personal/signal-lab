#!/usr/bin/env python3
"""
The exposure map's own check on real data (decisions/0050, 0055; HANDOFF task 54 step 4).

    make exposures-check

Walks every week of the store `params/` names through `resolve_exposures`, then the Tuesday after
each one, and writes `results/characteristics/<store_id>/exposures_check.md` and `.json`.
Counts, dates, means and one table of medians by reporting class: no instrument-week value is
printed or written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap

_bootstrap.require_one_thread()

REPO_ROOT = Path(__file__).resolve().parents[1]
# Cowork's read of the store (Python 3.10 outside the repo's environment), printed beside the
# measurement. Not a target: a figure that differs is reported, the method is not changed.
EXPECTED = {
    "store_weeks": 888,
    "first_week": "2002-12-27",
    "last_week": "2019-12-27",
    "instrument_weeks": 72606,
    "instruments_first_week": 73,
    "instruments_last_week": 84,
    "duration_measured": 6763,
    "duration_estimated": 65843,
    "duration_missing": 0,
    "measured_at_or_below_zero": 0,
    "mean_axis_duration": 1.4274,
    "mean_axis_real_nominal": 1.2792,
    "mean_axis_credit": 1.3006,
}
MEAN_TOLERANCE = 0.0001
PER_INSTRUMENT = {  # instrument -> (measured, estimated)
    "LT13TRUU": (677, 211),
    "LDC5TRUU": (758, 0),
    "LT01TRUU": (888, 0),
    "LT09TRUU": (888, 0),
    "LT11TRUU": (888, 0),
    "LUTLTRUU": (888, 0),
    "LBUTTRUU": (888, 0),
    "LUACTRUU": (888, 0),
}
COWORK_BY_CLASS_AT_LAST = {
    "Long Treasuries": 18.32,
    "Gold": 8.63,
    "IG Corporates": 5.22,
    "TIPS": 4.55,
    "Treasuries": 4.48,
    "EM Equities": 2.12,
    "European Equities": -1.14,
}
SHOULD_RAISE = ("2001-01-05", "2002-12-20")


def main() -> int:
    import pandas as pd

    from signal_lab.harness.experiment import ExposureMatrixMissing, resolve_exposures
    from signal_lab.params import get_params

    params = get_params()
    emap = resolve_exposures(None, params)
    weeks = emap.weeks
    gaps = pd.Series(weeks[1:] - weeks[:-1]).dt.days
    all_fridays = bool((weeks.dayofweek == 4).all())
    none_skipped = bool((gaps == 7).all())

    frames = []
    rule_rows = 0
    for week in weeks:
        f = emap.at(week)
        frames.append(f.assign(week=week))
        rule_rows += len(emap(week))
    cells = pd.concat(frames)
    fri_usage = emap.usage()

    tue = resolve_exposures(None, params)
    for week in weeks:
        tue.at(week + pd.Timedelta(days=4))
    tue_usage = tue.usage()

    measured = cells["axis_duration_provenance"] == "measured"
    dur = cells["axis_duration"]
    raised = {}
    for day in SHOULD_RAISE:
        try:
            emap.at(pd.Timestamp(day))
            raised[day] = False
        except ExposureMatrixMissing:
            raised[day] = True

    per_instrument = {}
    for sid in PER_INSTRUMENT:
        g = cells[cells.index == sid]
        est = g.loc[g["axis_duration_provenance"] == "estimated", "week"]
        per_instrument[sid] = {
            "measured": int((g["axis_duration_provenance"] == "measured").sum()),
            "estimated": int(len(est)),
            "estimated_first": str(est.min().date()) if len(est) else None,
            "estimated_last": str(est.max().date()) if len(est) else None,
        }

    last = cells[cells["week"] == weeks[-1]]
    by_class = last.groupby("reporting_class")["axis_duration"].median().sort_values()

    got = {
        "store_weeks": int(len(weeks)),
        "first_week": str(weeks[0].date()),
        "last_week": str(weeks[-1].date()),
        "all_fridays": all_fridays,
        "none_skipped": none_skipped,
        "instrument_weeks": int(len(cells)),
        "rule_rows_equal_instrument_weeks": bool(rule_rows == len(cells)),
        "instruments_first_week": int((cells["week"] == weeks[0]).sum()),
        "instruments_last_week": int((cells["week"] == weeks[-1]).sum()),
        "duration_measured": int(measured.sum()),
        "duration_estimated": int((~measured).sum()),
        "duration_missing": int(dur.isna().sum()),
        "measured_at_or_below_zero": int((dur[measured] <= 0).sum()),
        "mean_axis_duration": float(dur.mean()),
        "mean_axis_real_nominal": float(cells["axis_real_nominal"].mean()),
        "mean_axis_credit": float(cells["axis_credit"].mean()),
        "friday_usage_rows": int(len(fri_usage)),
        "friday_fitted_through_equals_used_on_date": bool(
            (fri_usage["fitted_through"] == fri_usage["used_on_date"]).all()
        ),
        "tuesday_usage_rows": int(len(tue_usage)),
        "tuesday_used_four_days_after_fitted_through": bool(
            ((tue_usage["used_on_date"] - tue_usage["fitted_through"]).dt.days == 4).all()
        ),
        "raises": raised,
        "per_instrument": per_instrument,
        "median_axis_duration_by_class_at_last_week": {k: float(v) for k, v in by_class.items()},
    }

    differs = []
    for k, want in EXPECTED.items():
        have = got[k]
        tol = MEAN_TOLERANCE if k.startswith("mean_") else 0
        if (isinstance(want, str) and have != want) or (
            not isinstance(want, str) and abs(have - want) > tol
        ):
            differs.append({"figure": k, "expected": want, "got": have})
    for sid, (m, e) in PER_INSTRUMENT.items():
        if (per_instrument[sid]["measured"], per_instrument[sid]["estimated"]) != (m, e):
            differs.append(
                {
                    "figure": sid,
                    "expected": [m, e],
                    "got": [per_instrument[sid]["measured"], per_instrument[sid]["estimated"]],
                }
            )
    if not (got["all_fridays"] and got["none_skipped"]):
        differs.append({"figure": "weeks", "expected": "all Fridays, none skipped", "got": False})
    if got["friday_usage_rows"] != EXPECTED["instrument_weeks"]:
        differs.append(
            {"figure": "friday_usage_rows", "expected": 72606, "got": got["friday_usage_rows"]}
        )
    if not got["friday_fitted_through_equals_used_on_date"]:
        differs.append(
            {"figure": "friday fitted_through", "expected": "= used_on_date", "got": False}
        )
    if not got["tuesday_used_four_days_after_fitted_through"]:
        differs.append({"figure": "tuesday usage", "expected": "4 days after", "got": False})
    if not all(raised.values()):
        differs.append({"figure": "raises", "expected": list(SHOULD_RAISE), "got": raised})
    got["differs_from_cowork"] = differs

    out_dir = REPO_ROOT / "results" / "characteristics" / emap.store.store_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "exposures_check.json").write_text(
        json.dumps(got, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    L = [
        f"# Exposure map check, store `{emap.store.store_id}` (HANDOFF task 54)",
        "",
        "Every store week walked through `resolve_exposures`, then the Tuesday after each one. "
        "Counts, dates, means and medians only.",
        "",
        "| Figure | Got | Cowork's read |",
        "|---|---|---|",
        f"| Store weeks | {got['store_weeks']} ({got['first_week']} to {got['last_week']}) "
        f"| 888, 2002-12-27 to 2019-12-27 |",
        f"| All Fridays / none skipped | {got['all_fridays']} / {got['none_skipped']} | yes / yes |",
        f"| Instrument-weeks | {got['instrument_weeks']:,} | 72,606 |",
        f"| Rule rows equal instrument-weeks (no row dropped for a missing value) "
        f"| {got['rule_rows_equal_instrument_weeks']} | |",
        f"| Instruments at the first / last week | {got['instruments_first_week']} / "
        f"{got['instruments_last_week']} | 73 / 84 |",
        f"| Duration cells measured / estimated / missing | {got['duration_measured']:,} / "
        f"{got['duration_estimated']:,} / {got['duration_missing']} | 6,763 / 65,843 / 0 |",
        f"| Measured duration cells at or below zero | {got['measured_at_or_below_zero']} | 0 |",
        f"| Mean of `axis_duration` | {got['mean_axis_duration']:.4f} | 1.4274 |",
        f"| Mean of `axis_real_nominal` | {got['mean_axis_real_nominal']:.4f} | 1.2792 |",
        f"| Mean of `axis_credit` | {got['mean_axis_credit']:.4f} | 1.3006 |",
        f"| Usage rows on the Fridays | {got['friday_usage_rows']:,}, fitted_through = used_on_date: "
        f"{got['friday_fitted_through_equals_used_on_date']} | 72,606, yes |",
        f"| Usage rows on the Tuesdays | {got['tuesday_usage_rows']:,}, used four days after "
        f"fitted_through: {got['tuesday_used_four_days_after_fitted_through']} | yes |",
        f"| 2001-01-05 and 2002-12-20 raise | {raised} | both raise |",
        "",
        "## Duration, measured and estimated weeks",
        "",
        "| Instrument | Measured | Estimated | Estimated from | Estimated to | Cowork's read |",
        "|---|---|---|---|---|---|",
    ]
    for sid, (m, e) in PER_INSTRUMENT.items():
        p = per_instrument[sid]
        L.append(
            f"| `{sid}` | {p['measured']} | {p['estimated']} | {p['estimated_first'] or '-'} "
            f"| {p['estimated_last'] or '-'} | {m} / {e} |"
        )
    L += [
        "",
        f"## Median `axis_duration` by reporting class at {got['last_week']}",
        "",
        "Gold reads above a 7-10y Treasury because it reads minus its real-yield loading. That "
        "is `decisions/0050` as ruled.",
        "",
        "| Class | Median | Cowork's read |",
        "|---|---|---|",
    ]
    for k, v in by_class.items():
        L.append(f"| {k} | {v:.2f} | {COWORK_BY_CLASS_AT_LAST.get(k, '')} |")
    L += ["", "## Figures that differ from Cowork's read", ""]
    L += [f"- {d}" for d in differs] or ["- none"]
    (out_dir / "exposures_check.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
