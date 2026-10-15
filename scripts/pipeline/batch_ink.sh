#!/usr/bin/env bash
# batch_ink.sh: resumable mass render + ink + overlay pipeline for tifxyz surfaces (or crops of them).
#
#   bash batch_ink.sh LIST                         LIST: one surface per line (# comments ok):
#                                                    NAME SRC_TIFXYZ [scroll=PHerc0268] [theta=T0:T1] [rows=R0:R1] [cols=C0:C1]
#                                                                    [z=Z0:Z1] [flip=auto|0|1] [depths=0,1,2] [gate=GATE.json]
#   bash batch_ink.sh one NAME SRC [key=value ...]   a single surface, same keys
#
# Per surface (work dir $BI_ROOT/NAME; every stage leaves state/<stage>.done and is skipped when re-run):
#   prep     bi_prep.py: copy/crop to $W/NAME (tifxyz, uuid = NAME), outward-normal check (flip when < 0.5)
#   chunks   crop_and_chunks.py: level-0 CT chunks of the 66-layer render, then bi_chunkfilter.py drops
#            the chunks it lists far from the surface on ragged meshes (outside the valid-node bbox +- 64 vox)
#   mirror   bi_mirror.py: copy them into the scroll's local CT mirror ($BI_ROOT/ct_<scroll>.zarr unless
#            BI_MIRROR_<SCROLL> is set), size cap $MIRROR_CAP_GB: evicts chunks older than 120 min that this job does
#            not use, never while another render / mirror tool is running (see bi_mirror.py)
#   render   vc_render_tifxyz, 66 layers, slice step 1, scale 1, pyramid 0, [--flip-normals] -> $W/render.zarr
#   ink      villa ink_9um seed42 / seed43 / dense_native, one thread each, $JOBS concurrent, d in $DEPTHS (S = 25 + d,
#            layers S..S+16), --direction reverse (only the reverse = reading side is used; INK_DIR=both also writes forward)
#   hecate   (HECATE=1 only; off by default) Erwin's hecate_prep.py + hecate.py, reverse, z-centre 32.5 + ENS_DEPTH, CPU.
#            Measured on the control (1 thread): ~5 s per 64x64 patch = ~65 min per native Mpx, ~47x one villa run -> excluded;
#            this stage is not exercised end to end and bi_post.py does not use its output
#   overlay  overlay.py (the reference fixed-scale overlay) -> $W/overlay_ref.png
#   post     bi_post.py: ensembles (d1, dmax), overlays, fibre renders, stats.json, tile grid (+ gate tiles)
#   panel    make_panel.py: $W/panel_{d1,dmax}/NAME.png (+ .json), whole surface, reading orientation
#   clean    KEEP_RENDER=0: delete render.zarr (ctlayers_31-35.tif keeps the CT layers the panels need)
# Small results (stats.json, PNG previews < 2 MB) are copied to $BI_SMALL/NAME.
# Measured (4 CPUs shared with another agent): villa ~84 s per Mpx per run (1 thread); 3 models x 3 depths with 2 jobs
# = ~7 min wall per Mpx of surface (a 4 cm2 isometric surface = 5.4 Mpx -> ~38 min); render 7-9 s per surface (incl. docker start);
# chunk listing ~62 s/Mpx (single core).
# Edit only via write-new-file + rename (see the last line).
# Env: PYH, PYI (python with numpy/scipy/zarr/tifffile; python with villa vesuvius + torch), CKPT (checkpoint dir), VC (vc_render_tifxyz runner,
#      default ./vc.sh), DOCKER_DATA_ROOT, BI_ROOT ($PWD/bi_work) BI_SMALL ($BI_ROOT/small) JOBS (2) DEPTHS ("0 1 2") ENS_DEPTH (1) BF16 (0)
#      VC_CPUS (2) CACHE_GB (2) MIRROR_CAP_GB (2.5) KEEP_RENDER (1) INK_DIR (reverse) HECATE (0) STAGES (all) FORCE ("")
#      RENDER_FILL (""; reflect = the ink models read render_fill.zarr, a copy with the blank margin filled by render_fill.py;
#      validity/scoring/overlays still use render.zarr; see docs/METHODS.md §5)
#      BI_MIRROR_<SCROLL> (private CT mirror path; default $BI_ROOT/ct_<scroll>.zarr), UMB_<SCROLL> (scroll-axis JSON)
# Review (2026-10-11) recommendations for a mass PHerc0268 search:
#   INK_DIR=both DEPTHS="<1-2 depths>" : bi_post then reports face specificity (forward vs reverse at the same S). Recto ink
#     is face-specific (PHerc0343 letters: 99 % / 72 % of reverse p>0.55 px have forward p<0.40, r(fwd,rev) 0.07 / 0.24);
#     two PHerc0268 test surfaces give 5 % and 0-4 % at every d in -6..+6 (r 0.48-0.73) = not ink. Same cost as 3 reverse depths.
#   gate=<tile_gate JSON> per surface: on one such surface the p>0.55 pixels sit on OFF_SHEET tiles (6.9 %) vs 0.4 % on ON_SHEET tiles.
#   KEEP_RENDER=0 (a render is ~60 MB per Mpx) and ENS_DEPTH inside DEPTHS (panels now follow ENS_DEPTH).
#   Changing INK_DIR on a finished surface needs FORCE="ink post panel" (the ink stage is marked done).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
BI_ROOT=${BI_ROOT:-$PWD/bi_work}; BI_SMALL=${BI_SMALL:-$BI_ROOT/small}
JOBS=${JOBS:-2}; DEPTHS=${DEPTHS:-"0 1 2"}; ENS_DEPTH=${ENS_DEPTH:-1}; BF16=${BF16:-0}; VC_CPUS=${VC_CPUS:-2}
CACHE_GB=${CACHE_GB:-2}; MIRROR_CAP_GB=${MIRROR_CAP_GB:-2.5}; KEEP_RENDER=${KEEP_RENDER:-1}; INK_DIR=${INK_DIR:-reverse}
RENDER_FILL=${RENDER_FILL:-}; HECATE=${HECATE:-0}; STAGES=${STAGES:-prep chunks mirror render ink hecate overlay post panel clean}; FORCE=${FORCE:-}
PYH=${PYH:-python3}; PYI=${PYI:-python3}; CKPT=${CKPT:?set CKPT to the checkpoint dir (docs/REPRODUCE.md)}; RUNINK=$HERE/run_ink_local.py; VC=${VC:-$HERE/vc.sh}
MODELS="hybrid_3d2d-seed42_step-075000 hybrid_3d2d-seed43_step-075000 dense_native-016000.rebuilt"
export BI_ROOT BI_SMALL BF16 PYI CKPT RUNINK INK_DIR RENDER_FILL

log() { echo "[$(date +%H:%M:%S)] $*"; }
ensure_docker() {
  docker info >/dev/null 2>&1 && return 0
  log "starting dockerd"; mkdir -p "$BI_ROOT/logs"; nohup dockerd --data-root "${DOCKER_DATA_ROOT:-/var/lib/docker}" >> "$BI_ROOT/logs/dockerd.log" 2>&1 &
  for _ in $(seq 60); do docker info >/dev/null 2>&1 && return 0; sleep 2; done; log "dockerd did not start"; return 1
}

# one villa run: MODEL S W  (atomic outputs; skip when present)
ink1() {
  local m=$1 s=$2 W=$3 e; e=$((s + 17))
  local out="$W/ink/${m}__s${s}_reverse.tif" Z="$W/render.zarr"; [ -n "$RENDER_FILL" ] && Z="$W/render_fill.zarr"
  [ -s "$out" ] && { [ "$INK_DIR" != both ] || [ -s "$W/ink/${m}__s${s}.tif" ]; } && return 0
  rm -f "$W/ink/.tmp_${m}__s${s}"*.tif
  (mkdir -p "$BI_ROOT/tmp"; cd "$BI_ROOT" && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMPDIR="$BI_ROOT/tmp" "$PYI" -I "$RUNINK" 1 "$BF16" -- \
      "$Z" "$CKPT/$m.pth" "$W/ink/.tmp_${m}__s${s}.tif" --overlap 0.5 --blend-mode hann --batch-size 4 \
      --direction "$INK_DIR" --layer-start "$s" --layer-end "$e" --no-compile --num-workers 0) > "$W/logs/ink_${m}__s${s}.log" 2>&1 \
    || { echo "FAILED ink $m s=$s ($W/logs/ink_${m}__s${s}.log)"; return 1; }
  if [ "$INK_DIR" = both ]; then
    mv -f "$W/ink/.tmp_${m}__s${s}.tif" "$W/ink/${m}__s${s}.tif"; mv -f "$W/ink/.tmp_${m}__s${s}_reverse.tif" "$out"
  else
    mv -f "$W/ink/.tmp_${m}__s${s}.tif" "$out"
  fi
  echo "ink $m s=$s $(grep -o 'E2E_WALL_S [0-9.]*' "$W/logs/ink_${m}__s${s}.log")"
}
export -f ink1

surface() {   # NAME SRC [key=value ...]
  local NAME=$1 SRC=$2; shift 2
  local SCROLL="" THETA="" ROWS="" COLS="" ZR="" FLIPM=auto DEP="$DEPTHS" GATE=""
  for kv in "$@"; do case $kv in
    scroll=*) SCROLL=${kv#*=};; theta=*) THETA=${kv#*=};; rows=*) ROWS=${kv#*=};; cols=*) COLS=${kv#*=};;
    z=*) ZR=${kv#*=};; flip=*) FLIPM=${kv#*=};; depths=*) DEP=${kv#*=}; DEP=${DEP//,/ };; gate=*) GATE=${kv#*=};;
    *) log "unknown key $kv"; return 2;; esac; done
  [ -n "$SCROLL" ] || SCROLL=$("$PYH" -I -c "import sys; sys.path.insert(0,'$HERE'); import bi_common as C; print(C.scroll_of('$SRC'))")
  local W=$BI_ROOT/$NAME; mkdir -p "$W/state" "$W/logs" "$W/ink"
  exec 9> "$W/.lock"; flock -n 9 || { log "$NAME: locked by another run"; return 3; }
  local MIRROR; MIRROR=$("$PYH" -I -c "import sys; sys.path.insert(0,'$HERE'); import bi_common as C; print(C.SCROLLS['$SCROLL']['mirror'])")
  done_() { touch "$W/state/$1.done"; }
  need() { case " $STAGES " in *" $1 "*) ;; *) return 1;; esac; [ -n "$FORCE" ] && [[ " $FORCE " == *" $1 "* ]] && rm -f "$W/state/$1.done"; [ ! -e "$W/state/$1.done" ]; }
  tstage() { local st=$1 t=$2; echo "$st $(( $(date +%s) - t ))" >> "$W/timing.tsv"; }
  local t
  log "== $NAME ($SCROLL) src=$SRC theta=$THETA rows=$ROWS cols=$COLS z=$ZR flip=$FLIPM depths='$DEP'"
  if need prep; then t=$(date +%s)
    args=(); [ -n "$THETA" ] && args+=(--theta "$THETA"); [ -n "$ROWS" ] && args+=(--rows "$ROWS"); [ -n "$COLS" ] && args+=(--cols "$COLS")
    [ -n "$ZR" ] && args+=(--z "$ZR")
    rm -rf "$W/$NAME"; "$PYH" -I "$HERE/bi_prep.py" "$SRC" "$W/$NAME" --scroll "$SCROLL" --name "$NAME" --flip "$FLIPM" "${args[@]}" \
      > "$W/logs/prep.json" || { log "prep failed"; return 1; }
    "$PYH" -I -c "import json; p=json.load(open('$W/prep.json')); print('prep: grid', p['grid'], 'area_cm2', p['area_cm2'], 'outward', p['outward_fraction'], 'flip', p['flip_normals'], 'theta', p['theta_deg'], 'z', p['z_vox'])"
    tstage prep "$t"; done_ prep; fi
  if need chunks; then t=$(date +%s)
    rm -rf "$W/cc"; "$PYH" -I "$HERE/crop_and_chunks.py" "$W/$NAME" "$W/cc/$NAME" -1e9 1e9 > "$W/logs/chunks.json" \
      || { log "chunks failed"; return 1; }
    for c in x y z; do cmp -s "$W/$NAME/$c.tif" "$W/cc/$NAME/$c.tif" || "$PYH" -I -c "
import tifffile, numpy as np, sys; a=tifffile.imread('$W/$NAME/$c.tif'); b=tifffile.imread('$W/cc/$NAME/$c.tif')
sys.exit(0 if a.shape==b.shape and np.array_equal(a,b) else 1)" || { log "chunk lister changed the grid ($c)"; return 1; }; done
    mv "$W/cc/$NAME.chunks.json" "$W/chunks.json"; rm -rf "$W/cc"; log "chunks: $(cat "$W/logs/chunks.json" | cut -c1-200)"
    # drop chunks crop_and_chunks.py lists far from the surface on ragged meshes (bbox +- 64 vox; see bi_chunkfilter.py)
    "$PYH" -I "$HERE/bi_chunkfilter.py" "$W/$NAME" "$W/chunks.json" | tee "$W/logs/chunk_filter.json" || return 1
    tstage chunks "$t"; done_ chunks; fi
  if need mirror; then t=$(date +%s)
    "$PYH" -I "$HERE/bi_mirror.py" "$W/chunks.json" --scroll "$SCROLL" --dst "$MIRROR" --cap-gb "$MIRROR_CAP_GB" | tee -a "$W/logs/mirror.json" \
      || { log "mirror failed"; return 1; }
    tstage mirror "$t"; done_ mirror; fi
  if need render; then t=$(date +%s); ensure_docker || return 1
    local FLIP=""; [ "$("$PYH" -I -c "import json; print(json.load(open('$W/prep.json'))['flip_normals'])")" = True ] && FLIP=--flip-normals
    # mirror again (no-op when complete): chunks may have been evicted by another job between the stages
    "$PYH" -I "$HERE/bi_mirror.py" "$W/chunks.json" --scroll "$SCROLL" --dst "$MIRROR" --cap-gb 1000 > "$W/logs/mirror_recheck.json" || return 1
    rm -rf "$W/render.zarr" "$W/render.tmp.zarr"
    (cd "$BI_ROOT" && VC_CPUS=$VC_CPUS OMP_NUM_THREADS=$VC_CPUS "$VC" vc_render_tifxyz --volume "$MIRROR" --group-idx 0 --scale 1 \
        --segmentation "$W/$NAME" --num-slices 66 --slice-step 1 --cache-gb "$CACHE_GB" --pyramid 0 $FLIP \
        --zarr-output "$W/render.tmp.zarr") > "$W/logs/render.log" 2>&1 || { log "render failed (logs/render.log)"; tail -5 "$W/logs/render.log"; return 1; }
    mv "$W/render.tmp.zarr" "$W/render.zarr"
    log "render: $(grep -o '"shape": \[[^]]*\]' "$W/render.zarr/0/.zarray" | tr -d '\n ') flip='$FLIP'"
    echo "flip_normals_used '$FLIP'" > "$W/logs/render_flip.txt"
    tstage render "$t"; done_ render; fi
  if need ink; then t=$(date +%s)
    if [ -n "$RENDER_FILL" ] && [ ! -d "$W/render_fill.zarr" ]; then
      "$PYH" -I "$HERE/render_fill.py" "$W/render.zarr" "$W/render_fill.zarr" --mode "$RENDER_FILL" > "$W/logs/render_fill.json" \
        || { log "render fill failed"; return 1; }; log "render fill: $(cat "$W/logs/render_fill.json")"; fi
    jl=(); for d in $DEP; do for m in $MODELS; do jl+=("$m $((25 + d))"); done; done
    printf '%s\n' "${jl[@]}" | W="$W" xargs -P "$JOBS" -L 1 bash -c 'ink1 "$0" "$1" "$W"'
    local miss=0; for d in $DEP; do for m in $MODELS; do [ -s "$W/ink/${m}__s$((25 + d))_reverse.tif" ] || miss=$((miss + 1)); done; done
    [ $miss -eq 0 ] || { log "ink: $miss maps missing"; return 1; }
    tstage ink "$t"; done_ ink; fi
  if [ "$HECATE" = 1 ] && need hecate; then t=$(date +%s)
    local ZC; ZC=$(awk -v d="$ENS_DEPTH" 'BEGIN{printf "%.2f", 32.5 + d}'); local HS=${HECATE_SCRIPTS:?HECATE=1 needs HECATE_SCRIPTS (pherc343-first-letters/ink/scripts)}
    rm -rf "$W/hec_prep.zarr"
    (cd "$BI_ROOT" && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 "$PYI" -I "$HS/hecate_prep.py" --src "$W/render.zarr" --out "$W/hec_prep.zarr" \
        --native-um 8.64 --native-um-z 8.64 --target-um 9.6 --z-center "$ZC" --nz 16 && \
     cd "$BI_ROOT" && OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMPDIR="$BI_ROOT/tmp" "$PYI" -I "$CKPT/hecate.py" --checkpoint "$CKPT/hecate_9.6um.pth" \
        --input "$W/hec_prep.zarr" --spacing-um 9.6 --output "$W/ink/hecate__zc${ZC}_reverse.png" --device cpu --batch-size 4 --reverse) \
        > "$W/logs/hecate.log" 2>&1 || { log "hecate failed (logs/hecate.log)"; return 1; }
    rm -rf "$W/hec_prep.zarr"; tstage hecate "$t"; done_ hecate; fi
  if need overlay; then t=$(date +%s)
    if [ "$ENS_DEPTH" = 1 ]; then "$PYH" -I "$HERE/overlay.py" "$W/render.zarr" "$W/ink" "$W/overlay_ref.png" | tee "$W/logs/overlay_ref.txt" \
      || { log "overlay failed"; return 1; }; fi
    tstage overlay "$t"; done_ overlay; fi
  if need post; then t=$(date +%s)
    pa=(); [ -n "$GATE" ] && pa+=(--gate "$GATE")
    "$PYH" -I "$HERE/bi_post.py" "$W" --ens-depth "$ENS_DEPTH" --small-dir "$BI_SMALL/$NAME" "${pa[@]}" || { log "post failed"; return 1; }
    if [ -s "$W/overlay_ref.png" ]; then "$PYH" -I -c "
import numpy as np; from PIL import Image
a=np.asarray(Image.open('$W/overlay_ref.png')); b=np.asarray(Image.open('$W/overlay_d1.png'))
print('overlay_d1 vs overlay.py: identical' if a.shape==b.shape and np.array_equal(a,b) else f'overlay_d1 vs overlay.py: max abs diff {np.abs(a.astype(int)-b.astype(int)).max()}')" | tee "$W/logs/overlay_check.txt"; fi
    tstage post "$t"; done_ post; fi
  if need panel; then t=$(date +%s)
    for v in "d$ENS_DEPTH" dmax; do   # review fix: was 'd1' always; with ENS_DEPTH != 1 make_panel crashed on the missing s26 maps
      "$PYH" -I "$HERE/make_panel.py" "$W" --out-dir "$W/panel_$v" --variant "$v" --small-copy "$BI_SMALL/$NAME/panel_$v" || { log "panel $v failed"; return 1; }
    done
    tstage panel "$t"; done_ panel; fi
  if need clean && [ "$KEEP_RENDER" = 0 ]; then rm -rf "$W/render.zarr" "$W/render_fill.zarr"; log "render.zarr deleted (KEEP_RENDER=0)"; done_ clean; fi
  log "== $NAME done: $W  (small: $BI_SMALL/$NAME)"
}

main() {
  case "${1:-}" in
    one) shift; surface "$@" < /dev/null ;;
    ""|-h|--help) sed -n 2,42p "$0"; return 1 ;;
    *) local LIST=$1 rc=0 line
       [ -r "$LIST" ] || { log "cannot read list $LIST"; return 1; }
       while read -r line; do line=${line%%#*}; [ -z "${line// }" ] && continue
         # shellcheck disable=SC2086
         ( surface $line ) < /dev/null || { rc=1; log "SURFACE FAILED: $line"; }
       done < "$LIST"; return $rc ;;
  esac
}
# one line: bash parses it whole before running, so editing this file during a run cannot inject commands.
# Edit this script only by writing a new file and renaming it over (running instances keep the old inode).
main "$@"; exit $?
