# Provenance: Project HERCULES | owner the owner | [id removed]
"""Write logs/sib/readcal2/REPORT.md (text below + a sha256 table of every committed readcal2 file) and
logs/sib/readcal2/report.json. Usage: python write_report.py DONE|RUNNING"""
import glob
import hashlib
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main(status):
    os.chdir(REPO)
    files = sorted(set(glob.glob('tools/sib/readcal2/**/*', recursive=True) + glob.glob('logs/sib/readcal2/**/*', recursive=True)
                       + glob.glob('tests/sib_readcal2_*_test.py')))
    files = [f for f in files if os.path.isfile(f) and not f.endswith(('REPORT.md', 'report.json', 'runs.jsonl'))
             and '__pycache__' not in f]
    cand = json.load(open('logs/sib/readcal2/candidates.json'))
    noise = json.load(open('logs/sib/readcal2/noise_psd.json'))['pooled']['fwd']
    ref = json.load(open('logs/sib/readcal2/refwin_manifest.json')) if os.path.exists('logs/sib/readcal2/refwin_manifest.json') else None
    body = open('tools/sib/readcal2/REPORT_body.md').read()
    body = body.replace('{STATUS}', status).replace('{N_TEXT}', str(len(cand['text_candidates']))) \
        .replace('{N_BLANK}', str(len(cand['blank_candidates']))).replace('{N_TILING}', str(len(cand['picker_tiling']))) \
        .replace('{N_HELD}', str(len(cand['held_rcpick1']))) \
        .replace('{N_REFWIN}', str(len([w for w in ref['windows'] if 'status' not in w])) if ref else 'pending') \
        .replace('{N_REFIMG}', str(ref['n_images']) if ref else 'pending') \
        .replace('{NOISE_MEAN}', f"{noise['mean']:.1f}").replace('{NOISE_VAR}', f"{noise['var_psd_mean_masked']:.0f}")
    rows = '\n'.join(f'| `{f}` | `{sha(f)}` |' for f in files)
    txt = f'{PROV}\n\n' + body + '\n## File hashes (sha256)\n\n| File | sha256 |\n|---|---|\n' + rows + '\n'
    open('logs/sib/readcal2/REPORT.md', 'w').write(txt)
    json.dump({'provenance': PROV, 'status': status, 'files_sha256': {f: sha(f) for f in files},
               'counts': {'text_candidates': len(cand['text_candidates']), 'blank_candidates': len(cand['blank_candidates']),
                          'picker_tiling': len(cand['picker_tiling']), 'held_rcpick1': len(cand['held_rcpick1'])}},
              open('logs/sib/readcal2/report.json', 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'RUNNING')
