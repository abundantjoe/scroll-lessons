# Provenance: Project HERCULES | owner the owner | [id removed]
"""C3 render fidelity: Pearson r between our render and the team SV over the declared crop.

Metric code: hercules.metrics.pixel.pearson (declared sha256 a5ab7fed...7c8).
Primary (declared, literal): all 2048 x 2048 crop pixels, per slice at zero offset; min over slices; pooled.
Supplementary (labelled as such): jointly-valid pixels only; integer slice-offset scan; integer canvas-shift scan;
reversed slice order. Nothing is re-aligned for the primary numbers.
"""
import json, os, sys, hashlib
import numpy as np
import zarr
from hercules.metrics.pixel import pearson

RENDER = sys.argv[1]            # our render zarr group (level 0 = 28 x 2048 x 2048)
SV = sys.argv[2]                # team SV zarr group (local mirror)
OUT = sys.argv[3]
X0, Y0, W, H = int(os.environ.get("C3_X0", 1152)), int(os.environ.get("C3_Y0", 2048)), 2048, 2048  # crop origin via env (DECL-C3-R1)

r = zarr.open_array(RENDER + '/0', mode='r')[:]
sv_arr = zarr.open_array(SV + '/0', mode='r')
M = 4  # margin for the shift scan
sv_big = sv_arr[:, Y0 - M:Y0 + H + M, X0 - M:X0 + W + M]
sv = sv_big[:, M:M + H, M:M + W]
assert r.shape == sv.shape == (28, H, W), (r.shape, sv.shape)

rv = (r > 0).any(0)
svv = (sv > 0).any(0)
both = rv & svv
res = {
    'provenance': 'Project HERCULES | owner the owner | [id removed]',
    'render_shape': list(r.shape), 'sv_crop_shape': list(sv.shape), 'sv_full_shape': list(sv_arr.shape),
    'crop': {'x': X0, 'y': Y0, 'width': W, 'height': H, 'axes': 'x=column, y=row on SV canvas'},
    'render_valid_px': int(rv.sum()), 'sv_valid_px': int(svv.sum()), 'joint_valid_px': int(both.sum()),
    'render_valid_not_sv': int((rv & ~svv).sum()), 'sv_valid_not_render': int((svv & ~rv).sum()),
    'exact_equal_voxel_fraction_all': float((r == sv).mean()),
    'mean_abs_diff_all': float(np.abs(r.astype(np.int16) - sv.astype(np.int16)).mean()),
    'max_abs_diff_all': int(np.abs(r.astype(np.int16) - sv.astype(np.int16)).max()),
}
per_all = [pearson(r[k], sv[k]) for k in range(28)]
per_valid = [pearson(r[k], sv[k], both) for k in range(28)]
res['primary_all_pixels'] = {
    'per_slice': per_all, 'min': float(np.nanmin(per_all)), 'argmin_slice': int(np.nanargmin(per_all)),
    'pooled': pearson(r, sv),
}
res['supp_joint_valid_pixels'] = {
    'per_slice': per_valid, 'min': float(np.nanmin(per_valid)), 'argmin_slice': int(np.nanargmin(per_valid)),
    'pooled': pearson(r, sv, np.broadcast_to(both, r.shape)),
}
# integer slice-offset scan: our slice k+d vs team slice k (overlapping slices only), pooled over joint-valid px
scan = {}
for d in range(-3, 4):
    ks = [k for k in range(28) if 0 <= k + d < 28]
    a = np.stack([r[k + d] for k in ks]); b = np.stack([sv[k] for k in ks])
    scan[str(d)] = pearson(a, b, np.broadcast_to(both, a.shape))
res['supp_slice_offset_scan_pooled_joint_valid'] = scan
res['supp_best_slice_offset'] = int(max(scan, key=lambda k: scan[k]))
res['supp_reversed_slice_order_pooled_joint_valid'] = pearson(r[::-1], sv, np.broadcast_to(both, r.shape))
# integer canvas-shift scan (team SV window shifted by dy, dx), zero slice offset, pooled over interior joint-valid px
inner = np.zeros_like(both); inner[M:-M, M:-M] = True
shift = {}
for dy in range(-M, M + 1):
    for dx in range(-M, M + 1):
        s = sv_big[:, M + dy:M + dy + H, M + dx:M + dx + W]
        shift[f'{dy},{dx}'] = pearson(r, s, np.broadcast_to(both & inner, r.shape))
best = max(shift, key=lambda k: shift[k])
res['supp_canvas_shift_scan_pooled_joint_valid_interior'] = {'best_dy_dx': best, 'r_best': shift[best],
                                                              'r_zero': shift['0,0'], 'all': shift}
np.save(OUT.replace('.json', '_render_valid.npy'), rv)
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('supp_canvas_shift_scan_pooled_joint_valid_interior',)}, indent=1)[:4000])
print('shift best', best, shift[best], 'zero', shift['0,0'])
