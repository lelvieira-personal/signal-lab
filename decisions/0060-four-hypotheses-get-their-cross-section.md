# 0060 — Four hypotheses get their cross-section: by rating and HY bucket, or by curve; a missing instrument is a data request, not a redesign

**Status:** decided 2026-10-14 and 2026-10-15 by the owner (OWNER-QUEUE L38).
Drafted by Cowork. Follows `decisions/0051`, `0054`, `0057` and `0059`.
**Amends `0051`** (instrument-level signals, item 3) and **`0057`** (a
`group_by` over a label refined by a second, item 1). No change to `params/`
or `vetoes/` here. **SUBSTRATE §6 and §7 need new wording** (owner-only);
it is proposed at the end and not applied.

## What the owner said

- **2026-10-14, 15:18,** on L38: "when there is no grouping the hypothesis can
  be done at instrument level, but for these hypotheses specifically I
  believe that rating and curve would work as groups."
- **2026-10-14, 15:26:** "i don't want to adapt a hypothesis just because we
  didn't download the data for a specific tradable instrument, especially if
  all that the hypothesis requires is something like more maturity buckets
  for a specific curve like the EUR curve which for sure we would have
  indices to follow. What I want to do in these cases is to ask for more
  data."
- **2026-10-15, 11:25:** "yes for rating with hy bucket."
- **2026-10-15, 18:24:** "yes on 0002 and 0003."

## What was found before he ruled

- The euro curve holds one index, `LET1TREU`, and it is the 1-3y: the 1-10y
  was requested and the pull returned the 1-3y (SUBSTRATE §5.4a). Every curve
  but USD holds one instrument (`0057`, the vocabulary table). The hedged
  Euro Treasury 1-10y (`H09122US`) is in the panel and excluded by `0013`.
- H-2026-0002 has core-inflation momentum for USD and EUR; H-2026-0003 has
  real policy rates for USD, EUR, JPY and GBP; H-2026-0010 has 10-year carry
  for USD and the Bund. Each can rank markets; none can rank them with the
  bonds the lab holds today.
- `rating` alone puts Ba, B and Caa in one `HY` group; `hy_bucket` keeps
  them apart.

## The rulings

1. **H-2026-0007: `group_by` rating, refined by `hy_bucket`.** The groups are
   the rating classes, with `HY` split into `Ba`, `B` and `Caa`. That is the
   six-segment ladder its rationale is built on (US IG, agency MBS, HY Ba, B
   and Caa, EM USD).
   - *Cowork's reading, from the hypothesis's own text:* `LF98TRUU`
     (`hy_bucket` `all`) forms no group in this cross-section, because "holding
     an index and its own components in the same cross-section
     double-counts".
   - *Cowork's proposal for the build, not ruled:* a group the hypothesis
     supplies no score for (here `Government`, `Aggregate`) gets no view, and
     its instruments carry none from this hypothesis.
2. **H-2026-0002, H-2026-0003 and H-2026-0010: `group_by` curve,** blocked
   on the data request below. Until it lands they cannot form their
   cross-section, and are not amended to fit the bonds the lab holds.
   - *Cowork's reading for 0002:* its groups are the curve's currency, so a
     linker and its nominal sit in one group (`USD` with `USD_real`, `EUR`
     with the euro linkers). The `0057` vocabulary keeps `USD_real` apart; the
     build maps the two together for this purpose.
   - 0002 and 0003 keep their directional test, which is defined today
     (`0059` ruling 2); `both` stays two tests.
3. **Where an axis has no grouping, a cross-section may be formed across
   instruments,** each instrument its own group. This amends `0051`, which
   did not authorise instrument-level scores. Recorded as the owner stated it,
   as a general rule. *Cowork asked whether it was meant for these four only
   and has no answer; read it as general until he says otherwise.*
4. **A missing instrument is a data request, not a redesign.** When a
   registered hypothesis cannot be formed because the lab lacks an instrument
   (a maturity band, a curve), the lab asks for the data. The hypothesis is
   not amended to fit what is held.

## The data request

The tickers were checked with Bloomberg's ASKB on 2026-10-15; the list,
with fields and what each serves, is `Claude outputs/bbg_pull_nonusd_govt_2026-10-15.csv`
(git-ignored).
- **Euro Treasury, all maturities and five bands:** `LEATTREU`, `LET3TREU`,
  `LET5TREU`, `LET7TREU`, `LET0TREU` (`LET1TREU` held). Daily from about 2002;
  the pull will show the day.
- **UK Gilts, all maturities and six bands:** `LSG1TRGU`, `I08043GB` to
  `I08048GB` (aliases `LF50TRGU` to `LF55TRGU`). Daily from 1999-01-29.
- **Euro inflation-linked:** `BEIG1T`, `BEIG3T`, daily from 2000-01-03. Their
  real-duration and real-yield fields are not yet known (the owner checks
  `FLDS` on the Terminal); 0002 needs them to match duration.
- **Japan Government:** `I29063JP` to `I29068JP`, from 2013-01-31 only;
  `I29063JP` did not resolve. Whether to add them is OWNER-QUEUE L39.
- **JPMaQS, metadata only:** whether 10-year carry exists for GBP and JPY,
  so 0010 has a score for more than two markets. A catalogue check, as in
  HANDOFF task 23.
- **Not requested:** the Germany bands (three index families, two without
  analytics); `LF87TREU`, `LF56TRGU`, `BKEU1T`, `BEIG2T` (duplicates or
  unused).

When the data lands, a new record admits the instruments (labels, cost
bucket, curve), the label map gains them, and the store is rebuilt.

## What it would take to build

- **The validator** (`harness/hypotheses.py`) accepts `group_by` as one label
  or a label refined by a second (`[rating, hy_bucket]`), with `0057`'s
  rules otherwise unchanged. It is built with the phase-2 solver (`0059`,
  "What it would take to build", item 2).
- **The four hypothesis files** gain their `group_by` line in the same task
  that teaches the validator the key, so the validator never sees a key it
  does not know. `0057` rule 1 holds: no result exists for any of them.
- **The instrument-level fallback** is a mapping rule in the same build.

## What it does not decide

- Japan (L39); the euro linkers' fields; the new-instrument record.
- How the phase-2 solver aggregates across hypotheses (`0059`).

## SUBSTRATE — proposed wording, not applied

**§7,** the template's `group_by` comment:

```yaml
group_by: market             # optional; one label, or a label refined by a second ([rating, hy_bucket]); not with scope on the same label (decisions/0057, 0060)
```

**§6,** after the sentence on cross-sectional expression: "Where an axis has
no grouping, the cross-section is formed across the instruments that carry
the axis, each its own group (`decisions/0060`)."
