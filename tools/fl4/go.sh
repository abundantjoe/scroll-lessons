#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4-A1 bootstrap (owner order: concentrate the whole fleet on PHerc0268 / PHerc0490A inner windings).
# usage: bash go.sh ME SCROLL LANE NLANES   (run from the worker's repo checkout, on its own sib branch)
# 1) stops this container's FL-2 / gate compute (CPU goes to FL-4), 2) copies the kit into tools/sib/ME/fl4,
# 3) writes /work/fl4/conf.sh, 4) launches the detached watchdog. Then arm keepalive (see the last line printed).
set -uo pipefail
ME=$1; SCROLL=$2; LANE=$3; NLANES=$4; MAIN=origin/claude/gifted-bell-gavnl5
REPO=$(git rev-parse --show-toplevel); cd "$REPO"; K=tools/sib/$ME/fl4
pkill -f 'fl2/watchdog.sh|fl2/pipeline.sh|gp_gate.sh|fl2/keepalive.sh|tools/fl2/keepalive.sh|vc_grow_seg_from_seed|vc_render_tifxyz|ink_detection.inference.infer|pairs0139c/gp_infer.py' 2>/dev/null
sleep 2
git fetch -q origin claude/gifted-bell-gavnl5 || { echo "fetch failed"; exit 1; }
mkdir -p $K /work/fl4 /work/own
for f in run.sh watchdog.sh setup_gp.sh gp_infer.py fl4.py BRIEF_FL4.md; do git show $MAIN:tools/fl4/$f > $K/$f; done
git show $MAIN:tools/fl2/keepalive.sh > $K/keepalive.sh
printf 'ME=%s\nSCROLL=%s\nLANE=%s\nNLANES=%s\n' "$ME" "$SCROLL" "$LANE" "$NLANES" > /work/fl4/conf.sh
FREE=$(df -BG --output=avail /work | tail -1 | tr -dc 0-9)
[ "${FREE:-0}" -lt 15 ] && rm -rf /work/fl2/render /work/fl2/infer /work/gp/render /work/gp/pred 2>/dev/null   # regenerable FL-2 / gate renders and predictions (outputs already pushed)
# re-run = restart on the current kit: stop this worker's FL4 run (markers keep finished steps), clear a premature ALL_DONE
pkill -f "tools/sib/$ME/fl4/run.sh|tools/sib/$ME/fl4/gp_infer.py" 2>/dev/null; rm -f $REPO/logs/sib/$ME/fl4/$SCROLL/ALL_DONE
pgrep -f "$REPO/$K/watchdog.sh" >/dev/null || (setsid nohup bash $REPO/$K/watchdog.sh >/dev/null 2>&1 </dev/null &)
sleep 1; pgrep -f "$REPO/$K/watchdog.sh" >/dev/null && echo "FL4 watchdog running ($ME $SCROLL lane $LANE/$NLANES)" || echo "FL4 watchdog NOT running"
echo "NEXT (harness-tracked background Bash, timeout 7200000; re-arm on every wake): WD=$REPO/$K/watchdog.sh DONE=$REPO/logs/sib/$ME/fl4/$SCROLL/ALL_DONE bash $REPO/$K/keepalive.sh $ME"
