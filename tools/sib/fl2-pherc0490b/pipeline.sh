#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# First Letters screen (RULES.md DECL-FL-1), PASS 2 worker fl2-pherc0490b (tools/fl/BRIEF_PASS.md @ dcb6a6b).
# Adapted from the pass-1 worker (branch claude/gifted-bell-gavnl5-sib-fl-pherc0490b, commit 20b8231):
# explicit seeds in the OUTER third of the scroll radius (fl.py seeds), own branch/paths, manifest "pass": 2. Detached, idempotent, commits + pushes per unit.
#   nohup bash tools/sib/fl2-pherc0490b/pipeline.sh loop > /work/fl/loop.log 2>&1 &
# Units (done markers in /work/fl/done/, 3 failures -> unit recorded FAILED and skipped):
#   env      docker/env/setup_env.sh (+ vc_build.sh with the session proxy), VC3D apps from villa 41701aa
#   list     anonymous S3 listing of PHerc0490B/ -> organizer tifxyz or auto-grow
#   grow_k   k=1..4 vc_grow_seg_from_seed on the organizer surface prediction (surface-m7), normal grids streamed;
#            vc_tifxyz_selfcross; keep iff 0 transverse self-intersections and area_cm2 >= 16
#   render_S / infer_S / tiles_S per kept segment: C2-NT render (-n 31 --flip-normals), official ink_9um
#            step-075000 infer both directions no TTA CPU, 2 x 2 cm u8 tiles (fl.py tiles)
# Never opens or views an image: numbers, hashes and file lists only.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$HERE" rev-parse --show-toplevel)
BRANCH=claude/gifted-bell-gavnl5-sib-reg0009b
W=/work/fl2
L=$REPO/logs/sib/fl2-pherc0490b
PY=/opt/hv/bin/python
VC=/work/bin/vc
CKPT=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
VOL=s3://vesuvius-challenge-open-data/PHerc0490B/volumes/20250521151215-8.640um-1.2m-116keV-masked.zarr/
SURF=s3://vesuvius-challenge-open-data/PHerc0490B/representations/predictions/surfaces/20250521151215-surface-20260413222639-surface-m7-L0-th0.2.zarr/
NGRID_URL=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0490B/representations/predictions/surfaces/20250521151215-surface-20260413222639-surface-m7-L0-th0.2.normal-grids
VOX=8.64
N_GROW=4
GROW_TIMEOUT=${GROW_TIMEOUT:-10h}
export FL_PASS=2
export VC_CPUS=${VC_CPUS:-3} OMP_NUM_THREADS=${OMP_NUM_THREADS:-3}
mkdir -p "$W/done" "$W/fail" "$W/grow" "$W/render" "$W/infer" "$W/ngrid" "$W/grow_cache" "$L"

utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(utc)] $*"; }
ledger() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$L/ledger.tsv"; }  # unit start end rc cmd

push() {  # commit logs + tools and push to the worker branch (retry 2,4,8,16 s)
  cd "$REPO" || return 1
  git add -A logs/sib/fl2-pherc0490b tools/sib/fl2-pherc0490b
  git diff --cached --quiet && return 0
  git commit -q -m "fl2-pherc0490b: $1

DECL-FL-1 First Letters screen, PHerc0490B PASS 2 worker (detached pipeline unit).

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01HH7JrwbTkn9dwNmok9D3bx" || return 1
  for d in 0 2 4 8 16; do sleep $d; git push -q -u origin "$BRANCH" && return 0; done
  log "push failed (will retry next unit)"; return 1
}

unit() {  # unit NAME FUNC [args]: skip if done or failed 3x; else run, mark, push
  local n=$1; shift
  [ -f "$W/done/$n" ] && return 0
  local f; f=$(cat "$W/fail/$n" 2>/dev/null || echo 0)
  if [ "$f" -ge 3 ]; then return 1; fi
  log "unit $n start (prior failures $f)"
  local s; s=$(utc)
  ( "$@" ) > "$W/$n.log" 2>&1; local rc=$?   # subshell: set -e / cd stay inside the unit
  ledger "$n" "$s" "$(utc)" "$rc" "$*"
  tail -c 20000 "$W/$n.log" > "$L/unitlogs/$n.log.tail" 2>/dev/null || { mkdir -p "$L/unitlogs"; tail -c 20000 "$W/$n.log" > "$L/unitlogs/$n.log.tail"; }
  if [ $rc -eq 0 ]; then
    touch "$W/done/$n"; log "unit $n done"; push "$n done"
  else
    echo $((f + 1)) > "$W/fail/$n"; log "unit $n FAILED rc=$rc ($((f + 1))/3)"
    [ $((f + 1)) -ge 3 ] && echo "{\"unit\":\"$n\",\"failed_utc\":\"$(utc)\",\"rc\":$rc,\"attempts\":3}" > "$L/FAILED_$n.json"
    push "$n failed rc=$rc ($((f + 1))/3)"
  fi
  return $rc
}

ensure_docker() {
  if ! docker info >/dev/null 2>&1; then
    HTTPS_PROXY=$HTTPS_PROXY HTTP_PROXY=$HTTPS_PROXY nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 &
    for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
  fi
  docker info >/dev/null 2>&1
}

u_env() {
  set -e
  mkdir -p /work/logs /work/scripts
  ensure_docker
  docker image inspect ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f >/dev/null 2>&1 || \
    docker pull ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
  local B=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
  if [ ! -x $B/vc_grow_seg_from_seed ] || [ ! -x $B/vc_tifxyz_selfcross ] || [ ! -x $B/vc_render_tifxyz ]; then
    [ -d /work/villa/.git ] || { git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
      git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection; }
    git -C /work/villa fetch --depth 1 origin 41701aa0eaa1aa765523db3f9f972b5830abf549 || true
    git -C /work/villa checkout -q 41701aa0eaa1aa765523db3f9f972b5830abf549
    # repo vc_build.sh with the session's proxy port (the file hardcodes 127.0.0.1:46883)
    sed "s#http://127.0.0.1:46883#${HTTPS_PROXY}#g" "$REPO/docker/env/vc_build.sh" > /work/scripts/vc_build_fl.sh
    bash /work/scripts/vc_build_fl.sh
  fi
  bash "$REPO/docker/env/setup_env.sh"
  echo "$CKPT_SHA  $CKPT" | sha256sum -c
  "$PY" - "$L/env.json" <<EOF
import hashlib, json, subprocess, sys
B = '/work/villa/volume-cartographer/build/hrc-release-gcc/bin'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
json.dump(dict(villa_head=subprocess.check_output(['git', '-C', '/work/villa', 'rev-parse', 'HEAD']).decode().strip(),
               binaries={a: sha(f'{B}/{a}') for a in ('vc_grow_seg_from_seed', 'vc_tifxyz_selfcross', 'vc_render_tifxyz')},
               checkpoint='$CKPT', checkpoint_sha256=sha('$CKPT'),
               vesuvius_infer_sha256=sha('/work/villa/vesuvius/src/vesuvius/ink_detection/inference/infer.py'),
               torch=subprocess.check_output(['/opt/hv-ink/bin/python', '-c', 'import torch;print(torch.__version__)']).decode().strip()),
          open(sys.argv[1], 'w'), indent=1)
EOF
}

u_list() { "$PY" "$HERE/fl.py" list "$L/s3_listing.json"; }

u_seeds() { "$PY" "$HERE/fl.py" seeds "$L/seeds.json" "$N_GROW"; }

u_org() {  # organizer branch: fetch the 3 largest tifxyz (x/y/z/meta) into $W/seg/<name>
  set -e
  "$PY" - "$L/s3_listing.json" "$W/seg" <<'EOF'
import json, os, subprocess, sys
rec = json.load(open(sys.argv[1]))
for s in rec['organizer_tifxyz'][:3]:
    d = os.path.join(sys.argv[2], s['tifxyz'].rstrip('/').split('/')[-1]); os.makedirs(d, exist_ok=True)
    for f in ('x.tif', 'y.tif', 'z.tif', 'meta.json'):
        if not os.path.exists(f'{d}/{f}'):
            subprocess.run(['curl', '-fsSL', '--retry', '4', '-o', f'{d}/{f}',
                            f"https://vesuvius-challenge-open-data.s3.amazonaws.com/{s['tifxyz']}{f}"], check=True)
    print(d)
EOF
  ls "$W/seg" > "$W/kept.txt"
}

u_grow() {  # u_grow K: one auto-grow attempt; the new auto_grown_* dir is recorded and evaluated
  set -e
  local k=$1 G=$W/grow
  cat > "$W/ngrid/normal-grids-remote.json" <<EOF
{"url": "$NGRID_URL"}
EOF
  cat > "$L/grow_params.json" <<EOF
{"mode": "seed", "voxelsize": $VOX, "use_cuda": false, "generations": 200, "step_size": 20,
 "min_area_cm": 1.0, "thread_limit": $VC_CPUS, "cache_size": 4000000000, "cache_root": "$W/grow_cache",
 "normal_grid_path": "$W/ngrid"}
EOF
  ls -1 "$G" | grep '^auto_grown_' | sort > "$W/grow_before_$k.txt" || true
  # a partial output of an interrupted earlier try of this attempt is removed first
  [ -f "$W/grow_new_$k.txt" ] && while read -r d; do [ -n "$d" ] && rm -rf "${G:?}/$d"; done < "$W/grow_new_$k.txt"
  ls -1 "$G" | grep '^auto_grown_' | sort > "$W/grow_before_$k.txt" || true
  cd "$W"
  local SEED; SEED=$("$PY" -c "import json,sys; s=json.load(open('$L/seeds.json'))['seeds'][$k-1].get('seed_xyz'); print(' '.join(map(str,s)) if s else '')")
  if [ -z "$SEED" ]; then
    printf '{"attempt": %s, "segment": null, "keep": false, "reason": "no outer-third seed in quadrant", "utc": "%s"}\n' "$k" "$(utc)" > "$L/grow/attempt_$k.json"; mkdir -p "$L/grow"; return 0
  fi
  echo "explicit seed (x y z): $SEED"
  timeout "$GROW_TIMEOUT" "$VC" vc_grow_seg_from_seed -v "$SURF" -t "$G" -p "$L/grow_params.json" --seed $SEED || { echo "grow rc=$?"; }
  ls -1 "$G" | grep '^auto_grown_' | sort | comm -13 "$W/grow_before_$k.txt" - > "$W/grow_new_$k.txt" || true
  mkdir -p "$L/grow"
  local seed; seed=$(grep -E 'Found seed location|seed location' "$W/grow_$k.log" 2>/dev/null | tail -1 || true)
  if [ ! -s "$W/grow_new_$k.txt" ]; then
    printf '{"attempt": %s, "segment": null, "keep": false, "reason": "no surface written (seed search failed, timeout, or area < min_area_cm 1.0)", "seed_line": "%s", "utc": "%s"}\n' \
      "$k" "$(grep -E 'seed|discarding|ERROR' "$W/grow_$k.log" | tail -3 | tr '\n"' ' _')" "$(utc)" > "$L/grow/attempt_$k.json"
    return 0
  fi
  local s; s=$(head -1 "$W/grow_new_$k.txt")
  "$VC" vc_tifxyz_selfcross "$G/$s" -o "$W/selfcross_$s.json" --threads "$VC_CPUS"
  cp "$W/selfcross_$s.json" "$L/grow/selfcross_$s.json"
  "$PY" "$HERE/fl.py" growrec "$G/$s" "$W/selfcross_$s.json" "$L/grow/attempt_$k.json"
  "$PY" - "$L/grow/attempt_$k.json" "$k" "$W/grow_$k.log" <<'EOF'
import json, re, sys
r = json.load(open(sys.argv[1])); r['attempt'] = int(sys.argv[2])
m = [l.strip() for l in open(sys.argv[3], errors='replace') if 'seed location' in l]
r['seed_line'] = m[-1] if m else None
json.dump(r, open(sys.argv[1], 'w'), indent=1)
EOF
  grep -q '"keep": true' "$L/grow/attempt_$k.json" && echo "$s" >> "$W/kept.txt"
  return 0
}

u_render() {  # u_render SEGDIR NAME
  set -e
  local sd=$1 s=$2 out=$W/render/$2.zarr
  rm -rf "$out"; cd "$W"
  "$VC" vc_render_tifxyz -v "$VOL" --remote-url "$VOL" --segmentation "$sd" --scale 1 --group-idx 0 \
    --num-slices 31 --slice-step 1 --voxel-size "$VOX" --voxel-unit micrometer --flip-normals \
    --cache-gb 4 --zarr-output "$out"
  "$PY" -c "import zarr,sys; a=zarr.open(sys.argv[1]+'/0','r'); print(a.shape,a.dtype); assert a.shape[0]==31 and str(a.dtype)=='uint8'" "$out"
}

u_infer() {  # u_infer NAME: official infer, both directions, no TTA, CPU (C2-NT chain, tools/c3/run_infer.sh)
  set -e
  local s=$1 o=$W/infer/$1
  mkdir -p "$o"; rm -f "$o/pred.tif" "$o/pred_reverse.tif"
  OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer "$W/render/$s.zarr" "$CKPT" \
    "$o/pred.tif" --direction both --batch-size 4 --num-workers 1 --no-compile
  test -s "$o/pred.tif" && test -s "$o/pred_reverse.tif"
  sha256sum "$o/pred.tif" "$o/pred_reverse.tif"
}

u_tiles() {  # u_tiles SEGDIR NAME SOURCE
  set -e
  local sd=$1 s=$2 out=$L/$2/tiles
  rm -rf "$out"
  "$PY" "$HERE/fl.py" tiles "$s" "$sd" "$W/render/$s.zarr" "$W/infer/$s/pred.tif" "$W/infer/$s/pred_reverse.tif" "$out" "$3"
}

run() {
  cd "$REPO" && git checkout -q "$BRANCH" 2>/dev/null
  [ "$(git config core.hooksPath)" = tools/hooks ] || bash tools/hooks/install.sh >/dev/null 2>&1 || true
  ensure_docker || true
  unit env u_env || { [ -f "$L/FAILED_env.json" ] && { touch "$W/done/ALL"; push "env failed 3x: stop"; }; return 1; }
  ensure_docker || return 1
  unit list u_list || { [ -f "$L/FAILED_list.json" ] && { touch "$W/done/ALL"; push "list failed 3x: stop"; }; return 1; }
  local src
  if "$PY" -c "import json,sys; sys.exit(0 if json.load(open('$L/s3_listing.json'))['organizer_tifxyz_count'] else 1)"; then
    src=organizer; unit org u_org || return 1; SEGROOT=$W/seg
  else
    src=auto; SEGROOT=$W/grow
    mkdir -p "$L/grow"
    unit seeds u_seeds || { [ -f "$L/FAILED_seeds.json" ] && { touch "$W/done/ALL"; push "seeds failed 3x: stop"; }; return 1; }
    for k in $(seq 1 $N_GROW); do unit "grow_$k" u_grow "$k" > /dev/null || true; done
    for k in $(seq 1 $N_GROW); do [ -f "$W/done/grow_$k" ] || [ "$(cat "$W/fail/grow_$k" 2>/dev/null || echo 0)" -ge 3 ] || return 1; done
  fi
  touch "$W/kept.txt"
  while read -r s; do
    [ -z "$s" ] && continue
    unit "render_$s" u_render "$SEGROOT/$s" "$s" || continue
    unit "infer_$s" u_infer "$s" || continue
    unit "tiles_$s" u_tiles "$SEGROOT/$s" "$s" "$src" || continue
  done < <(sort -u "$W/kept.txt")
  "$PY" - "$L" "$W/kept.txt" "$src" <<'EOF' > "$L/SUMMARY.json"
import glob, json, os, sys
L, kept, src = sys.argv[1], sys.argv[2], sys.argv[3]
segs = sorted(set(l.strip() for l in open(kept) if l.strip()))
out = dict(scroll='PHerc0490B', source=src, kept_segments=segs, segments={})
for s in segs:
    m = f'{L}/{s}/tiles/manifest.json'
    out['segments'][s] = (dict(n_kept_tile_positions=json.load(open(m))['n_kept_tiles'],
                               n_png=len(json.load(open(m))['tiles'])) if os.path.exists(m) else 'incomplete')
out['grow_attempts'] = [json.load(open(p)) | {'meta': None} for p in sorted(glob.glob(f'{L}/grow/attempt_*.json'))]
out['failed_units'] = sorted(os.path.basename(p) for p in glob.glob(f'{L}/FAILED_*.json'))
json.dump(out, sys.stdout, indent=1)
EOF
  local NT; NT=$("$PY" -c "import glob,json; print(sum(json.load(open(p))['n_kept_tiles'] for p in glob.glob('$L/*/tiles/manifest.json')))")
  echo "- $(utc) DONE $NT tiles (2 x 2 cm positions; PNGs for both directions); summary logs/sib/fl2-pherc0490b/SUMMARY.json" >> "$L/STATUS.md"
  touch "$W/done/ALL"; push "pipeline complete: DONE $NT tiles"
}

case "${1:-run}" in
  run) run ;;
  loop)
    while [ ! -f "$W/done/ALL" ]; do
      bash "$0" run || log "run returned rc=$? (restart in 120 s)"
      [ -f "$W/done/ALL" ] || sleep 120
    done
    log "ALL done" ;;
esac
