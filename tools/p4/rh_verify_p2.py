# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent verification and installation of a remote-harness PHASE-2 batch (RULES.md DECL-REMOTE-HARNESS-1
items 4-7 applied to DECL-P4-2 item 6 / DECL-P4-25-A1). Booleans and counts only; no letter content is printed.

usage: rh_verify_p2.py <harness_ref> <A dir> <B dir> <batch> <select.json (orchestrator's)> <pc_manifest.json>
       <pool_batches comma> <inner_ref> <out_json> [--install]

Checks (all must hold, else VOID and nothing is installed):
  A0 builder_ref code_sha256 == local files (or a DECLARED version from rh_verify.py);
  A1 the commit first adding <A>/SHA256SUMS precedes the one first adding <B>/SHA256SUMS;
  A2 A/SHA256SUMS matches every A file; key sha == builder_ref key_sha256;
  K1 cand entries: src set == the orchestrator select's candidate uuids, (strip, r, c) equal; each image sha ==
     the census key src_sha256 of its src;
  K2 n0 entries == the deterministic draw of p4_phase2.cmd_build (census rot-0 tiles of the pool batches' keys in
     /srv/scorer, minus candidates and PC pool, random.Random(NULL_SEED + _bidx(batch)).sample); each image sha ==
     sha of png_bytes(rot90(source tile, k=-1)), the source tile fetched from <inner_ref> and sha-checked against
     the census key;
  K3 pc entries: src in the PC pool; image sha == the PC manifest sha;
  J  every job: images == keysheet + its items; items = <=4 cand + 4 n0 + 1 pc; every cand and n0 file in exactly
     3 jobs, each pc file in exactly 1; brief template == the expected p4_phase2 brief template for the variant;
     brief sha == job record;
  B1-B3 as rh_verify.py (age hashes, transcript audit VALID + prompt == brief + after commit A, answer consistency).
--install: key -> /srv/scorer/p4p2_key_<batch>.json (O_EXCL 0400), .age -> /work/sealed_io/, job records ->
/work/jobs/, jobs json -> /work/p4/jobs_<batch>.json.
"""
import gzip
import hashlib
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, 'src')
sys.path.insert(0, 'tools/p4')
from rh_verify import (DECLARED, PROV, RCPT, first_commit_time, ls, norm_brief, sha, show, sums,  # noqa: E402
                       transcript_checks)

[line withheld: prize-candidate detail under review]
[line withheld: prize-candidate detail under review]


def main(ref, A, B, batch, sel_f, pcm_f, pools, inner_ref, out, install=False):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    from hercules.harness.audit import audit
    from hercules.harness.jobs import HEADER, RECIPIENT_FILE
    from hercules.scorer.keyaccess import decrypt_answer_logged
    import p4_phase2
    from p4_jobs import task_variant
    ck, res = {}, {'provenance': PROV, 'serves': 'DECL-REMOTE-HARNESS-1 items 4-7 for phase-2 batch ' + batch,
                   'ref': ref, 'jobs': {}}
    res['ref_commit'] = os.popen(f'git rev-parse {ref}').read().strip()
    bref = json.loads(show(ref, f'{A}/builder_ref.json'))
    ck['A0_code_hashes'] = all(sha(open(f, 'rb').read()) == h or h in DECLARED.get(f, ())
                               for f, h in bref['code_sha256'].items())
    ta, tb = first_commit_time(ref, f'{A}/SHA256SUMS'), first_commit_time(ref, f'{B}/SHA256SUMS')
    t_a = datetime.fromisoformat(ta[1])
    ck['A1_A_before_B'] = bool(ta and tb) and t_a < datetime.fromisoformat(tb[1])
    sa = sums(show(ref, f'{A}/SHA256SUMS'))
    ck['A2_sums'] = all(sa.get(os.path.basename(p)) == sha(show(ref, p, True)) for p in ls(ref, A)
                        if not p.endswith('SHA256SUMS') and os.path.basename(p) in sa) and len(sa) > 0
    key_b = show(ref, f'{A}/p4p2_key_{batch}.json', True)
    key = json.loads(key_b)
    ck['A2_key_sha'] = sha(key_b) == bref['key_sha256'][f'p4p2_key_{batch}.json']
    img = json.loads(show(ref, f'{A}/img_manifest.json'))
    sel = json.load(open(sel_f))
    pcm = json.load(open(pcm_f))['sha256']
    ckeys = {b: json.load(open(f'/srv/scorer/p4_key_{b}.json')) for b in pools.split(',')}
    allc = {u: v for k in ckeys.values() for u, v in k.items()}
    # K1
    cands = {u: v for u, v in key.items() if v['role'] == 'cand'}
    want = {d['uuid']: d for d in sel['candidates']}
    ck['K1_cand_set'] = sorted(v['src'] for v in cands.values()) == sorted(want) and all(
        (v['strip'], v['r'], v['c']) == (want[v['src']]['strip'], want[v['src']]['r'], want[v['src']]['c'])
        for v in cands.values())
    ck['K1_cand_img'] = all(img.get(u) == allc[v['src']]['src_sha256'] for u, v in cands.items())
    # K2: recompute the draw exactly as p4_phase2.cmd_build
    pool = list(json.load(open(sel_f))['pc_pool']['uuids'])
    excluded = set(want) | set(pool)
    census = sorted((u, v) for k in ckeys.values() for u, v in k.items() if v['rot'] == 0 and u not in excluded)
    seed = p4_phase2.NULL_SEED + p4_phase2._bidx(batch)
    draw = random.Random(seed).sample(census, p4_phase2.GROUP * -(-len(want) // p4_phase2.GROUP))
    n0 = {u: v for u, v in key.items() if v['role'] == 'n0'}
    ck['K2_n0_draw'] = sorted(v['src'] for v in n0.values()) == sorted(u for u, _ in draw) and all(v['rot'] == 90 for v in n0.values())
    res['n0_seed'] = seed
    k2img = True
    for u, v in n0.items():
        s = allc[v['src']]
        w = s['strip'].split('-', 1)[1]
        pb = show(inner_ref, f"{INNER[w]}_r{s['r']}_c{s['c']}.png", True)
        a = cv2.imdecode(np.frombuffer(pb, np.uint8), cv2.IMREAD_UNCHANGED)
        k2img &= sha(pb) == s['src_sha256'] and img.get(u) == sha(png_bytes(np.ascontiguousarray(np.rot90(a, k=-1))))
    ck['K2_n0_img'] = k2img
    # K3
    pcs = {u: v for u, v in key.items() if v['role'] == 'pc'}
    ck['K3_pc'] = all(v['src'] in pool and img.get(u) == pcm[v['src']] for u, v in pcs.items())
    ck['K_roles'] = len(key) == len(cands) + len(n0) + len(pcs)
    # J
    jobs_b = show(ref, f'{A}/jobs_{batch}.json', True)
    jobs = json.loads(jobs_b)
    ks, _, single, _ = task_variant(jobs['variant'])
    ref_brief = HEADER.format(role='reader', images='\n'.join([ks] + ['/work/p4/img/x.png'] * 9),
                              rcpt=open(RECIPIENT_FILE, encoding='ascii').read().strip(),
                              out='/work/sealed_io/00000000-0000-0000-0000-000000000000.age') + open(single, encoding='utf-8').read()
    tmpl = norm_brief(ref_brief)
    cnt = {u: 0 for u in key}
    j_ok = True
    for j in jobs['jobs']:
        job = j['job']
        brief = show(ref, f'{A}/briefs/brief_{job}.txt')
        recj = json.loads(show(ref, f'{A}/job_records/{job}.json'))
        items = [os.path.basename(p)[:-4] for p in recj['images'][1:]]
        for u in items:
            cnt[u] = cnt.get(u, 0) + 1
        roles = [key.get(u, {}).get('role') for u in items]
        ok = (norm_brief(brief) == tmpl and sha(brief.encode()) == recj['brief_sha256'] and recj['images'][0] == ks
              and roles.count('cand') <= 4 and roles.count('n0') == 4 and roles.count('pc') == 1 and None not in roles
              and recj['out'] == f'/work/sealed_io/{job}.age' and recj['recipient'] == RCPT
              and len(recj['images']) == j['n_images'])
        res['jobs'][job] = {'brief_ok': ok}
        j_ok &= ok
    ck['J_jobs'] = j_ok
    ck['J_cover'] = all(cnt[u] == 3 for u in list(cands) + list(n0)) and all(cnt[u] == 1 for u in pcs)
    # B1-B3
    sb = sums(show(ref, f'{B}/SHA256SUMS'))
    aud = {x['job']: x for x in json.loads(show(ref, f'{B}/audit.json')) if x.get('valid')}
    tmp = '/dev/shm/rh_verify_p2'
    os.makedirs(tmp, exist_ok=True)
    b1 = b2 = b3 = True
    for j in jobs['jobs']:
        job = j['job']
        r = res['jobs'][job]
        agef = [p for p in ls(ref, B) if p.endswith(f'{job}.age')]
        age = show(ref, agef[0], True) if agef else b''
        r['age_sha256'] = sha(age)
        r['B1'] = bool(age) and sb.get(f'{job}.age') == sha(age) and aud.get(job, {}).get('answer_sha256') == sha(age)
        brief = show(ref, f'{A}/briefs/brief_{job}.txt')
        recj = json.loads(show(ref, f'{A}/job_records/{job}.json'))
        tr = gzip.decompress(show(ref, f'{B}/transcripts/{job}.jsonl.gz', True))
        tp = f'{tmp}/{job}.jsonl'
        open(tp, 'wb').write(tr)
        au = audit(tp, recj['images'], sealed_output=recj['out'], recipient=RCPT)
        eq, times, body = transcript_checks(tr, brief)
        t_ok = bool(times) and min(datetime.fromisoformat(t.replace('Z', '+00:00')) for t in times) > t_a
        r['B2'] = {'audit_valid': au['valid'], 'n_violations': len(au['violations']), 'unread': len(au['unread_images']),
                   'prompt_eq_brief': eq, 'after_commit_A': t_ok, 'transcript_sha256': sha(tr)}
        b1 &= r['B1']
        b2 &= au['valid'] and eq and t_ok
        ap = f'{tmp}/{job}.age'
        open(ap, 'wb').write(age)
        try:
            same = body is not None and json.loads(body) == decrypt_answer_logged(ap, 'rh-verify-p2-consistency')
        except Exception:
            same = False
        r['B3_consistent'] = same
        b3 &= same
        os.remove(tp)
        os.remove(ap)
    ck['B1_age_hashes'], ck['B2_transcripts'], ck['B3_answer_consistency'] = b1, b2, b3
    res['checks'] = ck
    res['n'] = {'cand': len(cands), 'n0': len(n0), 'pc': len(pcs), 'jobs': len(jobs['jobs'])}
    res['PASS'] = all(ck.values())
    if install and res['PASS']:
        fd = os.open(f'/srv/scorer/p4p2_key_{batch}.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        with os.fdopen(fd, 'wb') as fh:
            fh.write(key_b)
        for j in jobs['jobs']:
            job = j['job']
            agef = [p for p in ls(ref, B) if p.endswith(f'{job}.age')][0]
            with open(f'/work/sealed_io/{job}.age', 'xb') as fh:
                fh.write(show(ref, agef, True))
            recj = json.loads(show(ref, f'{A}/job_records/{job}.json'))
            b2j = res['jobs'][job]['B2']
            recj.update({'valid': b2j['audit_valid'] and b2j['prompt_eq_brief'], 'answer_sha256': res['jobs'][job]['age_sha256'],
                         'verified_by': 'tools/p4/rh_verify_p2.py', 'harness_ref': res['ref_commit']})
            with open(f'/work/jobs/{job}.json', 'x') as fh:
                json.dump(recj, fh, indent=1)
        with open(f'/work/p4/jobs_{batch}.json', 'xb') as fh:
            fh.write(jobs_b)
        res['installed'] = True
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({'PASS': res['PASS'], 'checks': ck, 'n': res['n'], 'installed': res.get('installed', False)}))


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    main(*a, install='--install' in sys.argv)
