#!/usr/bin/env bash
# Run routine checks without a human in the loop.
#
#   scripts/unattended.sh check              make check only
#   scripts/unattended.sh audit-lean         make check, then the lean synthetic audit
#   scripts/unattended.sh audit --digest     make check, then the Bloomberg audit,
#                                            then ask Claude Code for a digest
#
# Survives a closed terminal when started as:
#   nohup scripts/unattended.sh audit --digest >/dev/null 2>&1 &
# Logs: results/audit/_unattended/<stamp>-<target>/ (git-ignored).
set -uo pipefail
cd "$(dirname "$0")/.."

target="${1:-check}"
digest="${2:-}"
case "$target" in
  check|audit-lean|audit) ;;
  *) echo "unknown target: $target (check | audit-lean | audit)" >&2; exit 2 ;;
esac

export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/signal-lab}"
stamp="$(date +%Y%m%d-%H%M%S)"
out="results/audit/_unattended/${stamp}-${target}"
mkdir -p "$out"
status="$out/status.txt"

log() { echo "$(date -Is) $*" | tee -a "$status"; }

log "start target=$target head=$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
t0=$SECONDS
make check >"$out/check.log" 2>&1
rc=$?
log "make check rc=$rc ($((SECONDS - t0)) s)"

if [ "$rc" -eq 0 ] && [ "$target" != "check" ]; then
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
