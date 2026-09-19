# OWNER-QUEUE — what only Leo can decide

Companion to `HANDOFF.md`. That file is work for Claude Code; this one is
decisions for the owner. Nothing here is a task: every item is a judgement,
a risk appetite, a tradeoff with no correct answer, or a governance signature
that SUBSTRATE §2 reserves to the owner.

**Maintained by Cowork, read by the Monday/Thursday push.** Agents may add an
item, restate one, or move a closed item to `## Closed` with the decision and
its date. An agent may never answer one. If an item can be settled by measuring
something, it does not belong here — it belongs in `HANDOFF.md` as a task, and
the item should say what measurement would retire it.

**Live** means actionable today. **Blocked** means the answer needs a
measurement that has not run. **Dormant** means it was deliberately deferred and
should stay quiet until its trigger fires.

---

## Live — actionable now

### L3. Does "phase 3" gate on the loader or on the data?
SUBSTRATE §16: *"Signal testing may not begin before phase 3,"* and phase 3 is
the JPMaQS loader. But `H-2026-0007`, `0008` and `0009` need only Bloomberg and
FRED series the lab already holds. Reading §16 as *the data this hypothesis
needs exists* would let three run now; reading it as *the loader exists* keeps
the clean separation between building and searching.

Either reading is defensible. Changing it is a SUBSTRATE amendment, not a
shortcut, and the conservative reading costs only time.

### L4. Holdout power belongs in SUBSTRATE §3
~350 weeks gives t ≈ 0.8 at a true IR of 0.30, so the holdout can only ever
fail a strategy, never confirm one. That is a material property of the lab's
own final test and it is currently recorded only in these notes. Transcribing
it into §3 is an owner act.

---

## Blocked — waiting on a measurement

### B1. Whether the volatility overlay becomes policy, and at what halflife
Built and tested: seed-paired over 5 seeds at h=13, a scalar 26-week overlay
moved 2008 bias −0.36/−0.54, calm-year bias +0.10, `te_p95` −0.0141 at IC 0.20
in all five seeds, and net IR up +0.10/+0.06. All ten paired calibration
differences went the right way.

**Retired by:** a halflife sweep across horizons. 26 weeks was the only value
tested, at one horizon and two IC rungs. Nothing reads it by default.

**Note for when it lands:** it competes with `H-2026-0008` for the same
variance. Once the book de-risks through its covariance, 0008 must be measured
as incremental to that, not against a never-de-risks baseline, or it gets
credited for what the risk model did.

### B2. The per-session turnover cap
`decisions/0024` left it unvalued; the sweep is `[0.10, 0.25, 0.50, none]`.
The 3-seed audit put it inside noise (mean net IR 0.27/0.27/0.27 at IC 0.02,
0.41/0.40/0.39 at IC 0.20).

**Retired by:** the ten-seed Bloomberg audit. Cannot be chosen from a lean run.

### B3. The 400% turnover backstop vs fast, strong signals
A small-universe cell ran 414% annual traded notional on realistic costs in the
synthetic grid. The Bloomberg grid's worst was 342%, inside the backstop.

**Retired by:** the ten-seed audit's turnover column at high IC and short
horizon. If nothing approaches 400%, the question closes itself.

### B4. `decisions/0030`'s threshold sensitivity to kurtosis
The ceiling is 1.72, the p99 of the worst annual bias under a correct model at
the measured excess kurtosis of 2.37. But p99 is 1.48 at κ=1 and 1.92 at κ=4,
and one Bloomberg cell read κ=14.65. Whether the threshold should sit at a
conservative κ, or be re-measured per run, is unsettled.

**Retired by:** the ten-seed audit's kurtosis distribution across cells. One
outlier out of seventeen is not enough to choose on.

### B5. The robust factor-loading estimator (`decisions/0015`)
Unchosen: shrinkage, resampling, robust regression or regime-conditional. It
will live in `params/characteristics.yaml`, which does not exist.

`H-2026-0010` declares that risk decomposition is the check on whether its
cross-sectional carry signal is really a single term-premium bet — so 0010 is
testable while its own stated safeguard is not.

**Retired by:** nothing measured yet; this is a modelling choice that needs a
candidate. Listed here because a hypothesis already depends on it.

---

## Dormant — deferred on purpose, with the trigger that wakes them

### D1. The two tracking-error penalty coefficients
`decisions/0100` open questions: SUBSTRATE §4's asymmetric TE penalty has two
coefficients, both null, and the objective **refuses to build** until they are
set. Deferred by the owner on 2026-09-09 until a candidate model exists, and
0100 records that refusing is the correct state rather than a gap.

**Wakes when:** a candidate model exists. The form is already settled
(conviction-scaled, linear between two endpoints, floored — `decisions/0019`).

### D2. Test-suite split — model-validity checks vs wiring
Deferred by the owner. **Wakes when:** `make check` runtime becomes an obstacle
to iteration. It went 1642 s → 417 s on 2026-09-18 for unknown reasons, so this
may have receded on its own.

### D3. Region labels are still placeholders (`decisions/0022`)
**Wakes when:** a hypothesis needs a region axis it can trust —
`H-2026-0001`, `0006`, `0009` and `0011` all target `region`.

### D4. G3OC as the live 3–7y series
The splice is live; the replacement is not actioned (`decisions/0022` area).

### D5. `git_key` and `git_key.pub` in the repo root
Ignored by `*key*`, so not at risk of being committed, but they sit in a
directory that gets cloned and archived. Hygiene, owner's call.

---

## Closed

### L1 — conditioning the frictionless covariance. CLOSED 2026-09-19.
`decisions/0029`. **§1, §3, §4 and §5 taken; §2 deferred.** The frictionless
twin is struck from the report as a ruler and kept as a covariance-error
diagnostic; empirical breadth is read off the constrained ladder; per-date
Pearson IC is reported beside rank IC.

§2 -- a ridge or eigenvalue floor chosen so the frictionless bias sits near 1.00
on the Bloomberg panel -- stays deferred, because that is a free parameter tuned
to a target on the evaluation panel and 0029's own closing section warns against
it.

The ten-seed audit confirmed the finding without the three-seed caveat:
`transfer_ratio` between -4 and +48, empirical breadth 0.12 at h4 against a
formula 151.7. The same reasoning is why `decisions/0033` measures the transfer
coefficient from the constrained book's own weights rather than from a twin.

**Wakes when:** someone proposes a conditioning that can be justified as a
measurement device rather than tuned until the ladder looks right.

### L8 — the rebalance policy. CLOSED 2026-09-19.
**Decided: weekly re-solve stays; no no-trade band, no partial adjustment.**
Recorded as a dated addendum to `decisions/0024`, following the 0013 precedent
rather than amending a decided record in place.

The ten-seed audit settled it: total cost drag across the whole grid is 17-35 bp
a year, about 0.06 of IR at the 6% budget, and that is the entire prize. Capping
turnover at 50% at IC 0.20 saved 12 bp and cost 0.033 of net IR. The persistence
the owner asked for already falls out of a cost-priced objective — 2% annual
turnover at h13, IC 0.02, under forced weekly re-solve.

Raised 2026-09-18 as a gap in the machinery; closed 2026-09-19 as a gap in the
documentation.

**Wakes when:** the cost model is revised, not when something is measured.

### L7 — measuring the transfer coefficient. CLOSED 2026-09-19.
`decisions/proposed/0033`. **All three recommendations taken.** TC gates nothing
and is a disclosed characteristic; the full-matrix estimator (Clarke-de Silva-
Thorley 2006 eq. 23) is the reported TC, with the diagonal form alongside for
comparability and the inversion-free alignment form as a control; `implied_ic`
prints at both TC = 1 and measured TC rather than silently changing meaning.

Published magnitudes for context: CDT (2006) report **0.671** for a long-only,
capped, beta-neutral 21-country EAFE book (0.620 diagonal); Ding (2010) cites
their 2002 simulation range as **0.3 to 0.8**.

The ten-seed audit confirmed why the frictionless twin cannot supply this
number: transfer ratios of -4 to +48, and empirical breadth of 0.12 at h4
against 151.7 from the formula.

Implementation is the same migration `decisions/0030` turned out to be — a rule
exposes `alpha()`, the engine carries it onto the path, a rule that does not
yields no TC rather than a wrong one.

### L6 — the registry's tickers against the real panel. CLOSED 2026-09-19.
`decisions/proposed/0032`; map at `data/requests/ticker_resolution.csv`.
27 of 42 unresolved names were genuine JPMaQS gaps; the rest was bookkeeping.

**Decisions:** the price-only concern is **withdrawn** — the pull is
`TOT_RETURN_INDEX_GROSS_DVDS` and `decisions/0013` had already settled it; the
stale `likely_price_only` column leaves the table on `make coverage && make
universe`. Europe stays **sub-country and sector only**; `MXEU` not pulled, and
the resulting two-draws-for-Europe asymmetry is accepted and disclosed because
the UK is a distinct market. `LUALTRUU` and `LT08TRUU` are **fabricated**,
removed not substituted. `H-2026-0010`'s term spread is **`LT01TRUU` vs
`LT11TRUU`**, `LT09TRUU` as mid-curve check. `DRTSCILM` joins the FRED request.
`H-2026-0007` takes **set A**, the six-segment quality ladder, with the Ba/B/Caa
collinearity disclosed in advance.

The validator gap it uncovered moves to its own record, `0034`.

When an item closes it moves here with the decision and its date rather than
being deleted — the record of how long a question sat is worth keeping.

### L2 / L5 — the left-tail check `H-2026-0007` lost. CLOSED 2026-09-18.
**Decision: shape 1.** `L = |q05(z)| / 1.645` is a reported characteristic on
every cell and is named, in a dated addendum, as `H-2026-0007`'s pre-registered
check. It gates nothing; no eleventh veto is added. Recorded in
`decisions/proposed/0031`, which needs promoting out of `proposed/` and the
addendum writing — both need git, so they queue in `HANDOFF.md` once the running
audit lands. The threshold stays unset and comes from `scripts/bias_map.py`'s
simulated null.

L2 was raised 2026-09-18 and closed the same day, before any result existed for
0007 — which was the whole point of raising it.

