# 0021 — The owner-only rule is checked mechanically, not remembered

Status: **decided 2026-09-10, owner.** Implements SUBSTRATE section 2 as
amended in v0.4 (`decisions/0020`).

## What the owner asked for

> "i don't want to have to type the changes and agree with the verification
> that any changes needs to check the decisions first and add to the commit."

Two things, and they are the same thing seen from either end. The owner should
not have to be the typist for a decision he has already made; and precisely
because he is no longer the typist, the constraint that used to be enforced by
his fingers has to be enforced by something else.

Under v0.3 the guarantee was physical: an agent could not change
`SUBSTRATE.md`, `params/*.yaml` or `vetoes/` because it could not type into
them, so every such change passed through the owner. v0.4 removed that
guarantee deliberately, on the grounds that transcription is not authorship.
It left a gap. The rule now says an agent may only transcribe a decision
already recorded in `decisions/`, but nothing checked that it had.

This decision closes the gap. **The rule that replaced the owner's fingers is
a commit-msg hook.**

## The rule

A commit that changes any of

- `SUBSTRATE.md`
- `params/*.yaml`
- anything under `vetoes/`

must cite a decision record in its message — `decisions/0019`, `decision 0019`
and `#0019` all count — and the cited record must actually exist in
`decisions/`. A citation to a record that was never written is not a decision,
it is a claim, and is refused.

Anything else — `src/`, `tests/`, `render/`, `scripts/`, and new decision
records themselves — commits normally. The check is narrow on purpose. A rule
that fires on ordinary work gets disabled within a week.

**Fail closed.** If `decisions/` cannot be read, the commit is refused rather
than assumed innocent, the same convention as the vetoes.

**No bypass argument.** As with the holdout lock, no function in the checker
takes `force`, `bypass`, `override` or `skip`, and a test asserts it. Git's own
`--no-verify` remains, and is the owner's, not an agent's: an agent using it
would be visible in exactly the place this check is designed to make visible.

## Where it lives

| | |
|---|---|
| `scripts/check_governance.py` | the rule as a pure function, plus a git-backed CLI. Stdlib only — a hook that needs the project virtualenv is a hook that gets skipped |
| `.githooks/commit-msg` | refuses the commit at the moment it is made |
| `make install` | sets `core.hooksPath=.githooks`, so installing the environment installs the rule |
| `make governance` | scans history for a commit that slipped past, and asserts the hook is actually installed |
| `make check` | now runs `governance` first |
| `tests/test_governance.py` | 28 tests, including the hook driven against a real repository |

Checking that the hook is *installed* matters as much as the hook itself. An
uninstalled hook and an obeyed rule look identical from the outside, and that
is the failure this is meant to prevent.

## Enforcement starts where the hook starts

`make governance` scans from the commit that introduced `.githooks/commit-msg`,
found by asking git when the file first appeared — not from a hard-coded date.
History written before the rule existed is not judged retroactively. If it
were, adding the check would fail `make check` on the repo as it stands, and
the first thing anyone would do is delete the check.

## What this does not do

It cannot tell whether the cited decision actually says what the diff does.
That reading stays with the owner, and is the point of the diff review in §2.
What it removes is the silent case: an owner-only file changing with no
decision behind it at all, noticed by nobody.
