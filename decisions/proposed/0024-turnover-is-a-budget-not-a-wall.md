# 0024 — Is the 150% turnover ceiling a wall or a budget?

Status: **proposed, 2026-09-11, agent. Blocking: no. Nothing changed.**
SUBSTRATE section 2 forbids an agent originating a change to `params/vetoes.yaml`
or to section 10, so this note states the conflict and stops.

## What the owner said

> "150% is the annual Turnover. It is allowed to have a larger turnover if
> conviction is higher for example, even if the annualized figure surpass 150%."

## What the lab currently does

SUBSTRATE section 10 lists `turnover` among the eleven vetoes:

| turnover | annualised traded notional <= 150% |

`params/vetoes.yaml` reads `max_annualised: 1.50`, and `vetoes/rules.py` kills
any run whose full-sample mean traded notional, annualised, exceeds it. Vetoes
"are not advisory". As written, a run that averaged 155% is dead however good it
was and whatever its conviction did.

That is a **wall**. The owner describes a **budget**. They are different objects
and the difference decides runs.

## The same question was already answered once, for tracking error

`decisions/0003` hit this exact shape. Section 4 said episodic tracking-error
excursions were allowed; section 10 made trailing-3y TE a hard veto. The
resolution was not to delete the veto but to change the STATISTIC it reads:
from the worst trailing-3y reading to the **95th percentile** of readings, so
"episodic excursions allowed" means something without the mandate test becoming
unenforceable.

The parallel for turnover is direct: read a high quantile of **rolling one-year
traded notional** rather than the full-sample mean. A strategy that spends one
conviction-rich year at 190% and sits at 110% otherwise passes; one that runs at
180% throughout does not.

## What the owner then clarified (2026-09-11, second message)

> "the idea is that the model doesn't generate too much trading in a single
> session, unless the scenario really changes and there is high conviction about
> it. If the model is addressing this without letting one single rebal session
> take too much of the turnover budget it would be great. I want to avoid a
> situation where we rebalanced too much on previous windows and then cannot do
> more when we really need it due to TO budget constraints."

That is two requirements, and they pull in opposite directions under any single
annual number:

1. **No single session takes too much of the budget.** A per-session limit.
2. **Never blocked later because of earlier trading.** No annual wall.

An annual cap satisfies neither cleanly. It permits one session to spend the
whole year in a week, and then it forbids trading outright for the rest of the
year -- precisely the failure named in (2).

## The mechanism this implies, now built into the audit

**A hard per-session cap on traded notional.** Generous against a ~2.9%/week
average at a 150% annual budget, but far below the budget itself, so a regime
shift can be acted on in one week and no week can consume the year.

**A progressive shadow cost keyed to trailing one-year turnover, and no annual
wall.** Zero at or below the 100% soft target; exactly the 10bp `decisions/0018`
set when trailing turnover reaches the 150% budget; rising on the same slope
beyond it rather than stopping:

    shadow(T) = coefficient * max(0, T - target) / (budget - target)

So 0bp at 100%, 10bp at 150%, 20bp at 200%, 40bp at 300%. Ordinary weeks
restrain themselves because trading grows dearer as the year is consumed; a week
with real alpha can always pay and trade. Dear is not the same as forbidden, and
that distinction is the whole of requirement (2).

**The bank is gone.** The previous version banked unused allowance and let the
balance go negative. That is requirement (2)'s failure wearing a friendlier
face: it made capacity a quantity to be spent, so an early over-trade genuinely
blocked a later one.

**Conviction is not wired in yet, deliberately.** "Unless there is high
conviction" points at scaling the per-session cap by conviction, exactly as
`decisions/0019` scales the tracking-error coefficient. Its two coefficients are
still null and the measure itself is registered as H-2026-0012, so wiring
conviction into turnover now would invent a second unmeasured knob. The
per-session cap is a plain parameter; conviction-scaling it is the natural
extension the moment 0019 lands.

## The number has not been chosen, so the audit measures it

`params/audit.yaml` sweeps `per_rebalance_caps: [0.10, 0.25, 0.50, null]` -- 3.5
weeks, 8.7 weeks and 17 weeks of a 150%/yr average, plus no limit -- and reports
net IR, realised annual turnover, the largest single session and the shadow cost
actually paid for each. `per_rebalance_cap_default` is null, so the base ladder
measures the layer rather than a candidate cap. Picking the production number
belongs in `params/constraints.yaml` and is an owner decision; the evidence for
it arrives with the first real audit table.

## Three coherent positions

1. **Keep the wall.** `max_annualised: 1.50` on the full-sample mean. Simple,
   defensible to an allocator, and inconsistent with what the owner just said.
2. **Budget with a quantile** (the `decisions/0003` pattern). The veto reads
   `turnover.statistic: p95` over rolling one-year windows, with the ceiling
   staying at 150%. Needs a second number: the excursion ceiling the quantile
   may not exceed, or none.
3. **Budget priced, not vetoed.** Drop the turnover veto; the section 4 shadow
   cost (`decisions/0018`, 10bp per unit above the 100% target) is the only
   restraint, and turnover becomes a reported characteristic rather than a gate.
   Honest about the economics, and it removes a capacity control that an
   investment professional will expect to see.

## What was done in the meantime, and what was not

**Not done:** `params/vetoes.yaml` is untouched, section 10 is untouched, and
the audit still evaluates the turnover veto at `max_annualised` exactly as the
parameter file states. While the question is open the audit's surviving-cells
bar is therefore conservative -- it may drop cells the owner would allow -- and
that is the safe direction.

**Done, because it is measurement rather than policy:** the ruler audit's BASE
cells no longer carry a hard per-rebalance turnover cap. They run under the
section 4 shadow cost alone, so turnover goes where the alpha justifies it, and
every cell reports `turnover_annual`, `turnover_p95_rolling_1y` and
`turnover_max_rolling_1y`. Hard caps remain as an experiment in the
turnover-shortfall cells, which is the point of that curve. The previous
behaviour -- hard-capping the base cells -- was binding on half to nine tenths
of rebalances, so the required-IC table was reporting the cap's answer as the
layer's answer.

## What the owner needs to decide

1. Which of the three positions above, for what the VETO reads.
2. If (2): the quantile, and whether an absolute excursion ceiling sits above it.
3. The per-session cap for production, from the swept evidence, into
   `params/constraints.yaml` as `turnover.max_per_rebalance`.
4. Whether the 100% soft target survives unchanged as the point at which the
   progressive shadow cost starts. `decisions/0018` set the 10bp; this note
   keeps that magnitude exactly at the 150% budget and changes only the shape
   between and beyond, from a step to a ramp.
5. Whether the per-session cap should later scale with conviction
   (`decisions/0019`, H-2026-0012) once a conviction measure is settled.

The audit's first real table will show what one-year turnover the layer actually
wants at each IC and horizon, which is the evidence this decision should be
taken on rather than in the abstract.
