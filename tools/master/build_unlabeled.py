# Provenance: Project HERCULES | [id removed]
"""Unlabelled stacks for SSL from an organizer surface volume (any scroll at the target scan setting).
usage: build_unlabeled.py <scroll> <segment> <sv_name> <out.npz> [--stride 64 --max 800]"""
import argparse, json, numpy as np, zarr, s3fs
B = 'vesuvius-challenge-open-data'
ap = argparse.ArgumentParser(); ap.add_argument('scroll'); ap.add_argument('segment'); ap.add_argument('sv'); ap.add_argument('out'); ap.add_argument('--stride', type=int, default=64); ap.add_argument('--max', type=int, default=800); ap.add_argument('--size', type=int, default=64)
a = ap.parse_args(); fs = s3fs.S3FileSystem(anon=True)
sv = zarr.open(zarr.storage.FSStore(f's3://{B}/{a.scroll}/segments/{a.segment}/surface-volumes/{a.sv}/0', fs=fs, mode='r'), mode='r'); stack = np.asarray(sv[:]); D, H, W = stack.shape; S = a.size
valid = stack[D // 2] > 0; cand = [(y, x) for y in range(0, H - S + 1, a.stride) for x in range(0, W - S + 1, a.stride) if valid[y:y + S, x:x + S].mean() >= 0.9]
rng = np.random.default_rng(0); rng.shuffle(cand); sel = cand[:a.max]
X = np.stack([stack[:, y:y + S, x:x + S] for y, x in sel]).astype(np.uint8); Y = np.zeros((len(sel), S, S), np.uint8)
np.savez_compressed(a.out, x=X, y=Y, pos=np.array(sel), meta=json.dumps({'scroll': a.scroll, 'segment': a.segment, 'sv': a.sv, 'unlabelled': True})); print('wrote', a.out, X.shape)
