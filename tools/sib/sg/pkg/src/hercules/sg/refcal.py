# Provenance: Project HERCULES | owner the owner | [id removed]
"""SG 11 REF calibration (proposed DECL-SG11-REFCAL-1): run the SG 11 layout test
mechanically on REF reads of sealed known-text bank windows and report pass rates.

Coded before any use; its sha256 is recorded in logs/sib/sg/proposals before it runs.
Numbers only: nothing here opens, displays or describes an image, and no seal is used
(the layout test needs only the readers' own boxes).

Input JSON: {"voxel_size_um": <from metadata.json>, "canvas_px_per_voxel": 1,
"windows": [{"window_id": str, "readers": {reader_id: [naming with "box" in canvas px]}}]}.
Per window: agreed letters (>= 2 readers, same identity, 150 px; the SG consensus code),
their boxes (member median), then gate.layout_metrics.  Output: per-window SG 11 metrics
and pass rates, plus
* the pass rate the B8 fraction bar would give at each candidate value in
  FRACTION_BAR_GRID (reported only; the bar is declared by the orchestrator);
* the pass rate of the pitch-CV bar and of each component; the height component is given
  both with SG semantics (evaluated only when >= 3 rows qualify) and alone over windows
  with >= 2 qualifying rows;
* the pitch / median-letter-height ratio for windows with >= 2 qualifying rows (the
  candidate basis of the B9 two-row alternative).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from . import constants as C
from . import gate as G

# candidate B8 fraction bars at which the pass rate is reported (report grid, not a bar)
FRACTION_BAR_GRID = (0.5, 0.6, 0.7, 0.75, 0.8, 0.9)
MIN_READERS = 2


def window_metrics(readers: Mapping[str, Any], ppm: float) -> dict:
    if len(readers) < MIN_READERS:
        return {"status": "NOT_EVALUATED", "reason": "fewer_than_2_readers"}
    groups = G._agreed(readers)
    boxes = []
    for g in groups:
        b = G._group_box(g, readers)
        if b is None:
            return {"status": "NOT_EVALUATED", "reason": "letter_box_missing"}
        boxes.append(b)
    m = G.layout_metrics(boxes, ppm) if boxes else {"status": "FAIL", "n_letters": 0, "n_rows": 0,
                                                     "n_rows_within_10deg": 0, "rows_ok": False}
    m["n_agreed"] = len(groups)
    r = pitch_over_height(boxes, ppm) if boxes else None
    if r is not None:
        m.update(r)
    return m


def pitch_over_height(boxes, ppm: float) -> dict | None:
    """Mean row pitch / median letter height over the rows whose baselines lie within the
    SG 11 angle bar, for any window with >= 2 such rows (layout_metrics computes the pitch
    only when >= 3 rows qualify; the B9 two-row alternative needs it at 2)."""
    b = np.asarray(boxes, dtype=float).reshape(-1, 4)
    fits = []
    for row in G.find_rows(b):
        x = (b[row, 0] + b[row, 2]) / 2
        slope, icpt = np.polyfit(x, b[row, 3], 1)
        if abs(np.degrees(np.arctan(slope))) <= C.SG11_BASELINE_MAX_DEG * (1 + C.BAR_REL_EPS):
            fits.append((row, slope, icpt))
    if len(fits) < 2:
        return None
    xref = float(np.concatenate([(b[r, 0] + b[r, 2]) / 2 for r, _, _ in fits]).mean())
    ang = float(np.mean([np.arctan(s) for _, s, _ in fits]))
    ys = sorted(s * xref + i for _, s, i in fits)
    pitch_mm = float(np.mean(np.diff(ys)) * np.cos(ang) / ppm)
    idx = sorted(i for r, _, _ in fits for i in r)
    h_mm = float(np.median((b[idx, 3] - b[idx, 1]) / ppm))
    lo, hi = C.SG11_HEIGHT_MM
    return {"n_rows_for_ratio": len(fits), "row_pitch_mm": pitch_mm, "pitch_over_height": pitch_mm / h_mm if h_mm > 0 else None,
            "two_row_window": len(fits) == 2, "median_height_mm_ge2_rows": h_mm,
            "height_median_ok_ge2_rows": bool(lo * (1 - C.BAR_REL_EPS) <= h_mm <= hi * (1 + C.BAR_REL_EPS))}


def calibrate(data: Mapping[str, Any]) -> dict:
    vox = float(data["voxel_size_um"])
    ppm = G.px_per_mm(vox, 1.0, float(data.get("canvas_px_per_voxel", 1.0)))
    per = {}
    for w in data["windows"]:
        per[w["window_id"]] = window_metrics(w["readers"], ppm)
    ev = {k: v for k, v in per.items() if v.get("status") in ("PASS", "FAIL")}
    n = len(ev)

    def rate(pred):
        return (sum(1 for v in ev.values() if pred(v)) / n) if n else None

    frac = [v.get("letter_height_mm_frac_in_band") for v in ev.values() if v.get("letter_height_mm_frac_in_band") is not None]
    cvs = [v.get("pitch_cv") for v in ev.values() if v.get("pitch_cv") is not None]
    poh = [v.get("pitch_over_height") for v in ev.values() if v.get("pitch_over_height") is not None]
    pct = lambda a: (np.percentile(a, [5, 25, 50, 75, 95]).tolist() if len(a) else None)  # noqa: E731
    out = {
        "provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
        "sg_version": C.SG_VERSION, "proposed_declaration": "DECL-SG11-REFCAL-1",
        "px_per_mm": ppm, "n_windows": len(per), "n_evaluated": n,
        "pass_rate_sg11": rate(lambda v: v["status"] == "PASS"),
        "pass_rate_rows": rate(lambda v: v.get("rows_ok") is True),
        "pass_rate_pitch_cv": rate(lambda v: v.get("pitch_ok") is True),
        "pass_rate_heights_median": rate(lambda v: v.get("heights_ok") is True),  # SG semantics (needs >= 3 rows)
        # the height component alone, over windows with >= 2 qualifying rows (calibration view)
        "pass_rate_heights_median_ge2_rows": rate(lambda v: v.get("height_median_ok_ge2_rows") is True),
        "pass_rate_at_fraction_bar": {f"{b:g}": rate(lambda v, b=b: v.get("heights_ok") is True
                                                     and (v.get("letter_height_mm_frac_in_band") or 0) >= b)
                                      for b in FRACTION_BAR_GRID},
        "letter_height_frac_in_band_p5_p25_p50_p75_p95": pct(frac),
        "pitch_cv_p5_p25_p50_p75_p95": pct(cvs),
        "pitch_over_height_p5_p25_p50_p75_p95": pct(poh),
        "n_two_row_windows": sum(1 for v in ev.values() if v.get("two_row_window")),
        "per_window": per,
    }
    return out


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="SG 11 REF calibration (numbers only)")
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = calibrate(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.out).write_text(json.dumps(G._hashable(res), indent=1, sort_keys=True, ensure_ascii=True) + "\n")
    print(f"windows {res['n_windows']} evaluated {res['n_evaluated']} sg11 pass rate {res['pass_rate_sg11']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
