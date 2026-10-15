#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 item 4 positive-control gate, OFFICIAL arm only (pairs0139c). Official data only:
# organizer segment PHerc0139 20260422000000-title_2026042222_zmid_flatboi (9.362 um tifxyz), volume
# 20250728140407-9.362um, render exactly as template fl-pherc0257@54b29c96 pipeline.sh (C2-NT), official ink_9um
# step-075000 (sha e635558a), both directions, no TTA, then the template cmd_tiles UNCHANGED.
# No community code, coordinates or weights are used (session integrity rule); DENSE arm not run (see ASK).
set -uo pipefail
REPO=/home/user/dominion; cd "$REPO"; BR=claude/gifted-bell-gavnl5-sib-pairs0139c
L=logs/sib/pairs0139c/fl2_gate; W=/work/fl2gate; ST=$W/state; mkdir -p $W $ST $L
SEG=20260422000000-title_2026042222_zmid_flatboi; TS=20260422000000
VOL=s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth; CKSHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
utc() { date -u +%FT%TZ; }
log() { echo "$(utc) $*" >> $L/STATUS.md; }
push() { ( flock 9; git add $L; git commit -q -m "pairs0139c: fl2 gate $1 (DECL-FL-2 item 4)

Provenance: Project HERCULES | [id removed]" -- $L; for i in 1 2 3 4; do git push -q origin $BR && break; sleep $((2**i)); done ) 9>/work/own/git.lock; }
# 1. environment (setup_env.sh; vesuvius with pip --ignore-requires-python if uv refuses; imagecodecs in /opt/hv)
if [ ! -f $ST/env.ok ]; then
  bash docker/env/setup_env.sh > $W/setup_env.log 2>&1; rc=$?
  if [ $rc -ne 0 ] || ! /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null; then
    [ -x /opt/hv-ink/bin/python ] || { uv venv /opt/hv-ink --python 3.13 -q && VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu; } >> $W/setup_env.log 2>&1
    VIRTUAL_ENV=/opt/hv-ink uv pip install -q pip >> $W/setup_env.log 2>&1
    /opt/hv-ink/bin/python -m pip install -q --ignore-requires-python --no-deps -e /work/villa/vesuvius >> $W/setup_env.log 2>&1
    VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r docker/env/hv-ink-freeze.txt --no-deps >> $W/setup_env.log 2>&1 || true
    bash docker/env/setup_env.sh >> $W/setup_env.log 2>&1; rc=$?
  fi
  [ -x /opt/hv/bin/python ] && VIRTUAL_ENV=/opt/hv uv pip install -q imagecodecs >> $W/setup_env.log 2>&1
  ok=1; /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null || ok=0
  echo "$CKSHA  $CKPT" | sha256sum -c --quiet 2>/dev/null || ok=0
  /work/bin/vc vc_render_tifxyz --help > /dev/null 2>&1 || ok=0
  [ "$(git -C /work/villa rev-parse HEAD)" = 41701aa0eaa1aa765523db3f9f972b5830abf549 ] || ok=0
  if [ $ok -eq 1 ]; then touch $ST/env.ok; log "env OK (villa 41701aa, ckpt sha e635558a verified, vesuvius infer importable)"; else log "env FAILED (setup_env rc=$rc; see /work/fl2gate/setup_env.log)"; push "env failed"; echo GATE_END; exit 1; fi
  push "env"
fi
# 2. organizer title segment, 9.362 um tifxyz (sha256 recorded)
d=$W/seg/$SEG
if [ ! -f $ST/seg.ok ]; then
  mkdir -p $d $L/tifxyz
  for f in meta.json x.tif y.tif z.tif; do
    curl -fsSL --retry 4 -o $d/$f "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/$SEG/mesh/$TS-on-20250728140407-9.362um.tifxyz/$f" || { log "fetch $f FAILED"; push "fetch failed"; echo GATE_END; exit 1; }
  done
  ( cd $d && sha256sum meta.json x.tif y.tif z.tif ) > $L/tifxyz/sha256.txt; cp $d/meta.json $L/tifxyz/meta.json
  curl -fsSL -o $W/vol_meta.json "${VOL/s3:\/\/vesuvius-challenge-open-data/https://vesuvius-challenge-open-data.s3.amazonaws.com}metadata.json"
  echo "$(sha256sum $W/vol_meta.json | cut -c1-64)  volume metadata.json" >> $L/tifxyz/sha256.txt
  FL_SCROLL=PHerc0139 /opt/hv/bin/python tools/sib/fl-pherc0257/fl.py measure $d $L/measure.json >> $W/gate.log 2>&1
  touch $ST/seg.ok; log "segment $SEG fetched (9.362 um tifxyz; sha256 in tifxyz/sha256.txt); measure.json written"; push "segment"
fi
VS=$(/opt/hv/bin/python -c "import json;d=json.load(open('$W/vol_meta.json'));print(float(d['scan']['tomo']['acquisition']['detector']['samplePixelSize'])*1000)")
# 3. render (template C2-NT command; voxel size from the volume metadata.json)
R=$W/render/$SEG.zarr
if [ ! -f $ST/render.ok ]; then
  rm -rf $R; mkdir -p $W/render; s=$(utc)
  /work/bin/vc vc_render_tifxyz -v $VOL --remote-url $VOL --segmentation $d --scale 1 --group-idx 0 \
    --num-slices 31 --slice-step 1 --voxel-size $VS --voxel-unit micrometer --flip-normals \
    --cache-gb 4 --zarr-output $R > $W/render.log 2>&1; rc=$?
  echo "{\"step\":\"render\",\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"voxel_size_um\":$VS,\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/render.log|cut -c1-64)\"}" >> $L/runs.jsonl
  [ $rc -eq 0 ] || { log "render FAILED rc=$rc"; tail -20 $W/render.log > $L/render.log.tail; push "render failed"; echo GATE_END; exit 1; }
  touch $ST/render.ok; log "render done (voxel ${VS} um from metadata.json)"; push "render"
fi
# 4. official infer, both directions, no TTA, CPU
P=$W/infer/$SEG.tif
if [ ! -f $ST/infer.ok ]; then
  mkdir -p $W/infer; s=$(utc)
  OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
    --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer.log 2>&1; rc=$?
  echo "{\"step\":\"infer_official\",\"utc_start\":\"$s\",\"utc_end\":\"$(utc)\",\"exit\":$rc,\"log_sha256\":\"$(sha256sum $W/infer.log|cut -c1-64)\"}" >> $L/runs.jsonl
  [ $rc -eq 0 ] || { log "infer FAILED rc=$rc"; tail -20 $W/infer.log > $L/infer.log.tail; push "infer failed"; echo GATE_END; exit 1; }
  ( cd $W/infer && sha256sum *.tif ) > $L/prediction_sha256_official.txt
  touch $ST/infer.ok; log "official infer done (both directions)"; push "infer official"
fi
# 5. template cmd_tiles, unchanged, both directions
mkdir -p $L/tiles_official
for PF in $W/infer/*.tif; do
  dl=$(basename $PF .tif); case $dl in *reverse*) dl=reverse;; *) dl=forward;; esac
  FL_SCROLL=PHerc0139 /opt/hv/bin/python tools/sib/fl-pherc0257/fl.py tiles $SEG $d $PF $dl organizer $L/tiles_official $L/tiles_official/manifest.json >> $W/gate.log 2>&1
done
grep "^tiles " $W/gate.log | tail -2 > $L/tiles_official/tiler_output.txt
/opt/hv/bin/python - $L/tiles_official/manifest.json $L/measure.json <<'PY' >> $L/STATUS.md
import json, sys, datetime
m = json.load(open(sys.argv[1])); me = json.load(open(sys.argv[2]))
T = m["tile_src_px"]; H, Wd = m["canvas_hw"]
print(f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ} tiles_official: {len(m['tiles'])} kept; canvas {H} x {Wd} px "
      f"({H*m['voxel_um']/1e4:.2f} x {Wd*m['voxel_um']/1e4:.2f} cm), tile {T} px (2 cm); grid rows {H//T}, cols {Wd//T}; mesh area {me['area_cm2']:.2f} cm2")
PY
push "tiles official"
echo GATE_END
