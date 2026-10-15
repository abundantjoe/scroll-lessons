# Provenance: Project HERCULES | owner the owner | [id removed]
"""READCAL-2 display and sheet builders (task readcal2). Calibration material only; never evidence of letters.

Everything here is deterministic given a seed; no function opens, shows or describes an image (arrays and hashes
only). Displays follow the I2 rules of hercules.display.builder: raw 0-255 probabilities, INTER_AREA downscaling
only, no enhancement, PNGs without text chunks, random-looking uuid file names drawn from a seeded stream.

Frames and scales
-----------------
canvas   the 9 um canvas of the window (2136 x 2136 px for 2 x 2 cm at 9.362 um); px_per_mm = 1000 / voxel_um
         (voxel size ALWAYS from the volume metadata.json, never assumed; callers pass it).
display  K_D2: the whole window at 1/2 scale by INTER_AREA (1068 px; 53.4 px/mm at 9.362 um).
         MS: the K_D2 overview plus the 4 quadrants at full scale (1068 px each, 106.8 px/mm).
Sheets (key, exemplar, placebo) are 1068 x 1068 display images. Exemplar and placebo glyph fields are built at
CANVAS resolution (blur sigma in canvas px = sigma_mm * px_per_mm_canvas; noise with the measured base-map
blank spectrum at canvas resolution) and then downscaled 1/2 by INTER_AREA, i.e. exactly the path a REF-ladder
window takes, so "sigma 0.30 mm on the exemplar" means the same blur operator as REF030.
"""
from __future__ import annotations

import hashlib
import io
import math
import uuid
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
FONT_SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
FONT_SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
GREEK = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡϹΤΥΦΧΨΩ'  # 24 capitals, lunate sigma U+03F9
NAMES = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu',
         'Nu', 'Xi', 'Omicron', 'Pi', 'Rho', 'Sigma (lunate)', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega']
KEYSHEET_SHA256 = '5da96bde05851b0cd9316292e5f7ef95d497a400f582c6869840a66dc6a65f88'  # METRIC-HASH-12
SHEET_PX = 1068
GRID_COLS, GRID_ROWS = 6, 4
CELL_W, CELL_H = SHEET_PX // GRID_COLS, SHEET_PX // GRID_ROWS  # 178 x 267 display px
LADDER_MM = (0.0, 0.15, 0.30, 0.45, 0.60)
EXEMPLAR_MM = (0.15, 0.30, 0.45)
WINDOW_PX = 2136
# Exemplar intensity model (declared constants; see REPORT.md): ink level = 229, the median over RCPICK-1 picker
# images of the per-image 99th percentile of the official reference display (RCPICK-1, numbers only); the
# background and the noise come from the measured base-map blank statistics (noise_psd.json).
INK_LEVEL = 229.0
CAP_HEIGHT_MM = 2.5  # letters on the K_D2 brief are "about 107-214 px tall" at 53.4 px/mm = 2.0-4.0 mm
GLYPH_BAND_DISPLAY_PX = 200  # glyph band per sheet row (display px); the remaining 67 px carry the label


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def png_bytes(img_u8: np.ndarray) -> bytes:
    """Grayscale PNG without ancillary chunks (same encoder call as hercules.display.builder.png_bytes)."""
    a = np.ascontiguousarray(img_u8)
    if a.dtype != np.uint8 or a.ndim != 2:
        raise ValueError('png_bytes needs a 2-D uint8 array')
    buf = io.BytesIO()
    Image.fromarray(a, mode='L').save(buf, format='PNG', optimize=False)
    return buf.getvalue()


def area_downscale(img_u8: np.ndarray, scale: float) -> np.ndarray:
    if scale == 1.0:
        return img_u8
    h, w = img_u8.shape
    return cv2.resize(img_u8, (int(round(w * scale)), int(round(h * scale))), interpolation=cv2.INTER_AREA)


def px_per_mm_canvas(voxel_um: float) -> float:
    v = float(voxel_um)
    if not (1.0 < v < 20.0):
        raise ValueError(f'implausible voxel size {v} um')
    return 1000.0 / v


class UuidStream:
    """Deterministic uuid4-format names from a seed (names carry no arm, state or window information)."""

    def __init__(self, seed: int, tag: str):
        h = hashlib.sha256(f'{int(seed)}|{tag}'.encode()).digest()
        self._rng = np.random.default_rng(np.frombuffer(h[:16], dtype=np.uint32))

    def next(self) -> str:
        return str(uuid.UUID(bytes=self._rng.bytes(16), version=4))


# ---------------------------------------------------------------------------------------------------- key sheet
def keysheet() -> np.ndarray:
    """Byte-exact regeneration of the frozen K_D2 key sheet (configs/briefs/probe2_keysheet.png, METRIC-HASH-12):
    6 x 4 cells of 178 x 267 px, DejaVu Serif Bold 120 glyph centred at (cx, 113), DejaVu Sans 22 name at (cx, 208)."""
    im = Image.new('L', (SHEET_PX, SHEET_PX), 255)
    d = ImageDraw.Draw(im)
    fg, fl = ImageFont.truetype(FONT_SERIF, 120), ImageFont.truetype(FONT_SANS, 22)
    for i, (ch, nm) in enumerate(zip(GREEK, NAMES)):
        r, c = divmod(i, GRID_COLS)
        cx = c * CELL_W + CELL_W // 2
        d.text((cx, r * CELL_H + 113), ch, font=fg, fill=0, anchor='mm')
        d.text((cx, r * CELL_H + 208), nm, font=fl, fill=0, anchor='mm')
    return np.asarray(im).copy()


# ---------------------------------------------------------------------------------------------------- glyphs
def glyph_coverage(ch: str, font_px: int, box_hw: tuple[int, int]) -> np.ndarray:
    """Anti-aliased coverage in [0, 1] (float64) of one glyph centred ('mm') in a box of (h, w) canvas px."""
    h, w = box_hw
    im = Image.new('L', (w, h), 0)
    ImageDraw.Draw(im).text((w // 2, h // 2), ch, font=ImageFont.truetype(FONT_SERIF, int(font_px)), fill=255,
                            anchor='mm')
    return np.asarray(im, dtype=np.float64) / 255.0


def font_px_for_cap(cap_px: float) -> int:
    """Font size whose cap height (glyph 'Η') is closest to cap_px (measured, not assumed)."""
    best = None
    lo = max(8, int(cap_px * 1.2))
    for fs in range(lo, int(cap_px * 1.6) + 2):
        cov = glyph_coverage('Η', fs, (int(cap_px * 3), int(cap_px * 3)))
        rows = np.nonzero(cov.max(1) > 0.5)[0]
        err = abs((rows[-1] - rows[0] + 1) - cap_px)
        if best is None or err < best[0]:
            best = (err, fs)
    return best[1]


def stroke_width_px(cov: np.ndarray) -> float:
    """Median stroke width of a glyph mask: 2 x the distance-transform value on its medial ridge."""
    m = (cov > 0.5).astype(np.uint8)
    if m.sum() == 0:
        return 0.0
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    ridge = (dt >= cv2.dilate(dt, np.ones((3, 3), np.uint8))) & (dt > 0)
    return float(2.0 * np.median(dt[ridge]))


def random_blob(target_area: float, box_hw: tuple[int, int], stroke_px: float, rng: np.random.Generator,
                tol: float = 0.01, margin_frac: float = 0.12) -> np.ndarray:
    """Random stroke blob (coverage in [0, 1]) with summed coverage within `tol` of target_area.

    Random polylines (2-4 vertices, round caps, anti-aliased, thickness = the glyph's stroke width) are drawn
    inside the central (1 - 2 margin_frac) part of the box until the area exceeds the target; the last stroke is
    then shortened by bisection so that the area matches. Strokes never form text on purpose; a letter-likeness
    check is left to the caller (tests measure the maximum IoU with every glyph)."""
    h, w = box_hw
    th = max(1, int(round(stroke_px)))
    y_lo, y_hi = margin_frac * h, (1 - margin_frac) * h
    x_lo, x_hi = margin_frac * w, (1 - margin_frac) * w
    ss = 8  # sub-pixel shift bits for cv2 anti-aliased drawing

    def draw(base: np.ndarray, pts: np.ndarray, frac: float) -> np.ndarray:
        out = base.copy()
        seg = pts.copy()
        # keep a prefix of the polyline of relative length `frac`
        lens = np.linalg.norm(np.diff(seg, axis=0), axis=1)
        total = lens.sum()
        keep, acc = [seg[0]], 0.0
        for k, L in enumerate(lens):
            if acc + L >= frac * total:
                t = (frac * total - acc) / max(L, 1e-9)
                keep.append(seg[k] + t * (seg[k + 1] - seg[k]))
                break
            keep.append(seg[k + 1])
            acc += L
        p = np.round(np.array(keep) * (1 << ss)).astype(np.int32).reshape(-1, 1, 2)
        canvas = np.zeros((h, w), np.uint8)
        cv2.polylines(canvas, [p], False, 255, th, cv2.LINE_AA, ss)
        return np.maximum(out, canvas.astype(np.float64) / 255.0)

    for _attempt in range(50):
        cov = np.zeros((h, w))
        for _stroke in range(40):
            n = int(rng.integers(2, 5))
            pts = np.c_[rng.uniform(x_lo, x_hi, n), rng.uniform(y_lo, y_hi, n)]
            full = draw(cov, pts, 1.0)
            if full.sum() < target_area:
                cov = full
                continue
            a, b = 0.0, 1.0
            for _ in range(40):
                mid = 0.5 * (a + b)
                if draw(cov, pts, mid).sum() < target_area:
                    a = mid
                else:
                    b = mid
            cand = draw(cov, pts, b)
            if abs(cand.sum() - target_area) <= tol * target_area:
                return cand
            break
    raise RuntimeError('random_blob: could not match the target area')


# ---------------------------------------------------------------------------------------------------- noise
@dataclass
class NoiseModel:
    """Second-order model of blank 9 um base-map texture at canvas resolution.

    radial_f: bin centres (cycles / canvas px, 0 .. 0.5); radial_psd: mean periodogram power in each bin, in
    (uint8 units)^2, normalised so that the mean over the full 2-D frequency grid equals the variance; mean: the
    blank map mean (uint8 units)."""
    radial_f: np.ndarray
    radial_psd: np.ndarray
    mean: float
    var: float

    def psd_on_grid(self, shape: tuple[int, int]) -> np.ndarray:
        fy = np.fft.fftfreq(shape[0])[:, None]
        fx = np.fft.fftfreq(shape[1])[None, :]
        f = np.sqrt(fy ** 2 + fx ** 2)
        s = np.interp(f, self.radial_f, self.radial_psd, left=self.radial_psd[0], right=self.radial_psd[-1])
        return np.maximum(s, 0.0)


def periodogram_tiles(img: np.ndarray, valid: np.ndarray | None, tile: int = 256, step: int = 128) -> np.ndarray:
    """Welch estimate: mean over fully valid tiles of |FFT(hann * (x - mean))|^2 / sum(hann^2). The mean over the
    frequency grid of the result equals the mean (window-weighted) variance of the tiles."""
    a = np.asarray(img, dtype=np.float64)
    v = np.ones(a.shape, bool) if valid is None else np.asarray(valid, bool)
    win = np.outer(np.hanning(tile), np.hanning(tile))
    norm = (win ** 2).sum() / tile ** 2
    acc, n = np.zeros((tile, tile)), 0
    for y in range(0, a.shape[0] - tile + 1, step):
        for x in range(0, a.shape[1] - tile + 1, step):
            if not v[y:y + tile, x:x + tile].all():
                continue
            t = a[y:y + tile, x:x + tile]
            F = np.fft.fft2((t - t.mean()) * win)
            acc += (np.abs(F) ** 2) / (tile * tile) / norm
            n += 1
    if n == 0:
        raise ValueError('no fully valid tile')
    return acc / n


def taper_weights(valid: np.ndarray, taper_px: float = 32.0) -> np.ndarray:
    k = int(round(3 * taper_px))
    er = cv2.erode(np.asarray(valid, np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0)
    return cv2.GaussianBlur(er.astype(np.float64), (0, 0), taper_px) * np.asarray(valid, bool)


def periodogram_masked(img: np.ndarray, valid: np.ndarray, taper_px: float = 32.0) -> np.ndarray:
    """Full-window periodogram with a smooth validity taper: w = Gaussian blur (sigma taper_px) of the valid mask
    eroded by 3 taper_px, so w falls smoothly to ~0 before the mask edge (no edge leakage of the strong low-frequency
    power); P = |FFT(w (x - m_w))|^2 / sum(w^2), m_w the w-weighted mean. The mean of P over the frequency grid equals
    the w^2-weighted variance. Resolves frequencies down to 1 / window size (letter scale), which 256 px tiles cannot."""
    a = np.asarray(img, dtype=np.float64)
    v = np.asarray(valid, bool)
    w = taper_weights(v, taper_px)
    if w.sum() <= 0:
        raise ValueError('no valid pixel')
    m = (a * w).sum() / w.sum()
    F = np.fft.fft2(np.where(v, a - m, 0.0) * w)
    return (np.abs(F) ** 2) / (w ** 2).sum()


def radial_average(psd2: np.ndarray, n_bins: int = 64) -> tuple[np.ndarray, np.ndarray]:
    h, w = psd2.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fy ** 2 + fx ** 2).ravel()
    edges = np.linspace(0.0, 0.5 * math.sqrt(2), n_bins + 1)
    idx = np.clip(np.digitize(f, edges) - 1, 0, n_bins - 1)
    s = np.bincount(idx, weights=psd2.ravel(), minlength=n_bins)
    c = np.bincount(idx, minlength=n_bins)
    centres = 0.5 * (edges[:-1] + edges[1:])
    ok = c > 0
    return centres[ok], s[ok] / c[ok]


def synth_noise(model: NoiseModel, shape: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
    """Zero-mean stationary Gaussian noise whose expected periodogram equals model.psd_on_grid(shape)."""
    s = model.psd_on_grid(shape)
    s[0, 0] = 0.0
    wn = rng.standard_normal(shape)
    out = np.real(np.fft.ifft2(np.fft.fft2(wn) * np.sqrt(s)))
    return out


# ---------------------------------------------------------------------------------------------------- sheets
def gaussian_blur_canvas(img: np.ndarray, sigma_mm: float, voxel_um: float, border=cv2.BORDER_REFLECT) -> np.ndarray:
    s_px = float(sigma_mm) * px_per_mm_canvas(voxel_um)
    a = np.asarray(img, dtype=np.float64)
    return a if s_px == 0 else cv2.GaussianBlur(a, (0, 0), s_px, borderType=border)


def glyph_layout(voxel_um: float, cap_mm: float = CAP_HEIGHT_MM):
    """Canvas geometry shared by exemplar and placebo sheets: (font_px, band_h, cell_w, centres)."""
    scale = 2  # canvas px per display px (K_D2 1/2 scale)
    cap_px = cap_mm * px_per_mm_canvas(voxel_um)
    fpx = font_px_for_cap(cap_px)
    band_h = GLYPH_BAND_DISPLAY_PX * scale
    cw = CELL_W * scale
    centres = [(r * band_h + band_h // 2, c * cw + cw // 2) for r in range(GRID_ROWS) for c in range(GRID_COLS)]
    return fpx, band_h, cw, centres


def glyph_field(covs: list[np.ndarray], voxel_um: float, cap_mm: float = CAP_HEIGHT_MM) -> np.ndarray:
    """Place 24 coverage boxes at the cell centres of a 4-band canvas field (GRID_ROWS * band_h x 2136)."""
    _, band_h, cw, centres = glyph_layout(voxel_um, cap_mm)
    field = np.zeros((GRID_ROWS * band_h, GRID_COLS * cw))
    for cov, (cy, cx) in zip(covs, centres):
        h, w = cov.shape
        y0, x0 = cy - h // 2, cx - w // 2
        ys, xs = slice(max(0, y0), min(field.shape[0], y0 + h)), slice(max(0, x0), min(field.shape[1], x0 + w))
        sub = cov[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        field[ys, xs] = np.maximum(field[ys, xs], sub)
    return field


def glyph_covs(voxel_um: float, cap_mm: float = CAP_HEIGHT_MM) -> tuple[list[np.ndarray], int]:
    fpx, band_h, cw, _ = glyph_layout(voxel_um, cap_mm)
    box = (band_h, cw)
    return [glyph_coverage(ch, fpx, box) for ch in GREEK], fpx


def placebo_covs(covs: list[np.ndarray], seed: int) -> tuple[list[np.ndarray], list[dict]]:
    """One random stroke blob per glyph, matched in summed coverage (ink area) and stroke width."""
    out, info = [], []
    for i, cov in enumerate(covs):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), 7919, i]))
        sw = stroke_width_px(cov)
        blob = random_blob(float(cov.sum()), cov.shape, sw, rng)
        out.append(blob)
        info.append({'glyph': GREEK[i], 'glyph_area_px': float(cov.sum()), 'blob_area_px': float(blob.sum()),
                     'stroke_px': sw})
    return out, info


def render_sheet(covs: list[np.ndarray], sigma_mm: float, noise: NoiseModel, voxel_um: float, seed: int,
                 labels: list[str] = NAMES, ink_level: float = INK_LEVEL, cap_mm: float = CAP_HEIGHT_MM
                 ) -> tuple[np.ndarray, dict]:
    """1068 x 1068 sheet: 4 bands of degraded ink shapes (canvas-resolution blur + base-map-spectrum noise,
    INTER_AREA 1/2) with a white label strip (DejaVu Sans 22, black) under every cell.

    The noise realisation depends on `seed` and `sigma_mm` only, NOT on the shapes, so an exemplar sheet and its
    placebo built with the same seed carry the identical noise field (paired control)."""
    field = glyph_field(covs, voxel_um, cap_mm)
    sig = gaussian_blur_canvas(field, sigma_mm, voxel_um, border=cv2.BORDER_CONSTANT)
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), int(round(sigma_mm * 1000)), 104729]))
    nz = synth_noise(noise, field.shape, rng)
    img = noise.mean + (ink_level - noise.mean) * sig + nz
    u8 = np.rint(np.clip(img, 0, 255)).astype(np.uint8)
    bands = area_downscale(u8, 0.5)  # (4 * 200) x 1068
    sheet = np.full((SHEET_PX, SHEET_PX), 255, np.uint8)
    pil = Image.new('L', (SHEET_PX, SHEET_PX), 255)
    d = ImageDraw.Draw(pil)
    fl = ImageFont.truetype(FONT_SANS, 22)
    for i, nm in enumerate(labels):
        r, c = divmod(i, GRID_COLS)
        d.text((c * CELL_W + CELL_W // 2, r * CELL_H + GLYPH_BAND_DISPLAY_PX + 33), nm, font=fl, fill=0, anchor='mm')
    sheet[:] = np.asarray(pil)
    for r in range(GRID_ROWS):
        sheet[r * CELL_H:r * CELL_H + GLYPH_BAND_DISPLAY_PX] = bands[r * GLYPH_BAND_DISPLAY_PX:(r + 1) * GLYPH_BAND_DISPLAY_PX]
    stats = {'sigma_mm': sigma_mm, 'sigma_canvas_px': sigma_mm * px_per_mm_canvas(voxel_um), 'seed': seed,
             'noise_std_realised': float(nz.std()), 'band_mean': float(bands.mean()),
             'ink_area_canvas_px': float(field.sum())}
    return sheet, stats


# ---------------------------------------------------------------------------------------------------- REF ladder
def blur_valid(ref: np.ndarray, valid: np.ndarray, sigma_mm: float, voxel_um: float) -> np.ndarray:
    """Normalised (masked) Gaussian blur: blur(ref * valid) / blur(valid) on valid pixels, 0 elsewhere.
    sigma 0 returns ref on valid pixels. BORDER_REFLECT as hercules.metrics.pixel.sigma_eq."""
    r = np.where(valid, np.nan_to_num(np.asarray(ref, np.float64)), 0.0)
    v = np.asarray(valid, np.float64)
    if sigma_mm == 0:
        return np.where(valid, r, 0.0)
    num = gaussian_blur_canvas(r, sigma_mm, voxel_um)
    den = gaussian_blur_canvas(v, sigma_mm, voxel_um)
    out = np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0.0)
    return np.where(valid, out, 0.0)


def to_u8(prob: np.ndarray) -> np.ndarray:
    """Raw 0-255 probabilities: values already in 0..255 are rounded and clipped (no windowing)."""
    return np.rint(np.clip(np.asarray(prob, np.float64), 0, 255)).astype(np.uint8)


def ref_ladder_images(ref: np.ndarray, valid: np.ndarray, voxel_um: float, sigmas=LADDER_MM) -> dict:
    """{sigma: 1068 x 1068 uint8 K_D2 display} for a 2136 x 2136 window of reference probabilities (0..255)."""
    if ref.shape != (WINDOW_PX, WINDOW_PX) or valid.shape != ref.shape:
        raise ValueError(f'window must be {WINDOW_PX} px square')
    out = {}
    for s in sigmas:
        out[float(s)] = area_downscale(to_u8(blur_valid(ref, valid, s, voxel_um)), 0.5)
    return out


# ---------------------------------------------------------------------------------------------------- MS / ROW
QUADS = {'TL': (0, 0), 'TR': (0, WINDOW_PX // 2), 'BL': (WINDOW_PX // 2, 0), 'BR': (WINDOW_PX // 2, WINDOW_PX // 2)}


def ms_images(window_u8: np.ndarray) -> list[tuple[str, np.ndarray, float, int, int]]:
    """MS item: [(part, image, scale canvas px per image px, y0, x0)] = overview at 1/2 + 4 full-scale quadrants."""
    if window_u8.shape != (WINDOW_PX, WINDOW_PX) or window_u8.dtype != np.uint8:
        raise ValueError('MS needs a 2136 x 2136 uint8 window')
    out = [('OV', area_downscale(window_u8, 0.5), 2.0, 0, 0)]
    q = WINDOW_PX // 2
    for name, (y0, x0) in QUADS.items():
        out.append((name, np.ascontiguousarray(window_u8[y0:y0 + q, x0:x0 + q]), 1.0, y0, x0))
    return out


def image_to_canvas(x: float, y: float, scale: float, x0: float, y0: float) -> tuple[float, float]:
    """hercules.scorer.display half-pixel convention: X = x0 + (x + 0.5) s - 0.5."""
    return x0 + (x + 0.5) * scale - 0.5, y0 + (y + 0.5) * scale - 0.5


def ms_merge(namings: list[dict], dedupe_px: float = 60.0) -> list[dict]:
    """Merge one reader's namings of one MS window, already in canvas px: {'ch', 'x', 'y', 'conf', 'part'}.
    Namings of the same identity within `dedupe_px` canvas px are one letter (a reader may list it in the
    overview and in a quadrant); the full-scale (quadrant) naming is kept, ties by list order; firm if any
    merged naming is firm. Different identities are never merged."""
    order = sorted(range(len(namings)), key=lambda i: (namings[i].get('part') == 'OV', i))
    kept: list[dict] = []
    for i in order:
        n = namings[i]
        dup = None
        for k in kept:
            if k['ch'] == n['ch'] and math.hypot(k['x'] - n['x'], k['y'] - n['y']) <= dedupe_px:
                dup = k
                break
        if dup is None:
            kept.append(dict(n))
        elif n.get('conf') == 'firm':
            dup['conf'] = 'firm'
    return kept


def row_baseline_y(row: dict, x: float) -> float:
    """ROW arm: reader row = {'y': baseline y at image x = 0, 'angle_deg': clockwise angle}; y at column x."""
    return float(row['y']) + math.tan(math.radians(float(row['angle_deg']))) * float(x)


def row_letter_residuals(rows: list[dict], letters: list[dict]) -> list[float | None]:
    """Signed distance (image px) of each letter's box bottom from the baseline of its declared row (None when
    the row index is missing or out of range). Reported only: ROW is scored on letters by the unchanged scorer."""
    out = []
    for l in letters:
        k = l.get('row')
        if not isinstance(k, int) or not (0 <= k < len(rows)):
            out.append(None)
            continue
        bx = l.get('box')
        yb = float(bx[3]) if bx else float(l['y'])
        out.append(yb - row_baseline_y(rows[k], float(l['x'])))
    return out
