"""
The nightly worker's gate and guard (decisions/0062, with its 2026-10-19
addendum). Both are stdlib scripts under scripts/nightly/; nothing here calls a
model, starts a session or reads data/.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
NIGHTLY = REPO_ROOT / "scripts" / "nightly"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"nightly_{name}", NIGHTLY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


gate_mod = _load("nightly_gate")
guard_mod = _load("guard")

LINE = "Nightly-release: 61 @2026-10-19T09:00 by=owner push=no"


def _gate(tmp_path: Path, line: str | None, now: str, slot: str = "night", **kw) -> dict:
    handoff = tmp_path / "HANDOFF.md"
    body = "# HANDOFF\n\n## Queue\n\n"
    if line is not None:
        body += line + "\n"
    handoff.write_text(body + "\n### 61. A task\n", encoding="utf-8")
    runs = tmp_path / "_nightly"
    runs.mkdir(exist_ok=True)
    args = gate_mod.argparse.Namespace(
        handoff=str(handoff),
        slot=slot,
        ran=str(runs / "ran-stamps.txt"),
        runs=str(runs),
        month_cap=float(kw.get("month_cap", 100)),
        sonnet_cap=6.0,
        opus_cap=12.0,
        now=now,
    )
    try:
        return gate_mod.gate(args)
    except gate_mod.Refusal as why:
        return {"GO": "0", "REASON": str(why)}


# Monday 2026-10-19; Thursday 2026-10-22.
MON_NIGHT = "2026-10-19T23:00"
THU_NIGHT = "2026-10-22T23:00"


def test_a_released_line_goes_with_sonnet_and_its_cap(tmp_path):
    out = _gate(tmp_path, LINE, MON_NIGHT)
    assert out["GO"] == "1"
    assert out["IDS"] == "61" and out["PUSH"] == "no" and out["MODEL"] == "sonnet"
    assert out["MODEL_ID"] == "claude-sonnet-5-5" and out["RUN_CAP"] == "6"
    assert out["LAST_START"] == "2026-10-20 04:30"
    assert out["WALL_SECONDS"] == str(7 * 3600)  # 23:00 to 06:00


def test_opus_doubles_the_cap(tmp_path):
    out = _gate(tmp_path, LINE + " model=opus", MON_NIGHT)
    assert out["MODEL_ID"] == "claude-opus-5-5" and out["RUN_CAP"] == "12"


@pytest.mark.parametrize(
    "line, reason",
    [
        (None, "no Nightly-release line"),
        ("Nightly-release: none @2026-10-19T09:00 by=owner push=no", "nothing is released"),
        ("Nightly-release: 61 @2026-10-19 by=owner push=no", "does not parse"),
        ("Nightly-release: 61 @2026-10-19T09:00 by=claude push=no", "does not parse"),
        ("Nightly-release: 61 @2026-10-19T09:00 by=owner push=maybe", "does not parse"),
        ("Nightly-release: 61 @2026-10-19T09:00 by=owner push=no model=fable", "does not parse"),
    ],
)
def test_the_line_must_be_present_released_and_well_formed(tmp_path, line, reason):
    out = _gate(tmp_path, line, MON_NIGHT)
    assert out["GO"] == "0" and reason in out["REASON"]


def test_two_release_lines_refuse(tmp_path):
    out = _gate(tmp_path, LINE + "\n" + LINE.replace("61", "62"), MON_NIGHT)
    assert out["GO"] == "0" and "exactly one" in out["REASON"]


def test_a_crlf_line_still_parses(tmp_path):
    assert _gate(tmp_path, LINE + "\r", MON_NIGHT)["GO"] == "1"


def test_a_stamp_runs_once(tmp_path):
    (tmp_path / "_nightly").mkdir()
    (tmp_path / "_nightly" / "ran-stamps.txt").write_text("2026-10-19T09:00\n")
    out = _gate(tmp_path, LINE, MON_NIGHT)
    assert out["GO"] == "0" and "already run" in out["REASON"]


@pytest.mark.parametrize(
    "now, slot, go",
    [
        ("2026-10-19T21:59", "night", "0"),
        ("2026-10-19T22:00", "night", "1"),
        ("2026-10-20T04:29", "night", "1"),
        ("2026-10-20T04:30", "night", "0"),
        ("2026-10-20T10:59", "day", "0"),
        ("2026-10-20T12:30", "day", "1"),
        ("2026-10-20T17:00", "day", "0"),
        ("2026-10-20T12:30", "night", "0"),
    ],
)
def test_the_slot_windows_and_the_last_start(tmp_path, now, slot, go):
    assert _gate(tmp_path, LINE, now, slot=slot)["GO"] == go


def test_the_day_slot_ends_at_18(tmp_path):
    out = _gate(tmp_path, LINE, "2026-10-20T12:30", slot="day")
    assert out["WALL_SECONDS"] == str(int(5.5 * 3600))


def test_long_waits_for_thursday_friday_or_saturday_night(tmp_path):
    line = LINE + " long"
    assert "Thursday" in _gate(tmp_path, line, MON_NIGHT)["REASON"]
    for night in ("2026-10-22T23:00", "2026-10-23T23:00", "2026-10-24T23:00"):
        out = _gate(tmp_path, line, night)
        assert out["GO"] == "1" and out["LONG"] == "yes"
        assert out["WALL_SECONDS"] == str(18 * 3600)
    # After midnight it is still Thursday's night.
    assert _gate(tmp_path, line, "2026-10-23T01:00")["GO"] == "1"
    # Never on the day slot.
    assert _gate(tmp_path, line, "2026-10-22T12:30", slot="day")["GO"] == "0"


def test_the_owner_may_name_another_night_and_cowork_may_not(tmp_path):
    tue = "Nightly-release: 61 @2026-10-19T09:00 by=owner push=no long=2026-10-20"
    assert _gate(tmp_path, tue, "2026-10-20T23:00")["GO"] == "1"
    assert _gate(tmp_path, tue, MON_NIGHT)["GO"] == "0"
    cowork = tue.replace("by=owner", "by=cowork")
    out = _gate(tmp_path, cowork, "2026-10-20T23:00")
    assert out["GO"] == "0" and "only the owner" in out["REASON"]


def _run_dir(runs: Path, name: str, cost: float | None, cap: str | None = "6") -> None:
    d = runs / name
    d.mkdir(parents=True)
    if cap is not None:
        (d / "cap").write_text(cap)
    if cost is not None:
        (d / "result.json").write_text(json.dumps({"total_cost_usd": cost}))


def test_the_monthly_cap_counts_this_month_and_unknown_costs_at_their_cap(tmp_path):
    runs = tmp_path / "_nightly"
    _run_dir(runs, "20261005-230000-night", 40.0)
    _run_dir(runs, "20261006-230000-night", None, cap="12")  # died before a result
    _run_dir(runs, "20260930-230000-night", 90.0)  # last month
    now = gate_mod.dt.datetime(2026, 10, 19, 23, 0)
    assert gate_mod.month_spend(runs, now) == pytest.approx(52.0)
    assert _gate(tmp_path, LINE, MON_NIGHT, month_cap=58)["GO"] == "1"  # 52 + 6 = 58
    out = _gate(tmp_path, LINE, MON_NIGHT, month_cap=57)
    assert out["GO"] == "0" and "monthly cap" in out["REASON"]


def test_the_cli_prints_shell_assignments(tmp_path):
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_text(LINE + "\n", encoding="utf-8")
    cmd = [
        sys.executable,
        str(NIGHTLY / "nightly_gate.py"),
        "gate",
        "--handoff",
        str(handoff),
        "--slot",
        "night",
        "--ran",
        str(tmp_path / "ran"),
        "--runs",
        str(tmp_path),
        "--month-cap",
        "100",
        "--sonnet-cap",
        "6",
        "--opus-cap",
        "12",
        "--now",
        MON_NIGHT,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    env = subprocess.run(
        ["bash", "-c", 'eval "$1"; printf "%s|%s" "$GO" "$LINE"', "_", res.stdout],
        capture_output=True,
        text=True,
        check=True,
    )
    assert env.stdout == f"1|{LINE}"


def test_result_reads_the_last_result_message(tmp_path):
    tr = tmp_path / "t.jsonl"
    tr.write_text(
        "\n".join(
            [
                json.dumps({"type": "system", "subtype": "init"}),
                "not json",
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "success",
                        "total_cost_usd": 1.23456,
                        "num_turns": 42,
                        "permission_denials": [{"tool_name": "Bash"}],
                    }
                ),
            ]
        )
        + "\n"
    )
    vals = gate_mod.result(tr, tmp_path / "r.json")
    assert vals == {"SUBTYPE": "success", "COST": "1.2346", "TURNS": "42", "DENIALS": "1"}
    assert json.loads((tmp_path / "r.json").read_text())["num_turns"] == 42
    assert (
        gate_mod.result(tmp_path / "missing.jsonl", tmp_path / "r2.json")["SUBTYPE"] == "no-result"
    )


@pytest.mark.parametrize(
    "command",
    [
        "head -5 data/raw/bloomberg/bbg.xlsx",
        "cat data/snapshots/x/panel.parquet",
        "python -c 'open(\"data/raw/a\")'",
        "cat .env",
        "cat ~/.config/signal-lab/nightly.env",
        "cat git_key",
        "echo $ANTHROPIC_API_KEY",
        "env",
        "make check && printenv",
        "cat /proc/self/environ",
        "ls data/raw; cat data/raw/x.csv",
    ],
)
def test_the_guard_refuses_vendor_data_and_secrets(command):
    assert guard_mod.verdict(command) is not None


@pytest.mark.parametrize(
    "command",
    [
        "make check",
        "scripts/unattended.sh check-scoped",
        "sha256sum data/raw/bloomberg/bbg_impvol_values_only.xlsx | cut -c1-16",
        "ls -la data/raw/bloomberg",
        "wc -c data/raw/bloomberg/bbg.xlsx",
        "git status --short",
        "grep -n environment docs/notes.md",
        "uv run --python 3.12 --group dev python scripts/build_label_map.py",
    ],
)
def test_the_guard_lets_ordinary_commands_and_hashes_through(command):
    assert guard_mod.verdict(command) is None


def test_the_guard_hook_exits_2_with_a_reason_and_fails_closed():
    def hook(stdin: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(NIGHTLY / "guard.py")], input=stdin, capture_output=True, text=True
        )

    ok = hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "make check"}}))
    assert ok.returncode == 0
    bad = hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "head data/raw/x"}}))
    assert bad.returncode == 2 and "vendor data" in bad.stderr
    assert hook("not json").returncode == 2


def test_the_worker_cannot_edit_its_own_plumbing():
    run_sh = (NIGHTLY / "run.sh").read_text()
    for path in (
        "/scripts/nightly/**",
        "/.claude/**",
        "/CLAUDE.md",
        "/SUBSTRATE.md",
        "/params/**",
        "/vetoes/**",
    ):
        assert f'"Edit({path})"' in run_sh and f'"Write({path})"' in run_sh
    assert '"Bash(git push *)"' in run_sh  # added to deny when push=no
    settings = json.loads((NIGHTLY / "settings.json").read_text())
    hook = settings["hooks"]["PreToolUse"][0]
    assert hook["matcher"] == "Bash" and "guard.py" in hook["hooks"][0]["command"]
