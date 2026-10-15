#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Dev matrix grouped by seed, 4 concurrent tracer jobs (4 cores), remote chunk cache cleared between
# seeds (the VC3D cache stores decoded 192^3 chunks and filled the disk once, 2026-09-25 ~19:50Z).
set -uo pipefail
cd /home/user/dominion
for s in "$@"; do
  for c in ${CFGS:-L15 L20 L25 S15 S20 S25}; do echo "$c $s"; done | xargs -P ${PAR:-4} -L 1 /opt/hv/bin/python tools/sib/tracer/dev_run.py
  echo "seed $s done $(date -u +%FT%TZ) cache $(du -sh /work/vchome 2>/dev/null | cut -f1) free $(df -h /home/user | tail -1 | awk '{print $4}')"
  rm -rf /work/vchome/.VC3D/remote_cache
done
if [ -n "${CONTROL:-}" ]; then
  /opt/hv/bin/python tools/sib/tracer/dev_control.py $(ls -d /work/dev/[LS]*_auto_grown_*) > /work/logs/dev_control_c4.log 2>&1
  /opt/hv/bin/python tools/sib/tracer/aggregate.py >> /work/logs/dev_control_c4.log 2>&1
fi
echo BATCHDONE
