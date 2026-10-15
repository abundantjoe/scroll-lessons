#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Rebuild the CPU tool environment in a fresh cloud container (about 10-15 min).
# Reproduces the 2026-09-24 setup recorded in docker/TOOLING.md. Idempotent.
# census FL2 copy of docker/env/setup_env.sh at origin/claude/gifted-bell-gavnl5 7168f33d (freeze-file and vesuvius fixes),
# plus: sparse checkout always includes vesuvius; vc_build copy takes the proxy from $HTTPS_PROXY. Environment only.
set -euo pipefail
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
DEPS_IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
CKPT_SHA=e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
PROXY=${HTTPS_PROXY:-http://127.0.0.1:46883}
mkdir -p /work/logs /work/bin /work/scripts /work/ckpt/ink_9um/hybrid_3d2d-seed42

# 1. Docker daemon with data under /work
if ! docker info >/dev/null 2>&1; then
  HTTPS_PROXY=$PROXY HTTP_PROXY=$PROXY nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 &
  for _ in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
fi
docker image inspect "$DEPS_IMG" >/dev/null 2>&1 || docker pull "$DEPS_IMG"

# 2. Villa source pinned to VILLA_SHA (sparse)
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
fi
git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"

# 3. Official CLI apps (GCC Release, inside the deps image)
cp "$REPO/tools/sib/census/fl2/vc_build_fl2.sh" /work/scripts/vc_build.sh
cp "$REPO/docker/env/vc_wrapper.sh" /work/bin/vc
chmod +x /work/scripts/vc_build.sh /work/bin/vc
[ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || \
  bash /work/scripts/vc_build.sh > /work/logs/vc_build.log 2>&1

# 4. Python envs
[ -x /opt/hv/bin/python ] || { uv venv /opt/hv --python 3.11 -q && \
  VIRTUAL_ENV=/opt/hv uv pip install -q numpy scipy opencv-python-headless tifffile "zarr<3" numcodecs pytest jsonschema pillow pyyaml requests boto3 s3fs fsspec imagecodecs; }
VIRTUAL_ENV=/opt/hv uv pip install -q imagecodecs 2>/dev/null || true   # LZW tifs (FL tiles)
if [ ! -x /opt/hv-ink/bin/python ] || ! /opt/hv-ink/bin/python -c "import vesuvius.ink_detection.inference.infer" 2>/dev/null; then
  [ -x /opt/hv-ink/bin/python ] || 
  uv venv /opt/hv-ink --python 3.13 -q
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cpu
  # villa vesuvius 0.2.4 declares requires-python >= 3.14 and uv refuses it on 3.13: install editable with pip --ignore-requires-python
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q pip
  /opt/hv-ink/bin/python -m pip install -q --ignore-requires-python --no-deps -e /work/villa/vesuvius
  # the freeze file pins torch 2.14.0+cpu (no longer offered) and has an editable git line uv rejects: install the rest
  grep -v -E '^(torch|torchvision)==|^-e ' "$REPO/docker/env/hv-ink-freeze.txt" > /tmp/hv-ink-freeze.clean.txt
  VIRTUAL_ENV=/opt/hv-ink uv pip install -q -r /tmp/hv-ink-freeze.clean.txt --no-deps || true
fi

# 5. Base checkpoint (public HF scrollprize/ink_9um, MIT), sha256-verified
CK=/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth
if [ ! -f "$CK" ] || ! echo "$CKPT_SHA  $CK" | sha256sum -c --quiet; then
  for i in 1 2 3 4; do
    curl -fsSL -o "$CK" "https://huggingface.co/scrollprize/ink_9um/resolve/7109667e2607db1b90c37c8b09cb876ea7fe7bb1/hybrid_3d2d-seed42/step-075000.pth" && break
    sleep $((2**i))
  done
  echo "$CKPT_SHA  $CK" | sha256sum -c
fi
echo "setup_env: OK"
