# Signal Lab build rules.
#
# Shipped as build.mk because the file-transfer bridge refuses to write a file
# named Makefile (make files can execute arbitrary commands). Make Makefile a
# one-line stub, once, and it never needs copying again:
#
#     printf 'include build.mk\n' > Makefile
#
# From bash, not PowerShell: PowerShell's `>` writes UTF-16 with CRLF, and make
# rejects both ("NUL character seen", then "missing separator").
#
# Or run it in place without renaming:  make -f build.mk check
#
#   make inspect-raw describe the shape of data/raw/, structure only
#   make coverage   rebuild the coverage table from the workbook's Index Map
#   make universe   rebuild the investable universe from the coverage table
#   make report     render the synthetic report
#   make cycle      build a synthetic snapshot and run one cycle
#   make governance SUBSTRATE section 2, checked mechanically
#
# uv manages Python 3.12 and the locked dependency set; nothing is installed
# into the system interpreter. `make check` is the definition of done.

# The virtualenv lives OUTSIDE the repo by default. This repo is normally
# checked out on the Windows filesystem and driven from WSL through /mnt/c,
# where 9p I/O makes building a venv of this size take minutes and `uv` cannot
# hardlink from its cache. Putting it on the Linux filesystem makes every uv
# operation fast; the source still lives on /mnt/c where git and your editor
# expect it. Override with UV_PROJECT_ENVIRONMENT=... if you keep the repo on a
# native Linux path.
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/signal-lab
export UV_LINK_MODE ?= copy

PY := uv run --python 3.12
PYTEST := $(PY) --group dev pytest

# The governance check is stdlib-only on purpose, so it runs from the commit
# hook without the project virtualenv -- and, deliberately, without uv. A rule
# about who may change the constitution should not be the first thing to fall
# over on a shell that happens to have a thinner PATH.
PYSTD := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
GOV := $(PYSTD) scripts/check_governance.py

.DEFAULT_GOAL := check
.PHONY: check lint test holdout governance report cycle digest snapshot clean lock install help inspect-raw coverage universe

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

install: ## sync the locked environment and install the commit hook
	uv sync --group dev
	git config core.hooksPath .githooks
	@echo "commit hook installed: owner-only changes must cite a decision"

lock: ## refresh uv.lock
	uv lock

lint: ## ruff check and format check
	$(PY) --group dev ruff check src vetoes render scripts tests
	$(PY) --group dev ruff format --check src vetoes render scripts tests

test: ## the full suite
	$(PYTEST) -q

holdout: ## the holdout lock, run explicitly and by name
	@echo "--- holdout lock (SUBSTRATE sections 2 and 3) ---"
	$(PYTEST) -m holdout -v

governance: ## SUBSTRATE section 2: owner-only changes cite a decisions/ record
	@echo "--- governance (SUBSTRATE section 2) ---"
	@$(GOV) --history
ifndef CI
	@$(GOV) --hooks
endif

check: governance lint test holdout ## governance, lint, tests, and the holdout lock
	@echo
	@echo "make check: OK"

report: ## render the synthetic report to leaderboard.html
	$(PY) --group dev python render/static_report.py --synthetic -o leaderboard.html

coverage: ## rebuild bbg_index_coverage.csv from the Index Map (decisions/0022)
	$(PY) --group dev python scripts/build_coverage.py

universe: ## rebuild investable_universe.csv from the coverage table
	$(PY) --group dev python scripts/build_universe.py

inspect-raw: ## describe data/raw/ -- sheet names, headers, dimensions, date ranges; no values
	$(PY) --with openpyxl python scripts/inspect_raw.py

snapshot: ## build the synthetic snapshot
	$(PY) --group dev python scripts/build_snapshot.py --id synthetic-v1 --overwrite

cycle: snapshot ## one nightly cycle against the synthetic snapshot
	$(PY) --group dev python scripts/nightly_cycle.py --snapshot synthetic-v1

digest: ## write results/digest.md from the last cycle
	$(PY) --group dev python scripts/digest.py -o results/digest.md

clean: ## remove build output, keep the store and snapshots
	rm -rf .pytest_cache .ruff_cache leaderboard.html
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
