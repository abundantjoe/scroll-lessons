"""DECL-P4-13 P4-M item 1: column profile of a strip canvas at 1 mm bins (numbers only).

Provenance: Project HERCULES | owner the owner | [id removed]
Never displays or describes pixels; it only accumulates sums and counts.

For every 1 mm bin along the canvas column axis (bin b = canvas cols [b*PX, (b+1)*PX), PX = px_per_mm of the
strip's grid.json) and every 1 mm bin along the canvas row axis, it accumulates over mesh-valid canvas pixels:
  sum of the channel value, and count of mesh-valid pixels.
Mesh-valid = p4-tiles-a/b canvas_mask rule (grid vertex valid at (i//20, j//20)).
Channels:
  m1  - the official 2.4 um ink prediction TIFF (uint8), read tile by tile.
  e2  - the surface-volume slab mean (DECL-P4-5 slab, slices 32..76) from the surface-volume zarr at level 4
        (38.4 um in-plane, mean-downsampled; depth not downsampled), streamed by HTTP range reads of the slab.
The 2-D (row-bin x col-bin) sums stay in the scratch output (npz). The committed JSON carries 1-D profiles only:
per tile row r (T-px bands) and all rows, per column bin, plus a row-bin profile restricted to chosen tile columns.
Usage:
  python col_profile.py m1 <pred.tif> <meshdir> <grid.json> <out.npz>
  python col_profile.py e2 <surface-volume zarr url> <meshdir> <grid.json> <out.npz> <manifest.jsonl>
"""
import json, sys, time, hashlib, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np, tifffile


def mesh_valid(md):
    xs = [tifffile.imread(f"{md}/mesh_{a}.tif") for a in "xyz"]
    v = np.ones(xs[0].shape, bool)
    for x in xs:
        v &= (x != -1) & np.isfinite(x)
    return v


def binner(H, W, px):
    nrb, ncb = int(np.ceil(H / px)), int(np.ceil(W / px))
    return nrb, ncb


def m1(pred, md, gj, out):
    t0 = time.time()
    g = json.load(open(gj))
    px = g["px_per_mm"]
    valid = mesh_valid(md)
    tf = tifffile.TiffFile(pred)
    p = tf.pages[0]
    H, W = p.shape
    th, tw = p.tilelength, p.tilewidth
    ntx, nty = -(-W // tw), -(-H // th)
    nrb, ncb = binner(H, W, px)
    S = np.zeros((nrb, ncb), np.float64)
    N = np.zeros((nrb, ncb), np.int64)
    fh = tf.filehandle
    for ty in range(nty):
        for tx in range(ntx):
            idx = ty * ntx + tx
            if p.databytecounts[idx] == 0:
                continue
            fh.seek(p.dataoffsets[idx])
            seg, _, _ = p.decode(fh.read(p.databytecounts[idx]), idx)
            seg = np.asarray(seg).reshape(th, tw)
            y0, x0 = ty * th, tx * tw
            y1, x1 = min(y0 + th, H), min(x0 + tw, W)
            seg = seg[: y1 - y0, : x1 - x0]
            ys, xs = np.arange(y0, y1), np.arange(x0, x1)
            m = valid[np.ix_(ys // 20, xs // 20)]
            rb = (ys / px).astype(int)
            cb = (xs / px).astype(int)
            # sum per (rb, cb) via bincount on flattened bin ids
            ids = (rb[:, None] * ncb + cb[None, :])[m]
            S.flat[:] += np.bincount(ids, weights=seg[m].astype(np.float64), minlength=nrb * ncb)
            N.flat[:] += np.bincount(ids, minlength=nrb * ncb)
        print("row", ty, "/", nty, "%.0fs" % (time.time() - t0), flush=True)
    np.savez_compressed(out, S=S, N=N, px_per_mm=px, H=H, W=W, T=g.get("T_canvas_px", g.get("T_px")))
    print("done", time.time() - t0)


def e2(url, md, gj, out, man, L=4, s0=32, s1=77):
    t0 = time.time()
    g = json.load(open(gj))
    px = g["px_per_mm"]
    valid = mesh_valid(md)
    za = json.loads(urllib.request.urlopen(f"{url}/{L}/.zarray").read())
    D, h, w = za["shape"]
    cd, ch, cw = za["chunks"]
    assert za["compressor"] is None and cd == D and za["dtype"] == "|u1", za
    f = 2 ** L
    H, W = g["canvas_shape"]
    nrb, ncb = binner(H, W, px)
    S = np.zeros((nrb, ncb), np.float64)
    N = np.zeros((nrb, ncb), np.int64)
    mf = open(man, "a")
    per = ch * cw
    rng = (s0 * per, s1 * per - 1)

    def get(k):
        y, x = k
        req = urllib.request.Request(f"{url}/{L}/0/{y}/{x}", headers={"Range": "bytes=%d-%d" % rng})
        for i in range(5):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    b = r.read()
                return k, 206, b
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return k, 404, b""
                time.sleep(2 ** i)
            except Exception:
                time.sleep(2 ** i)
        raise RuntimeError(k)
    keys = [(y, x) for y in range(-(-h // ch)) for x in range(-(-w // cw))]
    with ThreadPoolExecutor(32) as ex:
        for k, st, b in ex.map(get, keys):
            mf.write(json.dumps({"k": f"{L}/0/{k[0]}/{k[1]}", "status": st, "range": list(rng),
                                 "sha256": hashlib.sha256(b).hexdigest() if b else None}) + "\n")
            if st != 206:
                continue
            a = np.frombuffer(b, np.uint8).reshape(s1 - s0, ch, cw).astype(np.float32).mean(0)
            y0, x0 = k[0] * ch, k[1] * cw
            y1, x1 = min(y0 + ch, h), min(x0 + cw, w)
            a = a[: y1 - y0, : x1 - x0]
            # level-L pixel centre in canvas px
            yc = (np.arange(y0, y1) + 0.5) * f
            xc = (np.arange(x0, x1) + 0.5) * f
            gi = np.clip((yc // 20).astype(int), 0, valid.shape[0] - 1)
            gjx = np.clip((xc // 20).astype(int), 0, valid.shape[1] - 1)
            m = valid[np.ix_(gi, gjx)] & (a > 0)
            rb = np.minimum((yc / px).astype(int), nrb - 1)
            cb = np.minimum((xc / px).astype(int), ncb - 1)
            ids = (rb[:, None] * ncb + cb[None, :])[m]
            S.flat[:] += np.bincount(ids, weights=a[m].astype(np.float64), minlength=nrb * ncb)
            N.flat[:] += np.bincount(ids, minlength=nrb * ncb)
    np.savez_compressed(out, S=S, N=N, px_per_mm=px, H=H, W=W, T=g["T_canvas_px"], level=L, slab=[s0, s1 - 1])
    print("done", time.time() - t0)


if __name__ == "__main__":
    {"m1": m1, "e2": e2}[sys.argv[1]](*sys.argv[2:])
