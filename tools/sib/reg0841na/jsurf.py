# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fail-closed J clearance (CORR-RETRACE-RULE): min(point-to-triangulated-surface lower bound,
densified-vertex distance) from an axis-aligned box to the J-window surfaces of the 9 um organizer
meshes. Same construction as tools/sib/reg0841/jexcl_surface.py, as a reusable class; also
point distances (for canvas tiles)."""
import json, os, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reg0841"))
from jexcl import JExcl, load9, SEGID, WIN, LIMIT

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
NSUB = 24


class JSurf:
    def __init__(self):
        bank = json.load(open(f"{REPO}/logs/bank0841/summary.json"))["J"]
        tris = []
        for j, w in bank.items():
            P = load9(SEGID[w["segment"]]); V = ~np.all(P == -1, -1) & (P[..., 2] > 0)
            r0 = max(int(np.floor((w["y0"] - 20 + 0.5) / 20)), 0); r1 = min(int(np.ceil((w["y0"] + WIN + 20 + 0.5) / 20)), V.shape[0] - 1)
            c0 = max(int(np.floor((w["x0"] - 20 + 0.5) / 20)), 0); c1 = min(int(np.ceil((w["x0"] + WIN + 20 + 0.5) / 20)), V.shape[1] - 1)
            for r in range(r0, r1):
                for c in range(c0, c1):
                    a, b, cc, d = (r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)
                    for t in ((a, b, cc), (b, d, cc)):
                        if all(V[k] for k in t):
                            tris.append([P[k] for k in t])
        self.T = np.array(tris)
        self.cent = self.T.mean(1); self.rad = np.linalg.norm(self.T - self.cent[:, None], axis=2).max(1)
        self.emax = float(max(np.linalg.norm(self.T[:, i] - self.T[:, (i + 1) % 3], axis=1).max() for i in range(3)))
        self.gap = self.emax / NSUB
        u, v = np.meshgrid(np.arange(NSUB + 1), np.arange(NSUB + 1)); m = u + v <= NSUB
        self.bary = np.c_[u[m], v[m], NSUB - u[m] - v[m]] / NSUB
        self.tree = cKDTree(self.cent)
        self.vert = JExcl()

    def box_clearance(self, lo, hi, cap=500.0):
        lo = np.asarray(lo, float); hi = np.asarray(hi, float); cb = (lo + hi) / 2; hb = (hi - lo) / 2
        R = np.linalg.norm(hb) + cap + self.rad.max()
        idx = self.tree.query_ball_point(cb, R)
        ds = cap
        if idx:
            cd = np.linalg.norm(np.maximum(np.abs(self.cent[idx] - cb) - hb, 0), axis=1) - self.rad[idx]
            o = np.argsort(cd); idx = np.array(idx)[o]; cd = cd[o]
            for k0 in range(0, len(idx), 2000):
                if cd[k0] - self.gap >= ds:
                    break
                pts = np.einsum("sk,tkd->tsd", self.bary, self.T[idx[k0:k0 + 2000]]).reshape(-1, 3)
                ds = min(ds, float(np.linalg.norm(np.maximum(np.abs(pts - cb) - hb, 0), axis=1).min() - self.gap))
        return float(min(ds, self.vert.box_dist(lo, hi)))
