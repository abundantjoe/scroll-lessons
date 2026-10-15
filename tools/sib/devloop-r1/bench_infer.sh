#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Synthetic only. (1) fp16/bf16 feature rounding vs official fp32 map on the amx synthetic volume;
# (2) wall time, official CLI vs lc_infer (identity), on a random 31 x 2648 x 2648 volume (DEV window + 256 px margin).
cd /home/user/dominion
R=tools/sib/devloop-r1/run.sh
PY=/opt/hv-ink/bin/python
export OMP_NUM_THREADS=4
for fd in fp16 bf16; do [ -f logs/sib/devloop-r1/out/feat_${fd}_synth.log ] && grep -q within2 logs/sib/devloop-r1/out/feat_${fd}_synth.log && continue
  $R feat_${fd}_synth "$PY tools/sib/devloop-r1/lc_infer.py /work/amx/synth/synth.zarr none /work/dl/id_${fd}.tif --base-identity --feature-dtype $fd && $PY -c \"
import tifffile,numpy as np,json
out={}
for s in ('','_reverse'):
    x=tifffile.imread('/work/dl/id_${fd}'+s+'.tif').astype(int); y=tifffile.imread('/work/amx/synth/fp32'+s+'.tif').astype(int); d=np.abs(x-y)
    out['fwd' if not s else 'rev']=dict(max=int(d.max()),identical=float((d==0).mean()),within1=float((d<=1).mean()),within2=float((d<=2).mean()))
print(json.dumps(out))\""
done
$R make_big "$PY -c \"
import numpy as np, zarr, os
p='/work/dl/big.zarr'
if not os.path.exists(p):
    rng=np.random.default_rng(20260925); z=zarr.create_array(p, shape=(31,2648,2648), chunks=(31,128,128), dtype='uint8')
    for y in range(0,2648,512): z[:,y:y+512,:]=rng.normal(120,25,(31,min(512,2648-y),2648)).clip(0,255).astype(np.uint8)
print('ok')\""
$R time_official_big "t0=\$(date +%s.%N); $PY -m vesuvius.ink_detection.inference.infer /work/dl/big.zarr /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth /work/dl/big_off.tif --direction both --batch-size 4 --num-workers 1 --no-compile > /work/dl/big_off.log 2>&1; rc=\$?; echo wall_s \$(echo \$(date +%s.%N) - \$t0 | bc); grep 'Selected' /work/dl/big_off.log; exit \$rc"
$R time_lc_big "t0=\$(date +%s.%N); $PY tools/sib/devloop-r1/lc_infer.py /work/dl/big.zarr none /work/dl/big_lc.tif --base-identity --record /work/dl/big_lc.json > /work/dl/big_lc.log 2>&1; rc=\$?; echo wall_s \$(echo \$(date +%s.%N) - \$t0 | bc); tail -n 1 /work/dl/big_lc.log; sha256sum /work/dl/big_off.tif /work/dl/big_lc.tif /work/dl/big_off_reverse.tif /work/dl/big_lc_reverse.tif; exit \$rc"
echo BENCH_DONE
