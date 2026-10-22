"""
The nightly worker's gate and its result reader (decisions/0062, with its
2026-10-19 addendum). Stdlib only: `run.sh` calls it with the system python3
before any model call, so it must not need the project virtualenv.

    nightly_gate.py gate --handoff HANDOFF.md --slot night|day|poll \
        --ran results/audit/_nightly/ran-stamps.txt --runs results/audit/_nightly \
        --month-cap 100 --sonnet-cap 6 --opus-cap 12 [--now 2026-10-22T23:00]

prints shell assignments (`GO=1` or `GO=0` with `REASON=...`, and the run's
settings) for `run.sh` to eval. Every value is quoted with `shlex.quote`.

    nightly_gate.py result TRANSCRIPT.jsonl RESULT.json

copies the session's final `result` message to RESULT.json and prints
`SUBTYPE`, `COST`, `TURNS` and `DENIALS` the same way.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import sys
from pathlib import Path

LINE_PREFIX = "Nightly-release:"
LINE_RE = re.compile(
    r"^Nightly-release: (?P<ids>none|\d+(?:,\d+)*)"
    r" @(?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2})"
    r" by=(?P<by>owner|cowork)"
    r" push=(?P<push>yes|no)"
    r"(?: model=(?P<model>sonnet|opus))?"
    r"(?P<long> long(?:=(?P<long_night>\d{4}-\d{2}-\d{2}))?)?$"
)
MODEL_IDS = {"sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}

# The two slots (addendum of 2026-10-19). Times are local (ET on the owner's laptop).
NIGHT_FIRST = dt.time(22, 0)  # a start before this is not the night slot
NIGHT_LAST = dt.time(4, 30)  # no new task after this
NIGHT_END = dt.time(6, 0)  # the laptop leaves home
DAY_FIRST = dt.time(11, 0)
DAY_LAST = dt.time(17, 0)
DAY_END = dt.time(18, 0)
LONG_NIGHTS = {3, 4, 5}  # Thursday, Friday, Saturday nights (Monday is 0)
LONG_WALL = dt.timedelta(hours=18)
# decisions/0064: the `poll` slot has no clock window. A run that is not `long` gets this wall.
POLL_WALL = dt.timedelta(hours=5)


class Refusal(Exception):
    """The gate says no. The message is the reason, logged by run.sh."""


def release_line(handoff_text: str) -> str:
    lines = [ln.rstrip("\r") for ln in handoff_text.split("\n") if ln.startswith(LINE_PREFIX)]
    if not lines:
        raise Refusal("no Nightly-release line in HANDOFF.md")
    if len(lines) > 1:
        raise Refusal(f"{len(lines)} Nightly-release lines in HANDOFF.md; exactly one is allowed")
    return lines[0]


def parse(line: str) -> dict[str, str | None]:
    m = LINE_RE.match(line)
    if not m:
        raise Refusal(f"the release line does not parse: {line!r}")
    return m.groupdict()


def window(slot: str, now: dt.datetime) -> tuple[dt.date, dt.datetime, dt.datetime]:
    """(the slot's date, the last start, the slot's end) for a start at `now`."""
    t = now.time()
    if slot == "night":
        if t >= NIGHT_FIRST:
            night_of = now.date()
        elif t < NIGHT_LAST:
            night_of = now.date() - dt.timedelta(days=1)
        else:
            raise Refusal(f"{t:%H:%M} is outside the night slot (22:00 to 04:30)")
        nxt = night_of + dt.timedelta(days=1)
        return (
            night_of,
            dt.datetime.combine(nxt, NIGHT_LAST),
            dt.datetime.combine(nxt, NIGHT_END),
        )
    if slot == "day":
        if not (DAY_FIRST <= t < DAY_LAST):
            raise Refusal(f"{t:%H:%M} is outside the day slot (11:00 to 17:00)")
        d = now.date()
        return d, dt.datetime.combine(d, DAY_LAST), dt.datetime.combine(d, DAY_END)
    if slot == "poll":
        end = now + POLL_WALL
        return now.date(), end, end
    raise Refusal(f"unknown slot {slot!r}")


def month_spend(runs: Path, now: dt.datetime) -> float:
    """
    Spend of this month's runs, from their `result.json`. A run with no readable
    cost counts at its cap (the `cap` file written at its start): fail toward
    stopping, never toward spending.
    """
    total = 0.0
    prefix = now.strftime("%Y%m")
    if not runs.is_dir():
        return total
    for d in sorted(runs.iterdir()):
        if not (d.is_dir() and d.name.startswith(prefix)):
            continue
        cost = None
        try:
            cost = float(json.loads((d / "result.json").read_text())["total_cost_usd"])
        except (OSError, ValueError, KeyError, TypeError):
            pass
        if cost is None:
            try:
                cost = float((d / "cap").read_text().strip())
            except (OSError, ValueError):
                cost = 0.0  # no cap file: the run never reached the model call
        total += cost
    return total


def gate(args: argparse.Namespace) -> dict[str, str]:
    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now()
    line = release_line(Path(args.handoff).read_text(encoding="utf-8"))
    rel = parse(line)
    if rel["ids"] == "none":
        raise Refusal("nothing is released")
    ran = Path(args.ran)
    seen = set(ran.read_text().split()) if ran.exists() else set()
    if rel["stamp"] in seen:
        raise Refusal(f"stamp {rel['stamp']} has already run")
    night_of, last_start, end = window(args.slot, now)
    long = bool(rel["long"])
    if long:
        named = rel["long_night"]
        if args.slot != "night":
            raise Refusal("a long release waits for a night slot")
        if named is not None:
            if rel["by"] != "owner":
                raise Refusal("only the owner may name a night for a long run")
            if named != night_of.isoformat():
                raise Refusal(f"the long run is released for the night of {named}")
        elif night_of.weekday() not in LONG_NIGHTS:
            raise Refusal("a long release waits for a Thursday, Friday or Saturday night")
        wall = LONG_WALL
    else:
        if now >= last_start:
            raise Refusal(f"past the last start, {last_start:%H:%M}")
        wall = end - now
    model = rel["model"] or "sonnet"
    cap = args.opus_cap if model == "opus" else args.sonnet_cap
    spend = month_spend(Path(args.runs), now)
    if spend + cap > args.month_cap:
        raise Refusal(
            f"monthly cap: {spend:.2f} spent this month, this run may spend {cap:.2f}, "
            f"the cap is {args.month_cap:.2f}"
        )
    return {
        "GO": "1",
        "REASON": "released",
        "LINE": line,
        "IDS": rel["ids"],
        "STAMP": rel["stamp"],
        "BY": rel["by"],
        "PUSH": rel["push"],
        "MODEL": model,
        "MODEL_ID": MODEL_IDS[model],
        "RUN_CAP": f"{cap:g}",
        "LONG": "yes" if long else "no",
        "NIGHT_OF": night_of.isoformat(),
        "LAST_START": "none (long run)" if long else last_start.strftime("%Y-%m-%d %H:%M"),
        "WALL_SECONDS": str(int(wall.total_seconds())),
        "MONTH_SPEND": f"{spend:.2f}",
    }


def result(transcript: Path, out: Path) -> dict[str, str]:
    """The session's last `result` message, copied out of the transcript."""
    last = None
    try:
        with transcript.open(encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw.startswith("{"):
                    continue
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(msg, dict) and msg.get("type") == "result":
                    last = msg
    except OSError:
        pass
    if last is None:
        return {"SUBTYPE": "no-result", "COST": "", "TURNS": "", "DENIALS": "", "DENIED": ""}
    keep = {
        k: last.get(k)
        for k in (
            "subtype",
            "is_error",
            "total_cost_usd",
            "num_turns",
            "duration_ms",
            "session_id",
            "permission_denials",
            "modelUsage",
            "usage",
            "result",
        )
        if k in last
    }
    out.write_text(json.dumps(keep, indent=2), encoding="utf-8")
    denials = last.get("permission_denials") or []
    shown = []
    for d in denials[:3]:
        tool = d.get("tool_name", "?") if isinstance(d, dict) else "?"
        inp = d.get("tool_input", {}) if isinstance(d, dict) else {}
        what = (inp.get("command") or inp.get("file_path") or "") if isinstance(inp, dict) else ""
        shown.append(f"{tool}: {' '.join(str(what).split())[:160]}")
    return {
        "SUBTYPE": str(last.get("subtype", "")),
        "COST": ""
        if last.get("total_cost_usd") is None
        else f"{float(last['total_cost_usd']):.4f}",
        "TURNS": str(last.get("num_turns", "")),
        "DENIALS": str(len(denials)),
        "DENIED": " | ".join(shown),
    }


def emit(values: dict[str, str]) -> None:
    for k, v in values.items():
        print(f"{k}={shlex.quote(v)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--handoff", required=True)
    g.add_argument("--slot", required=True, choices=["night", "day", "poll"])
    g.add_argument("--ran", required=True)
    g.add_argument("--runs", required=True)
    g.add_argument("--month-cap", type=float, required=True)
    g.add_argument("--sonnet-cap", type=float, required=True)
    g.add_argument("--opus-cap", type=float, required=True)
    g.add_argument("--now", default=None, help="for tests: an ISO local time")
    r = sub.add_parser("result")
    r.add_argument("transcript")
    r.add_argument("out")
    args = ap.parse_args(argv)
    if args.cmd == "result":
        emit(result(Path(args.transcript), Path(args.out)))
        return 0
    try:
        emit(gate(args))
    except Refusal as why:
        emit({"GO": "0", "REASON": str(why)})
    except OSError as err:
        emit({"GO": "0", "REASON": f"the gate could not read a file: {err}"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
