# Provenance: Project HERCULES | owner the owner | [id removed]
"""D1 reader jobs (RULES.md DECL-D1-A3 item 6, DECL-D1-A5). 3 fresh fable readers per arm-state.

Stage "ref": REF0, REF015, REF030, REF045 (state A), read first (VOID check before any model arm).
Stage "model": BASE-A, BASE-B, RAW-A, RAW-B, CHANCE-A, CHANCE-B.
Each reader session: every gated J window of its arm-state + 1 canary + 1 blank (reader 0 and 2: first blank,
reader 1: second blank), items and LEFT/RIGHT sides in random order. REF items are single images (item id =
image uuid, k_d2_task.txt); BASE/RAW/CHANCE items are LEFT/RIGHT pairs of the two orders (random item uuid,
k_d2_pairs_task.txt). CHANCE: J window i shows the BASE maps of the next gated J window in window-id order
(cyclic) and is scored against window i; canary and blank items show their own BASE maps.
Scorer-held item map /srv/scorer/d1_items_<stage>.json (0400); job list /work/d1/jobs_<stage>.json.
Usage: python tools/d1/d1_jobs.py ref|model
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
SINGLE = 'configs/briefs/k_d2_task.txt'
PAIRS = 'configs/briefs/k_d2_pairs_task.txt'
IMG = '/work/d1/img'
STAGES = {'ref': [('REF0', 'A'), ('REF015', 'A'), ('REF030', 'A'), ('REF045', 'A')],
          'model': [('BASE', 'A'), ('BASE', 'B'), ('RAW', 'A'), ('RAW', 'B'), ('CHANCE', 'A'), ('CHANCE', 'B')]}
ORDERS = {'BASE': ('fwd', 'rev'), 'RAW': ('F', 'B'), 'CHANCE': ('fwd', 'rev')}


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main(stage):
    rng = secrets.SystemRandom()
    assert _sha(KS) == '5da96bde05851b0cd9316292e5f7ef95d497a400f582c6869840a66dc6a65f88'
    single = open(SINGLE, encoding='utf-8').read()
    pairs = open(PAIRS, encoding='utf-8').read()
    assert hashlib.sha256(single.encode()).hexdigest() == '74a0cbe86223d68a09cd28d8cc5a012438e72d628d59e7114fa096ccf2ac45f0'
    assert hashlib.sha256(pairs.encode()).hexdigest() == 'bd03427efc79db3b77838dfbe1323721dcaffbee48374e6f9e562b4c8554c9dc'
    key = json.load(open('/srv/scorer/d1_key.json'))
    man = {e['path'].split('/')[-1][:-4]: e['sha256'] for e in json.load(open('/work/d1/manifest.json'))['images']}
    wins = key['windows']
    gated = sorted(w for w, v in wins.items() if v['set'] == 'J' and v['gate']['pass'])
    blanks = sorted(w for w, v in wins.items() if v['set'] == 'blank')
    canary = [w for w, v in wins.items() if v['set'] == 'canary']
    assert len(blanks) == 2 and len(canary) == 1 and gated, (gated, blanks, canary)
    idx = {}
    for u, e in key['images'].items():
        idx[(e['window'], e['kind'], e['order'], e['state'])] = u
    out_items = f'/srv/scorer/d1_items_{stage}.json'
    out_jobs = f'/work/d1/jobs_{stage}.json'
    assert not os.path.exists(out_items) and not os.path.exists(out_jobs)
    all_items, jobs = {}, []
    for arm, state in STAGES[stage]:
        for r in range(3):
            plan = [(w, w, 'window') for w in gated] + [(canary[0], canary[0], 'canary'), (blanks[r % 2], blanks[r % 2], 'blank')]
            rng.shuffle(plan)
            items, paths, lines = {}, [KS], []
            nxt = {w: gated[(i + 1) % len(gated)] for i, w in enumerate(gated)}
            for content, scored, role in plan:
                if arm.startswith('REF'):
                    u = idx[(content, arm, 'single', 'A')]
                    p = f'{IMG}/{u}.png'
                    assert _sha(p) == man[u], p
                    items[u] = {'left': u, 'right': None, 'scored_window': scored, 'role': role}
                    paths.append(p)
                    continue
                kind = 'BASE' if arm == 'CHANCE' else arm
                src = nxt[content] if (arm == 'CHANCE' and role == 'window') else content
                o = list(ORDERS[arm])
                rng.shuffle(o)
                lu, ru = idx[(src, kind, o[0], state)], idx[(src, kind, o[1], state)]
                for u in (lu, ru):
                    assert _sha(f'{IMG}/{u}.png') == man[u], u
                iid = str(uuid.uuid4())
                items[iid] = {'left': lu, 'right': ru, 'scored_window': scored, 'role': role}
                paths += [f'{IMG}/{lu}.png', f'{IMG}/{ru}.png']
                lines.append(f'Item {iid}: LEFT = {IMG}/{lu}.png ; RIGHT = {IMG}/{ru}.png')
            task = single if arm.startswith('REF') else pairs.format(items='\n'.join(lines))
            job, brief = make('reader', task, paths)
            open(f'/work/d1/brief_{job}.txt', 'w', encoding='utf-8').write(brief)
            all_items[job] = items
            jobs.append({'arm': f'{arm}-{state}' if not arm.startswith('REF') else arm, 'reader': r, 'job': job,
                         'model': 'fable', 'n_images': len(paths)})
    with open(out_items, 'x') as fh:
        json.dump(all_items, fh, indent=1)
    os.chmod(out_items, 0o400)
    json.dump({'stage': stage, 'gated_J': gated, 'jobs': jobs}, open(out_jobs, 'w'), indent=1)
    for j in jobs:
        print(j['arm'], j['reader'], j['job'], j['n_images'])


if __name__ == '__main__':
    main(sys.argv[1])
