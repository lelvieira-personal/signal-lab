# 0070 -- The horizon of the trading cost in the rebalance objective

**Status:** RULED 2026-11-11 by the owner (see the owner ruling at the end). PROPOSED 2026-11-10 by Cowork, for the owner. It is on the reserved list of `decisions/0069` item 2: every option changes either a level in `params/constraints.yaml` (`IC_prior`) or how the cost of `params/costs.yaml` enters the objective, and so what every later verdict means. Nothing is built from it. The chain's M6 grid (the pilot of `decisions/0059` G) waits on it; the `0068` loader milestone does not and goes on.

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

## The evidence, landed (HANDOFF task 92, `results/audit/A-20261110-185308/`, one seed)

Net IR / `net_ir_excess` over its shuffled baseline / transfer / turnover a year / ex-ante TE. The engine charges the full half-spread in every row.

| Arm | Duration IC 0 | Duration IC 0.35 | Region IC 0 | Region IC 0.35 |
|---|---|---|---|---|
| Today (task 91 x1) | +0.04 / -0.01 / 0.02 / 6% / 4% | +0.08 / n/a / 0.07 / 6% / 4.6% | +0.37 / 0.00 / 0.02 / 6% / 4% | +0.35 / n/a / 0.02 / 7% / 3.8% |
| **(b): half-spread / 13 in the solve** | +0.23 / **-0.14** / 0.35 / 75% / 4.7% | +0.49 / **+0.32** / 0.33 / 74% / 4.5% | +0.55 / **+0.06** / 0.25 / 76% / 5.1% | +0.77 / **+0.39** / 0.22 / 76% / 4.9% |
| (b) and the shadow / 13 | | +0.51 / n/a / 0.54 / 94% / 5.0% | | +0.89 / n/a / 0.37 / 114% / 5.0% |
| Today's costs, first book not free | -0.25 / n/a / 0.14 / 0.6% / 1.1% | -0.23 / n/a / 0.16 / 0.6% / 1.1% | -0.08 / n/a / 0.00 / 0% / 1.0% | -0.08 / n/a / 0.03 / 0% / 1.0% |

What it says:
1. **Option (b) works.** With the half-spread amortised over the view's 13 weeks, the book tells planted IC 0.35 from IC 0 and from its shuffled baseline in both expressions (excess +0.32 and +0.39 against -0.14 and +0.06), at about 75% turnover, inside the 150% the mandate aims at. Amortising the shadow too adds little separation and pushes region turnover to 114%. Cowork's recommendation stands: (b), half-spread only.
2. **The IC 0 books' positive IR came from a free first book.** Cowork's guess is confirmed. Today `RebalanceStep` builds the first book from cash with costs set to zero and the engine never charges it (`portfolio/rebalance.py` L215-221, `harness/engine.py` L267-270); the book then barely trades away from it (first-to-last active weights correlated 0.87-0.88). Started from the no-view book and charged, every book at today's costs sits at the no-view book's -0.08, IC 0.35 included. So today's objective with an honest start tells nothing apart at all.
3. **The baselines are high under (b)** (+0.18 to +0.49 net IR at IC 0 and 0.35): a book that trades on noise picks up the sample's beta. That is what bar 2's excess exists to subtract, and it does.
4. **The ruler audit uses the same per-week unit**, but plants alpha with the planted IC itself (seven times the pilot's at IC 0.35), which is why it traded and this did not.

**A fourth question, raised by the evidence:** the free first book. Every phase-2 run, and the ruler audit, starts from a book bought for nothing. Cowork recommends that a run start from the minimum-TE (no-view) book, charged like any other trade, so a run measures the trading the signal causes and not a portfolio frozen on day one. That changes what every later verdict counts, so it is put to you with `0070` rather than ruled under `0069`. Not yet run together with (b): the task that builds your ruling runs both on the grid of `0059` G.

## Questions for the owner

1. (a), (b), (c) or (d)?
2. If (b): the half-spread only (recommended), or the shadow term too?
3. If (b): each hypothesis's own *h* (recommended), or a floor and a cap on it?
4. The first book: start every run from the no-view book and charge the trade out of it (recommended), or keep the free first book?

**Owner ruling, 2026-11-11** (chat, 11:54 ET: "yes to all", on Cowork's suggestions given in chat at 10:51 ET). Recorded by Cowork.

1. **Option (b):** the trading cost is amortised over the view's horizon in the rebalance objective. The engine still charges every trade its full cost in the net return. `IC_prior` stays 0.05.
2. **The half-spread only.** The `0040` shadow term is unchanged.
3. **Each hypothesis's own *h*,** with no floor and no cap. To be revisited if a hypothesis registers with *h* above 26 weeks.
4. **No free first book.** Every run starts from the no-view (minimum-TE) book, and the trade out of it is charged like any other trade. This holds for the ruler audit too.

**Condition.** (b) and the charged first book have not been run together: task 92 ran (b) on the free first book. The first step of the task that builds this ruling runs both together on task 92's cells (planted IC 0 and 0.35, both expressions, each with its shuffled baseline). If IC 0.35 does not separate from its baseline in both expressions, the task stops there, the M6 grid does not run, and this record returns to the owner.

**Consequence, accepted.** Every recorded audit before this ruling, the ruler audit included, started from a free first book. Those numbers stay as recorded, a true statement about the objective in force when they ran, and are not comparable with runs made after this ruling.

**Build.** Cowork writes the task (and any owner-only patch it needs, citing this record) after HANDOFF task 89 lands; the M6 grid of `0059` G follows it.
