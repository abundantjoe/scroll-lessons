# Provenance: Project HERCULES | owner the owner | [id removed]
"""Attempt 2 field selection (prereg_attempt2.md): leave-one-out over the 40 correspondences
(24 fit rows of the final pass + 16 attempt-1 held-out rows). Writes field_final.json."""
import json, os
import numpy as np
from scipy.interpolate import RBFInterpolator
REPO = "/home/user/dominion"; OUT = f"{REPO}/logs/sib/ktlb4p-prep/reg"
S = 1000.0
mod = json.load(open(f"{OUT}/model_final.json")); A = np.array(mod["A"]); c = np.array(mod["c"])
fr = json.load(open(f"{OUT}/fit_result.json"))["passes"][-1]["rows"]
plan = {p["id"]: p for p in json.load(open(f"{OUT}/patch_plan.json"))["patches"]}
ho = json.load(open(f"{OUT}/heldout_result.json"))["rows"]
P, Q, ids = [], [], []
for r in fr:
    P.append(r["p"]); Q.append(r["q"]); ids.append(r["id"])
for r in ho:
    p = np.array(plan[r["id"]]["centre_xyz"]) - 0.5  # block centre (origin + (n - 1)/2)
    P.append(p.tolist()); Q.append((A @ (p + np.array(r["d9"])) + c).tolist()); ids.append(r["id"])
P = np.array(P); Q = np.array(Q)
U = np.linalg.solve(A, (Q - c).T).T - P


def qf(X):
    x, y, z = (np.atleast_2d(X) / S).T
    return np.c_[x, y, z, np.ones(len(x)), x * x, x * y, y * y]


def fit(Pk, Uk, kind, sm):
    if kind == "Q":
        W = np.linalg.lstsq(qf(Pk), Uk, rcond=None)[0]
        return lambda X: qf(X) @ W
    r = RBFInterpolator(Pk / S, Uk, kernel=kind, degree=1, smoothing=sm)
    return lambda X: r(np.atleast_2d(X) / S)


grid = [0, 1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100]
cands = [("Q", 0.0)] + [(k, s) for k in ("thin_plate_spline", "linear") for s in grid]
res = []
for kind, sm in cands:
    e = np.array([U[i] - fit(P[np.arange(len(P)) != i], U[np.arange(len(P)) != i], kind, sm)(P[i])[0] for i in range(len(P))])
    n = np.linalg.norm(e, axis=1)
    res.append(dict(kind=kind, smoothing=sm, loo_rms9=float(np.sqrt((n ** 2).mean())), loo_max9=float(n.max())))
    print(res[-1], flush=True)
best = min(r["loo_rms9"] for r in res)
tied = [r for r in res if r["loo_rms9"] <= best + 0.01]
tied.sort(key=lambda r: (r["kind"] != "Q", -r["smoothing"], r["kind"] != "linear"))
ch = tied[0]
none = np.linalg.norm(U, axis=1)
out = dict(kind=ch["kind"], smoothing=ch["smoothing"], loo_rms9=ch["loo_rms9"], loo_max9=ch["loo_max9"],
           affine_only_rms9_over_40=float(np.sqrt((none ** 2).mean())), n_points=len(P), point_ids=ids,
           points_p9=P.tolist(), displacements_u9=U.tolist(), base_affine_sha256_note="model_final.json 9a777170...",
           candidates=res, tie_rule="within 0.01 vox of best: prefer Q, then larger smoothing, then linear kernel",
           form="f(p) = A (p + u(p)) + c; u fitted to points_p9 -> displacements_u9 with (kind, smoothing)")
if ch["kind"] == "Q":
    out["W"] = np.linalg.lstsq(qf(P), U, rcond=None)[0].tolist()
json.dump(out, open(f"{OUT}/field_final.json", "w"), indent=1)
print("CHOSEN", {k: out[k] for k in ("kind", "smoothing", "loo_rms9", "loo_max9", "affine_only_rms9_over_40")})
