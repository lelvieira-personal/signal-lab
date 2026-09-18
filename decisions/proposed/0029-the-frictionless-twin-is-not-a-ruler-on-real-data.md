# 0029 (PROPOSED) — The frictionless twin is not a ruler on real data

Status: **proposed, 2026-09-17**, from the standardisation probe
`results/audit/_probe/P-20260917-bbg1` (Bloomberg, 10 seeds, 320 frictionless
cells, 12 base cells, 32 panel diagnostics). Amends `decisions/0027` §3. Owner
decision required before anything in `params/` or the report changes. Nothing
here has been applied.

## Context

The first Bloomberg ruler audit (A-20260917-020949) produced a ladder that
barely responds to IC and a frictionless twin near zero, with empirical breadth
of 0.8 at h=4 and 0.0 at h=13 against a formula breadth of 151.7 and 46.7. Three
explanations were on the table. The probe ran all three down.

## What the probe found

**A. "The IC label is pooled, the book spends the cross-section" — refuted.**
The truth's common share (the part of its variance that moves every instrument
the same way on a date) is **0.01 at every horizon**. Planting the truth
standardised per date instead changes nothing: across all 160 cell pairs the two
modes agree to about 0.01 of IR. The `cross_sectional` mode stays in the code as
a measured no-op on this panel, not as a fix.

**B. "The audit's cross-sectional IC reading is an artefact" — partly true, and
presentational.** At h=26, IC 0.20: pooled 0.200, per-date Pearson 0.134,
per-date rank 0.026. The rank reading understates the planted signal about
fivefold because the truth is heavy-tailed within a date. The audit reports the
rank number, which is what made the ladder look emptier than it is.

**C. "The covariance eats the signal" — confirmed, and it is the whole story.**

| | synthetic | Bloomberg |
|---|---|---|
| frictionless bias statistic | 1.05–1.17 | **1.40–1.42** |
| frictionless IR at h=13, IC 0.20 | +1.11 | **−0.02** |
| frictionless IR at h=52, IC 0.02 → 0.20 | −0.17 → +0.37 | **−0.19 → −0.16** |

On the Bloomberg panel the frictionless ladder is **negative and flat in IC** at
every horizon but h=4. With 10 seeds the seed sd is 0.18–0.24 over 40 cells a
horizon, so a standard error of about 0.04: the negative level is not noise.

The machinery is not broken. At IC = 1 the same frictionless book returns
**+4.41 / +1.90 / +1.17 / +0.70** by horizon. What fails is the sizing: the
active covariance it inverts has a condition number of **6e4 to 2e5** (smallest
eigenvalue about 1e-7 in weekly variance units), so `inv(Sigma_x) alpha` loads
its budget onto directions the estimate says are nearly free. The book is sized
to 6.0% ex-ante TE and realises 10.9% to 13.8% at IC = 1. At a realistic IC the
covariance error dominates the alpha, and what is left drifts negative — the
more so the slower the signal, which holds the same noise positions for longer.
This is Jagannathan–Ma with the constraint removed: the long-only books on the
SAME covariance have a bias statistic of 0.92–1.01.

## What follows

1. **Strike the frictionless-derived numbers from the Bloomberg report** —
   empirical breadth, the FLAM-implied comparison, and the base/frictionless
   "price of the constraints" ratios (which ran to −8.6). They measure the
   covariance estimate, not the layer.
2. **Give the frictionless solve a conditioned covariance** — an eigenvalue
   floor or a ridge on `Sigma_x`, chosen so the frictionless bias statistic sits
   near 1.00 on the Bloomberg panel, and documented as part of the ruler rather
   than as a portfolio choice. The twin is only a reference if it is sized
   honestly.
3. **Keep the twin as the covariance-error diagnostic** it turned out to be: the
   bias statistic is the number that carries the finding.
4. **Read empirical breadth off the constrained ladder** until 2 is done.
5. **Report the per-date Pearson IC beside the rank IC** in `cells.csv` and the
   report (the columns exist now: `cross_sectional_pearson`,
   `cross_sectional_demeaned`).

## What the probe does NOT settle

- The right conditioning (floor level, ridge size, or a factor covariance) is
  unchosen. Whatever is picked has to be justified as a measurement device, not
  tuned until the ladder looks good.
- The constrained ladder's own noise: at h=13 the probe's base cells give net IR
  0.11 at IC 0.05 and 0.37 at IC 0.20, with a seed sd of 0.21–0.31 over 3 seeds.
  That is a response in the right direction and it is not resolvable at 3 seeds.
  `decisions/0028` (ten seeds) is still the right call for the base ladder.
- The TE veto question (`decisions/0027` §2) is untouched here and still forced:
  the probe's IC 0.20 base cells read TE p95 / budget of 1.39–1.41 while sized
  under budget.
