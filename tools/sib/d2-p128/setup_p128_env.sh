#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Training environment for task d2-p128 (CPU). Subset of docker/env/setup_env.sh steps 2, 4 (hv-ink) and 5:
# no Docker and no C++ build (training needs neither). Villa vesuvius is added by a .pth path entry, as the trainer
# session did (the editable install is refused: vesuvius requires Python >= 3.14, the venv is 3.13).
set -euo pipefail
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mkdir -p /work/logs /work/ckpt/ink_9um/hybrid_3d2d-seed42
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
  git -C /work/villa sparse-checkout set vesuvius
fi
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"
test "$(git -C /work/villa rev-parse HEAD)" = "$VILLA_SHA"
if ! /opt/hv-ink/bin/python -c "import cc3d, numba, SimpleITK, pandas, skimage, pytest" 2>/dev/null; then
  [ -x /opt/hv-ink/bin/python ] || \
  uv venv /opt/hv-ink --python 3.13 -q
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cpu
  grep -v '^-e \|^torch\|^torchvision' "$REPO/docker/env/hv-ink-freeze.txt" > /work/logs/hv-ink-freeze-noeditable.txt
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python -r /work/logs/hv-ink-freeze-noeditable.txt --no-deps
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python scipy scikit-image lazy_loader fft-conv-pytorch SimpleITK pandas connected-components-3d numba llvmlite --no-deps
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python pytest pygments
fi
SP=$(/opt/hv-ink/bin/python -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')
echo /work/villa/vesuvius/src > "$SP/villa_vesuvius.pth"
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
fi
echo "$CKPT_SHA  $CK" | sha256sum -c
/opt/hv-ink/bin/python -c 'import torch, vesuvius.ink_detection.training.train as t; print("torch", torch.__version__, "threads", torch.get_num_threads())'
echo "setup_p128_env: OK"
