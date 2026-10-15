#!/bin/bash
# RULES G-OWN: when the PHerc0139 known-text trace finishes, run the declared chain end to end.
# Nothing here chooses anything: the admissibility gate and the bars live in gown_result.py, fixed before the trace.
set -uo pipefail
D=${HERCULES_DATA:-/home/user/hercules_data}; R=${HERCULES_ROOT:-/home/user/hercules}
P=$D/patches/PHerc0139_gown
CKPT=$D/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth
log(){ echo "[gown $(date -u +%FT%TZ)] $*"; }

# 1. wait for the tracer to exit AND a grown patch to appear
while kill -0 "$(cat $P/gown.pid 2>/dev/null)" 2>/dev/null; do sleep 60; done
patch=$(ls -d $P/auto_* 2>/dev/null | head -1)
[ -n "$patch" ] || { log "NO PATCH: the trace produced nothing; G-OWN cannot run"; exit 1; }
log "trace done -> $patch"

# 2. admissibility gate BEFORE any compute is spent on rendering
$R/.venv/bin/python $R/scripts/gown_result.py --patch "$patch" --out $D/gates/gown/gown_gate.json 2>&1 | tail -6
v=$($R/.venv/bin/python -c "import json;print(json.load(open('$D/gates/gown/gown_gate.json'))['verdict'])")
[ "$v" = "VOID-OFF-SHEET" ] && { log "VOID-OFF-SHEET: not rendered, not read, re-seed required"; exit 2; }

# 3. the corpus read chain, unchanged: QC -> render -> plain seed42 both orders -> rule 5.5
log "reading $patch through the corpus chain"
HERCULES_INFER_LOCK=$D/logs/infer_prod.lock nice -n 10 $R/.venv/bin/python $R/scripts/run_patch_dir.py "$P" \
  --scroll PHerc0139 --vol 20250728140407 --ckpt "$CKPT" --tag ink9um_seed42+plain --no-tta \
  --only "$(basename "$patch")" --ledger $R/LEDGER.md --records $R/records/throughput.jsonl </dev/null 2>&1 | tail -5

# 4. the declared verdict
rd=$(ls -d "$patch"/read_ink9um_seed42_plain 2>/dev/null | head -1)
$R/.venv/bin/python $R/scripts/gown_result.py --patch "$patch" --read "$rd" --out $D/gates/gown/gown_result.json 2>&1 | tail -12
log "G-OWN complete"
