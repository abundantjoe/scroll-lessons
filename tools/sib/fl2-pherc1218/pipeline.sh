#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# RULES.md DECL-FL-1 / OWNER-STANDING-ORDER-5, tools/fl/BRIEF_PASS.md (dcb6a6b): First Letters extra pass,
# SCROLL PHerc1218, PASS 2 (worker on branch claude/gifted-bell-gavnl5-sib-trainer).
# PHerc1218 has no organizer segments in the bucket, so PASS 2 auto-grows up to 4 segments seeded in the OUTER
# third of the scroll radius (rules fixed in tools/sib/fl2-pherc1218/fl2.py before any data is read).
# Idempotent: every stage writes a marker under /work/fl2_1218/state and is skipped when present; results are
# committed and pushed after each unit. Every stage appends a row to logs/sib/fl2-pherc1218/runs.jsonl.
# Run detached with its own restart loop:
#   setsid nohup bash tools/sib/fl2-pherc1218/pipeline.sh --loop > /work/logs/fl2_1218.log 2>&1 &
# Never opens or views an image; PNG tiles are written for the census only.
set -uo pipefail
REPO=/home/user/dominion
cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-trainer
W=/work/fl2_1218; ST=$W/state; OUT=logs/sib/fl2-pherc1218
P=/opt/hv/bin/python; FL=tools/sib/fl2-pherc1218/fl2.py
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
VOL_URL=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc1218/volumes/20250521120456-8.640um-1.2m-116keV-masked.zarr
MIN_FREE_GB=8
mkdir -p $ST $OUT /work/logs /work/vchome

if [ "${1:-}" = "--loop" ]; then
  exec 9>$W/loop.lock; flock -n 9 || { echo "loop already running"; exit 0; }
  for i in $(seq 1 20); do
    bash "$0" && { echo "PIPELINE DONE $(date -u +%FT%TZ)"; exit 0; }
    echo "pipeline failed (attempt $i), restart in 120 s $(date -u +%FT%TZ)"; sleep 120
  done
  echo "$(date -u +%FT%TZ) fl2-pherc1218: GAVE UP after 20 attempts (see /work/logs/fl2_1218.log)" >> $OUT/STATUS.md
  MSG="gave up" ; git add $OUT/STATUS.md; git commit -q -m "fl2-pherc1218: gave up after 20 attempts

Provenance: Project HERCULES | owner the owner | [id removed]" && git push -q origin $BR
  exit 1
fi

log() { echo "[$(date -u +%FT%TZ)] $*"; }
status() { echo "$(date -u +%FT%TZ) fl2-pherc1218: $*" >> $OUT/STATUS.md; }
run() {  # run <label> <cmd...>: output to $W/logs/<label>.log; row in runs.jsonl (utc, command, rc, output sha256)
  local label=$1; shift; mkdir -p $W/logs
  local lf=$W/logs/$label.log t0; t0=$(date -u +%FT%TZ)
  "$@" > "$lf" 2>&1; local rc=$?
  $P - "$OUT/runs.jsonl" "$t0" "$(date -u +%FT%TZ)" "$rc" "$lf" "$label" "$@" <<'PY'
import hashlib, json, sys
f, t0, t1, rc, lf, label, *cmd = sys.argv[1:]
h = hashlib.sha256(open(lf, "rb").read()).hexdigest()
open(f, "a").write(json.dumps(dict(utc_start=t0, utc_end=t1, label=label, command=cmd, exit_code=int(rc),
                                   output=lf, output_sha256=h)) + "\n")
PY
  return $rc
}
push() {  # commit + push $OUT (retry with backoff)
  git add -A "$OUT" tools/sib/fl2-pherc1218 >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -q -m "fl2-pherc1218: $MSG

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019ijhigb9YTs2Pe7ncpxL4f" || return 1
  for t in 2 4 8 16; do
    git push -q origin $BR && return 0
    git pull -q --rebase origin $BR; sleep $t
  done
  return 1
}
vc() {  # vc <app> args...  (official villa 41701aa build inside the official deps image)
  local a=$1; shift
  docker run --rm --network host --cpus 4 -e OMP_NUM_THREADS=4 -e HTTPS_PROXY="${HTTPS_PROXY:-}" \
    -e https_proxy="${HTTPS_PROXY:-}" -e HOME=/work/vchome -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
    -e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro \
    -v /home/user:/home/user -v /work:/work $IMG "$BIN/$a" "$@"
}
free_gb() { df -BG --output=avail / | tail -1 | tr -dc 0-9; }

# ---- 1. environment (docker/env/setup_env.sh + vc_build.sh; TOOLING.md) --------------------------------------
if ! docker info >/dev/null 2>&1; then
  rm -f /var/run/docker.pid
  HTTPS_PROXY=$HTTPS_PROXY HTTP_PROXY=$HTTPS_PROXY nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 &
  for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || { log "dockerd failed"; status "env: dockerd failed"; exit 1; }
fi
if [ ! -f $ST/env.done ]; then
  status "env: building (villa 41701aa sparse volume-cartographer, official deps image, VC3D apps)"
  if [ -d /work/villa/.git ]; then
    git -C /work/villa sparse-checkout add .github volume-cartographer vesuvius ink-detection || exit 1
  fi
  git -C /work/villa fetch -q --depth 1 origin 41701aa0eaa1aa765523db3f9f972b5830abf549 || true
  git -C /work/villa checkout -q 41701aa0eaa1aa765523db3f9f972b5830abf549 || { status "env: villa checkout FAILED"; exit 1; }
  docker image inspect $IMG >/dev/null 2>&1 || run docker_pull docker pull $IMG || { status "env: deps image pull FAILED"; exit 1; }
  if [ ! -x $BIN/vc_render_tifxyz ] || [ ! -x $BIN/vc_grow_seg_from_seed ]; then
    # local copy of docker/env/vc_build.sh with the proxy taken from $HTTPS_PROXY (the original hard-codes a port)
    run vc_build bash tools/sib/fl2-pherc1218/vc_build.sh || { status "env: vc_build FAILED"; exit 1; }
  fi
  run setup_env bash docker/env/setup_env.sh || { status "env: setup_env FAILED"; exit 1; }
  for a in vc_render_tifxyz vc_grow_seg_from_seed vc_tifxyz_selfcross vc_gen_normalgrids; do
    [ -x $BIN/$a ] || { status "env: $a missing after build"; exit 1; }
  done
  [ "$(git -C /work/villa rev-parse HEAD)" = 41701aa0eaa1aa765523db3f9f972b5830abf549 ] || { status "env: villa not at 41701aa"; exit 1; }
  $P -c "import cv2, tifffile, zarr, numcodecs, boto3, scipy" || { status "env: /opt/hv python deps missing"; exit 1; }
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null || { status "env: vesuvius import failed"; exit 1; }
  touch $ST/env.done; status "env: ready"; MSG="environment ready" push
fi
echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { status "checkpoint sha256 mismatch"; exit 1; }
export PYTHONPATH=$REPO/src

# ---- 2. voxel size (I9), seeds, auto-grow 4 segments, keep 0-crossing >= 16 cm^2 ----------------------------
[ -f $ST/voxel.done ] || { run voxel $P $FL voxel && touch $ST/voxel.done || { status "voxel check FAILED"; exit 1; }; }
if [ ! -f $ST/seeds.done ]; then
  run seeds $P $FL seeds && touch $ST/seeds.done || { status "seeds FAILED"; exit 1; }
  status "seeds: 4 outer-third seeds chosen (seeds.json)"; MSG="seeds (outer third)" push || exit 1
fi
for k in 0 1 2 3; do
  D=$W/seg$k; mkdir -p $D
  [ -f $ST/post$k.done ] && continue
  if [ ! -f $ST/crop$k.done ]; then
    [ "$(free_gb)" -ge $MIN_FREE_GB ] || { status "disk: $(free_gb) GB free < $MIN_FREE_GB before crop $k"; exit 1; }
    run crop$k $P $FL crop $k || { status "crop $k FAILED"; exit 1; }; touch $ST/crop$k.done
  fi
  if [ ! -f $ST/ng$k.done ]; then
    rm -rf $D/ng
    run ng$k vc vc_gen_normalgrids -i $D/crop.zarr -o $D/ng --spiral-step 20 --preview-every 0 || { status "normal grids $k FAILED"; exit 1; }
    touch $ST/ng$k.done
  fi
  if [ ! -f $ST/trace$k.done ]; then
    status "segment $k: growing"
    rm -rf $D/trace; mkdir -p $D/trace
    SEED=$($P -c "import json;s=json.load(open('$D/crop.json'))['seed_local_zyx'];print(s[2],s[1],s[0])")
    $P - <<EOF || exit 1
import json
p = json.load(open("$REPO/tools/sib/fl2-pherc1218/L15.json"))
p.update({"generations": 80, "normal_grid_path": "$D/ng", "voxelsize": 17.28, "thread_limit": 4, "min_area_cm": 0.0})
json.dump(p, open("$D/params.json", "w"), indent=1)
EOF
    run trace$k vc vc_grow_seg_from_seed --volume $D/crop.zarr --target-dir $D/trace --params $D/params.json --seed $SEED
    touch $ST/trace$k.done
  fi
  run post$k $P $FL post $k || { status "post $k FAILED"; exit 1; }
  mkdir -p $OUT/seg$k; cp $D/post.json $D/crop.json $D/params.json $OUT/seg$k/ 2>/dev/null
  cp $D/selfcross*.json $OUT/seg$k/ 2>/dev/null
  if $P -c "import json,sys;sys.exit(0 if json.load(open('$D/post.json'))['keep'] else 1)"; then
    rm -rf $OUT/seg$k/native.tifxyz; cp -r $D/native.tifxyz $OUT/seg$k/
  fi
  gzip -c $W/logs/trace$k.log > $OUT/seg$k/trace.log.gz 2>/dev/null
  touch $ST/post$k.done
  status "segment $k: $($P -c "import json;p=json.load(open('$D/post.json'));print('KEEP' if p['keep'] else 'DROP', 'area', round(p.get('area_cm2',0),2), 'cm2 crossings', p.get('crossings_final'), p.get('why',''))")"
  MSG="segment $k grown and checked" push || exit 1
  rm -rf $D/crop.zarr $D/ng                            # scratch of this seed (regenerable)
done

# ---- 3-4. render (C2-NT), ink (both directions, no TTA), tiles --------------------------------------------
for k in 0 1 2 3; do
  D=$W/seg$k
  $P -c "import json,sys;sys.exit(0 if json.load(open('$D/post.json'))['keep'] else 1)" || continue
  [ -f $ST/tiles$k.done ] && continue
  if [ ! -f $ST/render$k.done ]; then
    [ "$(free_gb)" -ge $MIN_FREE_GB ] || { status "disk: $(free_gb) GB free < $MIN_FREE_GB before render $k"; exit 1; }
    status "segment $k: render"
    rm -rf $D/render.zarr
    run render$k vc vc_render_tifxyz -v $VOL_URL --remote-url $VOL_URL -g 0 --scale 1 -s $D/native.tifxyz \
      -n 31 --slice-step 1 --voxel-size 8.64 --voxel-unit micrometer --flip-normals --cache-gb 4 \
      --zarr-output $D/render.zarr || { status "render $k FAILED"; exit 1; }
    rm -rf /work/vchome/.VC3D/remote_cache
    touch $ST/render$k.done
  fi
  if [ ! -f $ST/ink$k.done ]; then
    status "segment $k: ink (both directions)"
    run ink$k env OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $D/render.zarr \
      $CKPT $D/ink.tif --direction both --batch-size 4 --num-workers 1 --no-compile || { status "ink $k FAILED"; exit 1; }
    touch $ST/ink$k.done
  fi
  run tiles$k $P $FL tiles $k || { status "tiles $k FAILED"; exit 1; }
  touch $ST/tiles$k.done
  status "segment $k: $($P -c "import json;print(len(json.load(open('$OUT/seg$k/manifest.json'))['tiles']))") tiles"
  MSG="segment $k tiles" push || exit 1
  rm -rf $D/render.zarr
done
N=$($P -c "
import json, glob
print(sum(len(json.load(open(f))['tiles']) for f in glob.glob('$OUT/seg*/manifest.json')))")
echo "DONE $N tiles" >> $OUT/STATUS.md
MSG="pipeline complete: $N tiles" push
exit 0
