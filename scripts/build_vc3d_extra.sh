#!/bin/bash
# Build the VC3D apps scripts/build_vc3d.sh left out, into the SAME install tree, then delete the build tree.
# RULES ("The team ships the measurements I have been hand-rolling"): vc_tifxyz_selfcross is the team's own
# detector for a surface that folds back onto itself -- the wrap-crossing failure R-INTERIOR diagnosed --
# vc_tifxyz_winding gives the per-node winding number, and vc_grow_seg_from_segments is the second growth stage.
# Disk is the binding constraint on this box: the build tree is removed as soon as the binaries are copied out,
# and the build refuses to start below MIN_FREE_GB.
set -euo pipefail
SRC=${VILLA:-${HERCULES_ROOT:-/home/user/hercules}/external/villa}/volume-cartographer
D=${HERCULES_DATA:-/home/user/hercules_data}
IMG=ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04
JOBS=${JOBS:-2}
MIN_FREE_GB=${MIN_FREE_GB:-5}
TARGETS=${TARGETS:-"vc_tifxyz_selfcross vc_tifxyz_winding vc_grow_seg_from_segments"}
free_gb() { df -B1G --output=avail / | tail -1 | tr -d ' '; }
[ "$(free_gb)" -ge "$MIN_FREE_GB" ] || { echo "build_vc3d_extra: only $(free_gb) GB free, need $MIN_FREE_GB" >&2; exit 1; }
B=$D/vc_build_extra
mkdir -p "$B" "$D/vc_install/bin" "$D/vc_install/lib"
cleanup() { echo "[build_extra $(date -u +%FT%TZ)] removing build tree"; rm -rf "$B"; }
trap cleanup EXIT
nice -n 19 docker run --rm --network host \
  -e HTTPS_PROXY -e https_proxy -e NO_PROXY -e no_proxy -e SSL_CERT_FILE=/ca.crt -e CURL_CA_BUNDLE=/ca.crt -e GIT_SSL_CAINFO=/ca.crt \
  -v /root/.ccr/ca-bundle.crt:/ca.crt:ro -v $SRC:/src:ro -v "$B:/build" -v $D/vc_install:/install \
  $IMG bash -lc "
set -euo pipefail
cmake -S /src -B /build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ \
      -DVC_USE_PCH=ON -DVC_TESTING=OFF -DVC_BUILD_APPS=ON -DVC_BUILD_FLATBOI=OFF -DVC_BUILD_PYTHON=OFF 2>&1 | tail -8
nice -n 19 cmake --build /build -j $JOBS --target $TARGETS 2>&1 | tail -25
for t in $TARGETS; do f=\$(find /build -maxdepth 3 -type f -name \$t -perm -u+x | head -1); [ -n \"\$f\" ] && cp -v \$f /install/bin/; done
find /build -maxdepth 3 -name '*.so*' -newer /install/bin -exec cp -v {} /install/lib/ \; 2>/dev/null | tail -3 || true
ls -la /install/bin
"
echo "[build_extra $(date -u +%FT%TZ)] done; free $(free_gb) GB"
