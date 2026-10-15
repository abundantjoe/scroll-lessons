# Provenance: Project HERCULES | owner the owner | [id removed]
"""Non-affine 9.366 -> 2.403 um map f(p) = A (p + u(p)) + c (prereg_na.md).
u: smooth field (9 um vox) fitted to the 40 old correspondences; RBF (scipy RBFInterpolator,
coords /1000, degree 1) or the quadratic M3 polynomial."""
import json, os
import numpy as np
from scipy.interpolate import RBFInterpolator

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
S = 1000.0


def load_points():
    aff = json.load(open(f"{REPO}/logs/sib/reg0841/affine_final.json"))
    A = np.array(aff["A"]); c = np.array(aff["c"])
    P, Q, ids = [], [], []
    for f in ("fit_eval_result.json", "heldout_result.json"):
        for r in json.load(open(f"{REPO}/logs/sib/reg0841/{f}"))["rows"]:
            P.append(r["p"]); Q.append(r["q_meas"]); ids.append(r["id"])
    P = np.array(P); Q = np.array(Q)
    U = np.linalg.solve(A, (Q - c - P @ A.T).T).T  # = d_i
    return A, c, P, U, ids


def quad_feats(X):
    x, y, z = (X / S).T
    return np.c_[x, y, z, np.ones(len(X)), x * x, x * y, y * y]


class Field:
    def __init__(self, P, U, kind, smoothing=0.0):
        self.kind = kind; self.smoothing = smoothing
        if kind == "Q":
            self.co = np.linalg.lstsq(quad_feats(P), U, rcond=None)[0]
        else:
            self.rbf = RBFInterpolator(P / S, U, kernel=kind, degree=1, smoothing=smoothing)

    def __call__(self, X):
        X = np.atleast_2d(np.asarray(X, float))
        return quad_feats(X) @ self.co if self.kind == "Q" else self.rbf(X / S)


class Map:
    def __init__(self, A, c, u):
        self.A = A; self.c = c; self.u = u; self.Ai = np.linalg.inv(A)

    def f(self, P):
        P = np.atleast_2d(P); return (P + self.u(P)) @ self.A.T + self.c

    def finv(self, Q, it=50, tol=1e-6):
        Q = np.atleast_2d(Q); p0 = (Q - self.c) @ self.Ai.T; p = p0.copy()
        for k in range(it):
            pn = p0 - self.u(p)
            step = np.abs(pn - p).max(); p = pn
            if step < tol:
                break
        return p, k + 1, float(step)

    def local_affine(self, pc, h=50.0):
        pc = np.asarray(pc, float); J = np.zeros((3, 3))
        for k in range(3):
            e = np.zeros(3); e[k] = h
            J[:, k] = (self.f(pc + e)[0] - self.f(pc - e)[0]) / (2 * h)
        return J, self.f(pc)[0] - J @ pc


def load_final():
    d = json.load(open(f"{REPO}/logs/sib/reg0841na/field_final.json"))
    A, c, P, U, ids = load_points()
    return Map(A, c, Field(P, U, d["kind"], d["smoothing"])), d
