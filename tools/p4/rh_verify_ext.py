# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent verification and installation of a remote-harness EXTENDED-TEST batch (RULES.md DECL-P4-3,
DECL-REMOTE-HARNESS-1 items 4-7; DECL-P4-25-A2). Booleans and counts only; no letter content is printed.

usage: rh_verify_ext.py <harness_ref> <A dir> <B dir> <batch> <p2_batch> <strip> <r> <c> <select.json (orchestrator's)>
       <pc_manifest.json> <pool_batches comma> <inner_ref> <out_json> [--install]

Checks (all must hold, else VOID and nothing is installed):
  A0 builder_ref code_sha256 == local files (or a DECLARED version); A1 commit A precedes commit B;
  A2 A/SHA256SUMS matches every listed A file; key sha == builder_ref key_sha256;
  E1 exactly one U entry: it is the installed phase-2 key's cand file whose src is (strip, r, c); its image sha == the
     census key src_sha256 of that src;
  E2 exactly one R entry: image sha == sha of png_bytes(rot90(U image, k=-1)); the U image is the source tile fetched
     from <inner_ref> and sha-checked against the census key;
  E3 the N0 set == the deterministic p4_ext.cmd_build draw (rot-0 census tiles of the pool batches' keys in
     /srv/scorer, minus the candidate source, the PC pool and the phase-2 N0 sources; random.Random(SEED +
     _bidx(batch)).sample(N_N0)); each N0 image == png_bytes(rot90(source tile)) with the source sha-checked;
  E4 PC entries: src in the PC pool; image sha == the PC manifest sha;
  J  18 jobs: each holds exactly one of U or R (9 each; 'arm' agrees), 8 N0 and 1 PC; each N0 tile in exactly 3
     jobs and never twice in one; each PC file in 1 job; brief template == the expected template; brief sha ==
     job record;
  B1-B3 as rh_verify.py.
  R2 (v2, METRIC-HASH-44) re-run of a void session: if <B>/age/<job>.age is absent, <job>.r2.age may stand in, ONLY if
     the attempt-1 audit entry is invalid with age_exists False, the attempt-1 transcript is present and has no sealed
     write, and the attempt-2 audit entry is valid; B1-B3 then apply to <job>.r2 (its transcript's first prompt must
     equal the commit-A brief, and its timestamps must follow commit A). At most one re-run per job.
--install: key -> /srv/scorer/p4ext_key_<batch>.json (O_EXCL 0400), .age -> /work/sealed_io/, job records ->
/work/jobs/, jobs json -> /work/p4/jobs_<batch>.json.
"""
import gzip
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, 'src')
sys.path.insert(0, 'tools/p4')
from rh_verify import (DECLARED, PROV, RCPT, first_commit_time, ls, norm_brief, sha, show, sums,  # noqa: E402
                       transcript_checks)
from rh_verify_p2 import INNER  # noqa: E402


def main(ref, A, B, batch, p2b, strip, r, c, sel_f, pcm_f, pools, inner_ref, out, install=False):
    import cv2
    import numpy as np
    from hercules.display.builder import png_bytes
    from hercules.harness.audit import audit
    from hercules.harness.jobs import HEADER, RECIPIENT_FILE
    from hercules.scorer.keyaccess import decrypt_answer_logged
    import p4_ext
    from p4_phase2 import _bidx
    from p4_jobs import task_variant
    r, c = int(r), int(c)
    ck, res = {}, {'provenance': PROV, 'serves': 'DECL-P4-3 / DECL-REMOTE-HARNESS-1 for extended batch ' + batch,
                   'ref': ref, 'ref_commit': os.popen(f'git rev-parse {ref}').read().strip(), 'jobs': {}}
    bref = json.loads(show(ref, f'{A}/builder_ref.json'))
    ck['A0_code_hashes'] = all(sha(open(f, 'rb').read()) == h or h in DECLARED.get(f, ())
                               for f, h in bref['code_sha256'].items())
    ta, tb = first_commit_time(ref, f'{A}/SHA256SUMS'), first_commit_time(ref, f'{B}/SHA256SUMS')
    t_a = datetime.fromisoformat(ta[1])
    ck['A1_A_before_B'] = bool(ta and tb) and t_a < datetime.fromisoformat(tb[1])
    sa = sums(show(ref, f'{A}/SHA256SUMS'))
    ck['A2_sums'] = len(sa) > 0 and all(sa.get(os.path.basename(p)) == sha(show(ref, p, True)) for p in ls(ref, A)
                                        if os.path.basename(p) in sa)
    key_b = show(ref, f'{A}/p4ext_key_{batch}.json', True)
    key = json.loads(key_b)
    ck['A2_key_sha'] = sha(key_b) == bref['key_sha256'][f'p4ext_key_{batch}.json']
    img = json.loads(show(ref, f'{A}/img_manifest.json'))
    p2 = json.load(open(f'/srv/scorer/p4p2_key_{p2b}.json'))
    pool = list(json.load(open(sel_f))['pc_pool']['uuids'])
    pcm = json.load(open(pcm_f))['sha256']
    ckeys = {b: json.load(open(f'/srv/scorer/p4_key_{b}.json')) for b in pools.split(',')}
    allc = {u: v for k in ckeys.values() for u, v in k.items()}

    def src_tile(src_uuid):
        s = allc[src_uuid]
        pb = show(inner_ref, f"{INNER[s['strip'].split('-', 1)[1]]}_r{s['r']}_c{s['c']}.png", True)
        assert sha(pb) == s['src_sha256'], src_uuid
        return cv2.imdecode(np.frombuffer(pb, np.uint8), cv2.IMREAD_UNCHANGED)

    rot = lambda a: sha(png_bytes(np.ascontiguousarray(np.rot90(a, k=-1))))  # noqa: E731
    U = [u for u, v in key.items() if v['role'] == 'U']
    R = [u for u, v in key.items() if v['role'] == 'R']
    want = [u for u, v in p2.items() if v['role'] == 'cand' and v['strip'].endswith(strip) and v['r'] == r and v['c'] == c]
    ck['E1_U'] = len(U) == 1 and len(want) == 1 and U[0] == want[0] and key[U[0]]['src'] == p2[want[0]]['src'] \
        and img.get(U[0]) == allc[p2[want[0]]['src']]['src_sha256']
    cand_src = p2[want[0]]['src'] if want else None
    ck['E2_R'] = len(R) == 1 and cand_src is not None and img.get(R[0]) == rot(src_tile(cand_src))
    used_n0 = {v['src'] for v in p2.values() if v['role'] == 'n0'}
    excluded = {cand_src} | set(pool) | used_n0
    census = sorted((u, v) for k in ckeys.values() for u, v in k.items() if v['rot'] == 0 and u not in excluded)
    seed = p4_ext.SEED + _bidx(batch)
    draw = random.Random(seed).sample(census, p4_ext.N_N0)
    n0 = {u: v for u, v in key.items() if v['role'] == 'n0'}
    ck['E3_n0_draw'] = sorted(v['src'] for v in n0.values()) == sorted(u for u, _ in draw) and all(v['rot'] == 90 for v in n0.values())
    ck['E3_n0_img'] = all(img.get(u) == rot(src_tile(v['src'])) for u, v in n0.items())
    res['n0_seed'] = seed
    pcs = {u: v for u, v in key.items() if v['role'] == 'pc'}
    ck['E4_pc'] = all(v['src'] in pool and img.get(u) == pcm[v['src']] for u, v in pcs.items())
    ck['K_roles'] = len(key) == 2 + len(n0) + len(pcs)
    jobs_b = show(ref, f'{A}/jobs_{batch}.json', True)
    jobs = json.loads(jobs_b)
    ks, _, single, _ = task_variant(jobs['variant'])
    tmpl = norm_brief(HEADER.format(role='reader', images='\n'.join([ks] + ['/work/p4/img/x.png'] * 10),
                                    rcpt=open(RECIPIENT_FILE, encoding='ascii').read().strip(),
                                    out='/work/sealed_io/00000000-0000-0000-0000-000000000000.age')
                      + open(single, encoding='utf-8').read())
    cnt = {u: 0 for u in key}
    arms = []
    j_ok = len(jobs['jobs']) == p4_ext.N_SESS
    for j in jobs['jobs']:
        job = j['job']
        brief = show(ref, f'{A}/briefs/brief_{job}.txt')
        recj = json.loads(show(ref, f'{A}/job_records/{job}.json'))
        items = [os.path.basename(p)[:-4] for p in recj['images'][1:]]
        for u in items:
            cnt[u] = cnt.get(u, 0) + 1
        roles = [key.get(u, {}).get('role') for u in items]
        arm = 'U' if 'U' in roles else 'R'
        arms.append(arm)
        ok = (norm_brief(brief) == tmpl and sha(brief.encode()) == recj['brief_sha256'] and recj['images'][0] == ks
              and roles.count('U') + roles.count('R') == 1 and roles.count('n0') == p4_ext.PER_N0
              and roles.count('pc') == 1 and None not in roles and len(set(items)) == len(items)
              and j.get('arm') == arm and recj['out'] == f'/work/sealed_io/{job}.age' and recj['recipient'] == RCPT
              and len(recj['images']) == j['n_images'])
        res['jobs'][job] = {'brief_ok': ok, 'arm': arm}
        j_ok = j_ok and ok
    ck['J_jobs'] = j_ok and arms.count('U') == arms.count('R') == p4_ext.N_SESS // 2
    ck['J_cover'] = all(cnt[u] == p4_ext.READS_PER_N0 for u in n0) and all(cnt[u] == 1 for u in pcs)
    sb = sums(show(ref, f'{B}/SHA256SUMS'))
    aud_all = json.loads(show(ref, f'{B}/audit.json'))
    aud = {x['job']: x for x in aud_all if x.get('valid')}
    bl = ls(ref, B)
    rerun = {}
    for j in jobs['jobs']:
        job = j['job']
        if not any(p.endswith(f'/{job}.age') for p in bl) and any(p.endswith(f'/{job}.r2.age') for p in bl):
            a1 = [x for x in aud_all if x['job'] == job and x.get('attempt', 1) == 1]
            a2 = [x for x in aud_all if x['job'] == job and x.get('attempt') == 2]
            t1 = gzip.decompress(show(ref, f'{B}/transcripts/{job}.jsonl.gz', True))
            _, _, body1 = transcript_checks(t1, show(ref, f'{A}/briefs/brief_{job}.txt'))
            rerun[job] = (len(a1) == 1 and not a1[0].get('valid') and a1[0].get('age_exists') is False and body1 is None
                          and len(a2) == 1 and a2[0].get('valid') is True)
    ck['R2_reruns_ok'] = all(rerun.values())
    res['reruns'] = sorted(rerun)
    tmp = '/dev/shm/rh_verify_ext'
    os.makedirs(tmp, exist_ok=True)
    b1 = b2 = b3 = True
    for j in jobs['jobs']:
        job = j['job']
        rr = res['jobs'][job]
        tag = f'{job}.r2' if job in rerun else job
        agef = [p for p in bl if p.endswith(f'/{tag}.age')]
        age = show(ref, agef[0], True) if agef else b''
        rr['age_sha256'] = sha(age)
        rr['attempt'] = 2 if job in rerun else 1
        rr['B1'] = bool(age) and sb.get(f'{tag}.age') == sha(age) and aud.get(job, {}).get('answer_sha256') == sha(age)
        brief = show(ref, f'{A}/briefs/brief_{job}.txt')
        recj = json.loads(show(ref, f'{A}/job_records/{job}.json'))
        tr = gzip.decompress(show(ref, f'{B}/transcripts/{tag}.jsonl.gz', True))
        tp = f'{tmp}/{job}.jsonl'
        open(tp, 'wb').write(tr)
        au = audit(tp, recj['images'], sealed_output=recj['out'], recipient=RCPT)
        eq, times, body = transcript_checks(tr, brief)
        t_ok = bool(times) and min(datetime.fromisoformat(t.replace('Z', '+00:00')) for t in times) > t_a
        rr['B2'] = {'audit_valid': au['valid'], 'n_violations': len(au['violations']), 'unread': len(au['unread_images']),
                    'prompt_eq_brief': eq, 'after_commit_A': t_ok, 'transcript_sha256': sha(tr)}
        b1 = b1 and rr['B1']
        b2 = b2 and au['valid'] and eq and t_ok
        ap = f'{tmp}/{job}.age'
        open(ap, 'wb').write(age)
        try:
            same = body is not None and json.loads(body) == decrypt_answer_logged(ap, 'rh-verify-ext-consistency')
        except Exception:
            same = False
        rr['B3_consistent'] = same
        b3 = b3 and same
        os.remove(tp)
        os.remove(ap)
    ck['B1_age_hashes'], ck['B2_transcripts'], ck['B3_answer_consistency'] = b1, b2, b3
    res['checks'] = ck
    res['n'] = {'U': len(U), 'R': len(R), 'n0': len(n0), 'pc': len(pcs), 'jobs': len(jobs['jobs'])}
    res['PASS'] = all(ck.values())
    if install and res['PASS']:
        fd = os.open(f'/srv/scorer/p4ext_key_{batch}.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        with os.fdopen(fd, 'wb') as fh:
            fh.write(key_b)
        for j in jobs['jobs']:
            job = j['job']
            tag = f'{job}.r2' if job in rerun else job
            agef = [p for p in bl if p.endswith(f'/{tag}.age')][0]
            with open(f'/work/sealed_io/{job}.age', 'xb') as fh:
                fh.write(show(ref, agef, True))
            recj = json.loads(show(ref, f'{A}/job_records/{job}.json'))
            b2j = res['jobs'][job]['B2']
            recj.update({'attempt': res['jobs'][job]['attempt'], 'valid': b2j['audit_valid'] and b2j['prompt_eq_brief'], 'answer_sha256': res['jobs'][job]['age_sha256'],
                         'verified_by': 'tools/p4/rh_verify_ext.py', 'harness_ref': res['ref_commit']})
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
