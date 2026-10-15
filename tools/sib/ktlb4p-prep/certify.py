# Provenance: Project HERCULES | owner the owner | [id removed]
"""Same-papyrus certification of the candidate windows (CORR-RETRACE-RULE) and papyrus units.

Points: every valid 9 um canvas position on a 4-px lattice of each segment (bilinear over the
20-vox grid; about 4-vox spacing, like the rule's 5 x 5 densification).
For every segment pair (a, b) with overlapping 3-D bounding boxes (+3 vox): the points of a are
queried against b's 5 x 5-densified mesh (4-vox vertex spacing):
  (a) literal form: distance to the nearest densified vertex;
  (b) point-to-surface form: |n . (x - v)| at the nearest vertex v (n = b's unit normal there),
      used when the in-plane offset is <= 2 * sqrt(2) vox (inside the 4-vox cell), else (a).
A window Wa (segment a) and a window Wb (segment b) are SAME papyrus if, in EITHER form, the
points of Wa (the already chosen window) whose nearest b point lies inside Wb (the candidate) give >= 1000 points within 2 vox and
count[0,1) >= 2 x count[2,3). Windows of the same segment are SAME if their canvases overlap.
Units: segments are grouped into re-trace clusters when >= 20 % of the smaller segment's
points lie within 2 vox (form b) of the other (reported with the full matrix).
Candidate windows must also pass the window frame gate (zero CT <= 5 %).
Independent set: greedy maximal set of pairwise non-SAME candidate windows, ordered by
(segment name, y0, x0) only; the reference value is never used to order or select.
Usage: certify.py WINDOWS_JSON OUT_JSON
"""
import json, os, sys, time
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree

REPO = "/home/user/dominion"
sys.path.insert(0, f"{REPO}/src")
from hercules.geometry.tifxyz import read_tifxyz, valid_mask, sample_grid, densify, vertex_normals  # noqa: E402

S3 = "/work/handed/s3/PHerc0500P2/segments"
LAT = 4
DENS = 5


def seg_points(seg):
    d9 = [d for d in os.listdir(f"{S3}/{seg}/mesh") if d.endswith("9.362um.tifxyz")][0]
    m = read_tifxyz(f"{S3}/{seg}/mesh/{d9}")
    s = m.scale[0]
    H, W = int(round(m.points.shape[0] / s)), int(round(m.points.shape[1] / s))
    cy, cx = np.mgrid[LAT // 2:H:LAT, LAT // 2:W:LAT]
    P = sample_grid(m.points.astype(np.float64), (cy + 0.5) * s, (cx + 0.5) * s)
    ok = valid_mask(P)
    dp = densify(m.points.astype(np.float64), DENS).astype(np.float64)
    dn = vertex_normals(dp)
    dv = valid_mask(dp) & np.isfinite(dn).all(-1)
    iy, ix = np.nonzero(dv)
    return dict(P=P[ok], cy=cy[ok], cx=cx[ok], V=dp[dv], N=dn[dv], vy=(iy / (s * DENS) - 0.5), vx=(ix / (s * DENS) - 0.5),
                lo=P[ok].min(0), hi=P[ok].max(0), n=int(ok.sum()), HW=(H, W))


def main():
    wj = json.load(open(sys.argv[1]))
    wins = [w for w in wj["windows"] if w["zero_ct_frac"] <= 0.05]
    segs = sorted({w["segment"] for w in wj["windows"]} | {s for s, v in wj["segments"].items() if "canvas_hw" in v})
    t0 = time.time()
    SP = {s: seg_points(s) for s in segs}
    print("points", {s[:14]: SP[s]["n"] for s in segs}, round(time.time() - t0, 1), flush=True)
    hits = {}  # (a, b) -> dict of arrays for points of a within 3 vox of b
    frac = {}
    for a in segs:
        for b in segs:
            if a == b:
                continue
            A_, B_ = SP[a], SP[b]
            if np.any(A_["lo"] > B_["hi"] + 3) or np.any(B_["lo"] > A_["hi"] + 3):
                continue
            tree = cKDTree(B_["V"])
            dnn, idx = tree.query(A_["P"], distance_upper_bound=6.0)
            m = np.isfinite(dnn)
            if not m.any():
                continue
            ii = idx[m]
            dvec = A_["P"][m] - B_["V"][ii]
            dperp = np.abs(np.einsum("ij,ij->i", dvec, B_["N"][ii]))
            inpl = np.sqrt(np.maximum(dnn[m] ** 2 - dperp ** 2, 0))
            dsurf = np.where(inpl <= 2 * np.sqrt(2), dperp, dnn[m])
            keep = (dsurf < 3) | (dnn[m] < 3)
            sel = np.nonzero(m)[0][keep]
            hits[(a, b)] = dict(i=sel, dnn=dnn[m][keep], dsurf=dsurf[keep], by=B_["vy"][ii[keep]], bx=B_["vx"][ii[keep]])
            frac[(a, b)] = float((dsurf < 2).sum() / A_["n"])
    print("pairs with hits", len(hits), round(time.time() - t0, 1), flush=True)
    # segment re-trace clusters
    parent = {s: s for s in segs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for (a, b), f in frac.items():
        small = min(SP[a]["n"], SP[b]["n"])
        if (f * SP[a]["n"]) / small >= 0.2:
            parent[find(a)] = find(b)
    clusters = defaultdict(list)
    for s in segs:
        clusters[find(s)].append(s)
    unit_of = {s: min(v) for v in clusters.values() for s in v}

    # window SAME tests (direction: chosen window's points -> candidate's segment surface)
    def overlap(wa, wb):
        return not (wa["y0"] + wa["h"] <= wb["y0"] or wb["y0"] + wb["h"] <= wa["y0"] or
                    wa["x0"] + wa["w"] <= wb["x0"] or wb["x0"] + wb["w"] <= wa["x0"])

    def subset(wc):
        c = wc["segment"]; A_ = SP[c]; outd = {}
        for (a, b), h in hits.items():
            if a != c:
                continue
            cy, cx = A_["cy"][h["i"]], A_["cx"][h["i"]]
            m = (cy >= wc["y0"]) & (cy < wc["y0"] + wc["h"]) & (cx >= wc["x0"]) & (cx < wc["x0"] + wc["w"])
            outd[b] = dict(by=h["by"][m], bx=h["bx"][m], dnn=h["dnn"][m], dsurf=h["dsurf"][m])
        return outd

    def same_to(sub, wb):
        h = sub.get(wb["segment"])
        if h is None:
            return False
        sel = (h["by"] >= wb["y0"]) & (h["by"] < wb["y0"] + wb["h"]) & (h["bx"] >= wb["x0"]) & (h["bx"] < wb["x0"] + wb["w"])
        for d in (h["dnn"][sel], h["dsurf"][sel]):
            c0, c1, c2 = (d < 1).sum(), ((d >= 1) & (d < 2)).sum(), ((d >= 2) & (d < 3)).sum()
            if c0 + c1 >= 1000 and c0 >= 2 * c2:
                return True
        return False

    order = sorted(range(len(wins)), key=lambda i: (wins[i]["segment"], wins[i]["y0"], wins[i]["x0"]))
    chosen, subs = [], []
    for i in order:
        w = wins[i]
        if any((wins[j]["segment"] == w["segment"] and overlap(wins[j], w)) or same_to(subs[k], w) for k, j in enumerate(chosen)):
            continue
        chosen.append(i); subs.append(subset(w))
    indep = [dict(wins[i], unit=unit_of[wins[i]["segment"]]) for i in chosen]
    out = dict(rule=__doc__, n_candidates=len(wj["windows"]), n_after_frame_gate=len(wins),
               units={k: v for k, v in clusters.items()}, segment_overlap_frac={f"{a}|{b}": f for (a, b), f in frac.items()},
               independent_windows=indep, n_independent=len(indep),
               n_independent_text=int(sum(not w["blank_candidate"] for w in indep)),
               n_independent_blank=int(sum(w["blank_candidate"] for w in indep)),
               n_units=len(clusters), seconds=round(time.time() - t0, 1))
    json.dump(out, open(sys.argv[2], "w"), indent=1, default=float)
    print({k: v for k, v in out.items() if k in ("n_candidates", "n_after_frame_gate", "n_independent", "n_independent_text",
                                                 "n_independent_blank", "n_units", "seconds")})


if __name__ == "__main__":
    main()
