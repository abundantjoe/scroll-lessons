#!/usr/bin/env bash
# Provenance: Project HERCULES | owner the owner | [id removed]
# P4-O harness batch prep (DECL-REMOTE-HARNESS-1 items 2-4, DECL-P4-14-A1, sigma2t), rh-e2 procedure.
# usage: prep_batch.sh <k> <stage> <builder_branch> <manifest_path_in_ref>
# Stage batch o<k>s<stage> (DECL-P4-14-A3 item 2): only tiles not read in earlier stages o<k>s1..s<stage-1>
# (overlapping tiles must be byte-identical to the earlier read); eligible if the new tiles include >= 3 gate
# tiles (c5-c8) and >= 4 title-zone tiles (c9-c19). N0 = n<batch>, ceil(n/8) rot-90 copies from this batch only.
# Writes COMMIT A under logs/sib/pairs0814b/rh/O<k>/A/<batch> and pushes it BEFORE any reader. Numbers and hashes only.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
k=$1; st=$2; BR=$3; MAN=$4
STRIP=20260701183124-w010-027
b=o${k}s$st; A=logs/sib/pairs0814b/rh/O$k/A/$b; W=/work/rh/$b
PRIOR=$(for ((j=1; j<st; j++)); do printf "o%ss%s " $k $j; done)
[ -e "$A/builder_ref.json" ] && { echo "commit A for $b already exists"; exit 1; }
RESUME=0
if [ -e /srv/scorer/p4_key_$b.json ]; then
  [ -e /srv/scorer/p4_key_n$b.json ] && [ -e /work/p4/jobs_census_$b.json ] && [ -e "$W/manifest_norm_$b.json" ] || { echo "partial state for $b"; exit 1; }
  RESUME=1; echo "RESUME packaging for $b (keys/jobs exist, no commit A)"
else
  rm -rf "$W"
fi
git fetch -q origin "$BR"
REF=$(git rev-parse "origin/$BR")
[ $RESUME = 1 ] && REF=$(cat "$W/builder_ref_commit")
python3 - "$REF" "$MAN" <<'PY'
import json, subprocess, sys
m = json.loads(subprocess.run(['git', 'show', f'{sys.argv[1]}:{sys.argv[2]}'], capture_output=True, check=True).stdout)
assert m['segment'] == '20260701183124-w010-027', m['segment']
PY
TD=$(dirname "$MAN")/tiles
mkdir -p "$W" "$A/briefs" "$A/job_records"
if [ $RESUME = 0 ]; then
echo "$REF" > "$W/builder_ref_commit"
PYTHONPATH=src /opt/hv/bin/python tools/p4/norm_manifest.py "$REF" "$MAN" "$TD" "$W"
python3 - "$W" "$b" $PRIOR <<'PY'
import json, sys
W, b, prior = sys.argv[1], sys.argv[2], sys.argv[3:]
m = json.load(open(f'{W}/manifest_norm.json'))
seen = {}
for pb in prior:
    for v in json.load(open(f'logs/sib/pairs0814b/rh/O{pb[1]}/A/{pb}/p4_key_{pb}.json')).values():
        seen[(v['r'], v['c'])] = v['src_sha256']
changed = [(t['r'], t['c']) for t in m['tiles'] if (t['r'], t['c']) in seen and seen[(t['r'], t['c'])] != t['sha256']]
assert not changed, f'tiles changed since an earlier stage read: {changed}'
new = [t for t in m['tiles'] if (t['r'], t['c']) not in seen]
g = sum(5 <= t['c'] <= 8 for t in new); tz = sum(9 <= t['c'] <= 19 for t in new)
info = {'batch': b, 'prior_batches': prior, 'n_manifest': len(m['tiles']), 'n_prior_overlap_identical': len(m['tiles']) - len(new),
        'n_new': len(new), 'gate_tiles_c5_c8': g, 'title_tiles_c9_c19': tz, 'other_tiles': len(new) - g - tz,
        'stage_rule_met': g >= 3 and tz >= 4}
print(json.dumps(info))
assert info['stage_rule_met'], 'stage rule not met (>= 3 gate c5-c8 and >= 4 title c9-c19 new tiles)'
json.dump(dict(m, tiles=new, stage=info), open(f'{W}/manifest_norm_{b}.json', 'w'), indent=1)
PY
n=$(python3 -c "import json;print(len(json.load(open('$W/manifest_norm_$b.json'))['tiles']))")
nn=$(( (n + 7) / 8 ))
PYTHONPATH=src /opt/hv/bin/python tools/p4/p4_jobs.py import $STRIP "$W/tiles" "$W/manifest_norm_$b.json" $b | tee "$W/import.json"
PYTHONPATH=src /opt/hv/bin/python tools/p4/p4_jobs.py null n$b $nn $b | tee "$W/null.json"
PYTHONPATH=src /opt/hv/bin/python tools/p4/p4_jobs.py jobs census_$b $b n$b sigma2t | tee "$W/jobs.json"
fi
cp /srv/scorer/p4_key_$b.json /srv/scorer/p4_key_n$b.json /work/p4/jobs_census_$b.json "$W/manifest_norm.json" "$W/manifest_norm_$b.json" "$A/"
python3 - "$A" "$REF" "$BR" "$MAN" "$TD" "$b" <<'PY'
import hashlib, json, os, shutil, sys
A, ref, br, man, td, b = sys.argv[1:]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
jobs = json.load(open(f'{A}/jobs_census_{b}.json'))
ko, kn = json.load(open(f'{A}/p4_key_{b}.json')), json.load(open(f'{A}/p4_key_n{b}.json'))
ref_brief = open('logs/p4/ref_brief_sigma2t.txt', encoding='utf-8').read()
def template(b):
    return [ln for ln in b.split('\n') if not ln.startswith('/work/p4/img/') and not ln.startswith('age -r ')]
img, match = {}, True
for j in jobs['jobs']:
    jid = j['job']
    shutil.copyfile(f'/work/p4/brief_{jid}.txt', f'{A}/briefs/brief_{jid}.txt')
    shutil.copyfile(f'/work/jobs/{jid}.json', f'{A}/job_records/{jid}.json')
    rec = json.load(open(f'/work/jobs/{jid}.json'))
    bt = open(f'/work/p4/brief_{jid}.txt', encoding='utf-8').read()
    assert hashlib.sha256(bt.encode()).hexdigest() == rec['brief_sha256']
    match &= template(bt) == template(ref_brief)
    for p, s in rec['image_sha256'].items():
        assert sha(p) == s
        if p.startswith('/work/p4/img/'):
            img[os.path.basename(p)[:-4]] = s
assert set(img) == set(ko) | set(kn), 'image set != keys'
code = ['tools/p4/norm_manifest.py', 'tools/p4/p4_jobs.py', 'tools/p4/score_p4.py', 'tools/p4/p4_phase2.py',
        'tools/p4/p4_ext.py', 'src/hercules/harness/audit.py', 'src/hercules/harness/jobs.py',
        'configs/briefs/keysheet_sigma2.png', 'configs/briefs/k_d2_task_sigma2t.txt', 'logs/p4/ref_brief_sigma2t.txt']
json.dump(dict(sorted(img.items())), open(f'{A}/img_manifest.json', 'w'), indent=1)
json.dump({'batch': b, 'declaration': 'DECL-P4-14, -A1, -A2, -A3 item 2; DECL-REMOTE-HARNESS-1; DECL-P4-12-A1',
           'builder_branch': br, 'builder_commit': ref, 'builder_manifest_partial': json.loads(__import__("subprocess").run(["git","show",f"{ref}:{man}"],capture_output=True).stdout).get("partial"), 'manifest': man,
           'tiles_dir': td, 'stage': json.load(open(f'{A}/manifest_norm_{b}.json'))['stage'], 'orchestrator_base_commit': 'e1c687d', 'variant': jobs['variant'],
           'recipient': open('/srv/scorer/seal.agekey.pub').read().strip(),
           'key_sha256': {f'p4_key_{b}.json': sha(f'{A}/p4_key_{b}.json'), f'p4_key_n{b}.json': sha(f'{A}/p4_key_n{b}.json')},
           'code_sha256': {p: sha(p) for p in code + ['tools/p4/rh_verify.py', 'tools/sib/pairs0814b/rh/prep_batch.sh']}, 'n_images': len(img), 'n_census': len(ko), 'n_null': len(kn),
           'n_jobs': len(jobs['jobs']), 'briefs_match_ref_sigma2t_template': match}, open(f'{A}/builder_ref.json', 'w'), indent=1)
print(json.dumps({'n_census': len(ko), 'n_null': len(kn), 'n_jobs': len(jobs['jobs']), 'briefs_match': match}))
assert match, 'brief template mismatch'
PY
(cd "$A" && find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS)
git add "$A" tools/sib/pairs0814b/rh
git commit -q -F - <<MSG
rh pairs0814b COMMIT A $b: keys, jobs, briefs, img manifest, builder_ref (pre-read)

Provenance: Project HERCULES | owner the owner | [id removed]

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01NfS4bhpLVnt2ShveEY6pYF
MSG
for i in 1 2 3 4 5; do git push -q -u origin claude/gifted-bell-gavnl5-sib-pairs0814b && break; sleep $((2**i)); done
git fetch -q origin claude/gifted-bell-gavnl5-sib-pairs0814b
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/claude/gifted-bell-gavnl5-sib-pairs0814b)" ] && echo "COMMIT_A_PUSHED $b $(git rev-parse --short HEAD)"
