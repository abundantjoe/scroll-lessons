#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# Download official scrollprize weights pinned to the catalogue commit and verify sha256 against
# data/catalogue/checkpoints.json (lfs_sha256). Appends one JSON line per file to logs/sib/ckpt-screen-c/downloads.jsonl.
# Anonymous HTTPS only; no login, no token, no licence acceptance.
set -uo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
DEST=${CKSCR_CKPT:-/work/ckscr/ckpt}
LOG=$ROOT/logs/sib/ckpt-screen-c/downloads.jsonl
for spec in "$@"; do   # spec = repo_name:path
  name=${spec%%:*}; path=${spec#*:}
  read -r commit sha bytes < <(python3 - "$ROOT" "$name" "$path" <<'PY'
import json, sys
d = json.load(open(sys.argv[1] + '/data/catalogue/checkpoints.json'))
for m in d['all_scrollprize_hf_models']:
    if m['repo'] == 'scrollprize/' + sys.argv[2]:
        f = [f for f in m['files'] if f['path'] == sys.argv[3]][0]
        print(m['commit_sha'], f['lfs_sha256'], f['bytes'])
PY
)
  out=$DEST/$name/$(basename "$path"); mkdir -p "$(dirname "$out")"
  url="https://huggingface.co/scrollprize/$name/resolve/$commit/$path"
  t0=$(date -u +%Y-%m-%dT%H:%M:%SZ); ok=0
  for i in 1 2 3 4 5; do curl -fsSL --retry 3 -C - -o "$out" "$url" && ok=1 && break; sleep $((2**i)); done
  got=$(sha256sum "$out" 2>/dev/null | cut -d' ' -f1); sz=$(stat -c %s "$out" 2>/dev/null || echo 0)
  python3 - "$LOG" "$t0" "$name" "$path" "$url" "$sha" "$got" "$bytes" "$sz" "$ok" <<'PY'
import json, sys, datetime
log, t0, name, path, url, exp, got, eb, sz, ok = sys.argv[1:]
rec = dict(utc_start=t0, utc_end=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           repo='scrollprize/' + name, path=path, url=url, sha256_expected=exp, sha256=got,
           bytes_expected=int(eb), bytes=int(sz), download_ok=ok == '1', verified=(got == exp and ok == '1'))
open(log, 'a').write(json.dumps(rec) + '\n'); print(json.dumps(rec))
PY
done
