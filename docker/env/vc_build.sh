#!/usr/bin/env bash
# Project HERCULES: build selected volume-cartographer CLI apps (no GUI target) inside the
# official CI deps image ghcr.io/scrollprize/vc3d-deps/linux (the image vc3d-ci.yml uses).
# GCC Release (GCC links real OpenMP; the Clang build uses a serial OpenMP shim).
set -euo pipefail
P="${HTTPS_PROXY:-http://127.0.0.1:46883}"   # this container's agent proxy (the port differs per session)
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
SRC=/work/villa/volume-cartographer
SHA=$(git -C /work/villa rev-parse HEAD)
DATE=$(git -C /work/villa log -1 --format=%cs HEAD)
TARGETS="vc_render_tifxyz vc_grow_seg_from_seed vc_grow_seg_from_segments vc_tifxyz_selfcross vc_calc_surface_metrics vc_flatten vc_gen_normalgrids"
echo "[$(date -Is)] start build SHA=$SHA image=$IMG targets=$TARGETS"
docker run --rm --name hrc-vc-build --network host --cpus 3 \
  -v "$SRC:/src" -v /root/.ccr/ca-bundle.crt:/ccr/ca-bundle.crt:ro -w /src \
  -e HTTPS_PROXY=$P -e https_proxy=$P \
  -e NO_PROXY=localhost,127.0.0.1 -e no_proxy=localhost,127.0.0.1 \
  -e SSL_CERT_FILE=/ccr/ca-bundle.crt -e GIT_SSL_CAINFO=/ccr/ca-bundle.crt -e CURL_CA_BUNDLE=/ccr/ca-bundle.crt \
  "$IMG" bash -c "
    set -euo pipefail
    time cmake -S /src -B /src/build/hrc-release-gcc -G Ninja \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ \
      -DCMAKE_TLS_CAINFO=/ccr/ca-bundle.crt \
      -DVC_TESTING=OFF -DVC_BUILD_APPS=ON -DVC_BUILD_FLATBOI=OFF -DVC_USE_PCH=ON \
      -DVC_GIT_SHA1=$SHA -DVC_GIT_COMMIT_DATE=$DATE
    time cmake --build /src/build/hrc-release-gcc --parallel 3 --target $TARGETS
    ls -la /src/build/hrc-release-gcc/bin/
  "
echo "[$(date -Is)] build finished rc=$?"
