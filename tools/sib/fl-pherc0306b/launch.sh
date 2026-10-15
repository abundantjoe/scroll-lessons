#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Start the fl-pherc0306b watchdog detached (idempotent: the watchdog holds a flock).
# Returns at once. After a container restart (/work lost) one call resumes from the pushed records.
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO" || exit 0
[ -f logs/sib/fl-pherc0306b/DONE ] && exit 0
mkdir -p /work/fl0306b
setsid nohup bash tools/sib/fl-pherc0306b/watchdog.sh >> /work/fl0306b/watchdog.out 2>&1 < /dev/null &
exit 0
