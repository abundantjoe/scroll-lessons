#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-O (RULES.md DECL-P4-14): official scrollprize/PHerc.1667-iteration-N on the PHerc. Paris 4 strip-a tiles.
Numbers only: no tile, map or CT image is opened, displayed or described; tiles are written as PNG bytes and
summarised by hashes and scalar statistics.

Input (DECL-P4-14 item 2): the organizer 2.4 um surface volume of 20260701183124-w010-027 (level 0, 109 slices,
surface = slice 54, canvas px = level-0 px, strip-a grid T 8343 from pairs0814b e2/grid.json). The model's native
voxel is the ~2 um class of its training surface volumes (SPECS.json), so the 2.4 um level 0 is used as is (no
in-plane resampling); the slab is the official centre crop of 62 of the 109 slices = slices 23..84
(vesuvius select_layer_indices / villa _compute_selected_layer_indices). Normalisation clip(0,200)/255.
Order: the documented training convention on organizer surface volumes: iterations 1-5 reverse_layers False (slices
ascending); iteration 0 reverse_layers True (card: "l_2 inference uses reverse_layers=True").
Inference: infer_1667.card_tiling (the card's loop: 256 window, stride 128, fmask skip, sigmoid, x4 bilinear, mean)
on the tile + 128 px halo, fmask = mesh-valid (strip-a canvas_mask rule). The backbone runs in channels_last_3d
memory layout (a layout change only; max |logit diff| 4e-7 measured, logged per run).
Display (DECL-P4-4 item 2 as restated in DECL-P4-14 item 2): raw prediction u8 = clip(p*255) truncated, 0 outside
mesh-valid, cv2.INTER_AREA 8343 -> 1068, PNG via hercules.display.builder.png_bytes (IHDR/IDAT/IEND only).
Usage: p4o_tiles.py --iteration N --tiles "r,c;r,c;..." --out logs/sib/ckpt-screen-b/p4o/<ckpt> [--threads 4]
       p4o_tiles.py --finalize --iteration N --out ...
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'src'))
import infer_1667 as I  # noqa: E402

PROV = I.PROV
SEG = '20260701183124-w010-027'
HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
SV = f'PHercParis4/segments/{SEG}/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr'
MESH = f'PHercParis4/segments/{SEG}/mesh/20260701183124-on-20260411134726-2.4um.tifxyz'
GRID_REF = 'origin/claude/gifted-bell-gavnl5-sib-pairs0814b:logs/sib/pairs0814b/e2/grid.json'
E2_MANIFEST_REF = 'origin/claude/gifted-bell-gavnl5-sib-pairs0814b:logs/sib/pairs0814b/e2/manifest.json'
NZ, CH = 109, 128
Z0, Z1 = 23, 85                  # official centre crop of 62 from 109 (start (109-62)//2 = 23)
T, OUT_SIDE, HALO = 8343, 1068, 128
H0, W0 = 69760, 170000
WORK = os.environ.get('P4O_WORK', '/work/p4o')
ORDER = {0: 'reverse', 1: 'forward', 2: 'forward', 3: 'forward', 4: 'forward', 5: 'forward'}


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git_json(ref):
    return json.loads(subprocess.check_output(['git', '-C', REPO, 'show', ref]))


_session = None


def sess():
    global _session
    if _session is None:
        import requests
        _session = requests.Session()
        _session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=3))
    return _session


def load_valid():
    """Mesh-valid grid (3488 x 8500): no coordinate == -1 and all finite (strip-a rule); tifs sha256-checked."""
    cache = f'{WORK}/mesh_valid.npy'
    if os.path.exists(cache):
        return np.load(cache)
    import tifffile
    e2 = git_json(E2_MANIFEST_REF)
    want = {k.split('/')[-1]: v for k, v in e2['input_sha256'].items() if k.endswith('.tif')}
    os.makedirs(f'{WORK}/mesh', exist_ok=True)
    P = []
    for n in ('x.tif', 'y.tif', 'z.tif'):
        p = f'{WORK}/mesh/{n}'
        if not os.path.exists(p):
            subprocess.run(['curl', '-fsSL', '--retry', '4', '-o', p, f'{HTTP}/{MESH}/{n}'], check=True)
        got = I.sha256(p)
        if n in want and got != want[n]:
            raise SystemExit(f'mesh {n} sha256 {got} != e2 manifest {want[n]}')
        P.append(tifffile.imread(p))
    P = np.stack(P, -1)
    valid = ~((P[..., 0] == -1) | (P[..., 1] == -1) | (P[..., 2] == -1))
    valid &= np.isfinite(P).all(-1)
    assert valid.shape == (H0 // 20, W0 // 20), valid.shape
    np.save(cache, valid)
    return valid


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
    """Slices Z0..Z1-1 of level-0 chunk (0, cy, cx) as uint8 (62,128,128), by HTTP byte range; 404 -> None."""
    key = f'{SV}/0/0/{cy}/{cx}'
    a, b = Z0 * CH * CH, Z1 * CH * CH - 1
    for i in range(7):
        try:
            r = sess().get(f'{HTTP}/{key}', headers={'Range': f'bytes={a}-{b}'}, timeout=120)
            if r.status_code == 404:
                return None, dict(k=f'0/0/{cy}/{cx}', status=404)
            if r.status_code == 206 and len(r.content) == b - a + 1:
                return np.frombuffer(r.content, np.uint8).reshape(Z1 - Z0, CH, CH), dict(
                    k=f'0/0/{cy}/{cx}', status=206, sha256=sha_bytes(r.content))
        except Exception:
            pass
        time.sleep(2 ** i)
    raise RuntimeError(f'chunk read failed: {key}')


def read_stack(y0, y1, x0, x1, Hp, Wp, order):
    """(Hp, Wp, 62) uint8 image of canvas rows [y0,y1), cols [x0,x1) (zeros outside the array/pad), in `order`."""
    img = np.zeros((Hp, Wp, Z1 - Z0), np.uint8)
    jobs = [(cy, cx) for cy in range(max(y0, 0) // CH, (min(y1, H0) - 1) // CH + 1)
            for cx in range(max(x0, 0) // CH, (min(x1, W0) - 1) // CH + 1)]
    recs = []
    h = hashlib.sha256()
    # bounded in-flight work (a 14.3 GB cgroup OOM-killed an unbounded map on r1 c14; S3_NOTES.md); same job order,
    # same records hash, same image bytes
    B = 256
    with cf.ThreadPoolExecutor(24) as ex:
        for i in range(0, len(jobs), B):
            part = jobs[i:i + B]
            for (cy, cx), (d, rec) in zip(part, ex.map(lambda j: get_chunk(*j), part)):
                recs.append(rec)
                h.update(json.dumps(rec, sort_keys=True).encode())
                if d is None:
                    continue
                ya, yb = max(cy * CH, y0), min(cy * CH + CH, y1, H0)
                xa, xb = max(cx * CH, x0), min(cx * CH + CH, x1, W0)
                blk = d[:, ya - cy * CH:yb - cy * CH, xa - cx * CH:xb - cx * CH]
                if order == 'reverse':
                    blk = blk[::-1]
                img[ya - y0:yb - y0, xa - x0:xb - x0] = np.transpose(blk, (1, 2, 0))
    return img, dict(chunks_read=sum(r['status'] == 206 for r in recs),
                     chunks_missing=sum(r['status'] == 404 for r in recs), chunk_records_sha256=h.hexdigest())


def masked_norm_mean(img, m, band=256):
    """mean(clip(img[m], 0, 200)) / 255 without the 2 x 4.6 GB copies of the boolean-index form (S3_NOTES.md):
    an exact integer sum per row band, so the value equals the old expression bit for bit."""
    if not m.any():
        return None
    s = 0
    for y in range(0, img.shape[0], band):
        sel = img[y:y + band][m[y:y + band]]
        s += int(np.minimum(sel, 200).sum(dtype=np.int64))
    return float(np.float64(s) / np.float64(int(m.sum()) * img.shape[2]) / 255.0)


class FastModel:
    """Official model with the backbone in channels_last_3d (layout only); callable like the HF model."""

    def __init__(self, model):
        import torch
        self.torch = torch
        self.m = model
        self.m.backbone.to(memory_format=torch.channels_last_3d)

    def __call__(self, t):
        return self.m(t.contiguous(memory_format=self.torch.channels_last_3d))


def png_chunks(b):
    names, p = [], 8
    while p < len(b):
        n = int.from_bytes(b[p:p + 4], 'big')
        names.append(b[p + 4:p + 8].decode('latin1'))
        assert int.from_bytes(b[p + 8 + n:p + 12 + n], 'big') == zlib.crc32(b[p + 4:p + 8 + n]) & 0xFFFFFFFF
        p += 12 + n
    return names


def run_tile(model, it, r, c, out, valid, log):
    import cv2
    from hercules.display import builder
    fn = f'{SEG}_r{r}_c{c}.png'
    jp = f'{out}/tiles/{fn}.json'
    if os.path.exists(jp):
        log(dict(skip=fn))
        return json.load(open(jp))
    t0 = time.time()
    order = ORDER[it]
    y0, x0 = r * T - HALO, c * T - HALO
    y1, x1 = (r + 1) * T + HALO, (c + 1) * T + HALO
    H, W = y1 - y0, x1 - x0
    Hp, Wp = I.pad256(H), I.pad256(W)
    m_reg = canvas_mask(valid, H0, W0, y0, y1, x0, x1)
    fm = np.zeros((Hp, Wp), np.uint8)
    fm[:H, :W] = m_reg
    n_win = sum(1 for yy in range(0, Hp - I.WINDOW + 1, I.STRIDE) for xx in range(0, Wp - I.WINDOW + 1, I.STRIDE)
                if not np.any(fm[yy:yy + I.WINDOW, xx:xx + I.WINDOW] == 0))
    log(dict(tile=fn, windows=n_win, eta_h=round(n_win * 3.3 / 3600, 2)))
    img, rd = read_stack(y0, y1, x0, x1, Hp, Wp, order)
    t_read = time.time() - t0
    norm_mean = masked_norm_mean(img[:H, :W], m_reg)
    ckd = f'{WORK}/it{it}/ckpt/{fn}'
    state = None
    if os.path.exists(f'{ckd}/n.json'):
        nj = json.load(open(f'{ckd}/n.json'))
        state = (np.load(f'{ckd}/pred.npy'), np.load(f'{ckd}/cnt.npy'), int(nj['n']))
        log(dict(tile=fn, resume_from_window=int(nj['n'])))

    def ckpt_fn(p_, c_, n_):
        os.makedirs(ckd, exist_ok=True)
        np.save(f'{ckd}/pred.tmp.npy', p_)
        np.save(f'{ckd}/cnt.tmp.npy', c_)
        os.replace(f'{ckd}/pred.tmp.npy', f'{ckd}/pred.npy')
        os.replace(f'{ckd}/cnt.tmp.npy', f'{ckd}/cnt.npy')
        with open(f'{ckd}/n.tmp.json', 'w') as f_:
            json.dump(dict(n=n_, utc=utc()), f_)
        os.replace(f'{ckd}/n.tmp.json', f'{ckd}/n.json')

    pred, cnt = I.card_tiling(model, Hp, Wp, fm, lambda y, x: img[y:y + I.WINDOW, x:x + I.WINDOW], I.train_norm,
                              state=state, ckpt_fn=ckpt_fn)
    del img
    core = (slice(HALO, HALO + T), slice(HALO, HALO + T))
    u8 = I.to_u8(pred[:H, :W][core])
    m = m_reg[core]
    cov = cnt[:H, :W][core] > 0
    raw_out_nonzero = float((u8[~m] > 0).mean()) if (~m).any() else 0.0
    u8[~m] = 0
    os.makedirs(f'{WORK}/it{it}/full', exist_ok=True)
    np.save(f'{WORK}/it{it}/full/{fn}.npy', u8)
    disp = cv2.resize(u8, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
    b = builder.png_bytes(disp)
    ch = png_chunks(b)
    assert sorted(set(ch)) == ['IDAT', 'IEND', 'IHDR'], ch
    os.makedirs(f'{out}/tiles', exist_ok=True)
    with open(f'{out}/tiles/{fn}', 'wb') as f:
        f.write(b)
    vals = u8[m]
    rec = dict(file='tiles/' + fn, r=r, c=c, png_sha256=sha_bytes(b), png_bytes=len(b), png_chunks=sorted(set(ch)),
               valid_fraction=float(m.mean()), canvas_rows=[r * T, (r + 1) * T], canvas_cols=[c * T, (c + 1) * T],
               order=order, slices=[Z0, Z1 - 1],
               stats=dict(domain='prediction u8 = clip(p*255) truncated, at mesh-valid canvas px, full resolution, '
                                 'before downscale',
                          valid_px=int(vals.size), mean=float(vals.mean()) if vals.size else None,
                          std=float(vals.std()) if vals.size else None,
                          p1=float(np.percentile(vals, 1)) if vals.size else None,
                          p99=float(np.percentile(vals, 99)) if vals.size else None,
                          min=int(vals.min()) if vals.size else None, max=int(vals.max()) if vals.size else None,
                          frac_zero_in_valid=float((vals == 0).mean()) if vals.size else None,
                          frac_nonzero_outside_valid=raw_out_nonzero,
                          frac_out_zero=float((disp == 0).mean()), out_mean=float(disp.mean()),
                          coverage_of_valid=float(cov[m].mean()) if m.any() else None,
                          input_normalised_mean_valid=norm_mean),
               full_res_u8_sha256=I.arr_sha(u8), model_windows=n_win,
               seconds_read=round(t_read, 1), seconds_total=round(time.time() - t0, 1), utc=utc(), **rd)
    with open(jp, 'w') as f:
        json.dump(rec, f, indent=1)
    log(rec)
    return rec


def finalize(it, out):
    grid = git_json(GRID_REF)
    e2 = git_json(E2_MANIFEST_REF)
    recs = [json.load(open(os.path.join(out, 'tiles', f))) for f in sorted(os.listdir(os.path.join(out, 'tiles')))
            if f.endswith('.png.json')]
    for rec in recs:
        b = open(os.path.join(out, rec['file']), 'rb').read()
        assert sha_bytes(b) == rec['png_sha256'], rec['file']
    spec = json.load(open(os.path.join(REPO, 'logs/sib/ckpt-screen-b/SPECS.json')))['checkpoints'][f'PHerc.1667-iteration-{it}']
    man = dict(provenance=PROV, declaration='RULES.md DECL-P4-14 (P4-O)', material=f'M-P4O-PHerc.1667-iteration-{it}',
               segment=SEG, surface_volume=f's3://vesuvius-challenge-open-data/{SV}', level_used=0,
               slab=dict(slices=[Z0, Z1 - 1], centre=54, n=Z1 - Z0, um=[round((Z0 - 54) * 2.4, 1), round((Z1 - 1 - 54) * 2.4, 1)],
                         rule='official centre crop of 62 of 109 slices'),
               order=ORDER[it], order_basis=('card: "l_2 inference uses reverse_layers=True to match the training-segment '
                                             'convention"' if it == 0 else 'l_2 trained with reverse_layers False '
                                             '(villa inference_resnet3d_3d_decoder.py segments_to_infer)'),
               checkpoint=dict(repo=spec['repo'], commit=spec['commit'], weights_sha256=spec['weights']['sha256'],
                               provenance='logs/sib/ckpt-screen-b/p4o/provenance.json'),
               inference=dict(wrapper='tools/sib/ckpt-screen-b/infer_1667.py',
                              wrapper_sha256=I.sha256(os.path.join(HERE, 'infer_1667.py')),
                              builder='tools/sib/ckpt-screen-b/p4o_tiles.py',
                              builder_sha256=I.sha256(os.path.abspath(__file__)),
                              normalisation='clip(0,200)/255', window=256, stride=128, halo_px=HALO, dtype='float32',
                              memory_layout='backbone channels_last_3d'),
               display='raw prediction u8 = clip(p*255) truncated; 0 outside mesh-valid; INTER_AREA 8343 -> 1068; '
                       'PNG IHDR/IDAT/IEND (DECL-P4-14 item 2)',
               grid=dict(ref=GRID_REF, T=grid['T_canvas_px'], canvas_shape=grid['canvas_shape']),
               input_sha256=e2['input_sha256'],
               n_tiles=len(recs), tiles=sorted(recs, key=lambda x: (x['r'], x['c'])),
               viewing='no tile, map or CT image was opened, displayed or described; numbers and hashes only',
               generated_utc=utc())
    e2t = {(t['r'], t['c']): t for t in e2['tiles']}
    man['checks'] = dict(all_png_sha256_recomputed_ok=True,
                         valid_fraction_equal_e2=all(abs(t['valid_fraction'] - e2t[(t['r'], t['c'])]['valid_fraction']) < 1e-9
                                                     for t in recs if (t['r'], t['c']) in e2t),
                         all_tiles_eligible_in_e2=all((t['r'], t['c']) in e2t for t in recs))
    p = os.path.join(out, 'manifest.json')
    json.dump(man, open(p, 'w'), indent=1)
    print(p, I.sha256(p), len(recs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iteration', type=int, required=True, choices=range(6))
    ap.add_argument('--tiles', default='')
    ap.add_argument('--out', required=True)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--finalize', action='store_true')
    a = ap.parse_args()
    if a.finalize:
        return finalize(a.iteration, a.out)
    import torch
    torch.set_num_threads(a.threads)
    valid = load_valid()
    model, ck = I.load_model(a.iteration)
    fm = FastModel(model)
    x = torch.rand(1, 1, 62, 256, 256, generator=torch.Generator().manual_seed(0))
    with torch.no_grad():
        model.backbone.to(memory_format=torch.contiguous_format)
        y_ref = model(x).logits
        model.backbone.to(memory_format=torch.channels_last_3d)
        y_cl = fm(x).logits
    layout_diff = float((y_ref - y_cl).abs().max())
    assert layout_diff < 1e-4, layout_diff
    logp = f'{a.out}/run_{os.getpid()}.log'
    os.makedirs(f'{a.out}/tiles', exist_ok=True)

    def log(rec):
        line = json.dumps({**rec, "log_utc": utc()})
        print(line, flush=True)
        with open(logp, 'a') as f:
            f.write(line + '\n')
    log(dict(start=True, iteration=a.iteration, checkpoint=ck, layout_max_abs_logit_diff=layout_diff,
             tiles=a.tiles, threads=a.threads, order=ORDER[a.iteration]))
    e2 = git_json(E2_MANIFEST_REF)
    elig = {(t['r'], t['c']) for t in e2['tiles']}
    for tok in [t for t in a.tiles.split(';') if t]:
        r, c = (int(v) for v in tok.split(','))
        if (r, c) not in elig:
            log(dict(skip_ineligible=[r, c]))
            continue
        run_tile(fm, a.iteration, r, c, a.out, valid, log)


if __name__ == '__main__':
    main()
