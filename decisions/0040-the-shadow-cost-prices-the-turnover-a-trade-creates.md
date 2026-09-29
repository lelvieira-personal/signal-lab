# 0040 — The shadow cost prices the turnover a trade creates

**Status:** decided in principle 2026-09-28 by the owner (OWNER-QUEUE L18:
"charge each trade at the trailing turnover it would create"). **Measure
first**, also the owner's choice on 2026-09-28: HANDOFF task 36 builds it as a
per-cell override and runs it. The `params/` change lands only after the owner
has read that run, in the same params change as `decisions/0038` (task 33), so
`params_hash` moves once. Drafted by Cowork. Amends `decisions/0024`; the
curve itself (start 0.75, reference 1.50, coefficient at the reference) is
unchanged.

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
