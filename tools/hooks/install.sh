#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
#
# Point git at the versioned hooks in tools/hooks for this clone.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
chmod +x tools/hooks/pre-commit
git config core.hooksPath tools/hooks
echo "core.hooksPath = $(git config core.hooksPath)"
