#!/usr/bin/env python3
"""bi_post.py: ensemble maps, overlays, fibre-visible renders and the stats JSON of one batch surface (scripts/pipeline/batch_ink.sh).

  python -I bi_post.py WORK_DIR [--ens-depth 1] [--tile-nodes 12] [--gate GATE.json] [--small-dir DIR] [--max-small-mb 1.9]

WORK_DIR holds prep.json, render.zarr (66 layers; layer k samples the CT at k - 32.5 vox along the outward normal),
ink/<model>__s<S>_reverse.tif (villa, uint8 = trunc(255 p), S = 25 + d) and logs/.
Only the reverse (reading side, Erwin's convention with outward normals) maps are used.
  p             villa uint8 / 255 (the scale of scripts/pipeline/overlay.py)
  ensemble d    mean of the three models' maps at depth d; ens_d1 = the overlay map of overlay.py
  dmax          per-pixel max over d in {0,1,2} of the per-depth ensembles (dmax_all: over every depth present)
  overlay       overlay.py semantics: CT layer 34, stretched p1..p99.5 over valid pixels, dimmed to 55 %;
                alpha = clip((p - 0.40) / 0.30, 0, 1), colour (1, .62, .12); valid = layer 33 > 0
  fibre         CT layer 33 and mean of layers 31-35, stretched p1..p99.5 over valid pixels
  tiles         node-grid tiles of --tile-nodes nodes (12 nodes = 240 px = 2.07 mm at 20 vox/node); node ranges are given
                in this surface's grid and in the source mesh's grid (prep.json crop offsets), so they intersect with
                gate-JSON tiles (the tile gate tool is not in this release). --gate: also the stats over every tile of that gate JSON, with its verdict.
Writes WORK_DIR/{ens_d*.tif, ens_dmax.tif, overlay_d1.png, overlay_dmax.png, fibre_l33.png, fibre_m31-35.png,
ctlayers_31-35.tif, stats.json} and small copies (<= --max-small-mb) of the PNGs and stats.json in --small-dir.
"""
import argparse, glob, json, os, re, sys, time
import numpy as np, tifffile, zarr
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_common as C  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('work'); ap.add_argument('--ens-depth', type=int, default=1); ap.add_argument('--tile-nodes', type=int, default=12)
ap.add_argument('--gate'); ap.add_argument('--gate-offset', default='auto'); ap.add_argument('--small-dir')
ap.add_argument('--max-small-mb', type=float, default=1.9)
a = ap.parse_args()
t0 = time.time(); W = a.work.rstrip('/')
prep = json.load(open(f'{W}/prep.json')); name = prep['name']; step = prep['step_vox']
r = zarr.open(f'{W}/render.zarr', mode='r')['0']; D, H, Wd = r.shape
assert D == 66, f'expected a 66-layer render, got {r.shape}'
L = {k: np.asarray(r[k]) for k in range(31, 36)}
valid = L[33] > 0; nv = int(valid.sum())
valid_all = np.ones((H, Wd), bool); PL = np.arange(18, 49)          # layer profile window: d -15..+15
LS = np.zeros((len(PL), H, Wd), np.uint8)
for y0 in range(0, H, 256):
    blk = np.asarray(r[:, y0:y0 + 256]); valid_all[y0:y0 + 256] = (blk > 0).all(0); LS[:, y0:y0 + 256] = blk[PL]


def layer_profile(m, ys=slice(None), xs=slice(None)):
    """mean CT per layer 18..48 over the pixels m; peak layer and contrast peak / min (on-sheet test 1: |peak - 33| <= 3
    and contrast > 1.02)."""
    if m.sum() < 50: return None
    pr = np.array([float(LS[i, ys, xs][m].mean(dtype=np.float64)) for i in range(len(PL))]); k = int(np.argmax(pr)); c = float(pr[k] / max(pr.min(), 1e-6))
    # own-sheet variant: the same test inside layers 25..41 (+-8 = half the PHerc0268 sheet spacing), so a brighter
    # neighbouring sheet ~16 layers away cannot take the peak; the peak must be an interior local maximum
    w = pr[7:24]; kl = int(np.argmax(w)); cl = float(w[kl] / max(w.min(), 1e-6)); interior = 0 < kl < len(w) - 1
    return dict(peak_layer=int(PL[k]), contrast=round(c, 4), ok=bool(abs(PL[k] - 33) <= 3 and c > 1.02),
                peak_local=int(25 + kl), contrast_local=round(cl, 4), ok_local=bool(interior and abs(kl + 25 - 33) <= 3 and cl > 1.02),
                prof=[round(float(v), 2) for v in pr])


tifffile.imwrite(f'{W}/ctlayers_31-35.tif', np.stack([L[k] for k in range(31, 36)]), compression='zlib')


def stretch(img, m):
    img = img.astype(np.float32); v = img[m]; lo, hi = np.percentile(v, 1), np.percentile(v, 99.5)   # float32 as overlay.py
    return np.clip((img - lo) / (hi - lo), 0, 1), [float(lo), float(hi)]


def overlay(ct, m, P):
    base, st = stretch(ct, m); base = base * 0.55
    al = np.clip((P - 0.40) / 0.30, 0, 1); col = np.array([1.0, 0.62, 0.12])   # float64, as overlay.py
    rgb = base[..., None] * (1 - al[..., None]) + col * al[..., None]; rgb[~m] = 0
    return (rgb * 255).astype(np.uint8), st


# ---- maps
maps = {}
for f in glob.glob(f'{W}/ink/*__s*_reverse.tif'):
    mm = re.match(r'(.+)__s(\d+)_reverse\.tif$', os.path.basename(f))
    if not mm or mm.group(1) not in C.MODELS: continue
    A = tifffile.imread(f)
    if A.shape != (H, Wd): raise SystemExit(f'{f}: shape {A.shape} != render {(H, Wd)}')
    maps[(mm.group(1), int(mm.group(2)) - 25)] = A.astype(np.float32) / 255.
depths = sorted({d for _, d in maps}); ens = {}
for d in depths:
    ms = [maps[(m, d)] for m in C.MODELS if (m, d) in maps]
    if len(ms) == len(C.MODELS): ens[d] = np.mean(ms, 0)
if a.ens_depth not in ens: raise SystemExit(f'ensemble depth {a.ens_depth} incomplete; have {sorted(ens)} from {sorted(maps)}')
P1 = ens[a.ens_depth]
d012 = [d for d in (0, 1, 2) if d in ens] or sorted(ens)   # review fix: depths without 0..2 (e.g. DEPTHS=-1) crashed here
Pmax = np.max([ens[d] for d in d012], 0)
Pmax_all = np.max([ens[d] for d in ens], 0)
for d, E in ens.items(): tifffile.imwrite(f'{W}/ens_d{d}.tif', np.round(E * 255).astype(np.uint8), compression='zlib')
# review addition: face specificity (needs INK_DIR=both). The forward map at the same S reads the same 17 layers in the
# opposite order (= the other face). Recto ink is face-specific: on the PHerc0343 letters control (S26) r(fwd, rev) =
# 0.07 and 99 % of the reverse p>0.55 pixels have forward p<0.40; on a PHerc0268 test surface (S26) r = 0.73 and only 5 % do.
fwd_ens = {}
for d in ens:
    fs_ = [f'{W}/ink/{m}__s{25 + d}.tif' for m in C.MODELS]
    if all(os.path.exists(f) for f in fs_):
        fwd_ens[d] = np.mean([tifffile.imread(f).astype(np.float32) / 255. for f in fs_], 0)
        tifffile.imwrite(f'{W}/ens_fwd_d{d}.tif', np.round(fwd_ens[d] * 255).astype(np.uint8), compression='zlib')
tifffile.imwrite(f'{W}/ens_dmax.tif', np.round(Pmax * 255).astype(np.uint8), compression='zlib')

ov1, st34 = overlay(L[34], valid, P1); Image.fromarray(ov1).save(f'{W}/overlay_d1.png')
ovm, _ = overlay(L[34], valid, Pmax); Image.fromarray(ovm).save(f'{W}/overlay_dmax.png')
f33, st33 = stretch(L[33], valid); f33[~valid] = 0; Image.fromarray((f33 * 255).astype(np.uint8)).save(f'{W}/fibre_l33.png')
mean5 = np.mean([L[k].astype(np.float32) for k in range(31, 36)], 0)
fm, stm = stretch(mean5, valid); fm[~valid] = 0; Image.fromarray((fm * 255).astype(np.uint8)).save(f'{W}/fibre_m31-35.png')

PCT = [1, 5, 25, 50, 75, 90, 95, 99, 99.9]


def summ(P, m=valid):
    v = P[m]
    return dict(frac_p040=round(float((v > 0.40).mean()), 5), frac_p055=round(float((v > 0.55).mean()), 5),
                mean=round(float(v.mean()), 4), pct={str(q): round(float(np.percentile(v, q)), 4) for q in PCT})


def corr(A, B, m=valid):
    x, y = A[m].astype(np.float64), B[m].astype(np.float64)
    return round(float(np.corrcoef(x, y)[0, 1]), 4)


per_map = {f'{m}__d{d:+d}': summ(maps[(m, d)]) for (m, d) in sorted(maps)}
inter_model = {}
for d in depths:
    have = [m for m in C.MODELS if (m, d) in maps]
    inter_model[f'd{d:+d}'] = {f'{have[i][:22]}|{have[j][:22]}': corr(maps[(have[i], d)], maps[(have[j], d)])
                               for i in range(len(have)) for j in range(i + 1, len(have))}
inter_depth = {f'd{d0:+d}|d{d1:+d}': corr(ens[d0], ens[d1]) for i, d0 in enumerate(sorted(ens)) for d1 in sorted(ens)[i + 1:]}


def face_stats(R_, F_, m=valid):
    rv, fv = R_[m], F_[m]; n055 = float((rv > 0.55).mean()); fsp = float(((rv > 0.55) & (fv < 0.40)).mean())
    return dict(r_fwd_rev=round(float(np.corrcoef(rv, fv)[0, 1]), 4), rev_p055=round(n055, 5), fwd_p055=round(float((fv > 0.55).mean()), 5),
                both_p055=round(float(((rv > 0.55) & (fv > 0.55)).mean()), 5), rev_p055_face_specific=round(fsp, 5),
                face_specific_share=round(fsp / n055, 4) if n055 > 0 else None)


face = {f'd{d:+d}': face_stats(ens[d], fwd_ens[d]) for d in sorted(fwd_ens)} or None
FS1 = fwd_ens.get(a.ens_depth)                    # forward ensemble at the overlay depth (None without INK_DIR=both)

# ---- tiles (node grid)
tn = a.tile_nodes; nr, nc = prep['grid']; X, Y, Z, ok = C.load_xyz(f'{W}/{name}')
qa = C.quad_area_vox2(X, Y, Z, ok, step) * C.VOX_UM ** 2 / 1e8
s = int(round(step)); r0s, c0s = prep['crop']['src_row0'], prep['crop']['src_col0']


def tile_stats(R0, R1, C0, C1):
    y0, y1, x0, x1 = R0 * s, min(R1 * s, H), C0 * s, min(C1 * s, Wd)
    m = valid[y0:y1, x0:x1]; n = int(m.sum()); o = dict(px=[y0, y1, x0, x1], valid_px=n,
                                                    area_cm2=round(float(np.nansum(qa[R0:min(R1, nr - 1), C0:min(C1, nc - 1)])), 4))
    if n < 50: return o
    p1 = P1[y0:y1, x0:x1][m]; pm = Pmax[y0:y1, x0:x1][m]
    lp = layer_profile(m, slice(y0, y1), slice(x0, x1))
    if lp: o.update(profile_peak=lp['peak_layer'], profile_contrast=lp['contrast'], profile_ok=lp['ok'],
                    profile_peak_local=lp['peak_local'], profile_contrast_local=lp['contrast_local'], profile_ok_local=lp['ok_local'])
    o.update(ink_p040=round(float((p1 > 0.40).mean()), 4), ink_p055=round(float((p1 > 0.55).mean()), 4),
             dmax_p040=round(float((pm > 0.40).mean()), 4), dmax_p055=round(float((pm > 0.55).mean()), 4),
             mean_p=round(float(p1.mean()), 4), p99=round(float(np.percentile(p1, 99)), 4))
    if FS1 is not None:
        f1 = FS1[y0:y1, x0:x1][m]; o.update(ink_p055_face_specific=round(float(((p1 > 0.55) & (f1 < 0.40)).mean()), 4),
                                           fwd_p055=round(float((f1 > 0.55).mean()), 4))
    return o


tiles = {}
for i, R0 in enumerate(range(0, nr, tn)):
    for j, C0 in enumerate(range(0, nc, tn)):
        R1, C1 = min(R0 + tn, nr), min(C0 + tn, nc)
        t = tile_stats(R0, R1, C0, C1)
        if t['valid_px'] == 0: continue
        t.update(nodes=[R0, R1, C0, C1], src_nodes=[R0 + r0s, R1 + r0s, C0 + c0s, C1 + c0s]); tiles[f'r{i}c{j}'] = t
pt = [t for t in tiles.values() if 'profile_ok' in t]
tiles_summary = dict(n=len(tiles), n_profiled=len(pt), n_profile_ok=sum(t['profile_ok'] for t in pt),
                     n_profile_ok_local=sum(t['profile_ok_local'] for t in pt),
                     ink_p040_profile_ok=round(float(np.average([t['ink_p040'] for t in pt if t['profile_ok']],
                                                                 weights=[t['valid_px'] for t in pt if t['profile_ok']])), 4) if any(t['profile_ok'] for t in pt) else None,
                     ink_p040_profile_fail=round(float(np.average([t['ink_p040'] for t in pt if not t['profile_ok']],
                                                                   weights=[t['valid_px'] for t in pt if not t['profile_ok']])), 4) if any(not t['profile_ok'] for t in pt) else None)
gate_tiles = None
if a.gate:
    G = json.load(open(a.gate)); gs = G['summary']['surface'].rstrip('/')
    if a.gate_offset == 'auto':
        off = (r0s, c0s) if os.path.abspath(gs) == prep['src'].rstrip('/') else (0, 0)
    else:
        off = tuple(int(v) for v in a.gate_offset.split(','))
    gate_tiles = dict(gate=os.path.abspath(a.gate), gate_surface=gs, offset_rows_cols=list(off), tiles={})
    for k, gt in G['tiles'].items():
        R0, R1, C0, C1 = gt['r0'] - off[0], gt['r1'] - off[0], gt['c0'] - off[1], gt['c1'] - off[1]
        if R1 <= 0 or C1 <= 0 or R0 >= nr or C0 >= nc: continue
        R0, C0 = max(R0, 0), max(C0, 0); R1, C1 = min(R1, nr), min(C1, nc)
        t = tile_stats(R0, R1, C0, C1); t.update(nodes=[R0, R1, C0, C1], verdict=gt.get('verdict'), ang=gt.get('ang'), gate_why=gt.get('why'),
                                                 peak=gt.get('peak'), contrast=gt.get('contrast'))
        gate_tiles['tiles'][k] = t
    on = [t for t in gate_tiles['tiles'].values() if t.get('verdict') == 'ON_SHEET' and t['valid_px'] >= 50]
    gate_tiles['n_on_sheet'] = len(on)
    if on:
        w = np.array([t['valid_px'] for t in on], float)
        gate_tiles['on_sheet_ink_p040'] = round(float(np.average([t['ink_p040'] for t in on], weights=w)), 4)
        gate_tiles['on_sheet_ink_p055'] = round(float(np.average([t['ink_p055'] for t in on], weights=w)), 4)
        if FS1 is not None:
            gate_tiles['on_sheet_ink_p055_face_specific'] = round(float(np.average([t['ink_p055_face_specific'] for t in on], weights=w)), 4)

# ---- timing from logs
timing = {}
for f in sorted(glob.glob(f'{W}/logs/ink_*.log')):
    txt = open(f).read(); w_ = re.search(r'E2E_WALL_S ([\d.]+)', txt); rss = re.search(r'PEAK_RSS_MB (\d+)', txt)
    pt = re.search(r'Selected (\d+) patches', txt)
    key = os.path.basename(f)[4:-4]; ndir = max(1, txt.count('Selected source layer indices'))   # review fix: INK_DIR=both = 2
    timing[key] = dict(wall_s=float(w_.group(1)) / ndir if w_ else None, directions=ndir, peak_rss_mb=int(rss.group(1)) if rss else None,
                       patches=int(pt.group(1)) if pt else None)
mpx = H * Wd / 1e6
walls = [v['wall_s'] for v in timing.values() if v['wall_s']]
stage = {}
if os.path.exists(f'{W}/timing.tsv'):
    for line in open(f'{W}/timing.tsv'):
        k, v = line.split()[:2]; stage[k] = float(v)
out = dict(name=name, scroll=prep['scroll'], src=prep['src'], crop=prep['crop'], grid=prep['grid'], render_shape=[D, H, Wd],
           render_mpx=round(mpx, 4), valid_px=nv, valid_frac=round(nv / (H * Wd), 4), valid_all66_px=int(valid_all.sum()),
           mesh_area_cm2=prep['area_cm2'], outward_fraction=prep['outward_fraction'], flip_normals=prep['flip_normals'],
           orientation=prep['orientation'], theta_deg=prep['theta_deg'], z_vox=prep['z_vox'],
           convention='villa reverse maps only (reading side, outward normals); S = 25 + d, layers S..S+16; p = uint8/255',
           depths=depths, ens_depth=a.ens_depth, dmax_depths=d012,
           layer_profile=(lambda lp: dict(lp, band_matched_depth=lp['peak_layer'] - 34,
                                          note='band_matched_depth = d whose 17-layer window centre (33 + d) lies 1 layer inside '
                                               'the CT band peak of this estimator (mean CT per layer over valid pixels), as d = +1 '
                                               'does on the PHerc0343 letters control (peak 35 by this estimator)'))(layer_profile(valid)),
           ensemble_d1=summ(P1), ensemble_dmax=summ(Pmax), ensemble_dmax_all=summ(Pmax_all),
           ensemble_by_depth={f'd{d:+d}': summ(E) for d, E in sorted(ens.items())}, per_map=per_map,
           inter_model_r=inter_model, inter_depth_r=inter_depth,
           face_specificity=face, face_note='forward vs reverse ensembles at the same S (INK_DIR=both); references: '
                                            'PHerc0343 letters control S26 r 0.07, face_specific_share 0.99; PHerc0268 test surface S26 '
                                            'r 0.73, share 0.05 (review_batch, 2026-10-11)',
           display_stretch=dict(ct34=st34, ct33=st33, mean31_35=stm),
           tile_nodes=tn, tile_mm=round(tn * step * C.VOX_UM / 1000, 3), tiles_summary=tiles_summary, tiles=tiles, gate_tiles=gate_tiles,
           timing=dict(ink_runs=timing, ink_wall_s_total=round(sum(v['wall_s'] * v['directions'] for v in timing.values() if v['wall_s']), 1),
                       ink_note='wall_s and ink_s_per_mpx_per_run are per direction (a both-direction run counts twice)',
                       ink_s_per_mpx_per_run=round(float(np.median(walls)) / mpx, 1) if walls else None, stages_s=stage,
                       post_s=round(time.time() - t0, 1)))
json.dump(out, open(f'{W}/stats.json', 'w'), indent=1)

if a.small_dir:
    os.makedirs(a.small_dir, exist_ok=True)
    json.dump(out, open(f'{a.small_dir}/stats.json', 'w'), indent=1)
    for fn in ('overlay_d1.png', 'overlay_dmax.png', 'fibre_l33.png', 'fibre_m31-35.png'):
        im = Image.open(f'{W}/{fn}'); k = 1
        while True:
            sm = im if k == 1 else im.resize((max(1, im.width // k), max(1, im.height // k)), Image.LANCZOS)
            p = f'{a.small_dir}/{fn}'; sm.save(p, optimize=True)
            if os.path.getsize(p) <= a.max_small_mb * 1e6: break
            k += 1
print(json.dumps(dict(name=name, mpx=round(mpx, 3), band_peak=out['layer_profile']['peak_layer'], band_contrast=out['layer_profile']['contrast'],
                      tiles_profile_ok=f"{tiles_summary['n_profile_ok']}/{tiles_summary['n_profiled']}",
                      tiles_profile_ok_local=f"{tiles_summary['n_profile_ok_local']}/{tiles_summary['n_profiled']}", ens_d1=out['ensemble_d1']['frac_p040'], ens_d1_p055=out['ensemble_d1']['frac_p055'],
                      inter_model_r_d1=inter_model.get(f'd{a.ens_depth:+d}'), face=(face or {}).get(f'd{a.ens_depth:+d}'), post_s=out['timing']['post_s'])))
