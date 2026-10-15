# Provenance: Project HERCULES | owner the owner | [id removed]
# Pick the chain2um control crop BY CODE, before any inference: the largest 8-connected component of
# 128-px canvas blocks with >50 % organizer supervision on PHerc0139 w043 (2.399 um canvas), then its
# block bbox + a 128-px context margin (render/inference crop). Evaluation pixels = supervised pixels
# inside the bbox. Numbers only; no image is written or viewed.
import json, sys, hashlib, numpy as np, zarr, tifffile
from scipy.ndimage import label
R = '/work/c2um/org/lab/2.399um-volume-20260102150214/20260918/'
B, M = 128, 128
ink = zarr.open(R + 'inklabels.zarr', mode='r')['0'][:] > 0
sup = zarr.open(R + 'supervision.zarr', mode='r')['0'][:] > 0
H, W = sup.shape; h, w = H // B, W // B
sb = sup[:h*B, :w*B].reshape(h, B, w, B).mean((1, 3))
lab, n = label(sb > 0.5, structure=np.ones((3, 3)))
sizes = [(lab == i).sum() for i in range(1, n + 1)]
k = int(np.argmax(sizes)) + 1
yy, xx = np.nonzero(lab == k)
y0, y1, x0, x1 = yy.min()*B, (yy.max()+1)*B, xx.min()*B, (xx.max()+1)*B
cy0, cy1, cx0, cx1 = y0 - M, y1 + M, x0 - M, x1 + M
mx = tifffile.imread('/work/c2um/org/mesh/x.tif')  # mesh grid; canvas = grid x 20
mv = np.kron((mx != -1).astype(np.uint8), np.ones((20, 20), np.uint8)).astype(bool)[:H, :W]
e_sup = sup[y0:y1, x0:x1]; e_ink = ink[y0:y1, x0:x1] & e_sup
out = dict(segment='20260112000000-w043_2026011217', canvas=[int(H), int(W)], block=B, margin=M,
           components=[int(s) for s in sizes], chosen_component_blocks=int(sizes[k-1]),
           eval_bbox_yx=[int(y0), int(y1), int(x0), int(x1)],
           crop_yx=[int(cy0), int(cy1), int(cx0), int(cx1)], crop_hw=[int(cy1-cy0), int(cx1-cx0)],
           eval_supervised_px=int(e_sup.sum()), eval_ink_px=int(e_ink.sum()),
           eval_ink_fraction=float(e_ink.sum() / e_sup.sum()),
           eval_area_cm2=float(e_sup.sum() * (2.399e-4) ** 2),
           crop_area_cm2=float((cy1-cy0) * (cx1-cx0) * (2.399e-4) ** 2),
           mesh_valid_fraction_crop=float(mv[cy0:cy1, cx0:cx1].mean()),
           mesh_valid_fraction_eval_sup=float(mv[y0:y1, x0:x1][e_sup].mean()))
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(json.dumps(out, indent=1))
