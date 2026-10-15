#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# dev-distft copy of docker/env/setup_env.sh, trimmed to what training needs:
# no docker daemon and no vc_render_tifxyz build (this session renders nothing; pairs are pre-built).
# villa sparse source (vesuvius), /opt/hv-ink torch CPU env, base checkpoint (sha256-verified). Idempotent.
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
if [ ! -x /opt/hv-ink/bin/python ]; then
  uv venv /opt/hv-ink --python 3.13 -q
fi
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python torch==2.14.0+cpu torchvision==0.29.0+cpu --index-url https://download.pytorch.org/whl/cpu
grep -v '^-e ' "$REPO/docker/env/hv-ink-freeze.txt" | grep -v '^torch' > /work/logs/freeze_noe.txt
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python -r /work/logs/freeze_noe.txt --no-deps || true
VIRTUAL_ENV=/opt/hv-ink uv pip install -q --python /opt/hv-ink/bin/python scipy scikit-image pytest pygments connected-components-3d numba fft_conv_pytorch SimpleITK pandas || true
SP=$(/opt/hv-ink/bin/python -c 'import site;print(site.getsitepackages()[0])')
echo /work/villa/vesuvius/src > "$SP/villa_vesuvius.pth"
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
fi
echo "$CKPT_SHA  $CK" | sha256sum -c
echo "setup_env: OK"
