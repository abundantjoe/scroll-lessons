#!/bin/bash
# vc_tools.sh -- run the REBUILT VC3D command-line tools (scripts/build_vc3d.sh -> $DATA/vc_install/{bin,lib})
# inside the CI builder image, with the data root mounted at /data (MASTER_PROMPT_v4 5.7, 5.9, 5.13).
#
#   vc_tools.sh trace   <scroll> <vol> <um> <X> <Y> <Z> <patches_dir>          5.7 tracer, one seed (level-0 voxels)
#   vc_tools.sh render  <scroll> <vol> <pitch-string> <um> <patch_dir> <render.zarr>   5.9 render, 28 slices, no flip
#   vc_tools.sh flatten <patch_dir> <out_dir>                                  5.13 vc_flatten (ABF++)
#   vc_tools.sh help
# Every host path must lie under $HERCULES_DATA (default /home/user/hercules_data); it is mapped to /data/... in the
# container. Environment: VC_DRY_RUN=1 prints the docker argv one element per line and runs nothing (tests);
# VC_THREADS (OMP_NUM_THREADS, default 2 = the tracer's thread_limit); VC_IMAGE overrides the image.
# Idempotent: trace skips a seed whose logs/seed_X_Y_Z.done exists; render skips when <render.zarr>.complete exists;
# flatten skips when <out_dir>/.flatten_complete exists. Logs go to <patches_dir>/logs/ (trace) or beside the output.
set -euo pipefail
DATA=${HERCULES_DATA:-/home/user/hercules_data}
IMG=${VC_IMAGE:-ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04}
BUCKET_HTTPS=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com
BUCKET_S3=s3://vesuvius-challenge-open-data
SURF_SUFFIX=${SURF_SUFFIX:--surface-20260413222639-surface-m7-L0-th0.2}   # team surface prediction id (section 3); override for e.g. the L2 predictions of 2.4 um rescans
VC_CACHE_SUFFIX=${VC_CACHE_SUFFIX:-}                          # keeps the VC volume cache of another prediction/volume of the same scroll apart (e.g. _L2)
CA=${CURL_CA_BUNDLE:-/root/.ccr/ca-bundle.crt}
PY=${VC_PYTHON:-${HERCULES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}/.venv/bin/python}
[ -x "$PY" ] || PY=$(command -v python3 || command -v python)   # no repo venv (e.g. CI): the interpreter on PATH
RENDER_TRIES=3                                                # 5.9: an all-zero render is re-rendered, give up after three
RENDER_CACHE_GB=${VC_RENDER_CACHE_GB:-4}                      # 5.9 says 8; 4 on this 15 GB box (task instruction)

usage() { sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
die() { echo "vc_tools.sh: $*" >&2; exit 1; }

# host path -> container path (/data/...). The path need not exist yet.
cpath() {
  local p; p=$(realpath -m "$1")
  case "$p" in "$DATA"/*) echo "/data${p#"$DATA"}" ;; "$DATA") echo /data ;; *) die "path not under $DATA: $1" ;; esac
}

# docker argv prefix; $1 = OMP threads
docker_argv() {
  printf '%s\n' docker run --rm --network host
  for e in HTTPS_PROXY https_proxy NO_PROXY no_proxy SSL_CERT_FILE=/ca.crt CURL_CA_BUNDLE=/ca.crt AWS_CA_BUNDLE=/ca.crt \
           AWS_EC2_METADATA_DISABLED=true HOME=/data/vc_home "OMP_NUM_THREADS=$1" LD_LIBRARY_PATH=/opt/vc/lib; do printf '%s\n' -e "$e"; done
  printf '%s\n' -v /root/.ccr/ca-bundle.crt:/ca.crt:ro -v "$DATA:/data" -v "$DATA/vc_install:/opt/vc:ro" "$IMG"
}

# run (or print) a docker command; argv is read from the array ARGV; stdout+stderr appended to log $1
run_docker() {
  local log=$1
  if [ "${VC_DRY_RUN:-0}" = 1 ]; then printf '%s\n' "${ARGV[@]}"; return 0; fi
  mkdir -p "$(dirname "$log")"; mkdir -p "$DATA/vc_home"
  { echo "# $(date -u +%FT%TZ) ${ARGV[*]}"; "${ARGV[@]}"; } >> "$log" 2>&1
}

fetch() {  # fetch <url> <dest> (curl with retries, atomic); skipped when dest exists
  [ -s "$2" ] && return 0
  mkdir -p "$(dirname "$2")"
  curl -fsS --retry 5 --retry-delay 3 --cacert "$CA" -o "$2.part" "$1" && mv "$2.part" "$2"
}

cmd_trace() {
  [ $# -eq 7 ] || die "trace <scroll> <vol> <um> <X> <Y> <Z> <patches_dir>"
  local scroll=$1 vol=$2 um=$3 X=$4 Y=$5 Z=$6 patches=$7
  local grids="$DATA/normal_grids/$scroll" pred="$vol$SURF_SUFFIX"
  local surf_https="$BUCKET_HTTPS/$scroll/representations/predictions/surfaces/$pred"
  mkdir -p "$grids" "$patches/logs" "$DATA/vc_cache/$scroll$VC_CACHE_SUFFIX"
  # 5.7: the store's metadata.json plus the remote marker; grid files are then fetched lazily into this dir
  echo "{\"url\": \"$surf_https.normal-grids\"}" > "$grids/normal-grids-remote.json"
  if [ ! -s "$grids/metadata.json" ]; then
    [ "${VC_DRY_RUN:-0}" = 1 ] || fetch "$surf_https.normal-grids/metadata.json" "$grids/metadata.json"
  fi
  local params="$patches/params.json" c_cache c_grids c_patches c_params
  c_cache=$(cpath "$DATA/vc_cache/$scroll$VC_CACHE_SUFFIX"); c_grids=$(cpath "$grids"); c_patches=$(cpath "$patches"); c_params=$(cpath "$params")
  # TRACE_GENERATIONS: RULES R-SMALL runs interior seeds at a reduced growth budget (a 5 cm2 patch grown at 60
  # generations has many chances to step across a 449 um wrap). Default 60, the budget every trace on record used.
  printf '{"mode":"seed","min_area_cm":0.2,"generations":%s,"thread_limit":2,"cache_root":"%s","direction_fields":[],"voxelsize":%s,"normal_grid_path":"%s"}\n' \
    "${TRACE_GENERATIONS:-60}" "$c_cache" "$um" "$c_grids" > "$params"
  local done="$patches/logs/seed_${X}_${Y}_${Z}.done"
  [ -f "$done" ] && { echo "trace: seed $X $Y $Z already done ($done)"; return 0; }
  mapfile -t ARGV < <(docker_argv 2)
  ARGV+=(/opt/vc/bin/vc_grow_seg_from_seed --volume "$BUCKET_S3/$scroll/representations/predictions/surfaces/$pred.zarr/"
         --target-dir "$c_patches" --params "$c_params" --seed "$X" "$Y" "$Z")
  local log="$patches/logs/trace_${X}_${Y}_${Z}_$(date -u +%Y%m%dT%H%M%SZ).log"
  run_docker "$log" && { [ "${VC_DRY_RUN:-0}" = 1 ] || echo "$log" > "$done"; }
}

render_is_zero() {  # 0 (true) when every sample of group "0" is zero (or the array is missing)
  "$PY" - "$1" <<'EOF'
import sys, zarr, numpy as np
try:
    a = zarr.open_group(sys.argv[1], mode="r")["0"]
    z, h, w = a.shape; sl = a[z // 2]; mx = int(np.asarray(sl).max())
    if mx == 0: mx = int(np.asarray(a[z // 4]).max()) or int(np.asarray(a[3 * z // 4]).max())
except Exception as e:
    print("render_is_zero: %s" % e, file=sys.stderr); sys.exit(0)
sys.exit(1 if mx > 0 else 0)
EOF
}

cmd_render() {
  [ $# -eq 6 ] || die "render <scroll> <vol> <pitch-string e.g. 8.640um-1.2m-116keV> <um> <patch_dir> <render.zarr>"
  local scroll=$1 vol=$2 pitch=$3 um=$4 patch=$5 out=$6
  [ -f "$out.complete" ] && { echo "render: complete ($out.complete)"; return 0; }
  mkdir -p "$DATA/vc_cache/$scroll"
  local c_cache c_patch c_out; c_cache=$(cpath "$DATA/vc_cache/$scroll"); c_patch=$(cpath "$patch"); c_out=$(cpath "$out")
  mapfile -t ARGV < <(docker_argv "${VC_THREADS:-2}")
  # RENDER_SLICES (default 28), RENDER_GROUP (pyramid level, default 0), RENDER_ARGS (extra renderer flags, e.g. "--scale-segmentation 4 --crop-x 160 ..."),
  # RENDER_AUTOCROP=0 drops --auto-crop (needed with an explicit crop): used by the 2.4 um route (B-2UM).
  local extra=(); [ -n "${RENDER_ARGS:-}" ] && read -ra extra <<< "$RENDER_ARGS"
  [ "${RENDER_AUTOCROP:-1}" = 1 ] && extra+=(--auto-crop)
  ARGV+=(/opt/vc/bin/vc_render_tifxyz --volume "$c_cache" --remote-url "$BUCKET_S3/$scroll/volumes/$vol-$pitch-masked.zarr/"
         --segmentation "$c_patch" --zarr-output "$c_out" --scale 1 --group-idx "${RENDER_GROUP:-0}" --num-slices "${RENDER_SLICES:-28}"
         --slice-step 1 --cache-gb "$RENDER_CACHE_GB" --voxel-size "$um" --voxel-unit micrometer "${extra[@]}" --pyramid 0)
  local log="${out%.zarr}_render.log" t rc
  [ "${VC_DRY_RUN:-0}" = 1 ] && { run_docker "$log"; return 0; }
  for t in $(seq 1 $RENDER_TRIES); do
    rm -rf "$out"
    rc=0; run_docker "$log" || rc=$?
    [ $rc -eq 0 ] || { echo "render: attempt $t exit $rc (see $log)" >&2; continue; }
    if render_is_zero "$out"; then echo "render: attempt $t all zero (transient fetch failure), re-rendering" >&2; rm -rf "$out"; continue; fi
    echo "$(date -u +%FT%TZ) attempts=$t" > "$out.complete"; return 0
  done
  die "render failed after $RENDER_TRIES attempts: $out"
}

cmd_flatten() {
  [ $# -eq 2 ] || die "flatten <patch_dir> <out_dir>"
  local patch=$1 out=$2
  [ -f "$out/.flatten_complete" ] && { echo "flatten: complete ($out/.flatten_complete)"; return 0; }
  local c_patch c_out; c_patch=$(cpath "$patch"); c_out=$(cpath "$out")
  mapfile -t ARGV < <(docker_argv "${VC_THREADS:-2}")
  ARGV+=(/opt/vc/bin/vc_flatten -i "$c_patch" -o "$c_out")
  run_docker "$(dirname "$out")/$(basename "$out")_flatten.log" && { [ "${VC_DRY_RUN:-0}" = 1 ] || date -u +%FT%TZ > "$out/.flatten_complete"; }
}

case "${1:-help}" in
  trace) shift; cmd_trace "$@" ;;
  render) shift; cmd_render "$@" ;;
  flatten) shift; cmd_flatten "$@" ;;
  help|-h|--help) usage ;;
  *) usage; die "unknown subcommand: $1" ;;
esac
