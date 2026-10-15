#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Overlay this package on a clean export of the repository HEAD (in a temp dir)
# and run the new and the existing geometry tests. Prints sha256 of every
# package file. Usage: bash run_merged_tests.sh [python]
set -euo pipefail
PKG=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$PKG" rev-parse --show-toplevel)
PY=${1:-/opt/hv/bin/python}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git -C "$REPO" archive HEAD src tests | tar -x -C "$TMP"
cp -r "$PKG/src/." "$TMP/src/"
cp -r "$PKG/tests/." "$TMP/tests/"
(cd "$PKG" && find src tests -type f -name '*.py' | sort | xargs sha256sum)
cd "$TMP"
PYTHONPATH=src "$PY" -m pytest -q -p no:cacheprovider tests/test_geometry_handed_rule.py \
  tests/test_geometry_handedness.py tests/test_geometry_level.py tests/test_pipeline_centre.py tests/test_pipeline_window.py
