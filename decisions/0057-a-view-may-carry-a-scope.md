# 0057 — A view may carry a scope: how a hypothesis uses a bond's labels

**Status:** decided 2026-10-11 by the owner (OWNER-QUEUE L28). Cowork proposed
it at his instruction ("design and ammend"); he answered "0057: B approved as
is". **Design B, the vocabulary and its mapping, the minimum reach of rule 4,
and the SUBSTRATE wording are all ruled as written below.** SUBSTRATE §6 and
§7 are amended in v0.11, transcribed by Cowork. Follows `decisions/0050`,
`0051` and `0054`. No change to `params/` or `vetoes/`.

## The problem

`decisions/0054` item 6 labels each bond by three things: its curve currency,
its rating class and whether its market is developed or emerging. The owner
ruled the labels on 2026-10-11 and wants hypotheses to be able to use them.

SUBSTRATE §6 has seven view axes. Under `decisions/0051` a view becomes an
expected return on every instrument that carries its axis. So a duration view
reaches every instrument with a duration cell: every bond, and every equity
through minus its real-yield loading. There is no way to say "duration on the
euro curve", "credit in HY only" or "EM credit against DM credit".

## Two designs

**A. New axes: curve, rating and market.** *Not recommended.*
- They are categories, not exposures. "The euro curve" is not something a
  portfolio is long or short of. It says *which* duration.
- A rating axis would sit on top of the credit axis, which already scales
  with credit risk through the credit loading.
- Three new axes would mean more registered tests on correlated quantities,
  the concern of L12.

**B. A scope on an existing axis.** *Recommended.* A hypothesis may restrict
the instruments its view reaches, by label, in one of two forms.

- **`scope`, a filter.** The view reaches only instruments whose label is in
  the set. The expected return on instrument *i* is the view, times *i*'s
  exposure on the axis, times 1 if *i* matches the scope and 0 if not.
  - *Duration on the euro curve:* `target_axis: duration`,
    `scope: {curve: [EUR]}`.
  - *Credit in HY only:* `target_axis: credit`, `scope: {rating: [HY]}`.
- **`group_by`, a cross-section across one label.** The signal gives one
  score per label value, the way a region signal gives one per region. Each
  instrument receives its own group's score times its exposure on the axis.
  - *EM credit against DM credit:* `target_axis: credit`, `group_by: market`.
- **An instrument without the label never matches.** An equity has no curve,
  so a curve-scoped duration view never reaches an equity.
- **No new column in the exposure matrix.** The axis cells stay as
  `decisions/0050` rules them. The labels sit beside them.

## The vocabulary a scope needs

A scope matches on exact values, so the labels need a fixed vocabulary. The
ruled labels are free text (`decisions/0054`) and stay as written; three
normalised columns sit beside them. **Every mapping below was Cowork's;** the
owner ruled it as written.

| Normalised column | Values | From the ruled label |
|---|---|---|
| `curve` | `USD` | USD |
| | `USD_real` | USD real (`LBUTTRUU`) |
| | `EUR`, `GBP`, `JPY` | as labelled (`LET1TREU`, `I12823GB`, `I02913JP`) |
| | `EUR_multi` | European, several (`I02513EU`, `LP05TREU`) |
| | `DM_multi` | Several, EUR, JPY, GBP and others (`LG38TRUU`) |
| | `EM_local_multi` | EM local, several (`I20344US`) |
| `rating` | `Government` | Government; Government (bills); Government, inflation-linked; Government, mixed IG and HY (`I20344US`) |
| | `Agency` | Agency MBS |
| | `Aggregate` | Aggregate, IG; Aggregate, IG (mostly government) |
| | `IG` | IG |
| | `HY` | HY Ba, HY B, HY Caa, HY all ratings. A fourth column, `hy_bucket` (`Ba`, `B`, `Caa`, `all`), keeps the split |
| | `Mixed` | Mixed IG and HY (`EMUSTRUU`, `I12877US`) |
| `market` | `DM` | DM; DM, with some EM (`LG38TRUU`) |
| | `EM` | EM |

**An index that spans several curves matches only its own `_multi` value,**
never a single-currency scope. Splitting it would need its currency weights,
which the lab does not have.

## How far each scope reaches today

Counted on the 23 bonds with a label row (the 24 of `0054` less `LTP5TRUU`,
which is tradable-only), from `Claude outputs/label_map_draft_2026-10-11.csv`.
Cash (`LD20TRUU`, USD, Government) is labelled too and is left out here.

| `curve` | Bonds | `rating` | Bonds | `market` | Bonds |
|---|---|---|---|---|---|
| USD | 15 | Government | 10 | DM | 20 |
| USD_real | 1 | Agency | 1 | EM | 3 |
| EUR | 1 | Aggregate | 2 | | |
| GBP | 1 | IG | 3 | | |
| JPY | 1 | HY | 5 | | |
| EUR_multi | 2 | Mixed | 2 | | |
| DM_multi | 1 | | | | |
| EM_local_multi | 1 | | | | |

**This is the finding to weigh before ruling.** Every curve but USD holds one
instrument, and the euro one is a 1-3 year index. "Duration on the euro curve"
would be one short-duration index, and `group_by: curve` would mostly compare
USD against single indices. The design works, but the universe is thin for
curve views. More curve-specific bond indices would be a data request (phase
2), not a design change.

## Rules that keep a scope honest

1. **A scope is pre-registered,** in the hypothesis file, before any result is
   seen. It is never changed after a run.
2. **The same signal under another scope is another hypothesis and another
   test** in the stepdown (SUBSTRATE §9). Trying scopes until one passes is
   the search the gate exists to charge for.
3. **Coverage is measured on the scoped set.** The `coverage` veto's
   "estimation universe" (SUBSTRATE §10) is the instruments the scope
   reaches.
4. **A minimum reach** (ruled as Cowork proposed it): a `scope` must reach at
   least two instruments with a row on 90% of dates, or the hypothesis must
   declare `expected_expression: directional`, because a view on one index is
   timing, not a cross-section.
5. **Region stays as `0054` ruled it.** The region axis reads equities only.
   A scope may also name `region`, for example `scope: {region: [EM]}` on the
   credit axis.

## SUBSTRATE — the wording, applied in v0.11 (owner approved 2026-10-11: "B approved as is")

**§6,** a new bullet after the one that begins "Views are formed in
**exposure space**":

> - A view may carry a **scope**, a set of values of an instrument label (a
>   bond's curve, rating or market; an instrument's region) that restricts the
>   instruments it reaches, or a **grouping** by one such label, giving one view
>   per value. Its expected return on an instrument is the view times the
>   instrument's exposure on the axis, and zero on an instrument outside the
>   scope or without the label. Labels are the owner's map (`decisions/0054`,
>   `0057`), not estimates. A scope is registered with its hypothesis; the same
>   signal under another scope is another hypothesis and another test (§9).

**§7,** after the template's `expected_expression` line:

```yaml
scope:                       # optional; label -> allowed values (decisions/0057)
  curve: [EUR]
group_by: market             # optional; one view per label value; not with scope on the same label
```

## What it would take to build

- **The normalised columns** in `data/universe/label_map.csv`, written from
  the table above.
- **`scope` and `group_by` in the hypothesis validator** (`harness/hypotheses.py`):
  known labels, known values, and the minimum reach.
- **The mapping from a view to expected returns** belongs to the phase-2
  solver (`decisions/0051`), which does not exist yet. A scope is a mask on
  that mapping and is built with it, not before.

## What the owner decided

1. **Design B.**
2. **The normalised vocabulary and its mapping,** as in the table above,
   uncorrected.
3. **The minimum reach of rule 4:** a `scope` reaches at least two instruments
   with a row on 90% of dates, or the hypothesis declares
   `expected_expression: directional`.
4. **The SUBSTRATE wording,** as above.

## Where it is built

- **The normalised columns** (`curve`, `rating`, `hy_bucket`, and the
  normalised `market`): HANDOFF task 55, in `data/universe/label_map.csv`.
- **`scope` and `group_by` in the hypothesis validator, and the mask on the
  view-to-alpha mapping:** with the phase-2 solver. Rule 4 needs the rows of
  the exposure matrix by date, so it is checked where the matrix is read.
