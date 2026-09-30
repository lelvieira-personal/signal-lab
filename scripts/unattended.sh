#!/usr/bin/env bash
# Run routine checks without a human in the loop.
#
#   scripts/unattended.sh check              make check only (fast tier)
#   scripts/unattended.sh check-full         make check-full only (the whole suite; HANDOFF task 37)
#   scripts/unattended.sh audit-lean         make check-full, then the lean synthetic audit
#   scripts/unattended.sh audit-baseline-pilot | audit-baseline   the decisions/0036 baseline cells
#   scripts/unattended.sh audit-knee         the live + baseline knee rungs, h13 (HANDOFF task 20)
#   scripts/unattended.sh audit-power        score-shuffle baselines at two knee rungs (HANDOFF task 25)
#   scripts/unattended.sh audit-friction-created  created-turnover shadow, IC 0.35/0.70, ten seeds, coefficient 10/20/40 (HANDOFF task 36)
#   scripts/unattended.sh audit-power10      span-limited score shuffles, IC 0.70, ten seeds (HANDOFF task 30)
#   scripts/unattended.sh audit-friction     shadow-cost 10/20/40 bp, IC 0.35/0.70, ten seeds (HANDOFF task 32)
#   scripts/unattended.sh audit-halflife     volatility-overlay halflife sweep, h4/13/26 x IC 0.35/0.70 x seeds 0-9
#                                            x halflife None/13/26/52 -- 240 cells; HALFLIFE_DEADLINE stops it cleanly
#                                            (HANDOFF task 35)
#   scripts/unattended.sh audit --digest     make check-full, then the Bloomberg audit,
#                                            then ask Claude Code for a digest
#
# An audit target's opening step is `make check-full`, not `make check`: an
# audit is hours, so an hour of engine tests in front of it is affordable, and
# it's the one place the engine must be proven (HANDOFF task 37). The bare
# `check` and `check-full` targets run exactly that one make target and stop.
#
# Survives a closed terminal when started as:
#   nohup scripts/unattended.sh audit --digest >/dev/null 2>&1 &
# Logs: results/audit/_unattended/<stamp>-<target>/ (git-ignored).
set -uo pipefail
cd "$(dirname "$0")/.."

target="${1:-check}"
digest="${2:-}"
case "$target" in
  check|check-full|audit-lean|audit|audit-baseline-pilot|audit-baseline|audit-knee|audit-power|audit-power10|audit-friction|audit-friction-created|audit-halflife) ;;
  *) echo "unknown target: $target (check | check-full | audit-lean | audit | audit-baseline-pilot | audit-baseline | audit-knee | audit-power | audit-power10 | audit-friction | audit-friction-created | audit-halflife)" >&2; exit 2 ;;
esac

export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/signal-lab}"
stamp="$(date +%Y%m%d-%H%M%S)"
out="results/audit/_unattended/${stamp}-${target}"
mkdir -p "$out"
status="$out/status.txt"

log() { echo "$(date -Is) $*" | tee -a "$status"; }

log "start target=$target head=$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
t0=$SECONDS
if [ "$target" = "check" ]; then
  check_target="check"
else
  check_target="check-full"
fi
make "$check_target" >"$out/check.log" 2>&1
rc=$?
log "make $check_target rc=$rc ($((SECONDS - t0)) s)"

if [ "$rc" -eq 0 ] && [ "$target" != "check" ] && [ "$target" != "check-full" ]; then
  t1=$SECONDS
  make "$target" >"$out/$target.log" 2>&1
  rc=$?
  log "make $target rc=$rc ($((SECONDS - t1)) s)"
  run_dir="$(ls -1dt results/audit/*/ 2>/dev/null | grep -v '/_unattended/' | head -1)"
  log "newest audit dir: ${run_dir:-none}"
fi
log "end rc=$rc"

if [ "$digest" = "--digest" ]; then
  if command -v claude >/dev/null 2>&1; then
    claude -p "Unattended run finished. Follow the 'Routine, unattended work' section of CLAUDE.md. Status file: $status. Logs are in $out. Write the digest as markdown to stdout." \
      --allowedTools "Read,Grep,Glob" >"$out/digest.md" 2>"$out/digest.err"
    log "digest rc=$? -> $out/digest.md"
  else
    log "digest skipped: claude not on PATH"
  fi
fi
exit "$rc"
