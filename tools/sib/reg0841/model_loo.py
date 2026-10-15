# Provenance: Project HERCULES | owner the owner | [id removed]
"""Leave-one-out comparison of mapping models on the 24 FIT correspondences only (pass 2 of
fit_result.json). No held-out data is read. Models (q2 = f(p9)):
 M0 affine (12 params)
 M1 affine + z-output term a*rho^2, rho = distance from the 9 um reconstruction axis (x=y=3851.25) (13)
 M2 affine + z-output terms in x^2, xy, y^2 (15)
 M3 affine + x^2, xy, y^2 terms in all outputs (21)
 M4 full quadratic in x, y, z for all outputs (30)
Coordinates are centred/scaled (by Pm and 1000 vox) before building the design matrix."""
import json, sys
import numpy as np
REPO = "/home/user/dominion"
d = json.load(open(f"{REPO}/logs/sib/reg0841/fit_result.json"))["passes"][-1]
P = np.array([r["p"] for r in d["rows"]]); Q = np.array([r["q"] for r in d["rows"]])
Pm = P.mean(0); AX = 3851.25


def feats(P, model):
    u = (P - Pm) / 1000.0; x, y, z = u.T; one = np.ones(len(P))
    lin = np.c_[x, y, z, one]
    rho2 = (((P[:, 0] - AX) ** 2 + (P[:, 1] - AX) ** 2) / 1e6)
    if model == "M0": return lin, lin
    if model == "M1": return lin, np.c_[lin, rho2]
    if model == "M2": return lin, np.c_[lin, x * x, x * y, y * y]
    if model == "M3": q = np.c_[lin, x * x, x * y, y * y]; return q, q
    if model == "M4":
        q = np.c_[lin, x * x, x * y, y * y, x * z, y * z, z * z]; return q, q


def fit(P, Q, model):
    Fxy, Fz = feats(P, model)
    cx = np.linalg.lstsq(Fxy, Q[:, :2], rcond=None)[0]; cz = np.linalg.lstsq(Fz, Q[:, 2], rcond=None)[0]
    return cx, cz


def pred(P, model, co):
    Fxy, Fz = feats(P, model); return np.c_[Fxy @ co[0], Fz @ co[1]]



def model_fn(model):
    """Model fitted on all 24 fit correspondences, returned as f(P) -> Q."""
    co = fit(P, Q, model)
    return lambda X: pred(np.atleast_2d(X), model, co)


if __name__ == "__main__":
    A = np.array(json.load(open(f"{REPO}/logs/sib/reg0841/affine_final.json"))["A"]); Ai = np.linalg.inv(A)
    out = {}
    for m in ["M0", "M1", "M2", "M3", "M4"]:
        co = fit(P, Q, m); res = (Q - pred(P, m, co)) @ Ai.T
        loo = []
        for i in range(len(P)):
            k = np.arange(len(P)) != i
            coi = fit(P[k], Q[k], m); loo.append(((Q[i] - pred(P[i:i + 1], m, coi)[0]) @ Ai.T))
        loo = np.array(loo); nl = np.linalg.norm(loo, axis=1)
        out[m] = dict(n_params=int(feats(P, m)[0].shape[1] * 2 + feats(P, m)[1].shape[1]),
                      fit_rms9=float(np.sqrt((np.linalg.norm(res, axis=1) ** 2).mean())),
                      loo_rms9=float(np.sqrt((nl ** 2).mean())), loo_max9=float(nl.max()),
                      loo_rms9_z=float(np.sqrt((loo[:, 2] ** 2).mean())), loo_rms9_xy=float(np.sqrt((loo[:, :2] ** 2).sum(1).mean())))
        print(m, {k: round(v, 3) for k, v in out[m].items()})
    json.dump(out, open(f"{REPO}/logs/sib/reg0841/model_loo.json", "w"), indent=1)
