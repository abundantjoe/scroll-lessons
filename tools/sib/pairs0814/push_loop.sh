#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Every 30 min until stage B is complete: copy new sha-checked block files, commit and push (<= 500 MB per push).
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
B=claude/gifted-bell-gavnl5-sib-pairs0814
while true; do
  done_flag=0; [ -e /work/sib/STAGE_B_COMPLETE ] && done_flag=1
  while true; do
    out=$(/opt/hv/bin/python tools/sib/pairs0814/push_blocks.py 2>&1); n=${out%% *}
    git add logs/sib/pairs0814 >/dev/null 2>&1
    git diff --cached --quiet || git commit -q -F - <<MSG
sib pairs0814: staged block pairs and registry (auto push, $n new files)

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018vpsU55LqA4PAQN5JbLdf8
MSG
    ok=0; for i in 1 2 3 4; do git push -q origin $B >/dev/null 2>&1 && { ok=1; break; }; sleep $((2**i)); done
    echo "$(date -u +%FT%TZ) push_loop new_files=$out push_ok=$ok" >> /work/sib/push_loop.log
    [ "$ok" = 1 ] || break
    [ "${n:-0}" -gt 0 ] 2>/dev/null || break
  done
  [ "$done_flag" = 1 ] && break
  sleep 1800
done
