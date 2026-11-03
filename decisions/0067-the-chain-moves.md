# 0067 -- The chain moves without the owner

**Status:** RULED by the owner, 2026-10-23, in chat: "I want the chain to move without me and only stop if an owner decision is blocking the chain from moving." Recorded by Cowork. Amends `decisions/0062` item 8 (the list that reserved "writing a new task into HANDOFF.md") and `decisions/0064`. Nothing else in `0062`, `0064` or `0065` changes.

**Owner ruling, 2026-10-23:** Cowork may write the next task of a roadmap chain into `HANDOFF.md` and release it, without asking, under the rules below. It stops, and tells the owner, only when an owner decision blocks the chain.

## What a chain is

A sequence of tasks that the board's milestones name (today, M5: the phase-2 solver, tasks 70 then 71), where each next task's specification already sits in a **decided** record under `decisions/` (not `decisions/proposed/`) or in the roadmap text of `HANDOFF.md`.

## Rules

1. **When.** Cowork writes the next task only after the previous task's receipt is in `## Done` as done (not STOPPED) and its check passed. It writes one task ahead at most: never a queue of unwritten-then-released tasks.
2. **How.** The task follows the format of the existing tasks (numbered, steps, the command and expected result per step, stop conditions, revision-note slot). It cites the decision that specifies it. It is released with `Nightly-release: <id> @<time> by=cowork push=no`, Sonnet, and carries the line "Written and released by Cowork under decisions/0067."
3. **Stop and notify the owner** (options, a recommendation, the exact files to open; push and email as in `0062` item 10) when any of these is true, and do nothing else on that thread:
   - the next task would touch `params/`, `SUBSTRATE.md` or `vetoes/` (Cowork may prepare the patch draft for review; the owner releases it);
   - its specification is not in a decided record, or needs a judgement that `decisions/` or `OWNER-QUEUE.md` reserve to the owner (an unruled item, an ambiguity that changes a result);
   - a golden would move, a hypothesis's signal, direction, scope or data would change, a new data pull is needed, or an audit run is needed (audits keep the owner's Thu-Sat rule);
   - the previous task stopped on the same mechanical cause twice, or hit a budget or turn cap;
   - the next step would need a push, or any action outside the lane-2 rules of `0064`.
4. **Push is unchanged.** Chain tasks are `push=no`. A push still needs a task that says to push, released as the owner did task 60; this decision does not change that.
5. **Reporting.** Each review records which chain task it wrote or released, or which stop condition held the chain, and the board shows the task's card and the chain's next step.
6. **Revocation.** The owner can end this at any time by a line in chat; Cowork then reverts to preparing tasks for release.
