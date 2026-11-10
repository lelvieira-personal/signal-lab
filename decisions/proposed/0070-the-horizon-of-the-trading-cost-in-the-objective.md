# 0070 -- The horizon of the trading cost in the rebalance objective

**Status:** PROPOSED 2026-11-10 by Cowork, for the owner. It is on the reserved list of `decisions/0069` item 2: every option changes either a level in `params/constraints.yaml` (`IC_prior`) or how the cost of `params/costs.yaml` enters the objective, and so what every later verdict means. Nothing is built from it. The chain's M6 grid (the pilot of `decisions/0059` G) waits on it; the `0068` loader milestone does not and goes on.

Everything marked **guess** is Cowork's reading, not a measurement.

## What was measured (HANDOFF tasks 90 and 91; `results/audit/A-20261110-135659/`, `A-20261110-173813/`)

Planted signals on the development window, *h* = 13 weeks, the params' `IC_prior` (0.05), one seed.

| | Net IR | Transfer | Turnover a year | Ex-ante TE |
|---|---|---|---|---|
| No-view book | -0.08 | n/a | 0% | 1.0% |
| Duration, planted IC 0 | +0.04 | 0.02 to 0.07 | 6% | about 4% |
| Duration, planted IC 0.35 | +0.08 | 0.07 | 6% | 4.6% |
| Region, planted IC 0 | +0.37 | 0.02 to 0.07 | 6% | about 4% |
| Region, planted IC 0.35 | +0.35 | 0.02 | 7% | 3.8% |

- A planted IC of 0.35 is far above anything a real macro signal carries, and the book does not tell it from noise.
- The harness is not at fault: with no friction the transfer is 0.72 and the views move the book; the views and alphas on one date match a rebuild outside the rule exactly (task 91, (c) and (e)).
- With `IC_prior` multiplied in the call, IC 0.35: x2 gives net IR +0.30 / +0.59 (duration / region) at 23% / 24% turnover; x4 +0.46 / +0.74 at 57% / 66%; x8 +0.58 / +0.92 at 80% / 91%.
- The arithmetic: the largest alpha on a date is about 1.4 bp a week (duration) and 2.7 bp a week (region), against a one-way half-spread of 5 and 10 bp. Over the 13 weeks the view is meant to last, that alpha is 18 and 35 bp (medians) against a round trip of 10 and 20 bp, and it exceeds the round trip on 72% and 77% of dates. The book still does not trade.

## Why (Cowork's reading of the code path the worker named)

`views.view_scale` turns a view with an *h*-week horizon into a **per-week** expected return: `IC_prior * sigma_week * z / sqrt(h)`. `long_only.solve` then weighs that one week of alpha against the **whole** one-way cost of the trade ("alpha and cost are per period and per unit traded"). A position expected to earn for 13 weeks is charged as if it had one week to pay for itself. That is a one-period objective applied to a multi-period view, and it under-trades by roughly a factor of *h*.

**Guess, to be tested by task 92:** the positive IRs at IC 0 are mostly the first book. It is built once, sized to the tracking-error target, and then hardly trades for sixteen years, so the run measures one frozen portfolio. That would explain why IC 0, IC 0.35 and the shuffled baseline read the same in the region runs.

## Options

- **(a) Raise `IC_prior`** (to 0.2 to 0.4, from the multiplier runs). It works mechanically. Against: `IC_prior` then stops being an information coefficient (0.05 was ruled on 2026-10-14 as a realistic prior), the factor needed depends on each hypothesis's horizon, and it also scales the view against the risk term, not only against costs.
- **(b) Amortise the trading cost over the view's horizon in the objective.** In the rebalance problem the half-spread is divided by the hypothesis's *h* (equivalently the alpha is the *h*-week one). The engine still charges every trade its full cost in the net return, so the product bar is unchanged in what it counts. *Basis:* the standard treatment of a one-period optimiser with persistent alphas: Grinold and Kahn, *Active Portfolio Management* (2nd ed., the chapter on transactions costs, turnover and trading: costs are amortised over the expected holding period before they are set against an alpha expressed per period); Garleanu and Pedersen, "Dynamic Trading with Predictable Returns and Transaction Costs", *Journal of Finance* 68(6), 2013 (the optimal trade weighs the cost against the discounted sum of the alpha over its persistence, not against one period of it).
- **(c) Amortise over one lab-wide horizon** (say 26 weeks) instead of each hypothesis's *h*. One rule, simpler to audit; wrong for a fast signal and for a slow one.
- **(d) Leave it.** Then the lab's gate cannot see a planted IC of 0.35 in a single-hypothesis run, and no realistic signal can pass. Not recommended.

**Cowork recommends (b)**, for the half-spread only. The `0040` shadow term stays as it is: it is a penalty you set per unit of annual turnover (40 bp at 150%), already an annual quantity, and its median charge in these runs is zero. `IC_prior` stays 0.05.

*What (b) would move:* every phase-2 book and so every later verdict; no recorded audit number (the ruler audit plants instrument-level alphas through its own path; **not checked** whether its alpha is per week or per horizon, task 92 reports it). Turnover would rise, to something like the x8 runs or above (**guess**: 80% to 150% a year at IC 0.35), still disclosed and not vetoed (`0038`).

## Evidence still coming (HANDOFF task 92, released 2026-11-10)

Task 92 runs option (b) in the call, without touching `params/`: planted IC 0 and 0.35, both expressions, each with its shuffled baseline, the half-spread divided by 13 in the solve and charged in full by the engine; the same with the shadow term divided too; and the first-book test (start from the no-view book). Its table is added here when it lands. You can rule before or after it.

## Questions for the owner

1. (a), (b), (c) or (d)?
2. If (b): the half-spread only (recommended), or the shadow term too?
3. If (b): each hypothesis's own *h* (recommended), or a floor and a cap on it?
