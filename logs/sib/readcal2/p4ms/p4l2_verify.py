# Provenance: Project HERCULES | owner the owner | [id removed]
"""End-to-end check of p4ms on the real P4-L L2 material (numbers and hashes only; nothing is viewed).

Channel source = the p4-l2 builder's own code (tools/sib/p4-l2/l2.py from origin/claude/gifted-bell-gavnl5-sib-p4-l2,
copied to /work/rc2/p4/l2.py, sha256 recorded): canvas_mask(load_valid(mesh)) and region() = level-0 max over slices
48..60, streamed by range requests. Mapping = global T_mid / T_hi from the L2 manifest.
1. S2 reproduction: rebuild the S2 image of --tiles and compare its PNG sha256 with the L2 manifest (must be equal).
2. Smoke: build S4 for the block at --block and S1 for its 4 tiles' quadrants; record hashes, valid fractions and
   mapping parameters only (images go to /work/rc2/p4/smoke, never opened, never pushed).
Output: logs/sib/readcal2/p4ms/verify_l2.json. Usage: python p4l2_verify.py --tiles 0,0 3,5 --block 0,0"""
import argparse
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
import p4ms as P  # noqa: E402

W = '/work/rc2/p4'
MESH = 'PHercParis4/segments/20260701183124-w010-027/mesh/20260701183124-on-20260411134726-2.4um.tifxyz'


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tiles', nargs='+', default=['0,0'])
    ap.add_argument('--block', default='0,0')
    ap.add_argument('--l2s', action='store_true', help='verify S2 against the L2S manifest (window mode, max > 0)')
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location('l2', f'{W}/l2.py')
    L2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(L2)
    man = json.load(open(f'{W}/l2_manifest.json'))
    ref_man = json.load(open(f'{W}/l2s_manifest.json')) if a.l2s else man
    mode_kw = dict(mode='window', positive_only=True) if a.l2s else dict(mode='global')
    grid = P.Grid.from_json(json.load(open(f'{W}/e2_grid.json')))
    mesh_dir = f'/work/rc2/s3/{MESH}'
    for n in ('x.tif', 'y.tif', 'z.tif', 'meta.json'):
        want = man['input_sha256'][f'{MESH}/{n}']
        assert sha_file(f'{mesh_dir}/{n}') == want, n
    valid = L2.load_valid(mesh_dir)
    H, Wc = grid.canvas_hw
    ex = cf.ThreadPoolExecutor(16)

    def source(y0, y1, x0, x1):
        m = L2.canvas_mask(valid, H, Wc, y0, y1, x0, x1)
        out, _, _, _ = L2.region(L2.SEG, y0, y1, x0, x1, (H, Wc), m, ex)
        return out, m
    th = man['thresholds']
    rec = {'provenance': P.PROV, 'l2_py_sha256': sha_file(f'{W}/l2.py'), 'l2_manifest_sha256': sha_file(f'{W}/l2_manifest.json'),
           'grid_sha256': sha_file(f'{W}/e2_grid.json'), 'thresholds': th, 'viewing': 'no image opened; hashes only'}
    tiles = ref_man['tiles']
    want = {(t['r'], t['c']): t for t in tiles}
    t0 = time.time()
    chk = []
    for s in a.tiles:
        r, c = (int(x) for x in s.split(','))
        sub = [want[(r, c)]]
        b = P.build(grid, sub, source, mode_kw['mode'], f'{W}/verify', 20260926, scales=('S2',), t_mid=th['T_mid'],
                    t_hi=th['T_hi'], positive_only=mode_kw.get('positive_only', False))
        v = P.verify_s2_against_manifest(b, sub)
        chk.append({'r': r, 'c': c, **v, 'built_sha256': list(b['manifest'].values()), 'manifest_sha256': want[(r, c)]['png_sha256']})
        print('S2', r, c, v, round(time.time() - t0, 1), flush=True)
    rec['s2_reproduction'] = chk
    rec['mode'] = mode_kw
    if a.l2s:
        rec['l2s_manifest_sha256'] = sha_file(f'{W}/l2s_manifest.json')
        open(os.path.join(HERE, 'verify_l2s.json'), 'w').write(json.dumps(rec, indent=1) + '\n')
        print(json.dumps({'s2_all_equal': all(x['all_equal'] for x in chk)}))
        return
    br, bc = (int(x) for x in a.block.split(','))
    blk = [want[k] for k in ((br, bc), (br + 1, bc), (br, bc + 1), (br + 1, bc + 1)) if k in want]
    b = P.build(grid, blk, source, 'global', f'{W}/smoke', 20260926, scales=('S4', 'S1'), t_mid=th['T_mid'], t_hi=th['T_hi'])
    rec['smoke'] = {'block': [br, bc], 'n_member_tiles': len(blk),
                    'images': {u: {k: v for k, v in b['key'][u].items() if k != 'map'} | {'sha256': b['manifest'][u],
                               'valid_fraction': b['key'][u]['map']['valid_fraction']} for u in b['key']},
                    'skipped': b['skipped'], 'seconds': round(time.time() - t0, 1)}
    open(os.path.join(HERE, 'verify_l2.json'), 'w').write(json.dumps(rec, indent=1) + '\n')
    print(json.dumps({'s2_all_equal': all(x['all_equal'] for x in chk), 'n_smoke': len(b['key']), 'skipped': len(b['skipped'])}))


if __name__ == '__main__':
    main()
