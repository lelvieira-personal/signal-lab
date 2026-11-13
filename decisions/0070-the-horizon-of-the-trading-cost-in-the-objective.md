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

## Addendum, 2026-11-12: how the ruling is built (delegated)

**Delegated ruling, 2026-11-12, Cowork review** (under `decisions/0069` items 3 and 4). The owner's ruling above says what is built; it does not say which *h* when a hypothesis registers a range, which rules it reaches, or what becomes of the recorded runs' code path. The questions, the choices and their bases:

1. **Which *h*.** A hypothesis registers `horizon_weeks` as `(lo, hi)`. *Options:* `lo`, `hi`, or the single *h* that `views.horizon_h_from_params(lo, hi, params)` already gives `Phase2Rule` (`phase2.py` L122, `self.h`). *Choice:* that same `self.h`. *Basis:* `views.view_scale` divides the view by `sqrt(h)` with that *h* to make it a per-week return; amortising the half-spread over the same *h* is then exactly "the alpha is the *h*-week one" of option (b), with nothing else moved. A different *h* in the two places would mix two horizons in one objective. The ruler audit's `_OptimiserRule` uses its cell's `horizon`, the *h* its planted alpha is scaled by (`audit/signals.py` L253).
2. **Which rules.** *Choice:* the amortisation and the charged first book apply to every rule that carries a view: `Phase2Rule` (its own `self.h`) and the ruler audit's `_OptimiserRule` (owner ruling item 4 names it). A `RebalanceStep` built without a view horizon (any rule with no view) keeps a divisor of 1. *Basis:* the ruling amortises over "the view's horizon"; a rule with no view has none, and a no-view book is unchanged by item 4 (it *is* the starting book).
3. **The first book.** On its first date a rule returns the no-view book: its own solve with every alpha 0, built at zero cost and not charged (the engine records no row for the first date, as today). From the second date the view enters, and every trade, the one out of the no-view book included, is set against the amortised half-spread in the solve and charged the full half-spread by the engine. *Basis:* ruling item 4; this is task 92's `pilot.FromNoViewRule`, whose (C) runs are the evidence the owner ruled on.
4. **The recorded runs stay reproducible.** The old behaviour (divisor 1, free first book built with the view) stays reachable by explicit constructor arguments, off by default, so every recorded audit and pilot grid, the task 69 reproduction gate and task 91's and 92's rows still reproduce exactly. No expected number in an existing test changes; a test that pins a recorded number passes the legacy arguments instead. *Basis:* the ruling's "Consequence, accepted": the recorded numbers "stay as recorded"; a number the code can no longer produce could not be checked.
5. **Where it lives.** In `portfolio/rebalance.py` (`RebalanceStep`: the divisor on the half-spread vector of a non-first step, before the linear shadow is added, so the `0040` shadow is unchanged, ruling item 2; and the first-book rule), set by `Phase2Rule` and `_OptimiserRule`. The engine's cost model is not touched. *Basis:* section C of `decisions/0059` (one rebalance step for the lab); task 69's extraction.

*Which numbers this can move:* every phase-2 and ruler-audit run made after it (the owner's ruling moves them; these choices fix only how). No recorded number, no golden. *What would reverse it:* the reviewer finding that `horizon_h_from_params` is not the *h* that scales the view, that a rule with no view is changed by the build, or that a recorded row no longer reproduces; or the owner striking it.

**Reviewer (`0069` item 4):** pending. HANDOFF task 93 runs in a fresh Opus session that did not make this ruling; its step 2 reads this addendum against the code and writes its line here before building anything.

**Reviewer, 2026-11-12, Claude Code (Opus, HANDOFF task 93, a fresh session that did not make the ruling): agree, with details settled inside the cited records.** Read against the code: `Phase2Rule` sets `self.h = views.horizon_h_from_params(lo, hi, params)` (`phase2.py` L122) and scales the view with that same `self.h` in both expressions (L125 `view_scale_from_params`, L129 `ic_prior / sqrt(self.h)`), and the ruler audit's planted alpha is divided by `sqrt(horizon)` of its cell (`audit/signals.py` L253), so item 1's *h* is the one that makes the alpha per week. `RebalanceStep.step` reads the cost through `half_spread_vector` alone and adds the linear shadow after it (`rebalance.py` L217-230), so a divisor there leaves the `0040` shadow as it is (item 5, ruling item 2). The first book is the rule's call with no drifted book, built at zero cost and recorded by the engine with no row (`rebalance.py` L215-221, `engine.py` L267-270), which is item 3 as `pilot.FromNoViewRule` ran it. Nothing in items 1 to 5 reaches the reserved list of `0069` item 2: the owner's ruling fixes the cost's horizon, the half-spread only and the charged first book; these items fix only where and with which *h*. Three details, settled inside items 2 to 4: (i) the pilot's no-view arm (a `Phase2Rule` fed identically zero scores) is a rule with no view, so it is built with the legacy arguments (divisor 1; its first book is the no-view book either way) and its run is unchanged (item 2's basis); (ii) on the first call the view rules do not read the view at all (no alpha, no exposure lookup), as `FromNoViewRule` did, so the condition grid's rows can reproduce exactly (item 3); (iii) every grid the ruler audit defines today is a recorded configuration (item 4), so its builders pass the legacy arguments and keep their keys, and the new objective is the default of `AuditCell` and `_OptimiserRule` for the rerun a later task defines (ruling item 4; this task does not rerun it).

## Addendum, 2026-11-13: task 95's stop is the `0040` prefill, not a fault in the solve (delegated)

**Delegated ruling, 2026-11-13, Cowork review** (under `decisions/0069` items 3 and 5). *The question:* task 95 stopped on its fault branch: on the second date the solve is handed an alpha 4.7x (duration) and 6.1x (region) the amortised half-spread of its largest instrument and trades about 4e-10, and the same idleness lasts to index 12 or 13 in every arm. Is the solve faulty, or is something in the objective pricing the trade out? *Options:* (a) a fault in the solve, to be fixed under `src/`; (b) a real effect of a cost term the task's criterion left out; (c) not decidable without more evidence. *Choice:* (b), with a confirming measurement (HANDOFF task 96) before any long run builds on it. *Basis:* the criterion Cowork wrote for task 95 compared the alpha with the half-spread over *h* alone and left out the `0040` created-turnover shadow, which this record's item 5 keeps un-amortised (the owner's "the half-spread only"). `decisions/0040` item 2 (owner, "prefill at 100% target") fills every missing rebalance of the trailing window at `target_annualised / ppy` (`harness/objective.py` `prefilled_trailing_traded`; `params/constraints.yaml`: target 1.00, start 0.75, reference 1.50, coefficient 40, 52 a year). On a run's first traded date the window is empty, so P = 51/52 = 0.981 and the marginal shadow is 40 x (0.981 - 0.75) / 0.75 = **12.3 bp per unit traded on each leg**, against a weekly alpha of 1.8 to 4.7 bp at its largest. Each near-zero week replaces a prefilled 1/52 with about 0, so the rate falls by about 1.03 bp a date and reaches 0 at index 13 (P = 39/52 = 0.75); the receipt's first material trades are at index 12 (duration, where the rate is about 1.0 bp) and 13 (region), and on the synthetic fixture at index 15. The same holds in arms (A) and (C), which carry the same shadow. The prediction is quantitative and the receipt matches it in every arm. *Which numbers it can move:* none; no code changes. It says each run of the `0070` defaults (and of every arm before it) lets about thirteen weeks pass before the view trades, about 1.6% of a 2004 to 2019 sample, the same in a run and its baseline. *What would reverse it:* task 96's run with the shadow coefficient at 0 still trading about nothing on index 1 where the best pair's alpha net of both legs' amortised half-spreads is positive, or its logged marginal shadow not following 12.3 bp falling to 0 at index 13. Then the reading is (a) and the fix is ruled from task 96's report. Whether the prefill should apply at the start of a run is the owner's (`0040` item 2 is his ruling and the shadow's levels are constraint levels, `0069` item 2); nothing here proposes to change it.

*Second agent:* not required (`0069` item 4): the ruling touches no number-making path. Task 96, an Opus session that did not make it, measures the prediction before task 94 is released.
