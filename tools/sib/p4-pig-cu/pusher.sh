#!/bin/bash
# periodic commit+push of p4-pig-cu numeric outputs. Provenance: Project HERCULES | owner the owner | [id removed]
cd /home/user/dominion
while true; do
  sleep 480
  git add logs/sib/p4-pig-cu/scores logs/sib/p4-pig-cu/injection 2>/dev/null
  if ! git diff --cached --quiet; then
    git commit -qm "p4-pig-cu: partial scores/injection numbers (auto, frozen code)

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BGvjN5PqxUioDsG1cJPaYj"
    for i in 1 2 3 4; do git push -q origin claude/gifted-bell-gavnl5-sib-p4-pig-cu && break; sleep $((2**i)); done
  fi
  grep -q ALLDONE /tmp/claude-0/sp/score_E1.log 2>/dev/null && grep -q ALLDONE /tmp/claude-0/sp/inj_C1.log 2>/dev/null && break
done
