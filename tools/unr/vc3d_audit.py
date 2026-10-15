#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-4: identity audit of grown PHerc0268 tifxyz surfaces (VC3D grower output on the lane branches; untrusted data, read as
float32 grids only) at native resolution. Per surface: materialise the tifxyz from git, run the W3 clearance of tools/unr/mesh_checks.py
on at most ~6000 vertices (grid stride), then from the per-vertex arrays: ON-PEAK (own lamina peak within 3 vox), CLEARANCE (>= 0.5 x
spacing), I5-on-surface JUMPs between grid-adjacent sampled vertices (|delta clearance_plus| or |delta clearance_minus| > 0.5 x the pair's
mean spacing), CONSISTENT fraction; the declared control = the same surface displaced by +0.5 x its median spacing along the normals.
usage: vc3d_audit.py <surfaces.txt> <out_dir> --worker K --workers 3 [--max_vertices 6000] [--only name1,name2]
       vc3d_audit.py summary <out_dir>"""
import os, sys, json, time, math, subprocess, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import mesh_checks as MC
REPO = os.path.abspath(os.path.join(HERE, '..', '..')); SCR = '/tmp/claude-0/-home-user-dominion/b19d92e8-9f98-5674-bc2b-8bf468fb8442/scratchpad/vc3d'
OWN_TOL, HALF, TUBE = 3.0, 40, 2
def J(o): return o.item() if hasattr(o, 'item') else str(o)

def materialise(branch, xpath, dst):
    d = os.path.dirname(xpath); os.makedirs(dst, exist_ok=True); ref = f'refs/watch/{branch}'
    for f in ('x.tif', 'y.tif', 'z.tif', 'meta.json'):
        r = subprocess.run(['git', 'show', f'{ref}:{d}/{f}'], cwd=REPO, capture_output=True)
        if r.returncode != 0:
            if f == 'meta.json': continue
            raise RuntimeError(f'git show failed for {d}/{f}: {r.stderr[-200:]}')
        open(os.path.join(dst, f), 'wb').write(r.stdout)
    return dst

def write_shifted(src_dir, dst_dir, shift_vox):
    import tifffile; m = MC.load_mesh(src_dir); V, F, N = MC.mesh_arrays(m); P = m['P'].copy(); valid = m['valid']; Ng = np.zeros_like(P); Ng[valid] = np.nan_to_num(N)
    Q = P + shift_vox * Ng; os.makedirs(dst_dir, exist_ok=True)
    for c, nm in enumerate('xyz'): tifffile.imwrite(os.path.join(dst_dir, nm + '.tif'), np.where(valid, Q[..., c], -1).astype(np.float32), metadata=None, software=False)
    meta = dict(m.get('meta', {})); meta['scale'] = m['scale']; meta['note'] = f'DECL-E2E-4 control: displaced by {shift_vox:.2f} vox along the grid normals'; json.dump(meta, open(os.path.join(dst_dir, 'meta.json'), 'w'))

def analyse(npz, stride):
    d = np.load(npz, allow_pickle=False); cp, cm, sp, own, ij = d['clearance_plus'], d['clearance_minus'], d['spacing'], d['own_offset'], d['ij'].astype(np.int64)
    on = np.isfinite(own) & (np.abs(own) <= OWN_TOL); clr = on & np.isfinite(sp) & (np.fmin(cp, cm) >= 0.5 * sp); n = len(cp)
    key = {(int(a), int(b)): k for k, (a, b) in enumerate(ij)}; jump_v = np.zeros(n, bool); pairs = 0; jumps = 0
    for k, (a, b) in enumerate(ij):
        for da, db in ((stride, 0), (0, stride)):
            q = key.get((int(a + da), int(b + db)))
            if q is None or not (on[k] and on[q]): continue
            s = 0.5 * (sp[k] + sp[q])
            if not np.isfinite(s): continue
            pairs += 1; dj = False
            for arr in (cp, cm):
                if np.isfinite(arr[k]) and np.isfinite(arr[q]) and abs(arr[k] - arr[q]) > 0.5 * s: dj = True
            if dj: jumps += 1; jump_v[k] = jump_v[q] = True
    cons = clr & ~jump_v
    return {'n_vertices': int(n), 'on_peak': round(float(on.mean()), 4) if n else None, 'clearance_pass': round(float(clr.mean()), 4) if n else None, 'pairs': int(pairs), 'jumps': int(jumps), 'jump_density': round(jumps / max(1, pairs), 4),
            'consistent': round(float(cons.mean()), 4) if n else None, 'spacing_p10_50_90': [round(float(v), 1) for v in np.nanpercentile(sp, [10, 50, 90])] if np.isfinite(sp).any() else None, 'own_offset_abs_p50_p90': [round(float(v), 2) for v in np.nanpercentile(np.abs(own), [50, 90])] if np.isfinite(own).any() else None}

def audit_one(name, branch, xpath, out, max_v):
    t0 = time.time(); rec = {'name': name, 'branch': branch, 'path': os.path.dirname(xpath)}; sdir = materialise(branch, xpath, os.path.join(SCR, name, 'surf'))
    m = MC.load_mesh(sdir); nval = int(m['valid'].sum()); stride = max(1, int(math.ceil(math.sqrt(nval / max_v)))); rec.update({'grid': list(m['valid'].shape), 'valid_cells': nval, 'scale': m['scale'], 'stride': stride, 'meta_target_volume': m.get('meta', {}).get('target_volume')})
    od = os.path.join(out, name); os.makedirs(od, exist_ok=True); store = MC.ChunkStore(MC.open_volume(MC.DEFAULT_VOLUME, threads=8))          # one chunk cache for the surface and its control
    rep = MC.run_check(sdir, od, w3=True, w3_half=HALF, w3_own_tol=OWN_TOL, w3_stride=stride, save_vertex=True, tag='surf', w3_tube=TUBE, store=store)
    w3 = rep.get('W3_clearance', {}); rec['w3'] = {k: w3.get(k) for k in ('vertices_tested', 'level0_chunks_fetched', 'level0_MB_fetched', 'fetch_secs', 'chunks_missing')}; rec['self_intersection'] = (rep.get('self_intersection') or {}).get('intersecting_pairs')
    rec['surface'] = analyse(os.path.join(od, 'surf_w3_vertex.npz'), stride); med_sp = (rec['surface']['spacing_p10_50_90'] or [None, 14.0])[1] or 14.0
    cdir = os.path.join(SCR, name, 'ctrl'); write_shifted(sdir, cdir, 0.5 * med_sp)
    MC.run_check(cdir, od, w3=True, w3_half=HALF, w3_own_tol=OWN_TOL, w3_stride=stride, save_vertex=True, tag='ctrl', w3_tube=TUBE, store=store); rec['chunks_total'] = store.n; rec['MB_total'] = round(store.bytes / 1e6, 1); del store
    rec['control'] = analyse(os.path.join(od, 'ctrl_w3_vertex.npz'), stride); rec['control_shift_vox'] = round(0.5 * med_sp, 2)
    s, c = rec['surface'], rec['control']; rec['identity_consistent'] = bool(s['consistent'] is not None and s['consistent'] >= 0.80 and s['jump_density'] <= 0.02)
    rec['secs'] = round(time.time() - t0, 1); json.dump(rec, open(os.path.join(od, 'audit.json'), 'w'), indent=1, default=J); return rec

def summary(out):
    recs = []
    for n in sorted(os.listdir(out)):
        f = os.path.join(out, n, 'audit.json')
        if os.path.exists(f): recs.append(json.load(open(f)))
    ok = [r for r in recs if r['surface']['on_peak'] is not None and r['control']['on_peak'] is not None]; dif = [r['surface']['on_peak'] - r['control']['on_peak'] for r in ok]
    S = {'declaration': 'DECL-E2E-4', 'n_audited': len(recs), 'sensitivity_onpeak_surface_minus_control_median': round(float(np.median(dif)), 4) if dif else None}
    S['sensitivity_pass'] = bool(dif and np.median(dif) >= 0.30)
    for key in ('on_peak', 'clearance_pass', 'consistent', 'jump_density'):
        v = [r['surface'][key] for r in ok]; w = [r['control'][key] for r in ok]
        S[key + '_surface_p10_50_90'] = [round(float(x), 4) for x in np.percentile(v, [10, 50, 90])] if v else None; S[key + '_control_p10_50_90'] = [round(float(x), 4) for x in np.percentile(w, [10, 50, 90])] if w else None
    S['identity_consistent_surfaces'] = [r['name'] for r in ok if r['identity_consistent']]; S['n_identity_consistent'] = len(S['identity_consistent_surfaces'])
    S['rows'] = [{'name': r['name'], 'valid_cells': r['valid_cells'], 'stride': r['stride'], 'on_peak': r['surface']['on_peak'], 'ctrl_on_peak': r['control']['on_peak'], 'consistent': r['surface']['consistent'], 'jump_density': r['surface']['jump_density'], 'spacing_p50': (r['surface']['spacing_p10_50_90'] or [None] * 3)[1], 'self_intersections': r.get('self_intersection'), 'secs': r['secs']} for r in recs]
    json.dump(S, open(os.path.join(out, 'summary.json'), 'w'), indent=1, default=J); print(json.dumps({k: v for k, v in S.items() if k != 'rows'}, default=J))

def main():
    if len(sys.argv) > 2 and sys.argv[1] == 'summary': return summary(sys.argv[2])
    ap = argparse.ArgumentParser(); ap.add_argument('surfaces'); ap.add_argument('out'); ap.add_argument('--worker', type=int, default=0); ap.add_argument('--workers', type=int, default=1); ap.add_argument('--max_vertices', type=int, default=6000); ap.add_argument('--only', default=None)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); lines = [l.split() for l in open(a.surfaces) if l.strip()]
    for i, (branch, xpath) in enumerate(lines):
        name = os.path.basename(os.path.dirname(os.path.dirname(xpath))) or f's{i}'
        if a.only and name not in a.only.split(','): continue
        if i % a.workers != a.worker or os.path.exists(os.path.join(a.out, name, 'audit.json')): continue
        try: r = audit_one(name, branch, xpath, a.out, a.max_vertices); print(json.dumps({'name': name, 'surface': r['surface'], 'control_on_peak': r['control']['on_peak'], 'secs': r['secs'], 'MB': r['w3'].get('level0_MB_fetched')}, default=J), flush=True)
        except Exception as e: print(json.dumps({'name': name, 'error': str(e)[-400:]}), flush=True); os.makedirs(os.path.join(a.out, name), exist_ok=True); json.dump({'name': name, 'error': str(e)[-1000:]}, open(os.path.join(a.out, name, 'error.json'), 'w'))

if __name__ == '__main__': main()
