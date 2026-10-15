# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-O (RULES.md DECL-P4-14) tiles of scrollprize/PHerc.1667-iteration-0 on the Paris 4 strip-a grid.

Builder only: never opens, views or prints image pixels. Writes numbers, hashes and PNG bytes only.

Model (official, unchanged): HF scrollprize/PHerc.1667-iteration-0 @ 06c30644 (config.json,
configuration_inkdetection.py, modeling_inkdetection.py by git blob oid; model.safetensors by sha256), loaded with
transformers.AutoModel.from_pretrained(trust_remote_code=True). The card's full-segment tiling loop (WINDOW 256,
STRIDE 128, a window is skipped if any fmask pixel is 0, sigmoid, bilinear x4, sum/count average,
uint8 = clip(pred * 255) truncated) is kept statement for statement (card_tiling, as in
tools/sib/ckpt-screen-b/infer_1667.py), with the training normalisation clip(0, 200) / 255 (ckpt-screen-b SPECS,
orchestrator ruling 2026-09-26 05:59Z).

Input: the official surface volume
  PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr
level 0: (109, 69760, 170000), 2.4 um in z, y and x (the model's documented ~2 um class; ruled model spacing 2.399
um, a 0.04 % difference, so nothing is resampled). Depth: the official centre crop of 62 of 109 slices
(start (109 - 62) // 2 = 23: slices 23..84; centre slice 54 = mesh surface). Direction: 'reverse' feeds the 62
slices in reverse order (84 -> 23), the card's documented iteration-0 inference setting (reverse_layers=True);
'forward' feeds 23 -> 84. Chunks (109, 128, 128) u8 uncompressed C order: one HTTP range request per chunk for
slices 23..84; a missing chunk (404) is fill 0.

Grid (identical to P4-B strip a / P4-E E2): T = 8343 canvas px from (0, 0), canvas px = level-0 px; mesh-valid by
the strip-a canvas_mask rule (tifxyz grid i // 20, j // 20); a tile is eligible at >= 50 % valid.
Per tile, the card tiling runs on a context region = tile + 128 px on every side (windows start at y0 - 128 step
128, so every tile pixel is covered by up to 4 windows exactly as inside a full-segment run); fmask = mesh-valid
(outside the canvas = 0). Display (DECL-P4-14 item 2 / DECL-P4-4 item 2): the raw 0-255 prediction, 0 outside
mesh-valid, cv2.INTER_AREA 8343 -> 1068, uint8 PNG IHDR/IDAT/IEND (hercules.display.builder.png_bytes).

Usage: p4o_tiles.py <mesh_dir> <out_dir> --only "r,c;r,c" [--direction reverse] [--threads 4]
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

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))
from hercules.display import builder  # noqa: E402

PROV = 'Project HERCULES | owner the owner | [id removed]'
SEG = '20260701183124-w010-027'
HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
SV = f'PHercParis4/segments/{SEG}/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr'
NZ, CH = 109, 128
D_MODEL = 62
Z0 = (NZ - D_MODEL) // 2          # 23
Z1 = Z0 + D_MODEL                 # 85 (exclusive)
T, NR, NC, OUT_SIDE, ELIG = 8343, 9, 21, 1068, 0.5
H0, W0 = 69760, 170000
WINDOW, STRIDE = 256, 128
CTX = 128
CLIP_MAX, DIVISOR = 200.0, 255.0
HF_DIR = os.environ.get('P4O_HF_DIR', '/work/p4o/hf/it0')
EXPECT = {  # catalogue: git blob oids (code/config) and LFS sha256 (weights), commit 06c30644
    'config.json': ('oid', '32accd0facbc9424458e5d268460de0f07e6bd7d'),
    'configuration_inkdetection.py': ('oid', '24ac6d12668bfb5cf4b448c8f61723e97264ee25'),
    'modeling_inkdetection.py': ('oid', 'c75143f25652f1e5fe9f7f7dc7b5183f00d37fb5'),
    'model.safetensors': ('sha256', '62c43b98f55c169ae874c684a59953b5ce1cb45140129107f861501cce3edaef'),
}

_s = requests.Session()
_s.mount('https://', requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=3))


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def verify_model_files():
    out = {}
    for name, (kind, want) in EXPECT.items():
        p = os.path.join(HF_DIR, name)
        if kind == 'oid':
            b = open(p, 'rb').read()
            got = hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()
        else:
            got = sha256_file(p)
        if got != want:
            raise SystemExit(f'{name}: {kind} {got} != {want}')
        out[name] = {kind: got, 'sha256': sha256_file(p)}
    return out


def load_model():
    from transformers import AutoModel
    return AutoModel.from_pretrained(HF_DIR, trust_remote_code=True).eval()


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


def get_chunk(cy, cx):
    """Slices Z0..Z1-1 of level-0 chunk (0, cy, cx) as (62, 128, 128) u8; None if absent (fill 0)."""
    key = f'{SV}/0/0/{cy}/{cx}'
    a, b = Z0 * CH * CH, Z1 * CH * CH - 1
    for i in range(6):
        try:
            r = _s.get(f'{HTTP}/{key}', headers={'Range': f'bytes={a}-{b}'}, timeout=60)
            if r.status_code == 404:
                return None, {'k': f'0/0/{cy}/{cx}', 'status': 404}
            if r.status_code == 206 and len(r.content) == b - a + 1:
                d = np.frombuffer(r.content, np.uint8).reshape(D_MODEL, CH, CH)
                return d, {'k': f'0/0/{cy}/{cx}', 'status': 206, 'sha256': hashlib.sha256(r.content).hexdigest()}
        except requests.RequestException:
            pass
        time.sleep(2 ** i)
    raise RuntimeError(f'chunk read failed: {key}')


class Band:
    """Rows [ry, ry+128) x cols [x0, x1) of slices Z0..Z1-1 (canvas coords, 128-aligned rows), zero outside."""

    def __init__(self, ex, ry, x0, x1, log):
        self.ry, self.x0, self.x1 = ry, x0, x1
        self.a = np.zeros((D_MODEL, CH, x1 - x0), np.uint8)
        if ry < 0 or ry >= H0:
            return
        cy = ry // CH
        cxs = list(range(max(x0, 0) // CH, (min(x1, W0) - 1) // CH + 1))
        for cx, (d, rec) in zip(cxs, ex.map(lambda c: get_chunk(cy, c), cxs)):
            log.append(rec)
            if d is None:
                continue
            xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W0)
            self.a[:, :, xa - x0:xb - x0] = d[:, :, xa - cx * CH:xb - cx * CH]


def card_tiling_banded(model, ry0, rx0, Hc, Wc, fmask, bands, norm_fn, reverse, progress=None):
    """The card's tiling loop over a (Hc, Wc) region whose rows start at canvas ry0 (128-aligned).
    tile = image[y:y+WINDOW, x:x+WINDOW] of the (H, W, 62) stack is assembled from two 128-row bands."""
    import torch
    import torch.nn.functional as F
    mask_pred = np.zeros((Hc, Wc), dtype=np.float32)
    mask_count = np.zeros((Hc, Wc), dtype=np.float32)
    n = 0
    with torch.no_grad():
        for y in range(0, Hc - WINDOW + 1, STRIDE):
            b0, b1 = bands(ry0 + y), bands(ry0 + y + CH)
            for x in range(0, Wc - WINDOW + 1, STRIDE):
                if np.any(fmask[y:y + WINDOW, x:x + WINDOW] == 0):
                    continue
                stack = np.concatenate([b0.a[:, :, x:x + WINDOW], b1.a[:, :, x:x + WINDOW]], axis=1)  # (62,256,256)
                if reverse:
                    stack = stack[::-1]
                tile = np.ascontiguousarray(np.transpose(stack, (1, 2, 0)))  # (256,256,62)
                t = torch.from_numpy(tile).permute(2, 0, 1)         # (62,256,256)
                t = norm_fn(t.unsqueeze(0).unsqueeze(0).float())    # (1,1,62,256,256)
                logits = model(t).logits                            # (1,1,64,64)
                prob = torch.sigmoid(logits)
                prob = F.interpolate(prob, scale_factor=4,
                                     mode="bilinear").squeeze().cpu().numpy()
                mask_pred[y:y + WINDOW, x:x + WINDOW] += prob
                mask_count[y:y + WINDOW, x:x + WINDOW] += 1.0
                n += 1
                if progress:
                    progress(n)
    pred = np.divide(mask_pred, mask_count,
                     out=np.zeros_like(mask_pred),
                     where=mask_count != 0)
    return pred, mask_count, n


def train_norm(t):
    """clip(0, 200) then Normalize(mean=0, std=1, max_pixel_value=255) == /255."""
    return t.clamp_(0.0, CLIP_MAX).div_(DIVISOR)


def png_chunks(b):
    names, p = [], 8
    while p < len(b):
        n = int.from_bytes(b[p:p + 4], 'big')
        names.append(b[p + 4:p + 8].decode('latin1'))
        crc = int.from_bytes(b[p + 8 + n:p + 12 + n], 'big')
        assert crc == zlib.crc32(b[p + 4:p + 8 + n]) & 0xFFFFFFFF
        p += 12 + n
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mesh_dir')
    ap.add_argument('out')
    ap.add_argument('--only', required=True)
    ap.add_argument('--direction', default='reverse', choices=['reverse', 'forward'])
    ap.add_argument('--threads', type=int, default=4)
    a = ap.parse_args()
    import torch
    import transformers
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    files = verify_model_files()
    model = load_model()
    run = dict(provenance=PROV, utc=utc(), torch=torch.__version__, transformers=transformers.__version__,
               threads=torch.get_num_threads(), dtype='float32', model_files=files, direction=a.direction,
               slices=[Z0, Z1 - 1], wrapper_sha256=sha256_file(os.path.abspath(__file__)))

    za = requests.get(f'{HTTP}/{SV}/0/.zarray', timeout=60).json()
    assert za['shape'] == [NZ, H0, W0] and za['chunks'] == [NZ, CH, CH] and za['dtype'] == '|u1' \
        and za['compressor'] is None and za['order'] == 'C' and za.get('dimension_separator') == '/', za
    P = np.stack([tifffile.imread(os.path.join(a.mesh_dir, n)) for n in ('x.tif', 'y.tif', 'z.tif')], -1)
    valid = ~((P[..., 0] == -1) | (P[..., 1] == -1) | (P[..., 2] == -1))
    valid &= np.isfinite(P).all(-1)
    del P
    assert valid.shape == (H0 // 20, W0 // 20), valid.shape

    tdir = os.path.join(a.out, 'tiles')
    os.makedirs(tdir, exist_ok=True)
    cen = os.path.join(a.out, 'census.jsonl')
    done = set()
    if os.path.exists(cen):
        done = {(d['r'], d['c']) for d in map(json.loads, open(cen)) if d.get('direction') == a.direction}
    with open(os.path.join(a.out, 'runs_meta.jsonl'), 'a') as f:
        f.write(json.dumps(run) + '\n')
    order = [tuple(int(v) for v in s.split(',')) for s in a.only.split(';') if s]
    ex = cf.ThreadPoolExecutor(24)
    chunk_log = open(os.path.join(a.out, 'chunks.jsonl'), 'a')
    for r, c in order:
        if (r, c) in done:
            continue
        t0 = time.time()
        y0, y1, x0, x1 = r * T, (r + 1) * T, c * T, (c + 1) * T
        m = canvas_mask(valid, H0, W0, y0, y1, x0, x1)
        vf = float(m.mean())
        rec = {'r': r, 'c': c, 'direction': a.direction, 'valid_fraction': vf, 'eligible': vf >= ELIG,
               'canvas_rows': [y0, y1], 'canvas_cols': [x0, x1]}
        if rec['eligible']:
            # context region: 128-aligned rows from y0 - CTX, window rows cover [y0 - CTX, y1 + CTX)
            ry0 = ((y0 - CTX) // CH) * CH
            Hc = y1 + CTX - ry0
            Hc = ((Hc - WINDOW + STRIDE - 1) // STRIDE) * STRIDE + WINDOW
            rx0 = x0 - CTX
            Wc = x1 + CTX - rx0
            Wc = ((Wc - WINDOW + STRIDE - 1) // STRIDE) * STRIDE + WINDOW
            fm = canvas_mask(valid, H0, W0, ry0, ry0 + Hc, rx0, rx0 + Wc).astype(np.uint8)
            clog, cache = [], {}

            def bands(ry):
                if ry not in cache:
                    for k in [k for k in cache if k < ry - CH]:
                        del cache[k]
                    cache[ry] = Band(ex, ry, rx0, rx0 + Wc, clog)
                return cache[ry]

            last = [time.time()]

            def prog(n):
                if time.time() - last[0] > 600:
                    last[0] = time.time()
                    print(f'  r{r} c{c} windows={n} {utc()}', flush=True)

            pred, cnt, n_win = card_tiling_banded(model, ry0, rx0, Hc, Wc, fm, bands, train_norm,
                                                  a.direction == 'reverse', prog)
            for cr in clog:
                chunk_log.write(json.dumps(dict(cr, tile=[r, c])) + '\n')
            chunk_log.flush()
            oy, ox = y0 - ry0, x0 - rx0
            p = pred[oy:oy + T, ox:ox + T]
            cov = cnt[oy:oy + T, ox:ox + T] > 0
            u8 = np.clip(p * 255, 0, 255).astype(np.uint8)   # card: raw 0-255, truncated
            inside = (np.arange(y0, y1) < H0)[:, None] & (np.arange(x0, x1) < W0)[None, :]
            u8[~(m & inside)] = 0
            vals = u8[m]
            out = cv2.resize(u8, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
            assert out.shape == (OUT_SIDE, OUT_SIDE) and out.dtype == np.uint8
            b = builder.png_bytes(out)
            ch = png_chunks(b)
            assert set(ch) <= {'IHDR', 'IDAT', 'IEND'} and ch[0] == 'IHDR' and ch[-1] == 'IEND', ch
            assert b[16:24] == OUT_SIDE.to_bytes(4, 'big') * 2 and b[24] == 8 and b[25] == 0
            fn = f'{SEG}_r{r}_c{c}.png'
            with open(os.path.join(tdir, fn), 'wb') as fh:
                fh.write(b)
            rec.update({
                'file': 'tiles/' + fn, 'png_sha256': hashlib.sha256(b).hexdigest(), 'png_bytes': len(b),
                'png_chunks': sorted(set(ch)),
                'stats': {'domain': 'raw prediction u8 at mesh-valid canvas px, before downscale',
                          'valid_px': int(vals.size), 'mean': float(vals.mean()), 'std': float(vals.std()),
                          'p1': float(np.percentile(vals, 1)), 'p50': float(np.percentile(vals, 50)),
                          'p99': float(np.percentile(vals, 99)),
                          'frac_valid_not_covered': float((~cov[m]).mean()),
                          'frac_out_zero': float((out == 0).mean()), 'out_mean': float(out.mean())},
                'windows': n_win, 'context_region': [ry0, rx0, Hc, Wc],
                'chunks_read': sum(cr['status'] == 206 for cr in clog),
                'chunks_missing': sum(cr['status'] == 404 for cr in clog)})
            del pred, cnt, p, u8, cache
        rec['seconds'] = round(time.time() - t0, 1)
        rec['utc'] = utc()
        with open(cen, 'a') as fh:
            fh.write(json.dumps(rec) + '\n')
        print('tile r%d c%d vf=%.3f %.1fs' % (r, c, vf, rec['seconds']), flush=True)
    ex.shutdown()
    print('ALL_DONE', utc(), flush=True)


if __name__ == '__main__':
    main()
