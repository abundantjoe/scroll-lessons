# REPORT-P47: counting windings inward of w010 on the 1.129 um volume (RULES.md DECL-P4-7 items 1-2)

Provenance: Project HERCULES | owner the owner | [id removed]
Data: `count_1129.json`. Code: `count.py`, `analyze.py`, `synth.py`, `plane.py`, `spiral.py`, `meshgrid.py`.
Numeric only: no image was written, displayed or viewed.

## Verdict
**Inconclusive. There is no evidence for more than 10 windings inward of w010.** Two item-2 checks fail, so this count cannot settle how many windings lie inside w010:
- the planted-sheet error is ≤ 1 winding in no more than ~81 % of trials in any pitch regime;
- the counts are not continuous across rays and z.

The detector that calibrates correctly finds a median of **4** sheet crossings inward of w010 (IQR 3-5). But on synthetic sheets it merges crossings closer than ~100 µm. So a tightly packed core of 10 windings at 70-100 µm pitch is neither confirmed nor excluded.

## Setup (fixed before any inner count was computed)
- **Centre:** the official umbilicus, mapped into the 1.129 um frame with the volume's `transform.json`.
- **Labelled crossings:** from the per-z polyline of the `20260623141924-w010-027` mesh. The mesh gives 18 crossings per ray.
- **Rays:** 64 rays × 24 z-levels, z 70-133 mm. Of the 1536 rays, **1416 are used**:
  - 67 have no w010 or w020 crossing (the strip's partial ends);
  - 42 cross a missing chunk;
  - 11 have incomplete labels.
- **Smoothing:** two variants.
  - A: 2-D Gaussian with FWHM 20 µm.
  - B: 2-D Gaussian with σ 20 µm.
- **Peaks:** minimum distance 20 µm. The threshold rule is "labelled-zone median count closest to 10".
- **Bug note:** the first run was stopped before any inner count existed. It labelled mesh column 0 as w010, but column 0 is w027 (see STATUS.md). That run is not used.

## Results
| | A: FWHM 20 µm | B: σ 20 µm |
|---|---|---|
| Calibration (labelled zone should give 10) | **fails**: 15 even at the top threshold of 16 (the grid edge) | **10** exactly, at threshold 6 |
| Labelled crossings hit, within ±max(20 µm, ¼ spacing) | 0.73 | 0.57 |
| Inner count, median (IQR) [min, max] | 6 (4-7) [1, 24] | **4 (3-5)** [1, 16] |
| Fraction of rays with count > 10 (need ≥ 80 % for DECL item 2) | 6.0 % | 1.5 % |
| Inner count ÷ labelled-zone ratio | 4.0 | 4.0 |
| Spacing: inner peaks, median (IQR) µm | 111 (71-175) | 172 (119-257) |
| Spacing: labelled w010-w020 from the mesh, µm | 159 (119-219) | 159 (119-219) |
| Spacing: image peaks in the labelled zone, µm | 94 (64-140) | 151 (111-208) |
| Adjacent-ray step ≥ 1 / ≥ 2 | 0.70 / 0.31 | 0.62 / 0.19 |
| Adjacent-z step ≥ 1 / ≥ 2 | 0.83 / 0.53 | 0.77 / 0.40 |
| Spearman(inner count, r(w010)) | 0.38 | 0.51 |

- **Median r(w010) per z level:** 0.51-1.82 mm. It is smallest at z 92-106 mm (0.51-0.81 mm).
- **B's median inner count per z:** 3-7, highest at z 111-117 mm, where r(w010) is 1.45-1.82 mm.
- **Implied mean spacing inside w010:** r(w010) divided by the count is 301 µm (IQR 230-413) under B. Under A it is 215 µm (150-299).

## Planted-sheet tests (1-D; real noise residuals; required error ≤ 1 winding)
| Pitch regime | A: median error / share with \|error\| ≤ 1 | B: median error / share with \|error\| ≤ 1 |
|---|---|---|
| 150-250 µm | +9 / 0.08 | +3 / 0.27 |
| 180-260 µm (like the labelled zone) | +10 / 0.07 | +5 / 0.16 |
| 100-150 µm | +3 / 0.30 | **0 / 0.81** |
| 70-100 µm | **0 / 0.80** | −3 / 0.28 |
| 50-70 µm | −3 / 0.33 | −7 / 0.14 |

- **Null test (no planted sheets):** A gives a median of 2-3 false peaks (max 6); B gives 2 (max 4).
- **Why this test is harsher than the real data:** the synthetic profiles are smoothed in 1-D, which leaves more noise than the 2-D smoothing of the real planes. On real data, B's labelled zone calibrates to exactly 10, and its image spacing (151 µm) matches the mesh spacing (159 µm).
- **What it does show:** under B, pitches below ~100 µm are under-counted by 3-7 windings. Under A, pitches above ~100 µm are over-counted.

## What this means (evidence only; no reading authorised)
1. **Beyond-labelled windings:** the DECL-P4-7 item-2 criterion is a count > 10 on ≥ 80 % of rays. Only 1.5-6 % of rays pass, so there is **no evidence** for windings beyond the labelled numbering.
2. **What the calibrated detector sees:** B resolves roughly 3-5 sheet-like crossings inside w010, at about the labelled spacing. It does not see ten 0.07-0.15 mm-pitch windings. Two explanations fit equally well, and this test cannot tell them apart:
   - (a) the core holds fewer resolvable sheets than the fit's numbering, for example a void, crushed material, or an umbilicus offset;
   - (b) the core holds tight windings that are merged below B's ~100 µm resolution.
3. **Continuity is poor:** 19-31 % of adjacent rays differ by 2 or more. A per-ray count is not a trustworthy winding number here.

## Next steps (validation-first)
- Cross-check against p4-core's 2.4 um count, and run a 2-D planted test: sheets inserted into real planes before smoothing.
- A structure-tensor or lasagna-cos cross-check of the sheet count along the same rays. It resolves orientation, not just intensity peaks.
- Only then, the VC3D trace of a core window (item 3), with its declared metrics.

Integrity: one event. It was caught and fixed before any inner count existed, and the misoriented run is not used.
