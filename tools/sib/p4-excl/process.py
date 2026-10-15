"""Per-tile minimum point-to-surface distance to the 8 labelled Paris 4 segments (DECL-P4-2 item 1).

usage: process.py <strip a|b> <npz> <commit> <blob> <struct_dir> <out_json> [<strip_mesh_dir> <grid_json>]

Primary (as tasked): min over the tile's points in tile_points.npz (<= 4096 random valid vertices).
Supplementary (fail-closed check, if the strip mesh is given): min over ALL valid grid vertices of
the tile, reconstructed with the tiler's own rule (grid vertex (gi, gj) belongs to tile (r, c) iff
gi*s in [r*T, (r+1)*T) and gj*s in [c*T, (c+1)*T)); the npz points must be a subset of it.
Coordinates only: x, y, z in 20260411134726 voxels.
"""
import sys, os, json, time, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
SEGS = ['20231016151002', '20230702185753', '20231031143852', '20231106155351',
        '20231012184424', '20231210121321', '20231007101619', '20230929220926']
VOX_MM = 0.0024          # metadata.json scan.tomo.acquisition.detector.samplePixelSize (mm)
FLAG_MM = 1.2
SHAPE_ZYX = (75784, 32693, 32693)
STRIPNAME = {'a': 'w010-027', 'b': 'w028-037'}
CKPT = None
FULL_STOP_VOX = 0.5      # all-vertex mode: stop refining a tile once an exact 0.5-vox distance is attained


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def per_tile(P, tid, ntiles, stop_vox, label):
    best = np.full(ntiles, np.inf); bseg = [''] * ntiles
    perseg, info, timing = {}, {}, {}
    order = np.argsort(tid, kind='stable')
    bounds = np.searchsorted(tid[order], np.arange(ntiles + 1))
    for s in SEGS:
        ts = time.time()
        ck = f'{CKPT}/{label}_{s}.json'
        if CKPT and os.path.exists(ck):                      # restart-safe per-segment checkpoint
            c = json.load(open(ck))
            dmin = np.array(c['dmin'], float); perseg[s], info[s], timing[s] = dmin, c['info'], c['secs']
            for n in np.nonzero(dmin < best)[0]:
                best[n] = dmin[n]; bseg[n] = s
            print(label, s, 'from checkpoint', flush=True)
            continue
        S = Surface(np.load(f'{SDIR}/{s}.npz')['grid'])
        dv, _ = S.tree.query(P, workers=4)
        dmin = np.full(ntiles, np.inf); inf_s = []
        for n in range(ntiles):
            ix = order[bounds[n]:bounds[n + 1]]
            if ix.size == 0:
                inf_s.append(None); continue
            d, _, inf = S.min_dist(P[ix], dv=dv[ix], stop_vox=stop_vox)
            dmin[n] = d; inf_s.append(inf)
        perseg[s], info[s] = dmin, inf_s
        for n in np.nonzero(dmin < best)[0]:
            best[n] = dmin[n]; bseg[n] = s
        timing[s] = round(time.time() - ts, 1)
        if CKPT:
            json.dump({'dmin': [float(x) for x in dmin], 'info': inf_s, 'secs': timing[s]}, open(ck + '.tmp', 'w'))
            os.replace(ck + '.tmp', ck)
        print(label, s, timing[s], 's', 'Lc', round(S.Lc, 3), flush=True)
        del S, dv
    return best, bseg, perseg, info, timing


def main():
    global SDIR, CKPT
    strip, npz, commit, blob, SDIR, out = sys.argv[1:7]
    CKPT = os.environ.get('P4EXCL_CKPT')
    if CKPT:
        CKPT = os.path.join(CKPT, sha(npz)[:16]); os.makedirs(CKPT, exist_ok=True)
    mdir = sys.argv[7] if len(sys.argv) > 7 else None
    gjson = sys.argv[8] if len(sys.argv) > 8 else None
    t0 = time.time()
    z = np.load(npz, allow_pickle=False)
    keys = sorted(z.keys(), key=lambda k: tuple(int(t[1:]) for t in k.split('_')))
    layout = {k: [list(z[k].shape), str(z[k].dtype)] for k in keys}
    assert all(z[k].ndim == 2 and z[k].shape[1] == 3 for k in keys), layout
    arrs = [np.asarray(z[k], np.float64) for k in keys]
    P = np.concatenate(arrs); tid = np.repeat(np.arange(len(keys)), [len(a) for a in arrs])
    fin = np.isfinite(P).all(1) & (P >= 0).all(1)
    P, tid = P[fin], tid[fin]
    lo, hi = P.min(0), P.max(0)
    if not (hi[0] < SHAPE_ZYX[2] and hi[1] < SHAPE_ZYX[1] and hi[2] < SHAPE_ZYX[0]):
        raise SystemExit(f'points outside 20260411134726 xyz frame: min {lo} max {hi}')
    best, bseg, perseg, info, timing = per_tile(P, tid, len(keys), 0.0, 'npz')
    t_primary = round(time.time() - t0, 1)

    full = None
    if mdir:
        import tifffile
        tf = time.time()
        g = json.load(open(gjson))
        T = int(g['T_px'] if 'T_px' in g else g['T_canvas_px'])          # tiles-b / tiles-a schema
        sc = g['canvas_per_grid_scale_rows_cols'] if 'canvas_per_grid_scale_rows_cols' in g else \
            [g['scale_canvas_per_grid']['rows'], g['scale_canvas_per_grid']['cols']]
        assert sc[0] == sc[1] and float(sc[0]).is_integer(), sc
        s = int(sc[0])
        X = np.stack([tifffile.imread(f'{mdir}/{c}.tif') for c in 'xyz'], -1)
        valid = (X >= 0).all(-1) & np.isfinite(X).all(-1)
        fsh = {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif', 'meta.json')}
        FP, ftid, subset_ok, nvert = [], [], {}, {}
        for n, k in enumerate(keys):
            r, c = (int(t[1:]) for t in k.split('_'))
            i0, i1 = -(-r * T // s), -(-(r + 1) * T // s)     # ceil: gi*s >= r*T and < (r+1)*T
            j0, j1 = -(-c * T // s), -(-(c + 1) * T // s)
            vi, vj = np.nonzero(valid[i0:i1, j0:j1])
            V = X[vi + i0, vj + j0].astype(np.float64)
            nvert[k] = len(V)
            # subset check: every npz point is one of these vertices (exact float32 match)
            a = np.ascontiguousarray(np.asarray(z[k], np.float32)).view('V12').ravel()
            b = np.ascontiguousarray(V.astype(np.float32)).view('V12').ravel()
            subset_ok[k] = bool(np.isin(a, b).all())
            FP.append(V); ftid.append(np.full(len(V), n))
        del X, valid
        FP = np.concatenate(FP); ftid = np.concatenate(ftid)
        fb, fs, fper, finfo, ftime = per_tile(FP, ftid, len(keys), FULL_STOP_VOX, 'all-vertex')
        full = dict(best=fb, seg=fs, per=fper, info=finfo, timing=ftime, T=T, s=s, mesh_sha=fsh,
                    subset_ok=subset_ok, nvert=nvert, n=int(len(FP)), secs=round(time.time() - tf, 1))
        del FP

    tiles = {}
    for n, k in enumerate(keys):
        e = {'min_vox': round(float(best[n]), 4), 'min_mm': round(float(best[n]) * VOX_MM, 6),
             'segment': bseg[n], 'labelled_adjacent': bool(best[n] * VOX_MM < FLAG_MM),
             'n_points': int((tid == n).sum()),
             'per_segment_mm': {s: round(float(perseg[s][n]) * VOX_MM, 6) for s in SEGS}}
        if full:
            fb = float(full['best'][n])
            e['all_vertex'] = {
                'n_vertices': full['nvert'][k], 'npz_points_subset': full['subset_ok'][k],
                'min_vox': round(fb, 4), 'min_mm': round(fb * VOX_MM, 6), 'segment': full['seg'][n],
                'labelled_adjacent': bool(fb * VOX_MM < FLAG_MM),
                'early_stop': bool(full['info'][full['seg'][n]][n]['early_stop']) if full['seg'][n] else False}
        tiles[k] = e
    res = {
        'provenance': PROV,
        'strip': STRIPNAME[strip],
        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'what': 'DECL-P4-2 item 1 training-overlap flag: per tile, minimum 3-D point-to-triangulated-surface '
                'distance (CORR-RETRACE-RULE form b; exact, no densification) from its points to the meshes of the '
                '8 labelled segments on 20260411134726',
        'inputs': {'strip': strip, 'branch': f'claude/gifted-bell-gavnl5-sib-p4-tiles-{strip}',
                   'path': f'logs/sib/p4-tiles-{strip}/tile_points.npz', 'commit': commit, 'git_blob': blob,
                   'sha256': sha(npz), 'n_tiles': len(keys), 'n_points': int(len(P)),
                   'n_points_dropped_invalid': int((~fin).sum()),
                   'points_bbox_xyz_vox': [lo.round(2).tolist(), hi.round(2).tolist()],
                   'labelled_meshes': 'logs/sib/p4-excl/downloads.jsonl (sha256 of every file) and structures.json'},
        'voxel_mm': VOX_MM,
        'voxel_source': 'volume 20260411134726 metadata.json scan.tomo.acquisition.detector.samplePixelSize = 0.0024 '
                        '(mm); metadata.json sha256 881bf77fc0f02a91040755da25d54ad958e290a528ec61489e411937112fba4d',
        'flag_rule': 'labelled_adjacent = min_mm < 1.2',
        'method': 'tifxyz grid quads with 4 valid corners -> triangles (a,b,e),(a,e,c); exact point-triangle '
                  'distance; KD-tree on vertices; candidate set and ball radius from the Lc = Lmax/sqrt(3) '
                  'vertex covering bound (tools/sib/p4-excl/surfdist.py)',
        'n_flagged': int((best * VOX_MM < FLAG_MM).sum()),
        'timing_s': {'primary_total': t_primary, 'primary_per_segment': timing},
        'tiles': tiles,
    }
    if full:
        fl = full['best'] * VOX_MM < FLAG_MM
        pf = best * VOX_MM < FLAG_MM
        res['all_vertex_check'] = {
            'why': 'tile_points.npz holds <= 4096 random vertices of ~1e5 per tile (mean spacing ~130 vox), so its '
                   'min can exceed the tile surface min; an exclusion should not fail open. This check uses every '
                   'valid vertex of the tile. Remaining discretisation: tile surface points are within Lc of a '
                   'tile vertex (strip mesh Lc reported in structures).',
            'strip_mesh_sha256': full['mesh_sha'], 'T_px': full['T'], 'canvas_per_grid': full['s'],
            'vertex_rule': 'gi*s in [r*T,(r+1)*T) and gj*s in [c*T,(c+1)*T), valid = x,y,z >= 0',
            'npz_subset_all_tiles': all(full['subset_ok'].values()),
            'n_vertices_total': full['n'], 'early_stop_vox': FULL_STOP_VOX,
            'n_flagged_all_vertex': int(fl.sum()),
            'flagged_all_vertex_not_npz': [k for n, k in enumerate(keys) if fl[n] and not pf[n]],
            'flagged_npz_not_all_vertex': [k for n, k in enumerate(keys) if pf[n] and not fl[n]],
            'max_npz_minus_all_vertex_mm': round(float(np.max(best - full['best'])) * VOX_MM, 6),
            'timing_s': {'total': full['secs'], 'per_segment': full['timing']},
        }
        res['n_flagged_union'] = int((fl | pf).sum())
    res['timing_s']['total'] = round(time.time() - t0, 1)
    json.dump(res, open(out, 'w'), indent=1)
    print('flagged npz', res['n_flagged'], 'union', res.get('n_flagged_union'), 'of', len(keys),
          'total', res['timing_s']['total'], 's')


if __name__ == '__main__':
    main()
