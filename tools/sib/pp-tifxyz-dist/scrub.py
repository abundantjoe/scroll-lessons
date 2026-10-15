"""Scrub a package tree before public release. Usage: scrub.py PKG_DIR OUT.json"""
import json, os, re, subprocess, sys, datetime
root, out = sys.argv[1], sys.argv[2]
CHK = {
 'secrets': r'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,}|xox[bap]-|BEGIN [A-Z ]*PRIVATE KEY|(?i:(api[_-]?key|secret|passw(or)?d|token)\s*[:=]\s*[\'"][^\'"]{8,})',
 'paths': r'/srv\b|/work\b|/tmp\b|scratchpad|/home/user|/root\b|claude-0',
 'governance': r'(?i)\bRULES\b|RULES\.md|hercules|governance|orchestrat|sibling|\bsib[-/]|dominion|standing.order|DECL-|\bseal(?!es\b)|decrypt|scorer',
 'paris4_title_search': r'(?i)paris ?4|PHercParis4|w010|w028|w037|w027|title[- _]?search|20260411134726|20231016151002',
 'personal': r'(?i)the owner|the owner|@gmail|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}',
 'contamination_grouping': r'(?i)contam',
}
files = []
for d, dn, fn in os.walk(root):
    dn[:] = [x for x in dn if x not in ('.git', '__pycache__', '.pytest_cache')]
    files += [os.path.join(d, f) for f in fn]
hits = {k: [] for k in CHK}
for f in files:
    rel = os.path.relpath(f, root)
    try:
        txt = open(f, encoding='utf-8').read()
    except UnicodeDecodeError:
        hits.setdefault('binary_files', []).append(rel); continue
    for k, rx in CHK.items():
        for m in re.finditer(rx, txt):
            ln = txt.count('\n', 0, m.start()) + 1
            hits[k].append(f'{rel}:{ln}:{m.group(0)}')
lic = os.path.exists(os.path.join(root, 'LICENSE')) and 'MIT License' in open(os.path.join(root, 'LICENSE')).read()
ok = lic and all(not v for v in hits.values())
res = {'note': 'governance pattern excludes the surname Seales (verbatim dataset citation author W. Brent Seales)', 'utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'files': sorted(os.path.relpath(f, root) for f in files),
       'n_files': len(files), 'license_mit': lic, 'checks': list(CHK), 'hits': hits, 'scrub_ok': ok}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({'scrub_ok': ok, 'n_files': len(files), 'hits': {k: len(v) for k, v in hits.items()}}))
for k, v in hits.items():
    for h in v[:20]: print(k, h)
