Provenance: Project HERCULES | owner the owner | [id removed]

# p4-tiles-a w1: DECL-P4-17-A1 block windows on M1

Builder report. No window, tile or map pixel was opened or viewed. The checks below use numbers, shapes and hashes only.

- Material: M1, the official 20260417190342 prediction on 20260701183124-w010-027 (2.4 um). The re-downloaded prediction and z.tif sha256 match the earlier M1 downloads (w1/downloads.jsonl).
- Windows: 15, each 2 x 2 strip-a tiles (4 x 4 cm, 16686 canvas px) cut to 1068 x 1068 (26.7 px/mm). In declared order:
  - 8 title windows: (0,15), (0,16), (2,15), (3,12), (1,15), (2,16), (0,18), (4,15);
  - 6 known-text controls: (0,5), (2,5), (0,7), (2,7), (4,3), (4,5);
  - the blank-end descriptive null (4,18).
- The rot-90 null copies are drawn by the harness (seed 20260927); they are not built here.
- Display: raw uint8 prediction, 0 outside mesh-valid, cv2.INTER_AREA, builder.png_bytes.
  - Every file: IHDR/IDAT/IEND only, 1068 x 1068, 8-bit grey (asserted).
  - 15 unique sha256.
  - The raw prediction has no nonzero pixels outside the mesh-valid mask in any window.
- Names: tiles/<uuid4>.png. The key (uuid -> r, c) is manifest.json only.
- frac_valid is 0.900-1.000 for all windows.
- **Labelled adjacency** (DECL-P4-17-A1 item 4). Source: p4-excl excl_a.json, sha256 c40f973f...8910. Each window takes the minimum over its 4 tiles of the npz-point and all-vertex distances.
  - **All 15 windows are labelled-adjacent** (< 1.2 mm).
  - The title windows' minimum distances are 0.00-0.33 mm, the controls' 0.00 mm, and (4,18) 0.566 mm.
  - So no w1 window can become a candidate. A positive window only redirects the model-free channels (L4, E2) to that place.
- Checked with tools/p4/norm_manifest.py (without --coverage) on this commit: 15 eligible, 15 unique PNGs, sha256 verified.
- Code: tools/sib/p4-tiles-a/build_w1.py. Timing: fetch about 30 s, build about 1 min.
- Integrity: no issues.
