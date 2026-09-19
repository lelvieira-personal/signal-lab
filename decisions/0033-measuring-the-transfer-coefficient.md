# 0033 — Measuring the transfer coefficient without rebuilding the frictionless twin

Proposed 2026-09-18 by Cowork. **DECIDED by the owner 2026-09-19: all three
recommendations in §6 taken.** TC gates nothing and is a disclosed
characteristic; estimator C is the reported TC with A and B alongside; the ruler
prints `implied_ic` at both TC = 1 and measured TC. Depends on `decisions/0015`,
`0023`, `0027`, `0029`. References verified by web retrieval on 2026-09-18;
see §8.

## 1. The gap

`src/signal_lab/audit/breadth.py` already carries

    def implied_ic(self, target_ir, horizon, transfer=1.0) -> float:
        """The IC the fundamental law would require: IR = IC sqrt(BR) TC."""

and **nothing in the lab estimates `transfer`.** Every implied-IC number the
ruler has ever printed assumes TC = 1, which is the assumption that the
long-only constraint, the 20% cash ceiling, the position and sleeve caps and the
turnover shadow cost transfer the signal into positions without loss.

This matters more than breadth does. In `IR = TC · IC · √BR`, breadth enters
under a square root and TC enters linearly. The lab measures breadth two ways
and TC not at all.

`ladder.transfer_ratio()` is not this number and its own docstring says so — it
is base net IR over frictionless net IR, costs included, and it is computed from
the frictionless cells that `decisions/0029` strikes on real data.

## 2. Definition

Clarke, de Silva and Thorley (2006), equation 23:

    TC  =  a'w / [ sqrt(a' Omega^-1 a) * sqrt(w' Omega w) ]

where `a` is the vector of expected active returns and `w` the implemented
active weights. This is the cosine of the angle between the implemented book and
the unconstrained optimum `w* ∝ Omega^-1 a`, measured in the `Omega` metric, and
under it the identity is exact:

    IR_constrained  =  TC * IR_unconstrained

Ding (2010, §23) states and proves that identity for the full-matrix form and
notes it does **not** hold for the diagonal approximation that Clarke, de Silva
and Thorley (2002) originally used — "the cross-sectional correlation
coefficient between risk-adjusted expected residual returns and risk-adjusted
active weights", i.e. `corr(a_i/sigma_i, w_i*sigma_i)`.

**Published magnitudes, retrieved rather than recalled.** Ding (2010, p.2)
reports the Clarke–de Silva–Thorley (2002) simulation range as **0.3 to 0.8**,
and notes the implication that a Grinold-formula IR "should be about halved".
Clarke, de Silva and Thorley (2006) work a directly comparable example — 21 EAFE
**countries**, long-only, a 20% cap on any country's active weight, market-beta
neutral, 1.00% monthly active risk — and report **TC = 0.671 on the full
covariance against 0.620 on the diagonal approximation**.

That example is close to this lab's problem: a long-only, benchmark-relative,
capped, country-level allocation. I previously told Leo 0.4–0.6 from memory.
That was wrong in both directions — too narrow, and centred too low.

## 3. Why not a frictionless twin

`decisions/0029` measured the twin's own covariance error rather than the price
of the constraints: condition number 6e4–2e5, bias 1.40–1.42, and a book that
realises 10.9–13.8% volatility against 6.0% ex-ante sizing. The cause is
structural, not a bug — **the constraints were doing the regularisation.** Remove
them and an ill-conditioned active covariance is inverted with nothing holding
the weights down, so the twin's answer is dominated by estimation error.

Any design that begins by re-solving the book unconstrained walks into the same
wall. The estimators below do not re-solve anything: they read the alpha vector
and the weights the constrained solve already produced.

**Confirmed at ten seeds, 2026-09-19.** `A-20260918-201042` (644 cells, 14 h,
rc=0) reproduces it without the three-seed caveat: frictionless net IR runs
-0.19 to +0.07 while the constrained ladder runs about +0.30, so the constrained
book beats its own unconstrained twin nearly everywhere, and
`ladder.transfer_ratio()` comes out between **-4 and +48**. Empirical breadth at
h4 reads **0.12 against 151.7** from the formula. A ratio that is negative, or
forty-eight, is not a measurement of anything. Whatever else is true, the twin
cannot serve as the reference book for a transfer coefficient, and 0029's
striking of the frictionless-derived numbers is not a precaution but a
requirement.

## 4. Three estimators, and what each actually costs

| # | estimator | formula | needs `Omega^-1`? | exact? |
|---|---|---|---|---|
| A | diagonal | `corr(a_i/sigma_i, w_i*sigma_i)` | no | no — ignores correlations |
| B | alignment | `corr(a, Omega w)` | no | not the level; = 1 iff `w ∝ w*` |
| C | full matrix | eq. 23 above | yes, one solve | yes — `IR_c = TC * IR_u` |

**A** is the number comparable to the published literature and to the 0.3–0.8
range. On a 95-series panel with a handful of common factors the diagonal
assumption is a real approximation, and CDT's own worked example shows the
direction: diagonal 0.620 against full-matrix 0.671, so **A understates**.

**B** exploits `w* ∝ Omega^-1 a  ⇒  Omega w* ∝ a`. It is a forward multiply, no
inverse, no conditioning exposure at all. It is an exact *indicator* of
optimality — it hits 1 if and only if the book is proportional to the
unconstrained optimum — but it is not the multiplicative TC of the identity.

**C** is the one the identity needs. I previously told Leo this could be done
"without inverting anything"; that was wrong for the level. `a' Omega^-1 a` is a
quadratic form in the inverse and it is exposed to the same small eigenvalues
0029 found. What makes it tractable rather than hopeless:

- It is **one linear solve per rebalance date**, `Omega x = a`, not an
  optimisation over a cone.
- It uses the **same Ledoit-Wolf shrunk covariance with constant-correlation
  target that the constrained solver already uses to build the book** — an
  object the lab has already shown is well enough behaved to produce a book, not
  the twin's unregularised one.
- The exposure is therefore measurable and must be disclosed: report the
  condition number of `Omega` per date beside every TC reading, which is the
  discipline 0029 exists to enforce.

**Recommendation:** compute all three, per cell. **C is primary**, A is the
comparability number, B is the conditioning-free control. When B and C disagree
materially, C is the suspect and the condition number says why.

## 5. What it does to the 0.30 bar

Using the measured `effective_bets_active = 11.67` from `A-20260917-020949`
(Meucci entropy on active returns — not a frictionless-derived number, so it
survives 0029) and `decisions/0027`'s `52/h` decisions a year, the IC required
for net IR 0.30:

| horizon | BR | TC=1.0 | TC=0.8 | TC=0.671 | TC=0.5 | TC=0.3 |
|---|---|---|---|---|---|---|
| 4 | 151.7 | 0.024 | 0.030 | 0.036 | 0.049 | 0.081 |
| 13 | 46.7 | 0.044 | 0.055 | 0.065 | 0.088 | 0.146 |
| 26 | 23.3 | 0.062 | 0.078 | 0.093 | 0.124 | 0.207 |
| 52 | 11.7 | 0.088 | 0.110 | 0.131 | 0.176 | 0.293 |

The ladder's IC rungs run 0.02 to 0.20. So:

- At h = 4 and h = 13 the bar is reachable across the whole plausible TC range.
- **At h = 52 the bar needs IC 0.13 at CDT's 0.671 and 0.29 at the bottom of the
  published range — the latter above the top rung the lab tests at all.**
  `H-2026-0011` is registered at 13–52 weeks and its own text concedes the
  horizon "sits awkwardly against a weekly rebalance". This is that concern with
  a number attached, and it is a *pre-result* number: it is arithmetic on
  measured breadth and published TC ranges, not a finding about the signal.

None of this is a reason to change a hypothesis. It is a reason to know TC
before reading a long-horizon null as evidence about markets.

## 6. Owner decisions — all three taken 2026-09-19

1. **Does TC gate anything? DECIDED: no** (owner, 2026-09-19). It is a disclosed
   characteristic and an input to `implied_ic`. A TC floor would be a gate on
   the constraint set, and the constraint set is the mandate.
2. **Which estimator is reported as "the" TC in the ruler? DECIDED: C**, with A
   alongside for comparability with the literature and B as the control (owner,
   2026-09-19).
3. **Does `implied_ic` switch from TC = 1 to measured TC? DECIDED: print both**
   (owner, 2026-09-19), because every prior audit printed the TC = 1
   version and a silent change of meaning in an append-only report is worse than
   a wider table.

## 7. Implementation, and the one thing that is not free

The estimators are ten lines each. The real work is the same migration
`decisions/0030` turned out to be: **only the weight rule knows its own alpha.**
`audit/ladder.py` builds `alpha` inside the rule's `__call__` (line ~424) and
throws it away; `RunContext.te_ex_ante` exists only because the same was true of
ex-ante TE, and `engine._ex_ante_te` reads it off the rule by `getattr` with a
missing attribute leaving the field `None` and the dependent veto unevaluable.

So: a rule MAY expose `alpha()`, the engine carries it onto the path as
`RunContext.alpha`, and a rule that does not expose it yields no TC rather than
a wrong one. One production construction site, the same shape as 0030, and the
precedent for how to do it is already committed.

Statistically this is cheap in a way an IR comparison is not. TC is a
cross-sectional correlation at each of 834 rebalance dates, so a cell yields a
distribution, not a single mean return. `decisions/0028` exists because net IR
differences below ~0.2 are unreadable at one seed; TC does not inherit that, and
does not need seed pairing to be read.

## 7a. TC under a rebalance policy that lets positions persist

Owner clarification, 2026-09-18: *signals observed weekly, positions allowed to
persist for weeks or up to a year, and not rebalancing in a given week is
acceptable.*

This does **not** change section 5. Breadth counts independent information, not
trades: a signal whose forecast lives a year does not deliver 52 independent
bets because it is observed 52 times, which is why `decisions/0027` sets
`52/h`. The h = 52 row stands.

It does change how a TC reading must be interpreted, and the point is easy to
get backwards:

**A book that deliberately does not trade sits away from its own optimum, so TC
falls by design.** Under weekly re-solve, TC measures the price of the
constraint set. Under a no-trade band or partial adjustment it measures the
constraint set *plus* the deliberate cost trade, and the two are not separable
from a single reading. A low TC would then be diagnosed as a constraint problem
when it is a policy choice that was made on purpose.

So if a rebalance policy other than weekly re-solve is adopted, TC must be
reported **twice**: against the implemented book, and against the book the same
alpha and covariance would have produced with an immediate re-solve. The
difference is the price of the persistence, which is a number worth having on
its own.

Two further consequences to check rather than assume:

- **The band width must be derived, not swept.** A tunable no-trade threshold is
  a free parameter fitted to the evaluation panel and invisible to the
  Romano-Wolf stepdown — the failure mode `H-2026-0012`'s note and
  `decisions/0016` both warn about. Garleanu and Pedersen (2013) give the
  principled form: trade *partially* toward an "aim portfolio" that is a
  weighted average of the current and expected future Markowitz portfolios, with
  slower-decaying predictors carrying more weight in the aim. That derives the
  trade rate from alpha decay and transaction costs rather than fitting it, and
  it fits `decisions/0018`'s existing choice to express the turnover penalty as
  an interpretable shadow cost rather than a lambda.
- **Stale weights against a live covariance.** Between trades the composition is
  fixed while `Omega` keeps updating, so realised risk drifts from the risk the
  book was sized for by more than it does under weekly re-solve. That is the
  same failure the TE path probe measured in 2007-09, arriving by a second
  route. It makes `decisions/0030`'s calibration statistic more informative
  under this policy, not less, and it is an argument for the volatility overlay
  (B1) rather than against it, since the overlay rescales risk without
  re-composing the book.

**None of this is a decision.** The rebalance policy itself — weekly re-solve,
a no-trade band, or partial adjustment toward an aim portfolio — is not decided
anywhere in the repo. `decisions/0024` prices turnover rather than walling it,
which is a statement about cost and not about whether to trade at all, and the
engine re-solves every week. That gap should be a record of its own.

## 8. What this does NOT answer

TC says how much signal survives the constraint set as a whole. It does not say
**which** constraint costs what. That needs a relaxation ladder — long-only off,
then the cash ceiling, then position and sleeve caps, then turnover, then the TE
budget — measuring the change at each rung. That compares IRs, so it needs ten
seeds and seed pairing, and it multiplies audit cells. It belongs after TC has
produced a number worth decomposing, not before.

## References

Verified by retrieval on 2026-09-18. `params/data_sources.yaml` allowlists no
reference resolver, so these are recorded here with their retrieval URLs rather
than registered as `literature` provenance under SUBSTRATE section 7. Note that
the same retrieval route would let several hypotheses be re-registered from
`adaptation` to `literature`, which STATUS.md flags as pending a resolver.

- Clarke, R., de Silva, H. and Thorley, S. (2002). "Portfolio Constraints and
  the Fundamental Law of Active Management." *Financial Analysts Journal*
  58(5), 48–66. DOI 10.2469/faj.v58.n5.2468. Full text is behind CFA Institute
  membership; the 0.3–0.8 range below is taken from Ding (2010), not read in the
  original.
- Clarke, R., de Silva, H. and Thorley, S. (2006). "The Fundamental Law of
  Active Portfolio Management." *Journal of Investment Management* 4(3), 54–72.
  Retrieved from https://joim.com/wp-content/uploads/emember/downloads/p0158.pdf
  Equation 23 is the definition used here; the EAFE example gives TC = 0.671
  full-matrix against 0.620 diagonal.
- Ding, Z. (2010). "The Fundamental Law of Active Management: Time Series
  Dynamics and Cross-Sectional Properties." Retrieved from
  https://math.nyu.edu/inmemoriam/avellaneda/FundamentalLawFT.pdf
  Source for the 0.3–0.8 range attributed to Clarke et al. (2002), and for the
  full-matrix redefinition and the `IR_c = TC * IR_u` identity.
- Garleanu, N. and Pedersen, L. H. (2013). "Dynamic Trading with Predictable
  Returns and Transaction Costs." *Journal of Finance* 68(6), 2309-2340.
  DOI 10.1111/jofi.12080. Working paper retrieved from
  https://www.nber.org/papers/w15205 -- source for "aim in front of the target",
  trading partially toward the aim, and slower-decaying predictors carrying more
  weight in the aim portfolio.
