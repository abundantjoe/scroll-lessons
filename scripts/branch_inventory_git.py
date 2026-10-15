"""Read-only branch inventory through git alone (for repositories the GitHub API cannot reach from here): fetches commit
history (no file contents) into a scratch bare repository and writes the same JSON as branch_inventory.py.

  python branch_inventory_git.py OWNER REPO [REPO ...] --work DIR --out inventory_git.json [--public REPO ...]
         [--upstream REPO=https://github.com/UP/REPO] [--self-email EMAIL]

For a fork (--upstream), each branch also gets `upstream_contained` (its head is in a current upstream branch) and
`own_commits` (number of commits not in any upstream branch whose author email is --self-email or a GitHub noreply
address of OWNER). Author identities are used only for this count and are not written out.
"""
import argparse
import json
import os
import subprocess


def git(d, *a):
    return subprocess.run(['git', '-C', d, *a], capture_output=True, text=True, check=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('owner')
    ap.add_argument('repos', nargs='+')
    ap.add_argument('--work', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--upstream', action='append', default=[])
    ap.add_argument('--self-email', default='')
    ap.add_argument('--public', action='append', default=[], help='repositories that are public (all others are private)')
    a = ap.parse_args()
    ups = dict(u.split('=', 1) for u in a.upstream)
    inv = {}
    for r in a.repos:
        d = os.path.join(a.work, r + '.git')
        if not os.path.exists(d):
            subprocess.run(['git', 'init', '-q', '--bare', d], check=True)
        filt = '--filter=tree:0' if r in ups else '--filter=blob:none'
        git(d, 'fetch', '-q', filt, f'https://github.com/{a.owner}/{r}', '+refs/heads/*:refs/heads/*')
        head = git(d, 'ls-remote', '--symref', f'https://github.com/{a.owner}/{r}', 'HEAD').split('\n')[0]
        default = head.split()[1].replace('refs/heads/', '') if head.startswith('ref:') else 'main'
        if r in ups:
            git(d, 'fetch', '-q', '--filter=tree:0', ups[r], '+refs/heads/*:refs/upstream/*')
        rows = []
        for line in git(d, 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads').split('\n'):
            if not line:
                continue
            name, sha = line.split()
            date = git(d, 'log', '-1', '--format=%cI', sha).strip()
            row = dict(branch=name, sha=sha, date=date, msg='', ahead=None, behind=None, n_files=0, top_dirs=[], cmp_status=None)
            if name != default:
                behind, ahead = git(d, 'rev-list', '--left-right', '--count', f'{default}...{sha}').split()
                row.update(ahead=int(ahead), behind=int(behind))
                if r not in ups:
                    files = git(d, 'diff', '--name-only', f'{default}...{sha}').split()
                    tops = {}
                    for f in files:
                        tops[f.split('/')[0]] = tops.get(f.split('/')[0], 0) + 1
                    row.update(n_files=len(files), top_dirs=sorted(tops.items(), key=lambda t: -t[1])[:5])
            if r in ups:
                row['upstream_contained'] = bool(git(d, 'for-each-ref', '--contains', sha, '--format=x', 'refs/upstream').strip())
                emails = git(d, 'log', '--format=%ae', sha, '--not', '--glob=refs/upstream/*').split()
                mine = [e for e in emails if (a.self_email and e.lower() == a.self_email.lower())
                        or (e.endswith('@users.noreply.github.com') and a.owner.lower() in e.lower())]
                row.update(not_in_upstream=len(emails), own_commits=len(mine))
            rows.append(row)
        inv[r] = dict(private=r not in a.public, default=default, branches=rows, fork_of=ups.get(r))
        print(r, len(rows), flush=True)
    json.dump(inv, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
