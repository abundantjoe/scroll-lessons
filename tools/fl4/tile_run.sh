#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# OWNER-ORDER-FL4-B lane runner: render (C2-NT, 31 layers, flip-normals, 8.64 um) + GP variant B forward and reverse on the
# tiles listed for lane LANE in logs/fl4t/<SHEET>/tiles.json; pushes 8-bit PNG ink maps to this branch. Idempotent (markers).
# usage: setsid nohup bash tools/fl4/tile_run.sh <SHEET> <LANE> &      done marker: logs/fl4t/<SHEET>/lane<LANE>/ALL_DONE
set -uo pipefail
SHEET=$1; LANE=$2; REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
BR=$(git rev-parse --abbrev-ref HEAD); K=$REPO/tools/fl4; W=/work/fl4t; ST=$W/state; mkdir -p $W $ST /work/own
S=$REPO/logs/fl4t/$SHEET; L=$S/lane$LANE; mkdir -p $L
CT=s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $L/pipeline.log; }
proxy_refresh(){ local p; p=$(grep -o 'http://127\.0\.0\.1:[0-9]\+' /root/.ccr/README.md 2>/dev/null | head -1)
  [ -n "$p" ] && [ "$p" != "${HTTPS_PROXY:-}" ] && export HTTPS_PROXY=$p https_proxy=$p DOCKER_HTTPS_PROXY=$p; return 0; }
push(){ local d; flock /work/own/git.lock -c "git add logs/fl4t/$SHEET/lane$LANE >/dev/null 2>&1; git diff --cached --quiet || git commit -q -m 'fl4t $SHEET lane$LANE: $1

Provenance: Project HERCULES | [id removed]
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'"
  for d in 2 4 8 16 32; do flock /work/own/git.lock git push -q origin HEAD:$BR 2>>$W/push.err && return 0
    flock /work/own/git.lock git pull -q --rebase origin $BR 2>>$W/push.err; sleep $d; done; log "WARN push failed: $1"; }
proxy_refresh
if [ ! -x /work/bin/vc ] || [ ! -x /opt/hv/bin/python ] || [ ! -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || ! docker info >/dev/null 2>&1; then
  log "env: setup_env.sh"; bash $REPO/docker/env/setup_env.sh > $W/setup_env.log 2>&1 || { log "env FAILED"; tail -40 $W/setup_env.log > $L/env_fail.log.tail; push "env failed"; exit 1; }
fi
if [ ! -f $ST/gp.ok ]; then bash $K/setup_gp.sh > $W/setup_gp.log 2>&1 || { log "GP env FAILED"; tail -40 $W/setup_gp.log > $L/env_fail.log.tail; push "GP env failed"; exit 1; }; touch $ST/gp.ok; log "GP env ok"; push "GP env ok"; fi
GPY=/opt/gp/bin/python; [ -x $GPY ] || GPY=/opt/hv-ink/bin/python
for t in $(python3 -c "import json;print(' '.join(json.load(open('$S/tiles.json'))['assign']['$LANE']))"); do
  proxy_refresh; R=$W/r_$t.zarr
  [ -f $L/${t}_reverse.png ] && [ -f $L/${t}_forward.png ] && continue
  if [ ! -f $ST/render_$t.ok ]; then rm -rf $R; log "render $t"
    ( cd $W && /work/bin/vc vc_render_tifxyz -v $CT --remote-url $CT --segmentation $S/tiles/$t --scale 1 --group-idx 0 --num-slices 31 --slice-step 1 \
      --voxel-size 8.64 --voxel-unit micrometer --flip-normals --cache-gb 3 --zarr-output $R > $W/render_$t.log 2>&1 ) || { log "render $t FAILED: $(tail -2 $W/render_$t.log | tr '\n' ' ')"; push "render $t failed"; continue; }
    touch $ST/render_$t.ok; fi
  for dir in forward reverse; do [ -f $L/${t}_$dir.png ] && continue; log "GP B $dir $t"
    FL_VOX_UM=8.64 OMP_NUM_THREADS=4 $GPY $K/gp_infer.py run $R $W/${t}_$dir.tif B $dir > $W/gp_${t}_$dir.log 2>&1 || { log "GP $t $dir FAILED: $(tail -2 $W/gp_${t}_$dir.log | tr '\n' ' ')"; continue; }
    /opt/hv/bin/python -c "
import tifffile,numpy as np,cv2,sys
p=tifffile.imread('$W/${t}_$dir.tif').astype(np.float32); p=p/(255.0 if p.max()>1.5 else 1.0)
cv2.imwrite('$L/${t}_$dir.png',np.clip(p*255,0,255).astype(np.uint8),[cv2.IMWRITE_PNG_COMPRESSION,9])" && rm -f $W/${t}_$dir.tif
    push "GP B $dir $t"; done
  [ -f $L/${t}_forward.png ] && [ -f $L/${t}_reverse.png ] && rm -rf $R
done
n=$(python3 -c "import json;print(len(json.load(open('$S/tiles.json'))['assign']['$LANE']))"); k=$(ls $L/*_reverse.png 2>/dev/null | wc -l)
[ "$k" -ge "$n" ] && { touch $L/ALL_DONE; push "lane complete ($k tiles)"; } || { log "incomplete $k/$n"; push "incomplete $k/$n"; }
