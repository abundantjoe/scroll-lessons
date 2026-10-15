#!/bin/sh
# One heavy job at a time (15 GB RAM): residual v0.1b + judge per finished chart; then inpainting net; then v0.2. Idempotent.
cd /home/user/megara
J="data/w028/crops.json 2.399 data/w028/pred_2.4um_team.tif data/labels/w028_inklabels.zarr 4 10 240"
ALL="text1 blank1 text2 text3 text4 text5 blank2"
for n in $ALL; do
  until test -f data/w028/derived/$n/topo.done; do sleep 15; done
  .venv/bin/python scripts/residual.py data/w028/derived/$n 2.399 --tag v0.1b || exit 1
  test -f data/w028/derived/$n/gate_v0.1b.json || .venv/bin/python scripts/gate_eval.py eval data/w028/derived/$n $n $J v0.1b || exit 1
  echo "$n v0.1b done $(date)"
done
D=""; for n in $ALL; do D="$D data/w028/derived/$n"; done
.venv/bin/python scripts/gate_eval.py summary v0.1b stats/w028_gate_t1_v0.1b.json $D
test -f data/w028/inpaint_w028.pt || .venv/bin/python scripts/inpaint_net.py train data/w028/inpaint_w028.pt $D || exit 1
for n in $ALL; do
  test -f data/w028/derived/$n/a_bot.npy || .venv/bin/python scripts/inpaint_net.py predict data/w028/inpaint_w028.pt data/w028/derived/$n || exit 1
  .venv/bin/python scripts/residual.py data/w028/derived/$n 2.399 --tag v0.2 || exit 1
  test -f data/w028/derived/$n/gate_v0.2.json || .venv/bin/python scripts/gate_eval.py eval data/w028/derived/$n $n $J v0.2 || exit 1
  echo "$n v0.2 done $(date)"
done
.venv/bin/python scripts/gate_eval.py summary v0.2 stats/w028_gate_t1_v0.2.json $D
echo CHAIN_DONE
