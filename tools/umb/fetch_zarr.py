#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Threaded fetch of one zarr-v2 array (one OME level) from the open-data bucket into a local .npy, chunk by chunk (the
agent proxy is request-bound: ~70 req/s with 32 threads vs ~2 req/s sequential). Optional z-range. Reads .zarray for the
shape/chunks/compressor and decodes with numcodecs. usage: fetch_zarr.py <s3 key of the level dir> <out.npy> [--z0 A --z1 B] [--threads 32]
"""
import argparse, json, numpy as np, s3fs, time
from concurrent.futures import ThreadPoolExecutor
from numcodecs import get_codec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('key'); ap.add_argument('out'); ap.add_argument('--z0', type=int, default=0); ap.add_argument('--z1', type=int, default=-1); ap.add_argument('--threads', type=int, default=32)
    a = ap.parse_args(); fs = s3fs.S3FileSystem(anon=True); key = a.key.rstrip('/'); za = json.loads(fs.cat_file(key + '/.zarray')); t0 = time.time()
    shape, chunks, dtype = za['shape'], za['chunks'], np.dtype(za['dtype']); comp = get_codec(za['compressor']) if za.get('compressor') else None; sep = za.get('dimension_separator', '.')
    order = za.get('order', 'C'); fill = za.get('fill_value', 0) or 0; z1 = shape[0] if a.z1 < 0 else min(a.z1, shape[0]); z0 = a.z0
    out = np.full((z1 - z0, shape[1], shape[2]), fill, dtype); cz, cy, cx = chunks
    keys = [(i, j, k) for i in range(z0 // cz, (z1 - 1) // cz + 1) for j in range((shape[1] - 1) // cy + 1) for k in range((shape[2] - 1) // cx + 1)]
    def get(ijk):
        i, j, k = ijk
        try: raw = fs.cat_file(f'{key}/{i}{sep}{j}{sep}{k}')
        except FileNotFoundError: return ijk, None
        arr = np.frombuffer(comp.decode(raw) if comp else raw, dtype).reshape(chunks, order=order); return ijk, arr
    n = 0
    with ThreadPoolExecutor(a.threads) as ex:
        for (i, j, k), arr in ex.map(get, keys):
            n += 1
            if arr is None: continue
            zs, ze = max(i * cz, z0), min((i + 1) * cz, z1); ys, ye = j * cy, min((j + 1) * cy, shape[1]); xs, xe = k * cx, min((k + 1) * cx, shape[2])
            out[zs - z0:ze - z0, ys:ye, xs:xe] = arr[zs - i * cz:ze - i * cz, :ye - ys, :xe - xs]
            if n % 2000 == 0: print(f'{n}/{len(keys)} chunks {time.time()-t0:.0f}s', flush=True)
    np.save(a.out, out); print('saved', a.out, out.shape, out.dtype, f'{time.time()-t0:.0f}s', 'nonzero', round(float((out != 0).mean()), 4), flush=True)

if __name__ == '__main__': main()
