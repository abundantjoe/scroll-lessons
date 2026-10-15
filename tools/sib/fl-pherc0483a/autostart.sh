#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Relaunch helper (not wired as a hook): on the fl-pherc0483a branch only, relaunch the detached watchdog after a container restart
# unless the pipeline has finished. No-op everywhere else. Returns immediately.
H=$(dirname "$(readlink -f "$0")"); REPO=$(git -C "$H" rev-parse --show-toplevel 2>/dev/null) || exit 0
[ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null)" = claude/gifted-bell-gavnl5-sib-fl-pherc0483a ] || exit 0
[ -f "$REPO/logs/sib/fl-pherc0483a/DONE" ] && exit 0
mkdir -p /work/fl0483a
setsid nohup bash "$H/watchdog.sh" >> /work/fl0483a/watchdog.out 2>&1 < /dev/null &
exit 0
