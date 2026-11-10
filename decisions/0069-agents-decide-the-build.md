# 0069 -- Agents decide the build; the owner keeps the ruler and the purpose

**Status:** RULED by the owner, 2026-11-10, in chat. Drafted and recorded by Cowork at his request (08:08 ET: "I want the agents to make decisions and only leave to me things that are really crucial, like decisions that would alter the purpose of the lab"). It amends `decisions/0062` item 8, `0064` (release), `0065` items 4 and 6 (push, release) and `0067` rules 1 to 4. Items 1 to 5 and 7 to 11 are in force from the ruling. Item 6 (the pins) waits for SUBSTRATE v0.14 (HANDOFF task 87), because §2 as it stands forbids it.

**Owner ruling, 2026-11-10** (chat). 08:14 ET, on Cowork's three questions: (1) the reserved list of item 2: "reserve list sounds good"; (2) delegated rulings take effect "immediately", with a weekly digest and no waiting period; (3) agents may push fast-forward after a passing check and transcribe plumbing pins: "yes". 08:20 ET, on this record as drafted, its SUBSTRATE wording and its four open points: "i am ok with all your proposals and Friday weekly digest sounds good". Cowork reads that as: (a) the delegation lapses when the search opens and he re-rules; (b) three tasks ahead; (c) the digest comes on Friday; (d) a hypothesis's scope and grouping are delegated (only its signal and direction are reserved), since that is what the draft proposed. Point (d) was put to him as a question, so it is named in the first digest for him to strike if the reading is wrong. Recorded by Cowork. The text below is the draft he approved, with the open points closed and one clerical correction (the SUBSTRATE bullet is the second "MAY NOT" bullet, not the third).

## What was measured

Read on 2026-11-10 from `results/audit/_nightly/*/status.txt`, `ran-stamps.txt`, `gate.log` and the review docs.

- Worker time from 2026-10-23 16:17 (the poll's first day) to 2026-11-10 08:00: 13,830 s in the 20 runs summed, about 3.8 hours in 17.6 days, under 1% of the clock.
- From 2026-10-29 to 2026-11-09: 6 runs, 1,634 s (27 minutes) in 12 days. A task is 5 to 30 minutes and $0.25 to $1.40. Month spend $3.61 of the $100 cap.
- The idle gaps (10-29 to 11-03, 11-05 to 11-07, 11-07 to 11-09) each ended on a chat ruling by the owner. The rulings were build choices: which option of `0059` D/E, what the transfer measure is for a rule with several views, the SUBSTRATE wording of an already-decided `0060`.
- Only the 05:30 review may write the next chain task (the 16:30 prompt forbids it), one task ahead, so the chain can move one link a day at best.

The 15-minute poll is not the constraint. The owner's turnaround is, because `0067` item 3 sends him every "ambiguity that changes a result", and before the search opens nearly every build choice is one.

## Why this is safe before the search opens, and not after

The reservations in SUBSTRATE §2 exist so that no agent can move the ruler to make a run pass. That risk needs real-data outcomes to fork on. Until the first real-data audit (board milestone M8) there are none: every number the build produces comes from synthetic or planted panels, where the truth is known and a wrong build choice shows up as a planted signal not recovered (M6 is that test). So the delegation below is bounded in time by M8.

## Decision

1. **The window.** From the owner's approval until the task that opens the search (the first real-data audit, M8) is released. That release is the owner's. At that point the owner rules what of this record persists; until he does, items 3 to 5 lapse and `0067` item 3 applies again.

2. **Reserved to the owner.** An agent prepares the decision (options, a recommendation, the files to open) and does nothing else on that thread:
   - SUBSTRATE §1 to §3: the purpose, the two bars, `target_net_ir`;
   - the holdout: its date, its lock, its unlock;
   - the universe's membership and the benchmark;
   - the cost model's levels (`params/costs.yaml`) and every constraint level in `params/constraints.yaml`;
   - every veto and its threshold (`vetoes/`, `params/vetoes.yaml`), and the multiple-testing gate;
   - a registered hypothesis's signal or direction;
   - any new data pull, and the vendor-data rule;
   - the spend caps (`scripts/nightly/config.sh`, `params/agents.yaml` budgets);
   - the planted-signal pilot's acceptance thresholds (`0059`, owner 2026-10-12: pilot first, then he rules);
   - opening the search (item 1), and anything this record does not clearly delegate that would change what a verdict means once the search is open.

3. **Everything else is delegated.** A build question outside item 2 is ruled by the agent that meets it, at once, and the work goes on. The ruling is a short record: a numbered file in `decisions/` or an addendum to the record it interprets, with a paragraph that starts `**Delegated ruling, <date>, <agent>**` and says the question, the options, the choice, its basis (a cited paper resolvable under SUBSTRATE §7's reference rule, an existing decision, or the argument from first principles), which numbers it can move, and what would reverse it. No basis, no ruling: it goes to the owner.

4. **A second agent stands where the owner stood.** A delegated ruling that touches a number-making path (`src/`, a golden, a store) is read, with its diff, by a reviewer that did not make it: a fresh session, Opus or stronger. It checks the basis, the reserved list and the tests. If it agrees, the ruling stands. If it does not and one round does not settle it, that thread stops and goes to the owner with both positions; independent work continues. The reviewer's line goes under the ruling.

5. **Receipts.** "Choices the text does not settle" in a receipt are ruled by the review under items 3 and 4, not listed for the owner, unless one falls in item 2.

6. **Plumbing pins.** Three things in `params/` may be transcribed by an agent, citing the record that decided the build and after `make check-full` passes on the tree that carries them: `data.yaml`'s `characteristics.store_id`, its `label_map` pin, and the `params_version` bump in the seven files that goes with either. The pin may name only a store or map built by a task whose specification is a decided or delegated record. Every other key in `params/` stays as SUBSTRATE §2 has it.

7. **The chain** (replaces `0067` rules 1 and 2). A task may be as large as a milestone step that one check can gate. Cowork may write up to three tasks ahead where they do not depend on each other's results, and releases them in order. Either review slot, and any linked Cowork session, may write and release. The model is named per task: Sonnet for building, Opus for specifications and for item 4.

8. **Push** (replaces `0067` rule 4). A chain task may say `git push origin main` and be released `push=yes by=cowork` when its check passed: fast-forward only, never forced, never another branch. A rejected push stops the chain and is reported (`CLAUDE.md` unchanged: a push still needs a task that says so).

9. **What still stops the chain** (replaces `0067` item 3): anything in item 2; a new data pull; an unresolved disagreement under item 4; the same mechanical failure twice for one task; a budget or turn stop. A golden that moves is no longer a stop by itself: it needs a delegated ruling that says why it moved, and the reviewer's agreement. Audits stay on the nightly worker and on Thursday to Saturday nights; an audit on planted or synthetic data may be released without asking.

10. **The weekly digest.** Every Friday Cowork writes one Project doc and one email: every delegated ruling of the week in one line each with its record's path, the reviewer splits waiting on the owner, the reserved decisions with a recommendation, and the roadmap position. The owner strikes a ruling by a line in chat; Cowork records the strike and writes the task that reverses it.

11. **What does not change.** The holdout lock; the vendor-data rule; `check-scoped` and `check-full` as the definition of done; hypothesis pre-registration and the append-only store; one unattended run at a time; one thread for recorded numbers; no reset, rebase or amend; the protected plumbing paths of `0065` item 3; the caps.

## SUBSTRATE §2 wording (approved by the owner 2026-11-10; v0.14, HANDOFF task 87)

Add to "Agents MAY":

> - Until the search opens (§16), rule a build question that `decisions/0069` item 2 does not reserve to the owner, by a record under `decisions/` that states its basis, reviewed by a second agent (`decisions/0069` items 3 and 4).
> - Transcribe the exposure store's id, the label map's pin and the `params_version` that goes with them, citing the record that decided the build, after the full check passes (`decisions/0069` item 6).

Change the first sentence of the "MAY NOT" bullet that begins **Originate** to:

> - **Originate** a change to `SUBSTRATE.md`, to anything under `vetoes/`, or to `params/*.yaml` beyond the pins of `decisions/0069` item 6.

## What has to change to make it real (status in HANDOFF tasks 86 and 87 and their receipts)

- SUBSTRATE v0.14 transcribed by Cowork; the owner reads the diff.
- `HANDOFF.md`'s contract paragraphs on `0062`, `0064` and `0067`.
- The two review scheduled tasks: the chain step in both slots, items 3 to 5 and 9 in place of the "right-hand column" rule for unreserved questions, the reviewer's model.
- A weekly digest scheduled task.
- **Not verified:** whether the commit hook, `make governance` or the exec server's hard-coded exclusion of `params/` lets a pin commit through. `scripts/exec_server/` is protected, so if it must change, that is the owner's or an interactive Claude Code session's. Until then a pin goes as today: a patch the owner releases.

## What it unblocks (Cowork's reading)

- M6: what the planted-signal pilot task holds (the thresholds stay the owner's).
- The `0068` loader and measured-duration tasks, and the `huber6-v6` pin after them.
- OWNER-QUEUE L41 (a rule about labels: delegated). L42 is how one hypothesis's groups are formed; it is not that hypothesis's signal or direction, so it would be delegated and named in the first digest. Say if scope and grouping belong in item 2.
- M7's design questions that the `0059` addenda left open (how `build_weight_rule` builds the universe and the cost model, where the E reports go), within the levels item 2 reserves.

## Risks, named

- A plausible, wrong build choice now lands without the owner seeing it first. The reviewer shares the author's blind spots more than the owner does. What limits it: the basis rule, the record, the pilot (a pipeline that cannot recover a planted signal fails in the open), the digest, and that every ruling is one commit to revert.
- The boundary of item 2 will be tested by cases this text did not foresee. The rule for those is the last line of item 2: to the owner.
- Cost rises: more worker time and an Opus review per ruling. Not estimated; the caps bound it.

## The open points, closed (owner, 2026-11-10)

- (a) Item 1: the delegation lapses when the search opens, and he re-rules.
- (b) Item 7: three tasks ahead.
- (c) Item 10: Friday.
- (d) A hypothesis's scope and grouping are delegated; Cowork's reading of "ok with all your proposals", named in the first digest.

## How to undo it

One line in chat. Cowork then applies `0067` item 3 as it stood, and delegated rulings already made stand unless struck.
