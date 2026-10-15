# Provenance: Project HERCULES | owner the owner | [id removed]
"""Score chain2um maps on the code-selected w043 control (numbers only; nothing is displayed).

Region E = organizer supervision pixels (label_set 20260918, value 255) inside the eval bbox of
control_selection.json. Labels: ink = inklabels 255, blank = 0, both inside supervision.
Metrics use src/hercules/metrics/pixel.py (sha256 a5ab7fed..., METRIC-HASH): Mann-Whitney AUC (average ranks)
and Pearson r. r_org = Pearson with the organizer 2.399 um map (model 20260417190342); r_lab = point-biserial
Pearson with the 0/1 labels. Usage: eval2um.py selection.json out.json name=mapdir [name=mapdir ...]
"""
import json, sys, hashlib
import numpy as np, zarr, tifffile
sys.path.insert(0, '/home/user/dominion/src')
from hercules.metrics.pixel import auc, pearson

sel = json.load(open(sys.argv[1]))
cy0, cy1, cx0, cx1 = sel['crop_yx']; y0, y1, x0, x1 = sel['eval_bbox_yx']
R = '/work/c2um/org/lab/2.399um-volume-20260102150214/20260918/'
ink = zarr.open(R + 'inklabels.zarr', mode='r')['0'][y0:y1, x0:x1] > 0
sup = zarr.open(R + 'supervision.zarr', mode='r')['0'][y0:y1, x0:x1] > 0
with tifffile.TiffFile('/work/c2um/org/inkmap_org.tif') as t:
    org = t.pages[0].asarray()[y0:y1, x0:x1].astype(np.float32)
lab = ink.astype(np.uint8)
out = dict(selection=sel, n_eval=int(sup.sum()), n_ink=int((ink & sup).sum()), n_blank=int((~ink & sup).sum()),
           organizer_map=dict(auc_labels=auc(org, lab, sup), r_labels=pearson(org, lab, sup),
                              mean_in_E=float(org[sup].mean())))
maps = {}
for spec in sys.argv[3:]:
    name, d = spec.split('=', 1)
    z = np.load(d + '/map.npz')
    m = z['map'][y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0]
    u8 = z['u8']
    maps[name] = (z['map'], u8)
    out[name] = dict(map_sha256_u8=hashlib.sha256(u8.tobytes()).hexdigest(),
                     auc_labels=auc(m, lab, sup), r_labels=pearson(m, lab, sup),
                     r_org_E=pearson(m, org, sup), r_org_bbox=pearson(m, org),
                     auc_labels_u8=auc(u8[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0], lab, sup),
                     mean_in_E=float(m[sup].mean()))
pairs = {}
names = list(maps)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = maps[names[i]], maps[names[j]]
        ai, bi = a[0][y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0], b[0][y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0]
        du8 = np.abs(a[1].astype(np.int16) - b[1].astype(np.int16))
        pairs[f'{names[i]}__vs__{names[j]}'] = dict(
            r_crop=pearson(a[0], b[0]), r_bbox=pearson(ai, bi), r_E=pearson(ai, bi, sup),
            u8_max_abs_diff=int(du8.max()), u8_mean_abs_diff=float(du8.mean()), u8_frac_diff_gt2=float((du8 > 2).mean()))
out['pairs'] = pairs
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'selection'}, indent=1))
