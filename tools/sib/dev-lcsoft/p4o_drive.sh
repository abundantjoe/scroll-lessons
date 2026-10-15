#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-O iteration driver (dev-lcsoft): one builder call per tile (resumable: done tiles are skipped by the builder),
# then finalize manifest, commit and push only logs/sib/dev-lcsoft/p4o/<ckpt>/ after every tile.
set -u
IT=$1; shift
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); cd "$REPO"
OUT=logs/sib/dev-lcsoft/p4o/PHerc.1667-iteration-$IT
export PYTHONPATH=/work/lcsoft/pylib_tf:/work/lcsoft/pylib_cv:/work/lcsoft/pylib:$REPO/src OMP_NUM_THREADS=4 P4O_WORK=/work/p4o_lcsoft
PY=/opt/hv-ink/bin/python
for T in "$@"; do
  r=${T%,*}; c=${T#*,}
  [ -f "$OUT/tiles/20260701183124-w010-027_r${r}_c${c}.png.json" ] && continue
  tools/sib/dev-lcsoft/run.sh "p4o_it${IT}_r${r}_c${c}" "$PY tools/sib/dev-lcsoft/p4o_tiles.py --iteration $IT --tiles '$T' --out $OUT --threads 4"
  # The pinned builder (ca732ae) exits 1 AFTER writing the tile: its log() passes 'utc' twice to dict().
  # Success = tile json and png written; the png sha256 is re-verified by finalize.
  [ -f "$OUT/tiles/20260701183124-w010-027_r${r}_c${c}.png.json" ] && [ -f "$OUT/tiles/20260701183124-w010-027_r${r}_c${c}.png" ] || { echo "tile $T not written; stopping"; exit 1; }
  $PY tools/sib/dev-lcsoft/p4o_finalize_mine.py $IT $OUT
  git add "$OUT" logs/sib/dev-lcsoft/runs.jsonl logs/sib/dev-lcsoft/out/p4o_it${IT}_r${r}_c${c}.log
  git commit -q -m "sib dev-lcsoft: P4-O iteration-$IT tile r${r} c${c}

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WN6ghNprnvpMBng1esTcHT" || true
  for k in 1 2 3 4; do git push -q origin claude/gifted-bell-gavnl5-sib-dev-lcsoft && break; sleep $((2**k)); done
done
echo DRIVE_DONE
