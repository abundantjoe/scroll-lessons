#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DECL-FL-2 First Letters push, PHerc1203, worker "census" = SECOND (seed lane 1). tools/fl2/BRIEF_FL2.md (sha256 0e07b757...).
# Template: fl-pherc0257 pipeline at 54b29c96 (per-unit logic unchanged). Parameters/paths changed per brief item 2:
#  - organizer raw tifxyz of PHerc1203 (s3 segments/raw/, coordinates of volume 20250820131727, as fl-pherc1203 NOTES),
#    the 5 T0 tracer test ids excluded (as the primary), ranked by fl.py list (x.tif size); lane 1 takes the odd ranks;
#    organizer segments are processed BEFORE any auto-grow (brief item 2);
#  - auto-grow: fl.py seeds ... 48, seeds with index % 2 == 1, names pherc1203_census_s<k>, NSEEDS 40, MIN_AREA 16 cm^2,
#    0 self-intersections (gate unchanged);
#  - tiles: every 2 x 2 cm cell with valid >= 50 %, both directions, OFFICIAL model only (DECL-FL-2-E1), written to
#    <SEG>/tiles_official/<SEG>_<forward|reverse>_rRR_cCC.png; manifest rows enriched (enrich_manifest.py).
# Detached, idempotent, pushes after every unit. Numbers only: no image is ever viewed.
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
BR=claude/gifted-bell-gavnl5-sib-census
ME=census; SCROLL=PHerc1203; LANE=1; VOLID=20250820131727
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/census/fl2; T=$REPO/tools/sib/census/fl2
PY=/opt/hv/bin/python; FL=$T/fl.py; export FL_SCROLL=$SCROLL
CT=s3://vesuvius-challenge-open-data/PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc1203/representations/predictions/surfaces/20250820131727-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc1203 has no organizer umbilicus (census products.json); fl.py seeds uses the CT-mask centroid axis
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NSEEDS=40; NSEEDCAND=48; MIN_AREA=16
T0="163217042 163219195 163223390 163227956 163230146"
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }

push() {  # one STATUS.md line per unit, then commit + push this worker's outputs (retry, rebase on rejection)
  cd "$REPO"; echo "$(date -u +%FT%TZ) $1" >> $L/STATUS.md
  flock /work/own/git.lock bash -c '
    git add '"$L"' '"$T"' >/dev/null 2>&1
    git diff --cached --quiet || git commit -q -m "census FL2 PHerc1203: $1

DECL-FL-2 compute worker unit (numbers and file lists only; no image viewed).

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FkYMAaqXwtCQvWWKzL2Gvv"
    for d in 2 4 8 16 32; do
      git push -q origin HEAD:'"$BR"' 2>>'"$W"'/push.err && exit 0
      git pull -q --rebase origin '"$BR"' 2>>'"$W"'/push.err; sleep $d
    done; exit 1' _ "$1" || log "WARN push failed for unit $1"
}

# ---- 1. environment ----
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then
  log "env: docker down after restart; re-running setup_env_fl2.sh (idempotent)"
  bash $T/setup_env_fl2.sh > $W/setup_env.log 2>&1 || { log "env re-setup FAILED"; exit 1; }
fi
if [ ! -f $ST/env.ok ]; then
  log "env: setup_env_fl2.sh"
  bash $T/setup_env_fl2.sh > $W/setup_env.log 2>&1 || { log "env FAILED (tail: $(tail -2 $W/setup_env.log | tr '\n' ' '))"; push "env FAILED"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_grow_seg_from_seed --help >/dev/null 2>&1; /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "env: vesuvius infer not importable"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests, imagecodecs" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs imagecodecs opencv-python-headless requests
  # voxel size from the volume's own metadata.json (never assumed); fl.py and the render use 9.362
  VOX=$(curl -fsS "$HTTPB/PHerc1203/volumes/20250820131727-9.362um-1.2m-113keV-masked.zarr/metadata.json" | $PY -c "import json,sys;print(json.load(sys.stdin)['scan']['tomo']['acquisition']['detector']['samplePixelSize'])")
  [ "$VOX" = "0.009362" ] || { log "env: metadata samplePixelSize $VOX != 0.009362"; push "env voxel mismatch"; exit 1; }
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; echo "voxel_mm_from_metadata $VOX"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > $L/env.txt
  touch $ST/env.ok; log "env: OK"; push "env OK"
fi

# ---- per-segment unit: render -> infer (both directions) -> tiles -> push ----
process_segment() {  # $1 name, $2 source (organizer|auto)
  local name=$1 SOURCE=$2; local d=$W/seg/$name O=$L/$name; mkdir -p $O
  [ -f $O/DONE ] && return 0
  local R=$W/render/$name.zarr P=$W/infer/$name/$name.tif
  if [ ! -f $ST/render_$name.ok ]; then
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_$name.ok ]; then
    mkdir -p $W/infer/$name; log "infer $name (official, both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_$name.log 2>&1 || { log "infer $name FAILED"; tail -20 $W/infer_$name.log > $O/infer.log.tail; push "infer $name failed"; return 1; }
    touch $ST/infer_$name.ok
  fi
  local nt=0 tf=0 PF dl
  for PF in $W/infer/$name/*.tif; do
    [ -f "$PF" ] || continue; nt=$((nt+1))
    case "$(basename "$PF" .tif)" in *_reverse) dl=reverse;; *) dl=forward;; esac
    $PY $FL tiles $name $d $PF $dl $SOURCE $O/tiles_official $O/tiles_official/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $dl FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name: $nt prediction tifs, failure=$tf"; push "tiles $name failed"; return 1; }
  $PY $T/enrich_manifest.py $O/tiles_official/manifest.json $SCROLL $VOLID official $CKPT_SHA $O/measure.json $O/tifxyz >> $L/pipeline.log 2>&1 || { log "manifest $name FAILED"; push "manifest $name failed"; return 1; }
  ( cd $W/infer/$name && sha256sum *.tif > $O/prediction_sha256.txt )
  local nk=$($PY -c "import json;print(len(json.load(open('$O/tiles_official/manifest.json'))['tiles']))")
  touch $O/DONE; log "segment $name: $nk tiles"; push "tiles $name ($SOURCE): $nk tiles"
  rm -rf $R
}

# ---- 2. organizer segments (all, lane 1 = odd ranks, T0 excluded), before any auto-grow ----
if [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  $PY - "$L/s3_list.json" "$L/organizer_selection.json" "$T0" "$LANE" <<'EOF'
import json, sys
lst, out, t0, lane = sys.argv[1], sys.argv[2], sys.argv[3].split(), int(sys.argv[4])
allsegs = json.load(open(lst))["tifxyz_segments"]
# fl.py list also returns <segment>/versions/<n> edit-history snapshots (same sheets); only top-level segments count
segs = [s for s in allsegs if "/versions/" not in s["prefix"]]
kept = [s for s in segs if not any(t in s["prefix"] for t in t0)]
rows = [dict(rank=i, prefix=s["prefix"], x_tif_bytes=s["x_tif_bytes"], lane=i % 2, mine=(i % 2 == lane)) for i, s in enumerate(kept)]
json.dump({"rule": "fl.py list order (x.tif bytes, largest first), T0 tracer test ids excluded; primary even ranks, second odd",
           "excluded_version_snapshots": len(allsegs) - len(segs),
           "excluded_T0": [s["prefix"] for s in segs if any(t in s["prefix"] for t in t0)], "ranked": rows}, open(out, "w"), indent=1)
print(f"organizer: {len(allsegs)} listed, {len(segs)} top-level, {len(kept)} after T0 exclusion, {sum(r['mine'] for r in rows)} for lane {lane}")
EOF
  touch $ST/list.ok; push "s3 listing and organizer selection"
fi
for pre in $($PY -c "import json;[print(r['prefix']) for r in json.load(open('$L/organizer_selection.json'))['ranked'] if r['mine']]"); do
  name=$(basename "$pre"); d=$W/seg/$name; O=$L/$name; mkdir -p $d $O/tifxyz
  [ -f $O/DONE ] && continue
  for f in x.tif y.tif z.tif meta.json mask.tif; do
    [ -s $d/$f ] || curl -fsS -o $d/$f "$HTTPB/$pre/$f" || rm -f $d/$f
  done
  [ -s $d/x.tif ] || { log "organizer $name: download failed"; push "organizer $name download failed"; continue; }
  cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $O/tifxyz/
  [ -f $O/measure.json ] || $PY $FL measure $d $O/measure.json >> $L/pipeline.log 2>&1
  [ -f $O/selfcross.json ] || /work/bin/vc vc_tifxyz_selfcross $d -o $O/selfcross.json > /dev/null 2>&1   # recorded, not a gate for organizer segments
  process_segment $name organizer
done

# ---- 3. auto-grow (lane 1 seeds), after the organizer segments ----
if [ ! -f $L/seeds.json ]; then
  $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NSEEDCAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; push "seeds FAILED"; exit 1; }
  push "seeds ($($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))") candidates)"
fi
NS=$($PY -c "import json;print(len(json.load(open('$L/seeds.json'))['seeds']))")
ntry=0
for ((k=0; k<NS && ntry<NSEEDS; k++)); do
  [ $((k % 2)) -eq $LANE ] || continue
  ntry=$((ntry+1)); name=pherc1203_census_s$k; R=$L/grow/$name.json; d=$W/seg/$name
  if [ ! -f $R ]; then
    mkdir -p $W/seg $L/grow; rm -rf $d
    read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$L/seeds.json'))['seeds'][$k]['seed_xyz'];print(*s)")"
    cat > $W/grow_params.json <<J
{"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":9.362,"thread_limit":3,
 "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
    cp $W/grow_params.json $L/grow_params.json
    log "grow $name seed ($sx $sy $sz)"; t0=$(date +%s)
    cd $W
    OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $d -p $W/grow_params.json \
      -s $sx $sy $sz --segment-name $name --skip-overlap-check > $W/grow_$name.log 2>&1; rc=$?; cd "$REPO"
    tail -40 $W/grow_$name.log > $L/grow/$name.log.tail
    if [ ! -f $d/x.tif ]; then xs=$(find $d -name x.tif 2>/dev/null | head -1); [ -n "$xs" ] && cp $(dirname $xs)/*.tif $(dirname $xs)/meta.json $d/ 2>/dev/null; fi
    ok=false; area=0; sc=null
    if [ -f $d/x.tif ]; then
      $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
      area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
      /work/bin/vc vc_tifxyz_selfcross $d -o $W/selfcross_$name.json > /dev/null 2>&1; cp $W/selfcross_$name.json $L/grow/${name}_selfcross.json 2>/dev/null
      sc=$($PY -c "import json;r=json.load(open('$W/selfcross_$name.json'));n=sum(c['transverse'] for c in r['census']);print(n if (n==0)==bool(r['clean_of_transverse_self_intersection']) else 'null')" 2>/dev/null || echo null)
      [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
    fi
    echo "{\"segment\":\"$name\",\"seed_index\":$k,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
    if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; cp $L/grow/${name}_measure.json $L/$name/measure.json; fi
    log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; push "grow $name: area $area cm2, selfx $sc, kept $ok"
  fi
  if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
    [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
    process_segment $name auto
  fi
done
log "PIPELINE PASS END: lane $LANE, $ntry grow attempts of $NS candidate seeds"
touch $L/PIPELINE_DONE; push "pipeline pass complete (lane $LANE, $ntry grow attempts, $NS seeds)"
