# 0038 — Turnover is priced and disclosed, never vetoed

**Status:** decided 2026-09-28 by the owner (OWNER-QUEUE B2, 2026-09-25; B3,
2026-09-28). Drafted by Cowork from the owner's words. Not yet applied: the
`params/`, `vetoes/` and `SUBSTRATE.md` changes land as HANDOFF task 33, citing
this record.

## The ruling

- **B2 (2026-09-25):** there is no per-rebalance turnover cap. Friction (the
  real costs in §8 and the shadow cost of `decisions/0024`) is what restrains
  trading. `params/audit.yaml` already has `per_rebalance_cap_default: null`,
  and the `per_rebalance_caps` sweep stays as a diagnostic.
- **B3 (2026-09-28), in the owner's words:** "400% level is only reported.
  Actually anything over 200% should be highlighted, but no veto. Drop the 400%
  as a reference." The window question is therefore moot: nothing vetoes, in
  either window.
- **The friction experiment is approved (B3c):** a sweep of the shadow-cost
  coefficient, so the owner can see how results respond to more friction.
  That's HANDOFF task 32.

## Why

The owner judges whether a heavily traded book is practical for an investor
by looking at it. A veto would hide exactly the result he wants to see. That
kind of book may still show what is valuable, and may motivate more friction
rather than a wall. This is the same move `decisions/0030` made for realised
tracking error: from a gate to a disclosed characteristic.

## What changes

1. **`params/vetoes.yaml`:** delete the `turnover:` block and remove `turnover`
   from `evaluation.order`.
2. **`SUBSTRATE.md` §10:** delete the `turnover` row. "Ten vetoes" becomes
   "Nine vetoes", citing this record.
3. **`SUBSTRATE.md` §4, Turnover row:** replace "A per-session cap stops any
   one rebalance consuming the year." with "There is no per-session cap
   (`decisions/0038`). Turnover is disclosed on every run and highlighted above
   200%; it is never vetoed."
4. **Disclosure.** Every run reports annual traded notional and rolling one-year
   traded notional (p95 and max), as the audit already does. Add
   `params/constraints.yaml` `turnover.highlight_annualised: 2.00`, a
   **reporting threshold only**. The report and leaderboard mark any cell whose
   annual figure **or** rolling one-year max exceeds it. Applying it to both
   windows is Cowork's reading of "anything over 200%". The owner may narrow it.
5. **Code:** the `turnover` check leaves `audit/ladder.py`'s veto evaluation,
   and every reader of `vetoes.turnover.max_annualised` goes. Tests that assert
   a turnover veto are rewritten to assert the highlight.

## Consequences

- **`params_hash` changes.** Hash-matched comparisons against earlier runs
  (`A-20260922-005316`, `A-20260926-161749` and the others) no longer match by
  construction. Task 33 records the old and new hash here. Any grid that reuses
  twins from a pre-0038 run must re-run them instead.
- **Past verdicts:** in the Bloomberg audits, annual turnover never exceeded
  400% (worst 342% and 355%), so no recorded verdict should change. Task 33
  verifies this from the stored `cells.csv` files.
- Turnover no longer protects against a malfunctioning book. The disclosure and
  the owner's review do that now.

## Addendum 2026-09-29: the highlight's windows (owner, OWNER-QUEUE L17)

The owner narrowed item 4. **The highlight applies to the annual figure and to
the rolling one-year p95 ("both"), not to the rolling one-year max.** The max
is still reported but not highlighted. The reason is evidence from the friction
sweeps (`A-20260928-151055`, `A-20260929-070540`): the rolling max was above
200% in 59 or 60 of 60 cells in both runs, whatever the friction, so it
separated nothing. The p95 does separate books: `created` at 40 bp and IC 0.35
is 0 of 10 above 200%.

In item 4, read "whose annual figure **or** rolling one-year max exceeds it"
as "whose annual figure **or** rolling one-year p95 exceeds it". The params key
is `turnover.highlight_annualised: 2.00`, plus
`turnover.highlight_windows: [annual, rolling_1y_p95]`. Both are reporting
only.

**Applied together with `decisions/0040`** by HANDOFF task 39, which
supersedes task 33, so `params_hash` moves once.

