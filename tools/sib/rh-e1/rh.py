# Provenance: Project HERCULES | owner the owner | [id removed]
"""rh-e1 remote harness helper (DECL-REMOTE-HARNESS-1). Numbers only: never opens an image, never prints any
tool-call content of a reader transcript, never decrypts.

commit_a <tag> <out_dir> <builder_ref> <key_batch>... <jobs_batch>
    Copies /srv/scorer/p4_key_<b>.json (+ sha256), /work/p4/jobs_<jobs_batch>.json, the batch's briefs and
    /work/jobs/<job>.json records, and writes img_manifest.json (uuid -> sha256 for every /work/p4/img file)
    and builder.json (ref + commit sha).
audit <jobs_batch> <out_dir> <subagent_dir> [<recipient>]
    For each job, finds the reader transcript(s) whose first user message equals the brief bytes, runs
    hercules.harness.audit.audit, writes <out_dir>/audit.json, harness_jobs.tsv, transcripts/<job>[.n].jsonl.gz
    and copies /work/sealed_io/<job>.age to <out_dir>/sealed_io/.
"""
import glob
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, 'src')
RCPT = 'age1vp0tkyj8xecncfmcxj748ceef89mpmwayljccaduapjx3aqhh5rstvvcq5'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def commit_a(out, ref, key_batches, jobs_batch):
    os.makedirs(f'{out}/briefs', exist_ok=True)
    os.makedirs(f'{out}/job_records', exist_ok=True)
    keys = {}
    for b in key_batches:
        src = f'/srv/scorer/p4_key_{b}.json'
        shutil.copyfile(src, f'{out}/p4_key_{b}.json')
        keys[f'p4_key_{b}.json'] = sha(src)
        assert sha(f'{out}/p4_key_{b}.json') == keys[f'p4_key_{b}.json']
    with open(f'{out}/keys.sha256', 'w') as fh:
        fh.writelines(f'{v}  {k}\n' for k, v in sorted(keys.items()))
    jf = f'/work/p4/jobs_{jobs_batch}.json'
    shutil.copyfile(jf, f'{out}/jobs_{jobs_batch}.json')
    jobs = json.load(open(jf))['jobs']
    briefs = {}
    for j in jobs:
        b = f"/work/p4/brief_{j['job']}.txt"
        shutil.copyfile(b, f"{out}/briefs/brief_{j['job']}.txt")
        shutil.copyfile(f"/work/jobs/{j['job']}.json", f"{out}/job_records/{j['job']}.json")
        briefs[j['job']] = sha(b)
    img = {f[:-4]: sha(f'/work/p4/img/{f}') for f in sorted(os.listdir('/work/p4/img')) if f.endswith('.png')}
    json.dump(img, open(f'{out}/img_manifest.json', 'w'), indent=1)
    commit = subprocess.run(['git', 'rev-parse', ref], capture_output=True, text=True, check=True).stdout.strip()
    json.dump({'builder_ref': ref, 'builder_commit': commit, 'jobs_sha256': sha(jf), 'brief_sha256': briefs,
               'keys_sha256': keys, 'n_img': len(img)}, open(f'{out}/builder.json', 'w'), indent=1)
    print(json.dumps({'jobs': len(jobs), 'keys': keys, 'n_img': len(img), 'builder_commit': commit}))


def _first_user(path):
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get('message') if isinstance(rec, dict) else None
            if isinstance(msg, dict) and msg.get('role') == 'user':
                c = msg.get('content')
                if isinstance(c, str):
                    return c
                if isinstance(c, list):
                    return ''.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text')
                return None
    return None


def _mtime_utc(p):
    return subprocess.run(['date', '-u', '-r', p, '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True,
                          check=True).stdout.strip()


def audit_batch(jobs_batch, out, subdir, rcpt=RCPT, age_dir='sealed_io'):
    from hercules.harness.audit import audit
    os.makedirs(f'{out}/{age_dir}', exist_ok=True)
    os.makedirs(f'{out}/transcripts', exist_ok=True)
    jobs = json.load(open(f'/work/p4/jobs_{jobs_batch}.json'))['jobs']
    trs = sorted(glob.glob(f'{subdir}/agent-*.jsonl'), key=os.path.getmtime)
    firsts = {t: _first_user(t) for t in trs}
    res, rows = {}, []
    for j in jobs:
        job = j['job']
        rec = json.load(open(f'/work/jobs/{job}.json'))
        brief = open(f'/work/p4/brief_{job}.txt', encoding='utf-8').read()
        mine = [t for t in trs if firsts[t] is not None and firsts[t].strip() == brief.strip()]
        runs = []
        for n, t in enumerate(mine):
            a = audit(t, rec['images'], sealed_output=rec['out'], recipient=rcpt)
            runs.append({'transcript': os.path.basename(t), 'valid': a['valid'], 'violations': a['violations'],
                         'unread_images': len(a['unread_images']), 'prompt_equals_brief': firsts[t] == brief,
                         'prompt_equals_brief_stripped': firsts[t].strip() == brief.strip(),
                         'done_utc': _mtime_utc(t)})
            with open(t, 'rb') as src, gzip.open(f"{out}/transcripts/{job}{'' if n == 0 else f'.{n}'}.jsonl.gz",
                                                 'wb') as dst:
                shutil.copyfileobj(src, dst)
        ex = os.path.exists(rec['out'])
        ans = sha(rec['out']) if ex else ''
        if ex:
            shutil.copyfile(rec['out'], f'{out}/{age_dir}/{job}.age')
        last = runs[-1] if runs else {}
        res[job] = {'valid': bool(last.get('valid')) and ex and len(runs) >= 1,
                    'violations': last.get('violations', ['no transcript found']),
                    'unread_images': last.get('unread_images'), 'prompt_equals_brief': last.get('prompt_equals_brief'),
                    'answer_sha256': ans, 'brief_sha256': hashlib.sha256(brief.encode()).hexdigest(),
                    'done_utc': last.get('done_utc'), 'n_runs': len(runs), 'runs': runs}
        rows.append(f"{last.get('done_utc')}\t{job}\treader\t{res[job]['valid']}\t{len(rec['images'])}\t"
                    f"{last.get('unread_images')}\t{';'.join(res[job]['violations'])}\t{ans}\t"
                    f"{res[job]['brief_sha256']}\n")
    lst = [dict(job=j, attempt=v['n_runs'], age_exists=bool(v['answer_sha256']),
                transcript_gz=f'{j}.jsonl.gz',
                transcript_sha256=hashlib.sha256(gzip.open(f'{out}/transcripts/{j}.jsonl.gz').read()).hexdigest()
                if v['n_runs'] else '', **v) for j, v in res.items()]
    json.dump(lst, open(f'{out}/audit.json', 'w'), indent=1)
    with open(f'{out}/harness_jobs.tsv', 'w') as fh:
        fh.write('done_utc\tjob\trole\tvalid\tn_images\tunread\tviolations\tanswer_sha256\tbrief_sha256\n')
        fh.writelines(rows)
    with open(f'{out}/SHA256SUMS', 'w') as fh:
        for f in ['audit.json', 'harness_jobs.tsv'] + [f'{age_dir}/{x}' for x in sorted(os.listdir(f'{out}/{age_dir}'))]:
            fh.write(f'{sha(f"{out}/{f}")}  {f}\n')
    print(json.dumps({j: {k: v[k] for k in ('valid', 'violations', 'unread_images', 'prompt_equals_brief',
                                            'n_runs')} for j, v in res.items()}, indent=1))


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'commit_a':
        commit_a(sys.argv[3], sys.argv[4], sys.argv[5:-1], sys.argv[-1])
    elif c == 'audit':
        audit_batch(*sys.argv[2:5], age_dir=sys.argv[5] if len(sys.argv) > 5 else 'sealed_io')
