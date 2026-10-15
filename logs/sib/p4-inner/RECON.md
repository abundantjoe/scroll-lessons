# P4-inner reconnaissance: windings w000-w009 of PHerc. Paris 4

Provenance: Project HERCULES | owner the owner | [id removed]
Generated: 2026-09-26T10:15Z. The machine-readable version is `recon.json`. The scripts are `ls.py`, `radii.py` and `probe.py`.

Viewing: no image, CT slice, render, ink map or photo was opened. I read only:
- listings and JSON metadata;
- HTTP HEAD byte sizes;
- mesh vertex-coordinate TIFFs (x/y/z), streamed into memory and not saved.

No title words are recorded.

Frame: all numbers are in the 20260411134726 frame (2.4 um voxels). r is the horizontal distance from the official umbilicus polyline.

## 1. Official products inward of w010
**No traced surface covers w000-w009.** This holds on both volumes.
- **Strips:** the 81 segment directories contain no strip below w010. The innermost strips are:
  - `20260701183124-w010-027`: 2.4 um mesh only;
  - `20260623141924-w010-027`: 2.4 um mesh, plus a 1.129 um mesh and a 1 um ink TIFF (1.18 GB).
- **Spiral fit:** the published dataset (dl.ash2txt.org `spiral_datasets/PHercParis4/`) holds only the fit's inputs. Its fitted per-winding meshes are not published.
  - `abs_winding.json` has 59 points, with windings 10-63 and none below 10.
  - None of the 89,237 `verified_patches/` entries is named w000-w009.
- **Radial extent of the strips** (r in mm, as p0 / p5 / p50 / p95 / p100):

| Strip | p0 | p5 | p50 | p95 | p100 | z range (mm) |
|---|---|---|---|---|---|---|
| 20260701 w010-027 | 0.27 | 1.49 | 3.62 | 6.29 | 9.19 | 28.7-172.9 |
| 20260623 w010-027 | 0.27 | 1.57 | 3.67 | 6.24 | 8.72 | 67.1-163.4 |
| 20260701 w028-037 | 2.05 | 3.61 | 6.22 | 9.10 | 13.44 | 28.7-172.8 |

  - The inner edge of w010-027 (p5 in each 10 mm z bin) lies at 0.70-1.62 mm.
  - So **w000-w009 fill a core of radius about 0.7-1.6 mm** around the umbilicus.
- **Dense 3-D products** cover the whole 2.4 um volume, including the core:
  - surface m7 L2 and recto L0 (`representations/predictions/surfaces/…`)
  - lasagna L2
  - fibers 0801 and 0915 (L1)
  - ink-3d 20260428123845

  I checked this with HEAD requests on the chunks at the umbilicus and at r = 0.75 mm, for z = 50-160 mm. Every chunk exists. Compressed sizes are 16 kB-4.2 MB, which means the content is not constant.
  - These are volumes, not a traced sheet.
  - No representation exists on 20260608103018.

## 2. Area of w000-w009, and the 1.129 um footprint
- **Model:**
  - Per z bin, the windings are r_k = r_in·(k+0.5)/10.5, where r_in is the w010-027 p5 radius.
  - The tortuosity is calibrated on the mesh area of w010-027 (τ ≈ 0.98).
- **Total area:** **~66-80 cm² over z 28.7-172.9 mm**, of which about **58 cm²** is inside the written region (z 38.4-163.2 mm).
- **w004-009:** about 84 % of the total, **~55-67 cm²**.
- **Validation:**
  - The same Σr model predicts w028-037/w010-027 ≈ 0.98. The mesh-area ratio is 1.05.
  - The abs_winding annotations give r(w010) = 1.46 mm at z = 153 mm, consistent with the mesh p5.
- **Caveat:** the implied pitch inside w010 is ~0.07-0.15 mm, against ~0.22 mm outside. The core may be compressed or damaged.
- **1.129 um footprint:** the core is covered only partly.
  - **x, y:** the umbilicus stays at least 3.9 mm inside the footprint.
  - **z:** the footprint covers only 67.4-135.3 mm, about 54 % of the written region.
  - The inner area inside the footprint is **~29-31 cm²**.

## 3. Cost on a 4-CPU container with no GPU
- **Tracing:**
  - The official `fit_spiral.py` needs an NVIDIA GPU (tutorial). It cannot run here.
  - The CPU route is VC3D patch growth on the surface-m7 L2 prediction, guided by lasagna and fibers. It needs a VC3D build, which is not installed.
  - Streamed inputs: surface-m7 about 70-120 MB, lasagna about 230 MB, fibers about 50-150 MB, and raw 2.4 um L2 about 1.6 GB.
  - Estimate: 4-40 CPU-h and under 1 GB of disk. This is not measured.
  - The dominant risk is winding assignment at ~0.1 mm pitch.
- **Rendering w004-009** (about 55-67 cm²):
  - 2.4 um L0 at 31 layers: about 30-36 GB. It has to be streamed in windows.
  - ink_9um input: about 1.3-1.5 GB.
- **Ink:**
  - **ink_9um step-075000:** public, and the cost is measured (logs/c3). It runs at ~0.16 CPU-h/cm², about 2.5 h wall for the strip. It was trained on all 8 labelled Paris 4 segments.
  - **2.4 um model 20260417190342:** the matching recipe is the public HF `scrollprize/ink_canonical_2um` (ResNet-152 3D, MIT). The link rests on the recipe name only. Estimated cost is ~5-20 CPU-h/cm², so only 2×2 cm windows are feasible.
  - **1 um model 20260709123958:** not on Hugging Face. A search returns nothing, and none of the 43 scrollprize models is a 1 um ink model. It cannot be run.

## 4. Official statements (location only)
- "The expected title region has shown no detectable ink so far — possibly a different ink, and the top rows are physically missing — so finding it may take better methods, higher resolution, or looking somewhere new." (https://scrollprize.org/prizes, re-fetched 2026-09-26T10:13:11Z)
- "The title often follows the end of the primary text, in a subsequent column that can be otherwise blank. When the final column of the primary text is short, it may also appear below this last column." (https://scrollprize.substack.com/p/30k-first-title-prize)
- No official source gives a winding, radius or coordinates for the title. "Inward of w010" is our derivation, not an organizer statement.

## Gaps
- Chunk sizes show that content exists. They do not show that sheets are resolved in the core.
- The p5 radius is used as a proxy for w010.
- The inner pitch is inferred, not measured.
- The CPU cost of the 2.4 um model is estimated, not benchmarked.
- The abs_winding points cluster near z ≈ 150 mm.
