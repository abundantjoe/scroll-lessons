#!/bin/bash
# RULES G-GP part 3: vc_grow_seg_from_segments -- the team's SECOND growth stage, a consensus surface grown from a
# directory of stage-1 patches. Parameters are the team's own, read verbatim off their published PHerc1447 segments
# (meta.json "vc_grow_seg_from_segments_params"); they are not tuned here.
#   vc_consensus.sh <scroll> <vol> <um> <X> <Y> <Z> <src_patches_dir> <target_dir>
set -euo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}
IMG=${VC_IMAGE:-ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04}
BUCKET_S3=s3://vesuvius-challenge-open-data
SURF_SUFFIX=${SURF_SUFFIX:--surface-20260413222639-surface-m7-L0-th0.2}
[ $# -eq 8 ] || { echo "usage: vc_consensus.sh <scroll> <vol> <um> <X> <Y> <Z> <src_dir> <tgt_dir>" >&2; exit 2; }
scroll=$1; vol=$2; um=$3; X=$4; Y=$5; Z=$6; src=$7; tgt=$8
cpath() { python3 -c "import os,sys;p=os.path.realpath(sys.argv[1]);r=os.path.realpath('$D');print('/data'+p[len(r):] if p.startswith(r) else sys.exit('not under data: '+p))" "$1"; }
mkdir -p "$tgt/logs" "$D/vc_cache/$scroll" "$D/normal_grids/$scroll"
params="$tgt/params.json"
# The team's published values, verbatim, plus the fields stage 2 needs to run here (cache root, voxel size, normal
# grids, thread limit). CONSENSUS_TH exists only so a LATER, separately declared experiment can vary it; this run
# uses the team's 6 and RULES records that it is not tuned.
cat > "$params" <<JSON
{
  "consensus_default_th": ${CONSENSUS_TH:-6},
  "consensus_limit_th": 2,
  "flip_x": false,
  "global_steps_per_window": 2,
  "step": 6,
  "thread_limit": ${VC_THREADS:-2},
  "voxelsize": $um,
  "cache_root": "$(cpath "$D/vc_cache/$scroll")",
  "normal_grid_path": "$(cpath "$D/normal_grids/$scroll")",
  "direction_fields": []
}
JSON
log="$tgt/logs/consensus_${X}_${Y}_${Z}_$(date -u +%Y%m%dT%H%M%SZ).log"
ARGV=(docker run --rm --network host)
for e in HTTPS_PROXY https_proxy NO_PROXY no_proxy SSL_CERT_FILE=/ca.crt CURL_CA_BUNDLE=/ca.crt AWS_CA_BUNDLE=/ca.crt \
         AWS_EC2_METADATA_DISABLED=true HOME=/data/vc_home "OMP_NUM_THREADS=${VC_THREADS:-2}" LD_LIBRARY_PATH=/opt/vc/lib; do
  ARGV+=(-e "$e")
done
# vc_grow_seg_from_segments opens its volume with VcDataset, the LOCAL filesystem zarr reader -- unlike stage 1 it
# has no s3:// path. VC_VOLUME points at a locally materialised store (scripts/fetch_pred_box.py); the s3 URL is kept
# as the default only so the failure is the tool's own clear one rather than a silently different volume.
volume_arg="$BUCKET_S3/$scroll/representations/predictions/surfaces/$vol$SURF_SUFFIX.zarr/"
if [ -n "${VC_VOLUME:-}" ]; then volume_arg=$(cpath "$VC_VOLUME"); fi
ARGV+=(-v /root/.ccr/ca-bundle.crt:/ca.crt:ro -v "$D:/data" -v "$D/vc_install:/opt/vc:ro" "$IMG"
       /opt/vc/bin/vc_grow_seg_from_segments
       --volume "$volume_arg"
       --src-dir "$(cpath "$src")" --target-dir "$(cpath "$tgt")" --params "$(cpath "$params")"
       --seed-coord "$X,$Y,$Z")
echo "# $(date -u +%FT%TZ) ${ARGV[*]}" >> "$log"
nice -n "${VC_NICE:-10}" "${ARGV[@]}" >> "$log" 2>&1
echo "[consensus $(date -u +%FT%TZ)] done; see $log"
