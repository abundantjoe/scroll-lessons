# Provenance: Project HERCULES | owner the owner | [id removed]
"""Line-spacing statistics of known text from official PHerc0139 human ink labels
(ruling B9: numbers only).  Nothing here displays, saves or describes an image.

Source (official, anonymous S3): PHerc0139/segments/<seg>/ink-labels/
9.362um-volume-20250728140407/20260918/{inklabels,supervision}.zarr/0 (zarr v3, one
sharded chunk; decoded here directly: shard index at the end, blosc inner chunks).
Pixel size from the label zarr's own OME scale (9.362 um), cross-checked against the
volume's metadata.json.

Per non-overlapping 2 x 2 cm tile with ink-label fraction >= 2 % (supervision masks are
too sparse to require; see MIN_SUPERVISED), and a row-periodicity score >= 0.3:
  1. orientation: rotate the ink mask (1/4 scale, INTER_AREA) through 0..179 deg; the
     row direction maximises the projection-profile contrast (CV^2; interlinear gaps are
     empty only along the rows); refined at full scale +-1 deg in 0.25 deg steps; the
     periodicity score (max autocorrelation at lags 1.5-12 mm) is reported for filtering;
  2. pitch: autocorrelation peak lag (parabolic refinement); rows: anchored on the
     smoothed profile maximum, stepped by the pitch, each refined to its ink centroid
     within +-pitch/2 -> consecutive pitches -> per-tile pitch CV;
  3. letter height: (a) median 5th-95th percentile extent of each row's ink mass
     ("band"); (b) median height, along the row normal, of connected ink components
     0.5-8 mm high.
Usage: python tools/sib/sg/label_spacing.py --cache DIR --out logs/sib/sg/label_spacing_0139.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

BUCKET = "vesuvius-challenge-open-data"
VOLUME = "20250728140407"
SEGMENTS = ("20250831000000-w040_2025083102", "20260108000000-w041_2026010816", "20260115000000-w044_2026011522",
            "20260302000000-w039_2026030210", "20260317000000-w035_2026031718")
TILE_MM = 20.0
# choice (measured): the supervision masks cover only 1-3.5 % of each canvas (no 2 cm tile
# is > 23 % supervised), so tiles are selected on the ink positives alone; row geometry
# needs only the positives.  The supervised fraction of each tile is still reported.
MIN_SUPERVISED = 0.0
MIN_INK = 0.02
LAG_MM = (1.5, 12.0)
COMP_H_MM = (0.5, 8.0)


# ------------------------------------------------------------------ zarr v3 shard decode


def decode_shard(buf: bytes, shape, inner, fill=0) -> np.ndarray:
    """Decode a single-shard zarr v3 uint8 array (sharding_indexed, bytes+blosc inner codecs,
    index = little-endian (offset, nbytes) uint64 pairs in C order + crc32c, at the end)."""
    import numcodecs

    gy, gx = math.ceil(shape[0] / inner[0]), math.ceil(shape[1] / inner[1])
    n = gy * gx
    idx_len = n * 16 + 4
    idx = np.frombuffer(buf[-idx_len:-4], dtype="<u8").reshape(n, 2)
    out = np.full((gy * inner[0], gx * inner[1]), fill, dtype=np.uint8)
    blosc = numcodecs.Blosc()
    empty = np.uint64(2 ** 64 - 1)
    for k in range(n):
        off, nb = idx[k]
        if off == empty and nb == empty:
            continue
        raw = blosc.decode(buf[int(off):int(off + nb)])
        a = np.frombuffer(raw, dtype=np.uint8).reshape(inner)
        i, j = divmod(k, gx)
        out[i * inner[0]:(i + 1) * inner[0], j * inner[1]:(j + 1) * inner[1]] = a
    return out[: shape[0], : shape[1]]


def fetch(key: str, cache: Path, log: list) -> bytes:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    p = cache / key
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
        p.write_bytes(s3.get_object(Bucket=BUCKET, Key=key)["Body"].read())
    b = p.read_bytes()
    log.append({"key": f"s3://{BUCKET}/{key}", "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    return b


def load_array(prefix: str, cache: Path, log: list, level: int = 0):
    meta = json.loads(fetch(prefix + f"{level}/zarr.json", cache, log))
    group = json.loads(fetch(prefix + "zarr.json", cache, log))
    ds = group["attributes"]["ome"]["multiscales"][0]["datasets"]
    assert ds[level]["path"] == str(level)
    scale = ds[level]["coordinateTransformations"][0]["scale"]
    shard = meta["codecs"][0]["configuration"]
    assert meta["data_type"] == "uint8" and meta["codecs"][0]["name"] == "sharding_indexed"
    assert [c["name"] for c in shard["codecs"]] == ["bytes", "blosc"]
    assert tuple(meta["chunk_grid"]["configuration"]["chunk_shape"]) >= tuple(meta["shape"])  # one shard
    buf = fetch(prefix + f"{level}/c/0/0", cache, log)
    return decode_shard(buf, meta["shape"], shard["chunk_shape"], meta["fill_value"]), float(scale[0])


# ------------------------------------------------------------------ measurement


def _rotate(a: np.ndarray, deg: float, interp=cv2.INTER_LINEAR) -> np.ndarray:
    h, w = a.shape
    m = cv2.getRotationMatrix2D(((w - 1) / 2, (h - 1) / 2), deg, 1.0)
    return cv2.warpAffine(a, m, (w, h), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def _acf(p: np.ndarray) -> np.ndarray:
    p = p - p.mean()
    n = len(p)
    f = np.fft.rfft(p, 2 * n)
    ac = np.fft.irfft(f * np.conj(f), 2 * n)[:n]
    return ac / ac[0] if ac[0] > 0 else np.zeros(n)


def _profile(mask: np.ndarray, deg: float) -> np.ndarray:
    """Row profile after rotating by ``deg``: ink per row, normalised by valid width (the
    rotated support) so corners do not create spurious periodicity."""
    r = _rotate(mask, deg)
    sup = _rotate(np.ones_like(mask), deg)
    w = sup.sum(axis=1)
    prof = np.where(w > 0.5 * mask.shape[1], r.sum(axis=1) / np.maximum(w, 1e-9), np.nan)
    good = np.isfinite(prof)
    return prof[good]


def _contrast(prof: np.ndarray) -> float:
    """Projection-profile contrast (CV^2): maximal when the projection runs along the rows,
    so interlinear gaps are empty (classic skew criterion)."""
    m = float(prof.mean()) if len(prof) else 0.0
    return float(prof.var() / (m * m)) if m > 0 else 0.0


def _score(prof: np.ndarray, lag_px: tuple[int, int]) -> tuple[float, int]:
    ac = _acf(prof)
    lo, hi = lag_px
    hi = min(hi, len(ac) - 2)
    if hi <= lo:
        return 0.0, 0
    seg = ac[lo:hi]
    k = int(np.argmax(seg))
    return float(seg[k]), lo + k


def measure_tile(mask: np.ndarray, px_mm: float) -> dict:
    """Orientation, pitch, pitch CV and letter heights of one binary ink tile."""
    mask = (mask > 0).astype(np.float32)
    small = cv2.resize(mask, (mask.shape[1] // 4, mask.shape[0] // 4), interpolation=cv2.INTER_AREA)
    lag_s = (int(LAG_MM[0] * px_mm / 4), int(LAG_MM[1] * px_mm / 4))
    coarse = [(_contrast(_profile(small, d)), d) for d in range(0, 180)]
    _, d0 = max(coarse)
    lag = (int(LAG_MM[0] * px_mm), int(LAG_MM[1] * px_mm))
    fine = [(_contrast(_profile(mask, d0 + e)), d0 + e) for e in np.arange(-1.0, 1.0001, 0.25)]
    _, deg = max(fine)
    prof = _profile(mask, deg)
    score = _score(prof, lag)[0]
    ac = _acf(prof)
    _, k = _score(prof, lag)
    # parabolic refinement only at a true local maximum (negative curvature), shift clipped
    # to +-0.5 px; a maximum on the edge of the lag window is not a period ("peak_at_lag_edge")
    edge = not (lag[0] < k < min(lag[1], len(ac) - 2) and ac[k] >= ac[k - 1] and ac[k] >= ac[k + 1])
    if not edge:
        y0, y1, y2 = ac[k - 1], ac[k], ac[k + 1]
        den = y0 - 2 * y1 + y2
        if den < 0:
            k = k + float(np.clip(0.5 * (y0 - y2) / den, -0.5, 0.5))
    pitch_px = float(k)
    if edge or not (pitch_px > 0):
        return {"row_angle_deg": float((-deg) % 180.0), "periodicity_score": float(score), "pitch_mm": None,
                "peak_at_lag_edge": True, "n_rows": 0, "row_pitches_mm": [], "pitch_cv": None,
                "band_fwhm_mm_median": None, "n_bands": 0, "component_height_mm_median": None, "n_components": 0}
    # rows: anchor on the global maximum of the profile smoothed at pitch/4, step +-pitch,
    # refine each row to its ink centroid within +-pitch/2 (iterated to < 0.5 px); windows cut by the tile
    # edge or holding < 25 % of the median row mass are dropped.
    sm = cv2.GaussianBlur(prof.reshape(-1, 1).astype(np.float64), (1, 0), sigmaX=0.1, sigmaY=pitch_px / 4).ravel()
    n = len(prof)
    half = pitch_px / 2.0
    anchor = float(np.argmax(sm))
    cents = [anchor + k * pitch_px for k in range(-int(n / pitch_px) - 1, int(n / pitch_px) + 2)]
    rows = []
    for c in cents:
        ok = False
        for _ in range(50):  # centroid iteration to convergence (< 0.5 px)
            lo, hi = int(math.ceil(c - half)), int(math.floor(c + half))
            if lo < 0 or hi >= n:
                break
            assert lo <= hi, (lo, hi)  # never a wrapped (negative) slice
            w = prof[lo:hi + 1]
            if w.sum() <= 0:
                break
            c_new = float(np.sum(np.arange(lo, hi + 1) * w) / w.sum())
            if abs(c_new - c) < 0.5:
                c, ok = c_new, True
                break
            c = c_new
        if ok:
            lo, hi = int(math.ceil(c - half)), int(math.floor(c + half))
            if lo >= 0 and hi < n:
                rows.append((c, lo, hi, float(prof[lo:hi + 1].sum())))
    rows = sorted({round(r[0], 1): r for r in rows}.values())  # rows converging to the same place: once
    if rows:
        med = float(np.median([r[3] for r in rows]))
        rows = [r for r in rows if r[3] >= 0.25 * med]
    peaks = [r[0] for r in rows]
    pitches = np.diff(peaks).astype(float)
    cv = float(pitches.std() / pitches.mean()) if len(pitches) >= 2 else None
    # (a) band height: 5th-95th percentile extent of each row's ink mass
    fwhm = []
    for c, lo, hi, _m in rows:
        w = prof[lo:hi + 1]
        cdf = np.cumsum(w) / w.sum()
        a, b = int(np.searchsorted(cdf, 0.05)), int(np.searchsorted(cdf, 0.95))
        fwhm.append((b - a) / px_mm)
    # (b) component heights along the row normal
    r = (_rotate(mask, deg, cv2.INTER_NEAREST) > 0.5).astype(np.uint8)
    n, _, st, _ = cv2.connectedComponentsWithStats(r, connectivity=8)
    hmm = st[1:, cv2.CC_STAT_HEIGHT] / px_mm
    hmm = hmm[(hmm >= COMP_H_MM[0]) & (hmm <= COMP_H_MM[1])]
    return {
        "row_angle_deg": float((-deg) % 180.0), "periodicity_score": float(score), "pitch_mm": pitch_px / px_mm,
        "peak_at_lag_edge": False,
        "n_rows": len(peaks), "row_pitches_mm": (pitches / px_mm).tolist(), "pitch_cv": cv,
        "band_fwhm_mm_median": float(np.median(fwhm)) if fwhm else None, "n_bands": len(fwhm),
        "component_height_mm_median": float(np.median(hmm)) if len(hmm) else None, "n_components": int(len(hmm)),
    }


def tiles(ink: np.ndarray, sup: np.ndarray, px_mm: float):
    t = int(round(TILE_MM * px_mm))
    H, W = ink.shape
    for y in range(0, H - t + 1, t):
        for x in range(0, W - t + 1, t):
            s = sup[y:y + t, x:x + t] > 0
            if s.mean() < MIN_SUPERVISED:
                continue
            m = ink[y:y + t, x:x + t] > 0
            if m.mean() < MIN_INK:
                continue
            yield (y, x), m, float(s.mean())


def summarise(vals):
    v = np.asarray([x for x in vals if x is not None and math.isfinite(x)], dtype=float)
    if not len(v):
        return None
    q = np.percentile(v, [5, 25, 50, 75, 95])
    return {"n": int(len(v)), "p5": q[0], "p25": q[1], "median": q[2], "p75": q[3], "p95": q[4],
            "min": float(v.min()), "max": float(v.max())}


def main() -> None:
    global TILE_MM
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tile-mm", type=float, default=TILE_MM)
    a = ap.parse_args()
    TILE_MM = a.tile_mm
    cache, log, per = Path(a.cache), [], []
    meta = json.loads(fetch(f"PHerc0139/volumes/{VOLUME}-9.362um-1.2m-113keV-masked.zarr/metadata.json", cache, log))
    vox = round(float(meta["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000.0, 6)
    for seg in SEGMENTS:
        pre = f"PHerc0139/segments/{seg}/ink-labels/9.362um-volume-{VOLUME}/20260918/"
        ink, s_ink = load_array(pre + "inklabels.zarr/", cache, log)
        sup, s_sup = load_array(pre + "supervision.zarr/", cache, log)
        assert abs(s_ink - vox) < 1e-6 and abs(s_sup - vox) < 1e-6, (s_ink, s_sup, vox)
        px_mm = 1000.0 / vox
        for (y, x), m, sfrac in tiles(ink, sup, px_mm):
            r = measure_tile(m, px_mm)
            r.update(segment=seg, tile_yx=[y, x], ink_fraction=float(m.mean()), supervised_fraction=sfrac)
            if r["pitch_cv"] is not None and r["band_fwhm_mm_median"]:
                r["pitch_over_height"] = r["pitch_mm"] / r["band_fwhm_mm_median"]
            per.append(r)
            print(seg[-17:], y, x, round(r["row_angle_deg"], 2), round(r["pitch_mm"], 3), r["n_rows"],
                  None if r["pitch_cv"] is None else round(r["pitch_cv"], 3), flush=True)
    ok = [r for r in per if r["periodicity_score"] >= 0.3]
    out = {
        "provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
        "source": "official PHerc0139 native9 human ink labels, label_set 20260918, 9.362 um volume " + VOLUME,
        "voxel_size_um_metadata": vox, "tile_mm": TILE_MM, "min_supervised": MIN_SUPERVISED, "min_ink": MIN_INK,
        "n_tiles": len(per), "n_tiles_periodic": len(ok), "periodicity_min": 0.3,
        "summary_periodic_tiles": {
            "pitch_mm": summarise(r["pitch_mm"] for r in ok),
            "pitch_cv": summarise(r["pitch_cv"] for r in ok),
            "band_fwhm_mm": summarise(r["band_fwhm_mm_median"] for r in ok),
            "component_height_mm": summarise(r["component_height_mm_median"] for r in ok),
            "pitch_over_band_height": summarise(r.get("pitch_over_height") for r in ok),
            "row_angle_deg": summarise(r["row_angle_deg"] for r in ok),
            "n_rows_per_tile": summarise(r["n_rows"] for r in ok),
        },
        "downloads": log, "tiles": per,
    }
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print("tiles", len(per), "periodic", len(ok))


if __name__ == "__main__":
    sys.exit(main())
