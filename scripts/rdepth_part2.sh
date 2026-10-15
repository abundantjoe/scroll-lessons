#!/bin/bash
# RULES R-DEPTH part 2 (owed by the ADMITTED verdict of 2026-09-19 03:45 UTC).
# The set was fixed in the declaration BEFORE any window was run, and this script does not choose it:
#   (a) the two flagged-unit surfaces, then (b) every read with onsheet_ct_std >= 35, in ledger order.
# gates/rdepth/part2_set.json is that set, written by enumerating read_stats.json; the order in the file IS the
# declared order. Each surface is read at BOTH off-centre windows under ledger keys |+5| and |-6|. Rule 5.5 is
# untouched: a unit flagged at a nonzero offset is a flagged unit exactly as at 0.
#
# HIGH runs before LOW for every surface because HIGH is the window that was admitted (margin gain +0.13786);
# that is an order within the declared set, not a change to it, and both are run.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
CKPT=$D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth
LIMIT=${RDEPTH_LIMIT:-0}          # 0 = the whole set
echo "[rdepth2 $(date -u +%FT%TZ)] start; set = $D/gates/rdepth/part2_set.json"
n=0
while IFS=$'\t' read -r scroll surf vol dir; do
  [ -f $D/gates/rdepth/part2_paused ] && { echo "[rdepth2 $(date -u +%FT%TZ)] paused by marker"; break; }
  for w in high low; do
    tag=ink9um_seed42+plain
    dt=$tag+d$([ "$w" = high ] && echo p5 || echo m6)
    rd="$dir/read_${dt//+/_}"
    [ -f "$rd/.read_complete" ] && { echo "[rdepth2] $scroll/$surf $w already read"; continue; }
    echo "[rdepth2 $(date -u +%FT%TZ)] $scroll/$surf window $w"
    HERCULES_INFER_LOCK=$D/logs/infer_prod.lock nice -n 12 $R/.venv/bin/python $R/scripts/run_patch_dir.py \
      "$(dirname "$dir")" --scroll "${scroll%%_*}" --vol "$vol" --ckpt "$CKPT" \
      --tag "$tag" --no-tta --reread --depth-window "$w" --only "$surf" \
      --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null 2>&1 | tail -3
  done
  n=$((n+1)); [ "$LIMIT" -gt 0 ] && [ "$n" -ge "$LIMIT" ] && { echo "[rdepth2] limit $LIMIT reached"; break; }
done < <(HERCULES_SUPERVISOR=$R/scripts/supervisor.sh $R/.venv/bin/python - <<'PY'
import json, os
D = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")
# NEVER hardcode a volume id here. A guessed id cost a wrong read once already (PHerc1203) and was about to cost
# another (PHerc0358: the guess 20250809160000 is not a volume; the real one is 20250821151737). The supervisor's
# COVERAGE string is the single authority, so it is parsed, and a scroll missing from it is skipped loudly.
import re
SUP = os.environ["HERCULES_SUPERVISOR"]
cov = re.search(r'COVERAGE=\$\{COVERAGE:-"([^"]*)"\}', open(SUP).read()).group(1)
VOL = {p.split(":")[0]: p.split(":")[1] for p in cov.split()}
for r in json.load(open(os.path.join(D, "gates", "rdepth", "part2_set.json"))):
    sc = r["scroll"].split("_")[0]          # PHerc0826_small / _src / _cons_part4 all read the same volume
    v = VOL.get(sc)
    if not v:
        print("[rdepth2] NO VOLUME ID for %s - skipped" % r["scroll"])
        continue
    print("\t".join([r["scroll"], r["surf"], v, r["dir"]]))
PY
)
echo "[rdepth2 $(date -u +%FT%TZ)] queue done ($n surfaces)"
