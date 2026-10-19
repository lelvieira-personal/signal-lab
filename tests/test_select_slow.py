"""The scoped slow tier (HANDOFF task 49): which slow test files can a change reach?

Fast tier. The selector is exercised on a small tree built in `tmp_path`, and
then, for what only the real tree can tell, on the real one: that nothing
reaches repo code by a route the selector cannot see, and that
`--slow-only-in` selects what the selector says it does.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import select_slow as sel  # noqa: E402

NOW = datetime(2026, 10, 7, 12, 0, 0)

BLOCK = f"{sel.BLOCK_BEGIN} -- test\nPY := uv run\ncheck:\n\t$(PY) pytest\n{sel.BLOCK_END}\n"


def write(root: Path, rel: str, text: str = "") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stamp(root: Path, when: datetime, line: str = "make check-full rc=0 (10 s)") -> None:
    write(
        root,
        "results/audit/_unattended/20261007-000000-check-full/status.txt",
        f"{when.isoformat()}-04:00 {line}\n",
    )


@pytest.fixture
def tree(tmp_path):
    """A repo in miniature. Slow files: test_one, test_two, test_three."""
    root = tmp_path
    write(root, "src/signal_lab/__init__.py")
    write(root, "src/signal_lab/a.py", "X = 1\n")
    write(root, "src/signal_lab/b.py", "X = 2\n")
    write(root, "src/signal_lab/c.py", "X = 3\n")
    write(root, "src/signal_lab/shared.py", "X = 4\n")
    write(root, "src/signal_lab/unused.py", "X = 5\n")
    write(root, "src/signal_lab/sub/__init__.py", "from . import leaf\n")
    write(root, "src/signal_lab/sub/leaf.py", "from signal_lab import c\n")
    write(root, "scripts/tool.py", "from signal_lab.sub import leaf\n")
    write(root, "tests/conftest.py", "def fixture():\n    from signal_lab import shared\n")
    write(
        root,
        "tests/test_one.py",
        "import pytest\nfrom signal_lab import a\n\n@pytest.mark.slow\ndef test_x():\n    pass\n",
    )
    write(
        root,
        "tests/test_two.py",
        "import pytest\n\n@pytest.mark.slow\ndef test_y():\n    from signal_lab.b import X\n",
    )
    write(
        root,
        "tests/test_three.py",
        "import pytest\nimport tool\n\npytestmark = pytest.mark.slow\n",
    )
    write(root, "tests/test_fast.py", "from signal_lab import a\n\ndef test_z():\n    pass\n")
    write(root, "build.mk", BLOCK)
    stamp(root, NOW - timedelta(days=1))
    return root


def run(root, changes, build_old=BLOCK, now=NOW, build_new=None):
    return sel.decide(root, changes, build_old, now, build_new)


SLOW = ["tests/test_one.py", "tests/test_three.py", "tests/test_two.py"]


def test_a_module_only_one_slow_file_imports_selects_only_that_file(tree):
    r = run(tree, [("M", "src/signal_lab/a.py")])
    assert r.tier == "SCOPED"
    assert r.selected == ["tests/test_one.py"]


def test_an_import_inside_a_function_is_followed(tree):
    r = run(tree, [("M", "src/signal_lab/b.py")])
    assert (r.tier, r.selected) == ("SCOPED", ["tests/test_two.py"])


def test_a_script_imported_by_bare_name_and_what_it_imports_are_followed(tree):
    for changed in ("scripts/tool.py", "src/signal_lab/sub/leaf.py", "src/signal_lab/c.py"):
        r = run(tree, [("M", changed)])
        assert (r.tier, r.selected) == ("SCOPED", ["tests/test_three.py"]), changed


def test_a_package_brings_its_init(tree):
    r = run(tree, [("M", "src/signal_lab/sub/__init__.py")])
    assert r.selected == ["tests/test_three.py"]


def test_a_slow_test_file_selects_itself_and_a_fast_one_selects_nothing(tree):
    assert run(tree, [("M", "tests/test_two.py")]).selected == ["tests/test_two.py"]
    r = run(tree, [("M", "tests/test_fast.py")])
    assert (r.tier, r.selected) == ("SCOPED", [])


def test_a_change_conftest_imports_selects_every_slow_file(tree):
    r = run(tree, [("M", "src/signal_lab/shared.py")])
    assert (r.tier, r.selected) == ("SCOPED", SLOW)


def test_a_module_nothing_imports_selects_nothing(tree):
    r = run(tree, [("M", "src/signal_lab/unused.py")])
    assert (r.tier, r.selected, r.left_out) == ("SCOPED", [], SLOW)


@pytest.mark.parametrize(
    "path",
    [
        "params/x.yaml",
        "vetoes/v.py",
        "pyproject.toml",
        "uv.lock",
        "tests/conftest.py",
        "tests/fixtures/x.csv",
        "tests/helper.py",
        "data/universe/x.json",
        ".githooks/commit-msg",
        "scripts/unattended.sh",
        "scripts/_bootstrap.py",
        "scripts/select_slow.py",
        "src/signal_lab/data.yaml",
        "an/unknown/path.txt",
    ],
)
def test_a_path_the_selector_cannot_place_is_full(tree, path):
    r = run(tree, [("M", "src/signal_lab/a.py"), ("M", path)])
    assert r.tier == "FULL"
    assert path in r.reason


def test_a_deleted_code_file_is_full_and_a_deleted_note_is_not(tree):
    assert run(tree, [("D", "src/signal_lab/a.py")]).tier == "FULL"
    assert run(tree, [("D", "tests/test_one.py")]).tier == "FULL"
    assert run(tree, [("D", "decisions/0001.md")]).tier == "SCOPED"


def test_neutral_paths_reach_no_slow_test(tree):
    r = run(
        tree,
        [
            ("M", "HANDOFF.md"),
            ("M", "decisions/0046.md"),
            ("M", "hypotheses/pending/H.yaml"),
            ("M", "docs/x.md"),
            ("M", "results/x/summary.json"),
            ("M", ".gitignore"),
        ],
    )
    assert (r.tier, r.selected, r.left_out) == ("SCOPED", [], SLOW)


def test_a_markdown_file_below_the_root_is_not_neutral(tree):
    assert run(tree, [("M", "src/signal_lab/NOTES.md")]).tier == "FULL"


def test_a_changed_check_block_is_full_and_a_new_target_outside_it_is_not(tree):
    changed = BLOCK.replace("pytest", "pytest -x")
    write(tree, "build.mk", changed)
    r = run(tree, [("M", "build.mk")])
    assert r.tier == "FULL" and "check block changed" in r.reason

    outside = "audit:\n\techo hi\n" + BLOCK + "# a comment\n"
    write(tree, "build.mk", outside)
    assert run(tree, [("M", "build.mk")]).tier == "SCOPED"


def test_the_check_block_compares_without_line_endings(tree):
    write(tree, "build.mk", BLOCK)
    crlf = BLOCK.replace("\n", "\r\n")
    assert run(tree, [("M", "build.mk")], build_old=crlf).tier == "SCOPED"


def test_a_missing_marker_on_either_side_is_full(tree):
    write(tree, "build.mk", "check:\n\techo\n")
    assert "marker" in run(tree, [("M", "build.mk")]).reason
    write(tree, "build.mk", BLOCK)
    r = run(tree, [("M", "build.mk")], build_old="check:\n\techo\n")
    assert r.tier == "FULL" and "marker" in r.reason
    assert run(tree, [("M", "build.mk")], build_old=None).tier == "FULL"


def test_the_new_side_of_a_replay_comes_from_the_ref_not_the_tree(tree):
    r = run(tree, [("M", "build.mk")], build_new=BLOCK.replace("pytest", "pytest -x"))
    assert r.tier == "FULL"


def test_no_full_pass_in_the_last_seven_days_is_full(tmp_path, tree):
    for p in (tree / "results").rglob("status.txt"):
        p.unlink()
    r = run(tree, [("M", "src/signal_lab/a.py")])
    assert r.tier == "FULL" and "7 days" in r.reason

    stamp(tree, NOW - timedelta(days=8))
    assert run(tree, [("M", "src/signal_lab/a.py")]).tier == "FULL"

    stamp(tree, NOW - timedelta(days=6))
    assert run(tree, [("M", "src/signal_lab/a.py")]).tier == "SCOPED"


def test_only_a_passing_whole_suite_run_counts(tree):
    for p in (tree / "results").rglob("status.txt"):
        p.unlink()
    for line in (
        "make check-full rc=2 (10 s)",
        "make check rc=0 (10 s)",
        "make check-scoped rc=0 (10 s) tier=SCOPED",
    ):
        stamp(tree, NOW - timedelta(hours=1), line)
        assert run(tree, [("M", "src/signal_lab/a.py")]).tier == "FULL", line
    stamp(tree, NOW - timedelta(hours=1), "make check-scoped rc=0 (10 s) tier=FULL")
    assert run(tree, [("M", "src/signal_lab/a.py")]).tier == "SCOPED"


def test_a_file_that_will_not_parse_is_full(tree):
    write(tree, "src/signal_lab/a.py", "def broken(:\n")
    r = run(tree, [("M", "src/signal_lab/a.py")])
    assert r.tier == "FULL" and "cannot parse" in r.reason


def test_selected_plus_left_out_is_every_slow_file_exactly_once(tree):
    for changed in ("src/signal_lab/a.py", "src/signal_lab/shared.py", "src/signal_lab/unused.py"):
        r = run(tree, [("M", changed)])
        assert sorted(r.selected + r.left_out) == SLOW, changed
    full = run(tree, [("M", "params/x.yaml")])
    assert sorted(full.selected + full.left_out) == SLOW


def test_a_full_result_leaves_no_slow_file_out(tree):
    """status.txt and check.log must agree: a FULL run ran every slow file (HANDOFF task 52)."""
    full = run(tree, [("M", "params/x.yaml")])
    assert full.tier == "FULL" and full.left_out == [] and full.selected == SLOW
    assert "left out (0):\n  (none)" in sel.render(full)


def test_the_output_says_which_tier_ran(tree):
    assert sel.render(run(tree, [("M", "src/signal_lab/a.py")])).splitlines()[0] == "SCOPED"
    first = sel.render(run(tree, [("M", "params/x.yaml")])).splitlines()[0]
    assert first.startswith("FULL: ")


# --- the real tree --------------------------------------------------------------

# Files under tests/ and src/ that reach repo code by subprocess, runpy,
# importlib.import_module, __import__ or exec. The selector reads imports and
# nothing else, so it cannot see through these: a new one has to be looked at by
# a person, and this list is where that happens.
#
# test_governance.py runs scripts/check_governance.py; scripts/check_governance.py
# is also imported by name there, so the selector does see it. This file shells
# out to `pytest --collect-only` below.
#
# test_nightly.py loads scripts/nightly/*.py by path with importlib and runs
# run.sh and the hook by subprocess. It is in the fast tier and no slow test
# imports what it runs (HANDOFF task 61, decisions/0062).
INVISIBLE = {"tests/test_governance.py", "tests/test_nightly.py", "tests/test_select_slow.py"}


def _reaches_by_other_means(path: Path) -> bool:
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] in ("subprocess", "runpy") for a in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in (
            "subprocess",
            "runpy",
        ):
            return True
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name in ("import_module", "__import__", "exec"):
                return True
    return False


def test_nothing_reaches_repo_code_in_a_way_the_selector_cannot_see():
    found = {
        p.relative_to(REPO_ROOT).as_posix()
        for d in ("tests", "src")
        for p in (REPO_ROOT / d).rglob("*.py")
        if _reaches_by_other_means(p)
    }
    assert found == INVISIBLE, (
        "the selector cannot see through subprocess, runpy, importlib or exec; "
        "look at the new file, then update INVISIBLE (tests/test_select_slow.py) "
        "or make it import what it runs"
    )


def _collect(*args: str) -> set[str]:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stdout[-2000:] + out.stderr[-2000:]
    return {line for line in out.stdout.splitlines() if "::" in line}


def test_slow_only_in_selects_what_the_selector_says():
    slow = [p.relative_to(REPO_ROOT).as_posix() for p in sel.slow_files(REPO_ROOT)]
    queries = {
        "all": ["-m", "not holdout"],
        "listing_all": ["-m", "not holdout", f"--slow-only-in={','.join(slow)}"],
        "fast": ["-m", "not slow and not holdout"],
        "listing_none": ["-m", "not holdout", "--slow-only-in="],
        "one": ["-m", "not holdout", f"--slow-only-in={slow[0]}"],
        "slow": ["-m", "slow"],
    }
    with ThreadPoolExecutor(max_workers=len(queries)) as pool:
        got = dict(zip(queries, pool.map(lambda q: _collect(*q), queries.values()), strict=True))

    assert got["listing_all"] == got["all"]
    assert got["listing_none"] == got["fast"]
    # the selector's idea of a slow file is pytest's
    assert {i.split("::")[0] for i in got["slow"]} == set(slow)
    # one listed file keeps the fast tests, and only that file's slow ones
    kept_slow = {i for i in got["one"] if i in got["slow"]}
    assert kept_slow and {i.split("::")[0] for i in kept_slow} == {slow[0]}
    assert got["fast"] <= got["one"]
