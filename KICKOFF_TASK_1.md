# Task 1 — Scaffold the Signal Lab (Phase 0)

Read `SUBSTRATE.md` in full before doing anything. It is the constitution
of this repository and every decision below is subordinate to it. If
anything in this task conflicts with `SUBSTRATE.md`, `SUBSTRATE.md` wins
and you stop and say so.

## What this task is

Build the skeleton of the lab so that, when real data arrives, we are
loading and running rather than writing code. **No real market data is
used in this task.** Every loader gets a synthetic backend that produces
panels with the same shape, ragged starts, missingness and frequency
breaks as the real vendors, and known planted properties so the harness
can be tested against ground truth.

Do not write any signal logic in this task. Do not run any experiment
that produces an information ratio. Hypotheses may be written; nothing
may be tested.

## Deliverables, in order

### 1. Repository and parameters
- Create the layout in `SUBSTRATE.md §15`. Python 3.12, `pyproject.toml`,
  pinned lock file. Dependencies: pandas, numpy, scipy, statsmodels, cvxpy
  (with an open-source solver; MOSEK optional behind a flag), pyarrow,
  plotly, pytest, hypothesis, pyyaml.
- Write `params/constraints.yaml`, `params/costs.yaml`, `params/vetoes.yaml`,
  `params/data.yaml`, `params/agents.yaml` from the values in `SUBSTRATE.md`.
  Every threshold and cost lives here and nowhere else. Add a
  `params_version` field and a loader that hashes the params directory.
- `.gitignore` excludes `data/raw/`, `data/snapshots/`, `results/artifacts/`,
  and any file matching `*key*` or `*.secret`. Secrets come from environment
  variables only.

### 2. Data layer with synthetic backend
- Define a single loader interface: `load_returns(snapshot_id) -> ReturnPanel`,
  `load_analytics(snapshot_id) -> AnalyticsPanel`,
  `load_macro(snapshot_id) -> VintagePanel`. Each panel carries per-series
  metadata: true daily start, tier, hedge flag, gross/net flag, splice record.
- `VintagePanel` is bitemporal: every observation has `real_date` and
  `knowledge_date`. Provide `as_of(knowledge_date)` that returns only what
  was knowable then.
- Implement the **loader invariants in `SUBSTRATE.md §5.1`** as functions
  with unit tests: business-day filter, per-series truncation at daily
  start, per-series prior-observation returns, no forward fill, splice
  application with a logged record, hedge-flag propagation, 2-day
  overlapping covariance for cross-region pairs.
- Implement the **holdout lock**: the loader raises on any request for
  dates ≥ `HOLDOUT_START`. There is no bypass flag. Test that it raises.
- Synthetic backend: generate a 100-series daily panel 1989–2019 with
  ragged starts drawn from the real coverage distribution (see the
  coverage CSVs in `data/universe/`), a subset that is month-end only
  before a break date, weekend/holiday gaps, six flagged hedged series,
  and a factor structure (5 latent factors) so cross-sectional signals
  have something to find. Provide a `plant()` helper that injects a known
  predictive relationship of chosen strength into a chosen family so
  phase 1 can verify recovery.

### 3. Results store
- SQLite schema from `SUBSTRATE.md §11`, append-only enforced with a
  trigger that rejects UPDATE and DELETE on `runs`, `metrics`, `verdicts`.
- Python API: `record_run()`, `record_metrics()`, `record_verdicts()`,
  `list_runs()`, `load_artifacts(run_id)`. Every run stores
  `params_version`, `data_snapshot_hash`, `seed`.
- Artifacts written as parquet under `results/artifacts/<run_id>/`.

### 4. Vetoes
- One function per veto in `SUBSTRATE.md §10`, signature
  `veto(run_context) -> Verdict(passed: bool, detail: str)`, thresholds
  read from `params/vetoes.yaml`. Tests for each: a passing case, a
  failing case, and a boundary case. The `lookahead` and `frequency`
  vetoes must be tested against the synthetic panel's known break dates.
- `apply_vetoes()` runs all of them, records all verdicts, and returns the
  first failure. Vetoes are evaluated **before** any return statistic is
  computed or displayed.

### 5. Hypothesis registry
- Parser and validator for the YAML template in `SUBSTRATE.md §7`,
  including `provenance`, `reference`, `data_required`, `proxy_for`.
  Missing direction or rationale → rejected. `literature` without a
  resolvable reference → rejected. Any `data_required` id not in the
  snapshot manifest → `blocked:data` and a request file written.
- `hypotheses/pending/`, `running/`, `done/` with a mover that records
  transitions in the results store.
- Write **ten** pre-registered hypotheses into `hypotheses/pending/`,
  at least one per family listed in `SUBSTRATE.md §6`, each with a real
  economic rationale. They will not be tested in this task. Do not look
  at any data to write them.

### 6. Render layer
- Port `views.py`, `static_report.py` and `mock_data.py` from the mock
  provided into `render/`. Replace `mock_data` reads with the results store
  API, keeping a `--synthetic` flag that regenerates the mock so the
  report can be built with no runs present.
- Add `streamlit_app.py` calling the same `views` functions. Entrypoint
  conventions for the internal deployment platform are unknown; leave a
  `DEPLOY.md` stub listing what needs confirming.

### 7. Agent budgets
- A wrapper around model calls that accumulates token usage from the API
  usage fields, kills the process at the ceiling in `params/agents.yaml`,
  and records cost per run in the results store. Test the kill path.

### 8. Scripts and CI
- `scripts/build_snapshot.py` (hash and freeze a panel),
  `scripts/nightly_cycle.py` (stub: load → for each pending hypothesis:
  validate → run → vetoes → record; budgets enforced; no signal logic yet),
  `scripts/digest.py` (write a short markdown digest of the last cycle).
- `pytest` passes. A `make check` runs tests, lint, and the holdout-lock
  test explicitly.

## How to work

- Small commits, each with a message saying what invariant it adds.
- When you hit a decision the substrate doesn't settle, write it as a
  question in `decisions/proposed/` and continue with the most
  conservative option. Do not invent thresholds.
- Prefer boring, testable code over clever code. This is a harness, not a
  library.
- At the end, write `STATUS.md`: what is built, what is stubbed, what is
  blocked, and the exact command to reproduce the synthetic report.

## Definition of done

`make check` passes; the synthetic report renders; the holdout lock is
tested; all ten vetoes have tests; ten hypotheses are registered; no real
data was touched; no IR was computed on anything but the planted synthetic
case, and that only as a smoke test, not as a result.
