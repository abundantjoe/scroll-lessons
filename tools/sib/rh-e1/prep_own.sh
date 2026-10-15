#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# rh-e1 P4-OWN G1 batch builder (DECL-P4-23 item 6(b), DECL-P4-23-A1, DECL-REMOTE-HARNESS-1).
# Uses ONLY the orchestrator tools tools/p4/norm_manifest.py and tools/p4/p4_jobs.py (plus own_split.py, which
# splits the manifest per segment into a local, never-pushed commit). Numbers only; never opens an image.
#
# usage: prep_own.sh <own_ref> <fold> <ARM> [<prefix>]
#   fold = f1|f2|f3, ARM = F1|F2|F3, prefix = own (default; a scratch prefix only for dry runs)
# batches: census keys <P>_<fold>a (w028-037) and <P>_<fold>b (w010-027); N0 n_<P>_<fold> = ceil(n/8) drawn from both;
#          jobs census_<P>_<fold> (sigma2t) and census_<P>_<fold>k (block) over the SAME keys; 8+1 sessions.
# default eligibility (valid_fraction >= 0.5), no --coverage.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
REF=$1; FOLD=$2; ARM=$3; P=${4:-own}
A="${P}_${FOLD}a"; B="${P}_${FOLD}b"; N="n_${P}_${FOLD}"; J="census_${P}_${FOLD}"; JK="census_${P}_${FOLD}k"
W=/work/p4/src_${P}_${FOLD}; mkdir -p "$W"
python3 tools/sib/rh-e1/own_split.py "$REF" "$FOLD" "$ARM" "$W/split.json"
SPLIT=$(python3 -c "import json;print(json.load(open('$W/split.json'))['split_commit'])")
TD=$(python3 -c "import json;print(json.load(open('$W/split.json'))['tiles_dir'])")
declare -A SEGB=([w028-037]="$A" [w010-027]="$B")
N_TOTAL=0; USED=()
for SEG in $(python3 -c "import json;print(' '.join(json.load(open('$W/split.json'))['segments']))"); do
  SHORT=${SEG##*-w}; SHORT=w${SHORT}; BATCH=${SEGB[$SHORT]}
  MP=$(python3 -c "import json;print(json.load(open('$W/split.json'))['segments']['$SEG']['path'])")
  python3 tools/p4/norm_manifest.py "$SPLIT" "$MP" "$TD" "$W/$BATCH"
  NB=$(python3 -c "import json;print(len(json.load(open('$W/$BATCH/manifest_norm.json'))['tiles']))")
  if [ "$NB" -gt 0 ]; then
    python3 tools/p4/p4_jobs.py import "$SEG" "$W/$BATCH/tiles" "$W/$BATCH/manifest_norm.json" "$BATCH"
    USED+=("$BATCH"); N_TOTAL=$((N_TOTAL+NB))
  fi
done
POOL=$(IFS=,; echo "${USED[*]}")
NN=$(( (N_TOTAL + 7) / 8 ))
python3 tools/p4/p4_jobs.py null "$N" "$NN" "$POOL"
python3 tools/p4/p4_jobs.py jobs "$J" "$POOL" "$N" sigma2t
python3 tools/p4/p4_jobs.py jobs "$JK" "$POOL" "$N" block
echo "{\"census_batches\": \"$POOL\", \"n_census\": $N_TOTAL, \"null\": \"$N\", \"n_null\": $NN, \"jobs\": [\"$J\", \"$JK\"], \"split\": \"$W/split.json\"}"
