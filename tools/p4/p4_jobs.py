# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-B census jobs (RULES.md DECL-P4-2 items 2-4). Numbers only; no image is opened for viewing.

import  <strip> <src_dir> <manifest.json> <batch>
        Copies each read-eligible tile PNG listed in the builder manifest (sha256 checked) to /work/p4/img/<uuid4>.png
        and writes the batch key /srv/scorer/p4_key_<batch>.json (O_EXCL, 0400):
        {uuid: {"segment", "strip", "r", "c", "rot": 0, "src_sha256"}}.
null    <batch> <n> [<census_batch>,...]
        Draws n tiles from all imported census tiles (or, if census batches are listed, from those batches only;
        DECL-P4-4) by random.Random(20260926 + batch index) and writes each rotated
        90 degrees clockwise (np.rot90(k=-1) of the decoded uint8 array; bytes via hercules.display.builder.png_bytes)
        as a new uuid; key /srv/scorer/p4_key_<batch>.json {uuid: {..., "rot": 90}}.
jobs    <batch> <census_batch>[,<census_batch>...] <null_batch> [v1|sigma2|sigma2t|block]
        Sessions of up to 8 census tiles + 1 N0 tile, shuffled (secrets.SystemRandom), key sheet first, frozen
        single-image task configs/briefs/k_d2_task.txt (v1) or, under DECL-P4-2-A2, the both-sigma key sheet
        configs/briefs/keysheet_sigma2.png (absolute path in the brief, as the Read tool requires) with
        configs/briefs/k_d2_task_sigma2.txt (sigma2); reader model 'opus' (DECL-P4-2-A1); briefs /work/p4/brief_<job>.txt; job list
        /work/p4/jobs_<batch>.json. Every census tile of the listed batches is placed exactly once.
"""
import hashlib
import json
import os
import random
import secrets
import sys
import uuid

sys.path.insert(0, 'src')

IMG = '/work/p4/img'
SCORER = '/srv/scorer'
KS = '/work/probe1/keysheet_5da96bde.png'
KS_SHA = '5da96bde05851b0cd9316292e5f7ef95d497a400f582c6869840a66dc6a65f88'
SINGLE = 'configs/briefs/k_d2_task.txt'
SINGLE_SHA = '74a0cbe86223d68a09cd28d8cc5a012438e72d628d59e7114fa096ccf2ac45f0'
KS2 = '/home/user/dominion/configs/briefs/keysheet_sigma2.png'
KS2_SHA = '164262e67dfd7589bdd03dddb1b8470267bd7d46d5c40b0af63fc1eb980db438'
SINGLE2 = 'configs/briefs/k_d2_task_sigma2.txt'
SINGLE2_SHA = '71b133f4cdcd4ff588b9c3ebc077a6e22aef62a0f6c8cd13530e083764e9f7bb'
SINGLE2T = 'configs/briefs/k_d2_task_sigma2t.txt'  # METRIC-HASH-35: title-zone size prior 2-6 mm (DECL-P4-12-A1)
SINGLE2T_SHA = 'f07fbdffab8ee0d62afb946fafc13b6a794ef5ab5e8506bdfbd5ae90c4f8bea0'
SINGLEB = 'configs/briefs/k_d2_task_block.txt'  # METRIC-HASH-38: title-scale block/ornament brief (DECL-P4-17)
SINGLEB_SHA = '2995f22f2c5fd5af39a1ce93fb7a3b78f240825e0c8294c06dd8c495e66ac1c5'


def task_variant(variant):
    """(key sheet, its sha, task text path, its sha) for a brief variant."""
    if variant == 'v1':
        return KS, KS_SHA, SINGLE, SINGLE_SHA
    if variant == 'sigma2':
        return KS2, KS2_SHA, SINGLE2, SINGLE2_SHA
    if variant == 'sigma2t':
        return KS2, KS2_SHA, SINGLE2T, SINGLE2T_SHA
    if variant == 'block':
        return KS2, KS2_SHA, SINGLEB, SINGLEB_SHA
    raise ValueError(variant)
NULL_SEED = 20260926
PER_SESSION = 8


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def _write_key(batch, key):
    path = f'{SCORER}/p4_key_{batch}.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(fd, 'w') as fh:
        json.dump(key, fh, indent=1)
    return path


def _keys():
    out = {}
    for f in sorted(os.listdir(SCORER)):
        if f.startswith('p4_key_') and f.endswith('.json'):
            out[f[7:-5]] = json.load(open(f'{SCORER}/{f}'))
    return out


def cmd_import(strip, src_dir, manifest, batch):
    man = json.load(open(manifest))
    os.makedirs(IMG, exist_ok=True)
    key = {}
    for t in man['tiles']:
        fn = f"{src_dir}/{strip}_r{t['r']}_c{t['c']}.png"
        assert _sha(fn) == t['sha256'], fn
        u = str(uuid.uuid4())
        with open(f'{IMG}/{u}.png', 'xb') as fh:
            fh.write(open(fn, 'rb').read())
        key[u] = {'segment': man['segment'], 'strip': strip, 'r': t['r'], 'c': t['c'], 'rot': 0,
                  'src_sha256': t['sha256']}
    path = _write_key(batch, key)
    print(json.dumps({'batch': batch, 'n': len(key), 'key_sha256': _sha(path)}))


def cmd_null(batch, n, pool_batches=None):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    keys = _keys()
    src = [keys[b] for b in pool_batches] if pool_batches else list(keys.values())
    census = sorted((u, v) for k in src for u, v in k.items() if v['rot'] == 0)
    bidx = int(hashlib.sha256(batch.encode()).hexdigest()[:8], 16) % 100000
    draw = random.Random(NULL_SEED + bidx).sample(census, n)
    key = {}
    for u0, v in draw:
        a = cv2.imread(f'{IMG}/{u0}.png', cv2.IMREAD_UNCHANGED)
        assert a is not None and a.dtype == np.uint8 and a.ndim == 2, u0
        r = np.ascontiguousarray(np.rot90(a, k=-1))
        u = str(uuid.uuid4())
        with open(f'{IMG}/{u}.png', 'xb') as fh:
            fh.write(png_bytes(r))
        key[u] = dict(v, rot=90, null_of=u0)
    path = _write_key(batch, key)
    print(json.dumps({'batch': batch, 'n': len(key), 'seed': NULL_SEED + bidx, 'key_sha256': _sha(path)}))


def cmd_jobs(batch, census_batches, null_batch, variant='v1'):
    from hercules.harness.jobs import make
    assert variant in ('v1', 'sigma2', 'sigma2t', 'block')
    ks, ks_sha, single, single_sha = task_variant(variant)
    assert _sha(ks) == ks_sha
    task = open(single, encoding='utf-8').read()
    assert hashlib.sha256(task.encode()).hexdigest() == single_sha
    keys = _keys()
    census = [u for b in census_batches for u, v in keys[b].items() if v['rot'] == 0]
    nulls = [u for u, v in keys[null_batch].items() if v['rot'] == 90]
    rng = secrets.SystemRandom()
    rng.shuffle(census)
    rng.shuffle(nulls)
    groups = [census[i:i + PER_SESSION] for i in range(0, len(census), PER_SESSION)]
    assert len(nulls) >= len(groups), (len(nulls), len(groups))
    jobs = []
    for g, nu in zip(groups, nulls):
        items = g + [nu]
        rng.shuffle(items)
        paths = [ks] + [f'{IMG}/{u}.png' for u in items]
        job, brief = make('reader', task, paths)
        with open(f'/work/p4/brief_{job}.txt', 'x', encoding='utf-8') as fh:
            fh.write(brief)
        jobs.append({'job': job, 'n_census': len(g), 'n_null': 1, 'model': 'opus', 'n_images': len(paths)})
    out = f'/work/p4/jobs_{batch}.json'
    with open(out, 'x') as fh:
        json.dump({'batch': batch, 'census_batches': census_batches, 'null_batch': null_batch, 'variant': variant,
                   'jobs': jobs}, fh,
                  indent=1)
    print(json.dumps({'jobs': len(jobs), 'census_tiles': len(census), 'out': out}))


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'import':
        cmd_import(*sys.argv[2:6])
    elif c == 'null':
        cmd_null(sys.argv[2], int(sys.argv[3]), sys.argv[4].split(',') if len(sys.argv) > 4 else None)
    elif c == 'jobs':
        cmd_jobs(sys.argv[2], sys.argv[3].split(','), sys.argv[4], *(sys.argv[5:6]))
