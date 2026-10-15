# Provenance: Project HERCULES | owner the owner | [id removed]
"""40-point leave-one-out selection of the deformation field (prereg_na.md). Writes field_final.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from field import load_points, Field
REPO = "/home/user/dominion"
A, c, P, U, ids = load_points()
grid = [0, 1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100]
cands = [("Q", 0.0, 0)] + [(k, s, i) for k in ("thin_plate_spline", "linear") for i, s in enumerate(grid)]
res = []
for kind, sm, rank in cands:
    e = []
    for i in range(len(P)):
        k = np.arange(len(P)) != i
        e.append(U[i] - Field(P[k], U[k], kind, sm)(P[i])[0])
    e = np.array(e); n = np.linalg.norm(e, axis=1)
    res.append(dict(kind=kind, smoothing=sm, loo_rms9=float(np.sqrt((n ** 2).mean())), loo_max9=float(n.max()),
                    loo_rms9_z=float(np.sqrt((e[:, 2] ** 2).mean()))))
    print(res[-1], flush=True)
none = np.linalg.norm(U, axis=1)
best = min(r["loo_rms9"] for r in res)
# ties within 0.01: simpler / larger smoothing. Order of preference: Q, then largest smoothing.
tied = [r for r in res if r["loo_rms9"] <= best + 0.01]
tied.sort(key=lambda r: (r["kind"] != "Q", -r["smoothing"], r["kind"] != "linear"))
ch = tied[0]
out = dict(kind=ch["kind"], smoothing=ch["smoothing"], loo_rms9=ch["loo_rms9"], loo_max9=ch["loo_max9"],
           affine_only_rms9_over_40=float(np.sqrt((none ** 2).mean())), n_points=len(P), point_ids=ids,
           candidates=res, tie_rule="within 0.01 vox of best: prefer Q, then larger smoothing, then linear kernel")
json.dump(out, open(f"{REPO}/logs/sib/reg0841na/field_final.json", "w"), indent=1)
print("CHOSEN", {k: out[k] for k in ("kind", "smoothing", "loo_rms9", "loo_max9", "affine_only_rms9_over_40")})
