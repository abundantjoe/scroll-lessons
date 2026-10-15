# Provenance: Project HERCULES | owner the owner | [id removed]
"""Make the D1 J seal (RULES.md DECL-SEAL, DECL-D1-A3 items 2-3, DECL-D1-A4). Prints and stores counts only.

Blank confirmation: a blank window is confirmed if the picker that saw it reports rows N and names <= 1 letter
on it. Each primary blank is used if confirmed, else its reserve (key field replaces_primary_rank) if a reserve
picker confirmed it; if neither, STOP (no seal). Sealers: exactly 3 audited-valid, schema-valid answers.
Seal = hercules.scorer.sealbuild.build_seal (sealpos label rule, METRIC-HASH-13) on J1-J5 with the official
0841 labels, plus {blank: true} windows; encrypted with age to the scorer recipient at /work/jseal/seal_J.age.
Summary (counts, agreement, blank confirmation, seal sha256) -> logs/d1/jseal_summary.json.
Usage: python tools/d1/make_jseal.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, 'src')
from hercules.harness.collect import load_answer, validate_reader  # noqa: E402
from hercules.scorer.seal import seal_encrypt  # noqa: E402
from hercules.scorer.sealbuild import build_seal  # noqa: E402

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
OUT = '/work/jseal/seal_J.age'


def main():
    jobs = json.load(open('/work/jseal/jobs.json'))['jobs']
    key = json.load(open('/srv/scorer/jseal_key.json'))
    imgs, wins = key['images'], key['windows']
    for j in jobs:
        assert json.load(open(f"/work/jobs/{j['job']}.json")).get('valid') is True, j
    # blank confirmation
    conf = {}
    for j in (x for x in jobs if x['role'] == 'picker'):
        ans = load_answer(f"/work/sealed_io/{j['job']}.age", 'jseal-blank-confirmation')
        assert validate_reader(ans), j
        for it in ans.get('items', []):
            im = imgs.get(it.get('id'))
            if im is None:
                continue
            left = it.get('left') or {}
            n = len(left.get('letters', []))
            conf[im['window']] = {'rows': left.get('rows'), 'n_named': n, 'confirmed': left.get('rows') == 'N' and n <= 1,
                                  'picker': j['tag']}
    primaries = sorted(w for w, v in wins.items() if v.get('blank') and not v.get('reserve'))
    blanks, repl = [], {}
    for p in primaries:
        if conf.get(p, {}).get('confirmed'):
            blanks.append(p)
            continue
        res = [w for w, v in wins.items() if v.get('reserve') and v.get('replaces_primary_rank') == wins[p].get('rank')]
        ok = [w for w in res if conf.get(w, {}).get('confirmed')]
        if not ok:
            print('STOP: blank', p, 'not confirmed and no confirmed reserve; confirmation', conf.get(p), 'reserves', res)
            sys.exit(2)
        blanks.append(ok[0])
        repl[p] = ok[0]
    # sealers
    sealers = [j for j in jobs if j['role'] == 'sealer']
    assert len(sealers) == 3, len(sealers)
    answers = {}
    for j in sealers:
        ans = load_answer(f"/work/sealed_io/{j['job']}.age", 'jseal-make')
        assert validate_reader(ans), j
        answers[j['tag']] = ans
    jw = sorted(w for w, v in wins.items() if v.get('J'))
    assert jw == ['J1', 'J2', 'J3', 'J4', 'J5'], jw
    lab = np.load(key['labels_file'])
    labels = {w: lab[w] for w in jw}
    org = {w: wins[w]['affine_levelled_window_to_organizer'] for w in jw}
    seal, summary = build_seal(answers, imgs, jw, labels=labels, blank_windows=blanks, organizer_affines=org)
    seal.update({'serves': 'RULES.md DECL-D1 J seal (DECL-SEAL, DECL-D1-A3, DECL-D1-A4)',
                 'frame': 'levelled window px of each window, state A, pixel centres at integers; org_x/org_y = organizer 9.366 um canvas px',
                 'sealer_jobs': {j['tag']: j['job'] for j in sealers}})
    assert not os.path.exists(OUT)
    sha = seal_encrypt(seal, open('/srv/scorer/seal.agekey.pub').read().strip(), OUT)
    summary.update({'provenance': PROV, 'seal_path': OUT, 'seal_sha256': sha, 'blank_confirmation': conf,
                    'blanks_used': blanks, 'blank_replacements': repl, 'sealer_jobs': {j['tag']: j['job'] for j in sealers}})
    os.makedirs('logs/d1', exist_ok=True)
    json.dump(summary, open('logs/d1/jseal_summary.json', 'w'), indent=1)
    print(json.dumps({k: summary[k] for k in ('S_prime', 'n_firm_total', 'blanks_used', 'blank_replacements', 'seal_sha256')}))
    for w, v in summary['windows'].items():
        print(w, {k: v.get(k) for k in ('n_letters', 'n_firm', 'n_agree_3', 'n_agree_2', 'n_label_positioned', 'blank')})


if __name__ == '__main__':
    main()
