# Provenance: Project HERCULES | owner the owner | [id removed]
"""Re-check of the pairs0139 exclusions under RULES.md CORR-RETRACE-RULE (2026-09-25T19:01:33Z). Numbers only.

1. Same-papyrus (Rule N, corrected, fail-closed): meshes densified 5 x 5 (hercules.geometry.tifxyz.densify). A segment
   is SAME as a window (w024, w047, w053, title) if EITHER form gives >= 1000 points within 2 vox AND
   count[0,1) >= 2 x count[2,3):
     vertex  = nearest densified vertex (hercules.geometry.contamination.same_papyrus, the literal rule);
     surface = point-to-triangulated-surface distance of the densified grid (reference implementation copied below).
   Evaluated with window points as A (the rule's direction) and, additionally, with the segment's points as A
   (reverse); a segment is excluded if any form in any direction says SAME, or if the earlier rule (exclusion.json,
   >= 1000 1-vox canvas samples within 2 vox, no ratio) excluded it. All numbers are recorded.
2. Rule S (distance exclusion) as point-to-surface distance: canvas pixels (1-vox renderer samples) of every kept
   segment whose distance to the triangulated 5 x 5-densified surface of a window is <= 11 vox. The union with the
   earlier sample-based masks (nearE/) is written to nearE2/.
Output /work/p139/exclusion_v2.json, /work/p139/nearE2/<segment>.npz."""
import json, math, os, sys, time
import numpy as np
from scipy.spatial import cKDTree
from hercules.geometry.tifxyz import read_tifxyz, valid_mask, densify
from hercules.geometry.contamination import cloud, same_papyrus

S = "/work/p139/s3/PHerc0139/segments"
WINDOWS = ["w024", "w047", "w053", "title"]
K5, MIN2, RATIO, D_S = 5, 1000, 2.0, 11.0


# ---- reference implementation, copied verbatim from branch claude/gifted-bell-gavnl5-sib-tribunal
# ---- (commit 95de3ba320a4718cedaea47085b39dbc52329713, src/hercules/tribunal/preread.py, lines 397-489)
def _closest_on_triangles(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Distance from points p (N, 3) to triangles (a, b, c) (N, 3) each (Ericson 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = np.einsum("ij,ij->i", ab, ap)
    d2 = np.einsum("ij,ij->i", ac, ap)
    bp = p - b
    d3 = np.einsum("ij,ij->i", ab, bp)
    d4 = np.einsum("ij,ij->i", ac, bp)
    cp = p - c
    d5 = np.einsum("ij,ij->i", ab, cp)
    d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    res = np.empty_like(p)
    done = np.zeros(len(p), dtype=bool)

    def put(mask, val):
        m = mask & ~done
        res[m] = val[m]
        done[m] = True

    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), c)
        w = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        den = 1.0 / (va + vb + vc)
        vv, ww = vb * den, vc * den
        inner = a + ab * vv[:, None] + ac * ww[:, None]
    put(np.ones(len(p), dtype=bool), inner)
    return np.linalg.norm(p - res, axis=1)


def surface_distances(A_dense: np.ndarray, B_dense_grid: np.ndarray, max_dist: float = 3.0, k_nn: int = 4,
                      workers: int = 1) -> np.ndarray:
    """Distance from each valid point of A (N, 3 or grid) to the triangulated surface of
    the densified grid B; inf beyond ``max_dist`` (plus a circumradius bound)."""
    a = cloud(A_dense)
    g = np.asarray(B_dense_grid, dtype=np.float64)
    vb = valid_mask(g)
    Hb, Wb = vb.shape
    idx_grid = np.full((Hb, Wb), -1, dtype=np.int64)
    idx_grid[vb] = np.arange(int(vb.sum()))
    bpts = g[vb]
    rc, cc = np.nonzero(vb)
    out = np.full(len(a), np.inf)
    if len(bpts) == 0 or len(a) == 0:
        return out
    # circumradius bound: any surface point is within half the longest quad diagonal of a vertex
    du = np.linalg.norm(g[:, 1:] - g[:, :-1], axis=-1)[vb[:, 1:] & vb[:, :-1]]
    dv = np.linalg.norm(g[1:] - g[:-1], axis=-1)[vb[1:] & vb[:-1]]
    hmax = float(max(du.max() if du.size else 0.0, dv.max() if dv.size else 0.0))
    reach = max_dist + hmax * math.sqrt(2.0) / 2.0 + 1e-6
    tree = cKDTree(bpts)
    d, nn = tree.query(a, k=k_nn, distance_upper_bound=reach, workers=workers)
    d = np.atleast_2d(d.reshape(len(a), -1))
    nn = np.atleast_2d(nn.reshape(len(a), -1))
    cand = np.isfinite(d[:, 0])
    qi = np.flatnonzero(cand)
    if qi.size == 0:
        return out
    best = np.full(qi.size, np.inf)
    for kk in range(nn.shape[1]):
        vid = nn[qi, kk]
        okv = vid < len(bpts)
        r0 = np.where(okv, rc[np.minimum(vid, len(rc) - 1)], 0)
        c0 = np.where(okv, cc[np.minimum(vid, len(cc) - 1)], 0)
        for dr in (-1, 0):
            for dc in (-1, 0):
                r, c = r0 + dr, c0 + dc
                inq = okv & (r >= 0) & (c >= 0) & (r + 1 < Hb) & (c + 1 < Wb)
                rr, cc2 = np.where(inq, r, 0), np.where(inq, c, 0)
                qv = inq & vb[rr, cc2] & vb[rr + 1, cc2] & vb[rr, cc2 + 1] & vb[rr + 1, cc2 + 1]
                if not qv.any():
                    continue
                sel = np.flatnonzero(qv)
                p = a[qi[sel]]
                p00, p01 = g[rr[sel], cc2[sel]], g[rr[sel], cc2[sel] + 1]
                p10, p11 = g[rr[sel] + 1, cc2[sel]], g[rr[sel] + 1, cc2[sel] + 1]
                for tri in ((p00, p01, p10), (p11, p10, p01)):
                    dd = _closest_on_triangles(p, *tri)
                    best[sel] = np.minimum(best[sel], dd)
    out[qi] = best
    out[out > max_dist] = np.inf
    return out
# ---- end of copied reference code


def surf_rule(A, Bgrid):
    d = surface_distances(A, Bgrid, 3.0, workers=3)
    c0 = int(np.sum(d < 1.0)); c1 = int(np.sum((d >= 1.0) & (d < 2.0))); c2 = int(np.sum((d >= 2.0) & (d < 3.0)))
    return dict(counts=[c0, c1, c2], n_within_2=c0 + c1, same=bool(c0 + c1 >= MIN2 and c0 >= RATIO * c2))


def vert_rule(A, B):
    r = same_papyrus(A, B, workers=3)
    return dict(counts=list(r.counts), n_within_2=int(r.n_within_2), same=bool(r.same))


def short(sid):
    return sid.split("-")[1].split("_")[0]


def mesh9(sid):
    ts = sid.split("-")[0]
    return read_tifxyz(f"{S}/{sid}/mesh/{ts}-on-20250728140407-9.362um.tifxyz")


def canvas_pixels_near(m, tree, reach):
    """canvas pixels (row, col) and xyz of the quads of m whose centre lies within reach of a tree point."""
    p = m.points.astype(np.float64); vm = valid_mask(m.points)
    qv = vm[:-1, :-1] & vm[:-1, 1:] & vm[1:, :-1] & vm[1:, 1:]
    qr, qc = np.nonzero(qv)
    cen = 0.25 * (p[qr, qc] + p[qr, qc + 1] + p[qr + 1, qc] + p[qr + 1, qc + 1])
    hd = 0.5 * np.maximum(np.linalg.norm(p[qr + 1, qc + 1] - p[qr, qc], axis=1), np.linalg.norm(p[qr + 1, qc] - p[qr, qc + 1], axis=1))
    d, _ = tree.query(cen, distance_upper_bound=reach + hd.max() + 1e-6)
    sel = np.flatnonzero(d <= reach + hd + 1e-6)
    K = 20
    f = (np.arange(K) + 0.5) / K
    t, u = np.meshgrid(f, f, indexing="ij"); t = t.ravel()[None, :, None]; u = u.ravel()[None, :, None]
    jj, ii = np.meshgrid(np.arange(K), np.arange(K), indexing="ij")
    pts, rc = [], []
    for s0 in range(0, sel.size, 5000):
        s_ = sel[s0:s0 + 5000]; r = qr[s_][:, None]; c = qc[s_][:, None]
        val = (1 - t) * ((1 - u) * p[r, c] + u * p[r, c + 1]) + t * ((1 - u) * p[r + 1, c] + u * p[r + 1, c + 1])
        pts.append(val.reshape(-1, 3))
        rc.append(np.stack([(r * K + jj.ravel()[None]).ravel(), (c * K + ii.ravel()[None]).ravel()], 1))
    if not pts:
        return np.zeros((0, 3)), np.zeros((0, 2), int)
    return np.concatenate(pts), np.concatenate(rc)


def main():
    t0 = time.time()
    old = json.load(open("/work/p139/exclusion.json"))
    kt = json.load(open("data/catalogue/known_text.json"))["scrolls"]["PHerc0139"]["segments"]["list"]
    all_s = [g["long_id"] for g in kt if "20250728140407" in g["meshes_on"]]
    by = {short(s): s for s in all_s}
    W = {w: densify(mesh9(by[w]).points, K5) for w in WINDOWS}
    Wtree = {w: cKDTree(cloud(W[w])) for w in WINDOWS}
    rows = {}
    cache = "/work/p139/retrace_v2.jsonl"
    done = {}
    if os.path.exists(cache):
        for l in open(cache):
            d = json.loads(l); done[d["segment"]] = d["row"]
    for s in all_s:
        if short(s) in WINDOWS:
            continue
        if s in done:
            rows[s] = done[s]; continue
        B = densify(mesh9(s).points, K5)
        Bc = cloud(B)
        r = {}
        for w in WINDOWS:
            # quick reject: no B point within 3 vox + window circumradius of any window vertex
            dmin, _ = Wtree[w].query(Bc, distance_upper_bound=60.0)
            if not np.isfinite(dmin).any():
                r[w] = dict(far=True); continue
            r[w] = dict(win_as_A=dict(vertex=vert_rule(W[w], B), surface=surf_rule(W[w], B)),
                        seg_as_A=dict(vertex=vert_rule(B, W[w]), surface=surf_rule(B, W[w])),
                        min_vertex_dist_vox=float(dmin.min()))
            r[w]["same"] = bool(any(r[w][dirn][form]["same"] for dirn in ("win_as_A", "seg_as_A") for form in ("vertex", "surface")))
        rows[s] = dict(short=short(s), per_window=r, same_corrected=bool(any(v.get("same") for v in r.values())),
                       excluded_old=bool(short(s) in old["E"]))
        with open(cache, "a") as f:
            f.write(json.dumps(dict(segment=s, row=rows[s])) + "\n")
        print(short(s), rows[s]["same_corrected"], {w: (v.get("win_as_A", {}).get("surface", {}).get("counts"), v.get("same")) for w, v in r.items()},
              f"{time.time()-t0:.0f}s", flush=True)
    new_found = sorted(short(s) for s, r in rows.items() if r["same_corrected"])
    E = sorted(set(old["E"]) | set(new_found))
    # Rule S as point-to-surface distance to the windows' triangulated 5x5-densified surfaces
    os.makedirs("/work/p139/nearE2", exist_ok=True)
    for s, r in rows.items():
        r["excluded"] = short(s) in E
        if r["excluded"]:
            continue
        m = mesh9(s)
        H, Wd = m.points.shape[:2]
        mask = np.zeros((H * 20, Wd * 20), bool)
        n_surf = 0
        for w in WINDOWS:
            g = W[w]
            vb = valid_mask(g)
            du = np.linalg.norm(g[:, 1:] - g[:, :-1], axis=-1)[vb[:, 1:] & vb[:, :-1]]
            dv = np.linalg.norm(g[1:] - g[:-1], axis=-1)[vb[1:] & vb[:-1]]
            hmax = float(max(du.max(), dv.max()))
            P, RC = canvas_pixels_near(m, Wtree[w], D_S + hmax * math.sqrt(2) / 2)
            if len(P) == 0:
                continue
            d = surface_distances(P, g, D_S, workers=3)
            hit = np.isfinite(d)
            n_surf += int(hit.sum())
            mask[RC[hit, 0], RC[hit, 1]] = True
        n_new = int(mask.sum())
        oldp = f"/work/p139/nearE/{s}.npz"
        if os.path.exists(oldp):
            z = np.load(oldp); sh = tuple(z["shape"])
            om = np.unpackbits(z["packed"])[:sh[0] * sh[1]].reshape(sh).astype(bool)
            assert sh == mask.shape
            r["rule_s_old_px"] = int(om.sum()); r["rule_s_old_not_in_surface_px"] = int((om & ~mask).sum())
            mask |= om
        r["rule_s_surface_px"] = n_new; r["rule_s_union_px"] = int(mask.sum())
        if mask.any():
            np.savez_compressed(f"/work/p139/nearE2/{s}.npz", packed=np.packbits(mask), shape=np.array(mask.shape))
        print("S", short(s), n_new, r["rule_s_union_px"], f"{time.time()-t0:.0f}s", flush=True)
    out = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
               rule="RULES.md CORR-RETRACE-RULE (fail-closed): SAME if vertex OR surface form (5 x 5 densification) gives "
                    ">= 1000 points within 2 vox and count[0,1) >= 2 count[2,3), either direction; union with the "
                    "earlier rule (exclusion.json); Rule S = point-to-surface distance <= 11 vox to the controls and "
                    "title, union with the earlier sample-based masks",
               reference_code="claude/gifted-bell-gavnl5-sib-tribunal 95de3ba3 src/hercules/tribunal/preread.py (copied)",
               E_old=old["E"], found_corrected=new_found, E=E,
               added_by_correction=sorted(set(E) - set(old["E"])),
               old_only=sorted(set(old["E"]) - set(new_found) - set(WINDOWS) - {"w025", "w048", "w052"}),
               segments=rows, seconds=round(time.time() - t0, 1))
    json.dump(out, open("/work/p139/exclusion_v2.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "segments"}, indent=1))


if __name__ == "__main__":
    main()
