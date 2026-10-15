"""p4-pig-gold GOLD detector (RULES.md DECL-P4-10 items 2-4). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]

CT bytes are reduced to per-column statistics, block means, areas and counts. Nothing is displayed, printed or
written as an image. Fetch helpers follow p4-highz tools/sib/p4-highz/common.py (range requests of contiguous
slices of uncompressed (Z,128,128) uint8 chunks; HTTP 404 = fill 0).

Detector (frozen in logs/sib/p4-pig-gold/params.json):
  per column (y, x) at the material's level, over the slab W (+-20 um around the mesh surface):
    v2 (2026-09-26, after a 1-location pilot injection showed v1 P = max 3-slice mean - median insensitive, because the
    published unsharp mask (coeff 4) gives a thin dense layer dark flanking lobes that cancel inside a 3-slice mean):
    P = max over z in W of [ v(z) - 0.5 (min v(z-3..z-1) + min v(z+1..z+3)) ]  (thin-layer ridge; flanks read
    3 slices beyond W)
    Sat = 1 if max_z v >= SAT else 0
  a column is usable iff mesh-valid and min_z v > 0 (in scan, chunk present);
  block means over B x B columns -> work grid (~9 um); Z = masked disc mean of P (radius R_MM) on the work grid;
  hot = Z > TAU (control-derived); tile score A_hot = hot work px x px area (mm^2).
"""
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import threading
import time

import numpy as np
import requests

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SEGS = f"{BUCKET}/PHercParis4/segments"
CH = 128
REF_TILES_B = "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b"
REF_PAIRS = "origin/claude/gifted-bell-gavnl5-sib-pairs0814b"

SV1129 = "surface-volumes/1.129um-0.23m-78keV-volume-20260608103018-L1.zarr"
SV24 = "surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"

# um per slice, centre slice (= mesh surface), level, in-plane um at that level, block B -> work px
MATERIALS = {
    "E1": {"seg": "20260623141924-w010-027", "sv": SV1129, "nz": 116, "centre": 58, "dz_um": 2.258, "level": 0,
           "px_um": 2.258, "B": 4, "grid_src": (REF_TILES_B, "logs/sib/p4-tiles-b/e1a1/manifest.json",
                                                   "logs/sib/p4-tiles-b/e1/grid.json"),
           "mesh": "20260623141924-w010-027/mesh/20260623141924-on-20260608103018-1.129um.tifxyz",
           "canvas_per_grid": 10, "coverage_rule": True, "role": "title"},
    "C1": {"seg": "20260623142658-w028-037", "sv": SV1129, "nz": 116, "centre": 58, "dz_um": 2.258, "level": 0,
           "px_um": 2.258, "B": 4, "grid_src": (REF_TILES_B, "logs/sib/p4-tiles-b/m2b/manifest.json",
                                                   "logs/sib/p4-tiles-b/m2b/grid.json"),
           "mesh": "20260623142658-w028-037/mesh/20260623142658-on-20260608103018-1.129um.tifxyz",
           "canvas_per_grid": 10, "coverage_rule": True, "role": "control"},
    "E2": {"seg": "20260701183124-w010-027", "sv": SV24, "nz": 109, "centre": 54, "dz_um": 2.4, "level": 1,
           "px_um": 4.8, "B": 2, "grid_src": (REF_PAIRS, "logs/sib/pairs0814b/e2/manifest.json",
                                                "logs/sib/pairs0814b/e2/grid.json"),
           "mesh": "20260701183124-w010-027/mesh/20260701183124-on-20260411134726-2.4um.tifxyz",
           "canvas_per_grid": 20, "coverage_rule": False, "role": "title"},
    "C2": {"seg": "20260701183125-w028-037", "sv": SV24, "nz": 109, "centre": 54, "dz_um": 2.4, "level": 1,
           "px_um": 4.8, "B": 2, "grid_src": None, "T": 8343,
           "mesh": "20260701183125-w028-037/mesh/20260701183125-on-20260411134726-2.4um.tifxyz",
           "canvas_per_grid": 20, "coverage_rule": False, "role": "control"},
}

_tl = threading.local()


def session():
    s = getattr(_tl, "s", None)
    if s is None:
        s = _tl.s = requests.Session()
        s.mount("https://", requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=64))
    return s


def get(url, rng=None, tries=8):
    h = {"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {}
    for i in range(tries):
        try:
            r = session().get(url, headers=h, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(30, 2 ** (i + 1)))


def git_json(ref, path):
    return json.loads(subprocess.check_output(["git", "show", f"{ref}:{path}"]))


def slab(mat, half_um, centre_off_um=0.0):
    m = MATERIALS[mat]
    c = m["centre"] + int(round(centre_off_um / m["dz_um"]))
    h = int(round(half_um / m["dz_um"]))
    return c - h, c + h  # inclusive


def load_material(name, scratch):
    """Grid (T in canvas px), eligible tiles and the mesh-valid vertex mask. Mesh tifs fetched, hashed, reduced."""
    import tifffile
    m = MATERIALS[name]
    os.makedirs(scratch, exist_ok=True)
    vpath = os.path.join(scratch, f"valid_{name}.npy")
    if os.path.exists(vpath):
        valid = np.load(vpath)
        inputs = json.load(open(vpath + ".json"))
    else:
        arrs, inputs = [], []
        for a in "xyz":
            key = f"PHercParis4/segments/{m['mesh']}/{a}.tif"
            b = get(f"{BUCKET}/{key}")
            inputs.append({"key": key, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
            p = os.path.join(scratch, f"mesh_{name}_{a}.tif")
            open(p, "wb").write(b)
            del b
            x = tifffile.imread(p)
            arrs.append((x != -1) & np.isfinite(x))
            del x
            os.remove(p)
        valid = arrs[0] & arrs[1] & arrs[2]
        np.save(vpath, valid)
        json.dump(inputs, open(vpath + ".json", "w"))
    za = json.loads(get(f"{SEGS}/{m['seg']}/{m['sv']}/{m['level']}/.zarray"))
    za0 = json.loads(get(f"{SEGS}/{m['seg']}/{m['sv']}/0/.zarray"))
    H0, W0 = za0["shape"][1], za0["shape"][2]
    tiles = []
    if m["grid_src"]:
        ref, man_p, grid_p = m["grid_src"]
        man, g = git_json(ref, man_p), git_json(ref, grid_p)
        T = int(g.get("T_px") or g.get("T_canvas_px"))
        for t in man["tiles"]:
            vf = t.get("valid_fraction")
            if vf is None or vf < 0.5:
                continue
            if m["coverage_rule"]:
                fo = (t.get("stats") or {}).get("frac_mesh_points_outside_1129_volume", t.get("frac_outside"))
                if fo is None or fo >= 0.5:
                    continue
            tiles.append({"r": t["r"], "c": t["c"], "valid_fraction_src": vf})
        grid_rc = g.get("tile_grid_rows_cols") or [g["tile_grid"]["n_rows"], g["tile_grid"]["n_cols"]]
    else:
        T = m["T"]
        cg = m["canvas_per_grid"]
        nr, nc = -(-H0 // T), -(-W0 // T)
        grid_rc = [nr, nc]
        for r in range(nr):
            for c in range(nc):
                gy0, gy1 = r * T // cg, min((r + 1) * T, H0) // cg
                gx0, gx1 = c * T // cg, min((c + 1) * T, W0) // cg
                vf = float(valid[gy0:gy1, gx0:gx1].sum()) / float((T // cg) ** 2)
                if vf >= 0.5:
                    tiles.append({"r": r, "c": c, "valid_fraction_src": vf})
    return {"name": name, "m": m, "T": T, "H0": H0, "W0": W0, "shape": za["shape"], "grid_rc": grid_rc,
            "tiles": tiles, "valid": valid, "mesh_inputs": inputs,
            "url": f"{SEGS}/{m['seg']}/{m['sv']}/{m['level']}"}


def level_valid(mat, ys, xs):
    """mesh-valid mask for level px rows ys, cols xs (level px -> canvas px centre -> grid vertex)."""
    m, valid = mat["m"], mat["valid"]
    f = 2 ** m["level"]
    cg = m["canvas_per_grid"]
    gy = np.minimum((ys * f + f // 2) // cg, valid.shape[0] - 1)
    gx = np.minimum((xs * f + f // 2) // cg, valid.shape[1] - 1)
    v = valid[gy][:, gx]
    H, W = mat["shape"][1], mat["shape"][2]
    return v & (ys < H)[:, None] & (xs < W)[None, :]


def fetch_chunk(mat, yc, xc, z0, z1):
    """uint8 array (z1-z0+1, 128, 128) of slices z0..z1 of chunk (yc, xc); None if absent (404)."""
    nz = mat["m"]["nz"]
    b = get(f"{mat['url']}/0/{yc}/{xc}", (z0 * CH * CH, (z1 + 1) * CH * CH - 1))
    if b is None:
        return None
    a = np.frombuffer(b, np.uint8)
    assert a.size == (z1 - z0 + 1) * CH * CH, (a.size, nz)
    return a.reshape(z1 - z0 + 1, CH, CH)


FLANK = 3


def column_stats(v, sat, fl=FLANK):
    """v: (n + 2 fl, h, w) uint8: the slab W plus fl flank slices on each side.
    Returns P (thin-layer ridge over W, float32), S (saturation flag over W), usable-in-scan mask (over W + flanks)."""
    vf = v.astype(np.float32)
    n = vf.shape[0]
    best = np.full(vf.shape[1:], -1e9, np.float32)
    for z in range(fl, n - fl):
        lo = vf[z - fl:z].min(0)
        hi = vf[z + 1:z + fl + 1].min(0)
        np.maximum(best, vf[z] - 0.5 * (lo + hi), out=best)
    S = (vf[fl:n - fl].max(0) >= sat).astype(np.float32)
    ok = v.min(0) > 0
    return best, S, ok


def block_sum(a, B):
    h, w = a.shape
    return a.reshape(h // B, B, w // B, B).sum((1, 3))


def disc_mean(val_sum, cnt, radius_px):
    """masked disc mean on the work grid: sum(val)/sum(cnt) over a disc; NaN where the disc has < 50 % usable."""
    import cv2
    r = int(round(radius_px))
    k = np.zeros((2 * r + 1, 2 * r + 1), np.float32)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    k[(yy ** 2 + xx ** 2) <= r * r] = 1.0
    num = cv2.filter2D(val_sum.astype(np.float32), -1, k, borderType=cv2.BORDER_CONSTANT)
    den = cv2.filter2D(cnt.astype(np.float32), -1, k, borderType=cv2.BORDER_CONSTANT)
    full = cv2.filter2D(np.ones_like(cnt, np.float32), -1, k, borderType=cv2.BORDER_CONSTANT)
    out = np.full(val_sum.shape, np.nan, np.float32)
    ok = den >= 0.5 * full * (cnt.max() if cnt.size else 1)
    out[ok] = num[ok] / den[ok]
    return out


def tile_work_maps(mat, r, c, windows, sat, threads=48, rows=None):
    """Work-grid maps for tile (r, c) for each slab window (name -> (z0, z1)).
    Returns dict: name -> {'P': sum of P, 'S': sum of Sat, 'n': usable count} on the work grid, plus meta."""
    m, T = mat["m"], mat["T"]
    f, B = 2 ** m["level"], m["B"]
    Tl = T // f  # tile side at this level (T divisible by f for all grids used: 8872, 8869 -> level 0; 8343 level 1 floor)
    y0l, x0l = r * T // f, c * T // f
    H, W = mat["shape"][1], mat["shape"][2]
    y1l, x1l = min(y0l + Tl, H), min(x0l + Tl, W)
    hw, ww = -(-(y1l - y0l) // B), -(-(x1l - x0l) // B)
    zmin = min(w[0] for w in windows.values())
    zmax = max(w[1] for w in windows.values())
    out = {k: {"P": np.zeros((hw, ww), np.float32), "S": np.zeros((hw, ww), np.float32),
               "n": np.zeros((hw, ww), np.float32)} for k in windows}
    meta = {"chunks": 0, "absent": 0, "mesh_valid_px": 0, "usable_px": {k: 0 for k in windows}}
    ycs = range(y0l // CH, (y1l - 1) // CH + 1)
    xcs = range(x0l // CH, (x1l - 1) // CH + 1)
    jobs = [(yc, xc) for yc in ycs for xc in xcs]
    # a single contiguous range covers all windows only if cheap; fetch each window separately
    wl = list(windows.items())

    def work(job):
        yc, xc = job
        ys = yc * CH + np.arange(CH)
        xs = xc * CH + np.arange(CH)
        vm = level_valid(mat, ys, xs)
        vm &= ((ys >= y0l) & (ys < y1l))[:, None] & ((xs >= x0l) & (xs < x1l))[None, :]
        if not vm.any():
            return job, None, 0, False
        res = {}
        absent = False
        for k, (z0, z1) in wl:
            a = fetch_chunk(mat, yc, xc, z0 - FLANK, z1 + FLANK)
            if a is None:
                absent = True
                res[k] = None
                continue
            P, S, ok = column_stats(a, sat)
            res[k] = (P, S, ok & vm)
        return job, res, int(vm.sum()), absent

    with cf.ThreadPoolExecutor(threads) as ex:
        for (yc, xc), res, nvm, absent in ex.map(work, jobs):
            if res is None:
                continue
            meta["chunks"] += 1
            meta["absent"] += int(absent)
            meta["mesh_valid_px"] += nvm
            # place into tile-local work grid (tile origin aligned to B within tile-local coords)
            ly, lx = yc * CH - y0l, xc * CH - x0l
            for k, v in res.items():
                if v is None:
                    continue
                P, S, ok = v
                okf = ok.astype(np.float32)
                meta["usable_px"][k] += int(ok.sum())
                # pad chunk into B-aligned local canvas
                sy, sx = ly % B, lx % B
                buf = np.zeros((3, CH + 2 * B, CH + 2 * B), np.float32)
                buf[0, sy:sy + CH, sx:sx + CH] = P * okf
                buf[1, sy:sy + CH, sx:sx + CH] = S * okf
                buf[2, sy:sy + CH, sx:sx + CH] = okf
                by0, bx0 = (ly - sy) // B, (lx - sx) // B
                hb = (CH + 2 * B) // B
                for i, key in enumerate(("P", "S", "n")):
                    bs = block_sum(buf[i], B)
                    # clip to work grid
                    a0, b0 = max(by0, 0), max(bx0, 0)
                    a1, b1 = min(by0 + hb, hw), min(bx0 + hb, ww)
                    if a1 > a0 and b1 > b0:
                        out[k][key][a0:a1, b0:b1] += bs[a0 - by0:a1 - by0, b0 - bx0:b1 - bx0]
    return out, meta


def score_maps(maps, px_mm, radius_mm, tau=None):
    """Z map (disc mean of P) and summary statistics; if tau given, hot area and components."""
    import cv2
    Pn, n = maps["P"], maps["n"]
    Bn = n.max() if n.size else 1
    Z = disc_mean(Pn, n, radius_mm / px_mm)
    Zs = disc_mean(maps["S"], n, radius_mm / px_mm)
    good = np.isfinite(Z)
    res = {"work_px_scored": int(good.sum()), "px_mm": px_mm}
    if good.any():
        zv = Z[good]
        res.update({"Z_max": float(zv.max()), "Z_p50": float(np.percentile(zv, 50)),
                    "Z_p99": float(np.percentile(zv, 99)), "Z_p9999": float(np.percentile(zv, 99.99)),
                    "Zs_max": float(np.nanmax(Zs))})
    if tau is not None:
        hot = good & (Z > tau)
        area_px = px_mm ** 2
        res["A_hot_mm2"] = float(hot.sum() * area_px)
        nl, lab, st, _ = cv2.connectedComponentsWithStats(hot.astype(np.uint8), connectivity=8)
        comps = sorted([(int(st[i, cv2.CC_STAT_AREA]), int(st[i, cv2.CC_STAT_WIDTH]), int(st[i, cv2.CC_STAT_HEIGHT]))
                        for i in range(1, nl)], reverse=True)
        res["n_comp"] = nl - 1
        res["largest_comp_mm2"] = float(comps[0][0] * area_px) if comps else 0.0
        res["n_comp_letter_scale"] = int(sum(1 for a, w, h in comps if 0.5 <= max(w, h) * px_mm <= 5.0))
    return Z, Zs, res
