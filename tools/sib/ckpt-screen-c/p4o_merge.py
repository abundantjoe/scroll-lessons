# Provenance: Project HERCULES | owner the owner | [id removed]
"""Merge sub-sibling tiles (s1-s3 branches) into logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4/tiles after
re-checking each PNG's sha256 against its json; report counts for DECL-P4-14-A3 item 2 (gate c5-c8 >= 3, title zone
c9-c19 >= 4). Prints READY when the interim manifest may be written. Never opens a tile's pixels (bytes and hashes only)."""
import hashlib
import json
import os
import subprocess

R = '/home/user/dominion'
OUT = f'{R}/logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4/tiles'


def git(*a):
    return subprocess.run(['git', '-C', R, *a], capture_output=True, check=False).stdout


os.makedirs(OUT, exist_ok=True)
merged = []
for s in ('s1', 's2', 's3'):
    ref = f'origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-c-{s}'
    git('fetch', '-q', 'origin', f'claude/gifted-bell-gavnl5-sib-ckpt-screen-c-{s}')
    names = git('ls-tree', '-r', '--name-only', ref).decode().split()
    for n in names:
        if not (n.startswith(f'logs/sib/ckpt-screen-c-{s}/PHerc.1667-iteration-4/tiles/') and n.endswith('.png.json')):
            continue
        base = os.path.basename(n)
        if os.path.exists(f'{OUT}/{base}'):
            continue
        rec = json.loads(git('show', f'{ref}:{n}'))
        png = git('show', f'{ref}:{n[:-5]}')
        if hashlib.sha256(png).hexdigest() != rec['png_sha256']:
            print('SHA MISMATCH', s, base)
            continue
        rec.setdefault('worker', s)
        rec['merged_from'] = dict(branch=ref, commit=git('rev-parse', ref).decode().strip())
        open(f'{OUT}/{base[:-5]}', 'wb').write(png)
        json.dump(rec, open(f'{OUT}/{base}', 'w'), indent=1)
        merged.append(base[:-5])
tiles = [json.load(open(f'{OUT}/{f}')) for f in os.listdir(OUT) if f.endswith('.png.json')]
gate = sorted((t['r'], t['c']) for t in tiles if 5 <= t['c'] <= 8)
title = sorted((t['r'], t['c']) for t in tiles if 9 <= t['c'] <= 19)
print(json.dumps(dict(merged=merged, n=len(tiles), gate=gate, title=title)))
if len(gate) >= 3 and len(title) >= 4:
    print('READY')
