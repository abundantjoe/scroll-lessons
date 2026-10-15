#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Training-only subset of docker/env/setup_env.sh (steps 2, 4 [hv-ink only], 5) for the D2 P384 trainer session.
# No docker daemon and no C++ build (training needs neither). Villa vesuvius is linked by a .pth path entry, as the
# trainer sibling did (the editable install requires Python >= 3.14; TOOLING.md used --ignore-requires-python).
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
if [ ! -x /opt/hv-ink/bin/python ]; then
  uv venv /opt/hv-ink --python 3.13 -q
fi
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python torch==2.14.0+cpu torchvision==0.29.0+cpu --index-url https://download.pytorch.org/whl/cpu
grep -v -e '^-e ' -e '^torch' "$REPO/docker/env/hv-ink-freeze.txt" > /work/logs/hv-ink-freeze-noeditable.txt
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python -r /work/logs/hv-ink-freeze-noeditable.txt --no-deps
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python pytest pygments scipy scikit-image
# train-path imports declared in villa 41701aa vesuvius/pyproject.toml (models extra); missing in the first test run
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python connected-components-3d==4.1.0 numba==0.67.0 llvmlite==0.49.0 fft-conv-pytorch==1.2.0 simpleitk==2.5.6 pandas==3.0.6
SP=$(/opt/hv-ink/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
echo /work/villa/vesuvius/src > "$SP/villa_vesuvius.pth"
/opt/hv-ink/bin/python -c 'import torch, vesuvius; print("torch", torch.__version__, "vesuvius", vesuvius.__file__)'
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
fi
echo "$CKPT_SHA  $CK" | sha256sum -c
sha256sum "$CK"
echo "setup_env_d2: OK"
