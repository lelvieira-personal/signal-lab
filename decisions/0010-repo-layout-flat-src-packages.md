# 0010 — Flat top-level packages under src/

Status: proposed, 2026-09-07, agent. Blocking: no.

## Question

SUBSTRATE section 15 lays out `src/loaders/`, `src/signals/`, `src/harness/`,
`src/portfolio/`, `src/stats/` — top-level package names with no project
namespace. Imports therefore read `from loaders.synthetic import ...` and
`import stats`.

`stats` in particular is a plausible name for a third-party package, so a
future dependency could shadow it depending on sys.path order.

## What was done

The substrate's layout, exactly. `pyproject.toml` sets
`[tool.pytest.ini_options] pythonpath = ["src", "."]` and scripts bootstrap via
`scripts/_bootstrap.py`; nothing is pip-installed, so `[tool.uv] package =
false`.

## Why that way

SUBSTRATE wins over an engineering preference. The alternative — a
`src/signal_lab/` namespace package — is more robust but would be an agent
editing the layout the constitution specifies, which section 2 forbids.

## What to decide

Whether to keep it. If a shadowing collision ever occurs, the fix is a
namespace package and an amendment to section 15, not a sys.path trick.

---
## Owner decision (2026-09-09, Leo)

Amend the constitution. Packages move under `src/signal_lab/`, which the owner
judged better engineering practice than flat top-level packages.

Note on spelling: the owner wrote `src/signal-labs/`. A hyphen is not legal in
a Python module name and the plural is inconsistent with the repository name,
so the package is `signal_lab`.

Scope of the move: everything that was under `src/` (`params.py`, `loaders/`,
`harness/`, `results/`, `signals/`, `portfolio/`, `stats/`). `vetoes/` and
`render/` stay at the top level, where SUBSTRATE section 15 puts them and where
`vetoes/` being adjacent to `params/` signals its owner-only status.

SUBSTRATE section 15 is to be amended; recorded in
`decisions/0100-substrate-amendments.md`.

Status: **closed**, pending the SUBSTRATE edit.
