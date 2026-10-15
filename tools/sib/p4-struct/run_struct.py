"""P4-I runner (RULES.md DECL-P4-8). Numbers only: tiles are read as uint8 arrays, never shown.

usage: python3 run_struct.py --data <dir holding logs/sib/... extracted from the builder branches>
                             --out logs/sib/p4-struct [--variant declared|anchored --decl <id>]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import struct_core as sc  # noqa: E402
import struct_rules as sr  # noqa: E402

PROV = 'Project HERCULES | owner the owner | [id removed]'
B = 'origin/claude/gifted-bell-gavnl5-sib-'

# strip, role, branch, manifest dir, eligibility, labelled-adjacency flags (file, per DECL-P4-8 item 4)
STRIPS = {
    'M1':   dict(material='M1', role='title', branch='p4-tiles-a', dir='logs/sib/p4-tiles-a', elig='all',
                 excl=('p4-excl', 'logs/sib/p4-excl/excl_a.json')),
    'M1-b': dict(material='M1', role='control', branch='p4-tiles-b', dir='logs/sib/p4-tiles-b', elig='all',
                 excl=None),
    'M2a':  dict(material='M2', role='title', branch='p4-tiles-a', dir='logs/sib/p4-tiles-a/m2a', elig='A1',
                 excl=('p4-excl', 'logs/sib/p4-excl/excl_d_a.json')),
    'M2b':  dict(material='M2', role='control', branch='p4-tiles-b', dir='logs/sib/p4-tiles-b/m2b', elig='A1',
                 excl=None),
    'E1-A1': dict(material='E1', role='title', branch='p4-tiles-b', dir='logs/sib/p4-tiles-b/e1a1', elig='A1',
                  excl=('p4-excl', 'logs/sib/p4-excl/excl_d_a.json')),
    'E2':   dict(material='E2', role='title', branch='pairs0814b', dir='logs/sib/pairs0814b/e2', elig='all',
                 excl=('p4-excl', 'logs/sib/p4-excl/excl_a.json')),
    'P4-F': dict(material='P4F', role='title', branch='p4-highz', dir='logs/sib/p4-highz/f1', elig='A1',
                 excl=('p4-excl', 'logs/sib/p4-excl/excl_d_a.json')),
}
SAME_GRID = ['M2a', 'E1-A1', 'P4-F']     # DECL-P4-8 item 6


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True, check=True).stdout.strip()


def frac_outside(t):
    """METRIC-HASH-29 norm_manifest semantics: stats first, else top level, else frac_outside; missing -> None."""
    k = 'frac_mesh_points_outside_1129_volume'
    st = t.get('stats') or {}
    if k in st:
        return st[k]
    if k in t:
        return t[k]
    return t.get('frac_outside')


def eligible(t, rule):
    if t.get('valid_fraction', 0) < 0.5:
        return False
    if rule == 'A1':
        fo = frac_outside(t)
        return fo is not None and fo < 0.5
    return True


def load(path):
    return cv2.imread(path, cv2.IMREAD_UNCHANGED)


def work(job):
    key, path, p95, variant, theta_c = job
    a = load(path)
    m = sc.support_mask(a)
    r = sc.tile_stat(a, m)
    r90 = sc.tile_stat(np.rot90(a), np.rot90(m))
    out = dict(key=key, S_row=r['S_row'], theta_star=r['theta_star'], period_mm_at_peak=r['period_mm_at_peak'],
               insufficient=r['insufficient'], support_frac=r['support_frac'],
               S_row_rot90=r90['S_row'], theta_star_rot90=r90['theta_star'],
               M_ink=None if p95 is None else sc.m_ink(a, m, p95))
    if variant == 'anchored':
        out['S_anch'] = sc.s_anch(sc.tile_R(a, m), theta_c)
        out['S_anch_rot90'] = sc.s_anch(sc.tile_R(np.rot90(a), np.rot90(m)), theta_c)
    return out


def control_p95(paths):
    """Pixel p95 over all support pixels of all control tiles of the material (exact, via histogram)."""
    h = np.zeros(256, np.int64)
    for p in paths:
        a = load(p)
        h += np.bincount(a[sc.support_mask(a)].ravel(), minlength=256)
    c = np.cumsum(h) / h.sum()
    return int(np.searchsorted(c, 0.95)), int(h.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--variant', default='declared', choices=['declared', 'anchored'])
    ap.add_argument('--decl', default=None)
    ap.add_argument('--procs', type=int, default=4)
    a = ap.parse_args()
    if a.variant != 'declared' and not a.decl:
        sys.exit('the anchored variant is not declared (ASK-1); pass the declaration id with --decl')
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)

    # ---- inputs, sha256-checked against the builders' manifests
    inputs, tiles, excl = {}, {}, {}
    for name, S in STRIPS.items():
        d = os.path.join(a.data, S['dir'])
        mp = os.path.join(d, 'manifest.json')
        if not os.path.exists(mp):
            inputs[name] = dict(status='not available', branch=B + S['branch'], dir=S['dir'])
            continue
        mb = open(mp, 'rb').read()
        man = json.loads(mb)
        commit = git('rev-parse', B + S['branch'])
        ppm = man.get('px_per_mm')
        ppm_src = 'manifest.json px_per_mm'
        gp = os.path.join(d, 'grid.json')
        if ppm is None and os.path.exists(gp):
            ppm = json.load(open(gp)).get('px_per_mm')
            ppm_src = 'grid.json px_per_mm (same directory; manifest has none)'
        rows, bad = [], []
        for t in man['tiles']:
            if not eligible(t, S['elig']):
                continue
            p = os.path.join(d, t['file'])
            h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            if h != t['png_sha256']:
                bad.append(t['file'])
                continue
            rows.append(dict(r=t['r'], c=t['c'], path=p, sha256=h, valid_fraction=t['valid_fraction'],
                             frac_outside=frac_outside(t)))
        if bad:
            sys.exit(f'{name}: sha256 mismatch {bad[:5]}')
        inputs[name] = dict(status='ok', branch=B + S['branch'], commit=commit, manifest=S['dir'] + '/manifest.json',
                            manifest_sha256=hashlib.sha256(mb).hexdigest(), segment=man.get('segment'),
                            px_per_mm=ppm, px_per_mm_source=ppm_src, band_px=[3 * ppm, 9 * ppm] if ppm else None,
                            display_px_per_mm=sc.PX_PER_MM_DISPLAY, n_eligible=len(rows), n_sha256_ok=len(rows),
                            eligibility=S['elig'], material=S['material'], role=S['role'])
        tiles[name] = rows
        if S['excl']:
            ep = os.path.join(a.data, S['excl'][1])
            if os.path.exists(ep):
                eb = open(ep, 'rb').read()
                ej = json.loads(eb)['tiles']
                excl[name] = {k: bool(v.get('labelled_adjacent_union', v.get('labelled_adjacent')))
                              for k, v in ej.items()}
                inputs[name]['excl'] = dict(file=S['excl'][1], sha256=hashlib.sha256(eb).hexdigest(),
                                            commit=git('rev-parse', B + S['excl'][0]),
                                            field='labelled_adjacent_union (else labelled_adjacent)')
            else:
                inputs[name]['excl'] = dict(file=S['excl'][1], status='not available: never STRUCT-positive')

    # ---- per material
    mats = {}
    for name, S in STRIPS.items():
        if name in tiles:
            mats.setdefault(S['material'], []).append(name)
    p95 = {}
    for m, names in mats.items():
        ctrl = [n for n in names if STRIPS[n]['role'] == 'control']
        p95[m] = control_p95([r['path'] for n in ctrl for r in tiles[n]]) if ctrl else None

    results, jobs = {}, []
    for m, names in mats.items():
        for n in names:
            for r in tiles[n]:
                jobs.append(((n, r['r'], r['c']), r['path'], p95[m][0] if p95[m] else None, 'declared', None))
    with Pool(a.procs) as pool:
        for o in pool.imap_unordered(work, jobs, chunksize=4):
            results[o['key']] = o

    if a.variant == 'anchored':
        # PROPOSED (ASK-1), runs only with a declaration id. theta_c from the declared pass;
        # S_anch then replaces S_row in the null, gate and positive rules.
        theta_c = {}
        for m, names in mats.items():
            ctrl = {k: v for k, v in results.items() if k[0] in names and STRIPS[k[0]]['role'] == 'control'}
            theta_c[m] = sr.gate(ctrl, float('inf'))['theta_c_median_nonblank'] if ctrl else None
        jobs2 = [(j[0], j[1], j[2], 'anchored', theta_c[STRIPS[j[0][0]]['material']]) for j in jobs
                 if theta_c[STRIPS[j[0][0]]['material']] is not None]
        with Pool(a.procs) as pool:
            for o in pool.imap_unordered(work, jobs2, chunksize=4):
                v = results[o['key']]
                v['S_row_declared'], v['S_row_rot90_declared'] = v['S_row'], v['S_row_rot90']
                v['S_row'], v['S_row_rot90'] = o['S_anch'], o['S_anch_rot90']
                v['theta_c_anchor'] = theta_c[STRIPS[o['key'][0]]['material']]

    struct, gates, positives = {}, {}, {}
    for m, names in mats.items():
        allk = [k for k in results if k[0] in names]
        null = [results[k]['S_row_rot90'] for k in allk if results[k]['S_row_rot90'] is not None]
        T = float(np.percentile(null, 99)) if null else None
        ctrl_names = [n for n in names if STRIPS[n]['role'] == 'control']
        for k in allk:
            v = results[k]
            n = k[0]
            if STRIPS[n]['role'] == 'title':
                if n in excl:
                    v['labelled_adjacent'] = excl[n].get(f'r{k[1]}_c{k[2]}')
                else:
                    v['labelled_adjacent'] = None
        ident = [abs(results[k]['S_row'] - results[k]['S_row_rot90']) / results[k]['S_row']
                 for k in allk if results[k]['S_row'] is not None]
        g = dict(material=m, strips=names, n_tiles=len(allk), n_null=len(null), T_mat_p99_rot90=T,
                 null_quantiles=dict(zip(['p50', 'p90', 'p99', 'max'], np.percentile(null, [50, 90, 99, 100]).tolist())) if null else None,
                 rot90_invariance_max_rel_diff=float(max(ident)) if ident else None,
                 n_insufficient=sum(1 for k in allk if results[k]['insufficient']))
        if ctrl_names:
            ctrl = {k: results[k] for k in allk if k[0] in ctrl_names}
            g.update(sr.gate(ctrl, T))
            g['control_pixel_p95'] = p95[m][0]
            g['control_pixels'] = p95[m][1]
            cs = [v['S_row'] for v in ctrl.values() if v['S_row'] is not None]
            c90 = [v['S_row_rot90'] for v in ctrl.values() if v['S_row_rot90'] is not None]
            g['auc_control_vs_rot90'] = sc.auc(cs, c90)
            g['theta_c_median_all_control'] = sc.circ_median([v['theta_star'] for v in ctrl.values()])
            g['status'] = 'passed' if g['pass'] else 'uninformative (gate failed)'
        else:
            g.update({'pass': False, 'status': 'uninformative (gate not evaluable: no known-text control on this material; ASK-2)'})
            g['theta_c_median_nonblank'] = None
        gates[m] = g
        title = {k: results[k] for k in allk if STRIPS[k[0]]['role'] == 'title'}
        pos = sr.struct_positive(title, T, g.get('theta_c_median_nonblank'), g['pass'])
        # descriptive, not a rule: how many title tiles would pass S_row/theta without the gate or flags
        g['descriptive_title_above_T'] = sum(1 for v in title.values() if v['S_row'] is not None and v['S_row'] > T)
        for n in names:
            if STRIPS[n]['role'] == 'title':
                positives[n] = [f'r{k[1]}_c{k[2]}' for k in pos if k[0] == n]
        for k in allk:
            v = results[k]
            struct.setdefault(k[0], {})[f'r{k[1]}_c{k[2]}'] = {kk: vv for kk, vv in v.items() if kk != 'key'}

    # ---- validation item 6: Jaccard across the same grid
    jac = {}
    present = [n for n in SAME_GRID if n in tiles]
    for i in range(len(present)):
        for j in range(i + 1, len(present)):
            x, y = present[i], present[j]
            U = {f'r{r["r"]}_c{r["c"]}' for r in tiles[x]} & {f'r{r["r"]}_c{r["c"]}' for r in tiles[y]}
            A = set(positives.get(x, [])) & U
            Bs = set(positives.get(y, [])) & U
            jv, p = sc.jaccard_perm_p(A, Bs, U)
            jac[f'{x}|{y}'] = dict(n_common_tiles=len(U), n_pos=[len(A), len(Bs)], jaccard=jv, perm_p=p,
                                   note=None if jv is not None else 'undefined: both STRUCT-positive sets are empty')
    missing = [n for n in SAME_GRID if n not in tiles]

    meta = dict(provenance=PROV, declaration='RULES.md DECL-P4-8', variant=a.variant, decl=a.decl,
                utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                code={f: hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f), 'rb').read()).hexdigest()
                      for f in ('struct_core.py', 'struct_rules.py', 'run_struct.py', 'test_struct.py')},
                params=sc.PARAMS, secs=round(time.time() - t0, 1),
                viewing='no image, tile or CT pixel was opened, displayed or described; arrays only')
    json.dump(dict(meta=meta, inputs=inputs, tiles=struct), open(os.path.join(a.out, 'struct.json'), 'w'), indent=1)
    json.dump(dict(meta=meta, gates=gates), open(os.path.join(a.out, 'gates.json'), 'w'), indent=1)
    json.dump(dict(meta=meta, positives=positives, jaccard_same_grid=jac, same_grid_missing=missing),
              open(os.path.join(a.out, 'positives.json'), 'w'), indent=1)
    print(json.dumps(dict(gates=gates, positives=positives, jaccard=jac), indent=1, default=str))


if __name__ == '__main__':
    main()
