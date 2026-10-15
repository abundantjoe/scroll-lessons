#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Build abf_uv_dump against the official libvc_flattening/libvc_core built by
# docker/env/vc_build.sh, inside the same official deps image, with the
# compile flags of vc_flatten.cpp (compile_commands.json), minus PCH and LTO.
set -euo pipefail
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
SRC=/work/villa/volume-cartographer
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p /work/flat1/bin
cp "$HERE/abf_uv_dump.cpp" /work/flat1/bin/abf_uv_dump.cpp
docker run --rm --network none -v "$SRC:/src" -v /work/flat1/bin:/out -w /src/build/hrc-release-gcc "$IMG" bash -c '
set -euo pipefail
B=/src/build/hrc-release-gcc
g++ -DUTILS_HAS_C3D_CODEC=1 -DUTILS_HAS_CURL=1 -I/src/core/include -I/src/libs/OpenABF/include -I/src/utils/include \
  -I/src/libs/c3d -I$B/_deps/vc_delta3d-src/include -isystem /usr/include/opencv4 -isystem /usr/include/eigen3 \
  -O2 -DNDEBUG -std=gnu++23 -march=x86-64-v3 -fopenmp -Wno-psabi -Wno-ignored-attributes \
  /out/abf_uv_dump.cpp -o /out/abf_uv_dump \
  -Wl,-rpath,$B/core:$B/utils:$B/libs/c3d \
  $B/core/libvc_flattening.so $B/core/libvc_core.so $B/utils/libutils.so $B/utils/libutils_c3d_codec.so $B/libs/c3d/libc3d.so \
  -lopencv_imgcodecs -lopencv_imgproc -lopencv_core -ltiff
ls -la /out/abf_uv_dump'
sha256sum /work/flat1/bin/abf_uv_dump
