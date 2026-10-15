#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-O (RULES.md DECL-P4-14 item 2) tile builder for one scrollprize/PHerc.1667-iteration-N checkpoint on the Paris 4
strip-a grid. Numbers only: tiles are written as PNG files and summarised by hashes and scalar statistics; no tile is
opened, displayed or described.

Input   the official 2.4 um surface volume of 20260701183124-w010-027 (level 0, uncompressed (109, 128, 128) u8 chunks,
        centre slice 54 = mesh surface), read by HTTP range requests of 62 contiguous slices per chunk.
Grid    strip a, as in pairs0814b e2 (T = 8343 canvas px from (0, 0), 9 x 21 tiles; mesh-valid = strip-a canvas_mask rule
        on the official tifxyz; c0 = outer end). Canvas px (i, j) = level-0 (row i, col j).
Model   the card geometry: 62 layers at 2.4 um (the model's ~2 um class; no in-plane or depth resampling, since the volume
        is already at 2.4 um), slices 54-31 .. 54+30 = 23..84 (--order index keeps increasing slice index, reverse flips
        it), clip(0, 200)/255 (card training statement), loaded and tiled exactly as ckpt-screen-b infer_1667.py:
        AutoModel.from_pretrained(trust_remote_code) of the verified HF snapshot, the card's tiling loop (WINDOW 256,
        STRIDE 128, skip a window with any fmask 0, sigmoid, x4 bilinear, sum/count).
        The loop runs on the tile plus a 128 px margin so that every tile pixel can be covered.
Display raw prediction, uint8 = clip(pred * 255) (card), 0 outside mesh-valid, cv2.INTER_AREA 8343 -> 1068, PNG via the
        project builder (IHDR/IDAT/IEND only), named 20260701183124-w010-027_r{r}_c{c}.png.
Usage   p4o_tile.py --iteration N --mesh-dir DIR --out OUTDIR --tiles "r,c;r,c;..." [--order index|reverse]
                    [--threads 4] [--synthetic]   (--synthetic: random volume, no network; smoke only)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PROV = 'Project HERCULES | owner the owner | [id removed]'
SEG = '20260701183124-w010-027'
HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
SV = f'PHercParis4/segments/{SEG}/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr'
NZ, CH = 109, 128
CENTRE, D_MODEL = 54, 62
Z0, Z1 = CENTRE - 31, CENTRE + 31          # slices 23..84 (62)
T, NR, NC, OUT_SIDE, ELIG = 8343, 9, 21, 1068, 0.5
H0, W0 = 69760, 170000
MARGIN = 128
MESH_SHA = {'x.tif': 'c304cdfd975587864cfcb2147aff1db0ddc9f3240260204cce6b2891c9910165',
            'y.tif': '9a4eefdae0705ad0f0b59e79093bf48f63dad7760a1ce0be5030e408c8f94139',
            'z.tif': 'a06716afd74c973d80c8f9275737fe95d776edd25537ae3076b07deb46c034f8'}
ZARRAY0_SHA = '8ffed5fa6ffe9f68513c5dc4ddf09bd77192abcf7eb69eee1dfa2551773f916f'


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def load_b_wrapper():
    """ckpt-screen-b infer_1667.py (load_model, card_tiling), imported unchanged from a verified copy."""
    p = os.environ.get('CKC_B_WRAPPER', '/work/ckscr/p4o/infer_1667.py')
    want = '431067ee40ff5cb2b0b1303bdc80c218a4838f395320c94a1505b44b47bfd5f6'
    got = sha256(p)
    assert got == want, f'infer_1667.py sha256 {got} != {want}'
    spec = importlib.util.spec_from_file_location('infer_1667', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.REPO = REPO  # its catalogue path is repo-relative; the file itself is unchanged
    return m, got


def canvas_mask(valid, H, W, y0, y1, x0, x1):
    """Verbatim rule of tools/sib/p4-tiles-a/tile_w010_027.py (e25635c), as in pairs0814b e2_tiles.py."""
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


_session = None


def get_chunk(cy, cx):
    """Slices Z0..Z1-1 of level-0 chunk (0, cy, cx) as (62, 128, 128) u8; (None, rec) if absent (fill 0)."""
    import requests
    global _session
    if _session is None:
        _session = requests.Session()
        _session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=3))
    key = f'{SV}/0/0/{cy}/{cx}'
    a, b = Z0 * CH * CH, Z1 * CH * CH - 1
    for i in range(6):
        try:
            r = _session.get(f'{HTTP}/{key}', headers={'Range': f'bytes={a}-{b}'}, timeout=120)
            if r.status_code == 404:
                return None, {'k': f'0/0/{cy}/{cx}', 'status': 404}
            if r.status_code == 206 and len(r.content) == b - a + 1:
                d = np.frombuffer(r.content, np.uint8).reshape(Z1 - Z0, CH, CH)
                return d, {'k': f'0/0/{cy}/{cx}', 'status': 206, 'range': [a, b],
                           'sha256': hashlib.sha256(r.content).hexdigest()}
        except requests.RequestException:
            pass
        time.sleep(2 ** i)
    raise RuntimeError(f'chunk read failed: {key}')


def read_region(y0, y1, x0, x1, ex, synthetic=False):
    """(y1-y0, x1-x0, 62) u8 stack of level-0 slices 23..84; outside the array = 0."""
    out = np.zeros((y1 - y0, x1 - x0, Z1 - Z0), np.uint8)
    if synthetic:
        rng = np.random.default_rng(y0 * 7 + x0)
        out[:] = rng.integers(40, 160, out.shape, dtype=np.uint8)
        return out, []
    jobs = [(cy, cx) for cy in range(max(y0, 0) // CH, (min(y1, H0) - 1) // CH + 1)
            for cx in range(max(x0, 0) // CH, (min(x1, W0) - 1) // CH + 1)]
    recs = []
    for (cy, cx), (d, rec) in zip(jobs, ex.map(lambda j: get_chunk(*j), jobs)):
        recs.append(rec)
        if d is None:
            continue
        ya, yb = max(cy * CH, y0), min(cy * CH + CH, y1, H0)
        xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W0)
        out[ya - y0:yb - y0, xa - x0:xb - x0, :] = np.transpose(
            d[:, ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH], (1, 2, 0))
    return out, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iteration', type=int, required=True)
    ap.add_argument('--mesh-dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--tiles', required=True, help='"r,c;r,c;..."')
    ap.add_argument('--order', choices=['index', 'reverse'], default='index')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--synthetic', action='store_true')
    ap.add_argument('--region', type=int, default=0, help='smoke only: crop the tile to this many px')
    a = ap.parse_args()
    for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[k] = str(a.threads)
    import cv2
    import tifffile
    import torch
    torch.set_num_threads(a.threads)
    sys.path.insert(0, os.path.join(REPO, 'src'))
    from hercules.display import builder
    B, bsha = load_b_wrapper()
    model, minfo = B.load_model(a.iteration)

    for n, want in MESH_SHA.items():
        assert sha256(os.path.join(a.mesh_dir, n)) == want, n
    P = np.stack([tifffile.imread(os.path.join(a.mesh_dir, n)) for n in ('x.tif', 'y.tif', 'z.tif')], -1)
    valid = ~((P[..., 0] == -1) | (P[..., 1] == -1) | (P[..., 2] == -1))
    valid &= np.isfinite(P).all(-1)
    del P
    assert valid.shape == (H0 // 20, W0 // 20), valid.shape

    tdir = os.path.join(a.out, 'tiles')
    os.makedirs(tdir, exist_ok=True)
    cen = os.path.join(a.out, 'census.jsonl')
    done = {(d['r'], d['c']) for d in map(json.loads, open(cen))} if os.path.exists(cen) else set()
    chunk_log = open(os.path.join(a.out, 'chunks.jsonl'), 'a')
    ex = cf.ThreadPoolExecutor(16)
    norm = lambda t: torch.clamp(t, 0, B.CLIP_MAX) / B.DIVISOR  # noqa: E731
    for s in a.tiles.split(';'):
        r, c = (int(v) for v in s.split(','))
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
        if a.region:  # smoke only: a centred crop of the tile
            y0, x0 = y0 + (T - a.region) // 2, x0 + (T - a.region) // 2
            y1, x1 = y0 + a.region, x0 + a.region
        m = canvas_mask(valid, H0, W0, y0, y1, x0, x1)
        vf = float(m.mean())
        rec = dict(r=r, c=c, valid_fraction=vf, eligible=vf >= ELIG, canvas_rows=[y0, y1], canvas_cols=[x0, x1],
                   level=0, iteration=a.iteration, order=a.order, synthetic=a.synthetic)
        if rec['eligible']:
            Y0, Y1, X0, X1 = y0 - MARGIN, y1 + MARGIN, x0 - MARGIN, x1 + MARGIN
            vol, recs = read_region(Y0, Y1, X0, X1, ex, a.synthetic)
            for cr in recs:
                chunk_log.write(json.dumps(dict(cr, tile=[r, c])) + '\n')
            chunk_log.flush()
            if a.order == 'reverse':
                vol = vol[:, :, ::-1]
            fm = canvas_mask(valid, H0, W0, Y0, Y1, X0, X1).astype(np.uint8) * 255
            t1 = time.time()
            nwin = [0]
            pred, count = B.card_tiling(model, vol.shape[0], vol.shape[1], fm,
                                        lambda yy, xx: vol[yy:yy + B.WINDOW, xx:xx + B.WINDOW],
                                        norm, progress=lambda n: nwin.__setitem__(0, n))
            t2 = time.time()
            del vol
            pred = pred[MARGIN:-MARGIN, MARGIN:-MARGIN]
            count = count[MARGIN:-MARGIN, MARGIN:-MARGIN]
            p8 = np.clip(pred * 255, 0, 255).astype(np.uint8)
            p8[~m] = 0
            side = OUT_SIDE if not a.region else max(8, round(a.region * OUT_SIDE / T))
            out = cv2.resize(p8, (side, side), interpolation=cv2.INTER_AREA)
            b = builder.png_bytes(out)
            fn = f'{SEG}_r{r}_c{c}.png'
            with open(os.path.join(tdir, fn), 'wb') as fh:
                fh.write(b)
            v = p8[m]
            rec.update(file='tiles/' + fn, png_sha256=hashlib.sha256(b).hexdigest(), png_bytes=len(b),
                       stats=dict(domain='uint8 prediction at mesh-valid canvas px, before downscale',
                                  valid_px=int(v.size), mean=float(v.mean()), std=float(v.std()),
                                  p1=float(np.percentile(v, 1)), p99=float(np.percentile(v, 99)),
                                  frac_ge128=float((v >= 128).mean()),
                                  frac_valid_unpredicted=float((count[m] == 0).mean()),
                                  frac_out_zero=float((out == 0).mean()), out_mean=float(out.mean())),
                       windows=nwin[0], chunks_read=sum(x['status'] == 206 for x in recs),
                       chunks_missing=sum(x['status'] == 404 for x in recs),
                       read_s=round(t1 - t0, 1), infer_s=round(t2 - t1, 1))
        rec['seconds'] = round(time.time() - t0, 1)
        rec['utc'] = utc()
        rec['wrapper_sha256'] = sha256(os.path.abspath(__file__))
        rec['b_wrapper_sha256'] = bsha
        rec['model'] = minfo
        with open(cen, 'a') as fh:
            fh.write(json.dumps(rec) + '\n')
        print('tile r%d c%d vf=%.3f %.1fs' % (r, c, vf, rec['seconds']), flush=True)
    ex.shutdown()
    print('ALL_DONE', utc(), flush=True)


if __name__ == '__main__':
    main()
