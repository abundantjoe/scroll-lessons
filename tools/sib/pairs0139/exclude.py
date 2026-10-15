# Provenance: Project HERCULES | owner the owner | [id removed]
"""Exclusions for the PHerc0139 D2 pairs (task pairs0139), enforced in code. Numbers only.

Exclusion set E: the clean controls w024, w047, w053 and the title segment (E0), the named 3-D neighbours w025, w048,
w052, and every segment found by Rule N.
Densified points = the renderer's canvas samples of the 9.362 um organizer mesh at --scale 1 (canvas pixel P samples
grid (P + 0.5) s, bilinear inside a quad whose 4 vertices are valid; 20 x 20 samples per quad, ~1 vox spacing).
Rule N (task text, exact): a segment with >= 1000 densified points within 2 vox (3-D, Euclidean) of any densified
point of E0 is a neighbour and is excluded whole. The count is reported for every segment.
Rule S (added): in kept segments every canvas pixel within 11 vox (exact) of a densified point of E0 (controls and
title) is excluded, so that no stored pair slab (21 slices = +-10 vox along the normal) samples control or title
papyrus. (A first version used all of E with a conservative 16 vox sphere bound; it flagged most of several segments
and was replaced before any pair was built.)
Search: sub-quads of 5 x 5 samples; centre c = mean of the 4 corner samples, radius h = max corner distance to c;
every sample of the sub-quad is a convex combination of the corners (bilinear), hence within h of c. A pair of
sub-quads can hold samples within D only if |c_a - c_b| <= D + h_a + h_b. Sub-quads with h > HC are replaced by
their 25 samples (h = 0), so the search radius is bounded by D + 2 HC.
Output: /work/p139/exclusion.json, /work/p139/nearE/<segment>.npz (packbits canvas mask of Rule-S pixels)."""
import json, os, time
import numpy as np
from scipy.spatial import cKDTree
from hercules.geometry.tifxyz import read_tifxyz, valid_mask

S = "/work/p139/s3/PHerc0139/segments"
CONTROLS = ["w024", "w047", "w053"]
TITLE = "title"
NAMED_NB = ["w025", "w048", "w052"]
D_N, N_MIN, D_S = 2.0, 1000, 11.0
K, KS = 20, 5            # samples per quad axis, samples per sub-quad axis
HC = 8.0                 # sub-quad radius cap (vox)
BLK = 20000              # a sub-quads per exact block


def segs():
    kt = json.load(open("data/catalogue/known_text.json"))["scrolls"]["PHerc0139"]["segments"]["list"]
    return [g["long_id"] for g in kt if "20250728140407" in g["meshes_on"]]


def short(sid):
    return sid.split("-")[1].split("_")[0]


class M:
    def __init__(self, sid):
        ts = sid.split("-")[0]
        m = read_tifxyz(f"{S}/{sid}/mesh/{ts}-on-20250728140407-9.362um.tifxyz")
        assert int(round(1 / float(np.float32(m.scale[0])))) == K
        self.sid = sid
        self.p = m.points.astype(np.float64)
        vm = valid_mask(m.points)
        H, W = vm.shape
        self.canvas = (H * K, W * K)
        qv = vm[:-1, :-1] & vm[:-1, 1:] & vm[1:, :-1] & vm[1:, 1:]
        qr, qc = np.nonzero(qv)
        n = K // KS
        # sub-quads: (quad, i, j), i, j in 0..n-1
        self.sq_r = np.repeat(qr, n * n); self.sq_c = np.repeat(qc, n * n)
        ij = np.tile(np.arange(n * n), qr.size)
        self.sq_i = ij // n; self.sq_j = ij % n
        C = self.corners(np.arange(self.sq_r.size))                      # (N, 4, 3)
        self.cent = C.mean(1)
        self.h = np.linalg.norm(C - self.cent[:, None], axis=-1).max(1)
        self.n_dense = int(qr.size) * K * K
        big = self.h > HC
        self.big = np.nonzero(big)[0]
        # search points: centres of normal sub-quads (radius <= HC) + all samples of big ones (radius 0)
        pts = [self.cent[~big]]; owner = [np.nonzero(~big)[0]]
        if self.big.size:
            P, _ = self.samples(self.big)
            pts.append(P.reshape(-1, 3)); owner.append(np.repeat(self.big, KS * KS))
        self.spts = np.concatenate(pts); self.sown = np.concatenate(owner)
        self.tree = cKDTree(self.spts)

    def _params(self, idx, jj, ii):
        base_j = (self.sq_i[idx] * KS)[:, None]; base_i = (self.sq_j[idx] * KS)[:, None]
        return base_j + jj[None, :], base_i + ii[None, :]

    def corners(self, idx):
        jj = np.array([0, 0, KS - 1, KS - 1]); ii = np.array([0, KS - 1, 0, KS - 1])
        return self.samples(idx, jj, ii)[0]

    def samples(self, idx, jj=None, ii=None):
        """canvas samples of sub-quads idx -> xyz (len, m, 3), canvas (row, col) (len, m, 2)."""
        if jj is None:
            jj, ii = np.meshgrid(np.arange(KS), np.arange(KS), indexing="ij"); jj = jj.ravel(); ii = ii.ravel()
        out = np.empty((idx.size, jj.size, 3)); rc = np.empty((idx.size, jj.size, 2), np.int64)
        for s0 in range(0, idx.size, 200000):
            sl = idx[s0:s0 + 200000]
            J, I = self._params(sl, jj, ii)                              # (b, m) pixel offsets in the quad
            r = self.sq_r[sl][:, None]; c = self.sq_c[sl][:, None]
            t = ((J + 0.5) / K)[..., None]; u = ((I + 0.5) / K)[..., None]
            p = self.p
            out[s0:s0 + sl.size] = (1 - t) * ((1 - u) * p[r, c] + u * p[r, c + 1]) + \
                t * ((1 - u) * p[r + 1, c] + u * p[r + 1, c + 1])
            rc[s0:s0 + sl.size, :, 0] = r * K + J; rc[s0:s0 + sl.size, :, 1] = c * K + I
        return out, rc


def near_pixels(a, others, D, exact):
    """canvas pixels (row, col) of a within D vox of a densified point of any mesh in others.
    exact=False returns the conservative sub-quad superset. Also returns the smallest exact distance seen (<= 60)."""
    hits = []; dmin = np.inf
    for b in others:
        # a query points: normal sub-quads by centre (radius h_a), big ones by samples (radius 0)
        abig = a.h > HC
        idx_n = np.nonzero(~abig)[0]
        d, _ = b.tree.query(a.cent[idx_n], distance_upper_bound=D + HC + HC + 1e-6)
        ok = d <= D + a.h[idx_n] + HC + 1e-6
        cand = idx_n[ok]
        if a.big.size:
            Pb, _ = a.samples(a.big)
            db, _ = b.tree.query(Pb.reshape(-1, 3), distance_upper_bound=D + HC + 1e-6)
            cand = np.union1d(cand, a.big[(db.reshape(a.big.size, -1) <= D + HC + 1e-6).any(1)])
        if cand.size == 0:
            continue
        if not exact:
            _, rc = a.samples(cand)
            hits.append(rc.reshape(-1, 2))
            continue
        for s0 in range(0, cand.size, BLK):
            blk = cand[s0:s0 + BLK]
            Pa, RCa = a.samples(blk)
            Pa = Pa.reshape(-1, 3); RCa = RCa.reshape(-1, 2)
            r = D + np.maximum(a.h[blk], 0) + HC + 1e-6
            near = b.tree.query_ball_point(a.cent[blk], r)
            jb = np.unique(b.sown[np.concatenate([np.asarray(l, int) for l in near])]) if len(near) else np.zeros(0, int)
            if jb.size == 0:
                continue
            Pb, _ = b.samples(jb)
            tb = cKDTree(Pb.reshape(-1, 3))
            dd, _ = tb.query(Pa, distance_upper_bound=60.0)
            dmin = min(dmin, float(dd.min()))
            h = dd <= D
            if h.any():
                hits.append(RCa[h])
    rc = np.unique(np.concatenate(hits), axis=0) if hits else np.zeros((0, 2), int)
    return rc, dmin


def main():
    t0 = time.time()
    all_s = segs()
    by = {short(s): s for s in all_s}
    E0 = [by[x] for x in CONTROLS + [TITLE]]
    mesh = {}
    rows = {}
    for s in E0:
        mesh[s] = M(s)
    print("E0 loaded", f"{time.time()-t0:.0f}s", {short(s): (mesh[s].spts.shape[0], int(mesh[s].big.size)) for s in E0},
          flush=True)
    cache = "/work/p139/exclusion_ruleN.jsonl"          # resume cache (one row per segment)
    done = {}
    if os.path.exists(cache):
        for l in open(cache):
            d = json.loads(l); done[d["segment"]] = d["row"]
    for s in all_s:
        if s in E0:
            continue
        if s in done:
            rows[s] = done[s]; print("N (cached)", short(s), rows[s]["n_dense_within_2vox_of_controls_title"], flush=True)
            continue
        ms = M(s)                                           # not kept: memory
        rc, dmin = near_pixels(ms, [mesh[e] for e in E0], D_N, exact=True)
        rows[s] = dict(short=short(s), n_dense=ms.n_dense, n_dense_within_2vox_of_controls_title=int(len(rc)),
                       min_dist_vox_to_controls_title=dmin if np.isfinite(dmin) else None,
                       neighbour_rule_N=bool(len(rc) >= N_MIN))
        del ms, rc
        with open(cache, "a") as f:
            f.write(json.dumps(dict(segment=s, row=rows[s])) + "\n")
        print("N", short(s), rows[s]["n_dense_within_2vox_of_controls_title"], dmin, f"{time.time()-t0:.0f}s", flush=True)
    found = [s for s, r in rows.items() if r["neighbour_rule_N"]]
    for x in NAMED_NB:
        rows[by[x]]["named_neighbour"] = True
    E = sorted(set(E0 + [by[x] for x in NAMED_NB] + found))
    os.makedirs("/work/p139/nearE", exist_ok=True)
    for s, r in rows.items():
        r["excluded"] = s in E
        if s in E:
            continue
        ms = M(s)
        rc, _ = near_pixels(ms, [mesh[e] for e in E0], D_S, exact=True)
        r["canvas_px_rule_S"] = int(len(rc))
        if len(rc):
            Hc, Wc = ms.canvas
            mask = np.zeros((Hc, Wc), bool); mask[rc[:, 0], rc[:, 1]] = True
            np.savez_compressed(f"/work/p139/nearE/{s}.npz", packed=np.packbits(mask), shape=np.array([Hc, Wc]))
        print("S", short(s), len(rc), f"{time.time()-t0:.0f}s", flush=True)
        del ms, rc
    out = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
               rule=dict(E0=[short(s) for s in E0], named_neighbours=NAMED_NB,
                         N=f">= {N_MIN} densified points within {D_N} vox of E0 (exact)",
                         S=f"canvas pixels within {D_S} vox (exact) of E0 (controls and title)",
                         densify="renderer canvas samples at --scale 1 (20 x 20 per quad, about 1 vox spacing)",
                         min_dist_note="exact minimum over the candidate pairs examined (<= 60 vox); null = none within the bound"),
               E=[short(s) for s in E], found_by_rule_N=[short(s) for s in found],
               named_not_found_by_rule_N=[x for x in NAMED_NB if by[x] not in found],
               found_not_named=[short(s) for s in found if short(s) not in NAMED_NB],
               dense_points_E0={short(s): mesh[s].n_dense for s in E0}, resume_cache=cache,
               segments=rows, seconds=round(time.time() - t0, 1))
    json.dump(out, open("/work/p139/exclusion.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "segments"}, indent=1))


if __name__ == "__main__":
    main()
