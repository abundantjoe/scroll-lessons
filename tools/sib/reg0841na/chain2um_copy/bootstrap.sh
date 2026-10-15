#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# chain2um bootstrap: runs docker/env/setup_env.sh unchanged, except that the build-script copy
# gets the current session proxy port (vc_build.sh hardcodes an older port).
set -euo pipefail
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
P="${HTTPS_PROXY:?}"
TMP=$(mktemp -d)
cp -r "$REPO/docker/env" "$TMP/env"
sed -i "s#http://127.0.0.1:46883#$P#g" "$TMP/env/vc_build.sh"
# setup_env derives REPO from its own dir via git; run it from a copy that points REPO at the checkout
sed -i "s#^REPO=.*#REPO=$TMP/repo#" "$TMP/env/setup_env.sh"
mkdir -p "$TMP/repo/docker"; ln -s "$TMP/env" "$TMP/repo/docker/env"
PROXY=$P bash "$TMP/env/setup_env.sh"
