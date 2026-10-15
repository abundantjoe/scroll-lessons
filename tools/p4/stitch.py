# Provenance: Project HERCULES | [id removed]
"""Edge-connected stitching of P4 display tiles (numbers only; this script never displays an image).

Tile (r, c) of a strip covers canvas [r*T, (r+1)*T) x [c*T, (c+1)*T) and is shown at 1068 px (53.4 px/mm), so
neighbouring tiles abut exactly: placing tile (r, c) at pixel (r*1068, c*1068) reproduces the canvas without gaps or
overlap. Missing tiles stay 0 (the display value outside the mesh).

sheet   <out.png|out.jpg> <scale> <tile_png> [<tile_png> ...]
        Contact sheet of every given tile of ONE strip (names <seg>_r<R>_c<C>.png), over the bounding box of the given
        tiles, resized by <scale> with INTER_AREA (0.5 = 26.7 px/mm), plus a bottom margin with a 1 cm scale bar and
        row/column tick labels. Writes <out>.json: segment, rows, cols, scale, px_per_mm, and each tile's sha256.
windows <out_dir> <tile_dir> <seg> [--stride 1]
        4 x 4 cm reader windows: every 2 x 2 block of tiles (r..r+1, c..c+1) present in <tile_dir>, stitched (2136 px)
        and resized to 1068 px with INTER_AREA (26.7 px/mm, the frozen 'block' brief scale, METRIC-HASH-38). Named
        <seg>_r<R>_c<C>.png by the top-left tile; a manifest_norm.json (p4_jobs import format; valid_fraction = mean
        of the 4 tiles' fractions from their .png.json records if present, else the fraction of non-zero px) is written.
"""
import hashlib
import json
import os
import re
import sys

import cv2
import numpy as np

sys.path.insert(0, 'src')
TILE = 1068
PX_PER_MM = 53.4
NAME = re.compile(r'(?P<seg>.+)_r(?P<r>\d+)_c(?P<c>\d+)\.png$')


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def _read(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    assert a is not None and a.dtype == np.uint8 and a.shape == (TILE, TILE), p
    return a


def _parse(paths):
    tiles = {}
    for p in paths:
        m = NAME.search(os.path.basename(p))
        assert m, p
        tiles[(int(m['r']), int(m['c']))] = (m['seg'], p)
    segs = {s for s, _ in tiles.values()}
    assert len(segs) == 1, f'one strip per sheet, got {segs}'
    return segs.pop(), tiles


def cmd_sheet(out, scale, *paths):
    scale = float(scale)
    seg, tiles = _parse(paths)
    rs = [r for r, _ in tiles]
    cs = [c for _, c in tiles]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    H, W = (r1 - r0 + 1) * TILE, (c1 - c0 + 1) * TILE
    canvas = np.zeros((H, W), np.uint8)
    for (r, c), (_, p) in tiles.items():
        canvas[(r - r0) * TILE:(r - r0 + 1) * TILE, (c - c0) * TILE:(c - c0 + 1) * TILE] = _read(p)
    if scale != 1.0:
        canvas = cv2.resize(canvas, (round(W * scale), round(H * scale)), interpolation=cv2.INTER_AREA)
    ppmm = PX_PER_MM * scale
    h, w = canvas.shape
    margin = max(60, round(8 * ppmm))
    out_img = np.full((h + margin, w), 255, np.uint8)
    out_img[:h] = canvas
    bar = round(10 * ppmm)  # 1 cm
    y = h + margin // 2
    cv2.rectangle(out_img, (20, y - 6), (20 + bar, y + 6), 0, -1)
    fs = max(0.6, margin / 90)
    cv2.putText(out_img, '1 cm', (30 + bar, y + 8), cv2.FONT_HERSHEY_SIMPLEX, fs, 0, 2)
    step = TILE * scale
    for c in range(c0, c1 + 1):
        cv2.putText(out_img, f'c{c}', (round((c - c0) * step + 4), h + margin - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    fs * 0.6, 0, 1)
    params = [cv2.IMWRITE_JPEG_QUALITY, 92] if out.lower().endswith(('.jpg', '.jpeg')) else []
    assert cv2.imwrite(out, out_img, params), out
    meta = {'provenance': 'Project HERCULES | [id removed]', 'segment': seg, 'rows': [r0, r1], 'cols': [c0, c1],
            'scale': scale, 'px_per_mm': ppmm, 'scale_bar_px_per_cm': bar, 'row_labels': 'top to bottom r%d..r%d' % (r0, r1),
            'n_tiles': len(tiles), 'tiles': {f'r{r}_c{c}': _sha(p) for (r, c), (_, p) in sorted(tiles.items())},
            'out_sha256': _sha(out)}
    json.dump(meta, open(out + '.json', 'w'), indent=1)
    print(json.dumps({k: meta[k] for k in ('segment', 'rows', 'cols', 'n_tiles', 'px_per_mm')}))


def _vf(p, a):
    j = p + '.json'
    if os.path.exists(j):
        return float(json.load(open(j))['valid_fraction'])
    return float((a > 0).mean())


def cmd_windows(out_dir, tile_dir, seg, *opts):
    stride = int(opts[opts.index('--stride') + 1]) if '--stride' in opts else 1
    have = {}
    for f in os.listdir(tile_dir):
        m = NAME.search(f)
        if m and m['seg'] == seg:
            have[(int(m['r']), int(m['c']))] = os.path.join(tile_dir, f)
    os.makedirs(f'{out_dir}/tiles', exist_ok=True)
    rows = []
    for (r, c) in sorted(have):
        if r % stride or c % stride:
            continue
        quad = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
        if not all(q in have for q in quad):
            continue
        big = np.zeros((2 * TILE, 2 * TILE), np.uint8)
        vfs = []
        for (rr, cc) in quad:
            a = _read(have[(rr, cc)])
            big[(rr - r) * TILE:(rr - r + 1) * TILE, (cc - c) * TILE:(cc - c + 1) * TILE] = a
            vfs.append(_vf(have[(rr, cc)], a))
        win = cv2.resize(big, (TILE, TILE), interpolation=cv2.INTER_AREA)
        from hercules.display.builder import png_bytes
        name = f'{seg}_r{r}_c{c}.png'
        b = png_bytes(np.ascontiguousarray(win))
        open(f'{out_dir}/tiles/{name}', 'wb').write(b)
        rows.append({'r': r, 'c': c, 'sha256': hashlib.sha256(b).hexdigest(), 'valid_fraction': float(np.mean(vfs)),
                     'window': '2x2 tiles r%d-%d c%d-%d, 4 x 4 cm, 26.7 px/mm' % (r, r + 1, c, c + 1),
                     'src_sha256': [_sha(have[q]) for q in quad]})
    json.dump({'segment': seg, 'kind': 'stitched 2x2 window (tools/p4/stitch.py windows)', 'tiles': rows},
              open(f'{out_dir}/manifest_norm.json', 'w'), indent=1)
    print(json.dumps({'segment': seg, 'n_windows': len(rows), 'n_tiles_in': len(have)}))


if __name__ == '__main__':
    {'sheet': cmd_sheet, 'windows': cmd_windows}[sys.argv[1]](*sys.argv[2:])
