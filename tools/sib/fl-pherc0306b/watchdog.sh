#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Watchdog for pipeline.sh (OWNER-STANDING-ORDER-5 item 2): reruns it until logs/sib/fl-pherc0306b/DONE exists.
# Backoff 2, 4, 8 ... 60 min; after 8 consecutive failures it writes FAILED + the STATUS line, pushes, and exits.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO" || exit 1
OUT=logs/sib/fl-pherc0306b; W=${FL_WORK:-/work/fl0306b}; mkdir -p "$W"
exec 9>"$W/watchdog.lock"; flock -n 9 || exit 0
fails=0; d=120
while [ ! -f "$OUT/DONE" ]; do
  bash tools/sib/fl-pherc0306b/pipeline.sh >> "$W/pipeline.out" 2>&1 && { fails=0; continue; }
  fails=$((fails + 1))
  echo "[$(date -u +%FT%TZ)] pipeline exit, failure $fails" >> "$W/pipeline.log"
  if [ $fails -ge 8 ]; then
    echo "$(date -u +%FT%TZ) fl-pherc0306b PHerc0306B: FAILED after 8 retries; last lines in $OUT/FAILED" > "$OUT/STATUS.md"
    tail -60 "$W/pipeline.out" > "$OUT/FAILED"
    git add "$OUT/STATUS.md" "$OUT/FAILED" && git commit -q -m "fl-pherc0306b: pipeline FAILED (watchdog gave up)

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_015H61w4qRrx3aANRD5hPdTN" && git push -q origin HEAD:claude/gifted-bell-gavnl5-sib-fl-pherc0306b
    exit 1
  fi
  sleep $d; d=$((d * 2)); [ $d -gt 3600 ] && d=3600
done
