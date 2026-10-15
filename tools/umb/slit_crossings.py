#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1-A1 bar M5b at full level-3 resolution: for every section with a topological core, cast vertical rays up and
down (perpendicular to the slit) from 5 points along the slit and count layer crossings in the slab-mean image; a closed
loop crosses each vertical line through the slit exactly twice, so |N_up - N_down| <= 1 and the totals agree along the
slit. Reads the volume again (y-slabs) and writes <out>/slit_crossings.json.
usage: slit_crossings.py <src> <out_dir> [--axis y] [--vox_um 69.12]
"""
import argparse, json, os, sys, numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from st_axis import open_source

def count_along(img, mask, p, direction, step=0.5, smooth=1.0):
    Y, X = img.shape; sm = ndi.gaussian_filter(img, smooth); rs = np.arange(0, max(X, Y), step); xs, ys = p[0] + rs * direction[0], p[1] + rs * direction[1]
    ok = (xs >= 0) & (xs < X - 1) & (ys >= 0) & (ys < Y - 1); xs, ys = xs[ok], ys[ok]
    inm = ndi.map_coordinates(mask.astype(np.float32), [ys, xs], order=0) > 0.5
    if inm.sum() < 10: return 0, 0.0
    last = np.nonzero(inm)[0].max(); prof = ndi.map_coordinates(sm, [ys[:last], xs[:last]], order=1)
    if len(prof) < 5: return 0, 0.0
    thr = 0.25 * prof.std(); pk = (prof[1:-1] > prof[:-2]) & (prof[1:-1] >= prof[2:]) & (prof[1:-1] - np.minimum(prof[:-2], prof[2:]) > thr); return int(pk.sum()), float(last * step)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--axis', default='y'); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--slab', type=int, default=16)
    a = ap.parse_args(); T = json.load(open(os.path.join(a.out, 'topo.json')))['sections']; V = open_source(a.src, axis=0 if a.axis == 'z' else 1); mm = 1000.0 / a.vox_um; out = []
    for t in T:
        if t.get('status') != 'ok': continue
        z0 = int(t['z_mid'] - a.slab / 2 + 0.5); z1 = z0 + a.slab; stack = np.asarray(V[z0:z1]).astype(np.float32) / 255.0; img = stack.mean(0); mask = ndi.binary_erosion((stack > 0).mean(0) > 0.5, iterations=14)
        core = np.array(t['core']); ends = t.get('slit_ends')
        if ends: e1, e2 = np.array(ends[0]), np.array(ends[1]); u = (e2 - e1) / (np.linalg.norm(e2 - e1) + 1e-9); half = np.linalg.norm(e2 - e1) / 2
        else: u = np.array([1.0, 0.0]); half = 1.0 * mm
        v = np.array([-u[1], u[0]]); rows = []
        for f in np.linspace(-0.8, 0.8, 5):
            p = core + f * half * u; nu, lu = count_along(img, mask, p, v); nd, ld = count_along(img, mask, p, -v); rows.append({'f': round(float(f), 2), 'up': nu, 'down': nd, 'len_up_mm': round(lu / mm, 2), 'len_down_mm': round(ld / mm, 2)})
        tot = [r['up'] + r['down'] for r in rows]; rec = {'z_mid': t['z_mid'], 'kind': t['kind'], 'rows': rows, 'balanced_frac': round(float(np.mean([abs(r['up'] - r['down']) <= 1 for r in rows])), 2), 'total_spread': int(max(tot) - min(tot)), 'mean_total': round(float(np.mean(tot)), 1)}
        out.append(rec); print(json.dumps({k: rec[k] for k in ['z_mid', 'kind', 'balanced_frac', 'total_spread', 'mean_total']}), flush=True)
    json.dump(out, open(os.path.join(a.out, 'slit_crossings.json'), 'w'), indent=1)

if __name__ == '__main__': main()
