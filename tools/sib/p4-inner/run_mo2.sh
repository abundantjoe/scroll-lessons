#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
[line withheld: prize-candidate detail under review]
set -uo pipefail
R="$1"; REPO=/home/user/dominion; T=$REPO/tools/sib/p4-inner
cd $REPO
[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]
  [ -f $D/manifest.json ] && { echo "$TAG already pushed"; continue; }
  avail=$(df --output=avail -BG / | tail -1 | tr -dc 0-9); [ "$avail" -lt 6 ] && { echo "LOW DISK ${avail}G"; exit 3; }
  [ -s $W/downloads.jsonl ] && [ $(wc -l < $W/downloads.jsonl) -eq 7 ] || bash $T/fetch_strip.sh $W/dl $W/downloads.jsonl $SEG || exit 4
  grep -q ALL_DONE $W/tile.log 2>/dev/null || P4_SEG=$SEG python3 $T/tile_strip.py $W/dl $W/out --skip-existing > $W/tile.log 2>&1 || exit 5
  [ -f $W/out/tile_geom.json ] || python3 $T/tile_geom_w128.py $W/out $W/out/tile_geom.json > $W/geom.log 2>&1 || exit 6
  [ -f $W/out/direction.json ] || python3 $T/direction_strip.py $W/dl $W/out/direction.json $TAG > $W/dir.log 2>&1 || exit 7
[line withheld: prize-candidate detail under review]
  rm -f $W/dl/*new_canon*.tif
[line withheld: prize-candidate detail under review]

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01AXfmasnYmkW3pgGvTRpDwK"
  for i in 1 2 3 4; do git push -q origin claude/gifted-bell-gavnl5-sib-p4-inner && break; sleep $((2**i)); done
  echo "PUSHED $TAG $(git rev-parse --short HEAD)"
done
echo ALL_STRIPS_DONE
