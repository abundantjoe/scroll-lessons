#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# DEV prep (renders, CT registration, reference) then the base-checkpoint DEV evaluation. Resumable: finished
# windows are skipped. Every step is logged in logs/sib/devloop/runs.jsonl by runlog.sh.
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
R=tools/sib/devloop/runlog.sh
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
THREADS=${THREADS:-4}
$R devloop_prep env PYTHONPATH=src OMP_NUM_THREADS=3 /opt/hv/bin/python tools/sib/devloop/evaluate.py prep
$R devloop_calib env PYTHONPATH=src /opt/hv/bin/python tools/sib/devloop/evaluate.py calib
$R devloop_eval_base env PYTHONPATH=src OMP_NUM_THREADS=$THREADS /opt/hv/bin/python tools/sib/devloop/evaluate.py eval \
   --ckpt "$CK" --tag base_step075000 --base --threads "$THREADS"
echo "run_base done $(date -u +%FT%TZ)"
