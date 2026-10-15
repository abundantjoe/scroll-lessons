#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 W12 FRAME TEST of a reference scroll (level-4 masked CT, 138.24 um/voxel, (z, y, x) uint8 from
tools/umb/fetch_zarr.py). The same test as UMB-GEOMETRY-RESULT item 1 on PHerc0268, written down so it is repeatable:
  1. mask = CT > 0 (the masked volume is 0 outside the scroll), eroded by `--erode` voxels so the mask edge never votes
     (a cylindrical outer surface would otherwise cast radial normals and fake a roll);
  2. 3-D structure tensor J = G_si * (grad G_sd * v)(grad G_sd * v)^T per voxel, sampled on a `--decim` grid (4 ->
     552.96 um, as in UMB-GEOMETRY-RESULT), eigen-decomposed: layering normal n = eigenvector of the largest eigenvalue,
     planar coherence c = (w2 - w1) / w2 (w0 <= w1 <= w2); voters = eroded-mask points with c >= `--coh`;
  2b. only the largest 26-connected component of the eroded-mask lattice votes (the scroll body; the sample holder, end
     plates and mask remnants at the volume ends are detached from it), with the discarded fraction recorded;
  3. roll-axis direction a = eigenvector of the SMALLEST eigenvalue of M = mean(n n^T) over the voters (every layering
     normal of a roll is perpendicular to its axis); reported with the eigenvalues l0 <= l1 <= l2 of M, the ratio l0/l1
     (an axis is well defined only if l0 << l1; a flattened stack has l0 ~ l1, both ~ 0), the tilt of a to the nearest
     volume axis and the tilt of the dominant normal direction e2 to its nearest axis; median |n . a| (0 for a roll);
     per-bin repeat along the volume axis nearest to a (frame stability along the scroll); |n_x|, |n_y|, |n_z| statistics
     comparable to UMB-GEOMETRY-RESULT.
  4. `--phantom`: the identical code path on two procedural volumes of known frame (a roll of concentric shells about an
     axis tilted 6 deg from z, and a flat stack of planes along z): recovered-axis error (deg) and the two ratios are the
     validation of the test, written into the same JSON. The phantom pass is evidence about the code only.
usage: frame_test.py <level4.npy> <out.json> --name PHerc0800 [--vox_um 138.24 --decim 4 --sd 1.0 --si 2.0 --coh 0.4
       --erode 5] | frame_test.py --phantom <out.json>
"""
import argparse, hashlib, json, os, time, numpy as np
from scipy import ndimage as ndi


def tensor_points(vol, sd, si, decim, erode, zblock=64):
    """Decimated structure-tensor samples inside the eroded mask. Returns (coords (N,3) int, J (N,6) float32,
    counts). vol: (Z, Y, X) uint8 (memmap ok)."""
    Z, Y, X = vol.shape; halo = max(int(np.ceil(3 * (sd + si))) + 1, erode + 1)
    coords, comps, n_mask, n_er = [], [], 0, 0
    for z0 in range(0, Z, zblock):
        z1 = min(Z, z0 + zblock); a, b = max(0, z0 - halo), min(Z, z1 + halo)
        blk = np.asarray(vol[a:b]); m = blk > 0; n_mask += int(m[z0 - a:z1 - a].sum())
        me = ndi.minimum_filter(m, size=2 * erode + 1, mode='constant', cval=False) if erode > 0 else m
        n_er += int(me[z0 - a:z1 - a].sum())
        zs = ((z0 + decim - 1) // decim) * decim
        if zs >= z1: continue
        sl = (slice(zs - a, z1 - a, decim), slice(0, Y, decim), slice(0, X, decim)); sel = me[sl]
        if not sel.any(): continue
        v = blk.astype(np.float32) / 255.0
        g = [ndi.gaussian_filter(v, sd, order=o) for o in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        J = [ndi.gaussian_filter(g[i] * g[j], si)[sl][sel] for i in range(3) for j in range(i, 3)]   # zz zy zx yy yx xx
        zz, yy, xx = np.nonzero(sel)
        coords.append(np.stack([zs + zz * decim, yy * decim, xx * decim], 1)); comps.append(np.stack(J, 1))
        del v, g, J
    if not coords: return np.zeros((0, 3), int), np.zeros((0, 6), np.float32), n_mask, n_er
    return np.concatenate(coords), np.concatenate(comps).astype(np.float32), n_mask, n_er


def eigen(J6):
    """J6 columns zz zy zx yy yx xx -> normals (N,3) in (z,y,x) order, planar coherence, trace."""
    N = J6.shape[0]; J = np.empty((N, 3, 3), np.float32)
    J[:, 0, 0], J[:, 0, 1], J[:, 0, 2] = J6[:, 0], J6[:, 1], J6[:, 2]
    J[:, 1, 0], J[:, 1, 1], J[:, 1, 2] = J6[:, 1], J6[:, 3], J6[:, 4]
    J[:, 2, 0], J[:, 2, 1], J[:, 2, 2] = J6[:, 2], J6[:, 4], J6[:, 5]
    w, e = np.linalg.eigh(J); n = e[:, :, 2]; coh = (w[:, 2] - w[:, 1]) / (w[:, 2] + 1e-12); tr = w.sum(1)
    return n, coh, tr


def frame(n):
    """Axis and stacking direction from the normals. n: (N,3) unit vectors in (z,y,x)."""
    M = (n.T @ n) / max(len(n), 1); l, e = np.linalg.eigh(M); axis = e[:, 0]; stack = e[:, 2]
    def tilt(v):
        k = int(np.argmax(np.abs(v))); return ['z', 'y', 'x'][k], float(np.degrees(np.arccos(min(1.0, abs(v[k])))))
    na, ta = tilt(axis); ns, ts = tilt(stack); dot = np.abs(n @ axis)
    return {'M_eigenvalues_l0_l1_l2': [float(x) for x in l], 'ratio_l0_over_l1': float(l[0] / max(l[1], 1e-12)),
            'ratio_l1_over_l2': float(l[1] / max(l[2], 1e-12)), 'axis_zyx': [float(x) for x in axis], 'axis_nearest_volume_axis': na,
            'axis_tilt_deg': ta, 'stack_dir_zyx': [float(x) for x in stack], 'stack_nearest_volume_axis': ns, 'stack_tilt_deg': ts,
            'median_abs_n_dot_axis': float(np.median(dot)), 'p90_abs_n_dot_axis': float(np.percentile(dot, 90)), 'n_voters': int(len(n))}


def normal_stats(n):
    a = np.abs(n); out = {}
    for i, k in enumerate('zyx'):
        out[f'median_abs_n_{k}'] = float(np.median(a[:, i])); out[f'frac_abs_n_{k}_gt_0.8'] = float((a[:, i] > 0.8).mean())
        out[f'frac_abs_n_{k}_gt_0.7'] = float((a[:, i] > 0.7).mean())
    return out


def largest_component(coords, decim, shape):
    """Keep the largest 26-connected component of the decimated eroded-mask lattice: the scroll body. The volume ends carry
    the sample holder, end plates and mask remnants (bright discs, fragments) detached from the scroll; they would vote
    with flat normals along z. Returns (keep mask, n_components, kept fraction, z-range of the kept body)."""
    g = np.zeros([(s + decim - 1) // decim for s in shape], bool); idx = tuple((coords // decim).T); g[idx] = True
    lab, nl = ndi.label(g, structure=np.ones((3, 3, 3)))
    if nl <= 1: return np.ones(len(coords), bool), int(nl), 1.0, [int(coords[:, 0].min()), int(coords[:, 0].max()) + 1]
    sizes = np.bincount(lab.ravel())[1:]; big = int(np.argmax(sizes)) + 1; keep = lab[idx] == big; zk = coords[keep][:, 0]
    return keep, int(nl), float(keep.mean()), [int(zk.min()), int(zk.max()) + 1]


def run_volume(vol, p, name, vox_um):
    t0 = time.time(); coords, J6, n_mask, n_er = tensor_points(vol, p['sd'], p['si'], p['decim'], p['erode']); t1 = time.time()
    keep, ncomp, kfrac, zr = largest_component(coords, p['decim'], vol.shape); coords, J6 = coords[keep], J6[keep]
    n, coh, tr = eigen(J6); vot = coh >= p['coh']; tr30 = float(np.percentile(tr, 30)) if len(tr) else 0.0; vot2 = vot & (tr >= tr30)
    res = {'name': name, 'shape_zyx': [int(x) for x in vol.shape], 'vox_um': vox_um, 'params': p,
           'counts': {'mask_voxels': n_mask, 'eroded_mask_voxels': n_er, 'decimated_points_all_components': int(len(keep)), 'components': ncomp, 'largest_component_fraction': kfrac,
                      'largest_component_z_range': zr, 'decimated_points': int(len(coh)),
                      'voters_coh': int(vot.sum()), 'voters_coh_and_contrast_p30': int(vot2.sum()), 'coh_median_all': float(np.median(coh)) if len(coh) else None},
           'frame_coh': frame(n[vot]) if vot.sum() > 10 else None, 'frame_coh_contrast': frame(n[vot2]) if vot2.sum() > 10 else None,
           'normals_coh': normal_stats(n[vot]) if vot.sum() > 10 else None}
    if res['frame_coh']:
        ax = res['frame_coh']['axis_nearest_volume_axis']; k = 'zyx'.index(ax); c = coords[vot][:, k]; nb = 8
        edges = np.linspace(c.min(), c.max() + 1, nb + 1); bins = []
        for i in range(nb):
            s = (c >= edges[i]) & (c < edges[i + 1])
            if s.sum() < 100: bins.append({'range_vox': [int(edges[i]), int(edges[i + 1])], 'n': int(s.sum())}); continue
            f = frame(n[vot][s]); ang = float(np.degrees(np.arccos(min(1.0, abs(np.dot(f['axis_zyx'], res['frame_coh']['axis_zyx']))))))
            bins.append({'range_vox': [int(edges[i]), int(edges[i + 1])], 'n': int(s.sum()), 'ratio_l0_over_l1': f['ratio_l0_over_l1'],
                         'axis_tilt_deg': f['axis_tilt_deg'], 'axis_vs_global_deg': ang, 'median_abs_n_dot_axis': f['median_abs_n_dot_axis']})
        res['bins_along_' + ax] = bins
    res['secs'] = {'tensor': round(t1 - t0, 1), 'total': round(time.time() - t0, 1)}
    return res


def phantom_roll(size=320, tilt_deg=6.0, pitch=6.0, wall=2.0, seed=0):
    """Concentric cylindrical shells about an axis tilted `tilt_deg` from z toward x, through the centre."""
    rng = np.random.default_rng(seed); t = np.radians(tilt_deg); a = np.array([np.cos(t), 0.0, np.sin(t)])   # (z,y,x)
    z, y, x = np.mgrid[:size, :size, :size].astype(np.float32); c = (size - 1) / 2; P = np.stack([z - c, y - c, x - c], -1)
    along = P @ a; r = np.sqrt(np.maximum((P * P).sum(-1) - along ** 2, 0)); v = 0.5 + 0.4 * np.cos(2 * np.pi * r / pitch)
    v = (v > 0.5 + 0.4 * np.cos(np.pi * wall / pitch)).astype(np.float32) * 0.6 + 0.2 + 0.05 * rng.standard_normal(v.shape).astype(np.float32)
    mask = (r < 0.42 * size) & (np.abs(along) < 0.45 * size); return (np.clip(v, 0, 1) * 255 * mask).astype(np.uint8), a


def phantom_stack(size=320, pitch=6.0, wall=2.0, seed=1):
    """Flat sheets stacked along z (normals all z): no roll axis exists; the ratio l0/l1 must be ~ 1."""
    rng = np.random.default_rng(seed); z, y, x = np.mgrid[:size, :size, :size].astype(np.float32); c = (size - 1) / 2
    v = (np.cos(2 * np.pi * z / pitch) > np.cos(np.pi * wall / pitch)).astype(np.float32) * 0.6 + 0.2 + 0.05 * rng.standard_normal(z.shape).astype(np.float32)
    mask = (np.abs(x - c) < 0.42 * size) & (np.abs(y - c) < 0.42 * size) & (np.abs(z - c) < 0.42 * size)
    return (np.clip(v, 0, 1) * 255 * mask).astype(np.uint8), np.array([1.0, 0, 0])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('npy', nargs='?'); ap.add_argument('out'); ap.add_argument('--name', default='')
    ap.add_argument('--vox_um', type=float, default=138.24); ap.add_argument('--decim', type=int, default=4); ap.add_argument('--sd', type=float, default=1.0)
    ap.add_argument('--si', type=float, default=2.0); ap.add_argument('--coh', type=float, default=0.4); ap.add_argument('--erode', type=int, default=5)
    ap.add_argument('--phantom', action='store_true'); ap.add_argument('--src', default='', help='s3 key of the level (provenance only)')
    a = ap.parse_args(); p = {'decim': a.decim, 'sd': a.sd, 'si': a.si, 'coh': a.coh, 'erode': a.erode}
    if a.phantom:
        out = {'kind': 'phantom', 'params': p, 'cases': {}}
        for nm, (vol, truth) in {'roll_tilt6': phantom_roll(), 'flat_stack': phantom_stack()}.items():
            r = run_volume(vol, p, nm, 1.0); f = r['frame_coh']
            r['truth_axis_zyx'] = [float(x) for x in truth]
            if nm.startswith('roll'): r['axis_error_deg'] = float(np.degrees(np.arccos(min(1.0, abs(np.dot(f['axis_zyx'], truth)))))); r['pass'] = bool(r['axis_error_deg'] <= 1.0 and f['ratio_l0_over_l1'] <= 0.1)
            else: r['stack_error_deg'] = float(np.degrees(np.arccos(min(1.0, abs(np.dot(f['stack_dir_zyx'], truth)))))); r['pass'] = bool(r['stack_error_deg'] <= 1.0 and f['ratio_l0_over_l1'] >= 0.5)
            out['cases'][nm] = r; print(nm, 'ratio', round(f['ratio_l0_over_l1'], 4), 'axis', [round(x, 3) for x in f['axis_zyx']], 'pass', r['pass'], flush=True)
        out['pass'] = all(c['pass'] for c in out['cases'].values()); json.dump(out, open(a.out, 'w'), indent=1); print('phantom pass', out['pass']); return
    vol = np.load(a.npy, mmap_mode='r'); h = hashlib.sha256()
    with open(a.npy, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    r = run_volume(vol, p, a.name or os.path.basename(a.npy), a.vox_um); r['input'] = {'npy': os.path.basename(a.npy), 'sha256': h.hexdigest(), 'src': a.src}
    json.dump(r, open(a.out, 'w'), indent=1); f = r['frame_coh']
    print(a.name, 'voters', r['counts']['voters_coh'], 'axis', f['axis_nearest_volume_axis'], 'tilt', round(f['axis_tilt_deg'], 2), 'ratio l0/l1', round(f['ratio_l0_over_l1'], 4),
          'stack', f['stack_nearest_volume_axis'], round(f['stack_tilt_deg'], 2), '|n.a| med', round(f['median_abs_n_dot_axis'], 3), r['secs'], flush=True)


if __name__ == '__main__': main()
