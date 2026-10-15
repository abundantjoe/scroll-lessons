"""DECL-P4-13 P4-M item 2, part c: mesh-anchored sheet test above strip a's top edge, using the organizers' own
re-meshed labelled segment 20231016151002 (open bucket, 20260411134726 frame) as the continuation hypothesis.

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only; CT values are sampled along normals and reduced to one index per vertex. Nothing is displayed.

Why: the tracker test (edge_cont.py) failed its own validation (positive-control r below the shuffled null; tracker
drift 148 um median). This test has no tracker. It asks whether the CT shows a sheet centred on an existing
organizer mesh, above strip a's edge as well as it does below it.

Method (level 2, 9.6 um voxels):
- Segment grid columns that overlap strip a (a vertex within 0.05 mm of a strip-a vertex with z in 168-172.9 mm)
  are kept; each gets the strip-a column c of that overlap vertex and the strip-a top-edge z of that grid column.
- For every kept segment vertex (every 2nd row, every 3rd kept column) with height h = z - edge_z in [-4, +6] mm:
  unit normal n from the segment grid (central differences), profile I(p + t n), t = -16..16 voxels (trilinear).
- Centred-peak index SPI = mean I(|t| <= 2) - mean I(6 <= |t| <= 12)  (sheet core minus the 58-115 um ring).
- Null: the same index at p + s n with s = +-13 voxels (125 um, half the measured 240-260 um winding pitch), i.e.
  centred in the inter-sheet gap.
- Reported per 0.5 mm height band and strip-a column: mean SPI on-mesh and null, with 95 % CI from a bootstrap
  over segment grid columns (the independent unit), the fraction of zero-valued (outside the organizers' mask)
  profile centres, and the vertex count.
- Band call 'sheet' when the on-mesh lower CI > the null upper CI and on-mesh mean >= 0.5 x the reference
  (the mean on-mesh SPI over h in [-4, -0.5] mm of the same column); 'no-sheet' when the on-mesh upper CI < 0.5 x
  reference or centres are > 50 % zero; else 'undetermined'.
Usage: python edge_anchor.py <strip meshdir> <seg prefix (2.4 um tifxyz)> <out.json> <manifest.jsonl> [cache]
"""
import json, os, sys, time
import numpy as np, tifffile
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
from zarrfetch import Vol
from edge_cont import tri

VOX_MM = 0.0024
L = 2
F = 2 ** L
T = 8343


def load(prefix):
    P = np.stack([tifffile.imread(f"{prefix}_{a}.tif").astype(np.float64) for a in "xyz"], -1)
    v = (P != -1).all(-1) & np.isfinite(P).all(-1) & (P != 0).any(-1)
    return P, v


def main(md, seg, out, man, cache=None):
    t0 = time.time()
    SA, va = load(f"{md}/mesh")
    gh, gw = va.shape
    first = np.where(va.any(0), va.argmax(0), -1)
    edge_z = np.where(first >= 0, SA[np.maximum(first, 0), np.arange(gw), 2] * VOX_MM, np.nan)
    ii, jj = np.nonzero(va)
    zA = SA[ii, jj, 2] * VOX_MM
    band = (zA > 168) & (zA <= 172.95) & (ii % 2 == 0) & (jj % 2 == 0)
    tree = cKDTree(SA[ii[band], jj[band]])
    bj = jj[band]
    P, v = load(seg)
    sh, sw = v.shape
    z = P[..., 2] * VOX_MM
    si, sj = np.nonzero(v & (z > 168) & (z <= 172.95))
    d, k = tree.query(P[si, sj], distance_upper_bound=0.05 / VOX_MM)
    ok = np.isfinite(d)
    col_c, col_ez = {}, {}
    for a, b, kk in zip(si[ok], sj[ok], k[ok]):
        if b not in col_c:
            j = bj[kk]
            col_c[b] = int((j * 20) // T)
            col_ez[b] = float(edge_z[j])
    kept = np.array(sorted(col_c))[::3]
    print("kept seg columns", len(kept), "%.0fs" % (time.time() - t0), flush=True)
    rows = np.arange(0, sh, 2)
    R, C = np.meshgrid(rows, kept, indexing="ij")
    R, C = R.ravel(), C.ravel()
    m = v[R, C] & (R >= 1) & (R < sh - 1) & (C >= 1) & (C < sw - 1)
    R, C = R[m], C[m]
    m = v[R + 1, C] & v[R - 1, C] & v[R, C + 1] & v[R, C - 1]
    R, C = R[m], C[m]
    ez = np.array([col_ez[c] for c in C])
    h = z[R, C] - ez
    m = (h >= -4) & (h <= 6)
    R, C, h, ez = R[m], C[m], h[m], ez[m]
    cc = np.array([col_c[c] for c in C])
    dr = P[R + 1, C] - P[R - 1, C]
    dc = P[R, C + 1] - P[R, C - 1]
    n = np.cross(dc, dr)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    p = P[R, C][:, ::-1] / F
    n = n[:, ::-1]
    print("vertices", len(R), flush=True)
    v3 = Vol(L, man, threads=48, mem_chunks=30000, cache_dir=cache)
    t = np.arange(-16, 17, dtype=np.float64)
    core = np.abs(t) <= 2
    ring = (np.abs(t) >= 6) & (np.abs(t) <= 12)

    def spi(offset):
        out = np.zeros(len(p), np.float32)
        cen = np.zeros(len(p), np.float32)
        B = 20000
        for s in range(0, len(p), B):
            q = p[s:s + B] + offset * n[s:s + B]
            pts = q[:, None, :] + t[None, :, None] * n[s:s + B, None, :]
            pr = tri(v3, pts.reshape(-1, 3)).reshape(len(q), len(t))
            out[s:s + B] = pr[:, core].mean(1) - pr[:, ring].mean(1)
            cen[s:s + B] = pr[:, 16]
        return out, cen
    on, cen = spi(0.0)
    print("on done %.0fs chunks %d" % (time.time() - t0, v3.n_get), flush=True)
    n1, _ = spi(13.0)
    n2, _ = spi(-13.0)
    null = np.concatenate([n1, n2])
    null_cols = np.concatenate([C, C])
    null_h = np.concatenate([h, h])
    null_cc = np.concatenate([cc, cc])
    rng = np.random.default_rng(20260926)

    def boot(vals, cols, nb=400):
        u, inv = np.unique(cols, return_inverse=True)
        sums = np.bincount(inv, weights=vals)
        cnt = np.bincount(inv)
        idx = rng.integers(0, len(u), (nb, len(u)))
        bm = sums[idx].sum(1) / cnt[idx].sum(1)
        return float(vals.mean()), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)), int(len(u))

    edges = np.arange(-4, 6.01, 0.5)
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "strip": "20260701183124-w010-027", "anchor_mesh": os.path.basename(seg),
           "method": __doc__.split("Method")[1].split("Usage")[0].strip(), "level": L,
           "chunks": {"fetched": v3.n_get, "absent_404": v3.n_404}, "groups": {}}
    groups = {"c9-c15": (cc >= 9) & (cc <= 15)}
    for c in sorted(set(cc.tolist())):
        groups[f"c{c}"] = cc == c
    for g, gm in groups.items():
        if gm.sum() < 50:
            continue
        gnull = np.concatenate([gm, gm])
        refm = gm & (h >= -4) & (h <= -0.5)
        ref = float(on[refm].mean()) if refm.any() else float("nan")
        bands = []
        for a, b in zip(edges[:-1], edges[1:]):
            bm = gm & (h >= a) & (h < b)
            bn = gnull & (null_h >= a) & (null_h < b)
            if bm.sum() < 20:
                bands.append({"h_mm": [float(a), float(b)], "n": int(bm.sum())})
                continue
            o = boot(on[bm], C[bm])
            nu = boot(null[bn], null_cols[bn])
            zf = float((cen[bm] == 0).mean())
            if o[1] > nu[2] and o[0] >= 0.5 * ref:
                call = "sheet"
            elif o[2] < 0.5 * ref or zf > 0.5:
                call = "no-sheet"
            else:
                call = "undetermined"
            bands.append({"h_mm": [float(a), float(b)], "n": int(bm.sum()), "n_seg_cols": o[3],
                          "spi_on_mean_ci": [round(o[0], 2), round(o[1], 2), round(o[2], 2)],
                          "spi_null_mean_ci": [round(nu[0], 2), round(nu[1], 2), round(nu[2], 2)],
                          "frac_centre_zero": round(zf, 3), "call": call})
        res["groups"][g] = {"ref_spi_below_edge": round(ref, 2), "n_vertices": int(gm.sum()), "bands": bands}
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out, "w"), indent=1)
    for g, x in res["groups"].items():
        print(g, "ref", x["ref_spi_below_edge"], "n", x["n_vertices"])
        for b in x["bands"]:
            if "call" in b:
                print("  h %5.1f..%4.1f n %6d on %s null %s zero %.2f %s" % (b["h_mm"][0], b["h_mm"][1], b["n"], b["spi_on_mean_ci"], b["spi_null_mean_ci"], b["frac_centre_zero"], b["call"]))


if __name__ == "__main__":
    main(*sys.argv[1:])
