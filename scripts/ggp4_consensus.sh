#!/bin/bash
# RULES G-GP part 4, milestone 2: build the consensus surface from the concentrated campaign.
# The source set is the campaign's traces PLUS the patch their seeds came from, gathered into one directory of
# symlinks because vc_grow_seg_from_segments takes a single --src-dir. Symlinks are used rather than copies so the
# sources stay single-authority; the whole tree is inside $HERCULES_DATA, which is what the container mounts.
#   ggp4_consensus.sh <scroll> <vol> <um> <X> <Y> <Z> [consensus_th]
# PART=<n> names the target directory and the records, so a later generation does not overwrite an earlier
# one; the source set is always EVERY trace in patches/<scroll>_dense plus the patch the first seeds came from.
set -euo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
sc=$1; vol=$2; um=$3; X=$4; Y=$5; Z=$6; th=${7:-6}; PART=${PART:-4}
src=$D/patches/${sc}_src; tgt=$D/patches/${sc}_cons_part${PART}
rm -rf "$src"; mkdir -p "$src"
# The symlinks MUST be relative. The container mounts $HERCULES_DATA at /data, so an absolute host symlink
# (/home/user/hercules_data/...) does not resolve inside it and vc_grow_seg_from_segments reports
# "no source surfaces found" -- which is exactly what happened on the first run.
srcpatch=$(python3 -c "import json;print(json.load(open('$D/gates/ggp/part4_source_patch.json'))['dir'])")
link() { ln -s "../$(basename "$(dirname "$1")")/$(basename "$1")" "$src/$(basename "$1")"; }
link "$srcpatch"
n=1
for d in $D/patches/${sc}_dense/auto_grown_*; do
  [ -d "$d" ] && { link "$d"; n=$((n+1)); }
done
# prove they resolve before spending the growth
bad=0
for l in "$src"/*; do [ -f "$l/x.tif" ] || { echo "[ggp part $PART] BROKEN LINK: $l"; bad=1; }; done
[ "$bad" -eq 0 ] || { echo "[ggp part $PART] refusing to run with unresolvable source links"; exit 1; }
echo "[ggp part $PART $(date -u +%FT%TZ)] source set: $n surfaces (1 seed patch + $((n-1)) campaign traces) in $src"
CONSENSUS_TH=$th VC_VOLUME=${VC_VOLUME:-$D/pred_local/$sc} VC_NICE=${VC_NICE:-8} VC_THREADS=${VC_THREADS:-2} \
  bash $R/scripts/vc_consensus.sh "$sc" "$vol" "$um" "$X" "$Y" "$Z" "$src" "$tgt"
echo "[ggp part $PART $(date -u +%FT%TZ)] measuring the consensus output with the same instruments"
bash $R/scripts/rcross.sh cons_part${PART} "$tgt" || true
$R/.venv/bin/python $R/scripts/mesh_distortion.py --batch "$tgt" --um "$um" \
  --label "G-GP part $PART consensus output" --json $D/gates/ggp/part${PART}_consensus_mesh.json || true
