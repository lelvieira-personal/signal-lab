"""The commit-time half of SUBSTRATE section 2.

An agent may transcribe an owner-approved decision into SUBSTRATE.md,
params/*.yaml or vetoes/. It may not originate one. Mechanically, that means:
every commit touching those paths cites a decision record that exists.

These tests exercise the pure rule, and then exercise the real hook against a
real git repository, because a hook that is not installed is a rule that is not
enforced and the difference is invisible from the pure function.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_governance as gov  # noqa: E402

DECISIONS = {"0013", "0019", "0020"}


# --- the rule itself ------------------------------------------------------


def test_ordinary_code_change_needs_no_citation():
    v = gov.check(["src/signal_lab/harness/engine.py"], "engine: fix drift order", DECISIONS)
    assert v.ok


def test_substrate_change_without_a_citation_is_refused():
    v = gov.check(["SUBSTRATE.md"], "substrate: tidy wording", DECISIONS)
    assert not v.ok
    assert "SUBSTRATE.md" in v.reason


def test_substrate_change_with_a_citation_is_allowed():
    v = gov.check(["SUBSTRATE.md"], "substrate: v0.4 (decisions/0020)", DECISIONS)
    assert v.ok
    assert v.cited == ("0020",)


@pytest.mark.parametrize(
    "path",
    [
        "params/costs.yaml",
        "params/objective.yaml",
        "vetoes/turnover.py",
        "vetoes/__init__.py",
        "SUBSTRATE.md",
    ],
)
def test_every_owner_only_path_is_covered(path):
    assert gov.owner_only_paths([path]) == (path,)
    assert not gov.check([path], "change it", DECISIONS).ok


@pytest.mark.parametrize(
    "path",
    [
        "src/signal_lab/params.py",
        "tests/test_params.py",
        "decisions/0021-x.md",
        "render/static_report.py",
    ],
)
def test_paths_the_agent_owns_are_not_caught(path):
    assert gov.owner_only_paths([path]) == ()


@pytest.mark.parametrize(
    "message",
    [
        "substrate: v0.4 (decisions/0020)",
        "substrate: v0.4, per decisions/0020-substrate-v04-amendment.md",
        "vetoes: drop active_drawdown\n\nAuthorised by decision 0020.",
        "params: turnover penalty\n\nSee #0019.",
    ],
)
def test_citation_forms(message):
    assert gov.cited_decisions(message)
    assert gov.check(["SUBSTRATE.md"], message, DECISIONS).ok


def test_a_citation_to_a_decision_that_does_not_exist_is_refused():
    v = gov.check(["SUBSTRATE.md"], "substrate: per decisions/0999", DECISIONS)
    assert not v.ok
    assert "0999" in v.reason


def test_an_unreadable_register_fails_closed():
    v = gov.check(["SUBSTRATE.md"], "substrate: per decisions/0020", None)
    assert not v.ok
    assert "Refusing" in v.reason


def test_windows_path_separators_are_still_owner_only():
    assert gov.owner_only_paths(["params\\costs.yaml"]) == ("params/costs.yaml",)


def test_a_mixed_commit_is_judged_on_its_owner_only_part():
    changed = ["src/signal_lab/params.py", "params/costs.yaml", "tests/test_params.py"]
    assert not gov.check(changed, "wire up costs", DECISIONS).ok
    assert gov.check(changed, "wire up costs (decisions/0019)", DECISIONS).ok


def test_there_is_no_bypass_argument():
    """The holdout lock has no escape hatch and neither does this."""
    import inspect

    banned = ("force", "bypass", "override", "skip", "unsafe", "allow_uncited")
    for name, fn in vars(gov).items():
        if not inspect.isfunction(fn) or name.startswith("_"):
            continue
        params = set(inspect.signature(fn).parameters)
        assert not params & set(banned), f"{name} takes an escape hatch"


# --- the hook, against a real repository ----------------------------------


def _git(repo: Path, *args: str, check: bool = True):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    r = tmp_path / "repo"
    (r / "scripts").mkdir(parents=True)
    (r / ".githooks").mkdir()
    (r / "decisions").mkdir()
    (r / "params").mkdir()
    (r / "src").mkdir()

    (r / "scripts" / "check_governance.py").write_text(
        (root / "scripts" / "check_governance.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    hook = r / ".githooks" / "commit-msg"
    hook.write_text(
        (root / ".githooks" / "commit-msg").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    hook.chmod(0o755)

    (r / "decisions" / "0020-substrate-v04-amendment.md").write_text("# 0020\n", encoding="utf-8")
    (r / "SUBSTRATE.md").write_text("v0.3\n", encoding="utf-8")
    (r / "params" / "costs.yaml").write_text("spread_bps: 15\n", encoding="utf-8")
    (r / "src" / "thing.py").write_text("x = 1\n", encoding="utf-8")

    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.com")
    _git(r, "config", "user.name", "t")
    _git(r, "config", "commit.gpgsign", "false")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "initial (decisions/0020)", "--no-verify")
    _git(r, "config", "core.hooksPath", ".githooks")
    return r


def test_hook_lets_an_ordinary_commit_through(repo: Path):
    (repo / "src" / "thing.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    r = _git(repo, "commit", "-m", "thing: bump", check=False)
    assert r.returncode == 0, r.stderr


def test_hook_refuses_an_uncited_substrate_change(repo: Path):
    (repo / "SUBSTRATE.md").write_text("v0.5\n", encoding="utf-8")
    _git(repo, "add", "-A")
    r = _git(repo, "commit", "-m", "substrate: bump", check=False)
    assert r.returncode != 0
    assert "governance: refused" in r.stderr
    assert _git(repo, "log", "--format=%s").stdout.count("substrate: bump") == 0


def test_hook_allows_a_cited_substrate_change(repo: Path):
    (repo / "SUBSTRATE.md").write_text("v0.5\n", encoding="utf-8")
    _git(repo, "add", "-A")
    r = _git(repo, "commit", "-m", "substrate: v0.5 (decisions/0020)", check=False)
    assert r.returncode == 0, r.stderr


def test_hook_refuses_an_uncited_params_change(repo: Path):
    (repo / "params" / "costs.yaml").write_text("spread_bps: 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    r = _git(repo, "commit", "-m", "costs: cheaper", check=False)
    assert r.returncode != 0
    assert "params/costs.yaml" in r.stderr


def test_history_scan_finds_a_commit_that_slipped_past_the_hook(repo: Path):
    (repo / "SUBSTRATE.md").write_text("v0.6\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "substrate: sneak", "--no-verify")
    bad = gov.check_history(repo)
    assert len(bad) == 1
    assert "SUBSTRATE.md" in bad[0][1].owner_only


def test_hooks_installed_reports_the_truth(repo: Path):
    assert gov.hooks_installed(repo)
    _git(repo, "config", "--unset", "core.hooksPath")
    assert not gov.hooks_installed(repo)


def test_history_before_the_hook_is_not_judged_retroactively(tmp_path: Path):
    """The rule starts where the hook starts.

    Otherwise adding governance would fail `make check` on every commit the
    repo already has, and the first thing anyone would do is delete the check.
    """
    root = Path(__file__).resolve().parents[1]
    r = tmp_path / "old"
    (r / "scripts").mkdir(parents=True)
    (r / ".githooks").mkdir()
    (r / "decisions").mkdir()
    (r / "decisions" / "0020-x.md").write_text("# 0020\n", encoding="utf-8")
    (r / "SUBSTRATE.md").write_text("v0.1\n", encoding="utf-8")
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.com")
    _git(r, "config", "user.name", "t")

    # Two commits from before the rule existed, one of them changing the
    # constitution with no citation anywhere.
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "initial")
    (r / "SUBSTRATE.md").write_text("v0.2\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "substrate: v0.2, no citation, pre-rule")

    assert gov.enforcement_start(r) is None

    # The rule arrives.
    (r / "scripts" / "check_governance.py").write_text(
        (root / "scripts" / "check_governance.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (r / ".githooks" / "commit-msg").write_text(
        (root / ".githooks" / "commit-msg").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "governance: enforce SUBSTRATE section 2 at commit time")

    assert gov.enforcement_start(r) is not None
    assert gov.check_history(r) == []

    # And it bites from here on.
    (r / "SUBSTRATE.md").write_text("v0.3\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "substrate: v0.3", "--no-verify")
    assert len(gov.check_history(r)) == 1
