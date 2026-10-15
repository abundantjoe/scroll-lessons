"""Read-only branch inventory of GitHub repositories (REST API through `gh api`): for every branch its last commit,
ahead/behind against the default branch and the top-level directories it changes. Writes the JSON that
scripts/branch_index.py turns into BRANCH_INDEX.md. It only reads; it never changes a branch.

  python branch_inventory.py OWNER REPO [REPO ...] --out inventory.json

The JSON holds raw commit messages; for private repositories keep it private (branch_index.py omits them).
"""
import argparse
import json
import subprocess
import sys


def gh(path):
    r = subprocess.run(['gh', 'api', path], capture_output=True, text=True)
    if r.returncode:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def gh_pages(path):
    out, page = [], 1
    while True:
        d = gh(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
        if not d:
            break
        out += d
        if len(d) < 100:
            break
        page += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('owner')
    ap.add_argument('repos', nargs='+')
    ap.add_argument('--out', default='inventory.json')
    a = ap.parse_args()
    inv = {}
    for r in a.repos:
        meta = gh(f'repos/{a.owner}/{r}') or {}
        default = meta.get('default_branch', 'main')
        rows = []
        for b in gh_pages(f'repos/{a.owner}/{r}/branches'):
            name, sha = b['name'], b['commit']['sha']
            cm = (gh(f'repos/{a.owner}/{r}/commits/{sha}') or {}).get('commit') or {}
            cmp = gh(f'repos/{a.owner}/{r}/compare/{default}...{sha}') if name != default else None
            tops = {}
            for f in (cmp or {}).get('files', []):
                top = f['filename'].split('/')[0]
                tops[top] = tops.get(top, 0) + 1
            rows.append(dict(branch=name, sha=sha, date=(cm.get('committer') or {}).get('date'),
                             msg=(cm.get('message') or '').split('\n')[0][:160],
                             ahead=(cmp or {}).get('ahead_by'), behind=(cmp or {}).get('behind_by'),
                             n_files=len((cmp or {}).get('files', [])),
                             top_dirs=sorted(tops.items(), key=lambda t: -t[1])[:5], cmp_status=(cmp or {}).get('status')))
            print(r, name, file=sys.stderr, flush=True)
        inv[r] = dict(private=meta.get('private'), default=default, branches=rows)
    json.dump(inv, open(a.out, 'w'), indent=1)
    print('done', {r: len(v['branches']) for r, v in inv.items()})


if __name__ == '__main__':
    main()
