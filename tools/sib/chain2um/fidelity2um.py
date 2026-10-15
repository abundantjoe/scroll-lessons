# Provenance: Project HERCULES | owner the owner | [id removed]
# Render fidelity: our vc_render_tifxyz -n 63 crop vs the organizer 2.399 um surface volume (109 slices, raw
# uncompressed chunks (109,128,128)). Scans slice offsets j = k + off and reports pooled / per-slice Pearson.
# Usage: fidelity2um.py render.zarr crop_y crop_x orgsv_dir out.json   (numbers only)
import sys, json, os, glob, numpy as np, zarr
sys.path.insert(0, '/home/user/dominion/src')
from hercules.metrics.pixel import pearson
rz, cy, cx, od, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
g = zarr.open(rz, mode='r'); r = (g['0'] if '0' in g else g)
chunks = {}
for f in glob.glob(od + '/c_*'):
    _, a, b = os.path.basename(f).split('_'); chunks[(int(a), int(b))] = np.fromfile(f, np.uint8).reshape(109, 128, 128)
ys = sorted({k[0] for k in chunks}); xs = sorted({k[1] for k in chunks})
org = np.concatenate([np.concatenate([chunks[(a, b)] for b in xs], 2) for a in ys], 1)
oy, ox = ys[0] * 128, xs[0] * 128
H, W = org.shape[1:]
ren = r[:, oy - cy:oy - cy + H, ox - cx:ox - cx + W]
assert ren.shape[1:] == (H, W), (ren.shape, org.shape)
res = dict(render=rz, render_shape=list(r.shape), region_yx=[oy, ox, H, W], offsets={})
for off in range(0, 109 - 63 + 1):
    res['offsets'][off] = pearson(ren, org[off:off + 63])
best = max(res['offsets'], key=lambda k: res['offsets'][k])
per = [pearson(ren[k], org[k + best]) for k in range(63)]
res |= dict(best_offset=best, pooled_r_best=res['offsets'][best], expected_offset=54 - 31,
            per_slice_min=min(per), per_slice_argmin=int(np.argmin(per)),
            reversed_pooled_r_at_expected=pearson(ren[::-1], org[23:86]),
            exact_equal_fraction_at_best=float((ren == org[best:best + 63]).mean()))
json.dump(res, open(outp, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'offsets'}))
