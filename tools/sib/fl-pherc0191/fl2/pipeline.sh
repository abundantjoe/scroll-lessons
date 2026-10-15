#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 First Letters push, PHerc0191, worker fl-pherc0191 = PRIMARY (seed lane 0). tools/fl2/BRIEF_FL2.md items 1-6.
# Template: tools/sib/fl-pherc0257/{pipeline.sh,fl.py} @54b29c96, logic unchanged; parameters per brief item 2, plus:
#  - per item 6, each segment goes grow -> render -> infer -> tile -> push before the next grow (process_seg);
#  - per item 5, tiles go to <SEG>/tiles_official/<SEG>_<forward|reverse>_rRR_cCC.png and the manifest rows gain
#    scroll, volume, model, model_sha256, segment_area_cm2 (annotate step; the tile computation is fl.py cmd_tiles unchanged);
#  - the 4 DECL-FL-1 segments pherc0191_auto_0..3 (0 self-intersections, >= 16 cm^2, tifxyz pushed) are processed first.
# Bucket (2026-09-30): no organizer tifxyz segments and no umbilicus for PHerc0191 -> auto-grow, UMB=none.
# Launch: setsid nohup bash tools/sib/fl-pherc0191/fl2/watchdog.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
ME=fl-pherc0191; BR=claude/gifted-bell-gavnl5-sib-$ME
SCROLL=PHerc0191; VOLUME=20250821151635; LANE=0; NSEEDS_CAND=48; NSEEDS=80; ROUNDS="0 1";   # owner order 06:00Z: seed list extended by one round (+40)
 MIN_AREA=16
W=/work/fl2; ST=$W/state; L=$REPO/logs/sib/$ME/fl2
PY=/opt/hv/bin/python; FL=$REPO/tools/sib/$ME/fl2/fl.py; export FL_SCROLL=$SCROLL
CT=s3://vesuvius-challenge-open-data/PHerc0191/volumes/20250821151635-9.362um-1.2m-113keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0191/representations/predictions/surfaces/20250821151635-surface-20260413222639-surface-m7-L0-th0.2.zarr/
HTTPB=https://vesuvius-challenge-open-data.s3.amazonaws.com
UMB=none
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
FL1=$REPO/logs/sib/$ME   # DECL-FL-1 outputs (reused segments)
mkdir -p $W $ST $L
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a $L/pipeline.log; }
status() { echo "$(date -u +%FT%TZ) $*" >> $L/STATUS.md; }

push() {  # commit + push this worker's outputs; retry with backoff, rebase on rejection
  local d   # FIX 2026-10-01: the retry loop below used the global $d (segment dir) -> "2" after a push
  cd "$REPO"; git add logs/sib/$ME/fl2 tools/sib/$ME/fl2 >/dev/null 2>&1
  git diff --cached --quiet || git commit -q -m "$ME fl2: $1

DECL-FL-2 compute worker unit (numbers and file lists only; no image viewed).

Provenance: Project HERCULES | [id removed]"
  for d in 2 4 8 16 32; do
    git push -q -u origin $BR 2>>$W/push.err && return 0
    git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d
  done; log "WARN push failed for unit $1"
}

# ---- 1. environment ----
if [ -f $ST/env.ok ] && ! docker info >/dev/null 2>&1; then
  log "env: docker down after restart; re-running setup_env.sh (idempotent)"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env re-setup FAILED"; exit 1; }
fi
if [ ! -f $ST/env.ok ]; then
  log "env: setup_env.sh"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env FAILED (tail: $(tail -2 $W/setup_env.log | tr '\n' ' '))"; status "env FAILED"; push "env failed"; exit 1; }
  docker info >/dev/null 2>&1 || { log "env: docker not running"; exit 1; }
  /work/bin/vc vc_render_tifxyz --help > $W/render_help.txt 2>&1 || { log "env: vc_render_tifxyz unusable"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "env: checkpoint sha mismatch"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "env: vesuvius infer not importable"; exit 1; }
  $PY -c "import numcodecs, cv2, tifffile, boto3, requests, imagecodecs" || VIRTUAL_ENV=/opt/hv uv pip install -q numcodecs imagecodecs
  { echo "villa $(git -C /work/villa rev-parse HEAD)"; echo "ckpt_sha256 $CKPT_SHA"; /opt/hv-ink/bin/python -c "import torch;print('torch',torch.__version__)"; } > $L/env.txt
  touch $ST/env.ok; log "env: OK"; status "env OK"
fi

# ---- per-segment chain: render -> infer (official) -> tiles -> annotate -> push ----
process_seg() {  # name segdir source area_cm2
  local name=$1 d=$2 source=$3 area=$4 O=$L/$1 R P nt tf PF stem dl
  mkdir -p $O/tiles_official
  [ -f $O/DONE_official ] && return 0
  R=$W/render/$name.zarr; P=$W/infer/$name/$name.tif
  if [ ! -f $ST/render_$name.ok ]; then
    local fr; fr=$(df --output=avail -BG /work | tail -1 | tr -dc 0-9)
    [ "${fr:-0}" -ge 6 ] || { log "render $name: only ${fr} GB free, skipped"; status "$name render SKIPPED (disk ${fr} GB)"; push "disk low"; return 1; }
    rm -rf $R; mkdir -p $W/render; log "render $name"
    /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 \
      --num-slices 31 --slice-step 1 --voxel-size 9.362 --voxel-unit micrometer --flip-normals \
      --cache-gb 4 --zarr-output $R > $W/render_$name.log 2>&1 || { log "render $name FAILED"; tail -20 $W/render_$name.log > $O/render.log.tail; status "$name render FAILED"; push "render $name failed"; return 1; }
    touch $ST/render_$name.ok
  fi
  if [ ! -f $ST/infer_$name.ok ]; then
    mkdir -p $W/infer/$name; log "infer $name (official, both directions, no TTA)"
    OMP_NUM_THREADS=3 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $R $CKPT $P \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $W/infer_$name.log 2>&1 || { log "infer $name FAILED"; tail -20 $W/infer_$name.log > $O/infer.log.tail; status "$name infer FAILED"; push "infer $name failed"; return 1; }
    touch $ST/infer_$name.ok
  fi
  nt=0; tf=0
  for PF in $W/infer/$name/*.tif; do
    [ -f "$PF" ] || continue; nt=$((nt+1)); stem=$(basename "$PF" .tif)
    case "$stem" in "$name") dl=forward;; "${name}_reverse") dl=reverse;; *) dl=$stem;; esac
    $PY $FL tiles $name $d $PF $dl $source $O/tiles_official $O/tiles_official/manifest.json >> $L/pipeline.log 2>&1 || { log "tiles $name $dl FAILED"; tf=1; }
  done
  [ $nt -ge 1 ] && [ $tf -eq 0 ] || { log "tiles $name: $nt prediction tifs, failure=$tf"; status "$name tiles FAILED"; push "tiles $name failed"; return 1; }
  $PY - "$O/tiles_official/manifest.json" "$SCROLL" "$VOLUME" "$CKPT_SHA" "$area" "$d" <<'EOF'
import json, sys, hashlib, os
p, scroll, vol, sha, area, d = sys.argv[1:]
m = json.load(open(p))
tx = {f: hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest() for f in ('x.tif', 'y.tif', 'z.tif') if os.path.exists(os.path.join(d, f))}
m.update(decl="DECL-FL-2", volume=vol, model="official ink_9um hybrid_3d2d-seed42 step-075000", model_sha256=sha,
         segment_area_cm2=float(area), tifxyz_sha256=tx)
for t in m["tiles"]:
    t.update(scroll=scroll, volume=vol, model="official", model_sha256=sha, segment_area_cm2=round(float(area), 4))
json.dump(m, open(p, "w"), indent=1)
print(len(m["tiles"]))
EOF
  ( cd $W/infer/$name && sha256sum *.tif > $O/prediction_sha256_official.txt )
  mkdir -p $O/tifxyz; for f in x.tif y.tif z.tif meta.json; do [ -f $O/tifxyz/$f ] || cp $d/$f $O/tifxyz/ 2>/dev/null; done
  local n; n=$($PY -c "import json;print(len(json.load(open('$O/tiles_official/manifest.json'))['tiles']))")
  touch $O/DONE_official; log "segment $name: $n official tiles"; status "$name official tiles=$n area_cm2=$area source=$source"
  push "tiles $name official ($n)"
  rm -rf $R   # render zarr is regenerable; keep disk
}

# ---- 2. reused DECL-FL-1 segments first ----
for k in 0 1 2 3; do
  name=pherc0191_auto_$k; src=$FL1/$name/tifxyz
  grep -q '^accepted' $FL1/state/grow_$k.done 2>/dev/null && [ -f $src/x.tif ] || continue
  d=$W/seg/$name; [ -f $d/x.tif ] || { mkdir -p $d; cp $src/* $d/; }
  area=$(sed -n 's/.*area_cm2=\([0-9.]*\).*/\1/p' $FL1/state/grow_$k.done)
  process_seg $name $d decl-fl-1-auto "$area"
done

# ---- 3. auto-grow, lane 0 (even seed indices), one segment at a time ----
if [ ! -f $L/s3_list.json ]; then $PY $FL list $SCROLL $L/s3_list.json >> $L/pipeline.log 2>&1 && push "s3 listing"; fi
if [ ! -f $L/seeds.json ]; then
  $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NSEEDS_CAND $L/seeds.json >> $L/pipeline.log 2>&1 || { log "seeds FAILED"; status "seeds FAILED"; push "seeds failed"; exit 1; }
  push "seeds ($NSEEDS_CAND candidates)"
fi
ntry=0
for RND in $ROUNDS; do
if [ $RND = 0 ]; then SF=$L/seeds.json; PFX=s; else SF=$L/seeds_r$RND.json; PFX=r${RND}s
  if [ ! -f $SF ]; then
    $PY $FL seeds ${CT/s3:\/\/vesuvius-challenge-open-data/$HTTPB} ${SURF/s3:\/\/vesuvius-challenge-open-data/$HTTPB} $UMB $NSEEDS_CAND $SF $RND >> $L/pipeline.log 2>&1 || { log "seeds round $RND FAILED"; status "seeds round $RND FAILED"; push "seeds r$RND failed"; continue; }
    push "seeds round $RND"
  fi
fi
NS=$($PY -c "import json;print(len(json.load(open('$SF'))['seeds']))")
for i in $(seq $LANE 2 $((NS-1))); do
  [ $ntry -ge $NSEEDS ] && break
  ntry=$((ntry+1)); name=pherc0191_${ME}_$PFX$i; R=$L/grow/$name.json; d=$W/seg/$name
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
    echo "{\"segment\":\"$name\",\"seed_index\":$i,\"seed\":[$sx,$sy,$sz],\"rc\":$rc,\"secs\":$(( $(date +%s)-t0 )),\"area_cm2\":$area,\"self_intersections\":$sc,\"kept\":$ok}" > $R
    if $ok; then mkdir -p $L/$name/tifxyz; cp $d/x.tif $d/y.tif $d/z.tif $d/meta.json $L/$name/tifxyz/; fi
    log "grow $name: rc=$rc area=$area cm2 selfx=$sc kept=$ok"; status "$name grow rc=$rc area_cm2=$area selfx=$sc kept=$ok"
    push "grow $name"
  fi
  if [ "$($PY -c "import json;print(json.load(open('$R'))['kept'])")" = "True" ]; then
    [ -f $d/x.tif ] || { mkdir -p $d; cp $L/$name/tifxyz/* $d/; }
    process_seg $name $d auto "$($PY -c "import json;print(json.load(open('$R'))['area_cm2'])")"
  fi
done
done
log "PIPELINE PASS COMPLETE (lane $LANE, $ntry grow attempts)"; status "official pass complete ($ntry grow attempts)"
touch $L/PIPELINE_DONE; push "pipeline pass complete"
