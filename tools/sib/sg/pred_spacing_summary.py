# Provenance: Project HERCULES | owner the owner | [id removed]
"""Bar-relevant fractions from logs/sib/sg/pred_spacing_0139.json (organizer model output,
calibration only): angle deviation from the render horizontal (circular, mod 180), the
fraction of periodic tiles with pitch CV <= the DECL-SG 11 bar, and per-segment spread.
Usage: python tools/sib/sg/pred_spacing_summary.py > logs/sib/sg/pred_spacing_0139_summary.json"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "pkg" / "src" / "hercules"))
from sg import constants as C  # noqa: E402

r = json.loads(Path("logs/sib/sg/pred_spacing_0139.json").read_text())
out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
       "label": r["label"], "source_sha256_note": "computed from logs/sib/sg/pred_spacing_0139.json", "cells": {}}
for thr in r["thresholds"]:
    for tmm in r["tile_mm"]:
        ok = [t for t in r["tiles"] if t["threshold"] == thr and t["tile_mm"] == tmm
              and t["periodicity_score"] >= r["periodicity_min"] and not t.get("peak_at_lag_edge")]
        dev = np.array([min(t["row_angle_deg"] % 180.0, 180.0 - t["row_angle_deg"] % 180.0) for t in ok])
        cv = np.array([t["pitch_cv"] for t in ok if t["pitch_cv"] is not None])
        rows3 = [t for t in ok if t["n_rows"] >= C.SG11_MIN_ROWS_FOR_CV]
        cv3 = np.array([t["pitch_cv"] for t in rows3 if t["pitch_cv"] is not None])
        pb = np.array([t["pitch_over_band"] for t in ok if t.get("pitch_over_band")])
        out["cells"][f"thr{thr}_tile{tmm:g}mm"] = {
            "n_periodic": len(ok),
            "angle_dev_from_horizontal_deg_p50_p90_max": np.percentile(dev, [50, 90, 100]).tolist() if len(dev) else None,
            "frac_angle_within_bar": float(np.mean(dev <= C.SG11_BASELINE_MAX_DEG)) if len(dev) else None,
            "n_with_cv": int(len(cv)), "frac_cv_within_bar": float(np.mean(cv <= C.SG11_PITCH_CV_MAX)) if len(cv) else None,
            "n_with_ge3_rows": int(len(cv3)),
            "frac_cv_within_bar_ge3_rows": float(np.mean(cv3 <= C.SG11_PITCH_CV_MAX)) if len(cv3) else None,
            "pitch_over_band_p5_p50_p95": np.percentile(pb, [5, 50, 95]).tolist() if len(pb) else None,
            "n_segments": len({t["segment"] for t in ok}),
        }
json.dump(out, sys.stdout, indent=1, sort_keys=True)
print()
