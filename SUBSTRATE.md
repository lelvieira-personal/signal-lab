# SUBSTRATE — Signal Lab

Status: v0.2, 2026-09-07. Owner: Leo. This document is the constitution of
the lab. Agents read it at the start of every task. Agents never edit it.
Changes are made by the owner, versioned, and recorded in `decisions/`.

---

## 1. Purpose

Find a weekly-rebalanced, long-only, ETF-implementable multi-asset model
that allocates across duration, credit quality, region, sector, style,
real-vs-nominal and cash, driven by a wide set of macro and market signals,
and that delivers a satisfactory **net-of-cost information ratio against a
50/50 equity/bond benchmark**.

This is a personal research lab. It uses index, macro and market data only.
No client data, no positions, no PII, ever.

This is not an SAA. Decisions are made at the instrument level and roll up
to exposures; nothing here sets sleeve weights directly.

---

## 2. What agents may and may not do

Agents MAY:
- Propose hypotheses into `hypotheses/pending/` using the template in §7.
- Write and test code under `src/`, `tests/`, `scripts/`.
- Run experiments through `run_experiment()` and only through it.
- Read the development window and everything in `data/` except the holdout.
- Write to the results store via the harness API.
- Kill their own runs when a budget or veto fires.

Agents MAY NOT:
- Read, load, or compute anything on dates after `HOLDOUT_START`.
  The loader refuses these dates; do not work around it.
- Edit `SUBSTRATE.md`, `params/*.yaml`, or anything under `vetoes/`.
- Change a veto threshold, a cost assumption, or the objective to make a
  run pass. If a threshold looks wrong, write a note in `decisions/proposed/`
  and stop.
- Select among runs by any criterion other than the pre-registered objective.
- Delete or rewrite rows in the results store. It is append-only.
- Splice month-end and daily observations into one return series.
- Forward-fill any data gap.
- Exceed the token or iteration budgets in `params/agents.yaml`.
- Call any external API not listed in `params/data_sources.yaml`.

If a task cannot be completed inside these rules, the correct output is a
short note explaining why, not a workaround.

---

## 3. The objective, pre-registered

Primary metric: **net information ratio** of the strategy's active return
versus the 50/50 benchmark over the development window, after the cost
model in §8 and an ETF fee-and-tracking drag per instrument.

Gross IR is recorded and never used for ranking.

Development window: `DEV_START` to `DEV_END` (params; v0.2: 2001-01-05 to
2019-12-27). Holdout: `HOLDOUT_START` = **2020-01-01** onward, locked. It is opened once, by the owner, on the
single candidate taken toward production, and the unlock is written to
`decisions/`.

Multiplicity is the central risk of this lab. The search tests many
signals; the best observed IR is a maximum over draws. Every reported IR
is accompanied by its position in the search null (§9). A run whose IR is
not distinguishable from that null is not a result.

---

## 4. Constraints (all parameters, see `params/constraints.yaml`)

| Constraint | v0.1 value |
|---|---|
| Direction | Long-only, no leverage |
| Cash | 0–20% of NAV |
| Positions | ≤ 30 instruments with non-zero weight |
| Turnover | ≤ 150% annualised (target reduction to 100% later) |
| Tracking error | ≤ 6.0% trailing 3y; episodic excursions allowed, not rewarded on average |
| Rebalance | Weekly, Friday close; alternates tested by averaging over Tue/Wed/Fri |
| Benchmark | 50/50 MSCI ACWI net TR (`NDUEACWF`) / Bloomberg Global Aggregate unhedged USD (`LEGATRUU`), rebalanced with the strategy; pre-1999 extended with `MXWO` and `SBWGU` (see §5.6) |
| FX | Unhedged USD by default; hedged series exist for a subset and are a separate axis, off in v0.1 |

TE handling: an asymmetric penalty, not a hard band. TE is cheap when
conviction dispersion is high and expensive when it is not.

---

## 5. Universe and data

### 5.1 Return series (Bloomberg, `TOT_RETURN_INDEX_GROSS_DVDS`)

107 index series across: cash, US Treasury maturity buckets, international
government, inflation-linked, credit (IG, HY, rating buckets, Euro, MBS,
loans, EM USD sovereign and corporate, EM local), US equity by size, DM and
EM regions, 22 US and European GICS sectors, styles for US/EAFE/World-ex-US/EM,
real assets, plus a hedged overlay tab. Index-to-ETF mapping is in
`data/universe/index_etf_map.csv` (owner-maintained).

**Loader invariants** — these are enforced in code and tested:

1. Drop non-business days. `#N/A` is missing, never zero, never carried.
2. Each series is truncated at its **true daily start** (Index Map column
   "First daily date"). Month-end observations before that date are not
   part of the daily panel. If pre-daily history is needed, it is a
   separate monthly panel, never spliced.
3. Returns are `level_t / level_prev_obs - 1` per series, using each
   series' own prior observation, not the prior row.
4. Series are gross total return. `NDDU`/`M1` MSCI series are net of
   withholding; note the mismatch, do not correct it in v0.1.
5. Known substitutions, applied in the loader with a logged splice record:
   `LT13TRUU` → `G3OC` (3-7y Treasury, ICE BofA, daily from 1986-11);
   `SPBDALB` (price index) → total-return loan index when available;
   `MXUS0RE` (discontinued 2023-05) → `MXUS0RL`.
6. Six series in the base tab are already USD-hedged (`H09122US`,
   `H12823US`, `BTSYTRUH`, `H02549US`, `LP01TRUH`, `M0JPHUSD`). They carry a
   hedge flag and are not mixed with unhedged peers in a region signal.
7. Non-synchronous closes: cross-region covariance is estimated on
   2-day overlapping returns. Same-day daily correlation across regions is
   biased low and is not used for optimisation.

### 5.2 Tiers by daily history

| Tier | Daily start | Role |
|---|---|---|
| Backbone | ≤ 2001 | Estimation, covariance, regime models, signal tests |
| Second | 2002–2009 | Signal tests from own start; covariance via factor map before |
| Tradable-only | ≥ 2010 | In the universe for implementation; loadings inherited from the factor map; never used to estimate a signal |

Tier assignment is in the coverage table; the loader reads it, agents do
not override it.

### 5.3 Characteristics and market signals (Bloomberg analytics tab)

Daily index OAS, yield-to-worst and effective duration on the fixed income
universe (spreads from 2003, yields from 1989–1997, durations from 1997);
companion OAS/yield tickers extending IG and HY spreads to 2001. MOVE
(1988), GS and Bloomberg US financial conditions (1990), DE/GB/JP 2y and
10y yields (1989–1994), DXY (1971), BBDXY (2005), 10y and 2y breakevens
(1999/2005), 10y TIPS yield (1997).

OAS on Treasury buckets is zero by construction and is dropped. OAD on
Treasury buckets is kept: it is the duration axis of the characteristic
map and converts yield views to return views.

### 5.4 FRED (`params/data_sources.yaml`, key supplied by owner)

US Treasury curve 3m/2y/5y/10y/30y, 5y and 10y TIPS real yields, 5y/10y
and 5y5y breakevens, fed funds, SOFR, VIX, Chicago Fed NFCI/ANFCI (weekly),
St Louis Fed stress index (weekly), economic policy uncertainty (daily),
broad/AFE/EM dollar indices (2006), WTI and Brent.

FRED's ICE BofA spread series start 2023-09 and are **not used**. Spreads
come from Bloomberg.

### 5.5 Benchmark

50/50 `NDUEACWF` / `LEGATRUU`, both USD, both daily from 1999. Extended
before 1999-01-01 with `MXWO` (developed only, gross dividends) and `SBWGU`
(sovereign only, no credit). The splice is recorded; results that depend on
pre-1999 benchmark history say so. Note: the bond leg is **unhedged**, so
benchmark volatility includes FX. Whether production benchmarks hedged or
unhedged is to be confirmed by the owner; `LEGATRUH` is the alternative.

### 5.6 Macrosynergy / JPMaQS (pending)

Point-in-time macro. Pull list in `data/jpmaqs/request.txt`. Every ticker
carries `value`, `grading`, `eop_lag`. Grade-3 vintages are downweighted
or excluded per `params/data.yaml`. Legacy euro-area prefixes (`DEM_`,
`FRF_`, `ITL_`, `ESP_`, `NLG_`) are mapped to countries in the loader.

Until JPMaQS lands, **no signal search runs**. Price-only signal families
(trend, carry, vol) are not tested in isolation first; the search opens
only when the full signal set is in. This is deliberate: a leaderboard
built on price signals alone would tacitly decide what works before the
macro block is tested.

---

## 6. Signal architecture

Signals are organised into **families**. Selection happens at the family
level; within a family, signals are averaged, not picked.

| Family | Frequency block | Examples |
|---|---|---|
| Growth | slow (monthly, vintage-dated) | intuitive GDP, mfg confidence, unemployment gap |
| Inflation | slow | core CPI trend, inflation expectations |
| Policy / real rates | slow | real policy rate, real 5y IRS yield, term premium |
| Credit conditions | slow | private credit growth, bank lending surveys |
| Liquidity / money | slow | real broad money, financial conditions |
| Terms of trade / external | slow | commodity ToT, fiscal trajectory |
| Spreads & curve | fast (daily) | OAS levels and changes, 2s10s, breakevens, real yields |
| Volatility & stress | fast | VIX, MOVE, FCIs, stress indices |
| Trend / momentum | fast | multi-horizon price trend, cross-sectional momentum |
| Carry | fast | duration carry, credit carry, equity carry |
| Valuation | slow | index P/B, P/E, yield gaps |

Rules:
- Slow-block signals are held constant between releases at their vintage
  value. Weekly rebalancing does not resample them.
- Fast-block signals may move weekly. Turnover is expected to concentrate
  here and is charged accordingly.
- Every signal is scored two ways: **cross-sectional** (relative tilts
  within an axis; expressible long-only) and **directional** (timing an
  axis; requires cash and is expected to be weaker). Both are reported.
- Views are formed in **exposure space** (duration, credit, region,
  sector, style, real/nominal, cash) and mapped to ETF weights by solving
  for the long-only portfolio whose exposures best match the view, subject
  to §4. The characteristic map is in `data/characteristics/`.
- Aggregation rule for v0.1 is shrunk z-score averaging across families.
  Entropy-weighted and BL-view-vector aggregation are registered
  alternatives, tested against that baseline, not instead of it.

---

## 7. Hypothesis pre-registration

Every experiment starts as a file in `hypotheses/pending/`, written
before any result is seen:

```yaml
id: H-2026-0001
family: policy_rates
signal: real_policy_rate_change_3m
direction: negative          # higher real policy rate -> lower duration exposure
target_axis: duration
rationale: >
  One paragraph of economics. Why should this predict that, at this horizon,
  in a way that survives the long-only constraint?
horizon_weeks: 4-13
expected_expression: cross_sectional | directional | both
proposed_by: agent | owner
```

Two more required fields:

```yaml
provenance: literature | adaptation | novel
reference: doi-or-url          # required for literature; harness fetches it
data_required: [list of series ids the signal needs]
```

`literature` means a specific, reputable, peer-reviewed or equivalent
source. The harness fetches the reference and rejects the hypothesis if it
cannot be resolved; a fabricated citation is a failure of the proposer,
logged as such. `adaptation` is a known effect re-expressed for long-only
ETFs at weekly frequency. `novel` is allowed, quota-limited per cycle in
`params/agents.yaml`, and tracked separately so its survival rate is visible.

**Data the lab does not have.** If any series in `data_required` is not
in the snapshot, the run is marked `blocked:data` and a request is written
to `data/requests/<hypothesis_id>.yaml` with source, series, fields, and
reason. The agent may propose a proxy, but the hypothesis must declare it
(`proxy_for:`), and proxy runs are tagged and excluded from the main
leaderboard. Silent substitution fails the `coverage` veto.

Hypotheses without a stated direction and rationale are rejected by the
harness before running. A hypothesis whose result contradicts its stated
direction is recorded as a failure, not flipped.

---

## 8. Cost model (`params/costs.yaml`)

Per unit of turnover, half-spread plus fee-and-tracking drag. v0.1 placeholders,
to be revised against live ETF data:

| Bucket | Half-spread (bps) | Annual fee+tracking drag (bps) |
|---|---|---|
| Treasuries, T-bills, US large-cap equity | 5 | 5 |
| IG credit, sectors, DM regions, styles | 10 | 15 |
| HY, EM equity and debt, loans, real assets | 20 | 35 |

Net return = gross − turnover × half-spread − drag/52 per week. All
reported performance is net. Gross is stored for diagnostics only.

---

## 9. Statistical discipline

- All standard errors are HAC (Newey-West, lag chosen by horizon) because
  weekly observations of slow signals overlap heavily.
- Confidence intervals and the search null come from a **block bootstrap**
  on the daily panel, block length ≥ the longest signal horizon.
- The **search null** is the distribution of the maximum IR obtained by
  running the same search on signals with destroyed information
  (block-shuffled in time, structure preserved). Every leaderboard IR is
  reported with its percentile in this distribution. Deflated Sharpe/IR is
  reported alongside.
- Effective sample size is counted in macro cycles, not observations.
  Daily sampling of a slow signal does not increase it; the harness
  reports it.
- Seed stability: each run is repeated across resampling seeds; the IR
  range across seeds is itself a veto (§10).
- Alternative rebalance days are averaged, not selected.

---

## 10. Vetoes (`vetoes/`, thresholds in `params/vetoes.yaml`)

Boolean functions, applied to every run, evaluated before any return
statistic is shown. Failing any one kills the run with the reason logged.

| Veto | v0.1 threshold |
|---|---|
| turnover | annualised ≤ 150% |
| cash | max weight ≤ 20% |
| tracking_error | trailing-3y TE ≤ 6.0% |
| positions | ≤ 30 non-zero |
| coverage | signal available for ≥ 80% of the estimation universe on ≥ 90% of dates |
| lookahead | bitemporal check passes: no observation used before its knowledge date |
| frequency | no series contributes returns before its true daily start |
| seed_stability | IR range across resampling seeds ≤ 0.15 |
| null_percentile | IR ≥ 95th percentile of the search null |
| direction | realised sign matches pre-registered direction |

Vetoes are not advisory and are not tuned per run.

---

## 11. Results store

```
results/
  runs.db                 SQLite, append-only
    runs(run_id, ts, hypothesis_id, family, aggregation, params_version,
         data_snapshot_hash, seed, status, killed_by, cost_tokens, cost_usd)
    metrics(run_id, name, value)            net_ir, gross_ir, te, turnover,
                                            max_cash, n_positions, null_pct,
                                            deflated_ir, ess_cycles, ...
    verdicts(run_id, veto, passed, detail)
  artifacts/<run_id>/     parquet: weights, active returns, IC series,
                          risk decomposition, exposure paths
  decisions/              append-only markdown; owner decisions and unlocks
```

Every run records the parameter file version and a hash of the data
snapshot it ran on, so any result can be regenerated. Artifacts are not
committed to git; they are regenerable.

---

## 12. Render layer

`render/views.py` builds every figure and table from the results store and
returns plain objects. `render/static_report.py` writes a self-contained
HTML leaderboard for sharing. `render/streamlit_app.py` serves the same
views. The leaderboard is sorted by the objective only; it has no other
sort; failed runs stay visible with the veto that stopped them; gross IR is
never plotted; holdout metrics are absent until unlocked.

---

## 13. Orchestration

The coordinator is `scripts/nightly_cycle.py`, a deterministic script, not
a model. It loads the snapshot, validates and runs each pending
hypothesis, applies vetoes, records results, writes the digest.

Model-driven roles inside that loop, each bounded:
- **Proposer** — writes hypotheses to `pending/`. Never sees results of
  the current cycle.
- **Implementer** — writes the signal module from the hypothesis file.
- **Critic** — reviews the implementation against the hypothesis before
  it runs; blocks on mismatch.
- **Diagnostician** — reads a failure and decides whether one refinement
  round is worth its cost.
- **Coordinator (model)** — orders the queue, spawns at most K refinements
  per proposal, stops the cycle. Cannot touch params or vetoes.

Owner touchpoints: the morning digest, `decisions/proposed/`,
`data/requests/`, and the leaderboard. Nothing in the loop waits on the
owner; blocked items wait, the rest proceeds.

## 14. Budgets (`params/agents.yaml`)

- Hard token ceiling per run and per nightly cycle; the wrapper kills on
  breach, it does not warn.
- Max proposals per family per cycle; max refinement rounds per proposal.
- Model tiering: cheap model for mechanical steps (config generation,
  result parsing, digest writing), expensive model for hypothesis
  generation and failure diagnosis.
- Agents read summary statistics, never raw return panels.
- Stable documents (this file, params, universe) are prompt-cached.
- Cost per run and per accepted idea is logged and shown on the digest.

---

## 15. Repository layout

```
signal-lab/
  SUBSTRATE.md
  params/            constraints, costs, vetoes, data, agents  (owner-only)
  vetoes/            one function per veto + tests             (owner-only)
  data/
    raw/             untouched vendor pulls (not committed)
    snapshots/       hashed, immutable panels the harness runs on
    universe/        index-ETF map, tiers, characteristic map
    requests/        agent data requests awaiting the owner
    jpmaqs/          request list, loader, grading rules
  src/
    loaders/         bloomberg, fred, jpmaqs, synthetic
    signals/         one module per family
    harness/         walk-forward engine, cost model, run_experiment()
    portfolio/       exposure mapping, long-only solver
    stats/           HAC, block bootstrap, search null, deflated IR
  hypotheses/        pending/ running/ done/
  results/           runs.db, artifacts/ (artifacts not committed)
  decisions/         append-only
  render/            views.py, static_report.py, streamlit_app.py
  tests/
  scripts/           nightly_cycle.py, build_snapshot.py, digest.py
```

---

## 16. Phases

0. Scaffold, params, loaders with a synthetic backend, results schema,
   vetoes with tests, render layer ported. **No real data.**
1. Walk-forward engine and cost model, validated on synthetic panels with
   planted properties (known IR, known drawdown, known turnover). The engine
   must recover a planted IR of 0.5 within its own confidence interval.
2. Real loaders: Bloomberg returns and analytics, FRED. Coverage report,
   tier assignment, characteristic map, factor loadings. Still no search.
3. JPMaQS loader, grading filter, vintage alignment. First pre-registered
   hypothesis batch. Search opens.
4. Nightly cycle with budgets, digest, leaderboard. Owner review of
   survivors. Holdout unlock on one candidate only.

Hypothesis writing may begin in phase 0. Signal testing may not begin
before phase 3.
