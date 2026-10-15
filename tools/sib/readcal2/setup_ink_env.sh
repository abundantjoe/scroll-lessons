#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Minimal CPU inference env for the noise-spectrum step (official infer only; no docker, no VC build):
# villa @ 41701aa sparse (vesuvius only), /opt/hv-ink (py3.13, torch cpu), frozen deps, base checkpoint sha256-verified.
set -euo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
mkdir -p /work/ckpt/ink_9um/hybrid_3d2d-seed42
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
  git -C /work/villa sparse-checkout set vesuvius
fi
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"
git -C /work/villa rev-parse HEAD
if [ ! -x /opt/hv-ink/bin/python ]; then
  uv venv /opt/hv-ink --python 3.13 -q
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cpu \
   || VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
fi
SP=$(/opt/hv-ink/bin/python -c 'import site;print(site.getsitepackages()[0])')
echo /work/villa/vesuvius/src > "$SP/hrc_villa_vesuvius.pth"
grep -v -E "^-e |^vesuvius|^torch|^torchvision" "$REPO/docker/env/hv-ink-freeze.txt" > /work/rc2/hv-ink-freeze-nov.txt
VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r /work/rc2/hv-ink-freeze-nov.txt --no-deps
/opt/hv-ink/bin/python -c "import torch, vesuvius.ink_detection.inference.infer as m; print('torch', torch.__version__, 'infer', m.__file__)"
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
fi
echo "$CKPT_SHA  $CK" | sha256sum -c
echo setup_ink_env: OK
