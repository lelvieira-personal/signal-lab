# 0031 — A left-tail calibration check, for the promise H-2026-0007 was registered against

Proposed 2026-09-18 by Cowork. **DECIDED by the owner 2026-09-18: shape 1.**
`L` is a reported characteristic on every cell and is named, in a dated addendum,
as `H-2026-0007`'s pre-registered check. It gates nothing and no eleventh veto is
added. Supersedes nothing. Depends on `decisions/0025`, `0026`, `0030`.

Still open inside this record: the threshold, which is not needed under shape 1
for gating but is needed to say whether a reading is large. It comes from
`scripts/bias_map.py`'s simulated null at the measured kurtosis, at p99, fixed
before it touches data.

Pending: promotion out of `proposed/` and the addendum to `H-2026-0007`, both of
which need git and so belong in `HANDOFF.md` once the running audit lands.

## The problem

`H-2026-0007` states its own risk before any result exists, and names the two
things that were meant to catch it:

> "The risk stated in advance is that this signal is short volatility: it buys
> widening spreads, so it adds exposure into precisely the episodes that produce
> the largest drawdowns, and its unconditional Sharpe ratio will look better
> than its behaviour in the left tail. **The tracking error veto and the active
> drawdown diagnostic are the intended checks on that, not the information
> ratio.**"

`decisions/0026` removed the active-drawdown gate. `decisions/0030` removed the
tracking-error veto. Both were right on their own terms and neither considered
this hypothesis.

The successor, `risk_calibration` on `bias_worst_annual`, does not check the same
thing. It asks whether the risk model told the truth over the worst *calendar
year*. A book whose damage is concentrated in five weeks rather than twelve
months passes it, and five weeks is precisely the shape 0007 declares — it says
*episodes*, not years.

So the most explicitly short-volatility hypothesis in the registry is the one
with no pre-registered guard. The window to fix that closes the first time 0007
is measured: a diagnostic added after a result is selection wearing a
governance costume.

## What is proposed

A statistic in the same family as 0030's, read in the left tail instead of the
spread. On the same standardised active return

    z_t  =  r_t / ( sigma_ex_ante(t-1) / sqrt(52) )

define

    L  =  | q05(z) | / 1.645

where `q05` is the 5th percentile of `z` over the evaluation window. Under a
correctly specified risk model, L = 1. A book that concentrates its losses into
a handful of weeks reads L > 1 while both `bias_full_sample` and
`bias_worst_annual` can look clean.

**Why this rather than the drawdown ratio.** A realised-versus-implied maximum
drawdown ratio was the first proposal and it is worse. Its numerator is a single
realised maximum — one observation, with the sampling error of one observation —
against the 834 weekly observations the bias statistic rests on. It also repeats
what `decisions/0026` ruled against: judging a book on the path it happened to
draw. `L` reads roughly 42 tail observations out of 834 and is a calibration
statement, not a level.

**Why not simply tighten `bias_worst_annual`.** The two measure different
failures and the worst-annual reading is already gated. A tighter ceiling there
would fail books whose whole year was mis-sized; it would still not see a book
that was correctly sized for 51 weeks and catastrophically wrong in one.

## What is NOT proposed here

- **No threshold.** The ceiling must be simulated from the null by the method
  `scripts/bias_map.py` already uses for 1.72 — at the measured excess kurtosis
  of `z` (2.37 on the Bloomberg base cells), at p99, fixed before it is computed
  on any data. A tail statistic is more kurtosis-sensitive than a spread
  statistic, so `decisions/0030`'s open question B4 applies here with more force,
  not less.
- **No new veto.** Two shapes were available; the owner chose the first on
  2026-09-18:
  1. `L` reported as a characteristic on every cell, and named in a dated
     addendum as `H-2026-0007`'s pre-registered check. Cheapest; binds only the
     hypothesis that asked for it.
  2. `L` as an eleventh veto alongside `risk_calibration`. Stronger, and it
     re-opens the question 0026 settled — whether a second ex-post gate earns
     its false-positive rate across ~150 audit cells.

  **Chosen: shape 1** (owner, 2026-09-18). 0007 is what created the gap; a
  lab-wide gate is a larger claim than the evidence supports today.
- **No edit to `hypotheses/pending/H-2026-0007.yaml`.** The registry's value is
  that it was written before the answers. The check is recorded here, dated, and
  the hypothesis file is left as written.

## What would retire the open part

The ten-seed Bloomberg audit's distribution of `q05(z)` across cells, alongside
the kurtosis column already queued for B4. Until then the threshold is unset and
`L` cannot gate anything.

## Also worth recording

The realised-versus-implied drawdown ratio should still be *reported*, using the
`decisions/0025` Magdon-Ismail–Atiya map run forward from the book's own ex-ante
TE. `decisions/0026` already keeps max active drawdown on every report; the
implied comparison costs nothing and is the number an investment professional
will ask for first. It is a characteristic, not a gate.
