# 0034 — A `data_required` name must resolve at registration

Proposed 2026-09-19 by Cowork. Status: **decided** 2026-10-21 by the owner ("In any case i agree with the proposed validation"); resolution sources fixed by HANDOFF task 63. Split out of
`decisions/proposed/0032` §6 by the owner's ruling, 2026-09-19, so the ticker
reconciliation could land without waiting on a code change.

## What happened

Two instruments in the pre-registered hypothesis registry do not exist.
`LUALTRUU` (`H-2026-0004`, and as an OAS field in `H-2026-0007`) and `LT08TRUU`
(`H-2026-0010`) are in no coverage table, no vendor pull, and the owner does not
recognise either — *"for sure not one that I use today. Maybe it was a typo or
LLM mistake."* Both were written by an agent in phase 0 and both survived
validation, review and eleven months of the registry being described as the
lab's strongest artefact.

They were found by hand, in a reconciliation nobody had scheduled.

## Why the harness did not catch them

`harness/hypotheses.py` already refuses a fabricated **citation**: a
`literature` provenance whose `reference` will not resolve is rejected at
registration, because SUBSTRATE section 7 treats inventing a source as a failure
of the proposer.

It does not refuse a fabricated **instrument**. `validate_hypothesis` type-checks
`data_required` as a list of strings and never asks whether the strings name
anything. Resolution happens later, at run time (`hypotheses.py` ~line 373),
where a name absent from the manifest yields `blocked:data`.

**`blocked:data` is the problem.** It is the correct and expected status for
every one of the 27 JPMaQS series the registry legitimately awaits. A fabricated
ticker produces exactly the same status, so the registry's own machinery
converts an invention into something that looks like patience. All eleven
hypotheses have been sitting at `blocked:data` since phase 0; two of them were
partly blocked on nothing.

A fabricated instrument and a fabricated citation are the same class of error.
The lab catches one at the door and files the other under "waiting for data".

## Proposed

`validate_hypothesis` resolves every `data_required` entry at registration and
rejects an entry that matches nothing:

1. **Bloomberg / FRED names** resolve against the coverage tables in
   `data/universe/` — `investable_universe.csv`, `bbg_index_coverage.csv`,
   `bbg_analytics_coverage.csv`, `bbg_exusd_bonds_coverage.csv`,
   `fred_coverage.csv` — plus the benchmark legs named in
   `params/constraints.yaml`, which are real and deliberately not holdable.
   An `INDEX_FIELD` suffix resolves on the ticker and the field separately.
2. **JPMaQS names** resolve against the naming convention of `decisions/0014`
   rather than against a pull, because no pull exists until phase 3. A
   well-formed `CCY_CATEGORY_TRANSFORM` name validates; a malformed one does
   not.
3. **Anything matching neither is rejected**, with the offending entry named.

The distinction this preserves: a name that is **real but not yet pulled** still
validates and still becomes `blocked:data`, which is the status working as
designed. A name that is **real nowhere** never reaches that status.

## What this does not do

- It does not check that a real ticker is the *right* ticker. `MXEF` was a real
  MSCI EM identifier and still wrong for this panel, where the series is `M1EF`.
  Resolution catches inventions, not mistakes, and the eight renames in 0032
  would all have passed this check.
- It does not re-validate the registry retroactively. The twelve existing files
  are corrected by the 0032 patch; this rule applies from registration onward.
  A one-off validation pass over `hypotheses/pending/` is worth running once the
  rule exists, and should find nothing.

## Cost

A resolver function, a call in `validate_hypothesis`, and the usual three tests
per rule — passing, failing, boundary. The coverage tables are already parsed
elsewhere in the repo. No owner-only path is touched: `harness/` and `tests/`
only.

## Why it is worth it now rather than in phase 3

Phase 3 opens the search. From that point a fabricated entry costs a cycle,
a `blocked:data` status that reads as routine, and an agent's attention to
re-discover — and the registry is about to be amended anyway by the 0032 patch,
so the validation pass over the corrected files is free if the rule exists
first.

## Owner's ruling, 2026-10-21

The owner agrees with the proposed validation (rules 1 to 3 above). Recorded
by Cowork from the owner's message of 2026-10-21. **No task is queued yet:**
writing one into `HANDOFF.md` is the owner's release, and this record has not
moved out of `decisions/proposed/` (a `git mv` is a worker commit).

## Correction to "What happened", 2026-10-21 (owner)

`LT08TRUU` is **not** fabricated. The owner reports it is a real Bloomberg
index, the US Treasury: Intermediate Index (US dollar, fixed-rate nominal
Treasuries, 1 to 9.9999 years to maturity; future ticker `I00049US`). Cowork has
not verified this. What `decisions/0032` found stands: the ticker was in no
coverage table and the owner did not recognise it. "Fabricated" and "does not
exist" in 0032, in OWNER-QUEUE L6 and in `H-2026-0010`'s notes are wrong for
`LT08TRUU`; they are right for `LUALTRUU` on the owner's word. Those records
are not edited here. The owner offered a one-off pull of `LT08TRUU`; it is not
needed by `H-2026-0010` as now specified (`LT01TRUU` against `LT11TRUU`).

**An open point this exposes.** Rule 1 resolves Bloomberg names against the
coverage tables. As written, a real Bloomberg ticker that is in no coverage
table yet, which is exactly `LT08TRUU`'s case, would be rejected, which
contradicts "a name that is real but not yet pulled still validates". Cowork
has not checked whether the coverage tables already hold names that were
confirmed but not pulled. The implementing task must say how a real Bloomberg
name that was never queried gets in (for example an owner-confirmed list).
