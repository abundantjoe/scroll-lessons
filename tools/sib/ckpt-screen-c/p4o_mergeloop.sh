#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Every 30 min: merge sub-sibling tiles, finalize the (interim) manifest when DECL-P4-14-A3 counts are met, commit, push.
R=/home/user/dominion; T=$R/tools/sib/ckpt-screen-c; D=logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4
while true; do
  cd $R
  o=$(python3 $T/p4o_merge.py); echo "$(date -u +%FT%TZ) $o"
  if echo "$o" | grep -q READY; then
    P4O_WORK=/work/p4o_c/fp32 /opt/hv-1667/bin/python $T/p4o_run.py --finalize --out $R/$D >/dev/null 2>&1 && echo "$(date -u +%FT%TZ) manifest written"
  fi
  git add logs/sib/ckpt-screen-c >/dev/null 2>&1
  if ! git diff --cached --quiet; then
    git commit -q -m "sib ckpt-screen-c: P4-O it4 tiles/manifest update (merge loop)

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Jpx7ZVorqZaNdHPfs1KiYC"
    for i in 1 2 3 4; do git push -q -u origin claude/gifted-bell-gavnl5-sib-ckpt-screen-c && break; sleep $((2**i)); done
  fi
  sleep 1800
done
