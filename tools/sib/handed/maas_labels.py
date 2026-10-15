# Provenance: Project HERCULES | owner the owner | [id removed]
"""Supplementary reader-free check: column slant of the official human ink
labels (label_set 20260918, 2.399 um canvas) of PHerc0139, resampled into
the LEVELLED frame of the organizer mesh (rows = iso-z, z increasing down,
level_mesh is a proper rotation so the chirality of the organizer grid is
kept). If the geometry prediction (organizer grid legible as stored) and the
Maas prior both hold, column edges slope with x decreasing downward.

Only numbers are written. Label arrays are read into memory and discarded.
Run with /opt/hv3 (zarr v3). Usage: python maas_labels.py OUT_JSON
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import zarr
from zarr.storage import FsspecStore

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import maas as M  # noqa: E402
from hercules.geometry import level_mesh as L  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

S3 = Path("/work/handed/s3")
LEVEL = 3
PX_UM = 2.399 * 2 ** LEVEL
BASE = "s3://vesuvius-challenge-open-data"


def open_level(prefix: str, name: str):
    st = FsspecStore.from_url(f"{BASE}/{prefix}{name}.zarr", storage_options={"anon": True}, read_only=True)
    g = zarr.open_group(st, mode="r")
    return g[str(LEVEL)]


def line_pitch(ink: np.ndarray, lo_mm=1.5, hi_mm=8.0) -> tuple[float, float]:
    prof = ink.sum(1).astype(float)
    prof -= prof.mean()
    ac = np.correlate(prof, prof, "full")[prof.size - 1:]
    ac /= ac[0] if ac[0] else 1
    lo, hi = int(lo_mm * 1000 / PX_UM), int(hi_mm * 1000 / PX_UM)
    k = lo + int(np.argmax(ac[lo:hi]))
    return float(k), float(ac[k])


def main() -> int:
    out = {"level": LEVEL, "pixel_um": PX_UM, "prior": "Maas's law: lines begin further left going down (unmirrored slope < 0)",
           "segments": []}
    for tif in sorted(S3.glob("PHerc0139/segments/*/mesh/*-on-20260102150214-2.399um.tifxyz")):
        seg = tif.parts[len(S3.parts) + 2]
        lab_prefix = f"PHerc0139/segments/{seg}/ink-labels/2.399um-volume-20260102150214/20260918/"
        rec = dict(segment=seg)
        try:
            ink_a = open_level(lab_prefix, "inklabels")
            sup_a = open_level(lab_prefix, "supervision")
            ink = np.asarray(ink_a[:]) > 0
            sup = np.asarray(sup_a[:]) > 0
            rec["label_shape_level"] = list(ink.shape)
            rec["label_sha256_level"] = hashlib.sha256(np.packbits(ink).tobytes()).hexdigest()
            m = read_tifxyz(tif)
            sx, sy = m.scale
            rec["canvas_hw_from_grid"] = [m.points.shape[0] / sy, m.points.shape[1] / sx]
            rec["canvas_hw_from_labels"] = [ink.shape[0] * 2 ** LEVEL, ink.shape[1] * 2 ** LEVEL]
            lv = L.level_mesh(m.points, step_vox=float(2 ** LEVEL))
            # levelled node -> canvas (x = u / sx, y = v / sy) -> label pixel at LEVEL
            cx = lv.src_u / sx / 2 ** LEVEL
            cy = lv.src_v / sy / 2 ** LEVEL
            ok = valid_mask(lv.points) & (cx >= 0) & (cy >= 0) & (cx < ink.shape[1] - 1) & (cy < ink.shape[0] - 1)
            ix = np.clip(np.round(cx).astype(int), 0, ink.shape[1] - 1)
            iy = np.clip(np.round(cy).astype(int), 0, ink.shape[0] - 1)
            lev = ok & ink[iy, ix] & sup[iy, ix]
            rec["levelled_shape"] = list(lev.shape)
            rec["level_angle_deg"] = lv.angle_deg
            rec["level_spread_deg"] = lv.spread_deg
            rec["z_trend_rows"] = float(np.nanmedian(np.diff(np.where(valid_mask(lv.points), lv.points[..., 2], np.nan), axis=0)))
            rec["ink_pixels"] = int(lev.sum())
            if lev.sum() < 1000:
                rec["note"] = "too little labelled ink"
                out["segments"].append(rec)
                continue
            pitch, acv = line_pitch(lev)
            rec["line_pitch_px"] = pitch
            rec["line_pitch_mm"] = pitch * PX_UM / 1000
            rec["line_pitch_autocorr"] = acv
            r = M.layout_slant(lev, pitch)
            rec.update({k: v for k, v in r.items() if k != "blocks"})
            rec["blocks"] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in b.items()} for b in r["blocks"]]
        except Exception as e:  # noqa: BLE001
            rec["error"] = repr(e)
        out["segments"].append(rec)
        print(seg, {k: rec.get(k) for k in ("ink_pixels", "line_pitch_mm", "n_measured", "n_left_neg", "n_left_pos",
                                            "n_right_neg", "n_right_pos", "median_slant_left_deg",
                                            "median_slant_right_deg", "error")}, flush=True)
    segs = [s for s in out["segments"] if s.get("n_measured")]
    out["pooled"] = dict(n_segments=len(segs), left_neg=sum(s["n_left_neg"] for s in segs),
                         left_pos=sum(s["n_left_pos"] for s in segs), right_neg=sum(s["n_right_neg"] for s in segs),
                         right_pos=sum(s["n_right_pos"] for s in segs))
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out["pooled"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
