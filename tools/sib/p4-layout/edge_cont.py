"""DECL-P4-13 P4-M item 2, part b: sheet-continuation test above strip a's official mesh top edge.

Provenance: Project HERCULES | owner the owner | [id removed]
Numbers only. CT voxels are sampled as numbers along mesh normals; nothing is displayed or described as an image.

Method (level-2 volume, 9.6 um voxels; distances along the sheet in mm):
- Segments: the top edge is cut into 1 mm segments (21 grid columns each). Per segment, NLAT lateral mesh columns;
  per column the edge vertex p0 (first mesh-valid grid row from the canvas top; row 0 = high z), the unit
  up-direction u (p0 minus the vertex 2 mm below, normalised) and the unit normal n (grid cross product, forward difference over 4 rows and +-2 columns).
- Profile at height d: I(p(d) + t n) for t = -TW..TW (1-voxel steps, trilinear), averaged over the segment's
  columns and over heights d-0.1, d, d+0.1 mm. p(d) is the mesh vertex for d < 0 (inside the mesh) and the linear
  extrapolation p0 + d u for d >= 0 (above the edge).
- Template: the mean in-mesh profile over d in [-2.0, -0.5] mm of the same segment, central +-TT.
- Continuity tracking: starting at offset 0 at d = -0.5 mm, for each step d += 0.1 mm the offset o may change by at
  most +-2 voxels; o is chosen to maximise the Pearson r of the template against the profile shifted by o.
  r(d) and o(d) are recorded.
- Sheet present at d: r(d) >= R_THR and the profile's central value > 0 (inside the organizers' scroll mask).
  R_THR = the 10th percentile of r over the positive control (below). d_cont = the last d >= 0 before the first
  run of 3 consecutive steps (0.3 mm) that fail.
- Positive control (sheet known to continue): the identical procedure with a pseudo-edge 6 mm below the true edge
  (template from 8.0-6.5 mm below, extrapolated linearly upward through the region the mesh does cover). It gives
  the r distribution of a continuing sheet and the tracker's point-to-mesh error there.
- Negative control (no sheet): the same template correlated at the segment's heights above the scroll mask end,
  plus a shuffled control: the template of segment k against the profile of segment k+97 (unrelated place).
Usage: python edge_cont.py <meshdir> <out.json> <manifest.jsonl> [cache_dir]
"""
import json, os, sys, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from zarrfetch import Vol

VOX_MM = 0.0024
L = 2
F = 2 ** L
UM = 2.4 * F
T = 8343
ROWS_PER_MM = 1 / 0.04795
SEG = 21
NLAT = 7
TW = int(round(400 / UM))   # profile half-width, voxels
TT = int(round(150 / UM))   # template half-width
DMAX = 7.0
DSTEP = 0.1


def tri(v, pts):
    p0 = np.floor(pts).astype(np.int64)
    f = (pts - p0).astype(np.float32)
    out = np.zeros(len(pts), np.float32)
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                w = (f[:, 0] if dz else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dx else 1 - f[:, 2])
                out += w * v.sample(p0 + [dz, dy, dx])
    return out


def pearson_shift(tmpl, prof, o):
    """r of tmpl (2TT+1) against prof (2TW+1) centred at integer offset o (per row)."""
    n = tmpl.shape[1]
    idx = (TW - TT) + o[:, None] + np.arange(n)[None]
    x = np.take_along_axis(prof, np.clip(idx, 0, prof.shape[1] - 1), 1)
    a = tmpl - tmpl.mean(1, keepdims=True)
    b = x - x.mean(1, keepdims=True)
    den = np.sqrt((a * a).sum(1) * (b * b).sum(1))
    return np.where(den > 0, (a * b).sum(1) / np.maximum(den, 1e-9), 0.0)


def main(md, out, man, cache=None):
    t0 = time.time()
    P = np.stack([tifffile.imread(f"{md}/mesh_{a}.tif").astype(np.float32) for a in "xyz"], -1)
    valid = (P != -1).all(-1) & np.isfinite(P).all(-1)
    gh, gw = valid.shape
    Q = P[..., ::-1] / F  # zyx, level-2 voxels
    first = np.where(valid.any(0), valid.argmax(0), -1)
    k2 = int(round(2 * ROWS_PER_MM))
    kfar = int(round(8.3 * ROWS_PER_MM))
    segs = []
    kpc = int(round(6 * ROWS_PER_MM))
    def okv(ii, jj):
        ii = np.asarray(ii); jj = np.asarray(jj)
        inb = (ii >= 0) & (ii + 4 < gh) & (jj >= 2) & (jj + 2 < gw)
        ii2 = np.clip(ii, 0, gh - 5); jj2 = np.clip(jj, 2, gw - 3)
        return inb & valid[ii2, jj2] & valid[ii2 + 2, jj2] & valid[ii2 + 4, jj2] & valid[ii2, jj2 + 2] & valid[ii2, jj2 - 2]
    for s0 in range(0, gw - SEG + 1, SEG):
        cols_ = s0 + np.linspace(2, SEG - 3, NLAT).astype(int)
        i0_ = first[cols_]
        if (i0_ < 0).any():
            continue
        base_ok = okv(i0_, cols_) & okv(i0_ + k2, cols_) & okv(i0_ + kpc, cols_) & okv(i0_ + kpc + k2, cols_)
        if base_ok.sum() >= 4:
            # replace failing columns by a passing one (duplicate) so arrays stay rectangular; record count
            good = np.nonzero(base_ok)[0]
            fix = np.where(base_ok, np.arange(NLAT), good[0])
            segs.append((s0, cols_[fix], i0_[fix], int(base_ok.sum())))
    NS = len(segs)
    print("segments", NS, flush=True)
    cols = np.array([s[1] for s in segs])          # (NS, NLAT)
    i0 = np.array([s[2] for s in segs])            # (NS, NLAT)

    def normal(ii, jj):
        dr = Q[ii + 4, jj] - Q[ii, jj]
        dc = Q[ii, np.minimum(jj + 2, gw - 1)] - Q[ii, jj - 2]
        nn = np.cross(dc, dr)
        return nn / np.linalg.norm(nn, axis=-1, keepdims=True)

    v = Vol(L, man, threads=48, mem_chunks=30000, cache_dir=cache)
    t = np.arange(-TW, TW + 1, dtype=np.float32)

    def prof_at(base_row, dd):
        """Mean profile per segment at height dd (mm) relative to an edge at grid row base_row (NS, NLAT)."""
        acc = np.zeros((NS, len(t)), np.float32)
        cnt = np.zeros(NS, np.float32)
        for d in (dd - DSTEP, dd, dd + DSTEP):
            if d < 0:
                ii = np.clip(base_row + int(round(-d * ROWS_PER_MM)), 0, gh - 5)
                p = Q[ii, cols]
                n = normal(ii, cols)
                w = okv(ii, cols).astype(np.float32)
            else:
                pe = Q[base_row, cols]
                pb = Q[base_row + k2, cols]
                u = pe - pb
                u /= np.linalg.norm(u, axis=-1, keepdims=True)
                p = pe + (d / (F * VOX_MM)) * u
                n = normal(base_row, cols)
                w = np.ones(cols.shape, np.float32)
            n = np.nan_to_num(n)
            pts = p[:, :, None, :] + t[None, None, :, None] * n[:, :, None, :]
            val = tri(v, pts.reshape(-1, 3)).reshape(NS, NLAT, len(t))
            ww = w.sum(1)
            acc += np.where(ww[:, None] > 0, (val * w[:, :, None]).sum(1) / np.maximum(ww, 1)[:, None], 0)
            cnt = cnt + (ww > 0).astype(np.float32)
        return acc / np.maximum(cnt, 1)[:, None], p

    def run(base_row, tmpl_from, tmpl_to, d_start, d_end):
        tm = []
        for d in np.arange(tmpl_from, tmpl_to + 1e-6, 0.25):
            pr, _ = prof_at(base_row, d)
            tm.append(pr)
        tmpl = np.mean(tm, 0)[:, TW - TT:TW + TT + 1]
        o = np.zeros(NS, int)
        rows = []
        for d in np.arange(d_start, d_end + 1e-6, DSTEP):
            pr, p = prof_at(base_row, round(d, 3))
            best_r = np.full(NS, -2.0)
            best_o = o.copy()
            for do in (-2, -1, 0, 1, 2):
                oo = np.clip(o + do, -(TW - TT), TW - TT)
                r = pearson_shift(tmpl, pr, oo)
                upd = r > best_r
                best_r = np.where(upd, r, best_r)
                best_o = np.where(upd, oo, best_o)
            o = best_o
            centre = pr[np.arange(NS), TW + o]
            rows.append({"d": round(float(d), 2), "r": best_r, "o": o.copy(), "centre": centre,
                         "zmm": p[:, NLAT // 2, 0] * F * VOX_MM, "prof": pr})
        return tmpl, rows

    # positive control: pseudo-edge 6 mm below the true edge
    pc_base = i0 + int(round(6 * ROWS_PER_MM))
    _, pc = run(pc_base, -2.0, -0.5, -0.5, 6.0)
    print("pc done %.0fs chunks %d" % (time.time() - t0, v.n_get), flush=True)
    r_pc = np.array([x["r"] for x in pc if x["d"] >= 0])  # (nd, NS)
    R_THR = float(np.percentile(r_pc, 10))
    # tracker vs mesh in the positive control: tracked point p(d)+o*n vs true mesh vertices of the same columns
    pc_err = []
    for x in pc:
        if x["d"] < 0.5 or abs(x["d"] * 10 - round(x["d"] * 10)) > 1e-6 or round(x["d"] * 10) % 5:
            continue
        d = x["d"]
        pe = Q[pc_base, cols]; pb = Q[pc_base + k2, cols]
        u = pe - pb; u /= np.linalg.norm(u, axis=-1, keepdims=True)
        n = normal(pc_base, cols)
        q = (pe + (d / (F * VOX_MM)) * u + x["o"][:, None, None] * n)[:, NLAT // 2]  # (NS,3)
        rr = np.clip(pc_base[:, NLAT // 2, None] - np.arange(int(round((d - 1.5) * ROWS_PER_MM)), int(round((d + 1.5) * ROWS_PER_MM)))[None], 0, gh - 1)
        M = Q[rr, cols[:, NLAT // 2, None]]
        pc_err.append(np.linalg.norm(M - q[:, None], axis=-1).min(1) * UM)
    pc_err = np.array(pc_err)
    # the real test above the true edge
    tmpl, up = run(i0, -2.0, -0.5, -0.5, DMAX)
    print("up done %.0fs chunks %d" % (time.time() - t0, v.n_get), flush=True)
    # shuffled negative control: segment templates against unrelated segments' in-mesh profiles at d = -0.5..-2
    sh = []
    perm = (np.arange(NS) + 97) % NS
    for x in up:
        if x["d"] <= -0.0:
            prof = x["prof"][perm]
            best = np.full(NS, -2.0)
            for oo in range(-(TW - TT), TW - TT + 1):
                best = np.maximum(best, pearson_shift(tmpl, prof, np.full(NS, oo)))
            sh.append(best)
    r_sh = np.array(sh) if sh else np.zeros((1, NS))

    def dcont(rows):
        res = np.zeros(NS)
        miss = np.zeros(NS, int)
        alive = np.ones(NS, bool)
        for x in rows:
            if x["d"] < 0:
                continue
            ok = (x["r"] >= R_THR) & (x["centre"] > 0)
            miss = np.where(ok, 0, miss + 1)
            alive &= miss < 3
            res = np.where(alive & ok, x["d"], res)
        return res
    d_up = dcont(up)
    d_pc = dcont(pc)
    # scroll-mask end along the extrapolated path (first d >= 0 with centre value 0 in 3 consecutive steps)
    mask_end = np.full(NS, np.nan)
    zc = np.zeros(NS, int)
    for x in up:
        if x["d"] < 0:
            continue
        zero = x["prof"].max(1) == 0
        zc = np.where(zero, zc + 1, 0)
        hit = (zc == 3) & np.isnan(mask_end)
        mask_end = np.where(hit, x["d"] - 0.2, mask_end)
    seg_c = (cols[:, NLAT // 2] * 20) // T
    res = {"provenance": "Project HERCULES | owner the owner | [id removed]",
           "segment": "20260701183124-w010-027", "volume": "20260411134726 (masked)", "level": L, "voxel_um": UM,
           "method": __doc__.split("Method")[1].split("Usage")[0].strip(),
           "params": {"seg_grid_cols": SEG, "n_lat": NLAT, "profile_halfwidth_um": TW * UM, "template_halfwidth_um": TT * UM,
                      "d_step_mm": DSTEP, "d_max_mm": DMAX, "offset_step_limit_vox": 2},
           "R_THR_pc_p10": R_THR,
           "positive_control": {"r_p10_p50_p90": np.percentile(r_pc, [10, 50, 90]).tolist(),
                                "d_cont_mm_p10_p50_p90": np.percentile(d_pc, [10, 50, 90]).tolist(),
                                "frac_full_6mm": float((d_pc >= 5.9).mean()),
                                "tracker_to_mesh_um_p50_p90": np.percentile(pc_err, [50, 90]).tolist() if len(pc_err) else None},
           "shuffled_null": {"r_max_over_offsets_p50_p90_p99": np.percentile(r_sh, [50, 90, 99]).tolist()},
           "chunks": {"fetched": v.n_get, "absent_404": v.n_404, "bytes": v.bytes},
           "seconds": round(time.time() - t0, 1),
           "segments": []}
    rz = {x["d"]: x for x in up}
    for k in range(NS):
        res["segments"].append({
            "c": int(seg_c[k]), "grid_cols": [int(segs[k][0]), int(segs[k][0] + SEG)],
            "n_lat_valid": int(segs[k][3]), "edge_row_med": float(np.median(i0[k])), "edge_z_mm": float(np.median(Q[i0[k], cols[k], 0]) * F * VOX_MM),
            "d_cont_mm": float(d_up[k]), "mask_end_mm": None if np.isnan(mask_end[k]) else float(mask_end[k]),
            "pc_d_cont_mm": float(d_pc[k]),
            "r_at_d": {str(d): round(float(rz[d]["r"][k]), 3) for d in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0) if d in rz},
            "offset_um_at_d": {str(d): round(float(rz[d]["o"][k] * UM), 1) for d in (0.0, 1.0, 2.0, 3.0, 4.0, 5.0) if d in rz},
            "z_mm_at_d": {str(d): round(float(rz[d]["zmm"][k]), 2) for d in (0.0, 1.0, 2.0, 5.0) if d in rz},
        })
    json.dump(res, open(out, "w"), indent=0)
    print("R_THR %.3f pc r p10/50/90 %s shuffled p50/90/99 %s pc err %s" % (
        R_THR, np.round(np.percentile(r_pc, [10, 50, 90]), 3), np.round(np.percentile(r_sh, [50, 90, 99]), 3),
        res["positive_control"]["tracker_to_mesh_um_p50_p90"]))
    print("pc d_cont p10/50/90", np.percentile(d_pc, [10, 50, 90]), "full 6mm frac %.2f" % (d_pc >= 5.9).mean())
    for c in sorted(set(seg_c.tolist())):
        m = seg_c == c
        du = d_up[m]
        me = mask_end[m]
        print("c%-2d n=%2d d_cont med %.2f p25 %.2f p75 %.2f max %.2f | >=1mm %.2f >=2mm %.2f | mask_end med %.2f | edge z %.2f | pc d med %.2f" % (
            c, m.sum(), np.median(du), np.percentile(du, 25), np.percentile(du, 75), du.max(), (du >= 1).mean(), (du >= 2).mean(),
            np.nanmedian(me) if np.isfinite(me).any() else np.nan, np.median(Q[i0[m], cols[m], 0]) * F * VOX_MM, np.median(d_pc[m])), flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
