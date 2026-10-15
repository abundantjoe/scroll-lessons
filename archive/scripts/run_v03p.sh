#!/bin/sh
cd /home/user/megara
J="data/w028/crops.json 2.399 data/w028/pred_2.4um_team.tif data/labels/w028_inklabels.zarr 4 10 240"
D=""
for n in text1 blank1 text2 text3 text4 text5 blank2; do
  test -f data/w028/derived/$n/s_top_v0.3p.npy || .venv/bin/python scripts/v03p.py data/w028/derived/$n 2.399 || exit 1
  test -f data/w028/derived/$n/gate_v0.3p.json || .venv/bin/python scripts/gate_eval.py eval data/w028/derived/$n $n $J v0.3p || exit 1
  D="$D data/w028/derived/$n"; echo "$n v0.3p done"
done
.venv/bin/python scripts/gate_eval.py summary v0.3p stats/w028_gate_t1_v0.3p.json $D && echo V03P_DONE
