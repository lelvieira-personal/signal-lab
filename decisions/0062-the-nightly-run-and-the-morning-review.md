# 0062 — The nightly run and the morning review: Claude Code works released tasks headless, Cowork reviews each morning

**Status:** decided 2026-10-19 by the owner ("yes, write it on 0062 and
consider it approved"), including the per-task model of items 2, 4 and 6.
Drafted by Cowork on 2026-10-18.
No change to `params/`, `vetoes/` or `SUBSTRATE.md`. It changes how the lab is
run: `HANDOFF.md`'s contract, `CLAUDE.md`, two new files under `scripts/nightly/`,
one edit to `scripts/unattended.sh`, and `scripts/nightly/settings.json`. Plumbing only:
nothing here changes how a hypothesis is tested, judged or recorded.

## What the owner said

2026-10-16 (the setup prompt, Project doc `claude/autonomy-setup-prompt-2026-10-16.md`):
- "Take me out of the relay between Cowork and Claude Code ... I'm contacted
  only for owner decisions."
- "Claude Code runs nightly, headless. It may use my API key or my
  subscription."
- "A scheduled Cowork session reviews afterwards every morning: reads the new
  receipts, checks them against primary sources ... and acts."
- "Cowork may rule alone on: test fixes that change no expectation's meaning,
  clerical corrections (names, ids, paths, line endings, typos in records),
  and re-releasing a stopped task once the cause is fixed."
- "Everything else comes to me: anything touching `params/`, `SUBSTRATE.md`
  or `vetoes/`; a hypothesis's design (signal, direction, scope, data); a new
  data pull; any OWNER-QUEUE item; a golden that moves; a receipt that
  disagrees with a primary source in a way that changes a result."

2026-10-18, answering Cowork's design: "1) API key", "2) agree with
suggestion" (the worker sits outside `params/agents.yaml`, see item 4),
"3) yes" (the release line), "4) yes" (a canary task for the dry run),
"5) yes" (push and email), "6) yes" (move `git_key`), and on the old
scheduled task "Signal Lab — what needs Leo": leave it disabled.

2026-10-19, on whether Sonnet suits every task: "yes, write it on 0062 and
consider it approved" (the release line names the model per task; Sonnet is
the default).

## The decision

### 1. When and how the nightly run starts

Windows Task Scheduler starts it at **01:30 ET**, every night, with
`wsl.exe -d Ubuntu -u lelvieira --cd /mnt/c/AI/signal-lab -- bash -lc 'bash scripts/nightly/run.sh night'`
(and `day` for the addendum's second slot).
Settings: run only when the user is logged on (the "whether logged on or not"
setting is tried in the dry run and adopted only if it works), wake the
computer, run as soon as possible after a missed start, stop after 20 hours.
Cron inside WSL is not used: WSL is not running after a reboot or once idle, so
cron misses nights silently.

### 2. The release line: the only thing that starts a model call

`HANDOFF.md` carries exactly one line, at column 0, under `## Queue`:

    Nightly-release: <ids|none> @<YYYY-MM-DDTHH:MM> by=<owner|cowork> push=<yes|no>[ model=<sonnet|opus>][ long]

- `<ids>` is one task number or several in order, comma-separated (`60` or
  `60,61`); `none` means nothing is released.
- `@` is the time it was written, ET. **A stamp runs once.** The wrapper
  records every stamp it has run and skips one it has seen.
- `push=no` makes the wrapper deny `git push` to the session, whatever the
  task text says. `push=yes` lets a task push where its own text says so.
- `model=` picks the session's model (item 4). Absent means `sonnet`. Rule
  of thumb for whoever writes the line: `opus` for a task that builds new
  statistical or solver code from a spec or a paper, or that re-runs a stop
  whose cause was not clear; `sonnet` for commits, loaders with written
  rules, checks and descriptions.
- `long` lets a released task start a run of more than five hours (an audit).
  Without it, a task whose own text expects a longer run is stopped before
  the run starts, with a receipt.
- The prose queue notes stay as they are. The line decides whether the night
  starts. The task text decides what is done.

Who may write it: the owner, always. Cowork, only to re-release a stopped task
under item 8, and then with `by=cowork`, and `push=yes` only if the owner's
release of that task carried it. Cowork may set `model=` when it writes the
line; the monthly cap of item 4 bounds what that costs.

### 3. The wrapper's gate, before any model call

`scripts/nightly/run.sh` is plain bash. It exits 0, writing one line to its
log, unless all of these hold:
- the lock is free (item 5);
- there is exactly one release line, it parses, its ids are not `none`, and
  its stamp has not run;
- `.git/index.lock` does not exist;
- the month's nightly spend so far is under the monthly cap (item 4);
- the laptop is on mains power (best effort, through `powershell.exe`; if the
  check cannot run, the run proceeds).

An empty night makes no model call and costs nothing.

### 4. Transport, model and caps

- **The API key** (owner, 2026-10-18), read from
  `~/.config/signal-lab/nightly.env` (WSL home, mode 600, never in the repo)
  and set only for the one `claude` call. It is not exported to the shell, so
  `scripts/unattended.sh --digest` and interactive sessions are not billed by
  it. A dedicated Console key, with a spend limit on its workspace if the
  Console offers one (Cowork has not verified that it does).
- **Model, per release line:** `sonnet` is `claude-sonnet-5-5` (the default);
  `opus` is `claude-opus-5-5`, twice Sonnet's price per token ($4/$20 against
  $2/$10 per million, input/output, Anthropic's price page on 2026-10-18).
  Fable is not offered to the worker. No fallback model: an unavailable model
  fails the night rather than switching silently.
- **Caps, per run:** `--max-budget-usd` $6 with `sonnet`, $12 with `opus`;
  `--max-turns 250`; wall clock 18 hours (SIGINT, then a kill 10 minutes
  later).
- **Cap, per month:** the wrapper sums `total_cost_usd` over the month's runs
  and does not start one once the sum reaches **$100** (the build figure). The
  owner lowers it to **$30** when the build ends. The figure lives in
  `scripts/nightly/config.sh`; changing it is the owner's call.
- **Relation to `params/agents.yaml` and SUBSTRATE §14** (owner, 2026-10-18,
  "agree with suggestion"): the nightly worker is not one of §13's model
  roles, so `agents.yaml`'s per-run and per-cycle ceilings do not bind it, and
  `params/` is not changed. Its caps are the ones above, recorded here. Its
  spend counts toward the owner's monthly figure all the same: when the
  research cycle starts spending, the two share the $30.
- `total_cost_usd` is Claude Code's own estimate, not the bill.

### 5. One run at a time

- One `flock` file, `~/.locks/signal-lab.lock` in WSL's home (not on
  `/mnt/c`). `run.sh` holds it for the whole run.
- `scripts/unattended.sh` takes the same lock and exits 75 if it is held,
  unless its parent already holds it (`SIGNAL_LAB_LOCK_HELD=1`, set by
  `run.sh`). Today "one at a time" is only a convention.
- While a run lives, `run.sh` rewrites `results/audit/_nightly/RUNNING` every
  60 s with the stamp, the start time, the release line and the current HEAD,
  so Cowork, which cannot see WSL, can tell a live run from a dead one.
- Not covered: an interactive session the owner starts during a night run.

### 6. The session

    claude -p "$(cat scripts/nightly/prompt.md)" \
      --model "$MODEL" \
      --permission-mode dontAsk --permission-prompts none \
      --setting-sources project --settings scripts/nightly/settings.json \
      --strict-mcp-config \
      --max-turns 250 --max-budget-usd "$RUN_CAP" \
      --output-format stream-json --verbose

`$MODEL` and `$RUN_CAP` come from the release line's `model=` (item 4).

- `.claude/settings.json` (committed) still applies, deny list included.
  `--allowedTools` and `--disallowedTools` on the command line add what an
  unattended task needs (flags, because a `-p` run applies a repository's
  allow rules only in a folder trusted interactively): Edit and Write;
  `git add`, `git commit`; `git push origin main` exactly (removed when
  `push=no`); `make` and `uv run --python 3.12 --group dev`; and denies web
  tools and edits to `scripts/nightly/`, `.claude/`, `CLAUDE.md`,
  `SUBSTRATE.md`, `params/` and `vetoes/`.
- A pre-tool hook refuses any shell command that names `data/raw`,
  `data/snapshots`, `.env` or `git_key`. The Read deny rules do not stop
  `head data/raw/...`, and task 59's receipt records one such slip.
- `BASH_DEFAULT_TIMEOUT_MS=1200000` (20 minutes) and
  `BASH_MAX_TIMEOUT_MS=57600000` (16 hours). The default ceiling is 10
  minutes; the last full suite took 596 s.
- `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` = 1
  (`decisions/0048`) and `UV_PROJECT_ENVIRONMENT=$HOME/.venvs/signal-lab`.
- The prompt (`scripts/nightly/prompt.md`) tells it: nobody is there to
  answer; read `SUBSTRATE.md`, `CLAUDE.md` and the top of `HANDOFF.md`; work
  only the released ids, in order; stop at the first failure with a STOPPED
  receipt that says which column of item 8 the stop falls in, in Claude
  Code's reading; ask nothing; push only where the task says and the release
  allows.

### 7. What each run leaves

`results/audit/_nightly/<stamp>/` (git-ignored, under `results/audit/`):
- `status.txt`: start and end HEAD; the release line; the gate's result;
  `claude`'s rc and end reason (success, budget, turns, timeout); cost and
  turns; the number of denied tool calls; the commits made; any owner-only
  path a commit touched; `origin/main` after the run.
- `result.json`: the session's final result object only.
- `transcript.jsonl`: the whole session. **Cowork never reads it**, because a
  tool output inside it can hold vendor values. The owner can.

### 8. Who decides what

| | Cowork alone | Cowork prepares the decision, recommends, notifies the owner, and does nothing else on that thread |
|---|---|---|
| A test fix that changes no expectation's meaning | yes; ruling in the task's revision note and the Project | |
| Clerical: names, ids, paths, line endings, typos in records | yes | |
| Re-releasing a stopped task once its cause is fixed | yes; a new stamp, `by=cowork`, `push=yes` only if the owner's release had it | |
| A receipt that disagrees with a primary source clerically | yes; corrected in an update line under the receipt | |
| A missed night, a budget or turn stop, a killed run | reports; may re-release once if the cause was mechanical | if it happens twice for the same task |
| Anything touching `params/`, `SUBSTRATE.md`, `vetoes/` | | yes |
| A hypothesis's signal, direction, scope or data; a new data pull | | yes |
| Any OWNER-QUEUE item | may add or restate one, never answer it | yes |
| A golden that moves | | yes |
| A receipt that disagrees with a primary source in a way that changes a result | | yes |
| Writing a new task into `HANDOFF.md` | | yes |

When unsure which column a case belongs in, it is the right-hand one.

### 9. The morning review

A Cowork scheduled task, **06:47 ET daily**, folder `C:\AI\signal-lab`. Each
run starts fresh, so its prompt carries this record's rules. It:
- reads `status.txt` and `result.json` of every nightly run since the last
  review, the new receipts, and `RUNNING`;
- verifies against primary sources: `git log`, the `_unattended/` and run
  directories a receipt names, file times against the check's start, and the
  remote itself (`git ls-remote` from the cloud workspace, not the local
  `origin/main`);
- acts under item 8;
- writes `claude/nightly-review-<date>.md` to the Project, and refreshes its
  mirror copy;
- if `RUNNING` is fresh (under 5 minutes old), says nothing about that run
  unless it has passed the runtime the task itself states.

It needs the laptop awake with the Claude desktop app open at 06:47. If it
cannot reach the laptop, it says so in one line and stops.

### 10. Notifications

- A phone push when there is a decision for the owner, a failure, or a
  missed night (a released stamp with no run).
- An email to the owner, subject `[signal-lab] decision: <one line>`, for
  owner decisions only, with the options and Cowork's recommendation.
- A quiet morning sends nothing; the Project doc is the record.

### 11. Hygiene that lands with this

- `git_key` and `git_key.pub` move out of the repo folder into WSL's
  `~/.ssh` (owner, 2026-10-18; OWNER-QUEUE D5 closes). The owner moves them;
  Cowork checks the push still works from the next push receipt.
- `CLAUDE.md`'s digest list says "turnover against the 400% backstop". There
  has been no turnover veto since `decisions/0038`, and the highlight is at
  200%. Corrected with this change.
- The old scheduled task "Signal Lab — what needs Leo" stays disabled
  (owner, 2026-10-18).

### 12. Before it runs alone

One supervised run of each, on a canary task (owner, 2026-10-18, "4) yes"):
`make check` and a receipt, `push=no`. The review is run by hand right after.
Neither is left to run alone until the owner has read what both did.

## What this does not decide

- Anything about hypotheses, the gate, the bars, the data or the holdout.
- The research cycle of SUBSTRATE §13 (`scripts/nightly_cycle.py`), its
  transport or its budgets: `decisions/0007` and `params/agents.yaml` stand.

## How to undo it

Disable the Windows task and the Cowork task, and set the release line to
`none`. Nothing else depends on them.

---

## Addendum, 2026-10-19 (08:15 ET): the times follow the owner's day

**What the owner said.** The laptop is plugged in at the office from about
07:30-08:00 to 18:30, and at home from about 20:30 to 06:00; it is unplugged
while he commutes. "23:00 is late enough. It stays plugged in always when it
is turned on. Email timing is fine. Running things while at the office is
fine. Plus I maybe working from home on Wed and always on Fridays, so you can
also include long tasks on Thu evening."

**Why the times change.** The 06:47 review fell in the commute every day, and
a 01:30 start left 4.5 hours before the laptop is unplugged. The rest of this
record stands; these items replace what they name.

- **Item 1, two worker slots.** Task Scheduler starts `run.sh` at **23:00 ET**
  and at **12:30 ET**, every day, with the same gate (item 3). A stamp still
  runs once, so a task re-released at the 05:30 review runs at 12:30 the same
  day instead of waiting a night. *(The 12:30 slot is Cowork's reading of
  "running things while at the office is fine"; the owner may strike it.)*
- **Item 3, a last start.** The gate adds: no new task starts within 90
  minutes of the slot's end, which is **04:30** for the night slot and
  **17:00** for the day slot. A second released id that would start later
  waits for the next slot.
- **`long` (item 2): only on the night slot of Thursday, Friday and
  Saturday,** before a day the owner is at home, so a 14-hour audit started
  at 23:00 ends around 13:00 with the laptop still plugged in. A `long` line
  on any other slot waits for the next allowed night, unless the owner
  writes it himself (`by=owner`) for a night before a home day he names
  (for example a Wednesday at home).
- **Item 9, two reviews.** **05:30 ET** (at home, before the owner leaves;
  its decisions reach his phone for the commute) and **16:30 ET** (after the
  day slot, before he leaves the office). Each covers every run since the one
  before. A run still live (`RUNNING` under 5 minutes old) is reported only if
  it has passed the runtime its task states.
- **New, item 9: while a run is live, Cowork does not edit tracked files.**
  A worker run commits `HANDOFF.md` and may `git add` what a task names; a
  Cowork edit in the middle of it could be committed half-made. A daytime
  Cowork session that finds `RUNNING` fresh drafts outside the repo
  (`Claude outputs/`) and applies after the run ends.
- **Item 11, power.** Windows on mains: never sleep, lid close does nothing.
  The owner sets this once. If the laptop is off at a slot, Task Scheduler
  starts the run when it is next turned on ("run as soon as possible after a
  missed start"), and the gate's last-start rule still applies.
- **Item 10** is unchanged: the 05:30 push and email are fine (owner).

---

## Clerical, 2026-10-19 (Cowork, under item 8)

- The worker's settings file is `scripts/nightly/settings.json`, not
  `.claude/nightly.json`: Cowork's tools may not write into `.claude/`. It holds
  only the guard hook; the allow and deny rules are flags in `run.sh`. The worker
  may edit neither (`Edit`/`Write` denied on `scripts/nightly/**` and `.claude/**`).
- `run.sh` reads `NIGHTLY_NOW` only to move the clock the gate reads, for tests
  and the supervised dry run.
