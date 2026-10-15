#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Merge finished PHerc.1667-iteration-5 tiles from sub-sibling (-s1..-s3) and DECL-P4-14-A3 fleet (o5w*) branches into
logs/sib/ckpt-screen-b/p4o/<ckpt>/tiles. Tiles are found under any logs/sib/*/p4o/<ckpt>/tiles/ path of a branch.
Checks: png sha256 == its record; for fleet tiles also a p4o/fleet/<worker>.json on that branch naming code commit
98cd075 with the parent builder sha256 values and the same png_sha256. Bytes are copied, never opened as images."""
import hashlib, json, os, subprocess, sys, time
CK = sys.argv[1] if len(sys.argv) > 1 else 'PHerc.1667-iteration-5'
REPO = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
P = os.path.join(REPO, 'logs/sib/ckpt-screen-b/p4o')
D = os.path.join(P, CK, 'tiles')
OK = dict(code_commit='98cd075', p4o='a32d7e86a7bdfd5a25a5ced280976a2dfa55f30c8b866a3ae149d74b729ec371',
          inf='29444f37ffb43669b1842570b123a5f791dd9d0f8aa7a4a07b8f776ed148cb12')


def git(*a, text=True):
    return subprocess.check_output(['git', '-C', REPO, *a], text=text)


def flat(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from flat(v)
    elif isinstance(o, list):
        for v in o:
            yield from flat(v)
    else:
        yield str(o)


os.makedirs(D, exist_ok=True)
heads = [l.split('refs/heads/')[1] for l in git('ls-remote', '--heads', 'origin').splitlines()]
FLEET = ('o5w', 'sib-p4-highz', 'sib-hzw')   # DECL-P4-14-A3, -A4
brs = [b for b in heads if 'ckpt-screen-b-s' in b or any(k in b for k in FLEET)]
merged = []
for br in brs:
    try:
        git('fetch', '-q', 'origin', br)
    except subprocess.CalledProcessError:
        continue
    B = f'origin/{br}'
    files = git('ls-tree', '-r', '--name-only', B, 'logs/sib').splitlines()
    fleet = {}
    for f in files:
        if '/p4o/fleet/' in f and f.endswith('.json'):
            try:
                d = json.loads(git('show', f'{B}:{f}'))
                fleet[d.get('png_sha256')] = d
            except Exception:
                pass
    for j in files:
        if not (j.endswith('.png.json') and f'/p4o/{CK}/tiles/' in j):
            continue
        name = os.path.basename(j)
        dst = os.path.join(D, name)
        if os.path.exists(dst):
            continue
        rec = json.loads(git('show', f'{B}:{j}'))
        png = subprocess.check_output(['git', '-C', REPO, 'show', f'{B}:{j[:-5]}'])
        got = hashlib.sha256(png).hexdigest()
        if got != rec['png_sha256']:
            print('SHA MISMATCH', br, name); continue
        if any(k in br for k in FLEET):
            fj = fleet.get(got)
            vals = set(flat(fj or {}))   # key names and nesting vary between workers; values must match
            if not fj or str(fj.get('code_commit', ''))[:7] != OK['code_commit'] or \
                    OK['p4o'] not in vals or OK['inf'] not in vals:
                print('SKIP (fleet record/code commit)', br, name); continue
        with open(dst[:-5], 'wb') as f:
            f.write(png)
        with open(dst, 'w') as f:
            json.dump(rec, f, indent=1)
        m = dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), branch=br,
                 commit=git('rev-parse', '--short', B).strip(), src=j, tile=name[:-5], png_sha256=got,
                 code_commit=(fleet.get(got) or {}).get('code_commit'))
        with open(os.path.join(P, 'merges.jsonl'), 'a') as f:
            f.write(json.dumps(m) + '\n')
        merged.append((br, name[:-5]))
        print('merged', br, name[:-5])
n = len([f for f in os.listdir(D) if f.endswith('.png.json')])
print('tiles', n)
