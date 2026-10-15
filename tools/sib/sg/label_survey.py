# Provenance: Project HERCULES | owner the owner | [id removed]
"""Survey of the official PHerc0139 human ink labels (label_set 20260918): component
counts and letter-blob sizes per segment, numbers only (ruling B9 feasibility check).
Usage: python tools/sib/sg/label_survey.py --cache DIR --out logs/sib/sg/label_survey_0139.json"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import label_spacing as LS  # noqa: E402

LETTER_MIN_MM = 1.0  # blobs with max side < 1 mm are specks (0.01-0.02 mm downsampling residue)
SETS = [(seg, "9.362um-volume-20250728140407", 0) for seg in LS.SEGMENTS] + [
    (seg, "2.399um-volume-20260102150214", 2) for seg in (
        "20250108000005-w030_2025010818", "20250831000000-w040_2025083102", "20260108000000-w041_2026010816",
        "20260112000000-w043_2026011217", "20260115000000-w044_2026011522", "20260126000000-w045_2026012619",
        "20260302000000-w039_2026030210", "20260317000000-w035_2026031718")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cache, log, per = Path(a.cache), [], []
    for seg, vol, level in SETS:
        pre = f"PHerc0139/segments/{seg}/ink-labels/{vol}/20260918/"
        ink, sc = LS.load_array(pre + "inklabels.zarr/", cache, log, level=level)
        px = 1000.0 / sc
        n, lab, st, cen = cv2.connectedComponentsWithStats((ink >= 128).astype(np.uint8), connectivity=8)
        h = st[1:, cv2.CC_STAT_HEIGHT] / px
        w = st[1:, cv2.CC_STAT_WIDTH] / px
        area = st[1:, cv2.CC_STAT_AREA] / px ** 2
        fill = area / np.maximum(h * w, 1e-12)
        big = np.maximum(h, w) >= LETTER_MIN_MM
        per.append({"letter_blobs": {"n": int(big.sum()), "canvas_height_mm": h[big].tolist(),
                                     "canvas_width_mm": w[big].tolist()},
                    "segment": seg, "labels_on": vol, "level": level, "px_um": sc, "shape": list(ink.shape),
                    "ink_fraction": float((ink >= 128).mean()), "n_components": int(n - 1),
                    "max_side_mm": sorted(float(v) for v in np.maximum(h, w)),
                    "bbox_fill_median": float(np.median(fill)) if n > 1 else None,
                    "centroid_nn_mm_median": (float(np.median(np.sort(np.hypot(*(cen[1:, None, :] - cen[None, 1:, :]).transpose(2, 0, 1)), axis=1)[:, 1])) / px
                                              if n > 2 else None)})
        print(seg[15:19], vol[:5], n - 1, flush=True)
    sides = np.concatenate([np.asarray(p["max_side_mm"]) for p in per if p["level"] == 2])
    uniq = [p for p in per if p["level"] == 2]  # the 9.362 um sets repeat these letters
    hh = np.concatenate([p["letter_blobs"]["canvas_height_mm"] for p in uniq])
    ww = np.concatenate([p["letter_blobs"]["canvas_width_mm"] for p in uniq])

    def stats(v):
        return {"n": int(len(v)), "p5_p25_p50_p75_p95": np.percentile(v, [5, 25, 50, 75, 95]).tolist(),
                "frac_in_2_4mm": float(np.mean((v >= 2.0) & (v <= 4.0)))}
    out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "label_set": "20260918", "threshold": ">= 128", "connectivity": 8, "per_set": per,
           "summary_2p4um_level2": {"n_sets": sum(p["level"] == 2 for p in per), "n_components": int(len(sides)),
                                    "max_side_mm_p5_p50_p95": np.percentile(sides, [5, 50, 95]).tolist() if len(sides) else None},
           "letter_blobs_2p4um_level2": {"min_side_mm": LETTER_MIN_MM, "canvas_height": stats(hh), "canvas_width": stats(ww),
                                         "max_side": stats(np.maximum(hh, ww)), "min_side": stats(np.minimum(hh, ww))},
           "downloads": log}
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
