#!/bin/bash
# commits worker progress every 30 min until the tile record exists
cd /home/user/dominion
J=logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/tiles/20260701183124-w010-027_r1_c16.png.json
while [ ! -f "$J" ]; do
  sleep 1800
  [ -f "$J" ] && break
  { echo "Provenance: Project HERCULES | owner the owner | [id removed]"; echo; echo "# STATUS o5w6 (auto, $(date -u +%FT%TZ))"; echo "Running tile r1 c16 (it5, forward, code 98cd075, ckpt sha256 9920d433...301b). Start $(cat /work/p4o/start_utc)."; echo; echo '```'; tail -n 5 /work/p4o/worker.log; ls -la /work/p4o/it5/ckpt/* 2>/dev/null | tail -n 4; echo '```'; } > logs/sib/o5w6/STATUS.md
  git add logs/sib/o5w6/STATUS.md && git commit -q -m "o5w6: progress checkpoint r1 c16

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Aieb8KpPNMmEGHDaJa3YLZ" && for i in 2 4 8 16; do git push -q -u origin claude/gifted-bell-gavnl5-sib-o5w6 && break; sleep $i; done
done
