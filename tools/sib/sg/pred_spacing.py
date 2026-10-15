# Provenance: Project HERCULES | owner the owner | [id removed]
"""Line-spacing calibration on the organizers' official 2.4 um ink predictions of
PHerc0139 (orchestrator approval of ASK Q6, 2026-09-25T19:41Z).

ORGANIZER MODEL OUTPUT (CALIBRATION ONLY): never evidence of any letter.  Numbers only:
nothing here displays, saves or describes an image.

Segments: the 18 PHerc0139 segments that appear in no project record or log (ASK Q7
default; no sealed, read, canary, clean-control, neighbour or C3 role).  Prediction: model
20260417190342 (new_canon_autoresearch_recipe) on volume 20260102150214 (2.399 um from
metadata.json).  Pixel = render pixel of that volume: the prediction shape is checked
equal to the segment's 2.399 um surface-volume shape.  Downscaled x4 with INTER_AREA
(9.596 um), binarised at 128 (and 96 / 160 for sensitivity; ASK Q8), then measured with
label_spacing.measure_tile on non-overlapping tiles (ink >= 2 %, periodicity >= 0.3
for the summary).  Resumable: one JSON per segment under --work.

Usage: python tools/sib/sg/pred_spacing.py --work DIR --out logs/sib/sg/pred_spacing_0139.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import label_spacing as LS  # noqa: E402

LABEL = "organizer model output (calibration only)"
BUCKET = "vesuvius-challenge-open-data"
VOLUME = "20260102150214"
MODEL = "20260417190342-new_canon_autoresearch_recipe"
SEGMENTS = (
    "20250108000001-w026_2025010854", "20250108000002-w027_2025010845", "20250108000003-w028_2025010836",
    "20250223000000-w059_2025022312", "20251226000000-w055_2025122611", "20260115000001-w056_2026011514",
    "20260127000000-w057_2026012713", "20260130000000-w031_2026013019", "20260203000000-w032_2026020303",
    "20260210000000-w058_2026021020", "20260219000000-w033_2026021913", "20260302000001-w050_2026030220",
    "20260303000000-w034_2026030317", "20260306000000-w038_2026030608", "20260306000001-w051_2026030600",
    "20260310000000-w037_2026031015", "20260316000000-w036_2026031607", "20260318000000-w049_20260318",
)
DOWN = 4
THRESHOLDS = (96, 128, 160)
TILE_MM = (20.0, 30.0)
PERIODIC_MIN = 0.3


def s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", config=Config(signature_version=UNSIGNED))


def segment(seg: str, work: Path, vox_um: float) -> dict:
    import tifffile

    out = work / f"{seg}.json"
    if out.exists():
        return json.loads(out.read_text())
    c = s3()
    sid = seg.split("-")[0]
    key = (f"PHerc0139/segments/{seg}/ink-detection/PHerc0139-{sid}-2.399um-0.22m-78keV-volume-{VOLUME}-"
           f"{MODEL}-tile256-stride128.tif")
    zkey = f"PHerc0139/segments/{seg}/surface-volumes/2.399um-0.22m-78keV-volume-{VOLUME}.zarr/0/.zarray"
    sv_shape = json.loads(c.get_object(Bucket=BUCKET, Key=zkey)["Body"].read())["shape"]
    tif = work / f"{seg}.tif"
    c.download_file(BUCKET, key, str(tif))
    h = hashlib.sha256()
    with open(tif, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    rec = {"segment": seg, "label": LABEL, "key": f"s3://{BUCKET}/{key}", "bytes": tif.stat().st_size,
           "sha256": h.hexdigest(), "sv_shape": sv_shape}
    pred = tifffile.imread(tif)
    tif.unlink()  # keep only the hash (disk budget)
    rec["shape"] = list(pred.shape)
    assert pred.dtype == np.uint8 and list(pred.shape) == list(sv_shape[1:]), (pred.shape, sv_shape)
    small = cv2.resize(pred, (pred.shape[1] // DOWN, pred.shape[0] // DOWN), interpolation=cv2.INTER_AREA)
    del pred
    px_um = vox_um * DOWN
    px_mm = 1000.0 / px_um
    rec["px_um"] = px_um
    rec["tiles"] = []
    for thr in THRESHOLDS:
        ink = (small >= thr).astype(np.uint8) * 255
        for tmm in TILE_MM:
            LS.TILE_MM = tmm
            for (y, x), m, _s in LS.tiles(ink, np.full_like(ink, 255), px_mm):
                r = LS.measure_tile(m, px_mm)
                r.update(threshold=thr, tile_mm=tmm, tile_yx=[y, x], ink_fraction=float(m.mean()))
                if r["pitch_mm"] and r["band_fwhm_mm_median"]:
                    r["pitch_over_band"] = r["pitch_mm"] / r["band_fwhm_mm_median"]
                if r["pitch_mm"] and r["component_height_mm_median"]:
                    r["pitch_over_component_height"] = r["pitch_mm"] / r["component_height_mm_median"]
                rec["tiles"].append(r)
    out.write_text(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    meta = json.loads(s3().get_object(Bucket=BUCKET, Key=f"PHerc0139/volumes/{VOLUME}-2.399um-0.2m-78keV-masked.zarr/metadata.json")["Body"].read())
    vox = round(float(meta["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000.0, 6)
    recs = []
    for seg in SEGMENTS:
        r = segment(seg, work, vox)
        recs.append(r)
        print(seg[15:19], len(r["tiles"]), flush=True)
    summary = {}
    for thr in THRESHOLDS:
        for tmm in TILE_MM:
            ok = [t for r in recs for t in r["tiles"] if t["threshold"] == thr and t["tile_mm"] == tmm
                  and t["periodicity_score"] >= PERIODIC_MIN and not t["peak_at_lag_edge"]]
            summary[f"thr{thr}_tile{tmm:g}mm"] = {
                "n_tiles_periodic": len(ok),
                "n_tiles_all": sum(1 for r in recs for t in r["tiles"] if t["threshold"] == thr and t["tile_mm"] == tmm),
                "n_segments": len({r["segment"] for r in recs for t in r["tiles"] if t in ok}),
                "pitch_mm": LS.summarise(t["pitch_mm"] for t in ok),
                "pitch_cv": LS.summarise(t["pitch_cv"] for t in ok),
                "n_rows": LS.summarise(t["n_rows"] for t in ok),
                "band_mm": LS.summarise(t["band_fwhm_mm_median"] for t in ok),
                "component_height_mm": LS.summarise(t["component_height_mm_median"] for t in ok),
                "pitch_over_band": LS.summarise(t.get("pitch_over_band") for t in ok),
                "pitch_over_component_height": LS.summarise(t.get("pitch_over_component_height") for t in ok),
                "row_angle_deg": LS.summarise(t["row_angle_deg"] for t in ok),
            }
    res = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]", "label": LABEL,
           "approval": "orchestrator answer to ASK Q6, 2026-09-25T19:41:05Z; segments per ASK Q7 default",
           "volume": VOLUME, "voxel_size_um_metadata": vox, "downscale": DOWN, "model": MODEL,
           "thresholds": list(THRESHOLDS), "tile_mm": list(TILE_MM), "periodicity_min": PERIODIC_MIN,
           "segments": [{k: r[k] for k in ("segment", "key", "bytes", "sha256", "shape", "sv_shape", "px_um")} for r in recs],
           "summary": summary, "tiles": [dict(t, segment=r["segment"]) for r in recs for t in r["tiles"]]}
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("done", {k: v["n_tiles_periodic"] for k, v in summary.items()})


if __name__ == "__main__":
    main()
