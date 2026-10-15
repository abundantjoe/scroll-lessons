# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent verification and installation of a P4-OWN G1 remote-harness batch (RULES.md DECL-REMOTE-HARNESS-1,
DECL-P4-23 item 6(b), DECL-P4-23-A1/-A2, METRIC-HASH-48). Booleans and counts only; no letter content is printed.

usage: rh_verify_own.py <rh_ref> <Adir> <Bdir> <fold> <ARM> <own_ref> <out_json> [--install]
  fold f1|f2|f3, ARM F1|F2|F3. Batches (rh-e1 prep_own.sh): census keys own_<fold>a (w028-037) and own_<fold>b
  (w010-027; either may be absent when it has 0 eligible tiles), N0 n_own_<fold>, job sets census_own_<fold>
  (sigma2t) and census_own_<fold>k (block) over the same keys. Files are looked up anywhere below Adir / Bdir.

Checks (all must hold, else the batch is VOID and nothing is installed):
  C0 code: prep_own.sh and own_split.py at <rh_ref> == METRIC-HASH-48; tools/p4/{p4_jobs,norm_manifest}.py at
     <rh_ref> == the local files; own-lead run_arms.py at <own_ref> == METRIC-HASH-48;
  A1 the commit first adding Adir precedes (is an ancestor of, and differs from) the commit first adding Bdir;
  A2 key shapes: census rot 0 with segment == strip == the batch's segment; N0 rot 90 with null_of in the census;
     keys.sha256 in Adir (if present) matches;
  K1 own-lead manifest at <own_ref>: arm == ARM; model_final_sha256 and train_manifest_sha256 == the arm's
     train/summary.json; tile set == the RECIPE.md (6b5bdc5) '<ARM> held-out tiles' list (24 tiles, every tile once);
     Adir records own_ref (split.json own_ref or builder json) == <own_ref>;
  K2 key census set == manifest tiles with valid_fraction >= 0.5, src_sha256 == png_sha256 == sha256 of the PNG
     bytes at <own_ref>;
  K3 N0 draw recomputed: random.Random(20260926 + bidx('n_own_<fold>')).sample(sorted census, ceil(n/8)) == the
     null_of set; every N0 image recomputed byte-exactly (png_bytes(np.rot90(tile, k=-1)));
  A3 img_manifest: every census uuid sha == src_sha256; every N0 uuid sha == its recomputed sha;
  A5 per job set: jobs json variant (sigma2t | block), census_batches == the key batches, null_batch == n_own_<fold>;
     every brief == logs/p4/ref_brief_<variant>.txt after normalisation; images == job record; keysheet first;
     counts; each job set covers every census tile once and every N0 tile once;
  B1 exactly one .age per job; sha256 == audit answer_sha256 (and B SHA256SUMS where listed);
  B2 exactly one transcript per job; local audit VALID; first user message == brief; all timestamps after commit A;
  B3 the decrypted answer equals the transcript's sealed heredoc body (purpose 'rh-verify-consistency', logged).
--install (only if all pass): keys -> /srv/scorer (O_EXCL, 0400), .age -> /work/sealed_io/, job records (valid from
B2) -> /work/jobs/, jobs json -> /work/p4/jobs_<jobset>.json.
"""
import gzip
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, 'src')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rh_verify import (PROV, RCPT, brief_images, first_commit_time, ls, norm_brief, sha, show, sums,  # noqa: E402
                       transcript_checks)

MH48 = {'tools/sib/rh-e1/prep_own.sh': 'f30807ac49bdd589d782813ac51ac48a8a5350691f9fbe4cdc2b33908d3e9fa3',
        # METRIC-HASH-50: 626cdbb4... with its 3 'heldout_maps' paths corrected to 'maps' (nothing else changed)
        'tools/sib/rh-e1/own_split.py': 'b400e9a4e0d80df0fa07ba986fc6189d216f278372bb61ac7d814a0c67cf39f4'}
RUN_ARMS = ('tools/sib/own-lead/run_arms.py', {  # scheduling-only versions, each reviewed and pinned
    '07633449969a8f889898d447edc29b8d270278334749eba24f5aa1e084f19980',  # METRIC-HASH-48
    '2722d3ac53319d76d7f735ca84cf21d91fb5cdc04e0954cafe3357dc8be01a8c',  # METRIC-HASH-50 (own-lead 15debde6)
    '1d8f83efc956ab4180924b8a4c13f4ebfc73dc5ba662fcad79dc355e3788d1f8'})  # METRIC-HASH-51 (own-lead 484025e2)
MAPS = 'maps'  # METRIC-HASH-50: run_arms.py writes F-arm held-out maps to logs/sib/own-<fold>/maps/
RECIPE = ('6b5bdc5', 'logs/sib/own-lead/p4own/RECIPE.md')
SEGS = {'a': '20260701183125-w028-037', 'b': '20260701183124-w010-027'}
NULL_SEED, PER_SESSION = 20260926, 8


def recipe_list(arm):
    txt = show(RECIPE[0], RECIPE[1])
    line = [ln for ln in txt.splitlines() if re.match(rf'^- {arm} held-out tiles \(\d+\):', ln)]
    assert len(line) == 1
    items = [x.strip() for x in line[0].split('):', 1)[1].split(';') if x.strip()]
    out = []
    for it in items:
        s, rc = it.split(':')
        r, c = rc.split(',')
        out.append((s.strip(), int(r), int(c)))
    return out


def find(ref, root, suffix):
    return [p for p in ls(ref, root) if p.endswith(suffix)]


def main(ref, A, B, fold, arm, own_ref, out, install=False):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    from hercules.harness.audit import audit
    from hercules.scorer.keyaccess import decrypt_answer_logged
    own = subprocess.run(['git', 'rev-parse', own_ref], capture_output=True, text=True, check=True).stdout.strip()
    res = {'provenance': PROV, 'serves': 'DECL-REMOTE-HARNESS-1; DECL-P4-23 6(b), -A1, -A2; METRIC-HASH-48',
           'ref': ref, 'ref_commit': subprocess.run(['git', 'rev-parse', ref], capture_output=True,
                                                    text=True).stdout.strip(),
           'fold': fold, 'arm': arm, 'own_ref': own, 'checks': {}, 'jobs': {}}
    ck = res['checks']
    nb, js = f'n_own_{fold}', {'sigma2t': f'census_own_{fold}', 'block': f'census_own_{fold}k'}
    # C0 code
    c0 = {p: sha(show(ref, p, True)) == h for p, h in MH48.items()}
    for p in ('tools/p4/p4_jobs.py', 'tools/p4/norm_manifest.py'):
        c0[p] = sha(show(ref, p, True)) == sha(open(p, 'rb').read())
    c0[RUN_ARMS[0]] = sha(show(own, RUN_ARMS[0], True)) in RUN_ARMS[1]
    res['C0'] = c0
    ck['C0_code'] = all(c0.values())
    # A1 order
    a_first, b_first = first_commit_time(ref, A), first_commit_time(ref, B)
    anc = bool(a_first and b_first) and subprocess.run(['git', 'merge-base', '--is-ancestor', a_first[0],
                                                        b_first[0]]).returncode == 0
    ck['A1_A_before_B'] = anc and a_first[0] != b_first[0]
    res['commit_A'], res['commit_B'] = a_first, b_first
    t_a = datetime.fromisoformat(a_first[1])
    # A2 keys
    keys, raw_keys = {}, {}
    for x in ('a', 'b'):
        f = find(ref, A, f'/p4_key_own_{fold}{x}.json')
        if f:
            raw_keys[f'own_{fold}{x}'] = show(ref, f[0], True)
            keys[f'own_{fold}{x}'] = json.loads(raw_keys[f'own_{fold}{x}'])
    fn = find(ref, A, f'/p4_key_{nb}.json')
    raw_keys[nb] = show(ref, fn[0], True) if len(fn) == 1 else b'{}'
    kn = json.loads(raw_keys[nb])
    kc = {u: v for b, k in keys.items() if b != nb for u, v in k.items()}
    shape = all(v['rot'] == 0 and v['segment'] == v['strip'] == SEGS[b[-1]] for b, k in keys.items()
                for v in k.values())
    shape = shape and bool(kn) and all(v['rot'] == 90 and v.get('null_of') in kc for v in kn.values())
    ksum = find(ref, A, 'keys.sha256')
    sums_ok = True
    for kf in ksum:
        s = sums(show(ref, kf))
        sums_ok = sums_ok and all(s.get(f'p4_key_{b}.json') in (None, sha(r)) for b, r in raw_keys.items())
    ck['A2_keys'] = shape and sums_ok and len(fn) == 1
    res['key_sha256'] = {b: sha(r) for b, r in raw_keys.items()}
    # K1 manifest vs recipe and training summary
    man = json.loads(show(own, f'logs/sib/own-{fold}/{MAPS}/manifest.json'))
    summ = json.loads(show(own, f'logs/sib/own-{fold}/train/summary.json'))
    rl = recipe_list(arm)
    short = {s: re.search(r'(w\d{3}-\d{3})$', s).group(1) for s in SEGS.values()}
    mset = [(short[t['seg']], t['r'], t['c']) for t in man['tiles']]
    recs = [x for x in find(ref, A, '.json') if x.endswith('split.json') or x.endswith('builder.json')
            or x.endswith('builder_ref.json')]
    refs_rec = set()
    for p in recs:
        d = json.loads(show(ref, p))
        for k in ('own_ref', 'builder_commit', 'builder_ref'):
            if isinstance(d.get(k), str) and re.fullmatch(r'[0-9a-f]{40}', d[k]):
                refs_rec.add(d[k])
    k1 = {'arm': man.get('arm') == arm == summ.get('arm'),
          'model_sha': man.get('model_final_sha256') == summ.get('model_final_sha256')
          and all(t.get('model_final_sha256') == summ['model_final_sha256'] for t in man['tiles']),
          'train_manifest_sha': man.get('train_manifest_sha256') == summ.get('train_manifest_sha256'),
          'recipe_set': len(rl) == 24 and len(set(rl)) == 24 and sorted(mset) == sorted(rl),
          'own_ref_recorded': refs_rec == {own}}
    res['K1'] = k1
    ck['K1_manifest'] = all(k1.values())
    # K2 eligible set and bytes
    elig, pngs = {}, {}
    for t in man['tiles']:
        name = f"{t['seg']}_r{t['r']}_c{t['c']}"
        b = show(own, f'logs/sib/own-{fold}/{MAPS}/tiles/{name}.png', True)
        pngs[(t['seg'], t['r'], t['c'])] = b
        if t.get('valid_fraction', 0) >= 0.5:
            elig[(t['seg'], t['r'], t['c'])] = t['png_sha256']
    res['ineligible_tiles'] = sorted(f"{short[t['seg']]}_r{t['r']}_c{t['c']}" for t in man['tiles']
                                     if t.get('valid_fraction', 0) < 0.5)
    keyset = {(v['segment'], v['r'], v['c']): v['src_sha256'] for v in kc.values()}
    ck['K2_eligible_bytes'] = (keyset == elig and len(keyset) == len(kc)
                               and all(sha(pngs[k]) == h for k, h in elig.items()))
    # K3 N0 draw and bytes
    n_c = len(kc)
    bidx = int(hashlib.sha256(nb.encode()).hexdigest()[:8], 16) % 100000
    draw = random.Random(NULL_SEED + bidx).sample(sorted(kc.items()), math.ceil(n_c / PER_SESSION))
    k3 = sorted(u for u, _ in draw) == sorted(v['null_of'] for v in kn.values())
    null_sha = {}
    for u, v in kn.items():
        src = kc[v['null_of']]
        a = cv2.imdecode(np.frombuffer(pngs[(src['segment'], src['r'], src['c'])], np.uint8), cv2.IMREAD_UNCHANGED)
        k3 = k3 and a is not None and a.dtype == np.uint8 and a.ndim == 2
        null_sha[u] = sha(png_bytes(np.ascontiguousarray(np.rot90(a, k=-1))))
        k3 = k3 and {kk: vv for kk, vv in v.items() if kk not in ('rot', 'null_of')} == \
            {kk: vv for kk, vv in src.items() if kk != 'rot'}
    ck['K3_null_draw'] = k3
    res['n_census'], res['n_null'], res['null_seed'] = n_c, len(kn), NULL_SEED + bidx
    # A3 img manifest
    imf = find(ref, A, 'img_manifest.json')
    img = {}
    for p in imf:
        d = json.loads(show(ref, p))
        d = d.get('images', d) if isinstance(d, dict) else d
        if isinstance(d, list):
            d = {os.path.basename(x.get('file', x.get('uuid', '')))[:36]: x.get('sha256') for x in d}
        img.update({k[:36]: v for k, v in d.items()})
    ck['A3_img'] = bool(imf) and all(img.get(u) == v['src_sha256'] for u, v in kc.items()) and \
        all(img.get(u) == h for u, h in null_sha.items())
    # A5 briefs and cover, per job set
    a5, cover, alljobs = True, True, []
    raw_jobs = {}
    for variant, jb in js.items():
        jf = find(ref, A, f'/jobs_{jb}.json')
        if len(jf) != 1:
            a5 = False
            continue
        raw_jobs[jb] = show(ref, jf[0], True)
        jobs = json.loads(raw_jobs[jb])
        a5 = a5 and jobs.get('variant') == variant and sorted(jobs.get('census_batches', [])) == \
            sorted(b for b in keys) and jobs.get('null_batch') == nb
        refn = norm_brief(open(f'logs/p4/ref_brief_{variant}.txt').read())
        seen_c, seen_n = [], []
        for j in jobs['jobs']:
            job = j['job']
            bf, rf = find(ref, A, f'/brief_{job}.txt'), find(ref, A, f'/{job}.json')
            if len(bf) != 1 or len(rf) != 1:
                a5 = False
                continue
            brief, recj = show(ref, bf[0]), json.loads(show(ref, rf[0]))
            ims = brief_images(brief)
            ok = norm_brief(brief) == refn and ims == recj['images'] and ims[0].endswith('keysheet_sigma2.png') \
                and sha(brief.encode()) == recj['brief_sha256'] and recj['out'] == f'/work/sealed_io/{job}.age' \
                and recj['recipient'] == RCPT and len(ims) == j['n_images'] == 1 + j['n_census'] + j['n_null'] \
                and j['n_census'] <= PER_SESSION and j['n_null'] == 1 and j.get('model') == 'opus'
            for p in ims[1:]:
                u = os.path.basename(p)[:-4]
                (seen_n if u in kn else seen_c).append(u)
            a5 = a5 and ok
            res['jobs'][job] = {'jobset': jb, 'brief_ok': ok, 'brief_sha256': recj['brief_sha256']}
            alljobs.append((jb, job, brief, recj))
        cover = cover and sorted(seen_c) == sorted(kc) and sorted(seen_n) == sorted(kn)
    ck['A5_briefs'], ck['A5_cover'] = a5, cover
    # B
    sb = {}
    for p in find(ref, B, 'SHA256SUMS'):
        sb.update(sums(show(ref, p)))
    aud = {}
    for p in find(ref, B, 'audit.json'):
        for x in json.loads(show(ref, p)):
            if x.get('valid'):
                aud[x['job']] = x
    tmp = '/dev/shm/rh_verify_own'
    os.makedirs(tmp, exist_ok=True)
    b1 = b2 = b3 = bool(alljobs)
    for jb, job, brief, recj in alljobs:
        r = res['jobs'][job]
        agef = find(ref, B, f'/{job}.age')
        trf = [p for p in ls(ref, B) if re.search(rf'/{job}(\.\d+)?\.jsonl\.gz$', p)]
        age = show(ref, agef[0], True) if len(agef) == 1 else b''
        r['age_sha256'] = sha(age)
        r['B1'] = len(agef) == 1 and bool(age) and sb.get(f'{job}.age', sha(age)) == sha(age) and \
            aud.get(job, {}).get('answer_sha256') == sha(age)
        if len(trf) != 1:
            r['B2'] = {'n_transcripts': len(trf)}
            b1, b2, b3 = b1 and r['B1'], False, False
            continue
        tr = gzip.decompress(show(ref, trf[0], True))
        tp = f'{tmp}/{job}.jsonl'
        open(tp, 'wb').write(tr)
        au = audit(tp, recj['images'], sealed_output=recj['out'], recipient=RCPT)
        eq, times, body = transcript_checks(tr, brief)
        t_ok = bool(times) and min(datetime.fromisoformat(t.replace('Z', '+00:00')) for t in times) > t_a
        r['B2'] = {'audit_valid': au['valid'], 'n_violations': len(au['violations']),
                   'unread': len(au['unread_images']), 'prompt_eq_brief': eq, 'after_commit_A': t_ok,
                   'transcript_sha256': sha(tr)}
        ap = f'{tmp}/{job}.age'
        open(ap, 'wb').write(age)
        try:
            dec = decrypt_answer_logged(ap, 'rh-verify-consistency')
            same = body is not None and json.loads(body) == dec
        except Exception:
            same = False
        r['B3_consistent'] = same
        b1, b2, b3 = b1 and r['B1'], b2 and au['valid'] and eq and t_ok, b3 and same
        os.remove(tp)
        os.remove(ap)
    ck['B1_age_hashes'], ck['B2_transcripts'], ck['B3_answer_consistency'] = b1, b2, b3
    res['PASS'] = all(ck.values())
    if install and res['PASS']:
        for b, raw in raw_keys.items():
            fd = os.open(f'/srv/scorer/p4_key_{b}.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
            with os.fdopen(fd, 'wb') as fh:
                fh.write(raw)
        for jb, job, brief, recj in alljobs:
            with open(f'/work/sealed_io/{job}.age', 'xb') as fh:
                fh.write(show(ref, find(ref, B, f'/{job}.age')[0], True))
            b2j = res['jobs'][job]['B2']
            recj = dict(recj, valid=b2j['audit_valid'] and b2j['prompt_eq_brief'],
                        answer_sha256=res['jobs'][job]['age_sha256'], verified_by='tools/p4/rh_verify_own.py',
                        harness_ref=res['ref_commit'])
            with open(f'/work/jobs/{job}.json', 'x') as fh:
                json.dump(recj, fh, indent=1)
        for jb, raw in raw_jobs.items():
            with open(f'/work/p4/jobs_{jb}.json', 'xb') as fh:
                fh.write(raw)
        res['installed'] = True
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({'PASS': res['PASS'], 'checks': ck, 'n_census': n_c, 'n_null': len(kn),
                      'ineligible': res['ineligible_tiles'], 'installed': res.get('installed', False)}))


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    main(*a, install='--install' in sys.argv)
