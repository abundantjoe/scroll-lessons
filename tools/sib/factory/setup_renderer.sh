#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Build ONLY the official vc_render_tifxyz (villa 41701aa, GCC Release) inside the official CI deps
# image, as in docker/env/setup_env.sh + vc_build.sh, but taking the proxy port from $HTTPS_PROXY
# (the port in vc_build.sh is stale after a container restart). Idempotent. Writes under /work only.
set -euo pipefail
VILLA_SHA=41701aa0eaa1aa765523db3f9f972b5830abf549
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
P=${HTTPS_PROXY:?HTTPS_PROXY must be set}
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
mkdir -p /work/logs /work/bin
if ! docker info >/dev/null 2>&1; then
  HTTPS_PROXY=$P HTTP_PROXY=$P nohup dockerd --data-root /work/docker > /work/logs/dockerd.log 2>&1 &
  for _ in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
fi
docker image inspect "$IMG" >/dev/null 2>&1 || docker pull "$IMG"
if [ ! -d /work/villa/.git ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa /work/villa
  git -C /work/villa sparse-checkout set .github volume-cartographer
fi
git -C /work/villa fetch --depth 1 origin "$VILLA_SHA" || true
git -C /work/villa checkout -q "$VILLA_SHA"
test "$(git -C /work/villa rev-parse HEAD)" = "$VILLA_SHA"
cp "$REPO/docker/env/vc_wrapper.sh" /work/bin/vc && chmod +x /work/bin/vc
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz
if [ ! -x "$BIN" ]; then
  DATE=$(git -C /work/villa log -1 --format=%cs HEAD)
  docker run --rm --network host --cpus 3 -v /work/villa/volume-cartographer:/src \
    -v /root/.ccr/ca-bundle.crt:/ccr/ca-bundle.crt:ro -w /src \
    -e HTTPS_PROXY="$P" -e https_proxy="$P" -e NO_PROXY=localhost,127.0.0.1 -e no_proxy=localhost,127.0.0.1 \
    -e SSL_CERT_FILE=/ccr/ca-bundle.crt -e GIT_SSL_CAINFO=/ccr/ca-bundle.crt -e CURL_CA_BUNDLE=/ccr/ca-bundle.crt \
    "$IMG" bash -c "set -euo pipefail
      cmake -S /src -B /src/build/hrc-release-gcc -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc \
        -DCMAKE_CXX_COMPILER=g++ -DCMAKE_TLS_CAINFO=/ccr/ca-bundle.crt -DVC_TESTING=OFF -DVC_BUILD_APPS=ON \
        -DVC_BUILD_FLATBOI=OFF -DVC_USE_PCH=ON -DVC_GIT_SHA1=$VILLA_SHA -DVC_GIT_COMMIT_DATE=$DATE
      cmake --build /src/build/hrc-release-gcc --parallel 3 --target vc_render_tifxyz"
fi
/work/bin/vc vc_render_tifxyz --help > /work/logs/vc_render_help.txt 2>&1 || true
sha256sum "$BIN"
echo "setup_renderer: OK"
