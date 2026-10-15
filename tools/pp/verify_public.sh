#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# READY check (RULES.md DECL-PP-1-A2 item 2 a-d) for one published Progress Prize repository.
# usage: tools/pp/verify_public.sh <tool>   -> prints a JSON verdict; the report goes to logs/pp/verify_<tool>.json
set -u
tool="$1"
repo="https://github.com/abundantjoe/$tool"
work="${TMPDIR:-/tmp}/ppverify_$tool"
rm -rf "$work" && mkdir -p "$work"
cd "$work" || exit 1
git clone -q "$repo" src 2>clone.err || { echo "{\"tool\":\"$tool\",\"clone\":false}"; exit 1; }
cd src
sha=$(git rev-parse HEAD); ncommits=$(git rev-list --count HEAD)
python3 -m venv ../venv >/dev/null 2>&1
. ../venv/bin/activate
pip -q install --upgrade pip >/dev/null 2>&1
inst=0; pip -q install -e ".[test]" >../pip.log 2>&1 || pip -q install -e . >>../pip.log 2>&1 || inst=1
pip -q install pytest >>../pip.log 2>&1
pytest -q -p no:cacheprovider >../pytest.log 2>&1; prc=$?
summary=$(tail -1 ../pytest.log)
deactivate
readme=$(ls README* 2>/dev/null | head -1)
chk() { grep -q -F "$1" "$readme" 2>/dev/null && echo true || echo false; }
cit_vc=$(chk "Vesuvius Challenge - CT Scans of Herculaneum Papyri")
cit_auth=$(chk "Giorgio Angelotti, Stephen Parsons, Sean Johnson")
lic=$( [ -f LICENSE ] && grep -q -i "MIT" LICENSE && echo true || echo false)
data_lic=$(grep -r -l -i "CC BY-NC 4.0\|CC-BY-NC 4.0\|CC‑BY‑NC 4.0" . --include=*.md 2>/dev/null | head -1)
ai=$(grep -q -i "AI coding agents" "$readme" 2>/dev/null && echo true || echo false)
leak=$(grep -r -n -I -E "/srv/|/work/|scratchpad|HERCULES|RULES\.md|w010-027|w028-037|HRC-JB|claude/gifted|age1[a-z0-9]{20}|BEGIN (RSA|OPENSSH|EC) PRIVATE|ghp_[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}" . --exclude-dir=.git 2>/dev/null | head -5)
cd /home/user/dominion
python3 - "$tool" "$sha" "$ncommits" "$inst" "$prc" "$summary" "$cit_vc" "$cit_auth" "$lic" "$data_lic" "$ai" "$leak" <<'EOF'
import json, sys
t, sha, n, inst, prc, summ, cvc, cau, lic, dl, ai, leak = sys.argv[1:13]
v = {'tool': t, 'commit': sha, 'n_commits': int(n), 'install_ok': inst == '0', 'pytest_rc': int(prc),
     'pytest_summary': summ, 'readme_cites_vc_dataset': cvc == 'true', 'readme_cites_vc_authors': cau == 'true',
     'license_mit': lic == 'true', 'data_licence_file': dl or None, 'ai_disclosure': ai == 'true',
     'leak_hits': leak.splitlines() if leak else []}
v['auto_checks_pass'] = (v['install_ok'] and v['pytest_rc'] == 0 and v['readme_cites_vc_dataset']
                         and v['readme_cites_vc_authors'] and v['license_mit'] and v['ai_disclosure']
                         and not v['leak_hits'])
json.dump(v, open(f'logs/pp/verify_{t}.json', 'w'), indent=1)
print(json.dumps(v))
EOF
