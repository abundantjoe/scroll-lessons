# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 reader jobs (RULES.md DECL-D3-A1 items 5-6): 3 fresh fable readers per (arm, state), arms FA, NULLA, REVA, CTRL.

Each session: every gated J window of the arm-state + 1 canary + 1 blank (reader 0 and 2: first blank, reader 1:
second blank), LEFT/RIGHT pairs of the arm's two orders in random item order and sides (k_d2_pairs_task.txt).
Display key /srv/scorer/d3_key.json (images: window, arm, kind 'BASE', order fwd|rev, state; windows as the D1 key).
Scorer-held item map /srv/scorer/d3_items.json (0400); job list /work/d3/jobs_d3.json.
Usage: python tools/d1/d3_jobs.py
"""
import hashlib
import json
import os
import secrets
import sys
import uuid

sys.path.insert(0, 'src')
from hercules.harness.jobs import make  # noqa: E402

KS = '/work/probe1/keysheet_5da96bde.png'
PAIRS = 'configs/briefs/k_d2_pairs_task.txt'
IMG = '/work/d3/img'
KEY = '/srv/scorer/d3_key.json'
ITEMS = '/srv/scorer/d3_items.json'
JOBS = '/work/d3/jobs_d3.json'
MANIFEST = '/work/d3/manifest.json'
ARMS = ('FA', 'NULLA', 'REVA', 'CTRL')


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    rng = secrets.SystemRandom()
    assert _sha(KS) == '5da96bde05851b0cd9316292e5f7ef95d497a400f582c6869840a66dc6a65f88'
    pairs = open(PAIRS, encoding='utf-8').read()
    assert hashlib.sha256(pairs.encode()).hexdigest() == 'bd03427efc79db3b77838dfbe1323721dcaffbee48374e6f9e562b4c8554c9dc'
    key = json.load(open(KEY))
    man = {e['path'].split('/')[-1][:-4]: e['sha256'] for e in json.load(open(MANIFEST))['images']}
    wins = key['windows']
    gated = sorted(w for w, v in wins.items() if v['set'] == 'J' and v['gate']['pass'])
    blanks = sorted(w for w, v in wins.items() if v['set'] == 'blank')
    canary = [w for w, v in wins.items() if v['set'] == 'canary']
    assert len(blanks) == 2 and len(canary) == 1 and gated, (gated, blanks, canary)
    idx = {(e['window'], e['arm'], e['order'], e['state']): u for u, e in key['images'].items()}
    assert not os.path.exists(ITEMS) and not os.path.exists(JOBS)
    all_items, jobs = {}, []
    for arm in ARMS:
        for state in ('A', 'B'):
            for r in range(3):
                plan = [(w, 'window') for w in gated] + [(canary[0], 'canary'), (blanks[r % 2], 'blank')]
                rng.shuffle(plan)
                items, paths, lines = {}, [KS], []
                for w, role in plan:
                    o = ['fwd', 'rev']
                    rng.shuffle(o)
                    lu, ru = idx[(w, arm, o[0], state)], idx[(w, arm, o[1], state)]
                    for u in (lu, ru):
                        assert _sha(f'{IMG}/{u}.png') == man[u], u
                    iid = str(uuid.uuid4())
                    items[iid] = {'left': lu, 'right': ru, 'scored_window': w, 'role': role}
                    paths += [f'{IMG}/{lu}.png', f'{IMG}/{ru}.png']
                    lines.append(f'Item {iid}: LEFT = {IMG}/{lu}.png ; RIGHT = {IMG}/{ru}.png')
                job, brief = make('reader', pairs.format(items='\n'.join(lines)), paths)
                open(f'/work/d3/brief_{job}.txt', 'w', encoding='utf-8').write(brief)
                all_items[job] = items
                jobs.append({'arm': f'{arm}-{state}', 'reader': r, 'job': job, 'model': 'fable', 'n_images': len(paths)})
    with open(ITEMS, 'x') as fh:
        json.dump(all_items, fh, indent=1)
    os.chmod(ITEMS, 0o400)
    json.dump({'stage': 'd3', 'gated_J': gated, 'jobs': jobs}, open(JOBS, 'w'), indent=1)
    for j in jobs:
        print(j['arm'], j['reader'], j['job'], j['n_images'])


if __name__ == '__main__':
    main()
