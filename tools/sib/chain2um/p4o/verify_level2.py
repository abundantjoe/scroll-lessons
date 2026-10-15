# Provenance: Project HERCULES | owner the owner | [id removed]
# (a) organizer SV level 2 vs our 4x4 XY mean of level 0 (same slab z [23, 85)), 512 x 512 level-0 px at the
#     r5_c10 verify region; (b) re-read of tile r0_c0 centre ROI reproduces the manifest sha256. Numbers only.
import json, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import p4o_stack as P
sys.path.insert(0, '/home/user/dominion/src'); from hercules.metrics.pixel import pearson
y0, x0 = 45824, 87552
l0 = P.read_stack(y0, y0 + 512, x0, x0 + 512).astype(np.float64)
ours = l0.reshape(128, 4, 128, 4, 62).mean((1, 3))
org = P.read_stack(y0 // 4, y0 // 4 + 128, x0 // 4, x0 // 4 + 128, level=2).astype(np.float64)
d = np.abs(np.rint(ours) - org)
m = json.load(open('/work/p4o/tiles_manifest.json'))['tiles']['r0_c0']
a, b, c_, e = m['center_roi_canvas_yx']
rh = P.stack_sha256(P.read_stack(a, b, c_, e))
out = dict(level2_vs_xy4mean_r=pearson(ours, org), level2_max_abs_diff_after_rint=float(d.max()), level2_mean_abs_diff=float(d.mean()),
           level2_frac_exact=float((d == 0).mean()), reread_r0_c0_sha256=rh, manifest_r0_c0_sha256=m['center_roi_slab_sha256'],
           reread_matches=rh == m['center_roi_slab_sha256'])
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(json.dumps(out))
