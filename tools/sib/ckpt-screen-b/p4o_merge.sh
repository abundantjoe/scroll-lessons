#!/bin/bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Merge finished sub-sibling tiles (png + png.json, sha256-verified) into the parent tiles dir; numbers only.
cd "$(git rev-parse --show-toplevel)"
CK=${1:-PHerc.1667-iteration-5}
D=logs/sib/ckpt-screen-b/p4o/$CK/tiles
mkdir -p $D
for s in 1 2 3; do
  B=origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s$s
  git fetch -q origin claude/gifted-bell-gavnl5-sib-ckpt-screen-b-s$s 2>/dev/null || continue
  for j in $(git ls-tree --name-only $B $D/ 2>/dev/null | grep '\.png\.json$'); do
    p=${j%.json}
    [ -f "$j" ] && continue
    git show $B:$j > "$j.tmp" && git show $B:$p > "$p.tmp" || { rm -f "$j.tmp" "$p.tmp"; continue; }
    want=$(python3 -c "import json;print(json.load(open('$j.tmp'))['png_sha256'])")
    got=$(sha256sum "$p.tmp" | cut -d' ' -f1)
    if [ "$want" = "$got" ]; then mv "$j.tmp" "$j"; mv "$p.tmp" "$p"; echo "merged s$s $(basename $p)"; else rm -f "$j.tmp" "$p.tmp"; echo "SHA MISMATCH s$s $(basename $p)"; fi
  done
done
ls $D/*.png.json 2>/dev/null | wc -l
