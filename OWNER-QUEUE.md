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

### L1. `decisions/proposed/0029` — conditioning the frictionless covariance
Proposed 2026-09-17, committed in `1b6babf`, untouched since. The probe showed
the frictionless twin measures its own covariance error, not the layer it was
built to price: bias 1.40–1.42, condition number 6e4–2e5, and everything
derived from it in `A-20260917-020949` should be struck.

**Recommendation on file:** take §1, §3, §4 and §5. **Defer §2** — it asks for
a ridge chosen so the frictionless bias sits near 1.00 on the Bloomberg panel,
which is a free parameter tuned to a target on the evaluation panel, and 0029's
own closing section warns against exactly that.

**Blocks:** the Bloomberg report's breadth and price-of-constraints sections
stay wrong until §1 lands.

### L2. `H-2026-0007` lost both of its pre-registered checks
0007 states in advance that it is short volatility and that *"the tracking
error veto and the active drawdown diagnostic are the intended checks on that,
not the information ratio."* `decisions/0026` removed the first, `decisions/0030`
removed the second. The successor, `risk_calibration`, asks whether the risk
model told the truth — not whether losses concentrate in the left tail. A book
that correctly forecasts its own blow-up passes it.

Neither removal was wrong, but 0007 was registered against a promise that has
been withdrawn. Either it names a left-tail diagnostic in advance, or 0030
carries a line acknowledging what a signal registered against the old veto has
lost. **This is the one item that would be awkward to discover after the search
opens.** See `claude/hypothesis-registry-review-2026-09-18.md`.

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

Nothing yet. When an item closes, move it here with the decision and its date
rather than deleting it — the record of how long a question sat is worth
keeping.
