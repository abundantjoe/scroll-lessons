"""The radial-normal gate (median |cos| between the surface normal and the radial direction from the scroll axis,
plus radial spread). Reported because it is what many pipelines use, and because it is BLIND to layer jumps:
a surface that steps from one sheet to the next still faces outward. See README, 'What the gate cannot see'."""
import json, sys, numpy as np
from .tifxyz import read, valid_mask

def gate(X, Y, Z, ux, uy, um_per_vox=8.64):
    v = valid_mask(X)
    du = np.stack([np.gradient(a, axis=1) for a in (X, Y, Z)], -1); dv = np.stack([np.gradient(a, axis=0) for a in (X, Y, Z)], -1)
    n = np.cross(du, dv); n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    rad = np.stack([X - ux, Y - uy, np.zeros_like(X)], -1); R = np.linalg.norm(rad, axis=-1); rad /= np.maximum(R[..., None], 1e-9)
    c = np.abs((n * rad).sum(-1))[v]; Rv = R[v]
    side_cm = np.sqrt(v.sum()) * um_per_vox * 1e-4  # grid of cells; one cell per vertex here
    p10, p90 = np.percentile(Rv, [10, 90])
    return {"median_cos": float(np.median(c)), "frac_gt08": float((c > 0.8).mean()), "R_p10": float(p10), "R_p90": float(p90),
            "spread_vox": float(p90 - p10), "n_valid": int(v.sum())}

if __name__ == "__main__":
    d, ux, uy = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); X, Y, Z = read(d); print(json.dumps(gate(X, Y, Z, ux, uy), indent=1))
