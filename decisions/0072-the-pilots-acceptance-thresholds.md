# 0072 -- The planted-signal pilot's acceptance thresholds (`decisions/0059` G)

**Status:** APPLIED 2026-11-15 by Cowork (afternoon review, addendum at the end) and moved from `proposed/` to `decisions/`: region cross-sectional accepted on the pilot, duration directional not accepted. Was: PROPOSED 2026-11-14 by Cowork (afternoon review), for the owner. Reserved (`decisions/0069` item 2: "the planted-signal pilot's acceptance thresholds"; and, where it touches bar 1 or bar 2, SUBSTRATE §1 to §3). **RULED BY THE OWNER, CONDITIONALLY, 2026-11-14 19:01 ET: the recommendation, applied after HANDOFF task 98's receipt** (owner ruling at the end of this record). **Twin design ruled 2026-11-15 09:36 ET: (k) keep** (owner ruling, last paragraph). Stays in `proposed/` until the review that reads task 98's receipt applies it and moves it to `decisions/`; task 98's step 0 expects this path untracked.

## Where things stand

Task 94 ran the grid of `0059` G on the `0070` defaults: 140 runs, all complete, lookahead passed on all 140 (`results/audit/A-20261114-030208/report.md`, `cells.csv`; planted data, no vendor values; receipt in `HANDOFF.md` `## Done`, 2026-11-14). The numbers below are Cowork's arithmetic on `cells.csv` (25 runs per expression at `IC_prior` x1, 5 seeds each).

| | region cross-sectional | duration directional |
|---|---|---|
| mean `net_ir_excess` at IC 0 / 0.05 / 0.10 / 0.20 / 0.35 | -0.017 / 0.064 / 0.109 / 0.180 / 0.309 | 0.009 / 0.000 / 0.055 / 0.044 / 0.111 |
| slope of excess on planted IC (OLS, 25 runs) | 0.88, t = 6.2 | 0.29, t = 1.9 |
| IC 0.35 excess min vs IC 0 excess max (G's "clear of") | 0.180 > 0.091: clear | -0.055 < 0.072: not clear |
| IC 0 runs with excess > 0 (first half of bar 2) | 3 of 5 | 3 of 5 |
| IC 0 runs with net IR >= 0.30 (bar 1) | 0 of 5 | 2 of 5 |
| IC 0 runs passing bar 1 and excess > 0 | 0 of 5 | 1 of 5 |
| baseline twins (35) with net IR >= 0.30 | 8 | 16 |
| baseline twins' realised IC, per seed (`realised_ic_by_column`) | -0.03 to +0.10 | 0.00 to +0.15 |

**Three things the table says (Cowork's reading; task 98 tests each):**
1. **Region separates; duration does not, at five seeds.** A directional view has one column: about 60 independent 13-week blocks in 2004 to 2019, so a single score's realised IC carries a standard error near 0.13 (1/sqrt(60), a back-of-envelope figure). The block-shuffled baseline twin is itself such a draw: its realised IC ran 0.00 to 0.15 on duration. Against that noise a planted IC of 0.05 to 0.20 is not resolvable with five pairs. That would be a power property of the design, not a fault, but it is unconfirmed (task 98 step 1).
2. **Noise earns money in this window.** IC 0 duration runs averaged net IR 0.30 (region 0.13), and the shuffled twins about the same, against -0.077 for a zero-view book (task 91, pre-`0070` objective). Any active risk the long-only book took seems to have been paid over 2004 to 2019 (one guess: a long-only book cannot short, so a symmetric noisy view tilts it toward risk). If that holds, **bar 1 on its own passes noise often (2 of 5 IC 0 duration runs) and bar 2 carries the protection.** Task 98 step 2 measures the zero-view floor on the `0070` defaults and where the IC 0 runs' active return comes from.
3. **`IC_prior` moves the answer through costs, not monotonically:** at IC 0.10, region 0.108 / 0.109 / 0.044 and duration 0.037 / 0.055 / 0.107 at x0.5 / x1 / x2. No threshold is proposed on it; it is reported.

The first-trade question of the prefill ruling (`decisions/0070`, owner line of 2026-11-13) is not answered by task 94 (its column caught a forced sale); task 98 step 3 answers it.

## The bars, options

**A. Dose-response, per expression.**
- **(a1)** G's example as written: mean excess rises with planted IC (Spearman rank 1.0 across the five levels) and every IC 0.35 run clears every IC 0 run. Strict; with five seeds one bad draw fails it.
- **(a2)** A slope test: OLS slope of `net_ir_excess` on planted IC positive with t >= 2 over the runs at `IC_prior` x1, **and** mean excess at IC 0.35 above mean excess at IC 0 by at least 0.10 (*provisional*: about a third of the region gap measured). Uses every run, tolerates one bad seed.
- **(a3)** (a2), judged on more seeds for the directional expression (20, as a `long` run) before any verdict on it.

**B. False pass at IC 0.**
- **(b1)** The share of IC 0 runs that pass bar 1 **and** the first half of bar 2 (excess > 0) is at most 10% (*provisional*; needs at least 15 IC 0 runs per expression to mean anything, which task 98 adds).
- **(b2)** As (b1) at 5%.
- **(b3)** Run the real bar 2 (the stepdown of SUBSTRATE §9) on the pilot's IC 0 runs and require its false-pass rate at most its nominal 5%. Closest to what a verdict will use; needs a build task (the pilot does not run the stepdown).

**C. What an expression that fails means.** (c1) The rule is accepted per expression: cross-sectional now, directional when it passes. (c2) Neither is accepted until both pass.

## Cowork recommends

**(a2) + (b1) + (c1), ruled after task 98**, and (a3) for the directional expression if task 98 confirms reading 1 (the power, not a fault). On today's numbers that accepts region cross-sectional (t 6.2, gap 0.33, false pass 0 of 5) and leaves duration directional unaccepted. *Basis:* (a2) uses all 25 runs instead of two extremes; a 10% false-pass bar on a planted pilot is looser than the 5% FWER of bar 2 because the pilot reads only the first half of bar 2 and five-to-fifteen runs cannot resolve 5%. **Separately, for you only** (SUBSTRATE §2, reserved): reading 2, if task 98 confirms it, says bar 1 alone does little against noise in this window; nothing here proposes to change it.

## Questions for the owner

1. Rule now on today's numbers, or after task 98 (recommended)?
2. A: (a1), (a2) or (a3)? The 0.10 gap: yours to set.
3. B: (b1), (b2) or (b3)?
4. C: (c1) or (c2)?

## Owner ruling, 2026-11-14 19:01 ET (chat, linked session)

The owner's words: "Go with after 98 recommended pending decision." Read by Cowork as answering the four questions:
1. **After task 98** (not on today's numbers).
2. **A: (a2)**, the gap of 0.10 as written; **(a3)** for duration directional if task 98 confirms reading 1 (power, not a fault): 20 seeds as a `long` run before any verdict on it.
3. **B: (b1)**, at most 10% of IC 0 runs passing bar 1 and excess > 0, judged on at least 15 IC 0 runs per expression (task 94's seeds 0 to 4 plus task 98's 5 to 14).
4. **C: (c1)**, accepted per expression.

**How it is applied (Cowork's reading; the owner strikes it by a line in chat).** The review that reads task 98's receipt applies the ruling to the pooled numbers and moves this record to `decisions/`, without coming back to the owner, **unless** one of these holds, in which case only that point comes back: (i) task 98 trims the null grid below 10 new seeds, so (b1) has fewer than 15 IC 0 runs for an expression; (ii) task 98 step 1 stops on its fault branch (the shuffle keeps truth), which would change what the baseline twin and so `net_ir_excess` mean; (iii) task 98's numbers make a *provisional* figure (the 0.10 gap or the 10%) plainly unfit, e.g. no expression could meet it on any IC; Cowork does not reset a reserved number itself. The separate SUBSTRATE §2 note (bar 1 alone against noise) is not part of this ruling and stays with the owner.

## What it would move

The acceptance run of `0059` ("the owner rules them; then the acceptance run") and, through it, M7 (the first signal modules). No recorded audit number, golden or verdict: the pilot is planted.

## Addendum, 2026-11-15 (Cowork, morning review): task 98 stopped on step 1; condition (ii) read as not met; one question on the twin

**What happened.** Task 98 stopped on step 1's literal fault branch (receipt in `HANDOFF.md` `## Done`, 2026-11-14; report `results/pilot_null/ic_report.md`). Steps 2 and 3 (the IC 0 runs on seeds 5 to 14, the zero-view floor, the factor attribution, the first trade) did not run. So this ruling is not applied yet: there are still only 5 IC 0 runs per expression.

**Cowork's reading (delegated ruling `decisions/0073`): the stop was Cowork's test, not the shuffle.** The 200 draws were five seed clusters; with the seed as the unit both means are inside chance (duration z 1.3, region z 1.2). The shuffle cannot carry truth into an IC 0 twin at all, so task 99 step 1 tests it directly and on 15 seeds. **So condition (ii) above ("the shuffle keeps truth") is read as not met, and HANDOFF task 99 (the rest of task 98) is released.** Strike this by a line in chat if you read your condition literally (the step-1 stop branch fired); then nothing of `0072` is applied until you rule.

**The question for you (your condition (ii): what the twin, and so `net_ir_excess`, means).** `plant_axis_signal` orthogonalises the live cell's noise to the real truth, so its realised IC is exactly the planted IC, with no luck. The twin's noise is orthogonalised to the shuffled truth only, so it keeps the noise's chance IC against the real truth: SD about 0.115 on the one directional column (0.047 on region's six). Task 94's twins ran 0.00 to +0.15 (duration). `net_ir_excess` = live minus twin therefore carries one luck term, the twin's, which is as large as the planted ICs of 0.05 to 0.20 on duration. That is most of reading 1 (the power).
- **(k) Keep it** (the `0036` / `0059` G design). Duration's power comes from more seeds: your (a3), 20 seeds `long`. No number of task 94 or 98 changes.
- **(m) Orthogonalise the twin's noise to the real truth too.** Both cells luck-free. The twin's realised IC becomes about IC x corr(shuffled, real truth), near 0. At IC 0 the two cells are almost the same score, so excess at IC 0 is near 0 by construction and (b1)'s false-pass test stops measuring anything. Highest power. Reruns task 94's twins.
- **(n) Orthogonalise neither.** Both cells carry the same seed's luck, as a real signal would, and it cancels in the pair: at IC 0 the two scores are identical and excess is exactly 0, so (b1) again measures nothing. The live cell's realised IC becomes the planted IC plus luck. Reruns task 94 whole.
- In a real audit the luck sits in the live score (a zero-IC signal still has a chance IC), and a shuffled baseline adds a fresh draw of its own (Cowork's understanding of `0036`, not re-read this run). So a real comparison carries two luck terms; (k) carries one, (m) and (n) none.

**Cowork recommends (k)**: it is the only option under which the IC 0 false-pass test (b1) still measures noise; it is the design every planted audit since `0036` used; it is closer to a real comparison (one luck term against two) than (m) or (n) (zero); and (a3) already buys the power. Task 99's step 1 reports the twins' realised IC under (k), (m) and (n) for seeds 0 to 14 (no solves), so you can see the size before you choose. Task 99 does not depend on the answer: under (k) nothing reruns; under (m) or (n) the IC 0 twins of task 99 (20 runs, about 1.4 hours, a guess) and task 94's grid would be rerun.

**Owner ruling, 2026-11-15 09:36 ET (chat, linked session).** The owner's words: "decision 0072: keep". Read by Cowork as **(k): keep the twin as built** (the `0036` / `0059` G design; the twin's noise orthogonalised to the shuffled truth only). Nothing of task 94 or task 99 reruns; duration directional gets its power from (a3), 20 seeds as a `long` run, as already ruled. The owner did not strike the addendum's reading of condition (ii), so it stands: the step-1 stop does not bring the ruling back to him. The review that reads task 99's receipt applies (a2) + (b1) + (c1) to the pooled numbers and moves this record to `decisions/`, unless condition (i) or (iii) holds, or task 99's step 1 reverses `decisions/0073` (its direct shuffle test or the 15-seed test fails); then only that point comes back to the owner.

## Addendum, 2026-11-15 (Cowork, afternoon review): the ruling applied to task 99's pooled numbers

**Delegated ruling, 2026-11-15, Cowork review** (applying the owner's ruling of 2026-11-14 as its "How it is applied" paragraph directs, with the twin as built, (k), ruled 2026-11-15). *The question:* do the pooled numbers meet (a2) + (b1), per expression (c1), and does any condition bring the ruling back to the owner? *Conditions:* (i) not met: task 99 ran all ten new seeds, so 15 IC 0 runs per expression. (ii) not met: `decisions/0073` stands (task 99 step 1: seed-unit z -0.20 duration, -0.95 region over 15 seeds; the shuffle's mean correlation with the real truth +0.003 and +0.009, inside 3 SD/sqrt(200); the reviewer agrees). (iii) not met: region meets both provisional figures, so neither is plainly unfit.

*The numbers* (Cowork's arithmetic on `results/audit/A-20261114-030208/cells.csv` and `results/audit/A-20261115-105504/cells.csv`; `IC_prior` x1, zero-score rows left out; excess = live net IR minus its twin's):

| | region cross-sectional | duration directional |
|---|---|---|
| (a2) slope of excess on planted IC, t: the grid's 25 runs | 0.88, t 6.17 | 0.29, t 1.86 |
| same with the null grid's 10 IC 0 runs added (35) | 0.84, t 7.28 | 0.33, t 2.50 |
| (a2) gap, mean excess IC 0.35 minus IC 0 (grid / pooled) | 0.326 / 0.295 | 0.102 / 0.120 |
| (b1) IC 0 runs with net IR >= 0.30 and excess > 0 (15) | 1 (6.7%) | 4 (26.7%) |

*Choice.* **Region cross-sectional: accepted on the pilot** ((a2) t >= 2 and gap >= 0.10 on either run set; (b1) at most 10%); confirmed on fresh seeds by the acceptance run (`decisions/0074`, HANDOFF task 100) before M7 builds on it. **Duration directional: not accepted** ((b1) fails, 27%; (a2) fails on the grid's 25 runs and passes only when the null grid's IC 0 runs are pooled in, which triples the weight of IC 0 and is not the balanced set the slope was proposed on). Read "the runs at `IC_prior` x1" as the grid's 25; the pooled figure is reported beside it and changes neither verdict. *Basis:* the owner's ruling above, applied as written; the arithmetic is in the table and can be re-run from the two files.

*Why duration fails (b1) (for the owner; not ruled here).* Duration IC 0 runs pass bar 1 in 6 of 15 (40%) and their twins in 47%; excess > 0 in 10 of 15. The IC 0 duration books and their twins carry the same persistent factor tilt (mean active exposure over the null grid's 10 seeds, live vs twin: real yield -1.27 vs -1.40, inflation -1.85 vs -1.92, credit -0.94 vs -1.02, equity +0.050 vs +0.041; active return 1.31% vs 1.34% a year; unexplained 0.44% vs 0.40%: Cowork, from the null grid's `cells.csv`). Leaked truth would make the live run and its twin differ; they do not. So this is a structural tilt the long-only rule takes from any noisy duration view in 2004 to 2019, which bar 2's excess removes and bar 1 does not: reading 2 of this record, confirmed. Under (b1) as ruled, a directional duration expression cannot be accepted while bar 1 passes its noise about 40% of the time (expected false pass about 0.4 x 0.5 to 0.67, i.e. 20 to 27%, against 10%). Bar 1 is SUBSTRATE §2 and (b1) is this record's: both the owner's.

*(a3).* The 20-seed duration run (ruled) can improve (a2)'s power but is unlikely to bring (b1) under 10% (4 of 15 has a 95% interval of roughly 8% to 55%). Cowork has written it (HANDOFF task 101) and holds it for the owner: run it as ruled, or hold it until bar 1 or (b1) for directional expressions is settled.

*Which numbers it can move:* none recorded; it decides which expression the acceptance run tests and, through it, M7 (cross-sectional first). *What would reverse it:* the owner striking a reading here; the acceptance run failing on fresh seeds (region then not accepted and back to the owner); an arithmetic error found by the reviewer.

*Review pending* until HANDOFF task 100 step 1 (Opus, fresh session; `decisions/0069` item 4 is not strictly required, since nothing here touches `src/`, a golden or a store, but it is done anyway).

**Owner ruling, 2026-11-17 22:26 ET (chat, linked session), on (a3).** The owner's words: "accept recommendation on task 101". Read by Cowork as: **HANDOFF task 101 (the 20-seed duration directional run) is held**, not run, until bar 1 or (b1) for directional expressions is settled. Duration directional stays not accepted on the pilot; region cross-sectional goes on through the acceptance run (HANDOFF task 100) to M7. The open question (whether bar 1, SUBSTRATE §2, or (b1) should treat a directional expression differently, given the shared factor tilt above) stays with the owner, on the reserved list; nothing here rules it. Task 101's text is unchanged and can be released as written once that is settled.

**Owner ruling, 2026-11-17 22:37 ET (chat, linked session), on bar 1 and directional expressions.** Cowork set out four options: (1) leave bar 1 and (b1) as they are, so a directional duration expression cannot be accepted on the pilot and the lab goes on with cross-sectional expressions; (2) measure (b1) with the full bar 2 (excess > 0 **and** the stepdown of `stats.multiple_testing.gate`) in place of excess > 0 alone, since the pilot reads only the first half of bar 2; (3) change bar 1 itself (SUBSTRATE §2); (4) loosen the 10%. The owner's words: "1 now and 2 next, agree". So: **(1) now**: bar 1, (b1) and the 10% stand; duration directional is not accepted; M7 goes ahead on region cross-sectional. **(2) next**: measure the IC 0 duration runs' false passes under the full bar 2. Task 101 stays held until that measurement is read. Options (3) and (4) are not taken.

*Cowork's notes for writing the measurement (not ruled; build choices are delegated under `0069`):* the gate needs at least `min_shuffles` = 100 block shuffles per test (`params/vetoes.yaml`), so it needs new solves, about 100 per run. A rough guess from the `vetoes.yaml` comment (~28 h for a 12-test cycle at 100 shuffles) is a day and a half of machine time for 15 runs. Whether the phase-2 path already calls the gate is not established: a grep of `harness/experiment.py` found no call. If it does not, wiring it is a number-making `src/` change and needs a reviewer (`0069` item 4). It runs after HANDOFF task 100 and on planted data only; the reading goes back to the owner, because (b1) is his.
