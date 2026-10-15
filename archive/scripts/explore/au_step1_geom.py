"""AUDIT step 1 (TRAINING crop only): label geometry.

How thick are the labelled strokes?  The erosion margins used in step 2 must be margins that
actually leave pixels behind, so the attainable margins are read off the training crop first.
"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import au_lib as A

res = {}
for seg, crop in A.TRAIN:
    L, text, blank, m = A.load_masks(seg, crop)
    d_in = A.edt_mm(L)          # for label pixels: distance to nearest non-label px  (= half stroke width at the ridge)
    d_out = A.edt_mm(~L)        # for non-label pixels: distance to nearest label px
    qs = [50, 75, 90, 95, 99, 99.9]
    ent = {
        "shape": list(L.shape),
        "label_frac": round(float(L.mean()), 4),
        "mask_frac": round(float(m.mean()), 4),
        "text_px": int(text.sum()), "blank_px": int(blank.sum()),
        "d_in_mm_quantiles_on_text": {str(q): round(float(np.percentile(d_in[text], q)), 4) for q in qs},
        "d_in_mm_max": round(float(d_in[text].max()), 4),
        "frac_text_deeper_than": {f"{t}": round(float((d_in[text] > t).mean()), 4)
                                  for t in (0.05, 0.1, 0.15, 0.2, 0.3, 0.45, 0.6, 1.0)},
        "frac_blank_further_than": {f"{t}": round(float((d_out[blank] > t).mean()), 4)
                                    for t in (0.3, 0.45, 0.6, 0.9, 1.3, 2.0, 3.0, 5.0)},
        "d_out_mm_max_on_mask": round(float(d_out[m].max()), 3),
        "on_sheet_unlabelled_frac_gt5mm": round(float((m & (d_out > 5.0)).mean()), 4),
    }
    res[f"{seg}/{crop}"] = ent
    print(seg, crop, flush=True)
    for k, v in ent.items():
        print("  ", k, v, flush=True)
A.jwrite(os.path.join(A.ROOT, "stats/explore/au_step1_geom.json"), res)
