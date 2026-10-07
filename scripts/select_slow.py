"""Which slow test files can a change reach? (HANDOFF task 49, OWNER-QUEUE L24)

A slow test file has to run when a changed file is inside what it imports,
directly or through other modules. Otherwise it can be left out. Everything
this script does not understand is FULL: a path it cannot place, a file it
cannot parse, a git call that fails.

    python3 scripts/select_slow.py [--base REF] [--head REF]
                                   [--pytest-args-file PATH]

The first line of the output is `FULL: <reason>` or `SCOPED`. Then the slow
files selected, the slow files left out, and each changed path with its kind.
Standard library only, like check_governance.py: it runs before the virtualenv
is worth building.

It reads imports, nothing else. A test that reaches repo code by other means
(subprocess, runpy, importlib, exec) is invisible to it; the fast tier holds a
list of the files that do that, so a new one fails loudly
(tests/test_select_slow.py).
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

FULL_MAX_AGE_DAYS = 7

BLOCK_BEGIN = "# check-block: begin"
BLOCK_END = "# check-block: end"

# Where the tests put code on sys.path, so where a bare `import x` can land.
SEARCH_DIRS = ("src", ".", "scripts", "render", "tests")

# Paths that need a full run whatever they are, before any other rule.
ALWAYS_FULL = {
    "pyproject.toml",
    "uv.lock",
    "tests/conftest.py",
    "scripts/unattended.sh",
    "scripts/_bootstrap.py",
    "scripts/select_slow.py",
}
NEUTRAL_DIRS = ("decisions/", "hypotheses/", "docs/", "results/")


class Full(Exception):
    """Raised anywhere the selector cannot be sure; the message is the reason."""


@dataclass
class Result:
    tier: str  # "FULL" | "SCOPED"
    reason: str = ""
    selected: list[str] = field(default_factory=list)
    left_out: list[str] = field(default_factory=list)
    kinds: dict[str, str] = field(default_factory=dict)

    def first_line(self) -> str:
        return f"FULL: {self.reason}" if self.tier == "FULL" else "SCOPED"


# --- imports -----------------------------------------------------------------


def _parse(path: Path) -> ast.AST:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError) as exc:
        raise Full(f"cannot parse {path.as_posix()}: {type(exc).__name__}") from exc


def _module_files(root: Path, dotted: str) -> set[Path]:
    """Repo files that `import <dotted>` can land on, with their parent packages."""
    if not dotted:
        return set()
    parts = dotted.split(".")
    found: set[Path] = set()
    for base in SEARCH_DIRS:
        target = (root / base).joinpath(*parts)
        for cand in (target.with_suffix(".py"), target / "__init__.py"):
            if cand.is_file():
                found.add(cand)
    return {p for f in found for p in _with_parents(root, f)}


def _with_parents(root: Path, f: Path) -> set[Path]:
    """The file plus every `__init__.py` above it inside the repo: importing a
    module imports its packages first."""
    out = {f}
    cur = f.parent
    while cur != root and root in cur.parents:
        init = cur / "__init__.py"
        if init.is_file():
            out.add(init)
        cur = cur.parent
    return out


def _imports_of(root: Path, f: Path) -> set[Path]:
    """Repo files `f` imports, at any depth of nesting (functions included)."""
    tree = _parse(f)
    found: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found |= _module_files(root, alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = f.parent
                for _ in range(node.level - 1):
                    base = base.parent
                rel = base.relative_to(root) if root in (base, *base.parents) else None
                if rel is None:
                    raise Full(f"relative import leaves the repo in {f.as_posix()}")
                prefix = ".".join(rel.parts)
                # relative to the importing package: resolve by path, not by name
                mod = ".".join(p for p in (prefix, node.module or "") if p)
                found |= _rel_files(root, mod)
                for alias in node.names:
                    found |= _rel_files(root, ".".join(p for p in (mod, alias.name) if p))
            else:
                mod = node.module or ""
                found |= _module_files(root, mod)
                for alias in node.names:
                    if alias.name != "*":
                        found |= _module_files(root, f"{mod}.{alias.name}")
    return found


def _rel_files(root: Path, dotted: str) -> set[Path]:
    """Like `_module_files`, but `dotted` is already relative to the repo root."""
    parts = dotted.split(".") if dotted else []
    target = root.joinpath(*parts)
    out: set[Path] = set()
    for cand in (target.with_suffix(".py"), target / "__init__.py"):
        if parts and cand.is_file():
            out |= _with_parents(root, cand)
    return out


def closure(root: Path, start: Path, cache: dict[Path, set[Path]] | None = None) -> set[Path]:
    """`start` plus everything it imports, transitively."""
    seen: set[Path] = set()
    todo = [start]
    cache = {} if cache is None else cache
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        if f not in cache:
            cache[f] = _imports_of(root, f)
        todo.extend(cache[f] - seen)
    return seen


# --- slow files --------------------------------------------------------------


def has_slow_mark(path: Path) -> bool:
    """True when the file mentions `pytest.mark.slow` anywhere: a decorator, a
    module-level `pytestmark`, or `pytest.param(..., marks=...)`."""
    for node in ast.walk(_parse(path)):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "slow"
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "mark"
        ):
            return True
    return False


def slow_files(root: Path) -> list[Path]:
    return sorted(p for p in (root / "tests").glob("test_*.py") if has_slow_mark(p))


# --- the changed files -------------------------------------------------------


def kind_of(path: str) -> str:
    """neutral | code | full for one repo-relative POSIX path."""
    if path in ALWAYS_FULL:
        return "full"
    if path == "build.mk":
        return "build"  # neutral only if its check block is unchanged
    if path == ".gitignore" or path.startswith(NEUTRAL_DIRS):
        return "neutral"
    if "/" not in path and path.endswith(".md"):
        return "neutral"
    parts = path.split("/")
    if path.endswith(".py"):
        if parts[0] == "src" and len(parts) > 2 and parts[1] == "signal_lab":
            return "code"
        if len(parts) == 2 and parts[0] in ("scripts", "render"):
            return "code"
        if len(parts) == 2 and parts[0] == "tests" and parts[1].startswith("test_"):
            return "code"
    return "full"


def check_block(text: str) -> str | None:
    """The lines of build.mk between the two markers, line endings normalised."""
    lines = text.replace("\r\n", "\n").split("\n")
    begins = [i for i, line in enumerate(lines) if line.startswith(BLOCK_BEGIN)]
    ends = [i for i, line in enumerate(lines) if line.startswith(BLOCK_END)]
    if len(begins) != 1 or len(ends) != 1:
        return None
    a, b = begins[0], ends[0]
    if b < a:
        return None
    return "\n".join(lines[a : b + 1])


def recently_proven(root: Path, now: datetime, max_age_days: int = FULL_MAX_AGE_DAYS) -> bool:
    """A passing whole-suite run in the last `max_age_days` days, per status.txt."""
    full = re.compile(r"^(\S+) make check-full rc=0\b")
    scoped = re.compile(r"^(\S+) make check-scoped rc=0\b.*\btier=FULL\b")
    cutoff = now - timedelta(days=max_age_days)
    for status in (root / "results" / "audit" / "_unattended").glob("*/status.txt"):
        try:
            lines = status.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            m = full.match(line) or scoped.match(line)
            if not m:
                continue
            try:
                when = datetime.fromisoformat(m.group(1))
            except ValueError:
                continue
            if when.tzinfo is not None and now.tzinfo is None:
                when = when.replace(tzinfo=None)
            if when >= cutoff:
                return True
    return False


def decide(
    root: Path,
    changes: list[tuple[str, str]],
    build_old: str | None,
    now: datetime,
    build_new: str | None = None,
) -> Result:
    """`changes` is [(status letter, repo-relative path)]; D means deleted."""
    kinds: dict[str, str] = {}
    code: list[str] = []
    reason = ""
    for status, path in sorted(set(changes), key=lambda c: c[1]):
        kind = kind_of(path)
        if kind == "build":
            if status == "D":
                new = ""
            elif build_new is not None:
                new = build_new
            else:
                new = (root / "build.mk").read_text(encoding="utf-8")
            old_block = check_block(build_old) if build_old is not None else None
            new_block = check_block(new)
            if old_block is None or new_block is None:
                kind, why = "full", "build.mk: a check-block marker is missing"
            elif old_block != new_block:
                kind, why = "full", "build.mk: the check block changed"
            else:
                kind, why = "neutral", ""
            reason = reason or why
        elif kind == "code" and status == "D":
            kind, why = "full", f"{path} was deleted or renamed"
            reason = reason or why
        elif kind == "full":
            reason = reason or f"{path} is not a path the selector can place"
        kinds[path] = kind if kind != "full" else "FULL"
        if kind == "code":
            code.append(path)

    slow = [p.relative_to(root).as_posix() for p in slow_files(root)]

    if any(k == "FULL" for k in kinds.values()):
        return Result("FULL", reason, [], slow, kinds)
    if not recently_proven(root, now):
        return Result(
            "FULL",
            f"no whole-suite pass in the last {FULL_MAX_AGE_DAYS} days",
            [],
            slow,
            kinds,
        )

    try:
        cache: dict[Path, set[Path]] = {}
        shared = closure(root, root / "tests" / "conftest.py", cache)
        changed = {root / c for c in code}
        selected = []
        for s in slow:
            reach = closure(root, root / s, cache) | shared
            if reach & changed:
                selected.append(s)
    except Full as exc:
        return Result("FULL", str(exc), [], slow, kinds)
    left_out = [s for s in slow if s not in selected]
    return Result("SCOPED", "", selected, left_out, kinds)


# --- git ---------------------------------------------------------------------


def _git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Full(f"git could not run: {exc}") from exc
    if proc.returncode != 0:
        raise Full(f"git {' '.join(args)} failed (rc={proc.returncode})")
    return proc.stdout


def git_changes(root: Path, base: str, head: str | None) -> list[tuple[str, str]]:
    refs = [base, head] if head else [base]
    out = _git(root, "-c", "core.quotePath=false", "diff", "--name-status", "--no-renames", *refs)
    changes = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if not path:
            raise Full(f"unreadable git diff line: {line!r}")
        changes.append((status[0], path))
    if not head:
        untracked = _git(
            root, "-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard"
        )
        changes += [("A", p) for p in untracked.splitlines() if p]
    return changes


def git_build(root: Path, ref: str) -> str | None:
    try:
        return _git(root, "show", f"{ref}:build.mk")
    except Full:
        return None


def render(result: Result) -> str:
    lines = [result.first_line()]
    lines.append(f"selected ({len(result.selected)}):")
    lines += [f"  {s}" for s in result.selected] or ["  (none)"]
    lines.append(f"left out ({len(result.left_out)}):")
    lines += [f"  {s}" for s in result.left_out] or ["  (none)"]
    lines.append(f"changed paths ({len(result.kinds)}):")
    lines += [f"  {k:8s} {p}" for p, k in sorted(result.kinds.items())] or ["  (none)"]
    return "\n".join(lines)


def pytest_args(result: Result) -> str:
    """The selection part of the pytest command: empty means the whole suite."""
    if result.tier == "FULL":
        return ""
    return f'-m "not holdout" --slow-only-in={",".join(result.selected)}'


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--head", default=None, help="replay mode: diff base..head, no untracked files")
    ap.add_argument("--pytest-args-file", help="write the selection's pytest arguments here")
    args = ap.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        changes = git_changes(root, args.base, args.head)
        build_old = git_build(root, args.base)
        build_new = git_build(root, args.head) if args.head else None
        result = decide(root, changes, build_old, datetime.now().astimezone(), build_new)
    except Full as exc:
        result = Result("FULL", str(exc))
    print(render(result))
    if args.pytest_args_file:
        Path(args.pytest_args_file).write_text(pytest_args(result) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
