#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# pairs0814b: copy the unchanged pairs0814 code's outputs byte for byte into this branch's paths and push them.
# Block npz files are committed in batches of <= 500 MB (each file < 90 MB, else refused and recorded).
set -u
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SEGS="20250928235953 20250926051122"
L=logs/sib/pairs0814b; D=data/sib/pairs0814b/blockpairs
mkdir -p $L/stage_a $L/registry $D
for s in $SEGS; do
  [ -f logs/sib/pairs0814/stage_a/$s.json ] && cp logs/sib/pairs0814/stage_a/$s.json $L/stage_a/
  [ -f logs/sib/pairs0814/registry/$s.jsonl ] && cp logs/sib/pairs0814/registry/$s.jsonl $L/registry/
  [ -f /work/sib/blocks/$s/SEGMENT_DONE.json ] && cp /work/sib/blocks/$s/SEGMENT_DONE.json $L/registry/$s.SEGMENT_DONE.json
done
cp logs/sib/pairs0814/runs.jsonl $L/runs.jsonl
commit() {
  git commit -q -F - <<MSG
sib pairs0814b: $1

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NfS4bhpLVnt2ShveEY6pYF
MSG
  for i in 1 2 3 4 5; do git push -q -u origin claude/gifted-bell-gavnl5-sib-pairs0814b && return 0; sleep $((2**i)); done
  echo "PUSH FAILED $(date -u +%FT%TZ)" >> $L/push_refusals.log; return 1
}
batch=0
for s in $SEGS; do
  mkdir -p $D/$s
  for f in /work/sib/blockpairs/$s/*.npz; do
    [ -e "$f" ] || continue
    case "$f" in *.tmp.npz) continue;; esac
    b=$(basename "$f"); [ -f $D/$s/$b ] && continue
    sz=$(stat -c %s "$f")
    if [ "$sz" -ge 94371840 ]; then echo "$s/$b $sz bytes >= 90 MB, not committed" >> $L/oversize.log; continue; fi
    cp "$f" $D/$s/$b; git add $D/$s/$b; batch=$((batch + sz))
    if [ $batch -ge 450000000 ]; then commit "block npz batch ($batch bytes)"; batch=0; fi
  done
  (cd $D/$s && ls *.npz >/dev/null 2>&1 && sha256sum *.npz > SHA256SUMS)
done
git add $L $D tools/sib/pairs0814b
git diff --cached --quiet || commit "registry, stage A, run log and block npz progress"
