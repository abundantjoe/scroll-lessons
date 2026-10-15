#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-1 First Letters screen for PHerc0800 (OWNER-STANDING-ORDER-5: detached, self-restarting, idempotent).
# Launch once:  nohup setsid bash tools/sib/fl-pherc0800/pipeline.sh watchdog >/dev/null 2>&1 &
# The watchdog reruns the worker until /work/fl-pherc0800/ALL.done exists (max 6 attempts, 5 min apart).
# The worker: environment -> select -> per segment (render+infer, tiles) and commits/pushes after each unit.
# Numbers only: no image is ever opened or viewed.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-p4-layout
WK=/work/fl-pherc0800
LOG=$WK/pipeline.log
mkdir -p "$WK"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(ts) $*" >> "$LOG"; }

push() {  # commit and push logs/sib/fl-pherc0800 (+ STATUS line)
  cd "$REPO" || return 1
  git add logs/sib/fl-pherc0800 tools/sib/fl-pherc0800 >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -qm "fl-pherc0800: $1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0191DUShgpKy22se1NCgd38m" || return 1
  local k
  for k in 1 2 3 4 5; do
    git push -q origin "$BR" && return 0
    git pull -q --no-rebase origin "$BR" >/dev/null 2>&1
    sleep $((2**k))
  done
  log "push FAILED: $1"; return 1
}

status() { mkdir -p "$REPO/logs/sib/fl-pherc0800"; echo "$(ts) $*" >> "$REPO/logs/sib/fl-pherc0800/STATUS.md"; }

worker() {
  log "worker start pid $$"
  local free; free=$(df --output=avail -BG / | tail -1 | tr -dc 0-9)
  if [ "$free" -lt 12 ]; then log "disk ${free}G free < 12G: stop"; status "BLOCKED: disk ${free} GB free"; push "blocked disk"; return 2; fi
  if [ ! -f $WK/env.done ]; then
    bash "$REPO/docker/env/setup_env.sh" >> $WK/setup_env.log 2>&1 || { log "setup_env failed"; return 1; }
    touch $WK/env.done; log "env ok"
  fi
  local PY=/opt/hv/bin/python D="$REPO/tools/sib/fl-pherc0800/fl_driver.py"
  if [ ! -f "$REPO/logs/sib/fl-pherc0800/segments.json" ]; then
    $PY "$D" select >> "$LOG" 2>&1 || { log "select failed"; return 1; }
    status "segments selected"; push "segments selected"
  fi
  local s
  for s in $($PY -c "import json;print(' '.join(json.load(open('$REPO/logs/sib/fl-pherc0800/segments.json'))['chosen']))"); do
    if [ ! -f $WK/$s/pred.tif.done ]; then
      log "seg $s render+infer"
      $PY "$D" "seg:$s" >> "$LOG" 2>&1 || { log "seg $s failed"; status "seg $s render/infer FAILED (see $WK/$s/*.log)"; push "seg $s failed"; return 1; }
    fi
    if [ ! -f $WK/$s/tiles.done ]; then
      $PY "$D" "tiles:$s" >> "$LOG" 2>&1 || { log "tiles $s failed"; return 1; }
      status "tiles pushed for $s"; push "tiles $s"
    fi
  done
  touch $WK/ALL.done; status "DONE: all segments tiled"; push "all segments tiled"; log "ALL done"
}

case "${1:-watchdog}" in
  worker) worker ;;
  watchdog)
    exec 9>"$WK/watchdog.lock"; flock -n 9 || { echo "already running"; exit 0; }
    for a in 1 2 3 4 5 6; do
      [ -f $WK/ALL.done ] && exit 0
      log "watchdog attempt $a"
      bash "$0" worker; rc=$?
      [ -f $WK/ALL.done ] && exit 0
      [ $rc -eq 2 ] && exit 2
      sleep 300
    done
    status "STOPPED after 6 failed attempts (see $LOG)"; push "stopped after 6 attempts" ;;
esac
