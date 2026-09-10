"""Owner-only paths may be *transcribed* by an agent, never *originated*.

SUBSTRATE section 2, as amended in v0.4:

    An agent may apply a change to `SUBSTRATE.md`, `params/*.yaml` or anything
    under `vetoes/` only when the owner has already decided it and the decision
    is recorded in `decisions/`, and must cite that decision in the commit.

This module is the mechanical half of that rule. It answers one question --
"does this commit touch an owner-only path without citing a decision that
exists?" -- and it answers it the same way whether it is called from a
commit-msg hook, from `make check`, or from a test.

It is deliberately stdlib-only. A commit hook that needs a virtualenv to run is
a commit hook that gets disabled the first time it is inconvenient.

Fail closed. If the decision register cannot be read, the answer is no.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Paths the owner alone decides. Prefixes, matched against repo-relative
# POSIX paths.
OWNER_ONLY_PREFIXES: tuple[str, ...] = (
    "SUBSTRATE.md",
    "params/",
    "vetoes/",
)

# Enforcement begins at the commit that introduced the hook, found by asking
# git when this file first appeared. Anchoring on the marker rather than on a
# date means history written before the rule existed is not retroactively
# judged, and no constant has to be maintained.
HOOK_MARKER = ".githooks/commit-msg"

# Fallback only, for a checkout with no history for the marker (a shallow clone
# in CI, say). Commits authored before this date are not scanned.
ENFORCED_FROM = "2026-09-10"

# `decisions/0019`, `decisions/0019-conviction.md`, `decision 0019`, `#0019`.
CITATION_RE = re.compile(
    r"(?:decisions?[ /\-]|#)(\d{4})\b",
    re.IGNORECASE,
)

DECISION_FILE_RE = re.compile(r"^(\d{4})[-_].*\.md$")


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str
    owner_only: tuple[str, ...] = ()
    cited: tuple[str, ...] = ()

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.ok


def owner_only_paths(changed: list[str]) -> tuple[str, ...]:
    """The subset of `changed` that only the owner may decide."""
    hits = []
    for raw in changed:
        path = raw.strip().replace("\\", "/").lstrip("./")
        if not path:
            continue
        for prefix in OWNER_ONLY_PREFIXES:
            if path == prefix or path.startswith(prefix):
                hits.append(path)
                break
    return tuple(sorted(set(hits)))


def cited_decisions(message: str) -> tuple[str, ...]:
    """Decision numbers cited anywhere in a commit message."""
    return tuple(sorted(set(m.group(1) for m in CITATION_RE.finditer(message))))


def check(
    changed: list[str],
    message: str,
    known_decisions: set[str] | None,
) -> Verdict:
    """The whole rule, as a pure function.

    `known_decisions` is the set of four-digit ids that exist in `decisions/`.
    `None` means the register could not be read, which is a failure, not a pass.
    """
    touched = owner_only_paths(changed)
    if not touched:
        return Verdict(True, "no owner-only paths touched")

    if known_decisions is None:
        return Verdict(
            False,
            "cannot read decisions/, so the citation cannot be verified. "
            "Refusing rather than assuming.",
            owner_only=touched,
        )

    cited = cited_decisions(message)
    if not cited:
        return Verdict(
            False,
            "this commit changes owner-only files and cites no decision.\n"
            "  " + "\n  ".join(touched) + "\n"
            "SUBSTRATE section 2: an agent may transcribe a decision the owner "
            "has already made and recorded in decisions/, never originate one.\n"
            "Add the decision to the commit message, e.g. "
            "'(decisions/0019)'.",
            owner_only=touched,
        )

    missing = tuple(d for d in cited if d not in known_decisions)
    if missing:
        return Verdict(
            False,
            "cites decision(s) that do not exist in decisions/: "
            + ", ".join(missing)
            + ".\nA citation to a record that was never written is not a "
            "decision, it is a claim.",
            owner_only=touched,
            cited=cited,
        )

    return Verdict(
        True,
        "owner-only change cites " + ", ".join("decisions/" + d for d in cited),
        owner_only=touched,
        cited=cited,
    )


# --------------------------------------------------------------------------
# git-backed CLI
# --------------------------------------------------------------------------


def _git(args: list[str], cwd: Path, ok_codes: tuple[int, ...] = (0,)) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if out.returncode not in ok_codes:
        raise subprocess.CalledProcessError(out.returncode, args, out.stdout, out.stderr)
    return out.stdout


def repo_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    return Path(_git(["rev-parse", "--show-toplevel"], start).strip())


def read_decisions(root: Path) -> set[str] | None:
    """Ids present in decisions/. None if the directory is missing."""
    d = root / "decisions"
    if not d.is_dir():
        return None
    ids = {m.group(1) for p in d.iterdir() if (m := DECISION_FILE_RE.match(p.name))}
    return ids or None


def check_staged(root: Path, message: str) -> Verdict:
    changed = _git(["diff", "--cached", "--name-only"], root).splitlines()
    return check(changed, message, read_decisions(root))


def check_commit(root: Path, rev: str) -> Verdict:
    changed = _git(["show", "--pretty=format:", "--name-only", rev], root).splitlines()
    message = _git(["log", "-1", "--format=%B", rev], root)
    return check(changed, message, read_decisions(root))


def enforcement_start(root: Path) -> str | None:
    """The commit that introduced the hook, or None if it is not in history."""
    out = _git(
        ["log", "--diff-filter=A", "--format=%H", "--", HOOK_MARKER],
        root,
    ).split()
    return out[-1] if out else None


def revs_to_check(root: Path) -> list[str]:
    """Every commit the rule applies to, oldest first.

    From the commit that introduced the hook (inclusive -- that commit is
    itself subject to the rule) to HEAD. With no marker in history, fall back
    to a date so that a shallow checkout still checks something.
    """
    start = enforcement_start(root)
    if start is None:
        return _git(["log", f"--since={ENFORCED_FROM}", "--format=%H", "--reverse"], root).split()
    return (
        _git(
            ["log", f"{start}^..HEAD", "--format=%H", "--reverse"], root, ok_codes=(0, 128)
        ).split()
        or _git(["log", "--format=%H", "--reverse"], root).split()
    )


def check_history(root: Path) -> list[tuple[str, Verdict]]:
    bad = []
    for rev in revs_to_check(root):
        v = check_commit(root, rev)
        if not v.ok:
            bad.append((rev, v))
    return bad


def hooks_installed(root: Path) -> bool:
    try:
        path = _git(["config", "--get", "core.hooksPath"], root).strip()
    except subprocess.CalledProcessError:
        return False
    return path == ".githooks"


def _fail(rev: str | None, verdict: Verdict) -> int:
    where = f" in {rev[:8]}" if rev else ""
    sys.stderr.write(f"\ngovernance: refused{where}.\n{verdict.reason}\n\n")
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--commit-msg", metavar="FILE", help="path to COMMIT_EDITMSG")
    g.add_argument("--rev", help="check one existing commit")
    g.add_argument(
        "--history",
        action="store_true",
        help="check every commit since the hook was introduced",
    )
    g.add_argument("--hooks", action="store_true", help="assert the hook is installed")
    p.add_argument("-C", dest="cwd", default=".", help="run as if started in this directory")
    a = p.parse_args(argv)

    root = repo_root(Path(a.cwd).resolve())

    if a.hooks:
        if hooks_installed(root):
            print("governance: commit hook installed (core.hooksPath=.githooks)")
            return 0
        sys.stderr.write(
            "\ngovernance: the commit hook is not installed, so nothing is "
            "enforcing SUBSTRATE section 2 at commit time.\n"
            "Run:  make install   (or: git config core.hooksPath .githooks)\n\n"
        )
        return 1

    if a.commit_msg:
        message = Path(a.commit_msg).read_text(encoding="utf-8", errors="replace")
        v = check_staged(root, message)
        return 0 if v.ok else _fail(None, v)

    if a.rev:
        v = check_commit(root, a.rev)
        return 0 if v.ok else _fail(a.rev, v)

    bad = check_history(root)
    for rev, v in bad:
        _fail(rev, v)
    if bad:
        return 1
    start = enforcement_start(root)
    where = f"since {start[:8]}" if start else f"since {ENFORCED_FROM}"
    print(f"governance: OK, no uncited owner-only change {where}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
