#!/usr/bin/env bash
# The nightly worker (decisions/0062, with its 2026-10-19 addendum).
#
# Started by Windows Task Scheduler, twice a day:
#   wsl.exe -d Ubuntu -u lelvieira --cd /mnt/c/AI/signal-lab -- bash -lc 'bash scripts/nightly/run.sh night'   (23:00)
#   wsl.exe -d Ubuntu -u lelvieira --cd /mnt/c/AI/signal-lab -- bash -lc 'bash scripts/nightly/run.sh day'     (12:30)
# (`bash run.sh`, not `./run.sh`: git on /mnt/c may not keep the execute bit.)
#
# A slot with nothing released makes no model call: the lock, git, power and the
# gate (nightly_gate.py) decide first, and a skip is one line in
# results/audit/_nightly/gate.log. A run that starts writes
# results/audit/_nightly/<stamp>-<slot>/ (status.txt, result.json,
# transcript.jsonl, claude.err, cap). Cowork reads status.txt and result.json,
# never transcript.jsonl (decisions/0062 item 7).
#
# The worker cannot edit this file, config.sh, guard.py, prompt.md, settings.json or .claude/.
set -uo pipefail

slot="${1:-}"
case "$slot" in
  night | day) ;;
  *) echo "usage: run.sh night|day" >&2; exit 2 ;;
esac
repo="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$repo" || exit 2
# shellcheck source=config.sh
. scripts/nightly/config.sh

base="results/audit/_nightly"
mkdir -p "$base"
gatelog="$base/gate.log"
glog() { echo "$(date -Is) slot=$slot $*" >>"$gatelog"; }

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1   # decisions/0048
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/signal-lab"

# 1. One run at a time (item 5). scripts/unattended.sh takes the same lock.
mkdir -p "$HOME/.locks"
exec 9>"$HOME/.locks/signal-lab.lock"
if ! flock -n 9; then glog "skip: the lock is held"; exit 0; fi
export SIGNAL_LAB_LOCK_HELD=1

# 2. Git must be usable: a lock file Cowork's shell left would break every commit.
if [ -e .git/index.lock ]; then glog "skip: .git/index.lock exists"; exit 0; fi

# 3. Mains power, best effort. Win32_Battery.BatteryStatus 1, 4 and 5 are on battery.
if command -v powershell.exe >/dev/null 2>&1; then
  bat="$(timeout 10 powershell.exe -NoProfile -Command \
    '$b = Get-CimInstance Win32_Battery | Select-Object -First 1; if ($b) { [int]$b.BatteryStatus } else { 2 }' \
    2>/dev/null | tr -d '\r' | head -1)"
  case "$bat" in 1 | 4 | 5) glog "skip: on battery (BatteryStatus=$bat)"; exit 0 ;; esac
fi

# 4. The release line, its stamp, the slot's times and the monthly cap.
# NIGHTLY_NOW (an ISO local time) is for tests only: it moves the clock the gate reads.
if ! gate="$(python3 scripts/nightly/nightly_gate.py gate --handoff HANDOFF.md --slot "$slot" \
  --ran "$base/ran-stamps.txt" --runs "$base" --month-cap "$MONTH_CAP_USD" \
  --sonnet-cap "$SONNET_CAP_USD" --opus-cap "$OPUS_CAP_USD" ${NIGHTLY_NOW:+--now "$NIGHTLY_NOW"})"; then
  glog "skip: the gate failed to run"
  exit 0
fi
eval "$gate"
if [ "${GO:-0}" != "1" ]; then glog "skip: ${REASON:-unknown}"; exit 0; fi

# 5. The key, from WSL's home only, set for the one claude call (item 4).
envf="$HOME/.config/signal-lab/nightly.env"
if [ ! -f "$envf" ] || [ "$(stat -c %a "$envf")" != "600" ]; then
  glog "skip: RELEASED ($LINE) but $envf is missing or not mode 600"
  exit 0
fi
key="$(sed -n 's/^ANTHROPIC_API_KEY=//p' "$envf" | head -1 | tr -d '\r')"
if [ -z "$key" ]; then glog "skip: RELEASED ($LINE) but $envf has no ANTHROPIC_API_KEY"; exit 0; fi
case "$key" in
  sk-ant-*) ;;
  *) glog "skip: RELEASED ($LINE) but the value in $envf does not start with sk-ant- (a key id or a masked label?)"; exit 0 ;;
esac
if ! command -v claude >/dev/null 2>&1; then glog "skip: RELEASED ($LINE) but claude is not on PATH"; exit 0; fi

# 6. The run.
stamp="$(date +%Y%m%d-%H%M%S)"
out="$base/${stamp}-${slot}"
mkdir -p "$out"
status="$out/status.txt"
log() { echo "$(date -Is) $*" >>"$status"; }
echo "$RUN_CAP" >"$out/cap"
echo "$STAMP" >>"$base/ran-stamps.txt"   # a stamp runs once, even if this run dies
start_head="$(git rev-parse --short HEAD)"
log "start slot=$slot head=$start_head claude=$(claude --version 2>/dev/null | head -1)"
log "release: $LINE"
log "model=$MODEL_ID run_cap_usd=$RUN_CAP month_spend_usd=$MONTH_SPEND push=$PUSH long=$LONG last_start='$LAST_START' wall_s=$WALL_SECONDS"
glog "run: $out ($LINE)"

# The heartbeat Cowork reads, since it cannot see WSL (item 5).
beat() {
  while true; do
    {
      echo "stamp=$STAMP"
      echo "slot=$slot"
      echo "run=$out"
      echo "release=$LINE"
      echo "head=$(git rev-parse --short HEAD 2>/dev/null)"
      echo "beat=$(date -Is)"
    } >"$base/RUNNING.tmp" && mv -f "$base/RUNNING.tmp" "$base/RUNNING"
    sleep 60
  done
}
beat &
beat_pid=$!
trap 'kill "$beat_pid" 2>/dev/null; rm -f "$base/RUNNING" "$base/RUNNING.tmp"' EXIT

prompt="$(cat scripts/nightly/prompt.md)"
prompt="${prompt//@@SLOT@@/$slot}"
prompt="${prompt//@@STAMP@@/$STAMP}"
prompt="${prompt//@@IDS@@/$IDS}"
prompt="${prompt//@@PUSH@@/$PUSH}"
prompt="${prompt//@@LONG@@/$LONG}"
prompt="${prompt//@@LAST_START@@/$LAST_START}"
prompt="${prompt//@@MODEL@@/$MODEL}"
prompt="${prompt//@@OUT@@/$out}"

# Permissions (item 6). On the command line rather than in a settings file:
# a -p run applies a repository's allow rules only in a folder trusted
# interactively, while flags always apply. The repo's .claude/settings.json deny
# list applies as well; deny beats allow.
allow=(
  Read Edit Write Glob Grep
  "Bash(make *)" "Bash(scripts/unattended.sh *)" "Bash(bash scripts/unattended.sh *)"
  "Bash(uv run --python 3.12 --group dev *)"
  "Bash(git status)" "Bash(git status *)" "Bash(git log *)" "Bash(git diff *)" "Bash(git show *)"
  "Bash(git rev-parse *)" "Bash(git rev-list *)" "Bash(git ls-files *)" "Bash(git check-ignore *)"
  "Bash(git add *)" "Bash(git mv *)" "Bash(git commit *)" "Bash(git am *)"
  "Bash(git push origin main)"
  "Bash(ls *)" "Bash(wc *)" "Bash(head *)" "Bash(tail *)" "Bash(grep *)" "Bash(sha256sum *)"
  "Bash(date)" "Bash(date *)" "Bash(mkdir *)" "Bash(mktemp *)"
)
deny=(
  WebFetch WebSearch
  "Edit(/scripts/nightly/**)" "Write(/scripts/nightly/**)" "Edit(/.claude/**)" "Write(/.claude/**)"
  "Edit(/CLAUDE.md)" "Write(/CLAUDE.md)" "Edit(/SUBSTRATE.md)" "Write(/SUBSTRATE.md)"
  "Edit(/params/**)" "Write(/params/**)" "Edit(/vetoes/**)" "Write(/vetoes/**)"
  "Bash(git push --force *)" "Bash(git push -f *)" "Bash(git push origin main --force *)"
  "Bash(git push origin main -f *)" "Bash(git push origin main +*)"
  "Bash(git reset *)" "Bash(git rebase *)" "Bash(git commit --amend *)" "Bash(git checkout *)"
  "Bash(git switch *)" "Bash(git stash *)" "Bash(git clean *)" "Bash(git config *)"
  "Bash(git branch *)" "Bash(git tag *)" "Bash(git merge *)" "Bash(git pull *)"
  "Bash(curl *)" "Bash(wget *)" "Bash(ssh *)" "Bash(scp *)"
)
if [ "$PUSH" != "yes" ]; then deny+=("Bash(git push *)" "Bash(git push)"); fi

t0=$SECONDS
printf '%s' "$prompt" | env -u ANTHROPIC_AUTH_TOKEN -u CLAUDE_CODE_OAUTH_TOKEN \
  ANTHROPIC_API_KEY="$key" \
  BASH_DEFAULT_TIMEOUT_MS=1200000 BASH_MAX_TIMEOUT_MS=57600000 \
  DISABLE_AUTOUPDATER=1 \
  timeout --signal=INT --kill-after=10m "${WALL_SECONDS}s" \
  claude -p \
    --model "$MODEL_ID" \
    --permission-mode dontAsk --permission-prompts none \
    --setting-sources project --settings scripts/nightly/settings.json \
    --strict-mcp-config \
    --max-turns "$MAX_TURNS" --max-budget-usd "$RUN_CAP" \
    --output-format stream-json --verbose \
    --allowedTools "${allow[@]}" \
    --disallowedTools "${deny[@]}" \
  >"$out/transcript.jsonl" 2>"$out/claude.err"
rc=$?
unset key
elapsed=$((SECONDS - t0))
case "$rc" in
  124) why="wall clock (${WALL_SECONDS} s)" ;;
  137) why="killed after the wall clock" ;;
  *) why="claude exited" ;;
esac

eval "$(python3 scripts/nightly/nightly_gate.py result "$out/transcript.jsonl" "$out/result.json")"
log "claude rc=$rc ($elapsed s) end_reason='$why' subtype=$SUBTYPE cost_usd=$COST turns=$TURNS denials=$DENIALS"
end_head="$(git rev-parse --short HEAD)"
log "end head=$end_head (start $start_head)"
log "commits: $(git log --format='%h %s' "$start_head..HEAD" | tr '\n' ';' | sed 's/;$//')"
owner_paths="$(git diff --name-only "$start_head..HEAD" | grep -E '^(SUBSTRATE\.md|params/|vetoes/)' | tr '\n' ' ')"
log "owner-only paths committed: ${owner_paths:-(none)}"
log "uncommitted paths: $(git status --porcelain | wc -l)"
log "origin/main=$(git rev-parse --short origin/main 2>/dev/null || echo '?') ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo '?')"
log "end rc=$rc"
exit 0
