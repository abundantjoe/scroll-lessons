# Provenance: Project HERCULES | owner the owner | [id removed]
"""J-window exclusion in the 9.366 um frame (D1 benchmark windows J1-J5).

J corners: logs/bank0841/summary.json "J" (segment, y0, x0; window 2136 x 2136 canvas px),
identical to logs/d1/d3_feas_count_A.json J_windows rows/cols (checked at run time).
Canvas px c <-> tifxyz grid g = (c + 0.5)/20 (d3_feas_count_A method). J points: the 9 um
organizer mesh (<id>-on-20250821151531-9.366um) bilinearly sampled every 0.25 grid node
(<= 5 vox spacing) over the window grown by 1 grid node (20 px) on each side, own segment only.
A box is admissible iff its Euclidean 3-D distance to every J point is >= 144 + MARGIN vox;
MARGIN = 12 vox covers the sampling gap (<= 3.6 vox), resample support and blur."""
import json, os
import numpy as np, tifffile
from scipy.spatial import cKDTree

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
MESH = "/work/reg/mesh"
SEGID = {"w00": "20260220213127-w00", "214732": "20260220214732-auto_grown_20260220144552896",
         "022814": "20260221022814-auto_grown_20260220174252405"}
LIMIT = 144.0
MARGIN = 12.0
WIN = 2136


def load9(seg):
    ts = seg.split("-")[0]
    d = f"{MESH}/{seg}/mesh/{ts}-on-20250821151531-9.366um.tifxyz"
    return np.stack([tifffile.imread(f"{d}/{a}.tif").astype(np.float64) for a in "xyz"], -1)


def j_points(step=0.25):
    bank = json.load(open(f"{REPO}/logs/bank0841/summary.json"))["J"]
    feas = json.load(open(f"{REPO}/logs/d1/d3_feas_count_A.json"))["J_windows"]
    pts, info = [], {}
    for j, w in bank.items():
        seg = SEGID[w["segment"]]
        assert feas[j]["segment"] == seg and feas[j]["rows"] == [w["y0"], w["y0"] + WIN] \
            and feas[j]["cols"] == [w["x0"], w["x0"] + WIN], j
        P = load9(seg); V = ~np.all(P == -1, -1) & (P[..., 2] > 0)
        H, W = V.shape
        g0r = (w["y0"] - 20 + 0.5) / 20; g1r = (w["y0"] + WIN + 20 + 0.5) / 20
        g0c = (w["x0"] - 20 + 0.5) / 20; g1c = (w["x0"] + WIN + 20 + 0.5) / 20
        rr = np.arange(np.floor(g0r), np.ceil(g1r) + 1e-9, step)
        cc = np.arange(np.floor(g0c), np.ceil(g1c) + 1e-9, step)
        R, C = np.meshgrid(rr, cc, indexing="ij"); R = R.ravel(); C = C.ravel()
        # nearest-node validity: any valid neighbour node -> keep (conservative: includes rims)
        r0 = np.clip(np.floor(R).astype(int), 0, H - 2); c0 = np.clip(np.floor(C).astype(int), 0, W - 2)
        fr = np.clip(R - r0, 0, 1)[:, None]; fc = np.clip(C - c0, 0, 1)[:, None]
        n = [(r0, c0), (r0 + 1, c0), (r0, c0 + 1), (r0 + 1, c0 + 1)]
        wts = [(1 - fr) * (1 - fc), fr * (1 - fc), (1 - fr) * fc, fr * fc]
        allv = V[n[0]] & V[n[1]] & V[n[2]] & V[n[3]]
        X = sum(P[a] * b for a, b in zip(n, wts))
        # partial cells: add each valid corner node itself
        anyv = np.zeros(len(R), bool)
        extra = [P[a][V[a] & ~allv] for a in n]
        p = np.concatenate([X[allv]] + extra)
        info[j] = dict(segment=seg, n_points=int(len(p)), valid_nodes=int(V[int(g0r):int(g1r) + 1, int(g0c):int(g1c) + 1].sum()),
                       bbox_min=p.min(0).tolist(), bbox_max=p.max(0).tolist())
        pts.append(p)
    return np.unique(np.concatenate(pts).round(3), axis=0), info


class JExcl:
    def __init__(self):
        self.p, self.info = j_points()
        self.tree = cKDTree(self.p)

    def box_dist(self, lo, hi):
        """Min Euclidean distance from J points to axis-aligned box [lo, hi] (x, y, z vox)."""
        lo = np.asarray(lo, float); hi = np.asarray(hi, float)
        c = (lo + hi) / 2; h = (hi - lo) / 2
        R = np.linalg.norm(h) + LIMIT + MARGIN + 50
        idx = self.tree.query_ball_point(c, R)
        if not idx:
            return float("inf")
        q = self.p[idx]
        d = np.linalg.norm(np.maximum(np.abs(q - c) - h, 0), axis=1)
        return float(d.min())

    def ok(self, lo, hi):
        return self.box_dist(lo, hi) >= LIMIT + MARGIN


if __name__ == "__main__":
    J = JExcl()
    print(json.dumps({"n_points": int(len(J.p)), "windows": J.info}, indent=1))
