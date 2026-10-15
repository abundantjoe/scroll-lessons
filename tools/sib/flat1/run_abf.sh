#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Run abf_uv_dump (official ABF++) inside the official deps image.
# Usage: run_abf.sh <in.tifxyz> <out_dir> [iterations] [lscm_only] [scale_to_area]
set -euo pipefail
IMG=ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f
exec docker run --rm -i --network none --cpus "${VC_CPUS:-3}" -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-3}" \
  -v /work/villa/volume-cartographer:/src:ro -v /work:/work "$IMG" /work/flat1/bin/abf_uv_dump "$@"
