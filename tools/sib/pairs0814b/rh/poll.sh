#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-O stage poller (DECL-P4-14-A3 item 2), every 5 min. o2 = ckpt-screen-b iteration-5, o3 = ckpt-screen-c
# iteration-4. Exits printing "READY <k> <stage> <branch> <manifest>" when the builder's manifest holds, beyond the
# tiles already read in earlier stages, >= 3 gate tiles (c5-c8) and >= 4 title-zone tiles (c9-c19).
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
while true; do
  out=$(python3 - <<'PY'
import glob, json, re, subprocess
def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True)
for k, x, it in ((2, 'b', 'iteration-5'), (3, 'c', 'iteration-4')):
    br = f'claude/gifted-bell-gavnl5-sib-ckpt-screen-{x}'
    if git('fetch', '-q', 'origin', br).returncode:
        print(f'o{k}: fetch failed'); continue
    mans = [m for m in git('ls-tree', '-r', '--name-only', f'origin/{br}', '--', f'logs/sib/ckpt-screen-{x}/p4o').stdout.split()
            if m.endswith('/manifest.json') and it in m]
    done = sorted(glob.glob(f'logs/sib/pairs0814b/rh/O{k}/A/o{k}s*/p4_key_o{k}s*.json'))
    seen = {(v['r'], v['c']) for f in done for v in json.load(open(f)).values()}
    st = len(done) + 1
    for m in mans:
        d = json.loads(git('show', f'origin/{br}:{m}').stdout)
        new = [t for t in d.get('tiles', []) if t.get('valid_fraction', 0) >= 0.5 and (t['r'], t['c']) not in seen]
        g = sum(5 <= t['c'] <= 8 for t in new); tz = sum(9 <= t['c'] <= 19 for t in new)
        print(f"o{k}s{st} {m} partial={d.get('partial')} n={len(d.get('tiles', []))} new={len(new)} gate={g} title={tz}")
        if g >= 3 and tz >= 4:
            print(f'READY {k} {st} {br} {m}')
PY
)
  echo "$(date -u +%T) $out"
  echo "$out" | grep -q '^READY' && exit 0
  sleep 300
done
