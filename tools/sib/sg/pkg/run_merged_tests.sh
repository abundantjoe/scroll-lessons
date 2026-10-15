#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Test the staged package in its MERGED layout without writing outside tools/sib/sg:
# copy src/, tests/, configs/, tools/ and pyproject.toml to a scratch directory, overlay
# pkg/src/hercules/sg -> src/hercules/sg and pkg/tests/test_sg_*.py -> tests/, then run a
# plain pytest there (default: the whole suite). Usage: run_merged_tests.sh [pytest args]
set -euo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
PKG="$ROOT/tools/sib/sg/pkg"
W=$(mktemp -d "${TMPDIR:-/tmp}/sg_merged.XXXXXX")
trap 'rm -rf "$W"' EXIT
cp -r "$ROOT/src" "$ROOT/tests" "$ROOT/configs" "$ROOT/pyproject.toml" "$W/"
cp -r "$ROOT/tools" "$W/tools"
test ! -e "$W/src/hercules/sg" || { echo "src/hercules/sg already exists in the repo" >&2; exit 2; }
cp -r "$PKG/src/hercules/sg" "$W/src/hercules/sg"
cp "$PKG"/tests/test_sg_*.py "$W/tests/"
find "$W" -name __pycache__ -prune -exec rm -rf {} +
cd "$W"
PY=${PY:-/opt/hv/bin/python}
if [ "$#" -eq 0 ]; then set -- tests; fi
"$PY" -m pytest -q -p no:cacheprovider "$@"
