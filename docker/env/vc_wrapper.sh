#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Project HERCULES wrapper: run a built volume-cartographer CLI app inside the official
# vc3d-deps runtime image. Usage: /work/bin/vc <app> [args...]   e.g. /work/bin/vc vc_render_tifxyz --help
# Mounts /work and /home/user read-write at the same paths so host paths work unchanged.
set -euo pipefail
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
app="$1"; shift
# Proxy port can change on container restart; take it from the session environment.
P="${HTTPS_PROXY:-http://127.0.0.1:46883}"
exec docker run --rm -i --network host --cpus "${VC_CPUS:-3}" \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-3}" \
  -e HTTPS_PROXY="$P" -e https_proxy="$P" \
  -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt -e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt \
  -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro \
  -v /work:/work -v /dev/shm:/dev/shm -v /home/user:/home/user -w "$PWD" \
  "$IMG" "$BIN/$app" "$@"
