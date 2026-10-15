"""Loading maps and exporting predictions in formats the Vesuvius community already uses.

Inputs: .npy, .npz (``file.npz:key``), .png/.jpg/.tif (first channel). Exports: 8-bit grayscale PNG (ink bright, the convention of the
Vesuvius ink-detection overviews) plus a JSON sidecar that pins the image to segment coordinates.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
__all__ = ["load_map", "export_png"]


def load_map(path: str) -> np.ndarray:
    """Load a 2-D map. ``a.npz:key`` selects an array from an npz; images are read as their first channel."""
    key = None
    if ".npz:" in path:
        path, key = path.split(".npz:", 1); path += ".npz"
    ext = os.path.splitext(path)[1].lower()
    if ext == ".npy":
        return np.load(path)
    if ext == ".npz":
        z = np.load(path)
        if key is None:
            if len(z.files) != 1:
                raise ValueError(f"{path} holds {z.files}; use {path}:<key>")
            key = z.files[0]
        a = z[key]
        if a.dtype == np.uint8 and key.endswith("_bits"):
            raise ValueError("packed bit arrays are unpacked by inkeval.example, not load_map")
        return a
    a = np.asarray(Image.open(path))
    return a[..., 0] if a.ndim == 3 else a


def export_png(score: np.ndarray, mask: np.ndarray, out_png: str, *, segment: str | None = None, y0: int = 0, x0: int = 0,
               pitch_um: float = 2.4, lo_pct: float = 1.0, hi_pct: float = 99.0, method: str = "", **meta) -> dict:
    """Write ``score`` as an 8-bit PNG (ink bright, 0 outside the mask) and a ``.json`` sidecar with its segment placement.

    The stretch maps the [lo_pct, hi_pct] percentiles inside the mask to [1, 255]; 0 is reserved for 'not judged'. The sidecar records
    the stretch so the PNG can be mapped back to score units, and the canvas origin so it can be pasted into a segment-sized canvas.
    """
    s = np.asarray(score, np.float32); m = np.asarray(mask, bool)
    v = s[m]
    lo, hi = (float(np.percentile(v, lo_pct)), float(np.percentile(v, hi_pct))) if v.size else (0.0, 1.0)
    img = np.clip((s - lo) / max(hi - lo, 1e-9), 0, 1) * 254 + 1
    img = np.where(m, img, 0).astype(np.uint8)
    Image.fromarray(img).save(out_png, optimize=True)
    side = {"format": "inkeval-prediction-v1", "image": os.path.basename(out_png), "segment": segment,
            "canvas_origin_yx": [int(y0), int(x0)], "shape_yx": list(img.shape), "pitch_um": pitch_um,
            "stretch": {"lo": lo, "hi": hi, "lo_pct": lo_pct, "hi_pct": hi_pct, "value_0": "not judged (outside mask)",
                        "value_1_255": "score linearly mapped from [lo, hi], clipped"},
            "method": method, **meta}
    with open(os.path.splitext(out_png)[0] + ".json", "w") as f:
        json.dump(side, f, indent=1)
    return side
