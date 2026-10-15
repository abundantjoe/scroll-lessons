#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-W windows (DECL-P4-17 item 1): w and wpc sets, 1 worker each, push every 10 min; manifests via windows_manifest.py.
R=/home/user/dominion; T=$R/tools/sib/p4-l2; L=$R/logs/sib/p4-l2; W=/work/l2
for s in w wpc; do nohup python3 $T/windows.py $W/raw $L/l2s/manifest.json $L --set $s >> $W/win_$s.log 2>&1 & done
while :; do
  sleep 600
  a=$(pgrep -f "windows.py $W/raw" | wc -l)
  for s in w wpc; do python3 $T/windows_manifest.py $L/${s}_l2s $s >> $W/win_manifest.log 2>&1; done
  git -C $R add logs/sib/p4-l2/w_l2s logs/sib/p4-l2/wpc_l2s tools/sib/p4-l2
  git -C $R commit -q -m "p4-l2: P4-W windows (L2S) progress

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VYfh6gj6Kr8Qyurerayy9B" && git -C $R push -q origin claude/gifted-bell-gavnl5-sib-p4-l2
  [ "$a" -eq 0 ] && break
done
echo WIN_DONE >> $W/win_manifest.log
