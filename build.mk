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
#   make audit-halflife                          volatility-overlay halflife sweep, h4/13/26 x IC 0.35/0.70 x seeds 0-9 x halflife None/13/26/52 (240 cells, task 35)
#   make jpmaqs-pull                             THE OWNER RUNS THIS: set -a; source .env; set +a; make jpmaqs-pull (HANDOFF task 44)
#   make macro-snapshot                          freeze the newest raw JPMaQS pull as a macro snapshot
#   make jpmaqs-coverage                         coverage report from the macro snapshot -- dates and counts only
#   make jpmaqs-catalogue                        the 27 registered JPMaQS tickers against the vendor catalogue
#   make jpmaqs-candidates                       catalogue names sharing each unresolved ticker's cid and stem
#   make jpmaqs-name-search                      name search of the cached catalogue for H-2026-0004, 0005, 0010
#   make measurement-loadings                    the loading-estimator test, decisions/0046 (HANDOFF task 45); ARGS=--time-only to time it
#   make characteristics                         the estimated half of the characteristic map; stores huber6-v1 to v3, v3 is the one params/ names (HANDOFF tasks 51-53, decisions/0049, 0055)
#   make exposures-check                         walk every week of that store through resolve_exposures (HANDOFF task 54)
#   make fdr-study                                Monte Carlo: FDR vs FWER on the registry's shape, no engine runs (HANDOFF task 34)
#   make governance SUBSTRATE section 2, checked mechanically
#   make check         fast tier -- wiring checks only (HANDOFF task 37, OWNER-QUEUE D2)
#   make check-scoped  the definition of done: the whole suite unless every changed file can be placed, then only the slow tests it can reach (HANDOFF task 49)
#   make check-full    the whole suite, and the opening step of every audit
#   make test-slow     model-validity checks only: the engine, an optimiser solve, a Monte Carlo
#
# uv manages Python 3.12 and the locked dependency set; nothing is installed
# into the system interpreter. `make check-scoped` is the definition of done for
# any commit touching src/, scripts/, tests/, vetoes/ or params/; `make check`
# (the fast tier) is enough for HANDOFF.md, OWNER-QUEUE.md, decisions/,
# hypotheses/ or docs (HANDOFF task 37, OWNER-QUEUE D2).

# The virtualenv lives OUTSIDE the repo by default. This repo is normally
# checked out on the Windows filesystem and driven from WSL through /mnt/c,
# where 9p I/O makes building a venv of this size take minutes and `uv` cannot
# hardlink from its cache. Putting it on the Linux filesystem makes every uv
# operation fast; the source still lives on /mnt/c where git and your editor
# expect it. Override with UV_PROJECT_ENVIRONMENT=... if you keep the repo on a
# native Linux path.
.DEFAULT_GOAL := check
.PHONY: report cycle digest snapshot clean lock install help inspect-raw coverage universe audit audit-lean audit-baseline-pilot audit-baseline audit-knee audit-power audit-power10 audit-friction audit-friction-created audit-halflife jpmaqs-catalogue jpmaqs-candidates jpmaqs-name-search jpmaqs-pull macro-snapshot jpmaqs-coverage measurement-loadings describe-loadings describe-fit characteristics exposures-check exusd-analytics-coverage fx-check fdr-study impvol-coverage

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

install: ## sync the locked environment and install the commit hook
	uv sync --group dev
	git config core.hooksPath .githooks
	@echo "commit hook installed: owner-only changes must cite a decision"

lock: ## refresh uv.lock
	uv lock

# check-block: begin -- what defines the check; scripts/select_slow.py compares it with the base, and a change here means a full run
export UV_PROJECT_ENVIRONMENT ?= $(HOME)/.venvs/signal-lab
export UV_LINK_MODE ?= copy
# One thread is the reference configuration (decisions/0048): numbers repeat only there.
export OMP_NUM_THREADS = 1
export OPENBLAS_NUM_THREADS = 1
export MKL_NUM_THREADS = 1

PY := uv run --python 3.12
PYTEST := $(PY) --group dev pytest
PYTEST_ARGS ?=

# The governance check is stdlib-only on purpose, so it runs from the commit
# hook without the project virtualenv -- and, deliberately, without uv. A rule
# about who may change the constitution should not be the first thing to fall
# over on a shell that happens to have a thinner PATH.
PYSTD := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
GOV := $(PYSTD) scripts/check_governance.py


.PHONY: lint test test-fast test-slow holdout governance check check-full check-scoped

lint: ## ruff check and format check
	$(PY) --group dev ruff check src vetoes render scripts tests
	$(PY) --group dev ruff format --check src vetoes render scripts tests

test: ## the full suite
	$(PYTEST) -q $(PYTEST_ARGS)

test-fast: ## wiring checks only -- excludes slow (model-validity) and holdout (HANDOFF task 37)
	$(PYTEST) -q -m "not slow and not holdout" $(PYTEST_ARGS)

test-slow: ## model-validity checks only: the engine, an optimiser solve, a Monte Carlo (HANDOFF task 37)
	$(PYTEST) -q -m slow $(PYTEST_ARGS)

holdout: ## the holdout lock, run explicitly and by name
	@echo "--- holdout lock (SUBSTRATE sections 2 and 3) ---"
	$(PYTEST) -m holdout -v

governance: ## SUBSTRATE section 2: owner-only changes cite a decisions/ record
	@echo "--- governance (SUBSTRATE section 2) ---"
	@$(GOV) --history
ifndef CI
	@$(GOV) --hooks
endif

check: governance lint test-fast holdout ## fast tier: governance, lint, wiring checks, the holdout lock
	@echo
	@echo "make check: OK"

check-full: governance lint test holdout ## full tier: governance, lint, the WHOLE suite, the holdout lock
	@echo
	@echo "make check-full: OK"

check-scoped: governance lint ## the whole suite unless every changed file can be placed, then only the slow tests that can reach a change (HANDOFF task 49)
	@sel=$$(mktemp); \
	if ! $(PYSTD) scripts/select_slow.py >$$sel 2>&1; then echo "FULL: the selector failed" >$$sel; fi; \
	echo "--- selector (scripts/select_slow.py) ---"; cat $$sel; \
	if [ "$$(head -1 $$sel)" = SCOPED ]; then \
		picked=$$(awk '/^selected/{f=1;next} /^left out/{f=0} f&&/^  tests/{print $$1}' $$sel | paste -sd, -); \
		left=$$(awk '/^left out/{f=1;next} /^changed paths/{f=0} f&&/^  tests/{print $$1}' $$sel | paste -sd, -); \
		echo "check-scoped tier=SCOPED"; echo "check-scoped left out: $$left"; \
		$(PYTEST) -q -m "not holdout" --slow-only-in="$$picked" $(PYTEST_ARGS); rc=$$?; \
	else \
		echo "check-scoped tier=FULL"; \
		$(PYTEST) -q $(PYTEST_ARGS); rc=$$?; \
	fi; rm -f $$sel; [ $$rc -eq 0 ] || exit $$rc
	@$(MAKE) --no-print-directory -f $(firstword $(MAKEFILE_LIST)) holdout
	@echo
	@echo "make check-scoped: OK"
# check-block: end

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

audit-halflife: ## volatility-overlay halflife sweep, h4/13/26, IC 0.35/0.70, seeds 0-9, halflife None/13/26/52 -- 240 cells (HANDOFF task 35)
	$(PY) --group dev python scripts/run_audit.py --source bloomberg --grid halflife

audit: ## the ruler audit on the Bloomberg snapshot (decisions/0023); hours, not minutes
	$(PY) --group dev python scripts/run_audit.py --source bloomberg

jpmaqs-catalogue: ## the 27 registered JPMaQS tickers against the vendor catalogue -- metadata only (HANDOFF task 23)
	$(PY) --group dev python scripts/jpmaqs_catalogue_check.py

jpmaqs-candidates: ## catalogue names sharing each unresolved JPMaQS ticker's cid and xcat stem -- names only, no choice (HANDOFF task 27)
	$(PY) --group dev python scripts/jpmaqs_candidates.py

jpmaqs-name-search: ## name search of the cached JPMaQS catalogue for 0004, 0005, 0010 -- names only, no choice (HANDOFF task 29)
	$(PY) --group dev python scripts/jpmaqs_name_search.py

MACRO_SNAPSHOT ?= jpmaqs-macro-v1
PULL_ID ?=

jpmaqs-pull: ## the vendor pull -- THE OWNER RUNS THIS, with .env sourced in their own shell (HANDOFF task 44)
	$(PY) --group dev python scripts/jpmaqs_pull.py

macro-snapshot: ## freeze a raw JPMaQS pull as an immutable macro snapshot (HANDOFF task 44)
	$(PY) --group dev python scripts/build_macro_snapshot.py --id $(MACRO_SNAPSHOT) $(if $(PULL_ID),--pull-id $(PULL_ID))

jpmaqs-coverage: ## coverage report from the macro snapshot -- dates and counts only (HANDOFF task 44)
	$(PY) --group dev python scripts/jpmaqs_coverage.py --id $(MACRO_SNAPSHOT)

measurement-loadings: ## six factors, rolling OLS against four candidate estimators, one report (HANDOFF task 45, decisions/0046)
	$(PY) --group dev python scripts/run_measurement.py $(ARGS)

exusd-analytics-coverage: ## true daily start per ticker and field of the ex-USD analytics file (HANDOFF task 52, decisions/0052)
	$(PY) --group dev python scripts/build_exusd_analytics_coverage.py

impvol-coverage: ## coverage of the implied-vol file by lab id: first and last Friday, stale weeks removed (HANDOFF task 59, decisions/0061)
	$(PY) --group dev python scripts/impvol_coverage.py

exposures-check: ## every store week through resolve_exposures: counts, means and the usage log (HANDOFF task 54, decisions/0055)
	$(PY) --group dev python scripts/check_exposures.py $(if $(ARGS),$(ARGS))

fx-check: ## converted NDDLUK against NDDUUK, weekly, same day and lagged: the FX conversion's own check (HANDOFF task 53, decisions/0053)
	$(PY) --group dev python scripts/check_fx_conversion.py

characteristics: ## the estimated half of the characteristic map: Huber loadings on six factors, walk-forward, plus the measured cells (HANDOFF task 51, decisions/0049)
	$(PY) --group dev python scripts/build_characteristics.py $(if $(ARGS),$(ARGS))

describe-loadings: ## how stable each estimator's loadings are, a description not a test (HANDOFF task 48); RUN=M-... for another run
	$(PY) --group dev python scripts/describe_loadings.py stability $(if $(RUN),--run $(RUN))

describe-fit: ## how well the loadings predict at all, plus predicted_vs_actual.html (HANDOFF task 48); RUN=M-... for another run
	$(PY) --group dev python scripts/describe_loadings.py fit $(if $(RUN),--run $(RUN))

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
