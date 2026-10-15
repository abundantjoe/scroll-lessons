# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN tile inference (DECL-P4-23 items 3, 5, 7). Numbers only: maps are written and hashed, never opened.

Per tile (seg, r, c) of the strip-a grid (T = 8343 px): the core [r*T,(r+1)*T) x [c*T,(c+1)*T) is predicted in
windows of WIN x WIN core px with HALO px of context on every side (input zeros beyond the canvas/missing chunks,
as p4o_tiles.read_stack), model in eval mode, sigmoid, bilinear x4 upsampling (F.interpolate, align_corners False)
of the stride-4 output to canvas px; a window is skipped if its core has no mesh-valid px (its p stays 0).
Display identical to P4-O: u8 = clip(p*255) truncated at canvas px, 0 outside mesh-valid, INTER_AREA 8343 -> 1068,
PNG IHDR/IDAT/IEND. Record = the P4-O per-tile json fields (png_sha256, valid_fraction, stats) plus
train_manifest_sha256, model_final_sha256, min_dist_to_X_mm (tile) and train_min_dist_to_X_mm.
Resumable: the band of windows done so far is checkpointed in <work>/<arm>/<tile>/ (u8 rows + n.json) after each band.
--save-npz writes the full-res u8 map (0 outside mesh-valid) as <out>/arrays/<tile>.npz (for col. -1 AUC by p4-excl)."""
import argparse
import json
import os

import numpy as np

import own_common as C

WIN, HALO = 1024, 160   # HALO >= measured receptive-field radius (151 px, configs A/B)


def predict_tile(model, torch, seg, r, c, valid, ckd, log):
    T = C.tile_px(seg)
    H0, W0 = C.SEGS[seg]
    y0, x0 = r * T, c * T
    m = C.canvas_mask(seg, valid, y0, y0 + T, x0, x0 + T)
    u8 = np.zeros((T, T), np.uint8)
    b0 = 0
    os.makedirs(ckd, exist_ok=True)
    if os.path.exists(f'{ckd}/n.json'):
        b0 = json.load(open(f'{ckd}/n.json'))['bands_done']
        u8 = np.load(f'{ckd}/u8.npy')
        log(dict(resume_band=b0))
    bands = list(range(0, T, WIN))
    miss = 0
    for bi, by in enumerate(bands):
        if bi < b0:
            continue
        bh = min(WIN, T - by)
        if not m[by:by + bh].any():
            continue
        ya, yb = y0 + by - HALO, y0 + by + bh + HALO
        img, rd = C.read_region(seg, ya, yb, x0 - HALO, x0 + T + HALO)
        miss += rd['chunks_missing']
        for bx in range(0, T, WIN):
            bw = min(WIN, T - bx)
            if not m[by:by + bh, bx:bx + bw].any():
                continue
            ph, pw = -(-(bh + 2 * HALO) // 4) * 4, -(-(bw + 2 * HALO) // 4) * 4
            win = np.zeros((ph, pw, C.NZ), np.uint8)
            win[:bh + 2 * HALO, :bw + 2 * HALO] = img[:, bx:bx + bw + 2 * HALO]
            x = torch.from_numpy(C.norm(win)).permute(2, 0, 1)[None, None]
            with torch.no_grad():
                p = torch.sigmoid(model(x))
                p = torch.nn.functional.interpolate(p, scale_factor=4, mode='bilinear', align_corners=False)
            p = p[0, 0, HALO:HALO + bh, HALO:HALO + bw].numpy()
            u8[by:by + bh, bx:bx + bw] = C.to_u8(p)
        del img
        np.save(f'{ckd}/u8.tmp.npy', u8)
        os.replace(f'{ckd}/u8.tmp.npy', f'{ckd}/u8.npy')
        json.dump(dict(bands_done=bi + 1, utc=C.utc()), open(f'{ckd}/n.tmp.json', 'w'))
        os.replace(f'{ckd}/n.tmp.json', f'{ckd}/n.json')
        log(dict(band=bi + 1, of=len(bands)))
    return u8, m, miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True, help='model_final.pth')
    ap.add_argument('--summary', required=True, help='the arm summary.json')
    ap.add_argument('--tiles', required=True, help='"seg:r,c;seg:r,c" (seg may be w010-027 / w028-037 short name)')
    ap.add_argument('--out', required=True, help='maps dir: tiles/<seg>_r<R>_c<C>.png(.json), arrays/')
    ap.add_argument('--tile-dist', default='', help='json {"<seg>_r<R>_c<C>": min_dist_to_X_mm} from p4-excl')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--save-npz', action='store_true')
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    ck = torch.load(a.model, weights_only=False)
    summ = json.load(open(a.summary))
    assert C.sha256_file(a.model) == summ['model_final_sha256']
    model = C.build_model(ck['cfg'])
    model.load_state_dict(ck['model'])
    model.eval()
    arm = ck['arm']
    dist = json.load(open(a.tile_dist)) if a.tile_dist else {}
    short = {s.split('-', 1)[1]: s for s in C.SEGS}
    os.makedirs(f'{a.out}/tiles', exist_ok=True)
    log = C.jlog(f'{a.out}/run_{arm}_{os.getpid()}.log')
    log(dict(start=True, arm=arm, tiles=a.tiles, model_final_sha256=summ['model_final_sha256'],
             train_manifest_sha256=summ['train_manifest_sha256'],
             code_sha256={f: C.sha256_file(os.path.join(C.HERE, f)) for f in ('infer.py', 'own_common.py')}))
    for tok in [t for t in a.tiles.split(';') if t]:
        seg, rc = tok.split(':')
        seg = short.get(seg, seg)
        r, c = (int(v) for v in rc.split(','))
        name = f'{seg}_r{r}_c{c}'
        jp = f'{a.out}/tiles/{name}.png.json'
        if os.path.exists(jp):
            log(dict(skip=name))
            continue
        import time
        t0 = time.time()
        valid = C.load_valid(seg)
        u8f, m, miss = predict_tile(model, torch, seg, r, c, valid, f'{C.WORK}/infer/{arm}/{name}', log)
        b, u8, disp = C.display_png(u8f, m)
        assert sorted(set(C.p4o(seg).png_chunks(b))) == ['IDAT', 'IEND', 'IHDR']
        open(f'{a.out}/tiles/{name}.png', 'wb').write(b)
        vals = u8[m]
        rec = dict(file=f'tiles/{name}.png', seg=seg, r=r, c=c, arm=arm, png_sha256=C.sha_bytes(b), png_bytes=len(b),
                   valid_fraction=float(m.mean()), canvas_rows=[r * C.tile_px(seg), (r + 1) * C.tile_px(seg)],
                   canvas_cols=[c * C.tile_px(seg), (c + 1) * C.tile_px(seg)], tile_px=C.tile_px(seg), order='forward', slices=[C.Z0, C.Z1 - 1],
                   stats=dict(domain='prediction u8 = clip(p*255) truncated, at mesh-valid canvas px, full resolution, '
                                     'before downscale', valid_px=int(vals.size),
                              mean=float(vals.mean()) if vals.size else None,
                              std=float(vals.std()) if vals.size else None,
                              p1=float(np.percentile(vals, 1)) if vals.size else None,
                              p99=float(np.percentile(vals, 99)) if vals.size else None,
                              min=int(vals.min()) if vals.size else None, max=int(vals.max()) if vals.size else None,
                              frac_zero_in_valid=float((vals == 0).mean()) if vals.size else None,
                              frac_out_zero=float((disp == 0).mean()), out_mean=float(disp.mean())),
                   full_res_u8_sha256=C.arr_sha(u8), chunks_missing=miss,
                   train_manifest_sha256=summ['train_manifest_sha256'], model_final_sha256=summ['model_final_sha256'],
                   min_dist_to_X_mm=(0.0 if C.in_x_zone(seg, r, c) else dist.get(name)),
                   train_min_dist_to_X_mm=summ['min_dist_to_X_mm'], seconds_total=round(time.time() - t0, 1),
                   utc=C.utc())
        if a.save_npz:
            os.makedirs(f'{a.out}/arrays', exist_ok=True)
            np.savez_compressed(f'{a.out}/arrays/{name}.npz', u8=u8, valid=m)
            rec['npz_sha256'] = C.sha256_file(f'{a.out}/arrays/{name}.npz')
        json.dump(rec, open(jp, 'w'), indent=1)
        log(rec)
    # manifest (P4-O format + P4-OWN fields), rebuilt from all tile records
    recs = [json.load(open(f'{a.out}/tiles/{f}')) for f in sorted(os.listdir(f'{a.out}/tiles')) if f.endswith('.json')]
    for rr in recs:
        assert C.sha256_file(os.path.join(a.out, rr['file'])) == rr['png_sha256']
    man = dict(provenance=C.PROV, declaration='RULES.md DECL-P4-23 (P4-OWN)', material=f'M-P4OWN-{arm}', arm=arm,
               surface_volume=C.VOL, level_used=0, slab=dict(slices=[C.Z0, C.Z1 - 1], n=C.NZ), order='forward',
               normalisation='clip(0,200)/255', model_final_sha256=summ['model_final_sha256'],
               train_manifest_sha256=summ['train_manifest_sha256'], train_min_dist_to_X_mm=summ['min_dist_to_X_mm'],
               recipe_sha256=summ['recipe_sha256'],
               display='raw prediction u8 = clip(p*255) truncated; 0 outside mesh-valid; INTER_AREA 8343 -> 1068; '
                       'PNG IHDR/IDAT/IEND (identical to P4-O)',
               n_tiles=len(recs), tiles=sorted(recs, key=lambda x: (x['seg'], x['r'], x['c'])),
               viewing='no tile, map or CT image was opened, displayed or described; numbers and hashes only',
               generated_utc=C.utc())
    json.dump(man, open(f'{a.out}/manifest.json', 'w'), indent=1)
    log(dict(manifest_sha256=C.sha256_file(f'{a.out}/manifest.json'), n_tiles=len(recs)))


if __name__ == '__main__':
    main()
