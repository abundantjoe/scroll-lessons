# Provenance: Project HERCULES | owner the owner | [id removed]
"""rh-e2 COMMIT A assembler for DECL-P4-3 extended-test batches (p4_ext.py build). Numbers and hashes only; images
are decoded by code for the rot90 recomputation check and never opened for viewing.

usage: commit_a_ext.py <A_dir> <batch> <p2_batch> <cand_uuid> <pool_batches_csv> <command>
"""
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter

sys.path.insert(0, 'src')
RCPT = 'age1vp0tkyj8xecncfmcxj748ceef89mpmwayljccaduapjx3aqhh5rstvvcq5'
CODE = ['tools/p4/p4_ext.py', 'tools/p4/p4_phase2.py', 'tools/p4/p4_jobs.py', 'tools/p4/score_p4.py',
        'src/hercules/harness/audit.py', 'src/hercules/harness/jobs.py', 'src/hercules/display/builder.py',
        'configs/briefs/keysheet_sigma2.png']


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main(A, batch, p2b, cand, pools, command):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    os.makedirs(f'{A}/briefs', exist_ok=True)
    os.makedirs(f'{A}/job_records', exist_ok=True)
    shutil.copyfile(f'/srv/scorer/p4ext_key_{batch}.json', f'{A}/p4ext_key_{batch}.json')
    shutil.copyfile(f'/work/p4/jobs_{batch}.json', f'{A}/jobs_{batch}.json')
    J = json.load(open(f'{A}/jobs_{batch}.json'))
    for j in J['jobs']:
        shutil.copyfile(f"/work/p4/brief_{j['job']}.txt", f"{A}/briefs/brief_{j['job']}.txt")
        shutil.copyfile(f"/work/jobs/{j['job']}.json", f"{A}/job_records/{j['job']}.json")
    k = json.load(open(f'{A}/p4ext_key_{batch}.json'))
    p2 = json.load(open(f'/srv/scorer/p4p2_key_{p2b}.json'))
    imgs = {u: sha(f'/work/p4/img/{u}.png') for u in sorted(k)}
    json.dump(imgs, open(f'{A}/img_manifest.json', 'w'), indent=1)
    rot = lambda u: png_bytes(np.ascontiguousarray(np.rot90(cv2.imread(f'/work/p4/img/{u}.png', cv2.IMREAD_UNCHANGED), k=-1)))
    roles = Counter(v['role'] for v in k.values())
    U = [u for u, v in k.items() if v['role'] == 'U']
    R = [u for u, v in k.items() if v['role'] == 'R']
    assert U == [cand] and len(R) == 1 and p2[cand]['role'] == 'cand' and k[cand]['src'] == p2[cand]['src']
    r_ok = hashlib.sha256(rot(cand)).hexdigest() == imgs[R[0]]
    n0 = {u: v for u, v in k.items() if v['role'] == 'n0'}
    n0_ok = all(hashlib.sha256(rot(v['src'])).hexdigest() == imgs[u] for u, v in n0.items())
    pc_ok = all(imgs[u] == sha(f"/work/p4/img/{v['src']}.png") for u, v in k.items() if v['role'] == 'pc')
    census = {}
    for b in pools.split(','):
        census.update({u: b for u in json.load(open(f'/srv/scorer/p4_key_{b}.json'))})
    sel = json.load(open(json.load(open(f'/work/p4/jobs_{p2b}.json'))['select']))
    excluded = {p2[cand]['src']} | set(sel['pc_pool']) | {v['src'] for v in p2.values() if v['role'] == 'n0'}
    n0_pool_ok = all(v['src'] in census for v in n0.values()) and not any(v['src'] in excluded for v in n0.values())
    per = Counter()
    sess_ok = True
    arms = Counter()
    for r in glob.glob(f'{A}/job_records/*.json'):
        items = [os.path.basename(p)[:-4] for p in json.load(open(r))['images'][1:]]
        c = Counter(k[u]['role'] for u in items)
        sess_ok &= (c['n0'] == 8 and c['pc'] == 1 and c['U'] + c['R'] == 1 and len(set(items)) == len(items))
        arms['U' if c['U'] else 'R'] += 1
        per.update(u for u in items if k[u]['role'] == 'n0')
    n0_three = all(per[u] == 3 for u in n0)
    norm = lambda b: re.sub(r'/work/p4/img/[0-9a-f-]+\.png\n', '', re.sub(r'/work/sealed_io/[0-9a-f-]+\.age', 'X', b))
    ref = norm(open(f"logs/p4/ref_brief_{J['variant']}.txt").read())
    tmpl = all(norm(open(f).read()) == ref for f in glob.glob(f'{A}/briefs/*.txt'))
    out = {'batch': batch, 'declaration': 'RULES.md DECL-P4-25-A2 item 1; DECL-P4-3 unchanged', 'command': command,
           'p2_batch': p2b, 'candidate_file': cand, 'candidate_source': p2[cand]['src'],
           'candidate_strip_rc': [p2[cand]['strip'], p2[cand]['r'], p2[cand]['c']],
           'orchestrator_base_commit': subprocess.check_output(['git', 'rev-parse', 'origin/claude/gifted-bell-gavnl5'], text=True).strip(),
           'variant': J['variant'], 'n0_seed': J['n0_seed'], 'n0_pool_batches': pools.split(','),
           'n0_by_batch': dict(Counter(census[v['src']] for v in n0.values())),
           'n0_from_all_zero_tiles': sum(json.load(open(f"/srv/scorer/p4_key_{census[v['src']]}.json"))[v['src']]['src_sha256'].startswith('3308991ca1d6') for v in n0.values()),
           'recipient': RCPT, 'key_sha256': {f'p4ext_key_{batch}.json': sha(f'/srv/scorer/p4ext_key_{batch}.json')},
           'code_sha256': {p: sha(p) for p in CODE + [f"configs/briefs/k_d2_task_{J['variant']}.txt", f"logs/p4/ref_brief_{J['variant']}.txt"]},
           'pc_pool_manifest_sha256': sha('logs/p4/pc_pool_m1/manifest.json'),
           'roles': dict(roles), 'arms': dict(arms), 'n_sessions': len(J['jobs']), 'n_images': len(imgs),
           'checks': {'R_equals_rot90_U': r_ok, 'n0_equal_rot90_src': n0_ok, 'pc_copies_identical': pc_ok,
                      'n0_from_pool_batches_and_not_excluded': n0_pool_ok, 'sessions_8n0_1pc_1arm_no_dup': sess_ok,
                      'each_n0_in_3_sessions': n0_three, 'briefs_match_ref_template': tmpl}}
    assert all(out['checks'].values()), out['checks']
    json.dump(out, open(f'{A}/builder_ref.json', 'w'), indent=1)
    files = sorted(glob.glob(f'{A}/*.json') + glob.glob(f'{A}/briefs/*') + glob.glob(f'{A}/job_records/*'))
    open(f'{A}/SHA256SUMS', 'w').write(''.join(f'{sha(f)}  {os.path.relpath(f, A)}\n' for f in files))
    print(json.dumps({x: out[x] for x in ('batch', 'roles', 'arms', 'n0_by_batch', 'n0_from_all_zero_tiles', 'checks')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
