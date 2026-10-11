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

### L28. The label map: a region, a sector and a style for each instrument
Added 2026-10-07 by Cowork, out of L27 (d). It wakes D3.

**Ruled in part, 2026-10-10 (owner):**
- **The regions** are US, Developed Europe, Japan, APAC ex-Japan, EM and
  Global.
- **Gold and commodities carry no region.** They are their own Commodities
  bucket (owner: "let it be its own Commodities bucket").
- **A sector or style index carries its parent's region.**
- **Sector and style labels wait** until a hypothesis targets them.
- **Cowork drafts the map** for the owner to correct, with a parent for each
  of the eight tradable-only instruments (L29) in the same table.

**Still open:** his corrections to that draft. L32 is ruled (`NDDLUK`
leaves), so the draft can be written.

`decisions/0050` gives the matrix a label block. Only `cash` has a source.
`data/universe/investable_universe.csv` carries `section` and
`reporting_class` and no region, sector or style column, and the loader's
`region` is the workbook section, a placeholder (`decisions/0022`: "A real
region map is an owner decision and has not been made").

**Why it is live.** H-2026-0001, 0006, 0009 and 0011 target `region`. The
wiring can land without it, with the region axis still raising; those four
cannot run until it exists. No hypothesis targets sector or style.

**What the owner would be deciding:**
- the list of regions, and which region each of the 93 investable series
  belongs to, bonds included;
- whether a sector or style index also carries its parent's region (a US
  Financials index is both US and Financials);
- whether sector and style labels are set now or when a hypothesis needs
  them.

**Cowork has offered** to draft the map from `section` and the index names
for the owner to correct. Every entry would be a guess until he confirms it.

### L29. Universe loose ends after `decisions/0052`
Added 2026-10-07 by Cowork.

**Answered 2026-10-10 (owner, from Bloomberg):**
- **`I02513EU` is EUR:** "Bloomberg Pan-European Government Total Return
  Index Unhedged EUR". It is one of nineteen local-currency series, and
  what to do with them is L32.
- **`LET1TREU` is the Euro Treasury 1-3y:** "Bloomberg Euro-Aggregate:
  Treasury -- 1-3 Year". Its future ticker is `I02119EU`. The universe
  file's name and SUBSTRATE §5.4a's "1-10y" are corrected with the L31 and
  L32 work.
- **The tradable-only parents** are drafted with L28.

- **`I02513EU` (Pan-European Government).** Its median loading on the dollar
  factor is 0.10, against −1.00 and −1.15 for the two euro indices the lab
  converted to dollars itself. *Cowork's inference:* it is a euro return
  treated as a dollar one, the same kind of series `decisions/0052` removed.
  SUBSTRATE §5.4a already flags its currency as unconfirmed. **Retired by:**
  the owner reading its currency on Bloomberg.
- **`LET1TREU` may not be the index its name says** (added 2026-10-08 by
  Cowork, from task 52). The universe file and SUBSTRATE §5.4a call it Euro
  Treasury 1-10y. Its median measured `INDEX_OAD_TSY` is 1.84, where a 1-10y
  euro government index would sit near 4 to 5, and its loading on the real-
  yield factor is +0.28, the only positive one among the ex-USD bonds
  (`results/characteristics/huber6-v2/report.md`). *Cowork's recollection,
  not verified:* `LET1TREU` is the Euro Treasury 1-3y. **Retired by:** the
  owner reading its name and maturity band on Bloomberg.
- **The eight tradable-only instruments have no row in the matrix**
  (L27 (e)). SUBSTRATE §5.2 says they inherit loadings; no record says from
  what. The owner's pull of 2026-10-07 found earlier daily history for one:
  - `M1CXNNA` (US High Dividend Yield): the gross sibling `M2CXNNA` is daily
    from 2000-12-29. The owner did not take the splice. It would mix a gross
    series with net siblings and is an owner-only edit to `params/data.yaml`.
  - `MXEU0RL` (Europe Real Estate): the predecessor `MXEU0RE` is daily from
    1995, pulled as a price index in euros. Usable only as
    `TOT_RETURN_INDEX_GROSS_DVDS` in dollars.
  - `LTP5TRUU` (TIPS 0-5y): monthly before 2010-06, which may not be spliced.
  - Five MSCI style indices: nothing earlier found.
- **What the owner would be deciding:** the parent each inherits from, or
  that they stay unholdable in the development window. Seven of the eight
  start in 2015 or later.

### L33. One FX source, and which
Added 2026-10-10 by Cowork, out of L32.

After HANDOFF task 53 the lab converts with two FX sources:
- **FRED's noon New York spot:** the five ex-USD bonds, as delivered in
  `bbg_exusd_bonds_usd_unhedged.csv`, about 200 dropped days each;
- **Bloomberg's generic close** (`bbg_curncy_hist.xlsx`): the eighteen
  series of `decisions/0053`.

MSCI and, as far as Cowork knows, Bloomberg's indices convert at the WM 4pm
London fix. Neither source is that.

**The one test available** is MSCI UK, in sterling converted against the
index in dollars, weekly, 2006-2019 *(Cowork's read)*:
- **Bloomberg close:** 237 bp/yr tracking error;
- **FRED noon:** 141 bp/yr.

Both residuals reverse the next week (lag-1 autocorrelation about −0.5) and
show no drift. The four ex-USD bonds converted both ways differ by 195 to
210 bp/yr weekly.

**What the owner would be deciding:**
- (a) keep two sources, the state after task 53;
- (b) everything on the Bloomberg file, with no dropped days;
- (c) everything on FRED noon, which needs a FRED pull of six more series and
  drops US holidays;
- (d) a Bloomberg London 4pm source, if one resolves. *Cowork's
  recollection, not verified:* Bloomberg's `BFIX` and `L160` pricing
  sources.

**Not urgent.** The noise is weekly and mean-reverting. It matters most for
the region and dollar signals on the eighteen converted series.

### L12. Is the registry the right shape, now that the stepdown is the bar?
Added 2026-09-21 at the owner's request. Bears on `decisions/0036` §6,
SUBSTRATE §9 and §13, and on what is bought from Macrosynergy.

SUBSTRATE v0.5 made the `multiple_testing` veto — Romano-Wolf at FWER 5%, family
level then within family — **bar 2, how a signal is judged**. It used to be a
footnote at the end of a pipeline nobody had run. It is now the gate.

The registry was written before that was true, and it does not sit well against
it. **`effective_bets_active` is 11.67 across 95 series.** Of twelve
hypotheses, **four target `region`, three `credit` and two `duration`; the
other three (`cash`, `conviction`, `real_nominal`) are one each.** Each of the
twelve sits in its own SUBSTRATE §6 family (`growth`, `inflation`, …,
`conviction`), so "family level first" is trivial today: the dependence lives
in the shared *target axis*, not in the family. A stepdown learns dependence
from the block bootstrap, so correlated tests do not pay full multiplicity,
but they do not buy twelve independent shots either. Twelve registrations
concentrated on three axes over roughly twelve effective bets means **how the
tests are grouped does most of the work**, and nobody has chosen that grouping
against this constraint.

*Corrected 2026-09-28 by Cowork at the owner's request. The earlier text said
five `region` and four `credit`, and treated the target axis as the family.
Counts are from `target_axis` and `family` in `hypotheses/pending/*.yaml` as of
`076c80e`.*

Two decisions inside it:

- **How families are defined.** SUBSTRATE §6 lists eleven, and the stepdown runs
  at family level first. With one hypothesis per family that step does
  nothing. Whether the four `region` tests and the three `credit` tests should
  instead be grouped as families (and the stepdown run on those groups) decides
  most of what survives.
- **How many hypotheses per family per cycle.** `params/agents.yaml` already
  carries the knob (`max proposals per family per cycle`). It was sized as a
  cost lever (`decisions/0007`); it is now also a statistical one.

**And it is live now because of procurement.** 27 JPMaQS tickers are being
bought for nine hypotheses. If those nine collapse to two or three effective
tests under the stepdown, that is a different purchase, and task 23's catalogue
check is already queued.

**Cannot be retired by measuring — yet.** The correlation structure of the
twelve signals cannot be estimated because `src/signal_lab/signals/` is empty,
so nothing builds a signal from a hypothesis file. This is a design judgement
today. **It becomes measurable once signals exist**, at which point the honest
version is to estimate the joint distribution and read the effective number of
independent tests off it rather than guess — and the owner has asked that it be
revisited then.

---

## Blocked — waiting on a measurement

### B4. `decisions/0030`'s threshold sensitivity to kurtosis
The ceiling is 1.72, the p99 of the worst annual bias under a correct model at
the measured excess kurtosis of 2.37. But p99 is 1.48 at κ=1 and 1.92 at κ=4,
and one Bloomberg cell read κ=14.65. Whether the threshold should sit at a
conservative κ, or be re-measured per run, is unsettled.

**Retired by:** the ten-seed audit's kurtosis distribution across cells. One
outlier out of seventeen is not enough to choose on.

---

## Dormant — deferred on purpose, with the trigger that wakes them

### L10. The `seed_stability` threshold has no measurement behind it
Added 2026-09-20 by Cowork. **Rewritten and moved to Dormant on 2026-10-07**
at the owner's instruction (he accepted Cowork's offer to do both). The
earlier text is in git history.

- `params/vetoes.yaml` sets `seed_stability.max_ir_range = 0.15`.
- **The earlier text judged that number against the wrong seeds.** It compared
  0.15 with the spread across *audit* seeds (0.26 to 1.42 per cell in
  `A-20260919-155557`). Each audit seed plants a different noise history, so
  that spread is the sampling error of an IR over sixteen years, about 0.25.
- **The veto is about *resampling* seeds** (`vetoes/rules.py`: "IR range
  across resampling seeds"): one history, solved again with resampled inputs.
  That spread should be much smaller. Nobody has measured it.
- **Nothing is resampled for a real signal until the phase-2 solver exists.**
  The veto has no input today, so 0.15 can't be judged either way.
- SUBSTRATE §10: a veto whose input is absent fails. That bites on the first
  real hypothesis.

**Wakes when:** the phase-2 solver resamples a planted signal. Measure the
range across resampling seeds there, then set the threshold from it or change
the statistic (a range is the worst-behaved summary of ten draws). `vetoes/`
and `params/` are owner-only.

### D8. When to flip `data.jpmaqs.status`
Added 2026-10-07 by Cowork. It was inside L23, which is now ruled.

`params/data.yaml` holds `status: credentials_supplied`. The loader, the macro
snapshot and the coverage report exist (HANDOFF tasks 44 and 46), and the
grade rule is decided (`decisions/0006` addendum). Flipping the status is the
owner's, and `params/` is owner-only.

**It opens nothing by itself.** `decisions/0016`: the search cannot open until
a matrix has been chosen. `src/signal_lab/signals/` is empty and there is no
phase-2 solver.

**For the owner to read first:** nine of 26 tickers start after 2001-01-05,
most of them in late 2003 or early 2004, and three have no usable rows
(`results/jpmaqs_coverage.md`).

**Wakes when:** the exposure matrix is wired (L27) and one signal module
exists.

### D6. Does "phase 3" gate on the loader or on the data?
Moved from Live to Dormant by the owner, 2026-09-21, without being answered —
because on the evidence it does not bind either way.

SUBSTRATE §16 says *"Signal testing may not begin before phase 3,"* and phase 3
is the JPMaQS loader. Four registered hypotheses need no JPMaQS at all:
`H-2026-0007` (12 Bloomberg OAS series), `0008` (MOVE plus four FRED), `0009`
(six Bloomberg, post-`0032`) and `0012` (**zero** series — it is the conviction
measurement question). So the permissive reading would let four run today.

**It buys nothing.** `src/signal_lab/signals/` is empty — `__init__.py` at 44
bytes and a `.keep` — so no code turns a hypothesis file into a signal.
`src/signal_lab/stats/` holds only `blocks.py`, the block shuffle: no
Romano-Wolf stepdown, no HAC, no search null, no deflated IR. And since
SUBSTRATE v0.5 the `multiple_testing` veto **is** §3's evidence bar, so a
hypothesis run today fails bar 2 by construction — §10 is explicit that a veto
whose input is absent fails. Vetoed before it is judged, whichever reading of
§16 applies.

**Wakes when:** `src/signal_lab/signals/` can build a signal from a hypothesis
file **and** the Romano-Wolf stepdown exists. At that point the question becomes
real and should be re-raised as a Live item.

### D1. The two tracking-error penalty coefficients
`decisions/0100` open questions: SUBSTRATE §4's asymmetric TE penalty has two
coefficients, both null, and the objective **refuses to build** until they are
set. Deferred by the owner on 2026-09-09 until a candidate model exists, and
0100 records that refusing is the correct state rather than a gap.

**Wakes when:** a candidate model exists. The form is already settled
(conviction-scaled, linear between two endpoints, floored — `decisions/0019`).

### D7. The two-step one-sided stepdown, and a bootstrap null for bar 2
Added 2026-09-29 by Cowork. **Deferred by the owner the same day** ("keep
things as is for now").

The source is Romano, Shaikh & Wolf (2014, *Econometrica* 82(5)), which the
owner supplied, and Romano & Wolf (2018), "Multiple Testing of One-Sided
Hypotheses: Combining Bonferroni and the Bootstrap". Cowork has not read the
2018 chapter. Two ideas:
- **(a) The two-step correction.** Drop clearly negative hypotheses from
  Romano-Wolf's critical value at a small β, for more power on one-sided
  tests.
- **(b) A block-bootstrap null.** Build the null from the weekly
  live-minus-baseline series instead of engine shuffles, so k stops costing
  engine hours. This would amend `decisions/0036`.

**Wakes when:** the owner reopens it, or real signals exist and the shuffle
budget (k) binds.

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

### L32. Nineteen return series are in their local currency, not dollars — CLOSED 2026-10-10 (ruled; `decisions/0053`; HANDOFF task 53)

**Ruled 2026-10-10 (owner):**
- **The base currency is USD.** Series are kept in their quote currency and
  converted in the loader.
- **The FX source is** `bbg_curncy_hist.xlsx`, which he supplied, read
  through an explicit quote-convention table.
- **Carried from Cowork's proposals:** `NDDLUK` out, the guard, and the
  ex-USD bonds left on FRED (L33).

Added 2026-10-10 by Cowork, while checking the owner's answer that
`I02513EU` is EUR.

**What was found.** `data/universe/raw_manifest.csv` declares the whole
`TR Levels` sheet in USD. The Index Map's `Quote ccy` column (Bloomberg
`CRNCY`) disagrees for 19 return series. The loader maps that column and
never checks it.

| Currency | Series |
|---|---|
| EUR | `I02513EU`; `MXEUG`; the eleven MSCI Europe sectors `MXEU0EN`, `MXEU0MT`, `MXEU0IN`, `MXEU0CD`, `MXEU0CS`, `MXEU0HC`, `MXEU0FN`, `MXEU0IT`, `MXEU0TC`, `MXEU0UT` and `MXEU0RL` (tradable-only) |
| GBP | `NDDLUK` |
| CAD | `MXCA` |
| HKD | `MXCN` |
| INR | `MXIN` |
| KRW | `MXKR` |
| TWD | `TAMSCI` |

`LGTRTRGU` and `LGTRTRJU` were the same case and are already out
(`decisions/0052`).

**The pull carried no currency override** (checked 2026-10-10 at the owner's
request). The workbook holds values only, so no BDH formula survives. Its own
record of the pull, `Loader Notes` rows 3-5 and the cell comments dated
2026-09-07, gives the overrides as `Per=D, Fill=NA, Days=A`, with nothing for
currency. Bloomberg's long names say it too: "MSCI UK Net Total Return Local
Index", "MSCI Europe Real Estate GICS Level 1 Local Index".

**The returns confirm it** *(Cowork's read of `huber6-v2`, median loading on
the dollar factor)*:
- 17 of the 18 estimated series read +0.10 to +0.85. `MXCN` reads −0.01,
  as a currency pegged to the dollar would.
- Every dollar-quoted peer in the same classes reads −0.07 to −0.37 for
  equities, and −0.61 to −1.15 for the converted ex-USD bonds.
- **The cleanest pair is MSCI UK:** `NDDLUK` (sterling) reads +0.53 and
  `NDDUUK` (dollars) −0.24. Their equity loadings are 0.96 and 1.01.

**What it touches.**
- **The rows:** 11 of the 13 European Equities rows, 1 of 9 DM ex-US, 5 of 12
  EM Equities (`MXCN`'s HKD is pegged, so it matters little), 1 Ex-USD bond
  and 1 tradable-only.
- **The numbers:** every real-data number that used their returns, which
  includes their loadings in `huber6-v1`, `huber6-v2` and
  `M-20261003T181155Z`, and real-data covariances and tracking error. Each
  treats a local return as a dollar one.
- **What it does not touch:** the factors (`NDUEACWF`, `DXY` and the rest) and
  the benchmark, which are all in dollars.

**What the owner would be deciding:**
- **How they become dollars:**
  - (a) re-pull the 19 with Bloomberg's currency override to USD, same field
    (`TOT_RETURN_INDEX_GROSS_DVDS`);
  - (b) convert in the lab as local × spot, as the ex-USD bonds were. This
    needs bilateral FX for seven currencies, and the FRED panel holds none;
  - (c) remove them.
- **`NDDLUK`:** MSCI UK in sterling, beside `NDDUUK` in dollars. By
  `decisions/0052`'s reasoning it is a restatement.
- **A guard:** the loader refuses a series whose `Quote ccy` is not its
  sheet's declared currency, unless a conversion is recorded.

**Numbers recorded before stand** (the run of record, `huber6-v1` and
`huber6-v2`), as with `decisions/0052`.

### L31. The wording of SUBSTRATE after `decisions/0051` and `0052` — CLOSED 2026-10-10 (ruled; SUBSTRATE v0.10 transcribed by Cowork in the working tree, lands with HANDOFF task 53 step 0)

**Transcribed 2026-10-10:**
- **§6:** the wording of `decisions/0051`, verbatim.
- **§5.4a:** rewritten to list what landed. `LET1TREU` is recorded as 1-3y
  and Japan as the Aggregate; `I02513EU` is EUR and converted
  (`decisions/0053`); `LGTRTRGU` and `LGTRTRJU` are not investable.
- **The record:** `decisions/0100` gains a v0.10 table.

**Also transcribed:** §5.1 invariant 8, every return is in USD
(`decisions/0053`). The owner approved it on 2026-10-10.

Added 2026-10-07 by Cowork. Two sentences of the constitution no longer say
what the lab does. Nothing has been edited.

**Ruled in part, 2026-10-10 (owner):**
- **§6:** the wording at the end of `decisions/0051`, as proposed.
- **§5.4a:** list the unhedged series that landed, in place of "until they
  land".
- **Cowork may transcribe both as v0.10.**

**Held by Cowork:** §5.4a's text depends on L32 (`I02513EU` is a EUR return)
and on `LET1TREU` being 1-3y. Both sections are transcribed together once
L32 is ruled.

- **§6,** "mapped to ETF weights by solving for the long-only portfolio whose
  exposures best match the view". `decisions/0051` rules that views become
  expected returns and nothing is held at a target. Proposed wording is at
  the end of that record. **The phase-2 solver should not be built before
  this is transcribed.**
- **§5.4a,** "Until they land, the FX axis is represented only by
  `LGTRTRGU`, `LGTRTRJU`, `I20344US`, and `I02513EU`". The unhedged series
  have landed and `decisions/0052` removed the first two.

**What the owner would be deciding:** the wording, and that Cowork may
transcribe it as v0.10.

### L30. What `INDEX_OAD_TSY` is for the TIPS index — CLOSED 2026-10-10 (ruled; `decisions/0050` addendum of 2026-10-10)

**Answered 2026-10-10 (owner, from Bloomberg):** it is the real-rate
duration, the sensitivity to a parallel shift in the real Treasury curve.
It is not a spread duration. **Ruled:** TIPS's duration axis reads the
measured value, as Treasuries and IG do.

Added 2026-10-07 by Cowork, out of L27 (c).

`LBUTTRUU`'s estimated real-yield loading is 1.22 times its measured
duration, and rising (1.20, 1.24, 1.36 across three periods, *Cowork's
read*). Every other government index reads at or below 1. Cowork doesn't
know whether the field is a real duration for this index or a
nominal-equivalent one. `decisions/0050` reads the estimate for TIPS until
this is answered.

**Retired by:** the owner reading the field's definition for an
inflation-linked index on Bloomberg.


### L27. The columns of the exposure matrix, and which cells are measured — CLOSED 2026-10-07 (ruled; `decisions/0050`; wiring not queued)
**RULED 2026-10-07.** Owner: "Yes, as stated", to the rulings Cowork put to him. Recorded as `decisions/0050`:
- **(a)** a factor block, a measured block beside it, and a label block;
- **(b)** equity, dollar and commodities stay columns, not view axes;
- **(c)** duration reads the measured value for Treasuries, Long Treasuries
  and IG Corporates, and the estimate everywhere else; credit and
  real/nominal read the estimate; TIPS read the estimate until L30 is
  answered;
- **(f)** where a measured cell has no value, the estimate stands in;
- **(g)** a measured value sits beside the factor cell and never replaces it.

**Not ruled, and carried forward:** (d) the labels, now L28; (e) the
tradable-only rows, now in L29. The same day the owner chose the solver's
form (`decisions/0051`), which is why (b) costs nothing. **The wiring is not
queued.**

*The item as it stood when ruled:*
Added 2026-10-07 by Cowork. The proposal is `decisions/proposed/0050`.

**Why it is live.** `decisions/0049` chose the estimator (Huber) and the
factors (six). It did not say what the matrix's columns are, and the matrix is
the next thing to build. HANDOFF task 51 builds only what every answer needs:
the Huber loadings, their standard errors, each instrument's explained share,
and the measured duration and spread beside them. Wiring the matrix into
`resolve_exposures` waits on this item.

**The gap.** SUBSTRATE §6 forms views on seven axes (duration, credit, region,
sector, style, real/nominal, cash). The regression has six factors (equity,
real yield, inflation, credit, dollar, commodities). Three factors have an
axis, three do not, and four axes are labels, not betas.

**What the owner would be deciding,** with Cowork's lean on each:
- **(a) The layout.** A factor block of six columns and a label block (region,
  sector, style, cash). Duration reads minus the real-yield column,
  real/nominal reads minus the inflation column, credit reads minus the credit
  column. *Lean: yes.*
- **(b) Whether equity, dollar and commodities become axes a hypothesis can
  target.** That would amend SUBSTRATE §6. *Lean: no, for now. They stay as
  columns for the risk decomposition.*
- **(c) Which cells are measured.** *Lean:* the real-yield and inflation cells
  of Treasuries, Long Treasuries, TIPS and IG Corporates come from the index's
  effective duration. HY and MBS are decided after reading task 51's table of
  estimated against measured. Credit stays estimated; duration times spread is
  untested.
- **(d) The region labels.** They are still placeholders (D3), and four of
  twelve hypotheses target `region`. *No lean. This wakes D3.*

**Partly retired by measuring.** Task 51's table settles the facts behind (c).
The rest is design.

**What task 51 found (added 2026-10-07 by Cowork; it restates the item and
answers nothing).** From `results/characteristics/huber6-v1/report.md`, and
from Cowork's own read of the store where a line says *(Cowork's read)*: counts
and medians made outside the repo's environment, to be reproduced by a task
before a decision cites them. The full account is the Project doc
`claude/tasks-50-51-review-2026-10-07.md`.

- **The gap between estimated and measured duration follows maturity.** The
  real-yield factor is the 10-year TIPS yield. At that tenor the regression
  returns the measured number: Treasuries 7-10y read 0.95 of measured
  duration. Away from it the two part: 1-3y reads 0.57, 3-7y 0.89, the two
  long indices 0.69 and 0.71.
- **"About 30%" for long bonds is a ratio of two medians.** Week by week the
  long indices read 0.84 of measured duration (10th to 90th percentile 0.66
  to 0.95), and 0.71 to 0.76 in 2009-15 *(Cowork's read)*.
- **TIPS read above measured, at 1.22.** Cowork doesn't know why. Whether
  `INDEX_OAD_TSY` is a real duration for `LBUTTRUU` is a question for the
  vendor's field definition.
- **HY reads 0.36 to 0.44 of its stated duration, MBS 0.82, the two EM
  dollar indices 0.54 and 0.64.** MBS falls to 0.65 in 2016-19 *(Cowork's
  read)*.
- **Duration times spread, scaled to the IG spread factor, overstates the HY
  credit loading.** The estimate is 0.37 to 0.68 of it across the five HY
  indices *(Cowork's read)*.
- **Where a measured cell would be empty.** The 8 Ex-USD Bonds have no
  measured duration at all. `LT13TRUU` (Treasuries 3-7y) has none before
  2007-01-12, which is 211 of its 888 weeks with a loading. No instrument has
  an empty week inside its measured span *(Cowork's read)*.
- **The label block cannot be built from the universe file.**
  `data/universe/investable_universe.csv` has `section` and `reporting_class`
  and no region, sector or style column. Only `cash` can be read today.
- **Eight tradable-only instruments have no row:** one TIPS, one US equity,
  four DM ex-US equity, one European equity, one EM equity. SUBSTRATE §5.2
  says they inherit loadings; no record says from what.
- **Explained share at the last week is below 0.5 for 22 of 87 instruments**
  *(Cowork's read)*, and the class medians hide the low ones: US Equities
  has a median of 0.75 and a minimum of 0.17. Commodities' 1.000 is an
  identity, since the factor is that index less cash.

**What this adds to the ruling,** with Cowork's lean on each:
- **(c), lean updated.** Measured for Treasuries, Long Treasuries and IG
  Corporates. Estimated for HY, MBS, EM and Ex-USD bonds. TIPS after the
  field definition is checked. Credit stays estimated.
- **(d), restated.** Region is not the only label missing: sector and style
  have no column either. No hypothesis targets sector or style; four target
  region.
- **(e) The eight tradable-only rows.** Which parent each inherits from, or
  they stay unholdable until that is ruled. *No lean.*
- **(f) A measured cell with no value** (3-7y before 2007). *Lean: the
  estimate stands in for it, marked `estimated`.*
- **(g) Whether a measured value replaces the factor cell or sits beside
  it.** `decisions/proposed/0050` point 1 replaces it. *Cowork's lean has
  changed: beside.* The six factor columns then stay one regression's output
  for the risk decomposition, and the duration and real/nominal axes read
  the measured value where (c) allows.

### L26. Recorded numbers depend on the thread count — CLOSED 2026-10-07 (ruled; HANDOFF task 50 landed 2026-10-07, `273182e`)
**LANDED 2026-10-07.** `273182e` pins one thread and re-records the three constants; `16a063b` is the estimator test at one thread, which reproduces the run of record exactly. Cowork verified both (Project doc `claude/tasks-50-51-review-2026-10-07.md`); the measurements are in the 2026-10-07 addendum to `decisions/0048`.

**RULED 2026-10-07: option (a), one thread is the reference.** Owner: "i accept all of your suggestions for the pending decisions". Recorded as
`decisions/0048`. HANDOFF task 50 applies it, re-records the three constants and
carries the hygiene list below.

*The item as it stood when ruled:*
Added 2026-10-07 by Cowork, from task 49's receipt (step 2). Not verified by
Cowork beyond the receipt: the two timing runs left no log.

**What task 49 measured, on the slow tier, back to back.**
- **Threads unset (32 cores): 1,319 s. One thread: 37 s.** The process ran
  about 30 busy threads on matrices too small to use them. This is most of why
  `check-full` swings from 388 s to 4,235 s.
- **With one thread, four of the eight exact comparisons in
  `tests/test_baseline.py` fail.** Net IR moves by 0.00002 to 0.00014
  (−0.87921 against the recorded −0.87935; −0.39164 against −0.39166; −0.40466
  against −0.40476). The receipt says "1e-4 to 1e-3"; the three pairs it
  prints are smaller than that.
- Nothing was re-recorded. Parallel tests were not trialled, by the task's own
  rule.

**Why it is the owner's.** Every number the lab has recorded was produced
with the thread count this machine happens to have. On a machine with a
different core count the same code would give slightly different numbers. The
movement is far below the 0.30 bar and the 0.26 per-seed spread, so no verdict
is at risk. The exact-equality tests, and the claim that a run reproduces, are.

**The options.**
- **(a) One thread is the lab's reference.** Set it in `build.mk`,
  `scripts/unattended.sh` and the test configuration. Re-record the four
  values once, under a `decisions/` record that prints old against new.
  Re-run the estimator test's run of record once and record whether it still
  reproduces. Checks drop from tens of minutes to about a minute.
- **(b) Leave threads unset.** Nothing is re-recorded. Checks stay slow and
  uneven, and results stay tied to this machine's core count.
- **(c) Trial a middle setting** (say four threads) first. Claude Code offered
  it. Cowork expects any change of count to move the same four values, and
  has not tested that.

**Cowork leans (a).** A single thread is the only setting another machine can
match. *A guess, untested:* the 14-hour ruler audit may shorten by a large
factor for the same reason, which would change what a search costs.

**Also inside it, hygiene with no judgement needed** (to be queued with
whichever option is ruled):
- Three `.gitignore` lines carry a trailing comment, which git does not
  support, so `results/audit/`, `results/fdr_vs_fwer/` and the
  `loadings.parquet` files are not ignored. Nothing has been committed.
- `data/universe/raw_meta.json` and `raw_structure.json` are untracked and
  force every scoped check to the full suite. `raw_meta.json` holds rows read
  from the vendor workbook, so both should be ignored, not committed.
- `make check-scoped` is now `CLAUDE.md`'s definition of done and has never
  been run end to end.

**Cannot be retired by measuring.** Which configuration is the reference is a
choice.

### B5. The exposure matrix: how loading estimators are tested (`decisions/0015`, `0016`) — moved to Live and rewritten 2026-10-01 — CLOSED 2026-10-07 (ruled; HANDOFF task 51 landed 2026-10-07, `d2d17fb`)
**LANDED 2026-10-07.** `d2d17fb` builds the store `data/characteristics/huber6-v1/`: 87 instruments estimated, 8 tradable-only not. Its Huber loadings equal the run of record's on all 446,244 shared cells (Cowork's check on the store; Project doc `claude/tasks-50-51-review-2026-10-07.md`). `resolve_exposures` still raises; wiring waits on L27.

**RULED 2026-10-07: option (c), Huber.** Owner: "i accept all of your suggestions for the pending decisions". Recorded as `decisions/0049`:
adopted on the owner's judgement and not detected by the gate, with measured
duration and spread kept for bond cells. HANDOFF task 51 builds the estimated
loadings. What the matrix's columns are is a new item, L27.

*The item as it stood when ruled:*
*Corrected by Cowork on 2026-10-01 at the owner's instruction. The earlier
entry said the estimator was "unchosen" and would live in
`params/characteristics.yaml`. `decisions/0015` records the owner overruling
that: the estimator is a research question. It is tested as a measurement
hypothesis (`decisions/0016`) and ranked on out-of-sample loading fidelity,
never on net IR. So the owner does not pick an estimator. What the owner
settles is how the candidates are judged.*

**Why it is on the critical path.** 0016: measurement hypotheses run before
the signal search, and the search "cannot open until a matrix has been
chosen". The JPMaQS loader alone does not open phase 3. `H-2026-0010` also
names the risk decomposition as its own safeguard, so 0010 is testable while
its safeguard is not.

**Decided 2026-10-01: `decisions/0046`, approved by the owner ("046 is
approved").** The owner said "let's test these factor estimates
methodologies", with joint partial betas and factors covering "equity beta,
credit spreads, yields, currency effect, inflation, commodities". The record
fixes:
- **six factors:** equity, real yield, inflation (breakeven), credit (IG OAS),
  dollar and commodities, all from series already in the snapshot, and not
  orthogonalised;
- **the score:** a Huber loss on one-week-ahead prediction errors against a
  rolling-OLS incumbent, gated at g = 1 on a block-bootstrap null, with a
  pass-or-fail uncertainty check and reported regime slices;
- **four candidates,** drafted in `hypotheses/proposed/`: Huber regression,
  Theil-Goldberger shrinkage to a peer prior, HMM regime-conditional loadings,
  and a Kalman filter. Michaud resampling is left out.

**The result (task 45, verified by Cowork; Cash excluded per the 0046
addendum):** no candidate beats rolling OLS. Huber +0.0016 (adjusted p 0.18)
and the shrinkage +0.0009 (0.16) are slightly better, with gains in stress
weeks. The HMM (−0.0066) and Kalman (−0.0005) are worse, and worst in stress.
Rolling OLS itself fails the uncertainty check (1.80 against 1.72, in 2008).
Huber (1.68), Kalman (1.58) and the HMM (1.38) pass. Detail is in the Project
doc `claude/tasks-44-45-review-2026-10-02.md`.

**Still open: which estimator enters the exposure matrix.** Cowork leans
Huber on robustness grounds, not on measured superiority.

**Owner, 2026-10-02:** asked whether any method tried combines Bayesian
regression, a time-varying component and shrinkage toward a long-run mean.
None does. He then ruled: **register and test one, shrinking to the
instrument's own long-run mean.** It is H-2026-0017, specified in the second
2026-10-02 addendum to `decisions/0046`, and HANDOFF task 47 runs it. The gate
covers all five candidates, because it was designed after the first results.
*The state-space form, the half-life grid and the deviation scale are Cowork's
choices; the owner can change them before task 47 starts.*

**Task 47's result (2026-10-03, verified by Cowork): `not_detected`, and the
closest of the five.** Mean-reverting loadings: statistic +0.0028, mean loss
0.2291 against rolling OLS's 0.2319, adjusted p 0.057 over five candidates at
g = 1, worst-year bias 1.59 (passes). Positive in 13 of 18 reporting classes
and in all four slices. Negative in Treasuries, Long Treasuries and IG
Corporates. The table and Cowork's reading are in the 2026-10-03 addendum to
`decisions/0046` and the Project doc `claude/task-47-review-2026-10-03.md`.

**What the owner is choosing.** `decisions/0046` §3 says that if no candidate
passes, the incumbent stays. The incumbent fails the uncertainty check (1.80
against 1.72). So no option follows §3 in full, and the ruling is which part
to waive:
- **(a) Rolling OLS.** Follows the gate and waives the uncertainty check. B4
  already doubts the 1.72 ceiling (it reads 1.92 at a kurtosis of 4).
- **(b) Mean-reverting (H-2026-0017).** Waives the gate at p = 0.057. It has
  the lowest loss, passes the check and gains in every slice. It is the most
  complex of the six and its grid binds at both ends.
- **(c) Huber (H-2026-0013).** Waives the gate at p = 0.20. Simple, passes the
  check narrowly (1.68), and gains most in the largest-move weeks.

**Task 48's descriptions (2026-10-06; verified by Cowork from the run
directories, and the receipt agrees).** None is a test and none changes a verdict.
Detail is in the Project doc `claude/task-48-review-2026-10-06.md`.
- **The fit is the same for all six.** Pooled out-of-sample R² runs from 0.691
  (HMM) to 0.704 (Theil-Goldberger); rolling OLS is 0.699. By class it runs
  from 0.30 (Gold) to 0.92 (Treasuries).
- **Which filter is "best" depends on one line of code.** With West and
  Harrison's covariance update the Kalman candidate reads +0.0027 (adjusted p
  0.052) and the mean-reverting candidate +0.0018 (0.264). As coded they read
  −0.0005 and +0.0028 (0.057). All five verdicts are `not_detected` either
  way. Cowork's synthetic check on 2026-10-03 said the mean-reverting
  candidate would barely move. On real data that was wrong.
- **Stability, as a ratio to rolling OLS** (below 1 is steadier):

  | Estimator | Weekly change | Weekly, 2008-09 | Annual change | Rank agreement with OLS |
  |---|---|---|---|---|
  | Huber | 1.03 | 1.01 | 0.95 | 0.98 |
  | Theil-Goldberger | 0.85 | 0.85 | 0.84 | 0.97 |
  | HMM | 1.27 | 2.01 | 0.65 | 0.83 |
  | Kalman | 1.79 | 2.01 | 1.41 | 0.90 |
  | Mean-reverting | 1.20 | 1.61 | 0.81 | 0.88 |

**Cowork now leans (c), Huber,** and withdraws its lean to (b).
- (b)'s case was that it had the lowest loss. That edge does not survive a
  change to the filter's covariance update, which nobody chose on purpose.
- Huber's numbers are identical in both runs. It passes the uncertainty
  check, is as stable as rolling OLS, and gains most in the largest-move
  weeks.
- With the fit equal across estimators, robustness and simplicity are what is
  left to choose on. The owner asked for robustness first (2026-10-01).
- Cowork's lean has now moved twice (Huber, mean-reverting, Huber). Weigh it
  accordingly.

**Retired by:** the owner's choice of estimator.

### L25. The six factors explain some classes poorly — CLOSED 2026-10-07 (ruled; HANDOFF task 51 landed 2026-10-07, `d2d17fb`)
**LANDED 2026-10-07.** `d2d17fb`: every estimated row carries `explained_share`. By class it is in `results/characteristics/huber6-v1/report.md`.

**RULED 2026-10-07: option (a), build on the six factors now and carry each
instrument's explained share.** Owner: "i accept all of your suggestions for the pending decisions". Recorded in `decisions/0049`,
points 4 and 5. HANDOFF task 51.

*The item as it stood when ruled:*
Added 2026-10-06 by Cowork, from task 48's fit description
(`results/measurement/M-20261003T181155Z/fit.md`). A description, not a test.

**What it shows (rolling OLS, out-of-sample R² against a loading of zero).**
- **Under 0.5:** Gold 0.30, EM Corporate Bonds 0.42, Japanese Equities 0.45,
  EM Sovereign Bonds 0.48.
- **0.5 to 0.7:** Ex-USD Bonds 0.55, MBS 0.61, EM Equities 0.62, HY
  Corporates 0.64, European Equities 0.68.
- **Above 0.7:** US Equities 0.71, APAC ex-Japan 0.75, Real Assets 0.81, Long
  Treasuries 0.86, IG Corporates 0.88, TIPS 0.88, DM ex-US Equities 0.88,
  Treasuries 0.92.
- **The equity factor carries 86% of all explained variation,** and all of it
  for US Equities. The six factors tell the 19 US sector and style indices
  apart by their market beta and nothing else.
- Ex-USD Bonds are explained mostly by the dollar factor (66%). No factor
  stands for a non-US yield.

**The decision.**
- **(a) Build the exposure matrix on the six factors now,** and carry each
  instrument's explained share with it, so the risk decomposition can say how
  much of a position the factors do not cover.
- **(b) Test a wider factor set first.** `decisions/0046` §1 already lists
  what was left out: volatility, liquidity and a high-yield credit factor. A
  non-US yield and a regional equity factor would be new. This is another
  measurement round, chosen after seeing where the fit is weak.

**Cowork leans (a).** The matrix is time-varying by design (`decisions/0015`)
and can be replaced. The signal search is what is waiting.

**Cannot be retired by measuring.** The measurement is in hand.

### L23. The grade filter leaves three JPMaQS tickers with no data — CLOSED 2026-10-07 (ruled; HANDOFF task 50 landed 2026-10-07, `273182e`)
**LANDED 2026-10-07.** `273182e` edits both hypothesis files as ruled. H-2026-0004 is blocked and H-2026-0001 is ready (the receipt's `triage()` run; Cowork confirmed the two files and the row counts in `results/jpmaqs_coverage.md`). `data/requests/H-2026-0004.yaml` is the 2026-09-28 file and still reads `awaiting_owner`.

**RULED 2026-10-07: option (a), keep `exclude`, with no threshold below 3.0.**
Owner: "i accept all of your suggestions for the pending decisions". Recorded as the 2026-10-07 addendum to `decisions/0006`. HANDOFF
task 50 parks H-2026-0004 and removes `EUR_MBCSCORE_SA` from H-2026-0001.
Option (c), a new source for the US leg, waits for the FRED point-in-time
loader and a new registration. `data.jpmaqs.status` is now Dormant item D8.

*The item as it stood when ruled:*
Added 2026-10-03 by Cowork, from task 46's coverage report
(`results/jpmaqs_coverage.md`). The task 46 receipt gave the total dropped and
did not say where it fell.

**All 22,919 rows dropped by `grade_3: exclude` sit in four tickers.**
- `EUR_BLSCSCORE_NSA_D2Q2QL2`: 4,158 rows, all grade 3. Nothing left.
- `USD_BLSCSCORE_NSA_D2Q2QL2`: 7,149 rows, all grade 3. Nothing left.
- `EUR_MBCSCORE_SA`: 7,806 rows, all grade 3. Nothing left.
- `USD_MBCSCORE_SA`: 3,806 of 7,813 rows dropped (49%).

**What that does to the registry.**
- **H-2026-0004 (bank lending standards) has no macro input.** Both of its
  JPMaQS tickers are gone.
- **H-2026-0001 (growth surprise) keeps five of seven series,** and one of the
  five is thinned by half.

**What the vendor says.** Macrosynergy's note on bank survey scores: "Average
grades are on the low side at the moment, as electronic vintage records are
not yet easily available." Cowork could not find a public definition of what
grades 1, 2 and 3 each mean. Its recollection is that grade 3 marks a history
rebuilt from a single later vintage with assumed release dates. That is
unverified.

**The options.**
- **(a) Keep `exclude`.** H-2026-0004 cannot run and is parked, on the record,
  and is not counted as a test. H-2026-0001 runs on what is left. No rule
  changes.
- **(b) Admit grade 3 for named survey categories,** with an added publication
  lag as a margin. This changes `params/data.yaml` and needs a `decisions/`
  record. The margin would be a judgement with no measurement behind it.
- **(c) Re-source H-2026-0004.** The Fed's loan officer survey may have true
  vintages on ALFRED (unverified); the ECB's probably does not. This is a new
  registration, and it waits on the FRED point-in-time loader.

**Cowork leans (a) now, and (c) for the US leg once the FRED loader exists.**
A data-quality rule loosened to rescue one hypothesis is the kind of choice
the lab exists to prevent.

**Two smaller points inside it.**
- Grades are not integers. They run from 1.0 to 3.0 in small steps, so
  `grade_3: exclude` drops only rows at exactly 3.0. Whether a threshold below
  3.0 is wanted is part of this ruling.
- **`data.jpmaqs.status` waits on this.** Flipping it is the owner's decision,
  made on the coverage report. Nine tickers also start after 2001-01-05, most
  of them in late 2003 or early 2004.

**Cannot be retired by measuring.**

### L24. When the full suite has to run, and why its runtime swings (added 2026-10-06) — CLOSED 2026-10-06 (ruled; HANDOFF task 49 landed 2026-10-07, `cbddeb0`; parallel tests not adopted; what it found is L26)
**Owner, 2026-10-06:** "write it on the queue but consider it approved as a handoff for claude code to work on". The question asked was whether the slow tests are worth their time on every change.

**What was approved,** as Cowork put it to the owner the same evening:
- **Explain the runtime first.** Every unattended run logs per-test times and the machine's load.
- **Try parallel tests** (`pytest-xdist`), and keep it only if a back-to-back trial shows it pays.
- **Scope the slow tier by what a change can reach.** A commit runs the slow tests whose imports reach a changed file, and the whole suite whenever that can't be shown.
- **Keep the whole suite** in front of every audit and for any change to the engine, optimiser, loaders, `params/` or `vetoes/`.
- **Not approved, and not in the task:** fewer seeds or replications in any statistical test.

**The evidence.** `check-full` has run from 388 s to 4,235 s on nearly the same suite, and on 2026-10-01 a run with 39 more tests finished 2.5 times faster than one 75 minutes earlier. The cause is not known. About 4 of the 40 `slow` tests are simulations; the rest are engine runs, optimiser solves and estimator fits. The detail is in the Project doc `claude/check-runtime-2026-10-06.md`.

**Three numbers in task 49 are Cowork's, not the owner's.** Say so if any should move.
- **0.70:** parallel tests are adopted only if they cut the slow tier's wall time by 30% or more.
- **7 days:** a scoped check falls back to the whole suite if no full pass is on record in the last 7 days.
- **The new wording of `CLAUDE.md`'s definition of done,** which names `make check-scoped`. It is in task 49, step 4f.

**It follows the D2 precedent:** no `decisions/` record, because nothing in `SUBSTRATE.md`, `params/` or `vetoes/` changes.

*What would reopen it:* task 49's receipt. If the replay in its step 4e fails, the scoped tier is not wired and `check-full` stays the definition of done.

### L21. Negative `eop_lag` on seven JPMaQS tickers (added 2026-10-02, HANDOFF task 44 part B) — CLOSED 2026-10-02 (HANDOFF task 46 landed)
**Owner, 2026-10-02 ("accept"):** keep the seven tickers; for JPMaQS a period may end after the number is known; the holdout binds on the knowledge date. Recorded in `decisions/0047`, with a checkpoint: a lag below −92 days stops the build. *Landed in commit 3519b1c (HANDOFF task 46); the checkpoint passed: no row is below -92 days.*

The JPMaQS pull `P-20261002T032635Z` landed (150,644 rows, 26 tickers). The
loader refused it, as task 44 specifies: **13,562 valued rows have a negative
`eop_lag`**, which puts `period_end` after `knowledge_date`, and `VintagePanel`
rejects that. None are NaN or infinite. Rows by ticker (of the ticker's rows):
`USD_BLSCSCORE_NSA_D2Q2QL2` 4,354 (7,149); `USD_MBCSCORE_SA` 3,182 (7,813);
`EUR_BLSCSCORE_NSA_D2Q2QL2` 3,131 (4,158); `JPY_INTRGDP_NSA_P1M1ML12_D3M3ML3`
2,189 (5,447); `EUR_MBCSCORE_SA` 360 (7,806); `EUR_INTRGDP_NSA_P1M1ML12_D3M3ML3`
224 (4,871); `GBP_INTRGDP_NSA_P1M1ML12_D3M3ML3` 122 (5,440). The other 19
tickers are clean. Claude Code's guess, not verified: survey scores and some
forecast-horizon series carry a reference period that ends after the date the
number is published.

Nothing was clipped, dropped or shifted, and no macro snapshot or coverage
report exists. The options are the owner's: **drop those seven**; **define
`period_end` for them some other way** (say, `min(real_date - eop_lag,
real_date)`, which says they are known on the day their period ends); or
**loosen `VintagePanel`'s check for them**, which touches the bitemporal
convention of `decisions/0014`. Which hypotheses each ticker serves is in
`data/requests/ticker_resolution.csv`.

*What would retire it:* the owner's choice, then a small task. No measurement.

### L22. The loading-estimator test's score is dominated by the cash index (added 2026-10-02, HANDOFF task 45) — CLOSED 2026-10-02 (HANDOFF task 46 landed)
**Owner, 2026-10-02:** "yes exclude cash". Recorded as the addendum to `decisions/0046`; the run without Cash is the result of record. *Landed in commit 3519b1c (HANDOFF task 46); the checkpoint passed: no row is below -92 days.*

`decisions/0046` scores every investable backbone and second-tier instrument
and scales each error by the instrument's robust volatility "so no instrument
dominates". `LD20TRUU` (the T-bill index, class `Cash`) has a robust volatility
near zero, so any loading error scaled by it is enormous: in run
`M-20261002T033239Z` it is about 100% of the loss differential for Huber, the
HMM and Kalman (statistics of order 1e5 to 1e7, which mean nothing). The run was
kept as specified. The sensitivity run `M-20261002T034221Z-sens` excludes the
Cash class and gives the same four verdicts, all `not_detected`, so nothing
recorded changes. The owner decides whether the registered spec excludes the
Cash class (the factors are themselves returns net of cash, so a loading of cash
on them is not an obvious measurement target) before any estimator is adopted or
the test is re-run.

*Also worth the owner's eye:* rolling OLS, the incumbent, reads 1.80 against the
1.72 bias ceiling in 2008, so it would itself fail the uncertainty check.

*What would retire it:* the owner's ruling on the Cash class.

### L4. Holdout power belongs in SUBSTRATE §3 — CLOSED 2026-10-01 (HANDOFF task 43 landed)
**Owner, 2026-10-01:** Cowork's draft §3 paragraph (0039 §3 + L4) is accepted. It is applied in SUBSTRATE v0.8, and `decisions/0039` carries the note. *Move to Closed when HANDOFF task 43 lands.*

~350 weeks gives t ≈ 0.8 at a true IR of 0.30, so the holdout can only ever
fail a strategy, never confirm one. That is a material property of the lab's
own final test and it is currently recorded only in these notes. Transcribing
it into §3 is an owner act.
*Cowork, 2026-10-01: a draft §3 paragraph combining 0039 §3 and this item is in
the Project doc `claude/task-42-review-2026-10-01.md` §4. It follows 0043's
gate, not 0039's FDR wording.*

### L19. What the 6% tracking-error budget means: a sizing target or a ceiling (added 2026-10-01) — CLOSED 2026-10-01 (HANDOFF task 43 landed)
**Owner, 2026-10-01 ("I accept your recs"):** (a), the 6% is the ex-ante sizing target σ, and the p95 is disclosed. Recorded in `decisions/0044`. *Move to Closed when HANDOFF task 43 lands.*

Task 35 (`A-20260930-033812`), policy arm (h26 scalar), recomputed by Cowork:
the mean ex-ante TE is 5.8-5.9% and realised/ex-ante is 0.95-0.99, so the book
is sized correctly on average. But the **p95 of trailing-3y realised TE is
1.12-1.19x the 6% budget** (seeds up to 1.39x). With no overlay it is 1.27-1.34x.

The ratio sits above 1 because a 3-year window swings around its mean. It is
not a sizing error. The choice:
- **(a) 6% is σ, the sizing target.** That is how `decisions/0025` derives
  it. Nothing changes; p95 is disclosed (0030).
- **(b) 6% is a ceiling a client sees on trailing-3y TE.** Size to about 5.1%
  (6%/1.18) and re-anchor 0025's map.

`params/constraints.yaml` names it `max_trailing_3y`, and its comment still
says §10 vetoes it (stale since 0030), which reads like (b). Cowork leans (a)
if the number is the lab's own and (b) if it is an investor-facing mandate.
**Retired by:** the owner's reading of the 6%, recorded in `decisions/`.

### L20. The gate passes every hypothesis in a search smaller than g (added 2026-10-01) — CLOSED 2026-10-01 (HANDOFF task 43 landed)
**Owner, 2026-10-01 ("I accept your recs"):** g = 1 below m = 8, and g = 2 at or above it. Recorded in `decisions/0045`. *Move to Closed when HANDOFF task 43 lands.*

`romano_wolf_gfwer` with g = 2 sets the critical value to −∞ when a set has
fewer than 2 tests. So **a single-hypothesis search is rejected (passes)
unconditionally**, and bar 2 reduces to `net_ir_excess > 0`.

This is correct for g-FWER, since one test can't make two false passes. But
the first planned real test (0009 alone) is m = 1, and L12's
`family_then_within` runs inside one-hypothesis families. Cowork's check
(independent nulls, k = 100, step 1): the false-pass rate per null hypothesis
is 1.00 at m = 1, 0.22 at m = 2, 0.10 at m = 4, 0.05 at m = 8 and 0.03 at
m = 12. Proposed amendment to 0043: **g = 1 below a floor of about m = 8, and
g = 2 at or above it**, with L12 deciding which m counts. Detail is in the
Project doc `claude/task-42-review-2026-10-01.md` (F1). **This must be settled
before the phase-2 solver runs a real hypothesis.**
### L16. A screen at a confirmation standard, and what confirms a candidate — CLOSED 2026-10-01 (HANDOFF task 42 landed)
**Owner, 2026-10-01, L16(a):** the generalized stepdown, P(two or more false passes) ≤ 5%, at 100 shuffles per test. Cowork picked 100 within the approved 50-100 range. Recorded in `decisions/0043`. Applied by HANDOFF task 42; SUBSTRATE v0.7 and `params/vetoes.yaml` were edited by Cowork. *Task 42 landed 2026-10-01.*

Added 2026-09-28 by Cowork, from the owner's L15 ruling ("screen",
`decisions/0039`). Two things are unruled:
- **FWER or FDR.** Romano-Wolf at FWER 5% controls the chance of *any* false
  pass, a confirmation standard. A screen usually controls the *share* of false
  passes (FDR, SUBSTRATE §9). Keeping FWER means screening at a confirmation
  standard, with 35-45% power at IC 0.70 before the stepdown.
  **Owner, 2026-09-28: "most likely FDR", to be confirmed after task 34's
  FDR-vs-FWER numbers are read. Not ruled.**
  **Task 34 reported 2026-09-29** (`results/fdr_vs_fwer/20260929-031720/`,
  Cowork doc `claude/tasks-34-36-review-2026-09-29.md`). The number of
  shuffles per test, k, decides more than FWER vs FDR:
  - At k ≤ 100, Romano-Wolf 5% has more power than BH 10% (IC 0.70: 0.175 vs
    0.152 at k = 100, and 0.144 vs 0.013 at k = 20).
  - BH 10% wins only at k ≥ 500 (0.274 vs 0.174).
  - k = 500 costs about 140 engine-hours per cycle.

  RSW-FDR, which uses the joint null like Romano-Wolf, was not implemented:
  the task cited the wrong paper (Cowork's error). The right one is Romano,
  Shaikh & Wolf 2008, *TEST* 17(3). **Cowork recommends not ruling yet:**
  implement RSW-FDR from that paper, re-run the study with small k (20-200),
  then choose.
  **Owner, 2026-09-29: yes, and Claude Code may fetch the paper.** Queued as
  HANDOFF task 38. L16(a) is still open until its numbers are read.
  **Task 38 reported 2026-09-29 (`459a257`, `results/fdr_vs_fwer/20260929-154138/`,
  verified by Cowork):**
  - RSW-FDR is **still not implemented**. Claude Code fetched and read the
    paper, but couldn't pin down which stepdown rank each critical value
    belongs to. One reading gave 100% FDR under the null; the other gave zero
    power on a 4-sigma signal. Cowork's note: the zero-power result could be
    an implementation bug rather than a wrong reading. That is unresolved.
  - The study (5,000 reps) now reports pFDR, the false share given at least
    one pass.

  | IC 0.70, n_true 3 | k=20 | 50 | 100 | 200 | 500 | 1000 |
  |---|---|---|---|---|---|---|
  | RW 5% power / pFDR | 0.15 / 0.06 | 0.15 / 0.05 | 0.17 / 0.06 | 0.17 / 0.06 | 0.17 / 0.07 | 0.18 / 0.06 |
  | BH 10% power / pFDR | 0.01 / 0.54 | 0.07 / 0.31 | 0.14 / 0.22 | 0.25 / 0.14 | 0.27 / 0.13 | 0.29 / 0.14 |

  At IC 0.35, RW has power 0.035 and pFDR about 0.25; BH 10% has 0.07 and
  about 0.33 at k ≥ 200.

  **Cowork's recommendation: the ruling is really about compute.** A cycle
  costs about 12 × k × 84 s: 28 h at k = 100, 56 h at k = 200, 140 h at
  k = 500.
  - **At a budget of k ≤ 100:** keep Romano-Wolf at FWER 5%. It has more
    power and a quarter of BH's false share.
  - **At k ≥ 200:** BH at FDR 10% buys about +45% power, and 1 in 7
    candidates is false against 1 in 16.
  - **Drop RSW-FDR** for now. Two faithful attempts failed, and BH already
    represents the FDR option.
  The owner has deferred the two-step and bootstrap-null variants (D7).
  **Owner, 2026-09-29 (evening):** the joint null is a block shuffle, not a
  bootstrap: SUBSTRATE §9 is amended by `decisions/0041`, with confidence
  intervals left on the bootstrap. A third option is now being measured:
  **generalized FWER**, P(2 or more false passes) ≤ α, which reuses
  Romano-Wolf's joint null. It is queued as HANDOFF task 40, together with
  standardising `romano_wolf` so that no hypothesis dominates the maximum by
  scale. **L16(a) stays open until task 40's numbers are read.**
  **Task 40 reported 2026-09-29** (`c0c4093`,
  `results/fdr_vs_fwer/20260929-204223/`). `romano_wolf_gfwer` is implemented
  from Romano & Wolf (2007), *Annals of Statistics* 35(4), Algorithm 2.1
  (fetched from arXiv:0710.2258); standardising `romano_wolf` is implemented
  and is now the default. Under the complete null at k=1000, `p_two_plus_false`
  sits within ~2 MC standard errors of nominal alpha for both variants
  (rw_g2_5: 0.056 vs 0.05; rw_g2_10: 0.109 vs 0.10) — the guarantee the
  procedure actually makes holds.

  | IC 0.70, n_true 3, rho_w 0.3, rho_b 0.2 | k=20 power/fwer | k=1000 power/fwer |
  |---|---|---|
  | romano_wolf_5 (standardised) | 0.218 / 0.099 | 0.179 / 0.042 |
  | rw_g2_5 | 0.343 / 0.224 | 0.348 / 0.177 |
  | rw_g2_10 | 0.419 / 0.309 | 0.426 / 0.276 |
  | bh_10 | 0.010 / 0.011 | 0.289 / 0.154 |

  Like the FWER-vs-FDR choice, `rw_g2_*`'s power is roughly flat across k
  (joint-null max), so it doesn't buy back power by spending shuffle budget
  the way `bh_10` does. **A fourth option is now on the table alongside plain
  Romano-Wolf and BH:** generalized FWER at g=2 nearly doubles power over
  plain Romano-Wolf at any k, at the cost of tolerating a single false pass
  17-22% of the time (only *two or more* false passes are held near 5-10%).
  Whether that tradeoff is acceptable given L15's "screen" ruling is unruled.
  **L16(a) stays open.**

  **Also outstanding, not a judgement call:** `decisions/0041`'s SUBSTRATE §9
  and §15 edits are drafted (verbatim diff in task 40's HANDOFF receipt) but
  **not applied** — Claude Code's permissions refuse writes to `SUBSTRATE.md`
  outright, so this needs Leo or Cowork to apply the three-line diff directly.
  Task 40 also deferred tasks 35 and 39 to the next overnight run (time budget
  against a same-day deadline, not a finding).
  **Correction, 2026-09-29 late evening (Cowork, verified against
  `results/fdr_vs_fwer/20260929-204223/summary.csv`):** the k=20 and k=50 rows
  above are **invalid**. Task 40's standardising used only the null draws'
  mean and sd (Cowork's spec error), which breaks exchangeability. Under the
  complete null, `romano_wolf_5` FWER is 0.127 at k=20 and 0.064 at k=50
  (nominal 0.05), and `rw_g2_5` P(V>=2) is 0.083 at k=20. The k≥100 rows are
  within about 0.01 of nominal. The fix (pool the observed value into the
  mean and sd) is HANDOFF task 41, which re-runs the study. **Don't read the
  small-k power figures until task 41's numbers are in.**
  **Task 41 reported 2026-09-29 (late evening)** (`0a5645f`,
  `results/fdr_vs_fwer/20260930-031720/`): the fix holds. Complete-null,
  headline correlation, k=20: `romano_wolf_5` FWER 0.052 (was 0.127),
  `rw_g2_5` P(V>=2) 0.049 (was 0.083), `rw_g2_10` P(V>=2) 0.098 (nominal
  0.05/0.10) — all within 2-3 MC standard errors of nominal. Against task
  38's pre-standardisation baseline, max |delta FWER| across all (mu, n_true,
  k) cells is now 0.0074 (was 0.066-0.078), consistent with MC noise rather
  than a real shift. **The small-k power/FWER table in the correction above
  is now safe to read** — task 40's g=2 tradeoff description (near-doubled
  power over plain Romano-Wolf, at the cost of a single false pass 17-31% of
  the time) stands under the fix; the earlier `T0`-only numbers it was partly
  drawn from were also individually within noise of the pooled ones except at
  k=20/50, where the direction of the finding (more power, more single-false-
  pass risk) is unchanged. L16(a) stays open.
- ~~**What confirms a candidate.**~~ **Ruled 2026-09-28:** replication and
  economic intuition are the gates, both required. A paper track and a live
  allocation are not. Recorded in `decisions/0039`. ~~Whether to adopt Cowork's
  operational proposal~~ **Ruled 2026-09-28: "yes, adopt all three"**: a thesis
  synthesis that lists what must be true, a replication target fixed before
  looking, and named rival explanations. Recorded in `decisions/0039`.
L4's holdout-power sentence should land in SUBSTRATE §3 in the same edit as
0039's paragraph.
**Partly retirable by measuring:** HANDOFF task 34 (queued 2026-09-28)
measures the power and the realised error of FWER against FDR on the registry's
shape. The choice stays the owner's.

### B1. Whether the volatility overlay becomes policy, and at what halflife — CLOSED 2026-10-01 (HANDOFF task 42 landed)
**Owner, 2026-10-01: policy, at 26 weeks** (Cowork's recommendation: 13 and 26 can't be told apart, and 26 was specified before the sweep). Recorded in `decisions/0042`. Applied by HANDOFF task 42; SUBSTRATE v0.7 and `params/audit.yaml` were edited by Cowork. *Move this item to Closed once task 42 lands.*

Built and tested: seed-paired over 5 seeds at h=13, a scalar 26-week overlay
moved 2008 bias −0.36/−0.54, calm-year bias +0.10, `te_p95` −0.0141 at IC 0.20
in all five seeds, and net IR up +0.10/+0.06. All ten paired calibration
differences went the right way.

**Retired by:** a halflife sweep across horizons. 26 weeks was the only value
tested, at one horizon and two IC rungs. Nothing reads it by default.
**Queued 2026-09-28 as HANDOFF task 35** (owner's L13 ruling). Blocked until it
reports.

**Note for when it lands:** it competes with `H-2026-0008` for the same
variance. Once the book de-risks through its covariance, 0008 must be measured
as incremental to that, not against a never-de-risks baseline, or it gets
credited for what the risk model did.

**Task 35 reported 2026-09-30** (`A-20260930-033812`, HANDOFF receipt has the
full tables). 240/240 cells, rc=0. The h13 no-overlay arm matched the knee
run's live cell to float epsilon at all 20 (ic, seed) pairs, so the sweep is
measuring the same book the earlier, narrower test did.

- **`risk_calibration` fails drop from 5-10 of 20 (no overlay, per horizon)
  to 0-2 of 20 with any halflife arm**, at every horizon (4, 13, 26), not
  just h13. Worst-annual bias falls from a 1.55-1.72 median (no overlay) to
  1.31-1.52 with an overlay; how many cells have 2008 as the worst year falls
  from 15-17/20 to 3-13/20 depending on the arm.
- **Net IR at h13 (the horizon B1's original test used): halflife 13 and 26
  both gain against the no-overlay control in 7-9 of 10 seeds at both IC
  rungs**, mean paired gain +0.05 to +0.07, sd 0.07-0.12 (se ~0.02-0.04) — the
  most consistent net-IR case in the grid. h4 and h26 are mixed in sign.
- **Halflife 13 vs 26 vs 52:** 13 and 26 are close on both risk calibration
  and net IR; 52 is weaker on the h13 net-IR gain at IC 0.35 (-0.003, not
  distinguishable from zero) though still clears risk calibration. Nothing in
  this sweep singles out 26 (the value B1's original test used) as better
  than 13.
- **Not part of this measurement, flagged in the receipt anyway:**
  `te_p95_to_budget` stays above 1 in every cell regardless of overlay
  (1.13-1.34) — an overlay narrows the gap (best at halflife 13) but does not
  close it on this reading.

**Still the owner's call:** whether the overlay becomes policy, and if so at
which halflife (13 and 26 are the strongest candidates on this evidence, 52
the weakest). Not ruled here.

### L17 — how wide the 200% turnover highlight reaches. CLOSED 2026-09-29.
**Owner: "both"**, meaning the annual figure and the rolling one-year p95. The
rolling max is still reported but not highlighted. Recorded as an addendum to
`decisions/0038`, and applied with 0040 by HANDOFF task 39. The full item
text is in git history.

### L18 — the shadow cost's 53-week echo. CLOSED 2026-09-29.
**Owner:** option (a) on 2026-09-28, then **"0040: 40bps"** on 2026-09-29 after
task 36 (`A-20260929-070540`): the largest week is at most 0.84× NAV, with no
detectable change in net IR. `decisions/0040` is adopted at 40 bp and applied
by HANDOFF task 39. A residual lag-52 rhythm (0.24-0.30 at 40 bp) remains; an
exponentially weighted window is the fix if it ever matters. The full item
text is in git history.

### D2 — the test-suite split. CLOSED 2026-09-29.
**Owner: "yes"**, after `make check` reached 3695 s. HANDOFF task 37 splits it
into a fast `make check` and a full `make check-full`.

### L13 — `risk_calibration` vetoes a quarter to a half of every grid, on 2008. CLOSED 2026-09-28.
**Owner: "approved, go ahead"**: B1's halflife sweep is queued now as
critical-path work, HANDOFF task 35. Whether the overlay then becomes policy is
B1, blocked on task 35. The friction sweep adds one data point: 21 of 60 cells
fail, 2008 is the worst year in 50 of 60, and friction does not move it
monotonically. The full item text is in git history.

### L14 — twelve JPMaQS tickers that didn't exist as named. CLOSED 2026-09-28.
The owner renamed H-0001 (2026-09-24) and 0004, 0005 and 0010 (2026-09-27,
"recs on all", plus dropping `DRTSCILM`), recorded as addenda to
`decisions/0032`. Task 31's vendor check: **26 of 26 resolve**
(`7ce2dff`), and `data/jpmaqs/request.txt` is written. The full item text is in
git history (`2448f52`).

### L15 — bar 2's power and what the lab is for. CLOSED 2026-09-28.
**Owner: "screen."** A pass on both bars makes a hypothesis a *candidate*, and
a bar-2 failure is *not detected*, not false. Recorded in `decisions/0039`. The
evidence is task 30 (`A-20260926-161749`): about 35-45% power at IC 0.70, 4 of
10 seeds. Follow-ups are in L16.

### B3 — the 400% turnover backstop. CLOSED 2026-09-28.
**Owner:** "400% level is only reported. Actually anything over 200% should be
highlighted, but no veto. Drop the 400% as a reference." No veto in any window.
The friction sweep is approved. Recorded in `decisions/0038`, together with B2.
Applied by HANDOFF task 33; the sweep is task 32. Reading "anything over 200%"
as both the annual figure and the rolling one-year max is Cowork's
interpretation, noted in 0038.

### B2 — the per-session (per-rebalance) turnover cap. CLOSED 2026-09-25.
**Owner:** no per-rebalance turnover cap. Turnover is restrained by friction,
the costs and the shadow cost of `decisions/0024`. This is already the state
of `params/audit.yaml` (`per_rebalance_cap_default: null`), so no params
change. The `per_rebalance_caps` sweep stays a diagnostic. Recorded in
`decisions/0038` (2026-09-28).

### L11 — SUBSTRATE §3 and the second bar. CLOSED 2026-09-21.
**Decided and transcribed the same day.** SUBSTRATE is at **v0.5**: §3 replaces
the single primary metric with the two bars of `decisions/0036` §6, and §10's
`multiple_testing` row names `net_ir_excess` as the statistic it tests. The
owner instructed the amendment; Cowork held the pen and originated nothing, per
§2. The commit cites `decisions/0036` and is its own diff for review, following
the `decisions/0030` precedent.

Nothing in `params/` or `vetoes/` moved: bar 1 keeps `target_net_ir: 0.30` and
bar 2 is the `multiple_testing` veto that `params/vetoes.yaml` already
configures at `fwer_alpha: 0.05`.

### L9 — the bar, after the no-information floor. CLOSED 2026-09-21.
**Decided: two bars.**

**Bar 1, the product bar, on the level: net IR >= 0.30.** Unchanged in value and
derived for the first time. The owner's appetite is 150 bp of active return, and
at the 5-6% budget `150 / 500 = 0.30`. `decisions/0023` carried that number on a
quotation alone; it now has a derivation. **`params/audit.yaml` does not change,
and `decisions/0025`'s tracking-error budget is unmoved** — 0025 derives the
budget from the IR an investor experiences, which is the level, and the level is
still 0.30. The coupling this item warned about does not fire.

**Bar 2, the evidence bar, on the excess: no number, a significance test.**
`net_ir_excess > 0` and survival of Romano-Wolf at FWER 5% with the excess as
the test statistic. A threshold is the wrong instrument: `decisions/0036` §1
shows the floor is the mean of a **420 bp-wide** distribution (-141 to +280 bp,
12% of tilts negative) on a **single history**, so any number subtracted from it
inherits that noise. **The gate already exists** — SUBSTRATE §10 lists
`multiple_testing` and `params/vetoes.yaml` already sets `romano_wolf`,
`fwer_alpha: 0.05`, `family_then_within`. It has simply never been
implementable, because `src/signal_lab/stats/` was one line until 0036 §4(a)'s
block shuffle landed.

**The owner's reasoning, in his words:** 150 bp is satisfactory, "but I also
don't want to arrive at it simply because I reached an arbitrary combination of
betas that already tends to achieve that 150 bps in the sample period we are
analyzing." Two questions, two bars. A candidate clearing bar 1 but not bar 2 is
beta available more cheaply; one clearing bar 2 but not bar 1 is a real signal
not worth the operational cost.

**Why this closed rather than staying blocked.** The half of this item that
waited on tasks 18 and 20 was the *number*, whose required-IC arithmetic depends
on the response shape between IC 0.20 and IC 1.00. Neither bar needs that shape:
bar 1 is a product statement at a given risk level, bar 2 is a test. Tasks 18
and 20 remain worth running — they measure whether this lab can *detect* a
signal that clears bar 2 — but they are off the bar's critical path.

**One owner act still outstanding, tracked as L11:** naming the excess statistic
in SUBSTRATE §3 and saying there that `multiple_testing` runs on it.

Raised 2026-09-20 when the floor was measured at 0.311 against a 0.30 bar;
closed 2026-09-21.

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

