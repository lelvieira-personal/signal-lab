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

1. Which of the three positions above.
2. If (2): the quantile, and whether an absolute excursion ceiling sits above it.
3. Whether the 100% soft target and its 10bp shadow cost (`decisions/0018`)
   survive unchanged in either case. They are a separate lever and nothing here
   touches them.

The audit's first real table will show what one-year turnover the layer actually
wants at each IC and horizon, which is the evidence this decision should be
taken on rather than in the abstract.
