#!/bin/bash
# Provenance: Project HERCULES | [id removed]
# p4v-02 repro gate (BRIEF_VERSO item 6), then the lanes (run_p4v.sh) on PASS only.
cd /home/user/dominion
N=20260701183124-w010-027_r0_c11; J=/work/own/repro/tiles/$N.png.json
while pgrep -f "out /work/own/repro " >/dev/null && [ ! -f $J ]; do sleep 30; done
[ -f $J ] || { echo "REPRO run ended without output"; exit 5; }
WANT=$(git show origin/claude/gifted-bell-gavnl5-sib-own-lead:logs/sib/own-s1/maps/tiles/$N.png.json | /opt/ckb/bin/python -c "import json,sys;print(json.load(sys.stdin)['png_sha256'])")
GOT=$(sha256sum /work/own/repro/tiles/$N.png | cut -c1-64)
REC=$(/opt/ckb/bin/python -c "import json;print(json.load(open('$J'))['png_sha256'])")
if [ "$GOT" = "$WANT" ] && [ "$REC" = "$WANT" ]; then V=PASS; else V=FAIL; fi
flock /work/own/git.lock -c "
  set -e
  mkdir -p logs/sib/p4v-02/fwd_x/repro; cp /work/own/repro/tiles/$N.png /work/own/repro/tiles/$N.png.json logs/sib/p4v-02/fwd_x/repro/
  echo '- '\$(date -u +%FT%TZ)' REPRO $V: forward $N png_sha256 $GOT (record $REC), own-lead $WANT' >> logs/sib/p4v-02/STATUS.md
  git add logs/sib/p4v-02 tools/sib/p4v-02
  git commit -qm 'p4v-02: repro gate forward $N: REPRO $V (DECL-P4-26-A2 item 6)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01S7WzvF2vxmV1oKK5c6U9p2

Provenance: Project HERCULES | [id removed]'
  for n in 1 2 3 4; do git push -q -u origin claude/gifted-bell-gavnl5-sib-p4v-02 && break; sleep \$((2**n)); done
"
echo "REPRO $V"
[ $V = PASS ] || exit 6
exec tools/sib/p4v-02/run_p4v.sh
