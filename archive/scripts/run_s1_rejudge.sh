#!/bin/sh
# After the per-crop reference refinement: regenerate label/class masks and re-judge every existing score map, then continue with v2 and v3.
cd /home/user/megara
SEG=20231005123336; P=2.4; CJ=data/s1/$SEG/crops.json; LAB=data/s1/labels/${SEG}_inklabels.png
until .venv/bin/python -c "import json,sys; c=json.load(open('$CJ')); sys.exit(0 if all('local_offset' in x for x in c['crops']) else 1)"; do sleep 15; done
for name in train held1 held2 held3; do
  D=data/s1/$SEG/derived/$name; rm -f $D/cls_text.npy $D/cls_blank.npy $D/label.npy $D/judge_*.json
  for tag in v0.1b v1a v1b v0.3p team; do test -f $D/s_bot_$tag.npy && { .venv/bin/python scripts/s1_judge.py $D $CJ $name $LAB $tag $P || exit 1; }; done
  echo "$name rejudged $(date)"
done
.venv/bin/python scripts/s1_summary.py data/s1/$SEG stats/s1_gate_$SEG.json && echo REJUDGE_DONE
rm -f stats/s1_v2_config.json stats/s1_v3_weights.json
scripts/run_s1_v2.sh >> /tmp/s1v2.log 2>&1 || { echo STAGE2_FAILED; exit 1; }
echo STAGE2_OK
scripts/run_s1_v3.sh >> /tmp/s1v3.log 2>&1 || { echo STAGE3_FAILED; exit 1; }
echo STAGE3_OK
