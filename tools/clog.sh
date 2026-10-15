#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Append a CHANGELOG line stamped with `date -u` (never typed). Usage: tools/clog.sh "text"
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
printf -- '- %s %s\n' "$(date -u +%H:%MZ)" "$*" >> CHANGELOG.md
