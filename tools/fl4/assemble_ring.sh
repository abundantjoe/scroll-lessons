#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-5 item 5: gather one ring's lane outputs (lane branch + local), unroll both ink_9um directions into continuous
# strips, draw cross-sections per patch. usage: assemble_ring.sh <ring> <seeds.json>
set -u; RING=$1; SEEDS=$2; REPO=$(git rev-parse --show-toplevel); cd $REPO; G=/dev/shm/$RING; mkdir -p $G
CT1=s3://vesuvius-challenge-open-data/PHerc0268/volumes/20251110183117-8.640um-1.2m-116keV-masked.zarr/1
timeout 120 git fetch -q --depth 1 --filter=blob:none origin +refs/heads/claude/gifted-bell-gavnl5-fl4t:refs/watch/fl4t
read -r UX UY RR <<<"$(python3 -c "
import json;S=[s for s in json.load(open('$SEEDS'))['seeds'] if s.get('result')=='seed'];print(S[0]['umb_x'],S[0]['umb_y'],round(sum(s['r_vox'] for s in S)/len(S)))")"
dirs=""
for i in 0 1 2 3 4 5 6 7; do d=$G/i$i; src=logs/fl4t/$RING/i$i; mkdir -p $d/tifxyz
  if [ $i = 0 ]; then [ -f $src/DONE ] || continue; cp $src/tifxyz/*.tif $d/tifxyz/; cp $src/ink9um_*.png $src/*_pieces.png $src/*_pieces.json $src/*_centre.png $d/ 2>/dev/null
  else git cat-file -e refs/watch/fl4t:$src/DONE 2>/dev/null || continue
    for f in $(git ls-tree -r --name-only refs/watch/fl4t -- $src | grep -E 'tifxyz/[xyz]\.tif$|ink9um_(forward|reverse)\.png$|_pieces\.(png|json)$|_centre\.png$'); do git show refs/watch/fl4t:$f > $d/${f#$src/}; done; fi
  [ -f $d/ink9um_forward.png ] && dirs="$dirs $d"
  [ -f $d/${RING}_i${i}_xsec.png ] || /opt/hv/bin/python tools/fl4/xsections.py $d/tifxyz $CT1 $d/${RING}_i$i $d/ink9um_forward.png >/dev/null 2>&1
done
echo "$RING patches with maps:$dirs"
for dir in forward reverse; do MAP_PATTERN="ink9um_{dir}.png" /opt/hv/bin/python tools/fl4/unroll_ring.py $dir logs/fl4t/${RING}_strip_$dir.png $UX $UY $RR $dirs | tail -1; done
mkdir -p logs/fl4t/${RING}_xsec; for d in $dirs; do cp $d/*_xsec.png $d/*_ink_bands.png $d/*_pieces.json logs/fl4t/${RING}_xsec/ 2>/dev/null; done; ls logs/fl4t/${RING}_xsec | wc -l
