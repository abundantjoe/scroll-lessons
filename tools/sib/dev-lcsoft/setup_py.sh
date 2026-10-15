#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Python-only subset of docker/env/setup_env.sh (steps 2, 4 hv-ink, 5) for task dev-lcsoft phase 1.
# No Docker / VC build: phase 1 needs only the model, the official loss and the checkpoint.
set -euo pipefail
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mkdir -p /work/logs /work/ckpt/ink_9um/hybrid_3d2d-seed42
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
  git -C /work/villa sparse-checkout set vesuvius ink-detection
fi
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"
echo "villa HEAD $(git -C /work/villa rev-parse HEAD)"
if ! /opt/hv-ink/bin/python -c "import vesuvius" 2>/dev/null; then
  [ -x /opt/hv-ink/bin/python ] || \
  uv venv /opt/hv-ink --python 3.13 -q
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q pip
  /opt/hv-ink/bin/python -m pip install -q -e /work/villa/vesuvius --no-deps --ignore-requires-python
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r "$REPO/docker/env/hv-ink-freeze.txt" --no-deps || true
fi
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
fi
echo "ckpt sha256 $(sha256sum "$CK" | cut -d' ' -f1)"
echo "$CKPT_SHA  $CK" | sha256sum -c
echo "setup_py: OK"
# 6. Side libraries the official training modules import (same set and versions as the amx sibling's /work/amx/pylib,
#    logs/sib/amx/out/boot_pylib.log), installed into /work/lcsoft/pylib; use PYTHONPATH=/work/lcsoft/pylib.
if ! PYTHONPATH=/work/lcsoft/pylib /opt/hv-ink/bin/python -c "import cc3d, skimage, SimpleITK, numba, pandas, fft_conv_pytorch" 2>/dev/null; then
  /opt/hv-ink/bin/python -m pip install -q --target /work/lcsoft/pylib connected-components-3d==4.1.0 fft-conv-pytorch==1.2.0 \
    lazy-loader==0.6 llvmlite==0.49.0 numba==0.67.0 pandas==3.0.6 scikit-image==0.26.0 scipy==1.18.1 simpleitk==2.5.6 --no-deps
fi
PYTHONPATH=/work/lcsoft/pylib /opt/hv-ink/bin/python -c "import cc3d; print('pylib OK')"
