#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4-A4: orchestrator-side FL-4 compute on pushed PHerc0268 segments (logs/fl4/local_queue.json), kit numerics unchanged.
set -uo pipefail
REPO=/home/user/dominion; cd $REPO; W=/work/fl4l; ST=$W/state; L=$REPO/logs/fl4l; mkdir -p $W $ST $L /work/own /work/logs
PY=/opt/hv/bin/python; GPY=/opt/hv-ink/bin/python; K=$REPO/tools/fl4; VOX=8.640
CT=s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/
export FL_SCROLL=PHerc0268 FL_VOX_UM=$VOX FL_VOLUME=20251110183117-8.640um-1.2m-116keV-masked FL_MODEL=GP_timesformer FL_MODEL_SHA=490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488
export FL_CHAIN="C2-NT vc_render_tifxyz -n 31 --flip-normals 8.640 um; GP TimeSformer (organizer HF scrollprize/timesformer_GP_scroll1 @61b81d31; Youssef Nader / 2023 Grand Prize team; MIT) via villa 41701aa; variant B x1.0923; window 64 stride 32 fp32 (DECL-FL-4-A4 local)"
log() { echo "[$(date -u +%FT%TZ)] $*" >> $L/local.log; }
push() { ( flock 9; git add logs/fl4l >/dev/null 2>&1; git commit -q -m "FL4 local (DECL-FL-4-A4): $1

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- logs/fl4l >/dev/null 2>&1; for d in 2 4 8 16; do git push -q origin claude/gifted-bell-gavnl5 2>>$W/push.err && break; git pull -q --rebase origin claude/gifted-bell-gavnl5 2>>$W/push.err; sleep $d; done ) 9>/work/own/git.lock; }
if [ ! -f $ST/env.ok ]; then
  rm -rf /root/.cache/uv /root/.cache/pip /root/.cache/huggingface
  log "env: free $(df -BG --output=avail /work | tail -1 | tr -dc 0-9)G before docker"
  bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "setup_env FAILED: $(tail -3 $W/setup_env.log | tr '\n' ' ')"; push "env failed"; exit 1; }
  docker info >/dev/null 2>&1 || { log "docker not running"; push "docker down"; exit 1; }
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --no-cache timesformer-pytorch==0.4.1 albumentations==2.0.8 pytorch-lightning==2.6.6 scipy opencv-python-headless psutil 2>>$W/setup_gp.log
  if [ ! -f /work/villa_gp/ink-detection/optimized_inference/inference.py ]; then
    git clone -q --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git /work/villa_gp && git -C /work/villa_gp sparse-checkout set ink-detection/optimized_inference && git -C /work/villa_gp checkout -q 41701aa
  fi
  mkdir -p /work/gp; echo "490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488  /work/gp/model.safetensors" | sha256sum -c --quiet 2>/dev/null || \
    curl -fsSL -o /work/gp/model.safetensors "https://huggingface.co/scrollprize/timesformer_GP_scroll1/resolve/61b81d31ddb93c89a2b3b00c66769d18bd96ccb2/model.safetensors"
  echo "490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488  /work/gp/model.safetensors" | sha256sum -c --quiet || { log "model sha mismatch"; push "model sha mismatch"; exit 1; }
  FL_VOX_UM=8.64 $GPY -c "import sys; sys.path.insert(0,'$K'); import gp_infer as G; m=G.model(); print('GP strict load OK', sum(p.numel() for p in m.parameters()))" >> $L/local.log 2>&1 || { log "GP load FAILED"; push "GP load failed"; exit 1; }
  { $GPY -c "import torch,zarr;print('torch',torch.__version__,'zarr',zarr.__version__)"; echo "villa_gp $(git -C /work/villa_gp rev-parse HEAD)"; } > $L/env.txt
  touch $ST/env.ok; log "env OK, free $(df -BG --output=avail /work | tail -1 | tr -dc 0-9)G"; push "env ok"
fi
docker info >/dev/null 2>&1 || { log "docker down: starting via setup_env (restart-proof)"; bash $REPO/docker/env/setup_env.sh >> $W/setup_env.log 2>&1; docker info >/dev/null 2>&1 || { log "docker start FAILED"; push "docker start failed"; exit 1; }; }
proxy_refresh() {   # DECL-FL-4-A4-E3: a harness restart moves the proxy port; take the live one from /root/.ccr/README.md
  local p; p=$(grep -o 'http://127\.0\.0\.1:[0-9]\+' /root/.ccr/README.md 2>/dev/null | head -1)
  [ -n "$p" ] && [ "$p" != "${HTTPS_PROXY:-}" ] && { export HTTPS_PROXY=$p https_proxy=$p DOCKER_HTTPS_PROXY=$p GLOBAL_AGENT_HTTPS_PROXY=$p YARN_HTTPS_PROXY=$p npm_config_https_proxy=$p; log "proxy now $p"; }
  return 0
}
proxy_refresh
N=$(python3 -c "import json;print(len(json.load(open('$REPO/logs/fl4/local_queue.json'))))")
# DECL-FL-4-A4-A2-E2: claimed-but-unfinished segments first (queue order), then unclaimed ones from the OUTER end of the queue;
# ordered by seed index descending: fleet lane k takes seeds k, k+16, k+32, ..., so the highest seeds are the last any lane reaches.
ORDER=$(python3 -c "
import json,os
q=json.load(open('$REPO/logs/fl4/local_queue.json')); c=set(open('$L/CLAIMED.txt').read().split())
a=[i for i,x in enumerate(q) if x['segment'] in c and not os.path.exists('$L/'+x['segment']+'/DONE')]
b=sorted((i for i,x in enumerate(q) if x['segment'] not in c),key=lambda i:-int(q[i]['segment'].rsplit('_i',1)[1]))
print(*(a+b))")
for q in $ORDER; do
  proxy_refresh
  read -r name wk dirs <<<"$(python3 -c "import json;x=json.load(open('$REPO/logs/fl4/local_queue.json'))[$q];print(x['segment'],x['worker'],x['dirs'])")"
  if ! grep -qx "$name" $L/CLAIMED.txt; then   # DECL-FL-4-A4-A1-E1: auto-claim, pushed before the segment starts
    grep -qx "$wk" $L/FLEET_ACTIVE.txt 2>/dev/null && continue   # that lane's fresh session computes it
    echo "$name" >> $L/CLAIMED.txt; push "claim $name"
  fi
  O=$L/$name; [ -f $O/DONE ] && continue; d=$W/seg/$name; mkdir -p $d $O/cover_gp_B $O/vgrid
  for f in x.tif y.tif z.tif meta.json; do [ -s $d/$f ] || git show origin/claude/gifted-bell-gavnl5-sib-$wk:logs/sib/$wk/fl4/PHerc0268/$name/tifxyz/$f > $d/$f; done
  R=/dev/shm/fl4r/$name.zarr   # render in RAM: the remote-chunk scratch (~0.6 GB) and output exceed this container's disk
  if [ ! -f $ST/render_$name.ok ] || [ ! -d $R ]; then
    rm -rf /dev/shm/fl4r; mkdir -p /dev/shm/fl4r; log "render $name (free $(df -BG --output=avail /work | tail -1 | tr -dc 0-9)G)"
    P="${HTTPS_PROXY:-http://127.0.0.1:46883}"
    ( cd $W && docker run --rm -i --network host --cpus 4 -e OMP_NUM_THREADS=4 -e HOME=/tmp -e XDG_CACHE_HOME=/tmp/.cache -e HTTPS_PROXY="$P" -e https_proxy="$P" \
        -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt -e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro \
        --tmpfs /tmp:size=6g --tmpfs /var/tmp:size=2g -v /work:/work -v /home/user:/home/user -v /dev/shm/fl4r:/dev/shm/fl4r -w $W \
        ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz \
        -v $CT --remote-url $CT --segmentation $d --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 \
        --voxel-size $VOX --voxel-unit micrometer --flip-normals --cache-gb 3 --zarr-output $R > $W/render.log 2>&1 ) || { log "render $name FAILED: $(tail -2 $W/render.log | tr '\n' ' ')"; push "render $name failed"; continue; }
    touch $ST/render_$name.ok
  fi
  [ "$dirs" = both ] && DL="forward reverse" || DL="$dirs"
  for dir in $DL; do
    [ -f $ST/post_${name}_$dir.ok ] && continue   # A4-A2-E2: cover+vgrid already done; never re-run them on a deleted prediction
    P=$W/pred/${name}_B_$dir.tif; mkdir -p $W/pred
    if [ ! -f $ST/gp_${name}_$dir.ok ]; then
      log "GP B $dir $name"; s=$(date -u +%FT%TZ)
      FL_VOX_UM=$VOX OMP_NUM_THREADS=4 $GPY $K/gp_infer.py run $R $P B $dir > $W/gp.log 2>&1; rc=$?
      echo "{\"segment\":\"$name\",\"direction\":\"$dir\",\"utc_start\":\"$s\",\"utc_end\":\"$(date -u +%FT%TZ)\",\"exit\":$rc,\"result\":$(tail -1 $W/gp.log | grep '^{' || echo null)}" >> $L/runs.jsonl
      [ $rc -eq 0 ] || { log "GP $name $dir FAILED: $(tail -2 $W/gp.log | tr '\n' ' ')"; push "GP $name $dir failed"; continue 2; }
      touch $ST/gp_${name}_$dir.ok
    fi
    AREA=$(python3 -c "import json;print(json.load(open('$d/meta.json')).get('area_cm2'))")
    FL_AREA_CM2=$AREA $PY $K/fl4.py cover $name $d $P $dir local-a4 $O/cover_gp_B $O/cover_gp_B/manifest.json >> $L/local.log 2>&1
    $PY $K/fl4.py vgrid $d $P $O/vgrid/B_$dir.tif $REPO/logs/fl4/seeds_inner_PHerc0268.json > $O/vgrid/B_$dir.json 2>>$L/local.log
    touch $ST/post_${name}_$dir.ok; rm -f $P; push "GP B $dir $name"
  done
  touch $O/DONE; rm -rf /dev/shm/fl4r; push "segment $name done"
done
log "queue complete"; touch $L/ALL_DONE; push "queue complete"
