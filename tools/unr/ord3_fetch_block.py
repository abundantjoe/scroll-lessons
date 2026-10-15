#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-2 item 2a / V11: fetch the raw level-0 block for pilot B into a (Y, Z, X) uint8 memmap in /dev/shm, chunk-aligned, counting
the chunks present (missing chunks are zeros = void), with `free -m` before the fetch, bytes and seconds written to <out_dir>/fetch.json.
usage: ord3_fetch_block.py <config.json> <out_dir> --y 5632 6016 --z 5632 7040 --x 2688 5248 [--min_free_mb 6000] [--threads 32]"""
import os, sys, json, time, argparse, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'master')); from e2e_sheet import Zarr0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('config'); ap.add_argument('out'); ap.add_argument('--y', type=int, nargs=2, required=True); ap.add_argument('--z', type=int, nargs=2, required=True); ap.add_argument('--x', type=int, nargs=2, required=True); ap.add_argument('--min_free_mb', type=int, default=6000); ap.add_argument('--threads', type=int, default=32)
    a = ap.parse_args(); cfg = json.load(open(a.config)); os.makedirs(a.out, exist_ok=True); (y0, y1), (z0, z1), (x0, x1) = a.y, a.z, a.x
    free = subprocess.run(['free', '-m'], capture_output=True, text=True).stdout.split('\n')[1]; avail = int(free.split()[-1])
    while avail < a.min_free_mb: print('waiting for memory: available', avail, 'MB', flush=True); time.sleep(60); free = subprocess.run(['free', '-m'], capture_output=True, text=True).stdout.split('\n')[1]; avail = int(free.split()[-1])
    ct = Zarr0(cfg['ct_l0'], a.threads); cz, cy, cx = ct.chunks; t0 = time.time(); Y, Z, X = y1 - y0, z1 - z0, x1 - x0
    blk = np.lib.format.open_memmap(os.path.join(a.out, 'block.npy'), mode='w+', dtype=np.uint8, shape=(Y, Z, X)); n_keys = 0; n_missing = 0; nbytes = 0
    for j in range(y0 // cy, (y1 - 1) // cy + 1):                                                                   # one chunk row of y at a time (3 rows for the declared block)
        keys = [(i, j, k) for i in range(z0 // cz, (z1 - 1) // cz + 1) for k in range(x0 // cx, (x1 - 1) // cx + 1)]; ys, ye = max(y0, j * cy), min(y1, (j + 1) * cy)
        for (i, jj, k), arr in ct.ex.map(ct.chunk, keys):
            n_keys += 1
            if arr is None: n_missing += 1; continue
            nbytes += arr.nbytes; zs, ze = max(z0, i * cz), min(z1, (i + 1) * cz); xs, xe = max(x0, k * cx), min(x1, (k + 1) * cx)
            sub = arr[zs - i * cz:ze - i * cz, ys - j * cy:ye - j * cy, xs - k * cx:xe - k * cx]                  # (z, y, x) -> (y, z, x)
            blk[ys - y0:ye - y0, zs - z0:ze - z0, xs - x0:xe - x0] = np.transpose(sub, (1, 0, 2))
        print('chunk row', j, 'done', round(time.time() - t0, 1), 's', flush=True)
    blk.flush(); secs = time.time() - t0; frac_nonzero = float((np.asarray(blk[Y // 2]) > 0).mean())
    rec = {'declaration': 'DECL-E2E-2 item 2a', 'key': cfg['ct_l0'], 'y': [y0, y1], 'z': [z0, z1], 'x': [x0, x1], 'shape_yzx': [Y, Z, X], 'chunks': [cz, cy, cx], 'n_chunks': n_keys, 'n_missing': n_missing, 'present_frac': round(1 - n_missing / max(1, n_keys), 4), 'bytes_fetched': nbytes, 'MB_per_s': round(nbytes / 1e6 / max(secs, 1e-6), 1), 'secs': round(secs, 1), 'free_before': free, 'nonzero_frac_mid_section': round(frac_nonzero, 4), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    json.dump(rec, open(os.path.join(a.out, 'fetch.json'), 'w'), indent=1); print(json.dumps(rec))

if __name__ == '__main__': main()
