#!/usr/bin/env bash
# One command to land the v0.4 amendment and the governance check.
#
# This exists only because the agent's shell on this machine lost its mount
# mid-session and cannot run git. Everything below was written and tested in
# the cloud container; nothing here needs a decision from you.
#
#     bash scripts/land_v04.sh
#
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# The transfer bridge refuses to write a file named Makefile, so build.mk is
# the shipped copy.
cp build.mk Makefile

# Hooks are only hooks if git can execute them.
chmod +x .githooks/commit-msg
git config core.hooksPath .githooks

echo "--- commit 1: the governance check (touches no owner-only path) ---"
git add scripts/check_governance.py tests/test_governance.py \
        .githooks/commit-msg decisions/0021-governance-check.md \
        build.mk Makefile scripts/land_v04.sh
git update-index --chmod=+x .githooks/commit-msg
git commit -F - <<'MSG'
governance: enforce SUBSTRATE section 2 at commit time

v0.4 lets an agent transcribe an owner-approved change to SUBSTRATE.md,
params/*.yaml or vetoes/. That removed the guarantee that used to be
physical -- the agent could not type into those files -- so the constraint
now has to be enforced by something other than the owner's fingers.

A commit-msg hook refuses any commit that changes an owner-only path
without citing a decisions/ record that exists. Fails closed when
decisions/ cannot be read. No bypass argument, and a test asserts it.
`make governance` also checks that the hook is actually installed, because
an uninstalled hook and an obeyed rule look identical from outside.

Enforcement starts at this commit, found by asking git when
.githooks/commit-msg first appeared, so existing history is not judged
retroactively.

See decisions/0021.
MSG

echo
echo "--- commit 2: SUBSTRATE v0.4, under the rule just installed ---"
git add -A
git commit -F - <<'MSG'
substrate: v0.4 (decisions/0020)

The eleven amendments the owner approved, listed in decisions/0100:
active_drawdown as an eleventh veto, hypothesis_transitions in the results
schema, cost ceilings and named model tiers, the single signal_lab package,
turnover as traded notional, the coverage-table columns replacing
index_etf_map.csv, a weekly proposer, period_end rather than real_date,
a time-varying characteristic map with per-cell provenance, the lookahead
veto extended to estimated parameters, and a conviction-dependent
tracking-error coefficient.

Transcribed under section 2 as amended in this same version: the owner
decided and recorded it, the agent held the pen. Review the diff.
MSG

echo
echo "--- make check ---"
make check
