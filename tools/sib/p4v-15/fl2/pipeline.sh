#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 First Letters push, PHerc0358, worker p4v-15 = SECOND (seed lane 1). Adapted from the fl-pherc0257 template
# (commit 54b29c96, tools/fl2/BRIEF_FL2.md item 2): the grow / render / infer / tiles commands are the template's, unchanged.
# Changes, parameters only: SCROLL/CT/SURF/UMB/branch/paths/names; 48 candidate seeds (fl.py plan table), lane 1 takes
# seed index % 2 == 1; NSEEDS=40; per-segment flow grow -> render -> infer -> tiles -> push (brief item 6); direction
# labels forward|reverse; tiles_<official|dense>/ with the brief item 5 manifest fields; DENSE arm once DENSE_OK.json
# (pilot) has been prepared locally into $W/dense/ (dense.env: DENSE_CKPT, DENSE_SHA).
# Resume: every unit leaves a marker (committed under $L, or $ST); finished units are skipped.
# Launch: setsid nohup bash tools/sib/p4v-15/fl2/watchdog.sh >/dev/null 2>&1 &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ME=p4v-15; LANE=1
BR=claude/gifted-bell-gavnl5-sib-$ME
SCROLL=PHerc0358; VOLUME=20250821151737; SL=pherc0358
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/$ME/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$ME/fl2/fl.py; export FL_SCROLL=$SCROLL
CT=s3://vesuvius-challenge-open-data/PHerc0358/volumes/20250821151737-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0358/representations/predictions/surfaces/20250821151737-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none   # PHerc0358 bucket listing 2026-10-01: photos/ representations/predictions/surfaces/ volumes/ (no umbilicus, no segments); fl.py seeds uses the CT-mask centroid axis
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
NCAND=48; NSEEDS=80; MIN_AREA=16; ROUNDS="0 1"   # NSEEDS = cumulative grow attempts over all seed rounds (40 per round)
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }
status() { echo "- $(date -u +%FT%TZ) $*" >> $L/STATUS.md; log "$*"; }

push() {  # commit + push this worker's outputs; retry with backoff
  cd "$REPO"; git add logs/sib/$ME/fl2 tools/sib/$ME/fl2 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "$ME: FL2 PHerc0358 $1 (DECL-FL-2)

DECL-FL-2 second worker (seed lane 1) unit; numbers and file lists only, no image viewed.

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016me3B1Lr8Gw9PGLyN8xWA3"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>$W/push.err && return 0
    git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 1. environment ----
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then   # container restart: dockerd is gone, the env marker is not
  log "env: docker down after restart; re-running setup_env.sh (idempotent)"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env re-setup FAILED"; exit 1; }
fi
if [ ! -f $ST/env.ok ]; then
  log "env: checks"
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_grow_seg_from_seed --help >/dev/null 2>&1; /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "env: vesuvius infer not importable"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests, imagecodecs" || { log "env: /opt/hv packages missing"; exit 1; }
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > $L/env.txt
  touch $ST/env.ok; status "env OK ($(tr '\n' ' ' < $L/env.txt))"; push "env"
fi

# ---- 2. segment source ----
if [ ! -f $L/s3_list.json ] || [ ! -f $ST/list.ok ]; then
  $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 || { log "list FAILED"; exit 1; }
  touch $ST/list.ok; status "s3 list: $($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))") organizer tifxyz segments"; push "s3 listing"
fi
NORG=$($PY -c "import json;print(len(json.load(open('$L/s3_list.json'))['tifxyz_segments']))")

# ---- DENSE arm (brief item 4): enabled once $W/dense/dense.env exists (made from the pilot's DENSE_OK.json) ----
ARMS="official"; DENSE_CKPT=""; DENSE_SHA=""
if [ -f $W/dense/dense.env ]; then
  source $W/dense/dense.env
  if echo "$DENSE_SHA  $DENSE_CKPT" | sha256sum -c --quiet 2>/dev/null; then ARMS="official dense"; else log "dense: sha mismatch; dense arm off"; fi
fi
ckpt_of() { [ "$1" = official ] && echo $CKPT || echo $DENSE_CKPT; }
sha_of() { [ "$1" = official ] && echo $CKPT_SHA || echo $DENSE_SHA; }

# ---- 3-4. per segment: render, infer (each arm), tiles (+push) ----
process() {  # process <segname> <source>
  local name=$1 source=$2 d=$W/seg/$1 O=$L/$1 R=$W/render/$1.zarr arm rc=0
  for arm in $ARMS; do [ -f $O/DONE_$arm ] || rc=1; done; [ $rc = 0 ] && return 0
  if [ ! -f $ST/render_$name.ok ] || [ ! -d $R ]; then
    rm -rf $R; mkdir -p $W/render $O; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { status "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok
  fi
  for arm in $ARMS; do
    [ -f $O/DONE_$arm ] && continue
    local I=$W/infer_$arm/$name P=$W/infer_$arm/$name/$name.tif T=$O/tiles_$arm
    if [ ! -f $ST/infer_${arm}_$name.ok ]; then
      mkdir -p $I; log "infer $arm $name (both directions, no TTA)"
      OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $(ckpt_of $arm) $P \
        --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_${arm}_$name.log 2>&1 || { status "infer $arm $name FAILED"; tail -20 $W/infer_${arm}_$name.log > $O/infer_$arm.log.tail; push "infer $arm $name failed"; continue; }
      touch $ST/infer_${arm}_$name.ok
    fi
    # the official infer writes <name>.tif (forward) and <name>_reverse.tif (reverse)
    local nt=0 tf=0 PF dl
    rm -f $T/manifest.json
    for PF in $I/*.tif; do
      [ -f "$PF" ] || continue; nt=$((nt+1))
      case "$(basename "$PF" .tif)" in "$name") dl=forward;; "${name}_reverse") dl=reverse;; *) log "tiles $arm $name: unexpected prediction $(basename $PF)"; tf=1; continue;; esac
      $PY $FL tiles $name $d $PF $dl $source $T $T/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $arm $name $dl FAILED"; tf=1; }
    done
    [ $nt -eq 2 ] && [ $tf -eq 0 ] || { status "tiles $arm $name: $nt prediction tifs, failure=$tf"; push "tiles $arm $name failed"; continue; }
    # brief item 5 manifest fields, per row (tile pixels and tiling untouched)
    $PY - $T/manifest.json "$SCROLL" "$VOLUME" "$arm" "$(sha_of $arm)" $L/grow/${name}_measure.json <<'PYEOF' || { status "manifest $arm $name FAILED"; continue; }
import json, sys
m, scroll, vol, arm, msha, meas = sys.argv[1:7]
d = json.load(open(m)); area = json.load(open(meas))["area_cm2"]
d.update(decl="DECL-FL-2", worker="p4v-15", seed_lane=1, model=arm, model_sha256=msha, volume=vol)
for t in d["tiles"]:
    t.update(scroll=scroll, volume=vol, model=arm, model_sha256=msha, segment_area_cm2=round(area, 4))
    g = meas.replace("_measure.json", ".json")
    t["seed_plan"] = json.load(open(g)).get("seed_plan", "none") if __import__("os").path.exists(g) else "organizer"
json.dump(d, open(m, "w"), indent=1)
PYEOF
    ( cd $I && sha256sum *.tif > $O/prediction_sha256_$arm.txt )
    touch $O/DONE_$arm; status "segment $name $arm: $($PY -c "import json;print(len(json.load(open('$T/manifest.json'))['tiles']))") tiles"; push "tiles $arm $name"
  done
  local all=0; for arm in $ARMS; do [ -f $O/DONE_$arm ] || all=1; done
  [ $all = 0 ] && rm -rf $R   # render zarr is regenerable; keep disk
  return $all
}

SEGS=()
if [ "$NORG" -gt 0 ]; then
  SOURCE=organizer; log "source: organizer ($NORG tifxyz segments); lane $LANE takes ranks with rank % 2 == $LANE"
  k=0
  for pre in $($PY -c "import json;[print(s['prefix']) for s in json.load(open('$L/s3_list.json'))['tifxyz_segments']]"); do
    k=$((k+1)); [ $(( (k-1) % 2 )) -eq $LANE ] || continue
    name=$(basename "$pre"); d=$W/seg/$name; mkdir -p $d
    for f in x.tif y.tif z.tif meta.json mask.tif; do
      [ -s $d/$f ] || curl -fsS -o $d/$f "$HTTPB/$pre/$f" || rm -f $d/$f
    done
    [ -s $d/x.tif ] || continue
    mkdir -p $L/grow $L/$name/tifxyz; [ -f $L/grow/${name}_measure.json ] || $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
    cp -n $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/
    SEGS+=("$name"); process $name organizer
  done
else
  SOURCE=auto; log "source: auto (no organizer tifxyz segments in the bucket)"
  ntry=0
  for RND in $ROUNDS; do
  SF=$L/seeds.json; [ $RND = 0 ] || SF=$L/seeds_r$RND.json
    if [ ! -f $SF ]; then
      FL_SEED_ROUND=$RND $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NCAND $SF >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; exit 1; }
      status "seeds: $($PY -c "import json;print(len(json.load(open('$SF'))['seeds']))") of $NCAND candidates (round $RND); lane $LANE takes index % 2 == $LANE"; push "seeds round $RND"
    fi
    NS=$($PY -c "import json;print(len(json.load(open('$SF'))['seeds']))")
    # seed_plan: "template" = one of fl.py's original 8 (z, azimuth) entries; "ext48" = the 40-entry DECL-FL-2 extension
    seedplan() { $PY -c "import json;s=json.load(open('$SF'))['seeds'][$1];P0=[(0.30,0),(0.45,90),(0.60,180),(0.75,270),(0.38,45),(0.53,135),(0.68,225),(0.83,315)];print('round$RND' if $RND else ('template' if (s['z_frac'],s['azimuth_deg']) in P0 else 'ext48'))"; }
    for ((i=LANE; i<NS && ntry<NSEEDS; i+=2)); do
      name=${SL}_${ME}_$([ $RND = 0 ] || echo r${RND}_)s$i; ntry=$((ntry+1)); R=$L/grow/$name.json; d=$W/seg/$name
      if [ ! -f $R ]; then
        mkdir -p $W/seg $L/grow; rm -rf $d
        read -r sx sy sz <<<"$($PY -c "import json;s=json.load(open('$SF'))['seeds'][$i]['seed_xyz'];print(*s)")"
        cat > $W/grow_params.json <<J
  {"mode":"seed","step_size":20,"generations":150,"min_area_cm":1.0,"voxelsize":9.362,"thread_limit":3,
   "cache_size":3000000000,"cache_root":"$W/vc_cache","use_cuda":false,"tgt_overlap_count":20,"search_effort":10}
J
        cp $W/grow_params.json $L/grow_params.json
        log "grow $name seed ($sx $sy $sz)"
        t0=$(date +%s)
        cd $W   # the grow app also writes a copy into its working directory; keep it out of the repo
        OMP_NUM_THREADS=3 timeout 8h /work/bin/vc vc_grow_seg_from_seed -v $SURF -t $d -p $W/grow_params.json \
          -s $sx $sy $sz --segment-name $name --skip-overlap-check > $W/grow_$name.log 2>&1; rc=$?; cd "$REPO"
        tail -40 $W/grow_$name.log > $L/grow/$name.log.tail
        # tolerate grow writing into a named subdirectory of -t
        if [ ! -f $d/x.tif ]; then xs=$(find $d -name x.tif 2>/dev/null | head -1); [ -n "$xs" ] && cp $(dirname $xs)/*.tif $(dirname $xs)/meta.json $d/ 2>/dev/null; fi
        ok=false; area=0; sc=null
        if [ -f $d/x.tif ]; then
          $PY $FL measure $d $L/grow/${name}_measure.json >> $L/pipeline.log 2>&1
          area=$($PY -c "import json;print(json.load(open('$L/grow/${name}_measure.json'))['area_cm2'])")
          (cd $W && /work/bin/vc vc_tifxyz_selfcross $d -o $W/selfcross_$name.json > /dev/null 2>&1); cp $W/selfcross_$name.json $L/grow/${name}_selfcross.json 2>/dev/null
          # vc_tifxyz_selfcross report: 'census' = one entry per quad triangulation; count transverse contacts over both,
          # and require the tool's own clean_of_transverse_self_intersection verdict to agree (else null = not kept)
          sc=$($PY -c "import json;r=json.load(open('$W/selfcross_$name.json'));n=sum(c['transverse'] for c in r['census']);print(n if (n==0)==bool(r['clean_of_transverse_self_intersection']) else 'null')" 2>/dev/null || echo null)
          [ "$sc" = "0" ] && $PY -c "import sys;sys.exit(0 if $area>=$MIN_AREA else 1)" && ok=true
        fi
        echo "{\"segment\":\"$name\",\"seed_index\":$i,\"seed_plan\":\"$(seedplan $i)\",\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
        if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; fi
        status "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; push "grow $name"
      fi
      if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
        [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
        SEGS+=("$name"); process $name auto
      fi
    done
  done
fi

NDONE=0; for name in "${SEGS[@]}"; do a=0; for arm in $ARMS; do [ -f $L/$name/DONE_$arm ] || a=1; done; [ $a = 0 ] && NDONE=$((NDONE+1)); done
if [ ${#SEGS[@]} -gt 0 ] && [ $NDONE -eq ${#SEGS[@]} ]; then
  status "PIPELINE COMPLETE (arms: $ARMS): source=$SOURCE segments=${#SEGS[@]}"; echo "$ARMS" > $L/PIPELINE_DONE; push "pipeline complete ($ARMS)"
else
  status "PIPELINE INCOMPLETE: $NDONE of ${#SEGS[@]} segments done (arms: $ARMS); watchdog retries"; push "pipeline incomplete"; exit 1
fi
