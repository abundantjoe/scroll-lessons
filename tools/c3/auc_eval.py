# Provenance: Project HERCULES | owner the owner | [id removed]
"""C3 AUC: Mann-Whitney AUC (hercules.metrics.pixel.auc) of model maps against native9 w040 labels.

Labels: HF scrollprize/datasets ink_9um/labels/native9-scrollprizeorg-21slices/w040, Z=14 plane.
Binarisation: ink = label > (min + max) / 2 of the label value range; blank = label == 0; other values ignored.
Valid pixels: model-input valid mask (any of the 28 slices nonzero) AND label canvas overlap.
Usage: auc_eval.py OUT.json MODE ...
  MODE crop  <render_valid.npy> name=map.tif ...   (maps are 2048 x 2048 on crop x1152 y2048)
  MODE full  <sv_zarr> name=map.tif ...            (maps are full SV canvas 6400 x 7980)
"""
import json, os, sys, hashlib
import numpy as np
import tifffile, zarr
from hercules.metrics.pixel import auc

OUT, MODE, SRC = sys.argv[1], sys.argv[2], sys.argv[3]
maps = dict(a.split('=', 1) for a in sys.argv[4:])
LAB = os.environ.get('C3_LAB', '/work/c3/data/hf/native9/w040/w040_inklabels.zarr/0')  # label array via env (DECL-C3-NT-R1)
SUP = os.environ.get('C3_SUP', '/work/c3/data/hf/native9/w040/w040_supervision_mask.zarr/0')  # supervision array via env
lab_arr = zarr.open_array(LAB, mode='r'); sup_arr = zarr.open_array(SUP, mode='r')
lab = lab_arr[14]; sup = sup_arr[14]
lo, hi = int(lab_arr[:].min()), int(lab_arr[:].max())
thr = (lo + hi) / 2.0
lab01 = np.full(lab.shape, 2, np.uint8)
lab01[lab > thr] = 1
lab01[lab == 0] = 0
res = {'provenance': 'Project HERCULES | owner the owner | [id removed]', 'mode': MODE,
       'label_array_shape': list(lab_arr.shape), 'label_plane': 14, 'label_value_range': [lo, hi],
       'binarisation_threshold': thr, 'maps': {}}
if MODE == 'crop':
    X0, Y0, W, H = int(os.environ.get("C3_X0", 1152)), int(os.environ.get("C3_Y0", 2048)), 2048, 2048  # crop origin via env (DECL-C3-R1)
    sl = (slice(Y0, Y0 + H), slice(X0, X0 + W))
    valid = np.load(SRC)
    L = lab01[sl]; S = sup[sl] > 0
    res['crop'] = {'x': X0, 'y': Y0, 'width': W, 'height': H}
else:
    sv = zarr.open_array(SRC + '/0', mode='r')
    assert sv.shape == lab_arr.shape, (sv.shape, lab_arr.shape)
    valid = np.zeros(sv.shape[1:], bool)
    for y in range(0, sv.shape[1], 512):
        valid[y:y + 512] = (sv[:, y:y + 512, :] > 0).any(0)
    L = lab01; S = sup > 0
    ys, xs = np.nonzero(lab > 0)
    bb = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    bbm = np.zeros_like(valid); bbm[bb] = True
    res['label_bbox_rows_cols'] = [int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())]
res['valid_px'] = int(valid.sum())
res['ink_px_valid'] = int(((L == 1) & valid).sum()); res['blank_px_valid'] = int(((L == 0) & valid).sum())
res['ink_px_valid_in_supervision'] = int(((L == 1) & valid & S).sum())
res['blank_px_valid_in_supervision'] = int(((L == 0) & valid & S).sum())
for name, path in maps.items():
    try:
        m = tifffile.imread(path)
    except ValueError:  # LZW needs imagecodecs (absent in /opt/hv): use the tif2npy.py decode of the same file
        m = np.load(path + '.npy')
    assert m.shape == L.shape, (name, m.shape, L.shape)
    ent = {'path': path, 'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest(),
           'shape': list(m.shape), 'dtype': str(m.dtype),
           'auc_declared_valid': auc(m, L, valid),
           'supp_auc_within_supervision_mask': auc(m, L, valid & S),
           'map_mean_valid': float(m[valid].mean())}
    if MODE == 'full':
        ent['supp_auc_within_label_bbox'] = auc(m, L, valid & bbm)
    res['maps'][name] = ent
    print(name, json.dumps(ent))
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'maps'}))
