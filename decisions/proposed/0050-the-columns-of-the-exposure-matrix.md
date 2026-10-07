# 0050 (proposed) — The columns of the exposure matrix, and which cells are measured

**Status:** proposed 2026-10-07 by Cowork. **Not decided.** OWNER-QUEUE L27.
Nothing may be built from this file until the owner rules.

## The gap

`decisions/0049` chose the estimator and the factors. It did not say what the
matrix's columns are. Two records answer differently:

- **SUBSTRATE §6** forms views on seven axes: duration, credit, region,
  sector, style, real/nominal and cash. A hypothesis targets one of them.
- **`decisions/0046` §1** estimates loadings on six factors: equity, real
  yield, inflation, credit, dollar and commodities.

Three of the six factors have an axis (real yield with duration, inflation
with real/nominal, credit with credit). Three do not (equity, dollar,
commodities). Four axes are labels, not betas (region, sector, style, cash).

## Cowork's proposal

**1. The matrix has two blocks.**
- **Factor block, six columns:** the Huber loading on each factor, with its
  standard error, or a measured value where one exists.
- **Label block:** region, sector, style and cash, one column per label, from
  `data/universe/investable_universe.csv`. All measured.

**2. The seven axes read from those columns.**

| Axis | Reads | Unit |
|---|---|---|
| duration | minus the real-yield column | years |
| real/nominal | minus the inflation column | years of breakeven sensitivity |
| credit | minus the credit column | years of IG-spread sensitivity |
| region, sector, style, cash | the label block | 0 or 1 |

**3. Equity, dollar and commodities are columns but not view axes.** They
serve the risk decomposition and are the controls that keep the other betas
clean. Making them axes a hypothesis can target would amend SUBSTRATE §6 and
the hypothesis vocabulary. *Cowork leans against doing that now.*

**4. Which cells are measured.**
- **Real yield, for Treasuries, Long Treasuries, TIPS and IG Corporates:**
  minus the index's effective duration (`INDEX_OAD_TSY`). The regression reads
  −10.4 where the long Treasury index's duration is 14.6.
- **Inflation, for the same indices:** minus the duration for nominal bonds,
  zero for TIPS.
- **HY Corporates and MBS: not proposed yet.** Their returns may not follow
  their stated duration closely. HANDOFF task 51 reports estimated against
  measured for every bond index, and the choice should be read from that.
- **Credit: estimated everywhere, for now.** The panel has no spread
  duration. Duration times spread is the usual measure and could be built
  from `INDEX_OAD_TSY` and `INDEX_OAS_TSY`. *Cowork has not tested it.*
- **Everything else is estimated,** including every cell of every equity,
  commodity and non-dollar bond index. A non-dollar bond's own duration is to
  its local yield, which is not a factor (OWNER-QUEUE L25).

**5. Every cell carries its provenance** (`measured` or `estimated`), and
every instrument its explained share (`decisions/0049`).

## What the owner would be deciding

- **(a)** The two-block layout and the axis table.
- **(b)** Whether equity, dollar and commodities become view axes.
- **(c)** The measured overrides in point 4, and whether credit gets one.
- **(d)** The region labels. They are still placeholders (`decisions/0022`,
  OWNER-QUEUE D3), and four of twelve hypotheses target `region`.

## What it would touch

- `vetoes/rules.py`: the `lookahead` veto's extension to estimated parameters
  (owner-only, by patch).
- `harness/experiment.py`: `resolve_exposures` stops raising.
- SUBSTRATE §6, only if (b) is yes.
