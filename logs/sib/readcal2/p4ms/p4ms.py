# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4 multi-scale display builder (readcal2 / p4ms). Numbers and PNG bytes only; the builder never opens or views an
image.

Input: a P4 tile set in the pairs0814b e2 / p4-l2 manifest format (manifest.json with tiles [{r, c, valid_fraction,
png_sha256, canvas_rows?, canvas_cols?}] + the strip-a grid: T_canvas_px, px_per_mm, canvas_shape), and a CHANNEL
SOURCE: any callable  source(y0, y1, x0, x1) -> (values, valid)  returning the material's per-canvas-pixel channel
(e.g. P4-L: level-0 max over slices 48..60; E2: +-53 um slab mean) and mesh-valid mask over a canvas rectangle
(pixels outside the canvas: value 0, not valid). The channel is the material's declared one; this builder changes
ONLY the display scale.

Scales (all from the same canvas, downscale only, cv2.INTER_AREA, 1068 px output):
  S4  whole-block windows: 2 x 2 tiles = 2 T canvas px (4 cm at 417.13 px/mm) -> 1068 px = 26.7 px/mm
  S2  the current tiles:   T = 8343 canvas px (2 cm)                            -> 1068 px = 53.4 px/mm
  S1  1 cm zooms:          the 4 quadrants of a tile (T//2 or T - T//2 px)       -> 1068 px = 106.8 px/mm
Value mapping (declared per material; identical function at every scale):
  'global'  L2: clip(255 (v - T_mid) / (T_hi - T_mid), 0, 255), np.rint, uint8 (DECL-P4-12 item 1)
  'window'  L2S / E2: linear 1-99 % stretch over the display window's mesh-valid px (with v > 0 for L2S,
            DECL-P4-12-A2 / DECL-P4-5-A1), i.e. the window the reader sees; 0 outside mesh-valid.
  In both, the uint8 canvas image is formed first, then INTER_AREA (the p4-l2 order), so S2 reproduces the existing
  tile PNG byte-for-byte for 'global' (verify_s2_against_manifest).
Eligibility: a display window is eligible iff >= 50 % of its canvas px are mesh-valid (the tile rule). S4 blocks sit on
the tile grid at stride 1 tile (every 2 x 2 group of grid cells, overlapping) and need all 4 member tiles in the
manifest; S1 zooms exist for every manifest tile.
Keys: every image gets a uuid name (seeded stream); the key maps it to (scale, r, c, part, canvas y0, x0, h, w,
scale_canvas_px_per_image_px) so hercules.scorer.display maps reader coordinates to canvas px (scale is non-integer).
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import uuid
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
OUT = 1068
SCALES = ('S4', 'S2', 'S1')


def png_bytes(a: np.ndarray) -> bytes:
    """Grayscale PNG, IHDR/IDAT/IEND only (same call as hercules.display.builder.png_bytes)."""
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(a, np.uint8), mode='L').save(buf, format='PNG', optimize=False)
    return buf.getvalue()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class UuidStream:
    def __init__(self, seed: int, tag: str):
        h = hashlib.sha256(f'{int(seed)}|{tag}'.encode()).digest()
        self._rng = np.random.default_rng(np.frombuffer(h[:16], dtype=np.uint32))

    def next(self) -> str:
        return str(uuid.UUID(bytes=self._rng.bytes(16), version=4))


@dataclass(frozen=True)
class Grid:
    T: int
    px_per_mm: float
    canvas_hw: tuple[int, int]
    n_rows: int
    n_cols: int

    @classmethod
    def from_json(cls, g: dict) -> 'Grid':
        tg = g.get('tile_grid', g)
        return cls(int(g['T_canvas_px']), float(g['px_per_mm']), tuple(int(v) for v in g['canvas_shape']),
                   int(tg['n_rows']), int(tg['n_cols']))

    def tile_rect(self, r: int, c: int) -> tuple[int, int, int, int]:
        return r * self.T, (r + 1) * self.T, c * self.T, (c + 1) * self.T


@dataclass(frozen=True)
class Window:
    scale: str
    r: int
    c: int
    part: str
    y0: int
    y1: int
    x0: int
    x1: int

    @property
    def h(self):
        return self.y1 - self.y0

    @property
    def w(self):
        return self.x1 - self.x0

    def px_per_mm(self, grid: Grid) -> float:
        return OUT / (self.h / grid.px_per_mm)


def windows(grid: Grid, tiles: list[dict], scales=SCALES) -> list[Window]:
    """All display windows of the requested scales for the manifest tile set (deterministic order)."""
    have = {(int(t['r']), int(t['c'])) for t in tiles}
    out = []
    T = grid.T
    for (r, c) in sorted(have):
        y0, y1, x0, x1 = grid.tile_rect(r, c)
        if 'S2' in scales:
            out.append(Window('S2', r, c, 'tile', y0, y1, x0, x1))
        if 'S1' in scales:
            h = T // 2
            for part, (ya, yb, xa, xb) in (('TL', (y0, y0 + h, x0, x0 + h)), ('TR', (y0, y0 + h, x0 + h, x1)),
                                           ('BL', (y0 + h, y1, x0, x0 + h)), ('BR', (y0 + h, y1, x0 + h, x1))):
                out.append(Window('S1', r, c, part, ya, yb, xa, xb))
        if 'S4' in scales and {(r + 1, c), (r, c + 1), (r + 1, c + 1)} <= have:
            out.append(Window('S4', r, c, 'block', y0, y0 + 2 * T, x0, x0 + 2 * T))
    order = {s: i for i, s in enumerate(SCALES)}
    return sorted(out, key=lambda w: (order[w.scale], w.r, w.c, w.part))


def value_map(values: np.ndarray, valid: np.ndarray, mode: str, t_mid: float | None = None,
              t_hi: float | None = None, positive_only: bool = False) -> tuple[np.ndarray, dict]:
    """Canvas-resolution uint8 display values (0 outside valid) and the mapping parameters used."""
    v = np.asarray(values)
    ok = np.asarray(valid, bool)
    if mode == 'global':
        if t_mid is None or t_hi is None or t_hi <= t_mid:
            raise ValueError('global mode needs T_mid < T_hi')
        # float32 arithmetic exactly as p4-l2 display_from_max, so S2 reproduces the L2 tiles byte for byte
        out = (v.astype(np.float32) - np.float32(t_mid)) * np.float32(255.0 / (t_hi - t_mid))
        np.clip(out, 0, 255, out=out)
        u8 = np.rint(out).astype(np.uint8)
        u8[~ok] = 0
        return u8, {'mode': 'global', 'T_mid': t_mid, 'T_hi': t_hi}
    if mode == 'window':
        sel = ok & (v > 0) if positive_only else ok
        if not sel.any():
            return np.zeros(v.shape, np.uint8), {'mode': 'window', 'lo': None, 'hi': None, 'n': 0}
        lo, hi = np.percentile(v[sel].astype(np.float64), [1.0, 99.0])
        if hi <= lo:
            hi = lo + 1.0
        out = np.clip((v.astype(np.float64) - lo) / (hi - lo) * 255.0, 0, 255)
        u8 = np.where(ok, np.rint(out), 0).astype(np.uint8)
        if positive_only:  # L2S: 0 where max == 0 as well (p4-l2 l2s.py)
            u8[v == 0] = 0
        return u8, {'mode': 'window', 'lo': float(lo), 'hi': float(hi), 'n': int(sel.sum()),
                    'positive_only': positive_only}
    raise ValueError(f'unknown mode {mode!r}')


def render(values: np.ndarray, valid: np.ndarray, mode: str, **kw) -> tuple[np.ndarray, dict]:
    """uint8 1068 x 1068 display of one window (values/valid are the window's canvas crop)."""
    h, w = values.shape
    if h < OUT or w < OUT:
        raise ValueError('downscale only: window smaller than the output')
    u8, par = value_map(values, valid, mode, **kw)
    img = cv2.resize(u8, (OUT, OUT), interpolation=cv2.INTER_AREA)
    par['valid_fraction'] = float(np.asarray(valid, bool).mean())
    return img, par


def build(grid: Grid, tiles: list[dict], source, mode: str, out_dir: str, seed: int, scales=SCALES,
          t_mid=None, t_hi=None, positive_only=False, min_valid=0.5) -> dict:
    """Render every eligible window of `scales`; write <out_dir>/<uuid>.png; return {'key', 'manifest', 'skipped'}."""
    os.makedirs(out_dir, exist_ok=True)
    names = UuidStream(seed, f'p4ms|{mode}')
    key, man, skipped = {}, {}, []
    for w in windows(grid, tiles, scales):
        vals, ok = source(w.y0, w.y1, w.x0, w.x1)
        if vals.shape != (w.h, w.w) or ok.shape != vals.shape:
            raise ValueError(f'source returned {vals.shape} for {w}')
        vf = float(np.asarray(ok, bool).mean())
        if vf < min_valid:
            skipped.append({'scale': w.scale, 'r': w.r, 'c': w.c, 'part': w.part, 'valid_fraction': vf})
            continue
        img, par = render(vals, ok, mode, t_mid=t_mid, t_hi=t_hi, positive_only=positive_only)
        b = png_bytes(img)
        u = names.next()
        with open(os.path.join(out_dir, u + '.png'), 'wb') as f:
            f.write(b)
        key[u] = {'scale': w.scale, 'r': w.r, 'c': w.c, 'part': w.part, 'y0': w.y0, 'x0': w.x0, 'h': w.h, 'w': w.w,
                  'scale_canvas_px_per_image_px': w.h / OUT, 'px_per_mm': w.px_per_mm(grid), 'map': par}
        man[u] = sha(b)
    return {'key': key, 'manifest': man, 'skipped': skipped}


def verify_s2_against_manifest(built: dict, tiles: list[dict]) -> dict:
    """S2 images must equal the existing tile PNGs (same channel, same mapping): compare sha256 per (r, c)."""
    want = {(int(t['r']), int(t['c'])): t['png_sha256'] for t in tiles}
    got = {(k['r'], k['c']): built['manifest'][u] for u, k in built['key'].items() if k['scale'] == 'S2'}
    same = sum(1 for rc in got if want.get(rc) == got[rc])
    return {'n_s2': len(got), 'n_equal': same, 'all_equal': same == len(got) and len(got) > 0}


def image_to_canvas(x: float, y: float, k: dict) -> tuple[float, float]:
    """Half-pixel convention of hercules.scorer.display: X = x0 + (x + 0.5) s - 0.5 (s may be non-integer)."""
    s = k['scale_canvas_px_per_image_px']
    return k['x0'] + (x + 0.5) * s - 0.5, k['y0'] + (y + 0.5) * s - 0.5


def load_tileset(manifest_path: str, grid_path: str) -> tuple[Grid, list[dict]]:
    m = json.load(open(manifest_path))
    g = json.load(open(grid_path))
    if 'grid' in g and 'T_canvas_px' in g['grid']:  # p4-l2 params.json form
        g = dict(g['grid'], px_per_mm=g.get('px_per_mm', 417.1314650253318), canvas_shape=g.get('canvas_shape', [69760, 170000]))
    return Grid.from_json(g), m['tiles']
