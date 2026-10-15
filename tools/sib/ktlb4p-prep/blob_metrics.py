# Provenance: Project HERCULES | owner the owner | [id removed]
"""Numeric 'blob field' measure of organizer reference ink maps (never viewed).
Binary ink = value >= 150 at native resolution, block-reduced (fraction) to ~10 um px and
thresholded at 0.5; valid region = native value > 0, reduced likewise. Per map: ink fraction of
the valid region, 8-connected components per cm^2, component area quantiles (mm^2), ink-area
fraction in components > 10 mm^2 (larger than any single letter's ink), and stroke width
= 2 x median distance-transform value on the skeleton (um). Usage: blob_metrics.py OUT_JSON"""
import glob, json, sys
import numpy as np
import tifffile
from scipy import ndimage as ndi
from skimage.morphology import skeletonize

def metrics(path, um):
    a = tifffile.imread(path)
    f = max(1, int(round(10.0 / um)))
    H, W = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    a = a[:H, :W]
    ink = (a >= 150).reshape(H // f, f, W // f, f).mean((1, 3)) >= 0.5
    val = (a > 0).reshape(H // f, f, W // f, f).mean((1, 3)) >= 0.5
    del a
    px_um = um * f
    area_cm2 = val.sum() * (px_um * 1e-4) ** 2
    lab, n = ndi.label(ink, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())[1:] * (px_um * 1e-3) ** 2  # mm^2
    big = sizes > 10.0
    sk = skeletonize(ink)
    dt = ndi.distance_transform_edt(ink)
    sw = 2 * np.median(dt[sk]) * px_um if sk.any() else float("nan")
    return dict(px_um=px_um, valid_cm2=float(area_cm2), ink_frac=float(ink.sum() / max(val.sum(), 1)),
                comps_per_cm2=float(n / max(area_cm2, 1e-9)), comp_area_mm2_q50=float(np.median(sizes)) if n else None,
                comp_area_mm2_q90=float(np.percentile(sizes, 90)) if n else None,
                ink_frac_in_comps_gt10mm2=float(sizes[big].sum() / max(sizes.sum(), 1e-12)) if n else None,
                stroke_width_um=float(sw))

out = {"0139_known_text": {}, "0500P2": {}}
for p in sorted(glob.glob("/work/k4p/ref0139/*.tif")):
    out["0139_known_text"][p.split("/")[-1][:-4]] = metrics(p, 2.399); print("0139", out["0139_known_text"][p.split("/")[-1][:-4]], flush=True)
for p in sorted(glob.glob("/work/k4p/ref/*.tif")):
    out["0500P2"][p.split("/")[-1][:-4]] = metrics(p, 2.215)
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k in ("0139_known_text", "0500P2"):
    v = [x for x in out[k].values() if x["valid_cm2"] > 1]
    print(k, len(v), {m: round(float(np.median([x[m] for x in v if x[m] is not None])), 3) for m in
                      ("ink_frac", "comps_per_cm2", "comp_area_mm2_q50", "comp_area_mm2_q90", "ink_frac_in_comps_gt10mm2", "stroke_width_um")})
