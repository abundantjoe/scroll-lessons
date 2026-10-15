#!/usr/bin/env bash
# Provenance: Project HERCULES | [id removed]
# Copy the given repo paths (as in the working tree) onto the lane branch claude/gifted-bell-gavnl5-fl4t without touching
# the local checkout: a throw-away index built from the remote tree + the files, one commit, pushed to the branch.
# usage: sync_fl4t.sh "<commit message>" <path>...
set -euo pipefail; MSG=$1; shift; BR=claude/gifted-bell-gavnl5-fl4t; cd "$(git rev-parse --show-toplevel)"
git fetch -q --depth 1 --filter=blob:none origin +refs/heads/$BR:refs/watch/fl4t
export GIT_INDEX_FILE=/dev/shm/idx_fl4t_$$; git read-tree refs/watch/fl4t
for p in "$@"; do m=100644; [ -x "$p" ] && m=100755; b=$(git hash-object -w "$p"); git update-index --add --cacheinfo $m,$b,"$p"; done
T=$(git write-tree); C=$(git commit-tree $T -p refs/watch/fl4t -m "$MSG

Provenance: Project HERCULES | [id removed]

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01JNjAnFPejnNF7eVAiNeRJp"); rm -f $GIT_INDEX_FILE; unset GIT_INDEX_FILE
for d in 2 4 8 16; do git push -q origin $C:refs/heads/$BR && { echo "synced $C to $BR"; exit 0; }; sleep $d; git fetch -q --depth 1 --filter=blob:none origin +refs/heads/$BR:refs/watch/fl4t; done; echo "sync failed"; exit 1
