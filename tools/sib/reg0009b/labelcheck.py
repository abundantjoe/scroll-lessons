# Provenance: Project HERCULES | owner the owner | [id removed]
"""Numbers-only alignment check of the official 20260918 ink labels against the official 2.401 um
reference ink map of the same segment (both on the 2.401 um canvas). Block-mean 4 x 4 downsampling;
NCC of the label map against the reference map over the supervision region, integer shifts within
+-24 downsampled px (+-96 canvas px), parabolic sub-pixel peak. Also label/ref agreement numbers."""
import json, os, sys, glob
import numpy as np, cv2, tifffile, zarr

seg = sys.argv[1]
D = f'/work/reg0009b/data/{seg}'
L = glob.glob(f'{D}/ink-labels/*/*/')[0]
lab = zarr.open_array(L + 'inklabels.zarr/0', mode='r')[:]
sup = zarr.open_array(L + 'supervision.zarr/0', mode='r')[:]
val = zarr.open_array(L + 'validation.zarr/0', mode='r')[:]
ink = tifffile.imread(glob.glob(f'{D}/ink-detection/*.tif')[0])
assert lab.shape == ink.shape, (lab.shape, ink.shape)
F = int(os.environ.get("LC_F", "4"))
H, W = ink.shape; f = F; h, w = H // f, W // f
def ds(a): return a[:h * f, :w * f].reshape(h, f, w, f).astype(np.float32).mean((1, 3))
Ld, Rd, Sd = ds(lab) / 255, ds(ink) / 255, ds(sup) / 255
ys, xs = np.nonzero(Sd > 0.99)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
R = 96 // F
tmpl = (Ld * (Sd > 0.99))[y0:y1, x0:x1]
win = np.pad(Rd, R)[y0:y1 + 2 * R, x0:x1 + 2 * R]
res = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
v, u = np.unravel_index(np.argmax(res), res.shape)
def sub(c, lo):
    if 0 < c < len(lo) - 1:
        den = lo[c - 1] - 2 * lo[c] + lo[c + 1]
        if den < 0: return c + 0.5 * (lo[c - 1] - lo[c + 1]) / den
    return float(c)
uu, vv = sub(u, res[v]), sub(v, res[:, u])
m = sup > 0
out = dict(segment=seg, canvas=[H, W], label_frac_canvas=float((lab > 0).mean()), supervision_frac=float(m.mean()),
           validation_frac=float((val > 0).mean()), validation_inside_supervision=float(((val > 0) & m).sum() / max((val > 0).sum(), 1)),
           label_ink_frac_in_supervision=float((lab[m] > 0).mean()),
           ref_ge150_frac_in_supervision=float((ink[m] >= 150).mean()),
           ref_ge150_given_label=float((ink[m & (lab > 0)] >= 150).mean()),
           ref_ge150_given_nolabel=float((ink[m & (lab == 0)] >= 150).mean()),
           ncc_ds_at_zero=float(res[R, R]), ncc_ds_peak=float(res[v, u]),
           # template (label) at window offset (u, v): label content lies at ref position + (u - R, v - R)
           label_to_ref_shift_canvas_px=[float((uu - R) * f), float((vv - R) * f)],
           downsample=F, note='shift = where the label content best matches the reference map, relative to identical canvas coordinates (canvas px, x then y)')
print(json.dumps(out, indent=1))
json.dump(out, open(f'/home/user/dominion/logs/sib/reg0009b/labelcheck_{seg.split("-")[0]}_f{F}.json', 'w'), indent=1)
