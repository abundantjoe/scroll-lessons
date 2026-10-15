"""P4-D (DECL-P4-4) labelled-adjacency for M2a / M2b tiles. Coordinates only.

usage: process_d.py <a|b> <npz> <commit> <blob> <npz_path_in_repo> <grid_json> <struct_dir> <mesh24_dir> <out>

npz flag: min over the tile's <key>__f20260411134726 points (builder's same-UV / affine points).
all-vertex flag: every valid vertex of the segment's official 20260411134726 tifxyz whose UV lies in the
tile's UV rectangle, widened by one 2.4 um grid cell on each side (fail-closed: never misses tile surface
between vertices at the edge; may include <= 1 cell (~20 vox, 0.05 mm) beyond the tile).
UV map (builder, verified in uv_check.json and re-verified here): i24 = (i + 0.5) * h24 / h1129 - 0.5.
labelled_adjacent = npz flag OR all-vertex flag (min_mm < 1.2).
"""
import sys, os, json, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
import process
from process import SEGS, VOX_MM, FLAG_MM, PROV, sha, per_tile

SEGID = {'a': '20260623141924-w010-027', 'b': '20260623142658-w028-037'}


def bilinear(G, V, i, j):
    i0 = np.floor(i).astype(int); j0 = np.floor(j).astype(int)
    fi = (i - i0)[:, None]; fj = (j - j0)[:, None]
    i1 = np.minimum(i0 + 1, G.shape[0] - 1); j1 = np.minimum(j0 + 1, G.shape[1] - 1)
    ok = V[i0, j0] & V[i1, j0] & V[i0, j1] & V[i1, j1]
    P = (G[i0, j0] * (1 - fi) * (1 - fj) + G[i1, j0] * fi * (1 - fj) + G[i0, j1] * (1 - fi) * fj
         + G[i1, j1] * fi * fj)
    return P, ok


def main():
    st, npz, commit, blob, rpath, gjson, sdir, mdir, out = sys.argv[1:10]
    process.SDIR = sdir; process.CKPT = None
    ck = os.environ.get('P4EXCL_CKPT')
    if ck:
        process.CKPT = os.path.join(ck, 'd_' + sha(npz)[:16]); os.makedirs(process.CKPT, exist_ok=True)
    t0 = time.time()
    z = np.load(npz); g = json.load(open(gjson))
    T = int(g['T_px'] if g.get('T_px') else g['T_canvas_px'])
    s = g.get('canvas_per_grid_scale_rows_cols') or [g['scale_canvas_per_grid']['rows'], g['scale_canvas_per_grid']['cols']]
    assert s[0] == s[1] and float(s[0]).is_integer()
    # schema: tiles-b m2b (__f20260411134726, _src, __grid_ij, __n_valid_vertices) or tiles-a m2a (__2p4 affine, __grid_rc)
    SB = any(k.endswith('__f20260411134726') for k in z.keys())
    K24, KIJ = ('__f20260411134726', '__grid_ij') if SB else ('__2p4', '__grid_rc')
    s = int(s[0]); h1, w1 = g['grid_shape']
    keys = sorted({k.split('__')[0] for k in z.keys()}, key=lambda k: tuple(int(t[1:]) for t in k.split('_')))
    G = np.stack([tifffile.imread(f'{mdir}/{c}.tif') for c in 'xyz'], -1).astype(np.float64)
    V = (G >= 0).all(-1) & np.isfinite(G).all(-1)
    h24, w24 = V.shape; ai, aj = h24 / h1, w24 / w1
    # re-verify the builder's same-UV points: bilinear of the 2.4 mesh at the mapped grid position
    chk = []
    P, tid, AV, atid, srcfrac, nav = [], [], [], [], {}, {}
    for n, k in enumerate(keys):
        p = np.asarray(z[k + K24], np.float64)
        src = z[k + '__f20260411134726_src'] if SB else np.full(len(p), 1, np.uint8)   # m2a: all affine
        ij = z[k + KIJ].astype(np.float64)
        q, ok = bilinear(G, V, (ij[:, 0] + 0.5) * ai - 0.5, (ij[:, 1] + 0.5) * aj - 0.5)
        m = ((src == 0) & ok) if SB else ok      # m2a: compare centre-map same-UV against the affine points
        chk.append(np.linalg.norm(q[m] - p[m], axis=1))
        srcfrac[k] = float((src == 1).mean())
        P.append(p); tid.append(np.full(len(p), n))
        r, c = (int(t[1:]) for t in k.split('_'))
        i0, i1 = -(-r * T // s), min(-(-(r + 1) * T // s), h1)     # 1.129 grid rows in tile [i0, i1)
        j0, j1 = -(-c * T // s), min(-(-(c + 1) * T // s), w1)
        lo_i, hi_i = (i0 + 0.5) * ai - 0.5, (i1 - 1 + 0.5) * ai - 0.5
        lo_j, hi_j = (j0 + 0.5) * aj - 0.5, (j1 - 1 + 0.5) * aj - 0.5
        I0, I1 = max(int(np.floor(lo_i)), 0), min(int(np.ceil(hi_i)) + 1, h24)   # 1-cell widening
        J0, J1 = max(int(np.floor(lo_j)), 0), min(int(np.ceil(hi_j)) + 1, w24)
        vi, vj = np.nonzero(V[I0:I1, J0:J1])
        A = G[vi + I0, vj + J0]
        nav[k] = [int(len(A)), [I0, I1], [J0, J1]]
        AV.append(A); atid.append(np.full(len(A), n))
    chk = np.concatenate(chk)
    P = np.concatenate(P); tid = np.concatenate(tid); AV = np.concatenate(AV); atid = np.concatenate(atid)
    del G
    best, bseg, per, info, tim = per_tile(P, tid, len(keys), 0.0, 'd-npz')
    fb, fs, fper, finfo, ftim = per_tile(AV, atid, len(keys), process.FULL_STOP_VOX, 'd-all-vertex')
    tiles = {}
    for n, k in enumerate(keys):
        nf = bool(best[n] * VOX_MM < FLAG_MM); af = bool(fb[n] * VOX_MM < FLAG_MM)
        u = min(best[n], fb[n])
        tiles[k] = {'min_mm': round(float(u) * VOX_MM, 6), 'segment': bseg[n] if best[n] <= fb[n] else fs[n],
                    'labelled_adjacent': nf or af, 'npz_flag': nf, 'all_vertex_flag': af,
                    'npz': {'n_points': int((tid == n).sum()), 'affine_fallback_fraction': round(srcfrac[k], 6),
                            'n_valid_vertices_1129': int(z[k + '__n_valid_vertices'][0]) if SB else None,
                            'min_mm': round(float(best[n]) * VOX_MM, 6), 'segment': bseg[n],
                            'per_segment_mm': {sg: round(float(per[sg][n]) * VOX_MM, 6) for sg in SEGS}},
                    'all_vertex': {'n_vertices_24': nav[k][0], 'grid24_rows': nav[k][1], 'grid24_cols': nav[k][2],
                                   'min_mm': round(float(fb[n]) * VOX_MM, 6), 'segment': fs[n],
                                   'early_stop': bool(finfo[fs[n]][n]['early_stop']) if fs[n] else False,
                                   'per_segment_mm': {sg: round(float(fper[sg][n]) * VOX_MM, 6) for sg in SEGS}}}
    fl = np.array([tiles[k]['labelled_adjacent'] for k in keys])
    res = {
        'provenance': PROV, 'strip': SEGID[st], 'material': 'M2' + st, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'what': 'DECL-P4-4 item 2 labelled-adjacency: min 3-D point-to-triangulated-surface distance (exact, '
                'CORR-RETRACE-RULE form b) in the 20260411134726 frame to the 8 labelled segments; '
                'labelled_adjacent = npz flag OR all-vertex flag',
        'inputs': {'branch': f'claude/gifted-bell-gavnl5-sib-p4-tiles-{st}', 'path': rpath, 'commit': commit,
                   'git_blob': blob, 'sha256': sha(npz), 'grid_json_sha256': sha(gjson),
                   'mesh_2400nm': {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif', 'meta.json')},
                   'labelled_meshes': 'logs/sib/p4-excl/downloads.jsonl and structures.json',
                   'n_tiles': len(keys), 'n_npz_points': int(len(P)), 'n_all_vertex_points': int(len(AV))},
        'voxel_mm': VOX_MM, 'flag_rule': 'min_mm < 1.2',
        'uv_map': {'rule': 'i24 = (i + 0.5) * h24 / h1129 - 0.5 (same for j)', 'h1129_w1129': [h1, w1],
                   'h24_w24': [h24, w24], 'T_px': T, 'canvas_per_grid': s,
                   'reverify_points': 'm2b: builder same-UV points (src 0) vs my centre-map bilinear; m2a: builder affine points vs my centre-map bilinear',
                   'reverify_same_uv_points_dist_vox': {'n': int(len(chk)), 'median': float(np.median(chk)),
                                                        'p99': float(np.percentile(chk, 99)), 'max': float(chk.max())}},
        'all_vertex_rule': 'valid 2.4 um vertices with grid row in [floor(lo), ceil(hi)] and col likewise, lo/hi = '
                           'mapped first/last 1.129 um grid row/col of the tile (one-cell widening); early stop at '
                           f'{process.FULL_STOP_VOX} vox (only below the flag threshold)',
        'n_flagged': int(fl.sum()),
        'n_flagged_npz': int(sum(tiles[k]['npz_flag'] for k in keys)),
        'n_flagged_all_vertex': int(sum(tiles[k]['all_vertex_flag'] for k in keys)),
        'flag_disagreements': {k: {'npz': tiles[k]['npz']['min_mm'], 'all_vertex': tiles[k]['all_vertex']['min_mm']}
                               for k in keys if tiles[k]['npz_flag'] != tiles[k]['all_vertex_flag']},
        'timing_s': {'total': round(time.time() - t0, 1), 'npz_per_segment': tim, 'all_vertex_per_segment': ftim},
        'tiles': tiles}
    json.dump(res, open(out, 'w'), indent=1)
    print('flagged', res['n_flagged'], 'npz', res['n_flagged_npz'], 'allv', res['n_flagged_all_vertex'], 'of', len(keys),
          'uvchk', res['uv_map']['reverify_same_uv_points_dist_vox'], res['timing_s']['total'], 's')


if __name__ == '__main__':
    main()
