# Signal Lab build rules.
#
# Shipped as build.mk because the file-transfer bridge refuses to write a file
# named Makefile (make files can execute arbitrary commands). To get `make check`
# working, one command from the repo root:
#
#     cp build.mk Makefile
#
# Or run it in place without renaming:  make -f build.mk check
#
# Applying patches/*.patch with `git am` creates the real Makefile for you.
#
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
# Stdlib only, so it runs from the commit hook without the project venv.
GOV := $(PY) python scripts/check_governance.py

.DEFAULT_GOAL := check
.PHONY: check lint test holdout governance report cycle digest snapshot clean lock install help

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

snapshot: ## build the synthetic snapshot
	$(PY) --group dev python scripts/build_snapshot.py --id synthetic-v1 --overwrite

cycle: snapshot ## one nightly cycle against the synthetic snapshot
	$(PY) --group dev python scripts/nightly_cycle.py --snapshot synthetic-v1

digest: ## write results/digest.md from the last cycle
	$(PY) --group dev python scripts/digest.py -o results/digest.md

clean: ## remove build output, keep the store and snapshots
	rm -rf .pytest_cache .ruff_cache leaderboard.html
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
