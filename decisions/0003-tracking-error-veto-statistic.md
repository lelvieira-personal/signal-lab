# 0003 — TE veto: hard band or asymmetric penalty, and which statistic?

Status: proposed, 2026-09-07, agent. Blocking: no. Conservative option taken.

## Question

Two parts of SUBSTRATE pull in different directions.

Section 4 says tracking error is handled by "an asymmetric penalty, not a hard
band. TE is cheap when conviction dispersion is high and expensive when it is
not." Section 10 lists `tracking_error` as a veto with a hard threshold:
trailing-3y TE ≤ 6.0%, and says vetoes "are not advisory".

Section 4 also says episodic excursions are allowed but not rewarded on
average, which suggests the veto should not fire on a single excursion. Nothing
says which statistic of the trailing-3y TE series the veto reads: the maximum
over the run, the final reading, or a quantile.

## What was done

Both mechanisms exist. `vetoes/rules.py:veto_tracking_error` enforces the hard
ceiling from `params/vetoes.yaml`, reading `statistic: max` — the worst
trailing-3y reading over the run. `params/constraints.yaml` carries the
asymmetric penalty's shape with a null coefficient, and the objective will
refuse to build until the owner sets one.

## Why that way

The maximum is the conservative reading and is the only one that cannot be
gamed by timing: a run whose TE spent two years at 8% and ended at 5% would
pass on a final-reading test, and would have breached the mandate throughout.
It is also the reading that makes "episodic excursions are allowed" a genuine
tension rather than a free pass, which is why this note exists.

## What to decide

1. Is the veto statistic `max`, or a high quantile (say the 95th percentile of
   trailing-3y readings), which would let a genuinely episodic excursion pass?
2. What is the asymmetric penalty's coefficient, and is it a penalty in the
   objective, a soft constraint in the solver, or both?
3. If the answer to (1) is a quantile, section 10's "vetoes are not advisory"
   needs a sentence saying so, since a quantile ceiling is a softer object than
   the table implies.

---
## Owner decision (2026-09-09, Leo)

The owner separated the two concepts, correctly:

> "if TE is meant for optimization, then I believe that we should not allow the
> max TE to be surpassed, however it could make sense that the TE value could be
> higher depending on conviction on the signals of the model being tested. if TE
> in this context means the TE that we experienced over the backtest to validate
> whether the model passes or not, then the relative drawdown is probably what I
> prefer to use as a metric."

Stated maximum active drawdown: **10%.**

### What was implemented, and why it is not 10%

Both mechanisms now exist, and there are eleven vetoes rather than ten.

1. **In the optimiser**, TE is a hard per-rebalance cap with a conviction-scaled
   target. `params/constraints.yaml` carries the asymmetric penalty's shape with
   a `null` coefficient; the objective refuses to build until the owner sets it.
   Still outstanding.

2. **As a veto**, `tracking_error` is retained but loosened from the worst
   trailing-3y reading to the **95th percentile** (`statistic: p95`). TE is the
   *mandate* test: it asks whether the strategy stayed inside what the investor
   was told. Dropping it entirely would let a model run at 9% TE against a 50/50
   benchmark and pass on drawdown alone, which is a breach of the thing the
   mandate promises whatever the drawdown looked like. The p95 is what "episodic
   excursions allowed" (section 4) has to mean if it means anything.

3. **A new eleventh veto, `active_drawdown`**, is the economic test: what the
   allocator actually lived through. TE is symmetric and so penalises the upside
   dispersion the strategy is paid for; drawdown does not.

### Why the threshold is 3x TE and not an absolute 10%

A 10% cap and a 6% TE budget are not jointly satisfiable. Monte Carlo, 20,000
paths of weekly active returns over the 19-year development window:

| TE | IR | Median max active DD | P(breach 10%) | P(breach 15%) |
|---|---|---|---|---|
| 6% | 0.20 | 20.5% | 99% | 82% |
| 6% | 0.30 | 18.3% | 98% | 73% |
| 6% | 0.50 | 15.3% | 94% | 52% |
| 6% | 0.80 | 12.2% | 78% | 24% |
| 4% | 0.30 | 12.5% | 75% | 30% |
| 3% | 0.30 |  9.4% | 44% | 10% |

At the 6% TE ceiling and a realistic IR of 0.3, a 10% cap kills **98%** of
paths — including every path where the strategy is genuinely good. Even an
exceptional IR of 0.8 breaches it 78% of the time. The veto would not be a
filter; it would be a reject-everything switch, and the leaderboard would be
empty for a reason that has nothing to do with the signals.

Note also that this simulation is *optimistic*: it assumes constant volatility
and normal returns. Real active returns have fat tails and volatility
clustering, both of which deepen drawdowns.

The threshold is therefore expressed as a **multiple of the TE ceiling**
(`te_multiple: 3.0`, i.e. 18.0% at the current 6% TE) rather than as an absolute
number. Drawdown and TE are not independent quantities, so an absolute cap set
against one TE budget becomes either trivial or impossible under another; the
multiple keeps them coupled and tightens automatically if the TE budget is cut.
At 3x, roughly the worse half of paths fail at IR 0.3 — a real bar that a good
strategy can clear.

### What the owner may want to change

`params/vetoes.yaml` has `active_drawdown.absolute`, which overrides the
multiple when set. Setting it to `0.10` restores the stated preference exactly.
Three coherent positions:

- **Keep 3x TE (18%)** — as implemented. A demanding but passable bar.
- **Set `absolute: 0.10` and cut the TE ceiling to 3%** — internally consistent,
  and a genuinely tight mandate. This is the honest way to have a 10% drawdown
  limit.
- **Set `absolute: 0.10` and keep TE at 6%** — the veto then rejects almost
  everything, which may be the intent if the bar is meant to be near-impossible.

### Owner's answer (2026-09-09)

> "let's keep the 18%"

`te_multiple: 3.0` stands, `absolute: null`. At the current 6.0% TE ceiling the
active-drawdown veto fires above 18.0%, and it moves with the TE budget if that
is ever cut.

Status: **closed.**
