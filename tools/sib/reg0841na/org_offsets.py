# Provenance: Project HERCULES | owner the owner | [id removed]
"""Offset between the organizer mapping and our CT map at canvas points (mesh geometry + frozen field only;
no CT read, no ink map, no image). ASK.md defaults 1-3.
Canvas px c <-> grid g = (c + 0.5)/20 (d3_feas_count_A convention); organizer correspondence
c2 = (c9 + 10) N2/N9 - 10 (B0841-BANK), N = grid * 20. D = f^-1(q2_org) - p9 (9 um vox), split along the
9 um mesh normal. Point sets: (a) geometric superset of fold-A tiles: 128 px tiles, stride 64, >= 90 %
mesh-valid px, every tile grid node >= 110 vox (= 144 - 20 sqrt2 - 4: node-to-pixel <= one cell diagonal, J sampling <= 3.6) from the J points of jexcl.py, so the set contains
every tile whose px are >= 144 vox from J); (b) the 18 dropped tiles (d3_stage1.json); (c) J-window centres; (d) the exact 288 fold-A tiles
(inputs/d3_pool_fa_origins.json from the work branch, source manifest sha256 8b127e10...)."""
import json, os, sys
import numpy as np, tifffile
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reg0841"))
from field import load_final
from jexcl import JExcl, SEGID
REPO = "/home/user/dominion"
MAP, FD = load_final()
mf = json.load(open(f"{REPO}/logs/sib/reg0841/mesh_fit.json"))["joint"]; A0 = np.array(mf["A"]); c0 = np.array(mf["c"])


def loadm(seg, frame):
    ts = seg.split("-")[0]
    d = f"/work/reg/mesh/{seg}/mesh/{ts}-on-{frame}.tifxyz"
    P = np.stack([tifffile.imread(f"{d}/{a}.tif").astype(np.float64) for a in "xyz"], -1)
    return P, ~np.all(P == -1, -1) & (P[..., 2] > 0)


def bil(P, V, g):
    r, c = g[:, 0], g[:, 1]; H, W = V.shape
    r0 = np.clip(np.floor(r).astype(int), 0, H - 2); c0_ = np.clip(np.floor(c).astype(int), 0, W - 2)
    fr = (r - r0)[:, None]; fc = (c - c0_)[:, None]
    ok = V[r0, c0_] & V[r0 + 1, c0_] & V[r0, c0_ + 1] & V[r0 + 1, c0_ + 1] & (r >= 0) & (c >= 0) & (r <= H - 1) & (c <= W - 1)
    X = P[r0, c0_] * (1 - fr) * (1 - fc) + P[r0 + 1, c0_] * fr * (1 - fc) + P[r0, c0_ + 1] * (1 - fr) * fc + P[r0 + 1, c0_ + 1] * fr * fc
    dr = (P[r0 + 1, c0_] - P[r0, c0_]) * (1 - fc) + (P[r0 + 1, c0_ + 1] - P[r0, c0_ + 1]) * fc
    dc = (P[r0, c0_ + 1] - P[r0, c0_]) * (1 - fr) + (P[r0 + 1, c0_ + 1] - P[r0 + 1, c0_]) * fr
    n = np.cross(dr, dc); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return X, n, ok


class Seg:
    def __init__(self, seg):
        self.P9, self.V9 = loadm(seg, "20250821151531-9.366um"); self.P2, self.V2 = loadm(seg, "20260319124803-2.403um")
        self.N9 = np.array(self.V9.shape) * 20; self.N2 = np.array(self.V2.shape) * 20

    def offsets(self, rc9):
        g9 = (rc9 + 0.5) / 20
        p9, n, ok9 = bil(self.P9, self.V9, g9)
        c2 = (rc9 + 10) * self.N2 / self.N9 - 10
        q2, _, ok2 = bil(self.P2, self.V2, (c2 + 0.5) / 20)
        ok = ok9 & ok2
        D = MAP.finv(q2)[0] - p9
        Da = MAP.finv(p9 @ A0.T + c0)[0] - p9
        dn = np.sum(D * n, 1); dt = np.linalg.norm(D - dn[:, None] * n, axis=1)
        dna = np.sum(Da * n, 1); dta = np.linalg.norm(Da - dna[:, None] * n, axis=1)
        return dict(ok=ok, D=D, dn=dn, dt=dt, Da=Da, dna=dna, dta=dta, p9=p9)


def stats(o, mask):
    D = o["D"][mask]; nD = np.linalg.norm(D, axis=1); nDa = np.linalg.norm(o["Da"][mask], axis=1)
    q = lambda v: dict(median=float(np.median(v)), p95=float(np.percentile(v, 95)), max=float(np.max(v)))
    return dict(n=int(mask.sum()), mesh_pair=dict(norm=q(nD), normal_abs=q(np.abs(o["dn"][mask])), tangential=q(o["dt"][mask]),
                                                 mean_vec=D.mean(0).tolist()),
                mesh_affine=dict(norm=q(nDa), normal_abs=q(np.abs(o["dna"][mask])), tangential=q(o["dta"][mask])))


J = JExcl(); jt = J.tree
bank = json.load(open(f"{REPO}/logs/bank0841/summary.json"))["J"]
dropped = json.load(open(f"{REPO}/logs/d1/d3_stage1.json"))["pools"]["fa"]["dropped"]
out = dict(field=dict(kind=FD["kind"], loo_rms9=FD["loo_rms9"], loo_max9=FD["loo_max9"]), segments={}, J={}, dropped=[])
allo = []; sup_sets = {}; o288 = []
ORIG = json.load(open(f"{REPO}/logs/sib/reg0841na/inputs/d3_pool_fa_origins.json"))["tiles"]
inv = {v: k for k, v in SEGID.items()}
for key, seg in SEGID.items():
    S = Seg(seg)
    H, W = S.N9
    # pixel validity (g = (c+0.5)/20 needs 4 valid nodes)
    Wv = S.V9[:-1, :-1] & S.V9[1:, :-1] & S.V9[:-1, 1:] & S.V9[1:, 1:]
    gr = np.floor((np.arange(H) + 0.5) / 20).astype(int); gc = np.floor((np.arange(W) + 0.5) / 20).astype(int)
    okr = gr < Wv.shape[0]; okc = gc < Wv.shape[1]
    vp = np.zeros((H, W), bool); vp[np.ix_(okr, okc)] = Wv[np.ix_(gr[okr], gc[okc])]
    ii = np.pad(vp.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    nd, _ = jt.query(S.P9.reshape(-1, 3), distance_upper_bound=200); nd = nd.reshape(S.V9.shape); nd[~S.V9] = np.inf
    tiles = []
    for y0 in range(0, H - 128 + 1, 64):
        for x0 in range(0, W - 128 + 1, 64):
            cnt = ii[y0 + 128, x0 + 128] - ii[y0, x0 + 128] - ii[y0 + 128, x0] + ii[y0, x0]
            if cnt * 10 < 9 * 16384:
                continue
            g0r, g1r = int((y0 + 0.5) / 20), int((y0 + 127.5) / 20) + 1; g0c, g1c = int((x0 + 0.5) / 20), int((x0 + 127.5) / 20) + 1
            if nd[g0r:g1r + 1, g0c:g1c + 1].min() < 110:
                continue
            tiles.append((y0 + 63.5, x0 + 63.5))
    tiles = np.array(tiles)
    sup_sets[key] = set((int(round(a - 63.5)), int(round(b - 63.5))) for a, b in tiles)
    o = S.offsets(tiles)
    out["segments"][key] = dict(n_tiles_superset=int(len(tiles)), **stats(o, o["ok"]))
    allo.append(o)
    for j, w in bank.items():
        if w["segment"] == key:
            oj = S.offsets(np.array([[w["y0"] + 1067.5, w["x0"] + 1067.5]]))
            out["J"][j] = dict(segment=key, ok=bool(oj["ok"][0]), p9=oj["p9"][0].tolist(), D_mesh_pair=oj["D"][0].tolist(),
                               norm=float(np.linalg.norm(oj["D"][0])), normal=float(oj["dn"][0]), tangential=float(oj["dt"][0]),
                               D_mesh_affine=oj["Da"][0].tolist(), norm_mesh_affine=float(np.linalg.norm(oj["Da"][0])),
                               u_field=MAP.u(oj["p9"])[0].tolist())
    for t in dropped:
        if SEGID[t["segment"].split("-", 1)[1].split("_")[0] if False else [k for k, v in SEGID.items() if v == t["segment"]][0]] == seg:
            od = S.offsets(np.array([[t["y0"] + 63.5, t["x0"] + 63.5]]))
            out["dropped"].append(dict(segment=key, y0=t["y0"], x0=t["x0"], ok=bool(od["ok"][0]), norm=float(np.linalg.norm(od["D"][0])),
                                       normal=float(od["dn"][0]), tangential=float(od["dt"][0])))
    t288 = [t for t in ORIG if inv[t["segment"]] == key]
    if t288:
        ot = S.offsets(np.array([[t["y0"] + 63.5, t["x0"] + 63.5] for t in t288], float))
        ot["in_superset"] = np.array([(t["y0"], t["x0"]) in sup_sets[key] for t in t288])
        o288.append(ot)
        out.setdefault("fa288_per_segment", {})[key] = dict(n_tiles=len(t288), **stats(ot, ot["ok"]))
o = {k: np.concatenate([a[k] for a in allo]) for k in allo[0]}
t = {k: np.concatenate([a[k] for a in o288]) for k in o288[0]}
out["fa288"] = dict(n_tiles=int(len(t["ok"])), n_in_superset=int(t["in_superset"].sum()), **stats(t, t["ok"]))
dd = np.array([d["norm"] for d in out["dropped"] if d["ok"]]); dnn = np.array([abs(d["normal"]) for d in out["dropped"] if d["ok"]])
out["dropped_summary"] = dict(n=int(len(dd)), norm_median=float(np.median(dd)), norm_max=float(dd.max()), normal_abs_max=float(dnn.max()))
print("FA288", json.dumps(out["fa288"]))
out["all_superset"] = stats(o, o["ok"])
out["note"] = "Superset of the 288 fold-A tiles (ASK 1). Field uncertainty ~ LOO RMS at patch sites; the J neighbourhood has no patch within 160 vox (interpolated)."
json.dump(out, open(f"{REPO}/logs/sib/reg0841na/org_offsets.json", "w"), indent=1)
print(json.dumps(out["all_superset"], indent=1)); print({k: v["n_tiles_superset"] for k, v in out["segments"].items()})
for j, v in out["J"].items(): print(j, v["ok"], round(v["norm"], 2), round(v["normal"], 2), round(v["tangential"], 2), round(v["norm_mesh_affine"], 2))
print("dropped max", max(d["norm"] for d in out["dropped"]), len(out["dropped"]))
