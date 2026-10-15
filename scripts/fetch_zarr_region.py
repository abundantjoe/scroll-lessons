#!/usr/bin/env python3
"""Mirror a rectangular (y, x) region of an OME-zarr v2 level from S3 into a local
zarr directory with identical layout (uncompressed chunks are copied byte for byte).
Idempotent: existing chunk files of the right size are skipped; a '.done' marker is
written per region. Missing keys (404) are recorded as absent = fill_value.

usage: fetch_zarr_region.py <base_url_of_store> <level> <y0> <y1> <x0> <x1> <local_store> [--workers N]
Region bounds are in level pixels; whole chunks that intersect the region are fetched.
"""
import sys, os, json, argparse, concurrent.futures as cf, time, urllib.request, urllib.error

def get(url, retries=6):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(f"failed {url}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("level", type=int)
    ap.add_argument("y0", type=int); ap.add_argument("y1", type=int)
    ap.add_argument("x0", type=int); ap.add_argument("x1", type=int)
    ap.add_argument("local"); ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    base = a.base.rstrip("/")
    os.makedirs(os.path.join(a.local, str(a.level)), exist_ok=True)
    for f in [".zattrs", ".zgroup"]:
        p = os.path.join(a.local, f)
        if not os.path.exists(p):
            b = get(f"{base}/{f}")
            if b: open(p, "wb").write(b)
    zp = os.path.join(a.local, str(a.level), ".zarray")
    if not os.path.exists(zp):
        b = get(f"{base}/{a.level}/.zarray"); assert b, "no .zarray"; open(zp, "wb").write(b)
    za = json.load(open(zp))
    assert za["compressor"] is None and za["dimension_separator"] == "/", za
    cz, cy, cx = za["chunks"]; sz, sy, sx = za["shape"]
    nbytes = cz * cy * cx  # uint8
    marker = os.path.join(a.local, str(a.level), f".done_{a.y0}_{a.y1}_{a.x0}_{a.x1}")
    jobs = []
    for zc in range((sz + cz - 1) // cz):
        for yc in range(a.y0 // cy, min((a.y1 - 1) // cy + 1, (sy + cy - 1) // cy)):
            for xc in range(a.x0 // cx, min((a.x1 - 1) // cx + 1, (sx + cx - 1) // cx)):
                jobs.append((zc, yc, xc))
    if os.path.exists(marker):
        missing = [j for j in jobs if not (os.path.exists(os.path.join(a.local, str(a.level), str(j[0]), str(j[1]), str(j[2]))) or os.path.exists(os.path.join(a.local, str(a.level), str(j[0]), str(j[1]), str(j[2]) + ".absent")))]
        if not missing: print("already done", marker); return
        print(f"marker present but {len(missing)} chunks missing: refetching", flush=True)
    def work(j):
        zc, yc, xc = j
        d = os.path.join(a.local, str(a.level), str(zc), str(yc))
        p = os.path.join(d, str(xc))
        if os.path.exists(p) and os.path.getsize(p) == nbytes: return 0
        if os.path.exists(p + ".absent"): return 0
        b = get(f"{base}/{a.level}/{zc}/{yc}/{xc}")
        os.makedirs(d, exist_ok=True)
        if b is None:
            open(p + ".absent", "w").close(); return 0
        tmp = p + ".part"; open(tmp, "wb").write(b); os.replace(tmp, p); return len(b)
    t0 = time.time(); tot = 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for i, n in enumerate(ex.map(work, jobs)):
            tot += n
            if i % 500 == 0: print(f"{i}/{len(jobs)} chunks, {tot/1e6:.0f} MB, {time.time()-t0:.0f}s", flush=True)
    open(marker, "w").write(json.dumps({"chunks": len(jobs), "bytes": tot, "seconds": time.time() - t0}))
    print(f"done {len(jobs)} chunks {tot/1e9:.2f} GB in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
