# 0051 — Views become alphas; the stock/bond mix is an outcome

**Status:** decided 2026-10-07 by the owner (he chose "Alpha form" when
Cowork put the two forms to him). Drafted by Cowork. Follows
`decisions/0015` and `0050`. **It needs an amendment to SUBSTRATE §6, whose
wording is proposed at the end and is NOT applied** (OWNER-QUEUE L31). No
change to `params/` or `vetoes/`. Nothing is built from this record until a
task says so.

## The question

SUBSTRATE §6 says views are formed in exposure space and "mapped to ETF
weights by solving for the long-only portfolio whose exposures best match the
view". There are two ways to do that, and they give different books.

- **Target-exposure form.** Each view sets a target on its axis. The solver
  matches the targets and holds every exposure no view names at the
  benchmark's. A sector, style or region view is then financed inside the
  equity sleeve, and the only way to hold more equity is to hold less cash,
  which §4 caps at 20%.
- **Alpha form.** Each view becomes expected returns on the instruments that
  carry its axis. The summed expected returns go to the long-only solver
  the lab already has (`portfolio/long_only.py`), under §4's constraints and
  the tracking-error budget. Nothing is held at a target.

## What the owner said

> "i believe the decision to overweight equities vs bench is probably one of
> the most important for high IR, so not having a signal that would capture
> that seems concerning. On the other hand ... if the estimates are favor
> equity signals, then the overall overweight to equities would be a natural
> consequence and there is no need to enforce it at the macro asset class
> level. The macro allocation would then be more of an interpretation of the
> bottom-up results from studying many granular signals."

Only the alpha form allows that. Under the target-exposure form the
overweight cannot happen, whatever the signals say.

## The ruling

1. **A view becomes expected returns.** For each instrument, the sum over
   axes of its exposure on the axis (`decisions/0050`) times the view on that
   axis.
2. **The solver is `portfolio/long_only.solve`,** with §4's constraints
   unchanged. The phase-2 solver extends it and does not replace it.
3. **No exposure is held at a target, and none is held at the benchmark's
   level because no view names it.** The stock/bond mix, the equity beta and
   every other factor exposure are outcomes of the solve.
4. **They are reported on every run,** beside the weights, with the share of
   the tracking-error budget each one uses.
5. **The tracking-error budget is what bounds them** (`decisions/0044`).

## The caveat, recorded so it is not rediscovered

A sum of sector and style views is not a view on equities. If every sector
signal is positive because the market is rich and rising, the book is long
equity beta and no signal said it should be. The control is item 4: read the
decomposition every cycle. Against a 50/50 benchmark equity beta will be the
largest single use of the budget. *Cowork's rough arithmetic, a guess:* ten
points of equity overweight is 1.5 to 2 points of tracking error.

## What it does not decide

- **How a signal's score becomes a view in return units.** Not designed.
- **Instrument-level signals.** The alpha form can carry an
  instrument-specific term, and the owner wants "space for purely
  idiosyncratic signals". SUBSTRATE §6 and §7 form views on axes only, so
  this is not authorised yet.
- **The conviction coefficients** (`decisions/0019`, OWNER-QUEUE D1). They
  stay null and the budget stays hard.
- **How views are aggregated across families** (§6: shrunk z-score averaging
  is the baseline).
- **What the solver must pass on planted signals.** That is its own spec.

## Proposed wording for SUBSTRATE §6 — NOT APPLIED

The bullet that begins "Views are formed in **exposure space**" would open:

> Views are formed in **exposure space** (duration, credit, region, sector,
> style, real/nominal, cash) and mapped to ETF weights by turning each view
> into expected returns on the instruments that carry its axis and solving
> the long-only problem of §4 on their sum (`decisions/0051`). No exposure
> is held at a target, and none is held at the benchmark's level because no
> view names it: the stock/bond mix and every factor exposure are outcomes
> of the solve, reported on every run and bounded by the tracking-error
> budget.

The rest of the bullet, from "The characteristic map is in
`data/characteristics/`", is unchanged.
