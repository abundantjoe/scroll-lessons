# Provenance: Project HERCULES | owner the owner | [id removed]
"""Write the D3 stage-2 record logs/d1/d3_stage2.json (RULES.md DECL-D3-A3 item 7) before d3_jobs.py runs.

Numbers and hashes only; opens no image and never reads /srv/scorer.
Records: stage-2 script sha256 (/work/d3/scripts vs tools/d3 mirror), E1/E2 record hashes, per-arm model_final
sha256 and summary/train-log hashes, per-arm inference record sha256 with per-window thread counts and return codes,
the display manifest sha256 and image count, and the blob-f180 file hashes.
Usage: python tools/d3/d3_stage2_record.py   (from the repo root)
"""
import hashlib
import json
import os
import sys
import time

ARMS = ('CTRL', 'FA', 'NULLA', 'REVA')
SCRIPTS = ('d3_infer.py', 'd3_build.py', 'label_equiv.py', 'infer_arms.sh', 'start_d3_stage2.sh', 'd3_e1.py',
           'd3_ledger_run.sh')
OUT = 'logs/d1/d3_stage2.json'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    assert not os.path.exists('/work/d3/jobs_d3.json'), 'jobs already exist: the record must precede d3_jobs.py'
    rec = {'provenance': PROV, 'generated_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'serves': 'RULES.md DECL-D3-A3 item 7 (stage-2 record before d3_jobs.py)',
           'viewing': 'no image was opened; numbers only', 'scripts': {}, 'prechecks': {}, 'arms': {}}
    for s in SCRIPTS:
        w, t = f'/work/d3/scripts/{s}', f'tools/d3/{s}'
        e = {'work': sha(w) if os.path.exists(w) else None, 'mirror': sha(t) if os.path.exists(t) else None}
        e['identical'] = e['work'] is not None and e['work'] == e['mirror']
        rec['scripts'][s] = e
    for k, p in (('E1', 'logs/d1/d3_e1.json'), ('E2', 'logs/d1/d3_e2_dryrun.json'),
                 ('E2_recheck', 'logs/d1/d3_e2_dryrun_recheck.json'), ('stage2_pre', 'logs/d1/d3_stage2_pre.json')):
        rec['prechecks'][k] = {'path': p, 'sha256': sha(p)}
    for a in ARMS:
        run = f'/work/d3/runs/{a}'
        inf = f'/work/d3/work/infer_{a}.json'
        summ = json.load(open(f'{run}/summary.json'))
        mf = sha(f'{run}/model_final.pth')
        assert summ.get('steps') == 2000, (a, summ.get('steps'))
        ir = json.load(open(inf))
        wins = {}
        for w, v in sorted(ir['windows'].items()):
            assert v['returncode'] == 0 and v['checkpoint_sha256'] == mf, (a, w)
            wins[w] = {'threads': v['threads'], 'returncode': v['returncode'], 'seconds': v['seconds'],
                       'outputs': {n: o['sha256'] for n, o in sorted(v['outputs'].items())}}
        rec['arms'][a] = {'model_final_sha256': mf, 'summary_sha256': sha(f'{run}/summary.json'),
                          'train_log_sha256': sha(f'{run}/train_log.jsonl'), 'resumptions': summ.get('resumptions'),
                          'infer_record': inf, 'infer_record_sha256': sha(inf), 'n_windows': len(wins),
                          'threads_used': sorted({v['threads'] for v in wins.values()}), 'windows': wins}
    man = json.load(open('/work/d3/manifest.json'))
    rec['display_manifest'] = {'path': '/work/d3/manifest.json', 'sha256': sha('/work/d3/manifest.json'),
                               'n_images': len(man['images'])}
    rec['blob_f180'] = {p: sha(p) for p in ('/work/d3/blob_f180.json', 'logs/d1/d3_blob_f180.json')}
    assert all(e['identical'] for e in rec['scripts'].values()), rec['scripts']
    with open(OUT, 'w') as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps({'out': OUT, 'sha256': sha(OUT), 'arms': {a: v['model_final_sha256'][:12]
                      for a, v in rec['arms'].items()}, 'n_images': rec['display_manifest']['n_images']}))


if __name__ == '__main__':
    sys.exit(main())
