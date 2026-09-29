# 0039 — The lab screens; it does not confirm

**Status:** decided 2026-09-28 by the owner (OWNER-QUEUE L15: "screen").
Drafted by Cowork. Sections marked *open* are not ruled yet (OWNER-QUEUE L16).
Nothing here is applied until a HANDOFF task lands it, citing this record.

## The measurement behind it

Task 30 (`A-20260926-161749`) planted a signal of IC 0.70 on the development
window, far stronger than a realistic macro signal. The signal beat all 20
score-span shuffles in 4 of 10 seeds. The estimated single-test power is about
35-45% at 5%, before Romano-Wolf. The limit is one draw of noise-timing luck
per history, worth −0.15 to +0.47 in excess at the same IC, not the width of
the null. More history shrinks the luck and the information at the same
rate. The holdout has the same property (OWNER-QUEUE L4): about 350 weeks
gives t ≈ 0.8 at a true IR of 0.30.

## The ruling

The lab is a **screen**:
- **A pass on both bars makes a hypothesis a *candidate*:** worth capital, scrutiny
  and further evidence. It is never reported as confirmed or proven.
- **A bar-2 failure is "not detected", not "false".** The hypothesis is not
  retired on that ground alone. The record states the power at the planted IC
  nearest its realised IC, so a reader sees how likely a real effect was to be
  missed.
- **Bar 1 is unchanged** (net IR ≥ 0.30), and so is the rest of §10.

## What changes, when applied

1. **`SUBSTRATE.md` §3:** a paragraph after bar 2 stating the above and the
   measured power. It should also carry L4's holdout-power sentence, so both
   power limits sit in one place. One owner edit, not two.
2. **Report and leaderboard wording:** "candidate" and "not detected", never
   "confirmed" or "rejected".
3. **Hypothesis lifecycle:** a `done/` hypothesis that fails bar 2 carries
   `verdict: not_detected` and the power figure, not `rejected`.

## Open — OWNER-QUEUE L16

- **Is Romano-Wolf at FWER 5% still the right bar for a screen?** *Owner,
  2026-09-28: most likely FDR, to be confirmed once HANDOFF task 34's
  FDR-vs-FWER study is read. Not ruled.* FWER
  controls the chance of *any* false pass, which is a confirmation standard.
  Screens usually control the *share* of false passes (FDR, e.g.
  Benjamini-Hochberg, SUBSTRATE §9). Keeping FWER while calling the output a
  screen means screening at a confirmation standard, which has low power on
  top of low power.

## Confirmation gates — decided 2026-09-28 (owner, OWNER-QUEUE L16)

A candidate is admitted only through **two gates, both required**:

1. **Replication.** The effect shows up where it was not tested.
2. **Economic intuition.** In the owner's words: "The thesis needs to be
   synthesized in a way that fits as plausible real world discovery. It may be
   surprising at times, but if the statements that need to be true about them
   need to be so far-fetched that borderlines what a conspiracy theorist would
   need to assume to be true for the theory to be real, then it means we are
   probably off track."

A paper track and a live allocation are **not** gates. Neither can confirm a
signal at a realistic IR in any realistic time (t ≈ IR·√years; IR 0.30 needs
about 44 years for t = 2).

**How the gates are made operational. Proposed by Cowork; adopted in full by
the owner on 2026-09-28 (OWNER-QUEUE L16: "yes, adopt all three"):**
- **A thesis synthesis per candidate.** State the mechanism in plain language,
  say who is on the other side of the trade and why the edge persists, and list
  **the statements that must be true for it to work**. The owner judges that
  list against the plausibility test above. It is also checked against the
  pre-registered rationale: the right channel, horizon and sign. A result that
  works for a different reason than the one registered fails the gate, even if
  it is profitable.
- **The replication target is fixed before looking**, in the hypothesis file
  or at candidate time, and before any replication data is read. Otherwise the
  gate becomes a search. Candidate targets: other markets or cross-sections of
  the same signal (e.g. 0010's carry exists on 14 cids), or the holdout, which
  is read once.
- **Rival explanations are named and checked:** a static tilt, a known factor,
  or a single macro bet (the B5 risk decomposition, when it exists).

