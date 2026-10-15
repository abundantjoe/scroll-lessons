"""P4-E material E2 (RULES.md DECL-P4-5): raw-CT slab-mean tiles of 20260701183124-w010-027 on the P4-B strip-a grid.

Provenance: Project HERCULES | owner the owner | [id removed]

Builder only: never opens, views or prints image pixels. Writes numbers, hashes and PNG bytes only.

Material: the official surface volume
  PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
(109 slices, centre slice 54 = mesh surface). Level 0 is (109, 69760, 170000) = the strip-a 2.4 um render canvas,
so canvas px (i, j) = level-0 (row i, col j). The job reads multiscale level 2. Its in-plane pixel is 9.6 um
(<= 18.7 um); it is the mean of 4 x 4 level-0 px, so canvas px (i, j) lies in level-2 px (i // 4, j // 4). Depth is
not downsampled, and z stays 2.4 um per slice at every level. Slab = slices 32..76 (54 +- 22, 45 slices, +-52.8 um).
Chunks are uncompressed C-order (109, 128, 128) u8, so each chunk is read by one HTTP range request of the 45
contiguous slices. A missing chunk (404) is fill 0.

Per tile, the grid, mask and downscale are identical to P4-B strip a (logs/sib/p4-tiles-a at e25635c):
T = 8343 canvas px from (0, 0), 9 x 21 tiles, mesh-valid by the strip-a canvas_mask rule, eligible if >= 50 % valid.
1. The slab mean on the canvas is the level-2 slab mean at (i // 4, j // 4), i.e. a nearest parent lookup, no
   interpolation.
2. A linear 1-99 % stretch over the tile's mesh-valid canvas px (hercules.display.builder.linear_window_ct), then 0
   outside mesh-valid.
3. cv2.INTER_AREA 8343 -> 1068, then a uint8 PNG with IHDR/IDAT/IEND only (builder.png_bytes).

Usage: e2_tiles.py <mesh_dir> <out_dir> [--level 2] [--only r,c] [--tag name]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time
import zlib

import cv2
import numpy as np
import requests
import tifffile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from hercules.display import builder  # noqa: E402

PROV = "Project HERCULES | owner the owner | [id removed]"
SEG = "20260701183124-w010-027"
HTTP = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SV = f"PHercParis4/segments/{SEG}/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
NZ, CH = 109, 128
CENTRE, HALF = 54, 22  # slices 32..76
Z0, Z1 = CENTRE - HALF, CENTRE + HALF + 1
T, NR, NC, OUT_SIDE, ELIG = 8343, 9, 21, 1068, 0.5
H0, W0 = 69760, 170000

_s = requests.Session()
_s.mount("https://", requests.adapters.HTTPAdapter(pool_connections=48, pool_maxsize=48, max_retries=3))


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canvas_mask(valid, H, W, y0, y1, x0, x1):
    """Verbatim rule of tools/sib/p4-tiles-a/tile_w010_027.py (e25635c)."""
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


def get_chunk(level, cy, cx):
    """Slab mean (float32 128 x 128) of slices Z0..Z1-1 of chunk (0, cy, cx); returns (mean, record)."""
    key = f"{SV}/{level}/0/{cy}/{cx}"
    a, b = Z0 * CH * CH, Z1 * CH * CH - 1
    for i in range(6):
        try:
            r = _s.get(f"{HTTP}/{key}", headers={"Range": f"bytes={a}-{b}"}, timeout=60)
            if r.status_code == 404:
                return None, {"k": f"{level}/0/{cy}/{cx}", "status": 404}
            if r.status_code == 206 and len(r.content) == b - a + 1:
                d = np.frombuffer(r.content, np.uint8).reshape(Z1 - Z0, CH, CH)
                return d.mean(axis=0, dtype=np.float64).astype(np.float32), {
                    "k": f"{level}/0/{cy}/{cx}", "status": 206, "range": [a, b],
                    "sha256": hashlib.sha256(r.content).hexdigest()}
        except requests.RequestException:
            pass
        time.sleep(2 ** i)
    raise RuntimeError(f"chunk read failed: {key}")


def slab_region(level, f, ly0, ly1, lx0, lx1, shape, ex):
    """Level-`level` slab mean over rows [ly0,ly1), cols [lx0,lx1); outside the array = 0."""
    out = np.zeros((ly1 - ly0, lx1 - lx0), np.float32)
    H, W = shape
    jobs = [(cy, cx) for cy in range(max(ly0, 0) // CH, (min(ly1, H) - 1) // CH + 1)
            for cx in range(max(lx0, 0) // CH, (min(lx1, W) - 1) // CH + 1)]
    recs = []
    for (cy, cx), (m, rec) in zip(jobs, ex.map(lambda j: get_chunk(level, *j), jobs)):
        recs.append(rec)
        if m is None:
            continue
        ya, yb = max(cy * CH, ly0), min(cy * CH + CH, ly1, H)
        xa, xb = max(cx * CH, lx0), min(cx * CH + CH, lx1, W)
        out[ya - ly0:yb - ly0, xa - lx0:xb - lx0] = m[ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH]
    return out, recs


def png_chunks(b):
    names, p = [], 8
    while p < len(b):
        n = int.from_bytes(b[p:p + 4], "big")
        names.append(b[p + 4:p + 8].decode("latin1"))
        crc = int.from_bytes(b[p + 8 + n:p + 12 + n], "big")
        assert crc == zlib.crc32(b[p + 4:p + 8 + n]) & 0xFFFFFFFF
        p += 12 + n
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh_dir")
    ap.add_argument("out")
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    f = 2 ** a.level
    za = requests.get(f"{HTTP}/{SV}/{a.level}/.zarray", timeout=60).json()
    assert za["shape"][0] == NZ and za["chunks"] == [NZ, CH, CH] and za["dtype"] == "|u1" and za["compressor"] is None \
        and za["order"] == "C" and za.get("dimension_separator") == "/", za
    LH, LW = za["shape"][1:]
    assert (LH, LW) == (-(-H0 // f), -(-W0 // f)), (LH, LW)

    P = np.stack([tifffile.imread(os.path.join(a.mesh_dir, n)) for n in ("x.tif", "y.tif", "z.tif")], -1)
    valid = ~((P[..., 0] == -1) | (P[..., 1] == -1) | (P[..., 2] == -1))
    valid &= np.isfinite(P).all(-1)
    del P
    assert valid.shape == (H0 // 20, W0 // 20), valid.shape

    tdir = os.path.join(a.out, "tiles")
    os.makedirs(tdir, exist_ok=True)
    cen = os.path.join(a.out, f"census{a.tag}.jsonl")
    done = set()
    if os.path.exists(cen):
        done = {(d["r"], d["c"]) for d in map(json.loads, open(cen))}
    only = None
    if a.only:
        only = {tuple(int(v) for v in s.split(",")) for s in a.only.split(";")}
    ex = cf.ThreadPoolExecutor(32)
    chunk_log = open(os.path.join(a.out, f"chunks{a.tag}.jsonl"), "a")
    for r in range(NR):
        for c in range(NC):
            if (r, c) in done or (only is not None and (r, c) not in only):
                continue
            t0 = time.time()
            y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
            m = canvas_mask(valid, H0, W0, y0, y1, x0, x1)
            vf = float(m.mean())
            rec = {"r": r, "c": c, "valid_fraction": vf, "eligible": vf >= ELIG, "canvas_rows": [y0, y1],
                   "canvas_cols": [x0, x1], "level": a.level}
            if rec["eligible"]:
                ly0, ly1, lx0, lx1 = y0 // f, (y1 - 1) // f + 1, x0 // f, (x1 - 1) // f + 1
                L, recs = slab_region(a.level, f, ly0, ly1, lx0, lx1, (LH, LW), ex)
                for cr in recs:
                    chunk_log.write(json.dumps(dict(cr, tile=[r, c])) + "\n")
                chunk_log.flush()
                iy = np.arange(y0, y1) // f - ly0
                ix = np.arange(x0, x1) // f - lx0
                inside = (np.arange(y0, y1) < H0)[:, None] & (np.arange(x0, x1) < W0)[None, :]
                img = L[np.ix_(iy, ix)]
                img[~inside] = 0
                t1 = time.time()
                vals = img[m]
                disp, (lo, hi) = builder.linear_window_ct(img, valid=m)
                disp[~m] = 0
                out = cv2.resize(disp, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
                assert out.shape == (OUT_SIDE, OUT_SIDE) and out.dtype == np.uint8
                b = builder.png_bytes(out)
                ch = png_chunks(b)
                assert set(ch) <= {"IHDR", "IDAT", "IEND"} and ch[0] == "IHDR" and ch[-1] == "IEND", ch
                assert b[16:24] == OUT_SIDE.to_bytes(4, "big") * 2 and b[24] == 8 and b[25] == 0
                fn = f"{SEG}_r{r}_c{c}{a.tag}.png"
                with open(os.path.join(tdir, fn), "wb") as fh:
                    fh.write(b)
                rec.update({
                    "file": "tiles/" + fn, "png_sha256": hashlib.sha256(b).hexdigest(), "png_bytes": len(b),
                    "png_chunks": sorted(set(ch)),
                    "stats": {"domain": "slab mean (slices 32..76, level %d) at mesh-valid canvas px, before stretch" % a.level,
                              "valid_px": int(vals.size), "mean": float(vals.mean()), "std": float(vals.std()),
                              "p1": lo, "p99": hi, "min": float(vals.min()), "max": float(vals.max()),
                              "frac_zero_in_valid": float((vals == 0).mean()),
                              "frac_nonzero_outside_valid": float((img[~m] > 0).mean()) if (~m).any() else 0.0,
                              "frac_out_zero": float((out == 0).mean()), "out_mean": float(out.mean())},
                    "chunks_read": sum(cr["status"] == 206 for cr in recs),
                    "chunks_missing": sum(cr["status"] == 404 for cr in recs),
                    "read_s": round(t1 - t0, 1), "compute_s": round(time.time() - t1, 1)})
                del img, disp, L
            rec["seconds"] = round(time.time() - t0, 1)
            rec["utc"] = utc()
            with open(cen, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            if rec["eligible"]:
                print("tile r%d c%d vf=%.3f %.1fs" % (r, c, vf, rec["seconds"]), flush=True)
    ex.shutdown()
    print("ALL_DONE", utc(), flush=True)


if __name__ == "__main__":
    main()
