# Provenance: Project HERCULES | owner the owner | [id removed]
"""Validation of DECL-P4-24 (e) extrapolation, mesh geometry only (no CT):
fit the edge tangent on the last 10 valid vertices of a column exactly as
holes.py does, predict INTO the mesh by d mm, and measure the perpendicular
miss from the true mesh vertex (known surface). If the miss exceeds the
+-60 um profile window, a peak found at that distance beyond the edge is not
evidence that the SAME sheet continues.
usage: holes_extrap_check.py <mesh_dir> <out.json>"""
import json, sys
import numpy as np
X, Y, Z = (np.load(f"{sys.argv[1]}/{c}.npy") for c in "xyz")
V = (X != -1) & (Z > 0)
P = np.stack([X, Y, Z], -1).astype(float)
T = 8343
out = {}
for r, sgn in ((0, -1), (8, 1)):
    g0, g1 = (r * T) // 20, min(3488, ((r + 1) * T) // 20)
    for dmm in (0.5, 1, 2, 5):
        n = int(round(dmm / 0.048)); drift = []
        for j in range(0, 8500, 25):
            rows = np.where(V[g0:g1, j])[0] + g0
            if len(rows) < n + 12:
                continue
            seq = rows[:10] if r == 0 else rows[-10:]
            d = np.polyfit(seq.astype(float), P[seq, j], 1)[0]; t = sgn * d / np.linalg.norm(d)
            i0 = seq[0] if r == 0 else seq[-1]
            it = i0 + n if r == 0 else i0 - n
            if not V[it, j]:
                continue
            v = P[it, j] - P[i0, j]; along = v @ (-t)
            drift.append(float(np.linalg.norm(v - along * (-t)) * 2.4))
        a = np.array(drift)
        out[f"r{r}_{dmm}mm"] = {"n_columns": int(a.size), "perp_drift_um_p50": float(np.median(a)),
                                "p75": float(np.percentile(a, 75)), "frac_within_60um": float(np.mean(a < 60))}
json.dump(out, open(sys.argv[2], "w"), indent=1); print(json.dumps(out))
