#!/bin/bash
# Build the VC3D command-line tools from the villa checkout at external/villa (HEAD, 2026-09-16) inside the
# project's own CI builder image, because the published runtime image (tag edge/main, built 2026-05-13) predates
# --flip-normals (2026-06-17) and remote normal grids (2026-07-08). Idempotent: skips when the install marker exists.
# Outputs: /home/user/hercules_data/vc_install/{bin,lib} (run the tools with scripts/vc_tools.sh, which mounts it).
set -euo pipefail
SRC=${VILLA:-${HERCULES_ROOT:-/home/user/hercules}/external/villa}/volume-cartographer
D=${HERCULES_DATA:-/home/user/hercules_data}
IMG=ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04
JOBS=${JOBS:-3}
TARGETS=${TARGETS:-"vc_render_tifxyz vc_grow_seg_from_seed vc_flatten vc_tifxyz2obj vc_obj2tifxyz vc_gen_normalgrids vc_tifxyz_trim"}
mkdir -p $D/vc_build $D/vc_install
if [ -f $D/vc_install/.complete ]; then echo "already built: $(cat $D/vc_install/.complete)"; exit 0; fi
docker run --rm --network host \
  -e HTTPS_PROXY -e https_proxy -e NO_PROXY -e no_proxy -e SSL_CERT_FILE=/ca.crt -e CURL_CA_BUNDLE=/ca.crt -e GIT_SSL_CAINFO=/ca.crt \
  -v /root/.ccr/ca-bundle.crt:/ca.crt:ro -v $SRC:/src:ro -v $D/vc_build:/build -v $D/vc_install:/install \
  $IMG bash -lc "
set -euo pipefail
cd /src
cmake -S /src -B /build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DVC_USE_PCH=ON -DVC_TESTING=OFF -DVC_BUILD_APPS=ON -DVC_BUILD_FLATBOI=ON -DVC_BUILD_PYTHON=OFF 2>&1 | tail -15
cmake --build /build -j $JOBS --target $TARGETS flatboi 2>&1 | tail -40 || cmake --build /build -j $JOBS --target $TARGETS 2>&1 | tail -40
mkdir -p /install/bin /install/lib
for t in $TARGETS flatboi; do f=\$(find /build -maxdepth 3 -type f -name \$t -perm -u+x | head -1); [ -n \"\$f\" ] && cp -v \$f /install/bin/; done
find /build -maxdepth 3 -name '*.so*' -exec cp -v {} /install/lib/ \; 2>/dev/null | tail -5 || true
ls -la /install/bin
"
git -C "${VILLA:-${HERCULES_ROOT:-/home/user/hercules}/external/villa}" rev-parse HEAD > $D/vc_install/.complete
echo "built at villa $(cat $D/vc_install/.complete)"
