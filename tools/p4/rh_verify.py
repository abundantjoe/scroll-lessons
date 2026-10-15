# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent verification and installation of a remote-harness batch (RULES.md DECL-REMOTE-HARNESS-1 items 4-7).
Booleans and counts only; no letter content is printed or written.

usage: rh_verify.py <harness_ref> <rh_dir> <census_batch> <null_batch> <jobs_batch> <ref_brief> <out_json> [--coverage] [--install]

Checks (all must hold, else the batch is VOID and nothing is installed):
  A0 builder_ref.json code_sha256 == the local files' sha256, or an earlier declared version listed in DECLARED;
  A1 the commit that first adds <rh_dir>/A precedes the commit that first adds <rh_dir>/B;
  A2 key files and jobs json in A match A/SHA256SUMS where listed; the key holds census (rot 0) and N0 (rot 90,
     null_of in census) entries only;
  A3 img_manifest sha256 of every census uuid == key src_sha256;
  A4 builder manifest (builder_ref.json): the key's (r, c) set == tiles with valid_fraction >= 0.5
     (and, with coverage, frac_mesh_points_outside_1129_volume < 0.5) and src_sha256 == png_sha256;
  A5 every brief equals the reference brief after collapsing each run of image-path lines to one marker and normalising
     the job uuid; its image count == n_images == 1 + n_census + n_null of the job; its image list ==
     the job record's image list; keysheet first; the jobs cover every census tile exactly once and every N0 once;
  B1 .age sha256 == B/SHA256SUMS and == audit answer_sha256;
  B2 for every job: hercules.harness.audit.audit on the transcript is VALID; the first user message == the brief;
     every transcript timestamp is later than the commit time of A;
  B3 the decrypted .age answer equals, as JSON, the heredoc body of the transcript's sealed write (purpose
     'rh-verify-consistency', logged).
--install (only if all pass): keys -> /srv/scorer/p4_key_<batch>.json (O_EXCL, 0400), .age -> /work/sealed_io/,
job records (with valid from B2) -> /work/jobs/, jobs json -> /work/p4/jobs_<jobs_batch>.json.
"""
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, 'src')
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
RCPT = 'age1vp0tkyj8xecncfmcxj748ceef89mpmwayljccaduapjx3aqhh5rstvvcq5'
# earlier declared versions still valid for batches built with them (METRIC-HASH-27 norm_manifest; METRIC-HASH-28 rh_verify)
DECLARED = {'tools/p4/norm_manifest.py': {'b549026e8ff2cff9f8b97ff221d87f44d3bed7cc1702f4874c5efc8c1a6f4d0d'}}
HEREDOC = re.compile(r"<<'EOF'\n(?P<body>.*)\nEOF\n?\Z", re.S)


def show(ref, path, binary=False):
    out = subprocess.run(['git', 'show', f'{ref}:{path}'], capture_output=True, check=True).stdout
    return out if binary else out.decode('utf-8')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def ls(ref, path):
    out = subprocess.run(['git', 'ls-tree', '-r', '--name-only', ref, '--', path], capture_output=True, check=True)
    return out.stdout.decode().split()


def first_commit_time(ref, path):
    out = subprocess.run(['git', 'log', '--diff-filter=A', '--format=%H %cI', ref, '--', path], capture_output=True,
                         check=True).stdout.decode().split('\n')
    rows = [r.split() for r in out if r.strip()]
    return rows[-1] if rows else None  # oldest adding commit


def sums(text):
    d = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            d[os.path.basename(parts[1].lstrip('*'))] = parts[0]
    return d


def norm_brief(text):
    lines = []
    for ln in text.split('\n'):
        if ln.startswith('/work/p4/img/'):
            if lines and lines[-1] == '<IMG>':
                continue  # a run of image lines collapses to one marker; the count is checked against the job
            ln = '<IMG>'
        lines.append(ln)
    out = '\n'.join(lines)
    return re.sub(r'/work/sealed_io/[0-9a-f-]{36}\.age', '/work/sealed_io/<JOB>.age', out)


def brief_images(text):
    return [ln for ln in text.split('\n') if ln.startswith('/work/p4/img/') or ln.endswith('keysheet_sigma2.png')]


def transcript_checks(raw, brief):
    first_user, times, body = None, [], None
    for line in raw.decode('utf-8').splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if rec.get('timestamp'):
            times.append(rec['timestamp'])
        msg = rec.get('message')
        if not isinstance(msg, dict):
            continue
        if msg.get('role') == 'user' and first_user is None:
            c = msg.get('content')
            if isinstance(c, str):
                first_user = c
            elif isinstance(c, list):
                first_user = ''.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text')
        if msg.get('role') == 'assistant' and isinstance(msg.get('content'), list):
            for b in msg['content']:
                if isinstance(b, dict) and b.get('type') == 'tool_use' and b.get('name') == 'Bash':
                    m = HEREDOC.search((b.get('input') or {}).get('command', ''))
                    if m:
                        body = m.group('body')
    return first_user == brief, times, body


def main(ref, rh, cb, nb, jb, ref_brief, out, install=False, cov=False):
    from hercules.harness.audit import audit
    from hercules.scorer.keyaccess import decrypt_answer_logged
    res = {'provenance': PROV, 'serves': 'RULES.md DECL-REMOTE-HARNESS-1 items 4-7', 'ref': ref,
           'ref_commit': subprocess.run(['git', 'rev-parse', ref], capture_output=True).stdout.decode().strip(),
           'checks': {}, 'jobs': {}}
    ck = res['checks']
    a_first, b_first = first_commit_time(ref, f'{rh}/A'), first_commit_time(ref, f'{rh}/B')
    anc = subprocess.run(['git', 'merge-base', '--is-ancestor', a_first[0], b_first[0]]).returncode == 0
    ck['A1_A_before_B'] = bool(a_first and b_first and anc and a_first[0] != b_first[0])
    res['commit_A'], res['commit_B'] = a_first, b_first
    t_a = datetime.fromisoformat(a_first[1])
    sa = sums(show(ref, f'{rh}/A/SHA256SUMS'))
    key_c = show(ref, f'{rh}/A/p4_key_{cb}.json', True)
    key_n = show(ref, f'{rh}/A/p4_key_{nb}.json', True)
    jobs_b = show(ref, f'{rh}/A/jobs_{jb}.json', True)
    listed = {f: sa.get(f) for f in (f'p4_key_{cb}.json', f'p4_key_{nb}.json', f'jobs_{jb}.json')}
    got = {f'p4_key_{cb}.json': sha(key_c), f'p4_key_{nb}.json': sha(key_n), f'jobs_{jb}.json': sha(jobs_b)}
    kc, kn, jobs = json.loads(key_c), json.loads(key_n), json.loads(jobs_b)
    ck['A2_sums'] = all(listed[f] in (None, got[f]) for f in got) and any(listed.values())
    ck['A2_key_shape'] = all(v['rot'] == 0 for v in kc.values()) and all(
        v['rot'] == 90 and v.get('null_of') in kc for v in kn.values())
    res['key_sha256'] = {f'p4_key_{cb}.json': got[f'p4_key_{cb}.json'], f'p4_key_{nb}.json': got[f'p4_key_{nb}.json']}
    img = json.loads(show(ref, f'{rh}/A/img_manifest.json'))
    img = img.get('images', img) if isinstance(img, dict) else img
    if isinstance(img, list):
        img = {os.path.basename(x.get('file', x.get('uuid', '')))[:36]: x.get('sha256') for x in img}
    img = {k[:36]: v for k, v in img.items()}
    ck['A3_img_census'] = all(img.get(u) == v['src_sha256'] for u, v in kc.items())
    ck['A3_img_null_present'] = all(u in img for u in kn)
    bref = json.loads(show(ref, f'{rh}/A/builder_ref.json'))
    res['builder_ref'] = bref
    ck['A0_code_hashes'] = all(sha(open(f, 'rb').read()) == h or h in DECLARED.get(f, ())
                               for f, h in bref['code_sha256'].items())
    bm = json.loads(show(bref['builder_commit'], bref['manifest']))
    elig = {}
    for t in bm['tiles']:
        if t.get('valid_fraction', 0) < 0.5:
            continue
        if cov:
            fo = (t.get('stats') or {}).get('frac_mesh_points_outside_1129_volume')
            if fo is None:  # METRIC-HASH-29 semantics, as tools/p4/norm_manifest.py
                fo = t.get('frac_mesh_points_outside_1129_volume', t.get('frac_outside'))
            if fo is None or fo >= 0.5:
                continue
        elig[(t['r'], t['c'])] = t['png_sha256']
    keyrc = {(v['r'], v['c']): v['src_sha256'] for v in kc.values()}
    ck['A4_builder_eligible_set'] = keyrc == elig
    res['n_census'], res['n_null'], res['n_eligible_builder'] = len(kc), len(kn), len(elig)
    refn = norm_brief(open(ref_brief).read())
    seen_c, seen_n, a5 = [], [], True
    for j in jobs['jobs']:
        job = j['job']
        brief = show(ref, f'{rh}/A/briefs/brief_{job}.txt')
        recj = json.loads(show(ref, f'{rh}/A/job_records/{job}.json'))
        ims = brief_images(brief)
        ok = norm_brief(brief) == refn and ims == recj['images'] and ims[0].endswith('keysheet_sigma2.png') \
            and sha(brief.encode()) == recj['brief_sha256'] and recj['out'] == f'/work/sealed_io/{job}.age' \
            and recj['recipient'] == RCPT and len(ims) == j['n_images'] == 1 + j['n_census'] + j['n_null']
        for p in ims[1:]:
            u = os.path.basename(p)[:-4]
            if u in kc:
                seen_c.append(u)
            elif u in kn:
                seen_n.append(u)
            else:
                seen_c.append('?' + u)
        a5 = a5 and ok
        res['jobs'][job] = {'brief_ok': ok, 'brief_sha256': recj['brief_sha256']}
    ck['A5_briefs'] = a5
    ck['A5_cover'] = sorted(seen_c) == sorted(kc) and sorted(seen_n) == sorted(kn)
    sb = sums(show(ref, f'{rh}/B/SHA256SUMS'))
    aud = {x['job']: x for x in json.loads(show(ref, f'{rh}/B/audit.json')) if x.get('valid')}
    tmp = '/dev/shm/rh_verify'
    os.makedirs(tmp, exist_ok=True)
    b1 = b2 = b3 = True
    for j in jobs['jobs']:
        job = j['job']
        r = res['jobs'][job]
        agefile = [p for p in ls(ref, f'{rh}/B') if p.endswith(f'{job}.age')]
        age = show(ref, agefile[0], True) if agefile else b''
        r['age_sha256'] = sha(age)
        r['B1'] = bool(age) and sb.get(f'{job}.age') == sha(age) and \
            aud.get(job, {}).get('answer_sha256') == sha(age)
        brief = show(ref, f'{rh}/A/briefs/brief_{job}.txt')
        recj = json.loads(show(ref, f'{rh}/A/job_records/{job}.json'))
        tr = gzip.decompress(show(ref, f'{rh}/B/transcripts/{job}.jsonl.gz', True))
        tp = f'{tmp}/{job}.jsonl'
        open(tp, 'wb').write(tr)
        au = audit(tp, recj['images'], sealed_output=recj['out'], recipient=RCPT)
        eq, times, body = transcript_checks(tr, brief)
        t_ok = bool(times) and min(datetime.fromisoformat(t.replace('Z', '+00:00')) for t in times) > t_a
        r['B2'] = {'audit_valid': au['valid'], 'n_violations': len(au['violations']),
                   'unread': len(au['unread_images']), 'prompt_eq_brief': eq, 'after_commit_A': t_ok,
                   'transcript_sha256': sha(tr)}
        b1 = b1 and r['B1']
        b2 = b2 and au['valid'] and eq and t_ok
        ap = f'{tmp}/{job}.age'
        open(ap, 'wb').write(age)
        try:
            dec = decrypt_answer_logged(ap, 'rh-verify-consistency')
            same = body is not None and json.loads(body) == dec
        except Exception:
            same = False
        r['B3_consistent'] = same
        b3 = b3 and same
        os.remove(tp)
        os.remove(ap)
    ck['B1_age_hashes'], ck['B2_transcripts'], ck['B3_answer_consistency'] = b1, b2, b3
    res['PASS'] = all(ck.values())
    if install and res['PASS']:
        for b, raw in ((cb, key_c), (nb, key_n)):
            fd = os.open(f'/srv/scorer/p4_key_{b}.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
            with os.fdopen(fd, 'wb') as fh:
                fh.write(raw)
        for j in jobs['jobs']:
            job = j['job']
            agefile = [p for p in ls(ref, f'{rh}/B') if p.endswith(f'{job}.age')][0]
            with open(f'/work/sealed_io/{job}.age', 'xb') as fh:
                fh.write(show(ref, agefile, True))
            recj = json.loads(show(ref, f'{rh}/A/job_records/{job}.json'))
            b2j = res['jobs'][job]['B2']
            recj.update({'valid': b2j['audit_valid'] and b2j['prompt_eq_brief'], 'answer_sha256':
                         res['jobs'][job]['age_sha256'], 'verified_by': 'tools/p4/rh_verify.py', 'harness_ref':
                         res['ref_commit']})
            with open(f'/work/jobs/{job}.json', 'x') as fh:
                json.dump(recj, fh, indent=1)
        with open(f'/work/p4/jobs_{jb}.json', 'xb') as fh:
            fh.write(jobs_b)
        res['installed'] = True
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({'PASS': res['PASS'], 'checks': ck, 'n_census': res['n_census'], 'n_null': res['n_null'],
                      'installed': res.get('installed', False)}))


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    main(*a, install='--install' in sys.argv, cov='--coverage' in sys.argv)
