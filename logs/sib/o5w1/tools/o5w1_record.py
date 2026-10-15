#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""o5w1: progress (STATUS.md) and final records for the one DECL-P4-14-A3 tile. Numbers and hashes only."""
import hashlib, json, os, sys, time, glob
REPO = '/home/user/dominion'
OUT = f'{REPO}/logs/sib/o5w1/p4o/PHerc.1667-iteration-5'
FN = '20260701183124-w010-027_r0_c7.png'
CKB = '/work/o5w1/ckb'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()
def utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
start = open('/work/o5w1/start_utc').read().strip()
code = dict(commit='98cd07501bbd3ec4dd0d1f09bf6101389f458080', branch='claude/gifted-bell-gavnl5-sib-ckpt-screen-b',
            p4o_tiles_sha256=sha(f'{CKB}/tools/sib/ckpt-screen-b/p4o_tiles.py'),
            infer_1667_sha256=sha(f'{CKB}/tools/sib/ckpt-screen-b/infer_1667.py'),
            fetch_sha256=sha(f'{CKB}/tools/sib/ckpt-screen-b/fetch.py'))
ck = json.load(open('/work/o5w1/fetch2.json'))
jp = f'{OUT}/tiles/{FN}.json'
if sys.argv[1] == 'status':
    n = json.load(open(f'/work/p4o/it5/ckpt/{FN}/n.json')) if os.path.exists(f'/work/p4o/it5/ckpt/{FN}/n.json') else None
    logs = glob.glob(f'{OUT}/run_*.log')
    tot = None
    for lp in logs:
        for l in open(lp):
            d = json.loads(l)
            if 'windows' in d: tot = d['windows']
    alive = os.path.exists('/proc/%s' % open('/work/o5w1/worker.pid').read().strip())
    s = open(f'{REPO}/logs/sib/o5w1/STATUS.md').read().split('\n## Progress')[0]
    s += (f'\n## Progress ({utc()})\n- worker alive: {alive}; tile r0 c7 started {start}; windows total {tot}; '
          f'last 15-min checkpoint at window {n["n"] if n else "none yet"} ({n["utc"] if n else "-"}); done: {os.path.exists(jp)}.\n')
    open(f'{REPO}/logs/sib/o5w1/STATUS.md', 'w').write(s)
else:
    rec = json.load(open(jp))
    png = f'{OUT}/{rec["file"]}'
    assert sha(png) == rec['png_sha256'], 'png sha256 mismatch'
    end = rec['utc']
    t0 = time.mktime(time.strptime(start, '%Y-%m-%dT%H:%M:%SZ')); t1 = time.mktime(time.strptime(end, '%Y-%m-%dT%H:%M:%SZ'))
    out = dict(provenance=PROV, declaration='RULES.md DECL-P4-14-A3', worker='o5w1',
               branch='claude/gifted-bell-gavnl5-sib-o5w1', tile=dict(segment='20260701183124-w010-027', r=0, c=7, file=rec['file']),
               material='M-P4O-PHerc.1667-iteration-5', code=code,
               checkpoint=dict(repo=ck['repo'], commit=ck['commit'], file='model.safetensors', sha256=ck['sha256'],
                               sha256_catalogue_ok=ck['verified'], bytes=ck['bytes']),
               depth_orders=[rec['order']], slices=rec['slices'], png_sha256=rec['png_sha256'],
               full_res_u8_sha256=rec['full_res_u8_sha256'], start_utc=start, end_utc=end,
               runtime_s=int(t1 - t0), builder_seconds_total=rec['seconds_total'], threads=4,
               out_path_note='WORKER.md layout re-rooted under logs/sib/o5w1/ (task instruction); --out is an output path only, no geometry option passed',
               viewing='no tile, map or CT image was opened, displayed or described; numbers and hashes only')
    json.dump(out, open(f'{REPO}/logs/sib/o5w1/o5w1_r0_c7.json', 'w'), indent=1)
    os.makedirs(f'{REPO}/logs/sib/o5w1/p4o/fleet', exist_ok=True)
    json.dump(dict(worker='o5w1', branch='claude/gifted-bell-gavnl5-sib-o5w1', tile=[0, 7], code_commit='98cd075',
                   p4o_tiles_sha256=code['p4o_tiles_sha256'], infer_1667_sha256=code['infer_1667_sha256'],
                   png_sha256=rec['png_sha256']), open(f'{REPO}/logs/sib/o5w1/p4o/fleet/o5w1.json', 'w'), indent=1)
    print(json.dumps(out))
