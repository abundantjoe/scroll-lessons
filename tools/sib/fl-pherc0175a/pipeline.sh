#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# RULES.md DECL-FL-1: First Letters screen for PHerc0175A (sibling tracer). Idempotent: every stage writes a
# marker under /work/fl175a/state and is skipped when present; results are committed and pushed after each
# unit. Run detached with its own restart loop:
#   setsid nohup bash tools/sib/fl-pherc0175a/pipeline.sh --loop > /work/logs/fl175a.log 2>&1 &
# Never opens or views an image; tiles are written for the census only.
set -uo pipefail
REPO=/home/user/dominion
cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-tracer
W=/work/fl175a; ST=$W/state; OUT=logs/sib/fl-pherc0175a
P=/opt/hv/bin/python; FL=tools/sib/fl-pherc0175a/fl.py
BIN5=/work/villa-gated/volume-cartographer/build/hrc-gated-c5/bin
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
VOL_URL=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0175A/volumes/20250521115057-8.640um-1.2m-116keV-masked.zarr
mkdir -p $ST $OUT /work/logs

if [ "${1:-}" = "--loop" ]; then
  exec 9>$W/loop2.lock; flock -n 9 || { echo "loop already running"; exit 0; }
  for i in $(seq 1 20); do
    bash "$0" && { echo "PIPELINE DONE $(date -u +%FT%TZ)"; exit 0; }
    echo "pipeline failed (attempt $i), restart in 120 s $(date -u +%FT%TZ)"; sleep 120
  done
  echo "PIPELINE GAVE UP"; exit 1
fi

log() { echo "[$(date -u +%FT%TZ)] $*"; }
push() {  # commit + push the given paths (retry with backoff)
  git add -A "$@" >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -q -m "fl-pherc0175a: $MSG

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0186WKVwnaMbrHB2LUw9XEsR" || return 1
  for t in 2 4 8 16; do git push -q origin $BR && return 0; sleep $t; done; return 1
}
vc() {  # vc <bin_dir> <app> args...   (official deps image; HOME holds the remote chunk cache)
  local b=$1 a=$2; shift 2
  docker run --rm --network host --cpus 4 -e OMP_NUM_THREADS=4 -e HTTPS_PROXY="${HTTPS_PROXY:-}" \
    -e https_proxy="${HTTPS_PROXY:-}" -e HOME=/work/vchome -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
    -e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro \
    -v /home/user:/home/user -v /work:/work \
    ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f "$b/$a" "$@"
}

# ---- 1. environment -------------------------------------------------------------------------------------
if ! docker info >/dev/null 2>&1; then
  rm -f /var/run/docker.pid
  nohup dockerd --data-root /home/user/work/docker > /work/logs/dockerd.log 2>&1 9>&- &   # do not leak the loop lock fd
  for _ in $(seq 1 40); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || { log "dockerd failed"; exit 1; }
fi
[ -x $BIN5/vc_grow_seg_from_seed ] || { log "gated build c5 missing"; exit 1; }
[ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || { log "official build missing"; exit 1; }
if [ ! -f $ST/env.done ]; then
  log "env: vesuvius + CPU torch + checkpoint"
  git -C /work/villa sparse-checkout add vesuvius || exit 1
  git -C /work/villa checkout -q 41701aa0eaa1aa765523db3f9f972b5830abf549 || exit 1
  git fetch -q origin claude/gifted-bell-gavnl5 && git show origin/claude/gifted-bell-gavnl5:docker/env/hv-ink-freeze.txt > $W/hv-ink-freeze.txt
  if [ ! -x /opt/hv-ink/bin/python ]; then
    uv venv /opt/hv-ink --python 3.14 -q   # vesuvius @ 41701aa requires Python >=3.14,<3.15 || exit 1
  fi
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu || exit 1
  # the 3.13 freeze does not resolve on 3.14: install vesuvius with its declared dependencies (CPU torch kept)
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python -e /work/villa/vesuvius \
    --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match || exit 1
  # vesuvius[models] minus cucim-cu13 (CUDA only) and volume-cartographer (built separately)
  /opt/hv/bin/python -c "import tomllib;d=tomllib.load(open('/work/villa/vesuvius/pyproject.toml','rb'))['project']['optional-dependencies']['models'];print('\n'.join(x for x in d if not x.startswith(('cucim','volume-cartographer'))))" > $W/models-req.txt
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python -r $W/models-req.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match || exit 1
  VIRTUAL_ENV=/opt/hv-ink uv pip freeze --python /opt/hv-ink/bin/python > $W/hv-ink-freeze-actual.txt; cp $W/hv-ink-freeze-actual.txt $OUT/
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "vesuvius import failed"; exit 1; }
  mkdir -p "$(dirname $CKPT)"
  if ! echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet 2>/dev/null; then
    for t in 2 4 8 16; do
      curl -fsSL -o $CKPT "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break; sleep $t
    done
    echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "checkpoint sha mismatch"; exit 1; }
  fi
  touch $ST/env.done
fi

# ---- 2. segments (no organizer segments exist: auto-grow 4, keep 0-crossing >= 16 cm^2) ------------------
[ -f $ST/seeds.done ] || { $P $FL seeds && touch $ST/seeds.done && MSG="seeds" push $OUT || exit 1; }
for k in 0 1 2 3; do
  D=$W/seg$k
  if [ ! -f $ST/crop$k.done ]; then log "crop $k"; $P $FL crop $k || exit 1; touch $ST/crop$k.done; fi
  if [ ! -f $ST/ng$k.done ]; then
    log "normal grids $k"; rm -rf $D/ng
    vc $BIN5 vc_gen_normalgrids -i $D/crop.zarr -o $D/ng --spiral-step 20 --preview-every 0 > $D/ng.log 2>&1 || exit 1
    touch $ST/ng$k.done
  fi
  if [ ! -f $ST/trace$k.done ]; then
    log "trace $k"; rm -rf $D/trace; mkdir -p $D/trace
    SEED=$($P -c "import json;s=json.load(open('$D/crop.json'))['seed_local_zyx'];print(s[2],s[1],s[0])")
    $P - <<EOF || exit 1
import json
p = json.load(open("$REPO/logs/sib/tracer/presets/L15.json"))
p.update({"generations": 80, "normal_grid_path": "$D/ng", "voxelsize": 17.28, "thread_limit": 4, "min_area_cm": 0.0})
json.dump(p, open("$D/params.json", "w"), indent=1)
EOF
    vc $BIN5 vc_grow_seg_from_seed --volume $D/crop.zarr --target-dir $D/trace --params $D/params.json --seed $SEED > $D/trace.log 2>&1
    touch $ST/trace$k.done
  fi
  if [ ! -f $ST/post$k.done ]; then
    log "post $k"; $P $FL post $k || exit 1
    mkdir -p $OUT/seg$k; cp $D/post.json $D/crop.json $D/params.json $OUT/seg$k/ 2>/dev/null
    if $P -c "import json,sys;sys.exit(0 if json.load(open('$D/post.json'))['keep'] else 1)"; then
      rm -rf $OUT/seg$k/native.tifxyz; cp -r $D/native.tifxyz $OUT/seg$k/
    fi
    gzip -c $D/trace.log > $OUT/seg$k/trace.log.gz
    touch $ST/post$k.done; MSG="segment $k grown and checked" push $OUT || exit 1
    rm -rf $D/crop.zarr $D/ng                           # scratch of this seed (regenerable)
  fi
done

# ---- 3-4. render (C2-NT), ink (both directions, no TTA), tiles --------------------------------------------
for k in 0 1 2 3; do
  D=$W/seg$k
  $P -c "import json,sys;sys.exit(0 if json.load(open('$D/post.json'))['keep'] else 1)" || continue
  if [ ! -f $ST/render$k.done ]; then
    log "render $k"; rm -rf $D/render.zarr
    vc /work/villa/volume-cartographer/build/hrc-release-gcc/bin vc_render_tifxyz -v $VOL_URL --remote-url $VOL_URL \
      -g 0 --scale 1 -s $D/native.tifxyz -n 31 --flip-normals --zarr-output $D/render.zarr > $D/render.log 2>&1 || exit 1
    rm -rf /work/vchome/.VC3D/remote_cache
    touch $ST/render$k.done
  fi
  if [ ! -f $ST/ink$k.done ]; then
    log "ink $k"
    OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer $D/render.zarr $CKPT $D/ink.tif \
      --direction both --batch-size 4 --num-workers 1 --no-compile > $D/ink.log 2>&1 || exit 1
    touch $ST/ink$k.done
  fi
  if [ ! -f $ST/tiles$k.done ]; then
    log "tiles $k"; $P $FL tiles $k || exit 1
    touch $ST/tiles$k.done; MSG="segment $k tiles" push $OUT || exit 1
    rm -rf $D/render.zarr
  fi
done
echo "$(date -u +%FT%TZ) fl-pherc0175a: pipeline complete ($(ls $OUT/*/manifest.json 2>/dev/null | wc -l) tiled segments)" >> $OUT/STATUS.md
MSG="pipeline complete" push $OUT
exit 0
