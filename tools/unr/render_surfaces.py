#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Owner-requested gallery of grown sheet surfaces of PHerc0268 (raw level-0 CT sampled ON each surface; no ink model, no claim about
ink or letters). Two sources: (a) ORD-3 tracker exports (grow_status.npz: rows every 4 sections; CLEAN anchored cells only, positions
interpolated linearly between two consecutive CLEAN rows, nothing filled across gaps); (b) VC3D tifxyz surfaces grown by HERCULES lanes
(grid upsampled bilinearly to the render pitch; cells outside the grid's valid mask stay black). Intensity: trilinear level-0 sample,
mean of the layers -1, 0, +1 along the surface normal, stretched p1-p99 of the valid pixels; invalid pixels black. A banner states the
source, the size in mm, the render pitch and the valid fraction; a 1 mm scale bar is drawn.
usage: render_surfaces.py ord3 <grow_status.npz> <out.png> --y0 5632 --title "..."
       render_surfaces.py tifxyz <tifxyz_dir> <out.png> --pitch 2 --max_side 2400 --title "..." """
import os, sys, json, argparse, numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import mesh_checks as MC
VOX = 8.64

def stretch(img, valid):
    out = np.zeros(img.shape, np.uint8)
    if valid.sum() > 100:
        lo, hi = np.percentile(img[valid], [1, 99]); out[valid] = (np.clip((img[valid] - lo) / (hi - lo + 1e-9), 0, 1) * 255).astype(np.uint8)
    return out

def annotate(arr, pitch_vox, lines, out):
    from PIL import Image, ImageDraw
    H, W = arr.shape; band = 16 * len(lines) + 10; can = Image.new('RGB', (max(W, 760), H + band), (18, 18, 18)); can.paste(Image.fromarray(arr).convert('RGB'), (0, band)); d = ImageDraw.Draw(can)
    for i, t in enumerate(lines): d.text((6, 4 + 16 * i), t, fill=(235, 235, 235))
    L = int(round(1000.0 / VOX / pitch_vox)); y = band + H - 12; x0 = 10
    if L < W - 20: d.rectangle([x0, y, x0 + L, y + 4], fill=(255, 200, 0)); d.text((x0, y - 14), '1 mm', fill=(255, 200, 0))
    can.save(out)

def sample_layers(store, P, N, valid, offs=(-1, 0, 1)):
    acc = np.zeros(valid.shape, np.float32); pts = P[valid]; nn = N[valid]
    for o in offs:
        v = np.zeros(valid.shape, np.float32); q = pts + o * nn; ok = np.isfinite(q).all(1); vv = np.zeros(len(q), np.float32); vv[ok] = store.sample(q[ok]); v[valid] = vv; acc += v
    return acc / len(offs)

def render_ord3(npz, out, y0, title, origin_y_is_block=True):
    G = np.load(npz); st = G['status'][:, 0]; pos = G['pos'][:, 0].astype(np.float64); ys = G['ys'].astype(np.int64); clean = G['clean'] if 'clean' in G.files else np.ones(st.shape, bool)
    order = np.argsort(ys); st, pos, ys, clean = st[order], pos[order], ys[order], clean[order]; ok = (st == 1) & clean; R, U = ok.shape
    sys.path.insert(0, HERE); import ord3
    nrm = np.stack([ord3.frame(pos[i], 3.0)[1] for i in range(R)])                                                  # in-section normal (z, x)
    Y = ys[-1] - ys[0] + 1; P = np.full((Y, U, 3), np.nan); N = np.full((Y, U, 3), np.nan); valid = np.zeros((Y, U), bool)
    for i in range(R - 1):
        both = ok[i] & ok[i + 1]; dy = ys[i + 1] - ys[i]
        for s in range(dy + (1 if i == R - 2 else 0)):
            t = s / dy; r = ys[i] - ys[0] + s; zx = (1 - t) * pos[i] + t * pos[i + 1]; nz = (1 - t) * nrm[i] + t * nrm[i + 1]; nz /= np.linalg.norm(nz, axis=1, keepdims=True) + 1e-9
            P[r, :, 0] = zx[:, 1]; P[r, :, 1] = ys[i] + s + y0; P[r, :, 2] = zx[:, 0]; N[r, :, 0] = nz[:, 1]; N[r, :, 1] = 0; N[r, :, 2] = nz[:, 0]; valid[r] = both
    store = MC.ChunkStore(MC.open_volume(MC.DEFAULT_VOLUME, threads=8)); img = sample_layers(store, P, N, valid); arr = stretch(img, valid)
    cols = np.nonzero(valid.any(0))[0]; arr = arr[:, cols.min():cols.max() + 1] if len(cols) else arr; v = valid[:, cols.min():cols.max() + 1] if len(cols) else valid
    lines = [title, f'{arr.shape[1] * VOX / 1000:.1f} mm along the sheet x {arr.shape[0] * VOX / 1000:.2f} mm along y (sections {ys[0] + y0}-{ys[-1] + y0}); 1 vox/px (8.64 um); CLEAN-anchored cells only: {v.mean():.1%} of the frame', 'raw CT on the surface (mean of layers -1..+1), p1-p99 stretch; black = no identity-kept cell; no ink model applied']
    annotate(arr, 1.0, lines, out); return {'out': out, 'shape': list(arr.shape), 'valid_frac': round(float(v.mean()), 4), 'MB_fetched': round(store.bytes / 1e6, 1)}

def render_tifxyz(d, out, pitch, max_side, title):
    m = MC.load_mesh(d); V, F, Nv = MC.mesh_arrays(m); Pg = m['P']; valid_g = m['valid']; sc = m['scale'][0]; H, W = valid_g.shape
    zoom = (1.0 / sc) / pitch; Hn, Wn = int(H * zoom), int(W * zoom)
    if max(Hn, Wn) > max_side: pitch = pitch * max(Hn, Wn) / max_side; zoom = (1.0 / sc) / pitch; Hn, Wn = int(H * zoom), int(W * zoom)
    Ng = np.zeros_like(Pg); Ng[valid_g] = np.nan_to_num(Nv); Pf = np.where(np.isnan(Pg), 0, Pg)
    yy, xx = np.mgrid[0:Hn, 0:Wn].astype(np.float32) / zoom
    P = np.stack([ndi.map_coordinates(Pf[..., c], [yy, xx], order=1, mode='nearest') for c in range(3)], -1); N = np.stack([ndi.map_coordinates(Ng[..., c], [yy, xx], order=1, mode='nearest') for c in range(3)], -1)
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-9; valid = ndi.map_coordinates(valid_g.astype(np.float32), [yy, xx], order=0, mode='constant') > 0.5
    # a pixel is valid only if all four surrounding grid cells are valid (no interpolation across holes)
    vg = valid_g.astype(np.float32); allv = ndi.minimum_filter(vg, size=2, origin=-1); valid &= ndi.map_coordinates(allv, [yy, xx], order=0, mode='constant') > 0.5
    img = np.zeros(valid.shape, np.float32); mb = 0.0; src = MC.open_volume(MC.DEFAULT_VOLUME, threads=8); T = 768                    # tiles of T x T px, one small chunk cache each (bounded memory)
    for r0 in range(0, Hn, T):
        for c0 in range(0, Wn, T):
            v = valid[r0:r0 + T, c0:c0 + T]
            if not v.any(): continue
            store = MC.ChunkStore(src); img[r0:r0 + T, c0:c0 + T] = sample_layers(store, P[r0:r0 + T, c0:c0 + T], N[r0:r0 + T, c0:c0 + T], v); mb += store.bytes / 1e6; del store
    arr = stretch(img, valid); store = type('S', (), {'bytes': mb * 1e6})()
    meta = m.get('meta', {}); area = meta.get('area_cm2')
    lines = [title, f'grid {H}x{W} cells at {1 / sc:.0f} vox/cell -> {Wn}x{Hn} px at {pitch:.1f} vox/px ({pitch * VOX:.0f} um/px); {Wn * pitch * VOX / 1000:.1f} x {Hn * pitch * VOX / 1000:.1f} mm frame' + (f'; surface area {area:.2f} cm2' if area else ''), f'raw CT on the surface (mean of layers -1..+1 along the grid normal), p1-p99 stretch; black = outside the grown grid; valid {valid.mean():.1%} of the frame; no ink model applied']
    annotate(arr, pitch, lines, out); return {'out': out, 'shape': list(arr.shape), 'pitch_vox': round(pitch, 2), 'valid_frac': round(float(valid.mean()), 4), 'MB_fetched': round(store.bytes / 1e6, 1), 'grid': [H, W], 'scale': sc, 'area_cm2': area}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('kind', choices=['ord3', 'tifxyz']); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--y0', type=int, default=5632); ap.add_argument('--pitch', type=float, default=2.0); ap.add_argument('--max_side', type=int, default=2400); ap.add_argument('--title', default='')
    a = ap.parse_args(); r = render_ord3(a.src, a.out, a.y0, a.title) if a.kind == 'ord3' else render_tifxyz(a.src, a.out, a.pitch, a.max_side, a.title); print(json.dumps(r))

if __name__ == '__main__': main()
