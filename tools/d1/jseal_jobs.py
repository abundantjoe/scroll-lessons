# Provenance: Project HERCULES | owner the owner | [id removed]
"""D1 J-seal agent jobs (RULES.md DECL-D1-A3 items 1-3, DECL-D1-A4).

picker  : 1 fresh fable picker; key sheet, then the 2 primary blank images (single-image items, random order).
reserve : (only with --reserve W) 1 fresh fable picker; key sheet, then the reserve image(s) named on the command line.
sealers : 3 fresh fable sealers; key sheet, then the 5 J images (single-image items, random order per sealer).
Task text configs/briefs/k_d2_task.txt (METRIC-HASH-14). Writes /work/jseal/jobs.json (appends reserve pickers).
Usage: python tools/d1/jseal_jobs.py initial | reserve <image path> [...]
"""
import hashlib
import json
import os
import secrets
import sys

sys.path.insert(0, 'src')
from hercules.harness.jobs import make  # noqa: E402

KS = '/work/probe1/keysheet_5da96bde.png'
TASK = 'configs/briefs/k_d2_task.txt'
JOBS = '/work/jseal/jobs.json'


def _check():
    assert hashlib.sha256(open(KS, 'rb').read()).hexdigest() == '5da96bde05851b0cd9316292e5f7ef95d497a400f582c6869840a66dc6a65f88'
    t = open(TASK, encoding='utf-8').read()
    assert hashlib.sha256(t.encode()).hexdigest() == '74a0cbe86223d68a09cd28d8cc5a012438e72d628d59e7114fa096ccf2ac45f0'
    return t


def _images():
    man = json.load(open('/work/jseal/manifest.json'))
    out = {}
    for e in man['images']:
        p = f"/work/jseal/{e['path']}"
        assert hashlib.sha256(open(p, 'rb').read()).hexdigest() == e['sha256'], p
        out.setdefault(e['path'].split('/')[0], []).append(p)
    return out


def _job(role, task, imgs, tag):
    order = imgs[:]
    secrets.SystemRandom().shuffle(order)
    job, brief = make(role, task, [KS] + order)
    open(f'/work/jseal/brief_{tag}.txt', 'w', encoding='utf-8').write(brief)
    return {'tag': tag, 'role': role, 'job': job}


def main():
    task = _check()
    imgs = _images()
    if sys.argv[1] == 'initial':
        assert not os.path.exists(JOBS)
        assert len(imgs.get('J', [])) == 5 and len(imgs.get('blank', [])) == 2, {k: len(v) for k, v in imgs.items()}
        jobs = [_job('picker', task, imgs['blank'], 'picker_0')]
        jobs += [_job('sealer', task, imgs['J'], f'sealer_{i}') for i in range(3)]
        json.dump({'jobs': jobs}, open(JOBS, 'w'), indent=1)
    elif sys.argv[1] == 'reserve':
        d = json.load(open(JOBS))
        paths = sys.argv[2:]
        assert paths and all(p in imgs.get('blank_reserve', []) for p in paths), paths
        n = sum(1 for j in d['jobs'] if j['role'] == 'picker')
        d['jobs'].append(_job('picker', task, paths, f'picker_{n}'))
        json.dump(d, open(JOBS, 'w'), indent=1)
    for j in json.load(open(JOBS))['jobs']:
        print(j['tag'], j['role'], j['job'])


if __name__ == '__main__':
    main()
