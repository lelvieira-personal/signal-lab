"""
A PreToolUse hook for the nightly worker's Bash calls (decisions/0062 item 6).
Stdlib only. It refuses a command that names vendor data or a secret, because
the Read deny rules do not stop `head data/raw/...` and a nightly run has nobody
watching. Exit 2 blocks the call and shows Claude the reason; exit 0 lets the
permission rules decide.

The rule (CLAUDE.md, SUBSTRATE section 2) is wider than this hook: a script that
opens a vendor file itself is not seen here. The hook catches the direct forms.
"""

from __future__ import annotations

import json
import re
import sys

FORBIDDEN = re.compile(
    r"data/raw|data/snapshots"
    r"|(?:^|[\s/=\"'])\.env(?:\.[\w-]+)?(?=$|[\s\"';|&)])"
    r"|nightly\.env|git_key|\.credentials\.json|ANTHROPIC_API_KEY|/environ\b"
    # A bare environment dump would print the session's API key.
    r"|(?:^|[;&|(]\s*)(?:env|printenv|export\s+-p|declare\s+-x|set)\s*(?=$|[;&|)])"
)
# Forms that name a vendor path without printing a value: a hash, a listing, a size.
_ARGS = r"[^;&|`$<>()\n]+"
ALLOWED = (
    re.compile(rf"^\s*sha256sum\s{_ARGS}(?:\|\s*(?:cut|head -c)\s{_ARGS})?\s*$"),
    re.compile(rf"^\s*ls(?:\s+-[A-Za-z]+)*\s{_ARGS}$"),
    re.compile(rf"^\s*wc\s+-c\s{_ARGS}$"),
)


def verdict(command: str) -> str | None:
    """None to let the call through, else the reason it is refused."""
    if not FORBIDDEN.search(command):
        return None
    if any(rx.match(command) for rx in ALLOWED):
        return None
    return (
        "nightly guard (decisions/0062): this command names vendor data or a secret "
        "(data/raw, data/snapshots, .env, a key). Vendor data never leaves the machine "
        "and is never printed. Use the repo's own scripts (e.g. `make inspect-raw`), "
        "which report shapes and counts; a hash, `ls` or `wc -c` of such a path is allowed."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
        if not isinstance(command, str):
            raise TypeError("command is not a string")
    except (ValueError, TypeError, AttributeError) as err:
        print(f"nightly guard: unreadable hook input ({err}); refusing", file=sys.stderr)
        return 2
    why = verdict(command)
    if why:
        print(why, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
