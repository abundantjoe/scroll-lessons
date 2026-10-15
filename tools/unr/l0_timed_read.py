#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UNR-1 W12: one timed level-0 (8.64 um) window read on the reference scroll with class L0.slab of
tools/umb/core_native.py: a 16-section y-slab, `--w_mm` wide in x and `--h_mm` tall in z (default 24 x 90 mm, the
DECL-UNR-1 edge-window geometry), centred in the volume unless --x0/--z0/--y0 are given; y0 snaps to a chunk boundary so
the slab touches one chunk row in y (the minimum read: every touched 128^3 chunk is fetched whole, 16 sections kept).
Records bytes fetched (chunks x chunk bytes), resident bytes, seconds, chunks present/absent, `free -m` before and
after, and the slab's nonzero fraction. usage: l0_timed_read.py <s3 key of level 0> <out.json> [--w_mm 24 --h_mm 90]
"""
import argparse, json, os, subprocess, sys, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb')); from core_native import L0, VOX


def free_mb():
    try: return int(subprocess.run(['free', '-m'], capture_output=True, text=True).stdout.split('\n')[1].split()[6])
    except Exception: return -1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('key'); ap.add_argument('out'); ap.add_argument('--w_mm', type=float, default=24.0); ap.add_argument('--h_mm', type=float, default=90.0)
    ap.add_argument('--n', type=int, default=16); ap.add_argument('--x0', type=int, default=-1); ap.add_argument('--z0', type=int, default=-1); ap.add_argument('--y0', type=int, default=-1); ap.add_argument('--threads', type=int, default=32)
    a = ap.parse_args(); t0 = time.time(); L = L0(a.key, a.threads); Z, Y, X = L.shape; cz, cy, cx = L.chunks
    w, h = int(round(a.w_mm * 1000 / VOX)), int(round(a.h_mm * 1000 / VOX)); h = min(h, Z); w = min(w, X)
    x0 = a.x0 if a.x0 >= 0 else max(0, X // 2 - w // 2); z0 = a.z0 if a.z0 >= 0 else max(0, Z // 2 - h // 2); y0 = a.y0 if a.y0 >= 0 else (Y // 2 // cy) * cy
    fb = free_mb(); t1 = time.time(); slab, info = L.slab(y0, a.n, z0, z0 + h, x0, x0 + w); t2 = time.time(); fa = free_mb()
    rec = {'key': a.key, 'zarray': {'shape': L.shape, 'chunks': L.chunks, 'dimension_separator': L.sep}, 'window': {'y0': y0, 'n_sections': a.n, 'z0': z0, 'z1': z0 + h, 'x0': x0, 'x1': x0 + w, 'w_mm': round(w * VOX / 1000, 2), 'h_mm': round(h * VOX / 1000, 2)},
           'chunks_present': info['chunks'], 'chunks_touched': info['of'], 'bytes_fetched': int(info['chunks'] * cz * cy * cx), 'bytes_touched_if_all_present': int(info['of'] * cz * cy * cx),
           'resident_bytes': int(slab.nbytes), 'secs_slab': round(t2 - t1, 2), 'secs_total_incl_zarray': round(t2 - t0, 2), 'MB_per_s_fetched': round(info['chunks'] * cz * cy * cx / 1e6 / max(t2 - t1, 1e-6), 1),
           'free_mb_before': fb, 'free_mb_after': fa, 'nonzero_fraction': round(float((slab > 0).mean()), 4), 'slab_shape_n_z_x': list(slab.shape), 'threads': a.threads}
    json.dump(rec, open(a.out, 'w'), indent=1); print(json.dumps(rec, indent=1), flush=True)


if __name__ == '__main__': main()
