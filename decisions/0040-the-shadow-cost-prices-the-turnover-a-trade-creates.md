# 0040 — The shadow cost prices the turnover a trade creates

**Status:** **decided 2026-09-29 by the owner: adopted, at 40 bp** (OWNER-QUEUE
L18, "0040: 40bps"). The form was decided in principle on 2026-09-28 and
measured first by HANDOFF task 36 (`A-20260929-070540`, reviewed in the Cowork
doc `claude/tasks-34-36-review-2026-09-29.md`). It is applied by HANDOFF task 39,
together with `decisions/0038`, so `params_hash` moves once. Drafted by
Cowork. It amends `decisions/0024`: the start (0.75) and reference (1.50) are
unchanged, the coefficient goes from 10 to 40 bp at the reference, and the
pricing is by the turnover a trade creates.

## Why

The friction sweep (`A-20260928-151055`, Cowork doc
`claude/friction-sweep-2026-09-28.md`) found that the 0024 shadow cost echoes
on a 53-week cycle. The cost per unit is **flat in the size of the current
trade** and set from the **previous 52 weeks**. A large trade raises it for a
year; when that trade rolls out of the window the cost collapses and the
backlog trades at once. The lag-53 autocorrelation of weekly turnover is
0.73-0.78 at 40 bp and about 0 at other lags. The largest single week *rises*
with friction, from about 1.0x NAV at 10 bp to 1.8-1.9x at 40 bp. So friction
as built makes trading lumpier, which undercuts the premise of B2 (no
per-rebalance cap).

## The ruling, made precise (the owner's choices of 2026-09-28)

Notation: `W = round(periods_per_year)` (52). `P` is traded notional over the
**previous W−1 rebalances**. `x` is this rebalance's traded notional. The
window that includes this trade is then W long, and `T(x) = (P + x)·ppy/W` is
the trailing annual turnover the trade **creates**. `s` is the start (0.75), `r`
the reference (1.50) and `κ = coefficient × 1e-4`.

1. **The marginal unit pays the curve at the turnover it creates** (owner:
   "the marginal unit"). The shadow charged for a trade of size `x` is the
   integral of the 0024 curve along the trade:

       S(x) = ∫₀ˣ κ·max(0, T(u) − s)/(r − s) du
            = κ/(2(r − s)) · [max(0, T(x) − s)² − max(0, T(0) − s)²] · W/ppy

   Its derivative is `S'(x) = shadow(T(x))`. The last unit traded pays exactly
   what the curve says at the post-trade level, so "coefficient bp at 150%"
   keeps its 0018/0024 meaning. `S` is convex and quadratic in `x`, so one
   lump costs more than the same trading spread over several weeks.
2. **Before a full window exists, missing weeks count at the 100% target**
   (owner: "prefill at 100% target"). Each missing rebalance is filled with
   `target_annualised / ppy`, and the window is always W long. This replaces,
   for this form only, today's convention of annualising over the weeks
   observed. Under the new pricing that convention would make a week-2 trade
   count about 26 times over.
3. **Real costs are unchanged**, and the shadow still never enters net IR
   (0018).

## What changes, when applied (after task 36, with task 33)

1. `params/constraints.yaml` `turnover.penalty`: `form: linear` becomes
   `form: created_marginal` (the name is Cowork's; the owner may rename it),
   and the comment block describes 1 and 2 above. The coefficient is whatever
   the owner picks after task 36.
2. Code: the audit's optimiser rule reads the form. `harness.objective`
   accepts the new form and no longer raises on it.
3. The `form: linear` path stays in code, so earlier runs remain
   reproducible.

## Open

- **The coefficient under the new form.** At the same coefficient the new form
  charges lumps more and steady trading about the same, so the level that holds
  turnover near target may differ. Task 36 runs 10, 20 and 40 bp to show this.
- **The cliff when a lump rolls out of the window is still there.** The new
  pricing should spread out the catch-up trade rather than remove the cliff.
  The owner chose not to add an exponentially weighted window (L18 option b)
  for now; task 36's lag-53 autocorrelation will show whether that holds up.

## Addendum 2026-09-29: the measurement and the ruling

**Task 36** (`A-20260929-070540`, against the trailing control
`A-20260928-151055`, same hashes):
- The largest single-week trade is at most 0.84× NAV (was up to 2.00×), lower
  in 60 of 60 pairs.
- At 40 bp, annual turnover is 130% at IC 0.35 and 164% at IC 0.70 (was 160%
  and 182%).
- There is no detectable change in net IR (paired means −0.075 to +0.030, sd
  0.08-0.19).
- The annual echo is down to 0.24-0.30 at lag 52 (was 0.73-0.78 at lag 53). It
  moved to lag 52 by construction and is not gone. That is the "Open" cliff
  above, now a moderate rhythm rather than lumps.

**The owner's ruling, 2026-09-29: adopt `created`, coefficient 40 bp.**

**The exact `SUBSTRATE.md` edits, applied by task 39 citing this record and
0038:**
1. **§4, Turnover row.** Replace "zero at 75%, 10bp at 150%, rising without
   bound (§8, `decisions/0017`, `0018`)" with "zero at 75%, 40bp at 150%,
   rising without bound, **charged at the trailing turnover each trade
   creates**, so a lump costs more than the same trading spread out (§8,
   `decisions/0017`, `0018`, `0040`)". The per-session-cap sentence is
   replaced as 0038 item 3 says.
2. **§4, the "Turnover handling" paragraph.** Replace "A one-sided linear
   penalty on trailing one-year turnover, priced as a shadow cost in basis
   points (`decisions/0018`), starts at 75%, reaches 10bp at 150% and keeps
   rising" with "A one-sided shadow cost in basis points (`decisions/0018`),
   linear in trailing one-year turnover, starts at 75%, reaches 40bp at 150%
   and keeps rising. Each trade is charged the curve at the trailing turnover
   it creates, with the marginal unit paying the curve at the post-trade level
   (`decisions/0040`)".

**`params/constraints.yaml`:** `turnover.penalty.form: created_marginal`,
`coefficient: 40.0`, and the comment block rewritten to describe items 1 and 2
of "The ruling, made precise". The magnitude table in that comment is
recomputed at 40 bp.

## Applied 2026-09-30 (HANDOFF task 39)

`params_hash` moved once, together with `decisions/0038`:
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c` (v0.6.0) ->
`ba19198d4e9048abb82a0ece868881561f008f7c6f3043d4cdbfdf44dbfade93` (v0.7.0).
Owner-only edits applied by Cowork directly to the working tree at the
owner's instruction (Claude Code's permissions refused them, as they did
task 40's `SUBSTRATE.md` step). Code: `AuditCell.shadow_form` defaults to
`None`, reading `constraints.turnover.penalty.form` from params exactly as
`shadow_coefficient` already did (`resolve_shadow_form`,
`audit/ladder.py`) -- `created_marginal` is now what a default cell reaches,
not `linear`. `harness.objective.turnover_penalty` accepts
`created_marginal` (its marginal-RATE curve is unchanged from `linear`;
the convex per-trade integral stays in `_OptimiserRule`, which never called
that function). `GOLDEN_NET_IR` (`tests/test_baseline.py`,
`-0.8793457503233992`) is now reproduced only by an explicit
`shadow_form="trailing", shadow_coefficient=10.0` override; a new golden,
`GOLDEN_NET_IR_CREATED_MARGINAL = -0.3916592047250338`, records the same
cell (`AuditCell(0.10, 13, 0)`) under today's default.

## Addendum, 2026-10-01: what convexity does and does not buy (task 42 review, F5)

The sentence "`S` is convex and quadratic in `x`, so one lump costs more than
the same trading spread over several weeks" overstates it. S is the integral of
the marginal curve along cumulative traded notional, so **within a fixed
window, a lump and the same trading split across weeks cost exactly the
same.** Splitting is cheaper only by the trades that roll out of the window in
between. Recomputed by Cowork for a 0.40 trade at 40 bp:

- prior 0%/week: 0.00 bp either way;
- prior 2%/week: lump 10.03 bp, split 9.81 bp;
- prior 5%/week: 42.67 bp vs 42.13 bp.

The shadow prices the annual total, not lumpiness. The ruling stands. If
lumpiness itself is to be priced, that is a market-impact term in the size of a
single trade, a separate decision. The `params/constraints.yaml` comment was
corrected in params v0.9.0 (owner's acceptance, 2026-10-01).

## Addendum, 2026-11-13: the forced leg of a trade belongs in the trailing window (delegated)

**Delegated ruling, 2026-11-13, Cowork review** (under `decisions/0069` items 3 and 5). *The question:* HANDOFF task 96 (receipt, step 2) found that when the drifted book holds an instrument that has left the step's holdable set, `RebalanceStep.step` (`portfolio/rebalance.py` L239) drops it from `w0`, so the solve's `sol.turnover` counts only the buy that restores the budget, while the engine (`costs.py` L132-134) records and charges both legs. `turnover_log` appends `sol.turnover` (L272), so the trailing window that item 1's `T` and the session cap (L126, L138) read leaves the forced sale out. In the pilot this is `TAMSCI` at 0.001495 on index 2 (0.080 bp of shadow at index 13). Does the window record the turnover the book went through, or only the part the solve chose? *Options:* (a) leave it: the window holds the solve's turnover only; (b) the window holds the turnover the book went through on the date: `sol.turnover` plus the sum of |drifted weight| outside `hold`, which is what the engine records; (c) put the forced sale into the solve itself (keep the instrument in `w0` with a fixed target of 0). *Choice:* (b). *Basis:* item 1 of this record prices the marginal unit at `T`, "the trailing annual turnover", and the curve of `0024` it inherits is set against the book's annual turnover (target 100%, reference 150%), which the engine measures with both legs; a window that leaves out turnover the book really had understates `T` and so the shadow and the cap, and does so only on dates the solve cannot control. (c) changes the solve's feasible set for no gain over (b), since the sale is forced either way. The shadow still prices only what the next trade adds (item 1), and real costs and net IR are untouched (item 3; the engine already charges both legs). *Which numbers it can move:* the shadow and the session cap, on any run after a date when a held instrument leaves the holdable set; so possibly goldens of cells whose universe has such dates. Each golden that moves is listed with that reason; none moves for any other. In the pilot the effect is at most 2a x 0.0015 (about 0.08 bp) for 52 weeks after index 2. *What would reverse it:* the reviewer showing that `0024` or this record measures turnover on the solve's choice only (for example, that the lab's reported annual turnover, the `0038` highlight, is computed from `sol.turnover` and not from the engine), or a golden moving by more than the forced legs explain. Then (a) stands and nothing is built.

*Second agent:* required (`0069` item 4: the build touches `src/` and possibly goldens). **Review pending**: step 1 of HANDOFF task 97, a fresh Opus session that did not make this ruling, reviews it before anything is built; do not chain on it until that line is written here. Not built before task 94's grid, which runs on the code as it is (the pilot's effect is the 0.08 bp above).

*Reviewer (HANDOFF task 97, Claude Code Opus, 2026-11-14):* agrees, because the reversal condition does not hold. Every turnover the lab reports is the engine's, with both legs: `harness/costs.py` `CostModel.turnover` (L124-134) reindexes target and drifted to their union, so a dropped instrument is a full-size sale; `engine.py` L313 records that as the path's `turnover`; `annualised_turnover` (L127), the `0038` highlight's `turnover_annual` (`audit/ladder.py` L570, L1024) and the pilot's `turnover_first_year` (`audit/pilot.py` L359-363) all read `path.turnover`. SUBSTRATE §8 also measures turnover "from the *drifted* book to the new target". Neither `0024` nor this record defines the window on the solve's choice alone. Item 1's `T` is "the trailing annual turnover", and its curve (start 75%, reference 150%, target 100%) is calibrated against the reported figure, so a window without the forced leg understates `T` against its own calibration. Nothing in the build is on `0069` item 2's list: no level in `params/` moves (coefficient, start, reference, target, prefill are as they are), and real costs and net IR are untouched because the engine already charges both legs. Option (c) would change the solve's feasible set for no gain, as the ruling says. Two details, settled inside this record: (i) the forced leg of date k enters the window the shadow reads from date k+1, because the coefficients are fixed before the trade (item 1 prices what a trade *adds*, and the sale is not the solve's choice); (ii) `shadow_paid_bps` prices the solve's `x` without the forced leg, for the same reason. The per-session cap is unchanged (it bounds the solve's own trade); the annual wall of the turnover-shortfall cells reads the window and so now counts the forced leg, consistent with (b).
