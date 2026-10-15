#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Drive stage B over every PHerc0814 segment as stage A finishes it (resumable; logs every pass in runs.jsonl).
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
export PYTHONPATH=src
while true; do
  tools/sib/pairs0814/runlog.sh /work/sib/stage_b_pass_$(date -u +%H%M%S).log /opt/hv/bin/python tools/sib/pairs0814/stage_b.py all
  n=$(ls /work/sib/blocks/*/SEGMENT_DONE.json 2>/dev/null | wc -l)
  [ "$n" -ge 19 ] && break
  sleep 60
done
echo "stage B complete $(date -u +%FT%TZ)" > /work/sib/STAGE_B_COMPLETE
