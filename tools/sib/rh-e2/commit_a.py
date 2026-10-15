# Provenance: Project HERCULES | owner the owner | [id removed]
"""rh-e2 COMMIT A assembler (DECL-REMOTE-HARNESS-1 item 4). Numbers and hashes only; opens no image for viewing.

usage: commit_a.py <A_dir> <batch> <null_batch> <jobs_batch> <builder_branch> <builder_commit> <manifest> <tiles_dir> <norm_manifest_json> <variant> [note]
Copies keys, jobs json, briefs, job records and the normalised manifest into A_dir; writes img_manifest.json,
builder_ref.json (key and code sha256, template check vs logs/p4/ref_brief_<variant>.txt) and SHA256SUMS.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

RCPT = 'age1vp0tkyj8xecncfmcxj748ceef89mpmwayljccaduapjx3aqhh5rstvvcq5'
CODE = ['tools/p4/norm_manifest.py', 'tools/p4/p4_jobs.py', 'tools/p4/score_p4.py', 'tools/p4/p4_phase2.py',
        'tools/p4/p4_ext.py', 'src/hercules/harness/audit.py', 'src/hercules/harness/jobs.py',
        'configs/briefs/keysheet_sigma2.png']


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main(A, batch, nbatch, jbatch, br, bc, manifest, tiles, norm, variant, note=''):
    os.makedirs(f'{A}/briefs', exist_ok=True)
    os.makedirs(f'{A}/job_records', exist_ok=True)
    for b in (batch, nbatch):
        shutil.copyfile(f'/srv/scorer/p4_key_{b}.json', f'{A}/p4_key_{b}.json')
    shutil.copyfile(f'/work/p4/jobs_{jbatch}.json', f'{A}/jobs_{jbatch}.json')
    shutil.copyfile(norm, f'{A}/{os.path.basename(norm)}')
    jobs = json.load(open(f'{A}/jobs_{jbatch}.json'))
    assert jobs['variant'] == variant
    for j in jobs['jobs']:
        shutil.copyfile(f"/work/p4/brief_{j['job']}.txt", f"{A}/briefs/brief_{j['job']}.txt")
        shutil.copyfile(f"/work/jobs/{j['job']}.json", f"{A}/job_records/{j['job']}.json")
    kc = json.load(open(f'{A}/p4_key_{batch}.json'))
    kn = json.load(open(f'{A}/p4_key_{nbatch}.json'))
    keys = {**kc, **kn}
    for f in glob.glob('/srv/scorer/p4_key_*.json'):
        b = os.path.basename(f)[7:-5]
        if b not in (batch, nbatch):
            assert not (set(json.load(open(f))) & set(keys)), f'uuid collision with {b}'
    imgs = {u: sha(f'/work/p4/img/{u}.png') for u in sorted(keys)}
    json.dump(imgs, open(f'{A}/img_manifest.json', 'w'), indent=1)
    norm_b = lambda s: re.sub(r'/work/p4/img/[0-9a-f-]+\.png\n', '', re.sub(r'/work/sealed_io/[0-9a-f-]+\.age', 'X', s))
    ref = norm_b(open(f'logs/p4/ref_brief_{variant}.txt').read())
    tmpl = [norm_b(open(f).read()) == ref for f in glob.glob(f'{A}/briefs/*.txt')]
    used = {p for r in glob.glob(f'{A}/job_records/*.json') for p in json.load(open(r))['images'] if '/work/p4/img/' in p}
    assert used == {f'/work/p4/img/{u}.png' for u in keys}
    out = {'batch': batch, 'null_batch': nbatch, 'jobs_batch': jbatch, 'builder_branch': br, 'builder_commit': bc,
           'manifest': manifest, 'tiles_dir': tiles,
           'orchestrator_base_commit': subprocess.check_output(['git', 'rev-parse', 'origin/claude/gifted-bell-gavnl5'], text=True).strip(),
           'harness_commit_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
           'variant': variant, 'recipient': RCPT,
           'key_sha256': {f'p4_key_{b}.json': sha(f'/srv/scorer/p4_key_{b}.json') for b in (batch, nbatch)},
           'code_sha256': {p: sha(p) for p in CODE + [f'configs/briefs/k_d2_task_{variant}.txt', f'logs/p4/ref_brief_{variant}.txt']},
           'n_images': len(imgs), 'n_census': len(kc), 'n_null': len(kn), 'n_sessions': len(jobs['jobs']),
           'session_sizes': sorted({(j['n_census'], j['n_null']) for j in jobs['jobs']}),
           'unique_src_png': len({v['src_sha256'] for v in kc.values()}),
           'briefs_match_ref_template': all(tmpl), 'note': note}
    json.dump(out, open(f'{A}/builder_ref.json', 'w'), indent=1)
    files = sorted(glob.glob(f'{A}/*.json') + glob.glob(f'{A}/briefs/*') + glob.glob(f'{A}/job_records/*'))
    with open(f'{A}/SHA256SUMS', 'w') as fh:
        for f in files:
            fh.write(f'{sha(f)}  {os.path.relpath(f, A)}\n')
    print(json.dumps({k: out[k] for k in ('n_images', 'n_census', 'n_null', 'n_sessions', 'session_sizes', 'unique_src_png', 'briefs_match_ref_template')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
