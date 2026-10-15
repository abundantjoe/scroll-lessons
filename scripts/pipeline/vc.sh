#!/usr/bin/env bash
# vc.sh: run a volume-cartographer CLI app (built from ScrollPrize/villa at commit 41701aa) inside the official
# vc3d-deps runtime image. Usage: vc.sh <app> [args...]   e.g.  vc.sh vc_render_tifxyz --help
# Env: VC_BIN (directory holding the built apps, e.g. <villa>/volume-cartographer/build/<preset>/bin),
#      VC_IMAGE (default below), VC_MOUNTS (space-separated host dirs mounted at the same paths; default $PWD),
#      VC_CPUS (default 3).
set -euo pipefail
IMG=${VC_IMAGE:-ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f}
: "${VC_BIN:?set VC_BIN to the directory with the built volume-cartographer apps (docs/REPRODUCE.md)}"
app="$1"; shift
mounts=(); for d in ${VC_MOUNTS:-$PWD} "$VC_BIN"; do mounts+=(-v "$d:$d"); done
envs=(); for v in HTTPS_PROXY https_proxy SSL_CERT_FILE CURL_CA_BUNDLE; do [ -n "${!v:-}" ] && envs+=(-e "$v=${!v}"); done
[ -n "${SSL_CERT_FILE:-}" ] && mounts+=(-v "$SSL_CERT_FILE:$SSL_CERT_FILE:ro")
exec docker run --rm -i --network host --cpus "${VC_CPUS:-3}" -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-3}" \
  "${envs[@]}" "${mounts[@]}" -w "$PWD" "$IMG" "$VC_BIN/$app" "$@"
