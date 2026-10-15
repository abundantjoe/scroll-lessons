#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Per segment: nominal registration -> depth check -> depth-corrected registration (resumable: outputs are cached).
cd /home/user/dominion
export PYTHONPATH=src
for d in /work/reg0009b/data/*/; do
  s=$(basename "$d"); [ -d "$d/mesh" ] || continue
  tools/sib/reg0009b/runlog.sh /work/reg0009b/logs/reg_$s.out /opt/hv/bin/python tools/sib/reg0009b/reg.py "$s"
  tools/sib/reg0009b/runlog.sh /work/reg0009b/logs/depth_$s.out /opt/hv/bin/python tools/sib/reg0009b/depthcheck.py "$s"
  tools/sib/reg0009b/runlog.sh /work/reg0009b/logs/regdc_$s.out /opt/hv/bin/python tools/sib/reg0009b/reg.py --dc "$s"
done
echo PIPELINE_DONE
