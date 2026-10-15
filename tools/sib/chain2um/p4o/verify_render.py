# Provenance: Project HERCULES | owner the owner | [id removed]
# Verify on w010-027 that the organizer 2.4 um SV (as read by p4o_stack.read_stack) equals the official
# vc_render_tifxyz --flip-normals render: per region, pooled Pearson over the 109 slices at offset 0 and the
# chain slab [23, 85). Regions: 3 tiles drawn by seed 20260926 among r0-5 c0-17 tiles with >= 95 % mesh-valid,
# 256 x 256 at the 128-aligned tile centre. Numbers only.
import json, subprocess, sys, os, numpy as np, zarr
sys.path.insert(0, os.path.dirname(__file__)); import p4o_stack as P
sys.path.insert(0, '/home/user/dominion/src'); from hercules.metrics.pixel import pearson
vf = json.load(open('/work/p4o/tile_valid_frac.json'))
cand = sorted(k for k, f in vf.items() if f >= 0.95 and int(k.split('_')[0][1:]) <= 5 and int(k.split('_c')[1]) <= 17)
pick = [cand[i] for i in np.random.default_rng(20260926).choice(len(cand), 3, replace=False)]
V = 's3://vesuvius-challenge-open-data/PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/'
res = dict(candidates=len(cand), picked=pick, regions=[])
for k in pick:
    r, c = int(k.split('_')[0][1:]), int(k.split('_c')[1])
    y0, y1, x0, x1 = P.tile_bounds(r, c)
    cy, cx = ((y0 + y1) // 2) // 128 * 128, ((x0 + x1) // 2) // 128 * 128
    out = f'/work/p4o/render_{k}.zarr'
    cmd = ['/work/bin/vc', 'vc_render_tifxyz', '-v', V, '--remote-url', V, '--segmentation', '/work/p4o/mesh', '--scale', '1',
           '--group-idx', '0', '--num-slices', '109', '--slice-step', '1', '--voxel-size', '2.4', '--voxel-unit', 'micrometer',
           '--flip-normals', '--crop-x', str(cx), '--crop-y', str(cy), '--crop-width', '256', '--crop-height', '256',
           '--cache-gb', '4', '--zarr-output', out]
    if not os.path.exists(out):
        rc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    else:
        rc = 0
    ren = zarr.open(out, mode='r')['0'][:]                                   # (109, 256, 256)
    sv = np.transpose(P.read_stack(cy, cy + 256, cx, cx + 256, z0=0, nz=109), (2, 0, 1))
    slab = P.read_stack(cy, cy + 256, cx, cx + 256)                          # (256, 256, 62) default z0=23
    per = [pearson(ren[i], sv[i]) for i in range(109)]
    res['regions'].append(dict(tile=k, canvas_yx=[cy, cx], render_rc=rc, cmd=' '.join(cmd),
        pooled_r_offset0=pearson(ren, sv), per_slice_min=float(np.nanmin(per)), per_slice_argmin=int(np.nanargmin(per)),
        exact_equal_fraction=float((ren == sv).mean()), pooled_r_reversed=pearson(ren[::-1], sv),
        slab_equals_render_23_85=bool((np.transpose(slab, (2, 0, 1)) == sv[23:85]).all()),
        slab_vs_render_23_85_r=pearson(np.transpose(slab, (2, 0, 1)), ren[23:85]),
        sv_nonzero_fraction=float((sv > 0).mean())))
    print(json.dumps(res['regions'][-1] | {'cmd': '...'}), flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
