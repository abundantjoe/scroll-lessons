#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# reproduce.sh VOLUME_URL MESH_DIR : re-render MESH_DIR from VOLUME_URL with the official renderer in a fresh
# temporary directory, rebuild the image, and compare sha256 with package.json. Exit 0 only if byte-identical.
set -euo pipefail
PKG=$(cd "$(dirname "$0")" && pwd)
VOL=${1:?volume URL}; MESH=${2:?mesh dir}
case "$MESH" in /*) ;; *) MESH="$PKG/$MESH";; esac
PY=${HRC_PYTHON:-/opt/hv/bin/python}
# the renderer runs in Docker via /work/bin/vc, which mounts only /work and /home/user: stay under /work
BASE=${HRC_REPRO_BASE:-/work/repro}; mkdir -p "$BASE"
CLEAN=$(mktemp -d "$BASE/hrc_repro_XXXXXX")
cp -r "$MESH" "$CLEAN/mesh"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$PKG/tools/reproduce_check.py" --package "$PKG" --volume-url "$VOL" --mesh "$CLEAN/mesh" --workdir "$CLEAN/work"
