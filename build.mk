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
#   make audit      the ruler audit on real data (decisions/0023, phase 2.5)
#   make audit-lean the same, two ICs and one seed -- shape and runtime only
#   make audit-baseline-pilot / audit-baseline   the block-shuffled baseline cells (decisions/0036)
#   make audit-knee                              live + baseline at IC 0.35/0.50/0.70, h13 (60 cells)
#   make audit-friction-created                  the same 60 cells priced with the created-turnover shadow (task 36)
#   make audit-friction                          live cells at shadow-cost 10/20/40 bp x IC 0.35/0.70 x seeds 0-9 -- 60 cells
#   make audit-power10                           span-limited score shuffles, IC 0.70 x seeds 0-9 x 20 perms, h13 (200 cells)
#   make audit-power                             score-shuffle baselines, IC 0.35/0.70 x seeds 0/1 x 20 perms, h13 (80 cells)
#   make jpmaqs-catalogue                        the 27 registered JPMaQS tickers against the vendor catalogue
#   make jpmaqs-candidates                       catalogue names sharing each unresolved ticker's cid and stem
#   make jpmaqs-name-search                      name search of the cached catalogue for H-2026-0004, 0005, 0010
#   make fdr-study                                Monte Carlo: FDR vs FWER on the registry's shape, no engine runs (HANDOFF task 34)
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
.PHONY: check lint test holdout governance report cycle digest snapshot clean lock install help inspect-raw coverage universe audit audit-lean audit-baseline-pilot audit-baseline audit-knee audit-power audit-power10 audit-friction audit-friction-created jpmaqs-catalogue jpmaqs-candidates jpmaqs-name-search fdr-study

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

audit-lean: ## the ruler audit on the SYNTHETIC panel, small grid (validation)
	$(PY) --group dev python scripts/run_audit.py --source synthetic --lean

audit-baseline-pilot: ## block-shuffled baseline, h13 only, 40 cells (decisions/0036)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid baseline-pilot

audit-baseline: ## block-shuffled baseline, every horizon, 160 cells (decisions/0036)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid baseline

audit-knee: ## live + baseline at IC 0.35/0.50/0.70, h13 only, 60 cells (HANDOFF task 20)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid knee

audit-power: ## score-shuffle baselines, IC 0.35/0.70, seeds 0/1, 20 perms, h13 -- 80 cells (HANDOFF task 25)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid power

audit-friction-created: ## shadow priced at the turnover a trade creates, IC 0.35/0.70, seeds 0-9, coefficient 10/20/40 -- 60 cells (HANDOFF task 36)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid friction_created

audit-power10: ## span-limited score shuffles, IC 0.70, seeds 0-9, 20 perms, h13 -- 200 cells (HANDOFF task 30)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid power10

audit-friction: ## shadow-cost 10/20/40 bp, IC 0.35/0.70, seeds 0-9, live cells only -- 60 cells (HANDOFF task 32)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid friction

audit: ## the ruler audit on the Bloomberg snapshot (decisions/0023); hours, not minutes
	$(PY) --group dev python scripts/run_audit.py --source bloomberg

jpmaqs-catalogue: ## the 27 registered JPMaQS tickers against the vendor catalogue -- metadata only (HANDOFF task 23)
	$(PY) --group dev python scripts/jpmaqs_catalogue_check.py

jpmaqs-candidates: ## catalogue names sharing each unresolved JPMaQS ticker's cid and xcat stem -- names only, no choice (HANDOFF task 27)
	$(PY) --group dev python scripts/jpmaqs_candidates.py

jpmaqs-name-search: ## name search of the cached JPMaQS catalogue for 0004, 0005, 0010 -- names only, no choice (HANDOFF task 29)
	$(PY) --group dev python scripts/jpmaqs_name_search.py

fdr-study: ## Monte Carlo: FDR vs FWER on the registry's shape -- no engine runs (HANDOFF task 34)
	$(PY) --group dev python scripts/fdr_vs_fwer.py

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
