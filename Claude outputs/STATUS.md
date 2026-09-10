# STATUS — end of Task 1 (Phase 0)

Written 2026-09-07. Read `SUBSTRATE.md` first; it governs everything below.

**No real market data was touched.** The Bloomberg workbook and the FRED panel
in `data/raw/` were never opened. The only files read from `data/universe/` are
the coverage tables, and only for the distribution of first-daily dates used to
give the synthetic panel realistic ragged starts. No ticker's values were read.

**No information ratio was computed.** Not on synthetic data either. The planted
relationship in `plant()` is verified by rank IC, which is what phase 1 needs;
the walk-forward engine that would produce an IR does not exist.

## Reproduce the synthetic report

```bash
cd /mnt/c/AI/signal-lab          # from WSL
cp build.mk Makefile             # once, see the note below
uv sync --group dev
make check                       # lint, 191 tests, holdout lock by name
make report                      # writes leaderboard.html
```

The Makefile ships as `build.mk`: the file-transfer bridge refuses to write a
file named `Makefile`, since make files can execute arbitrary commands. Copy it
once as above, or run `make -f build.mk check` in place. Applying
`patches/*.patch` with `git am` creates the real `Makefile` for you.

The full phase 0 loop, including a snapshot and one cycle:

```bash
make cycle                       # build synthetic-v1, run the cycle
make digest                      # results/digest.md
```

`make check` is the definition of done and currently passes: ruff clean,
191 tests, the 11 holdout-lock tests run explicitly by name.

## What is built and working

**Params.** `params/{constraints,costs,vetoes,data,data_sources,agents}.yaml`.
Every threshold and cost in the lab lives there and nowhere else; `src/params.py`
loads them, checks the six files agree on `params_version`, and hashes the
directory. That hash travels with every run.

`data_sources.yaml` was not in the task's list of five but SUBSTRATE section 2
requires it ("call any external API not listed in `params/data_sources.yaml`"),
so it exists.

**Data layer.** One interface — `load_returns`, `load_analytics`, `load_macro` —
with a synthetic backend and three vendor backends that raise a clear "lands in
phase N" rather than returning an empty panel. Panels carry per-series metadata:
true daily start, tier, hedge flag, gross/net flag, splice record, region.

`VintagePanel` is bitemporal. `as_of(knowledge_date)` returns the latest vintage
published on or before that date, and `usage_log()` produces what the lookahead
veto reads, so a signal cannot fail to declare a peek.

All seven loader invariants of section 5.1 are functions with tests, including
the one that matters most: `returns_from_prior_observation` measures each
series' return against its own last observation, not the previous row. The test
shows `pct_change()` silently losing a real return across a gap.

**Holdout lock.** `enforce_holdout` raises on any date on or after 2020-01-01,
is called at every loader entry point, and has no bypass argument anywhere —
asserted by a test that inspects every signature in the module for `force`,
`bypass`, `override` and friends. Unlocking requires `unlocked_by` and
`unlocked_on` to be set, or it still refuses.

**Synthetic backend.** 100 series, 1989-01-02 to 2019-12-27, ~7,900 business
days. Ragged starts drawn from the real coverage distribution (tiers come out
76/11/13 against the real 75/12/10). Twelve series are month-end only before a
break date. Six flagged hedged. Weekend and holiday gaps plus idiosyncratic
single-day gaps so gaps are not aligned across series. Five latent factors with
persistent volatility, so cross-sectional signals have structure to find and
regime models have regimes.

`plant()` injects a known predictive relationship. Calibration check: a planted
IC of 0.05 recovers at 0.051 on the planted panel and 0.005 on the unplanted
one.

**Results store.** SQLite, append-only enforced by triggers on `runs`, `metrics`
and `verdicts` — an `UPDATE` or `DELETE` is an error at the database, not a
convention. Every run records `params_version`, `params_hash`,
`data_snapshot_hash` and `seed`. Artifacts are parquet under
`results/artifacts/<run_id>/`. `list_runs()` deliberately offers no `order_by`.

**Vetoes.** All ten of section 10, one function each, thresholds from params,
each with a passing, failing and boundary test. `lookahead` and `frequency` are
tested against the synthetic panel's known break dates and against the real
mistake — treating `real_date` as the knowledge date. `apply_vetoes` records
every verdict and returns the first failure in the configured order; a veto that
raises is recorded as a failure, never skipped. A veto with a missing input
FAILS: fail-open would put an unmeasured run on the leaderboard.

**Hypothesis registry.** Parser and validator for the section 7 template.
Missing direction or rationale is rejected; a rationale under 120 characters is
rejected; `literature` without a resolvable reference is rejected. Eleven
hypotheses registered in `hypotheses/pending/`, one per family. `pending →
running → done` with transitions recorded in the store. Missing series produce
`blocked:data` and a request file.

**Render layer.** `views.py` holds every figure; `static_report.py` and
`streamlit_app.py` both consume it, and a test asserts the Streamlit app grows
no figure code of its own. Sources are the results store or, behind
`--synthetic`, the regenerated mock — which renders a banner that cannot be
switched off. Section 12's constraints are tested, not trusted: one sort, failed
runs visible with their veto, gross IR nowhere in the document, no holdout
metric while locked. An empty store renders a real report saying so.

**Budgets.** Token usage read from the API's own usage fields including cache
reads; kill at the ceiling, with the killer injected so the kill path is tested
without killing pytest. Cost recorded per run. A response with no usage field is
refused, because an uncounted call is an uncapped call.

**Scripts.** `build_snapshot.py` (freeze and hash, with `--verify`),
`nightly_cycle.py`, `digest.py`. `make check` runs lint, tests and the holdout
lock explicitly.

## What is stubbed

| Thing | Where | Lands in |
|---|---|---|
| `run_experiment()` — walk-forward engine, cost model, long-only solver | `scripts/nightly_cycle.py` | phase 1 |
| `src/signals/`, `src/portfolio/`, `src/stats/` | empty packages | phases 1–3 |
| Romano-Wolf stepdown, block bootstrap, HAC, search null, deflated IR | `src/stats/` | phase 3 |
| Bloomberg loader | `src/loaders/bloomberg.py` | phase 2 |
| FRED loader | `src/loaders/fred.py` | phase 2 |
| JPMaQS loader | `src/loaders/jpmaqs.py` | phase 3 |
| HTTP reference resolver | `harness/hypotheses.py` | when a host is allowlisted |

The `multiple_testing` veto is complete as a veto: it reads a stepdown verdict
and checks it was produced at the configured alpha by the configured procedure.
What it cannot do is produce that verdict, because the stepdown needs the joint
distribution of every test statistic in a cycle. Until `src/stats/` lands the
veto fails closed, which is correct.

## What is blocked

1. **Agent budget numbers — blocking phase 4.** `decisions/proposed/0007`.
   SUBSTRATE section 14 requires hard ceilings and states no numbers; inventing
   them is forbidden. All six are `null` and the wrapper refuses to make a model
   call. Six numbers are needed. Nothing else is blocked by this: the cycle's
   deterministic steps run and report "model roles: disabled".

2. **All eleven hypotheses are `blocked:data`.** Expected. They need real vendor
   series and the only snapshot is synthetic. Eleven request files are in
   `data/requests/`. They clear in phases 2 and 3.

3. **The search gate is closed.** SUBSTRATE section 5.6: no search until JPMaQS
   is in. `scripts/nightly_cycle.py` prints this on every run.

4. **Ten open questions** in `decisions/proposed/`. The conservative option was
   taken in each and the reasoning written down. Worth your attention:
   - `0003` — the TE veto reads the *worst* trailing-3y value. Section 4's
     "asymmetric penalty, not a hard band" and section 10's hard ceiling pull
     apart, and the choice of statistic decides how far.
   - `0007` — the budget numbers, above.
   - `0009` — section 6 lists **eleven** families; the task asked for **ten**
     hypotheses with at least one per family. Not jointly satisfiable. Eleven
     were written, since coverage is the substantive rule and the count is not.
   - `0004` — gross IR was removed from the report entirely, not just from
     charts. Reversible if you want the cost drag visible.

## Two things worth knowing

**No hypothesis claims a citation.** All eleven are `provenance: adaptation`
with no `reference`. Several of these effects have real literatures, but no
reference resolver is enabled, so nothing could be verified, and writing DOIs
from memory is exactly how a fabricated citation enters a registry — which
section 7 calls a failure of the proposer. Re-register the relevant ones as
`literature` once a resolver host is allowlisted in `params/data_sources.yaml`.

**A phase 0 cycle records `blocked:no_engine`, not a veto failure.**
`decisions/proposed/0011`. With no engine there is no run context, and the
vetoes would all fail closed — putting "killed by lookahead" into an append-only
store when the real cause is that phase 1 has not happened. The store cannot be
corrected, so the status names the actual reason.
