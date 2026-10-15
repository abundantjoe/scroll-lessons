# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN G1 helper for rh-e1 (DECL-P4-23 item 6(b), DECL-P4-23-A1). Numbers and hashes only; never opens an image.

usage: own_split.py <own_ref> <fold> <arm> <out_json> [<recipe_ref> <recipe_path>]
  - reads logs/sib/own-<fold>/maps/manifest.json at <own_ref> (git show);
  - asserts manifest 'arm' == <arm> and every tile's 'arm' (if present) == <arm>; records model_final_sha256;
  - asserts the eligible set (valid_fraction >= 0.5, the norm_manifest default) is a subset of the RECIPE.md
    '<ARM> held-out tiles' list at <recipe_ref> (default 6b5bdc5, logs/sib/own-lead/p4own/RECIPE.md);
  - splits the manifest per segment (adds top-level 'segment', keeps each tile record unchanged) and writes a LOCAL
    commit whose parent is <own_ref> and whose tree adds logs/sib/rh-e1/own_split/<fold>/<segment>.json, so that the
    unchanged tools/p4/norm_manifest.py can read manifest and tiles from one ref. The commit is never pushed.
  - writes <out_json>: {own_ref, split_commit, arm, model_final_sha256, recipe list, per-segment manifest paths/sha256,
    n per segment, eligible (r, c) per segment}.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile


def git(*a, inp=None, env=None):
    return subprocess.run(['git', *a], input=inp, capture_output=True, check=True, env=env).stdout


def recipe_list(ref, path, arm):
    txt = git('show', f'{ref}:{path}').decode()
    line = [ln for ln in txt.splitlines() if re.match(rf'^- {arm} held-out tiles \(\d+\):', ln)]
    assert len(line) == 1, f'RECIPE line for {arm} not found exactly once'
    items = line[0].split('):', 1)[1]
    out = set()
    for it in items.split(';'):
        it = it.strip()
        if not it:
            continue
        strip, rc = it.split(':')
        r, c = rc.split(',')
        out.add((strip.strip(), int(r), int(c)))
    return out


def main(own_ref, fold, arm, out_json, recipe_ref='6b5bdc5', recipe_path='logs/sib/own-lead/p4own/RECIPE.md'):
    own_commit = git('rev-parse', own_ref).decode().strip()
    man_path = f'logs/sib/own-{fold}/maps/manifest.json'
    raw = git('show', f'{own_commit}:{man_path}')
    m = json.loads(raw)
    assert m.get('arm') == arm, ('manifest arm', m.get('arm'), arm)
    assert all(t.get('arm', arm) == arm for t in m['tiles']), 'tile arm mismatch'
    rec = recipe_list(recipe_ref, recipe_path, arm)
    segs = sorted({t['seg'] for t in m['tiles']})
    short = {s: re.search(r'(w\d{3}-\d{3})$', s).group(1) for s in segs}
    elig = [t for t in m['tiles'] if t.get('valid_fraction', 0) >= 0.5]
    got = {(short[t['seg']], t['r'], t['c']) for t in elig}
    assert got <= rec, ('eligible tiles not in RECIPE list', sorted(got - rec))
    # local split commit: parent = own_commit, tree = own tree + split manifests
    with tempfile.TemporaryDirectory() as td:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(td, 'index'))
        git('read-tree', own_commit, env=env)
        per = {}
        for s in segs:
            sm = {k: v for k, v in m.items() if k != 'tiles'}
            sm['segment'] = s
            sm['tiles'] = [t for t in m['tiles'] if t['seg'] == s]
            sm['split_by'] = 'rh-e1 own_split.py (tile records unchanged; top-level segment added)'
            b = json.dumps(sm, indent=1).encode()
            blob = git('hash-object', '-w', '--stdin', inp=b).decode().strip()
            p = f'logs/sib/rh-e1/own_split/{fold}/{s}.json'
            git('update-index', '--add', '--cacheinfo', f'100644,{blob},{p}', env=env)
            per[s] = {'path': p, 'sha256': hashlib.sha256(b).hexdigest(), 'n_tiles': len(sm['tiles']),
                      'eligible_rc': sorted([t['r'], t['c']] for t in sm['tiles'] if t.get('valid_fraction', 0) >= 0.5)}
        tree = git('write-tree', env=env).decode().strip()
        cenv = dict(os.environ, GIT_AUTHOR_DATE='2026-01-01T00:00:00Z', GIT_COMMITTER_DATE='2026-01-01T00:00:00Z',
                    GIT_AUTHOR_NAME='rh-e1', GIT_AUTHOR_EMAIL='rh-e1@local', GIT_COMMITTER_NAME='rh-e1',
                    GIT_COMMITTER_EMAIL='rh-e1@local')
        split = git('commit-tree', tree, '-p', own_commit, '-m', f'rh-e1 local split of {man_path} (never pushed)',
                    env=cenv).decode().strip()
    out = {'own_ref': own_commit, 'manifest': man_path, 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
           'tiles_dir': f'logs/sib/own-{fold}/maps/tiles', 'split_commit': split, 'arm': m.get('arm'),
           'model_final_sha256': m.get('model_final_sha256'), 'train_manifest_sha256': m.get('train_manifest_sha256'),
           'recipe_ref': recipe_ref, 'recipe_path': recipe_path, 'recipe_list': sorted(list(x) for x in rec),
           'n_manifest_tiles': len(m['tiles']), 'n_eligible': len(elig), 'segments': per}
    with open(out_json, 'w') as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({'split_commit': split, 'arm': out['arm'], 'n_eligible': len(elig),
                      'per_segment': {s: v['n_tiles'] for s, v in per.items()}}))


if __name__ == '__main__':
    main(*sys.argv[1:])
