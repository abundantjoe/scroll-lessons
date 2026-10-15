#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# D3 copy of /work/bin/vc (same official vc3d-deps image, same binaries, same mounts), except that the proxy is taken
# from the current environment ($HTTPS_PROXY): /work/bin/vc hard-codes 127.0.0.1:46883, which stopped working when
# the agent proxy moved to another port after the ~10:20Z container restart (render error: "Failed to connect ...
# via 127.0.0.1 after 0 ms").
set -euo pipefail
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
BIN=/work/villa/volume-cartographer/build/hrc-release-gcc/bin
P="${HTTPS_PROXY:-http://127.0.0.1:46883}"
app="$1"; shift
exec docker run --rm -i --network host --cpus "${VC_CPUS:-3}" \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-3}" \
  -e HTTPS_PROXY="$P" -e https_proxy="$P" \
  -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt -e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt \
  -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro \
  -v /work:/work -v /home/user:/home/user -w "$PWD" \
  "$IMG" "$BIN/$app" "$@"
