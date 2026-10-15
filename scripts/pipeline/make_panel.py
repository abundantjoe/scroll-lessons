#!/usr/bin/env python3
"""make_panel.py: submission-style image of one batch surface: the fixed-scale ink overlay (scripts/pipeline/overlay.py
semantics) on the dimmed fibre-visible CT layer, a 1 cm scale bar and a caption, named after the tifxyz mesh.

  python -I make_panel.py WORK_DIR --out-dir DIR [--variant d1|dmax] [--area R0:R1,C0:C1 | --auto-area] [--gate G.json]
                          [--orient reading|raw] [--max-cm2 4.0] [--ct-layer 34]

WORK_DIR = a scripts/pipeline/batch_ink.sh surface directory (prep.json, <mesh>/ tifxyz, ctlayers_31-35.tif or render.zarr,
ens_d1.tif / ens_dmax.tif). Output DIR/<mesh name>.png (prize rule: the image is named after the tifxyz mesh) and
DIR/<mesh name>.json (provenance: geometry sha256, maps sha256, area in raw and reading pixels, 3D mesh area of the area,
pixel size, orientation, stretch, command line).
Every pixel inside the image frame is computed from the CT render and the ink map: CT layer (default 34 = d +1),
stretched p1..p99.5 over the valid pixels of the WHOLE surface, x 0.55; ink alpha = clip((p - 0.40) / 0.30, 0, 1),
colour (1, .62, .12). Nothing is drawn on the data: the caption is above and the scale bar below the frame.
--area   raw render pixels (row range, column range; end exclusive). Default: the whole surface.
--auto-area  the window (<= --max-cm2 of 3D mesh area) with the most pixels p > 0.55, restricted to ON_SHEET tiles of
         --gate when given; a screening convenience, recorded in the sidecar as such.
--orient reading = high z at the top and theta decreasing to the right (Erwin's rule, measured from the mesh and the
         umbilicus in prep.json); raw = render orientation.
"""
import argparse, hashlib, json, os, sys
import numpy as np, tifffile
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_common as C  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('work'); ap.add_argument('--out-dir', required=True); ap.add_argument('--variant', default='d1')
ap.add_argument('--area'); ap.add_argument('--auto-area', action='store_true'); ap.add_argument('--gate')
ap.add_argument('--orient', default='reading', choices=('reading', 'raw')); ap.add_argument('--max-cm2', type=float, default=4.0)
ap.add_argument('--ct-layer', type=int, default=34); ap.add_argument('--small-copy', help='also save a copy <= 1.9 MB here')
a = ap.parse_args()
W = a.work.rstrip('/'); prep = json.load(open(f'{W}/prep.json')); name = prep['name']; step = prep['step_vox']; s = int(round(step))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
if os.path.exists(f'{W}/ctlayers_31-35.tif') and 31 <= a.ct_layer <= 35:
    ct = tifffile.imread(f'{W}/ctlayers_31-35.tif')[a.ct_layer - 31]; v33 = tifffile.imread(f'{W}/ctlayers_31-35.tif')[2]
    ct_src = f'{W}/ctlayers_31-35.tif'
else:
    import zarr
    r = zarr.open(f'{W}/render.zarr', mode='r')['0']; ct = np.asarray(r[a.ct_layer]); v33 = np.asarray(r[33]); ct_src = f'{W}/render.zarr'
valid = v33 > 0; H, Wd = ct.shape
def ens(d):
    fs = [f'{W}/ink/{m}__s{25 + d}_reverse.tif' for m in C.MODELS]
    return (np.mean([tifffile.imread(f).astype(np.float32) / 255. for f in fs], 0), fs) if all(os.path.exists(f) for f in fs) else (None, fs)


ink_path = f'{W}/ens_{a.variant}.tif'; ink_files = [ink_path]
if a.variant.startswith('d') and a.variant[1:].lstrip('+-').isdigit():
    P, ink_files = ens(int(a.variant[1:]))                       # exact float ensemble (overlay.py arithmetic)
elif a.variant == 'dmax':
    E = [ens(d) for d in (0, 1, 2)]; E = [e for e in E if e[0] is not None]
    P = np.max([e[0] for e in E], 0) if E else None; ink_files = sum([e[1] for e in E], [])
else:
    P = None
if P is None:
    P = tifffile.imread(ink_path).astype(np.float32) / 255.; ink_files = [ink_path]
assert P.shape == ct.shape
X, Y, Z, ok = C.load_xyz(f'{W}/{name}')
qa = C.quad_area_vox2(X, Y, Z, ok, step); qa = np.nan_to_num(qa)        # vox^2 per quad
# per-pixel 3D area (vox^2): quad area spread over its s x s pixels
pa = np.kron(qa, np.ones((s, s)))[:H, :Wd] / (s * s)
if pa.shape != (H, Wd): pa = np.pad(pa, ((0, H - pa.shape[0]), (0, Wd - pa.shape[1])))
cm2 = C.VOX_UM ** 2 / 1e8
area_note = 'given'
if a.area:
    rr, cc = a.area.split(','); y0, y1 = (int(v) for v in rr.split(':')); x0, x1 = (int(v) for v in cc.split(':'))
elif a.auto_area:
    m = valid & (P > 0.55)
    if a.gate:
        G = json.load(open(a.gate)); gm = np.zeros_like(valid)
        off = (prep['crop']['src_row0'], prep['crop']['src_col0']) if os.path.abspath(G['summary']['surface'].rstrip('/')) == prep['src'].rstrip('/') else (0, 0)
        for t in G['tiles'].values():
            if t.get('verdict') == 'ON_SHEET':
                gm[max(0, (t['r0'] - off[0]) * s):max(0, (t['r1'] - off[0]) * s), max(0, (t['c0'] - off[1]) * s):max(0, (t['c1'] - off[1]) * s)] = True
        m &= gm
    I = np.pad(m.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    A = np.pad(pa.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    box = lambda S, y0, y1, x0, x1: S[y1, x1] - S[y0, x1] - S[y1, x0] + S[y0, x0]
    best = None; side = int(np.sqrt(a.max_cm2 / cm2))          # px side of a flat square of max area
    hs = sorted({min(H, side)} | ({H} if H < side else set()))
    for h in hs:
        for y0 in range(0, H - h + 1, s * 2):
            y1 = y0 + h; x0 = 0
            for x1 in range(s, Wd + 1, s):
                while box(A, y0, y1, x0, x1) * cm2 > a.max_cm2: x0 += s
                sc = box(I, y0, y1, x0, x1)
                if best is None or sc > best[0]: best = (int(sc), y0, y1, x0, x1)
    _, y0, y1, x0, x1 = best; area_note = f'auto: max count of p>0.55 pixels{" on ON_SHEET gate tiles" if a.gate else ""} within <= {a.max_cm2} cm2 (screening convenience)'
else:
    y0, y1, x0, x1 = 0, H, 0, Wd
area3d = float(pa[y0:y1, x0:x1].sum()) * cm2; nvalid = int(valid[y0:y1, x0:x1].sum())
px_um = float(np.sqrt(pa[y0:y1, x0:x1][valid[y0:y1, x0:x1]].mean())) * C.VOX_UM if nvalid else float('nan')
# whole-surface CT stretch (as overlay.py), then crop
ct = ct.astype(np.float32); v = ct[valid]; lo, hi = np.percentile(v, 1), np.percentile(v, 99.5)   # float32 as overlay.py
base = np.clip((ct - lo) / (hi - lo), 0, 1) * 0.55
al = np.clip((P - 0.40) / 0.30, 0, 1); col = np.array([1.0, 0.62, 0.12])   # float64, as overlay.py
rgb = base[..., None] * (1 - al[..., None]) + col * al[..., None]; rgb[~valid] = 0
img = (rgb[y0:y1, x0:x1] * 255).astype(np.uint8)
o = prep['orientation']
if a.orient == 'reading':
    if o['flip_ud']: img = img[::-1]
    if o['flip_lr']: img = img[:, ::-1]
h, w = img.shape[:2]
bar = 10000.0 / C.VOX_UM                                  # 1 cm in render pixels (1 px = 1 voxel along the mesh)
F = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
fs = max(14, min(36, int(w / 60))); top = int(fs * 3.2); bot = int(fs * 3.5); pad = 20
Wc = max(w, int(bar) + 2 * pad, 900) + 2 * pad; Hc = h + top + bot
can = Image.new('RGB', (Wc, Hc), (0, 0, 0)); can.paste(Image.fromarray(img), (pad, top))
dr = ImageDraw.Draw(can)
lab = {'d1': 'ink = mean of 3 villa models, reverse (reading side), d = +1 (layers 26-42)',
       'dmax': 'ink = max over d 0..+2 of the mean of 3 villa models, reverse (reading side)'}.get(a.variant, a.variant)
if a.variant not in ('d1', 'dmax') and a.variant.startswith('d') and a.variant[1:].lstrip('+-').isdigit():   # review fix
    _d = int(a.variant[1:]); lab = f'ink = mean of 3 villa models, reverse (reading side), d = {_d:+d} (layers {25 + _d}-{41 + _d})'
dr.text((pad, int(fs * 0.3)), f'{name}   |   {prep["scroll"]}   |   {"reading orientation" if a.orient == "reading" else "raw render orientation"}',
        fill=(255, 255, 255), font=F(fs))
dr.text((pad, int(fs * 1.6)), f'{lab}; overlay alpha = p 0.40-0.70; CT layer {a.ct_layer} (d {a.ct_layer - 33:+d}) dimmed; '
        f'area {area3d:.2f} cm2 (3D mesh)', fill=(200, 200, 200), font=F(int(fs * 0.8)))
yb = top + h + int(fs * 0.9); dr.rectangle([pad, yb, pad + bar, yb + max(4, fs // 3)], fill=(255, 255, 255))
dr.text((pad + bar + 12, yb - int(fs * 0.35)), '1 cm', fill=(255, 255, 255), font=F(fs))
if np.isfinite(px_um) and abs(px_um / C.VOX_UM - 1) > 0.05:      # review fix: flag non-isometric meshes next to the bar
    dr.text((pad + bar + 12 + 4 * fs, yb - int(fs * 0.2)), f'(bar at nominal 8.64 um/px; mesh px here {px_um:.2f} um = '
            f'{100 * (px_um / C.VOX_UM - 1):+.0f} %)', fill=(255, 200, 120), font=F(int(fs * 0.7)))
os.makedirs(a.out_dir, exist_ok=True); out = f'{a.out_dir}/{name}.png'; can.save(out, optimize=True)
side = dict(image=os.path.abspath(out), mesh=name, scroll=prep['scroll'], mesh_dir=os.path.abspath(f'{W}/{name}'),
            geometry_sha256={c: sha(f'{W}/{name}/{c}') for c in ('x.tif', 'y.tif', 'z.tif')},
            ink_maps={os.path.abspath(f): sha(f) for f in ink_files}, variant=a.variant, ct_source=ct_src, ct_layer=a.ct_layer,
            ct_stretch_whole_surface=[float(lo), float(hi)], area_raw_px=dict(row0=y0, row1=y1, col0=x0, col1=x1), area_selection=area_note,
            area_cm2_3d=round(area3d, 4), over_max_cm2=bool(area3d > a.max_cm2), valid_px=nvalid, mean_px_um=round(px_um, 3),
            orientation=dict(mode=a.orient, **o), scale_bar_px=round(bar, 1), frame_offset_px=[pad, top],
            ink_in_area=dict(frac_p040=round(float((P[y0:y1, x0:x1][valid[y0:y1, x0:x1]] > 0.40).mean()), 4) if nvalid else None,
                             frac_p055=round(float((P[y0:y1, x0:x1][valid[y0:y1, x0:x1]] > 0.55).mean()), 4) if nvalid else None),
            annotation='none (no letters drawn or marked); caption above and scale bar below the image frame',
            command=' '.join(sys.argv))
json.dump(side, open(f'{a.out_dir}/{name}.json', 'w'), indent=1)
if a.small_copy:
    os.makedirs(a.small_copy, exist_ok=True); k = 1
    while True:
        sm = can if k == 1 else can.resize((can.width // k, can.height // k), Image.LANCZOS)
        sm.save(f'{a.small_copy}/{name}.png', optimize=True)
        if os.path.getsize(f'{a.small_copy}/{name}.png') <= 1.9e6: break
        k += 1
    json.dump(dict(side, small_copy_downscale=k), open(f'{a.small_copy}/{name}.json', 'w'), indent=1)
print(json.dumps({k: side[k] for k in ('image', 'area_raw_px', 'area_cm2_3d', 'over_max_cm2', 'mean_px_um', 'ink_in_area')}))
