#!/usr/bin/env python3
"""bi_prep.py: copy or crop one tifxyz surface for the batch pipeline and decide the render normal direction.

  python -I bi_prep.py SRC.tifxyz OUT_DIR --scroll PHerc0268 [--name NAME] [--theta T0:T1] [--rows R0:R1] [--cols C0:C1]
                       [--z Z0:Z1] [--flip auto|0|1]

Crop: nodes outside the selection are set to -1 (tifxyz invalid), then all-invalid leading/trailing rows and columns are
trimmed. theta = degrees around the umbilicus, unwrapped along the node columns (bi_common.theta_by_column; equal to
crop_arc.py's theta % 360 for a surface spanning < 360 deg). --rows/--cols index the SOURCE grid (end exclusive).
Normal: + must point away from the umbilicus (poc_chain.sh 'render' rule: flip when the outward fraction of the node
normals n = dP/dcol x dP/drow is < 0.5); --flip 0|1 forces it (validation only).
Writes OUT_DIR/{x,y,z}.tif, meta.json (uuid = name) and OUT_DIR/../prep.json (crop offsets in the source grid, area,
outward fraction, flip, reading orientation, theta/z extent, sha256 of the geometry files); prints prep.json.
"""
import argparse, hashlib, json, os, sys
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_common as C  # noqa: E402


def rng(s):
    if not s: return None
    a, b = s.split(':'); return float(a), float(b)


ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--scroll', default=None); ap.add_argument('--name', default=None)
ap.add_argument('--theta'); ap.add_argument('--rows'); ap.add_argument('--cols'); ap.add_argument('--z')
ap.add_argument('--flip', default='auto', choices=('auto', '0', '1'))
a = ap.parse_args()
scroll = a.scroll or C.scroll_of(a.src); umb = C.load_umb(C.SCROLLS[scroll]['umb'])
name = a.name or os.path.basename(os.path.normpath(a.out))
X, Y, Z, ok = C.load_xyz(a.src); meta = json.load(open(f'{a.src}/meta.json')); step = 1.0 / meta['scale'][0]
H0, W0 = X.shape; keep = ok.copy()
if a.rows:
    r0, r1 = (int(v) for v in rng(a.rows)); m = np.zeros_like(keep); m[r0:r1] = True; keep &= m
if a.cols:
    c0, c1 = (int(v) for v in rng(a.cols)); m = np.zeros_like(keep); m[:, c0:c1] = True; keep &= m
if a.z:
    z0, z1 = rng(a.z); keep &= (Z >= z0) & (Z <= z1)
T = C.theta_by_column(X, Y, Z, ok, umb)
if a.theta:
    t0, t1 = rng(a.theta); Tm = np.where(ok, T, np.nan)
    # accept the requested interval on any turn: shift it to the turn holding most of the surface's columns
    best = max(range(-3, 4), key=lambda k: int(np.sum((Tm >= t0 + 360 * k) & (Tm <= t1 + 360 * k))))
    keep &= (Tm >= t0 + 360 * best) & (Tm <= t1 + 360 * best)
if not keep.any(): raise SystemExit('empty selection')
rr = np.where(keep.any(1))[0]; cc = np.where(keep.any(0))[0]
R0, R1, Cc0, Cc1 = int(rr.min()), int(rr.max()) + 1, int(cc.min()), int(cc.max()) + 1
os.makedirs(a.out, exist_ok=True)
Xs, Ys, Zs, ks = (A[R0:R1, Cc0:Cc1] for A in (X, Y, Z, keep))
sha = {}
for c, A in (('x', Xs), ('y', Ys), ('z', Zs)):
    p = f'{a.out}/{c}.tif'; tifffile.imwrite(p, np.where(ks, A, -1).astype(np.float32))
    sha[f'{c}.tif'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
qa = C.quad_area_vox2(Xs, Ys, Zs, ks, step); area = float(np.nansum(qa))
frac, med, nn = C.outward_fraction(Xs, Ys, Zs, ks, umb)
flip = (frac < 0.5) if a.flip == 'auto' else (a.flip == '1')
orient = C.reading_orientation(Xs, Ys, Zs, ks, umb)
Ts = T[R0:R1, Cc0:Cc1][ks]
m = {k: v for k, v in meta.items() if k not in ('bbox', 'area_vx2', 'area_cm2', 'uuid', 'name')}
P = np.stack([Xs[ks], Ys[ks], Zs[ks]], 1)
m.update(uuid=name, name=name, format='tifxyz', type='seg', scale=meta['scale'], bbox=[P.min(0).tolist(), P.max(0).tolist()],
         area_vx2=area, area_cm2=area * C.VOX_UM ** 2 / 1e8,
         source=f'bi_prep.py crop of {os.path.abspath(a.src)} (source uuid {meta.get("uuid")}): source rows {R0}..{R1 - 1}, '
                f'cols {Cc0}..{Cc1 - 1}; theta {a.theta}, rows {a.rows}, cols {a.cols}, z {a.z}')
json.dump(m, open(f'{a.out}/meta.json', 'w'), indent=1)
rep = dict(name=name, scroll=scroll, src=os.path.abspath(a.src), src_uuid=meta.get('uuid'), src_grid=[H0, W0],
           crop=dict(theta=a.theta, rows=a.rows, cols=a.cols, z=a.z, src_row0=R0, src_col0=Cc0, src_row1=R1, src_col1=Cc1),
           grid=[R1 - R0, Cc1 - Cc0], scale=meta['scale'], step_vox=step, valid_nodes=int(ks.sum()),
           area_cm2=round(area * C.VOX_UM ** 2 / 1e8, 4), outward_fraction=round(frac, 4), normal_dot_radial_median=round(med, 4),
           n_normals=nn, flip_normals=bool(flip), flip_mode=a.flip,
           flip_note=('normals point away from the umbilicus already' if not flip else 'render with --flip-normals') +
                     ('' if abs(frac - 0.5) > 0.2 else ' (WARNING: ambiguous outward fraction)'),
           orientation=orient, theta_deg=[round(float(np.min(Ts)), 2), round(float(np.max(Ts)), 2)],
           z_vox=[round(float(Zs[ks].min()), 1), round(float(Zs[ks].max()), 1)], sha256=sha)
json.dump(rep, open(os.path.join(os.path.dirname(os.path.abspath(a.out)), 'prep.json'), 'w'), indent=1)
print(json.dumps(rep))
