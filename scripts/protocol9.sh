#!/bin/bash
# MASTER_PROMPT_v4 protocol 9, the automatable parts, ready before a candidate exists so none of it is written under
# time pressure. It does NOTHING that alters a map: no enhancement, no threshold, no resample. Steps 2, 3 and 6 are
# human judgement and are printed as a checklist, not performed.
#   protocol9.sh <scroll> <vol> <um> <patch_dir>
# With P9_DRY=1 it runs nothing: it prints every command it would run and checks every input it depends on exists.
# That mode is there because three separate path bugs were found in this project's scripts on the night of
# 2026-09-19 alone, and protocol 9 is the one script that must not be debugged while a candidate is on the table.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
[ $# -eq 4 ] || { echo "usage: protocol9.sh <scroll> <vol> <um> <patch_dir>" >&2; exit 2; }
sc=$1; vol=$2; um=$3; patch=$4; name=$(basename "$patch")
# Step 6 re-reads the candidate where it actually lives. It used to look in $D/patches/$sc, which is wrong for any
# candidate in a _cons_*, _small or _dense directory -- i.e. for every surface the concentrated campaign produces.
home=$(cd "$(dirname "$patch")" && pwd)
DRY=${P9_DRY:-0}
run() { if [ "$DRY" = 1 ]; then echo "    WOULD RUN: $*"; else "$@"; fi; }
need() { if [ -e "$1" ]; then echo "    ok   $1"; else echo "    MISSING $1"; MISS=$((MISS+1)); fi; }
MISS=0
echo "=== protocol 9 for $sc/$name ===  (patch dir $home, dry-run=$DRY)"
if [ "$DRY" = 1 ]; then
  echo "--- input check"
  for f in x y z; do need "$patch/$f.tif"; done
  need "$R/scripts/vc_tools.sh"; need "$R/scripts/mesh_distortion.py"; need "$R/scripts/rcross.sh"
  need "$R/scripts/run_patch_dir.py"; need "$R/scripts/package_submission.py"; need "$R/scripts/verify_package.py"
  need "$D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
  need "$D/models/ink_9um/hybrid_3d2d-seed43/step-075000.pth"
  need "$R/review_sheets/reference/REFERENCE_w040_known_text_4cm2_9.362um.png"
  need "$R/review_sheets/reference/CONTROL_w040_rule55_PROMISING_CANDIDATE_cluster.png"
  need "$D/vc_install/bin/vc_tifxyz_selfcross"
fi

echo "--- step 4a: flatten the mesh (5.13)"
flat=$D/flat_p9/${sc}__${name}
run bash $R/scripts/vc_tools.sh flatten "$patch" "$flat" 2>&1 | tail -2

echo "--- step 4b: geometry of the flattened mesh at a MATCHED baseline (G-GP: vc_flatten changes node density)"
run $R/.venv/bin/python $R/scripts/mesh_distortion.py "$patch" "$flat" --um "$um" --baseline-um 187.2 \
  --label "protocol 9 step 4: before and after flattening" 2>&1 | tail -4

echo "--- step 4c: self-intersection census of both (R-CROSS; a contact is a physical impossibility)"
run bash $R/scripts/rcross.sh p9_${name} "$patch" "$flat" 2>&1 | tail -2

echo "--- step 4d: re-render and re-read the FLATTENED mesh; the letters must persist or the candidate is NOT ESTABLISHED"
run mkdir -p $D/patches/${sc}_p9
run cp -r "$flat" $D/patches/${sc}_p9/${name}_flat
run env HERCULES_INFER_LOCK=$D/logs/infer_p9.lock $R/.venv/bin/python $R/scripts/run_patch_dir.py $D/patches/${sc}_p9 \
  --scroll "$sc" --vol "$vol" --ckpt $D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth \
  --tag ink9um_seed42+tta+flat --only "${name}_flat" --reread \
  --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null 2>&1 | tail -6

echo "--- step 6 confirmatory reader: seed43 (G-B-43 admitted it as a FILTER; it never flags and never un-flags)"
run env HERCULES_INFER_LOCK=$D/logs/infer_p9.lock $R/.venv/bin/python $R/scripts/run_patch_dir.py "$home" \
  --scroll "$sc" --vol "$vol" --ckpt $D/models/ink_9um/hybrid_3d2d-seed43/step-075000.pth \
  --tag ink9um_seed43+tta --only "$name" --reread \
  --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null 2>&1 | tail -6

cat <<'NOTE'
--- the steps this script does NOT do, because they are judgement, not automation:
  2. Look at the UNALTERED forward map beside review_sheets/reference/REFERENCE_w040_known_text_4cm2_9.362um.png
     at matched scale. List every letter-like mark with position, height and width in px and mm and the proposed
     Greek letter. Count ONLY marks 2-4 mm tall sitting in rows. Fewer than 10 inside any 4.00 cm2 window means the
     scroll is NOT submittable yet: extend the region and re-read. Never lower the count, never resample the map.
  3. Choose the 4.00 cm2 window (side = round(20000/um) px) containing the most listed letters.
  5. package_submission.py with letters.json, heldout.md, method.md, then verify_package.py -- EVERY check must PASS.
  6. Only then message the owner with "$50,000 SUBMISSION READY: ...".
  8. Stop conditions: fewer than 10 letters in one window; letters visible only after an alteration; the reverse order
     showing the same marks at the same strength; marks coinciding with tears, hole rims or fibre bands in the CT
     (the model's known false-positive mode on real papyrus is an EDGE response at voids and cracks); the flattened
     render losing the letters; the team not confirming legibility.
NOTE
if [ "$DRY" = 1 ]; then
  echo
  if [ "$MISS" -eq 0 ]; then echo "protocol 9 dry run: every input present, every command printed."
  else echo "protocol 9 dry run: $MISS MISSING INPUT(S) -- fix them before a candidate exists."; exit 1; fi
fi
