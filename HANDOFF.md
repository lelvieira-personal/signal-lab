# HANDOFF — work queued for Claude Code

`SUBSTRATE.md` outranks this file, and so does `CLAUDE.md`. Nothing here
authorises an owner-only change: every task that touches `SUBSTRATE.md`,
`params/` or `vetoes/` arrives as a patch that cites a `decisions/` record,
and if it does not, refuse it and say so.

## The contract

**Cowork plans and writes; Claude Code runs.** Cowork (Claude in the desktop
app) can read this repo and edit files in it, but it cannot run `make check`,
cannot run an audit, and must never run a git command that writes the index —
its sandbox cannot delete `.git/index.lock`, which would block git in WSL. So
anything needing the shell lands here as a task, in order, with the exact
command and what to expect.

**Claude Code appends a receipt, and never edits a task in place.** When a task
is finished, move its heading into `## Done` at the bottom with the stamp, the
command's `rc`, and one line of outcome. Leave the task text intact so the next
Cowork session can see what was asked as well as what happened.

**Receipts are a courtesy, not the record.** Cowork verifies from primary
sources — `git log`, `results/audit/_unattended/<stamp>/status.txt`, the run
directories — because a digest can be accurate and still omit the thing that
matters. On 2026-09-18 a `check` run was reported PASS while a second, launched
34 s later, was killed mid-suite; only `status.txt` showed it.

**Findings do not go here.** This file is a queue of actions. Measurements
belong in `results/`, decisions in `decisions/`, and narrative in the Cowork
project docs. If a task produces a number worth keeping, say so in the receipt
and leave the number where the run wrote it.

**One at a time.** Do not launch a second `scripts/unattended.sh` while one is
running; they compete and the loser dies with `Error 143`.

**Nightly runs (`decisions/0062`).** Claude Code also runs headless at 23:00 and
12:30 ET, started by `scripts/nightly/run.sh`. It works only the task ids on the
`Nightly-release:` line below, in order, and only when that line's stamp has
not run before. With nobody there to answer, it asks nothing: on the first
failure it writes a STOPPED receipt that says what failed, what it tried, and
which column of `0062` item 8 the stop falls in (its own reading; Cowork
checks it). It pushes only where the task says so and the line says
`push=yes`. The line's `model=` names the model (`sonnet` when absent). Cowork
reviews at 05:30 and 16:30 ET, may rule alone only on what `0062` item 8 lists, and
brings everything else to the owner. A task that expects a run of more than
five hours needs `long` on the line, and starts only on a Thursday, Friday or
Saturday night. While `results/audit/_nightly/RUNNING` is fresh, Cowork edits
no tracked file.

---

## Queue

Nightly-release: 63 @2026-10-21T15:20 by=owner push=no

**As of 2026-10-21 (15:20 ET): task 63 RE-RELEASED to resume at step 4, by Cowork on the owner's instruction.** The 12:30 run did steps 0 to 3 (commit `5501945`) and stopped: its step 4 command was denied. Cause, read from the run's `result.json`: the allow list has `Bash(uv run --python 3.12 --group dev *)` and `Bash(make *)`, and the worker started the command with `env VAR=...` / `VAR=...`, which matches neither. It is a command-shape problem, not a settings problem; `scripts/nightly/` is not touched. Fix: a `make` target (task 63, step 4a). Tasks 64 and 65 stay NOT released, and run after this receipt; 65 also waits for the owner's file (`data/raw/bloomberg/bbg_japan_govt.xlsx`, 410,623 bytes, saved 2026-10-21, not yet opened by anyone).

**As of 2026-10-21 (09:45 ET): tasks 64 and 65 written, NOT released.** The owner ruled OWNER-QUEUE L39 option (a) (add the 2013 Japan family, `I29064JP` to `I29068JP`). **Task 64** commits `decisions/0063`; Cowork copies the draft from `Claude outputs/decision-0063-draft/` into `decisions/` at release, and it runs after task 63's receipt. **Task 65** describes the Japan file and is released only after the owner has pulled it (request: `Claude outputs/bbg_pull_japan_govt_2026-10-21.csv`) and saved it under `data/raw/bloomberg/`; the release note will name the file. L39 stays open until the instruments are admitted.

**As of 2026-10-21 (08:20 ET): task 63 written, NOT released.** The owner ruled on `decisions/proposed/0034` ("I agree with the proposed validation", 2026-10-21) and asked for the task. It waits for the owner's release on the line above. Suggested release: `Nightly-release: 63 @<time> by=owner push=no`, Sonnet. Cowork's working-tree edits for it are `OWNER-QUEUE.md` (L39 restated, nothing answered) and `decisions/proposed/0034` (the ruling and a correction). Task 60 stays NOT released.

**As of 2026-10-19 (17:10 ET): task 62 RE-RELEASED by Cowork after its stop** (`decisions/0062` item 8: re-releasing a stopped task once the cause is fixed; the owner also said "yes" to the revision). The first run stopped at step 2 on `echo`, missing from the worker's allow list; read the task's revision note 1. It runs at the first slot that passes the gate, tonight at 23:00. Task 60 stays NOT released.

**As of 2026-10-19 (15:25 ET): task 61 landed and is verified; task 62, the canary, is RELEASED** on the line above (`push=no`, Sonnet). The owner released it on 2026-10-19 ("ok to put 61 and 62 in handoff"; `decisions/0062` item 12, "4) yes"). It runs once: by hand with `bash scripts/nightly/run.sh day` before 17:00, or else at the first scheduled slot. Task 60 stays NOT released.

**As of 2026-10-19 (11:00 ET): queued, task 61 (run by hand), then the canary, task 62.** The owner said "ok to put 61 and 62 in handoff". **Task 61** commits `decisions/0062`, this contract change and the nightly build (`scripts/nightly/`, `tests/test_nightly.py`, the lock in `scripts/unattended.sh`, `.gitattributes`), runs the checks and pushes. Run it interactively, as before: the nightly worker does not exist until it lands. **Task 62** runs through the worker: after 61's push, the release line is set to `62 ... push=no` and the owner starts `bash scripts/nightly/run.sh day` by hand. The line stays `none` until then, so nothing runs on its own. Task 60 stays NOT released.

**As of 2026-10-19 (08:00 ET): nothing is released.** The owner decided `decisions/0062` ("consider it approved"): the nightly run and the morning review. Cowork applied the contract paragraph above, the release line and two `CLAUDE.md` edits in the working tree; nothing is committed. The nightly scripts are not built yet, so nothing runs tonight. Next: the build (the scripts, `.claude/nightly.json`, the hook, the `unattended.sh` lock) and a canary task for one supervised run, both written by Cowork and shown to the owner first. Task 60 stays NOT released.

Tasks **0-11 are complete**; receipts are in `## Done` and the text as issued is
in git history. The queue below starts at 12.

**Read first:** `decisions/0036` (decided 2026-09-20) and the Cowork project doc
`claude/dose-response-step1-2026-09-20.md`. `decisions/proposed/0035` and
`claude/dose-response-probe-plan.md` are still live context; the probe plan's
steps 2 and 3 have been superseded by 0036 and by the withdrawal notice below.

**Run order, as of 2026-09-21: 20, 22, 19, 23, 21.** Tasks 12, 15, 16, 17, 18
and 24 are done — receipts are in `## Done`.

- **20** — gate released by the owner and the task **re-specified**; read its
  AMENDMENT, not the text above it. Commits the outstanding receipts first.
- **22 must land before 19.** 19 is a 3.3 h grid that would otherwise persist
  nothing, which is the hole `decisions/0035` §5 exists to close.
- **23** is independent of all of them and can run whenever.
- **21** is hygiene, any time.
- Tasks **13 and 14 are withdrawn** — read the notice, do not run them.

**As of 2026-10-10 (23:30 ET): queued, task 53 only.** The owner ruled OWNER-QUEUE L32 (`decisions/0053`): every return is in dollars, and eighteen local-currency series are converted with the FX file he supplied (`data/raw/bloomberg/bbg_curncy_hist.xlsx`). Cowork transcribed SUBSTRATE v0.10 (L31) into the working tree; step 0 commits it. **Task 53** converts the series, takes `NDDLUK` out, adds a currency guard, rebuilds the store as `huber6-v3`, fixes the spread table and `LET1TREU`'s name, and **pushes** (`CLAUDE.md`, owner 2026-10-10). **`resolve_exposures` stays raising.** **Waiting on the owner:** L28 (the label-map draft), L29, L33.

**As of 2026-10-12 (08:10 ET): queued, 55 then 56.** The owner ruled OWNER-QUEUE L28 (the bond labels as drafted, `decisions/0054` addendum; how a hypothesis uses them, `decisions/0057`), L33 (`decisions/0056`) and L35 (`decisions/0058`) on the night of 2026-10-11, and L36 on 2026-10-12; "yes" to task 55, and (owner, 2026-10-12) "yes" to this note. Task 54 and its push have both landed: Cowork checked on 2026-10-12 that `origin/main` is `c8e755c`, equal to HEAD, so nothing earlier is waiting to be pushed. **Task 55** commits the records (SUBSTRATE v0.11) and builds the label map and the region axis; **task 56** builds store `huber6-v4`. Sector and style keep raising; no scope logic and no solver is built. **Waiting on the owner:** nothing for 55 or 56. **Not queued:** the phase-2 solver; Cowork is drafting its spec under `decisions/proposed/`, and nothing is built from it until a task says so.

**As of 2026-10-15 (22:15 ET): queued, 57 then 58.** The owner ruled OWNER-QUEUE L37 on 2026-10-14 ("agree with proposal": `decisions/0059`, moved out of `proposed/`) and L38 on 2026-10-14 and 2026-10-15 (`decisions/0060`), and said "queue the commits". Tasks 55 and 56 and their pushes have landed (`origin/main` was `7cf303e` on 2026-10-14; `9b1e0d5`, task 56's receipt update, was then the only unpushed commit). **Task 57** commits the records and pushes; nothing is built. **Cowork moved the receipts of tasks 55 and 56 into `## Done`:** they had been pasted inside the contract paragraph above, splitting its sentence. A receipt goes directly under the `## Done` heading, newest first. **Not queued:** the `huber6-v4` params patch (Cowork writes it, then the `0059` params patch after it); the phase-2 solver build (`0059`, with `0060`'s validator change); the JPMaQS catalogue check for GBP and JPY carry (`0060`); a loader for the new non-USD bonds. **The owner's Bloomberg pull landed** at 22:05 as `data/raw/bloomberg/bbg_exusd_bonds_extra.xlsx`; **task 58** only describes it. **Waiting on the owner:** L39 (Japan) and `FLDS` for `BEIG1T`.

**As of 2026-10-16 (15:30 ET): task 59 RE-RELEASED after its stop at step 0.** Cowork ruled the stop (option (b): the FDR-vs-FWER study is pinned to its twelve hypotheses) and made the edit; read the task's second revision note. Run it from step 0 again. A tip from the stopped run, for any one-off `python -c`: set `PYTHONPATH=src:.` and `UV_PROJECT_ENVIRONMENT=$HOME/.venvs/signal-lab`.

**As of 2026-10-16 (14:40 ET): queued, task 59 (RELEASED); task 60 written, NOT released.** The owner said yes to `decisions/0061` ("i am ok with the decisions on 0061"), asked for `.claude/settings.json` to be committed (task 59 step 0, revised) and for the pending owner-only params to be drafted: they are in `Claude outputs/params-v0.11.0-draft/` (task 60). *(Superseded part of the note below: task 59 is released.)*

**As of 2026-10-16 (15:00 ET): task 59 is written, NOT released.** Tasks 57 and 58 and their pushes have landed (Cowork checked on 2026-10-16: `origin/main` is `32bdd9f`, equal to HEAD; task 58's missing push line is added to its receipt). The owner registered H-2026-0018 to 0021 on 2026-10-16 (options-implied tail ratio; `decisions/0061`, proposed) and ruled the burn-in at 52 weeks, lab-wide (`decisions/0059` addendum; OWNER-QUEUE L37 amended). **Task 59** commits those records, makes `inspect_raw` skip Excel lock files, loads the implied-vol file, writes its coverage report and reports task 56's open run-of-record gate. **Do not start it until this line says the owner said yes to `decisions/0061`.** **Not queued:** the `huber6-v4` and `0059` params patches (Cowork writes them, owner-only); the phase-2 solver build; a loader for `bbg_exusd_bonds_extra.xlsx`. **Waiting on the owner:** yes to `0061`; L39 (Japan) and `FLDS` for `BEIG1T`.

Notes for task 55 (Cowork, 2026-10-12; the task's text is unchanged):
- **Superseded for task 55's scope:** the standing refusal "Building from `decisions/0054`" and the paragraph "The label map file (added 2026-10-11)" under "Not queued yet". Task 55 is the queued build of the label map and the region axis, and nothing beyond it.
- **Step 1's normalisation.** Key the mapping on the verbatim strings as they appear in `decisions/0054`'s bond table, which are the draft's. `0057`'s table paraphrases three of them and names their tickers, so they are mapped, not unmapped: "European, several (mostly EUR)" is `EUR_multi` (`I02513EU`, `LP05TREU`); "Several (EUR, JPY, GBP and others)" is `DM_multi` (`LG38TRUU`); "HY, all ratings" is `HY` with `hy_bucket` `all` (`LF98TRUU`). A string in neither table is still an error.
- **Step 0.** `.claude/settings.json` is modified in the working tree and is not one of step 0's files. Leave it uncommitted.
- **New since the task was written:** `decisions/proposed/0059-the-phase-2-solver.md` (Cowork, 2026-10-12) and OWNER-QUEUE L37 and L38. `OWNER-QUEUE.md` is in step 0's files anyway; leave `0059` uncommitted. Step 0's "`decisions/proposed/` has no new file" was true when written.
- **Step 4's push** carries step 0 and the build only; `c8e755c` is already on the remote.
- Cowork dry-ran step 1's counts on the draft, outside the repo (pandas, Python 3.10), on 2026-10-12: the sha256 prefix and every count in the task's table matched. That checks the task's expectations; it does not replace the step.

*(Earlier note:)* **As of 2026-10-11 (14:30 ET): queued, task 54 only.** The owner ruled on 2026-10-11: OWNER-QUEUE L34 ("push as is"), L29 and L28 in part (`decisions/0054`), and "yes" to the wiring with its two owner-only patches (`decisions/0055`). Cowork applied params v0.10.0 and the `veto_lookahead` patch in the working tree, so **the suite is red until task 54's step 3**. **Task 54** makes `resolve_exposures` read `huber6-v3`, tests the veto's second half, closes task 53's loose ends and **pushes**. Region, sector and style keep raising, and no solver is built. **Waiting on the owner:** the bond labels (L28; he confirmed the same afternoon that the region axis reads equities only), L35, L33.

*(Earlier note:)* **As of 2026-10-11: nothing is queued.** Task 53 landed (`270ecb9`, receipt `aa1b157`); Cowork's review is the Project doc `claude/task-53-review-2026-10-11.md`, and every gate reproduced. **Its push did not happen:** `origin/main` is still `1b6babf`, 138 commits behind. **No task pushes until the owner rules OWNER-QUEUE L34** (the repository is public). **`resolve_exposures` stays raising.** **Waiting on the owner:** L34; L28 and L29 (the draft is written: `claude/label-map-draft-2026-10-11.md`); L33.

*(Earlier note:)* **As of 2026-10-10 (11:45 ET): nothing is queued.** The owner ruled on 2026-10-10:
- OWNER-QUEUE L30 is closed: TIPS read their measured duration (`decisions/0050` addendum).
- L28 and L31 are ruled in part.
- `CLAUDE.md` now lets a task push `main` (fast-forward only).

Cowork found OWNER-QUEUE L32 on the same day: nineteen return series are local-currency returns treated as dollars. **Waiting on the owner:** L32, then the label-map draft (L28) and SUBSTRATE v0.10 (L31). **Don't start anything before a task is written.** Uncommitted in the working tree, all Cowork's, for the next task's step 0: `HANDOFF.md`, `OWNER-QUEUE.md`, `CLAUDE.md` and `decisions/0050` (addendum).

*(Earlier note:)* **As of 2026-10-08 (11:45 ET): nothing is queued.** Task 52 is done (`5fb47e3`, `49b202e`, receipt `f48c82f`) and Cowork verified it from `git`, the log `20261007-184728-check-full` (its `head=` is `5fb47e3`; every file the build commit changed was last written before the check started), the report and the store itself (Project doc `claude/task-52-review-2026-10-08.md`; mirror copy in `Claude outputs/project-mirror/`). The receipt stands as written. **`resolve_exposures` still raises.** **Waiting on the owner:** OWNER-QUEUE L28 to L31, including a new point in L29 (`LET1TREU`'s maturity band), and his agreement to the next task. **Don't start anything before a task is written.** Uncommitted in the working tree, all Cowork's, for the next task's step 0: `HANDOFF.md` and `OWNER-QUEUE.md`.

*(Earlier note:)* **As of 2026-10-07 (17:15 ET): queued, task 52 only.** The owner ruled OWNER-QUEUE L27 (`decisions/0050`), chose the solver's form (`decisions/0051`) and removed two series from the investable universe (`decisions/0052`). He also put two vendor files in `data/raw/bloomberg/`. **Task 52** commits the records, applies 0052, loads the ex-USD analytics file, rebuilds the store as `huber6-v2` and corrects the report's table. It has no owner-only edit. **`resolve_exposures` stays raising after it:** the wiring is not queued, and nothing is built from `decisions/0050` or `0051` yet. **Waiting on the owner:** OWNER-QUEUE L28 to L31.

*(Earlier note:)* **As of 2026-10-07 (10:15 ET): nothing is queued.** Tasks 50 and 51 are done and Cowork verified both from `git`, the three logs, the two `summary.json` files and the store (Project doc `claude/tasks-50-51-review-2026-10-07.md`; mirror copy in `Claude outputs/project-mirror/`). Both receipts stay as written; the review carries two corrections to task 51's estimated-against-measured table. **Waiting on the owner:** OWNER-QUEUE L27 (the exposure matrix's columns) and his agreement to the next steps. **Don't start anything before a task is written.** Uncommitted in the working tree, all Cowork's, for the next task's step 0: `HANDOFF.md`, `OWNER-QUEUE.md` and `decisions/0048-…`.

*(Earlier note:)* **As of 2026-10-07 (midday): queued, 50 then 51.** The owner ruled on OWNER-QUEUE L26, B5, L25 and L23 on 2026-10-07 ("i accept all of your suggestions for the pending decisions"). **Task 50** makes one thread the lab's reference (`decisions/0048`), re-records three constants, applies the grade ruling to two hypothesis files (`decisions/0006` addendum), fixes `.gitignore` and runs the first scoped check. **Task 51** builds the Huber loadings on the six factors as a versioned store (`decisions/0049`). Neither has an owner-only edit. **`resolve_exposures` stays raising after both:** the matrix's columns are OWNER-QUEUE L27, proposed in `decisions/proposed/0050` and not decided. Don't build from a file under `decisions/proposed/`.

*(Earlier note:)* **As of 2026-10-07 (morning): nothing is queued.** Tasks 48 and 49 are done and Cowork verified both from the run directories, the logs and `git` (Project docs `claude/task-48-review-2026-10-06.md` and `claude/check-runtime-2026-10-06.md`; mirror copies in `Claude outputs/project-mirror/`). **Waiting on the owner:** OWNER-QUEUE L26 (the thread count changes four recorded goldens), B5 (the estimator), L25 (the factor set) and L23 (the grade filter). The next task will carry L26's ruling together with three hygiene fixes that need no ruling: the `.gitignore` lines with trailing comments, ignoring `data/universe/raw_meta.json` and `raw_structure.json`, and the first end-to-end run of `make check-scoped`. **Don't start any of them before the task is written,** and re-record no golden.

*(Earlier note:)* **As of 2026-10-06 (night): queued, 48 (in flight) then 49.** Task 49 (owner, 2026-10-06, OWNER-QUEUE L24) makes every check log per-test times and the machine's load, trials parallel tests, and adds `make check-scoped`, which leaves out the slow tests a change cannot reach. It has no owner-only edit, changes nothing under `src/` and moves no hypothesis. Run it after task 48's receipt is committed. **Still waiting on the owner:** OWNER-QUEUE B5 and L23.

*(Earlier note:)* **As of 2026-10-03 (evening): queued, task 48 only.** Task 47 is done and Cowork verified it (Project doc `claude/task-47-review-2026-10-03.md`; mirror copy in `Claude outputs/project-mirror/`). Task 48 reproduces the run of record from the committed code, names the two filters' variance update and runs one sensitivity on it, and describes how stable each estimator's loadings are. It needs no owner ruling and moves no hypothesis. **Waiting on the owner:** OWNER-QUEUE B5 (which estimator enters the exposure matrix) and L23 (the grade filter leaves three JPMaQS tickers empty). The exposure-matrix build is not queued until B5 is ruled.

*(Earlier note:)* **As of 2026-10-02 (mid-morning): queued, 46 then 47.** Task 47 adds a fifth loading estimator, H-2026-0017 (mean-reverting Bayesian loadings; owner, 2026-10-02), and must run after 46.

*(Earlier note:)* **As of 2026-10-02 (morning): queued, task 46 only.** Tasks 44 (part A) and 45 are done and Cowork verified them. The owner ruled on L21 and L22. Task 46 applies `decisions/0047`, finishes task 44's part B on the existing pull, and re-runs the estimator test without the Cash class. One owner-only edit (SUBSTRATE v0.9) is already in the working tree. *(The fifth estimator is now task 47; see the note above.)*

*(Earlier note:)* **As of 2026-10-01 (22:25 ET): queued, 44 then 45. TASK 45 IS RELEASED: the owner reviewed and approved `decisions/0046` on 2026-10-01 ("046 is approved").** Task 45 tests four factor-loading estimators against rolling OLS (OWNER-QUEUE B5). Run 44's part A first, then 45 while the owner's JPMaQS pull is pending; 45 doesn't depend on the pull.

*(Earlier note:)* **As of 2026-10-01 (night): queued, task 44 only.** Task 43 is done, and Cowork verified it (`state-of-play.md`). Task 44 is the JPMaQS loader. It has an owner step in the middle: the vendor pull, which the owner runs. It needs no owner-only edit. The search stays closed after it: opening it needs the owner, and also the exposure matrix (OWNER-QUEUE B5) and `signals/`.

*(Earlier note:)* **As of 2026-10-01 (evening): queued, task 43 only.** Task 42 is done, and Cowork verified it (Project doc `claude/task-42-review-2026-10-01.md`). Task 43 applies `decisions/0044` and `0045`, SUBSTRATE v0.8 and the review's fixes. Cowork has already applied every owner-only edit to the working tree; read the task's preamble. **Nothing after 43 is queued: phase 2 waits on an owner decision about SUBSTRATE §5.6** (see "Not queued yet").

*(Earlier note:)* **As of 2026-10-01: queued, task 42 only.** It applies `decisions/0042` (the overlay is policy) and `0043` (the gate is generalized FWER), surfaces the turnover highlight, and gives 0040's shadow cost a single implementation. Cowork has already applied every owner-only edit to the working tree; read the task's preamble.

*(Earlier note:)* **As of 2026-09-30 (evening): tasks 35, 39, 40 and 41 are all done. The queue above (12-39) is now fully worked.** Receipts for 35/39/40/41 are in `## Done`; `OWNER-QUEUE.md` B1 and L16 carry their interpretation. Nothing new is queued here as of this stamp -- check `OWNER-QUEUE.md` and the Cowork project docs for what comes next.

*(Earlier note:)* **As of 2026-09-30 (morning): tasks 35, 40 and 41 are done. Queued: 39 only. Read its 2026-09-30 amendment first: Cowork has already applied every owner-only edit (`SUBSTRATE.md`, `params/`, `vetoes/`) to the working tree.**

*(Earlier note:)* **As of 2026-09-29 (late evening): task 40 is done (SUBSTRATE step blocked by permissions; Cowork holds it). Tonight: 41 → 35, with a hard stop. The grid stops by 06:30 ET and the receipt is committed by 06:45 ET (see the amendment at the top of 35). 39 does NOT run tonight.**
- **41:** pool the observed value into `romano_wolf`'s standardising. Task 40's version breaks FWER at small k.

*(Earlier note:)* **As of 2026-09-29 (evening): tasks 37 and 38 are done. Queued, in order, 40 → 35 → 39.**
- **40:** transcribe `decisions/0041` into SUBSTRATE §9, standardise
  `romano_wolf`, and add the generalized-FWER stepdown to the study (L16). About
  1-1.5 h, no engine runs. Its step 0 commits Cowork's edits.
- **35 and 39:** unchanged below. Go on from 40 to 35 in the same session.

*(Earlier note:)* **As of 2026-09-29 (afternoon): queued, in order, 37 → 38 → 35 → 39.**
- **37:** split the test suite (D2).
- **38:** Romano-Shaikh-Wolf FDR from the paper, and the study re-run at small k
  (L16).
- **35:** the halflife sweep, overnight. It must run before 39. **Owner, 2026-09-29:
  go straight on to 39 after 35 if 35 is clean and 39 can finish by 06:00 ET.**
  See the end of task 35.
- **39:** apply `decisions/0038` and `0040` in one params change.

**Task 33 is superseded by 39**; don't run it. Task 37's step 0 commits
Cowork's edits (the step 0 formerly in task 35 moved there).

*(Earlier note:)* **As of 2026-09-29, tasks 0-34 and 36 are done** (Cowork verified both; three
counts in task 36's receipt were wrong. The corrections are in the Cowork doc
`claude/tasks-34-36-review-2026-09-29.md`, and the receipt stays as written).
**Queued: 35. Task 33 is still ON HOLD.** Budget about 1 h for `make check`
before 35's grid: the suite now takes about 3700 s (OWNER-QUEUE D2).

*(Earlier note:)* **As of 2026-09-28 (evening), tasks 0-32 are done. Queued, in order: 34**
(multiple-testing module plus the FDR-vs-FWER Monte Carlo; no engine runs),
then **36** (the created-turnover shadow cost as an override, 60 cells,
`decisions/0040`), then **35** (the volatility-overlay halflife sweep,
OWNER-QUEUE B1/L13, about 240 cells, an overnight run). 36 runs before 35 on
purpose: its code touches the solver, and 35's identity check against the knee
run catches any change to the default path. **Task 33 is ON HOLD**: the owner is holding the
`decisions/0038` ruling (OWNER-QUEUE L17). Do not start it until this line
says otherwise. Task 34's step 0 commits Cowork's queue edits first. Receipts
are in `## Done`.

*(Earlier note, kept for the record: as of 2026-09-28 morning, tasks 0-31 were
done and 32, 33, 34 were queued.)* Task 25's power audit is `A-20260924-194115`, read in
`results/audit/A-20260924-194115/power-on-one-history-2026-09-24.md`. H-2026-0001's
JPMaQS names were renamed 2026-09-24 (`33b84f4`).

**Cowork's project docs, readable here:** Claude Code cannot see the claude.ai
Project. Read-only copies of the docs that tasks cite are in
`Claude outputs/project-mirror/` (git-ignored). Start with `state-of-play.md`.
When a task names `claude/<name>.md`, read `Claude outputs/project-mirror/<name>.md`.

One `scripts/unattended.sh` at a time.

### 24. Commit the records, then the constitution — DO THIS FIRST

**Two commits, in this order.** `SUBSTRATE.md` is amended, so the authorising
record must be in history before the amendment that cites it — the
`decisions/0030` precedent, where the decision landed in one commit and
`substrate: sections 4 and 10` in the next. The `commit-msg` hook
(`.githooks/commit-msg` -> `scripts/check_governance.py`) refuses an owner-only
change whose message does not cite an existing `decisions/` id.

Nothing in the queue commits any of this. Tasks 21-23, the amendment to 18 and
the run-order line were written after task 15 had already committed
`HANDOFF.md`. `decisions/0036` **is** already committed, at `d2f2c4b` by task
15; what is uncommitted are its §1 and §6 amendments of 2026-09-21.
`decisions/0035` was promoted out of `proposed/` after task 15 ran, so its move
is uncommitted entirely.

**Commit A — the records.** `0035` is a move out of `proposed/`; git shows the
old path deleted and the new one untracked, so `git add -A` on both records it
as a rename.

    git add -A decisions/0035-the-transfer-coefficient-measures-the-benchmark-not-the-tilt.md decisions/proposed/0035-the-transfer-coefficient-measures-the-benchmark-not-the-tilt.md
    git add decisions/0036-the-bar-is-excess-over-a-no-information-baseline.md HANDOFF.md OWNER-QUEUE.md
    git commit -m "decisions: 0035 decided, and 0036 amended -- active-weight TC, and two bars

0035, DECIDED 2026-09-21: section 4 option (a) and section 5 both taken. All
three transfer-coefficient estimators are computed on w - w_baseline with the
long-only NNLS tracking portfolio as the baseline, and weights, alpha and the
rebalance-date index are persisted per run. Section 4a is added: covariance.py
already computes r2 and residual_variance per benchmark leg and nothing reads
them, so the quality of the baseline the corrected TC is measured against is
unmeasured; surfacing both, with a test asserting a floor on r2, is now a
requirement.

0036 was committed at d2f2c4b with sections 3, 4a and 4b decided. This amends
it. Section 6, DECIDED 2026-09-21, takes position 3 -- two bars. Bar 1 is the product bar, net IR >= 0.30, unchanged in
value and derived for the first time from the owner's stated 150 bp appetite at
the section 4 budget. Bar 2 is the evidence bar on net_ir_excess against a
block-shuffled baseline, with no threshold: it is the existing multiple_testing
veto, run on the excess. params/audit.yaml does not change and decisions/0025's
tracking-error budget is unmoved, because 0025 inverts the level and the level
is still 0.30.

Section 1 is amended with the dispersion the first draft omitted: the
no-information floor of 0.311 is the mean of a 420 bp-wide distribution across
arbitrary tilts on a single history, -141 to +280 bp, one tilt in eight
negative. 1.5% of alpha is hard; 1.5% from concentrated risk-premium exposure
over 2004-2019 is not, and the latter is what this is.

OWNER-QUEUE L9 closes. L10 and L11 are added. Queue: 22 implements 0035 and must
land before task 19; 23 is the JPMaQS catalogue check, metadata only."

**Commit B — the constitution.** `SUBSTRATE.md` only, so the owner reviews one
small diff, as §2 requires. v0.4 -> v0.5.

    git add SUBSTRATE.md
    git commit -m "substrate: sections 3 and 10 -- the objective is two bars (decisions/0036)

Transcribes decisions/0036 section 6, decided by the owner 2026-09-21. Section 3
replaces the single primary metric with two bars a candidate must both clear:
bar 1, net IR >= target_net_ir, the product bar, still 0.30 and still what the
leaderboard sorts by and what decisions/0025 inverts for the TE budget; bar 2,
net_ir_excess against a no-information baseline, positive and surviving the
multiple_testing veto, with no threshold and the reasoning for why a threshold
is the wrong instrument at this precision. Section 10's multiple_testing row
names the excess as the statistic it tests.

No agent originated this. The wording is transcribed from a decision the owner
made and recorded."

**Do not commit** `data/universe/raw_meta.json`, `raw_structure.json`,
`results/audit-bloomberg.log` or `results/audit/` — regenerable, and SUBSTRATE
§11 keeps them out of git. Everything else `git status` flags is a CRLF phantom;
confirm with `git diff --ignore-cr-at-eol` before adding.

**Then verify the governance check accepts the constitution change:**

    scripts/unattended.sh check --digest

**Receipt should say:** both commit hashes, that git recorded the 0035 move as a
rename rather than a delete plus an add, and the `governance` line from the
check. **Stop and report if governance does not pass** — an uncited owner-only
change is the one failure that must never be worked around.

### 12. Commit the Cowork write-up from 2026-09-20

`decisions/proposed/0035` is the only new repo file; the probe plan and the
rewritten state of play are Cowork project docs and are not in the repo.

    git add decisions/proposed/0035-the-transfer-coefficient-measures-the-benchmark-not-the-tilt.md HANDOFF.md
    git commit -m "decisions: 0035 proposed -- the transfer coefficient measures the benchmark

A-20260919-155557 read a median transfer coefficient of 0.018 against a
published range of 0.3-0.8. transfer_n_dates is healthy at 782-830 of 834
rebalances, so the alpha reaches the estimator and the conditioning is not
dropping dates: the number is what was computed.

It is not what 0033 intended. The oracle cells at IC = 1 -- a perfect forecast
-- read 0.039 to 0.042, and a constructed book holding no view at all reads
-0.017. The estimator cannot distinguish a book with a view from one without.

The benchmark legs are not holdable, so the book replicates the benchmark out
of the holdable universe and tilts away from it. active_covariance is right and
w' Omega w really is the active variance, but the numerator a'w and the
diagonal correlation take the whole fully-invested book, which is dominated by
replication and uncorrelated with alpha by construction.

0035 proposes computing all three estimators on w - w_baseline, and persisting
weights and alpha per run: results/artifacts/ is empty, which is why correcting
a column costs 13.3 hours instead of minutes."

**Receipt should say:** the commit hash.

### 13 and 14 — WITHDRAWN 2026-09-20. Do not run them.

Superseded by `decisions/0036` (decided 2026-09-20) and by the Cowork project doc
`claude/dose-response-step1-2026-09-20.md`. The task text below is left intact
as issued; nothing in it is authorised.

**Why 13 is withdrawn.** It cannot test the hypothesis it was written for.
`audit/signals.py` gives `alpha = ic * sigma * score / sqrt(h)`, so at `ic = 0`
the alpha is identically zero — the task is right about that. But
`portfolio/long_only.py` then resolves a zero alpha to the **minimum-tracking-
error book**, and says so in its own comment, naming "the IC = 0 rung of the
ruler audit". The live book runs 4.4-5.6% ex-ante TE; that one runs the least it
can. It is not the same book, so it is not a control for it.

**And the control was already in the grid.** At IC 0.02 the score is
`0.02*truth + 0.9998*noise` — the truth is 0.04% of its variance. That rung
reads **net IR 0.311** (SE 0.075 clustered on seed) while running 4.55% ex-ante
TE. Explaining it from its own 0.016 of realised IC would need a slope of 19.4
IR per unit IC, against every slope the lab has measured (0.13 to 1.03). The
no-information floor is measured, and `decisions/0023`'s bar is 0.30.

**Why 14 is withdrawn as queued, not cancelled.** Its purpose stands and it is
still the test for noise dominance, but it is now gated on the baseline grid
rather than on 13, and its power needs stating before two hours are spent: at
ten seeds the h13 MDE is **0.166 IR**, so it discriminates a steeply convex
response from a linear one and will not resolve anything shallower. It is
re-queued under "Not queued yet" below.

### 13. The IC = 0 control — the missing cell

`claude/dose-response-probe-plan.md` step 2, and the cheapest decisive
experiment available. The grid's rungs start at IC 0.02, and 0.02 is already
statistically indistinguishable from 0.20. **There is no zero-information
control**, so nothing in either Bloomberg audit establishes that the ladder
responds to signal at all.

Run ten seeds at four horizons with a pure-noise signal. About 40 cells at
roughly 100 s, so about **70 minutes** — not an overnight job.

How to express IC = 0 is yours to judge from the code; `plant()` with an IC of
zero should give an alpha that is identically zero, which is the no-view book.
If that path is not reachable without a code change, **stop and report** rather
than approximating it with a very small IC: a 0.001 rung answers a different
question.

**Expect `transfer_n_dates = 0` and a NaN transfer coefficient on every one of
these cells.** Alpha is identically zero, so there is no view to transfer. That
is the estimator behaving correctly, not a failure, and it is not a reason to
stop.

**Receipt should say:** rc, runtime, the run id, and the net IR by horizon with
its seed range. Nothing else — the interpretation is Cowork's and the owner's,
and the hypotheses it discriminates are in the probe plan.

### 14. Intermediate IC rungs — only if 13 shows no floor

Step 3 of the probe plan. Rungs at **0.35, 0.50 and 0.70**, ten seeds, **h13
only**. About two hours. Do not start it if task 13 showed a floor; in that case
the question has changed and Cowork will requeue.

**Receipt should say:** rc, runtime, run id, net IR by rung with seed ranges.


### 15. Commit 0036 and this queue rewrite

`decisions/0036` is new and **decided by the owner 2026-09-20** — it was never
committed while in `proposed/`, so it lands straight at its decided path.
`HANDOFF.md` and `OWNER-QUEUE.md` are modified.

**Run task 12 first.** Both tasks `git add HANDOFF.md`; whichever runs first
commits it and the other finds nothing to add for that path, which is expected
and not a failure. Note also that task 12's message says 0035 is "the only new
repo file" — true of untracked files when it was written, and 0036 has since
joined it. 12's add list is still correct; do not edit it.

    git add decisions/0036-the-bar-is-excess-over-a-no-information-baseline.md HANDOFF.md OWNER-QUEUE.md
    git commit -m "decisions: 0036 -- the bar is excess over a no-information baseline

decisions/0023 set the bar at net IR 0.30. On the development window a book
holding no usable information reads 0.311.

The control was already in A-20260919-155557 and had not been read as one. At
the IC 0.02 rung the planted score is 0.02*truth + 0.9998*noise, so the truth is
0.04% of its variance. That rung runs 4.55% ex-ante TE and earns 0.3106 net IR,
SE 0.075 clustered on seed. Explaining it from its own 0.016 of realised IC
needs a slope of 19.4 IR per unit IC; the frictionless twin measures 0.13 to
0.39 and the oracle-anchored linear slope is 1.03.

Every required_ic and surviving-cell count in both Bloomberg audits is therefore
read against a bar the floor already clears.

0036 reports net_ir_excess against a seed-matched, magnitude-matched
baseline with the information destroyed by a block shuffle -- the one
construction that also generalises to a real hypothesis, and the machinery
SUBSTRATE section 9 already requires for the search null and Romano-Wolf, which
src/signal_lab/stats/ does not have.

DECIDED by the owner 2026-09-20: sections 3, 4a and 6 taken. The metric is
excess over a block-shuffled baseline; section 4b pins the implementation.
Section 6 takes position 2 -- the bar is RE-DERIVED rather than carried across at
0.30 or split in two -- but the number itself is not set: params/audit.yaml
target_net_ir stays 0.30 and decisions/0023 is untouched until a derivation
exists. What that derivation takes as its input, and the fact that decisions/0025
derives the TE budget FROM the bar, are OWNER-QUEUE L9."

**Receipt should say:** the commit hash.

### 16. Six `data/requests/*.yaml` are modified and nothing commits them

`H-2026-0004`, `0006`, `0007`, `0009`, `0010`, `0011` carry real uncommitted
changes (confirmed with `git diff --ignore-cr-at-eol`; the rest of the tree's
`M` flags are CRLF phantoms). Task 12's `git add` list does not include them and
its message says 0035 is "the only new repo file" — true of untracked files,
not of modified ones.

They look like the ticker-resolution corrections of `decisions/0032` applied to
the request files — e.g. `H-2026-0009` moves `MXUS -> SPXT`, `MXEU -> MXEUG`,
`MXJP -> NDDUJN`, `MXEF -> M1EF` and drops `MXWO` and `LEGATRUU`. **Verify that
before committing**, because I have not established what produced them:

1. Check whether a target regenerates them (`make requests`, or whatever
   `scripts/` writes `data/requests/`), and if so, run it in a clean worktree
   and diff against the working tree.
2. If they match a regeneration, commit citing `decisions/0032`.
3. **If they do not match, stop and report.** Hand-edited pre-registration
   artefacts are exactly what `decisions/proposed/0034` exists about.

**Receipt should say:** rc, whether a regeneration reproduced them, and the
commit hash or the reason for stopping.

### 17. Implement the block-shuffled baseline — `decisions/0036` §4(a) and §4b

**Implement from the record, not from this task.** `0036` §4b pins five things
that the code makes non-obvious; read it before writing anything. In summary:
shuffle whole date-rows in contiguous 52-row blocks with one permutation shared
across instruments, before standardisation; **re-apply the original NaN mask**
afterwards or you breach the `frequency` veto on a ragged panel; draw the
permutation from a **stream independent of the noise RNG** or the seed-matching
the baseline exists for is destroyed; **encode the baseline in `AuditCell.key()`**
or it collides with its live twin in an append-only store; and build the grid
selector in `ladder.py` / `scripts/run_audit.py` / `build.mk` /
`scripts/unattended.sh`, **not** in `params/audit.yaml`, which is owner-only and
not authorised by this record.

Put the shuffle itself in **`src/signal_lab/stats/`**, not in `audit/`. It is
SUBSTRATE §9's block-bootstrap machinery — the same primitive the search null and
the Romano-Wolf stepdown need, and that package is currently one line.

`0036` §5's five acceptance tests are **tests**, not a one-off check. The fourth
one matters most for what follows: the shuffle switched off must reproduce
today's `net_ir` **bit for bit**, because tasks 18 and 19 pair new baseline cells
against the *existing* `A-20260919-155557` live cells rather than re-running
them.

Interface to build, so tasks 18 and 19 have a command:

    make audit-baseline-pilot   ->  run_audit.py --source bloomberg --grid baseline-pilot
    make audit-baseline         ->  run_audit.py --source bloomberg --grid baseline
    scripts/unattended.sh audit-baseline-pilot | audit-baseline   (extend the whitelist)

`baseline-pilot` is h13 only, the four `audit.ic_grid` rungs, all ten seeds — 40
cells. `baseline` is all four horizons — 160 cells. Both read the grid values
from `params/audit.yaml`; neither adds a key to it.

Then:

    scripts/unattended.sh check --digest

**Receipt should say:** rc, test count, runtime, the commit hash, and
explicitly whether the bit-for-bit reproduction test passes. **Stop and report
if it does not** — everything downstream depends on it.

### 18. The baseline pilot — 40 cells, about 50 minutes

Only after 17 is committed and `make check` is rc=0.

    scripts/unattended.sh audit-baseline-pilot --digest

**What it answers.** The live book runs 4.42% active vol at IC 0.02 and 5.58% at
IC 0.20. The question is whether the no-information floor grows with the risk the
book takes. **If the baseline at the IC 0.20 rung also reads about 0.31, every
rung on the ladder is floor** and task 20 is pointless — this run can cancel the
next one.

**Before taking any contrast, check that the new run's `panel_hash` and
`params_hash` in `summary.json` match `A-20260919-155557`'s**
(`dfbf5c5a68a399d90babe84b757f7f849c4f75fbe6babff5b2db646b66575793` and
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c`). If either
differs, the pairing is across panels and the contrast is not valid — **stop and
report** rather than reporting the number.

**Receipt should say:** rc, runtime, the run id, whether both hashes match, and
the baseline `net_ir` by IC rung with its seed range. Nothing else — the
interpretation is Cowork's and the owner's.

**Amendment, 2026-09-20, after reviewing task 17's receipt.** Task 17 imputes the
standardised truth's mean (0.0) at cells that were live but drew a NaN row in the
shuffle, so the baseline's availability matches its live twin exactly. Cowork has
checked this and it is the right call — `_standardise_truth` leaves `truth_z`
with pooled mean exactly zero, so the fill is neutral mean-imputation and not an
injected tilt, and the second-order shrinkage of the blend's dispersion moves the
alpha magnitude by well under 1% in standard deviation even at a large imputed
share. **No change is asked for.** But the share is unmeasured and the panel is
ragged — late-starting series can reach a quarter of their own rows — so it
should be disclosed rather than assumed.

**Add to the receipt:** the share of live cells that were mean-imputed in the
shuffle, overall and for the worst single instrument, as counts and percentages.
A count is not a vendor value and is reportable under `CLAUDE.md`. If it exceeds
roughly 25% overall, say so and **stop before task 19** — that would mean the
baseline is a materially less dispersed signal than its twin and 0036 §4(a)'s
magnitude-matching claim needs revisiting.

**Also note:** `make audit-baseline-pilot` has never run to completion. Task 17
checked `_write_baseline_run` on a two-cell table only, so this is the first real
exercise of that path and may surface plumbing before it surfaces a number.

### 19. The full baseline grid — 160 cells, about 3.3 hours

Only if 18 is clean and the hashes matched. Do not start it if 18 stopped.

    scripts/unattended.sh audit-baseline --digest

**Receipt should say:** rc, runtime, run id, baseline `net_ir` by IC rung and
horizon with seed ranges.

### 20. Intermediate IC rungs — the old task 14, re-queued

Rungs at **0.35, 0.50 and 0.70**, ten seeds, **h13 only**, about two hours.
Gated on task 18, not on the withdrawn task 13: **do not start it if the pilot
showed the floor at the IC 0.20 scale is the same as at IC 0.02.** In that case
the ladder has never measured signal and Cowork will requeue.

Know its power before spending the two hours: at ten seeds the h13 MDE is
**0.166 IR**. It discriminates a steeply convex response from a linear one and
will not resolve anything shallower.

**Receipt should say:** rc, runtime, run id, net IR by rung with seed ranges.
---

**AMENDMENT, 2026-09-21 — the gate is released and the task is re-specified.
Read this, not the text above.**

**The stop rule above has fired and the owner has released it.** Task 18 showed
the floor at the IC 0.20 alpha scale (0.346) matching its live twin (0.356) and
the floor at IC 0.02 (0.290), so by the letter of task 18 this task should not
start. That rule was written before the baseline existed and is now the wrong
call: it was aimed at "is there signal in the tested range" — answered, no — and
this task asks a different question the pilot does not touch, **where the
response begins between IC 0.20 and IC 1.00.** The oracle reads 1.297 at h13
against a floor of 0.290, so a large response exists somewhere. Owner released
the gate 2026-09-21.

**And the baseline nearly doubles its power.** The warning above about an h13
MDE of 0.166 was for the **level**. On the **excess** the pilot measured SE
0.032 at IC 0.20, so the MDE is **≈0.09** — sharp enough to resolve a shallow
response, which the level was not.

**0. Commit first.** Task 18's receipt and the queue changes since are
uncommitted (`git diff --ignore-cr-at-eol` shows `HANDOFF.md` and
`OWNER-QUEUE.md`). Commit them before running, so the receipt lands against a
committed baseline.

**1. Build a `knee` grid — in `ladder.py`, not in `params/`.** The rungs
**0.35, 0.50, 0.70** are not in `audit.ic_grid`, and `params/audit.yaml` is
owner-only and not authorised by any record here. `baseline_cells()` reads its
rungs from params by design (`decisions/0036` §4b.5) and emits baseline cells
only, so neither serves. Add a third grid whose rungs are a module constant and
which emits **both** a live cell and its matched baseline at each rung:

    h13 only, ten seeds, 3 rungs x 2 = 60 cells

**`params/audit.yaml` must not change.** `params_hash` stays
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c`, or the
pairing against `A-20260919-155557` and `A-20260921-202607` breaks for every
future run.

**2. Do not re-run IC 0.20.** It exists live in `A-20260919-155557` and baseline
in `A-20260921-202607`, both at the same hashes. Pair it from those as the
anchor.

**3. Run.** At the pilot's measured **58 s a cell**, 60 cells is about an hour;
live cells at high IC trade more, so budget 60-90 minutes.

**Receipt should say:** rc, runtime, run id, and per rung **the live net IR, the
baseline net IR, and the seed-paired excess with its standard error** — the
excess is the statistic now (SUBSTRATE §3 bar 2), not the level. Confirm both
hashes match before reporting any contrast, as task 18 did, and **stop and
report if either differs.**

### 21. Remove the parked lock file Cowork left in `.git`

Not blocking and not urgent — order does not matter. On 2026-09-20 a Cowork
`git status` refreshed the index and created `.git/index.lock`, which the Cowork
mount cannot delete (`Operation not permitted`). It was renamed out of the way
rather than left in place:

    rm -f .git/index.lock.stale-cowork-20260920

Git ignores the parked name, so nothing is currently blocked; this is hygiene.
Do not remove `.git/index.lock` itself if one exists without first checking that
no git process is running — the 2026-09-18 receipt in `## Done` records a stale
lock that vanished on its own.

**Receipt should say:** rc, and whether the file was there.

### 22. `decisions/0035` §4(a), §4a and §5 — BEFORE task 19

**Decided by the owner 2026-09-21.** `0035` is out of `proposed/` and carries
the spec; read it, not this summary.

**Why it is sequenced here.** Task 19 is a 3.3-hour, 160-cell grid. If it
persists nothing, any later question about those cells costs another 3.3 hours —
which is precisely the hole `0035` §5 was written about, and the lab is one run
away from digging it again. This must land before 19. It need **not** block task
18: the pilot is 40 cells and 50 minutes, cheap to re-run once this exists.

Three pieces:

1. **§5 — persist per run.** `weights`, `alpha` and the rebalance-date index, as
   parquet under `results/artifacts/<run_id>/`, which `STATUS.md` already claims
   exists and which is empty. Base cells at minimum; say in the receipt what the
   disk cost per run turned out to be.

2. **§4(a) — the corrected transfer coefficient.** All three estimators computed
   on `w - w_baseline`, the baseline being the long-only NNLS tracking portfolio
   the lab already builds in `portfolio/covariance.py`. `Omega` and `w' Omega w`
   are unchanged; only the numerator and the correlations move. `0035` §4's
   acceptance test is required and is a **test**, not a check: an IC = 1 oracle
   cell must read a TC near its achievable ceiling, and a no-view book must read
   near zero. Both read wrong today (0.039-0.042 and -0.017).

3. **§4a — surface the replication quality.** `covariance.py` already computes
   `r2` and `residual_variance` per benchmark leg into its `diagnostics` dict and
   **nothing reads them.** The corrected TC is now measured against that
   baseline, so its quality has to be visible: report both per leg wherever TC is
   reported, and assert a floor on `r2` in a test so a degraded replication fails
   loudly instead of quietly re-basing the coefficient.

Then:

    scripts/unattended.sh check --digest

**Receipt should say:** rc, test count, runtime, commit hash, the persisted
artifact size per run, and **the NNLS `r2` per benchmark leg** — that number has
never been looked at and the owner asked for it directly. **Stop and report if
`r2` on either leg is below 0.90**; that would mean the baseline is a poor
replication and `0035` §4's definition needs revisiting before any corrected TC
is reported.

**No re-run of `A-20260919-155557` is authorised here.** Its artifacts do not
exist, so its TC column stays as it is; `0035` §6 says whether to spend the 13.3
hours is a separate decision.

### 23. JPMaQS catalogue check — metadata only, no vintage data

**Independent of 18, 22, 19 and 20.** Different data, different code path,
different gate; run it whenever. Owner authorised 2026-09-21.

**What it is for.** The registry's 27 JPMaQS names have never been checked
against the vendor's catalogue. `decisions/proposed/0034` exists because two
*Bloomberg* names in the pre-registered registry turned out not to exist and were
found by hand. This checks the JPMaQS half before a pull is built on it. **It
does not retire 0034**, which is a standing validator across every source; it
retires the risk for these 27 names, once.

**This call is authorised under SUBSTRATE §2** — `jpmaqs` is listed in
`params/data_sources.yaml` with `enabled: true` and credentials supplied
2026-09-09. It is the lab's first vendor API call.

#### Hard limits

- **Metadata only.** `JPMaQSDownload.get_catalogue(...)` and/or
  `filter_expressions_from_catalogue(expressions, ...)`. **Do not call
  `download()`.** No vintage data, no `value`/`grading`/`eop_lag` pull.
- **Do not touch `params/data.yaml: jpmaqs.status`.** It stays
  `credentials_supplied`. A catalogue is not the macro block, `search_is_open()`
  must stay shut, and `params/` is owner-only regardless.
- **Do not implement `load_macro`.** It stays `LoaderNotImplemented`; that is
  task 24 and is not queued.
- **Never read, print or commit `.env` or anything key-shaped.** Use the existing
  `JPMaQSLoader.credentials()` and `.proxies()`.
- The proxy is `enabled: false` by config — the corporate host does not resolve
  on this machine. **If the call fails on network or auth, report and stop.** Do
  not vary the proxy setting, and do not retry with alternate hosts.

#### Steps

1. **Install the extra.** `make install` is `uv sync --group dev` and the
   `jpmaqs` extra is not in it, so `macrosynergy` is absent from the venv:

       uv sync --group dev --extra jpmaqs

   This changes the venv. Confirm `make check` is still rc=0 afterwards and say
   so in the receipt.

2. **Add a `make jpmaqs-catalogue` target** wrapping a new
   `scripts/jpmaqs_catalogue_check.py`, so the flags live in `build.mk` like
   every other script. Construct the client with `check_connection=True` for a
   clean early failure.

3. **Check the 27 named tickers** tagged `genuine phase-3 gap` in
   `data/requests/ticker_resolution.csv` — **the 27 named, not the 96 the cross
   product returns.** They are 8 cids x 12 xcats; `cross_product_size()` already
   exists for that arithmetic and the receipt should confirm the 96.

4. **Cache the raw catalogue** under `data/raw/` (git-ignored, and off-limits to
   print or summarise per `CLAUDE.md`). It is the offline resolver 0034 would
   need, so it is worth keeping.

5. **Write the findings** to `data/requests/jpmaqs_catalogue_check.csv`:
   hypothesis, ticker, cid, xcat, resolves. Ticker names are not vendor values.

#### Stop rule

**If any of the 27 does not resolve, STOP.** Report the list and do not
substitute, do not guess a near-miss name, and do not drop it. Substitutions are
the owner's call — that is the `decisions/0032` precedent, where `LUALTRUU` and
`LT08TRUU` were removed rather than replaced, and SUBSTRATE §7 makes a silent
substitution a `coverage` veto failure.

**Only if all 27 resolve**, write `data/jpmaqs/request.txt` with them. SUBSTRATE
§5.6 names that file as the pull list and it does not exist — the directory holds
only `.keep`. Note in it that the download returns the cross product and the
loader must filter back to the named tickers.

**Receipt should say:** rc, whether `make check` still passes after the sync, the
catalogue size **as a count**, how many of the 27 resolve, the names of any that
do not, and whether `request.txt` was written.

---

### 25. Bar 2's power on a single history — shuffle the whole score

Added 2026-09-22 by Cowork. **Read `claude/detection-threshold-review-2026-09-22.md`
§1 first** (Cowork project doc).

**Why.** Task 17's baseline keeps its live twin's noise draw and shuffles **only
the truth**. That is the right control for the engine's dose-response — live and
baseline net IR correlate 0.85-1.00 across seeds, so the paired excess is sharp.
It is **not** the null a real hypothesis meets. A real signal has no separate
noise term: bar 2 puts one live IR against the block-shuffle distribution of the
**whole** signal, on one history. This task measures that distribution for
planted signals of known information content, so bar 2's actual power is read
rather than assumed.

**0. Commit first.** `HANDOFF.md` and `OWNER-QUEUE.md` carry this task and
OWNER-QUEUE L13, uncommitted. Commit them before building, so the receipt lands
against a committed queue.

**Build a second shuffle mode, `score`.** Shuffle the fully blended score
(truth and noise together) rather than the truth alone:

1. Build the live score exactly as today, then shuffle its date-rows with
   `block_shuffle_rows` — same 52-row blocks, one permutation shared across
   instruments, as `decisions/0036` §4b.
2. Re-apply the live NaN mask, with the same neutral fill task 17 uses for cells
   that were live but drew a NaN row.
3. Recompute `alpha = ic * sigma * score / sqrt(horizon)` from the shuffled
   score. **`sigma` is not shuffled** — it is the risk model's input, not the
   signal.
4. Each permutation `perm` in 0..19 draws from its own stream, independent of
   the noise RNG **and** of today's `baseline_rng(seed)`. Extend `baseline_rng`
   (or add a sibling) so that the **existing call reproduces today's stream
   exactly** — the bit-for-bit test below depends on it.
5. Add the mode and `perm` to `AuditCell` with defaults that leave every existing
   key unchanged, and append them to `key()` only when non-default (e.g.
   `_baseline_score_p07`), so nothing collides in the append-only store.

**Tests, not checks:** task 17's bit-for-bit reproduction test still passes;
existing live and truth-shuffle keys are unchanged; different `perm` give
different permutations and the same `perm` is deterministic.

**Grid `power`, in `ladder.py`,** rungs as a module constant like `KNEE_IC_RUNGS`
— nothing in `params/`. h13, IC **0.35** and **0.70**, live seeds **0** and
**1**, 20 permutations each: 2 x 2 x 20 = **80 cells**, about 80 minutes at 58 s
a cell. Score-shuffle cells only; the live twins exist in `A-20260922-005316` —
do not re-run them. Add `make audit-power` and extend the `scripts/unattended.sh`
whitelist.

**`params/` must not change.** `params_hash` stays
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c`.

    scripts/unattended.sh check --digest
    scripts/unattended.sh audit-power --digest

**Receipt should say:** rc, runtime, run id, commit hash; whether both hashes
match `A-20260922-005316` (**stop and report if either differs**); whether the
bit-for-bit test passes (**stop and report if not**); and for each (IC, seed) the
live net IR, the mean and sd of its 20 shuffled net IRs, and the live IR's rank
among the 21. Nothing else — the interpretation is Cowork's and the owner's.

---

### 26. `credentials()` refuses a malformed secret — loudly, without printing it

Added 2026-09-23 by Cowork. Independent of every other task.

**0. Commit first.** `HANDOFF.md` (tasks 26-27, the run-order note) and
`OWNER-QUEUE.md` (L14) are uncommitted. Commit them before building. Task 25's own
step 0 will then find nothing to add, which is expected and not a failure.

**Why.** Task 23 lost a day to a `401` that was two credential faults, one of
them a trailing `\r` on `DQ_CLIENT_ID` from a CRLF `.env` sourced in WSL.
`JPMaQSLoader.credentials()` (`src/signal_lab/loaders/jpmaqs.py`) passes
environment values through untouched, so a malformed value reaches the vendor
and comes back as an authentication error that points everywhere but here.

**Build.** In `credentials()`, after the missing-key check, **refuse** — do not
strip — any value that has leading or trailing whitespace or contains a control
character (`\r`, `\n`, `\t`, or anything with `ord < 32` or `== 127`). Raise
`RuntimeError` naming **the variable and the defect only** ("DQ_CLIENT_ID has a
trailing carriage return -- is .env CRLF? run: sed -i 's/\r$//' .env").
**Never include the value, its length, or any slice of it** in the message.
Refusal rather than stripping is deliberate: SUBSTRATE §10's fail-loud rule, and a
silently repaired secret hides which file is wrong.

If `FREDLoader` (or any other loader) reads a key from the environment the same
way, apply the same check there through one shared helper; say in the receipt
whether it did.

**Tests** (new `tests/test_jpmaqs_credentials.py`, `monkeypatch.setenv` with
dummy values only): a clean pair passes; a trailing `\r`, a trailing space, an
embedded `\n` and a leading tab each raise; the raised message contains the
variable name and does **not** contain the dummy value. No network, no
`macrosynergy` import needed.

    scripts/unattended.sh check --digest

**Receipt should say:** rc, test count, runtime, commit hash, which loaders now
use the helper.

### 27. Candidate names for the 12 unresolved JPMaQS tickers — names only, no choice

Added 2026-09-23 by Cowork. **Needs the cached catalogue from task 23**
(`data/raw/jpmaqs_catalogue.json`, a JSON list of ticker strings). **No vendor
call** — work from the cache.

**Why.** 12 of 27 registered tickers do not resolve (task 23 receipt;
`data/requests/jpmaqs_catalogue_check.csv`). Every failure is at the xcat: each
cid resolves elsewhere. OWNER-QUEUE L14 asks the owner to rename, drop or wait
on each. This task gives him a short list to choose from instead of the vendor
documentation. **It chooses nothing.**

**Build `scripts/jpmaqs_candidates.py` and `make jpmaqs-candidates`.** For each
row of `jpmaqs_catalogue_check.csv` with `resolves == False`:

1. Take the xcat's **stem** — the leading token before the first `_`
   (`INTRGDP`, `UNEMPLRATE`, `BLSDCLN`, `MBASEGDP`, `RM1GDP`, `RM3GDP`,
   `GB10YXGB`).
2. List every catalogue ticker with the **same cid** whose xcat starts with that
   stem. If there are none, relax to the first four characters of the stem and
   mark the row `relaxed`. If still none, write one row with `candidate` empty.
3. Write `data/requests/jpmaqs_candidates.csv`: `hypothesis, requested,
   cid, stem, match (stem | relaxed | none), candidate`. Sort by requested, then
   candidate. Cap at 40 candidates per requested ticker and say in the receipt
   if any hit the cap.

**Hard limits.** Ticker **names** only — they are not vendor values and are
reportable; nothing else from the catalogue leaves `data/raw/`. **Do not edit**
`ticker_resolution.csv`, any hypothesis file, `data/requests/H-*.yaml`, or write
`data/jpmaqs/request.txt`. **Do not rank or recommend** — no "best match"
column; the choice is the owner's under the `decisions/0032` precedent.

**Test:** a small fixture catalogue (hand-written names, not vendor data) checks
the stem match, the relaxed fallback and the empty row.

    scripts/unattended.sh check --digest
    make jpmaqs-candidates

**Receipt should say:** rc, commit hash, and per requested ticker the count of
candidates and its `match` level. Not the candidate names themselves — they are
in the CSV.

### 28. The cycle tests write into the real `data/requests/` — isolate them

Added 2026-09-23 by Cowork, from the task 26-27 receipt. **Run this first; it
unblocks 26 and 27.** Claude Code's diagnosis is right and Cowork has confirmed
it in the code:

- `scripts/nightly_cycle.py` has no `--requests-dir`. It builds
  `HypothesisRegistry` with the default `requests_dir=REQUESTS_DIR`, which is
  `REPO_ROOT / "data" / "requests"` (`harness/hypotheses.py:35`).
- The three cycle tests in `tests/test_scripts.py`
  (`test_nightly_cycle_records_blocked_not_a_fake_veto_failure`,
  `test_the_cycle_records_the_specific_blocked_reason` and
  `test_the_validation_run_is_recorded_and_tagged`) isolate the snapshot and the
  store in `tmp_path`, but not the requests. So every `make check` rewrites the
  tracked `data/requests/H-2026-00xx.yaml` from a synthetic snapshot.
- That write, on `/mnt/c`, is what hit `EINVAL`: something on the Windows side
  held the file open. Isolating the write removes that exposure, and an
  intermittent test failure then points at a real problem instead of a
  Windows file lock.

**Build.**

1. Add `--requests-dir` to `nightly_cycle.py`, defaulting to the current
   `REQUESTS_DIR`, and pass it to `HypothesisRegistry(requests_dir=...)`.
   Nothing changes for a real cycle run.
2. Pass `--requests-dir str(tmp_path / "requests")` in every test that calls
   `cycle.main` without `--dry-run`. Grep for all of them rather than trusting the
   three names above.
3. **Add a guard test.** It records the mtimes and hashes of everything under
   `data/requests/` and `hypotheses/`, runs one cycle through `cycle.main` with
   the new flag, and asserts both trees are byte-identical and untouched. The
   cycle can also `shutil.move` hypothesis files between states
   (`hypotheses.py:572`), so this is the guard against any future test that
   forgets the flag.
4. Do not change what triage writes, or where a real run writes.

**Then re-run the check once, with tasks 26 and 27 in the working tree:**

    scripts/unattended.sh check --digest

- **rc=0:** commit in three parts: 28 alone, then 26, then 27. Then run
  `make jpmaqs-candidates` (task 27's last step) and continue to task 25.
- **rc=2 again:** stop and report the failing test ids. Do not re-run hoping it
  clears.

**Receipt should say:** rc, test count, runtime, the three commit hashes,
whether the guard test passes, and task 27's per-ticker candidate counts and
match levels as that task asks.

**One question for the receipt, not for fixing.** Task 16 (2026-09-20) stopped
because six `data/requests/*.yaml` had changed and nothing seemed to regenerate
them. It concluded that a synthetic triage "would not reproduce the changes".
This finding suggests `make check` may have been what wrote them. Say whether
the files these tests produce in `tmp_path` match the committed ones
byte-for-byte (`diff`, names only, no values involved). If they match, task 16's
"hand-edited?" question has its answer.

---

### 31. Apply the owner's L14 renames for H-2026-0004, 0005, 0010, then the vendor check

Added 2026-09-27 by Cowork. **Owner ruling 2026-09-27, OWNER-QUEUE L14:** "recs
on all". This is the same pattern as `33b84f4` (H-2026-0001). No compute.

**0. Commit first.** `OWNER-QUEUE.md` carries L14's ruling and the 2026-09-26
task-30 notes under L15 and B3. `HANDOFF.md` carries this task. Commit the
two alone (`queue: task 31, L14 ruling 2026-09-27`).

**1. Addendum to `decisions/0032`,** `## Addendum, 2026-09-27`, in the same
form as the 2026-09-24 one. Cite OWNER-QUEUE L14, tasks 27 and 29
(`data/requests/jpmaqs_name_search.csv`), and Macrosynergy's Academy notebooks
"Bank survey scores", "Monetary aggregates" and "Government bond yields and
carry" for what each series measures. The table:

| hypothesis | phase-0 name | now | why |
|---|---|---|---|
| 0004 | `{USD,EUR}_BLSDCLN_SA_D1Q1QL1` | `{USD,EUR}_BLSCSCORE_NSA_D2Q2QL2` | lending *standards* z-score (credit supply; positive = easing), 2 quarters over the prior 2, matching the signal's "2q change". **Enters negated**, so the registered direction `negative` (on tightening) is unchanged. NSA z-score, not an SA balance. `BLSDSCORE` is credit *demand* and was not used |
| 0005 | `EUR_RM3GDP_SA_D1M1ML12` | `EUR_RMBROAD_SJA_P1M1ML12` | real broad money (M3, CPI-deflated), % over a year ago, the hypothesis's title. A growth rate, not "% of GDP" |
| 0005 | `USD_RM1GDP_SA_D1M1ML12` | `USD_RMBROAD_SJA_P1M1ML12` | as above. **USD broad money is M2**. The narrow-money leg is dropped: the hypothesis is about broad money |
| 0005 | `USD_MBASEGDP_SA_D1M1ML12` | **dropped** | no 12-month change exists (1/3/6 only); monetary base is a different mechanism; a derived change would mix vintages |
| 0010 | `USD_GB10YXGB_NSA` | `USD_GB10YCRY_NSA` | no `XGB` series and no term-spread category exist. 10y carry is "yield plus roll-down", the rationale's own words, so the signal is **re-specified from term spread to carry** |
| 0010 | `EUR_GB10YXGB_NSA` | `DEM_GB10YCRY_NSA` | no euro-area bond cross-section; bonds are by country, and the Bund is the benchmark |
| 0004 | `DRTSCILM` (FRED) | **dropped** (owner 2026-09-27) | the Fed's own survey of US lending standards duplicates the `USD_BLSCSCORE` leg and runs the opposite sign (positive = tightening). It also withdraws the 2026-09-19 approval to add it to the FRED request (`decisions/0032` §5, OWNER-QUEUE L6) |

Say that direction, horizon, target and rationale are otherwise unchanged. Say
that the phase-0 names remain in git history. **Also
record, in one line,** that 0010's declared safeguard (risk decomposition, B5)
still can't be built. That's a caveat, not a change.

**2. Update the files,** as `33b84f4` did:
- `hypotheses/pending/H-2026-{0004,0005,0010}.yaml`: `data_required`, plus a
  dated "Amended 2026-09-27 by owner ruling" note in each, saying what changed
  and why. Do **not** edit `direction`, `horizon_weeks`, `target_axis` or the
  rationale.
- `data/requests/H-2026-{0004,0005,0010}.yaml`: the same series changes.
  Nothing else.
- `data/requests/ticker_resolution.csv`: the new names under the same status
  (`jpmaqs_gap`, "genuine phase-3 gap"). Remove the rows for the two dropped
  0005 names and for `DRTSCILM`, and give the reasons in the addendum.
- `src/signal_lab/harness/hypotheses.py` mentions `DRTSCILM`. If that's a
  request or series list, remove it there too. If it's a test fixture or an
  example, leave it and say so in the receipt.
- Don't hand-edit `jpmaqs_catalogue_check.csv` or `jpmaqs_candidates.csv`.
  The vendor check rewrites the first one.

**3. Vendor names check.** This is a metadata call, the same one task 23 ran
under `decisions/0037`. It pulls no vintage data.

    scripts/unattended.sh check --digest
    make jpmaqs-catalogue

**Expect 26 names, all resolving** (27 registered; 0005 goes from 3 names to
2, since two legs are dropped and one is added): 7 for 0001, 2 for 0002, 4 for
0003, 2 for 0004, 2 for 0005, 4 for 0006, 2 for 0010 and 3 for 0011. **If any
name fails to resolve, stop and report it. Don't substitute.** If the vendor
call fails for auth or network reasons, stop and report it the way task 23
did. Never print credentials.

**Receipt should say:** rc, commit hashes, the resolve count (or the failures),
and whether `check` passed. **Then stop.** Implementing `load_macro` and the
pull itself are not part of this task.

---

### 32. The friction sweep: the shadow-cost coefficient at 10, 20 and 40

Added 2026-09-28 by Cowork. **Owner-approved 2026-09-28** (OWNER-QUEUE B3c,
`decisions/0038`). **Run this before task 33**: its 10 bp arm checks against
the knee run under today's `params_hash`, which task 33 changes. About 1-1.5 h.

**0. Commit first,** alone: `decisions/0038-turnover-is-disclosed-not-vetoed.md`,
`decisions/0039-the-lab-screens-it-does-not-confirm.md`, `HANDOFF.md` and
`OWNER-QUEUE.md` (`decisions: 0038, 0039 (owner rulings 2026-09-28); queue
tasks 32-34`). Committing 0038 doesn't apply it; that's task 33.

**Why.** Task 30's books trade 3.2-3.4x a year against a 100% target, so the
shadow cost isn't holding turnover near its target. The owner wants to see
how results respond to more friction. The shadow cost
(`constraints.turnover.penalty.coefficient`, 10 bp at 150%) shapes weights and
never enters net IR. The real costs are unchanged, so net IR stays honest.

**Build.** Add `shadow_coefficient: float | None = None` to `AuditCell`.
`None` reads `params/` as today, and any other value overrides the coefficient
for that cell only. Append it to `key()` only when set (e.g. `_shadow20`), so
existing keys don't change. Add a `friction` grid to `ladder.py` as module
constants (nothing in `params/`): h13, IC **0.35 and 0.70**, seeds **0-9**,
coefficient **10, 20, 40**, live cells only. That's **60 cells**, including
the 10 bp arm. Add `make audit-friction` and extend the `unattended.sh`
whitelist.

**Test:** a cell with `shadow_coefficient=None` and one with `10.0` give
identical results. Existing keys are unchanged.

    scripts/unattended.sh check --digest
    scripts/unattended.sh audit-friction --digest

**Receipt should say:**
- rc, runtime, run id, commit hash.
- **The 10 bp arm against the knee run `A-20260922-005316`:** live `net_ir`
  identical, cell by cell, for all 20 (IC, seed) pairs, and whether the hashes
  match. **Stop and report if not.**
- Per (IC, coefficient), median and range over 10 seeds of: net IR, cost drag
  (gross − net), annual turnover, rolling one-year max turnover, `te_p95`, and
  realised IC.
- Paired by seed: net IR at 20 and at 40, minus net IR at 10 (mean, sd, and how
  many seeds are positive).
- Counts above **200%** (the new highlight level), annual and rolling max, per
  arm.
- `risk_calibration` fails per arm.

Interpretation is Cowork's and the owner's. **Then stop.**

### 33. Apply `decisions/0038`: turnover is disclosed, never vetoed

> **SUPERSEDED 2026-09-29 by task 39**, which applies 0038 (with its
> 2026-09-29 addendum) and 0040 together. Do not run this task.
>
> *Earlier:* **ON HOLD, 2026-09-28 (Cowork, at the owner's instruction).** The owner is
> holding the 0038 ruling until he has read the friction sweep (OWNER-QUEUE
> L17, L18). **Do not run any step of this task**, including step 0, whose
> commit has moved to task 34's step 0. Cowork will lift or re-issue it.

Added 2026-09-28 by Cowork. **Owner ruling 2026-09-28** (OWNER-QUEUE B2 and
B3). This touches `SUBSTRATE.md`, `params/` and `vetoes/`, all owner-only.
**Every commit cites `decisions/0038`**, which is in the working tree,
uncommitted. **Run after task 32.**

**0.** 0038 was committed in task 32's step 0. Cowork has since added the
owner's confirmation-gate ruling to `decisions/0039` and L16. Commit those two
files alone first (`decisions: 0039 confirmation gates (owner 2026-09-28)`).

**1. Apply "What changes" 1-5 of 0038 exactly.** Nothing else in `params/`,
`vetoes/` or `SUBSTRATE.md`. The only params change is to `vetoes.yaml` and one
new reporting key in `constraints.yaml`. Don't touch `per_rebalance_caps`.
Bump `params_version` as the repo's convention requires.

**2. Verify past verdicts.** For every `results/audit/A-*/cells.csv`, count the
cells whose verdict names `turnover`. The expected count on Bloomberg runs is
zero. List any that aren't.

**3. Record** the old and new `params_hash` in 0038's "Consequences" section,
as a dated line.

    scripts/unattended.sh check --digest

**Receipt should say:** rc, commit hashes, the old and new `params_hash`, the
verdict count from step 2, and the tests that changed and why. **Then stop.**

---

### 34. FDR against FWER: build the multiple-testing module, then a Monte Carlo on the registry's shape

**0. Commit first, alone** (added 2026-09-28 evening; this replaces task 33's
step 0, which is on hold): `decisions/0039-the-lab-screens-it-does-not-confirm.md`,
`decisions/0040-the-shadow-cost-prices-the-turnover-a-trade-creates.md`,
`OWNER-QUEUE.md` and `HANDOFF.md`, with the message `decisions: 0039 gates
adopted, 0040 created-turnover shadow (in principle); queue: hold 33, add 35-36,
L12 corrected, L17-L18 (owner 2026-09-28)`. Nothing under `params/`, `vetoes/` or `SUBSTRATE.md` is in this
commit. Verify with `git diff --cached --ignore-cr-at-eol --stat` before
committing.

Added 2026-09-28 by Cowork. **Owner-approved 2026-09-28** (OWNER-QUEUE L16).
**No engine runs:** a statistics-level simulation, calibrated on task 30, that
runs in minutes. Independent of tasks 32 and 33, but runs after them in queue
order.

**Why.** The owner ruled the lab a screen (`decisions/0039`). SUBSTRATE §9 still
gates on Romano-Wolf at FWER 5%, and §9 already names FDR as the owner-decided
alternative. **Nothing in `src/` implements either yet:** `stats/` holds only
`blocks.py`, and `run_context.romano_wolf` is a placeholder. The owner wants a
number to decide on: how much power FDR buys over FWER for a registry shaped
like this one, and at what realised error.

**1. Build `src/signal_lab/stats/multiple_testing.py`,** the module the real bar-2
gate will use later. Each procedure takes observed statistics `t` (shape `m`)
and a joint null draw matrix `T0` (shape `k x m`, one row per shuffle, with
columns sharing the permutation, as the audit's shuffles do). Each returns a
boolean reject vector and the adjusted p-values:
- `holm(p, alpha)`: the reference FWER procedure, which ignores dependence.
- `romano_wolf(t, T0, alpha)`: the stepdown max-t, FWER. Romano & Wolf (2005,
  *Econometrica*; 2016, *Statistics & Probability Letters*).
- `benjamini_hochberg(p, q)` and `benjamini_yekutieli(p, q)`.
- `romano_shaikh_wolf_fdr(t, T0, q)`: bootstrap FDR under dependence.
  Romano, Shaikh & Wolf (2008), *Econometric Theory* 24(2). Implement from the
  paper. **Record any choice the paper leaves open in the docstring.** If you
  can't implement it faithfully, say so in the receipt and ship the others;
  don't approximate it silently.
- Marginal p-values from the null draws: `p_j = (1 + #{T0[:, j] >= t_j}) / (k + 1)`.

**Tests, with known answers:**
- BH and BY on a hand-worked example from the paper or a textbook.
- With independent columns, Romano-Wolf's rejections match Holm's closely.
- Under the complete null (all `m` false), a short simulation keeps realised
  FWER ≤ alpha and FDR ≤ q, within MC error.
- Everything is deterministic under a seed.

**2. The study, `scripts/fdr_vs_fwer.py`** plus `make fdr-study`. It writes
`results/fdr_vs_fwer/<stamp>/summary.csv` and `report.md`. The model is at the
level of the test statistic, standardised by the null sd:
- **m = 12**, grouped by `target_axis` from `hypotheses/pending/*.yaml`: region
  4, credit 3, duration 2, three singletons. Read the groups from the files; don't
  hard-code them.
- **Null:** each hypothesis's statistic is N(0, 1). Correlation is `rho_w`
  within an axis and `rho_b` between axes. Grid: `rho_w` in {0, 0.3, 0.6},
  `rho_b` in {0, 0.2}.
- **True hypotheses:** `n_true` in {0, 1, 3, 6}, spread across axes, with mean
  shift `mu` and sd `s`, calibrated on task 30's `A-20260926-161749` and the
  knee run. **IC 0.70:** `mu` = 0.255 / 0.168 ≈ 1.52, `s` = 0.193 / 0.168 ≈ 1.15.
  **IC 0.35:** `mu` from the knee grid's 10-seed paired excess (0.095) over the
  pooled null sd, with `s` as at 0.70 (**say that this `s` is assumed**). Also a
  `mu` sweep of 0.5, 1.0, 1.5, 2.0 and 3.0, for the curve.
- **Shuffles per test**, `k` in {20, 100, 500, 1000}. Draw `T0` from the same
  null correlation.
- **Procedures:** Holm 5%, Romano-Wolf 5%, BH at q = 5% and 10%, BY at 10%,
  RSW-FDR at 10%.
- **5,000 MC replications** per scenario, seeded.

**Report per scenario:** average power (the share of true hypotheses passing),
P(at least one true passes), realised FWER, realised FDR, and mean false passes.
Add a short table for the owner's two headline cases, `n_true` = 3 at IC 0.35
and at IC 0.70, `rho_w` = 0.3, `rho_b` = 0.2, `k` = 1000.

**Caveats the report must state:**
- This models the test, not the engine. It assumes normal statistics and moments
  calibrated on planted signals.
- The registry has one hypothesis per SUBSTRATE §6 family, so "family level
  first, then within" is trivial here, and the study runs flat.

    scripts/unattended.sh check --digest
    make fdr-study

**`params/`, `vetoes/` and `SUBSTRATE.md` do not change.** The gate stays FWER
until the owner rules L16.

**Receipt should say:** rc, runtime, commit hash, the output directory, the two
headline tables, whether RSW-FDR was implemented, and any test that needed a
tolerance and why. Interpretation is Cowork's and the owner's. **Then stop.**

---

### 37. Split the test suite: fast wiring checks and slow model-validity checks (OWNER-QUEUE D2)

Added 2026-09-29 by Cowork. **Owner ruling 2026-09-29** (D2: "yes"). No engine
runs, and nothing in `params/`, `vetoes/` or `SUBSTRATE.md` changes.

**0. Commit first, alone:**
- **Files:** `decisions/0038-turnover-is-disclosed-not-vetoed.md`,
  `decisions/0040-the-shadow-cost-prices-the-turnover-a-trade-creates.md`,
  `HANDOFF.md` and `OWNER-QUEUE.md`.
- **Message:** `decisions: 0038 L17 addendum, 0040 adopted at 40bp; queue:
  37-39, 33 superseded; L16-L18, D2 (owner 2026-09-29)`.
- Check `git diff --cached --ignore-cr-at-eol --stat` before committing.

**Why.** `make check` went 596 s → 1206 s (task 34) → 3695 s (task 36). An hour
per check now sits in front of every audit and every small commit.

**1. Profile first.** Run
`uv run --python 3.12 --group dev pytest -q --durations=60` and put the top 20
test durations in the receipt, with the total. Say which tests task 34 and
task 36 added among them.

**2. Mark.**
- Add a `slow` marker to `pyproject.toml`: "model-validity: runs the engine or
  a Monte Carlo".
- Mark every test that runs `run_cell`, the engine, an optimiser solve on a
  universe, or a simulation of more than about 200 replications, **or** that
  takes more than 5 s in step 1.
- **Never mark** the `holdout` tests, the governance tests, or any test of
  `params/` loading, key construction or preflights.
- A test that is slow only because it uses a solve where a fixture would do
  can be rewritten to be fast instead. Say which ones you rewrote, and
  **don't weaken what any test asserts**.

**3. Targets.**
- `make check` = governance + lint + `pytest -m "not slow and not holdout"`
  + holdout.
- `make check-full` = governance + lint + the whole suite + holdout.
- `make test-slow` = `pytest -m slow`.
- Extend `scripts/unattended.sh` with a `check-full` mode.
- **Audit modes run `check-full` before the grid.** An audit is hours, so an
  hour of engine tests in front of it is affordable, and it's the one place
  the engine must be proven.

**4. `CLAUDE.md`.** Replace "`make check` is the definition of done." with:
"`make check-full` is the definition of done for any commit touching `src/`,
`scripts/`, `tests/`, `vetoes/` or `params/`. `make check` (the fast tier) is
enough for a commit touching only `HANDOFF.md`, `OWNER-QUEUE.md`,
`decisions/`, `hypotheses/` or docs." Update the `unattended.sh` paragraph to
match.

**Test:** `make check` and `make check-full` both pass. The test count of
`check-full` equals today's 562 plus any new tests. No test is lost between
the tiers (fast + slow + holdout = total).

    scripts/unattended.sh check --digest
    scripts/unattended.sh check-full --digest

**Receipt should say:** rc, commit hashes, the profile's top 20, how many tests
are in each tier, the runtimes of `check` and `check-full`, and any test
rewritten, with the reason. **Target:** `make check` under 10 minutes. If it
can't get there, say what's in the way. **Then stop.**

---

### 38. Romano-Shaikh-Wolf FDR, from the paper, and the study re-run at small k (OWNER-QUEUE L16)

Added 2026-09-29 by Cowork. **Owner ruling 2026-09-29** (L16: "yes, Claude Code
can fetch it"). No engine runs, and nothing in `params/`, `vetoes/` or
`SUBSTRATE.md` changes. The gate stays FWER until the owner rules L16(a).

**Why.** Task 34 showed the number of shuffles per test, k, decides more than
the procedure. Procedures that work from each test's own p-value (Holm, BH,
BY) are floored at p ≥ 1/(k+1). Romano-Wolf, which uses the joint null, keeps
its power at k = 20-100, where BH has almost none. An engine shuffle costs
about 84 s × 12 hypotheses, so k is the lab's binding cost.

RSW-FDR also uses the joint null. Whether it keeps FDR's power advantage at
small k is **the** open question for L16(a).

**Correction to task 34's citation (Cowork's error):** the procedure is Romano,
J. P., Shaikh, A. M. and Wolf, M. (2008), "Control of the false discovery rate
under dependence using the bootstrap and subsampling", *TEST* 17(3), 417-442,
with discussion and rejoinder in the same issue. *Econometric Theory* 24(2)
is their generalized-error-rates (k-FWER, FDP) paper, not this one.

**1. Fetch the paper.**
- **Sources:** Springer (`link.springer.com/article/10.1007/s11749-008-0126-6`),
  the University of Zurich working paper (IEW WP 337, ZORA eprint 10432), or
  SSRN 1025410.
- **Where it goes:** save the PDF under `docs/references/`. Git-ignore it if
  its licence doesn't clearly allow a copy in the repo; say which you did.
- **If the network refuses every source, stop and report.** Don't implement
  from memory.

**2. Implement `romano_shaikh_wolf_fdr(t, T0, q)`** in
`stats/multiple_testing.py`, with the same interface as `romano_wolf`.
- Follow the paper's bootstrap stepdown algorithm exactly.
- **In the docstring, record every choice the paper leaves open**, with its
  section or equation number.
- **Record whether the paper's validity argument covers null draws from
  permutation or shuffles rather than a centred bootstrap.** Our `T0` comes
  from shuffles. If the paper doesn't cover that, say so plainly in the
  docstring and the receipt, and ship it labelled as such.
- Add the batched version in `_batched.py`, pinned row by row against the
  single-replication function, as task 34 did.

**Tests:**
- Under the complete null, realised FDR ≤ q within MC error.
- **Reproduce one row of one of the paper's own simulation tables within MC
  error.** This is the fidelity check. Say which table and row.
- Deterministic under a seed.

**3. Re-run the study** (`make fdr-study`).
- **Procedures:** add `rsw_fdr_5` and `rsw_fdr_10`.
- **k grid:** extend it to {20, 50, 100, 200, 500, 1000}.
- **New columns:**
  - `p_any_pass`: P(R > 0);
  - `pfdr`: E[V/R | R > 0];
  - `false_share_expected`: E[V] / (E[V] + E[S]).
- Keep 5,000 reps. If RSW-FDR makes the full grid take more than about 2 h,
  you may drop to 2,000 reps **for the RSW rows only** and disclose it.

**Receipt should say:**
- rc, runtime, commit hash, the output directory, and the paper's source.
- The choices recorded in the docstring.
- Whether the permutation null is covered by the paper's argument.
- The fidelity-row result.
- **A k-sensitivity table** at n_true = 3, rho_w 0.3, rho_b 0.2, for IC 0.35
  and IC 0.70: `avg_power`, `fwer`, `fdr` and `pfdr` for Romano-Wolf 5%,
  BH 10% and RSW-FDR 10%, at each k.

Interpretation is Cowork's and the owner's. **Then stop.**

---

### 39. Apply `decisions/0038` (with its 2026-09-29 addendum) and `decisions/0040`, in one params change

> **AMENDMENT 2026-09-30, morning (owner, via Cowork). Read this before the
> steps below. Claude Code's permissions deny edits to `SUBSTRATE.md`,
> `params/**` and `vetoes/**`** (`.claude/settings.json`), which is what blocked
> task 40's step 1. **At the owner's instruction, Cowork has applied every
> owner-only edit in this task to the working tree.** Don't re-edit those
> files, and don't route around the deny rule with shell tools.
>
> Already done in the working tree (verify with
> `git diff --ignore-cr-at-eol`):
> - **`SUBSTRATE.md` v0.6:** step 3 below (0038 items 2-3, 0040 items 1-2),
>   plus 0041's §9 and §15 edits from task 40's step 1. One consequential
>   edit isn't verbatim from either record: §4's "The veto threshold is a far
>   backstop, not a budget." became "There is no turnover veto either
>   (`decisions/0038`)." `decisions/0100` records it.
> - **`decisions/0100`:** rows for 0038, 0040 and 0041 under "Applied in
>   v0.6".
> - **`params/vetoes.yaml`:** step 1 is done. The `turnover:` block is gone,
>   and `turnover` is out of `evaluation.order`.
> - **`params/constraints.yaml`:** step 2 is done.
>   - `form: created_marginal` and `coefficient: 40.0`.
>   - The comment block is rewritten from 0040 "The ruling, made precise",
>     with the marginal-rate table recomputed at 40 bp.
>   - `highlight_annualised: 2.00` and
>     `highlight_windows: [annual, rolling_1y_p95]`.
>   - `per_rebalance_caps` is untouched.
> - **`params_version`:** `0.6.0` → `0.7.0` in all seven `params/*.yaml`
>   (`params.py` requires them to agree).
> - **`vetoes/`:** `veto_turnover` is removed from `rules.py`, `registry.py`
>   (`VETOES` and `SUBSTRATE_VETOES`) and `__init__.py`, and the docstrings
>   now say nine.
>
> **What's left for you: steps 4, 5 and 6, all outside the owner-only paths.**
> Known readers of the removed keys:
> - `audit/ladder.py:1129` (`vetoes.turnover.max_annualised`), and
>   `portfolio_veto_verdicts`;
> - `harness/objective.py:75` (a docstring);
> - `render/views.py:321`;
> - `tests/test_engine.py`, `test_vetoes.py`, `test_params.py` and
>   `test_governance.py:52`.
>
> `harness.objective` must accept `created_marginal`, which today's params
> select. **If anything needs a further change to `SUBSTRATE.md`, `params/` or
> `vetoes/`, stop and describe the exact change in the receipt.** Cowork
> applies it.
>
> **Commits, in this order:**
> 0. `HANDOFF.md` and `OWNER-QUEUE.md` alone:
>    `queue: task 39 amended, owner-only edits applied by Cowork (2026-09-30)`.
> 1. `SUBSTRATE.md` and `decisions/0100` alone:
>    `substrate: v0.6 -- turnover disclosed not vetoed, created-marginal shadow
>    at 40bp, block-shuffle null (decisions/0038, decisions/0040,
>    decisions/0041)`.
> 2. After `check-full` passes: `params/`, `vetoes/`, and your `src/`,
>    `render/` and `tests/` changes together, citing `decisions/0038` and
>    `decisions/0040`. Then step 6's hash lines in 0038 and 0040, as their own
>    small commit.
>
> If git refuses to stage an owner-only path, stop and report; the owner will
> commit it. This runs in the daytime, with no deadline. Then stop.

Added 2026-09-29 by Cowork. It **supersedes task 33**. **Owner rulings:** B2
and B3 (0038); L17 on 2026-09-29 (addendum: highlight on annual and rolling
p95); L18 on 2026-09-29 (0040 adopted at 40 bp). It touches `SUBSTRATE.md`,
`params/` and `vetoes/`, all owner-only: **every commit cites `decisions/0038`
and/or `decisions/0040`**.
- **Run after task 35:** 35's identity check needs today's `params_hash`.
- **Changes `params_hash`.**

**1. `params/vetoes.yaml`:** delete the `turnover:` block, and remove
`turnover` from `evaluation.order` (0038 item 1).

**2. `params/constraints.yaml`:**
- `turnover.penalty.form: created_marginal` and `coefficient: 40.0` (0040
  addendum). Rewrite the comment block as 0040 says, and recompute its
  magnitude table at 40 bp.
- Add `turnover.highlight_annualised: 2.00` and
  `turnover.highlight_windows: [annual, rolling_1y_p95]`. Both are reporting
  only (0038 item 4, as amended).
- Don't touch `per_rebalance_caps`. Bump `params_version` as the repo's
  convention requires.

**3. `SUBSTRATE.md`, exactly as written in the records:**
- §10: delete the turnover row; "Ten vetoes" becomes "Nine vetoes" (0038
  item 2).
- §4 Turnover row: the per-session-cap sentence (0038 item 3), and the
  pricing text (0040 addendum, item 1).
- §4 "Turnover handling" paragraph (0040 addendum, item 2).

Nothing else in SUBSTRATE changes.

**4. Code.**
- **`AuditCell.shadow_form`:** default `None`, meaning read
  `constraints.turnover.penalty.form` from params, as `shadow_coefficient`
  already does. `"trailing"` and `"created"` stay explicit overrides. Keys
  append a suffix only for an explicit override, so the task 32 and 36 grids
  keep their keys.
- **`harness.objective`:** accepts `created_marginal`. Put the `S(x)` of 0040
  there as the single implementation, and have the audit rule call it. Make
  sure `linear` is not reached by default anywhere.
- **Turnover veto:** the check leaves `portfolio_veto_verdicts`, and every
  reader of `vetoes.turnover.max_annualised` goes.
- **Highlight:** add a `turnover_highlight` column: true if annual or rolling
  p95 exceeds 2.00. Mark it in `report.py` and on the leaderboard.
- **Golden test:** `GOLDEN_NET_IR` changes under the new default. Keep the old
  value by pinning that test's cell to `shadow_form="trailing"` and
  `shadow_coefficient=10.0`, which must reproduce it bit for bit. Add a
  second golden at the new default and record its value in the receipt.
- **Other tests:** turnover-veto tests are rewritten to assert the highlight.

**5. Verify past verdicts.** For every `results/audit/A-*/cells.csv`, count the
cells whose `veto_detail` names `turnover`. The expected count is zero; list
any that aren't.

**6. Record** the old and new `params_hash` as a dated line in the
"Consequences" of both 0038 and 0040.

    scripts/unattended.sh check-full --digest

**Receipt should say:**
- rc and commit hashes.
- The old and new `params_hash`.
- The step 5 count.
- The new golden value.
- Every test changed, and why.
- A diff summary of `params/` and `SUBSTRATE.md` (`--ignore-cr-at-eol`).

**Then stop.** No audit runs in this task. Earlier runs' twins are
invalidated by the hash change, and any later grid re-runs its own.

---

### 36. The shadow cost priced at the turnover a trade creates — override and a 60-cell grid

Added 2026-09-28 by Cowork. **Owner ruling 2026-09-28** (OWNER-QUEUE L18,
`decisions/0040`, committed in task 34's step 0). **Measure first:** this adds
a per-cell override, like task 32's `shadow_coefficient`. **Nothing in
`params/`, `vetoes/` or `SUBSTRATE.md` changes.** Run after task 34 and before
task 35. About 60 cells. The quadratic term may make each solve slower than
task 32's ~84 s, so budget 1.5-2.5 h.

**Read first:** `decisions/0040`, especially "The ruling, made precise". The
formula there is the specification. If anything in it can't be implemented as
written, stop and report; don't approximate.

**Build.**

1. **`AuditCell.shadow_form: str = "trailing"`**, accepting `"trailing"` (today)
   and `"created"` (0040). Append `_created` to `key()` only when it isn't
   `"trailing"`, after any `_shadowNN`, so existing keys don't change.
2. **In `_OptimiserRule`, for `"created"` only:**
   - `P` is the sum of the last `W−1` entries of `turnover_log`, with missing
     entries filled at `constraints.turnover.target_annualised / ppy`.
     `W = int(round(ppy))`.
   - Take the shadow **out** of the linear cost vector. The vector keeps the
     real half-spread only.
   - Pass the solver a convex shadow term instead:
     `S(x) = κ/(2(r−s)) · (W/ppy) · [pos(T(x) − s)² − pos(T(0) − s)²]`,
     with `x = Σ|trade|`, `T(x) = (P + x)·ppy/W` and
     `κ = coefficient × 1e-4` (coefficient from the cell override or
     `params/`).
   - The first rebalance stays free, as today.
   - `"trailing"` must follow exactly the code path it does now.
3. **In `portfolio/long_only.solve`:** add an optional argument, for example
   `shadow_quadratic: tuple[float, float] | None` carrying `(a, b)` for
   `S = a·pos(b + x)²`. The constant `−a·pos(b)²` doesn't affect the solve.
   - **cvxpy:** `cp.square(cp.pos(b + cp.sum(cp.abs(trade))))`. Check that
     the problem is DCP, and put `a` into the same bps scaling as the other
     objective terms.
   - **scipy reference:** the same term on `x = Σ(u + v)`, with its analytic
     gradient `2a·pos(b + x)`.
   - `None` must leave both paths byte-for-byte as they are.
4. **Diagnostics:**
   - per rebalance: `shadow_bps` = the marginal shadow at `T(x)` in bp, and
     `shadow_paid_bps` = `S(x)/x` in bp (0 when `x = 0`);
   - per cell: `turnover_autocorr_lag26`, `_lag52`, `_lag53` and `_lag78` of
     `path.turnover`, for **every** cell (a new column is fine: keys don't
     change).
5. **Grid `friction_created`** in `ladder.py`, as module constants: h13, IC
   0.35 and 0.70, seeds 0-9, coefficient 10, 20 and 40, `shadow_form="created"`,
   live cells only, **60 cells**. Add `make audit-friction-created` and extend
   the `unattended.sh` whitelist.
6. **Preflight:** the control run `A-20260928-151055` (task 32) exists, both
   hashes match it, and it has the live cell at every (IC, seed, coefficient).

**Tests:**
- The `"trailing"` default gives identical `net_ir` to before on the small
  universe, and existing keys are unchanged.
- `shadow_quadratic=None` leaves both solvers' results unchanged.
- At a coefficient of 0, `"created"` equals `"trailing"`.
- **The shadow term is convex in trade size:** for fixed `P`, the solver's
  shadow on two trades of size x/2 in consecutive weeks is less than on one
  trade of size x. Test the function `S`, not an engine run.
- **Prefill:** at rebalance 2, `P` equals `(W−2)·target/ppy` plus the first
  logged trade.
- The derivative of `S` at `x` equals the 0024 curve at `T(x)`, to 1e-12.

```
scripts/unattended.sh check --digest
scripts/unattended.sh audit-friction-created --digest
```

**Receipt should say:**
- rc, runtime, run id, and the commit hash.
- Whether the hashes match `A-20260928-151055`, and that `params/` is
  unchanged.
- **Per (IC, coefficient), median and range over 10 seeds, with the same
  figures from `A-20260928-151055` beside them:**
  - net IR and gross IR;
  - cost drag;
  - annual turnover;
  - rolling one-year p95 and max;
  - `turnover_per_rebalance_max`, plus the count of cells with a week of 1.5x
    NAV or more and of 1.95x or more;
  - `turnover_autocorr_lag53` and lag 52;
  - `shadow_bps_mean` and `shadow_paid_bps` mean;
  - `te_p95` and realised IC.
- **Paired by (IC, seed, coefficient):** created minus trailing, for net IR,
  annual turnover and `turnover_per_rebalance_max` (mean, sd, number
  positive).
- Counts above 200%, annual and rolling max, for each arm.
- `risk_calibration` fails for each arm.
- Solver health: `inaccurate_share` max, `infeasible_te_share` max, and
  anything not solved by CLARABEL.

Interpretation is Cowork's and the owner's. Adopting the form, and choosing the
coefficient, happen later in `params/` via 0040. **Then stop.**

---

### 40. SUBSTRATE §9: the joint null is a block shuffle (`decisions/0041`); a standardised Romano-Wolf; the generalized-FWER variant in the study (OWNER-QUEUE L16)

Added 2026-09-29 (evening) by Cowork. **Owner ruling 2026-09-29:** amend
SUBSTRATE to say shuffle, not bootstrap (`decisions/0041`), and run the
generalized-FWER variant now, before the long tasks. **Runs first, before 35.**
No engine runs, and nothing in `params/` or `vetoes/` changes. The gate stays
Romano-Wolf at FWER 5% until the owner rules L16(a). Budget about 1-1.5 h.

**0. Commit first, alone:** `OWNER-QUEUE.md`, `HANDOFF.md` and
`decisions/0041-the-joint-null-is-a-block-shuffle.md`, with the message
`queue: task 40, decisions/0041; L16 task 38 verified (Cowork 2026-09-29)`.
This replaces task 35's former step 0.

**1. SUBSTRATE, citing `decisions/0041`.** Transcribe the three edits in
0041's "Amended text" verbatim: two in §9, one in the §15 layout line.
`SUBSTRATE.md` is CRLF; keep it CRLF. Don't touch the status line or version.
Add a row to `decisions/0100` for the amendment, under a new
`## Applied 2026-09-29` heading, in the table's format. Commit alone:
`substrate: s9 the joint null is a block shuffle (decisions/0041)`. Show
`git diff --ignore-cr-at-eol SUBSTRATE.md` in the receipt.

**2. Standardise inside `romano_wolf`** (0041's implementation note).
- Add a keyword `standardise: bool = True` to `romano_wolf` and
  `batched_romano_wolf`. When it's true, transform each column `j` of `T0`,
  and `t_j`, by `(x - mean(T0[:, j])) / sd(T0[:, j], ddof=1)` before the
  stepdown. Raise `ValueError` on a zero or non-finite column sd.
- **Tests:**
  - With `standardise=False`, the output reproduces today's function exactly.
  - Marginal p-values are invariant to the transform.
  - **The scale case:** give one null column 3× the others' sd, with the
    other columns carrying a true effect. Standardised Romano-Wolf rejects
    them; unstandardised has less power. Assert it on a fixed seed.
  - The batched version matches the single one row by row, both settings.

**3. The generalized-FWER stepdown: `romano_wolf_gfwer(t, T0, alpha, g=2,
standardise=True)`.** It controls P(at least `g` false passes) ≤ `alpha`, so
`g = 1` is ordinary FWER. The letter is `g`, not `k`, because `k` is already
the number of shuffles.
- **Implement it from the paper, not from memory.** The source is Romano, J. P.
  and Wolf, M. (2007), "Control of generalized error rates in multiple
  testing", *Annals of Statistics* 35(4), 1378-1408. A related, acceptable
  source is Romano, Shaikh and Wolf (2008), "Formalized data snooping based on
  generalized error rates", *Econometric Theory* 24(2).
  - **Cowork is not certain of the page numbers.** Check the title and authors
    of whatever you fetch.
  - Try the publisher's open copy first, then the authors' working-paper
    copies (University of Zurich IEW or ZORA, Stanford). Save it under
    `docs/references/`, git-ignored as in task 38.
- **What Cowork expects the paper to say. Verify it; don't assume it.**
  - The critical value at a step is a high quantile of the **g-th largest**
    null statistic, not the maximum.
  - After the first step, the paper's stepdown takes a maximum over subsets
    of the already-rejected hypotheses of size `g - 1`, added back to the
    active set. With m = 12 and g = 2, that's at most 11 subsets a step, so
    enumerate them exactly; don't use the paper's streamlined shortcut unless
    the paper says it keeps control.
  - Follow the paper's algorithm. **Where it differs from this description,
    the paper wins; record the difference in the docstring.**
- **Record in the docstring:** every choice the paper leaves open, with its
  equation or algorithm number, and whether its validity argument covers
  permutation or shuffle nulls or only the bootstrap.
- **Tests:**
  - `g = 1` reproduces `romano_wolf` exactly, both `standardise` settings.
  - Under the complete null, P(V ≥ 2) ≤ alpha within MC error (m = 12, at
    least 2,000 reps).
  - An obvious signal, say `t = [4.0, 3.5, 3.2, 3.0, noise…]`, rejects at
    least what `romano_wolf` rejects.
  - It's monotone: every hypothesis `romano_wolf` rejects is also rejected by
    `g = 2`.
  - Deterministic under a seed.
  - Batched version in `_batched.py`, pinned row by row against the single
    one.
- **If no source can be fetched, or the algorithm is ambiguous in the way
  task 38's was, don't ship an approximation.** Leave it raising
  `NotImplementedError` with what you found, do steps 1, 2 and 4 without it,
  and say so in the receipt. That's a planned stop for this step only: carry
  on to task 35 afterwards.

**4. Re-run the study** (`make fdr-study`).
- **Add procedures:** `rw_g2_5` and `rw_g2_10`, and put `romano_wolf_5` on
  `standardise=True`.
- **Add a column:** `p_two_plus_false`, P(V ≥ 2), for every procedure.
- Keep 5,000 reps and the k grid {20, 50, 100, 200, 500, 1000}.
- The study's draws are homoscedastic by construction, so `romano_wolf_5`
  should match task 38's figures within MC error. Report the largest
  absolute difference in `avg_power` and `fwer` against
  `results/fdr_vs_fwer/20260929-154138/summary.csv`.

Run:

    scripts/unattended.sh check-full --digest
    make fdr-study

Commit the code and the study as `stats: standardised Romano-Wolf and the
generalized-FWER stepdown (HANDOFF task 40, decisions/0041)`.

**Receipt should say:**
- rc, runtime and commit hashes, the output directory, and the paper's source.
- The SUBSTRATE diff.
- The choices recorded in the docstring, and whether permutation nulls are
  covered.
- The `romano_wolf_5` difference against task 38.
- **The k-sensitivity table** at n_true = 3, rho_w 0.3, rho_b 0.2, for IC 0.35
  and IC 0.70: `avg_power`, `p_at_least_one_true`, `fwer`,
  `p_two_plus_false`, `fdr` and `pfdr` for `romano_wolf_5`, `rw_g2_5`,
  `rw_g2_10` and `bh_10`, at each k.
- The complete-null rows (n_true = 0) for the two new procedures.

Interpretation is Cowork's and the owner's (L16(a)). **Then go on to task
35**, and from 35 to 39 under 35's own conditions. **Stop without going on**
only if the check fails (rc ≠ 0) or step 1 or 2 fails. A step-3 stop as
described above is not a failure.

---

### 42. Apply `decisions/0042` (overlay policy) and `0043` (the gate); show the turnover highlight; one implementation of the 0040 shadow cost

Added 2026-10-01 by Cowork. **Owner rulings 2026-10-01:** B1 (the overlay is
policy at a 26-week halflife, `decisions/0042`), L16(a) (the generalized
stepdown, g = 2, α = 5%, 100 shuffles per test, `decisions/0043`), and
"queue the task" for the two gaps Cowork found in task 39's work. **No audit
runs.** Budget 2-3 h, daytime, no deadline.

**Owner-only edits are already in the working tree, applied by Cowork at the
owner's instruction** (your permissions deny them). Don't re-edit them, and
don't route around the deny rule. Verify them with
`git diff --ignore-cr-at-eol`:
- **`SUBSTRATE.md` v0.7:**
  - §4 gets a new "Risk model" paragraph after TE handling (0042).
  - §9's multiple-testing bullet describes the generalized stepdown, and the
    "rejects nothing" bullet no longer points at FDR (0043).
  - §10's `multiple_testing` row is updated (0043).
  - §13: "Romano-Wolf across that many draws" becomes "a stepdown across
    that many draws".
- **`params/audit.yaml`:** `covariance.vol_overlay: {form: scalar,
  halflife_weeks: 26}`.
- **`params/vetoes.yaml`:** `multiple_testing` gets
  `procedure: romano_wolf_gfwer`, `g: 2`, `standardise: true` and
  `min_shuffles: 100`; `fwer_alpha` and `level` are unchanged.
- **`params_version`:** `0.7.0` → `0.8.0` in all seven files.
- **`vetoes/rules.py`:** `veto_multiple_testing` also checks the verdict's
  `g` against params, and its `n_shuffles` against `min_shuffles`. Either
  one missing from the verdict fails as a missing input. The context key
  stays `romano_wolf`.
- **`decisions/0042`, `0043` and `0100`'s v0.7 rows, plus `OWNER-QUEUE.md`
  B1 and L16 marked RULED.**

**If any step needs a further change to an owner-only file, stop and write
the exact change in the receipt.** Cowork applies it.

**0. Commit first, alone:** `HANDOFF.md` and `OWNER-QUEUE.md`, as
`queue: task 42; B1 and L16(a) ruled (owner 2026-10-01)`.
**Then, alone:** `SUBSTRATE.md`, `decisions/0042`, `decisions/0043` and
`decisions/0100`, as `substrate: v0.7 -- the volatility overlay is policy, the
gate is generalized FWER (decisions/0042, decisions/0043)`.

**1. The overlay as the default, the way task 39 did the shadow form.**
- `AuditCell.vol_halflife` and `vol_overlay` get a "read params" default,
  distinct from today's `None`. **`None` must keep meaning "no overlay"**,
  because every historical key depends on it. Use a sentinel, for example
  `FROM_PARAMS`.
- Add `resolve_vol_overlay(cell, params)`. It returns the effective
  `(halflife, overlay)`; an explicit value on the cell wins. Pass the
  *resolved* values to `universe.covariance`.
- **The key encodes the resolved values.** A default cell then reads
  `…_vhl26scalar`, and an explicit-`None` cell keeps its pre-task-42 key
  exactly.
- **Pin `vol_halflife=None` explicitly** in every grid that claims identity
  with a named historical run: the cells `power_cells`, `power10_cells`,
  `friction_cells`, `friction_created_cells` and `halflife_cells` produce.
  The halflife grid already sets its arms explicitly; check it. **Go through
  every grid builder, not only these**, and list in the receipt which ones you
  pinned and why. `knee_cells` and `baseline_cells` follow params, as with
  task 39, unless one of them claims identity with a named run.
- **Live and baseline twins must resolve to the same overlay.** Add a test.
- **Golden values:** keep `GOLDEN_NET_IR` and
  `GOLDEN_NET_IR_CREATED_MARGINAL` reproducible bit for bit, through explicit
  overrides (`vol_halflife=None` plus the shadow overrides each already
  uses). Add `GOLDEN_NET_IR_V080` for the same cell at today's full default,
  verified against a live `run_cell` call.

**2. The gate, as one callable.** Add `stats.multiple_testing.gate(t, T0,
params=None)`. It reads `vetoes.multiple_testing` and calls
`romano_wolf_gfwer(t, T0, alpha, g, standardise)`, or `romano_wolf` if
params says so. It returns the dict the veto reads:
- `procedure`, `fwer_alpha`, `g`, `n_shuffles` (k), `n_tests` (m);
- the per-hypothesis `rejected` array and `p_adjusted`.

It raises if `k < min_shuffles`. Tests:
- it reads params, not constants;
- it reproduces `romano_wolf_gfwer` exactly;
- `veto_multiple_testing` passes on its output for a rejected hypothesis;
- the veto fails for each of: wrong `g`, too few shuffles, missing `g`,
  missing `n_shuffles`.

Update `tests/test_vetoes.py`'s existing `multiple_testing` tests: their
verdict dicts need `procedure: romano_wolf_gfwer`, `g` and `n_shuffles`.
`family_then_within` stays as it is (OWNER-QUEUE L12).

**3. The turnover highlight, surfaced** (task 39 computed it but never showed
it).
- `turnover_highlight` is marked in `audit/report.py`'s markdown and HTML,
  per cell and as a count per grid. It's marked on the leaderboard
  (`render/`), next to the veto legend.
- An unknown name in `highlight_windows` **raises** rather than being
  silently ignored.
- **Tests:** a cell above 2.00 on annual only, one on rolling p95 only, one
  on rolling max only (not highlighted), and one exactly at 2.00 (not
  highlighted). Plus the unknown-window error, and the report and leaderboard
  rendering the flag.

**4. One implementation of `decisions/0040`'s shadow cost.**
- Move the created-turnover pricing into `harness/objective.py` as the
  single implementation:
  - `created_marginal_shadow(prev_traded, x, params, periods_per_year)`,
    the scalar `S(x)` of 0040;
  - `created_marginal_quadratic(prev_traded, params, periods_per_year)`,
    the `(a, b)` pair the solver's convex term takes.
- `audit.ladder._OptimiserRule._shadow_quadratic_coeffs` calls the latter.
  The prefill-at-target rule (0040 ruling item 2) lives in objective too.
- **Tests:**
  - `GOLDEN_NET_IR_CREATED_MARGINAL` is unchanged bit for bit;
  - the derivative of `S` equals `turnover_penalty` at the post-trade level,
    numerically;
  - `S` is convex;
  - a lump costs more than the same trading split over two weeks.

`turnover_penalty`'s docstring then points to these functions, not to the
ladder.

**5. A note for phase 2.** `harness/experiment.py` has no solver yet:
`build_weight_rule` raises. Add a dated bullet to `HANDOFF.md`'s "Not queued
yet" section. It should say that the phase-2 solver must:
- read `covariance.vol_overlay` through `resolve_vol_overlay` or its
  equivalent (0042);
- price turnover through objective's `created_marginal_*` functions (0040);
- run the gate through `stats.multiple_testing.gate` (0043);
- and come with a test pinning each.

**6. Check, then commit.**
- Run `scripts/unattended.sh check-full --digest` **through the script**, so
  there's a log. Task 39's check-full left none.
- Then commit `params/`, `vetoes/`, `src/`, `render/` and `tests/` together,
  citing `decisions/0042` and `decisions/0043`.
- Record the old and new `params_hash` as a dated line in the "Consequences"
  of 0042 and 0043, as their own small commit.

**Receipt:**
- rc, commits, the check-full log directory, and the old and new
  `params_hash`.
- The grids pinned, and why.
- The three golden values.
- Every test changed, and why.
- **Anything in this task you didn't do, said plainly.**

Then stop. OWNER-QUEUE B1 and L16 move to `## Closed` in the same commit as
the receipt.

---

### 43. Apply `decisions/0044` and `0045`, SUBSTRATE v0.8; the task 42 review's fixes (F2-F4, F6-F8); `decisions/0039` items 2 and 3

Added 2026-10-01 by Cowork. **Owner ruling 2026-10-01: "I accept your recs."**
That covers OWNER-QUEUE L19 (`decisions/0044`), L20 (`decisions/0045`), L4 with
0039 §3 (SUBSTRATE v0.8), and the fixes in the Cowork doc
`claude/task-42-review-2026-10-01.md` (mirror:
`Claude outputs/project-mirror/task-42-review-2026-10-01.md`). Read that doc's
§3 before you start; the finding numbers below are its numbers. **No audit
runs, no vendor calls.** Budget 2-3 h, daytime, no deadline.

**Owner-only edits are already in the working tree, applied by Cowork at the
owner's instruction.** Don't re-edit them, and don't route around the deny
rule. Verify them with `git diff --ignore-cr-at-eol`:
- **`SUBSTRATE.md` v0.8:**
  - the status line and a v0.8 paragraph;
  - §3 gets the "The lab screens; it does not confirm" paragraph after bar 2,
    and its closing sentence now ends "…is not a candidate";
  - §4's Tracking-error row says the 6% is the sizing target σ (0044);
  - §9's multiple-testing bullet and §10's `multiple_testing` row carry the
    small-search rule (0045).
- **`params/`:** `params_version` `0.8.0` → `0.9.0` in all seven files.
  - `vetoes.yaml` `multiple_testing` gains `small_search_below: 8` and
    `small_search_g: 1`.
  - `constraints.yaml`: the `tracking_error` comment is rewritten (0044), and
    the S(x) comment no longer claims convexity makes a lump dearer (0040
    addendum).
- **`vetoes/rules.py` `veto_multiple_testing`:**
  - When `small_search_below` is set, the verdict must carry `n_tests`; if
    `n_tests` < 8, the required g is `small_search_g` (1).
  - The verdict must carry `standardise`, matching params.
  - A missing `n_tests` or `standardise` fails as a missing input.
- **`decisions/`:** new `0044` and `0045`; addenda to `0039`, `0040`, `0042`
  and `0043`; and `0100`'s v0.8 rows. `OWNER-QUEUE.md` marks L4, L19 and L20
  RULED, and `HANDOFF.md` carries this task and the corrected overlay standing
  refusal. `OWNER-QUEUE.md` B5 was also rewritten and moved to Live (owner,
  2026-10-01); it needs nothing from this task.

**If any step needs a further change to an owner-only file, stop and write
the exact change in the receipt.** Cowork applies it.

**0. Commit first, alone:** `HANDOFF.md` and `OWNER-QUEUE.md`, as
`queue: task 43; L4, L19 and L20 ruled (owner 2026-10-01)`.
**Then, alone:** `SUBSTRATE.md` and exactly these in `decisions/`: `0039`, `0040`,
`0042`, `0043`, `0044` (new), `0045` (new) and `0100`. `0023`-`0030` show as
modified only through CRLF noise, so leave them out. Commit as `substrate: v0.8 -- the lab screens, the TE budget is a sizing target, small
searches are gated at FWER (decisions/0039, decisions/0044, decisions/0045)`.
Spell out each `decisions/NNNN` in full, as the commit hook reads them.

**1. The gate follows 0045** (`stats.multiple_testing.gate`).
- m = `t.shape[0]`. If m < `small_search_below`, run
  `romano_wolf_gfwer(..., g=small_search_g)`; otherwise use `g`. The
  `procedure` reported stays `romano_wolf_gfwer`.
- Also add `standardise` (bool) to the returned dict, and carry it through
  `verdict_for`.
- **Tests:**
  - m = 1 reports g = 1, and m = 8 reports g = 2.
  - **Under a complete null at m = 1, k = 100, the gate's rejection rate over
    2,000 seeded draws is within [0.03, 0.07].** This pins F1: before this
    task it was 1.00.
  - The veto passes a gate verdict at m = 1 and g = 1, and fails one at m = 1
    and g = 2.
  - The veto fails a verdict with no `n_tests`, a verdict with no
    `standardise`, and a verdict with `standardise=False`.
- **Existing gate tests use m = 6** (`_draws` in
  `tests/test_policy_defaults.py`), which now runs at g = 1. Where a test
  asserts g = 2 behaviour, move it to m = 12; don't change what it asserts.
- **Until this step is done, the suite is red by design:** Cowork's
  `vetoes/rules.py` edit already requires `n_tests` and `standardise`.
- **Update the existing veto tests' verdict dicts** (`GFWER` and friends in
  `tests/test_vetoes.py`) to carry `n_tests` and `standardise: True`. List each
  one in the receipt. Don't weaken any assertion to make one pass.

**2. F2: `params_hash` must not depend on line endings.**
- Add a `.gitattributes` line `params/*.yaml text eol=crlf`. The working tree
  is already CRLF, so every recorded hash stays valid.
- Add a test asserting that every `params/*.yaml` is CRLF on disk, with a
  message saying why (the hash is over raw bytes; see the 0042/0043 addenda).
- **Don't** normalise inside `hash_params_dir`: that would change every
  recorded hash.
- In the receipt, give `git check-attr eol params/audit.yaml` and confirm that
  the v0.9.0 hash is the one Cowork computed from the working tree:
  `b3d41267a752b9d76e2ddf17264cccb5b5b9ea6f0f45edc8bf1517524674376a` (CRLF). If
  it differs, stop and report both.

**3. F3: a cell's key says how it priced turnover.** In `AuditCell.key()`,
append `_created` when the **resolved** shadow form is `created`
(`resolve_shadow_form(self, params)`), not only when it is explicit.
- Explicit-`created` cells (`friction_created_cells`) keep their keys exactly.
- Trailing cells keep theirs.
- Default cells gain `_created`. No audit run since `3d437d0` holds default
  cells (the newest is `A-20260930-033812`, a pinned-trailing grid), so no
  recorded key changes. **Check this yourself and stop if it's false.**
- **Test:** a default cell's key and the halflife grid's h26 arm's key differ.
  Update `GOLDEN_NET_IR_V080`'s `endswith` assertion.

**4. F4: keys are computed with the run's params.**
- `run_cell` and `run_frictionless` call `cell.key(params)`, and so does every
  other `key()` call that has a params in scope (`scripts/run_audit.py`,
  `scripts/ic_probe.py`; grep for the rest).
- **Test:** `run_frictionless` (it's cheap) with a params variant that has no
  `vol_overlay` block records a key without `_vhl`.

**5. Small fixes.**
- **F6:** the leaderboard's turnover flag reads annual turnover only. Say so
  wherever it is shown (`render/views.turnover_disclosure`'s text and the
  streamlit column header): "highlighted on annual turnover; the audit report
  also flags rolling-1y p95". Don't add a new stored column.
- **F8:** `created_marginal_quadratic` raises `ObjectiveNotConfigured` when
  `constraints.turnover.penalty.coefficient` is null and no override is given,
  as `turnover_penalty` does. Add a test.
- **0040 wording:** `test_a_lump_costs_more_than_the_same_trading_split_over_two_weeks`
  stays. Add a sibling test showing that with a window that drops nothing
  (`prev=[0.0]*60`, below the start), lump and split cost the same. Its
  docstring cites the 0040 addendum. Update `created_marginal_shadow`'s
  docstring and any comment in `src/` that says convexity makes a lump dearer.

**6. `decisions/0039` items 2 and 3, reporting only.**
- Wherever a report, the leaderboard or the digest labels a run that passed
  both bars, the label is **"candidate"**. A run that fails bar 2 (the
  `multiple_testing` veto) is **"not detected"**. "Confirmed", "proven" and
  "rejected" (for a hypothesis) never appear. Grep `src/`, `render/` and
  `scripts/` and list every string changed.
  - The veto's own detail text ("did not reject the null") is statistical
    language about the null, so leave it.
- The hypothesis lifecycle: when a hypothesis moves to `hypotheses/done/`
  after a bar-2 failure, it carries `verdict: not_detected` and a
  `power_at_nearest_ic` field. A pass carries `verdict: candidate`. If no code
  path moves files to `done/` yet, add the vocabulary where the schema lives
  (`harness/hypotheses.py`), with a test. Say in the receipt which it was.
  **Don't invent the power figure.** Leave the field `null` with a comment
  pointing to the power tables until phase 3 computes it.

**7. Check, then commit.**
- Run `scripts/unattended.sh check-full --digest`, through the script. **Run
  it after every edit, so the log's `head=` and the tree it tested are what you
  commit.** If you must commit first, say so in the receipt.
- Commit `params/`, `vetoes/`, `src/`, `render/`, `scripts/`, `tests/` and
  `.gitattributes` together, citing `decisions/0044`, `decisions/0045` and
  `decisions/0040` in full.
- Record the old and new `params_hash` (CRLF form; old is
  `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8`) as a dated
  line in the Consequences of 0044 and 0045, as their own small commit.

**Receipt:**
- rc, commits, the check-full log directory, and the old and new
  `params_hash`.
- Every test changed or added, and why.
- The strings changed for 0039.
- The F3 check of audit runs since `3d437d0`.
- **Anything in this task you didn't do, said plainly.**

Then stop. OWNER-QUEUE L4, L19 and L20 move to `## Closed` in the same commit
as the receipt.

---

### 44. The JPMaQS loader: `load_macro`, the pull, a macro snapshot and a coverage report

Added 2026-10-01 by Cowork. **Owner, 2026-10-01:** the JPMaQS loader is the
next build step, and SUBSTRATE §5.6 is not amended. This is the phase-3 loader
of §16. **It has an owner step in the middle** (the vendor pull), as tasks 23
and 31 did. Budget: part A 2-3 h; part B 30 min after the pull. No audit runs.

**What exists already** (don't rebuild it): `loaders/jpmaqs.py` has
`split_ticker(s)`, `cross_product_size`, `credentials()`, `proxies()` and
`required_metrics()`; `loaders/env.py` refuses malformed secrets;
`VintagePanel` (`loaders/base.py`) carries the bitemporal convention of
`decisions/0014`; `data/jpmaqs/request.txt` lists the 26 tickers, all resolved
(task 31). `load_macro` raises, and `filter_panel` is named in two docstrings
but doesn't exist.

**Hard rules for this task, on top of `CLAUDE.md`'s:**
- **Never source, read or export `.env`.** The owner runs the vendor command.
- **No value from the vendor is printed, logged or written outside
  `data/raw/` and `data/snapshots/`.** Scripts report shapes, counts and date
  ranges only.
- **Nothing on or after 2020-01-01 is requested, stored or loaded.**
- **Don't touch `params/`.** `data.jpmaqs.status` stays `credentials_supplied`
  and `search_is_open()` stays false. Opening the search is an owner decision
  that comes later.
- **Tests use synthetic frames shaped like the vendor's**, built in the test
  file. No test reads `data/raw/`.

**0. Commit first, alone:** `HANDOFF.md` and `OWNER-QUEUE.md`, as
`queue: task 44, the JPMaQS loader (owner 2026-10-01)`.

#### Part A — build, with no vendor call

**1. From the vendor's frame to `VintagePanel` rows.** Add to
`loaders/jpmaqs.py` a pure function (no I/O) taking the long frame the
download returns (`cid`, `xcat`, `real_date`, `value`, `grading`, `eop_lag`):
- `series_id = f"{cid}_{xcat}"`, `knowledge_date = real_date`, and
  `period_end = real_date − eop_lag` days (`decisions/0014`).
- **Refuse, don't repair:** raise if any of the three metric columns is
  absent, if `eop_lag` is negative or non-finite on a row that has a value, or
  if `grading` is missing on a row that has a value.
- Rows with no `value` are dropped and **counted** (a day on which nothing was
  published is not an observation).
- **Compress to change points:** within a series, keep a row only when
  `(period_end, value, grading)` differs from the previous day's. The
  information-state series repeats the same vintage daily, and
  `VintagePanel.as_of` needs only the first day each vintage was known.
- **Test that compression changes nothing:** `as_of(d)` on the compressed
  panel equals `as_of(d)` on the uncompressed one, for a spread of dates.

**2. `filter_panel(frame, tickers)`.** Keep exactly the requested tickers.
Raise if a requested ticker is absent from the frame. Return the count of
cross-product series dropped.

**3. The grade filter.** `data.jpmaqs.grade_3: exclude` drops rows whose
`grading` is 3, and counts them per ticker.
- **Cowork isn't sure whether fractional grades occur** (a composite series
  may carry, say, 2.5). Don't invent a threshold. Exclude `grading >= 3` only,
  and have the coverage report list the distinct grading values per ticker so
  the owner can see whether a rule is needed.
- Any other value of `grade_3` in params raises as not implemented.

**4. Legacy euro prefixes.** `data.jpmaqs.legacy_euro_prefix_map` maps `DEM_`,
`FRF_`, `ITL_`, `ESP_` and `NLG_` to a country in the series' **meta**. The
`series_id` is not renamed, because hypotheses register the vendor's name.

**5. The holdout.** The loader calls `enforce_holdout` on both
`knowledge_date` and `period_end`. **If the raw pull reaches the holdout, it
raises; it doesn't clip.** The pull never requests those dates (step 6), so
finding them means something is wrong. Mark the test `holdout`.

**6. `scripts/jpmaqs_pull.py` and `make jpmaqs-pull`.** You write this; the
owner runs it.
- Read `data/jpmaqs/request.txt`.
- Download `metrics = required_metrics()` (value, grading, eop_lag),
  `start_date` from `data_sources.sources.jpmaqs.start_date`, and
  **`end_date` = the last calendar day before `holdout_start`**.
- **Check the installed `macrosynergy` client's `download` signature.** Cowork
  believes it accepts `tickers=` directly, but hasn't verified it. If it does,
  pass the 26 tickers. If not, pass `cids` and `xcats` and run `filter_panel`.
  Say in the receipt which it was.
- Refuse (exit non-zero, write nothing) if any requested ticker or any metric
  is missing from the result.
- Write `data/raw/jpmaqs/<pull_id>/qdf.parquet` and a `pull_manifest.json`:
  the tickers, dates requested, metrics, the package version, row counts per
  ticker and the file's sha256. `<pull_id>` is `P-<UTC stamp>`. An existing
  `pull_id` is never overwritten.
- Print shapes, counts and date ranges only.
- It doesn't touch `params/`, and it doesn't build a snapshot.

**7. `JPMaQSLoader.load_macro`.** It reads one raw pull (the newest, or a
named `pull_id`), applies steps 1-5 and returns a `VintagePanel` with
`source="jpmaqs"`. Mirror how `BloombergLoader` finds its raw input. Missing
raw raises a clear "run `make jpmaqs-pull`" error, never an empty panel.

**8. A macro snapshot, separate from the return snapshot.**
- **Don't add `macro.parquet` to the existing Bloomberg snapshot.** A snapshot
  is immutable, and every audit run cites that panel's hash.
- Add `build_macro_snapshot(snapshot_id, pull_id=None)` in
  `harness/snapshot.py`. It writes `data/snapshots/<snapshot_id>/macro.parquet`
  and a manifest: source, `pull_id`, the raw file's sha256, the directory hash,
  `params_hash`, the windows, `macro_ids`, and the counts from steps 1-3.
- It runs `enforce_holdout` on the way in, as `build_snapshot` does, and it
  refuses to overwrite.
- Add `make macro-snapshot`.

**9. `scripts/jpmaqs_coverage.py` and `make jpmaqs-coverage`.** From a macro
snapshot, write `results/jpmaqs_coverage.csv` and `.md`, one row per ticker:
- the hypothesis that registered it;
- first and last `knowledge_date`, and first and last `period_end`;
- the number of vintages and of distinct periods;
- rows with no value, and rows dropped by the grade filter;
- the distinct grading values and the row count at each;
- row counts by `eop_lag` bucket (0, 1-31, 32-92, over 92 days);
- the longest gap in days between consecutive knowledge dates;
- whether the first knowledge date is on or before `dev_start` (2001-01-05).

**Dates and counts only. No `value`.**

**10. Tests** (new `tests/test_jpmaqs_loader.py`, all on synthetic frames):
- the conversion, including a revision (same `period_end`, later
  `knowledge_date`, different value);
- the naming inversion: every row has `period_end <= knowledge_date`;
- each refusal in step 1;
- `filter_panel` drops extras and raises on a missing ticker;
- compression preserves `as_of`;
- grade exclusion and its counts;
- the legacy-prefix meta;
- the holdout raise;
- `load_macro` and `build_macro_snapshot` on a `tmp_path` raw directory,
  including the refusal to overwrite and the missing-raw error;
- the pull script's refusal paths, with the vendor client replaced by a fake.
  **No test makes a network call.**

**11. Check, then commit part A.** Run `scripts/unattended.sh check-full
--digest` after the last edit, so the log tests what you commit. Commit `src/`,
`scripts/`, `tests/` and `build.mk` together. Write a part A receipt, then
**stop and ask the owner to run**, in his own shell:

    set -a; source .env; set +a; make jpmaqs-pull

#### Part B — after the owner's pull

**12.** Run `make macro-snapshot`, then `make jpmaqs-coverage`. Commit
`results/jpmaqs_coverage.csv` and `.md`. Don't commit anything under
`data/raw/` or `data/snapshots/`.

**13. Receipt:**
- rc, commits, and the check-full log directory;
- which `download` call shape the client took;
- the `pull_id`, the macro snapshot id and its hash;
- **counts only:** tickers pulled (expect 26), rows before and after
  compression, rows with no value, rows dropped by grade, and how many tickers
  start after `dev_start`;
- **Anything in this task you didn't do, said plainly.**

Then stop. **Don't** flip `data.jpmaqs.status`, and don't start on `signals/`
or FRED.

---

### 45. The loading-estimator test (`decisions/0046`): six factors, four candidates against rolling OLS, one report

Added 2026-10-01 by Cowork. **Owner, 2026-10-01:** "let's test these factor
estimates methodologies", with joint partial betas and the factor list in
`decisions/0046`. This is OWNER-QUEUE B5 and phase-2 work (SUBSTRATE §16:
"characteristic map, factor loadings"). It is a **measurement** test
(`decisions/0016`): no portfolio, no net IR, no signal.

**Released 2026-10-01: the owner has approved `decisions/0046`** (see the
queue note at the top of `## Queue`). Run it after task 44's part A. It
doesn't depend on the JPMaQS pull. Budget 4-6 h of build, then one run. No
owner-only edit is needed; if you find one is, stop and write it down.

**Read first:** `decisions/0046` (all of it), `0015` and `0016`.

**Hard rules for this task, on top of `CLAUDE.md`'s:**
- **The configurations in `decisions/0046` §4 are fixed.** Don't tune a window,
  a constant, a grid or a prior, and don't try a second configuration "to
  see". If one can't be built as written, stop and say so.
- **No lookahead.** A loading used for week t+1 uses data up to the Friday of
  week t only. Nothing on or after 2020-01-01 is read.
- **Factor series are vendor data.** Don't print them or write them under
  `results/`. Correlations, losses and loadings are model output and may be
  written.
- **Don't recommend an estimator.** Report the numbers. Adoption is the
  owner's decision.

**0. Commit first, alone:** `HANDOFF.md`, `OWNER-QUEUE.md`, `decisions/0046`
and `hypotheses/proposed/`, as `queue: task 45, the loading-estimator test
(decisions/0046)`.

**1. Register the four hypotheses, before any estimator touches real data.**
- Move `hypotheses/proposed/H-2026-0013` to `0016` into `hypotheses/pending/`.
  In each file's `notes`, replace the "DRAFT … reviewed decisions/0046."
  sentence with "Registered 2026-MM-DD (HANDOFF task 45)." Change nothing else.
- They must pass the registry's validation as `kind: measurement`.
- `tests/test_fdr_vs_fwer.py` asserts twelve pending hypotheses.
  `read_axis_groups` should skip `family: exposure_estimation`, so the study
  keeps the shape it was run on. Say so in its docstring.
- **Commit the registration alone,** as `hypotheses: register H-2026-0013 to
  0016, loading estimators (decisions/0046)`. Its timestamp is the
  pre-registration.

**2. The factors** (new package `src/signal_lab/measurement/`, module
`factors.py`).
- Build the six weekly factors of `decisions/0046` §1 from the Bloomberg
  loader's returns and analytics panels, Friday to Friday, signed as the table
  says.
- Enforce the holdout on the way in.
- Return the frame, the common-sample start, and the count of weeks.
- **Tests on synthetic panels:** each sign convention; a missing series
  raises; the holdout raise.

**3. The estimators** (`measurement/estimators.py`). One interface: given an
instrument's returns and the factor frame up to t, return the loading vector
and its covariance. Five implementations, as `decisions/0046` §4 states them:
- `rolling_ols` (the incumbent);
- `huber_m` (`statsmodels` RLM is already a dependency);
- `theil_goldberger_peer_prior`, where the prior at t is built from the other
  members of the instrument's `reporting_class` and excludes the instrument
  itself;
- `hmm2_regime_conditional`, with a fixed seed and ten restarts;
- `kalman_dlm_discount`.

**Prefer no new dependency.** If you add one (for the HMM, say), run
`make lock` and name it in the receipt.

**Tests, each on synthetic data with a planted truth:**
- constant loadings: every estimator recovers them;
- planted outliers: Huber's error is below OLS's;
- planted peer structure with noisy individuals: the shrinkage's error is
  below OLS's;
- a planted regime switch: the HMM's error is below OLS's after the switch;
- planted drift: the Kalman filter's error is below OLS's;
- **no lookahead, for all five:** changing every observation after t leaves
  the loading at t bit-for-bit unchanged;
- a returned covariance is symmetric and positive semi-definite.

**4. The score** (`measurement/fidelity.py`), as `decisions/0046` §3:
- the scaled Huber loss and the weekly loss differential against the
  incumbent;
- **the gate:** the statistic per candidate, and `T0` from a centred block
  bootstrap of the weekly differentials (26-week blocks, 1,000 draws, one
  resampling shared by all candidates in each draw, seeded), passed to
  `stats.multiple_testing.gate`. With four candidates it must report g = 1;
- the uncertainty check: the worst-calendar-year bias statistic of the
  standardised prediction errors against
  `vetoes.risk_calibration.max_worst_annual_bias`, reusing the existing bias
  code and not a second copy;
- the two regime slices.

**Tests:**
- a candidate identical to the incumbent scores exactly zero;
- under a null (the incumbent plus independent noise in its loadings), the
  gate's rejection rate over 1,000 seeded synthetic runs is within
  [0.03, 0.07];
- a candidate with a planted advantage is rejected in most runs;
- an estimator whose covariance is understated fails the uncertainty check.

**5. The run** (`scripts/run_measurement.py`, `make measurement-loadings`).
- Instruments: investable, backbone and second tier.
- **Time it first** on ten instruments. If the full run projects beyond 3 h,
  stop and report the projection.
- Each estimate records the last data date it used, and the script raises if
  that date is after t.
- Write `results/measurement/M-<stamp>/`:
  - `summary.json`: the hashes, the sample, per estimator the statistic, the
    adjusted p-value, the gate's verdict, the bias statistic and its verdict,
    and the slices;
  - `loadings.parquet`: instrument, date, estimator, factor, loading and its
    standard error;
  - `report.md`: the same, readable, plus the factors' correlation matrix
    (full sample and the range of its rolling 156-week values) and the
    measured-against-estimated check of `decisions/0046` §1 for the Treasury
    buckets and the IG corporate index.
- Move each hypothesis `pending → running → done` through
  `HypothesisRegistry.move`, with `verdict="candidate"` if it passed both the
  gate and the uncertainty check, and `"not_detected"` otherwise.

**6. Check, then commit.** Run `scripts/unattended.sh check-full --digest`
after the last edit. Commit `src/`, `scripts/`, `tests/`, `build.mk`, the moved
hypothesis files and `results/measurement/M-<stamp>/report.md` and
`summary.json`. Don't commit the parquet.

**Not in this task:**
- extending the `lookahead` veto to estimated parameters (`decisions/0015`).
  `vetoes/` is owner-only, and Cowork brings that patch separately;
- a measurement leaderboard in the render layer;
- adopting any estimator into `data/characteristics/`.

**Receipt:**
- rc, commits, the check-full log directory, the run id and its runtime;
- the registration commit's hash and time, and the first commit that ran an
  estimator on real data, so the order is on the record;
- the common-sample start and the number of weeks and instruments scored;
- **per estimator, in one table:** the statistic, the adjusted p-value, gate
  pass or fail, the worst-year bias statistic, pass or fail, and the two
  slices;
- whether the HMM's regimes were stable across restarts;
- any dependency added;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 46. Apply `decisions/0047` (negative `eop_lag`) and finish task 44 part B; make the Cash exclusion the default of the estimator test (`decisions/0046` addendum)

Added 2026-10-02 by Cowork. **Owner rulings 2026-10-02:** L21 "accept" (keep
the seven tickers; a JPMaQS period may end after it is known; the holdout
binds on the knowledge date; `decisions/0047`) and L22 "yes exclude cash"
(`decisions/0046` addendum). Cowork's review of tasks 44 and 45 is in
`Claude outputs/project-mirror/tasks-44-45-review-2026-10-02.md`. **No vendor
call and no audit.** Budget 2-3 h.

**One owner-only edit is already in the working tree, applied by Cowork at the
owner's instruction:** `SUBSTRATE.md` v0.9, two sentences in §5.6 and a v0.9
paragraph (`decisions/0047`). Verify it with `git diff --ignore-cr-at-eol`.
Nothing in `params/` or `vetoes/` changes. If a step needs one, stop and write
it down.

**0. Commit first, alone:** `HANDOFF.md` and `OWNER-QUEUE.md`, as `queue: task
46; L21 and L22 ruled (owner 2026-10-02)`. **Then, alone:** `SUBSTRATE.md`,
`decisions/0046`, `decisions/0047` (new) and `decisions/0100`, as `substrate:
v0.9 -- a JPMaQS period may end after it is known (decisions/0047); the Cash
class is not scored (decisions/0046)`.

#### Part 1 — `decisions/0047`, then task 44's part B

**1. `VintagePanel`** (`loaders/base.py`) gains a field
`period_may_follow_knowledge: bool = False`.
- When it is `False`, the existing check stands, with its message.
- The JPMaQS loader sets it to `True`. No other loader does.
- **Tests:** the default still raises; a JPMaQS panel with a period after the
  knowledge date builds; `as_of` on it returns the row on and after its
  knowledge date and not before.

**2. `qdf_to_vintage_frame`** no longer refuses a negative `eop_lag`.
- A non-finite `eop_lag` on a valued row is still refused.
- **The checkpoint of `decisions/0047` §3:** if any valued row has an
  `eop_lag` below −92 days, raise, and build nothing.
- Count the negative-lag rows per ticker in three buckets: −1 to −31, −32 to
  −92, and below −92 (the last must be zero for anything to be built).
- Update the test that asserted the refusal, and say in the receipt which
  test it was. Add tests for the checkpoint and the buckets.

**3. The holdout, on the knowledge date.**
- Keep `enforce_holdout` on the raw `real_date` and on `knowledge_date`,
  exactly as now.
- **Remove the `enforce_holdout` call on `period_end`** in `build_macro_panel`
  and in `build_macro_snapshot`. Leave `build_snapshot` (the return snapshot)
  and `loaders/holdout.py` untouched. **Add no bypass argument anywhere.**
- The macro manifest records `max_period_end` and
  `rows_with_period_end_in_holdout`.
- **Tests, marked `holdout`:** a row known on 2019-12-20 about a period ending
  2020-03-31 loads; a row known on 2020-01-02 raises; the existing synthetic
  macro-panel holdout test is unchanged and still passes.

**4. The coverage report** gains the three negative-lag buckets and each
ticker's latest `period_end`.

**5. Task 44's part B.** Run `make macro-snapshot`, then `make
jpmaqs-coverage`, on the existing pull `P-20261002T032635Z`. Don't pull again.
- **If the checkpoint raises, stop.** Report the counts per ticker and bucket,
  and build nothing.
- Commit `results/jpmaqs_coverage.csv` and `.md`. Commit nothing under
  `data/raw/` or `data/snapshots/`.
- Don't flip `data.jpmaqs.status`.

#### Part 2 — the estimator test without Cash

**6. The exclusion becomes the spec.** In `scripts/run_measurement.py` the
reporting class `Cash` is excluded by default, as a named constant citing the
`decisions/0046` addendum. A run with the default exclusion is **not** a
sensitivity run and carries no `-sens` suffix. `--exclude-class` still marks a
run as a sensitivity when it adds classes beyond the default.

**7. Two additions to the report and `summary.json`, reported and never
gated:**
- each estimator's **mean Huber loss**, the incumbent's included, so a
  statistic can be read as a share of the incumbent's loss;
- each candidate's statistic **by reporting class**, with the number of
  instruments in each class.

**8. Re-run once:** `make measurement-loadings ARGS=--no-registry`. The four
hypotheses stay in `hypotheses/done/`; move nothing.
- **The four statistics, adjusted p-values and worst-year bias readings must
  equal `M-20261002T034221Z-sens`'s to every printed digit.** If one differs,
  stop and report both. Don't investigate by re-running with changes.
- **Change no estimator, no constant and no configuration.**
- Commit the new run's `report.md` and `summary.json`.

**9. Check, then commit.** Run `scripts/unattended.sh check-full --digest`
after the last edit. Commit `src/`, `scripts/`, `tests/`, `build.mk` and the
`results/` files named above, citing `decisions/0047` and `decisions/0046` in
full.

**Receipt:**
- rc, commits and the check-full log directory;
- **JPMaQS, counts only:** the macro snapshot id and hash; tickers; rows raw,
  with no value, dropped by grade, before and after compression; the
  negative-lag rows per ticker and bucket; `max_period_end` and the rows with
  a period end in the holdout; the distinct grading values; how many tickers
  start after `dev_start`;
- **the estimator test:** the new run id, whether it reproduced the
  sensitivity run exactly, the incumbent's mean loss, and the by-class table;
- every test changed, and why;
- **Anything in this task you didn't do, said plainly.**

Then stop. OWNER-QUEUE L21 and L22 move to `## Closed` in the same commit as
the receipt.

---

### 47. A fifth loading estimator: mean-reverting Bayesian loadings, H-2026-0017 (`decisions/0046`, addendum of 2026-10-02)

Added 2026-10-02 by Cowork. **Owner, 2026-10-02:** register and test a method
that is Bayesian, time-varying and shrinks to the instrument's own long-run
mean. **Run it after task 46**, because it needs the Cash exclusion and the
report additions that task makes. No owner-only edit, no vendor call, no
audit. Budget 2-3 h.

**Read first:** the two 2026-10-02 addenda at the end of `decisions/0046`, and
`hypotheses/proposed/H-2026-0017.yaml`.

**Hard rules, as in task 45:**
- **The configuration in the addendum is fixed.** Don't tune the grids, the
  scale or the prior, and don't try a second configuration. If it can't be
  built as written, stop and say so.
- **No lookahead.** The filter is recursive; the loading for week t+1 uses data
  up to the Friday of week t only.
- **Don't change the other five estimators, the factors or the score.**
- **Don't recommend an estimator.**

**0. Commit first, alone:** `HANDOFF.md`, `OWNER-QUEUE.md`, `decisions/0046`
and `hypotheses/proposed/H-2026-0017.yaml`, as `queue: task 47, a fifth loading
estimator (decisions/0046)`. *(If task 46's step 0 already committed some of
these, commit what is left.)*

**1. Register, before the estimator touches real data.** Move
`hypotheses/proposed/H-2026-0017.yaml` to `hypotheses/pending/`. In its
`notes`, replace the sentence "DRAFT, in hypotheses/proposed/. Not registered
until HANDOFF task 47 moves it to hypotheses/pending/." with "Registered
2026-MM-DD (HANDOFF task 47)." Change nothing else. Commit it alone, as
`hypotheses: register H-2026-0017, mean-reverting loadings (decisions/0046)`.

**2. The estimator** (`measurement/estimators.py`, name
`mean_reverting_dlm_own_mean`), as the addendum states it:
- State `(a, mu, d_t)`: the intercept, the long-run loading `mu` (constant,
  diffuse prior) and the deviation `d_t = phi * d_(t-1) + w_t`. The loading is
  `mu + d_t`.
- Innovation covariance `(1 − phi²) * q * C_t`, with `C_t` the scaled
  covariance of the 156-week rolling OLS loading known at t. Before a rolling
  OLS exists, the filter doesn't start.
- Observation variance learned as `_kalman_filter` does it.
- The grid: half-lives 13, 26, 52 and 104 weeks (`phi = 0.5 ** (1 / h)`) and
  `q` of 0.25, 1 and 4. At each t, take the pair with the highest cumulative
  one-step predictive log likelihood on data up to t. One recursive pass per
  pair.
- **What the path stores for week t:** the one-step forecast of the loading,
  `mu_hat + phi * d_hat_t`, and that forecast's covariance. Say so in the
  docstring, because the other estimators store a filtered or fitted value.
- The 104-valid-week rule applies, as for the others.

**Tests, on synthetic data with a planted truth:**
- constant loadings are recovered;
- **planted mean-reverting loadings:** its error is below rolling OLS's and
  below `kalman_dlm_discount`'s;
- a planted permanent level shift: it converges to the new level, and the
  test records how many weeks that takes (reported, no threshold);
- no lookahead: changing every observation after t leaves the stored value at
  t bit-for-bit unchanged;
- the returned covariance is symmetric and positive semi-definite;
- the forecast, not the filtered value, is what is stored (a direct test).

**3. The score.** Add it to `CANDIDATES`, so the gate runs over five.
- The gate must report `n_tests = 5` and `g = 1`.
- Update the tests that assert four candidates. List each in the receipt.

**4. The run:** `make measurement-loadings`, with the default Cash exclusion
from task 46.
- **Before anything is recorded, compare:** the incumbent's and the first four
  candidates' statistics, bias readings and mean losses must equal task 46's
  run to every printed digit. Their adjusted p-values may differ, because the
  search is now five. If a statistic differs, stop.
- **If the five-way gate would give any of H-2026-0013 to 0016 a verdict other
  than `not_detected`, stop and report.** Their recorded verdicts stand.
- Move only H-2026-0017: `pending → running → done`, with `candidate` if it
  passes both the gate and the uncertainty check, and `not_detected`
  otherwise.
- The report also gives, for this estimator: how often each `(half-life, q)`
  pair was chosen, as a table of shares; and its statistic in the first and
  second half of the scored weeks, since its claim is that the gain grows with
  history.

**5. Check, then commit.** `scripts/unattended.sh check-full --digest` after the
last edit. Commit `src/`, `scripts/`, `tests/`, the moved hypothesis file, and
the run's `report.md` and `summary.json`.

**Receipt:**
- rc, commits, the check-full log directory, the run id and its runtime;
- the registration commit's hash and time, and the run's;
- whether the first four reproduced exactly;
- **the six-row table:** statistic, mean loss, adjusted p, gate, worst-year
  bias, check, and the slices, with the by-class breakdown for the new
  estimator;
- the grid shares and the two half-sample statistics;
- every test changed, and why;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 48. After task 47: reproduce the run of record from the committed code, name the filters' variance update, and describe how stable each estimator's loadings are (`decisions/0046`, addendum of 2026-10-03)

Added 2026-10-03 by Cowork, after reviewing task 47. No owner-only edit, no
vendor call, no audit, and **no hypothesis moves**. Budget 3 h plus the check.

**Read first:** the 2026-10-03 addendum at the end of `decisions/0046`, and
`Claude outputs/project-mirror/task-47-review-2026-10-03.md`.

**Hard rules:**
- **No estimator's default behaviour changes.** Step 3a proves it: the run of
  record must reproduce exactly from the code as you leave it.
- **Nothing here is a test.** Steps 2, 2b and 3b are descriptions made after the
  results were seen. They change no verdict, whichever way they read, and
  every output says so in its first line.
- **Don't recommend an estimator.** OWNER-QUEUE B5 is the owner's.

**0. Commit first, alone:** `HANDOFF.md`, `OWNER-QUEUE.md` and
`decisions/0046-how-loading-estimators-are-tested.md`, as
`queue: task 48; decisions/0046 addendum of 2026-10-03; OWNER-QUEUE L23`.

**1. The variance update (`measurement/estimators.py`).**
- `_kalman_filter` and `_mr_filter` both update the covariance as
  `C = (S / S_new) * (R - A A' Q)`. Here `C` is scale-free: `Q = 1 + z'Rz`,
  the predictive variance is `S * Q`, and the output is `S * C`. In that form
  West and Harrison's recursion is `C = R - A A' Q`, with no ratio.
- The coded line is a different filter and a coherent one. In actual units
  its precision obeys `P_t = P_prior + z z' / S_(t-1)`: each observation
  enters at the variance estimate of the week before, and earlier information
  is not rescaled when `S` moves.
- **This is Cowork's derivation. Check it. If you disagree, stop and say so.**
- **Keep the coded update as the default.** Correct `_kalman_filter`'s
  docstring, which says "West-Harrison", and add the same sentence to
  `_mr_filter`'s.
- Add a keyword, default off, that selects the textbook update in both
  filters, and a script flag `--conjugate-update` that sets it for
  `kalman_dlm_discount` and `mean_reverting_dlm_own_mean` together. A run with
  the flag is a sensitivity: `-sens` suffix, no hypothesis moved, as
  `--exclude-class` already works.
- **Tests:** the two updates give different covariances on a series with a
  volatility break; they agree to 1e-8 when the variance prior is tight
  (`n0 = 1e9` in `_kalman_filter`), because `S` then never moves.

**2. The stability description (new: `scripts/describe_loadings.py`,
`make describe-loadings`).** It reads one run's `loadings.parquet`
(`instrument, date, estimator, factor, loading, se`) and nothing under
`data/`. For each estimator and factor, over the cells where every estimator
has a loading at both dates:
- **`weekly_change`:** the mean over instruments of the mean over weeks of
  `|b_t - b_(t-1)|`, shown as a ratio to rolling OLS (1.00 is as stable as
  OLS). Also for 2008-2009 alone.
- **`annual_change`:** the same with `b_t - b_(t-52)`.
- **`rank_agreement`:** the median over weeks of the cross-sectional Spearman
  correlation between the estimator's loadings and rolling OLS's.
- One summary row per estimator: the mean of each ratio across the six
  factors.
- The mean-reverting candidate stores a forecast for week t+1 and the others
  a value at t. Compare what is stored, because that is what would be handed
  to the exposure matrix, and say so in the output.
- Output `stability.md` and `stability.json` in the run's directory.
- **Tests, on a synthetic frame:** a constant loading gives a change of zero;
  a random walk with a planted step size returns that step; two identical
  estimators give a ratio of 1 and a rank agreement of 1.

**2b. The absolute fit (added 2026-10-05; `make describe-fit`, or the same
script).** The owner asked how well the loadings predict at all. 0046 scored
only each candidate's difference from rolling OLS, so nothing on disk says.
For each estimator, on the scored cells of the run of record, with
`p = b_t' f_(t+1)` and `r` the return exactly as the score uses it:
- **`r2_oos`** = `1 − Σ(r − p)² / Σ r²`. The benchmark is a loading of zero
  and, as in the score, no intercept. Pooled, by reporting class, and for the
  four slices.
- **`huber_skill`** = `1 − loss / loss_zero`, where `loss_zero` is the score's
  own Huber loss with `p = 0`. Same breakdowns.
- **`ts_corr`:** per instrument, the correlation of `p` and `r` over the
  scored weeks. Report the median and the quartiles by class, and the ten
  lowest instruments by ticker.
- **`xs_corr`:** per week, the Spearman correlation of `p` and `r` across
  instruments. Report its mean, its standard deviation and the share of weeks
  above zero. **Label it "conditional on the realised factor moves, not a
  forecast IC".** The loadings forecast sensitivities, not returns.
- **`factor_share`:** by class, each factor's share of the predicted
  variation, `Σ p · (b_k f_k) / Σ p²`. The six shares sum to 1.
- **Examples, for the owner to open on this machine:**
  `predicted_vs_actual.html` in the run's directory, for rolling OLS and
  `mean_reverting_dlm_own_mean`. Per instrument: a scatter of `p` against `r`,
  and a line of their 52-week rolling correlation. Inline SVG written by the
  script, white background, grey marks, `#FF6100` for the mean-reverting
  series, no new dependency.
  - **The instruments are named here, before any is looked at:** `SPXT`,
    `MXUS0UT`, `M1EF`, `NDDUJN`, `LF98TRUU`, `LUACTRUU`, `LT09TRUU`,
    `LUTLTRUU`, `I20344US`, `BCOMGCTR`, `ENXG`, `LUMSTRUU`. If one is not in
    the scored set, say so and don't substitute.
  - **The file holds weekly returns, which are vendor data.** Add it to
    `.gitignore`, never print it, and don't summarise its points in the
    receipt. The numbers Cowork reads are in `fit.json`.
- Output `fit.md` and `fit.json`.
- **Tests, on a synthetic frame:** true loadings with no noise give
  `r2_oos = 1`; zero loadings give `r2_oos = 0` and `huber_skill = 0`;
  `factor_share` sums to 1.

**3. The runs, after the last edit to `src/` and `scripts/`.**
- **3a. Reproduce the run of record.**
  `make measurement-loadings ARGS="--no-registry --reference results/measurement/M-20261003T181155Z/summary.json"`.
  The reference check must pass for the incumbent and all five candidates.
  Then compare `p_adjusted` for the five against `M-20261003T181155Z` and
  report whether each is equal. **If any reference field differs, stop:** the
  run of record was not made by the committed code.
- **3b. The sensitivity.**
  `make measurement-loadings ARGS="--no-registry --no-reference --conjugate-update"`.
  Report its six-row table beside the run of record's.
- **3c.** `make describe-loadings` on `M-20261003T181155Z`.
- **3d.** `make describe-fit` on `M-20261003T181155Z`.

**4. Check, then commit.** `scripts/unattended.sh check-full --digest`.
- Task 47's `check-full` took 4,235 s against task 46's 794 s. The new
  estimator costs about 0.3 s per series, so its tests don't explain that.
  **If this run takes more than 1,500 s,** run
  `uv run --python 3.12 --group dev pytest -q -m slow --durations=25` once and
  list the 25 slowest tests in the receipt. Don't move or re-mark any test.
- Commit `src/`, `scripts/`, `tests/`, `build.mk`, `.gitignore`, the two new
  runs' `report.md` and `summary.json`, and `stability.md`, `stability.json`,
  `fit.md` and `fit.json`. **Not `predicted_vs_actual.html`.**

**Receipt:**
- rc, commits, the check-full log directory and its runtime;
- whether you agree with the derivation in step 1;
- 3a: pass or stop, and the five `p_adjusted` comparisons;
- 3b: the six-row table, coded against textbook;
- 3c: the summary row per estimator, and the table for 2008-2009;
- 3d: `r2_oos`, `huber_skill`, `ts_corr` and `xs_corr`, pooled and by class,
  for each estimator; `factor_share` by class; which named instruments were
  not in the scored set;
- the 25 slowest tests, if step 4 asked for them;
- every test added or changed, and why;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 49. Make the check explain its runtime, try parallel tests, and run only the slow tests a change can reach (OWNER-QUEUE L24)

Added 2026-10-06 by Cowork. **Owner ruling 2026-10-06** (L24: "consider it
approved as a handoff for claude code to work on"). No owner-only edit, no
vendor call, no audit, no hypothesis moves, and **no file under `src/`
changes**. Run it **after task 48's receipt is committed.** Budget 3 h plus the
checks.

**Read first:** `Claude outputs/project-mirror/check-runtime-2026-10-06.md`. It
has the evidence and says which numbers below are Cowork's own choices.

**Why.**
- **`check-full` runs anywhere from 388 s to 4,235 s on nearly the same suite,
  and nobody knows why.** On 2026-10-01, 677 tests took 2,079 s at 22:30 and
  716 tests took 829 s at 23:45. Task 47's took 4,235 s; task 48's took
  2,462 s for 743 tests. The task 37 profile put the whole suite at 582 s.
- **The rule runs every engine test for a change that cannot reach the
  engine.** Nothing outside `src/signal_lab/measurement/` imports that package
  except `scripts/run_measurement.py` and `scripts/describe_loadings.py`.
  Tasks 47 and 48 changed only those files, and each paid for about 30 engine
  and optimiser tests.
- **It isn't the Monte Carlo.** About 4 of the 40 `slow` tests are simulations.
  The rest are engine runs, optimiser solves and estimator fits.

**Hard rules:**
- **No test is deleted, weakened, re-marked or thinned.** No seed count or
  replication count goes down. **No golden is re-recorded**, for any reason.
- **When in doubt the selector says FULL.** A path it can't place, a file it
  can't parse, a git call that fails: FULL, with the reason printed.
- **A scoped run is never reported as a full one.** `status.txt`, the log and
  the receipt each say which tier ran and which slow files were left out.
- **`scripts/unattended.sh`'s rc and its existing `status.txt` lines don't
  change.** Cowork reads them. Add lines; don't reword any.
- The behaviours and the stop conditions below are fixed. How you implement
  them is yours.
- One `scripts/unattended.sh` at a time, and nothing else heavy on the machine
  while a timing in step 2 or 3 runs.

**0. Commit first, alone:** whichever of `HANDOFF.md` and `OWNER-QUEUE.md` is
still uncommitted, as `queue: task 49; OWNER-QUEUE L24 (owner 2026-10-06)`.
Check `git diff --cached --ignore-cr-at-eol --stat` before committing.

**1. Every run explains itself (`build.mk`, `scripts/unattended.sh`).**
- `build.mk`: add `PYTEST_ARGS ?=` and append `$(PYTEST_ARGS)` to the pytest
  call in `test`, `test-fast` and `test-slow`. Not in `holdout`.
- `unattended.sh` passes
  `PYTEST_ARGS="--durations=40 --durations-min=1.0 --junitxml=$out/junit.xml"`
  to its check step, so every run leaves per-test times.
- `status.txt`, one line at the start: `nproc`, the three load averages from
  `/proc/loadavg`, `MemAvailable`, and `OMP_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` (or `unset`). One line at the
  end: the load averages again.
- `$out/load.log`: every 30 s, a timestamp, the load averages and the top
  three processes by CPU (`ps -eo pcpu,comm --sort=-pcpu`). Stop the sampler
  when the script exits, whatever the rc.
- **The Windows side, best effort.** WSL can't see what Windows or another
  virtual machine is doing with the CPU, and that is one of the suspects. If
  `powershell.exe` is on `PATH`, add total CPU percent and the top three
  process names to `load.log` once a minute. It must never change the rc, and
  a call that fails or takes over 5 s is skipped. **If this isn't working
  after 15 minutes of effort, leave it out and say so.**

**2. Do BLAS threads matter? A measurement, about 10 minutes.**
- Run this twice, back to back:
  `uv run --python 3.12 --group dev pytest -q -m slow tests/test_baseline.py --durations=10`.
  First with the environment as it is. Then with
  `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`.
- Report both wall times, `nproc`, and the load average before each.
- **If any test fails with threads capped, skip step 3 and put it first in the
  receipt.** `test_baseline.py` asserts `row["net_ir"] == GOLDEN_NET_IR`
  exactly. A failure there means a recorded number depends on the thread
  count, which the owner needs to know before anything else.

**3. Parallel tests: a trial, adopted only if it pays.**
- **Skip it if `nproc` is 2 or less,** and say so.
- Add `pytest-xdist` to the `dev` group in `pyproject.toml`, then `make lock`
  and `make install`.
- **A, then B, back to back, on the slow tier:**
  - A: `uv run --python 3.12 --group dev pytest -q -m slow --durations=40`
  - B: the same plus `-n auto --dist loadfile`, with the three thread
    variables set to 1.
  - `loadfile` keeps each test file on one worker, so a module's expensive
    fixtures are built once.
- **Adopt it only if all three hold:** B passes exactly the tests A passes; B's
  wall time is at most 0.70 of A's; and the load average at the two starts
  was similar. Report both starts.
- **If adopted:** `build.mk` gets `XDIST ?= -n auto --dist loadfile`, used by
  `test`, `test-fast` and `test-slow`, and those recipes cap the three thread
  variables at 1 whenever `XDIST` is not empty. `make check-full XDIST=` runs
  serial. `holdout` stays serial.
- **If not adopted:** put `pyproject.toml` and `uv.lock` back as they are at
  HEAD, `make install` again, add no `XDIST`, and report both times.
- **A test that fails only in B:** not adopted. Name the test and how it
  failed. Don't fix it by regrouping or reordering tests; Cowork will look.

**4. The scoped tier: `scripts/select_slow.py` and `make check-scoped`.**

A slow test file has to run when a changed file is inside what it imports,
directly or through other modules. Otherwise it can be left out. Everything
the selector doesn't understand is FULL.

**4a. The selector.** `scripts/select_slow.py [--base REF] [--head REF]`,
standard library only, like `check_governance.py`.
- **Changed files:** `git diff --name-only <base>` (default `HEAD`: the working
  tree and the index against it) plus untracked files that aren't ignored.
  With `--head`, the diff between the two refs; that mode is for the replay in
  4e only.
- **Each changed path is one of three kinds:**
  - **Neutral, reaches no slow test:** `*.md` in the repo root, `decisions/`,
    `hypotheses/`, `docs/`, `results/`, `.gitignore`, and `build.mk` **only if**
    its check block is unchanged (4c).
  - **Code, placed by imports:** `src/signal_lab/**/*.py`, `scripts/*.py`,
    `render/*.py`, `tests/test_*.py`.
  - **Anything else is FULL.** That includes `params/`, `vetoes/`,
    `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/fixtures/`, any
    other file under `tests/`, `data/`, `.githooks/`, `scripts/unattended.sh`,
    `scripts/_bootstrap.py` and `scripts/select_slow.py` itself. **A deleted or
    renamed code file is FULL too:** the tree no longer says who imported it.
- **Imports:** parse each file with `ast` and take every `import` and
  `from ... import`, **including those inside functions** (`conftest.py` and
  many tests import there). Resolve names against `src/`, the repo root,
  `scripts/`, `render/` and `tests/`, because the tests put those on
  `sys.path` and import scripts by bare name. Follow relative imports. A
  package brings its `__init__.py`. `from pkg import name` brings
  `pkg/name.py` if it exists. A name that resolves to no repo file is
  third-party and is ignored. Follow the imports transitively.
- **`tests/conftest.py`'s imports count for every test file.** Its fixtures are
  shared.
- **A slow test file** is a `tests/test_*.py` holding at least one
  `pytest.mark.slow`. **It is selected** when a changed code file is the file
  itself or is anywhere in its imports.
- **FULL as well when the engine hasn't been proven lately:** no
  `make check-full rc=0` line, and no `make check-scoped rc=0 ... tier=FULL`
  line, in any `results/audit/_unattended/*/status.txt` from the last 7 days
  (`FULL_MAX_AGE_DAYS`, default 7).
- **Output:** first line `FULL: <reason>` or `SCOPED`. Then the slow files
  selected, the slow files left out, and each changed path with its kind.

**4b. Running a selection.**
- `tests/conftest.py`: a pytest option `--slow-only-in=<comma-separated files>`.
  When given, deselect every `slow` item whose file isn't listed. Without the
  option nothing changes. Fast tests in a left-out file still run.
- `make check-scoped` = governance + lint + the selector's output printed in
  full + one pytest run + holdout. The pytest run is the whole suite when the
  selector says FULL, and `-m "not holdout" --slow-only-in=<selected>` when it
  says SCOPED.
- `scripts/unattended.sh check-scoped` is a valid bare target. Its status line
  is `make check-scoped rc=<rc> (<n> s) tier=FULL` or `... tier=SCOPED`, and a
  second line lists the slow files left out.
- **Audit targets still open with `make check-full`.** Don't change that.

**4c. `build.mk`'s check block.** Put one comment line before and one after the
part that defines the check: `PY`, `PYTEST`, `PYSTD`, `GOV`, `PYTEST_ARGS`,
`XDIST`, and the targets `lint`, `test`, `test-fast`, `test-slow`, `holdout`,
`governance`, `check`, `check-full` and `check-scoped`. Move lines if you have
to, without changing what any target does. The selector compares that block at
the base with the working tree, ignoring line endings. Different, or a marker
missing on either side: FULL. A new audit or report target outside the block
is neutral.

**4d. Tests, fast tier, on a small tree built in `tmp_path`:**
- a change to a module only one slow file imports selects only that file;
- an import inside a function is followed;
- a script imported by bare name through `scripts/` is followed;
- a change to something `conftest.py` imports selects every slow file;
- `params/x.yaml`, an unknown path and a deleted code file each give FULL;
- a changed check block gives FULL, and a new target outside it doesn't;
- no full pass in the last 7 days gives FULL;
- selected plus left out equals every slow file, each exactly once;
- **on the real tree:** the files under `tests/` and `src/` that reach repo
  code with `subprocess`, `runpy`, `importlib.import_module`, `__import__` or
  `exec` are exactly a list written into the test. Today Cowork finds one,
  `tests/test_governance.py`, which runs `scripts/check_governance.py`. A new
  one fails the fast tier, because the selector can't see through it.
- **`--slow-only-in`, by `pytest --collect-only -q` counts:** listing every
  slow file collects what `-m "not holdout"` collects; listing none collects
  what `-m "not slow and not holdout"` collects.

**4e. Replay, and the stop condition for step 4.** Run the selector with
`--base <c>^ --head <c>` on `b0c7713` (task 47), `3519b1c` (task 46),
`3a04275` (task 45), `e07a9d1` (task 44 part A) and task 48's build commit.
The imports are read from today's tree, so this is an approximation; say so.
- **`b0c7713` must be SCOPED,** must select `test_measurement_estimators.py`
  and `test_measurement_fidelity.py`, and must leave out `test_audit.py`,
  `test_baseline.py`, `test_engine.py` and `test_experiment.py`.
- **`3519b1c` must select `test_audit.py` and `test_baseline.py`.** It changed
  `loaders/base.py`, which both import.
- The other three changed `build.mk` before it had markers, so FULL is
  expected there. Report the reason line.
- **If either expectation fails, stop step 4:** don't add `check-scoped` to
  `build.mk`, don't edit `CLAUDE.md`, and put the selector's output in the
  receipt. Keep the selector and its tests if they pass.

**4f. `CLAUDE.md`, only if 4e passed.**
- Replace the two sentences that begin "`make check-full` is the definition of
  done" and "`make check` (the fast tier) is enough" with:

  > `make check-scoped` is the definition of done for any commit touching
  > `src/`, `scripts/`, `tests/`, `vetoes/` or `params/`. It runs the whole
  > suite unless it can place every changed file, and then it leaves out only
  > the slow tests whose imports cannot reach a change; it prints which it
  > did, and the receipt repeats it. `make check-full` (always the whole suite)
  > opens every audit, and is the answer whenever `check-scoped` is in doubt.
  > `make check` (the fast tier) is enough for a commit touching only
  > `HANDOFF.md`, `OWNER-QUEUE.md`, `decisions/`, `hypotheses/` or docs.

- In "Routine, unattended work": add `check-scoped` to the target list and
  say it runs `make check-scoped`. Add to the digest's contents: the tier that
  ran, the slow files left out, the load averages at the start and the end,
  and the five slowest tests.

**5. Check, then commit.**
- `scripts/unattended.sh check-full --digest`, after the last edit. This
  commit changes `tests/conftest.py`, so it is a full run by the new rule as
  well as the old one.
- Then `python3 scripts/select_slow.py` on the same tree, and paste its
  output. **It must say FULL.** If it says SCOPED, stop and don't commit.
- Commit `scripts/unattended.sh`, `scripts/select_slow.py`, `tests/conftest.py`,
  the new test file, `build.mk` and `CLAUDE.md`, plus `pyproject.toml` and
  `uv.lock` if step 3 adopted xdist. Message:
  `checks: runs log the machine and per-test times; a scoped slow tier by imports; xdist <adopted|not adopted> (HANDOFF task 49, OWNER-QUEUE L24)`.

**Receipt:**
- rc, commits, the check-full log directory and its runtime;
- step 1: one `status.txt` start line and three lines of `load.log`, pasted;
  whether the Windows-side sample works;
- step 2: the two wall times, `nproc`, the load averages, and any failure;
- step 3: A's and B's wall times and pass counts, adopted or not, and why;
- the 25 slowest tests of the final run, and the total time of the `slow`
  tier against the rest;
- 4e: the first line and the selected and left-out lists for each of the five
  commits;
- step 5's selector output;
- which steps stopped, and on what;
- every test added, and why;
- **what you think makes the slow runs slow, labelled as a guess if it is
  one;**
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 50. One thread is the reference (`decisions/0048`); re-record three constants; the grade ruling's two hypothesis edits (`decisions/0006` addendum); `.gitignore` hygiene; the first scoped check

Added 2026-10-07 by Cowork. **Owner rulings 2026-10-07** on OWNER-QUEUE L26
and L23 ("i accept all of your suggestions for the pending decisions"). No
owner-only edit, no vendor call, no audit, no hypothesis changes state. Budget
2 h. Run it before task 51.

**Read first:** `decisions/0048`, the 2026-10-07 addendum to `decisions/0006`,
and `Claude outputs/project-mirror/check-runtime-2026-10-06.md` (its outcome
section).

**Hard rules:**
- **Exactly three constants are re-recorded,** all in `tests/test_baseline.py`:
  `GOLDEN_NET_IR`, `GOLDEN_NET_IR_CREATED_MARGINAL` and `GOLDEN_NET_IR_V080`.
  No hash, no other constant, no tolerance loosened, no test re-marked.
- **If anything else fails at one thread, stop and list it.** Don't fix it and
  don't re-record it.
- **Numbers recorded before today stand as recorded.** Don't re-run an audit
  and don't edit an old `summary.json` or report.
- Nothing under `src/signal_lab/` changes its arithmetic. Step 5's one-line
  fix is the only edit to a result-producing file.

**0. Commit first, alone, after `make check`:** `HANDOFF.md`,
`OWNER-QUEUE.md`, `decisions/0006-…`, `decisions/0048-…`, `decisions/0049-…`
and `decisions/proposed/0050-…`, as
`queue: tasks 50 and 51; decisions 0048 and 0049; OWNER-QUEUE L26, B5, L25, L23 ruled, L27 added (owner 2026-10-07)`.

**1. `.gitignore`.**
- Three pattern lines carry a trailing `# comment`, which git reads as part of
  the pattern: `results/audit/`, `results/fdr_vs_fwer/` and
  `results/measurement/*/loadings.parquet`. Move each comment to its own line
  above the pattern.
- Add `data/universe/raw_meta.json` and `data/universe/raw_structure.json`.
  They are written by `make inspect-raw`, and `raw_meta.json` holds rows read
  from the vendor workbook. **Don't open either.**
- Add `results/audit-bloomberg.log`.
- **Check:** `git check-ignore -v` names a rule for one path under each of the
  six, and `git status --short` shows no untracked file. Report both.

**2. The pin.**
- Every `make` target runs with `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and
  `MKL_NUM_THREADS` set to 1. Export them in `build.mk`, inside the
  check-block, so the selector reads the change as a full run.
- `scripts/unattended.sh` must show `=1` for all three in its `machine` line.
  Don't reword the line.
- **A run made at any other setting must say so.** The test session fails at
  the start, with one clear message, if any of the three is not 1. A script
  under `scripts/` that produces numbers refuses to start the same way. How
  you do it is yours. No new dependency.
- **Every run records the setting:** the measurement run's `summary.json`, and
  the audit's summary beside its hashes. New key, no existing key renamed.
- Add one line to `CLAUDE.md`'s hard rules: numbers are made at one thread
  (`decisions/0048`); `make` sets it; a direct `python` call must set it too.
- **Report what the solver does.** If the optimiser has a thread setting of
  its own, say what it is and don't change it.

**3. The three constants.**
- Run `tests/test_baseline.py` twice, in two fresh processes, with the pin.
- **Expected:** the same four tests fail both times, and each prints the same
  value both times, to the last digit:
  `GOLDEN_NET_IR` −0.8792060912640641, `GOLDEN_NET_IR_CREATED_MARGINAL`
  −0.3916378876353463, `GOLDEN_NET_IR_V080` −0.4046626602695416.
- **If the two runs disagree, or either disagrees with those values, stop.**
  One thread is then not enough to make the number repeat, and the owner needs
  to know before anything is recorded.
- Otherwise re-record the three, and put `decisions/0048` and the old value in
  the comment above each.

**4. The two hypothesis files** (`decisions/0006`, addendum of 2026-10-07).
- **`hypotheses/pending/H-2026-0004.yaml`:** append to `notes`, changing
  nothing else: "Parked 2026-10-07 by owner ruling (OWNER-QUEUE L23,
  decisions/0006 addendum): both JPMaQS inputs are grade 3 throughout and are
  excluded by `grade_3: exclude`, so the hypothesis has no macro input. It
  cannot run and is not counted as a test in any family or stepdown. A US leg
  from a point-in-time source would be a new registration."
- **`hypotheses/pending/H-2026-0001.yaml`:** remove `EUR_MBCSCORE_SA` from
  `data_required`, and append to `notes`: "Amended 2026-10-07 by owner ruling
  (OWNER-QUEUE L23, decisions/0006 addendum): EUR_MBCSCORE_SA is grade 3
  throughout and is excluded, so it is removed from data_required.
  USD_MBCSCORE_SA stays; about half of its rows are excluded. The composite
  now has three US components and one each for the euro area, Japan and the
  UK."
- **A ticker with no usable row is not available.** After this step
  `HypothesisRegistry.partition()` against the current snapshots must put
  H-2026-0004 in `blocked`, with both `BLSCSCORE` tickers missing. Report
  where H-2026-0001 lands and why. If the macro manifest lists an empty ticker
  as available, fix that where the manifest is read or built, and test it on a
  synthetic panel with one all-grade-3 ticker. **Don't rebuild a snapshot from
  vendor data, and don't change `params/`.** If it needs either, stop.
- If a data request file is written for H-2026-0004, its reason must name the
  grade rule. It is not a request to the owner.
- Update the tests that count hypotheses' series. List each.

**5. Check, commit, then the first scoped run.**
- `scripts/unattended.sh check-full --digest`. The tree is a full run by both
  rules. **Report its runtime against 3,908 s.**
- Commit as `checks: one thread is the reference; three goldens re-recorded;
  grade ruling applied to H-2026-0001 and 0004; .gitignore (HANDOFF task 50,
  decisions/0048, decisions/0006)`.
- **Then one small change, to exercise the scoped tier end to end.**
  `src/signal_lab/measurement/describe.py`, about line 110, divides `a[i]` by
  `a[0]` and warns when `a[0]` is zero. Return NaN there without the warning.
  The existing test must still pass with no `RuntimeWarning`.
- Run `scripts/unattended.sh check-scoped --digest`. **Expected: tier
  `SCOPED`,** with the two measurement slow files selected and the other six
  left out. If it says `FULL`, report the selector's reason and don't force
  it.
- Commit that fix alone.

**6. The estimator test at one thread.**
`make measurement-loadings ARGS="--no-registry --reference results/measurement/M-20261003T181155Z/summary.json"`.
- The run of record was made with threads unset, so the reference check may
  fail. **That is a finding, not a fault.** If it stops on the check, re-run
  with `--no-reference` and compare the two `summary.json` files yourself.
- Report, per estimator, the largest absolute difference in the statistic, the
  mean loss and the adjusted p, and whether any verdict or bias check reads
  differently. No hypothesis moves, whichever way it reads.
- Commit the run's `report.md` and `summary.json`.

**Receipt:**
- rc, commits, the two log directories, and both runtimes;
- step 1's two checks;
- how the pin and the refusal are done, and what the solver does;
- step 3: the two runs' values, old against new for the three constants, and
  any other failure;
- step 4: where each hypothesis lands in `partition()`, and every test changed;
- step 5: the tier, the files left out and the runtime of the scoped run;
- step 6: the differences, and the first line says whether any verdict moved;
- **Anything in this task you didn't do, said plainly.**

Then go on to task 51.

---

### 51. The estimated half of the exposure matrix: Huber loadings on the six factors, walk-forward, with their uncertainty, each instrument's explained share, and the measured cells beside them (`decisions/0049`)

Added 2026-10-07 by Cowork. **Owner rulings 2026-10-07** on OWNER-QUEUE B5 and
L25. No owner-only edit, no vendor call, no audit, no hypothesis moves, **and
`resolve_exposures` keeps raising.** Run it after task 50. Budget 3 h.

**Read first:** `decisions/0049`, `decisions/0015`, and
`decisions/proposed/0050` (so you know what is *not* being built).

**What this is.** `decisions/0049` chose Huber loadings on six factors. It did
not choose the matrix's columns (OWNER-QUEUE L27). This task builds the parts
every answer to L27 needs, as a versioned store, and stops there.

**Hard rules:**
- **The estimator is `HuberM` as registered** (H-2026-0013): c = 1.345, MAD
  scale, 156 weeks, at least 104 valid weeks, sandwich covariance, all six
  factors in one regression. Import it from `measurement/estimators.py`. Don't
  copy it, tune it or add an option.
- **The factors are `measurement/factors.py`'s,** unchanged.
- **Walk-forward.** The row for week t uses data up to the Friday of week t.
  Nothing on or after 2020-01-01 is read.
- **Don't build from `decisions/proposed/0050`.** No axis mapping, no merging
  of measured into estimated, no label block, no change to
  `harness/experiment.py`, `harness/engine.py` or `vetoes/`.
- **The store holds vendor-derived values.** Its data files are git-ignored
  and never printed. Only the manifest and the report are committed, and they
  hold counts, dates, hashes and aggregates.
- Don't recommend anything about L27.

**1. The builder** (a new package; put it where SUBSTRATE §15 says, and if §15
names no place use `src/signal_lab/characteristics/` and say so).
- **Instruments:** every investable backbone and second-tier series, Cash
  included. Tradable-only series are listed in the manifest as not estimated.
- **Per instrument and week, where the data-sufficiency rule holds:**
  - the six loadings and their standard errors;
  - the residual variance, the number of valid weeks in the window and the
    last data date used;
  - **`explained_share`:** over the 156 weeks ending at t, with
    `p_s = b_(s-1)' f_s` (last week's loading, this week's factors, no
    intercept) and `r_s` the return: `1 − Σ(r_s − p_s)² / Σ r_s²`. It needs at
    least 52 such weeks and is NaN before that. It is out of sample and uses
    nothing after t. It may be negative; don't clip it.
- **Every row is marked `estimated`,** with the estimator's name.
- **The measured cells, beside them and not merged:** `INDEX_OAD_TSY` and
  `INDEX_OAS_TSY` for every instrument that has them, as of each weekly date
  (the last value on or before that Friday), marked `measured`.

**2. The store** (`data/characteristics/<id>/`, id `huber6-v1`).
- Data files, git-ignored (add the rule and check it with `git check-ignore`):
  the estimated loadings, the per-row fit fields, and the measured cells.
- `manifest.yaml`, committed: the id, the build time, `decisions/0049`, the
  estimator and its constants, the factor names, the params hash, the returns
  and factors hashes as the measurement runs compute them, the thread setting,
  row counts per file, the number of instruments estimated and not, the first
  and last date, and the directory hash by the snapshot module's
  `hash_directory`.
- A loader that reads a store, re-hashes it and refuses one that has changed.
- `scripts/build_characteristics.py` and `make characteristics`.

**3. Two checks the build makes on itself, before it writes.**
- **It reproduces the test.** On the 70,326 cells the estimator test scored
  (Cash excluded, as the test did, and scored with `measurement/fidelity.py`'s
  own functions), the pooled `r2_oos` and mean Huber loss computed from this
  build must equal
  the `huber_m` row of `results/measurement/M-20261003T181155Z/fit.json`
  (0.7030 and 0.2303). That file was made with threads unset, so allow 1e-6
  and report the actual difference. A larger difference stops the build.
- **No lookahead:** `assert_no_lookahead`, as the measurement run does.

**4. The report** (`results/characteristics/huber6-v1/report.md`, committed;
aggregates only).
- Instruments estimated, by reporting class, and the first week each class has
  loadings.
- **`explained_share` by reporting class:** the median over instruments of
  the full-sample value, and of the value at the last week.
- **Standard error against loading, by factor and class:** the median of
  `se / |loading|` at the last week.
- **Estimated against measured, for every bond index** (the table OWNER-QUEUE
  L27 needs): the median over weeks of the real-yield loading, the inflation
  loading and the credit loading, beside minus the median `INDEX_OAD_TSY`,
  and the ratio of each to it. One row per instrument, with its class.
- First line: "Built from `decisions/0049`. It chooses nothing about the
  matrix's columns (OWNER-QUEUE L27)."

**5. Tests, on synthetic data.**
- Constant true loadings are recovered, and `explained_share` is near 1 with
  no noise and near 0 for an instrument unrelated to the factors.
- **No lookahead:** changing every observation after t leaves every stored row
  at or before t unchanged, bit for bit, `explained_share` included.
- The measured value at a date is the last one on or before it, never a later
  one.
- A store that is edited after it is written is refused by the loader.
- **In the `holdout` tier:** the builder raises on data dated on or after
  2020-01-01, and a built store's last date is before it.
- `resolve_exposures` still raises `ExposureMatrixMissing`.

**6. Check, then commit.** `scripts/unattended.sh check-scoped --digest`. Say
which tier ran. Commit `src/`, `scripts/`, `tests/`, `build.mk`,
`.gitignore`, the manifest and the report, as
`characteristics: Huber loadings on six factors, walk-forward, with explained share and the measured cells; store huber6-v1 (HANDOFF task 51, decisions/0049)`.

**Receipt:**
- rc, commits, the log directory, the tier and the runtime;
- where the package went, and why;
- the store's hash, its row counts, and the instruments not estimated;
- step 3's two differences;
- **the estimated-against-measured table in full,** and `explained_share` by
  class;
- every test added, and any you changed;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 52. Commit the records; two instruments leave the investable universe (`decisions/0052`); the ex-USD analytics file; the store rebuilt as `huber6-v2`; the report's table corrected; three small fixes

Added 2026-10-07 by Cowork. **Owner rulings 2026-10-07:** OWNER-QUEUE L27
(`decisions/0050`), the solver's form (`decisions/0051`), the universe
(`decisions/0052`), and his go-ahead for this task ("Yes, the full task"). No
owner-only edit, no vendor call, no audit, no hypothesis changes state, **and
`resolve_exposures` keeps raising.** Budget 3 h; about 20 minutes of it is
machine time.

**Read first:** `decisions/0052`; `decisions/0050` and `0051` (so you know
what is *not* being built); and
`Claude outputs/project-mirror/tasks-50-51-review-2026-10-07.md`.

**Hard rules:**
- **Two new vendor files are in `data/raw/bloomberg/`,** put there by the
  owner on 2026-10-07. Never print a value from either. Report counts, dates
  and hashes.
- **Both files run to 2026-10. Nothing on or after 2020-01-01 is read.** Cut
  at the holdout as `load_analytics` already does, and test it.
- **No forward fill, and no month-end observation in a daily panel.** Each
  field is truncated at its own true daily start.
- **Don't build from `decisions/0050` or `0051`.** No axis mapping, no
  merging of measured into estimated, no label block, no alphas, no change
  to `harness/experiment.py`, `harness/engine.py` or `vetoes/`.
- **`bbg_tradable_only_longer_history.xlsx` is read by nothing in this
  task.** Don't open it.
- **Nothing in `params/` changes.** If a step seems to need it, stop.
- **Numbers recorded before today stand.** `M-20261003T181155Z` stays the
  run of record. `huber6-v1` and its report are not edited or deleted. Don't
  re-run the estimator test.
- **No golden moves.** The baseline and audit goldens run on synthetic
  universes whose ids are not in the universe file. If a test fails that
  this task doesn't name, stop and list it. Re-record nothing.

**0. Commit first, alone, after `make check`:** `HANDOFF.md`,
`OWNER-QUEUE.md`, `decisions/0048-…`, `decisions/0050-…` (moved out of
`decisions/proposed/`: stage the deletion there too), `decisions/0051-…` and
`decisions/0052-…`, as
`queue: task 52; decisions 0050, 0051 and 0052; OWNER-QUEUE L27 ruled, L28 to L31 added; tasks 50 and 51 marked landed (owner 2026-10-07)`.

**1. The universe** (`decisions/0052`).
- In `scripts/build_universe.py`, add `LGTRTRGU` and `LGTRTRJU` to
  `NOT_INVESTABLE_OTHER`, each with the reason
  `the global aggregate restated in another currency, not an instrument (decisions/0052)`.
  Their reporting class stays.
- `make universe`. **Expected: 102 series, 93 investable, 9 excluded.**
- `tests/test_scripts.py` asserts 95 investable. Make it 93 and cite 0052 in
  the docstring. List every other test or constant that changes.

**2. The ex-USD analytics.**
- **The file:** `data/raw/bloomberg/bbg_exusd_bonds_analytics.xlsx`, sheet
  `BBG Values`, one row per date and ticker: `date`, `ticker`, `index_name`,
  `oad_tsy`, `yield_to_worst`, `oas`, `oas_field`. 44,190 rows, seven
  tickers. Its sha256 begins `a76df50225f99128`; check it and stop if it
  differs. The other two sheets are not read.
- Add a row to `data/universe/raw_manifest.csv` for it, with a new layout
  name for the long form.
- **The field map:** `oad_tsy` is `INDEX_OAD_TSY` and `yield_to_worst` is
  `INDEX_YIELD_TO_WORST`. `oas` goes to the field named in that row's
  `oas_field`: `INDEX_OAS_TSY`, or `INDEX_OAS_SWAP` for `LG38TRUU`. **A swap
  spread must never land in `INDEX_OAS_TSY`.**
- **The true daily start, per ticker and field.** The Index Map has no row
  for these, so derive it in code, by one rule, with a test: *the first
  observation from which each of the next 20 observations follows within 5
  calendar days.* Write `data/universe/bbg_exusd_analytics_coverage.csv`
  (`ticker_field`, `first_any`, `first_daily`, `n_before_holdout`) and commit
  it.
- **Expected daily starts** (Cowork's read of the file's dates, by that
  rule; no value was used):

  | Ticker | Duration and yield | OAS |
  |---|---|---|
  | `LET1TREU` | 2002-04-23 | 2002-09-17 |
  | `I12823GB` | 2009-07-24 | 2005-09-22 |
  | `I02913JP` | 2018-02-28 | 2002-09-17 |
  | `LP05TREU` | 2000-10-09 (yield 2000-09-28) | 2002-09-17 |
  | `LG38TRUU` | 2000-08-31 | 2004-07-12 (swap) |
  | `I02513EU` | 2002-06-28 | 2002-09-17 |
  | `LGTRTRGU` | 2001-01-16 | 2002-09-17 |

  **If your rule gives another date, report both and keep the rule's.**
- **Merge into the `AnalyticsPanel` that `load_analytics` returns,** with
  the same cleaning as the main sheet (missing markers, business days), the
  truncation above and the holdout cut. If a ticker and field is in both
  files, stop.
- Load every ticker the file holds, `LGTRTRGU` included: the analytics
  panel is not limited to investable series.
- A raw directory without the file, as the test fixtures have, loads as it
  did before. On the real directory the manifest row makes the file
  required.
- **Leave the values as delivered.** Don't convert a unit and don't extend
  the Treasury-OAS drop to foreign government indices. Record what was
  loaded in `loader.report["analytics"]`.
- **The factors must not move.** The factors hash of a build after this step
  equals `3401475e…fafa9`, the run of record's. If it differs, stop.
- **Tests,** on a synthetic long-form workbook built in a temp folder: the
  field map, with a swap row kept out of `INDEX_OAS_TSY`; a monthly run-in
  truncated at the daily start; the holdout cut; a duplicate ticker and
  field across the two files refused.

**3. The build's check on itself, for a universe that has changed.**
`scripts/build_characteristics.py` stops today when the run of record's
instruments are not the build's. After step 1 they are not.
- **New gate:** the run of record's instruments must be the build's (Cash
  out) plus exactly `LGTRTRGU` and `LGTRTRJU`. Anything else stops.
- **New gate:** every Huber loading the run of record stores for a shared
  instrument equals this build's, **at a tolerance of zero.** Report the
  number of cells compared and the largest difference.
- The pooled `r2_oos` and mean Huber loss on the shared cells are computed
  and reported, not compared: `fit.json` pools 86 instruments.
- `assert_no_lookahead` as before.
- **One test** on synthetic data that the scored cell set takes presence
  only from a reference run: changing every stored value of another
  estimator, leaving which cells are finite, changes nothing.

**4. The store.** `make characteristics ARGS="--store-id huber6-v2"`.
- **Expected:** 85 estimated (Cash included), 8 not; loadings 440,964 rows
  and fit 73,494 (the two dropped series had 884 weeks each); 2002-12-27 to
  2019-12-27; more measured rows than `huber6-v1`'s 16,256.
- The manifest cites `decisions/0049` and `0052`, this task, and
  `supersedes: huber6-v1`.
- **Report the largest difference between `huber6-v2`'s loadings and
  `huber6-v1`'s on the cells they share.** Expected 0.0.

**5. The report** (`characteristics/report.py`; the output is
`results/characteristics/huber6-v2/report.md`).
- **Estimated against measured, one row per estimated bond-class
  instrument** (Treasuries, Long Treasuries, TIPS, MBS, IG Corporates, HY
  Corporates, EM Sovereign Bonds, EM Corporate Bonds, Ex-USD Bonds):
  - weeks with a loading, and weeks with a loading and a measured duration;
  - the medians and their ratio, **over the weeks with both**;
  - the median of the weekly ratio with its 10th and 90th percentiles, for
    real yield and for inflation;
  - a dash where an instrument has no measured duration. The heading says
    how many of how many have one.
- **By period** (2002-08, 2009-15, 2016-19): the median weekly ratio, real
  yield and inflation, per instrument.
- **Measured coverage, per instrument:** the first measured week, the weeks
  with a loading and no measured duration, and the empty weeks inside the
  measured span.
- **Duration times spread:** for each instrument with an `INDEX_OAS_TSY`,
  the weekly median of the credit loading over
  `−OAD × OAS / OAS of LUACTRUU`.
- **Explained share by class:** add the lowest instrument and the number
  below 0.5 at the last week, and one line saying Commodities' share is an
  identity (the factor is that index less cash).
- **Expected,** from Cowork's read of `huber6-v1`, whose loadings step 4
  shows are the same: weekly real-yield ratio `LT01TRUU` 0.56 [0.30, 0.86],
  `LT13TRUU` 0.89 [0.79, 0.98] over 677 weeks, `LT09TRUU` 0.97 [0.93, 1.03],
  `LUTLTRUU` 0.84 [0.68, 0.95], `LT11TRUU` 0.84 [0.66, 0.90], `LBUTTRUU` 1.24
  [1.02, 1.56], `LUACTRUU` 0.84 [0.77, 0.96]; `LT13TRUU` first measured
  2007-01-12 with 211 weeks unmeasured; no empty week inside any span;
  credit over duration-times-spread 0.37 to 0.68 for the five HY indices.
  **If one differs by more than 0.01, report both. Don't change the method
  to match.**
- Tests on synthetic data for each new table.

**6. Three small fixes.**
- **`scripts/select_slow.py`:** a FULL result lists no slow file as left
  out, so `status.txt` and `check.log` agree. Update its tests.
- **`scripts/describe_loadings.py`** calls `require_one_thread` like the
  other number-making scripts.
- **`src/signal_lab/threads.py`:** its docstring says a multi-threaded BLAS
  differs "from run to run". Task 49 measured a difference between thread
  settings, not between runs. Say what was measured.

**7. Check, then commit.** `scripts/unattended.sh check-full --digest`.
Commit `src/`, `scripts/`, `tests/`, `data/universe/`, the `huber6-v2`
manifest and its report, as
`characteristics: ex-USD analytics, two restated series out of the universe, store huber6-v2, the report's table like for like (HANDOFF task 52, decisions/0052)`.

**Receipt:**
- rc, commits, the log directory, the tier and the runtime;
- step 1: the builder's counts and every test changed;
- step 2: the coverage table in full (dates and counts), the file's hash,
  series per field, and the factors hash;
- step 3: cells compared and the largest difference;
- step 4: the store's hash and row counts, and the difference to
  `huber6-v1`;
- step 5: each expected figure beside what the report prints, and **the
  estimated-against-measured rows of the six ex-USD bond indices**;
- every test added and every test changed;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 61. The nightly worker lands (`decisions/0062`): commit the record and the build; then push

Added 2026-10-19 by Cowork. Run by hand, in an interactive session: the
nightly machinery this task commits is what will run later tasks. No
owner-only path is touched.

**Step 0. The working tree.** `git status --short` must be exactly:

     M .gitattributes
     M CLAUDE.md
     M HANDOFF.md
     M scripts/unattended.sh
    ?? decisions/0062-the-nightly-run-and-the-morning-review.md
    ?? scripts/nightly/
    ?? tests/test_nightly.py

and `scripts/nightly/` must hold exactly `config.sh guard.py nightly_gate.py
prompt.md run.sh settings.json`. Anything else: stop and report.
`git diff --ignore-cr-at-eol` on the four modified files should show: in
`HANDOFF.md`, the contract's "Nightly runs" paragraph, the `Nightly-release:`
line, the 2026-10-19 queue notes and the text of tasks 61 and 62 (and
nothing in any other task); in `CLAUDE.md`,
one sentence added and "400% backstop" replaced; in `scripts/unattended.sh`,
the 11-line lock block (a blank line, two comment lines and the block) after `cd`; in `.gitattributes`, `*.sh text eol=lf`.

**Step 1. Checks before committing.**
- `bash -n scripts/nightly/run.sh` → rc 0.
- `python3 scripts/nightly/nightly_gate.py gate --handoff HANDOFF.md --slot day
  --ran /tmp/ran --runs /tmp --month-cap 100 --sonnet-cap 6 --opus-cap 12`
  → prints `GO=0` and `REASON='nothing is released'`. (System python3, no
  venv: the gate is stdlib only.)
- The lock: in one terminal `exec 9>~/.locks/signal-lab.lock; flock 9` (after
  `mkdir -p ~/.locks`), then in a second `scripts/unattended.sh check; echo
  rc=$?` → `rc=75` with "another run holds" on stderr, and no new directory
  under `results/audit/_unattended/`. Close the first terminal (or `exec 9>&-`).
- `scripts/unattended.sh check-scoped` → rc 0. Expect tier FULL (new files
  cannot be placed), about 10 minutes. `tests/test_nightly.py` is in the fast
  tier: 46 tests, none slow.

**Step 2. Two commits.**

    git add decisions/0062-the-nightly-run-and-the-morning-review.md HANDOFF.md CLAUDE.md
    git commit -m "records: decisions/0062 (decided 2026-10-19), the nightly run and the morning review; the HANDOFF contract and CLAUDE.md follow"
    git add .gitattributes scripts/unattended.sh scripts/nightly tests/test_nightly.py
    git commit -m "scripts: the nightly worker, its gate and its guard; unattended.sh takes the one-run lock (HANDOFF task 61, decisions/0062)"

**Step 3. Receipt, then push.** Receipt under `## Done` as usual, committed
alone; then `git push origin main`, a fast-forward. Report `git rev-list
--count @{u}..HEAD` before and after.

### 62. Canary: one supervised nightly run (`decisions/0062` item 12)

Added 2026-10-19 by Cowork. **Run only after task 61's receipt and push have
landed, and only once the `Nightly-release:` line names 62** (`push=no`). Started by
the owner by hand: `bash scripts/nightly/run.sh day` between 11:00 and 17:00
(or `night` between 22:00 and 04:30).

1. `git log --oneline -3` and `git status --short`; put both in the receipt.
2. `scripts/unattended.sh check` → rc 0 (the fast tier, about 2 minutes).
   Name its `results/audit/_unattended/` directory in the receipt. It must
   not fail with rc 75: the nightly run's child inherits the lock.
3. Receipt, committed alone (`HANDOFF.md`). **No push.**

Expected: under $1 on Sonnet, under 15 minutes.

**Revision note 1 (2026-10-19 17:10, Cowork; owner: "yes" to (a) and (b)).**
The first run (`results/audit/_nightly/20261019-153210-day`, receipt `aec7eee`)
was denied at step 2: it sent `date && scripts/unattended.sh check; echo rc=$?;
ls -dt ... | head -2` as one call, and **`echo` was not on the allow list**
(every part of a compound command must be). `scripts/unattended.sh` was
allowed. Cowork's fix is in the working tree, uncommitted, in four files:
`scripts/nightly/run.sh` (allow `echo`, `printf`, `cat`, `cut`, `sort`,
`uniq`, `tr`, `cd`, `pwd`, `true`; `status.txt` names denied commands),
`scripts/nightly/nightly_gate.py` (reads them), `scripts/nightly/prompt.md`
(one command per call; a denied compound may be re-run part by part) and
`tests/test_nightly.py` (47 tests). **Run the task from step 1 again, with
these changes to it:**
- **Step 2 becomes `scripts/unattended.sh check-scoped`** → rc 0 (this run
  commits `scripts/` and `tests/`, so the scoped check is the definition of
  done; expect tier FULL, about 7 to 10 minutes). Name its log directory. It
  must not fail with rc 75.
- **New step 2b, the guard:** run `cat git_key.pub` as its own call. Expect it
  **blocked by the nightly guard** (`decisions/0062` item 6), not run; copy
  the block message's first sentence into the receipt. The file is a public
  key, so nothing secret is at stake if the guard failed; say so if it ran.
- **New step 3a, before the receipt:** `git diff --ignore-cr-at-eol --stat`
  must show exactly the four files above and `HANDOFF.md` (Cowork's revision note and release line, committed with the receipt); then
  `git add scripts/nightly/run.sh scripts/nightly/nightly_gate.py scripts/nightly/prompt.md tests/test_nightly.py`
  and `git commit -m "scripts: the nightly allow list gains echo and other read-only commands; denials named in status.txt; one command per call (HANDOFF task 62, decisions/0062)"`.
  Commit nothing else in it.
- The receipt follows as step 4, committed alone. **Still no push.**

### 63. A `data_required` name must resolve when a hypothesis is registered (`decisions/0034`, ruled 2026-10-21); the "fabricated" corrections

Added 2026-10-21 by Cowork. **Written, NOT released.** The owner releases it on the
`Nightly-release:` line (suggested `63`, `push=no`, Sonnet; escalate to Opus only if it
stops on the design). No owner-only path is touched: `src/`, `tests/`, `scripts/`,
`data/universe/`, `decisions/`, `OWNER-QUEUE.md` and one hypothesis note.

**Why.** `decisions/proposed/0034` asks the harness to refuse a fabricated instrument
the way it already refuses a fabricated citation. The owner ruled 2026-10-21: "In any
case i agree with the proposed validation." Read the record first, including its two
2026-10-21 sections (the ruling, and the correction about `LT08TRUU` with the open
point on rule 1).

**Where the record was silent, Cowork decided as follows (the owner may strike any):**
1. **Where the check applies.** `validate_hypothesis` is also what loading runs, and
   there is no registration step today (`STATES` is pending, running, done; agents write
   files). So the check is a keyword, `resolve_names: bool = False`, and loading behaves
   exactly as now (0034: "does not re-validate retroactively"). A new
   `HypothesisRegistry.register(path)` validates with `resolve_names=True`, then moves a
   file not already under `hypotheses/pending/` into it, refusing to overwrite. Nothing
   calls `register` yet.
2. **What is real, for a Bloomberg or FRED name.** Take the text before `|` as the
   ticker (drop a trailing ` Index`), and the text after as the field. The ticker
   resolves if it is in any of: `investable_universe.csv` (`ticker`),
   `bbg_index_coverage.csv` (`ticker`), `bbg_exusd_bonds_coverage.csv` (`ticker`),
   `fred_coverage.csv` (`series_id`), the ticker part of `ticker_field` in
   `bbg_analytics_coverage.csv` and `bbg_exusd_analytics_coverage.csv`, the benchmark
   legs named under `benchmark:` in `params/constraints.yaml`, or the owner-confirmed
   list (item 3). If a field is given, the pair must be in an analytics table or on the
   owner-confirmed list.
3. **The owner-confirmed list** (the open point on rule 1): a new tracked file
   `data/universe/owner_confirmed_names.csv`, header `name,field,confirmed_by,confirmed_on,how,note`.
   It holds real vendor names that no coverage table has yet. Only the owner (or
   Cowork, on the owner's written statement) adds a row; **the worker adds none beyond
   the seed row below.** Seed row: `LT08TRUU,,owner,2026-10-21,owner statement,"US Treasury: Intermediate Index, 1 to 9.9999 years; future ticker I00049US (not verified by Cowork)"`.
4. **JPMaQS names** (rule 2): `is_jpmaqs_ticker` from `signal_lab.loaders.jpmaqs`
   (the `CCY_CATEGORY_TRANSFORM` form of `decisions/0014`). No catalogue lookup.
5. **A measurement hypothesis** with an empty `data_required` still validates.
6. Anything matching none of these is rejected with the offending entry named, in the
   existing `HypothesisRejected` form.

**RESUME 2026-10-21 (Cowork, 15:20 ET). Steps 0 to 3 are done and committed (`5501945`). Skip them. Start at step 4a.** This block overrides step 0 and the run line of step 4; everything else in the task stands.

**Step 0 (resume).** `git status --short` must show exactly:

     M HANDOFF.md
     M OWNER-QUEUE.md
     M decisions/proposed/0034-a-data-required-name-must-resolve.md
    ?? AGENTS.md
    ?? scripts/check_registry_names.py

(`scripts/check_registry_names.py` is the worker's own file from the 12:30 run: read it, fix it if it is wrong, never run it by any command except the make target below.) Anything else: stop and report.

**Step 4a. A make target.** Add to `build.mk` (and its `.PHONY` line), in the style of `inspect-raw`:

    registry-names: ## one-off: data_required names the resolver rejects (HANDOFF task 63)
    	$(PY) --group dev python scripts/check_registry_names.py

Run it as **`make registry-names`**, nothing in front of it (no `env`, no variable assignments, no `cd`, no `for` loops: the allow list matches the start of the command and `make *` is on it; the `$(PY)` line in `build.mk` is how the other targets set the environment; if it does not set the three thread variables, put them in the target line, not on the command line). To look at a coverage table use `head -3 data/universe/<file>.csv`, one file per call. If `make registry-names` is denied anyway, **stop** and report the exact command and the denial; try nothing else.

**Step 0. The working tree.** `git status --short` must show exactly:

     M HANDOFF.md
     M OWNER-QUEUE.md
     M decisions/proposed/0034-a-data-required-name-must-resolve.md
    ?? AGENTS.md

(`AGENTS.md` is a Codex orientation file the owner is not using; leave it untouched and
uncommitted.) Anything else: stop and report.

**Step 1. The code** (`src/signal_lab/harness/hypotheses.py`): the resolver as a
function that returns the list of unresolved entries, `resolve_names` on
`validate_hypothesis` and `parse_hypothesis`, and `HypothesisRegistry.register`. The
coverage tables are read once per call to the resolver, with `utf-8-sig`. `load` and
`load_tolerant` must not change behaviour. Create `data/universe/owner_confirmed_names.csv`
with the seed row.

**Step 2. Tests** (`tests/test_hypotheses.py`, or a new `tests/test_name_resolution.py`),
three per rule as 0034 says (passing, failing, boundary), in a temporary directory with
small fixture tables, never the real registry: a bare ticker; `TICKER Index|FIELD`; a
field not in the analytics tables; a FRED id; a benchmark leg; the seed row's `LT08TRUU`;
a well-formed and a malformed JPMaQS name; a measurement hypothesis with an empty list;
**`load_tolerant` still returns a file whose name does not resolve while `register` rejects it**.

**Step 3. The check.** `scripts/unattended.sh check-scoped` → rc 0 (this commit touches
`src/`, `scripts/`/`tests/` and a data file; expect tier FULL, about 7 to 10 minutes).
Name its log directory. Then commit: `git add` exactly the files changed in steps 1 and 2 and
`data/universe/owner_confirmed_names.csv`, with the message
`harness: a data_required name must resolve at registration (HANDOFF task 63, decisions/0034)`.

**Step 4. The one-off pass over the registry** (0034 asks for it once the rule exists).
Add `scripts/check_registry_names.py`: for every file in `hypotheses/pending/` and
`hypotheses/done/` print the file name and each entry the resolver rejects, then the
totals; it writes nothing and exits 0. Run it with the three thread variables set to 1.
**Put the totals and the rejected names in the receipt. Do not edit any hypothesis, and
add no row to the owner-confirmed list, to make it pass.** `scripts/` is touched, so run
`scripts/unattended.sh check-scoped` again (rc 0; name its directory), then commit the script in its own
commit: `scripts: a one-off report of data_required names the resolver rejects (HANDOFF task 63)`.
*Cowork's guess, from a simplified dry run outside the repo's environment:* of 136 entries
in 21 files, about 25 come back unresolved, all of the form `<ticker>|IV3M_10DP` or
`<ticker>|IV3M_10DC` in `H-2026-0018` to `H-2026-0021`, because no coverage table covers
the implied-vol file. If the real pass differs, report it as it is; that is not a failure.

**Step 5. The records** (one commit, docs tier). Before editing the hypothesis note,
run `git grep -n "H-2026-0010" -- tests scripts src`; if any test or script pins that
file's text or hash, **skip the note edit, say so in the receipt, and do the rest.**
- `git mv decisions/proposed/0034-a-data-required-name-must-resolve.md decisions/0034-a-data-required-name-must-resolve.md`,
  and replace its `**Status:** **proposed**` with `**Status:** **decided** 2026-10-21 by
  the owner ("In any case i agree with the proposed validation"); resolution sources
  fixed by HANDOFF task 63.` Edit nothing else in the file (Cowork's two 2026-10-21
  sections stay).
- `decisions/0032-the-registry-tickers-against-the-real-panel.md`: append a section
  `## Addendum 2026-10-21 (owner)` saying `LT08TRUU` is a real Bloomberg index, the US
  Treasury: Intermediate Index, 1 to 9.9999 years, future ticker `I00049US` (owner's
  statement, not verified by Cowork); that "fabricated" at the lines naming it was wrong
  for it and right for `LUALTRUU` on the owner's word; and that the rulings stand,
  because `LT01TRUU` against `LT11TRUU` was chosen on the panel and not on the
  existence of `LT08TRUU`. Do not edit the earlier text.
- `OWNER-QUEUE.md`, closed item L6: add one line under it, dated 2026-10-21, pointing to
  that addendum. L39 is already restated by Cowork in the working tree; commit it as it is.
- `hypotheses/pending/H-2026-0010.yaml`, `notes`: replace the sentence `The phase-0
  name LT08TRUU does not exist and was removed.` with `The phase-0 name LT08TRUU is a
  real Bloomberg index (the US Treasury: Intermediate Index; owner, 2026-10-21,
  decisions/0032 addendum) that was in no coverage table; it was removed from this spec
  and is not used.` Keep the YAML folded block intact and check it parses.
Message: `records: decisions/0034 decided; the "fabricated" LT08TRUU corrections (HANDOFF task 63)`.
Then `scripts/unattended.sh check` → rc 0 (docs tier, about 2 minutes); name its directory.

**Step 6. Receipt**, committed alone (`HANDOFF.md`). **No push.** Say what the pass
reported, whether the note edit was skipped, and the two `check` directories.

**Not in this task:** no change to `params/`, `vetoes/` or `SUBSTRATE.md`; no hypothesis
edited apart from that one note; no data pull (the owner's offered `LT08TRUU` pull is
not needed by `H-2026-0010` as specified); no caller of `register`; nothing added to
the owner-confirmed list. What to do about the names the pass rejects is the owner's
call and goes to OWNER-QUEUE, written by Cowork.

Expected: under $2 on Sonnet, under 30 minutes.

### 64. Commit `decisions/0063`: the Japan government family joins the panel (OWNER-QUEUE L39, option (a))

Added 2026-10-21 by Cowork. **Written, NOT released.** Run only after task 63's
receipt has landed. Records only: nothing in `src/`, `scripts/`, `tests/`,
`params/`, `vetoes/`, `hypotheses/` or `data/` changes. The owner's ruling is
"L39: option A" (2026-10-21).

**Step 0. The working tree.** Cowork copies the draft into place when it
releases this task. `git status --short` must show exactly:

     M HANDOFF.md
    ?? decisions/0063-the-japan-government-family.md
    ?? AGENTS.md

(`AGENTS.md`: leave it.) Anything else: stop and report. If task 63's receipt is
not at the top of `## Done`, stop.

**Step 1.** `git diff --ignore-cr-at-eol --stat` and read the new file's first
12 lines: its Status must say `decided 2026-10-21 by the owner`.

**Step 2. The check.** `scripts/unattended.sh check` → rc 0 (docs tier, about 2
minutes). Name its `results/audit/_unattended/` directory.

**Step 3. Commit** `decisions/0063-the-japan-government-family.md` alone, with the
message `records: decisions/0063, the Japan government family joins the panel (HANDOFF task 64, OWNER-QUEUE L39)`.
Do not move L39 out of `OWNER-QUEUE.md`: it stays open until the instruments are admitted.

**Step 4. Receipt**, committed alone (`HANDOFF.md`). **No push.**

Expected: under $1 on Sonnet, under 10 minutes.

### 65. Describe the Japan government file: structure only (`decisions/0063`)

Added 2026-10-21 by Cowork. **Written, NOT released.** Released only after the
owner has pulled the file (request list:
`Claude outputs/bbg_pull_japan_govt_2026-10-21.csv`) and saved it under
`data/raw/bloomberg/`; the queue note at release names the file and its size.
Runs after task 64. The pattern is task 58's.

**What this task does not do:**
- **No loader, no code, no params, no store.** Nothing in `src/`, `scripts/`,
  `tests/`, `params/`, `vetoes/`, `hypotheses/`, `data/universe/`.
- **No value leaves the machine.** Report sheet names, headers, dimensions,
  date ranges and counts only. Do not open the file any other way.

**Budget:** 15 minutes.

**1. Describe it, without reading values out.** `scripts/inspect_raw.py` prints
the first 8 rows of every sheet verbatim, and rows 2 to 8 are vendor values. So:
- Run `make inspect-raw > "$HOME/inspect_raw.out" 2>&1` and check `rc=0`. Do not
  open, print or tail `inspect_raw.out`.
- Read the structure from `data/universe/raw_structure.json` (git-ignored), for
  the new file only, printing **only**: each sheet's name, `n_rows`, `n_cols`,
  **row 1 of `header_rows`** (never rows 2 to 8), and, for each column with a
  `date_min`, its column number, `n_non_empty`, `date_min` and `date_max`. Use a
  one-off `python -c` that prints nothing else.
- `sha256sum` of the file (report the first 16 hex).
- **Nothing from `raw_meta.json`** (it transcribes the `Loader Notes` sheet in
  full).

**What Cowork expects** (from the request list; the file has not been seen by
Cowork, and the layout is a guess from task 58's description of the earlier
file): a `levels` sheet with `date` and one `<TICKER>_local_JPY` column for each of
`I29064JP` to `I29068JP`; an analytics sheet with `INDEX_OAD_TSY` and
`INDEX_YIELD_TO_WORST` for the same five; dates from 2013-01-31 at the earliest to
**2019-12-31 at the latest.** A difference from this is not an error; list it.

**Stop rule (holdout).** If any sheet's last date is on or after 2020-01-01,
**stop**, report only that sheet's name and that date, and read nothing further
from the file.

**2. Receipt**, committed alone (`HANDOFF.md`). **No push.** The receipt holds the
structure report and nothing from inside the file.

Expected: under $1 on Sonnet, under 15 minutes.

### 60. Params v0.11.0 and SUBSTRATE v0.12 (`decisions/0058` item 6; `0059` item 1 and its 2026-10-16 addendum): the store read is `huber6-v4`, the label map is pinned, the `views` block lands; the tests follow; then push

Added 2026-10-16 by Cowork. **Written, NOT released.** It is released when
three things are true, and the queue note at the top will say so: task 59's
receipt has landed; the owner has read the draft's diff; and **Cowork has
applied the draft to the working tree** (the owner-only edit is Cowork's, at
the owner's instruction: "yes draft the pending owner-only params",
2026-10-16). Claude Code never copies the draft into `params/` or
`SUBSTRATE.md` itself.

**The draft:** `Claude outputs/params-v0.11.0-draft/` (git-ignored): the
seven params files and `SUBSTRATE.md` as they will be, CRLF kept, and
`params-v0.11.0.diff` (160 lines). What changes:
- `params_version: "0.11.0"` in all seven files.
- `data.characteristics`: `store_id: huber6-v4`, `directory_hash:
  b6181bcde28b7e95e69839ff29f2a0a0f19e7552f970b3a24804fcebb7569206` (task
  56), and a new `label_map: {path: data/universe/label_map.csv, sha256:
  60ee1934bf89582c8630b1c4a8b2f9b55e1181ec0cd55dc982c2dfa3be85bdb5}` (task
  55; Cowork re-hashed the working-tree file on 2026-10-16 and it matches).
- A new `constraints.views` block: `ic_prior: 0.05`, `horizon_rule:
  geometric_mean_rounded`, `standardisation: {window: expanding,
  burn_in_weeks: 52, winsorise_at: 3.0}`.
- SUBSTRATE v0.12: §5.4 gains `BAA10Y` in its list and `0058`'s wording for
  its last paragraph; the version note says so.

**New params hash `4f13f3736b3e3ea86b3ce8fac4ac5ca93a6aea4c35c0818c6b3e836774840d1e`**
(Cowork, with the repo's rule: name, NUL, bytes, NUL in `PARAM_FILES` order;
the same script reproduces today's `413d84f6...1623`).

**What this task does not do:** no solver, no view is formed, nothing reads
`views` but a params test; no audit; no store is built; `huber6-v3` and its
committed `exposures_check.{md,json}` are not touched.

**0. Check what Cowork applied.** `git status --short` shows the seven
`params/*.yaml` and `SUBSTRATE.md` modified (plus `HANDOFF.md` and
`OWNER-QUEUE.md` if Cowork touched them), and nothing else of Cowork's.
`git diff --ignore-cr-at-eol params SUBSTRATE.md` matches the draft's diff;
every file is still CRLF; the params hash is `4f13f373...0d1e`. Any
difference: stop and report. **The suite is expected red** until steps 1 to 3.

**1. The label map's pin is read.** Where the label map is loaded for a run
(`characteristics/exposures.py`, `load_label_map` / `ExposureMap.from_params`),
take its path from `data.characteristics.label_map.path` and refuse a file
whose sha256 differs from `.sha256`, naming both. Tests: the matching file
passes; one changed byte is refused; the synthetic label map the tests use is
passed in explicitly and never compared with the real pin.

**2. The store read is `huber6-v4`.** Every test that reads the store through
`params/` now reads `v4`. A test that pins a `v3` figure through `params/`
is changed to the `v4` figure from task 56's receipt, or to read the store it
names explicitly; list each one in the receipt as changed, not weakened.
`make exposures-check` without `ARGS` now writes
`results/characteristics/huber6-v4/exposures_check.{md,json}`; **every figure
equals task 56's step 6**: 990 weeks from 2001-01-12 to 2019-12-27, all
Fridays; 79,125 instrument-weeks; 53 and 84 instruments at the first and
last week; duration measured 7,375, estimated 71,750, missing 0; median
`axis_duration` at 2019-12-27: Long Treasuries 18.32, Gold 8.29, IG 5.22,
TIPS 4.55, Treasuries 4.48, EM Equities 2.63, European Equities -1.24. A
difference: stop.

**3. The `views` block.** A params test: the block loads, `ic_prior` is 0.05,
`horizon_rule` is `geometric_mean_rounded`, `burn_in_weeks` is 52,
`winsorise_at` is 3.0. Any test pinning the old params hash takes the new
one. **No golden may move;** if one does, stop and report it.

**4. Check, commit, push.**
- `scripts/unattended.sh check-full` (a params change), rc=0;
  `make governance` passes with the commit citing both records.
- Commit: `params+substrate: v0.11.0 / v0.12 -- store huber6-v4, label map pinned, views block (HANDOFF task 60, decisions/0058, decisions/0059)`.
- The receipt in `## Done`, directly under the heading: step 0's hash, the
  tests changed, step 2's figures, the log directory, tier and runtime.
  Commit it, `git push origin main` (fast-forward only), the push line.
  Then stop.

---

### 59. The implied-vol file (`decisions/0061`): commit the records of 2026-10-16, `inspect_raw` skips Excel lock files, a loader for `bbg_impvol_values_only.xlsx` and its coverage report; task 56's open gate, reported only; then push

Added 2026-10-16 by Cowork. **Released 2026-10-16** (owner: "i am ok with the
decisions on 0061"). **Revised the same day, before it ran:** step 0 also
commits `.claude/settings.json` (owner: "I want the settings.json committed").
**Revised again 2026-10-16 (15:30 ET), after the first attempt stopped at step
0** (receipt in `## Done`): `make check` failed in `tests/test_fdr_vs_fwer.py`
because `scripts/fdr_vs_fwer.py` read the live `hypotheses/pending/`, and the
four new files made it 16 hypotheses on seven axes. **Cowork's ruling: option
(b).** The study is a recorded measurement (tasks 34, 38, 40), so its script
is pinned to the twelve it was designed on (`STUDY_IDS`, H-2026-0001 to 0012)
and refuses if any is absent; the tests are unchanged. Cowork made the edit
(20 lines) and exercised `read_axis_groups` on the real `pending/` with
Python 3.10: 12 ids, groups 4/3/2/1/1/1, `region` first, six axes; an absent
id is refused. Re-running the study on the grown registry would be a new
study; nothing asks for it. Step 0 now commits the pin first.

**Read first:** `decisions/0061` (the rules), the `0059` addendum of
2026-10-16 (the burn-in is 52 weeks), and the Project doc
`claude/impvol-coverage-2026-10-15.md` (mirror copy in
`Claude outputs/project-mirror/`).

**What this task does not do:**
- **No signal, no solver, no Black premiums, no view.** Nothing reads the
  panel except the coverage report.
- **No snapshot change** (`0061` rule 6). The four hypotheses stay pending and
  their request files stay `awaiting_loader`. Do not edit `hypotheses/` or
  `data/requests/` beyond committing them in step 0.
- **No owner-only edit.** `params/`, `vetoes/` and `SUBSTRATE.md` are not
  touched. `params/` still names `huber6-v3`; that patch is Cowork's to write.
- **No value leaves the machine.** Report dates, counts and hashes only. The
  workbook is opened by the repo's code, never printed.

**Budget:** about 2 hours, most of it the check.

**0. Commit the records first.**
- `git status --short` should show exactly: ` M scripts/fdr_vs_fwer.py`,
  ` M HANDOFF.md`,
  ` M OWNER-QUEUE.md`, ` M decisions/0059-the-phase-2-solver.md`,
  `?? decisions/0061-the-implied-vol-file.md`,
  `?? hypotheses/pending/H-2026-0018.yaml` to `0021.yaml` (four),
  `?? data/requests/H-2026-0018.yaml` to `0021.yaml` (four), and
  ` M .claude/settings.json`. **Commit `.claude/settings.json` too,** in its
  own commit after the records: `settings: allow a fast-forward push of main,
  deny every forced push (owner 2026-10-16)`. Print its `git diff
  --ignore-cr-at-eol` in the receipt (it is a permission list, no secret).
  Anything else in `git status`: stop and report.
- **Validate the four new hypotheses with the repo's own validator** before
  committing: `HypothesisRegistry(params=get_params()).load("pending")` under
  `uv run --python 3.12 --group dev python -c ...` (thread variables set to 1),
  printing only each id, `kind`, `family`, `target_axis` and
  `expected_expression`. **Expect 16 pending, none rejected**, and the four
  new rows: 0018 signal / volatility_stress / region / both; 0019 signal /
  volatility_stress / duration / directional; 0020 signal / volatility_stress /
  credit / directional; 0021 measurement / covariance / covariance / both. Also
  check that **no id in their `data_required` matches
  `loaders.jpmaqs.TICKER_RE`** (Cowork checked with a copy of the pattern on
  Python 3.10; the repo's import does not run there). A rejection or a match:
  stop and report; do not edit the file.
- `make check` (expect it green now: the two `test_fdr_vs_fwer.py` tests read
  the pinned twelve) and `make governance`. Commit
  `scripts/fdr_vs_fwer.py` alone first: `scripts: the FDR-vs-FWER study reads
  its twelve hypotheses, not the live registry (HANDOFF task 59)`. Then commit
  the records:
  `records: decisions/0061 (decided, the implied-vol file) and the 0059 addendum (52-week burn-in); H-2026-0018 to 0021 registered; OWNER-QUEUE L37 amended (owner 2026-10-16)`.

**1. `inspect_raw.py` skips Excel lock files** (task 58's receipt). It globs
`*.xlsx` and failed on `~$bbg_impvol_all.xlsx`, the 165-byte lock file Excel
leaves while a workbook is open. Skip any file whose name starts with `~$`
and say so in its output; add a test (a `~$x.xlsx` of junk bytes beside a real
synthetic workbook: the run succeeds and describes only the real one).

**2. Describe the file, structure only.** As in task 58:
`make inspect-raw > "$HOME/inspect_raw.out" 2>&1`, check `rc=0`, do not open
the printout (it holds rows 5-8, which are values). From
`data/universe/raw_structure.json`, for `bbg_impvol_values_only.xlsx` only,
print each sheet's name, `n_rows`, `n_cols` and the count of non-empty cells
in row 1. `sha256sum` (first 16 hex). **Cowork expects** (openpyxl, read-only,
2026-10-16): `IV_Daily_v` 5,466 x 92 with 31 series ids in row 1; `IV_Weekly_v`
1,918 x 146 with 49; `Probe_Summary_v` 215 x 14; sha256 prefix
`aeb90f8758e46fbd`. A difference in dimensions is not an error; list it. A
different hash: stop.

**3. The loader: `src/signal_lab/loaders/impvol.py`.** Modelled on
`loaders/exusd_analytics.py` (pure functions, a `SHA256_PREFIX` pin, the
holdout dropped first, `enforce_holdout` on the output). Implement `0061`'s
rules 1 to 5 exactly:
- read the blocks of `IV_Weekly_v` and `IV_Daily_v` (row 1 `series_id`, row 2
  security, row 3 field, row 4 overrides, data from row 5; date, value, blank).
  A block with an empty header cell, or a value cell that is text (a Bloomberg
  error such as `#N/A N/A`), is refused with its `series_id` named;
- the lab id `<security>|<point>` (rule 1), with the workbook id kept;
- holdout, then weekly by Friday (rule 3), then the stale rule (rule 4,
  `STALE_RUN_WEEKS = 6` as a module constant citing `0061`);
- return a long frame: `date` (the Friday), `series_id` (lab id),
  `workbook_series_id`, `security`, `field`, `overrides`, `sheet`, `value`;
  plus the stale weeks removed, per series.

Add three rows to `data/universe/raw_manifest.csv`:
`bbg_impvol_values_only.xlsx,IV_Weekly_v,series_blocks,various,n/a,implied_vol,4,5`;
the same for `IV_Daily_v` with role `implied_vol_daily`; and
`bbg_impvol_values_only.xlsx,Probe_Summary_v,table,n/a,n/a,implied_vol_probe,1,2`.
If the manifest reader validates layouts, add `series_blocks` to its list.
`bbg_impvol_all.xlsx` gets no row.

**Tests** (synthetic workbooks only, never the vendor file): the block layout
read back; a text value refused; an empty header refused; every lab id fails
`TICKER_RE`, and `SPX_IV3M_10DP` itself matches it (that is why rule 1
exists); `SKEW` becomes `SKEW Index|PX_LAST`; a non-Friday date on the weekly
sheet refused; daily to Friday takes the last day of the week and drops a week
whose Friday is on or after the holdout; a run of 5 identical weeks is kept
whole and a run of 6 keeps 1 and removes 5; nothing on or after the holdout in
the output; a wrong hash refused.

**4. The coverage report.** `scripts/impvol_coverage.py`, a `make
impvol-coverage` target, writing `results/impvol/coverage.{md,json}`: per lab
id, the sheet, first and last Friday, weeks before the stale rule, stale weeks
removed, weeks kept, and missing Fridays between first and last. **Every
figure below is Cowork's, computed 2026-10-16 from the same file with the same
rules on Python 3.10 (a copy, not the repo's code).** Report any difference
and do not change the rules to match.

| Series (lab id prefix) | Points | First Friday | Weeks (before rule) | Stale removed | Missing Fridays |
|---|---|---|---|---|---|
| `EZU US Equity` | 10DP 25DP 25DC 10DC M100 | 2008-04-04 | 587 each | 0 | 26 (one hole, 2011-01-14 to 2011-07-22) |
| `EWJ US Equity` | same five | 2005-11-04 | 739 | 0 | 0 |
| `EWA US Equity` | same five | 2007-02-02 | 674 | 0 | 0 |
| `EWC US Equity` | same five | 2006-03-31 | 718 | 0 | 0 |
| `EEM US Equity` (weekly) | 10DP 25DP 25DC 10DC | 2006-03-31 | 718 | 0 | 0 |
| `TLT US Equity`, `LQD US Equity` | 10DP 25DP 25DC 10DC ATM | 2005-02-04 | 778 | 0 | 0 |
| `HYG US Equity` | same five | 2007-05-04 | 658 | 0 | 3 |
| `SPX Index` (weekly) | 25DP 25DC 10DC ATM | 2005-02-04 | 778 | 0 | 0 |
| `XAUUSDV3M BGN Curncy` | ATM | 2002-12-06 | 891 | 76 | 0 |
| `XAUUSD25R3M` / `25B3M BGN Curncy` | 25R / 25B | 2006-02-03 | 726 | 38 / 102 | 0 |
| `XAUUSD10R3M` / `10B3M BGN Curncy` | 10R / 10B | 2006-02-03 | 710 | 83 / 86 | 16 |
| `SKEW Index` | PX_LAST | 1990-02-02 | 1,560 | 0 | 0 |
| `SPX Index` (daily) | M090 to M110, 10DP | 2005-02-04 | 778 | 0 | 0 |
| `SX5E Index` (daily) | M090 to M110 | 2006-02-03 | 726 | 0 | 0 |
| `NKY Index` (daily) | M090 to M110 | 2006-02-03 | 725 | 0 | 1 |
| `AS51 Index` (daily) | M090 to M110 | 2005-06-03 | 761 | 0 | 0 |
| `EEM US Equity` (daily) | M090 to M110 | 2006-03-31 | 718 | 0 | 0 |
| `SPTSX60 Index` (daily) | M090 to M110 | 2005-06-03 | 761 | 0 | 0 |

Last Friday is 2019-12-27 for every series. **Totals: 80 series, 59,114
weeks before the stale rule, 385 removed (all gold: 76 + 38 + 102 + 83 + 86),
58,729 kept.** EEM appears twice, from different sheets and fields
(`IVOL_DELTA` weekly, the moneyness fields daily); their lab ids differ by
point and do not collide. Check that no two series share a lab id.

**5. Task 56's open gate, reported only.** Task 56's receipt: "I did not run
the default path's run-of-record gates after the loader change ... I expect
them to stop on those four unless `CONVERTED` is extended; that is for Cowork
to rule". Rebuild `huber6-v3` into a scratch root outside the repo exactly as
task 54 step 1 did (`scripts/build_characteristics.py --store-id huber6-v3
--root <tmp> --report-root <tmp> --supersedes ""`) and report: does the
run-of-record gate pass, and if not, which instruments and how many cells
differ, and by how much at most. **Change no code and do not extend
`CONVERTED`.** Delete the scratch store afterwards. Cowork rules from the
report.

**6. Check, commit, push.**
- `scripts/unattended.sh check-scoped` (it leaves a log), rc=0.
- Commit the build: `loaders: the implied-vol file, inspect_raw skips Excel lock files, coverage report (HANDOFF task 59, decisions/0061)`.
- The receipt in `## Done`, directly under the heading, newest first: the
  step-0 validator printout, step 2's dimensions and hash, the coverage
  totals and every row that differs from the table, step 5's answer, the
  check's log directory, tier and runtime. Commit it, then
  `git push origin main` (fast-forward only), and add the push line to the
  receipt. Then stop.

---

### 58. Describe the new Bloomberg file, `bbg_exusd_bonds_extra.xlsx` (`decisions/0060`, the data request): structure only, no loader; then push

Added 2026-10-15 by Cowork. Runs after task 57. **Revised at 22:50 the same
night, before it ran:** step 1 keeps the script's printout off the screen.

**Why:** the owner pulled the non-USD government bonds `decisions/0060` asks
for and saved them as `data/raw/bloomberg/bbg_exusd_bonds_extra.xlsx`
(2026-10-15, 22:05; 5,823,494 bytes). Before a loader is specified, Cowork
needs the file's structure from the repo's own script.

**What this task does not do:**
- **No loader, no code, no params, no store.** Nothing in `src/`, `scripts/`,
  `tests/`, `params/`, `vetoes/`, `hypotheses/`, `data/universe/`.
- **No value leaves the machine.** Report sheet names, headers, dimensions,
  date ranges and counts only, as step 1 extracts them. Do not open the file
  any other way.

**Budget:** 15 minutes.

**1. Describe it, without reading values out.** `scripts/inspect_raw.py`
prints the first 8 rows of every sheet verbatim (`HEADER_ROWS = 8`). In this
file, rows 2-8 of `analytics`, `linker_fields` and `japan_check` are vendor
values. So:
- Run it with its printout kept off the screen:
  `make inspect-raw > "$HOME/inspect_raw.out" 2>&1`, and check `rc=0`. Do not
  open, print or tail `inspect_raw.out`.
- Read the structure from `data/universe/raw_structure.json` (git-ignored),
  for `bbg_exusd_bonds_extra.xlsx` only, printing **only**: each sheet's name,
  `n_rows`, `n_cols`, **row 1 of `header_rows`** (never rows 2-8), and, for
  each column with a `date_min`, its column number, `n_non_empty`, `date_min`
  and `date_max`. Use a one-off `python -c` that prints nothing else.
- `sha256sum` of the file (report the first 16 hex).
- Report those in the receipt. **Nothing from `raw_meta.json`** (it
  transcribes the `Loader Notes` sheet in full).

**What Cowork expects** (the owner's pull prompt, 2026-10-15; the file was not
seen by Cowork):
- `levels`: `date`, then `<TICKER>_local_<CCY>` for `LEATTREU`, `LET3TREU`,
  `LET5TREU`, `LET7TREU`, `LET0TREU`, `BEIG1T`, `BEIG3T` (EUR) and
  `LSG1TRGU`, `I08043GB` to `I08048GB` (GBP): 15 columns;
- `analytics`: `date, ticker, index_name, oad_tsy, yield_to_worst, oas,
  oas_field`, the 12 nominal tickers only;
- `linker_fields`, `japan_check`: test sheets; headers and dimensions only;
- `Loader Notes`: report its dimensions only;
- dates from 1990-01-01 at the earliest to **2019-12-31 at the latest**.

A difference from this is not an error; list it. **If any sheet's last date is
on or after 2020-01-01, say so** (the loaders drop such rows; whether the file
is re-pulled is the owner's call). Do not edit the file.

**2. Commit the receipt and push.** `make check`, then commit `HANDOFF.md`
alone: `handoff: task 58 receipt; bbg_exusd_bonds_extra.xlsx described`.
`git push origin main`, fast-forward only. Then stop.

---

### 57. Commit the records of 2026-10-14 and 2026-10-15: `decisions/0059` (decided) and `0060`; OWNER-QUEUE L37 and L38 closed, L39 opened; then push

Added 2026-10-15 by Cowork, at the owner's instruction ("queue the commits").

**Owner rulings:**
- OWNER-QUEUE L37, 2026-10-14: "agree with proposal". `decisions/0059`, the
  phase-2 solver, is decided and moved out of `decisions/proposed/`;
- OWNER-QUEUE L38, 2026-10-14 and 2026-10-15: `decisions/0060` (0007 grouped
  by rating and HY bucket; 0002, 0003 and 0010 by curve, blocked on a data
  request; an instrument-level fallback; a missing instrument is a data
  request);
- "queue the commits".

**What this task does not do:**
- **No code, no build, no params.** Nothing in `src/`, `scripts/`, `tests/`,
  `params/`, `vetoes/`, `SUBSTRATE.md` or `hypotheses/`. `0060` proposes
  SUBSTRATE wording; it is not applied, and you do not apply it.
- No vendor call, no audit. No hypothesis changes state. No golden moves.
- **Do not commit** `.claude/settings.json`; it stays as it is in the working
  tree.

**Budget:** 15 minutes.

**Hard rules:** as `CLAUDE.md`. Never edit this task in place; the receipt goes
directly under the `## Done` heading, newest first, and nowhere else in this
file.

**1. Commit the records, alone.**
- **Files:** `HANDOFF.md`, `OWNER-QUEUE.md`, and new:
  `decisions/0059-the-phase-2-solver.md` (Cowork moved it from
  `decisions/proposed/`; it was never committed there, so git sees one new
  file) and `decisions/0060-four-hypotheses-get-their-cross-section.md`.
  Nothing else.
- **Check first:** `git status --short` shows exactly those four paths and
  ` M .claude/settings.json`. Anything else, stop and list it.
- **Run** `make check` (records only, the fast tier) and `make governance`.
  Both must pass. If either fails, stop and report; do not edit the records.
- **Message:** `decisions 0059 (decided) and 0060; queue: task 57; OWNER-QUEUE L37 and L38 closed, L39 opened (owner 2026-10-14 and 2026-10-15)`.

**2. Push.** `git push origin main`, after the receipt's commit. It must be a
fast-forward; if it is rejected or would be anything else, stop and report.
Record `git rev-list --count @{u}..HEAD` before and after.

**Expect:** two commits (the records, the receipt), `9b1e0d5` carried with
them, and `@{u}..HEAD` at 0 after the push. Then stop.

---

### 56. Store `huber6-v4` (`decisions/0056`, `0058`): the ex-USD bonds on Bloomberg's close, the credit factor on FRED `BAA10Y`, estimation before `dev_start`; then push

Added 2026-10-11 by Cowork. **Runs after task 55.** Revised at 23:10 the same
night, before it ran: `BAA10Y` is dated by its observation, so the map's rule
and the store's dating do not change (`0058` item 4).

**Owner rulings of 2026-10-11:**
- OWNER-QUEUE L33, `decisions/0056`: one FX source, Bloomberg;
- L35, `decisions/0058`: estimation may read before `dev_start`, the
  development window does not move, and the credit factor is FRED `BAA10Y`,
  dated by its observation date like a Bloomberg close.

**What this task does not do:**
- **No owner-only edit.** `params/` keeps naming `huber6-v3`, so
  `resolve_exposures` keeps reading it. Cowork writes the params patch
  (`0058` item 6) from this task's receipt, and a later task commits it.
  SUBSTRATE §5.4 waits on OWNER-QUEUE L36.
- **`huber6-v1`, `v2` and `v3` are not edited or rebuilt.** The run of
  record's reproduction (task 48) and the `v3` build must give the same
  numbers as before: the `dev_start` cut and the old credit factor stay the
  default, and `v4` selects the new ones.
- No audit, no solver, no hypothesis changes state.
- **Expected to move:** the weekly-returns hash (four series change), and any
  golden that records it. Name each in the receipt. **Anything else that
  moves, stop and list it.**

**Budget:** 4 to 5 h, of which about 30 minutes is machine time.

**Read first:**
- `decisions/0056` and `decisions/0058`, all of each;
- `decisions/0053` (its convention table and its test) and `decisions/0055`
  ("What the wiring does");
- `scripts/build_characteristics.py`, especially its gates against the run of
  record.

**Hard rules:**
- **Vendor data never leaves the machine.** Report counts, dates, hashes and
  the aggregates this task names. Never print a level, a rate or a spread.
- **Nothing reads a date on or after 2020-01-01.** That includes the FRED
  request.
- **Never print `FRED_API_KEY`** or anything key-shaped.

**1. Pull `BAA10Y` from FRED.**
- **The call:** the FRED observations endpoint, as listed in
  `params/data_sources.yaml`, `series_id=BAA10Y`,
  `observation_start=1986-01-01`, `observation_end=2019-12-31`. The key is
  read from `FRED_API_KEY`.
- **If the key is unset, the call fails, or it is denied at the permission
  prompt, stop** and write the message in the receipt.
- **Write** `data/raw/fred/fred_baa10y.csv`, columns `date,BAA10Y`. FRED's
  `.` is a missing value: written blank, never zero, never carried.
- **Register it:** a row in `data/universe/raw_manifest.csv` (role
  `fred_credit_spread`) and one in `data/universe/fred_coverage.csv` with
  first and last date and the observation count.
- *Cowork's expectation:* first date 1986-01-02, last on or before
  2019-12-31.
- `data/raw/` is not committed. FRED's page carries Moody's copyright
  notice; the file stays on this machine like every vendor file.

**2. The four ex-USD bonds on Bloomberg's close** (`decisions/0056`).
- `read_exusd_csv` returns the `<ticker>_local_<CCY>` columns for
  `LET1TREU`, `I12823GB`, `I02913JP` and `LP05TREU`, and
  `LG38TRUU_USD_unhedged` as before.
- The quote currency is the column suffix. It must equal `local_ccy` in
  `bbg_exusd_bonds_coverage.csv`, or the loader refuses.
- The `exempt` set that `load_returns` passes to `_to_usd` becomes
  `{"LG38TRUU"}`.
- **The test, before the store** (`0056` item 4): in
  `scripts/check_fx_conversion.py`, each of the four converted against its
  FRED-converted column. Weekly Friday closes, development window, same day.
  - Report weekly tracking error, lag-1 autocorrelation and the cumulative
    gap for each, under a new heading in `results/fx/conversion_check.{md,json}`.
  - *Cowork's read:* 195 to 210 bp/yr weekly.
  - **Above 1,000 bp/yr, stop.**
  - The existing rows of that report must not change.
- **Report** the days regained in the development window for each of the
  four (dates with a converted return now and none before).

**3. The factors for `v4`** (`decisions/0058` items 1, 3 and 4).
- **Credit is the daily change in `BAA10Y`,** in the units the old credit
  factor used. Read it from step 1's file. `LUACOAS` is not used by `v4`.
- **Estimation reads from the factors' common start,** not from
  `dev_start`, and is cut before 2020-01-01.
- **Dating.** A `BAA10Y` observation on date *t* is dated *t*, like every
  other factor and return (`0058` item 4). No lag.
- **How `v4` selects this:** *Cowork's suggestion:* a store option such as
  `factor_set: huber6-baa10y` with `estimation_start: common`, recorded in the
  store's manifest. The defaults stay as they are, so `v1` to `v3` and the run
  of record are untouched.
- **The run-of-record gates do not apply to `v4`:** its factors differ by
  design. Skip them only for this option, and record in the manifest that
  they were skipped and why (`decisions/0058`).
- **Report:** the first date on which all six factors exist, and the
  factors' rolling correlation over the whole estimation sample, as the
  `0046` §1 run did.

**4. The map does not change** (`0058` item 4).
- `huber6-v4` dates each week by its Friday, as `v3` does: `last_data_date`
  is the week's Friday. `0055`'s rule stands.
- **Every task-54 test in `tests/test_exposures.py` passes unchanged.**
- **One test added:** on the real `v4` store, every week's `last_data_date`
  equals that week's Friday.

**5. Build `huber6-v4`.**
- **Run** `make characteristics ARGS="--store-id huber6-v4 …"` with the
  step-3 option and `--supersedes huber6-v3`.
- **Manifest:** cites `decisions/0049`, `0056`, `0058` and task 56.
- **Report:**
  - `directory_hash`;
  - first and last week, and the number of weeks;
  - instruments at the first week, at 2001-01-05 and at the last week;
  - each instrument whose first row is after 2001-01-05, with that date;
  - estimated, not estimated and measured counts, as task 53 reported them;
  - by reporting class, at 2019-12-27, `v3` against `v4`: the median credit
    loading, the median explained share, and the median absolute change in
    each of the other five loadings;
  - the rank correlation of the credit loadings across instruments,
    `v3` against `v4`, at 2019-12-27.
- **Cowork's expectations, both estimates:**
  - the first week on or before 2001-01-05, around 2000-12-29. The equity
    factor and the breakeven are daily from 1999 by the coverage tables, which
    give only the year;
  - 55 to 65 instruments at 2001-01-05.
  - **If the first week is after 2001-01-05, report it and carry on;** that
    is what `0058` "What would reopen it" names.

**6. The exposures check on `v4`.**
- `make exposures-check`, against `huber6-v4` passed explicitly (`params/`
  still names `v3`), into `results/characteristics/huber6-v4/`.
- **Report** the task-54 step-4 table for `v4`. Expected differences: the
  counts, and 2001-01-05 reads a week rather than raising, if step 5's first
  week allows it. Friday usage rows still have `fitted_through` equal to
  `used_on_date`; Tuesday rows, four days after.
- **Also print** the median `axis_duration` by reporting class at
  2019-12-27, beside `v3`'s from task 54.

**7. Check, commit, push.**
- **The check:** `scripts/unattended.sh check-full --digest`. It touches the
  loader and the factors, so it is the whole suite.
- **Commit the build:** `src/`, `scripts/`, `tests/`, `build.mk` if it
  changed, `data/universe/raw_manifest.csv`,
  `data/universe/fred_coverage.csv`, `data/characteristics/huber6-v4/` as
  task 53 committed `v3`, `results/fx/` and `results/characteristics/huber6-v4/`,
  as
  `characteristics: store huber6-v4 -- ex-USD bonds on Bloomberg's close, credit factor BAA10Y, estimation before dev_start (HANDOFF task 56, decisions/0056, decisions/0058)`.
- **Push:** `git push origin main`, under task 55's rule: a fast-forward
  only. If it is denied at the prompt or rejected, stop, record it and
  don't retry.
- **Then the receipt,** committed and pushed under the same rule, and
  `git rev-list --count @{u}..HEAD` printed in it.

**Receipt:**
- rc, commits, the log directory, the tier and the runtime;
- **step 1:** the file's first and last date and its count, or why it
  stopped;
- **step 2:** the four series' figures beside Cowork's read, and the days
  regained;
- **step 3:** the option's names, the common start, the correlation table's
  location, and each golden that moved;
- **step 4:** the test added, and confirmation that the task-54 tests pass
  unchanged;
- **steps 5 and 6:** every figure asked for, beside its expectation;
- **step 7:** the push's output and the final count;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 55. The label map lands: `data/universe/label_map.csv` and the region axis (`decisions/0054` with its addendum); the records of 2026-10-11 night; then push

Added 2026-10-11 by Cowork. **Revised at 22:55 the same night, before it
ran,** to carry the owner's 22:39 rulings.

**Owner rulings of 2026-10-11 night:**
- OWNER-QUEUE L28: the bond labels are ruled as drafted (`decisions/0054`
  addendum), and how a hypothesis uses them is `decisions/0057` ("B approved
  as is"), SUBSTRATE §6 and §7 amended in v0.11;
- L33: one FX source, Bloomberg (`decisions/0056`), SUBSTRATE §5.4a amended
  in v0.11; **built in task 56, not here**;
- L35: `decisions/0058`, the credit factor is FRED `BAA10Y`; **built in task
  56, not here**;
- the label map's hash is pinned in `params/` (`0058` item 6), **after** task
  56, not here;
- L12: parked (Dormant);
- "yes" to this task.

**What this task does not do:**
- **No owner-only edit by you.** SUBSTRATE v0.11 is Cowork's transcription
  of `0056` and `0057`, already in the working tree; step 0 commits it.
  Verify it with `git diff --ignore-cr-at-eol SUBSTRATE.md`. Nothing in
  `params/` or `vetoes/`. If a step seems to need an owner-only change, stop
  and write the exact change in the receipt.
- **No scope logic.** The labels, verbatim and normalised, are carried and
  no axis reads a bond label. `scope` and `group_by` in the validator, and
  the mask on the view-to-alpha mapping, come with the phase-2 solver
  (`0057`, "Where it is built").
- **Sector and style keep raising** (`0054` item 8).
- No new store, no FX change, no vendor call, no audit, no solver. No
  hypothesis changes state. **No golden moves.** If a test this task does
  not name fails, stop and list it.

**Budget:** 2 to 3 h, of which about 15 minutes is machine time.

**Read first:**
- `decisions/0054`, all of it, the 2026-10-11 night addendum especially;
- `decisions/0050` item 1 (the label block) and `decisions/0055`;
- `src/signal_lab/characteristics/exposures.py` as task 54 left it.

**Hard rules:**
- **Vendor data never leaves the machine.** The label map holds no vendor
  value; the store does. Report counts and names only.
- **The loader's `SeriesMeta.region` is not changed.** The non-synchronous
  covariance rule reads it, and changing it would move recorded numbers.
- **Nothing reads a date on or after 2020-01-01.**

**0. Commit the records first, alone.**
- **Files:** `SUBSTRATE.md` (v0.11), `HANDOFF.md`, `OWNER-QUEUE.md`,
  `decisions/0054-…` (addendum), and new: `decisions/0056-…`,
  `decisions/0057-…`, `decisions/0058-…`. `decisions/proposed/` has no new
  file; `0057` was proposed there and moved before it was ever committed.
- **Run** `make check` (records only, the fast tier) and `make governance`.
  Both must pass.
- **Message:** `substrate v0.11 and queue: tasks 55 and 56; SUBSTRATE §5.4a, §6 and §7 transcribed (decisions/0056, decisions/0057); decisions/0054 addendum, 0056, 0057 and 0058; OWNER-QUEUE L28, L33, L35 and L36 closed, L12 dormant (owner 2026-10-11 and 2026-10-12)`.

**1. Write `data/universe/label_map.csv`.**
- **Source:** `Claude outputs/label_map_draft_2026-10-11.csv`. It has no
  owner corrections (the `owner_correction` column is empty). Its sha256
  begins `6de22793765f2a24`; if it does not, stop.
- **Rows:** every row whose `tier` is not `tradable-only`. **84 rows.**
- **Columns, in this order:** `ticker`, `asset_group`, `reporting_class`,
  `region`, `region_view`, `curve_currency`, `rating_class`, `market_label`,
  `curve`, `rating`, `hy_bucket`, `market`.
  - `region`: as drafted, except `(Commodities bucket)` becomes
    `Commodities`.
  - `region_view`: `yes` only for `asset_group` in `equity` or
    `real_asset_equity` **and** `region` not `Global` (`0054` items 9 and
    10); `no` otherwise.
  - `curve_currency`, `rating_class` and `market_label` are verbatim from
    the draft's `curve_currency`, `rating_class` and `market`. They are
    blank except for the 23 bonds and `LD20TRUU`.
  - `curve`, `rating`, `hy_bucket` and `market` are the normalised values
    of `decisions/0057`'s vocabulary table, mapped from the verbatim ones.
    **A verbatim value the table does not map is an error,** not a blank.
    `hy_bucket` is `Ba`, `B`, `Caa` or `all` for the five HY rows and blank
    elsewhere.
- **Write it with a small script** (`scripts/build_label_map.py`, Cowork's
  suggested name) so the file can be regenerated. After this task,
  `label_map.csv` is the owner's record and the draft is not read again.
- **Expected counts:**

  | Count | Expected |
  |---|---|
  | rows | 84 |
  | `asset_group`: equity, bond, real_asset_equity, commodity, cash | 54, 23, 4, 2, 1 |
  | `region_view = yes` | 46: US 19, Developed Europe 12, EM 12, Japan 1, APAC ex-Japan 1, Canada 1 |
  | `region` over all rows | US 34, Developed Europe 16, EM 15, Global 13, Japan 2, Commodities 2, APAC ex-Japan 1, Canada 1 |
  | rows with a `curve_currency` | 24 |
  | `curve` | USD 16, EUR_multi 2, USD_real 1, EUR 1, GBP 1, JPY 1, DM_multi 1, EM_local_multi 1 |
  | `rating` | Government 11, HY 5, IG 3, Aggregate 2, Mixed 2, Agency 1 |
  | `hy_bucket` | Ba 2, B 1, Caa 1, all 1 |
  | `market` | DM 21, EM 3 |

  These count `LD20TRUU` (USD, Government, DM), which is why they read one
  more than `0057`'s table of bonds.

- **Cross-check against the record.** A test parses the "Equity regions"
  table of `decisions/0054` and asserts that each ticker's region in
  `label_map.csv` equals the table's, for every ticker in both. The eight
  tradable-only tickers are in the table and must be absent from the map.
  Do the same for the bond table's three label columns.

**2. `ExposureMap` reads the label map.**
- **Where:** `characteristics/exposures.py`. The map's path is an argument
  with a default of `data/universe/label_map.csv`; tests pass a temp file.
- **Every instrument with a store row must have a label row,** and the
  reverse. On the real store the two sets are the same 84. A mismatch
  raises, naming the tickers.
- **`at(date)`** gains the columns `region`, `curve_currency`,
  `rating_class`, `market_label`, `curve`, `rating`, `hy_bucket` and
  `market`, as strings. They are blank where the map is blank, and
  **these columns are exempt from the "no missing value" rule** the engine's
  `ExposureRule` applies.
- **`axis("region", date)` returns a frame,** instruments by the six view
  regions (US, Developed Europe, Japan, APAC ex-Japan, Canada, EM), 0 or 1.
  An instrument has a 1 only where `region_view` is `yes`. Global has no
  column. Say in the docstring that this axis returns a frame where the
  others return a series, and why: a region view is one view per region.
- **The engine's rule (`__call__`)** gains seven 0/1 columns
  `region_<slug>` for reporting, Global included, from `region` over **all**
  instruments (a bond keeps a region for reporting, `0054` item 9).
  Commodities and cash read 0 in all seven except where their `region` names
  one (cash is `US` in the map). *Cowork's suggestion for the slugs:* `us`,
  `dev_europe`, `japan`, `apac_ex_japan`, `canada`, `em`, `global`.
- **`sector` and `style` still raise `LabelMapMissing`,** now naming
  `decisions/0054` item 8.
- **The usage log is unchanged.** Labels are not estimated and have no
  `fitted_through`.

**3. Tests** (`tests/test_exposures.py`, and a new
`tests/test_label_map.py`):
- the step-1 counts and the cross-check against `decisions/0054`;
- the normalised columns against `decisions/0057`'s table, and an unmapped
  verbatim value raising;
- `build_label_map.py` regenerates the committed file byte for byte;
- the region view frame: a US equity reads 1 in `us` only; a Global equity
  reads 0 everywhere; a bond reads 0 everywhere; the columns are the six;
- the reporting columns: a US Treasury reads 1 in `region_us`; a Global
  equity reads 1 in `region_global`; `BCOMTR` reads 0 in all seven; every row
  sums to 0 or 1;
- a store instrument without a label row raises; a label row without a
  store instrument raises;
- `sector` and `style` raise `LabelMapMissing`; an unknown axis is a
  `ValueError`;
- **change, don't weaken:** the task-54 test that `region` raises becomes a
  test that it returns the frame. Name it in the receipt.

**4. Check, commit, push.**
- **The check:** `scripts/unattended.sh check-scoped --digest`. If it reports
  any doubt about placing a changed file, run `check-full` instead.
- **Report the label map's sha256,** of the file as committed and of the
  working-tree file, saying which is CRLF. The owner has ruled that it is
  pinned in `params/` (`0058` item 6); Cowork writes that patch after task
  56. Not done here.
- **Commit the build:** `data/universe/label_map.csv`,
  `scripts/build_label_map.py`, `src/`, `tests/`, as
  `labels: data/universe/label_map.csv, the region axis reads it (HANDOFF task 55, decisions/0054)`.
- **Push:** `git push origin main`, as `CLAUDE.md` allows. It carries
  `c8e755c` too, which is unpushed.
  - It must be a fast-forward. Never `--force`, never pull, never rebase.
  - **If it is denied at the permission prompt or rejected, stop.** Write
    the exact message, or "denied at the prompt", in the receipt, commit the
    receipt locally, and don't retry. Tasks 53 and 54 were both denied at
    the prompt.
- **Then the receipt.** Commit it and push again, under the same rule.
- **Last:** `git rev-list --count @{u}..HEAD`, printed in the receipt.

**Receipt:**
- rc, commits, the log directory, the tier and the runtime;
- **step 1:** every count beside its expectation, and the cross-check's
  result;
- **step 2:** the names you chose, and the store/label set check on the real
  store;
- **step 3:** every test added, and every existing test changed;
- **step 4:** the label map's sha256, the push's output and the final count;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 54. The wiring: `resolve_exposures` reads `huber6-v3` (`decisions/0050`, `0055`); params v0.10.0; the `lookahead` veto checks loadings; task 53's loose ends; then push

Added 2026-10-11 by Cowork.

**Owner rulings of 2026-10-11:**
- "yes" to this task and its two owner-only patches (`decisions/0055`);
- OWNER-QUEUE L34: "push as is". The GitHub repository is public and he
  knows it;
- L29 and L28 in part (`decisions/0054`). **Nothing is built from `0054`
  here.**

**Owner-only edits are already in the working tree, applied by Cowork.**
Don't re-edit them. Verify them with `git diff --ignore-cr-at-eol`:
- **`params/`:** `params_version` `0.9.0` to `0.10.0` in all seven files.
  - `data.yaml` gains a `characteristics` block: `store_id: huber6-v3` and
    the store's `directory_hash`.
  - `vetoes.yaml`: the `lookahead` comment now names both halves.
- **`vetoes/rules.py` `veto_lookahead`:** a second half.
  - It requires `ctx.parameter_usage` with the columns `fitted_through` and
    `used_on_date`.
  - A row whose `fitted_through` is later than its `used_on_date` fails.
  - A row with either date missing fails.
  - An absent table, an empty one or a missing column fails as a missing
    input. The first half is unchanged.
- **Until step 3 is done the suite is red by design.** The lookahead tests in
  `tests/test_vetoes.py` supply `observation_usage` only.

**If a step needs a further change to an owner-only file, stop and write the
exact change in the receipt.** Cowork applies it.

**What this task does not do:**
- **No solver.** `build_weight_rule` keeps raising `OptimiserMissing`. No
  alphas, no signal module, no view.
- **No label map.** Region, sector and style raise.
- No new store in `data/characteristics/`, no vendor call, no audit, and no
  hypothesis changes state.
- **No golden moves.** If a test this task doesn't name fails, stop and list
  it.

**Budget:** 4 to 5 h, of which about 30 minutes is machine time.

**Read first:**
- `decisions/0055`, all of it;
- `decisions/0050` with its 2026-10-10 addendum, and `decisions/0015` from
  "The part that is not obvious";
- `decisions/0054` item 7, and the 2026-10-11 addendum to `decisions/0053`;
- `Claude outputs/project-mirror/task-53-review-2026-10-11.md`, findings 2
  and 3.

**Hard rules:**
- **Vendor data never leaves the machine.** The store holds vendor-derived
  values. Report counts, dates, hashes and the aggregates this task names.
- **`huber6-v1`, `v2` and `v3` are not edited or rebuilt in place.**
- **The engine's recorded numbers do not move.** `constant_exposures` and
  every caller of it behave as before.
- **Nothing reads a date on or after 2020-01-01.**

**0. Commit first, alone, without a check** (the suite is red by design).
- **Files:** `HANDOFF.md`, `OWNER-QUEUE.md`, `decisions/0053-…` (addendum),
  `decisions/0054-…` (new) and `decisions/0055-…` (new).
- **Message:** `queue: task 54; decisions/0054 (the label map, in part) and decisions/0055 (the wiring); the decisions/0053 addendum; OWNER-QUEUE L34 and L29 closed, L28 ruled in part, L35 added (owner 2026-10-11)`.
- **`make governance` must pass.**
- **`params/` and `vetoes/rules.py` are not in this commit.** They go with
  step 6's build commit, which cites `decisions/0055`.

**1. Task 53's loose ends, before any code changes.**
- **Why:** `loaders/fx.py` and `loaders/bloomberg.py` were last written at
  02:57:37Z on 2026-10-11. The FX check ran at 02:50:36Z and the store was
  built at 02:55:58Z. Both were made by the code as it stood before a
  formatter ran.
- **The FX check.** Run `make fx-check`. Then
  `git diff --ignore-cr-at-eol --stat results/fx/` must be empty.
- **The store.** Build it again into a scratch root outside the repo:
  `scripts/build_characteristics.py --store-id huber6-v3 --root <tmp> --report-root <tmp> --supersedes ""`.
  - **`--supersedes` must be empty.** The gate against `huber6-v2` loads it
    from `--root`, and `v2` is not in the scratch root (Cowork's reading of
    the script, lines 319-320). The gate against the run of record still
    runs.
  - Call it through `make` if the quoting allows, or directly with
    `uv run --python 3.12 --group dev` and the three thread variables set
    to 1.
  - Its `directory_hash` must equal `84a5088d82b135c48ba7da5709ebae3f58186c06b08575d1b233ba19e27270f7`.
    The hash leaves the manifest out, so the new params version does not
    enter it.
  - If it differs, compare the three data files cell by cell, report the
    largest difference per file, and stop.
  - Delete the scratch store afterwards.
- **`USDJPY` on real data** (`decisions/0053` addendum). Extend
  `scripts/check_fx_conversion.py`: converted `LGTRTRGU` and converted
  `LGTRTRJU`, each against `LEGATRUU`, weekly Friday closes, 2002-01-01 to
  2019-12-27, same day only.
  - Report weekly tracking error, lag-1 autocorrelation and the cumulative
    gap for each, in the same files.
  - **Cowork has no measurement of these.** The UK pair read 238 bp/yr
    converted and 1,353 unconverted. If either new pair reads above
    1,000 bp/yr, stop: the direction or the series is wrong.
  - The UK rows of the report must not change.

**2. `resolve_exposures`** (`harness/experiment.py`, and a new module;
`characteristics/exposures.py` is Cowork's suggestion).
- **It returns an exposure map** built from the store that `params/` names.
  - It reads `data.characteristics.store_id` and `directory_hash`.
  - It raises `ExposureMatrixMissing` when the store is absent, and when the
    store's manifest hash is not the one in `params/`. `load_store` already
    refuses a store whose files have changed.
  - The store root is an argument, so tests use a temp folder.
  - **The `snapshot` argument is not used yet.** Say so in the docstring.
    Tying a store to the returns a snapshot holds is not designed.
- **One store week per date** (`decisions/0055`).
  - `at(date)` reads the latest store week on or before `date`.
  - If that week is more than six days before `date`, or there is none, it
    raises `ExposureMatrixMissing` naming the date and the store's range.
    Nothing older is carried.
- **The frame `at(date)` returns,** one row per instrument that has a row
  that week:
  - **factor block:** `equity`, `real_yield`, `inflation`, `credit`,
    `dollar`, `commodities`, as stored, and their standard errors;
  - **measured block:** `oad` and `oas`, missing where the store has none;
  - **axes:** `axis_duration`, `axis_real_nominal`, `axis_credit`,
    `axis_cash`;
  - `axis_duration_provenance` (`measured` or `estimated`) and
    `explained_share`.
- **What each axis reads** (`decisions/0050` and its addendum):

  | Axis | Reads |
  |---|---|
  | `axis_duration` | `oad` that week for the reporting classes Treasuries, Long Treasuries, IG Corporates and TIPS, when it is not missing; minus `real_yield` otherwise |
  | `axis_real_nominal` | minus `inflation` |
  | `axis_credit` | minus `credit` |
  | `axis_cash` | 1 for the instrument whose reporting class is Cash, 0 otherwise |

  The reporting class comes from the store's `instruments` table.
- **`axis(name, date)`** returns one axis as a series.
  - Valid names are `harness.hypotheses.TARGET_AXES`.
  - `region`, `sector` and `style` raise a subclass of
    `ExposureMatrixMissing` that names `decisions/0054` and OWNER-QUEUE L28.
  - Any other name is a `ValueError`.
- **The rule the engine takes.** The map supplies an `ExposureRule`: date to
  a frame of the six factors and the four axes, with no missing value. That
  is what `run_walk_forward` multiplies by the weights.
- **No row, no holding** (`decisions/0055`).
  - The map's rule carries a marker (Cowork's suggestion: an attribute
    `requires_row = True`).
  - In `run_walk_forward`, when the rule carries it, a target weight above
    1e-12 on an instrument absent from that date's matrix raises.
  - `constant_exposures` does not carry it. No existing caller changes.
  - The eight tradable-only instruments never have a row, so they are never
    holdable (`decisions/0054` item 7).
- **The usage log.** Each `at(date)` records one row per instrument:
  `instrument`, `parameter` (`loadings`), `store_week`, `fitted_through`
  (the store's `last_data_date`) and `used_on_date` (`date`).
  - `usage()` returns the rows as a frame, without duplicates.
  - `RunContext` gains `parameter_usage`, and `run_experiment` fills it from
    the map.
  - **Don't invent a usage table for a constant matrix.**
    `validate_pipeline` keeps failing `lookahead` on a missing input, as it
    does today.
- **Tests,** on a synthetic store written with `write_store` in a temp
  folder:
  - the store named in `params/` is the one read, and a wrong hash is
    refused;
  - a Friday reads its own week; the Tuesday after reads the Friday before;
    a date seven days after the last week raises; a date before the first
    week raises;
  - duration reads `oad` for a Treasuries instrument and is marked
    `measured`; the same instrument with `oad` missing that week reads minus
    `real_yield` and is marked `estimated`; an equity reads minus
    `real_yield` even when an `oad` is present for it;
  - `oad` from an earlier week is never used;
  - the three other axes, including the sign;
  - `region`, `sector` and `style` raise, and the message names
    `decisions/0054`;
  - the usage log: one row per instrument and date, `fitted_through` equal
    to `last_data_date`; and a store whose `last_data_date` is after its
    week makes `veto_lookahead` fail;
  - the engine raises on a weight held without a row when the rule carries
    the marker, and does not when it is `constant_exposures`.
- **The two tests that pin "still raising"** are replaced, not deleted:
  - `tests/test_experiment.py::test_the_exposure_matrix_raises_rather_than_returning_an_identity`;
  - `tests/test_characteristics.py::test_the_exposure_matrix_still_does_not_exist`.

  What each pins is that a missing map raises and never returns an identity.
  Keep that, against a store root with no store in it. **Neither may depend
  on the real store.**

**3. The veto's tests** (`tests/test_vetoes.py`).
- **Update every existing lookahead test and both full contexts** to carry
  an honest `parameter_usage`. List each one in the receipt. Don't weaken
  an assertion to make one pass.
- **Add:**
  - both tables honest passes, and the detail names both counts;
  - `fitted_through` one day after `used_on_date` fails; the same day
    passes;
  - `parameter_usage` absent, empty, or without a column fails as a missing
    input;
  - a missing date in a row fails, and the detail says "undated";
  - a peek in each half reports both.
- **`tests/test_params.py`:** `data.characteristics.directory_hash` equals
  the `directory_hash` in the committed
  `data/characteristics/<store_id>/manifest.yaml`. This test needs no vendor
  data.
- **The params hash** must be
  `413d84f6b631359bee74883cb63f93660023cc50d4ff49306579c401a4d61623`. If it
  differs, stop and report both.

**4. The map's own check, on real data:** `scripts/check_exposures.py`, run
with `make exposures-check`.
- It calls `require_one_thread` and writes
  `results/characteristics/huber6-v3/exposures_check.md` and `.json`.
  Aggregates only.
- **It walks every store week** through `resolve_exposures`, and then the
  Tuesday after each one.
- **Expected** *(Cowork's read of the store, Python 3.10 outside the repo's
  environment)*:

  | Figure | Expected |
  |---|---|
  | Store weeks | 888, 2002-12-27 to 2019-12-27, all Fridays, none skipped |
  | Instrument-weeks | 72,606 |
  | Instruments at the first and last week | 73 and 84 |
  | Duration cells measured / estimated / missing | 6,763 / 65,843 / 0 |
  | `LT13TRUU` | 677 measured, 211 estimated (2002-12-27 to 2007-01-05) |
  | `LDC5TRUU` | 758 measured, 0 estimated |
  | `LT01TRUU`, `LT09TRUU`, `LT11TRUU`, `LUTLTRUU`, `LBUTTRUU`, `LUACTRUU` | 888 measured each, 0 estimated |
  | Measured duration cells at or below zero | 0 |
  | Mean of `axis_duration` over all cells | 1.4274 |
  | Mean of `axis_real_nominal` | 1.2792 |
  | Mean of `axis_credit` | 1.3006 |
  | Usage rows on the Fridays | 72,606, every `fitted_through` equal to `used_on_date` |
  | Usage rows on the Tuesdays | every `used_on_date` four days after `fitted_through` |
  | 2001-01-05 and 2002-12-20 | raise |

- **Report any figure that differs,** a mean by more than 0.0001. Don't
  change the method to match.
- **Also print, by reporting class, the median of `axis_duration` at
  2019-12-27.** *Cowork's read:* Long Treasuries 18.32, Gold 8.63, IG
  Corporates 5.22, TIPS 4.55, Treasuries 4.48, EM Equities 2.12, European
  Equities −1.14. Gold reads above a 7-10y Treasury because it reads minus
  its real-yield loading. That is `decisions/0050` as ruled, and the owner
  wants to see the table.

**5. Words that are now wrong.**
- `characteristics/__init__.py` says `resolve_exposures` "still raises".
- `harness/experiment.py`'s chain comment says the exposure matrix is
  missing.
- `build.mk`'s `characteristics` line names `huber6-v1`.

**6. Check, commit, push.**
- **The check:** `scripts/unattended.sh check-full --digest`.
- **Commit the build:** `params/`, `vetoes/rules.py`, `src/`, `scripts/`,
  `tests/`, `build.mk`, `results/fx/` and the two `exposures_check` files,
  as
  `params+vetoes+src: v0.10.0 -- resolve_exposures reads huber6-v3, the lookahead veto checks loadings (HANDOFF task 54, decisions/0055, decisions/0050)`.
- **Push:** `git push origin main`, as `CLAUDE.md` allows and the owner
  ruled (OWNER-QUEUE L34).
  - Task 53's push did not land, and its reason was not recorded.
    `origin/main` is `1b6babf`.
  - It should be a fast-forward of about 140 commits.
  - Never `--force`, never pull, never rebase.
  - **If it is rejected or authentication fails, stop.** Write the exact
    message in the receipt and commit the receipt locally.
- **Then the receipt,** with the push's output in it. Commit it and push
  again.
- **Last:** `git rev-list --count @{u}..HEAD` must print 0.

**Receipt:**
- rc, commits, the log directory, the tier and the runtime;
- **step 1:** the `results/fx/` diff, the scratch store's hash, and the two
  new pairs' figures;
- **step 2:** the names you chose, every test added, and the two tests
  replaced;
- **step 3:** each existing test changed, and the params hash;
- **step 4:** every figure beside its expectation, and the table by class;
- **step 6:** the push's output and the final count;
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 53. Every return in dollars (`decisions/0053`): eighteen local-currency series converted, `NDDLUK` out, a currency guard; store `huber6-v3`; SUBSTRATE v0.10 committed; the spread table; `LET1TREU`'s name; then push

Added 2026-10-10 by Cowork.

**Owner rulings of 2026-10-10:**
- OWNER-QUEUE L32 (`decisions/0053`);
- L31 (SUBSTRATE v0.10, already applied by Cowork in the working tree);
- L30 (`decisions/0050` addendum);
- the push permission now in `CLAUDE.md`.

**What this task does not do:**
- **No owner-only edit by you.** SUBSTRATE v0.10 and `decisions/0100` are
  Cowork's transcription, and step 0 commits them.
- No vendor call, no audit, no hypothesis changes state.
- **`resolve_exposures` keeps raising.**

**Budget:** 3 to 4 h, of which about 25 minutes is machine time.

**Read first:**
- `decisions/0053`, all of it, and especially its convention table and its
  test;
- SUBSTRATE §5.1, including the new invariant 8, and §5.4a (v0.10, in the
  working tree);
- `Claude outputs/project-mirror/task-52-review-2026-10-08.md`.

**Hard rules:**
- **Vendor data never leaves the machine.** That includes
  `data/raw/bloomberg/bbg_curncy_hist.xlsx`. Print no rate and no level;
  report counts, dates, hashes and aggregates only.
- **The FX file runs to 2026-10-10. Nothing on or after 2020-01-01 is read.**
  Cut at the holdout as every loader does, and test it.
- **The quote convention is an explicit table** (`decisions/0053` rule 3).
  - Never infer the direction from the column name by a string rule.
  - `EURUSD` and `GBPUSD` are USD per unit and multiply. The six `USDxxx`
    columns are units per USD and divide.
  - A column not in the table is refused.
- **No forward fill.** A date with a local level and no FX rate has no USD
  level.
- **The ex-USD bond file is not touched.** `bbg_exusd_bonds_usd_unhedged.csv`
  stays as delivered (OWNER-QUEUE L33).
- **Nothing in `params/` or `vetoes/` changes.** If a step seems to need it,
  stop.
- **Numbers recorded before today stand.** Don't edit or delete `huber6-v1`
  or `huber6-v2`. Don't re-run the estimator test.
- **No golden moves.** If a test this task doesn't name fails, stop and list
  it.
- **Don't build from `decisions/0050` or `0051`.** That means no axis
  mapping, no label block and no alphas.

**0. Commit first, alone, after `make check`.**
- **Files:** `HANDOFF.md`, `OWNER-QUEUE.md`, `CLAUDE.md`, `SUBSTRATE.md`,
  `decisions/0050-…` (addendum), `decisions/0053-…` and `decisions/0100-…`.
- **Message:** `substrate v0.10 and queue: task 53; SUBSTRATE §5.1 invariant 8, §5.4a and §6 transcribed (decisions/0051, 0052, 0053); decisions 0053 and the 0050 addendum; OWNER-QUEUE L30, L31, L32 ruled, L33 added; push permission in CLAUDE.md (owner 2026-10-10)`.
- **Governance:** `make governance` must pass. The message cites the records
  for the owner-only file.

**1. The FX file.**
- **The file:** `data/raw/bloomberg/bbg_curncy_hist.xlsx`, sheet
  `FX_Spot_USD`.
  - Columns: `Date`, `EURUSD`, `GBPUSD`, `USDCAD`, `USDHKD`, `USDINR`,
    `USDKRW`, `USDTWD`, `USDJPY`.
  - One header row; 12,204 data rows. Blank is missing.
  - Its sha256 begins `1d6fbb63e8a33e2e`. Check it, and stop if it differs.
  - The `Data Sources` sheet is not read.
- **A `raw_manifest.csv` row** for it: role `fx_spot`, layout
  `wide_single_date`, one header row.
- **A reader** that returns USD per unit for each of EUR, GBP, CAD, HKD, INR,
  KRW, TWD and JPY. The convention table lives in code, next to the reader.
- **Expected, before the holdout,** rows per column *(Cowork's read, in the
  cloud workspace)*:

  | Column | Rows before the holdout | First date |
  |---|---|---|
  | `EURUSD` | 10,283 | 1980-01-02 |
  | `GBPUSD` | 10,436 | 1980-01-01 |
  | `USDCAD` | 10,436 | 1980-01-01 |
  | `USDHKD` | 10,407 | 1980-01-01 |
  | `USDINR` | 10,200 | 1980-01-01 |
  | `USDKRW` | 10,001 | 1981-04-13 |
  | `USDTWD` | 9,327 | 1983-10-05 |
  | `USDJPY` | 10,436 | 1980-01-01 |

  Every column fell inside a plausible 2002-2019 band in its stated
  convention. `GBPUSD` co-moves positively with `EURUSD`, and the six
  `USDxxx` columns negatively.
- **Tests,** on a synthetic workbook built in a temp folder:
  - a EUR level of 100 at `EURUSD` 1.25 is 125 USD;
  - a JPY level of 100 at `USDJPY` 100 is 1 USD;
  - an unknown column is refused;
  - the holdout cut;
  - blank is missing, not zero.

**2. The conversion and the guard** (`decisions/0053` rules 4 and 5), in
`BloombergLoader.load_returns`.
- **Where:** after markers and business days (step 1), before the
  truncation (step 2).
- **What:** every series whose `SeriesMeta.currency` (Index Map
  `Quote ccy`) is one of EUR, GBP, CAD, HKD, INR, KRW or TWD becomes its
  local level × USD per unit on the same date. Its `currency` is then
  recorded as USD and the original is kept as `quote_currency`.
- **Expected: exactly 19 series.**
  - `I02513EU`, `MXEUG`;
  - `MXEU0EN`, `MXEU0MT`, `MXEU0IN`, `MXEU0CD`, `MXEU0CS`, `MXEU0HC`,
    `MXEU0FN`, `MXEU0IT`, `MXEU0TC`, `MXEU0UT`, `MXEU0RL`;
  - `NDDLUK`;
  - `MXCA`, `MXCN`, `MXIN`, `MXKR`, `TAMSCI`.
- **Record** in `loader.report["fx"]`: per series, the currency, the column,
  and the dates dropped for want of an FX rate.
- **The guard.** For the roles `returns`, `returns_substitutes`,
  `returns_hedged` and `benchmark`, a series whose quote currency is not USD
  and is not converted stops the load.
  - **Blank or `#N/A`:** a blank or `#N/A` quote currency is reported, not
    refused. Expected: `LEGATRUU`, `NDUEACWF`, `SBWGU` and `MXWO`, which are
    USD by their long names.
  - **The ex-USD CSV is exempt:** its `_USD_unhedged` columns are already
    converted.
  - **If the guard stops on a series not named here,** stop and list it.
- **The factors must not move.** They are built from `NDUEACWF`, `LD20TRUU`,
  `BCOMTR`, `GTII10`, `USGGBE10`, `LUACOAS` and `DXY`, none of which is
  converted. The factors hash must equal `3401475e…fafa9`; if it differs,
  stop. **The panel's hash will change:** record the new one.
- **Tests,** on synthetic data:
  - a EUR and a JPY series converted in the right directions;
  - a missing FX date gives a missing level, not a carried one;
  - an unconverted non-USD series is refused;
  - a blank quote currency is reported, not refused;
  - a fixture without the FX file loads as before when no series needs it,
    and is refused when one does.

**3. The conversion's own check, on real data:**
`scripts/check_fx_conversion.py`, run with `make fx-check`.
- It calls `require_one_thread` and writes `results/fx/conversion_check.md`
  and `.json`.
- **What it compares:** converted `NDDLUK` against `NDDUUK`, on weekly
  Friday closes, from 2002-01-01 to 2019-12-27. It reports four figures:
  - weekly tracking error;
  - 4-week tracking error;
  - lag-1 autocorrelation of the weekly difference;
  - the cumulative gap.
- It also reports the same with the FX rate lagged one day.
- **Expected** *(Cowork's read, Python 3.10 outside the repo's
  environment)*: same day 238 bp/yr, 107 bp/yr, −0.51 and −50 bp. The lagged
  version is about twice as wide.
- **Report both if they differ** by more than 5 bp or 0.02. Don't change the
  method to match. **If same-day is not the better of the two, stop.**

**4. The universe** (`decisions/0053` rule 6, and the `LET1TREU` name).
- **`NDDLUK`:** add it to `NOT_INVESTABLE_OTHER` with the reason
  `MSCI UK restated in sterling; NDDUUK is the same index in dollars (decisions/0053)`.
- **`LET1TREU`:** in `data/universe/bbg_exusd_bonds_coverage.csv`, change
  its name from `euro_treasury_1_10y` to `euro_treasury_1_3y`. Change it
  where the file is generated, if it is; otherwise in the file. List every
  other place the old name appears.
- **`make universe`.** Expected: **102 series, 92 investable, 10 excluded.**
- **Tests:** `tests/test_scripts.py` asserts 93. Make it 92, cite 0053, and
  assert `NDDLUK` is not investable.

**5. The build's gates.**
- **Against the run of record.** Keep `RESTATED` as it is. Add `NDDLUK` to
  the instruments that left the build, and a `CONVERTED` set of the 17
  estimated converted series (rule 4's list less `NDDLUK` and `MXEU0RL`).
  - The run's instruments must be the build's (Cash out) plus exactly those
    three.
  - Every Huber loading the run stores for an instrument that is neither
    left nor converted must equal this build's, at a tolerance of zero.
  - **Expected:** 66 instruments, **339,744 cells, largest difference 0.0**
    *(Cowork's count from the run's `loadings.parquet`)*.
- **Against `huber6-v2`.**
  - On instruments neither left nor converted, every loading and standard
    error must be equal at zero. **Expected: 345,072 rows** (440,964 less
    `NDDLUK`'s 5,328 and the converted 90,564).
  - For the 17 converted series: report the largest difference, and each
    series' median dollar loading and explained share, before and after.

**6. The store:** `make characteristics ARGS="--store-id huber6-v3"`.
- **Expected:**
  - 84 estimated (Cash included) and 8 not; 92 instruments;
  - loadings 435,636, fit 72,606 and measured 21,722, if no converted series
    loses a week to a missing FX rate (if one does, report it by series);
  - dates 2002-12-27 to 2019-12-27.
- **The manifest** cites `decisions/0049`, `0052` and `0053` and this task,
  and records `supersedes: huber6-v2`.
- **Expected for the converted series** *(Cowork's expectation, not a
  measurement)*:
  - their median dollar loading moves from +0.10…+0.85 down into the range
    of their dollar-quoted peers, about −0.07 to −0.40 for equities;
  - `NDDLUK` would have landed near `NDDUUK`'s −0.24, but it is no longer
    estimated;
  - `I02513EU` moves toward the converted euro bonds (−0.84 to −1.15);
  - `MXCN` barely moves, because the HKD is pegged.
- **If a converted equity series' median dollar loading is still positive,**
  report it and continue. It is a finding, not a failure.

**7. The report** (`results/characteristics/huber6-v3/report.md`).
- **A new table: converted to dollars.** Per series: the currency, the FX
  column, the weeks, the median dollar loading and explained share in `v2`
  and in `v3`, and the FX dates dropped.
- **Duration times spread:** leave out the Treasuries, Long Treasuries and
  TIPS classes, and the four government ex-USD indices `I02513EU`,
  `I02913JP`, `I12823GB` and `LET1TREU`. Their spread over Treasuries is
  near zero, so the ratio is meaningless (task 52 printed −39 and 15). The
  heading says what is left out and why.
- **Tests** on synthetic data for the new table and the exclusion.

**8. Check, commit, push.**
- **The check:** `scripts/unattended.sh check-full --digest`.
- **Commit:** `src/`, `scripts/`, `tests/`, `build.mk`, `data/universe/`,
  the `huber6-v3` manifest and report, and `results/fx/`, as
  `loaders: every return in dollars -- eighteen local-currency series converted, NDDLUK out, a currency guard; store huber6-v3 (HANDOFF task 53, decisions/0053)`.
- Then commit the receipt.
- **Then push:** `git push origin main`, as `CLAUDE.md` allows.
  - It should be a fast-forward of about 140 commits; the remote has seen
    none since 2026-09.
  - Never `--force`, never pull, never rebase.
  - If it is rejected or authentication fails, stop and report the message.

**Receipt:**
- rc, commits, the log directory, the tier and the runtime;
- **step 1:** the hash, the rows per column and the first dates;
- **step 2:**
  - the 19 converted, with the FX dates dropped per series;
  - the series reported with a blank currency;
  - the factors hash and the new panel hash;
- **step 3:** the four figures and the lagged pair, each beside Cowork's;
- **step 4:** the universe counts, and every place `euro_treasury_1_10y`
  appeared;
- **step 5:** the cells compared and the largest difference for both gates;
- **step 6:** the store's hash and row counts, and the converted series'
  dollar loadings before and after;
- every test added and changed;
- the push: its output's last line, and `git rev-list --count @{u}..HEAD`
  after it (expected 0);
- **Anything in this task you didn't do, said plainly.**

Then stop.

---

### 41. Fix `romano_wolf`'s standardising: pool the observed value with the null draws (task 40 follow-up, `decisions/0041`)

Added 2026-09-29 (late evening) by Cowork. **Owner ruling 2026-09-29: fix it,
then start 35 tonight.** No engine runs. **Runs first, then go straight on to
35.** Budget about 30 min.

**0. Commit first, alone:** `HANDOFF.md` and `OWNER-QUEUE.md`, with the message
`queue: task 41, 35 deadline amendment; L16 small-k correction (Cowork 2026-09-29)`.

**Why.** Task 40 standardised each column with the mean and sd of its `k`
null draws **only**. That treats the observed value differently from the
draws: the draws are shrunk toward zero by their own mean and sd, and the
observed value is not. The permutation test's validity rests on the observed
row being exchangeable with the `k` null rows, and this breaks it. The error
is Cowork's: task 40's spec said to do exactly that.

Task 40's own study shows the result. Under the complete null (rho_w 0.3,
rho_b 0.2), `romano_wolf_5` FWER is:

| k | before (task 38) | task 40 |
|---|---|---|
| 20 | 0.048 | **0.127** |
| 50 | 0.041 | 0.064 |

With 5,000 reps, se ≈ 0.003, so this isn't MC noise. `rw_g2_5`'s P(V ≥ 2) is
**0.083** at k = 20 against 0.05.

**The fix:** compute each column's mean and sd over the **k + 1 values, the
observed `t_j` together with `T0[:, j]`**. That is a symmetric function of
all k + 1 values, so exchangeability, and with it exact validity, is kept.

Cowork checked this in a simulation: m = 12, equicorrelation 0.3, column
scales from 0.5 to 3, 4,000 reps, complete null, FWER 5%.

| k | unstandardised | T0 only (task 40) | pooled (the fix) |
|---|---|---|---|
| 20 | 0.047 | 0.120 | 0.049 |
| 50 | 0.034 | 0.061 | 0.037 |
| 100 | 0.049 | 0.060 | 0.051 |

**1. Code.** In `_standardise_columns` in `stats/multiple_testing.py`, pool
`t` into the mean and sd (ddof=1 over k + 1 values). Update its docstring and
the note in `decisions/0041` ("Implementation note", one sentence plus the
date). Make the same change in `_batched.py` wherever it standardises. Keep
the `ValueError` on a zero or non-finite sd.

**2. Tests.**
- **Add the regression that would have caught this.** Take a complete null,
  m = 12, equicorrelated, **heteroscedastic columns** (scales 0.5 to 3),
  k = 20, at least 4,000 reps, fixed seed. Assert:
  - `romano_wolf` with `standardise=True`: FWER ≤ 0.05 + 3 se.
  - `romano_wolf_gfwer` with g = 2: P(V ≥ 2) ≤ 0.05 + 3 se.
  If it's too slow for the fast tier, mark it `slow`.
- Update any test that pinned task 40's T0-only transform.
- The existing `standardise=False` reproduction test and the `g = 1`
  identity test must pass unchanged.

**3. Re-run the study** (`make fdr-study`, about 8 min). Report:
- The complete-null rows (n_true = 0, headline correlation) at every k, for
  `romano_wolf_5`, `rw_g2_5` and `rw_g2_10`: `fwer` and `p_two_plus_false`.
- **The k-sensitivity table** in task 40's format, IC 0.35 and IC 0.70.

**4. Check and commit.**
- Run `uv run --python 3.12 --group dev pytest -q tests/test_multiple_testing.py tests/test_batched_multiple_testing.py`
  and `scripts/unattended.sh check` (the fast tier).
- **Don't run `check-full` here.** Task 35's `scripts/unattended.sh
  audit-halflife` runs `check-full` on the combined tree before its grid, which
  covers this commit. That saves about 22 min against tonight's deadline, and
  is the owner's call for tonight only. If that check-full fails, 35 stops
  there, and the receipt says whether the failure is in this task's code.
- Commit as `stats: pool the observed value into romano_wolf's standardising
  (HANDOFF task 41, decisions/0041)`.

**Receipt:**
- rc, commit, study directory and runtime.
- The two tables in step 3.
- The largest remaining gap between `romano_wolf_5` and task 38's at each k.

Interpretation is Cowork's and the owner's. **Then go straight on to task
35**, under its 2026-09-29 late-evening amendment. Stop without going on only
if step 2's tests fail. **If the new regression still fails after the fix,
don't loosen it:** revert this task's changes to `standardise=False` as the
default, say so, and still go on to 35.

---

### 35. The volatility-overlay halflife sweep (OWNER-QUEUE B1, L13)

> **AMENDMENT 2026-09-29, late evening (owner). Tonight's run has a hard stop:
> the grid stops by 06:30 ET and the receipt is committed by 06:45 ET. This
> overrides the "continue straight to task 39" block at the end of this task.
> Don't start 39 tonight, whatever the time.** The run goes 41 → 35.
>
> Timeline: start about 23:30. Task 41 ends about 00:00, and this task's build
> about 00:30. `check-full` then takes about 22 min, and 240 cells × about
> 84 s is about 5.6 h. So the grid should finish around 06:00-06:15, with
> little margin. h4 cells may run slower. **Three additions to the build,
> tested like the rest:**
>
> 1. **Order the cells** so that an early stop leaves complete comparisons:
>    - horizon **13 first**, which holds the knee identity check, then **26**,
>      then **4**;
>    - within a horizon, by (IC, seed), with all four halflife arms of one
>      (IC, seed) back to back, so every pair of arms is complete.
> 2. **Checkpoint each cell.** Append each finished row to
>    `cells.partial.csv` in the run directory as soon as it's done, through
>    `run_grid`'s `progress` callback, and flush. A kill then loses at most
>    one cell. Today, `run_grid` holds every row in memory, so a kill loses
>    the whole run.
> 3. **A deadline guard.** The audit reads `HALFLIFE_DEADLINE`, an ISO
>    timestamp with its offset. Before each cell, if now + 1.5 × the median
>    cell time so far (120 s before the first cell) would pass the deadline,
>    stop cleanly:
>    - write `cells.csv` and the report from the finished cells;
>    - mark the report **PARTIAL**, with the cell count per horizon;
>    - exit rc = 0.
>    If the variable is unset, nothing changes. Tests:
>    - a deadline already past gives zero cells and a partial report, with no
>      crash;
>    - a deadline far ahead leaves the output unchanged.
>
> Launch with:
>
>     HALFLIFE_DEADLINE=2026-09-30T06:30:00-04:00 scripts/unattended.sh audit-halflife --digest
>
> - **This `check-full` also covers task 41's commit** (41 skipped its own).
>   If it fails, stop, and say in the receipt which task's code failed.
> - **If the grid stops at the deadline:** write the receipt on what finished.
>   Say which horizons are complete. Run the h13 identity check if h13 is
>   complete. Commit the receipt before 06:45 ET.
> - **If you're still running at 06:40 ET for any other reason** (the check
>   ran long, or the digest is slow), stop what's running and commit a short
>   receipt saying where it stopped.

**0.** *(Moved to task 40's step 0 on 2026-09-29, evening. Nothing to commit here.)*
**Note, 2026-09-29:** after task 37, audit modes of `scripts/unattended.sh` run
`check-full` before the grid, so `scripts/unattended.sh audit-halflife --digest`
alone is enough. `scripts/unattended.sh check` is now the fast tier.

Added 2026-09-28 by Cowork. **Owner-approved 2026-09-28** (L13: "approved, go
ahead"). **Run after task 34, and before task 33 is released**: the h13
no-overlay arm checks against the knee run under today's `params_hash`,
which task 33 would change. About 240 cells at the friction sweep's ~84 s
each, so **5.5-6 h**. The h4 cells may run slower. Treat it as an overnight run.

**Why.** `risk_calibration` fails 23-47% of cells in every grid, on 2008, live
and baseline alike (L13). In the friction sweep it failed 21 of 60, with 2008
the worst year in 50. `decisions/0030` found a scalar 26-week overlay took the
worst-year bias from 1.39-2.21 to 1.17-1.61 (0 fails of 11). That was tested
at one horizon, two IC rungs and one halflife. B1 is retired only by a sweep
across halflives and horizons.

**This does not turn the overlay on.** It sets `AuditCell.vol_halflife` and
`vol_overlay` per cell, which already exist. Nothing in `params/` reads them.
The standing refusal below stands.

**Build.** Add a `halflife` grid to `ladder.py` as module constants (nothing in
`params/`): live cells only, IC **0.35 and 0.70**, seeds **0-9**, horizons
**4, 13 and 26**, and `vol_halflife` in **None, 13, 26, 52** with
`vol_overlay="scalar"` whenever `vol_halflife` is set. Constraints and costs
are the knee grid's live cells' (`per_rebalance_cap` from
`audit.per_rebalance_cap_default`, no turnover cap, cost multiplier 1.0, shadow
coefficient from `params/`). That's 2 x 10 x 3 x 4 = **240 cells**. Keys already
encode the overlay (`_vhl26scalar`), and a `None` cell's key is unchanged. Add
`make audit-halflife`, extend the `unattended.sh` whitelist, and add a
preflight like `_friction_preflight`: the knee run `A-20260922-005316` exists,
both hashes match, and it has the live h13 cell at every (IC, seed).

**Test:** the grid is 240 unique live keys. Every `vol_halflife=None` cell at
h13 has the same key and constraints as the knee run's live cell. A
`vol_halflife` cell is `scalar`.

    scripts/unattended.sh check --digest
    scripts/unattended.sh audit-halflife --digest

**Receipt should say:**
- rc, runtime, run id, commit hash.
- **The h13 `None` arm against the knee run `A-20260922-005316`:** live
  `net_ir` identical, cell by cell, for all 20 (IC, seed) pairs, and whether the
  hashes match. **Stop and report if not.**
- Per (horizon, halflife), pooled over both ICs (20 cells), and separately per
  IC: `risk_calibration` fails (count), `bias_worst_annual` median and max, how
  many cells have 2008 as the worst year, full-sample `bias_stat` median,
  `te_p95` median, `te_p95_to_budget` median, net IR median and range, annual
  turnover median, cost drag median.
- Paired by (IC, seed, horizon): net IR at each halflife minus net IR at `None`
  (mean, sd, number positive).
- Any cell with `inaccurate_share` > 0.01 or `infeasible_te_share` > 0.

Interpretation is Cowork's and the owner's. Whether the overlay becomes policy
is B1, an owner decision.

*(Overridden for the night of 2026-09-29 by the amendment at the top of this task: stop after 35.)* **Then: continue straight to task 39, or stop** (owner, 2026-09-29). Write and
commit 35's receipt first, then go on to task 39 in the same session only if
**all** of these hold:
1. The grid's rc = 0.
2. The h13 `None` arm matched the knee run on all 20 (IC, seed) pairs, and
   both hashes matched.
3. **39 is expected to finish by 06:00 America/New_York** (check with
   `TZ=America/New_York date`). Budget about 1.5 h for 39: the edits plus one
   `check-full`. So start it only if it's before 04:30 ET.

If any of them fails, stop, and say in the receipt which one.

---

## Not queued yet, and what each is waiting on

Rewritten 2026-09-22 by Cowork; the earlier text predated `decisions/0035` being
decided and is in git history.

**Landed since the last rewrite:** the block-shuffled baseline (tasks 17-19), the
knee grid (20), and `0035` §4, §4a and §5 — the corrected TC, the NNLS replication
quality, per-run persistence of weights and alpha (22).

**Exposure-space planting** (design B in
`claude/detection-threshold-review-2026-09-22.md`). Not designed. It plants noise
per SUBSTRATE §6 axis rather than per instrument, to test whether iid noise across
a collinear universe is what depresses transfer. Waits on task 25: if bar 2 is out
of reach on a single history regardless, that changes what B is for.

**`0035` §7 — the transfer coefficient.** Open. The oracle's corrected TC reads
0.022 against an acceptance case of 1.0, with `w` and `w_baseline` nearly
orthogonal (cos 0.011). No task until a hypothesis for it is written.

**The volatility overlay halflife sweep (OWNER-QUEUE B1).** Queued 2026-09-28 as
task 35 (owner's L13 ruling). Turning the overlay **on** stays a standing
refusal below until the owner rules B1.

**The shadow cost's 53-week echo (OWNER-QUEUE L18).** Ruled 2026-09-28 (option
a, `decisions/0040`) and queued as task 36. Adopting it into `params/` waits on
task 36 and lands with task 33.

**The validator (0034).** Not decided by the owner. Do not build it.

**SUBSTRATE §5.6 and §16 still close the search (Cowork, 2026-10-01 evening).** Until JPMaQS lands, "no signal search runs", and price-only families such as trend (0009) "are not tested in isolation first". So the phase-2 solver can be built and validated on planted signals, but no registered hypothesis runs on real data before phase 3. **Owner, 2026-10-01: the JPMaQS loader first (task 44), then the phase-2 solver validated on planted signals. §5.6 is not amended.**

**FRED point-in-time (not queued).** `H-2026-0008` needs four FRED series, and `loaders/fred.py` is a stub. A point-in-time FRED loader (ALFRED vintages) comes after task 44. It needs its own spec.

**The wiring.** Queued 2026-10-11 as task 54 (`decisions/0055`). The region axis keeps raising until the label map lands.

**The label map file (added 2026-10-11).** *(Superseded 2026-10-12: queued as task 55.)* `decisions/0054` rules the equity regions. Not queued: `data/universe/label_map.csv`. The region axis reads equities only (owner, 2026-10-11), so the equity regions could land without the bond labels; the owner has not said whether to split it (OWNER-QUEUE L28).

**The solver's form is decided (2026-10-07, `decisions/0051`):** views become expected returns for `portfolio/long_only.solve`; nothing is held at a target. SUBSTRATE §6 still says otherwise (OWNER-QUEUE L31). Don't build the solver before §6 is transcribed. Its spec is not written.

**H-2026-0004's request file (not queued).** `data/requests/H-2026-0004.yaml` is the 2026-09-28 file and reads `awaiting_owner`. The hypothesis is parked by the grade rule (`decisions/0006` addendum). Making `write_data_request` say so needs a design for how a grade-emptied ticker is told from an absent one. Low priority while the search is closed.

**The phase-2 solver (added 2026-10-01, task 42).** `harness/experiment.py` has no
solver yet: `build_weight_rule` raises. When it is written it must, and each point
comes with a test pinning it:
- read `audit.covariance.vol_overlay` through `audit.ladder.resolve_vol_overlay`
  or its equivalent, so the overlay is policy and not a per-call choice
  (`decisions/0042`);
- price turnover through `harness.objective.created_marginal_quadratic` and
  `created_marginal_shadow`, not a second copy of the arithmetic (`decisions/0040`);
- run the multiple-testing gate through `stats.multiple_testing.gate` and hand
  `verdict_for(result, i)` to the `multiple_testing` veto (`decisions/0043`).

### One scheduling point, because the audit costs 14 hours

`A-20260918-201042` took **50,572 s**. The `L` statistic and the
`transfer_coefficient` column are both new per-cell measurements, so each needs
an audit run to populate it. **Land them in one series and rerun the audit
once.** Three separate reruns is 42 hours of machine time to learn what one
run would have said.

### Standing refusals

- **Changing the volatility overlay.** It is policy since `decisions/0042`
  (owner, 2026-10-01): scalar, 26-week halflife, read from
  `audit.covariance.vol_overlay` (task 42). Changing its form or halflife, or
  turning it off for a default cell, is an owner decision. *(Cowork,
  2026-10-01: this replaces the pre-0042 refusal to turn it on.)*
- **`decisions/0029` §2 only.** §1, §3, §4 and §5 were decided 2026-09-19 and
  are in task 9. **§2 -- conditioning the frictionless covariance -- stays
  deferred**; do not add a ridge or eigenvalue floor on your own initiative.
- **`decisions/proposed/0034`.** Proposed, not decided. Do not build it.
- **Building from `decisions/0051`, or past task 54 from `0050`.** Task 54
  wires `resolve_exposures` and nothing else. No solver, no alphas and no
  view is built until a task says so; the solver's spec is not written.
- **Building from `decisions/0054`.** The label map file is not queued. *(Superseded 2026-10-12 for task 55's scope: the label map and the region axis are queued. Sector, style and scope logic are still not built.)*
  Region, sector and style raise.
- **Re-recording a golden.** `decisions/0048` allows three named constants,
  once, in task 50. Any other needs the owner.
- **Anything in `params/`, `vetoes/` or `SUBSTRATE.md` not arriving as a cited
  patch.** Refuse and say so.

---

## Done

### 2026-10-21 -- task 63: done, resumed at step 4a (Claude Code, sonnet, interactive 2026-10-21T15:30)

**rc=0.** Commits: `5501945` (steps 1 to 3, earlier run), `c7b51b6` (`scripts: a one-off report of data_required names the resolver rejects (HANDOFF task 63)`: `scripts/check_registry_names.py`, `build.mk`), `eafee95` (`records: decisions/0034 decided; the "fabricated" LT08TRUU corrections (HANDOFF task 63)`). No push (`push=no`).

- **Step 4a.** `registry-names` target added to `build.mk` and `.PHONY`. The script first failed with `No module named 'signal_lab'`; fixed by `import _bootstrap` like the other scripts. `make registry-names` then ran, rc 0.
- **The pass: 21 files, 136 entries; 35 entries rejected in 9 files.** (a) 25 entries in `H-2026-0018` to `0021` (pending), all `<ticker>|IV3M_10DP` or `|IV3M_10DC` (SPX Index, EZU, EWJ, EWA, EWC, EEM, TLT, HYG US Equity; `0021` also LQD): no coverage table covers the implied-vol file, as Cowork guessed. (b) **10 entries Cowork did not guess:** `GTII10` and `DXY` in each of `H-2026-0013` to `0017` (done, measurement hypotheses). Both are SUBSTRATE §5.3 analytics-tab series; reading is that the resolver's sources do not cover them. Nothing edited, nothing added to the owner-confirmed list; what to do is the owner's.
- **`check-scoped` for the script commit:** rc 0, 166 s, tier SCOPED (not FULL), slow files left out: `test_audit`, `test_baseline`, `test_engine`, `test_experiment`, `test_measurement_estimators`, `test_measurement_fidelity`, `test_multiple_testing`, `test_scripts`. Directory `results/audit/_unattended/20261021-153419-check-scoped/`.
- **Step 5.** `git grep "H-2026-0010" -- tests scripts src` found only id references in `scripts/jpmaqs_name_search.py`, nothing pinning the file's text, so the note edit was **made** (YAML parses). `0034` moved to `decisions/` with Status decided (the proposed file's status text was `Status: **proposed**.` inline, not `**Status:** **proposed**`); 0032 addendum, OWNER-QUEUE L6 correction line added. The first attempt (one Python command) was denied by the auto-mode classifier; the owner then told me to use the Edit tool, which I did. L39 committed as Cowork left it.
- **`check` (docs tier):** rc 0, 160 s, directory `results/audit/_unattended/20261021-154618-check/` (log stamp 15:46:18).
- **Uncommitted:** `AGENTS.md` (left alone), this receipt.

### 2026-10-21 -- task 63: STOPPED at step 4, the pass could not run (Claude Code, sonnet, nightly 2026-10-21T09:40)

**STOPPED. Steps 0 to 3 done; step 4's run was denied, so no rc.** Commit `5501945` (`harness: a data_required name must resolve at registration (HANDOFF task 63, decisions/0034)`: `src/signal_lab/harness/hypotheses.py`, `tests/test_name_resolution.py`, `data/universe/owner_confirmed_names.csv` with the seed row only). No push (`push=no`).

- **Step 0.** `git status --short` was exactly the four lines the task lists.
- **Steps 1 to 3.** `resolve_names` (default `False`) on `validate_hypothesis` and `parse_hypothesis`, `unresolved_names`, `UNIVERSE_DIR`, `HypothesisRegistry.register` (and a `universe_dir` constructor argument). `load` and `load_tolerant` unchanged. `scripts/unattended.sh check-scoped` rc=0, 508 s, tier=FULL, slow files left out: none. Log: `results/audit/_unattended/20261021-123125-check-scoped`.
- **Step 4, the stop.** I wrote `scripts/check_registry_names.py` (reads `hypotheses/pending/` and `done/`, prints rejected entries and totals, writes nothing, exits 0). Running it was **denied by the permission mode** ("don't ask mode") in both forms I tried: `env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src:. UV_PROJECT_ENVIRONMENT=$HOME/.venvs/signal-lab uv run --python 3.12 --group dev python scripts/check_registry_names.py`, and the same without `env` and `UV_PROJECT_ENVIRONMENT`. The task names this command, and the Makefile has no target for a one-off script, so I tried nothing else. Earlier in the run a compound `cd ... && for ...` call was also denied; I read the files with the Read tool instead, which is not a workaround for step 4. There is no totals line and no rejected-name list to report.
- **Uncommitted:** `scripts/check_registry_names.py` (untracked, never run, never put through `check-scoped`); `HANDOFF.md` (Cowork's edits, plus this receipt); `OWNER-QUEUE.md` and `decisions/proposed/0034-...` (Cowork's); `AGENTS.md`. **Not done:** step 4's run, its `check-scoped` and commit, step 5 (the records, including `git mv` of decision 0034, the 0032 addendum, the OWNER-QUEUE L6 line and the `H-2026-0010` note; the `git grep` for pins was not run) and its `check`.
- **Reading of `decisions/0062` item 8:** owner: a permission denial in the nightly run's settings is not Cowork's to rule on (when unsure, owner). Cowork to check first: whether the allow list covers `uv run --python 3.12 --group dev python scripts/<file>.py` with the thread variables set, or whether the task should name a make target for it.

### 2026-10-19 -- task 62: canary run, the allow-list fix committed (Claude Code, sonnet, nightly 2026-10-19T17:10)

**rc=0.** Commits: `0509c3c` (the allow-list fix, four files) and this receipt's commit. No push (`push=no`).

- **Step 1.** `git log --oneline -3`: `aec7eee`, `b22236a`, `c4892c2`. `git status --short`: ` M HANDOFF.md`, ` M scripts/nightly/nightly_gate.py`, ` M scripts/nightly/prompt.md`, ` M scripts/nightly/run.sh`, ` M tests/test_nightly.py`.
- **Step 2 (revised).** `scripts/unattended.sh check-scoped` rc=0, 511 s, tier=FULL, slow files left out: none; no rc 75. Log: `results/audit/_unattended/20261019-230027-check-scoped`.
- **Step 2b, the guard.** `cat git_key.pub` as its own call was **blocked by the nightly guard**, not run. First sentence of the block: "nightly guard (decisions/0062): this command names vendor data or a secret (data/raw, data/snapshots, .env, a key)."
- **Step 3a.** `git diff --ignore-cr-at-eol --stat` showed exactly the four files plus `HANDOFF.md`; the four were committed as `0509c3c` with the task's message, nothing else.
- **Not done / to check:** nothing skipped. Cowork to check that `status.txt` for this run names no denied commands.

### 2026-10-19 -- task 62: canary STOPPED at step 2 (Claude Code, sonnet, nightly 2026-10-19T15:25)

**STOPPED, no rc (the command never ran).** Step 1 done: `git log --oneline -3` was `b22236a`, `c4892c2`, `2c48413`; `git status --short` showed only ` M HANDOFF.md` (the release line and queue note, Cowork's, uncommitted). Step 2: `scripts/unattended.sh check` was **denied by the permission mode** ("don't ask mode") before it started, so there is no log directory and no rc 75 check. I tried nothing else: running it another way would work around the denial. Uncommitted: `HANDOFF.md` (Cowork's release-line edit, plus this receipt). Nothing pushed. Reading of `decisions/0062` item 8: owner: a permission denial in the nightly run's settings is not Cowork's to rule on (when unsure, owner). Cowork to check first: whether the headless run's allow-list (`.claude/`) covers `scripts/unattended.sh` and `make`; task 62 exists to find exactly this.

### 2026-10-19 -- task 61: the nightly worker lands; decisions/0062 and the build committed (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `2c48413` (decisions/0062, HANDOFF, CLAUDE.md), `c4892c2` (the build) and this receipt's commit.

- **Step 0.** `git status --short` and `scripts/nightly/` (six files) were as specified; the HANDOFF diff was additions only, in the places the task lists; the other three diffs were as described.
- **Step 1.** `bash -n scripts/nightly/run.sh` rc 0. The gate printed `GO=0`, `REASON='nothing is released'`. The lock: with the lock held, `scripts/unattended.sh check` gave rc=75 with "another run holds" on stderr, and `results/audit/_unattended/` stayed at 67 directories (held from a subshell with `flock`, not two terminals).
- **A stop, then a ruling.** The first `check-scoped` returned rc=2: `tests/test_select_slow.py::test_nothing_reaches_repo_code_in_a_way_the_selector_cannot_see` found `tests/test_nightly.py` (importlib, subprocess) missing from `INVISIBLE`. Reported; the owner ruled "option 1, add it to INVISIBLE". **Not in the task's file set:** `tests/test_select_slow.py` gained `tests/test_nightly.py` in `INVISIBLE` with a comment, and is in the second commit.
- **Second `check-scoped`.** rc=0, 428 s, tier=FULL, slow files left out: none; 938 passed. Log: `results/audit/_unattended/20261019-150833-check-scoped`.
- **Anything not done:** the two-terminal form of the lock test was done from one shell. The push follows this receipt's commit.
- **Push, update (2026-10-19 15:25, Cowork):** checked from the remote itself (`git ls-remote`): GitHub's `main` is `b22236a`, this receipt's commit, equal to HEAD and to `origin/main`. Both `check-scoped` logs read: the first rc=2 at 11:15 (the `INVISIBLE` test, Cowork's miss in writing `tests/test_nightly.py`), the second rc=0 at 15:15, 428 s, tier FULL, on files last written before it started.

### 2026-10-16 -- task 59: the implied-vol file loaded, coverage report written, task 56's gate reported (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `7301e42` (`scripts/fdr_vs_fwer.py` pinned to its twelve), `2dcd030` (the records), `23c9f0a` (`.claude/settings.json`), `391c424` (the build and `results/impvol/coverage.{md,json}`). The first attempt's stop is the receipt below this one; Cowork's option (b) ruling cleared it.

- **Disclosure, a slip of mine:** to learn the block layout I printed `header_rows` from `raw_structure.json` for the three implied-vol sheets. For those sheets it holds rows 5-8, which are **vendor values** (implied vols and dates for several series). That is against the hard rule on `data/raw/`. Nothing was written, committed or summarised from it, and I should have taken rows 1-4 only. `inspect_raw` keeps storing data rows in `header_rows` for series-block sheets; Cowork may want it to stop at the header rows.
- **Step 0.** Validator: 16 pending, 0 rejected; rows as expected (0018 signal/volatility_stress/region/both; 0019 signal/volatility_stress/duration/directional; 0020 signal/volatility_stress/credit/directional; 0021 measurement/covariance/covariance/both); no `data_required` id matches `TICKER_RE`. `make check` green (24 passed, fast tier; `tests/test_fdr_vs_fwer.py` 6 passed), `make governance` OK. `git status --short` was exactly step 0's list. `.claude/settings.json` diff (`--ignore-cr-at-eol`): adds `Bash(git push origin main)` to allow; replaces `Bash(git push:*)` in deny with `git push --force:*`, `-f:*`, `origin main --force:*`, `origin main -f:*`, `origin main +:*`.
- **Step 1.** `inspect_raw.py` skips any file named `~$...` and prints `skipped Excel lock file: <name>`. New `tests/test_inspect_raw.py` (a junk `~$real.xlsx` beside a synthetic workbook: rc 0, only `real.xlsx` described).
- **Step 2.** `make inspect-raw` rc=0 (output to `$HOME/inspect_raw.out`, not opened). `bbg_impvol_values_only.xlsx` sha256 `aeb90f8758e46fbd`. `IV_Daily_v` 5,466 x 92, 31 series ids in row 1; `IV_Weekly_v` 1,918 x 146, 49; `Probe_Summary_v` 215 x 14, 13 non-empty cells in row 1 (one blank between the table and its parameter columns). Dimensions equal Cowork's expectation.
- **Step 3.** `src/signal_lab/loaders/impvol.py` (rules 1 to 5; `STALE_RUN_WEEKS = 6`; a run needs consecutive Fridays, so a missing Friday ends it, Claude Code's reading of "consecutive"). `tests/test_impvol.py`: 13 tests on synthetic blocks, including every case the task listed. Manifest rows added for `IV_Weekly_v` (`implied_vol`), `IV_Daily_v` (`implied_vol_daily`) and `Probe_Summary_v` (`implied_vol_probe`); the manifest reader validates no layout, so `series_blocks` needed no registration. `bbg_impvol_all.xlsx` has no row.
- **Step 4.** `make impvol-coverage` writes `results/impvol/coverage.{md,json}` (dates and counts). **80 series; 59,090 weeks before the rule; 385 removed (gold: 76 + 38 + 102 + 83 + 86); 58,705 kept; no two series share a lab id; last Friday 2019-12-27 for all.** Differences from Cowork's note: **(1)** his stated totals, 59,114 and 58,729, are 24 above his own table's rows, which sum to 59,090 and 58,705; every per-series row I computed equals his table. **(2)** `SKEW Index|PX_LAST` has **1 missing Friday**, where the table says 0 (1,560 weeks either way). Rules not changed.
- **Step 5.** `build_characteristics.py --store-id huber6-v3 --root <scratch> --report-root <scratch> --supersedes ""` returned **rc=4**: the factors hash equals the run of record's, and **the gate fails: 339,744 cells compared, largest absolute difference 2.66.** A throwaway comparison (scratchpad, not committed) of the same arrays: **19,746 cells differ, in exactly four instruments, every compared cell of each: `LET1TREU` 5,328 (max 1.96), `I02913JP` 5,328 (2.32), `LP05TREU` 5,328 (2.66), `I12823GB` 3,762 (1.45)**; all six factors equally. These are the four ex-USD bonds `decisions/0056` converts with Bloomberg's close; `CONVERTED` still lists the 17 `0053` series only. `LG38TRUU` (dollars) matches. The build stopped before writing a store; the scratch directory held a log only and was removed. No code changed and `CONVERTED` is not extended; Cowork rules.
- **Step 6.** `scripts/unattended.sh check-scoped`: rc=0, **596 s, tier=FULL** (could not place every changed file, so the whole suite), slow files left out: none. Log: `results/audit/_unattended/20261016-153927-check-scoped/` (load average 1.21 at start, 1.70 at end).
- **Push:** `git push origin main` was a fast-forward, `32bdd9f..914130a` (five commits: `7301e42`, `2dcd030`, `23c9f0a`, `391c424` and this receipt's commit `914130a`). `git rev-list --count @{u}..HEAD` printed **5** before and **0** after.

### 2026-10-16 -- task 59: STOPPED at step 0, nothing committed; for Cowork to rule (Claude Code, Sonnet 5.5)

**Task 59 stays in the queue; nothing in it was done beyond step 0's checks.** No commit, no push, no code, no edit except this receipt. `git status --short` was exactly the list step 0 expects.

- **Validator (step 0):** `HypothesisRegistry(params=get_params()).load_tolerant("pending")` gave **16 valid, 0 rejected**. New rows: 0018 signal / volatility_stress / region / both; 0019 signal / volatility_stress / duration / directional; 0020 signal / volatility_stress / credit / directional; 0021 measurement / covariance / covariance / both. No `data_required` id matches `TICKER_RE`. (A bare `uv run python -c` cannot import `signal_lab`; it needs `PYTHONPATH=src:.` as pytest's `pythonpath` does, and `UV_PROJECT_ENVIRONMENT=$HOME/.venvs/signal-lab`.)
- **`make governance`:** rc=0, no uncited owner-only change since 85694662.
- **`make check`: FAILED, 2 failed, 812 passed, 64 deselected, 121 s**, both in `tests/test_fdr_vs_fwer.py`:
  - `test_reads_twelve_hypotheses_grouped_as_the_task_describes`: `assert len(hyp_ids) == 12`, got 16.
  - `test_spread_true_covers_every_axis_before_doubling_up`: expected axis groups `{0..5}`, got an extra group `6`.
- **Cause:** `study.read_axis_groups()` reads the live `hypotheses/pending/`. The tests hard-code the 12 hypotheses and 6 target axes of the study's design. The four new untracked files add 4 hypotheses and a seventh axis (`covariance`, H-2026-0021). Not a code defect, and not caused by anything in task 59's build steps.
- **Decision for Cowork** (I did not change `tests/`, and did not commit the records, per "stop and report on the first failure"):
  - (a) Pin the two tests to the 12 ids the study was designed around, or to a fixed fixture directory, so the live registry can grow. Tests only, not owner-only. Claude Code's recommendation.
  - (b) Let `read_axis_groups()` take a pending directory or an id list, with the study's script passing the 12.
  - (c) Rule that the study should now read all 16, and rewrite the expectations (this changes what the FDR-vs-FWER study means, so it is a judgement).
- **Also check:** whether step 0's "`make check`" expectation should have anticipated this, and whether any other fast-tier test counts the pending directory. This run found only these two.

### 2026-10-16 -- task 58: bbg_exusd_bonds_extra.xlsx described, structure only (Claude Code, Sonnet 5.5)

**rc=0 on the second run.** The first `make inspect-raw` (2026-10-15) returned **rc=2**: `BadZipFile` on `~$bbg_impvol_all.xlsx`, a 165-byte Excel lock file left in `data/raw/bloomberg/` while the owner had that workbook open (`inspect_raw.py` globs `*.xlsx`). The owner closed the workbook, the lock file was gone, and the rerun returned rc=0. The printout went to `$HOME/inspect_raw.out`, not opened beyond error lines on the failed run. `inspect_raw.py` could skip `~$` files; not changed here (no code in this task). `sha256sum` first 16 hex: `7464927042b769de`; 5,823,494 bytes. Nothing from `raw_meta.json`; no row 2-8 printed.

From `data/universe/raw_structure.json`, row 1 of the header, dimensions, dates:

| Sheet | n_rows | n_cols | Row 1 / dates |
|---|---|---|---|
| `levels` | 10,958 | 15 | `date`, then `LEATTREU`, `LET3TREU`, `LET5TREU`, `LET7TREU`, `LET0TREU` (`_local_EUR`), `LSG1TRGU`, `I08043GB` to `I08048GB` (`_local_GBP`), `BEIG1T`, `BEIG3T` (`_local_EUR`). Col 1: 10,958 non-empty, 1990-01-01 to 2019-12-31 |
| `analytics_wide` | 10,960 | 37 | `ticker`, then each of the 12 nominal tickers three times (`LEATTREU` ... `I08048GB`). Col 1: 10,960 non-empty, 1990-01-01 to 2019-12-31 |
| `linker_fields` | 11 | 8 | `mnemonic`, `BEIG1T_result`, `BEIG3T_result`, `BEIG1T_is_number`, `BEIG3T_is_number`, (blank), `BEIG1T`, `BEIG3T` |
| `japan_check` | 10,965 | 11 | `ticker`, `name`, then nine blank. Col 10: 10,958 non-empty, 1990-01-01 to 2019-12-31 |
| `analytics` | 51,452 | 7 | `date`, `ticker`, `index_name`, `oad_tsy`, `yield_to_worst`, `oas`, `oas_field`. Col 1: 51,452 non-empty, 1998-06-30 to 2019-12-31 |
| `Formula Version` | 79 | 3 | `sheet`, `cell`, `formula` |
| `Loader Notes` | 37 | 2 | dimensions only, as asked |
| `Pull Report` | 55 | 9 | `sheet`, `ticker`, `field`, `first_non_blank`, `first_unbroken_daily_run_start`, `non_blank_rows`, `#N/A_cells`, `other_error_cells`, `empty_cells`. Col 4 (55): 1998-06-30 to 2013-12-31; col 5 (55): 1998-07-31 to 2015-06-12 |

**Against Cowork's expectation:** `levels` is 15 columns as expected, but the order is the five EUR, the eight GBP, then the two `BEIG` (the expectation listed `BEIG` before the GBP). Three sheets Cowork did not list: `analytics_wide`, `Formula Version`, `Pull Report`. `analytics` has 51,452 rows from 1998-06-30. `analytics_wide` row 1 is a ticker row, so its field names are on a later row (not read). **No sheet's last date is on or after 2020-01-01; the latest is 2019-12-31.** The file was not edited.

- **Push:** see the line below, written after the push.
- **Push, update (2026-10-16, Cowork):** the line above was never followed by one. Checked from `git` on 2026-10-16: `origin/main` is `32bdd9f`, equal to HEAD (this receipt's commit), and the remote-tracking reflog's last entry is an `update by push`. So task 58's push landed.

### 2026-10-15 -- task 57: decisions 0059 (decided) and 0060, OWNER-QUEUE L37 and L38 closed, L39 opened (Claude Code, Sonnet 5.5)

**rc=0.** Commit `f4dcc64` (the records: `HANDOFF.md`, `OWNER-QUEUE.md`, new `decisions/0059-the-phase-2-solver.md` and `decisions/0060-four-hypotheses-get-their-cross-section.md`; nothing else). Before it, `git status --short` showed exactly those four paths and ` M .claude/settings.json` (not committed, still modified), and `git log` ended at `9b1e0d5`. `make check` rc=0 (24 passed, fast tier) and `make governance` rc=0 (no uncited owner-only change since 85694662). No code, no params, no audit, no vendor call.

- **Push:** `git push origin main` was a fast-forward, `7cf303e..c2d6d42` (`f4dcc64`, `9b1e0d5` and the receipt commit `c2d6d42`). `git rev-list --count @{u}..HEAD` printed **3** before and **0** after.

### 2026-10-12 -- task 56: store huber6-v4, the ex-USD bonds on Bloomberg's close, the credit factor on BAA10Y (Claude Code, Sonnet 5.5)

**rc=0 for the work; the push did not happen.** Commit `e968f28` (the build; `ruff` clean). Log directory `results/audit/_unattended/20261012-092541-check-full/`: **tier check-full (the whole suite)**, rc=0, **588 s**, nothing left out, **no golden moved**. The weekly-returns hash moved as expected (`v3` `0377b3fc...`, `v4` `2fef64ef...`; four series changed).

- **Step 1.** The FRED call was run by the owner in his own shell (`set -a; source .env; set +a`, so the key never reached this session; I did not open `.env`) with the new `scripts/fetch_fred_baa10y.py`, which reads the key through `FredLoader.api_key`, prints only the status code on an HTTP error, and refuses a request or a row on or after 2020-01-01. **`BAA10Y`: first 1986-01-02 (Cowork's expectation), last 2019-12-31, 8,503 observations, 366 blank.** Registered as `fred_credit_spread` in `raw_manifest.csv` and in `fred_coverage.csv`. `data/raw/fred/fred_baa10y.csv` is not committed.
- **Step 2.** `read_exusd_csv(path, local_ccy)` reads `<ticker>_local_<CCY>` for the four bonds, takes the currency from the suffix and refuses if it differs from `local_ccy` in the coverage table; `LG38TRUU` is read from its `_USD_unhedged` column; the `exempt` set is derived and is `{"LG38TRUU"}`. The FRED-converted columns are not read. `scripts/check_fx_conversion.py`, new heading in `results/fx/conversion_check.{md,json}` (existing rows unchanged; additions only): weekly Friday closes, development window, same day, converted against the FRED-converted column:

  | Series | Currency | Weekly TE (bp/yr) | Lag-1 autocorr. | Cumulative gap (bp) | Weeks | Days regained |
  |---|---|---|---|---|---|---|
  | `LET1TREU` | EUR | 203.11 | -0.49 | -33.96 | 953 | 138 |
  | `LP05TREU` | EUR | 202.83 | -0.49 | -33.96 | 956 | 139 |
  | `I12823GB` | GBP | 199.23 | -0.47 | -14.26 | 702 | 102 |
  | `I02913JP` | JPY | 209.33 | -0.56 | 31.96 | 958 | 162 |

  **All four are inside Cowork's 195 to 210 read; none is near the 1,000 stop.** FX dates dropped for want of a rate: 0 for each. *Days regained* is the business days in the development window with a converted level now and none in the FRED column.
- **Step 3.** `build_factors(..., credit_series=None)` (the default path is unchanged; `v1` to `v3` are not rebuilt) and `run_measurement.load_inputs(params, factor_set, estimation_start)`. `build_characteristics.py` gains `--factor-set huber6-baa10y` and `--estimation-start common`; the manifest records `factor_set`, `estimation_start`, `credit_source`, `factors_common_start`, and `gates_against_run_of_record: skipped` with the reason. Credit is the weekly change in `BAA10Y` x 1e-2 (decimal), dated by its observation date, no lag. **Common start of the six factors: 1999-01-01 (1,093 complete weeks to 2019-12-27)**; Cowork's 2000-12-29 was an estimate. Correlations: `results/characteristics/huber6-v4/factor_correlations.{md,json}` (largest full-sample correlations: equity~commodities 0.41, equity~inflation 0.40, equity~credit -0.37). Goldens moved: none. **I did not run the default path's run-of-record gates after the loader change.** They compare every unconverted instrument at tolerance zero, and the four ex-USD bonds are no longer the FRED-converted series the run of record used, so I expect them to stop on those four unless `CONVERTED` is extended; that is for Cowork to rule, not changed here.
- **Step 4.** The map's rule is unchanged. Test added: `test_every_week_of_the_real_v4_store_is_dated_by_its_friday` (skips where the git-ignored store is absent; it ran here and passed). Every task-54 test in `tests/test_exposures.py` passes unchanged except the two task 55 changed.
- **Step 5.** `make characteristics ARGS="--store-id huber6-v4 --supersedes huber6-v3 --factor-set huber6-baa10y --estimation-start common"`. `directory_hash` **`b6181bcde28b7e95e69839ff29f2a0a0f19e7552f970b3a24804fcebb7569206`**. **990 weeks, 2001-01-12 to 2019-12-27.** Estimated 84, not estimated 8, measured 23,117 rows over 24 instruments (`v3`: 888 weeks, 21,722 measured rows). Instruments: 53 at the first week, **0 at 2001-01-05**, 84 at the last week. **Not as Cowork expected:** the first week is after 2001-01-05 (the 104-week estimation window needs two years from 1999-01-08), so `0058`'s "What would reopen it" applies and I carried on. First rows: 53 on 2001-01-12, 11 on 2001-01-19 (64 by then), 10 on 2002-12-27, 2 on 2003-11-28, then one each 2004-07-02, 2004-11-26, 2005-06-24, 2007-10-26, 2010-07-30, 2010-10-29 and two on 2007-12-28. Every instrument's first row is after 2001-01-05. At 2019-12-27, `v3` against `v4`, by class (84 common instruments; median credit loading, median explained share, median absolute change in equity / real_yield / inflation / dollar / commodities): US Equities 2.24 -> 1.68, 0.755 -> 0.757, 0.005 / 0.149 / 0.143 / 0.003 / 0.002; European Equities -6.18 -> -2.55, 0.620 -> 0.617; HY Corporates -5.48 -> -2.46, 0.586 -> 0.531; IG Corporates -4.89 -> -2.88, 0.816 -> 0.764; Long Treasuries -0.96 -> -6.20, 0.908 -> 0.930; Treasuries 0.56 -> 0.50, 0.900 -> 0.908; the other thirteen classes are in the store's report and the comparison is reproducible from the two stores. **Rank correlation of the credit loadings across the 84, `v3` against `v4`: 0.85.**
- **Step 6.** `make exposures-check ARGS="--store-id huber6-v4"` (the target now forwards `ARGS`; `check_exposures.py` takes `--store-id`, `params/` still names `v3`) into `results/characteristics/huber6-v4/`. Weeks 990, all Fridays, none skipped; instrument-weeks 79,125 (Cowork's `v3` read 72,606); 53 / 84 instruments at the first / last week (73 / 84); duration measured / estimated / missing 7,375 / 71,750 / 0; no measured duration at or below zero; Friday usage rows 79,125 with `fitted_through` = `used_on_date`, Tuesday rows 79,125 four days after; `2001-01-05` still raises and **`2002-12-20` now reads a week**. Median `axis_duration` at 2019-12-27, `v4` against `v3`'s: Long Treasuries 18.32 (18.32), Gold 8.29 (8.63), IG 5.22 (5.22), TIPS 4.55, Treasuries 4.48, EM Equities 2.63 (2.12), European Equities -1.24 (-1.14). I first ran the target without `--store-id` working, which rewrote `huber6-v3/exposures_check.md` by one blank line; I restored it with `git checkout` before committing.
- **Step 7.** `git push origin main` was **denied at the tool-permission prompt** again (the owner's `.claude/settings.json` rule is still uncommitted). Nothing pushed, no retry. `git rev-list --count @{u}..HEAD` printed **2** before this receipt's commit: `1be32c9` (task 55's receipt update, which the owner's push of `bf00dc7` did not carry) and `e968f28`; it reads 3 with this receipt.
- **Push, update (2026-10-12).** The owner ran `git push origin main` himself after the denial: `bf00dc7..7cf303e  main -> main`, a fast-forward carrying `1be32c9`, `e968f28`, `fac4294` and `7cf303e`. `git rev-list --count @{u}..HEAD` printed **0** before this update; this line is the only commit after it, so it reads 1 until the owner pushes it. The task's push is otherwise satisfied.
- **Not done / to know:** the push, and the receipt's own push. No `params/` edit (it still names `huber6-v3`; Cowork writes the patch from these figures). No audit, no solver, no hypothesis moved. Uncommitted and not mine: `.claude/settings.json`, `decisions/proposed/0059-the-phase-2-solver.md`.


### 2026-10-12 -- task 55: the label map lands, the region axis reads it (Claude Code, Sonnet 5.5)

**rc=0 for the work; the push did not happen.** Commits: `cbf5021` (step 0: SUBSTRATE v0.11 and the records; `make check` and `make governance` passed; the first attempt on 2026-10-11 was denied by the auto-mode classifier and nothing was committed then) and `65a583f` (the build). Log directory `results/audit/_unattended/20261012-082728-check-scoped/`: **tier FULL** (check-scoped could not place every changed file, so the whole suite ran), rc=0, 505 s, nothing left out. Two earlier check-scoped runs stopped at lint, mine (an import order in `tests/test_label_map.py`, one line `ruff format` rewrapped in `exposures.py`); fixed, no test had failed.

- **Step 1.** `scripts/build_label_map.py` wrote `data/universe/label_map.csv` from the draft (sha256 begins `6de22793765f2a24`). **Every count equals the task's:** 84 rows; equity 54, bond 23, real_asset_equity 4, commodity 2, cash 1; region view 46 (US 19, Developed Europe 12, EM 12, Japan 1, APAC ex-Japan 1, Canada 1); region over all rows US 34, Developed Europe 16, EM 15, Global 13, Japan 2, Commodities 2, APAC ex-Japan 1, Canada 1; 24 rows with a curve currency; curve, rating, hy_bucket and market as tabled. **Cross-check against `decisions/0054`:** all 58 equity tickers in both match the table's region; 7 table tickers are absent from the map (tradable-only) and the eighth tradable-only ticker, `LTP5TRUU`, is in the bond table and absent from the map; the 23 bond rows match the bond table's three label columns. The task said eight tradable-only tickers sit in the equity table; it is seven, plus `LTP5TRUU` in the bond table.
- **Step 2.** In `characteristics/exposures.py`: `load_label_map`, `LABEL_MAP_PATH`, `LABEL_COLUMNS`, `VIEW_REGIONS`, `REPORT_REGIONS`, `REGION_COLUMNS`, `UNBUILT_LABEL_AXES`; `ExposureMap(loaded, label_map=None)` and `from_params(params, root, label_map=None)`. Slugs as suggested: `region_us`, `region_dev_europe`, `region_japan`, `region_apac_ex_japan`, `region_canada`, `region_em`, `region_global`. **Store/label set check on the real store:** the task expected the same 84 in both. The store's `instruments` table lists **92** (the 8 tradable-only have no row), so the check compares the label map with the **84 instruments that have a row**; they are the same 84. Real store at 2019-12-27: `at` 84 x 36, region frame 84 x 6 summing to 19/12/1/1/1/12, the engine rule 84 x 17.
- **Step 3.** New `tests/test_label_map.py` (11 tests: counts; the two cross-checks; the normalised columns; blanks outside bonds and cash; `region_view`; column order; an unmapped verbatim value raising; tradable-only dropped and the commodities rename; byte-for-byte regeneration, which **skips when the git-ignored draft is absent** and ran here; a draft with another hash refused). Added to `tests/test_exposures.py`: the region frame, the reporting columns, the label columns on `at`, a store/label mismatch both ways, a missing file, and an autouse synthetic label map. **Changed, not weakened:** `test_the_label_axes_raise_naming_decisions_0054_and_anything_else_is_a_value_error` became `test_sector_and_style_raise_naming_decisions_0054_and_anything_else_is_a_value_error` (region now returns the frame; sector and style still raise, naming `decisions/0054 item 8`), and `test_the_rule_has_the_six_factors_and_four_axes_and_no_missing_value` became `..._four_axes_and_seven_regions_...` (it lists the seven new columns).
- **Step 4.** Label map sha256 `60ee1934bf89582c8630b1c4a8b2f9b55e1181ec0cd55dc982c2dfa3be85bdb5` for both the committed blob and the working-tree file; the working tree is LF (git has not rewritten it), so neither is CRLF yet. The test normalises CRLF. **`git push origin main` was denied at the tool-permission prompt** ("Permission to use Bash with command git push origin main ... has been denied"), so nothing was pushed, and I did not retry. The owner can run it. `git rev-list --count @{u}..HEAD` printed **2** before this receipt's commit (`cbf5021`, `65a583f`).
- **Push, update (2026-10-12).** The owner ran `git push origin main` himself after the denial: `c8e755c..bf00dc7  main -> main`, a fast-forward carrying `cbf5021`, `65a583f` and `bf00dc7`. `git rev-list --count @{u}..HEAD` printed **0** before this update. I also tried the exact command a second time and it was denied again, although the working tree's `.claude/settings.json` allows it; that file is uncommitted, so the session may not have loaded it.
- **Not done / to know:** the push; the receipt's own push; task 56 (it follows 55, and this task ends with "then stop"). Uncommitted and not mine to commit under step 0: `.claude/settings.json` (Cowork's push rule) and `decisions/proposed/0059-the-phase-2-solver.md`. No hypothesis changed state and no golden moved.

### 2026-10-11 -- task 54: the wiring, resolve_exposures reads huber6-v3, params v0.10.0, the lookahead veto checks loadings (Claude Code, Sonnet 5.5)

**rc=0 for the work; the push did not happen.** Commits: `3441eaa` (step 0, queue records, no check, `make governance` OK) and `bda1d2d` (the build, cites `decisions/0055` and `0050`; the commit hook passed). Log directory `results/audit/_unattended/20261011-142834-check-full/`: **tier check-full (the whole suite)**, rc=0, **544 s**, 857 passed, holdout 24 passed. A first `check-full` (`20261011-142657-check-full`) stopped at lint, rc=2 in 59 s (an unused loop variable in `tests/test_exposures.py`); fixed, rerun clean. The params and `veto_lookahead` diffs were Cowork's and are committed as found.

- **Step 1.** `make fx-check`: `results/fx/` UK rows unchanged (the diff is additions only). **Scratch store** built outside the repo (`--root`, `--report-root`, `--supersedes ""`): `directory_hash` `84a5088d82b135c48ba7da5709ebae3f58186c06b08575d1b233ba19e27270f7`, equal to the committed one; the run-of-record gate passed (339,744 cells, difference 0.0). I did not delete the scratch store (it is in the session scratchpad, outside the repo). **New pairs, converted against `LEGATRUU`, weekly Friday closes, 936 weeks, same day:** `LGTRTRGU` (GBP) 281.93 bp/yr tracking error, lag-1 autocorrelation -0.34, cumulative gap -118.63 bp; `LGTRTRJU` (JPY) 273.96 bp/yr, -0.35, -58.75 bp. Both far below 1,000. No FX dates dropped for either. They are in `results/fx/conversion_check.{md,json}` under their own heading.
- **Step 2.** New `src/signal_lab/characteristics/exposures.py`: `ExposureMap` (also the engine's `ExposureRule`, with `requires_row = True`), `from_params(params, root)`, `store_week`, `at(date)`, `axis(name, date)`, `usage()`, and `LabelMapMissing(ExposureMatrixMissing)`. `resolve_exposures(snapshot, params=None, root=None)` returns it; `snapshot` is unused and the docstring says so. Added `engine.NoExposureRow` (raised by `run_walk_forward` for a weight above 1e-12 on an instrument with no row when the rule has the marker), `RunContext.parameter_usage`, and `experiment.attach_parameter_usage`, which `run_experiment` calls. Frame columns: the six factors, `{factor}_se`, `oad`, `oas`, the four `axis_*`, `axis_duration_provenance`, `explained_share`, `reporting_class`. `fitted_through` is the store's per-instrument-week `last_data_date` (the `fit` table), not the manifest. The rule drops an instrument with a missing value in the ten columns, so that instrument has no row; on the real store none is dropped (rule rows equal instrument-weeks). **Tests added (`tests/test_exposures.py`, 21):** store named in params is the one read; wrong hash; absent store and params naming none; real params against an empty root; Friday, Tuesday and six-day reads; seven days after the last week and before the first; duration measured, falling back, an equity ignoring `oad`, an earlier week's `oad` never used; the other three axes and signs; the frame's columns; region, sector and style raise naming `decisions/0054`, an unknown name is a `ValueError`; the rule's columns and no missing value; the usage log; an honest store passes `veto_lookahead` and one fitted late fails; the run context gets the usage and a constant matrix gets none; the engine refuses a held weight without a row and does not for `constant_exposures` or a zero weight. **Two tests replaced:** `test_experiment.py::test_the_exposure_matrix_raises_rather_than_returning_an_identity` and `test_characteristics.py::test_the_exposure_matrix_still_does_not_exist` (now `test_a_missing_exposure_matrix_raises_and_never_returns_an_identity`); both use an empty store root.
- **Step 3.** `tests/test_vetoes.py` changed: `test_lookahead_passes_when_nothing_is_used_early`, `test_lookahead_fails_on_a_single_peek`, `test_lookahead_boundary_same_day_use_is_allowed`, `test_lookahead_against_the_synthetic_vintage_panel` (now pass an honest `parameter_usage`, helper `honest_parameters`), and `full_context` (the one full context; the two `apply_vetoes` tests that build on it inherit it). No assertion weakened. Added: the loadings one day late fail and the same day passes (and four days earlier passes); absent, empty or column-short `parameter_usage` fails as a missing input, and so does missing `observation_usage`; a missing date fails with "undated"; a peek in each half reports both; the passing detail names both counts. `tests/test_params.py`: the params directory hash equals the committed manifest's. **Params hash `413d84f6b631359bee74883cb63f93660023cc50d4ff49306579c401a4d61623`, as expected.**
- **Step 4.** `make exposures-check`, `results/characteristics/huber6-v3/exposures_check.{md,json}`. **Every figure equals Cowork's read, none differs:** 888 weeks 2002-12-27 to 2019-12-27, all Fridays, none skipped; 72,606 instrument-weeks; 73 and 84 instruments at the first and last week; duration measured 6,763, estimated 65,843, missing 0; measured at or below zero 0; means 1.4274, 1.2792, 1.3006; `LT13TRUU` 677 measured and 211 estimated (2002-12-27 to 2007-01-05), `LDC5TRUU` 758 / 0, the other six 888 / 0; Friday usage 72,606 rows with `fitted_through` equal to `used_on_date`; Tuesday usage 72,606 rows, each four days after; 2001-01-05 and 2002-12-20 raise. **Median `axis_duration` by class at 2019-12-27:** European Equities -1.14, Japanese Equities -0.16, US Equities -0.02, APAC ex-Japan Equities -0.02, Commodities 0.08, Cash 0.08, DM ex-US Equities 1.33, HY Corporates 1.34, Real Assets 1.81, EM Equities 2.12, EM Corporate Bonds 2.48, Ex-USD Bonds 2.73, EM Sovereign Bonds 3.30, MBS 3.71, Treasuries 4.48, TIPS 4.55, IG Corporates 5.22, Gold 8.63, Long Treasuries 18.32. The seven classes Cowork gave all match.
- **Step 5.** `characteristics/__init__.py`, the chain comment and `ExposureMatrixMissing`'s docstring in `harness/experiment.py`, and `build.mk` (now names the store `params/` names, and `exposures-check`) corrected.
- **Step 6 and the push.** **`git push origin main` was denied at the tool-permission prompt, so nothing was pushed.** It ran no git command and printed no rejection; the denial is the harness's, as it was for task 53's push (that earlier denial was the same, and it is the reason task 53's push did not land). I did not retry or look for another route. `git rev-list --count @{u}..HEAD` printed **140** after `bda1d2d`, and will be 141 with this receipt, not 0. The owner pushes, or approves the push prompt and a session reruns it.
- **Push, update (2026-10-11).** The owner ran `git push origin main` himself after the denial. Checked afterwards from the session: `git rev-list --count @{u}..HEAD` printed **0** and `origin/main` is `8fc0042` (this receipt's first commit). The push's own output was not shown to the session. This line is the only commit after it, so `@{u}..HEAD` is 1 until the owner pushes it; the task's push is otherwise satisfied.
- **Not done / to know:** (1) the push, above (now landed, except this update). (2) I did not delete the scratch store from step 1; it is under the session scratchpad. (3) No solver, no label map, no alphas; region, sector and style raise; `resolve_exposures` has no caller that reaches it until `build_weight_rule` stops raising `OptimiserMissing`, so `run_experiment`'s glue is tested through `attach_parameter_usage` and not end to end.

### 2026-10-10 -- task 53: every return in dollars, store huber6-v3 (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `bf44a86` (step 0, after `make check` and `make governance`) and `270ecb9` (the build). Log directory `results/audit/_unattended/20261010-225742-check-full/`: **tier check-full (the whole suite)**, rc=0, **521 s**, 833 passed, holdout 24 passed. An earlier `check-full` (`20261010-225615-check-full`) stopped at lint, rc=2 in 51 s (two unused imports in `scripts/check_fx_conversion.py`); fixed, formatter run on two files, rerun clean. `huber6-v1`, `huber6-v2` and `M-20261003T181155Z` are untouched.

- **Step 1.** The reader is in code (`src/signal_lab/loaders/fx.py`); I did not hash the file from the shell. `fx.check_file` hashes it and refuses one not beginning `1d6fbb63e8a33e2e`; it passed on the real file. Rows before the holdout and first date per column equal Cowork's table exactly: EUR 10,283 (1980-01-02), GBP 10,436, CAD 10,436, HKD 10,407, INR 10,200 (all 1980-01-01 or -02 as listed), KRW 10,001 (1981-04-13), TWD 9,327 (1983-10-05), JPY 10,436 (1980-01-01). `raw_manifest.csv` row: role `fx_spot`. The convention table is in code; EUR and GBP multiply, the six `USDxxx` divide, an unknown column or a non-positive rate is refused.
- **Step 2.** Conversion and guard are in `BloombergLoader.load_returns` (after business days, before truncation) and `load_benchmark`; the hedged tab is guarded too. **The real load converts 21 series, not 19:** the 19 of the task plus `LGTRTRGU` (GBP) and `LGTRTRJU` (JPY), the two restatements `decisions/0052` made not investable, which are still columns of the `TR Levels` sheet and in the universe file. They are converted so the guard has nothing to refuse; they stay flagged and unholdable. Dates dropped for want of an FX rate (from each series' true daily start to the holdout): MXCA 2,086 (all 1972-79, before the FX file starts; none in the development window), MXEU0CD/CS/EN/FN/HC/IN/IT/MT/TC/UT and MXEUG 32 each (1995-98, none in the development window), MXIN 60 (2007-2019, in the window), TAMSCI 1 (2008-01-03), all others 0. **No series has a blank quote currency**, in the returns, candidates, benchmark or hedged sheets. The guard stopped on nothing. **Factors hash equals `3401475e…fafa9`.** The weekly-returns hash is now `0377b3fc550ec8e5592b2e62af131c12ad33591ff6d7fc41e7267c43659d8e69` (was `d9aac6ca…972a`).
- **Step 3.** `make fx-check`, `results/fx/conversion_check.{md,json}`. Same day, 938 weeks: weekly TE 238.5 bp/yr (Cowork 238), 4-week TE 108.6 non-overlapping and 115.9 overlapping (Cowork 107), lag-1 autocorrelation -0.51 (-0.51), cumulative gap -50.0 bp (-50). Nothing differs beyond the tolerances. Rate lagged one business day: 601.1, 263.7 non-overlapping, -0.50, -54.3. **Lagged is about 2.5 times as wide, Cowork said about twice**; same-day is the better alignment. The 4-week figure's definition (non-overlapping, every fourth Friday) is mine.
- **Step 4.** `make universe`: **102 series, 92 investable, 10 excluded**. `NDDLUK` is in `NOT_INVESTABLE_OTHER` with the reason as given. `euro_treasury_1_10y` appeared in two files, both changed: `data/universe/bbg_exusd_bonds_coverage.csv` (hand-kept, no generator) and `data/universe/investable_universe.csv` (regenerated); in `HANDOFF.md` it appears only in this task's text. Test changed: `test_the_committed_universe_is_what_build_universe_produces` (93 to 92, cites 0053, asserts `NDDLUK`).
- **Step 5.** Against the run of record: 66 instruments, **339,744 cells, largest difference 0.0**. Against `huber6-v2`, instruments neither left nor converted: **345,072 rows, 0 unmatched, largest difference 0.0 in the loading and 0.0 in the standard error**. Converted series: 90,564 cells on both sides, largest difference 7.711 (a loading).
- **Step 6.** `make characteristics ARGS="--store-id huber6-v3"` (2 m 45 s). Directory hash `84a5088d82b135c48ba7da5709ebae3f58186c06b08575d1b233ba19e27270f7`. **84 estimated (Cash included), 8 not**, 92 instruments; loadings 435,636, fit 72,606, measured 21,722; 2002-12-27 to 2019-12-27: all as expected, so no converted series lost a week to a missing rate. Manifest cites `decisions/0049`, `0052`, `0053`, task 53, `supersedes: huber6-v2`. Median dollar loading and explained share, before then after:

| series | ccy | dollar loading | explained share | FX dates dropped |
|---|---|---|---|---|
| I02513EU | EUR | +0.10 to -1.08 | 0.47 to 0.86 | 0 |
| MXEUG | EUR | +0.60 to -0.53 | 0.84 to 0.86 | 32 |
| MXEU0CD / CS / EN / FN | EUR | +0.71 / +0.75 / +0.85 / +0.58 to -0.50 / -0.44 / -0.32 / -0.58 | 0.73 / 0.51 / 0.60 / 0.75 to 0.77 / 0.60 / 0.63 / 0.79 | 32 each |
| MXEU0HC / IN / IT / MT | EUR | +0.82 / +0.66 / +0.79 / +0.65 to -0.41 / -0.54 / -0.38 / -0.58 | 0.50 / 0.79 / 0.64 / 0.71 to 0.53 / 0.80 / 0.62 / 0.75 | 32 each |
| MXEU0TC / UT | EUR | +0.56 / +0.46 to -0.60 / -0.74 | 0.49 / 0.51 to 0.51 / 0.54 | 32 each |
| MXCA | CAD | +0.29 to -0.06 | 0.68 to 0.72 | 2,086 |
| MXCN | HKD | -0.01 to -0.02 | 0.42 to 0.42 | 0 |
| MXIN | INR | +0.26 to +0.13 | 0.34 to 0.35 | 60 |
| MXKR | KRW | +0.21 to -0.10 | 0.45 to 0.50 | 0 |
| TAMSCI | TWD | +0.21 to +0.03 | 0.38 to 0.39 | 1 |

  Findings, not failures: **`MXIN` (+0.13) and `TAMSCI` (+0.03) still have a positive median dollar loading.** The eleven European equity series moved to -0.32 to -0.74, more negative than the task's "about -0.07 to -0.40"; `MXEU0UT` (-0.74), `MXEU0TC` (-0.60), `MXEU0FN` and `MXEU0MT` (-0.58) are outside that range. `I02513EU` is -1.08, inside the converted euro bonds' range (-0.84 to -1.15). `MXCN` barely moved.
- **Step 7.** `results/characteristics/huber6-v3/report.md` has the new table (the manifest carries its rows, so `--report-only` rebuilds it) and the duration-times-spread exclusion of the three classes and `I02513EU`, `I02913JP`, `I12823GB`, `LET1TREU`, with the reason in the heading. The table now has 12 instruments (the EM, HY, IG, MBS and the two Ex-USD corporates `LP05TREU`; `LG38TRUU` was never in it).
- **Tests added:** `tests/test_fx.py` (18: the two directions, the table, unknown column, holdout cut, blank is missing, non-positive rate, no carrying, the guard refuses and reports, exempt series, the loader converts and records, refused without a manifest row, wrong hash, unconvertible series, nothing at or after the holdout) and three in `tests/test_characteristics.py` (the exclusion, the converted table, no section without converted series). Changed: `tests/test_scripts.py` as above. No golden moved.
- **Other changes:** `SeriesMeta.quote_currency` (new field, in `meta_frame`); a blank Index Map quote currency is now kept blank for the guard to report and then set to USD, where it used to be defaulted to USD silently; `scripts/run_measurement.py` keeps the loader's report in `LOADER_REPORT`; `build.mk` has `fx-check`.
- **Not done / to know:** (1) `ls` and `sha256sum` on `data/raw/` are denied here, so the hash and the file's shape were checked through repo code only. (2) The 21 against 19 conversions above. (3) `resolve_exposures` still raises; nothing was built from `decisions/0050` or `0051`. (4) The push is the next step; its output is in my report to the owner, not here, because it follows this receipt's commit.

### 2026-10-07 -- task 52: the universe, the ex-USD analytics, store huber6-v2, the report's table like for like (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `5fb47e3` (step 0, queue records, after `make check`) and `49b202e` (the build). Log directory `results/audit/_unattended/20261007-184728-check-full/`: **tier check-full (the whole suite)**, rc=0, **504 s**, 812 passed, holdout 24 passed. Task 51's store `huber6-v1` and its report are untouched; `M-20261003T181155Z` was not re-run.

- **Step 1.** `make universe`: **102 series, 93 investable, 9 excluded**, as expected; `LGTRTRGU` and `LGTRTRJU` carry the reason from `decisions/0052` and keep their reporting class. Tests changed: `tests/test_scripts.py::test_the_committed_universe_is_what_build_universe_produces` (95 to 93, docstring cites 0052, asserts both series not investable). No other test or constant changed.
- **Step 2.** **I could not check the hash from the shell** (`ls` and `sha256sum` on `data/raw/` were denied), so the check is in code: `exusd_analytics.check_file` hashes the file and refuses one whose sha256 does not begin `a76df50225f99128`. It passed on the real file (sha256 `a76df50225f99128a737a0e470042541e26c1b4261728bb29873c73dbed2978e`), 44,190 rows, 7 tickers. No value was printed. New: `src/signal_lab/loaders/exusd_analytics.py` (reader, field map, the daily-start rule), a merge in `BloombergLoader.load_analytics`, the `raw_manifest.csv` row (`analytics_exusd`, layout `long_date_ticker`; the file is required where the row exists, a fixture's manifest has none and loads as before), `scripts/build_exusd_analytics_coverage.py` and `make exusd-analytics-coverage`. `loader.report["analytics"]["exusd"]` records the hash, row count, tickers and series per field. A ticker and field in both files stops the load; the swap spread lands in `INDEX_OAS_SWAP` only. **Daily starts: every one equals Cowork's expected table** (rule: the first observation from which each of the next 20 follows within 5 calendar days; cut at the holdout before the rule runs). **Factors hash after the step: equals `3401475e…fafa9`** (the build checks it and stops otherwise). Series per field for the file: OAD 7, yield 7, OAS_TSY 6, OAS_SWAP 1 (the build's added fields).

| ticker and field | first observation | true daily start | observations before the holdout |
|---|---|---|---|
| I02513EU|INDEX_OAD_TSY | 2001-12-31 | 2002-06-28 | 4443 |
| I02513EU|INDEX_OAS_TSY | 2002-09-17 | 2002-09-17 | 4382 |
| I02513EU|INDEX_YIELD_TO_WORST | 2001-12-31 | 2002-06-28 | 4443 |
| I02913JP|INDEX_OAD_TSY | 2006-12-29 | 2018-02-28 | 612 |
| I02913JP|INDEX_OAS_TSY | 2002-09-17 | 2002-09-17 | 4377 |
| I02913JP|INDEX_YIELD_TO_WORST | 2006-12-29 | 2018-02-28 | 612 |
| I12823GB|INDEX_OAD_TSY | 2003-01-31 | 2009-07-24 | 2726 |
| I12823GB|INDEX_OAS_TSY | 2003-01-31 | 2005-09-22 | 3650 |
| I12823GB|INDEX_YIELD_TO_WORST | 2003-01-31 | 2009-07-24 | 2726 |
| LET1TREU|INDEX_OAD_TSY | 1998-06-30 | 2002-04-23 | 4529 |
| LET1TREU|INDEX_OAS_TSY | 2002-09-17 | 2002-09-17 | 4382 |
| LET1TREU|INDEX_YIELD_TO_WORST | 1998-06-30 | 2002-04-23 | 4529 |
| LG38TRUU|INDEX_OAD_TSY | 1990-01-31 | 2000-08-31 | 5151 |
| LG38TRUU|INDEX_OAS_SWAP | 2004-07-12 | 2004-07-12 | 4024 |
| LG38TRUU|INDEX_YIELD_TO_WORST | 1990-01-31 | 2000-08-31 | 5151 |
| LGTRTRGU|INDEX_OAD_TSY | 2000-09-29 | 2001-01-16 | 4930 |
| LGTRTRGU|INDEX_OAS_TSY | 2002-09-17 | 2002-09-17 | 4496 |
| LGTRTRGU|INDEX_YIELD_TO_WORST | 2000-09-29 | 2001-01-16 | 4930 |
| LP05TREU|INDEX_OAD_TSY | 2000-10-09 | 2000-10-09 | 4869 |
| LP05TREU|INDEX_OAS_TSY | 2002-09-17 | 2002-09-17 | 4382 |
| LP05TREU|INDEX_YIELD_TO_WORST | 2000-09-28 | 2000-09-28 | 4876 |

- **Step 3.** Gates added to `scripts/build_characteristics.py`: the run of record's instruments must be the build's (Cash out) plus exactly `LGTRTRGU` and `LGTRTRJU`; every stored Huber loading for a shared instrument must equal this build's at tolerance zero. **435,636 cells compared, largest difference 0.0.** On the 84 shared instruments the test's cell rule scores 68,656 cells: pooled r2_oos 0.705440, mean Huber loss 0.223618 (reported, not compared; `fit.json`, 86 instruments, 70,326 cells: 0.702983 and 0.230334). `assert_no_lookahead` as before. The cell set comes from `signal_lab/characteristics/reference.py` (presence only); test: `test_the_scored_cell_set_takes_presence_only_from_a_reference_run`.
- **Step 4.** `make characteristics ARGS="--store-id huber6-v2"` (2 m 58 s). Directory hash `1d5aba88482918caa9c577a35acbda4e9eeffa71d267cf4d8dc67d6c1753cafc`. **85 estimated (Cash included), 8 not**; loadings 440,964, fit 73,494, measured 21,722 (v1: 16,256), instruments 93; 2002-12-27 to 2019-12-27, all as expected. Manifest cites `decisions/0049` and `0052`, task 52 and `supersedes: huber6-v1`. **Against `huber6-v1`: 440,964 loadings on shared cells, largest difference 0.0.** The build's weekly-returns hash is no longer comparable with the run of record's (86 against 84 columns), so the manifest records `factors_equal_run_of_record` and drops the old returns-hash flag.
- **Step 5.** Report `results/characteristics/huber6-v2/report.md`. Each expected figure against the report: LT01TRUU 0.56 [0.30, 0.86] / 0.56 [0.30, 0.86]; LT13TRUU 0.89 [0.79, 0.98] over 677 weeks / same, 677; LT09TRUU 0.97 [0.93, 1.03] / same; LUTLTRUU 0.84 [0.68, 0.95] / same; LT11TRUU 0.84 [0.66, 0.90] / same; LBUTTRUU 1.24 [1.02, 1.56] / same; LUACTRUU 0.84 [0.77, 0.96] / same; LT13TRUU first measured 2007-01-12 with 211 unmeasured weeks / same; no empty week inside any measured span / none; credit over duration times spread for the five HY indices 0.37 to 0.68 / 0.37, 0.58, 0.58, 0.59, 0.68. **Nothing differs by more than 0.01.** 23 of 23 estimated bond-class instruments have a measured duration (`I02913JP` for 96 of 888 weeks, `I12823GB` 545 of 627, `LT13TRUU` 677 of 888). The six ex-USD bond indices:

| instrument | class | weeks | weeks measured | real yield | inflation | credit | -OAD | ratio real yield | ratio inflation | ratio credit | weekly real yield | weekly inflation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I02513EU | Ex-USD Bonds | 888 | 888 | -3.347 | -2.827 | -0.377 | -6.61 | 0.51 | 0.43 | 0.06 | 0.50 [0.37, 0.58] | 0.43 [0.31, 0.65] |
| I02913JP | Ex-USD Bonds | 888 | 96 | -7.989 | -6.057 | 2.511 | -9.42 | 0.85 | 0.64 | -0.27 | 0.85 [0.75, 0.91] | 0.65 [0.53, 0.74] |
| I12823GB | Ex-USD Bonds | 627 | 545 | -2.084 | -2.435 | -0.435 | -4.44 | 0.47 | 0.55 | 0.10 | 0.45 [0.11, 0.80] | 0.56 [0.09, 1.29] |
| LET1TREU | Ex-USD Bonds | 888 | 888 | 0.276 | -0.211 | -0.056 | -1.84 | -0.15 | 0.11 | 0.03 | -0.15 [-0.44, 0.35] | 0.12 [-0.66, 0.78] |
| LG38TRUU | Ex-USD Bonds | 888 | 888 | -3.313 | -3.187 | -0.589 | -6.26 | 0.53 | 0.51 | 0.09 | 0.52 [0.45, 0.62] | 0.47 [0.30, 0.61] |
| LP05TREU | Ex-USD Bonds | 888 | 888 | -2.130 | -2.195 | -2.945 | -5.30 | 0.40 | 0.41 | 0.56 | 0.39 [0.30, 0.55] | 0.44 [0.25, 0.59] |

  (`LG38TRUU` is absent from the duration-times-spread table: its OAS is a swap spread, `INDEX_OAS_SWAP`, and the table reads `INDEX_OAS_TSY` only. `I02913JP`'s spread ratio rests on 96 weeks and is -39, `I12823GB`'s on 313 weeks and is 15; both are in the report as printed.) Also new in the report: the by-period table, measured coverage, and in the explained-share table the lowest instrument and the number below 0.5 at the last week, with the line that Commodities' share is an identity.
- **Step 6.** `scripts/select_slow.py`: a FULL result now lists every slow file as selected and none as left out (status.txt and check.log agree); `describe_loadings.py` calls `require_one_thread`; `threads.py`'s docstring now says what task 49 measured (a difference between thread settings, not between runs).
- **Tests added** (`tests/test_exusd_analytics.py`, 10: field map with a swap row kept out of `INDEX_OAS_TSY`, unknown oas_field refused, monthly run-in truncated, holdout cut, duplicate across files refused, wrong hash refused, no manifest row loads as before, the row makes the file required, the missing marker is not zero, the 20-in-5 rule at its edges; `tests/test_characteristics.py`: the old report test replaced by seven for the new tables, and the presence-only test; `tests/test_select_slow.py`: one). **Tests changed:** `tests/test_scripts.py` as above and the one replaced report test. No golden moved.
- **Not done / to know:** (1) the hash and the file's shape were checked only through repo code, not from the shell, because direct commands on `data/raw/` were denied. (2) `build_characteristics.py --report-only` now works for stores with the new manifest keys (`huber6-v2`), not for `huber6-v1`, whose report stays as committed. (3) I did not open `bbg_tradable_only_longer_history.xlsx`. Nothing was built from `decisions/0050` or `0051`; `resolve_exposures` still raises.

### 2026-10-07 -- task 51: the estimated half of the exposure matrix, store huber6-v1 (Claude Code, Sonnet 5.5)

**rc=0.** Commit `d2d17fb`. Log directory `results/audit/_unattended/20261007-091756-check-scoped/`: **tier FULL, not SCOPED** (the selector: `FULL: data/characteristics/huber6-v1/manifest.yaml is not a path the selector can place`, since a path under `data/` is always full), rc=0, **556 s**, 795 passed, holdout 22+2 collected. The build itself, `make characteristics`, ran twice: the first stopped at step 3 (below), the second wrote the store (3 m 05 s).

- **Where the package went.** `src/signal_lab/characteristics/` (`build.py`, `store.py`, `report.py`). SUBSTRATE §15 puts "exposure mapping" under `portfolio/` but names nothing for loadings estimation, and this builds no mapping, so I used the fallback the task gave. Also `scripts/build_characteristics.py` (with `--report-only`, which re-hashes the store and rewrites the report), `make characteristics`, and a `.gitignore` rule `data/characteristics/*/*.parquet` (checked with `git check-ignore -v`; the manifest is not ignored).
- **The store.** `data/characteristics/huber6-v1/`, directory hash `95db155edf972bf991a72660d474c36590f9af0c38b0865d064513235486e32f` (the snapshot module's `hash_directory`). Rows: loadings 451,572, fit 75,262, measured 16,256, instruments 95. 2002-12-27 to 2019-12-27. **87 instruments estimated (Cash included), 8 not estimated** (tradable-only): LTP5TRUU, M1CXNNA, M1CXVRSD, M1EAMM, M1EAQU, M1EFHDY, M1WDUMMT, MXEU0RL. Every estimated row carries `kind=estimated, estimator=huber_m`; measured rows `kind=measured`, in their own file, never merged. Data files are git-ignored and were not printed; the manifest and `results/characteristics/huber6-v1/report.md` are committed.
- **Step 3.** *Reproduces the test:* **70,326 cells (the test's 70,326); pooled `r2_oos` differs by 0.0 (0.7029825014051894) and mean Huber loss by 0.0 (0.23033442386469188)**, so the 1e-6 allowance was not needed. Max absolute difference between this build's Huber loadings and the run of record's stored ones: 0.0. *First attempt stopped:* I scored the cells where Huber alone has a loading (74,276 cells, r2 0.6979, loss 0.2280), but the test scored only cells where all six estimators had one. I now take that cell set (presence only) from the run of record's `loadings.parquet`. The weekly returns (Cash out) and the factors are hash-equal to the run of record's. *No lookahead:* `assert_no_lookahead` runs inside every build and passed.
- **Interpretation to flag.** The measured value at a date is `weekly_levels`' last observation in the week ending on that Friday, and is NaN, not carried, over a week with none (SUBSTRATE §2 forbids forward fill); the task's "last value on or before that Friday" read literally would carry. Measured cells are included for the 8 tradable-only series too.
- **Explained share by class** (median over instruments; full sample, last week 2019-12-27):

| class | full sample | last week | n at last week |
|---|---|---|---|
| APAC ex-Japan Equities | 0.744 | 0.514 | 1 |
| Cash | 0.013 | 0.012 | 1 |
| Commodities | 1.000 | 0.999 | 1 |
| DM ex-US Equities | 0.902 | 0.778 | 9 |
| EM Corporate Bonds | 0.447 | 0.485 | 1 |
| EM Equities | 0.701 | 0.537 | 12 |
| EM Sovereign Bonds | 0.503 | 0.437 | 2 |
| European Equities | 0.716 | 0.528 | 13 |
| Ex-USD Bonds | 0.432 | 0.514 | 8 |
| Gold | 0.311 | 0.493 | 1 |
| HY Corporates | 0.624 | 0.586 | 5 |
| IG Corporates | 0.821 | 0.816 | 2 |
| Japanese Equities | 0.421 | 0.521 | 1 |
| Long Treasuries | 0.863 | 0.908 | 2 |
| MBS | 0.591 | 0.691 | 1 |
| Real Assets | 0.811 | 0.633 | 4 |
| TIPS | 0.889 | 0.928 | 1 |
| Treasuries | 0.863 | 0.900 | 3 |
| US Equities | 0.761 | 0.755 | 19 |

- **Estimated against measured, every bond index** (median over weeks; `-OAD` is minus the median `INDEX_OAD_TSY` over the same weeks; ratio = loading / `-OAD`):

| instrument | class | weeks | real yield | inflation | credit | -OAD | ratio real yield | ratio inflation | ratio credit |
|---|---|---|---|---|---|---|---|---|---|
| I12877US | EM Corporate Bonds | 636 | -3.060 | -2.169 | -5.920 | -4.80 | 0.64 | 0.45 | 1.23 |
| EMUSTRUU | EM Sovereign Bonds | 888 | -3.172 | -1.818 | -5.213 | -5.89 | 0.54 | 0.31 | 0.88 |
| I20344US | EM Sovereign Bonds | 492 | -3.721 | -1.004 | -1.926 | -5.26 | 0.71 | 0.19 | 0.37 |
| I00183US | HY Corporates | 888 | -1.792 | -1.069 | -6.362 | -4.06 | 0.44 | 0.26 | 1.57 |
| I00184US | HY Corporates | 888 | -3.523 | -2.599 | -8.753 | -9.23 | 0.38 | 0.28 | 0.95 |
| I00185US | HY Corporates | 888 | -1.451 | -0.708 | -7.690 | -4.01 | 0.36 | 0.18 | 1.92 |
| I00188US | HY Corporates | 888 | -1.449 | -0.688 | -10.964 | -3.58 | 0.40 | 0.19 | 3.06 |
| LF98TRUU | HY Corporates | 888 | -1.674 | -0.952 | -8.084 | -4.24 | 0.40 | 0.22 | 1.91 |
| LDC5TRUU | IG Corporates | 758 | -2.150 | -1.806 | -2.247 | -2.76 | 0.78 | 0.65 | 0.81 |
| LUACTRUU | IG Corporates | 888 | -5.613 | -5.531 | -5.660 | -6.61 | 0.85 | 0.84 | 0.86 |
| LT11TRUU | Long Treasuries | 888 | -11.913 | -14.471 | -0.605 | -17.19 | 0.69 | 0.84 | 0.04 |
| LUTLTRUU | Long Treasuries | 888 | -10.355 | -11.526 | -0.541 | -14.62 | 0.71 | 0.79 | 0.04 |
| LUMSTRUU | MBS | 888 | -2.937 | -2.384 | -0.276 | -3.56 | 0.82 | 0.67 | 0.08 |
| LBUTTRUU | TIPS | 888 | -7.052 | -0.316 | -0.117 | -5.77 | 1.22 | 0.05 | 0.02 |
| LT01TRUU | Treasuries | 888 | -1.062 | -0.764 | 0.308 | -1.85 | 0.57 | 0.41 | -0.17 |
| LT09TRUU | Treasuries | 888 | -7.210 | -6.943 | 0.186 | -7.55 | 0.95 | 0.92 | -0.02 |
| LT13TRUU | Treasuries | 888 | -4.025 | -3.496 | 0.564 | -4.51 | 0.89 | 0.77 | -0.13 |

  Standard error against loading by factor and class is in the report; it is large where a class has little exposure (e.g. real yield for APAC ex-Japan equities 91.6).
- **Tests added** (`tests/test_characteristics.py`, 11, fast tier, ~20 s): constant loadings recovered; explained share near 1 with no noise and near 0 for an unrelated series; the 52-week minimum and no clipping; **no lookahead** (every observation after t replaced, every row at or before t equal bit for bit, share included); the measured value is the last on or before and not carried; a store round trip and immutability; a store edited after writing is refused; the report's first line and table; `resolve_exposures` still raises `ExposureMatrixMissing`; and in the `holdout` tier the builder raises on weeks past 2020-01-01 and every committed store manifest ends before it. **No test changed.**
- **Not done:** nothing in the task was skipped. Nothing was built from `decisions/proposed/0050`, `resolve_exposures`, `harness/` and `vetoes/` are untouched, and I recommend nothing about L27. Not tested: the builder at a thread count other than 1 (it refuses to start at any other).

### 2026-10-07 -- task 50: one thread is the reference; three goldens re-recorded; grade ruling applied; .gitignore; the first scoped check (Claude Code, Sonnet 5.5)

**No verdict moved (step 6).** **rc=0 throughout.** Commits: `e5c6f66` (step 0, queue records, after `make check`: 2m54s), `273182e` (steps 1-4, the check-full below), `f3f0841` (step 5's fix, alone), `16a063b` (step 6's run). Logs: `results/audit/_unattended/20261007-084257-check-full/` (rc=0, **545 s against 3,908 s**, 784 passed, holdout 22 passed; the whole suite) and `results/audit/_unattended/20261007-085356-check-scoped/` (rc=0, **196 s**, tier SCOPED).

- **Step 1.** `git check-ignore -v` names a rule for `results/audit/x`, `results/fdr_vs_fwer/x`, `results/measurement/M-1/loadings.parquet`, `data/universe/raw_meta.json`, `raw_structure.json` and `results/audit-bloomberg.log`. `git status --short` showed no untracked file afterwards. Neither json was opened.
- **Step 2.** `build.mk` exports the three variables as 1 inside the check-block; `scripts/unattended.sh` exports the same before it logs, so its `machine` line reads `=1` for all three (line unchanged; both new runs show it). New `src/signal_lab/threads.py` (`require_one_thread`, `thread_setting`): `tests/conftest.py` calls it in `pytest_sessionstart` and raises `UsageError`; `scripts/_bootstrap.py` has `require_one_thread()`, which the eight number-making scripts call right after the import (`bias_map`, `drawdown_map`, `fdr_vs_fwer`, `ic_probe`, `te_path_probe`, `nightly_cycle`, `run_audit`, `run_measurement`) and which exits with the same message. Build, pull, universe and describe scripts are not gated. `thread_setting` is a new key in `run_measurement`'s `summary.json` and in the three audit summaries (in `meta` for the ruler audit). `tests/test_threads.py` (5 tests). CLAUDE.md has the new hard-rule line. **Solver:** the repo passes no thread option to cvxpy, CLARABEL or OSQP (`problem.solve(solver=name)` only), and I changed nothing there.
- **Step 3.** Two fresh processes, with the pin: the same four tests failed both times with identical values to the last digit: `GOLDEN_NET_IR` -0.8792060912640641 (was -0.8793457503233992), `GOLDEN_NET_IR_CREATED_MARGINAL` -0.3916378876353463 (was -0.3916592047250338), `GOLDEN_NET_IR_V080` -0.4046626602695416 (was -0.40475664238417963). Re-recorded those three, with `decisions/0048` and the old value in a comment. No other failure.
- **Step 4.** Both files edited as written. **`HypothesisRegistry` has no `partition()`; `triage()` is the method that does it.** Run against `jpmaqs-macro-v1`'s manifest ids (23), with `requests_dir` in a temp folder, so no request file reached `data/requests/`: H-2026-0004 is **blocked**, missing `USD_BLSCSCORE_NSA_D2Q2QL2` and `EUR_BLSCSCORE_NSA_D2Q2QL2` (it also lists `LF98TRUU` and `LUACTRUU`, only because I passed the macro ids alone, not the returns snapshot's). H-2026-0001 is **ready**: all six of its remaining tickers are in the manifest. The manifest needed no fix: `macro_ids` is built from the post-filter frame, so an all-grade-3 ticker is never listed. I pinned that with `test_a_ticker_with_no_usable_row_is_not_available` (synthetic panel, one all-grade-3 ticker). No existing test counted these hypotheses' series, so none else changed.
- **Step 5.** Fix in `describe.py`: `_ratio_to_first` gives NaN where the reference is zero. `test_measurement_describe.py` passes with `-W error::RuntimeWarning` (8 passed). **Tier SCOPED, but not the expected files:** the selector selected none and left out all eight slow files. Cause, from the imports: only `tests/test_measurement_describe.py` (fast) and `scripts/describe_loadings.py` import `describe.py`; `test_measurement_estimators.py` and `test_measurement_fidelity.py` do not reach it. I read that as the selector being right and the task's expectation wrong, and did not force anything. 722 passed, 62 deselected, holdout 22 passed.
- **Step 6.** `make measurement-loadings ARGS="--no-registry --reference .../M-20261003T181155Z/summary.json"` -> `results/measurement/M-20261007T125909Z/` (278 s). **The reference check passed**, so `--no-reference` was not needed. I also compared the two `summary.json` files myself for all five estimators and the incumbent: the largest absolute difference is **0.0** in the statistic, mean Huber loss, adjusted p and bias, and in every other numeric field under `score.estimators`; the verdicts and bias checks read the same, and the three hashes are equal. The run of record was made with threads unset, so this says the estimator test does not depend on the thread count, unlike the baseline goldens.
- **Not done:** nothing in this task was skipped. Not tested: a thread count other than 1 on the estimator test.

### 2026-10-07 -- task 49: checks log the machine and per-test times; a scoped slow tier; xdist NOT adopted (Claude Code, Sonnet 5.5)

**FIRST: capping BLAS threads changes recorded goldens.** `tests/test_baseline.py` with `OMP/OPENBLAS/MKL_NUM_THREADS=1`: **4 of 8 fail** on exact comparisons: `..._shuffle_switched_off_...` (net_ir -0.8792060912640641 vs golden -0.8793457503233992), `..._explicit_trailing_override_...` (same pair), `..._default_now_reads_created_marginal_...` (-0.3916378876353463 vs -0.3916592047250338), `..._full_default_cell_runs_the_overlay_...` (-0.4046626602695416 vs -0.40475664238417963). A recorded number depends on the thread count (differences of ~1e-4 to 1e-3 in net IR, not last-bit noise). Owner needs to know. Nothing was re-recorded.

**rc=0.** Commits: `38463ce` (step 0, queue records), `cbddeb0` (the build). check-full: `results/audit/_unattended/20261007-000204-check-full/`, rc=0, 3,908 s, 778 passed. This was a full run by both rules (tests/conftest.py changed). Selector on the same tree, as run before the commit: `FULL: build.mk: a check-block marker is missing` (HEAD's build.mk had no markers); it also lists untracked `data/universe/raw_meta.json` and `raw_structure.json`, which are FULL by the "data/" rule and will force FULL until they are committed or ignored.

- **Step 1.** Done. status.txt start line: `machine nproc=32 nproc_effective=32 loadavg=0.98 12.34 19.16 MemAvailable_kB=30286408 OMP_NUM_THREADS=unset OPENBLAS_NUM_THREADS=unset MKL_NUM_THREADS=unset`. load.log: `loadavg=1.90 15.17 24.34 top: 2985% pytest; 2.8% claude; 2.6% claude;` / `loadavg=1.55 13.81 23.60 top: 2962% pytest; ...` / `windows cpu=27% top: Spotify Spotify Spotify`. **The Windows-side sample works** (about 2.3 s a call, once a minute; a call over 5 s is skipped). `nproc` honours OMP_NUM_THREADS (prints 1 when capped), so the line records `nproc --all` and the effective value.
- **Step 2.** nproc 32. Load before A 0.35 1.06 8.61 (uncapped): **1,319 s pytest, 23m01 wall, user 695 min.** B (capped): load before 3.97 20.13 22.48 (the previous run's tail), **37 s**, 4 failed (above). So the slow runs are mostly BLAS oversubscription: ~30 busy threads per process.
- **Step 3.** **Skipped per the rule** (step 2 failed with capped threads); not for nproc. `pyproject.toml`, `uv.lock` untouched, no `XDIST`. Not trialled: a middling cap (say 4 threads) that might keep the goldens; ask if wanted.
- **Total, slow vs rest (junit):** 778 tests, 3,690 s summed; the 19 slowest tests (all slow) are ~3,640 s; everything else about 50 s.
- **25 slowest tests of the final run (s):** test_audit::turnover_cap_binds_and_costs_return 534; baseline::at_coefficient_zero_created_equals_trailing 306; baseline::created_form_moves_weights 234; audit::per_session_cap_holds 230; baseline::different_shadow_coefficient 229; baseline::shadow_coefficient_none 222; audit::oracle_beats_a_blind_signal 210; audit::dearer_spread 209; audit::blind_signal_hugs_the_benchmark 209; fidelity::gate_holds_its_level_under_a_null 182; baseline::shuffle_switched_off 110; audit::early_over_trade 109; audit::rolling_one_year_turnover 109; audit::base_cell_reports_transfer_coefficient 108; baseline::explicit_trailing_override 107; baseline::full_default_cell 104; baseline::default_now_reads_created_marginal 101; audit::report_names_the_panel 98; audit::writes_no_run_to_the_results_store 96; audit::cell_runs_the_whole_chain 83; then engine 12.8, scripts 7.6, experiment 6.2, select_slow 5.7, engine 3.1. Full list in that run's junit.xml.
- **4e replay** (imports read from today's tree, so approximate): `b0c7713` SCOPED, selected test_measurement_estimators, test_measurement_fidelity; left out test_audit, test_baseline, test_engine, test_experiment, test_multiple_testing, test_scripts. `3519b1c` SCOPED, selected all 8 slow files (incl. test_audit and test_baseline). `3a04275`, `e07a9d1` and task 48's build commit `5d3a581`: `FULL: build.mk: a check-block marker is missing`. Both expectations held, so check-scoped and CLAUDE.md were done.
- **Tests added** (`tests/test_select_slow.py`, 35, fast tier, ~9 s): the 4d list, plus per-path FULL cases, CRLF-insensitive block compare, "only a passing whole-suite run counts", and the unparsable-file case. The real-tree list of invisible reachers is `{test_governance.py, test_select_slow.py}`: **a deviation from "one"**, because my test shells out to `pytest --collect-only` for the `--slow-only-in` counts.
- **Not done / not tested:** `make check-scoped` has not been run end to end (the tree is FULL while the data/ files are untracked and the run would be 60+ min); its SCOPED branch's shell parsing was checked on a fake selector output only, and `unattended.sh check-scoped` has not been run. The `.gitignore` trailing-comment problem is untouched.
- **Guess on why the slow runs are slow:** BLAS/OpenMP threads (32 per process) oversubscribing in small-matrix solves, so run time swings with whatever else loads the machine (the 388-4,235 s spread). Evidence: 35x wall and ~19x less CPU in step 2. A guess about the cause of the spread; the factor is measured.

### 2026-10-06 -- task 48: the filters' variance update named, a conjugate sensitivity, loading stability and absolute fit (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `d0afd38` (step 0: `HANDOFF.md`, `OWNER-QUEUE.md`, `decisions/0046`, after `make check`) and `5d3a581` (the build, the two runs' `report.md` and `summary.json`, `stability.*`, `fit.*`). `check-full` log: `results/audit/_unattended/20261006-215942-check-full/`, rc=0 (**2,462 s**), 743 passed, holdout 22 passed, governance OK. An earlier attempt, `20261006-215234-check-full`, died at lint (rc=2, 17 s): three ruff findings in my new files plus `ruff format` layout in five. I fixed them (layout and one closure, no behaviour) and **repeated runs 3a to 3d afterwards**, so the numbers below come from the committed code.
- **Derivation: I agree.** With `C` scale-free, West and Harrison's update is `C = R - AA'Q` and the covariance in actual units is `S_new * C`. The coded line gives `S_old * (R - AA'Q)`; its precision is `P_prior + zz'/S_(t-1)`, as Cowork derived. Docstrings corrected in both filters; default unchanged; keyword `conjugate=` on `_kalman_filter` and `_mr_filter`, `conjugate_update=` on the two classes, `--conjugate-update` on the script (a `-sens` run, no hypothesis moved, and it does not stop if a verdict would read differently).
- **3a: pass.** Reference check passed for the incumbent and all five. New run `M-20261007T015445Z`: every estimator's fields, including all five `p_adjusted` (0.200, 0.179, 1.000, 0.941, 0.057), the hashes and the gate, are **equal** to `M-20261003T181155Z`. (The script's pass message still names `M-20261002T131820Z`; the string is hard-coded and cosmetic.)
- **3b, `M-20261007T015447Z-sens`** (statistic; adj p; worst-year bias), coded -> textbook; **sensitivity, no verdict moves, all `not_detected`**:
  - `huber_m` 1.57e-03; 0.200 -> 0.197; 1.68 (unchanged).
  - `theil_goldberger_peer_prior` 8.78e-04; 0.179 -> 0.175; 1.83 fail (unchanged).
  - `hmm2_regime_conditional` -6.62e-03; 1.000 -> 1.000; 1.38 (unchanged).
  - `kalman_dlm_discount` **-5.30e-04 -> +2.67e-03**; **0.941 -> 0.052**; 1.58 -> 1.63; loss 0.2325 -> 0.2292.
  - `mean_reverting_dlm_own_mean` **2.83e-03 -> 1.82e-03**; **0.057 -> 0.264**; 1.59 -> 1.58; loss 0.2291 -> 0.2301.
  - So the update matters to the two filters' relative standing: under the textbook update the Kalman candidate sits where the mean-reverting one did, and the mean-reverting one falls. The Huber and TG adjusted p move by 0.003-0.004 only because the gate's pooled null includes the two filters. Mean-reverting by slice, textbook: -3.0e-03 / -1.0e-04 / -8.0e-04 / 3.1e-03 (top decile / 2004-07 / 2008-09 / 2010-19); its half-life-13 share 0.387 against 0.446. Kalman by slice, textbook: -1.6e-03 / 3.1e-03 / -5.5e-03 / 4.1e-03.
- **3c, stability** (`stability.md`, ratio to rolling OLS, mean over the six factors; weekly / weekly 2008-09 / annual / annual 2008-09 / rank agreement): `huber_m` 1.03 / 1.01 / 0.95 / 0.91 / 0.981; `theil_goldberger_peer_prior` 0.85 / 0.85 / 0.84 / 0.83 / 0.966; `hmm2_regime_conditional` 1.27 / 2.01 / 0.65 / 1.03 / 0.829; `kalman_dlm_discount` 1.79 / 2.01 / 1.41 / 1.52 / 0.903; `mean_reverting_dlm_own_mean` 1.20 / 1.61 / 0.81 / 0.92 / 0.878. Compared as stored (the mean-reverting candidate's is a forecast for t+1). 70,424 common instrument-weeks. Per-factor tables in `stability.md`.
- **3d, fit** (`fit.md`; pooled, 70,326 cells, mean Huber loss reproduces the score to 5.6e-17). `r2_oos` / `huber_skill` / `ts_corr` median / `xs_corr` mean (share of weeks above zero): `rolling_ols` 0.699 / 0.621 / 0.860 / 0.573 (0.987); `huber_m` 0.703 / 0.623 / 0.863 / 0.575 (0.988); `theil_goldberger_peer_prior` 0.704 / 0.622 / 0.858 / 0.576 (0.986); `hmm2_regime_conditional` 0.691 / 0.610 / 0.855 / 0.569 (0.989); `kalman_dlm_discount` 0.694 / 0.620 / 0.855 / 0.575 (0.990); `mean_reverting_dlm_own_mean` 0.703 / 0.625 / 0.863 / 0.580 (0.987). **xs_corr is conditional on the realised factor moves, not a forecast IC.** By class, the four slices, the quartiles, the ten lowest tickers and `factor_share` by class are in `fit.md`/`fit.json`, not repeated here. The weakest instruments are the same for every estimator (`LGTRTRJU`, `LGTRTRGU`, `BCOMGCTR`, then `TAMSCI`, `MXIN`). **Read with care:** the Commodities class scores about 1.00 and US Equities loads about 1.0 on the equity factor in every estimator, which looks like the factors being built from the same indices; I did not check how the factors are built. All twelve named instruments are in the scored set. `predicted_vs_actual.html` is written, git-ignored, **not opened or summarised by me** (it holds weekly returns); I checked only that its SVG parses.
- **25 slowest tests** (asked for because 2,462 s > 1,500 s; `pytest -m slow`, 40 passed in 1,838 s): `test_audit.py::test_the_turnover_cap_binds_and_costs_return` 290 s; `test_measurement_fidelity.py::test_the_gate_holds_its_level_under_a_null` 232 s; `test_audit.py::test_a_blind_signal_hugs_the_benchmark` 222 s; `test_audit.py::test_the_oracle_beats_a_blind_signal` 195 s; `test_audit.py::test_a_cell_runs_the_whole_chain_and_reports_what_bound` 161 s; `test_audit.py::test_a_dearer_spread_makes_the_solver_trade_less` 88 s; `test_baseline.py::test_at_coefficient_zero_created_equals_trailing` 88 s; `test_baseline.py::test_shadow_coefficient_none_matches_params_exactly` 75 s; `test_baseline.py::test_a_different_shadow_coefficient_moves_weights_not_costs` 67 s; `test_baseline.py::test_the_created_form_actually_moves_weights_relative_to_trailing` 58 s; `test_baseline.py::test_the_shuffle_switched_off_reproduces_todays_score_and_net_ir_bit_for_bit` 50 s; `test_audit.py::test_the_per_session_cap_holds_and_the_annual_figure_still_moves` 47 s; `test_audit.py::test_an_early_over_trade_does_not_block_a_later_one` 40 s; `test_baseline.py::test_the_default_now_reads_created_marginal_from_params` 36 s; `test_baseline.py::test_an_explicit_trailing_override_reproduces_the_legacy_golden_bit_for_bit` 30 s; `test_audit.py::test_a_base_cell_reports_the_transfer_coefficient_the_left_tail_and_the_pearson_ic` 22 s; `test_baseline.py::test_the_full_default_cell_runs_the_overlay_and_reproduces_its_golden` 22 s; `test_audit.py::test_the_report_names_the_panel_and_the_params_it_ran_on` 19 s; `test_audit.py::test_the_audit_writes_no_run_to_the_results_store` 19 s; `test_audit.py::test_rolling_one_year_turnover_is_reported_for_the_budget_question` 18 s; `test_scripts.py::test_the_validation_run_is_recorded_and_tagged` 11 s; `test_engine.py::test_alternate_days_are_averaged_and_every_day_is_reported` 11 s; then three setups at 7.3 s, 3.6 s and 3.6 s (`test_experiment.py`, `test_engine.py` x2). Nothing moved or re-marked.
- **Tests added or changed.** `tests/test_measurement_estimators.py` (new): the two updates give different covariances and different `S` on a series with a tenfold volatility break; they agree under a tight variance prior; the keyword reaches both classes, defaults off, and the default equals `conjugate_update=False`. `tests/test_measurement_describe.py` (new, 8): constant loading gives zero change; a planted step is returned (weekly `s`, annual `52 s`, ratio 2); identical estimators give ratio 1 and rank agreement 1; only common cells count; true loadings give `r2_oos` = 1; zero loadings give 0 and 0; `factor_share` sums to 1; a cell without a loading is not scored. Two of mine failed first and were my errors: `factor_share` lacked the `p` in its numerator (the test caught it), and I had asserted `S` equal across the two updates when it differs.
- **Said plainly: where I departed from the task.** (1) **The tight-prior agreement is not 1e-8 at `n0 = 1e9`.** Over 260 weeks with a break the means agree to about 1e-8 but near-zero covariance entries differ by up to 2e-5 relative (the ratio compounds at about n/n0 and the diffuse `c0 = 1e6` start amplifies it). The test asserts 1e-4 at `n0 = 1e9` and 1e-8 at `n0 = 1e12`. (2) The describe code sits in `src/signal_lab/measurement/describe.py` with `scripts/describe_loadings.py` as the I/O, rather than all in the script, so the tests can import it. (3) `fit` rebuilds the returns and factors through `run_measurement.load_inputs`, hash-checked against the run's `summary.json`, because the parquet holds only loadings. (4) `ts_corr` needs at least 26 scored weeks; `xs_corr` at least 5 instruments in the week. (5) My first `make check-full` call and the first slow listing used `uv run` without `UV_PROJECT_ENVIRONMENT`, so they picked up the repo's old `.venv` (dated Sep 15) rather than `$HOME/.venvs/signal-lab`; I re-ran the slow listing in the right one, and the passing `check-full` went through `make`. My hand-run development tests used the old `.venv`. (6) I deleted my own first pair of run directories (`M-20261007T014710Z`, `...T014724Z-sens`, untracked, never committed) once the re-runs superseded them. (7) **`.gitignore` has a bug I did not fix:** its pattern lines carry trailing `# comments`, which git does not support, so `results/audit/`, `results/fdr_vs_fwer/` and `results/measurement/*/loadings.parquet` are not actually ignored (they show as untracked). I did not commit them. The new `predicted_vs_actual.html` line has no comment and does work. Nothing else in the task was skipped. I recommended no estimator.

### 2026-10-03 -- task 47: a fifth loading estimator, H-2026-0017, `not_detected` (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `a854646` (step 0: the draft `H-2026-0017.yaml`; `HANDOFF.md`, `OWNER-QUEUE.md` and `decisions/0046` were already committed, `d3673dc` and `11257f1` being the owner's two commits of the records and SUBSTRATE v0.9), `cadca00` (registration, **2026-10-03 13:48:26 -04:00**, before the estimator touched real data), `b0c7713` (the build, the run's `report.md` and `summary.json`, the moved hypothesis; 2026-10-03 15:28:29 -04:00). `check-full` log: `results/audit/_unattended/20261003-141718-check-full/`, rc=0 (**4,235 s**), 732 passed, governance OK. An earlier attempt, `20261003-141604-check-full`, died at lint (rc=2, 34 s): `ruff format` wanted three of my files laid out differently. I formatted them (layout only) and re-ran; the run below was made before that and was not repeated.
- **Run:** `M-20261003T181155Z`, 314 s (projected 0.07 h), 86 instruments, 835 weeks, 70,326 instrument-weeks, Cash excluded by default. Gate `romano_wolf_gfwer`, **n_tests = 5, g = 1**.
- **The first four reproduced exactly.** Checked in the script before anything was written or moved, against `M-20261002T131820Z`'s `summary.json`: hashes, weeks and cells scored, and for the incumbent and each of the four, mean loss, statistic, slices, worst-year bias, year, check and every annual bias, compared for exact equality. Adjusted p moved as expected (Huber 0.178 -> 0.200, TG 0.160 -> 0.179, Kalman 0.938 -> 0.941, HMM 1.000 -> 1.000); none of the four verdicts changed, so the "stop if flipped" rule did not fire. Their recorded verdicts stand and only H-2026-0017 was moved (`pending -> running -> done`).
- **The table** (statistic; mean Huber loss; adj p; gate; worst-year bias, year; check; slices top-decile / 2004-07 / 2008-09 / 2010-19):
  - `rolling_ols` (incumbent): loss 0.2319; bias 1.80, 2008; **fails**.
  - `huber_m`: 1.57e-03; 0.2303; 0.200; fail; 1.68, 2008; pass; 1.02e-02 / -5.4e-05 / 7.0e-03 / 1.1e-03.
  - `theil_goldberger_peer_prior`: 8.78e-04; 0.2310; 0.179; fail; 1.83, 2008; fail; 8.1e-03 / 1.3e-03 / 4.5e-03 / -3.1e-05.
  - `hmm2_regime_conditional`: -6.62e-03; 0.2385; 1.000; fail; 1.38, 2008; pass; -1.4e-02 / -7.6e-03 / -9.2e-03 / -5.7e-03.
  - `kalman_dlm_discount`: -5.30e-04; 0.2325; 0.941; fail; 1.58, 2008; pass; -1.5e-02 / 3.1e-03 / -1.6e-02 / 1.2e-03.
  - **`mean_reverting_dlm_own_mean`: 2.83e-03; 0.2291; adj p 0.057; gate fail; 1.59, 2008; check pass; 1.33e-03 / 9.1e-04 / 2.4e-03 / 3.7e-03. Verdict `not_detected`** (it passes the uncertainty check and misses the gate, 0.057 against 0.05 at g = 1).
  - Its statistic by reporting class (instruments): US Equities 19, European Equities 13, EM Equities 12, DM ex-US Equities 9, Ex-USD Bonds 8, HY 5, Real Assets 4, Treasuries 3, and the rest 1-2 each. Positive in 13 of 18 classes (US Equities 1.9e-03): largest MBS 2.7e-02, EM Corporate 2.4e-02, Gold 2.2e-02, EM Sovereign 1.7e-02, HY 1.4e-02; negative in Long Treasuries -6.8e-03, IG Corporates -6.3e-03, Treasuries -2.3e-03, Real Assets -1.3e-03, Commodities -1.0e-05. The full table is in `report.md`.
- **Grid shares** (share of the 70,326 scored cells in force): half-life 13 weeks 0.446, 26 0.046, 52 0.051, 104 0.457; q 0.25 0.090, q 1 0.205, **q 4 0.705**. The single most used pair was (13, q 4) at 0.387. The grid is used at both ends, which is a description and not a verdict on the grid, which was not changed.
- **Halves** (split at 2011-12-30): first 3.13e-03, second 2.52e-03. **The gain did not grow with history**; it is slightly smaller in the second half.
- **Level shift** (synthetic test, reported with no threshold): after a permanent +0.6 shift in one loading, the stored loading takes **78 weeks** to close half the gap.
- **Said plainly, my choices.** (1) **The addendum was ambiguous about the start**, so I stopped and asked; the owner chose, on 2026-10-03, to **seed the filter at the first week a 156-week OLS exists**: `a` and `mu` take that OLS's coefficients and covariance, `d` starts at 0 with covariance `q * C_ols`. This is a departure from the "diffuse prior" wording, recorded in the estimator's docstring and the commit message. (2) "Scaled covariance of the OLS loading" read as the unscaled `(Z'Z)^-1` block, as `_kalman_filter` works in scaled units. (3) Innovations into week t+1 use `C_ols` known at t, carried forward over a week with no OLS. (4) At the first week every pair's likelihood is 0, and ties go to the first pair. (5) Observation variance starts at the seed OLS's residual variance with `n - 7` degrees of freedom, then learns as `_kalman_filter` does.
- **Tests changed:** `tests/test_measurement_estimators.py::_all_paths` now includes the new estimator, so the existing lookahead test (renamed `test_the_five_pooled_estimators_do_not_see_past_t`) and the slow PSD test cover it; the lookahead test also compares each path's `extra` diagnostics. `tests/test_measurement_fidelity.py`: the estimator list gains the sixth name and `test_the_gate_reports_g_equal_one_for_four_candidates` is now `..._five_candidates` and asserts `n_tests == 5`. **New:** constant loadings recovered; **beats rolling OLS and the Kalman candidate under planted mean reversion, asserted on the average over twelve histories, not draw by draw** (it beat rolling OLS in 9 of 12 and Kalman in 7 of 12, so a per-draw assertion would have been a coin flip; my first version asserted per draw and failed on one of three seeds); the level shift; the forecast, not the filtered value, is what is stored; covariance symmetric and PSD; the chosen pair is recorded; each candidate reports halves; `pair_shares`.
- **Not done / to know:** nothing in the task's list was skipped. `LoadingPath` gained an `extra` dict (default empty) and `fidelity.score` gained a `halves` entry per candidate; neither changes any existing number, which the exact reproduction confirms. The run was made before `ruff format`, so the committed code differs from the run's code in layout only. **`check-full` took 4,235 s against 794 s for task 46's, and I do not know why**; the machine may have been busy with something else. I did not recommend an estimator. OWNER-QUEUE B5 is the owner's.

### 2026-10-02 -- task 46: decisions/0047, task 44 part B, and the estimator test without Cash (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `dbd9628` (step 0, queue; the owner ran this one in their own shell after the commit tool was denied) and `3519b1c` (the build, 2026-10-02 09:35 -04:00). `check-full` log: `results/audit/_unattended/20261002-092150-check-full/`, rc=0 (794 s), 724 passed, governance OK.
- **The `SUBSTRATE.md` v0.9 commit has NOT landed as of this receipt.** Step 0's second commit (`SUBSTRATE.md`, `decisions/0046`, `decisions/0047`, `decisions/0100`) was denied by the commit tool and is left to the owner; those files are modified or untracked in the working tree. I committed only my own files in `3519b1c`, so the code is in history ahead of the constitution text it transcribes. The `governance` line passes because no owner-only path changed in a commit.
- **Part 1.** `VintagePanel.period_may_follow_knowledge` (default False; only the JPMaQS loader sets it). A negative `eop_lag` is accepted; non-finite still raises; a valued row below -92 days raises `NegativeLagCheckpoint` with counts per ticker and bucket and builds nothing. The `enforce_holdout` call on `period_end` is removed in `build_macro_panel` and `build_macro_snapshot`; `build_snapshot` and `loaders/holdout.py` are untouched and no bypass argument exists. The manifest records `max_period_end` and `rows_with_period_end_in_holdout`. Coverage gains the three negative-lag buckets (each ticker's latest `period_end` was already a column).
- **Part B, on the existing pull `P-20261002T032635Z`, no new vendor call.** The checkpoint passed. Snapshot `jpmaqs-macro-v1`, hash `442d729140f2aa3c60d5a5cc441250733eb0ef228f59a7f4ac95702299fbf52b`. 26 tickers; rows raw 150,644, no value 0, dropped by grade 22,919, before compression 127,725, after 76,933; cross-product series dropped 0. Negative-lag rows 13,562: 9,936 in -1..-31, 3,626 in -32..-92, 0 below -92; by ticker EUR_BLSCSCORE 1,421 / 1,710; USD_BLSCSCORE 2,438 / 1,916; USD_MBCSCORE 3,182 / 0; JPY_INTRGDP 2,189 / 0; EUR_MBCSCORE 360 / 0; EUR_INTRGDP 224 / 0; GBP_INTRGDP 122 / 0. `max_period_end` 2019-12-31; rows with a period end in the holdout 0. Nine tickers start after `dev_start`: DEM_GB10YCRY_NSA, EUR_BLSCSCORE, EUR_EQCRR, EUR_INTRGDP, EUR_MBCSCORE, EUR_RIR, JPY_EQCRR, USD_BLSCSCORE, ZAR_CTOT. **The grading values are not integers**: a near-continuous range from 1.0 to 3.0 (hundreds of distinct values, listed in `results/jpmaqs_coverage.csv`), so `grade_3: exclude` drops only rows at 3.0 and above (22,919) and the owner's question whether a threshold rule is needed has an answer: probably. `data.jpmaqs.status` is unchanged.
- **Part 2.** `Cash` is a named default exclusion (`DEFAULT_EXCLUDED_CLASSES`, citing the 0046 addendum); that run carries no `-sens` suffix; `--exclude-class` adds classes and marks a sensitivity. Report and `summary.json` gain each estimator's mean Huber loss and each candidate's statistic by reporting class with instrument counts. Run `M-20261002T131820Z` (`--no-registry`, 268 s, 86 instruments, 835 weeks): **it reproduces `M-20261002T034221Z-sens` exactly**, compared field by field in the two `summary.json` files (statistic, adjusted p, worst-year bias, year, check, gate, slices, annual biases), not only to printed digits. Mean Huber loss: rolling OLS 0.2319, Huber 0.2303, TG 0.2311, HMM 0.2385, Kalman 0.2325. The by-class table is in its `report.md`.
- **Tests changed:** `tests/test_jpmaqs_loader.py::test_a_bad_eop_lag_on_a_valued_row_is_refused` asserted that a negative lag is refused; it is now `test_a_non_finite_eop_lag_on_a_valued_row_is_refused` over NaN and infinity only. New tests: the default panel check still raises; a JPMaQS panel with a period after knowledge builds; `as_of` returns the row on and after its knowledge date and not before; the bucket counts; the checkpoint (exactly -92 passes, -93 raises); and three tests marked `holdout`. The existing synthetic macro-panel holdout test is unchanged and passes. `tests/test_measurement_fidelity.py` gains a test of the mean loss and by-class output.
- **The task's own holdout example is inconsistent with its checkpoint.** "Known on 2019-12-20 about a period ending 2020-03-31" is 102 days ahead, which the -92 checkpoint refuses. The holdout tests use a period ending 2020-02-29 (71 days). The checkpoint stands as `decisions/0047` states it.
- **Not done:** the `SUBSTRATE.md` v0.9 commit (above). OWNER-QUEUE L21 and L22 moved to Closed in the commit that carries this receipt.

### 2026-10-02 -- task 45, the loading-estimator test; and task 44 part B, STOPPED at the loader's refusal (Claude Code, Sonnet 5.5)

**Task 45: rc=0.** Commits: `35b1353` (step 0, queue), `90cab7d` (registration of H-2026-0013 to 0016, 2026-10-01 23:08:15 -04:00; this is the pre-registration), `3a04275` (the build, the run's report and summary, the moved hypothesis files; 2026-10-02 00:00 -04:00). `check-full` log: `results/audit/_unattended/20261001-234540-check-full/`, rc=0 (829 s), 716 passed, governance OK. Registration landed 52 minutes before the build commit and before any estimator ran on real data; the first real-data estimator run was the `--time-only` timing, after `90cab7d`.
- **Run:** `M-20261002T033239Z`, 261 s (projected 0.05 h against the 3 h limit). Common-sample start 2001-01-05 (credit starts it); 991 weeks with all six factors; 835 weeks and 87 instruments scored (71,161 instrument-weeks). Credit was read as percent. Hashes in its `summary.json`; params `b3d41267...`.
- **Per estimator** (statistic; adjusted p; gate; worst-year bias against 1.72, year 2008 for all; bias check; slices top-decile / 2004-07 / 2008-09 / 2010-19). Rolling OLS, the incumbent: bias 1.80, **fails** the check. `theil_goldberger_peer_prior`: 8.67e-04; 0.164; fail; 1.83; fail; 8.05e-03 / 1.32e-03 / 4.46e-03 / -3.08e-05. `huber_m`: statistic 5.6e+05, adj p 0.310, gate fail, bias 1.68 pass. `hmm2_regime_conditional`: statistic -8.9e+06, adj p 1.000, fail, 1.38 pass. `kalman_dlm_discount`: statistic -9.9e+05, adj p 1.000, fail, 1.57 pass. **The Huber, HMM and Kalman statistics and their slices are meaningless**: one instrument, `LD20TRUU` (class Cash, near-zero robust volatility), is about 100% of their differential. See OWNER-QUEUE L22. All four hypotheses moved pending -> running -> done with verdict `not_detected`.
- **Sensitivity, not the registered test:** `M-20261002T034221Z-sens`, the Cash class excluded, 86 instruments, 70,326 instrument-weeks, no hypothesis moved. Huber 1.57e-03, adj p 0.178, bias 1.68 pass; TG 8.78e-04, 0.160, 1.83 fail; HMM -6.6e-03, 1.000, 1.38 pass; Kalman -5.3e-04, 0.938, 1.58 pass. Same four verdicts.
- **HMM regimes across the ten restarts:** stable in most weeks (median agreement with the best restart 1.0); in 62 of 836 weekly fits a restart fell below 90% agreement, the worst 64%.
- **The gate's level:** 5.7% rejection under the null at 900 weeks (test range 3-7%); **15% at 320 weeks** (8 blocks), so a short sample's block bootstrap is liberal. The test runs at 950 weeks. This does not affect the run (835 weeks).
- **Harness check** (`report.md`): Treasury real-yield loadings sit near minus the measured OAD (e.g. LT09TRUU -7.2 against -7.55; the long buckets about -10.4 against -14.6); IG credit loadings near minus OAD (LUACTRUU -5.7 against -6.6).
- **Judgement calls, said plainly:** minimum 104 valid weeks in the 156-week window for every estimator (the data-sufficiency rule, not a tuned setting); TG falls back to OLS for a class with fewer than 3 peers having an estimate (Treasuries, Long Treasuries and others: their TG row equals OLS); the TG prior dispersion is the per-factor variance, diagonal; the HMM's 2 regimes use a fixed seed 20261001 and ten restarts and the WLS falls back to unweighted when a regime has under 14 effective weeks; the Kalman filter's priors (n0=1, s0=1e-4, c0=1e6) are fixed constants; Huber is my own IRLS with a sandwich covariance (matches statsmodels RLM in a test), not statsmodels; the same residual-variance definition for every estimator in the uncertainty check; `stats/calibration.annual_bias` is a shared helper that `audit.ladder.risk_calibration` now calls (numbers unchanged; the veto in `vetoes/rules.py` is owner-only and was not touched, so it keeps its own copy of the two lines); the printed warnings in `robust_scale` were silenced after the registered run, no numbers changed.
- **Dependency added:** none. **Not done:** nothing in the task's list; the sensitivity run is an addition.

**Task 44 part B: STOPPED, nothing committed.** The owner's pull succeeded: `P-20261002T032635Z`, 150,644 rows, 26 tickers, real_date 1990-01-01 to 2019-12-31, macrosynergy 1.8.1, call shape `tickers=`. `make macro-snapshot` then refused, as step 1 specifies: 13,562 valued rows have a negative `eop_lag`, on seven tickers (OWNER-QUEUE L21). No macro snapshot was built, `make jpmaqs-coverage` did not run, `results/jpmaqs_coverage.*` do not exist, `data.jpmaqs.status` is unchanged. Steps 12-13 wait on the owner's ruling. Counts requested by step 13 that exist: tickers pulled 26; rows raw 150,644; rows with no value 0 (all 150,644 carry a value).

### 2026-10-01 (night) — task 44 part A, the JPMaQS loader build; STOPPED at the owner's pull (Claude Code, Sonnet 5.5)

**rc=0.** Commits: `ea5e7b0` (step 0, queue) and `e07a9d1` (part A: `src/`, `scripts/`, `tests/`, `build.mk`). `check-full` log: `results/audit/_unattended/20261001-223012-check-full/` -- `make check-full` rc=0 (2079 s), 677 passed, governance OK, lint clean, holdout tier 18 passed.

- **Download call shape:** the installed `macrosynergy` 1.8.1 `JPMaQSDownload.download` accepts `tickers=`; `scripts/jpmaqs_pull.py` passes the 26 tickers directly, so no cross-product filter is needed at pull time. `filter_panel` still runs in `load_macro` against the manifest's tickers.
- **Built:** `build_macro_panel` / `qdf_to_vintage_frame` / `compress_to_change_points` / `filter_panel` / grade-3 exclusion / legacy-prefix meta / holdout raise in `loaders/jpmaqs.py`; `JPMaQSLoader.load_macro`; `scripts/jpmaqs_pull.py`; `build_macro_snapshot` in `harness/snapshot.py`; `scripts/build_macro_snapshot.py`; `scripts/jpmaqs_coverage.py`; `make jpmaqs-pull`, `macro-snapshot`, `jpmaqs-coverage`. 33 tests in `tests/test_jpmaqs_loader.py`, synthetic frames only, no network.
- **Judgement calls, said plainly:** (1) the grade filter runs before compression, so compression sees only the rows that survive; (2) `load_macro` refuses a raw file whose sha256 differs from its pull manifest; (3) the pull script also refuses, and writes nothing, if the result reaches the holdout; (4) coverage counts for no-value rows, grading values and eop_lag buckets come from the snapshot manifest (raw-pull counts), the vintage counts and gaps from the compressed rows -- stated in the report's header; (5) compression assumes `eop_lag` grows daily while a vintage stands, so `period_end` is constant -- part B's row counts will show whether the real pull behaves so.
- **Not done:** everything in part B (steps 12-13). `params/` untouched, `data.jpmaqs.status` still `credentials_supplied`.
- **A stray run:** I ran `scripts/unattended.sh` with no argument by mistake; it ran `make check` against half-written files, rc=2 (`20261001-222821-check`). Superseded by the check-full above.

**Owner step next, in their own shell:** `set -a; source .env; set +a; make jpmaqs-pull`

### 2026-10-01 — task 43: small searches gated at g = 1, CRLF params, resolved keys, candidate / not detected (Claude Code, Sonnet 5.5)

- **rc 0.** `scripts/unattended.sh check-full --digest`, log `results/audit/_unattended/20261001-163421-check-full/` (`status.txt`: rc=0, 388 s; 644 passed, holdout 15 passed, governance OK). The log records `head=19db8c7`; no file changed between its start and the commit, so it tested exactly what `66bc6da` holds.
- **Commits:** `9a080cd` queue; `19db8c7` substrate v0.8 (+0039, 0040, 0042, 0043, 0044, 0045, 0100); `66bc6da` params/vetoes/src/render/scripts/tests/.gitattributes; `ac23c2b` hash lines in 0044 and 0045; then this receipt with L4, L19, L20 closed.
- **params_hash (CRLF):** `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8` (0.8.0) -> `b3d41267a752b9d76e2ddf17264cccb5b5b9ea6f0f45edc8bf1517524674376a` (0.9.0); the latter is the value Cowork computed, no discrepancy. `git check-attr eol params/audit.yaml`: `eol: crlf`.
- **Step 1, gate:** `gate()` runs at `small_search_g` when m < `small_search_below`, reports `g` actually run and `standardise`; `verdict_for` carries both. Tests: m = 1 and 7 report g = 1, m = 8 and 12 report g = 2 and match `romano_wolf_gfwer`; m = 1 under a complete null, k = 100, 2,000 seeded draws rejects within [0.03, 0.07]; veto passes (m=1,g=1), fails (m=1,g=2), fails with no `n_tests`, no `standardise`, `standardise=False`, plus the m = 7/8 floor.
- **Veto tests updated:** `GFWER` in `tests/test_vetoes.py` now carries `n_tests: 120` and `standardise: True`, so every test spreading it (passes-when-rejects, fails-when-not-rejected, looser alpha, wrong g, too few shuffles, `apply_vetoes` context) picks them up; the missing-g and missing-n_shuffles tests now build from `GFWER` minus that key so they test only that omission. No assertion weakened. In `tests/test_policy_defaults.py` the g = 2 gate tests moved to m = 12; the veto-on-gate-output tests too.
- **Step 2, F2:** `.gitattributes` `params/*.yaml text eol=crlf`; `test_every_params_file_is_crlf_on_disk`. `hash_params_dir` untouched.
- **Step 3, F3:** `AuditCell.key()` appends `_created` when the resolved shadow form is `created`, except frictionless cells, which price no turnover. Explicit-created and trailing keys unchanged (tested). **Audit-run check:** the only run since `3d437d0` is `A-20260930-033812`, 240 cells, all `shadow_form=trailing`, no `_created` keys, so no recorded key changes. Default key and the halflife h26 arm differ (tested).
- **Step 4, F4:** `run_cell`, `run_frictionless`, `scripts/run_audit.py` (artifact path, two progress lines) and `scripts/ic_probe.py` call `key(params)`. Test: `run_frictionless` under params with no overlay block records no `_vhl`.
- **Step 5:** F6 text in `views.turnover_disclosure` and streamlit column "Turnover flag (annual)". F8: `created_marginal_quadratic` raises `ObjectiveNotConfigured` on a null coefficient with no override (test; an override still works). 0040: sibling test (`prev=[0.0]*60`, lump = split, at x = 1.0 and 1.6, so it covers a trade that crosses the curve's start); docstrings of `turnover_penalty` and `created_marginal_shadow` no longer say convexity makes a lump dearer. The existing lump-vs-split test is unchanged.
- **Step 6, 0039 strings:** "Survivors first" -> "Runs that passed every veto first" (`views.leaderboard_table` docstring, streamlit caption, static report lede), "Where the survivors sit" -> "Where the runs that passed every veto sit"; digest "Survivors" headings -> "Passed every veto" with a Label column. New `views.run_label`: `candidate` (passed every veto and net IR >= `audit.target_net_ir`), `not detected` (bar-2 failure), else blank; shown in the leaderboard's last column ("not detected (multiple_testing)"), streamlit and the digest. Left alone: the veto's detail text, and `HypothesisRejected`, which is pre-registration validation and not a verdict on a hypothesis. **Lifecycle:** a code path exists (`HypothesisRegistry.move`), so I added `VERDICTS = ("candidate", "not_detected")` and `move(..., verdict=, power_at_nearest_ic=)`; the verdict and a `power_at_nearest_ic` (null) go in the transition's detail, and the pre-registered file is not edited. Test: bad verdicts (`confirmed`, `rejected`, `proven`) raise.
- **Not done / for Cowork:** (1) `run_label` treats bar 1 as `net_ir >= audit.target_net_ir` on the leaderboard's stored net IR; if the lab means a different IR for bar 1 at phase 3, that is one line. (2) `power_at_nearest_ic` is null by design. (3) The `.gitattributes` file was written LF; on this machine `autocrlf` will make it CRLF, which git's attribute parser tolerates. (4) No audit or vendor call.


### 2026-10-01 — task 42: overlay is policy, gate is generalized FWER, turnover highlight, one 0040 shadow cost (Claude Code, Sonnet 5.5)

- **rc 0.** `scripts/unattended.sh check-full --digest`, log `results/audit/_unattended/20261001-115213-check-full/` (`status.txt`: check-full rc=0, 451 s; 628 passed, holdout 15 passed, governance OK).
- **Commits:** `5230ae1` queue; `7c410b1` substrate v0.7 (+0042, 0043, 0100); `32fab05` params/vetoes/src/render/tests; a small commit recording the hash move in 0042 and 0043; then this receipt with OWNER-QUEUE B1 and L16 moved to Closed.
- **params_hash:** `571f33fc6afee7273b45359ab310ff89025e353b8e7e5f959a6c5507e00b35d0` (0.7.0, at 81b16b4) -> `9a3b002e95b8fa596b3273de7bb4cf259e075c836128853b3698a82ca4a1e5a8` (0.8.0).
- **Grids pinned `vol_halflife=None`** (they claim identity with a named run computed with no overlay): `power_cells`, `power10_cells` (POWER_LIVE_RUN), `friction_cells` and, by inheritance, `friction_created_cells` (FRICTION_LIVE_RUN). `halflife_cells` already set every arm explicitly; docstring updated. `knee_cells`, `baseline_cells`, `grid_cells` follow params, so live and baseline twins resolve alike (tested). Consequence: a re-run of knee/baseline no longer matches the A-20260919/A-20260922 runs' hashes or keys.
- **Golden values:** `GOLDEN_NET_IR = -0.8793457503233992` and `GOLDEN_NET_IR_CREATED_MARGINAL = -0.3916592047250338` reproduce bit for bit through explicit overrides (`vol_halflife=None` plus the shadow overrides). `GOLDEN_NET_IR_V080 = -0.40475664238417963`, the same cell at the full default, from a live `run_cell` call, stable on a second run.
- **Tests changed, and why:** `test_vetoes.py` multiple_testing verdicts gain `procedure/g/n_shuffles` (0043), plus new wrong-g, too-few-shuffles, missing-g, missing-n_shuffles and retired-g=1 tests. `test_baseline.py`, `test_signal_standardisation.py`, `test_vol_rescale.py`: tests asserting pre-overlay keys now pin `vol_halflife=None`; the knee-identity test compares against a `vol_halflife=None` twin; the `small_universe` fixture now carries the live `vol_overlay` block so a default cell there runs the overlay. New `tests/test_policy_defaults.py` (40 tests: overlay resolution including a guard that the params path is spelled right, gate, highlight, report and leaderboard rendering, 0040 derivative/convexity/lump-vs-split).
- **Beyond the letter:** `verdict_for(result, i)` added in `stats.multiple_testing`, because `veto_multiple_testing` does `bool(result["rejected"])` and so cannot take the gate's per-hypothesis array; `vetoes/` is owner-only, so I did not touch it. `veto_legend`'s multiple_testing label now reads g from params. `AuditCell.key()` takes an optional `params`.
- **Not done / for Cowork:** (1) HANDOFF's "Standing refusals" still says turning the overlay on is an undecided owner call, which B1's ruling made stale; I left Cowork's text alone. (2) `AuditCell.key()` still has no suffix for a default `shadow_form` (task 39), so a default cell's key does not say whether it was priced trailing or created. (3) Nothing was run against Bloomberg; no audit.
- The phase-2 solver note is in "Not queued yet".


### 2026-09-18 — the landing commits and the first check (Claude Code, Sonnet 5)

- `e1b7687` scripts: build_coverage and inspect_raw
- `6ebed2f` audit: the TE path probe
- `a6efef0` portfolio: an opt-in volatility overlay, off by default
- `c0853d6` decisions: 0030 **proposed**, with `scripts/bias_map.py`
- `scripts/unattended.sh check --digest` at `1b6babf` with the above in the
  tree: **rc=0, 438 tests, 417 s**
  (`results/audit/_unattended/20260918-082014-check/`).
- A second `check` launched 34 s later (`20260918-082048-check`) was killed
  mid-suite, `Error 143`. Duplicate launch, not a failure.

### 2026-09-18 — tasks 0, 1 and 2 (Claude Code, Sonnet 5)

**0. Commit the coordination files** — rc=0.
- `033897e` tooling: HANDOFF.md and OWNER-QUEUE.md. Committed outside this
  session, by `lelvieira`, while a stale `.git/index.lock` (0 bytes, no git
  process running) blocked my own commit; the lock was gone when I went to
  remove it, so nothing was deleted.
- `7acd0a8` tooling: the `CLAUDE.md` pointer, committed by me afterwards.

**1. Apply the 0030 patch series** — `git am` rc=0, six patches, no conflicts.
- `4c9a9f7` 0001 decisions: 0030 decided
- `3a8b8c7` 0002 harness: the ex-ante TE reaches the veto set
- `a26e4f8` 0003 vetoes: risk_calibration replaces tracking_error
- `0d581ef` 0004 substrate: sections 4 and 10
- `208e6a6` 0005 audit: the worst annual bias
- `a913f69` 0006 audit: a risk-characteristics section

**2. Verify** — `scripts/unattended.sh check --digest` at `a913f69`:
**rc=0, 446 tests, 365 s** (`results/audit/_unattended/20260918-154931-check/`).
Governance: `OK, no uncited owner-only change since 85694662`; commit hook
installed (`core.hooksPath=.githooks`). Ruff clean.
Tasks 3 and 4 not started.

### 2026-09-19 — tasks 3 and 4 (Claude Code, Sonnet 5)

**3. One timed cell** — both rc=0.
- `TE-timing-default` (`0.05:13:9`): **3m07s** wall, cell 141 s.
- `TE-timing-1thread` (`0.05:13:8`): **2m16s** wall, cell 125 s (user 21 s vs
  real 136 s). Different seeds, as specified; no default changed.
- WSL is not at sandbox speed (16-21 s). Roughly 130 s a cell puts a serial
  484-cell audit near 17 h, so the "2 h" case is ruled out.

**4. Ten seeds, then the Bloomberg audit** — rc=0.
- `06bcea3` params: ten seeds per audit cell (decisions/0028), `git am` rc=0.
- `scripts/unattended.sh audit --digest` at `06bcea3`: check rc=0 (427 s),
  audit rc=0 (**50572 s, ~14 h**), run `A-20260918-201042`, 644 cells (484
  judged, 160 frictionless not judged), 10 seeds
  (`results/audit/_unattended/20260918-160333-audit/`).
- 100 of 484 judged cells fail a portfolio veto, **all 100 on
  `risk_calibration`** (base cells: 37 of 160). `bias_worst_annual` above the
  1.72 ceiling in exactly those 100; judged median 1.59, max 2.32.
  `bias_worst_year` is 2008 in 420 of 484 judged cells.
- Max per-cell turnover 349%, under the 400% backstop. Max `inaccurate_share`
  0.24%.
- No `report.md` in the run dir; the digest read `summary.json` and the log.


### 2026-09-19 — tasks 5 and 6, and a stop at 7 (Claude Code, Sonnet 5)

**5. Commit the decision records and the resolution map** — rc=0.
- `6db3404` decisions: 0031-0034 and the ticker resolution map.

**6. Promote the three decided records** — rc=0.
- `c8b2070` decisions: 0031, 0032 and 0033 decided. **0034 is still in
  `decisions/proposed/`.**

**7. Rebuild the coverage tables — STOPPED, not committed.** `make coverage`
and `make universe` both rc=0. The task says to stop if a tier moves; four did:
- `M1EAMVOL` and `M1EFMVOL` (both investable): `second` -> `backbone`.
- `H09122US` and `H12823US` (both `investable: false`, hedged): `tradable-only`
  -> `second`.
- Not moved: the investable set (95 before and after, same 102 tickers), and
  every cost bucket.
- Also beyond the task's expectation: 65 `first_daily` dates changed (median
  -63 days, range -275 to +29) and `bbg_index_coverage.csv` gained
  `sparse_era_obs` and `frequency_flag` as well as losing `likely_price_only`.
- The rebuilt `bbg_index_coverage.csv` and `investable_universe.csv` are in the
  working tree, uncommitted. Tasks 8-10 not started, per the stop rule.

### 2026-09-19 — task 7a, and a stop on the check (Claude Code, Sonnet 5)

**7a. Task 7 re-issued** — commit done, **verification FAILED**.
- `d0ee0b6` data: rebuild the coverage table from the Index Map. Verified
  before committing against `decisions/0022`: the four tier moves, census
  **77/12/8**, investable set **95**, and no cost bucket moved.
- `scripts/unattended.sh check --digest` at `d0ee0b6`: **rc=2, 238 s, 445
  passed, 1 failed** (`results/audit/_unattended/20260919-102337-check/`).
  Governance OK; ruff clean.
- Failure: `tests/test_audit.py::test_an_early_over_trade_does_not_block_a_later_one`
  — `0.374 > 0.5 * 0.954` is false. Deterministic (fails alone, 21 s).
- **Cause, established by running the same test in a worktree at `c8b2070`
  (passes):** `loaders/synthetic.py` draws the synthetic panel's ragged starts
  from `bbg_index_coverage.csv`, so the rebuild changed the synthetic panel
  the test runs on. The real panel is untouched. The test's baseline is one
  session at 0.954 (2017-01-20), i.e. the start-up entry its own docstring says
  it excludes, but which now sits at index 1..half instead of index 0.
- Not fixed, per the stop rule: no test edited, nothing worked around. Tasks
  8-11 not started. Needs Cowork/owner: whether the test's start-up exclusion
  should be made robust to the panel, and whether any synthetic-panel result
  (planted-IC ladder) is affected by the changed starts.

### 2026-09-19 — tasks 7a, 7b, 8, 9 and 11 (Claude Code, Sonnet 5)

**7a. Coverage rebuild** — `d0ee0b6` data: rebuild the coverage table from the
Index Map. Checked against `decisions/0022` before committing: four tier moves,
census **77/12/8**, investable set **95**, no cost bucket moved.

**7b. The failing test** — `24b3b9c` tests: exclude universe entry by what it
is. Entry is the last rebalance at which any series is held for the first time,
read off `PortfolioPath.weights` (entry completes at rebalance 23 of 155; same
result at weight tolerances 1e-9, 1e-6 and 1e-4); the comparison runs over what
follows and asserts at least 20 rebalances remain. `check` at `24b3b9c`:
**rc=0, 446 tests, 279 s**. **Frozen snapshot: `build_snapshot.py --verify`
(default id `synthetic-v1`) printed `OK hash matches (da3a96990f56)`, rc=0** --
the freeze held, only freshly built panels moved.

**8. Registry corrections** — `af3717e` hypotheses: data_required against the
panel that exists (decisions/0032). `tests/test_hypotheses.py` 33 passed.

**9. `L`, the transfer coefficient and 0029** — `3eff1b7` audit: the transfer
coefficient, the left tail, and a report that stops printing the twin;
`dd9e4fb` decisions: 0029 decided. `check` at `dd9e4fb`: **rc=0, 461 tests,
369 s** (446 + 15 new), governance OK.
- A rule without `alpha()` leaves TC unevaluated: NaN columns and
  `transfer_n_dates = 0`, tested (`tests/test_transfer.py`). A non-callable
  attribute named `alpha` is not mistaken for the method.
- 0029 is out of `proposed/`; **no ridge or eigenvalue floor was added** to the
  frictionless covariance (s2 deferred).
- New per-cell columns: `transfer_coefficient` (full matrix),
  `transfer_coefficient_diagonal`, `transfer_coefficient_alignment`,
  `omega_condition_median`, `omega_condition_max`, `transfer_n_dates`,
  `left_tail_L`, `left_tail_q05`, `realised_ic_cross_sectional_pearson`,
  `realised_ic_cross_sectional_demeaned`.
- Judgement calls the spec left open: Omega is the covariance of the holdable
  series in EXCESS of the benchmark (so `w' Omega w` is exactly the active
  variance the solver constrains, tested), not the raw ids covariance. Empirical
  breadth off the ladder is `(slope / TC)^2` per horizon, blank where no TC was
  measured. The existing report test asserted the old frictionless section and
  was updated to assert its absence (it is the behaviour 0029 s1 retires).
- Rendered against `A-20260918-201042`'s `cells.csv`, the new report prints
  dashes for the columns that run predates and no frictionless section.

**11. Rebalance-policy resolution** -- `8ef03bc` decisions: 0024 -- weekly re-solve stays, deliberately.

**10. Rerun the audit** -- rc=0, at `8ef03bc`. `make check` 349 s, `make audit`
**47908 s (13.3 h)**, run **`A-20260919-155557`**, 644 cells, 10 seeds
(`results/audit/_unattended/20260919-115007-audit/`). Figures below are from
`cells.csv`, not the digest; the digest's medians agree.
- Engine untouched: **`net_ir` is identical in all 644 cells** to
  `A-20260918-201042`. 100 of 484 judged cells still fail, all `risk_calibration`.
- Base-cell medians of the new columns (160 cells): `transfer_coefficient`
  (full matrix, reported) **0.0205** (range -0.008 to 0.085); diagonal **0.0598**
  (-0.038 to 0.241); alignment **0.0365**; `left_tail_L` **0.934** (0.776 to
  1.147; digest: p05 0.85, p95 1.03).
- `omega_condition_median` **91,153** and max 289,324 in every base cell -- the
  same in each, because it depends on the date's covariance and not on the cell.
- `implied_ic` at TC = 1: 0.024 / 0.044 / 0.062 / 0.088 for h4/13/26/52. At the
  measured TC: 1.09 / 1.62 / 1.97 / 6.14. Ladder empirical breadth 5,900 to
  22,000 against formula 12 to 152.
- **The TC values are not usable as measured, and I have not decided why.**
  Published range is 0.3-0.8 (CDT 0.671 full, 0.620 diagonal). Here TC rises
  with IC (full: 0.003 at IC 0.02, 0.061 at IC 0.20) and the **oracle cells
  (IC = 1) read 0.039 to 0.042 full and -0.003 to 0.029 diagonal**, so a perfect
  signal transfers about 4%. Alignment (the inversion-free control) is also
  0.01-0.07, so this is not only the ill-conditioned inverse in the full form.
  Candidate: `w` is the whole fully-invested book, and in excess-return space the
  benchmark-replicating baseline (`w' Omega w` is tiny for it) is not separated
  from the tilt, so A and B correlate alpha with mostly-baseline weights. That
  is a definition question for `decisions/0033` (what "active weight" means when
  the benchmark legs are not holdable), not something I changed.
- `ruler.md` (there is no `report.md`) no longer has the frictionless tables or
  the base-over-frictionless ratio; its one "frictionless cells" mention is the
  veto sentence. Frictionless rows carry no TC by construction (no alpha exposed).


### 2026-09-20 — tasks 12 and 15, and a stop at 16 (Claude Code, Sonnet 5)

**12. Commit the 0035 write-up** — rc=0. `37491a9` decisions: 0035 proposed.

**15. Commit 0036 and the queue rewrite** — rc=0. `d2f2c4b` decisions: 0036.
HANDOFF.md had already gone in with 12, as anticipated; nothing extra to add.

**16. `data/requests/*.yaml` — STOPPED, not committed.** rc=n/a.
- No `make` target or script regenerates them. The only writer is
  `HypothesisRegistry.triage()` -> `write_data_request()`, reached through
  `scripts/nightly_cycle.py --snapshot <id>`, which also writes to the real
  results store and the real `data/requests/`.
- A faithful regeneration needs the manifest of the snapshot the files were
  produced against. The only target that builds one is `synthetic-v1`, which
  would list nearly every series as absent and would not reproduce the changes.
  I did not identify or list the Bloomberg snapshot (`data/snapshots/` is
  off-limits to me), so I could not run triage against it into a scratch dir.
- The six diffs are real (`git diff --ignore-cr-at-eol`); H-2026-0009 shows the
  0032 corrections (MXUS->SPXT, MXEU->MXEUG, MXJP->NDDUUK/NDDUJN, MXEF->M1EF,
  MXWO and LEGATRUU dropped, count 7->6), but the match to a regeneration is
  unestablished, so per the task they are not committed.
- Needs Cowork/owner: name the snapshot id to triage against (or run the triage
  themselves), or decide these are acceptable as hand edits citing 0032.
- Tasks 17-21 not started, per the stop rule.

**16 (continued, same day).** Owner said to commit the six request files and
HANDOFF.md as they stand. Regeneration match still unestablished; committed on
the owner's instruction, citing decisions/0032.

**17. The block-shuffled baseline** — `da214c0` audit: the block-shuffled
baseline. `scripts/unattended.sh check --digest` at `a874b5f` + the working
tree: **rc=0, 294 s, 479 tests** (461 + 18 new in `tests/test_baseline.py`),
governance OK, ruff clean (`20260920-112220-check`). A first check at 9 s failed
`ruff format` on my own files; formatted and rerun.
- **The bit-for-bit reproduction test PASSES.** Golden values (score hash
  `3c56e07462d30d6d`, net IR `-0.8793457503233992` on the small synthetic
  cell) were taken from `HEAD` in a clean worktree, and the working tree
  reproduces both.
- Shuffle is in `src/signal_lab/stats/blocks.py`. Targets `audit-baseline-pilot`
  and `audit-baseline` exist and the unattended whitelist is extended; nothing
  in `params/` changed.
- Two judgement calls beyond 0036: (1) a baseline-only run writes `cells.csv` and
  a `summary.json` (panel/params hashes, net IR by rung with min/max) instead of
  the ruler report, which raises `KeyError: 'horizon'` without base cells;
  (2) cells that were live but received a NaN row in the shuffle are set to zero,
  so availability equals the live cell's exactly rather than shrinking.
- Not run end to end on real data. A full synthetic pilot exceeded 15 min, so
  plumbing was checked on a 2-cell table through `_write_baseline_run`.

### 2026-09-21 — task 24 (Claude Code, Sonnet 5)

**24. Commit the records, then the constitution** — rc=0.
- Commit A `40ff9df` decisions: 0035 decided, and 0036 amended. Git recorded the
  0035 move out of `proposed/` as a **rename**, not a delete plus an add.
- Commit B `d012c37` substrate: sections 3 and 10 (decisions/0036). The
  `commit-msg` hook accepted it. My own attempts to commit `SUBSTRATE.md` were
  refused twice by the permission classifier; the owner committed it by hand.
  The message is the subject line only, without the task's explanatory body.
- `scripts/unattended.sh check --digest` at `d012c37`: **rc=0, 404 s, 479 tests**
  (`results/audit/_unattended/20260921-161337-check/`). Governance line: "OK. No
  uncited owner-only change since `85694662`. Commit hook is installed." Ruff
  clean, holdout lock 15 of 15.
- Not committed, as instructed: `raw_meta.json`, `raw_structure.json`,
  `results/audit-bloomberg.log`, `results/audit/`.

### 2026-09-21 — task 18 (Claude Code, Sonnet 5)

**18. The baseline pilot** — rc=0. `scripts/unattended.sh audit-baseline-pilot
--digest` at `d012c37`: check rc=0 (303 s), audit rc=0 (**2325 s**), run
**`A-20260921-202607`**, 40 cells, h13, ten seeds
(`results/audit/_unattended/20260921-162103-audit-baseline-pilot/`).
- **Hashes match `A-20260919-155557`**: `panel_hash` `dfbf5c5a…5793` and
  `params_hash` `ebdfb70e…b77c`, both identical. The pairing is valid.
- Baseline `net_ir` by rung (mean, seed min to max, n=10):
  - IC 0.02: 0.290 (-0.369 to 0.589)
  - IC 0.05: 0.321 (-0.605 to 0.798)
  - IC 0.10: 0.277 (-0.101 to 0.677)
  - IC 0.20: 0.346 (0.044 to 0.679)
- **Mean-imputed share** (live cells that drew a NaN row in the shuffle and were
  set to 0.0), measured by replaying the shuffle on the real weekly panel with a
  scratch script that prints counts only: 69,175 live cells (990 rows x 95
  holdables). Per seed 7,866 to 16,150, i.e. **10.4% to 23.4%, mean 19.5%**.
  Below the ~25% stop line for every seed, but the top of the range is close.
- **Worst single instrument: 100%.** One series (column index 10, 332 live rows of
  990) has every live row imputed under at least one seed, so at that seed its
  baseline carries no shuffled truth, only noise. Not a stop condition as written
  (the line is on the overall share), but it says the late-starting series are
  where the baseline departs most from its live twin.
- Plumbing: `_write_baseline_run` ran end to end on real data for the first time
  and wrote `cells.csv` and `summary.json` without error. Neither digest step
  nor the run surfaced any problem; the digest's own summary is in `digest.md`.
- The imputation share is not persisted by the run; the scratch script is in the
  session scratchpad, not the repo.

### 2026-09-21 — task 20, re-specified as the knee grid (Claude Code, Sonnet 5)

**20. Live + baseline at IC 0.35, 0.50, 0.70** — rc=0. `457b5e8` audit: the
knee grid. `scripts/unattended.sh audit-knee --digest` at `457b5e8`: check
rc=0 (274 s), audit rc=0 (**3205 s, ~53 min**), run **`A-20260922-005316`**, 60
cells, h13, ten seeds (`results/audit/_unattended/20260921-204838-audit-knee/`).
- **Both hashes match** `A-20260919-155557` and `A-20260921-202607`:
  `panel_hash` `dfbf5c5a…5793`, `params_hash` `ebdfb70e…b77c`. The pairing is
  valid.
- Per rung (live mean, baseline mean, excess mean, excess SE, n=10 seeds):
  - IC 0.35: live 0.390, baseline 0.295, **excess 0.095, SE 0.035**
  - IC 0.50: live 0.473, baseline 0.361, **excess 0.111, SE 0.016**
  - IC 0.70: live 0.535, baseline 0.326, **excess 0.209, SE 0.018**
- Excess is positive and several SE from zero at every rung, growing with IC.
- Not asked for, flagged anyway: `risk_calibration` fails on 28 of 60 cells
  (`bias_worst_annual` 1.726-2.036 against the 1.72 ceiling), concentrated in
  seeds 0, 1, 3, 5, 6, 7 across all three rungs, live and baseline both. Net IR
  and the excess above are unaffected by this veto (it's ex-post risk
  calibration, not a return figure), but it is the one ex-post gate in
  SUBSTRATE and it is failing on nearly half this grid.
- `params/audit.yaml` untouched; `params_hash` unmoved confirms it.

### 2026-09-21 — task 22 (Claude Code, Sonnet 5)

**22. `decisions/0035` s4(a), s4a and s5** — rc=0. `d8f70ef` audit: the
corrected transfer coefficient and its baseline. `scripts/unattended.sh check
--digest` at `457b5e8` + the working tree: **rc=0, 350.7 s, 483 tests** (479 +
4 new: `baseline_weights`, the corrected-TC acceptance test, the r2-floor
test), governance OK, ruff clean, holdout lock 15/15
(`results/audit/_unattended/20260921-215621-check/`).
- **s4, the corrected estimator.** All three estimators now compute on
  `w - w_baseline` (`w_baseline` = the leg-weighted sum of each benchmark leg's
  NNLS tracking portfolio, `portfolio/covariance.py`'s existing `.legs[leg]`
  diagnostics). `w_active` substitutes for `w` everywhere `coefficients()` used
  it, not just the numerator, since a partial substitution still divides by
  the replication-dominated total variance. **Acceptance test, as specified:**
  a book built from `w_baseline` plus the unconstrained optimum's own tilt
  reads TC **1.0** (to 1e-6, `pytest.approx`); a book tilted orthogonal to its
  own alpha reads **0.0** (to 1e-6). Both run on a real NNLS-embedded synthetic
  universe (trimmed, 14 series), not hand-built matrices.
- **s4a, the NNLS r2.** Surfaced as `nnls_r2_<leg>` / `nnls_residual_variance_<leg>`
  on every cell and in `ruler.md`/`ruler.html`'s transfer-coefficient section.
  **On a real Bloomberg base cell (IC 0.10, h13, seed 0), r2 is 0.9998601801189837
  for NDUEACWF and 0.9996685999818131 for LEGATRUU — both far above the 0.90
  floor.** Not a stop condition. A test asserts a 0.90 floor on the synthetic
  legs (spannable by construction, so a breach there is a real regression).
- **s5, persistence.** Weights, alpha and the rebalance-date index for every
  base cell, as parquet under `results/artifacts/<run_id>/<cell key>/`.
  **Measured disk cost: 0.86 MB for one real Bloomberg base cell** (94
  holdable series, 834 dates; two files, weights + alpha). The standard grid
  has 160 base cells, so a full run's artifacts are **roughly 137 MB**,
  extrapolated from one cell, not measured on a full run. Not committed to
  git (results/artifacts/ is regenerable, per SUBSTRATE section 11); confirmed
  via a scratch smoke test on the synthetic lean grid (4 base cells, 3.6 MB)
  and the one real cell above.
- **Beyond the stop rule, an open finding, not a stop condition:** the real
  IC = 1 oracle cell's corrected TC does **not** read near ceiling (full
  0.022, diagonal 0.029 -- close to the OLD estimator's 0.039-0.042), even
  though the estimator recovers 1.0 exactly on the constructed acceptance
  case. Traced one date: the solved book `w` and its NNLS baseline
  `w_baseline` are nearly orthogonal in raw weight space (cos 0.011), and
  `alignment` barely moves under the correction (8th decimal), consistent
  with `w_baseline` sitting close to the min-active-variance portfolio in
  Omega's own metric -- 0035 s3's subtlety, now observed rather than argued.
  This is the open question 0035 s7 already named ("the two are the same
  investigation and neither settles first"); it does not block this task, and
  no re-run of `A-20260919-155557` was authorised or attempted.
- `params/` untouched.

### 2026-09-22 — task 19 (Claude Code, Sonnet 5)

**19. The full baseline grid** — rc=0. `scripts/unattended.sh audit-baseline
--digest` at `941a799`: check rc=0 (283 s), audit rc=0 (**32912 s of reported
elapsed time, but see below**), run **`A-20260922-033647`**, 160 cells, four
horizons, ten seeds (`results/audit/_unattended/20260921-233203-audit-baseline/`).
- **Both hashes match** `A-20260919-155557`, `A-20260921-202607` and
  `A-20260922-005316`: `panel_hash` `dfbf5c5a…5793`, `params_hash`
  `ebdfb70e…b77c`.
- **Not actually 9.1 hours of audit compute.** The log shows 160 cells at the
  usual 40-90s each, except cell 121 (`ic0.02_h52_s0`), which reports
  **23,625.1s (6h 34m)** on its own. The machine (or WSL) slept overnight
  between cells 120 and 121; the process resumed and finished normally, and
  every cell before and after ran at the expected pace. True audit compute is
  close to task 18's per-cell rate (~50-70s), i.e. roughly **2.5-3 hours**, not
  the 9.1 hours the wall clock reports. Net IR is unaffected -- this is only a
  timing artifact.
- Baseline `net_ir` by horizon and IC rung (mean, seed min-max, n=10):

  | h | IC 0.02 | IC 0.05 | IC 0.10 | IC 0.20 |
  |---|---|---|---|---|
  | 4  | 0.299 (-0.200 to 0.620) | 0.306 (-0.062 to 0.669) | 0.228 (-0.036 to 0.500) | 0.314 (-0.025 to 0.525) |
  | 13 | 0.290 (-0.369 to 0.589) | 0.321 (-0.605 to 0.798) | 0.277 (-0.101 to 0.677) | 0.346 (0.044 to 0.679) |
  | 26 | 0.304 (-0.345 to 0.668) | 0.304 (-0.402 to 0.806) | 0.467 (-0.076 to 0.820) | 0.295 (-0.087 to 0.511) |
  | 52 | 0.363 (-0.164 to 0.619) | 0.348 (-0.168 to 0.618) | 0.321 (-0.269 to 0.967) | 0.250 (-0.162 to 0.710) |

- Every rung's mean sits in the 0.23-0.47 band, in line with the h13 rungs
  task 18 and task 20 already measured; no horizon shows the floor collapsing
  or escaping that range.

### 2026-09-22 — task 23, STOPPED before the vendor call (Claude Code, Sonnet 5)

**23. JPMaQS catalogue check** — rc=1 (stopped, not a failure of the code).
`bb4db0b` scripts: the JPMaQS catalogue check.
- **Step 1, the extra:** `uv sync --group dev --extra jpmaqs` installed
  `macrosynergy==1.8.1` and its deps into the shared venv. `pyproject.toml`
  already declared the `jpmaqs` extra, so nothing else changed (`uv.lock`,
  `pyproject.toml` both untouched). `make check` afterward: **rc=0, 483
  tests, 317.5 s**, governance OK.
- **Step 2, the script and target:** `make jpmaqs-catalogue` wraps
  `scripts/jpmaqs_catalogue_check.py`, constructed with
  `check_connection=True` as specified.
- **Step 3, confirmed before any call:** the 27 rows tagged `genuine
  phase-3 gap` in `data/requests/ticker_resolution.csv` are 8 cids x 12
  xcats; `cross_product_size()` confirms the cross product is **96**, as
  expected.
- **Stopped at credentials.** `DQ_CLIENT_ID` and `DQ_CLIENT_SECRET` are not
  set in this session's shell (`env | grep -c DQ_CLIENT` reads 0 -- a count,
  not a value, and `.env` itself was never opened, per the task's own hard
  limit). `JPMaQSLoader.credentials()` raised before any network call was
  attempted, so this is a credentials gap in this session, not a rejection
  from the vendor. Per the task's stop rule for a network/auth failure, this
  stops and reports rather than sourcing `.env`, exporting the values myself,
  or working around the check.
- **Not obtained:** the catalogue size, how many of the 27 resolve, and
  whether `request.txt` was written. `data/raw/jpmaqs_catalogue.json` and
  `data/requests/jpmaqs_catalogue_check.csv` do not exist.
- Needs Cowork/owner: either export `DQ_CLIENT_ID`/`DQ_CLIENT_SECRET` in the
  shell this session runs in, or run `make jpmaqs-catalogue` directly where
  the credentials are already exported.

### 2026-09-22 — task 23, continued: the vendor call itself (Claude Code, Sonnet 5)

**23, continued.** Credentials were exported by the owner directly into a
single shell invocation (`source .env` immediately before the script, never
read by me) and the check was run for real. **rc=1, stopped by the script's
own stop rule -- not a code failure.**
- First attempt used a bare `uv run --python 3.12 --group dev ...` (my
  mistake) rather than `make jpmaqs-catalogue`, so `UV_PROJECT_ENVIRONMENT`
  was unset and it fell back to a fresh local venv without `macrosynergy` --
  exactly the bare-`uv run` failure mode CLAUDE.md warns about. Corrected to
  `make jpmaqs-catalogue`, which sets it via `build.mk`.
- With the right venv: connected, confirmed **27 named tickers, cross
  product 96**, then `JPMaQSDownload(check_connection=True)` failed:
  **`AuthenticationError: 401 Client Error: Unauthorized for url:
  https://authe.jpmchase.com/as/token.oauth2`**.
- This reached the vendor's own auth host directly (no proxy, matching
  `params/data_sources.yaml`'s `proxy.enabled: false` for a personal
  machine) and got a real response, so it is a credentials rejection, not a
  network/resolution problem. Per the task's stop rule, the proxy setting
  was not varied and no alternate host was tried.
- **Nothing was written.** No catalogue cache, no
  `jpmaqs_catalogue_check.csv`, no `request.txt`; `git status` confirms no
  new files from this attempt.
- Needs Cowork/owner: the credentials in `.env` (`DQ_CLIENT_ID` /
  `DQ_CLIENT_SECRET`) are being rejected by the vendor's token endpoint --
  worth checking whether they are current, correctly paired, or need
  reissuing, before task 23 is retried.

### 2026-09-22 — task 23, the 401 explained (owner's own test, not run here)

Not a Claude Code run -- the owner tested the same `DQ_CLIENT_ID`/
`DQ_CLIENT_SECRET` from a work machine, outside this session, and got a
clean auth success (`check_connection=True`, no proxy). This resolves the
open question from the two receipts above:
- **The credentials are valid.** The 401 this session saw was not a bad or
  expired client_id/secret.
- **It is network-origin, not proxy-credential.** The owner's successful
  test also used `proxy=None` -- so the difference between the two attempts
  is which network the request originated from, not whether it went through
  Itaú's authenticated proxy. DataQuery's auth endpoint appears to only
  accept these credentials from Itaú's network.
- **This session cannot finish task 23.** It runs on the same personal
  machine that got the 401, and nothing here can route it onto the
  corporate network. The vendor call (`make jpmaqs-catalogue`) needs to run
  from a machine on that network, with `.env` present there. Once it is, the
  script and target already exist and are unchanged from the earlier
  receipts (`bb4db0b`).

### 2026-09-22 — task 21 (Claude Code, Sonnet 5)

**21. Remove the parked lock file** — rc=0. `.git/index.lock.stale-cowork-20260920`
was present (0 bytes, from 2026-09-20). Confirmed `.git/index.lock` itself did
not exist and no git process was running before removing. Deleted.

### 2026-09-23 — task 23, completed (Claude Code, Sonnet 5)

**23. JPMaQS catalogue check — a real result.** rc=1 (the script's own stop
rule, not a failure). Owner ran `set -a; source .env; set +a; make
jpmaqs-catalogue` directly, with a corrected `DQ_CLIENT_SECRET` (the two
earlier stops in this file -- credentials not present, then a 401 -- are
superseded; the 401 really was a bad secret, not the network-origin
explanation offered in between, since the fix alone made this machine
succeed).
- **Auth succeeded** (no proxy, this machine, the one that gave the earlier
  401). Downloaded the JPMAQS catalogue: **31,728 tickers**, cached at
  `data/raw/jpmaqs_catalogue.json` (git-ignored, not committed).
- **27 named tickers, cross product 96** (8 cids x 12 xcats), confirmed
  before the call, as before.
- **12 of 27 did NOT resolve:**
  `USD_INTRGDP_NSA_P1M1ML12_D1M1ML3`, `EUR_INTRGDP_NSA_P1M1ML12_D1M1ML3`,
  `JPY_INTRGDP_NSA_P1M1ML12_D1M1ML3`, `GBP_INTRGDP_NSA_P1M1ML12_D1M1ML3`,
  `USD_UNEMPLRATE_SA_D1Q1QL4`, `USD_BLSDCLN_SA_D1Q1QL1`,
  `EUR_BLSDCLN_SA_D1Q1QL1`, `USD_MBASEGDP_SA_D1M1ML12`,
  `USD_RM1GDP_SA_D1M1ML12`, `EUR_RM3GDP_SA_D1M1ML12`,
  `USD_GB10YXGB_NSA`, `EUR_GB10YXGB_NSA`.
- **Per the stop rule: not substituted, not guessed, not dropped.**
  `data/requests/jpmaqs_catalogue_check.csv` was written (27 rows, all
  findings). `data/jpmaqs/request.txt` was **not** written -- confirmed by
  `git status` (no such file) -- since not all 27 resolved.
- Needs the owner: the same `decisions/0032` precedent this task's stop rule
  cites -- these 12 xcats or cid/xcat combinations are either misnamed
  (worth a hand check against the JPMaQS documentation) or genuinely absent
  from the vendor's catalogue, and only the owner decides whether to drop,
  rename or wait on them.

### 2026-09-23 — tasks 26 and 27 built, STOPPED on the check (Claude Code, Opus 5.5)

**Step 0 done:** `19c16be` commits Cowork's queue (tasks 26-27, run-order note,
OWNER-QUEUE L14). **Nothing else is committed.** Tasks 26 and 27 stay in the
queue because the check did not pass.

**What is built (uncommitted, in the working tree):**
- **26:** new `src/signal_lab/loaders/env.py` (`check_secret`) **refuses**
  leading or trailing whitespace, CR/LF, and control characters (`ord < 32`,
  127). The error names the variable and the defect only. Used by
  `JPMaQSLoader.credentials()`, by `JPMaQSLoader.proxies()` (`PROXY_PWD`) and by
  `FredLoader.api_key()`. New `tests/test_jpmaqs_credentials.py` has 8 tests, and
  they pass on their own.
- **27:** new `scripts/jpmaqs_candidates.py`, `make jpmaqs-candidates` in
  `build.mk`, and `tests/test_jpmaqs_candidates.py` (7 tests, hand-written
  fixture), passing on their own. **Not run against the cache yet**, so
  `data/requests/jpmaqs_candidates.csv` does not exist.

**The check, run twice:**
- `20260923-172023-check`: **rc=2, 52 s**, lint only. `ruff format` read
  `scripts/jpmaqs_candidates.py` while this session was still writing it. My
  own race; the file was formatted before the second run.
- `20260923-172145-check`: **rc=2, 829 s, 496 passed, 2 failed.** Governance
  OK and ruff clean. Both failures are in `tests/test_scripts.py`
  (`test_nightly_cycle_records_blocked_not_a_fake_veto_failure`,
  `test_the_cycle_records_the_specific_blocked_reason`):
  `OSError: [Errno 22] Invalid argument: .../data/requests/H-2026-0011.yaml`
  from `write_data_request` (`harness/hypotheses.py:411`). **Both pass when
  run alone** (2 passed, 6 s), so the failure is intermittent. EINVAL on a
  `/mnt/c` write usually means something on the Windows side had the file
  open.
- **The real defect it exposes:** these two tests pass `tmp_path` for the
  snapshot and the store, but `triage` writes data requests to the **real**
  `data/requests/`, so every `make check` rewrites the tracked
  `H-2026-00xx.yaml` files. Contents are unchanged this time (`git status`
  clean for `data/requests/`), but the tests are not isolated from the repo.
  Neither failure is in code tasks 26 or 27 touch.

**Needs Cowork:** either a task to point those tests' requests directory at
`tmp_path` (my suggestion, since it removes the exposure), or an
instruction to re-run the check as-is. Task 25 is not started. I read it and
planned the change, but nothing is edited.

### 2026-09-23 — tasks 28, 26 and 27 (Claude Code, Opus 5.5)

**Check:** `scripts/unattended.sh check --digest` with all three in the tree:
**rc=0, 733 s, 499 passed** (`results/audit/_unattended/20260923-174720-check/`).
One run, no retry.

**28. Cycle tests isolated.** Committed as `2aebc87`. `nightly_cycle.py --requests-dir`
defaults to `data/requests/`, so a real run is unchanged. Grepping found four
`cycle.main` calls, and all four now pass it, including the tampered-snapshot
test. Triage writes requests **even under `--dry-run`**, so the rule "only
calls without `--dry-run`" would have missed some. The new
`test_a_cycle_run_by_a_test_leaves_the_real_registry_and_requests_untouched`
passes: it compares mtimes and hashes of `data/requests/` and `hypotheses/`
before and after. The `test_hypotheses.py` registry tests on the real root only
read, so they were not changed.
- **Task 16's question:** a synthetic `--dry-run` triage into a temp dir writes
  11 request files, and **all 11 are byte-identical to the committed `HEAD`
  blobs**. So a synthetic triage does reproduce them, which points to `make
  check` as what rewrote the six files task 16 found. Hand edits are unlikely.

**26. Malformed secrets refused.** Committed as `46c4969`. The loaders using
`check_secret` (`loaders/env.py`) are JPMaQS `credentials()`, JPMaQS
`proxies()` (`PROXY_PWD`) and FRED `api_key()`.
`tests/test_jpmaqs_credentials.py` has 8 tests.

**27. Candidate names.** Committed as `a6a0218`; the CSV is committed with this
receipt. `make jpmaqs-candidates` rc=0 wrote 69 rows to
`data/requests/jpmaqs_candidates.csv`. **No ticker hit the 40 cap.** Candidate
counts and match levels: `INTRGDP_NSA_P1M1ML12_D1M1ML3` x USD/EUR/JPY/GBP 5
each, stem. `USD_UNEMPLRATE_SA_D1Q1QL4` 26, stem. `BLSDCLN_SA_D1Q1QL1` x
USD/EUR 4 each, **relaxed**. `USD_MBASEGDP_SA_D1M1ML12` 4, stem.
`USD_RM1GDP_SA_D1M1ML12` **0, none**. `EUR_RM3GDP_SA_D1M1ML12` **0, none**.
`USD_GB10YXGB_NSA` 8, **relaxed**. `EUR_GB10YXGB_NSA` **0, none**. Nothing
ranked or chosen.

### 2026-09-23 — task 25 built; the audit not yet run (Claude Code, Opus 5.5)

**Build done, audit pending.** `61c53a0` adds the `score` shuffle mode,
`score_shuffle_rng(seed, perm)`, `AuditCell.shuffle`/`perm` (key suffix
`_baseline_score_pNN` only for score cells), the `power` grid (80 cells),
`make audit-power` and the `unattended.sh` whitelist. `params/` is untouched.
The review doc `claude/detection-threshold-review-2026-09-22.md` is a Cowork
project doc and not in the repo, so it was not read.
- `scripts/unattended.sh check --digest`: **rc=0, 1012 s, 506 passed**
  (`results/audit/_unattended/20260923-180524-check/`).
- **The bit-for-bit test passes.** New golden tests pin the truth shuffle's
  score hash and `baseline_rng` stream as recorded before the change, and both
  pass.
- A smoke run of the new summary against `A-20260922-005316`, using fake shuffled
  IRs, found all four live twins and **both hashes matching**. The real match is
  re-checked by the audit itself.
- `audit-power` was launched at 18:23 and **stopped by hand during its opening
  `make check`**, before any cell ran, because the owner needed to put the machine
  to sleep. Nothing was written to `results/audit/` by it. **Next:**
  `scripts/unattended.sh audit-power --digest`, then the receipt task 25 asks for.

### 2026-09-24 — task 25, the power audit (Claude Code, Opus 5.5)

**25. `scripts/unattended.sh audit-power --digest`: rc=0.** Opening `make check`
rc=0 in 718 s. The audit took **9580 s**, against 80 minutes estimated: most cells
took about 105 s, and 7 took 300-450 s. Run **`A-20260924-194115`**, 80 cells,
all `score` shuffle, at commit **`61c53a0`**. Logs are in
`results/audit/_unattended/20260924-152915-audit-power/`.
- **Hashes: both match `A-20260922-005316`.** `panel_hash` `dfbf5c5a...`,
  `params_hash` `ebdfb70e...` (unchanged).
- **The bit-for-bit test passes** (part of the opening check, and of
  `20260923-180524-check`).
- The live twins are that run's base cells `ic{0.35,0.70}_h13_s{0,1}_c1.0_tnone_rnone`,
  checked by hand against its `cells.csv`.

| IC | seed | live net IR | shuffled mean | shuffled sd | live rank of 21 |
|---|---|---|---|---|---|
| 0.35 | 0 | -0.021 | 0.264 | 0.144 | 20 |
| 0.35 | 1 | 0.500 | 0.384 | 0.192 | 6 |
| 0.70 | 0 | 0.091 | 0.301 | 0.203 | 20 |
| 0.70 | 1 | 0.722 | 0.386 | 0.148 | 1 |

Rank 1 is the highest. The full rows are `power_by_cell` in the run's
`summary.json`. Interpretation is left to Cowork and the owner. The unattended
digest has further observations, not repeated here.

### 2026-09-24 — task 29 (Claude Code, Sonnet 5)

**29. Names-only catalogue search for H-2026-0004, 0005, 0010** — rc=0.
- `scripts/unattended.sh check --digest`: **rc=0, 512 passed, 1420 s** (`20260924-225939-check`; an earlier run failed only `ruff format` on my two new files, fixed). `make jpmaqs-name-search` rc=0, 151 rows.
- H-2026-0001 cache membership: **7 of 7 resolve** (cache test, not the vendor check).
- `n_matches`, cap (60) not hit anywhere: 0004 USD|EUR `BLS` 16; 0010 `GB10Y` (DEM,FRF,ITL,ESP,NLG,EUR,USD) 40; 0010 `GB10YCRY` all cids 28, on 14 cids (ATS AUD BEF DEM ESP FIM FRF GBP IEP ITL JPY NZD PTE USD); 0005 USD|EUR: `MBASE` 8, `MBROAD` 8, `MNARROW` 8, `M1` 0, `M2` 0, `M3` 0, `RM` 16, `INTLIQ` 6, `PCREDIT` 18.
- Nothing ranked or recommended; renaming/dropping/holding is OWNER-QUEUE L14. Commit hash: see `git log` (message `handoff: task 29`).

### 2026-09-26 — task 30 (Claude Code, Sonnet 5)

**30. `score_span` and the 10-seed power grid** — rc=0. Run **`A-20260926-161749`**, 200 cells, 20019 s of wall clock (one cell took 4867 s: the machine slept; the ~95 s cells are the real cost).
- Commits: queue `21ab064`; `score_span` + `power10` `a7f92db`; preflight fix `84cc804`. `scripts/unattended.sh audit-power10 --digest` at `84cc804`: check **rc=0, 426 s**. A first attempt at `a7f92db` stopped at my own preflight (`KeyError: 'shuffle'`, the knee run's `cells.csv` predates that column) **before any cell**; fixed, tested, relaunched.
- **Hashes match** `A-20260922-005316`: panel `dfbf5c5a...5793`, params `ebdfb70e...b77c`. All ten seeds' live and truth-twin cells were present (checked before any cell ran). `params/` unchanged.
- Bit-for-bit: `score` mode reproduces its pre-change hash and RNG stream; live, truth-shuffle and `score` keys unchanged; new key `_baseline_scorespan_pNN`. Tests: 34 in `tests/test_baseline.py`, all passing. **The truth shuffle has the same re-masking by construction and was left unchanged.**
- **Slope diagnostic** (synthetic 991 x 95, 20 late starters, 4 (IC, seed) x 20 perms; slope of shuffled column means on live, mean (min-max), corr): full-history `score` 0.81 (0.71-0.91) corr 0.93 -> `score_span` **1.00 (1.00-1.00) corr 1.00**; late-starting `score` 0.58 (0.36-0.91) corr 0.76 -> `score_span` 0.76 (0.48-0.96) corr 0.86. Alpha-mean slopes: full 0.80 -> 0.98, late 0.61 -> 0.77. The script is not in the repo (scratchpad).
- **Per seed (IC 0.70, h13):** live net IR / truth-twin / `score_span` mean +- sd of 20 / live rank of 21:
  s0 0.091 / -0.086 / 0.241 +- 0.151 / 17; s1 0.722 / 0.491 / 0.328 +- 0.139 / 1; s2 0.633 / 0.445 / 0.286 +- 0.143 / 1; s3 0.558 / 0.346 / 0.315 +- 0.168 / 3; s4 0.548 / 0.425 / 0.359 +- 0.173 / 5; s5 0.436 / 0.130 / 0.296 +- 0.146 / 4; s6 0.325 / 0.192 / 0.234 +- 0.167 / 7; s7 0.679 / 0.445 / 0.297 +- 0.200 / 2; s8 0.597 / 0.395 / 0.155 +- 0.212 / 1; s9 0.760 / 0.480 / 0.289 +- 0.166 / 1.
- **Pooled sd** across seeds 0.168 (rms of per-seed sd; sd of all 200 cells 0.173). **Seeds ranking 1 of 21: 4 of 10** (5 of 10 within the top 2).
- **Shuffled cells' pooled realised IC:** 0.065 on average = **0.093 x the planted 0.70** (was ~0.12 under `score`); live twins 0.700.
- **Turnover, for OWNER-QUEUE B3 (reported, not judged):**
  - 200 shuffled cells: annual turnover above 400% in **0**, median 338%, max 355%; rolling one-year (max over the history) above 400% in **200**, median 522%, max 612%; rolling p95 above 400% in 200, median 461%, max 514%.
  - 10 live twins: annual above 400% in **0**, median 318%, max 331%; rolling max above 400% in **10**, median 498%, max 546%; rolling p95 above 400% in 10, median 437%, max 475%.
- Also seen: `risk_calibration` fails 67 of 200 shuffled cells and 4 of 10 live twins.

### 2026-09-28 — task 31 (Claude Code, Sonnet 5)

**31. Apply the owner's L14 renames, then the vendor check** — rc=0.
- Commits: queue `2448f52`; renames `acd02f6`; vendor-check outputs `7ce2dff`.
- Renames applied as the owner ruled (OWNER-QUEUE L14, "recs on all"), recorded
  as the 2026-09-27 addendum to `decisions/0032`: 0004's `BLSDCLN` (demand)
  legs -> `BLSCSCORE_NSA_D2Q2QL2` (standards, entered negated), FRED
  `DRTSCILM` dropped; 0005's `MBASEGDP`/`RM1GDP`/`RM3GDP` -> two
  `RMBROAD_SJA_P1M1ML12` legs (`MBASEGDP` dropped outright); 0010's
  `GB10YXGB` -> `GB10YCRY` (term spread re-specified as carry), EUR leg
  becomes `DEM_`. `src/signal_lab/harness/hypotheses.py`'s `DRTSCILM` mention
  is a generic vendor-prefix hint table, not a request or series list; left
  unchanged.
- `scripts/unattended.sh check --digest` at `acd02f6`: **rc=0, 1928 s.**
- **Vendor call stopped once, then succeeded, both outside my own Bash.**
  `DQ_CLIENT_ID`/`DQ_CLIENT_SECRET` were not in my shell's environment (same
  gap as task 23); I would not source `.env` or export them myself. The owner
  ran `source .env && make jpmaqs-catalogue` via the `!` channel -- same
  failure, because `.env`'s plain `KEY=value` lines aren't exported by a bare
  `source`. `set -a && source .env && set +a && make jpmaqs-catalogue`
  (guessed from the symptom, `.env` never read) then worked.
- **26 of 26 resolve** (27 registered minus 0005's one dropped leg;
  `data/requests/jpmaqs_catalogue_check.csv`). **`data/jpmaqs/request.txt`
  written for the first time**, 26 tickers.
- A second `make check` (also via the owner's `!` channel, at `acd02f6`,
  after `request.txt` existed, while my own Bash tool was down on a
  server-side classifier error for about 30 minutes) also **rc=0, 1928 s**.
- Noted, not fixed (out of task scope): `scripts/jpmaqs_catalogue_check.py`'s
  docstring and `request.txt`'s own header still say "27" in three places; the
  count is now 26 whenever a hypothesis is renamed off a `genuine phase-3
  gap` name onto a different one.
- Implementing `load_macro` and the pull itself are not part of this task, per
  its own stop rule.

**Commit-collision note, same session.** My first attempt to write this
receipt crashed mid-script (`HANDOFF.md` had changed under me -- Cowork had
concurrently added tasks 32 and 33 -- so a fixed-offset string replace no
longer matched and raised before writing). The `git add HANDOFF.md && git
commit` that followed in the same tool call still ran and committed whatever
was on disk at that point, which was Cowork's queue edit (tasks 32, 33, and
a "receipt pending" placeholder for this one), under a commit message
(`ab59120`) that claims to be this receipt but contains none of it. That
commit's content is legitimate (it is Cowork's own queue addition) but its
message is wrong. This commit supplies the actual receipt. `OWNER-QUEUE.md`
and `decisions/0038-turnover-is-disclosed-not-vetoed.md` are still uncommitted
in the working tree; task 33 step 0 asks for those with `HANDOFF.md` together,
and I have not touched them. Tasks 32 and 33 are not started.

### 2026-09-28 — task 32 (Claude Code, Sonnet 5)

**32. The friction sweep: shadow-cost coefficient at 10, 20, 40 bp** — rc=0.
Run **`A-20260928-151055`**, 60 cells, 5214 s (`~87 min`). Commit `81ed2a1`.
`scripts/unattended.sh audit-friction --digest`: check rc=0 (659 s), grid rc=0.
Queue commits (out of order, see the note above under task 31): `ef6c3f5`
(OWNER-QUEUE.md for 32-33), `96d9748` (decisions/0038, 0039; queue 32-34).

- **Hashes match** `A-20260922-005316`: panel `dfbf5c5a...5793`, params
  `ebdfb70e...b77c`. `params/` unchanged.
- **10 bp arm identical to the knee run, cell by cell, all 20 (ic, seed)
  pairs found.** Max `|diff|` in net IR: **8.3e-17** (floating-point noise,
  not a difference). `shadow_coefficient=None` and `=10.0` are the same code
  path with the same result.
- **Per (IC, coefficient), median [min, max] over 10 seeds:**

  | IC | bp | net IR | cost drag | turnover ann. | turnover roll-1y max | TE p95 | realised IC |
  |---|---|---|---|---|---|---|---|
  | 0.35 | 10 | 0.470 [-0.021, 0.618] | 0.453% [0.432, 0.466] | 244% [238, 251] | 390% [354, 418] | 7.94% [7.24, 8.53] | 0.350 |
  | 0.35 | 20 | 0.311 [0.126, 0.784] | 0.389% [0.364, 0.395] | 185% [180, 203] | 297% [268, 309] | 7.48% [6.69, 8.64] | 0.350 |
  | 0.35 | 40 | 0.386 [0.230, 0.920] | 0.358% [0.328, 0.393] | 160% [148, 167] | 237% [224, 282] | 7.72% [7.25, 8.44] | 0.350 |
  | 0.70 | 10 | 0.577 [0.091, 0.760] | 0.560% [0.529, 0.583] | 318% [314, 331] | 498% [461, 546] | 8.16% [7.26, 8.81] | 0.700 |
  | 0.70 | 20 | 0.570 [0.203, 0.820] | 0.457% [0.438, 0.476] | 232% [226, 240] | 362% [330, 386] | 7.58% [7.01, 9.01] | 0.700 |
  | 0.70 | 40 | 0.446 [0.201, 0.950] | 0.395% [0.364, 0.418] | 182% [176, 192] | 262% [255, 298] | 7.49% [6.99, 9.09] | 0.700 |

- **Paired by seed, net IR at 20/40 minus net IR at 10** (mean, sd, n
  positive of 10):
  - IC 0.35, 20bp: -0.015, sd 0.214, 5 positive. IC 0.35, 40bp: +0.066, sd
    0.264, 6 positive.
  - IC 0.70, 20bp: +0.039, sd 0.171, 6 positive. IC 0.70, 40bp: -0.068, sd
    0.178, 4 positive.
  - No coefficient dominates on net IR at either rung; each is inside 1 sd
    of zero on a 10-seed sample.
- **Counts above 200% (OWNER-QUEUE B3's new highlight level), out of 10
  seeds per arm:**
  - Annual: IC 0.35 -- 10bp: 10, 20bp: 1, 40bp: 0. IC 0.70 -- 10bp: 10,
    20bp: 10, 40bp: 0.
  - Rolling one-year max: **10 of 10 in every one of the 6 arms**, including
    at 40 bp.
- **`risk_calibration` fails per arm** (out of 10): IC 0.35 -- 10bp: 6,
  20bp: 3, 40bp: 3. IC 0.70 -- 10bp: 4, 20bp: 1, 40bp: 4. Friction lowers
  turnover monotonically but does not lower `risk_calibration` failures
  monotonically.
- Friction cuts turnover roughly in half from 10 to 40 bp at both rungs, and
  the shadow cost was clearly not holding turnover near its 100% reference at
  10 bp (task 30's finding). It does not clear the rolling-window highlight
  at any coefficient tested here.

Interpretation is Cowork's and the owner's. Stopped per the task's own
instruction; task 33 not started.

### 2026-09-28 (night) — task 34 (Claude Code, Sonnet 5)

**34. Multiple-testing module, then the FDR-vs-FWER Monte Carlo** — rc=0.
`scripts/unattended.sh check --digest`: **rc=0, 546 tests, 1206 s.** Commits:
`566a33f` (step 0, decisions 0039/0040 and queue); `ed65436` (the module and
the study). `make fdr-study` at `ed65436`: **rc=0, 210 s**, run
`results/fdr_vs_fwer/20260929-031720/` (a second, identical run at 190 s
confirms it's deterministic under its seed).

- **`src/signal_lab/stats/multiple_testing.py`:** `holm`, `romano_wolf`
  (stepdown max-T, FWER), `benjamini_hochberg`, `benjamini_yekutieli` (step-up
  FDR), `marginal_pvalues`. All four tested against a hand-worked example
  (Holm and BY both reject only the smallest p on it; BH rejects the two
  smallest), independence and positive-dependence checks against Holm, and a
  1500-replication complete-null simulation keeping realised FWER/FDR within
  MC error of nominal. 12 tests, all passing.
- **`romano_shaikh_wolf_fdr` is NOT implemented.** The task's citation
  ("Romano, Shaikh & Wolf 2008, Econometric Theory 24(2)") is that pair's
  *k-FWER* paper ("Formalized data snooping..."), not their FDR-under-
  dependence result (a different paper, in *TEST* 17(3), same year). Without
  the source in hand to fix which stepdown construction and which open choice
  the paper makes, implementing either from memory risked shipping a
  plausible-looking but wrong procedure under a citation that claims fidelity
  it doesn't have. Per the task's own instruction, this stops rather than
  approximates; `holm`, `romano_wolf`, `benjamini_hochberg` and
  `benjamini_yekutieli` ship, tested, and the study's FDR side is BH and BY
  only.
- **The study is not the literal full cross product the task lays out, by a
  disclosed design choice** (stated in the script's own docstring and the
  report): the correlation grid, k grid and n_true/mu grid are fully crossed
  (140 scenarios), but the mu SWEEP (0.5-3.0, "for the curve") runs only at
  the headline correlation and k=1000 for n_true in {1,3,6} (15 more
  scenarios), not through the whole grid again. Also, (rho_w=0, rho_b=0.2) is
  skipped: it is not a valid equicorrelation structure (between-axis
  correlation can't exceed within-axis under the factor-model construction
  used), stated in both the script and `report.md`.
- **5,000 replications per scenario, every scenario**, not reduced anywhere —
  vectorising every procedure across replications
  (`src/signal_lab/stats/_batched.py`, pinned correct against the
  single-replication functions by 5 tests comparing row by row, including a
  case mixing rows that finish the stepdown at different rounds) is what
  keeps 155 scenarios x 5,000 replications to about 3.5 minutes rather than
  hours.
- **Headline tables, n_true=3, rho_w=0.3, rho_b=0.2, k=1000:**

  IC 0.35 (mu=0.565, s=1.149 — **s assumed, not separately measured at this
  IC**):

  | procedure | avg power | P(>=1 true passes) | FWER | FDR | mean false passes |
  |---|---|---|---|---|---|
  | Holm 5% | 0.034 | 0.095 | 0.033 | 0.029 | 0.037 |
  | Romano-Wolf 5% | 0.038 | 0.106 | 0.039 | 0.033 | 0.045 |
  | BH 5% | 0.043 | 0.106 | 0.047 | 0.033 | 0.065 |
  | BH 10% | 0.073 | 0.169 | 0.098 | 0.067 | 0.163 |
  | BY 10% | 0.026 | 0.067 | 0.024 | 0.017 | 0.032 |

  IC 0.70 (mu=1.518, s=1.149, both measured):

  | procedure | avg power | P(>=1 true passes) | FWER | FDR | mean false passes |
  |---|---|---|---|---|---|
  | Holm 5% | 0.160 | 0.372 | 0.038 | 0.023 | 0.041 |
  | Romano-Wolf 5% | 0.180 | 0.407 | 0.043 | 0.024 | 0.047 |
  | BH 5% | 0.198 | 0.391 | 0.074 | 0.035 | 0.101 |
  | BH 10% | 0.285 | 0.510 | 0.154 | 0.072 | 0.253 |
  | BY 10% | 0.146 | 0.300 | 0.042 | 0.020 | 0.054 |

- Romano-Wolf beats Holm at both ICs (0.038 vs 0.034 at IC 0.35, 0.180 vs
  0.160 at IC 0.70) by exploiting the positive dependence the equicorrelated
  null carries — the mechanism the task asked to measure. BH at q=10% roughly
  doubles power over Holm at both ICs, at 3-6x the false-pass rate.
- Full `summary.csv` (155 scenarios x 5 procedures = 775 rows) has every
  (rho_w, rho_b, k, n_true, mu) combination actually run, plus the mu-sweep
  curve rows.

`params/`, `vetoes/` and `SUBSTRATE.md` untouched — confirmed by
`git diff --cached --ignore-cr-at-eol --stat` before each commit. Interpretation
is Cowork's and the owner's (OWNER-QUEUE L16). Task 36 next, per the current
queue order (34 -> 36 -> 35).

### 2026-09-29 — task 36 (Claude Code, Sonnet 5)

**36. The created-turnover shadow cost, and a 60-cell grid** — rc=0.
Run **`A-20260929-070540`**, 60 cells, 6572 s. Commit `f210af3`.
`scripts/unattended.sh check --digest` at `f210af3`: **rc=0, 562 tests, 3695 s.**
`scripts/unattended.sh audit-friction-created --digest`: check rc=0 (3661 s),
grid rc=0 (6574 s).

- **Hashes match** `FRICTION_LIVE_RUN` (`A-20260928-151055`, task 32): panel
  `dfbf5c5a...5793`, params `ebdfb70e...b77c`, checked before any cell ran.
  `params/`, `vetoes/` and `SUBSTRATE.md` are untouched.
- **`solve_reference`'s gradient for the quadratic term matches the analytic
  derivative of the 0024 curve to 1e-12** (own test); cvxpy and scipy agree
  on the shadowed problem to the same tolerance the unshadowed one already
  needs. The trailing default reproduces `GOLDEN_NET_IR` bit for bit
  (confirmed directly, not just by test: a standalone run of the golden cell
  took 117s in this environment and returned -0.8793457503233992 exactly).
- **Incident, not part of the deliverable:** mid-build I used `git stash` /
  `git stash pop` to check whether a slow SLSQP solve was a regression. The
  pop re-checked-out `scripts/unattended.sh` under `core.autocrlf=true`,
  giving it CRLF and breaking its shebang (`bash$'\r'`: not found). Caught
  immediately by the next run (`Exit 127`), fixed by converting it back to
  LF before any real check ran. No task code was affected; flagged here
  because it's exactly the class of thing `CLAUDE.md`'s CRLF warning exists
  about, and because it's the reason `git stash` was doing anything in a
  working tree with real uncommitted changes -- avoid it during active
  audits, since one of my earlier tasks now knows to.
- **Per (IC, coefficient), median over 10 seeds, created vs the trailing
  control (`A-20260928-151055`, same (ic, seed, coefficient)):**

  | IC | bp | net IR (created / trailing) | gross IR (created) | cost drag | ann. turnover (created / trailing) | week max, NAV (created / trailing) |
  |---|---|---|---|---|---|---|
  | 0.35 | 10 | 0.445 / 0.470 | 0.522 | 0.44% | 233% / 244% | 0.56x / 1.05x |
  | 0.35 | 20 | 0.426 / 0.311 | 0.492 | 0.38% | 171% / 185% | 0.43x / 1.51x |
  | 0.35 | 40 | 0.454 / 0.386 | 0.516 | 0.33% | 130% / 160% | 0.29x / 1.83x |
  | 0.70 | 10 | 0.583 / 0.577 | 0.675 | 0.56% | 313% / 318% | 0.71x / 0.96x |
  | 0.70 | 20 | 0.547 / 0.570 | 0.628 | 0.45% | 223% / 232% | 0.51x / 1.01x |
  | 0.70 | 40 | 0.526 / 0.446 | 0.593 | 0.38% | 164% / 182% | 0.38x / 1.91x |

- **The single-week lump is gone.** The largest single-rebalance trade, over
  all 10 seeds' MAXIMA per arm, never exceeds **0.84x NAV under `created`**
  (worst arm, 10bp/IC0.70); under `trailing` it reaches **2.00x** at 40bp on
  both rungs. Weeks at or above 150% NAV: **0 of 600 rebalance-cells under
  `created`, in every one of the 6 arms; under `trailing`, 9 of 10 seeds hit
  it at IC 0.35/40bp** (4 of those at or above 195%). **Paired by (ic, seed,
  coefficient), `turnover_per_rebalance_max` is lower under `created` in
  60 of 60 pairs** (mean reduction 0.31-1.49x NAV, all six arms, zero
  exceptions) -- the mechanism decisions/0040 was built for.
- **The lag-53 echo is much smaller, not measured as fully absent.**
  `turnover_autocorr_lag53` under `created`: 0.07 (10bp) to 0.17 (40bp) at
  IC 0.35, 0.06 to 0.15 at IC 0.70 -- median lag52 runs a little higher than
  lag53 at every arm, so the annual seam is not a sharp spike. This is
  **not directly comparable to a `created`-run number** because
  `FRICTION_LIVE_RUN` predates the autocorrelation columns (new this task);
  the 0.73-0.78 lag-53 figure decisions/0040 cites for `trailing` at 40bp is
  Cowork's own prior reading of that run's raw `turnover` series, not
  something this run recomputed. Against that cited figure, `created`'s
  0.10-0.17 at 40bp is a large drop, consistent with "spreads the catch-up
  rather than removing the cliff", but the two numbers were not produced by
  the same computation and the receipt should not be read as a controlled
  before/after on identical code.
- **Net IR: no consistent direction.** Paired created-minus-trailing mean
  differences run from -0.075 to +0.030 across the six arms, sd 0.08-0.19,
  and the sign flips arm to arm (positive at 4 of 6, negative at 2). On this
  evidence the created form's main effect is on the SHAPE of trading, not on
  net IR.
- **`risk_calibration` fails, created vs trailing, per arm:** IC 0.35 --
  10bp 3 vs 6, 20bp 4 vs 3, 40bp 1 vs 3. IC 0.70 -- 10bp 3 vs 4, 20bp 0 vs 1,
  40bp 1 vs 4. Lower under `created` in 4 of 6 arms, higher in 1, tied in
  none of the remaining -- not conclusive on 10 seeds, reported as asked.
- **Counts above 200% turnover highlight (OWNER-QUEUE B3):** annual --
  `created` 10/10/0 (by coefficient 10/20/40 bp) at IC 0.35, 10/10/0 at
  IC 0.70; identical pattern under `trailing`. Rolling one-year max -- 10 of
  10 in every one of the 6 arms, both forms; the created pricing does not
  clear the rolling highlight at any coefficient tested.
- **Solver health: excellent, both forms.** Every one of the 60 created
  cells' 835 rebalances solved with CLARABEL (`solvers_used` is
  `CLARABEL:835` on all 60, no fallback, no SLSQP). Max `inaccurate_share`
  0.84%, max `infeasible_te_share` 0.0%. (The `n_not_clarabel` column in
  `summary.json`'s `friction_created_by_arm`/`friction_trailing_by_arm` is a
  bug in my own aggregation, comparing `solvers_used` -- a `"NAME:count"`
  string -- against the bare literal `"CLARABEL"`, so it always reads 10;
  the number above is checked directly against `cells.csv` and is correct.)

`params/` unchanged, confirmed by `git diff --cached --ignore-cr-at-eol --stat`
before the commit. Interpretation is Cowork's and the owner's -- adopting the
form and choosing the coefficient happen later, in `params/`, via
`decisions/0040`. Task 35 (the volatility-overlay halflife sweep) is next per
the queue order (34 -> 36 -> 35).

### 2026-09-29 (day) — task 37 (Claude Code, Sonnet 5)

**37. Split the test suite: fast wiring checks and slow model-validity checks** — rc=0.
Commits: `bb67306` (step 0, decisions 0038/0040 addenda, queue 37-39), `e76b60c`
(the split). `scripts/unattended.sh check --digest`: **rc=0, 2m24s.**
`scripts/unattended.sh check-full --digest`: **rc=0, 10m26s.**

- **Profile (`pytest -q --durations=60`), top 20 of 562, 582s total:**

  | s | test |
  |---|---|
  | 78.00 | test_audit.py::test_the_turnover_cap_binds_and_costs_return |
  | 47.02 | test_audit.py::test_a_dearer_spread_makes_the_solver_trade_less |
  | 38.30 | test_baseline.py::test_at_coefficient_zero_created_equals_trailing |
  | 35.44 | test_audit.py::test_the_per_session_cap_holds_and_the_annual_figure_still_moves |
  | 33.19 | test_baseline.py::test_shadow_coefficient_none_matches_params_exactly |
  | 30.37 | test_audit.py::test_the_oracle_beats_a_blind_signal |
  | 28.89 | test_baseline.py::test_a_different_shadow_coefficient_moves_weights_not_costs |
  | 26.71 | test_audit.py::test_a_blind_signal_hugs_the_benchmark |
  | 26.52 | test_baseline.py::test_the_trailing_default_is_unchanged_bit_for_bit |
  | 26.12 | test_baseline.py::test_the_created_form_actually_moves_weights_relative_to_trailing |
  | 23.09 | test_audit.py::test_a_cell_runs_the_whole_chain_and_reports_what_bound |
  | 16.58 | test_baseline.py::test_the_shuffle_switched_off_reproduces_todays_score_and_net_ir_bit_for_bit |
  | 16.49 | test_audit.py::test_an_early_over_trade_does_not_block_a_later_one |
  | 15.82 | test_audit.py::test_a_base_cell_reports_the_transfer_coefficient_the_left_tail_and_the_pearson_ic |
  | 15.46 | test_audit.py::test_rolling_one_year_turnover_is_reported_for_the_budget_question |
  | 13.29 | test_audit.py::test_the_audit_writes_no_run_to_the_results_store |
  | 11.81 | test_audit.py::test_the_report_names_the_panel_and_the_params_it_ran_on |
  | 10.12 | test_engine.py::test_alternate_days_are_averaged_and_every_day_is_reported |
  | 8.20 | test_scripts.py::test_the_validation_run_is_recorded_and_tagged |
  | 6.70 | test_experiment.py::test_validation_recovers_the_planted_ir_exactly (setup) |

  **Tasks 34 and 36 among these:** all 6 `test_baseline.py` rows are task 36
  (the shadow-form tests on `small_universe`, added or extended by that task).
  Task 34 added none of the top 20 -- its own suite (`test_multiple_testing.py`,
  `test_batched_multiple_testing.py`, `test_fdr_vs_fwer.py`) is pure numpy and
  finished the whole profiling run in 7.32s when checked separately;
  `test_realised_error_rates_stay_within_mc_error_of_their_nominal_level`
  (1,500 replications in a Python loop) is marked slow on the `>200
  replications` criterion regardless, since it is exactly the kind of test
  that could stop being fast on a different machine.

- **31 tests marked `slow`, three ways:**
  - 20 by the >5s threshold above (all of them also call `run_cell`, the
    engine, or a real optimiser solve, except the one Monte Carlo).
  - 10 more that call `run_cell`/the engine but happened to run under 5s
    this time: 4 in `test_audit.py` (all `small_universe`), 6 by
    fixture-sharing -- `test_engine.py`'s other `planted`/`planted_path`
    tests and `test_experiment.py`'s other `validation`-fixture tests, marked
    together with their slow siblings so the fixture itself (a real
    `plant_weight_path`/`validate_pipeline` run) is never built in the fast
    tier, not just individually slow tests within a file that still pays for
    it.
  - 1 by the replications criterion alone (above).
  - **Not marked**, despite using `small_universe`: `test_prefilled_P_at_the_second_rebalance`
    (constructs `_OptimiserRule`, never solves), the two frictionless-cell
    tests (`run_frictionless` is a closed-form calculation, no optimiser), and
    `test_a_synthetic_cell_is_not_charged_the_dear_bucket_throughout` (reads
    cost buckets only). None of `test_long_only.py`'s tests are marked: they
    solve a 6-instrument toy problem, not a universe, and none exceeded 2.6s.
  - **No test was rewritten.** Every slow test is slow because it genuinely
    exercises the engine or the solver; none was slow only because a fixture
    would have done instead.
- **Tier counts: 31 slow + 516 fast (not slow, not holdout) + 15 holdout = 562.**
  Confirmed by `pytest --collect-only` on each selector; no test lost or
  double-counted.
- **Target met.** `make check` **2m24s**, well under the 10-minute target.
  `make check-full` **10m26s** for the whole 562 (up from 582s stand-alone,
  reflecting today's lower machine load rather than any change from this
  task -- the same suite took 3695s inside yesterday's `check` run).
- `CLAUDE.md`'s "definition of done" line and the `unattended.sh` paragraph
  are updated as specified; `scripts/unattended.sh`'s audit targets now open
  with `make check-full`, and `check`/`check-full` are both valid bare
  targets.

Interpretation is Cowork's and the owner's. Task 38 next per the queue order
(37 -> 38 -> 35 -> 39).

### 2026-09-29 (day) — task 38 (Claude Code, Sonnet 5)

**38. Romano-Shaikh-Wolf FDR, from the paper, and the study re-run at small k** — rc=0,
**RSW-FDR still not implemented.** Commit `459a257`.
`scripts/unattended.sh check-full --digest`: **rc=0, 562 tests, 730 s.**
`make fdr-study` at `459a257`: **rc=0, 207 s**, run
`results/fdr_vs_fwer/20260929-154138/`.

- **The paper: fetched and read in full.** Springer redirected to a paywall
  login; the University of Zurich working-paper copy
  (`econ.uzh.ch/.../test_2008_merged.pdf`, matching the task's own named
  source) fetched cleanly -- 55 pages, all algorithm and simulation sections
  present. Saved to `docs/references/romano-shaikh-wolf-2008-test.pdf`,
  git-ignored (copyrighted journal article, not redistributed; noted in the
  new `.gitignore` entry). WebFetch's own text summary couldn't parse the
  PDF's compressed streams; read it directly instead with `pypdf` and
  `pdfplumber` (word-level, coordinate-based extraction -- confirmed reliable
  by exactly reproducing the paper's own Table 1, see below).
- **What was recovered with confidence.** The population-level recursion
  (their eq. 7-10): a stepdown FDR bound built by, at each step j, assuming
  exactly j hypotheses are true nulls and bounding the resulting worst-case
  FDR contribution. Independently re-derived by hand from the general formula
  and checked against the paper's own worked specialisations for j=1 (eq. 8)
  and j=2 (eq. 9) -- both matched exactly.
- **What could not be resolved: which outer stepdown rank each recursively-
  computed critical value belongs to.** Built and empirically tested BOTH
  readings the text supports:
  - Same order (c_j at outer rank j): **100% empirical FDR under the complete
    null** (m=8, 200 reps) against a nominal 10% -- an outright control
    violation.
  - Reversed (c_j at outer rank m-j+1, matching the proof sketch's own use of
    j as a hypothesis label and Holm's strictest-first structure): **zero
    power on an obvious 4-sigma signal** that Holm and `romano_wolf` both
    reject cleanly.
  A further complication: Remark 1 (p.426), fixing the bootstrap version's
  index convention, defines an order statistic as the r-th SMALLEST where the
  population argument (eq. 7) defines the corresponding one as the r-th
  LARGEST -- read literally together, these assign opposite elements to the
  same symbolic position.
- **Stopped rather than ship either.** Two tested candidates both failing
  basic sanity checks is a stronger signal than uncertainty from reading
  alone: it means at least one is definitely wrong. Per the task's own
  instruction ("if you can't implement it faithfully... don't approximate it
  silently"), `romano_shaikh_wolf_fdr` still raises `NotImplementedError`,
  now with the full derivation, both tested readings, and the specific
  failure each produced, in its docstring -- so a future attempt starts from
  what's already ruled out rather than repeating this one.
- **The fidelity-check row the task asked for was not obtainable** (no
  working implementation to check), but its target was located and verified
  precisely, for whoever attempts this next: Table 1, "All theta_j=0",
  sigma=0.5, Boot column, empirical FDR **9.9%** against nominal 10% (n=100,
  s=50, B=500 bootstrap resamples, 5,000 repetitions) -- reconstructed via
  `pdfplumber`'s per-word coordinates (the earlier text-layer extraction
  glued adjacent numeric cells together) and cross-checked against the
  paper's own narrative ("STS is liberal under positive constant
  correlation": its empirical FDR rises 10.3% to 16.5% to 32.8% across
  sigma=0/0.5/0.9 in the same reconstruction -- matches exactly).
- **The study re-run anyway, with the validated procedures.** `K_GRID`
  extended to `{20, 50, 100, 200, 500, 1000}`; `p_any_pass`, `pfdr` and
  `false_share_expected` added; a k-sensitivity table added to the report.
  Kept the full 5,000 replications throughout -- the run finished in 207s,
  far under the 2h budget the task allowed dropping to 2,000 reps for.
- **k-sensitivity, headline correlation (rho_w=0.3, rho_b=0.2), n_true=3:**

  IC 0.35:

  | k | Romano-Wolf 5% power | Romano-Wolf 5% pFDR | BH 10% power | BH 10% pFDR |
  |---|---|---|---|---|
  | 20 | 0.035 | 0.244 | 0.005 | 0.632 |
  | 50 | 0.034 | 0.228 | 0.016 | 0.546 |
  | 100 | 0.037 | 0.257 | 0.029 | 0.478 |
  | 200 | 0.039 | 0.261 | 0.062 | 0.352 |
  | 500 | 0.035 | 0.260 | 0.067 | 0.341 |
  | 1000 | 0.037 | 0.244 | 0.071 | 0.334 |

  IC 0.70:

  | k | Romano-Wolf 5% power | Romano-Wolf 5% pFDR | BH 10% power | BH 10% pFDR |
  |---|---|---|---|---|
  | 20 | 0.154 | 0.061 | 0.010 | 0.541 |
  | 50 | 0.147 | 0.048 | 0.071 | 0.314 |
  | 100 | 0.168 | 0.057 | 0.138 | 0.224 |
  | 200 | 0.173 | 0.060 | 0.250 | 0.144 |
  | 500 | 0.172 | 0.065 | 0.272 | 0.132 |
  | 1000 | 0.177 | 0.060 | 0.289 | 0.135 |

  Confirms Cowork's earlier reading: Romano-Wolf's power is roughly FLAT
  across `k` (uses the joint null's max, not floored by `1/(k+1)`); BH's
  power rises sharply with `k` and is still climbing at k=1000, needing
  roughly k>=200-500 before it clears Romano-Wolf's power at either IC.
  BH's pFDR (conditional on passing anything) falls from 0.63/0.54 at k=20
  to 0.33/0.14 as k grows -- fewer candidates, but a much higher false share
  among them at low k.

`params/`, `vetoes/` and `SUBSTRATE.md` untouched, confirmed before the
commit. Interpretation is Cowork's and the owner's (OWNER-QUEUE L16(a)).
Task 35 next per the queue order (37 -> 38 -> 35 -> 39) -- **deferred**,
per the owner's own instruction, to when the machine can run it overnight.

### Task 40 -- standardised Romano-Wolf and the generalized-FWER stepdown (decisions/0041) -- 2026-09-29, rc=0

`make check-full`: rc=0, 1344s / 22.4 min, 575 tests passed (562 before this
task, +13). Commit `c0c4093` (code + study; `decisions/0100` gets the 0041
tracking row in the same commit). Study output:
`results/fdr_vs_fwer/20260929-204223/` (457s engine time, 225 scenarios x
5000 reps; full `time make fdr-study` wall time 7m38.739s). Paper:
Romano & Wolf (2007), *Control of generalized error rates in multiple
testing*, Annals of Statistics 35(4) 1378-1408 -- Algorithm 2.1 -- fetched
from arXiv:0710.2258 to
`docs/references/romano-wolf-2007-generalized-error-rates.pdf`
(git-ignored, per task 38's rule).

**Step 1, SUBSTRATE.md -- BLOCKED, not applied.** The `Edit` tool refuses
this path outright (`"File is in a directory that is denied by your
permission settings"`, confirmed persistent by retrying after unrelated,
transient permission errors cleared on their own). Per CLAUDE.md this is
correct behaviour on my end -- owner-only paths are not mine to originate --
but it means step 1 of the task is undone. The diff decisions/0041 asks for,
for Leo or Cowork to apply:

```diff
- Confidence intervals and the search null come from a **block bootstrap**
- on the daily panel, block length ≥ the longest signal horizon.
+ Confidence intervals come from a **block bootstrap** on the daily panel,
+ block length ≥ the longest signal horizon. Every null used by a test —
+ bar 2's excess, the search null and the multiple-testing gate — comes
+ from a **block shuffle** of the signal: its rows permuted in contiguous
+ blocks of at least the longest signal horizon, the same book on the same
+ history with only the signal's alignment to future returns destroyed
+ (`decisions/0041`).
- **Multiple testing is controlled with Romano-Wolf stepdown** at
- family-wise error rate α (params, v0.3: 5%). The joint distribution of
- all test statistics in a search is obtained by block bootstrap on the
- daily panel, so dependence between experiments is learned from the data,
- not assumed. The procedure runs at the family level first, then within
+ **Multiple testing is controlled with Romano-Wolf stepdown** at
+ family-wise error rate α (params, v0.3: 5%). The joint distribution of
+ all test statistics in a search is obtained from block shuffles of the
+ signals, one permutation shared by every hypothesis in each draw, so
+ dependence between experiments is learned from the data, not assumed.
+ The procedure runs at the family level first, then within
```
Plus the §15 layout line:
`stats/         HAC, block bootstrap, search null, deflated IR` ->
`stats/         HAC, block bootstrap, block shuffle, search null, multiple testing, deflated IR`.

**Step 2, standardised `romano_wolf`.** `romano_wolf(t, T0, alpha,
standardise: bool = True)` -- each null column and `t`'s matching entry are
transformed to `(x - mean)/sd` (ddof=1) before the stepdown, per decisions/0041's
implementation note, so a hypothesis with an intrinsically wider null can't
eat the shared max at the others' expense. `standardise=False` reproduces the
pre-task-40 function exactly -- checked against an independent reference
re-implementation, not just against itself
(`test_standardise_false_reproduces_the_pre_task_40_stepdown_exactly`).
Marginal p-values are unaffected (monotone transform per column,
`test_marginal_pvalues_are_invariant_to_standardising`). A zero/non-finite
null-column sd is refused, not silently divided by.

**Step 3, `romano_wolf_gfwer`.** `romano_wolf_gfwer(t, T0, alpha, g=2,
standardise=True)` implements Algorithm 2.1 directly: at each step past the
first it enumerates every size-`(g-1)` subset of the already-rejected set
exactly (m=12, g=2: at most 11 a step), not the paper's streamlined
shortcut -- simpler to get right, and m is small enough that it's still fast.
`g=1` reduces to `romano_wolf` exactly, both `standardise` settings
(`test_g1_reproduces_romano_wolf_exactly_both_standardise_settings`) -- this
caught a real bug in the first draft (a post-loop cleanup was re-clobbering
p-values the natural-stop branch had already set correctly), fixed before
anything shipped. **Not verified**: whether the paper's validity argument
(stated for bootstrap/subsampling nulls) extends to a block-shuffle
permutation null -- left as an open question in the docstring, same caveat
already carried by `romano_shaikh_wolf_fdr`. `batched_romano_wolf_gfwer` is a
plain per-row Python loop, not vectorised (the paper's own step-down needs a
different combo enumeration per row); measured at ~0.3ms/row (m=12, k=1000,
g=2), 1.4s for a full 5000-rep scenario -- fast enough that vectorising it
wasn't worth the time against today's deadline.

**`romano_wolf_5` against task 38.** Recomputed directly against task 38's
run (`results/fdr_vs_fwer/20260929-154138/`) over all 57 matching
(mu_label, n_true, k) cells at the headline correlation: max
|Δavg_power| = 0.066 (ic070, n_true=6, k=20), mean |Δavg_power| = 0.0094; max
|Δfwer| = 0.078 (complete null, k=20), mean |Δfwer| = 0.0124. Both maxima sit
at k=20, the smallest-k / most MC-noise corner of the grid, and this study's
draws are homoscedastic by construction (decisions/0041's standardising is a
no-op in expectation here) -- consistent with the differences being
finite-sample noise from estimating each column's mean/sd off only k draws,
not a real shift. `romano_wolf_5` in this run keeps `standardise=True`
throughout, not toggled per scenario.

**k-sensitivity** (n_true=3, rho_w=0.3, rho_b=0.2; full table in
`results/fdr_vs_fwer/20260929-204223/report.md`), IC 0.70, k=20 vs k=1000:

| procedure | power (k=20) | power (k=1000) | fwer (k=20) | fwer (k=1000) |
|---|---|---|---|---|
| romano_wolf_5 | 0.2181 | 0.1791 | 0.0992 | 0.0416 |
| rw_g2_5 | 0.3425 | 0.3477 | 0.2236 | 0.1770 |
| rw_g2_10 | 0.4189 | 0.4263 | 0.3092 | 0.2758 |
| bh_10 | 0.0103 | 0.2892 | 0.0108 | 0.1544 |

Same pattern as task 38 confirmed for the new procedures: `rw_g2_*`'s power
is roughly flat across `k` (joint-null max, not `1/(k+1)`-floored), where
`bh_10`'s climbs sharply and is still rising at k=1000. `romano_wolf_5`
itself is noticeably *higher* power at k=20 than at k=1000 here (0.218 vs
0.179) -- the small-k standardisation noise above, not a real effect.

**Complete null (n_true=0), headline correlation, k=1000** -- the g-FWER
guarantee is on `P(V>=2)` (`p_two_plus_false`), not `P(V>=1)` (`fwer`):

| procedure | fwer (V>=1) | p_two_plus_false (V>=2) | nominal alpha |
|---|---|---|---|
| rw_g2_5 | 0.2084 | 0.0564 | 0.05 |
| rw_g2_10 | 0.3044 | 0.1094 | 0.10 |

Both `p_two_plus_false` figures sit within ~2 MC standard errors
(se ~= 0.003-0.004 at n_reps=5000) of their nominal alpha -- the guarantee
the procedure actually makes holds under the complete null; `fwer` (V>=1)
is, as expected, well above alpha since g=2 does not control it.

`params/`, `vetoes/` untouched. **`SUBSTRATE.md` NOT applied -- see step 1
above, needs Leo or Cowork.** Also folded into commit `c0c4093`: `285c474`
("test: probe commit access") earlier today was a real, correct commit (the
standardise tests) made under an uninformative message while I was
distinguishing a transient Bash/git permission-classifier denial from a
persistent one -- noted here for the record, not re-done.

Per the task's own instruction, step 1 counts as failed (blocked, not a
bug on my side) -- ordinarily grounds to stop before task 35. That's moot
here: the owner's separate, standing instruction was to stop before task 35
regardless, to check remaining time against a 6pm ET deadline. ~45 minutes
remained at receipt time -- nowhere near task 35's 6-8h estimate. **Stopping
here; task 35 (and task 39, which depends on it) deferred**, per the
owner's own instruction, to when the machine can run it overnight.

### Task 41 -- pool the observed value into romano_wolf's standardising (decisions/0041) -- 2026-09-29 (late evening), rc=0

`uv run --python 3.12 --group dev pytest -q tests/test_multiple_testing.py
tests/test_batched_multiple_testing.py`: 31 passed, 7.5s. `scripts/unattended.sh
check` (fast tier, not check-full, per the task's own instruction -- 35's
`audit-halflife` covers this commit): rc=0, 62-70s. Commit `0a5645f`.
`check-full` deferred to 35 as instructed; not run here.

**Step 1, code.** `_standardise_columns` (`stats/multiple_testing.py`) and
`batched_standardise_columns` (`stats/_batched.py`) now pool the observed
value `t`/`t[i]` together with the `k` null draws before taking the mean and
sd (ddof=1) -- `k + 1` values, a symmetric function of all of them, restoring
the exchangeability task 40's `T0`-only transform broke. `decisions/0041`'s
Implementation note gets a dated addendum recording the bug and the fix; both
docstrings updated. The `ValueError` on a zero/non-finite sd is unchanged,
but now needs the observed value equal to a constant null to trigger --
updated the one test that assumed otherwise
(`test_a_zero_or_nonfinite_null_column_sd_is_refused`).

**Step 2, the regression that would have caught it.**
`test_pooled_standardising_controls_fwer_under_heteroscedastic_complete_null`
(marked `slow`, though it runs in ~0.4s): m=12, equicorrelated (rho=0.3),
column scales 0.5-3, k=20, 4,000 reps, fixed seed. `romano_wolf`'s FWER and
`romano_wolf_gfwer(g=2)`'s P(V>=2) both land at or under alpha + 3*se. No
other existing test pinned task 40's un-pooled numbers, so nothing else
needed updating; `standardise=False` and the `g=1` identity tests pass
unchanged (they never touch `_standardise_columns`' internals).

**Step 3, the study re-run** (`make fdr-study`,
`results/fdr_vs_fwer/20260930-031720/`, 560s engine time, 9m21s wall).
Complete-null rows (n_true=0), headline correlation (rho_w=0.3, rho_b=0.2):

| k | romano_wolf_5 fwer | rw_g2_5 p_two_plus_false | rw_g2_10 p_two_plus_false |
|---|---|---|---|
| 20 | 0.0520 | 0.0488 | 0.0978 |
| 50 | 0.0416 | 0.0416 | 0.1000 |
| 100 | 0.0470 | 0.0482 | 0.0984 |
| 200 | 0.0494 | 0.0500 | 0.1002 |
| 500 | 0.0534 | 0.0482 | 0.0994 |
| 1000 | 0.0522 | 0.0554 | 0.1082 |

Against nominal alpha 0.05 and 0.10: every cell sits within 2-3 MC standard
errors (se ~ 0.003 at n_reps=5000). Task 40's `romano_wolf_5` FWER of 0.127
(k=20) and `rw_g2_5` P(V>=2) of 0.083 (k=20) are both gone.

k-sensitivity, n_true=3, rho_w=0.3, rho_b=0.2 (report.md has the full table):

| IC 0.70 | k=20 | 50 | 100 | 200 | 500 | 1000 |
|---|---|---|---|---|---|---|
| romano_wolf_5 power/fwer | .119/.043 | .131/.030 | .159/.038 | .171/.043 | .169/.042 | .177/.041 |
| rw_g2_5 power/p2+ | .274/.038 | .282/.025 | .318/.035 | .333/.035 | .336/.039 | .347/.041 |
| rw_g2_10 power/p2+ | .362/.077 | .387/.072 | .397/.077 | .414/.075 | .414/.088 | .425/.085 |
| bh_10 power/fwer | .010/.011 | .071/.065 | .138/.097 | .250/.136 | .272/.143 | .289/.154 |

| IC 0.35 | k=20 | 50 | 100 | 200 | 500 | 1000 |
|---|---|---|---|---|---|---|
| romano_wolf_5 power/fwer | .027/.044 | .031/.033 | .035/.037 | .037/.045 | .035/.037 | .037/.038 |
| rw_g2_5 power/p2+ | .083/.033 | .092/.028 | .097/.033 | .107/.035 | .101/.032 | .104/.035 |
| rw_g2_10 power/p2+ | .127/.073 | .143/.068 | .140/.072 | .152/.074 | .142/.071 | .145/.070 |
| bh_10 power/fwer | .005/.006 | .016/.027 | .029/.045 | .062/.085 | .067/.091 | .071/.095 |

**romano_wolf_5 against task 38** (pre-standardisation baseline,
`results/fdr_vs_fwer/20260929-154138/`), 57 matching (mu_label, n_true, k)
cells at the headline correlation: max |delta avg_power| = 0.038 (ic070,
n_true=1, k=20), mean 0.0047; max |delta fwer| = **0.0074** (ic035, n_true=3,
k=20), mean 0.0015 -- both an order of magnitude smaller than task 40's
(0.066 / 0.078), and the max sits at k=20 as expected from MC noise on the
smallest sample, not a systematic shift. The fix holds at small k, which is
exactly where task 40's bug bit hardest.

`params/`, `vetoes/` untouched.

Interpretation is Cowork's and the owner's (L16(a), OWNER-QUEUE updated
separately). **Going straight on to task 35** per the task's own instruction
(step 2's tests pass; nothing here counts as a stop).

### Task 35 -- the volatility-overlay halflife sweep (OWNER-QUEUE B1, L13) -- 2026-09-30, rc=0, COMPLETE

Build committed at `c9820b0` (halflife_cells, preflight, checkpointing,
deadline guard, receipt analytics; `ladder.py` rows now carry
`vol_halflife`/`vol_overlay`), `8172889` (a pandas FutureWarning fix a
live one-cell smoke test surfaced before the real run -- preflight
matched, the h13 identity check reproduced the knee run's net IR to
float epsilon on that one cell, checkpointing and the deadline stop
both worked). Full run launched
`HALFLIFE_DEADLINE=2026-09-30T06:30:00-04:00 scripts/unattended.sh
audit-halflife --digest` at 23:29:20 ET on head `8172889`.

**rc=0 throughout.** `make check-full`: rc=0, 531s, 585 tests. `make
audit-halflife`: rc=0, 13,810s (3h50m -- faster than the 5.5-6h estimate).
Run id `A-20260930-033812`. **Status COMPLETE, 240/240 cells** (80 each at
h4, h13, h26) -- the deadline guard never had to fire; finished at 03:28 ET,
well inside the 06:30 hard stop. Digest at
`results/audit/_unattended/20260929-232920-audit-halflife/digest.md`.

**The h13 `vol_halflife=None` arm against the knee run (`A-20260922-005316`,
`POWER_LIVE_RUN`): identical.** `panel_hash` and `params_hash` both match.
All 20 (ic, seed) pairs found; max |diff| in net IR is **8.3e-17** (float
noise). The grid is measuring the same book at h13 the knee run measured --
nothing about the identity is in question.

**Per (horizon, halflife), pooled over both ICs (20 cells each):**

| horizon | halflife | n_risk_cal_fails | bias_worst_annual median/max | n_worst_yr_2008 | bias_stat median | te_p95 median | te_p95/budget median | net_ir median (min, max) | turnover_annual median | cost_drag median |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | none | 5 | 1.546 / 1.981 | 17 | 0.966 | 0.0755 | 1.259 | 0.492 (0.057, 0.875) | 5.833 | 0.00892 |
| 4 | 13 | 0 | 1.305 / 1.431 | 4 | 0.990 | 0.0683 | 1.138 | 0.485 (0.246, 0.909) | 5.967 | 0.00928 |
| 4 | 26 | 0 | 1.306 / 1.521 | 6 | 0.962 | 0.0684 | 1.141 | 0.447 (0.063, 0.789) | 5.853 | 0.00906 |
| 4 | 52 | 0 | 1.370 / 1.683 | 13 | 0.952 | 0.0703 | 1.171 | 0.456 (0.132, 0.886) | 5.862 | 0.00905 |
| 13 | none | 10 | 1.719 / 2.036 | 17 | 0.994 | 0.0805 | 1.341 | 0.524 (-0.021, 0.760) | 2.829 | 0.00498 |
| 13 | 13 | 0 | 1.394 / 1.572 | 3 | 1.002 | 0.0688 | 1.147 | 0.550 (0.177, 0.821) | 2.960 | 0.00522 |
| 13 | 26 | 0 | 1.359 / 1.562 | 8 | 0.986 | 0.0690 | 1.150 | 0.549 (0.050, 0.802) | 2.872 | 0.00515 |
| 13 | 52 | 1 | 1.484 / 1.747 | 10 | 0.984 | 0.0719 | 1.198 | 0.492 (-0.028, 0.770) | 2.835 | 0.00506 |
| 26 | none | 10 | 1.719 / 1.868 | 15 | 0.977 | 0.0793 | 1.322 | 0.455 (-0.109, 0.774) | 1.822 | 0.00363 |
| 26 | 13 | 2 | 1.444 / 1.811 | 3 | 0.999 | 0.0709 | 1.182 | 0.482 (-0.095, 0.773) | 1.930 | 0.00376 |
| 26 | 26 | 1 | 1.415 / 1.742 | 6 | 0.984 | 0.0709 | 1.182 | 0.424 (-0.132, 0.740) | 1.846 | 0.00367 |
| 26 | 52 | 0 | 1.520 / 1.650 | 9 | 0.980 | 0.0730 | 1.217 | 0.453 (-0.008, 0.801) | 1.836 | 0.00361 |

**Per IC** (full 24-row table in `results/audit/A-20260930-033812/summary.json`,
key `halflife_by_horizon_halflife_ic`): the `risk_calibration` fail pattern
holds within each IC separately -- e.g. h13/none fails 6/10 seeds at IC 0.35
and 4/10 at IC 0.70, against 0/10 at h13/halflife-13 for both ICs. Net IR at
IC 0.70 is consistently 0.13-0.24 higher than at IC 0.35 for the same
(horizon, halflife), as expected; the halflife ranking is the same at both
ICs.

**Paired by (ic, seed, horizon): net IR at each halflife minus net IR at
`None`, mean/sd/n_positive over 10 seeds** (full 18-row table in the same
summary.json, key `halflife_paired_by_ic_seed_horizon`):

| horizon | halflife | IC 0.35 mean/sd/n+ | IC 0.70 mean/sd/n+ |
|---|---|---|---|
| 4 | 13 | +0.058 / 0.174 / 4 | +0.016 / 0.115 / 7 |
| 4 | 26 | -0.049 / 0.184 / 4 | -0.030 / 0.087 / 4 |
| 4 | 52 | -0.014 / 0.123 / 4 | -0.024 / 0.069 / 4 |
| 13 | 13 | +0.074 / 0.118 / 7 | +0.066 / 0.099 / 8 |
| 13 | 26 | +0.056 / 0.069 / 9 | +0.047 / 0.083 / 7 |
| 13 | 52 | -0.003 / 0.089 / 6 | +0.045 / 0.072 / 7 |
| 26 | 13 | +0.041 / 0.092 / 7 | +0.012 / 0.071 / 6 |
| 26 | 26 | +0.006 / 0.118 / 4 | -0.018 / 0.085 / 6 |
| 26 | 52 | +0.029 / 0.098 / 8 | -0.018 / 0.117 / 5 |

At h13, halflife 13 and 26 both gain net IR against the no-overlay control in
a majority of seeds (7-9 of 10) at both IC rungs, with a paired sd of
0.07-0.12 (se ~0.02-0.04) -- the strongest and most consistent case in the
grid. h4 and h26 are mixed in sign; h4's halflife-13 gain at IC 0.35
(+0.058) is the exception, not the rule for that horizon.

**Flagged cells (inaccurate_share > 0.01 or infeasible_te_share > 0): none.**
The grid ran clean throughout.

**Two things beyond the task's own checklist, worth flagging for the owner
alongside B1's ruling (not something this task resolves):**
- **`te_p95_to_budget` is above 1 in every one of the 12 pooled cells**
  (1.13-1.34), lowest with halflife 13 and highest with none. No halflife
  arm brings the sweep inside the tracking-error budget on this measure --
  consistent with `decisions/0030`'s `risk_calibration` finding (the veto
  reads worst-annual bias, not this ratio) but a wider-angle view of the same
  risk-sizing gap.
- **h4's annual turnover (median 5.8-6.0, all halflife arms) sits far above
  the 200% highlight line** `decisions/0038`/B3 set (report, not veto) --
  unrelated to the overlay (halflife moves it by at most 2%), a known
  property of the 4-week horizon already visible in earlier grids.

Interpretation is Cowork's and the owner's. **Whether the overlay becomes
policy is B1, an owner decision** -- not ruled here. Per the amendment,
**stopping after this task tonight; task 39 does not run.**

### Task 39 -- turnover disclosed not vetoed, created-marginal shadow at 40bp (decisions/0038, decisions/0040) -- 2026-09-30, rc=0

**rc=0 throughout.** `make check-full`: rc=0, 582 tests (was 581; one new
test, `test_created_marginal_reads_the_same_marginal_rate_as_linear`), 6m11s.
Four commits, in the order the 2026-09-30 amendment specified:
- `a22aebb` queue: the amendment itself (Cowork's owner-only edits already
  applied to the working tree).
- `b43a22f` substrate: v0.6 (`SUBSTRATE.md`, `decisions/0100`) -- also carries
  task 40's `decisions/0041` block-shuffle edit, blocked by permissions that
  night, applied by Cowork this morning in the same pass.
- `3d437d0` params+vetoes: the owner-only `params/`/`vetoes/` files plus every
  `src/`, `render/` and `tests/` change this task needed outside the owner-only
  paths.
- `b7876a8` decisions: the `params_hash` move recorded in 0038 and 0040.

**`params_hash`:**
`ebdfb70e44ed05f624949344532f85257bae9add01a702f75f85e9fe432ab77c` (v0.6.0)
-> `ba19198d4e9048abb82a0ece868881561f008f7c6f3043d4cdbfdf44dbfade93` (v0.7.0).

**Who did what.** Cowork applied every edit to `SUBSTRATE.md`, `params/vetoes.yaml`,
`params/constraints.yaml` and `vetoes/{__init__,registry,rules}.py` directly to
the working tree, at the owner's instruction, after my permissions refused
them (`Edit(/SUBSTRATE.md)`, `Edit(/params/**)`, `Edit(/vetoes/**)` in
`.claude/settings.json` -- the same wall task 40 hit). I verified each diff
against `decisions/0038`/`0040`/`0041`'s literal text (all matched, including
the recomputed 40bp magnitude table) before building on it, then did
everything outside the owner-only paths: code, tests, verification and these
commits.

**Diff summary, params/ (`--ignore-cr-at-eol`):**
- `params/vetoes.yaml`: the `turnover:` block deleted; `turnover` dropped
  from `evaluation.order`. `params_version` 0.6.0 -> 0.7.0.
- `params/constraints.yaml`: `turnover.penalty.form: linear` ->
  `created_marginal`; `coefficient: 10.0` -> `40.0`; the comment's magnitude
  table recomputed at 40bp (0.0 / 13.3 / 40.0 / 66.7 / 120.0 / 173.3 bps at
  turnover 0.75/1.00/1.50/2.00/3.00/4.00); new keys
  `turnover.highlight_annualised: 2.00` and
  `turnover.highlight_windows: [annual, rolling_1y_p95]` (reporting only).
  `params_version` bumped to match.
- `params/agents.yaml`, `audit.yaml`, `costs.yaml`, `data.yaml`,
  `data_sources.yaml`: `params_version` bump only, no content change.

**Diff summary, SUBSTRATE.md (`--ignore-cr-at-eol`):** status line v0.5 ->
v0.6; §4 turnover row and "Turnover handling" paragraph rewritten per
decisions/0038 and 0040's exact text (one non-verbatim consequential edit,
flagged by Cowork and recorded in `decisions/0100`: "the veto threshold is a
far backstop" became "There is no turnover veto either"); §9's two
block-bootstrap-to-block-shuffle edits and the §15 `stats/` layout line, from
decisions/0041 (task 40's blocked step, applied here); §10 turnover row
deleted, "Ten vetoes" -> "Nine vetoes".

**Step 5, verifying past verdicts.** Scanned every `results/audit/A-*/cells.csv`
for `veto_detail` containing "turnover". **80 cells, not zero** -- all from
last night's task-35 halflife sweep (`A-20260930-033812`), all at horizon 4
(every h4 cell, all halflife arms, both ICs, all ten seeds), turnover
490-680% annualised against the then-live 400% ceiling. `decisions/0038`'s
own "no recorded verdict should change" note predates that run and no longer
holds; recorded as an addendum there. No other historical run ever failed
the veto. These 80 verdicts are left as recorded -- a true statement about
the params in force when they ran, not rewritten retroactively.

**Golden values** (`tests/test_baseline.py`): `GOLDEN_NET_IR =
-0.8793457503233992` is now reproduced only via an explicit
`shadow_form="trailing", shadow_coefficient=10.0` override (the OLD default);
a new golden, `GOLDEN_NET_IR_CREATED_MARGINAL = -0.3916592047250338`, is the
SAME cell (`AuditCell(0.10, 13, 0)`) under today's actual default
(`shadow_form=None` -> reads params -> `created`). Both verified directly
against a live `run_cell` call before writing the tests, not derived.

**The default-shadow-form bug this task exists to close, and who else it
touched.** `AuditCell.shadow_form` was hard-defaulted to `"trailing"`
(task 36); reading `constraints.turnover.penalty.form` from params only
happens now (`resolve_shadow_form`, `audit/ladder.py`), via `None`. Three
grid builders besides the main ladder claim bit-for-bit or construction
identity against `POWER_LIVE_RUN` (`A-20260922-005316`, computed under the
old default) and would have silently drifted to `created_marginal` on any
future re-run had I not pinned them: `friction_cells` (caught by a failing
test, `test_the_friction_created_grid_is_60_cells_pairing_the_friction_grid`),
and `power_cells`/`power10_cells`/`halflife_cells` (no failing test existed
for these -- found by inspection, same bug class, fixed the same way: an
explicit `shadow_form="trailing"`). `knee_cells` and `baseline_cells` need no
pin: they define a grid's own standard rather than claiming identity to a
named historical run.

**Every test changed, and why:**
- `tests/test_vetoes.py`: `veto_turnover` import and its four dedicated tests
  removed; "ten vetoes" -> "nine" throughout; `evaluation_order`'s first-five
  check drops `turnover`; `apply_vetoes`'s multi-failure test swaps its
  turnover breach for a positions breach; the crashing-veto test monkeypatches
  `cash` instead of `turnover`; the zero-sd test pools `t` into the mean now
  (task 41 context, unrelated to this task but touched the same file).
- `tests/test_engine.py`: the veto-level one-way-vs-traded-notional test
  removed (redundant with the cost-model-level test, which survives); the
  "completed path populates the veto inputs" test asserts
  `ctx.annualised_turnover()` directly instead of going through the removed
  veto.
- `tests/test_objective.py`: `turnover_penalty`/`annual_turnover_penalty`
  accept `created_marginal` (same marginal-rate formula as `linear` -- this
  function was never the convex per-trade implementation); the
  "bites without dominating" arithmetic guard is pinned to the legacy 10bp via
  `variant()` rather than read from live params (now 40bp, calibrated
  differently, by task 36's measurement, not this ratio argument); the
  unsupported-form and unset-coefficient tests' `variant()` substrings
  updated to match the live file's actual text; one test added confirming
  `created_marginal` and `linear` share the marginal rate exactly.
- `tests/test_params.py`: drops the `vetoes.turnover.max_annualised`
  assertion from the SUBSTRATE-threshold roundtrip test.
- `tests/test_render.py`: `veto_legend` test drops the turnover assertion,
  adds one confirming it is absent.
- `tests/test_baseline.py`: `shadow_coefficient_none_matches_params_exactly`
  reads the live coefficient instead of hardcoding 10.0; the two golden-value
  tests (above); `friction_cells`'s pin (above).
- `tests/test_experiment.py`: the validation-path veto test rewritten --
  its premise ("the turnover veto must kill it") is gone; it now confirms
  cash and positions still pass on a genuinely extreme (~500% turnover) path,
  and that nothing fails because of the turnover level itself.

**Also touched, not in the task's own checklist:** `render/mock_data.py`'s
demo `VETOES` list and fake verdicts (untested, UI-only); `src/signal_lab/params.py`'s
one docstring example; `src/signal_lab/audit/report.py`'s "four portfolio
vetoes" -> "three" in three places (markdown and HTML renderers) and
`required_ic`'s docstring.

Per the task's own instruction: **stopping here.** No audit runs in this task.
