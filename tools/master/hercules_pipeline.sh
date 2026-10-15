#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# HERCULES master pipeline, one shot per scroll (DECL-E2E-1 + DECL-UMB-2/A1 + DECL-UNR-1 + DECL-FL-7), native resolution end to end:
#   S0 frame survey (level 4, bookkeeping only: roll axis / stacking axis, mask bbox)          -> frame.json
#   S1 umbilicus: U-turn operator on the band's y positions, bars B1-B5 (tools/umb/core_native.py, umb2_bars.py) -> umbilicus/, umbilicus_checks.json
#   S2 sheet trace over the band at level 0 (tools/master/e2e_sheet.py trace)                  -> surface.npz, surface_tifxyz/, trace_checks.json (G1-G3)
#   S3 mesh checks: self-intersection, neighbour crossing, uv distortion (tools/unr/mesh_checks.py) -> mesh_checks.json (G4)
#   S4 render 17 layers along the normal at every y of the band (e2e_sheet.py render)           -> render.npz, centre.png, render_checks.json (G5, fibres)
#   S5 master ink model forward + reverse (e2e_sheet.py ink)                                     -> ink_fwd.png, ink_rev.png, ink_checks.json
#   S6 gold painting + every bar in one file (e2e_sheet.py gold)                                -> gold.png, gold_preview.png, checks.json
# usage: hercules_pipeline.sh <config.json> <out_dir> [stages: 0123456]      (stages run in order; a stage is skipped if its output exists)
set -uo pipefail; CFG=$1; OUT=$2; ST=${3:-0123456}; REPO=/home/user/dominion; cd $REPO; PY=/opt/hv/bin/python; PYT=/opt/hv-ink/bin/python; mkdir -p $OUT /dev/shm/e2e
NAME=$($PY -c "import json;print(json.load(open('$CFG'))['name'])"); L4=$($PY -c "import json;print(json.load(open('$CFG'))['ct_l4'])"); L4NPY=/dev/shm/e2e/ct_L4_$NAME.npy
log(){ echo "[$(date -u +%FT%TZ)] $NAME $*" | tee -a $OUT/pipeline.log; }
has(){ [[ "$ST" == *$1* ]]; }
if has 0; then
  [ -f $L4NPY ] || { log "S0 fetch level 4"; $PY tools/umb/fetch_zarr.py $L4 $L4NPY > $OUT/fetch_L4.log 2>&1 || { log "S0 level-4 fetch failed"; exit 1; }; }
  [ -f $OUT/frame.json ] || { log "S0 frame survey"; OMP_NUM_THREADS=2 $PY tools/unr/frame_test.py $L4NPY $OUT/frame.json --name $NAME > $OUT/frame.log 2>&1 || log "S0 frame survey failed (recorded, pipeline continues)"; }
fi
if has 1; then
  YS=$($PY -c "import json;print(' '.join(str(y) for y in json.load(open('$CFG'))['umbilicus_y']))")
  mkdir -p $OUT/umbilicus; [ -f $OUT/umbilicus/core_native.json ] && [ -f $OUT/umbilicus/DONE ] || { log "S1 umbilicus at y $YS"; OMP_NUM_THREADS=2 $PY tools/umb/core_native.py $OUT/umbilicus --l3 /nonexistent --depth_mm 0 --cache "" --y $YS > $OUT/umbilicus/core_native.log 2>&1 || log "S1 core_native failed (recorded)"; }
  $PY tools/umb/umb2_bars.py $OUT/umbilicus_checks.json --glob "$OUT/umbilicus/core_native.json" --md $OUT/umbilicus_table.md > $OUT/umb2_bars.log 2>&1 || log "S1 bars failed (recorded)"
fi
if has 2; then [ -f $OUT/surface.npz ] || { log "S2 sheet trace"; OMP_NUM_THREADS=3 $PY tools/master/e2e_sheet.py trace $CFG $OUT --ct_l4 $L4NPY > $OUT/trace.log 2>&1 || { log "S2 trace failed: $(tail -1 $OUT/trace.log)"; exit 2; }; }; fi
if has 3; then [ -f $OUT/mesh_checks.json ] || { log "S3 mesh checks"; OMP_NUM_THREADS=2 $PY tools/unr/mesh_checks.py check $OUT/surface_tifxyz $OUT/mesh_checks.json > $OUT/mesh_checks.log 2>&1 || log "S3 mesh checks failed (recorded)"; }; fi
if has 4; then [ -f $OUT/render.npz ] || { log "S4 render"; OMP_NUM_THREADS=3 $PY tools/master/e2e_sheet.py render $CFG $OUT > $OUT/render.log 2>&1 || { log "S4 render failed: $(tail -1 $OUT/render.log)"; exit 4; }; }; fi
if has 5; then [ -f $OUT/ink.npz ] || { log "S5 master ink model"; OMP_NUM_THREADS=4 $PYT tools/master/e2e_sheet.py ink $CFG $OUT > $OUT/ink.log 2>&1 || { log "S5 ink failed: $(tail -1 $OUT/ink.log)"; exit 5; }; }; fi
if has 6; then log "S6 gold + checks"; $PY tools/master/e2e_sheet.py gold $CFG $OUT > $OUT/gold.log 2>&1 || { log "S6 gold failed: $(tail -1 $OUT/gold.log)"; exit 6; }; fi
log "DONE: $(python3 -c "import json;c=json.load(open('$OUT/checks.json'));print({k:v for k,v in c.get('gold',{}).items() if k!='statement'})" 2>/dev/null)"; touch $OUT/DONE
