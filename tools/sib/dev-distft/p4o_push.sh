#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Every 15 min: commit and push any new P4-O iteration-2 tile (PNG + json), the run log and runs.jsonl.
# Tiles are added as bytes only; nothing opens them.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
OUT=logs/sib/dev-distft/p4o/iteration-2
while true; do
  git add "$OUT" logs/sib/dev-distft/runs.jsonl logs/sib/dev-distft/out 2>/dev/null
  if ! git diff --cached --quiet; then
    N=$(ls $OUT/tiles/*.png.json 2>/dev/null | wc -l)
    git commit -q -m "sib dev-distft P4-O iteration-2: $N of 108 tiles

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018MPzKxBJy8gwCSqvMeSeW7"
    for i in 1 2 3 4; do git push -q origin claude/gifted-bell-gavnl5-sib-dev-distft && break; sleep $((2**i)); done
  fi
  [ -f /work/p4o/RUN_DONE ] && { git add -A $OUT; git diff --cached --quiet || { git commit -q -m "sib dev-distft P4-O iteration-2: manifest

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018MPzKxBJy8gwCSqvMeSeW7"; git push -q origin claude/gifted-bell-gavnl5-sib-dev-distft; }; exit 0; }
  sleep 900
done
