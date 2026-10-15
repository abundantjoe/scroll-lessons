"""P4-L (RULES.md DECL-P4-12): thin-slab MAX channel of the 2.4 um surface volume on the strip-a grid.

Provenance: Project HERCULES | owner the owner | [id removed]

Builder only: never opens, views or prints image pixels. Writes numbers, hashes and PNG bytes only.
Parameters are frozen in logs/sib/p4-l2/l2/params.json (pushed before any computation).

Channel: per canvas px, the max over slab slices 48..60 (54 +- 6, +-14.4 um; centre slice 54 = mesh surface) of
the level-0 uint8 voxels. Canvas px (i, j) = level-0 (row i, col j). Chunks are uncompressed C-order
(109, 128, 128) u8, so the 13 contiguous slab slices of a chunk are one HTTP range request. 404 = fill 0.
Display: clip(255*(max - T_mid)/(T_hi - T_mid), 0, 255) -> np.rint -> uint8, 0 outside mesh-valid,
cv2.INTER_AREA 8343 -> 1068, PNG IHDR/IDAT/IEND (builder.png_bytes).
Grid, mesh-valid rule and eligibility are those of pairs0814b e2 (cc81a677) verbatim.

Usage:
  l2.py thresholds <ctl_mesh_dir> <out_dir> --worker k --nworkers n ; l2.py thresholds-merge <ctl_mesh_dir> <out_dir>
  l2.py tiles <mesh_dir> <out_dir> <thresholds.json> --worker k --nworkers n [--only "r,c;r,c"]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import sys
import time
import zlib

import numpy as np
import requests
import tifffile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

PROV = "Project HERCULES | owner the owner | [id removed]"
HTTP = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SEG = "20260701183124-w010-027"
CTL = "20260701183125-w028-037"
SVNAME = "surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
NZ, CH = 109, 128
CENTRE, HALF = 54, 6  # slices 48..60, +-14.4 um
Z0, Z1 = CENTRE - HALF, CENTRE + HALF + 1
T, OUT_SIDE, ELIG = 8343, 1068, 0.5
LEVEL = 0
SEED, SAMPLE_FRAC = 20260926, 0.10

_s = requests.Session()
_s.mount("https://", requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=3))


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sv_key(seg):
    return f"PHercParis4/segments/{seg}/{SVNAME}"


def canvas_mask(valid, H, W, y0, y1, x0, x1):
    """Verbatim rule of tools/sib/p4-tiles-a/tile_w010_027.py (e25635c) / pairs0814b e2_tiles.py."""
    gh, gw = valid.shape
    ys = np.arange(y0, y1)
    xs = np.arange(x0, x1)
    iny = (ys >= 0) & (ys < H)
    inx = (xs >= 0) & (xs < W)
    gy = np.clip((ys * gh) // H, 0, gh - 1)
    gx = np.clip((xs * gw) // W, 0, gw - 1)
    m = valid[np.ix_(gy, gx)]
    m &= iny[:, None] & inx[None, :]
    return m


def load_valid(mesh_dir):
    P = np.stack([tifffile.imread(os.path.join(mesh_dir, n)) for n in ("x.tif", "y.tif", "z.tif")], -1)
    valid = ~((P[..., 0] == -1) | (P[..., 1] == -1) | (P[..., 2] == -1))
    valid &= np.isfinite(P).all(-1)
    return valid


def slab_max_from_stack(stack):
    """stack: (n_slab, h, w) uint8 -> per-px max (uint8). Production projection (also used by the unit tests)."""
    return stack.max(axis=0)


def display_from_max(mx, valid, t_mid, t_hi):
    """Production display value: clip(255*(max - T_mid)/(T_hi - T_mid), 0, 255), rint, uint8; 0 outside valid."""
    v = (mx.astype(np.float32) - np.float32(t_mid)) * np.float32(255.0 / (t_hi - t_mid))
    np.clip(v, 0, 255, out=v)
    d = np.rint(v).astype(np.uint8)
    d[~valid] = 0
    return d


def get_chunk(seg, cy, cx):
    """Slab (13, 128, 128) uint8 of chunk (0, cy, cx) at level 0, or None for 404; plus a record."""
    key = f"{sv_key(seg)}/{LEVEL}/0/{cy}/{cx}"
    a, b = Z0 * CH * CH, Z1 * CH * CH - 1
    for i in range(7):
        try:
            r = _s.get(f"{HTTP}/{key}", headers={"Range": f"bytes={a}-{b}"}, timeout=60)
            if r.status_code == 404:
                return None, {"k": f"{LEVEL}/0/{cy}/{cx}", "status": 404}
            if r.status_code == 206 and len(r.content) == b - a + 1:
                d = np.frombuffer(r.content, np.uint8).reshape(Z1 - Z0, CH, CH)
                return d, {"k": f"{LEVEL}/0/{cy}/{cx}", "status": 206, "range": [a, b],
                           "sha256": hashlib.sha256(r.content).hexdigest()}
        except requests.RequestException:
            pass
        time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"chunk read failed: {key}")


def region(seg, y0, y1, x0, x1, shape, m, ex, t_hi=None):
    """Slab max over canvas rows [y0,y1), cols [x0,x1) (0 outside the array), plus a uint8 voxel histogram of the
    13 slab voxels at mask m (m has the region's shape), plus n voxels > t_hi at m."""
    H, W = shape
    out = np.zeros((y1 - y0, x1 - x0), np.uint8)
    hist = np.zeros(256, np.int64)
    n_hi = 0
    jobs = [(cy, cx) for cy in range(max(y0, 0) // CH, (min(y1, H) - 1) // CH + 1)
            for cx in range(max(x0, 0) // CH, (min(x1, W) - 1) // CH + 1)]
    recs = []
    for (cy, cx), (d, rec) in zip(jobs, ex.map(lambda j: get_chunk(seg, *j), jobs)):
        recs.append(rec)
        ya, yb = max(cy * CH, y0), min(cy * CH + CH, y1, H)
        xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W)
        mm = m[ya - y0:yb - y0, xa - x0:xb - x0]
        if d is None:
            hist[0] += int(mm.sum()) * (Z1 - Z0)
            continue
        sub = d[:, ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH]
        out[ya - y0:yb - y0, xa - x0:xb - x0] = slab_max_from_stack(sub)
        if mm.any():
            vox = sub[:, mm]
            hist += np.bincount(vox.ravel(), minlength=256)
            if t_hi is not None:
                n_hi += int((vox > t_hi).sum())
    # voxels of valid px beyond the array edge are fill 0 (none expected: mask is False there)
    return out, hist, n_hi, recs


def q_hist(hist, q):
    """Inverted-CDF quantile of an integer histogram: smallest v with CDF(v) >= q."""
    c = np.cumsum(hist)
    return int(np.searchsorted(c, q * c[-1], side="left"))


def zarray(seg):
    za = requests.get(f"{HTTP}/{sv_key(seg)}/{LEVEL}/.zarray", timeout=60)
    j = za.json()
    assert j["shape"][0] == NZ and j["chunks"] == [NZ, CH, CH] and j["dtype"] == "|u1" and j["compressor"] is None \
        and j["order"] == "C" and j.get("dimension_separator") == "/", j
    return j, hashlib.sha256(za.content).hexdigest()


def ctl_sample(valid, H, W):
    nr, nc = -(-H // T), -(-W // T)
    el = []
    for r in range(nr):
        for c in range(nc):
            vf = float(canvas_mask(valid, H, W, r * T, (r + 1) * T, c * T, (c + 1) * T).mean())
            if vf >= ELIG:
                el.append((r, c, vf))
    n = math.ceil(SAMPLE_FRAC * len(el))
    idx = np.random.default_rng(SEED).choice(len(el), n, replace=False)
    return nr, nc, el, [el[i] for i in sorted(idx)]


def cmd_thresholds(a):
    """Worker k of n: per-tile control histograms -> <out_dir>/ctl_w<k>.jsonl."""
    za, za_sha = zarray(CTL)
    H, W = za["shape"][1:]
    valid = load_valid(a.mesh_dir)
    assert valid.shape == (H // 20, W // 20), (valid.shape, H, W)
    nr, nc, el, pick = ctl_sample(valid, H, W)
    ex = cf.ThreadPoolExecutor(a.threads)
    fo = open(os.path.join(a.out, "ctl_w%d.jsonl" % a.worker), "a")
    for r, c, vf in pick[a.worker::a.nworkers]:
        t0 = time.time()
        y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
        m = canvas_mask(valid, H, W, y0, y1, x0, x1)
        _, h, _, recs = region(CTL, y0, y1, x0, x1, (H, W), m, ex)
        fo.write(json.dumps({"r": r, "c": c, "valid_fraction": vf, "valid_px": int(m.sum()), "voxels": int(h.sum()),
                    "median": q_hist(h, 0.5), "p99.9": q_hist(h, 0.999), "frac_vox_zero": float(h[0] / h.sum()),
                    "chunks_read": sum(x["status"] == 206 for x in recs),
                    "chunks_missing": sum(x["status"] == 404 for x in recs),
                    "chunks_sha256_of_sorted_list": hashlib.sha256("\n".join(sorted(
                        f'{x["k"]} {x.get("sha256", "404")}' for x in recs)).encode()).hexdigest(),
                    "seconds": round(time.time() - t0, 1), "hist": h.tolist()}) + "\n")
        fo.flush()
        print("ctl tile r%d c%d %.1fs" % (r, c, time.time() - t0), flush=True)
    ex.shutdown()


def cmd_thresholds_merge(a):
    za, za_sha = zarray(CTL)
    H, W = za["shape"][1:]
    valid = load_valid(a.mesh_dir)
    nr, nc, el, pick = ctl_sample(valid, H, W)
    per = {}
    for fn in sorted(os.listdir(a.out)):
        if fn.startswith("ctl_w") and fn.endswith(".jsonl"):
            for l in open(os.path.join(a.out, fn)):
                d = json.loads(l)
                per[(d["r"], d["c"])] = d
    assert set(per) == {(r, c) for r, c, _ in pick}, "sample incomplete"
    hist = np.zeros(256, np.int64)
    for k in per:
        hist += np.array(per[k]["hist"], np.int64)
    n = len(pick)
    t_mid, t_hi = q_hist(hist, 0.5), q_hist(hist, 0.999)
    msha = {f: hashlib.sha256(open(os.path.join(a.mesh_dir, f), "rb").read()).hexdigest()
            for f in ("meta.json", "x.tif", "y.tif", "z.tif")}
    out = {"provenance": PROV, "declaration": "RULES.md DECL-P4-12 item 1 / DECL-P4-6 item 2",
           "computed_utc": utc(), "computed_before": "any E2 (w010-027) tile pixel",
           "material": f"s3://vesuvius-challenge-open-data/{sv_key(CTL)}", "level": LEVEL,
           "level0_zarray_sha256": za_sha, "level0_shape": za["shape"],
           "mesh": f"PHercParis4/segments/{CTL}/mesh/{CTL.split('-')[0]}-on-20260411134726-2.4um.tifxyz",
           "mesh_sha256": msha, "slab_slices_inclusive": [Z0, Z1 - 1],
           "grid": {"T": T, "origin": [0, 0], "n_rows": nr, "n_cols": nc, "n_eligible": len(el)},
           "sample": {"seed": SEED, "fraction": SAMPLE_FRAC, "n": n, "fraction_of_eligible": n / len(el),
                      "tiles": [[r, c] for r, c, _ in pick]},
           "n_voxels": int(hist.sum()), "frac_voxels_zero": float(hist[0] / hist.sum()),
           "T_mid": t_mid, "T_hi": t_hi,
           "quantile_rule": "inverted CDF on the exact uint8 histogram (smallest v with CDF(v) >= q)",
           "other_quantiles": {str(q): q_hist(hist, q) for q in (0.01, 0.1, 0.25, 0.75, 0.9, 0.99, 0.999, 0.9999)},
           "mean": float((np.arange(256) * hist).sum() / hist.sum()),
           "histogram": hist.tolist(),
           "per_tile": [{k: v for k, v in per[(r, c)].items() if k != "hist"} for r, c, _ in pick],
           "note": "params.json's abbreviation 'sha256 x da81..' names the control meta.json hash; the full mesh hashes are mesh_sha256 here"}
    json.dump(out, open(os.path.join(a.out, "thresholds.json"), "w"), indent=1)
    print("T_mid", t_mid, "T_hi", t_hi, "tiles", n, "of", len(el), "frac0", out["frac_voxels_zero"], flush=True)


def png_chunks(b):
    names, p = [], 8
    while p < len(b):
        n = int.from_bytes(b[p:p + 4], "big")
        names.append(b[p + 4:p + 8].decode("latin1"))
        crc = int.from_bytes(b[p + 8 + n:p + 12 + n], "big")
        assert crc == zlib.crc32(b[p + 4:p + 8 + n]) & 0xFFFFFFFF
        p += 12 + n
    return names


def order_tiles(eligible):
    """r0 and r1 first (DECL-P4-12 item 5), then rows 2.. ; within a row by column."""
    return sorted(eligible, key=lambda rc: (0 if rc[0] <= 1 else 1, rc[0], rc[1]))


def cmd_tiles(a):
    import cv2
    from hercules.display import builder
    th = json.load(open(a.thresholds))
    t_mid, t_hi = int(th["T_mid"]), int(th["T_hi"])
    assert t_hi > t_mid
    za, _ = zarray(SEG)
    H0, W0 = za["shape"][1:]
    assert (H0, W0) == (69760, 170000)
    valid = load_valid(a.mesh_dir)
    assert valid.shape == (H0 // 20, W0 // 20)
    ref = json.load(open(a.ref_manifest))
    ref_t = {(t["r"], t["c"]): t for t in ref["tiles"]}
    tiles = order_tiles(list(ref_t))
    if a.only:
        only = {tuple(int(v) for v in s.split(",")) for s in a.only.split(";")}
        tiles = [t for t in tiles if t in only]
    tiles = tiles[a.worker::a.nworkers]
    tdir = os.path.join(a.out, "tiles")
    os.makedirs(tdir, exist_ok=True)
    cen = os.path.join(a.out, "census_w%d.jsonl" % a.worker)
    done = set()
    if os.path.exists(cen):
        done = {(d["r"], d["c"]) for d in map(json.loads, open(cen))}
    ex = cf.ThreadPoolExecutor(a.threads)
    chunk_log = open(os.path.join(a.out, "chunks_w%d.jsonl" % a.worker), "a")
    for r, c in tiles:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
        m = canvas_mask(valid, H0, W0, y0, y1, x0, x1)
        vf = float(m.mean())
        assert vf == ref_t[(r, c)]["valid_fraction"] and int(m.sum()) == ref_t[(r, c)]["stats"]["valid_px"], (r, c)
        mx, hist, n_hi, recs = region(SEG, y0, y1, x0, x1, (H0, W0), m, ex, t_hi=t_hi)
        for cr in recs:
            chunk_log.write(json.dumps(dict(cr, tile=[r, c])) + "\n")
        chunk_log.flush()
        t1 = time.time()
        vals = mx[m]
        vh = np.bincount(vals, minlength=256)
        disp = display_from_max(mx, m, t_mid, t_hi)
        out = cv2.resize(disp, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
        assert out.shape == (OUT_SIDE, OUT_SIDE) and out.dtype == np.uint8
        b = builder.png_bytes(out)
        ch = png_chunks(b)
        assert set(ch) <= {"IHDR", "IDAT", "IEND"} and ch[0] == "IHDR" and ch[-1] == "IEND", ch
        assert b[16:24] == OUT_SIDE.to_bytes(4, "big") * 2 and b[24] == 8 and b[25] == 0
        fn = f"{SEG}_r{r}_c{c}.png"
        with open(os.path.join(tdir, fn), "wb") as fh:
            fh.write(b)
        rec = {"file": "tiles/" + fn, "r": r, "c": c, "png_sha256": hashlib.sha256(b).hexdigest(),
               "png_bytes": len(b), "png_chunks": sorted(set(ch)), "valid_fraction": vf,
               "canvas_rows": [y0, y1], "canvas_cols": [x0, x1], "level": LEVEL,
               "stats": {"domain": "slab max (slices %d..%d, level 0) at mesh-valid canvas px" % (Z0, Z1 - 1),
                         "valid_px": int(vals.size), "max_mean": float(vals.mean()), "max_std": float(vals.std()),
                         **{"max_p%s" % q: q_hist(vh, float(q) / 100) for q in ("1", "50", "99", "99.9")},
                         "max_min": int(vals.min()), "max_max": int(vals.max()),
                         "frac_valid_max_gt_T_hi": float((vals > t_hi).mean()),
                         "frac_valid_max_le_T_mid": float((vals <= t_mid).mean()),
                         "frac_valid_max_zero": float((vals == 0).mean()),
                         "vox_median": q_hist(hist, 0.5), "vox_p99.9": q_hist(hist, 0.999),
                         "n_vox": int(hist.sum()), "n_hi": n_hi,
                         "frac_out_zero": float((out == 0).mean()), "frac_out_255": float((out == 255).mean()),
                         "out_mean": float(out.mean())},
               "chunks_read": sum(cr["status"] == 206 for cr in recs),
               "chunks_missing": sum(cr["status"] == 404 for cr in recs),
               "read_s": round(t1 - t0, 1), "compute_s": round(time.time() - t1, 1), "utc": utc()}
        with open(cen, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("tile r%d c%d %.1fs" % (r, c, time.time() - t0), flush=True)
        del mx, disp, out
    ex.shutdown()
    print("WORKER_DONE", a.worker, utc(), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for nm in ("thresholds", "thresholds-merge"):
        p = sp.add_parser(nm)
        p.add_argument("mesh_dir")
        p.add_argument("out")
        p.add_argument("--worker", type=int, default=0)
        p.add_argument("--nworkers", type=int, default=1)
        p.add_argument("--threads", type=int, default=16)
    p = sp.add_parser("tiles")
    p.add_argument("mesh_dir")
    p.add_argument("out")
    p.add_argument("thresholds")
    p.add_argument("--ref-manifest", required=True)
    p.add_argument("--worker", type=int, default=0)
    p.add_argument("--nworkers", type=int, default=1)
    p.add_argument("--threads", type=int, default=16)
    p.add_argument("--only", default="")
    a = ap.parse_args()
    {"thresholds": cmd_thresholds, "thresholds-merge": cmd_thresholds_merge, "tiles": cmd_tiles}[a.cmd](a)


if __name__ == "__main__":
    main()
