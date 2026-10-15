#!/bin/bash
# RULES R-CROSS: run the team's own vc_tifxyz_selfcross census over a population of tifxyz dirs.
# Report-only; nothing is modified and no verdict changes. Reports land in $D/gates/rcross/<population>/<name>.json
#   rcross.sh <population-name> <tifxyz dir | dir-of-tifxyz-dirs> ...
set -u
D=${HERCULES_DATA:-/home/user/hercules_data}
BIN=/opt/vc/bin/vc_tifxyz_selfcross
IMG=${VC_IMAGE:-ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04}
pop=$1; shift
outdir=$D/gates/rcross/$pop; mkdir -p "$outdir"
cpath() { python3 -c "import os,sys;p=os.path.realpath(sys.argv[1]);r=os.path.realpath('$D');print('/data'+p[len(r):] if p.startswith(r) else sys.exit('not under data: '+p))" "$1"; }
targets=()
for a in "$@"; do
  if [ -f "$a/x.tif" ]; then targets+=("$a")
  else for d in "$a"/*/; do [ -f "$d/x.tif" ] && targets+=("${d%/}"); done; fi
done
echo "[rcross $(date -u +%FT%TZ)] $pop: ${#targets[@]} surfaces"
for t in "${targets[@]}"; do
  name=$(basename "$(dirname "$t")")__$(basename "$t")
  rep="$outdir/$name.json"
  [ -s "$rep" ] && continue
  nice -n 19 docker run --rm -e LD_LIBRARY_PATH=/opt/vc/lib -v "$D:/data" -v "$D/vc_install:/opt/vc:ro" "$IMG" \
    $BIN "$(cpath "$t")" -o "$(cpath "$outdir")/$name.json" >> "$outdir/census.log" 2>&1 \
    || echo "[rcross] FAILED $name" | tee -a "$outdir/census.log"
done
echo "[rcross $(date -u +%FT%TZ)] $pop done: $(ls "$outdir"/*.json 2>/dev/null | wc -l) reports"
