"""Display builder (section 5.5, I2): linear displays only.

Provenance: Project HERCULES | owner the owner | [id removed]

Rules enforced here:
- CT images (RAW-F/RAW-B, REF CT) get a fixed linear 1-99 % window computed over the
  WHOLE window, declared in advance; model maps are shown as raw 0-255 probabilities.
- Downscaling only by area mean (cv2.INTER_AREA). No sharpening, CLAHE, gamma,
  morphology or colour maps.
- One PNG per order; LEFT/RIGHT assignment randomised per reader; the key goes to the
  scorer only. PNGs are written without any text chunks.
"""
import hashlib
import io
import secrets
import uuid

import cv2
import numpy as np
from PIL import Image

MAX_SIDE_PX = 1068
LINEAR_LO_PCT = 1.0
LINEAR_HI_PCT = 99.0

# Tile layouts (READ-CAL grid). Sizes in cm on the canvas, stride in cm.
# D1Q: "four 1 x 1 cm quadrants at full scale, 50 % overlap" is read as 1 x 1 cm tiles
# at 0.5 cm stride (3 x 3 = 9 tiles in a 2 x 2 cm window, containing the 4 quadrants).
# D1S (amended by RULES.md DECL-READCAL-A1): 1.0 x 0.6 cm row strips at full scale,
# stride 0.4 cm vertically and 0.5 cm horizontally, last strip flush with the edge.
# No image shown to a reader may exceed MAX_SIDE_PX per side (HARNESS-COORD).
LAYOUTS = {
    "D2": {"scale": 0.5, "tile_cm": None, "stride_cm": None},
    "D1Q": {"scale": 1.0, "tile_cm": (1.0, 1.0), "stride_cm": (0.5, 0.5)},
    "D1S": {"scale": 1.0, "tile_cm": (0.6, 1.0), "stride_cm": (0.4, 0.5)},
}


def px_per_cm(voxel_um):
    """Canvas px per cm; one render px = one voxel at mesh scale 0.05 / 20 px per cell."""
    return 10000.0 / float(voxel_um)


def linear_window_ct(img, valid=None):
    """Map a CT float image to uint8 with a linear window at the 1st/99th percentile of
    the whole window (valid pixels only)."""
    img = np.asarray(img, dtype=np.float64)
    vals = img[valid] if valid is not None else img[np.isfinite(img)]
    lo, hi = np.percentile(vals, [LINEAR_LO_PCT, LINEAR_HI_PCT])
    if hi <= lo:
        hi = lo + 1.0
    out = (img - lo) / (hi - lo) * 255.0
    out = np.clip(np.nan_to_num(out, nan=0.0), 0, 255)
    return np.rint(out).astype(np.uint8), (float(lo), float(hi))


def model_map_u8(prob):
    """Model maps are shown as raw 0-255 probabilities (no windowing)."""
    p = np.asarray(prob)
    if p.dtype == np.uint8:
        return p
    p = np.asarray(p, dtype=np.float64)
    if p.max() <= 1.0 + 1e-9:
        p = p * 255.0
    return np.rint(np.clip(p, 0, 255)).astype(np.uint8)


def area_downscale(img_u8, scale):
    if scale == 1.0:
        return img_u8
    h, w = img_u8.shape
    nh, nw = int(round(h * scale)), int(round(w * scale))
    return cv2.resize(img_u8, (nw, nh), interpolation=cv2.INTER_AREA)


def raw_slab_means(stack):
    """RAW-F = mean of slices n//2+1..n//2+5; RAW-B = mean of n//2-5..n//2-1 (-n 31)."""
    n = stack.shape[0]
    c = n // 2
    raw_f = stack[c + 1:c + 6].astype(np.float64).mean(axis=0)
    raw_b = stack[c - 5:c].astype(np.float64).mean(axis=0)
    return raw_f, raw_b


def png_bytes(img_u8):
    """Encode a grayscale PNG with no ancillary text chunks."""
    buf = io.BytesIO()
    Image.fromarray(img_u8, mode="L").save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def tile_origins(win_h, win_w, voxel_um, layout):
    """Canvas-px origins (y, x, h, w) of display tiles inside a window."""
    spec = LAYOUTS[layout]
    if spec["tile_cm"] is None:
        return [(0, 0, win_h, win_w)]
    ppc = px_per_cm(voxel_um)
    th, tw = (int(round(spec["tile_cm"][0] * ppc)), int(round(spec["tile_cm"][1] * ppc)))
    sh, sw = (int(round(spec["stride_cm"][0] * ppc)), int(round(spec["stride_cm"][1] * ppc)))
    th, tw = min(th, win_h), min(tw, win_w)

    def starts(total, t, s):
        out = list(range(0, max(total - t, 0) + 1, max(s, 1)))
        if out[-1] != total - t:
            out.append(total - t)
        return out

    return [(y, x, th, tw) for y in starts(win_h, th, sh) for x in starts(win_w, tw, sw)]


def build_items(text_img_u8, nontext_img_u8, window_id, canvas_y0, canvas_x0, voxel_um,
                layout, rng=None):
    """Return reader items: for each tile, a LEFT/RIGHT PNG pair with randomised order,
    plus the scorer key. Image names are random UUIDs."""
    assert text_img_u8.shape == nontext_img_u8.shape
    rng = rng or secrets.SystemRandom()
    spec = LAYOUTS[layout]
    items = []
    for (ty, tx, th, tw) in tile_origins(*text_img_u8.shape, voxel_um, layout):
        t = area_downscale(text_img_u8[ty:ty + th, tx:tx + tw], spec["scale"])
        b = area_downscale(nontext_img_u8[ty:ty + th, tx:tx + tw], spec["scale"])
        if max(t.shape) > MAX_SIDE_PX:
            raise ValueError(f"display tile {t.shape} exceeds {MAX_SIDE_PX} px per side")
        text_left = rng.random() < 0.5
        left, right = (t, b) if text_left else (b, t)
        lp, rp = png_bytes(left), png_bytes(right)
        items.append({
            "item_id": str(uuid.uuid4()),
            "left_name": str(uuid.uuid4()) + ".png", "left_png": lp,
            "right_name": str(uuid.uuid4()) + ".png", "right_png": rp,
            "key": {
                "window_id": window_id,
                "scale": 1.0 / spec["scale"],  # canvas px per image px
                "y0": canvas_y0 + ty, "x0": canvas_x0 + tx,
                "side_order": {"left": "text" if text_left else "nontext",
                               "right": "nontext" if text_left else "text"},
                "layout": layout,
                "px_per_mm_image": px_per_cm(voxel_um) / 10.0 * spec["scale"],
                "left_sha256": hashlib.sha256(lp).hexdigest(),
                "right_sha256": hashlib.sha256(rp).hexdigest(),
            },
        })
    return items
