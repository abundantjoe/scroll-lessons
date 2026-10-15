#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Phase-1 smoke of every render-input checkpoint on the synthetic render (no CT data), 4 threads, primary windows;
# plus a determinism repeat and a precision comparison (villa CPU autocast) on GP; then numbers-only checks.
set -uo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); T=$ROOT/tools/sib/ckpt-screen-c
PY=/opt/hv-ink/bin/python; S=/work/ckscr/smoke/smoke384.npy; O=/work/ckscr/smoke/out; C=/work/ckscr/ckpt
run() { "$T/runlog.sh" "$1" "$PY" "$T/screen_infer.py" --render "$S" --threads 4 "${@:2}"; }
JULY="$C/timesformer_scroll5_july_retreat/timesformer_scroll5_july_retreat_20241113070770_frepoch=9.ckpt"
GP=$C/timesformer_GP_scroll1/model.safetensors
run smoke_july_fp32 --ckpt timesformer_scroll5_july_retreat --weights "$JULY" --out $O/july_fp32.tif
run smoke_gp_fp32 --ckpt timesformer_GP_scroll1 --weights $GP --out $O/gp_fp32.tif
run smoke_large_fp32 --ckpt timesformer_large_scroll1_01122024 --weights $C/timesformer_large_scroll1_01122024/model.safetensors --out $O/large_fp32.tif
run smoke_resnet_fp32 --ckpt resnet50_7.9um_scroll1_frags --weights $C/resnet50_7.9um_scroll1_frags/model.safetensors --out $O/resnet_fp32.tif
run smoke_gp_fp32_repeat --ckpt timesformer_GP_scroll1 --weights $GP --out $O/gp_fp32_repeat.tif
run smoke_gp_official --ckpt timesformer_GP_scroll1 --weights $GP --out $O/gp_official.tif --precision official
"$T/runlog.sh" smoke_check "$PY" "$T/smoke_check.py" "$S" "$O"
echo SMOKE_ALL_DONE
