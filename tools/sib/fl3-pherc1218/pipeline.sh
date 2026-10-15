#!/bin/bash
# Provenance: Project HERCULES | [id removed]
# FL pass 3 PHerc1218 worker: restart loop around idempotent units (tools/fl/BRIEF_PASS.md @ dcb6a6ba).
cd /home/user/dominion
python3 -c 'import numcodecs,tifffile,cv2,PIL,scipy' 2>/dev/null || pip install -q numcodecs tifffile imagecodecs opencv-python-headless pillow scipy
while pgrep -f "docker/env/setup_env.sh" >/dev/null; do sleep 60; done
for attempt in $(seq 1 12); do
  python3 tools/sib/fl3-pherc1218/units.py && grep -q "^DONE" logs/sib/fl3-pherc1218/STATUS.md 2>/dev/null && exit 0
  echo "$(date -u +%FT%TZ) attempt $attempt failed; restarting in 300 s" >> logs/sib/fl3-pherc1218/progress.log
  sleep 300
done
echo "$(date -u +%FT%TZ) FAILED after 12 attempts" >> logs/sib/fl3-pherc1218/STATUS.md
