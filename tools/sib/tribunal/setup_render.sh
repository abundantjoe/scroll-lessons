#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# TRIBUNAL copy of docker/env/setup_env.sh steps 1-3 only (docker, pinned villa, official CLI build); no ink venv or checkpoint.
# Rebuild the CPU tool environment in a fresh cloud container (about 10-15 min).
# Reproduces the 2026-09-24 setup recorded in docker/TOOLING.md. Idempotent.
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
  git -C /work/villa sparse-checkout set .github volume-cartographer vesuvius ink-detection
fi
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"

# 3. Official CLI apps (GCC Release, inside the deps image)
cp "$REPO/tools/sib/tribunal/vc_build_proxyenv.sh" /work/scripts/vc_build.sh
cp "$REPO/docker/env/vc_wrapper.sh" /work/bin/vc
chmod +x /work/scripts/vc_build.sh /work/bin/vc
[ -x /work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz ] || \
  bash /work/scripts/vc_build.sh > /work/logs/vc_build.log 2>&1

echo "setup_render: OK"
