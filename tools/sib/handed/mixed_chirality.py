# Provenance: Project HERCULES | owner the owner | [id removed]
"""Where does a mesh's chirality vote split? Per mesh: vertices whose local
chirality is -1 under EVERY available r_out source (a genuine orientation
reversal of the parameterisation: fold, sheet jump or self-overlap) versus
vertices where the sources disagree (an r_out problem); connected-component
structure of the reversed set; conditioning of the normal-line centre.
Numbers only. Usage: python mixed_chirality.py OUT_JSON SCROLL [SCROLL ...]"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import label

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_meshes as A  # noqa: E402
from hercules.geometry import level_mesh as L  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402
from hercules.pipeline.centre import geometric_centre_curve  # noqa: E402

out = []
for scroll in sys.argv[2:]:
    for d in sorted(A.S3.glob(f"{scroll}/segments/*/mesh/*.tifxyz")):
        vol = d.name.split("-on-")[1].split("-")[0]
        if scroll == "PHerc0009B" or "2.399um" in d.name:
            continue
        p = read_tifxyz(d).points.astype(np.float64)
        ok = valid_mask(p)
        src = {}
        cc, ci = A.centroid_curve(scroll)
        if cc is not None and vol in ci.get("volume", ""):
            src["centroid"] = cc
        uc, _ = A.umbilicus_curve(scroll, vol)
        if uc is not None:
            src["umbilicus"] = uc
        gc, gi = geometric_centre_curve(p.astype(np.float32), z_bin_vox=400.0, min_vertices=50, stride=2)
        src["geometric"] = gc
        maps = {k: L.chirality_map(p, v) for k, v in src.items()}
        clear = np.ones(p.shape[:2], bool)
        for m in maps.values():
            clear &= np.isfinite(m) & (np.abs(np.nan_to_num(m)) > 0.1)
        n_clear = int(clear.sum())
        all_neg = clear.copy()
        all_pos = clear.copy()
        for m in maps.values():
            all_neg &= np.nan_to_num(m) < 0
            all_pos &= np.nan_to_num(m) > 0
        split = clear & ~all_neg & ~all_pos
        lab, n = label(all_neg)
        sizes = np.bincount(lab.ravel())[1:] if n else np.array([0])
        out.append(dict(scroll=scroll, segment=d.parts[len(A.S3.parts) + 2], sources=sorted(src), n_clear=n_clear,
                        frac_all_sources_reversed=float(all_neg.sum() / max(n_clear, 1)),
                        frac_sources_disagree=float(split.sum() / max(n_clear, 1)),
                        reversed_components=int(n), reversed_largest_component_share=float(sizes.max() / max(all_neg.sum(), 1)),
                        geometric_cond_median=float(np.median(gi["cond"])), geometric_cond_max=float(np.max(gi["cond"]))))
        r = out[-1]
        print(scroll, r["segment"][:22], "reversed %.3f (largest comp %.2f of %d comps) disagree %.3f cond med %.1f max %.1f" % (
            r["frac_all_sources_reversed"], r["reversed_largest_component_share"], r["reversed_components"],
            r["frac_sources_disagree"], r["geometric_cond_median"], r["geometric_cond_max"]), flush=True)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
