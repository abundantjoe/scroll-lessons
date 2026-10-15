# Provenance: Project HERCULES | owner the owner | [id removed]
"""Batch-control builders (code only; the orchestrator chooses the material).

* positive canaries: known-text tiles from the canary reserve fold K, blurred to the
  base model's sigma_eq by a Gaussian of DECLARED sigma (mm; the same cv2.GaussianBlur
  with BORDER_REFLECT that hercules.metrics.pixel.sigma_eq uses to measure sigma_eq);
* baits: wrong-order maps, blank maps (a supplied blank-window map or one synthesised
  from a real map: constant, pixel shuffle or phase scramble), NULL-arm maps;
* mirror canaries: the glyphs E K R C G B N rendered with a font, mirrored and not.

Display rule (hercules.display.builder): model maps as raw 0-255 probabilities (the
identity window), CT as a linear 1-99 % window over the whole tile; downscaling only by
cv2.INTER_AREA; no enhancement of any kind. PNGs carry no ancillary chunks (only
IHDR, IDAT, IEND; verified on every write) and get random UUID names. Nothing here
opens, views or describes an output image; all tests are numerical.
"""

from __future__ import annotations

import hashlib
import secrets
import struct
import uuid
import zlib
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from hercules.display.builder import MAX_SIDE_PX, area_downscale, linear_window_ct, model_map_u8, png_bytes

MIRROR_GLYPHS = ("E", "K", "R", "C", "G", "B", "N")
DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ALLOWED_PNG_CHUNKS = frozenset({b"IHDR", b"IDAT", b"IEND"})
BAIT_KINDS = ("wrong_order", "blank", "null_arm")
BLANK_MODES = ("constant", "pixel_shuffle", "phase_scramble")


# ----------------------------------------------------------------------------- primitives

def gaussian_blur_mm(img: np.ndarray, sigma_mm: float, px_per_mm: float) -> np.ndarray:
    """Gaussian blur of declared sigma (mm) at ``px_per_mm`` canvas px per mm (float64
    out). Identical kernel and border to metrics.pixel.sigma_eq; sigma 0 = identity."""
    if not (sigma_mm >= 0 and px_per_mm > 0):
        raise ValueError("sigma_mm must be >= 0 and px_per_mm > 0")
    a = np.asarray(img, dtype=np.float64)
    s_px = float(sigma_mm) * float(px_per_mm)
    if s_px == 0:
        return a.copy()
    return cv2.GaussianBlur(a, (0, 0), s_px, borderType=cv2.BORDER_REFLECT)


def to_display_u8(img: np.ndarray, window: str) -> tuple[np.ndarray, dict]:
    """``raw``: model map as 0-255 probabilities (identity window, rounding only);
    ``p1p99``: linear window at the tile's 1st/99th percentile (CT)."""
    if window == "raw":
        a = np.asarray(img)
        if a.dtype != np.uint8:
            a = np.rint(np.clip(np.asarray(a, dtype=np.float64), 0, 255)).astype(np.uint8) \
                if np.nanmax(a) > 1.0 + 1e-9 else model_map_u8(a)
        return a, {"window": "raw"}
    if window == "p1p99":
        u8, (lo, hi) = linear_window_ct(img)
        return u8, {"window": "p1p99", "lo": lo, "hi": hi}
    raise ValueError("window must be 'raw' or 'p1p99'")


def png_chunks(data: bytes) -> list[bytes]:
    """Chunk types of a PNG byte string (CRC verified)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i, out = 8, []
    while i < len(data):
        (n,) = struct.unpack(">I", data[i:i + 4])
        typ = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + n]
        (crc,) = struct.unpack(">I", data[i + 8 + n:i + 12 + n])
        if zlib.crc32(typ + body) & 0xFFFFFFFF != crc:
            raise ValueError(f"bad CRC in chunk {typ!r}")
        out.append(typ)
        i += 12 + n
    return out


def encode_png(img_u8: np.ndarray) -> bytes:
    """PNG bytes with no ancillary chunks; raises if any would be present."""
    a = np.asarray(img_u8)
    if a.dtype != np.uint8 or a.ndim != 2:
        raise ValueError("expected a 2-D uint8 image")
    if max(a.shape) > MAX_SIDE_PX:
        raise ValueError(f"image {a.shape} exceeds {MAX_SIDE_PX} px per side")
    b = png_bytes(a)
    extra = set(png_chunks(b)) - ALLOWED_PNG_CHUNKS
    if extra:
        raise ValueError(f"PNG carries ancillary chunks {sorted(extra)}")
    return b


def write_image(img_u8: np.ndarray, out_dir: str | Path) -> dict:
    """Write one display PNG under a random UUID name; return name and sha256 only."""
    b = encode_png(img_u8)
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4()}.png"
    (d / name).write_bytes(b)
    return {"name": name, "sha256": hashlib.sha256(b).hexdigest(), "shape": list(np.asarray(img_u8).shape)}


def _finish(img: np.ndarray, window: str, display_scale: float) -> tuple[np.ndarray, dict]:
    u8, wmeta = to_display_u8(img, window)
    out = area_downscale(u8, float(display_scale))
    return out, {**wmeta, "display_scale": float(display_scale), "interp": "INTER_AREA"}


# ----------------------------------------------------------------------------- positive canaries

def build_positive_canary(ref_map: np.ndarray, *, sigma_mm: float, px_per_mm: float, display_scale: float = 0.5,
                          window: str = "raw", canary_id: str, source: dict | None = None) -> tuple[np.ndarray, dict]:
    """Known-text tile (canvas resolution, 0-255 or 0-1) blurred to sigma_eq by a
    Gaussian of declared sigma, then displayed. Returns (display image, key)."""
    ref = np.asarray(ref_map, dtype=np.float64)
    if np.nanmax(ref) <= 1.0 + 1e-9:
        ref = ref * 255.0
    blurred = gaussian_blur_mm(ref, sigma_mm, px_per_mm)
    img, dmeta = _finish(np.rint(np.clip(blurred, 0, 255)).astype(np.uint8), window, display_scale)
    key = {"type": "positive_canary", "canary_id": canary_id, "sigma_mm": float(sigma_mm),
           "sigma_px": float(sigma_mm) * float(px_per_mm), "px_per_mm": float(px_per_mm),
           "canvas_hw": list(ref.shape), **dmeta, "source": source or {}}
    return img, key


# ----------------------------------------------------------------------------- baits

def blank_like(map_img: np.ndarray, mode: str, rng: np.random.Generator) -> np.ndarray:
    """A text-free map with the grey levels of ``map_img``:
    constant (its median), pixel_shuffle (same histogram, no spatial structure) or
    phase_scramble (same amplitude spectrum, random phases, so the same texture scale
    but no letters)."""
    a = np.asarray(map_img, dtype=np.float64)
    if mode == "constant":
        return np.full_like(a, float(np.median(a)))
    if mode == "pixel_shuffle":
        flat = a.ravel().copy()
        rng.shuffle(flat)
        return flat.reshape(a.shape)
    if mode == "phase_scramble":
        F = np.fft.fft2(a - a.mean())
        ph = np.angle(np.fft.fft2(rng.standard_normal(a.shape)))  # Hermitian-symmetric phases
        out = np.real(np.fft.ifft2(np.abs(F) * np.exp(1j * ph))) + a.mean()
        return out
    raise ValueError(f"mode must be one of {BLANK_MODES}")


def build_bait(kind: str, map_img: np.ndarray, *, display_scale: float = 0.5, window: str = "raw",
               bait_id: str, blank_mode: str | None = None, rng: np.random.Generator | None = None,
               source: dict | None = None) -> tuple[np.ndarray, dict]:
    """``wrong_order``: the NON-text-order map, displayed exactly like a text map;
    ``null_arm``: the NULL-arm map; ``blank``: a supplied blank-window map
    (blank_mode None) or one synthesised from ``map_img`` by :func:`blank_like`."""
    if kind not in BAIT_KINDS:
        raise ValueError(f"kind must be one of {BAIT_KINDS}")
    a = np.asarray(map_img, dtype=np.float64)
    if np.nanmax(a) <= 1.0 + 1e-9:
        a = a * 255.0
    meta: dict[str, Any] = {}
    if kind == "blank" and blank_mode is not None:
        a = blank_like(a, blank_mode, rng or np.random.default_rng(secrets.randbits(63)))
        meta["blank_mode"] = blank_mode
    img, dmeta = _finish(np.rint(np.clip(a, 0, 255)).astype(np.uint8), window, display_scale)
    key = {"type": "bait", "kind": kind, "bait_id": bait_id, "canvas_hw": list(a.shape), **meta, **dmeta,
           "source": source or {}}
    return img, key


# ----------------------------------------------------------------------------- mirror canaries

def font_sha256(path: str | Path = DEFAULT_FONT) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def glyph_mask(ch: str, *, height_px: int, canvas_hw: tuple[int, int], font_path: str | Path = DEFAULT_FONT) -> np.ndarray:
    """Anti-aliased coverage (0..1) of glyph ``ch`` whose cap height is ~``height_px``,
    centred on a canvas of ``canvas_hw``."""
    H, W = canvas_hw
    size = max(8, int(round(height_px / 0.73)))  # DejaVu cap height ~0.73 em
    font = ImageFont.truetype(str(font_path), size)
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    x0, y0, x1, y1 = dr.textbbox((0, 0), ch, font=font)
    dr.text(((W - (x1 - x0)) / 2 - x0, (H - (y1 - y0)) / 2 - y0), ch, fill=255, font=font)
    return np.asarray(im, dtype=np.float64) / 255.0


def asymmetry(img: np.ndarray) -> float:
    """||g - fliplr(g)||_1 / ||g||_1 (0 for a left-right symmetric image)."""
    g = np.asarray(img, dtype=np.float64)
    return float(np.abs(g - g[:, ::-1]).sum() / max(np.abs(g).sum(), 1e-12))


def build_mirror_canaries(*, glyphs: Sequence[str] = MIRROR_GLYPHS, letter_height_mm: float = 3.0,
                          px_per_mm: float, canvas_hw: tuple[int, int] = (1068, 1068), sigma_mm: float = 0.0,
                          ink: float = 230.0, background: float = 64.0, display_scale: float = 0.5,
                          window: str = "raw", font_path: str | Path = DEFAULT_FONT,
                          rng: np.random.Generator | None = None) -> list[tuple[np.ndarray, dict]]:
    """For every glyph one normal and one mirrored (left-right) image, in random order.
    Map-like appearance: background ~ the model's no-ink level, glyph at ``ink``; the
    optional blur uses the same declared-sigma Gaussian as the positive canaries."""
    rng = rng or np.random.default_rng(secrets.randbits(63))
    fsha = font_sha256(font_path)
    out = []
    for ch in glyphs:
        m = glyph_mask(ch, height_px=int(round(letter_height_mm * px_per_mm)), canvas_hw=canvas_hw, font_path=font_path)
        base = background + (ink - background) * m
        base = gaussian_blur_mm(base, sigma_mm, px_per_mm)
        for mirrored in (False, True):
            a = base[:, ::-1] if mirrored else base
            img, dmeta = _finish(np.rint(np.clip(a, 0, 255)).astype(np.uint8), window, display_scale)
            key = {"type": "mirror_canary", "glyph": ch, "mirrored": mirrored, "mirror_axis": "left_right",
                   "letter_height_mm": letter_height_mm, "sigma_mm": sigma_mm, "font_sha256": fsha,
                   "font_file": Path(font_path).name, "glyph_asymmetry": asymmetry(m), **dmeta}
            out.append((img, key))
    order = rng.permutation(len(out))
    return [out[i] for i in order]


def write_controls(controls: Sequence[tuple[np.ndarray, dict]], out_dir: str | Path) -> list[dict]:
    """Write every control image; return the scorer-side keys with file name and sha256
    (the key never goes into the image directory)."""
    keys = []
    for img, key in controls:
        w = write_image(img, out_dir)
        keys.append({**key, "control_uid": str(uuid.uuid4()), "image": w})
    return keys
