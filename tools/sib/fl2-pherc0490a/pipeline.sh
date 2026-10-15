#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# RULES.md DECL-FL-1, tools/fl/BRIEF_PASS.md (dcb6a6b): First Letters extra PASS 2 for PHerc0490A.
# No organizer segments exist -> auto-grow up to 4 segments seeded in the OUTER third of the radius.
# Idempotent: each unit writes a marker under /work/fl2_0490a/state and is skipped when present; results
# are committed and pushed after each unit. Detached with its own restart loop:
#   setsid nohup bash tools/sib/fl2-pherc0490a/pipeline.sh --loop > /work/logs/fl2_0490a.log 2>&1 &
# Never opens or views an image; tiles are written for the census only.
set -uo pipefail
REPO=/home/user/dominion
cd "$REPO"
BR=claude/gifted-bell-gavnl5-sib-regrescan
W=/work/fl2_0490a; ST=$W/state; OUT=logs/sib/fl2-pherc0490a
P=/opt/hv/bin/python; FL=tools/sib/fl2-pherc0490a/fl.py
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
VOL_URL=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0490A/volumes/20250521151210-8.640um-1.2m-116keV-masked.zarr
mkdir -p $ST $OUT /work/logs

if [ "${1:-}" = "--loop" ]; then
  exec 9>$W/loop.lock; flock -n 9 || { echo "loop already running"; exit 0; }
  for i in $(seq 1 20); do
    bash "$0" && { echo "PIPELINE DONE $(date -u +%FT%TZ)"; exit 0; }
    echo "pipeline failed (attempt $i), restart in 120 s $(date -u +%FT%TZ)"; sleep 120
  done
  echo "$(date -u +%FT%TZ) FAILED: pipeline gave up after 20 attempts (see /work/logs/fl2_0490a.log)" >> $OUT/STATUS.md
  MSG="pipeline gave up" bash -c "cd $REPO && git add $OUT && git commit -q -m 'fl2-pherc0490a: pipeline gave up

Provenance: Project HERCULES | owner the owner | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01USRhAAo5Prm8JPQWJDzRaq' && git push -q origin $BR"
  exit 1
fi

log() { echo "[$(date -u +%FT%TZ)] $*"; }
push() {  # commit + push the given paths (retry with backoff)
  git add -A "$@" >/dev/null 2>&1
  git diff --cached --quiet && return 0
  git commit -q -m "fl2-pherc0490a: $MSG

Provenance: Project HERCULES | owner the owner | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01USRhAAo5Prm8JPQWJDzRaq" || return 1
  for t in 2 4 8 16; do git push -q origin $BR && return 0; git pull -q --no-rebase origin $BR; sleep $t; done; return 1
}
vc() {  # vc <app> args...   (official deps image, vanilla villa 41701aa build; HOME holds the remote chunk cache)
  local a=$1; shift
  docker run --rm --network host --cpus 4 -e OMP_NUM_THREADS=4 -e HTTPS_PROXY="${HTTPS_PROXY:-}" \
    -e https_proxy="${HTTPS_PROXY:-}" -e HOME=/work/vchome -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
    -e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro \
    -v /home/user:/home/user -v /work:/work $IMG "$BIN/$a" "$@"
}

# ---- 1. environment (docker/env/setup_env.sh from the orchestrator branch; idempotent) --------------------
if [ ! -f $ST/env.done ]; then
  log "env: setup_env.sh"
  git fetch -q origin claude/gifted-bell-gavnl5 || exit 1
  [ -d /work/orch ] || git worktree add -q --detach /work/orch origin/claude/gifted-bell-gavnl5 || exit 1
  VIRTUAL_ENV=/opt/hv uv pip install -q numpy scipy "zarr<3" numcodecs boto3 s3fs tifffile imagecodecs \
    opencv-python-headless || { log "hv deps failed"; exit 1; }
  bash /work/orch/docker/env/setup_env.sh >> /work/logs/setup_env.log 2>&1 || log "setup_env returned non-zero (checked below)"
  if ! /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null; then
    # vesuvius @ 41701aa requires Python >=3.14,<3.15 (as found by the tracer sibling): rebuild the ink venv on 3.14
    log "ink venv: rebuilding on Python 3.14"; rm -rf /opt/hv-ink
    uv venv /opt/hv-ink --python 3.14 -q || exit 1
    VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu || exit 1
    VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python -e /work/villa/vesuvius --no-deps || exit 1
    VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r /work/orch/docker/env/hv-ink-freeze.txt --no-deps || true
  fi
  [ -x $BIN/vc_render_tifxyz ] || bash /work/orch/docker/env/vc_build.sh >> /work/logs/vc_build.log 2>&1 || exit 1
  /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" || { log "vesuvius import failed"; exit 1; }
  echo "$CKPT_SHA  $CKPT" | sha256sum -c --quiet || { log "checkpoint sha mismatch"; exit 1; }
  touch $ST/env.done
fi
if ! docker info >/dev/null 2>&1; then
  rm -f /var/run/docker.pid
  HTTPS_PROXY=${HTTPS_PROXY:-} nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 &
  for _ in $(seq 1 40); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || { log "dockerd failed"; exit 1; }
fi
[ -x $BIN/vc_grow_seg_from_seed ] || { log "official build missing"; rm -f $ST/env.done; exit 1; }

# ---- 2. segments (no organizer segments: auto-grow 4 in the outer third, keep 0 crossings, >= 16 cm^2) ----
[ -f $ST/seeds.done ] || { $P $FL seeds && touch $ST/seeds.done && MSG="seeds (outer third)" push $OUT || exit 1; }
for k in 0 1 2 3; do
  D=$W/seg$k
  if [ ! -f $ST/crop$k.done ]; then
    log "crop $k"
    if ! $P $FL crop $k > $W/crop$k.log 2>&1; then
      mkdir -p $D; echo "{\"k\": $k, \"keep\": false, \"why\": \"crop/seed snap failed\"}" > $D/post.json
      touch $ST/crop$k.done $ST/ng$k.done $ST/trace$k.done; cp $W/crop$k.log $D/crop.log
    else touch $ST/crop$k.done; fi
  fi
  if [ ! -f $ST/ng$k.done ]; then
    log "normal grids $k"; rm -rf $D/ng
    vc vc_gen_normalgrids -i $D/crop.zarr -o $D/ng --spiral-step 20 --preview-every 0 > $D/ng.log 2>&1 || exit 1
    touch $ST/ng$k.done
  fi
  if [ ! -f $ST/trace$k.done ]; then
    log "trace $k"; rm -rf $D/trace; mkdir -p $D/trace
    SEED=$($P -c "import json;s=json.load(open('$D/crop.json'))['seed_local_zyx'];print(s[2],s[1],s[0])")
    $P - <<PY || exit 1
import json
p = {"compactness": True, "direction_fields": [], "mode": "seed", "reject_dist_th": 1.5,
     "space_line_weight": 0.1, "step_size": 20, "generations": 80, "normal_grid_path": "$D/ng",
     "voxelsize": 17.28, "thread_limit": 4, "min_area_cm": 0.0}
json.dump(p, open("$D/params.json", "w"), indent=1)
PY
    vc vc_grow_seg_from_seed --volume $D/crop.zarr --target-dir $D/trace --params $D/params.json --seed $SEED > $D/trace.log 2>&1
    touch $ST/trace$k.done
  fi
  if [ ! -f $ST/post$k.done ]; then
    log "post $k"
    [ -f $D/post.json ] && grep -q '"crop/seed snap failed"' $D/post.json || { $P $FL post $k || exit 1; }
    mkdir -p $OUT/seg$k; cp $D/post.json $D/crop.json $D/params.json $OUT/seg$k/ 2>/dev/null
    if $P -c "import json,sys;sys.exit(0 if json.load(open('$D/post.json'))['keep'] else 1)"; then
      rm -rf $OUT/seg$k/native.tifxyz; cp -r $D/native.tifxyz $OUT/seg$k/
    fi
    [ -f $D/trace.log ] && gzip -c $D/trace.log > $OUT/seg$k/trace.log.gz
    touch $ST/post$k.done; MSG="segment $k grown and checked" push $OUT || exit 1
    rm -rf $D/crop.zarr $D/ng
  fi
done

# ---- 3-4. render (C2-NT), ink (both directions, no TTA), tiles --------------------------------------------
for k in 0 1 2 3; do
  D=$W/seg$k
  $P -c "import json,sys;sys.exit(0 if json.load(open('$D/post.json'))['keep'] else 1)" || continue
  if [ ! -f $ST/render$k.done ]; then
    log "render $k"; rm -rf $D/render.zarr
    vc vc_render_tifxyz -v $VOL_URL --remote-url $VOL_URL \
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
N=$($P -c "import json,glob;print(sum(len(json.load(open(f))['tiles']) for f in glob.glob('$OUT/*/manifest.json')))")
if [ "$N" = "0" ] && ! ls $OUT/*/manifest.json >/dev/null 2>&1; then
  echo "$(date -u +%FT%TZ) DONE 0 (no auto-grown segment passed 0 crossings and >= 16 cm^2)" >> $OUT/STATUS.md
else
  echo "$(date -u +%FT%TZ) DONE $N" >> $OUT/STATUS.md
fi
MSG="pipeline complete" push $OUT
exit 0
