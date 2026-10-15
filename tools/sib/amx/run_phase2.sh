#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Items 4, 5, int8 probe, synthetic bf16 chain, then a replicate of the item-3 grid. Strictly sequential.
cd /home/user/dominion
R=tools/sib/amx/run.sh
L=logs/sib/amx
export PYTHONPATH=/work/amx/pylib
[ -f $L/profile_split.json ] || $R profile_split "cd tools/sib/amx && /opt/hv-ink/bin/python profile_split.py --threads 4 --out ../../../$L/profile_split.json"
[ -f $L/cache_path.json ] || $R cache_path "cd tools/sib/amx && /opt/hv-ink/bin/python cache_path.py --threads 4 --out ../../../$L/cache_path.json"
[ -f $L/int8_feas.json ] || $R int8_feas "cd tools/sib/amx && /opt/hv-ink/bin/python int8_feas.py --threads 4 --out ../../../$L/int8_feas.json"
[ -f $L/synth_chain_gate.json ] || $R synth_chain "/opt/hv-ink/bin/python tools/sib/amx/synth_chain.py $L/synth_chain_gate.json"
$R bench_grid_rep "GRID_OUT=/home/user/dominion/$L/bench_grid_rep.jsonl tools/sib/amx/run_grid.sh"
echo PHASE2_DONE
