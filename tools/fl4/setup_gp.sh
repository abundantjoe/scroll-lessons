#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# DECL-FL-4 / -A1: CPU environment for the Grand Prize TimeSformer (organizer copy HF scrollprize/timesformer_GP_scroll1
# @61b81d31, MIT, by Youssef Nader for the 2023 Grand Prize team) run through villa 41701aa optimized_inference.
# Idempotent. Creates /opt/gp (venv), /work/villa_gp (sparse villa at 41701aa), /work/gp/model.safetensors (sha-checked).
set -euo pipefail
GPSHA=490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488
HFREV=61b81d31ddb93c89a2b3b00c66769d18bd96ccb2; VREV=41701aa
mkdir -p /work/gp
if [ ! -x /opt/gp/bin/python ] || ! /opt/gp/bin/python -c "import torch, timesformer_pytorch, albumentations, pytorch_lightning, zarr, safetensors, cv2, tifffile, scipy, fsspec" 2>/dev/null; then
  uv venv -q --python 3.11 /opt/gp
  VIRTUAL_ENV=/opt/gp uv pip install -q --index-url https://download.pytorch.org/whl/cpu torch
  VIRTUAL_ENV=/opt/gp uv pip install -q timesformer-pytorch==0.4.1 einops albumentations pytorch-lightning "zarr>=3" numcodecs fsspec \
    safetensors tifffile opencv-python-headless scipy tqdm psutil numpy
fi
if [ ! -f /work/villa_gp/ink-detection/optimized_inference/inference.py ]; then
  rm -rf /work/villa_gp
  git clone -q --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git /work/villa_gp
  git -C /work/villa_gp sparse-checkout set ink-detection/optimized_inference
  git -C /work/villa_gp checkout -q $VREV
fi
[ "$(git -C /work/villa_gp rev-parse --short=7 HEAD)" = "$VREV" ] || { echo "villa_gp not at $VREV"; exit 1; }
if ! echo "$GPSHA  /work/gp/model.safetensors" | sha256sum -c --quiet 2>/dev/null; then
  curl -fsSL -o /work/gp/model.safetensors.part "https://huggingface.co/scrollprize/timesformer_GP_scroll1/resolve/$HFREV/model.safetensors"
  mv /work/gp/model.safetensors.part /work/gp/model.safetensors
  echo "$GPSHA  /work/gp/model.safetensors" | sha256sum -c --quiet || { echo "GP model sha256 mismatch"; exit 1; }
fi
FL_VOX_UM=8.64 /opt/gp/bin/python -c "
import sys; sys.argv=['x']; sys.path.insert(0,'$(dirname "$0")'); import gp_infer as G; m=G.model(); print('GP model strict load OK', sum(p.numel() for p in m.parameters()))"
echo GP_ENV_OK
