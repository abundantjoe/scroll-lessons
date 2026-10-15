# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-SG item 7, the copy test: no letter has NCC >= 0.8 with any training-label patch
at any 15 deg rotation step.

Method (all numeric; nothing here displays or saves an image):
  * each letter crop is rotated about its centre by every step in SG7_ROTATIONS_DEG
    (cv2.warpAffine, bilinear) and then compared on the disc inscribed in the crop, so
    every rotation compares the same support and no rotated-in border pixel is used;
  * when a label patch is smaller than the crop, the rotated crop is centre-cut to a
    d x d square, d = min(crop and patch sides), before the disc mask is applied;
  * the masked normalised cross-correlation (Pearson r over the disc) is computed at
    EVERY placement of the disc fully inside the patch ("valid" mode), with FFTs:
        num  = corr(I, Mz)              Mz = M * (T - mean_M T)
        varI = corr(I^2, M) - corr(I, M)^2 / n
        ncc  = num / sqrt(varI * sum(Mz^2))
  * a letter is a copy when |NCC| >= 0.8 (ruling B6); crops with n_eff < 30 are not
    evaluable and make the test FAIL (ruling B7);
  * placements whose image variance is ~0 (flat label regions) have undefined NCC and
    are set to 0 (SG7_FLAT_REL_EPS); a crop that is itself flat on its disc cannot be
    tested and makes the item FAIL (it cannot be shown not to be a copy).
The brute-force reference ``ncc_bruteforce`` is used by the unit tests only.
"""

from __future__ import annotations

import math
import os
from typing import Mapping, Sequence

import cv2
import numpy as np
from scipy import fft as sfft

from .constants import (SG7_ABS_NCC, SG7_FLAT_REL_EPS, SG7_NCC_MAX, SG7_NEFF_MIN, SG7_NULL_MAX_FALSE_FLAGS,
                        SG7_NULL_MIN_TILES, SG7_ROTATIONS_DEG)

MIN_DISC_SIDE = 8  # choice: below 8 px a disc holds < 50 px and NCC is meaningless
PATCH_CHUNK = 16  # memory bound only; results do not depend on it
FFT_WORKERS = int(os.environ.get("SG7_FFT_WORKERS", "-1"))  # scipy.fft threads (-1 = all cores); results identical


def disc_mask(d: int) -> np.ndarray:
    """Boolean disc inscribed in a d x d square (pixel centres within (d-1)/2 + 0.5)."""
    c = (d - 1) / 2.0
    yy, xx = np.mgrid[0:d, 0:d]
    return (yy - c) ** 2 + (xx - c) ** 2 <= (c + 0.5) ** 2 - 1e-9


def rotate_crop(crop: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate about the crop centre (bilinear); angle 0 returns an exact copy."""
    crop = np.asarray(crop, dtype=np.float64)
    if angle_deg % 360 == 0:
        return crop.copy()
    h, w = crop.shape
    m = cv2.getRotationMatrix2D(((w - 1) / 2.0, (h - 1) / 2.0), float(angle_deg), 1.0)
    return cv2.warpAffine(crop, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def centre_square(a: np.ndarray, d: int) -> np.ndarray:
    h, w = a.shape
    y0, x0 = (h - d) // 2, (w - d) // 2
    return a[y0 : y0 + d, x0 : x0 + d]


def templates_for(crop: np.ndarray, d: int, rotations: Sequence[float] = SG7_ROTATIONS_DEG):
    """Rotated, centre-cut, zero-mean masked templates (n_rot, d, d), mask, per-template sum Mz^2."""
    m = disc_mask(d)
    out = np.zeros((len(rotations), d, d), dtype=np.float64)
    ss = np.zeros(len(rotations), dtype=np.float64)
    for i, a in enumerate(rotations):
        t = centre_square(rotate_crop(crop, a), d)
        mu = t[m].mean()
        tz = np.where(m, t - mu, 0.0)
        out[i] = tz
        ss[i] = float((tz * tz).sum())
    return out, m, ss


def _fshape(H: int, W: int, d: int) -> tuple[int, int]:
    return (sfft.next_fast_len(H + d - 1, real=True), sfft.next_fast_len(W + d - 1, real=True))


def kernel_fft(ker: np.ndarray, fshape) -> np.ndarray:
    """FFT of flipped kernels (k, d, d) for valid-mode correlation at ``fshape``."""
    return sfft.rfft2(ker[..., ::-1, ::-1], fshape, axes=(-2, -1), workers=FFT_WORKERS)


def _corr_valid(img_f: np.ndarray, kf: np.ndarray, fshape, H: int, W: int, d: int) -> np.ndarray:
    """Valid-mode correlation of images (FFT given, (n, ...)) with kernels (FFT given, (k, ...))."""
    full = sfft.irfft2(img_f[:, None] * kf[None], fshape, axes=(-2, -1), workers=FFT_WORKERS)
    return full[..., d - 1 : H, d - 1 : W]


def masked_ncc_maps(patches: np.ndarray, templates: np.ndarray, mask: np.ndarray, t_ss: np.ndarray,
                    t_fft: np.ndarray | None = None, m_fft: np.ndarray | None = None) -> np.ndarray:
    """NCC maps (n_patch, n_tmpl, H-d+1, W-d+1) for same-shape patches (n_patch, H, W).

    ``t_fft`` / ``m_fft``: optional precomputed kernel FFTs of the templates / mask at
    ``_fshape(H, W, d)`` (a cache; results are identical)."""
    patches = np.asarray(patches, dtype=np.float64)
    _, H, W = patches.shape
    d = templates.shape[-1]
    n = float(mask.sum())
    fshape = _fshape(H, W, d)
    if t_fft is None:
        t_fft = kernel_fft(templates, fshape)
    if m_fft is None:
        m_fft = kernel_fft(mask.astype(np.float64)[None], fshape)
    i_f = sfft.rfft2(patches, fshape, axes=(-2, -1), workers=FFT_WORKERS)
    i2_f = sfft.rfft2(patches * patches, fshape, axes=(-2, -1), workers=FFT_WORKERS)
    s1 = _corr_valid(i_f, m_fft, fshape, H, W, d)[:, 0]
    s2 = _corr_valid(i2_f, m_fft, fshape, H, W, d)[:, 0]
    var_i = s2 - s1 * s1 / n  # n * variance of the image under the disc
    num = _corr_valid(i_f, t_fft, fshape, H, W, d)
    # Flat guard relative to each patch's own global variance (scale-free).
    gvar = patches.reshape(len(patches), -1).var(axis=1)
    floor = SG7_FLAT_REL_EPS * n * np.maximum(gvar, np.finfo(float).tiny)
    ok = var_i > floor[:, None, None]
    den = np.sqrt(np.where(ok, var_i, 1.0))[:, None] * np.sqrt(t_ss)[None, :, None, None]
    ncc = np.where(ok[:, None], num / den, 0.0)
    return np.clip(ncc, -1.0, 1.0)


def coherence_area_px(a: np.ndarray) -> float:
    """Area (px) where the crop's normalised autocorrelation is >= 0.5 (FFT, zero-padded).

    Diagnostic only (never a bar): the number of independent samples in a compared disc is
    about disc area / coherence area, and the chance maximum of the SG 7 statistic rises
    steeply as that number falls (logs/sib/sg/copytest_null.json)."""
    a = np.asarray(a, dtype=np.float64)
    a = a - a.mean()
    h, w = a.shape
    f = sfft.rfft2(a, (2 * h, 2 * w))
    ac = sfft.irfft2(f * np.conj(f), (2 * h, 2 * w))
    if ac[0, 0] <= 0:
        return math.inf
    ac = np.fft.fftshift(ac / ac[0, 0])
    # count the connected-at-origin region >= 0.5 (it is the central blob for smooth fields)
    return float((ac >= 0.5).sum())


def ncc_bruteforce(patch: np.ndarray, template_zm: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Direct masked Pearson r at every valid placement (reference for tests)."""
    patch = np.asarray(patch, dtype=np.float64)
    H, W = patch.shape
    d = template_zm.shape[0]
    t = template_zm[mask]
    out = np.zeros((H - d + 1, W - d + 1))
    for y in range(H - d + 1):
        for x in range(W - d + 1):
            v = patch[y : y + d, x : x + d][mask]
            v = v - v.mean()
            den = math.sqrt(float((v * v).sum()) * float((t * t).sum()))
            out[y, x] = float((v * t).sum()) / den if den > 0 else 0.0
    return out


def copy_test(letter_crops: Sequence[np.ndarray], label_patches: Sequence[np.ndarray],
              rotations: Sequence[float] = SG7_ROTATIONS_DEG, enforce_neff: bool = True) -> dict:
    """DECL-SG 7 with rulings B6 and B7.  Returns {"status": PASS|FAIL, "max_abs_ncc", ...}.

    ``letter_crops``: 2-D float arrays cut by code from the candidate map at the agreed
    letter boxes; ``label_patches``: 2-D arrays of every training-label patch, at the same
    px/mm as the crops (the caller resamples; this function never guesses a scale).
    A letter is a copy when |NCC| >= 0.8 at any rotation step and placement (ruling B6;
    the signed value at that maximum and the signed extremes are reported).  A crop is
    evaluable against a patch-size group only if its n_eff (disc area / autocorrelation
    half-max area) is >= SG7_NEFF_MIN there (ruling B7); a crop below the floor in any group,
    or flat, makes the test FAIL.  ``enforce_neff=False`` is for the synthetic null only.
    """
    if len(letter_crops) == 0:
        return {"status": "FAIL", "reason": "no_letter_crops", "per_letter": []}
    if len(label_patches) == 0:
        return {"status": "FAIL", "reason": "no_label_patches", "per_letter": []}
    patches = [np.asarray(p, dtype=np.float64) for p in label_patches]
    for p in patches:
        if p.ndim != 2 or not np.isfinite(p).all():
            raise ValueError("label patches must be finite 2-D arrays")
    groups: dict[tuple[int, int], list[int]] = {}
    for j, p in enumerate(patches):
        groups.setdefault(p.shape, []).append(j)
    per = []
    for li, crop in enumerate(letter_crops):
        crop = np.asarray(crop, dtype=np.float64)
        if crop.ndim != 2 or not np.isfinite(crop).all():
            raise ValueError("letter crops must be finite 2-D arrays")
        coh = coherence_area_px(crop)
        best = {"letter": li, "max_abs_ncc": -1.0, "signed_ncc_at_max": None, "max_signed_ncc": -1.0,
                "min_signed_ncc": 1.0, "patch": None, "angle_deg": None, "yx": None, "d": None,
                "n_eff_by_group": {}, "not_evaluable": []}
        for shape, idx in sorted(groups.items()):
            d = min(crop.shape[0], crop.shape[1], shape[0], shape[1])
            gkey = f"{shape[0]}x{shape[1]}"
            if d < MIN_DISC_SIDE:
                best["not_evaluable"].append({"patch_shape": list(shape), "reason": "disc_too_small", "d": d})
                continue
            n_eff = float(np.pi * (d / 2.0) ** 2 / coh) if math.isfinite(coh) and coh > 0 else 0.0
            best["n_eff_by_group"][gkey] = n_eff
            tmpl, mask, ss = templates_for(crop, d, rotations)
            if not (ss > 0).all():
                best["not_evaluable"].append({"patch_shape": list(shape), "reason": "flat_crop", "d": d})
                continue
            if enforce_neff and n_eff < SG7_NEFF_MIN:
                best["not_evaluable"].append({"patch_shape": list(shape), "reason": "n_eff_below_floor", "d": d,
                                              "n_eff": n_eff, "floor": SG7_NEFF_MIN})
                continue
            fs = _fshape(shape[0], shape[1], d)
            t_fft, m_fft = kernel_fft(tmpl, fs), kernel_fft(mask.astype(np.float64)[None], fs)
            for c0 in range(0, len(idx), PATCH_CHUNK):
                chunk = idx[c0 : c0 + PATCH_CHUNK]
                maps = masked_ncc_maps(np.stack([patches[j] for j in chunk]), tmpl, mask, ss, t_fft, m_fft)
                best["max_signed_ncc"] = max(best["max_signed_ncc"], float(maps.max()))
                best["min_signed_ncc"] = min(best["min_signed_ncc"], float(maps.min()))
                a = np.abs(maps)
                pi, ri, y, x = np.unravel_index(int(np.argmax(a)), maps.shape)
                v = float(a[pi, ri, y, x])
                if v > best["max_abs_ncc"]:
                    best.update(max_abs_ncc=v, signed_ncc_at_max=float(maps[pi, ri, y, x]), patch=int(chunk[pi]),
                                angle_deg=float(rotations[ri]), yx=[int(y), int(x)], d=int(d))
        stat = best["max_abs_ncc"] if SG7_ABS_NCC else best["max_signed_ncc"]
        best["copy"] = bool(stat >= SG7_NCC_MAX)
        best["n_eff"] = min(best["n_eff_by_group"].values()) if best["n_eff_by_group"] else 0.0
        per.append(best)
    copies = [p["letter"] for p in per if p["copy"]]
    unevaluable = [p["letter"] for p in per if p["not_evaluable"]]
    status = "PASS" if not copies and not unevaluable else "FAIL"
    reason = "pass" if status == "PASS" else ("copy_found" if copies else "not_evaluable")
    return {"status": status, "reason": reason,
            "bar": f"|NCC| < {SG7_NCC_MAX} at every rotation step; n_eff >= {SG7_NEFF_MIN:g} per crop",
            "n_rotations": len(rotations), "n_letters": len(per), "n_patches": len(patches),
            "max_abs_ncc": max(p["max_abs_ncc"] for p in per),
            "max_signed_ncc": max(p["max_signed_ncc"] for p in per),
            "min_signed_ncc": min(p["min_signed_ncc"] for p in per),
            "copies": copies, "not_evaluable": unevaluable,
            "n_eff_min": min(p["n_eff"] for p in per), "n_eff_median": float(np.median([p["n_eff"] for p in per])),
            "neff_floor_enforced": bool(enforce_neff), "per_letter": per}


def copy_test_null_check(null_tile_crops: Mapping[str, Sequence[np.ndarray]],
                         label_patches: Sequence[np.ndarray]) -> dict:
    """Ruling B7: the copy test applied to letter crops from >= 40 empirical-null tiles
    against the real training-label patch set must give 0 false flags; else SG 7 is
    UNINFORMATIVE at this geometry (and the patch geometry must be re-declared).

    Null crops below the n_eff floor are counted separately (``not_evaluable``); they would
    fail SG 7 anyway and are no evidence either way."""
    tiles = sorted(null_tile_crops)
    per, flags, unevaluable = {}, 0, 0
    for t in tiles:
        r = copy_test(null_tile_crops[t], label_patches)
        per[t] = {k: r.get(k) for k in ("n_letters", "copies", "not_evaluable", "max_abs_ncc", "n_eff_min")}
        flags += len(r.get("copies", []))
        unevaluable += len(r.get("not_evaluable", []))
    ok = len(tiles) >= SG7_NULL_MIN_TILES and flags <= SG7_NULL_MAX_FALSE_FLAGS
    return {"status": "INFORMATIVE" if ok else "UNINFORMATIVE", "n_null_tiles": len(tiles),
            "false_flags": flags, "not_evaluable_crops": unevaluable, "n_patches": len(label_patches),
            "min_tiles": SG7_NULL_MIN_TILES, "max_false_flags": SG7_NULL_MAX_FALSE_FLAGS, "per_tile": per}


def crop_boxes(image: np.ndarray, boxes: Sequence[Sequence[float]], margin_px: int = 0) -> list[np.ndarray]:
    """Cut letter crops [x0, y0, x1, y1] (canvas px, inclusive-exclusive after rounding) from a map.

    Pure array slicing for the copy test; the pixels are never displayed.
    """
    image = np.asarray(image)
    H, W = image.shape[:2]
    out = []
    for b in boxes:
        x0, y0, x1, y1 = (int(round(v)) for v in b)
        x0, y0 = max(0, x0 - margin_px), max(0, y0 - margin_px)
        x1, y1 = min(W, x1 + margin_px), min(H, y1 + margin_px)
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"empty crop box {b}")
        out.append(np.asarray(image[y0:y1, x0:x1], dtype=np.float64))
    return out
