# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-26-A2 item 4: facing geometry for every w010-027 tile (own-lead grid, T = 8343 px, canvas
69760 x 170000, tiles r0-r8 x c0-c20), both directions. Geometry only: no CT, no image.

Method = DECL-P4-26-A1 fallback (4) (facing_fallback.py): from each valid tile vertex (winding
k = floor(s)) along its unit vertex normal, the official w010-027 mesh's surface of winding
  OUTER: k+1 along +n_out (the side this tile's VERSO faces; the outer winding's recto touches it)
  INNER: k-1 along -n_out (the side this tile's recto faces)
within 250 um, found by iterated local planes (3 iterations) on the target winding's vertices (rows
g0-60..g1+60) and accepted if the final point lies within 10 um of the target's local plane.
n_out = mesh_audit normals oriented away from the umbilicus by tile majority (p4-depth sign.json:
recto = inward). The hit is mapped to the target's canvas position: nearest target vertex (row, col)
plus the least-squares sub-cell offset along its grid tangents; canvas = 20 x grid (scale 0.05).
Outputs per tile: coverage (hits / valid vertices with a finite normal), median canvas displacement
(dy, dx) = facing canvas - source canvas, and a 32 x 32 correspondence field (cell centres of the
tile; source = nearest grid vertex; facing canvas row/col, NaN where none).
Windings with no k+1 (w027) or k-1 (w010) inside this mesh have no target: coverage 0 there.
usage: facing_all.py <mesh_dir> <out_dir> <shard k/n> [budget_s]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_audit import normals  # noqa: E402

T = 8343
NR, NC = 9, 21
T_MAX_VOX = 250 / 2.4
NGRID = 32
ORDER = [c for c in range(14, 21)] + [c for c in range(9, 14)] + [c for c in range(0, 9)]


def load(mesh_dir):
    d = Path(mesh_dir)
    X, Y, Z = (np.load(d / f'{c}.npy') for c in 'xyz')
    V = (X != -1) & np.isfinite(Z) & (Z > 0)
    P = np.stack([X, Y, Z], -1).astype(np.float32)
    S = np.load(d / 's.npy')
    a = json.load(open(d / 'umb.json'))
    U = np.array(sorted([[p['z'], p['x'], p['y']] for p in a['control_points']]), float)
    return P, V & np.isfinite(S), S, U


def out_normals(Pt, v, U):
    N = normals(np.where(v[..., None], Pt, np.nan))
    ux = np.interp(Pt[..., 2], U[:, 0], U[:, 1])
    uy = np.interp(Pt[..., 2], U[:, 0], U[:, 2])
    dot = N[..., 0] * (Pt[..., 0] - ux) + N[..., 1] * (Pt[..., 1] - uy)
    ok = v & np.isfinite(dot)
    return (1.0 if np.nanmedian(dot[ok]) >= 0 else -1.0) * N, ok


def hits(P, V, S, g0, g1, src_pts, src_k, dirs, dk):
    """Returns facing grid (row, col) float (NaN if none) for each source point."""
    H = V.shape[0]
    ra, rb = max(0, g0 - 60), min(H, g1 + 60)
    Pr = P[ra:rb].astype(np.float64)
    Vr = V[ra:rb]
    Kr = np.floor(S[ra:rb])
    out = np.full((len(src_pts), 2), np.nan)
    for k in np.unique(src_k):
        sel = np.where(src_k == k)[0]
        m = Vr & (Kr == k + dk)
        if m.sum() < 100:
            continue
        cols = np.where(m.any(0))[0]
        c0, c1 = cols.min(), cols.max() + 1
        blk = np.where(m[:, c0:c1, None], Pr[:, c0:c1], np.nan)
        Nb = normals(blk)
        mm = m[:, c0:c1] & np.all(np.isfinite(Nb), -1)
        QI = np.argwhere(mm)
        Q = blk[mm]
        NQ = Nb[mm]
        tree = cKDTree(Q)
        p = src_pts[sel]
        n = dirs[sel]
        x = p + n * (T_MAX_VOX / 2)
        t = np.full(len(p), np.nan)
        for _ in range(3):
            _, j = tree.query(x)
            den = np.sum(n * NQ[j], 1)
            t = np.where(np.abs(den) > 0.2, np.sum((Q[j] - p) * NQ[j], 1) / np.where(den == 0, 1, den), np.nan)
            x = p + n * np.nan_to_num(t)[:, None]
        _, j = tree.query(x)
        resid = np.abs(np.sum((x - Q[j]) * NQ[j], 1)) * 2.4
        good = np.isfinite(t) & (t > 0) & (t <= T_MAX_VOX) & (resid <= 10)
        # sub-cell position along the target's grid tangents
        rr, cc = QI[j, 0], QI[j, 1]
        rr1 = np.clip(rr + 1, 0, blk.shape[0] - 1)
        cc1 = np.clip(cc + 1, 0, blk.shape[1] - 1)
        du = blk[rr, cc1] - blk[rr, cc]
        dv = blk[rr1, cc] - blk[rr, cc]
        d = x - Q[j]
        A = np.stack([du, dv], -1)                      # (n, 3, 2)
        ab = np.full((len(p), 2), 0.0)
        okA = np.all(np.isfinite(A), axis=(1, 2))
        if okA.any():
            AtA = np.einsum('nij,nik->njk', A[okA], A[okA])
            Atd = np.einsum('nij,ni->nj', A[okA], d[okA])
            det = AtA[:, 0, 0] * AtA[:, 1, 1] - AtA[:, 0, 1] ** 2
            inv = np.stack([np.stack([AtA[:, 1, 1], -AtA[:, 0, 1]], -1), np.stack([-AtA[:, 1, 0], AtA[:, 0, 0]], -1)], 1) / np.where(det == 0, np.nan, det)[:, None, None]
            ab[okA] = np.clip(np.einsum('njk,nk->nj', inv, Atd), -1, 1)
        fr = (ra + rr + ab[:, 1]).astype(float)
        fc = (c0 + cc + ab[:, 0]).astype(float)
        res = np.where(good[:, None], np.stack([fr, fc], 1), np.nan)
        out[sel] = res
    return out


def tile(P, V, S, U, r, c):
    H, W = V.shape
    g0, g1 = (r * T) // 20, min(H, -(-((r + 1) * T) // 20))
    h0, h1 = (c * T) // 20, min(W, -(-((c + 1) * T) // 20))
    Pt = P[g0:g1, h0:h1].astype(np.float64)
    v = V[g0:g1, h0:h1]
    rec = {'tile': f'r{r}_c{c}', 'grid_rows': [g0, g1], 'grid_cols': [h0, h1], 'n_valid': int(v.sum())}
    if v.sum() < 100:
        rec['skip'] = 'fewer than 100 valid vertices'
        return rec, None
    Nout, ok = out_normals(Pt, v, U)
    idx = np.argwhere(ok)
    src = Pt[ok]
    K = np.floor(S[g0:g1, h0:h1])[ok]
    src_canvas = np.stack([(idx[:, 0] + g0) * 20.0, (idx[:, 1] + h0) * 20.0], 1)
    fields = {}
    # 32 x 32 cell centres -> nearest source vertex index
    cy = r * T + (np.arange(NGRID) + 0.5) * T / NGRID
    cx = c * T + (np.arange(NGRID) + 0.5) * T / NGRID
    gi = np.clip(np.rint(cy / 20).astype(int) - g0, 0, g1 - g0 - 1)
    gj = np.clip(np.rint(cx / 20).astype(int) - h0, 0, h1 - h0 - 1)
    pos = -np.ones(v.shape, np.int64)
    pos[idx[:, 0], idx[:, 1]] = np.arange(len(idx))
    for name, sign, dk in (('outer', +1.0, +1), ('inner', -1.0, -1)):
        f = hits(P, V, S, g0, g1, src, K, sign * Nout[ok], dk)
        found = np.all(np.isfinite(f), 1)
        disp = f[found] * 20.0 - src_canvas[found]
        rec[name] = {'coverage': float(found.mean()) if len(found) else 0.0,
                     'n_hits': int(found.sum()), 'n_sources': int(len(found)),
                     'median_dy_px': float(np.median(disp[:, 0])) if found.any() else None,
                     'median_dx_px': float(np.median(disp[:, 1])) if found.any() else None,
                     'iqr_dy_px': [float(np.percentile(disp[:, 0], 25)), float(np.percentile(disp[:, 0], 75))] if found.any() else None,
                     'iqr_dx_px': [float(np.percentile(disp[:, 1], 25)), float(np.percentile(disp[:, 1], 75))] if found.any() else None,
                     'target_winding': f'k{dk:+d} of the source winding (floor(s)); w027 has no outer and w010 no inner target in this mesh'}
        F = np.full((NGRID, NGRID, 2), np.nan, np.float32)
        pi = pos[gi[:, None], gj[None, :]]
        okc = pi >= 0
        F[okc] = (f[pi[okc]] * 20.0).astype(np.float32)
        fields[name] = F
    rec['field_rule'] = '32 x 32 cells of the tile; source = nearest grid vertex to the cell centre; value = facing canvas (row, col) px, NaN where none'
    return rec, fields


def main(mesh_dir, out_dir, shard, budget=1e9):
    k_sh, n_sh = map(int, shard.split('/'))
    budget = float(budget)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    P, V, S, U = load(mesh_dir)
    tiles = [(r, c) for c in ORDER for r in range(NR)]
    t0 = time.time()
    for (r, c) in tiles[k_sh::n_sh]:
        f = out / f'r{r}_c{c}.json'
        if f.exists():
            continue
        if time.time() - t0 > budget:
            print('BUDGET_EXIT', flush=True)
            return
        ts = time.time()
        rec, fields = tile(P, V, S, U, r, c)
        rec['wall_s'] = round(time.time() - ts, 1)
        if fields is not None:
            np.savez_compressed(out / f'r{r}_c{c}.npz', outer=fields['outer'], inner=fields['inner'])
        json.dump(rec, open(f, 'w'), indent=1)
        print(json.dumps({'tile': rec['tile'], 'outer': (rec.get('outer') or {}).get('coverage'), 'inner': (rec.get('inner') or {}).get('coverage'), 'wall_s': rec['wall_s']}), flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:])
