# Provenance: Project HERCULES | owner the owner | [id removed]
"""rh-e2 transcript audit (DECL-REMOTE-HARNESS-1 items 5-6). Prints and stores counts/booleans only; never
prints any tool-call content or reader text.

usage: audit_e2.py <map.tsv> <out_dir> [<commit_A_dir>]   (default logs/sib/rh-e2/A, the E2 batch)
map.tsv rows: job<TAB>transcript_path<TAB>attempt
For each job: hercules.harness.audit.audit(transcript, allowed_images, sealed_output, recipient) with the images
from the brief's job record; plus prompt == brief (first user message of the transcript, byte-equal), and
handback == 'DONE' (final assistant text). Writes out_dir/audit.json, out_dir/harness_jobs.tsv,
out_dir/transcripts/<job>[.rN].jsonl.gz and copies out_dir/age/<job>.age.
"""
import gzip
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, 'src')
from hercules.harness.audit import audit  # noqa: E402

A = 'logs/sib/rh-e2/A'
RCPT = 'age1vp0tkyj8xecncfmcxj748ceef89mpmwayljccaduapjx3aqhh5rstvvcq5'


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text')
    return None


def prompt_and_handback(path):
    first_user, last_text = None, None
    for line in open(path, encoding='utf-8'):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get('message') if isinstance(rec, dict) else None
        if not isinstance(msg, dict):
            continue
        if msg.get('role') == 'user' and first_user is None:
            first_user = _text(msg.get('content'))
        if msg.get('role') == 'assistant':
            t = _text(msg.get('content'))
            if t:
                last_text = t
            for b in msg.get('content') if isinstance(msg.get('content'), list) else []:
                if isinstance(b, dict) and b.get('type') == 'tool_use' and b.get('name') == 'SubagentHandback':
                    vals = [v for v in (b.get('input') or {}).values() if isinstance(v, str)]
                    last_text = '\n'.join(vals)
    return first_user, last_text


def main(map_tsv, out, a_dir=None):
    global A
    A = a_dir or A
    os.makedirs(f'{out}/transcripts', exist_ok=True)
    os.makedirs(f'{out}/age', exist_ok=True)
    rows = [ln.rstrip('\n').split('\t') for ln in open(map_tsv) if ln.strip()]
    res = []
    for job, tpath, attempt in rows:
        rec = json.load(open(f'{A}/job_records/{job}.json'))
        brief = open(f'{A}/briefs/brief_{job}.txt', encoding='utf-8').read()
        a = audit(tpath, rec['images'], sealed_output=rec['out'], recipient=RCPT)
        p, h = prompt_and_handback(tpath)
        # attribute the sealed file only to an attempt whose transcript made the sealed write
        exists = os.path.exists(rec['out']) and 'no sealed write' not in a['violations']
        ans = _sha(rec['out']) if exists else ''
        # image bytes unchanged since commit A
        img_ok = all(_sha(q) == s for q, s in rec['image_sha256'].items())
        valid = a['valid'] and exists and p == brief and img_ok
        suffix = '' if attempt == '1' else f'.r{attempt}'
        gz = f'{out}/transcripts/{job}{suffix}.jsonl.gz'
        with open(tpath, 'rb') as src, gzip.open(gz, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        if exists:
            shutil.copyfile(rec['out'], f'{out}/age/{job}{suffix}.age')
        res.append({'job': job, 'attempt': int(attempt), 'valid': valid, 'audit_valid': a['valid'],
                    'violations': a['violations'], 'n_calls': len(a['calls']),
                    'n_reads': sum(c['name'] == 'Read' for c in a['calls']),
                    'unread_images': len(a['unread_images']), 'prompt_eq_brief': p == brief,
                    'handback_is_DONE': (h or '').strip() == 'DONE', 'images_unchanged': img_ok,
                    'age_exists': exists, 'answer_sha256': ans, 'brief_sha256': rec['brief_sha256'],
                    'transcript_sha256': _sha(tpath), 'transcript_gz': os.path.basename(gz)})
    json.dump(res, open(f'{out}/audit.json', 'w'), indent=1)
    with open(f'{out}/harness_jobs.tsv', 'w') as fh:
        fh.write('job\tattempt\tvalid\tprompt_eq_brief\thandback_is_DONE\tn_reads\tunread\tviolations\tanswer_sha256\tbrief_sha256\n')
        for r in res:
            fh.write(f"{r['job']}\t{r['attempt']}\t{r['valid']}\t{r['prompt_eq_brief']}\t{r['handback_is_DONE']}\t"
                     f"{r['n_reads']}\t{r['unread_images']}\t{';'.join(r['violations'])}\t{r['answer_sha256']}\t{r['brief_sha256']}\n")
    print(json.dumps([{k: r[k] for k in ('job', 'attempt', 'valid', 'prompt_eq_brief', 'handback_is_DONE',
                                         'n_reads', 'unread_images', 'violations')} for r in res]))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
