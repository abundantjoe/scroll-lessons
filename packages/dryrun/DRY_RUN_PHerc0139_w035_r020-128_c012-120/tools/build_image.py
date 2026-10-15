# Provenance: Project HERCULES | owner the owner | [id removed]
"""Deterministic package image from a raw CT surface render (uint8, H x W) of the official renderer.

Layout (all uint8 greyscale, canonical PNG, see pngio.py):
  rows [0, HEADER)                  header strip; zero, except the DRY RUN stamp in its top-left corner
                                    (dry run only)
  rows [HEADER, HEADER + h)         CT panel: linear 1-99 % window of the whole render (valid = render > 0),
                                    then cv2.INTER_AREA downscale by `scale` when scale < 1; no other operation
  rows [HEADER + h, + FOOTER)       footer strip; zero, except the 1 cm scale bar (a solid 255 rectangle of
                                    BAR_H rows) and its "1 cm" label
Scale bar length: round(10000 / voxel_um * scale) px = 1 cm at the final px/mm, voxel_um from the volume's
metadata.json. Text: cv2.putText, FONT_HERSHEY_SIMPLEX, LINE_8 (no anti-aliasing)."""
import cv2
import numpy as np

HEADER = 64
FOOTER = 96
BAR_H = 16
BAR_X0 = 32
BAR_Y0_IN_FOOTER = 56           # bar rows [56, 72) of the footer
LABEL_ORG_IN_FOOTER = (BAR_X0, 44)
STAMP_TEXT = "DRY RUN"
STAMP_ORG = (16, 46)
FONT = cv2.FONT_HERSHEY_SIMPLEX
STAMP_SCALE, STAMP_THICK = 1.4, 3
LABEL_SCALE, LABEL_THICK = 0.9, 2
LO_PCT, HI_PCT = 1.0, 99.0


def linear_window(raw: np.ndarray):
    """uint8 CT panel by a linear 1-99 % window over valid (> 0) render pixels; invalid pixels stay 0."""
    raw = np.asarray(raw)
    if raw.dtype != np.uint8 or raw.ndim != 2:
        raise ValueError("raw render must be a 2-D uint8 array")
    valid = raw > 0
    if valid.sum() < 100:
        raise ValueError("render has fewer than 100 valid pixels")
    lo, hi = np.percentile(raw[valid].astype(np.float64), [LO_PCT, HI_PCT])
    lo, hi = float(lo), float(hi)
    if hi <= lo:
        hi = lo + 1.0
    out = (raw.astype(np.float64) - lo) / (hi - lo) * 255.0
    out = np.rint(np.clip(out, 0.0, 255.0)).astype(np.uint8)
    out[~valid] = 0
    return out, lo, hi


def panel(raw: np.ndarray, scale: float):
    img, lo, hi = linear_window(raw)
    if not (0.0 < scale <= 1.0):
        raise ValueError("scale must be in (0, 1]; no upsampling")
    if scale < 1.0:
        h, w = img.shape
        img = cv2.resize(img, (int(round(w * scale)), int(round(h * scale))), interpolation=cv2.INTER_AREA)
    return img, lo, hi


def bar_length_px(voxel_um: float, scale: float) -> int:
    return int(round(10000.0 / float(voxel_um) * float(scale)))


def stamp_strip(width: int) -> np.ndarray:
    s = np.zeros((HEADER, width), np.uint8)
    cv2.putText(s, STAMP_TEXT, STAMP_ORG, FONT, STAMP_SCALE, 255, STAMP_THICK, cv2.LINE_8)
    return s


def footer_strip(width: int, voxel_um: float, scale: float) -> np.ndarray:
    f = np.zeros((FOOTER, width), np.uint8)
    L = bar_length_px(voxel_um, scale)
    if BAR_X0 + L > width:
        raise ValueError("image narrower than a 1 cm scale bar")
    f[BAR_Y0_IN_FOOTER:BAR_Y0_IN_FOOTER + BAR_H, BAR_X0:BAR_X0 + L] = 255
    cv2.putText(f, "1 cm", LABEL_ORG_IN_FOOTER, FONT, LABEL_SCALE, 255, LABEL_THICK, cv2.LINE_8)
    return f


def compose(raw: np.ndarray, voxel_um: float, scale: float, dry_run: bool):
    p, lo, hi = panel(raw, scale)
    w = p.shape[1]
    head = stamp_strip(w) if dry_run else np.zeros((HEADER, w), np.uint8)
    img = np.concatenate([head, p, footer_strip(w, voxel_um, scale)], axis=0)
    info = dict(window_lo=lo, window_hi=hi, panel_rows=[HEADER, HEADER + p.shape[0]], panel_shape=list(p.shape),
                image_shape=list(img.shape), bar_length_px=bar_length_px(voxel_um, scale),
                bar_length_exact_px=10000.0 / float(voxel_um) * float(scale),
                bar_rows=[HEADER + p.shape[0] + BAR_Y0_IN_FOOTER, HEADER + p.shape[0] + BAR_Y0_IN_FOOTER + BAR_H],
                bar_x0=BAR_X0, px_per_mm=1000.0 / float(voxel_um) * float(scale))
    return img, info
