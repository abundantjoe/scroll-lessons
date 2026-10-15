Provenance: Project HERCULES | owner the owner | [id removed]

# Proposals from sibling task contam (for the orchestrator to declare or reject)

These are proposals only. Nothing here is declared, sealed or scored.

## P1. Adopt the contam3d tooling as the FL-09 / I7 method (METRIC-HASH entry)

- Code: tools/sib/contam/contam3d.py (sha256 in REPORT.md and contam_summary.json). It builds on
  src/hercules/geometry/contamination.py, which stays byte-identical (METRIC-HASH-0).
  Suggested: copy contam3d.py into src/hercules/geometry/ (for example as contamination3d.py),
  record its hash in a new METRIC-HASH entry, then mark "Contamination / FL-09 certificate" in
  METHOD.md as VALIDATED only after that entry exists.
- Tests: tests/sib_contam_test_core.py (26 synthetic tests) and tests/sib_contam_test_real.py
  (real-mesh checks plus live planted faults). pytest does not collect the sib_ file names by
  default, so run them explicitly.
- Real-data gate: the planted-fault record logs/sib/contam/planted_faults_0139.json
  (all_caught must be true).

## P2. Same-papyrus rule as implemented (declare explicitly)

- Densify each tifxyz 5 x 5, which gives 4 vox spacing on the organizers' 20 vox grids. Other
  grids get k = ceil(5 * step / 20), so the spacing stays the same.
- For each A sample: the normal distance is the minimum over the B samples within 6 vox
  (Euclidean, 8 nearest) of |(a - b) . n_b|.
- SAME iff #(nd < 2) >= 1000 AND #[0,1) >= 2 x #[2,3). The test runs both ways (A in B and B in
  A). A pair is SAME if either direction is SAME.
- Papyrus units are the connected components of SAME, from geometry only, never segment names.
- These are the RCBANK-1 bins, applied to samples instead of vox^2. At 4 vox spacing, 1000
  samples is about 16000 vox^2 (0.014 cm^2 at 9.362 um), so the area bar is about 16x
  RCBANK-1's 1000 vox^2. If the orchestrator wants RCBANK-1's area bar exactly, declare
  "area(nd < 2) >= 1000 vox^2". The code reports area_within_2_vox2 for every pair.
- Limitation that needs a declaration: the rule cannot separate a true re-trace from two
  windings pressed into contact over an area, or a trace that hopped onto the next winding. Both
  put > 1000 samples within 2 vox. The ratio c01/c23 (reported per pair) separates them only
  partly (see REPORT: re-traces give ratios of about 50-120, seam overlaps 2-5). Proposal: keep
  the rule as the conservative (over-merging) choice for contamination. For D2 pair building,
  treat a unit with a weak edge (ratio < 10) as one unit anyway. Over-merging only removes
  training material; it never lets contamination through.

## P3. FL-09 certificate definition (SG item 8), choose one reading

- PRIMARY (implemented as `passed`): grow R by 64 canvas px in its own plane (the
  DECL-READCAL-A2 halo idiom). Every surface point of R+halo must be >= 128 vox (3-D Euclidean)
  from every surface point of every training patch.
- ALT (reported as `passed_alt_scalar`): every surface point of R itself must be >= 192 vox
  (128 + 64, px taken as vox).
- The two readings are not nested. PRIMARY is stricter along the sheet; ALT is stricter across
  windings (192 vs 128). The conservative choice is to require BOTH.
- Optional voxel-level margin (DECL-D3-A2 precedent, 144 = 128 + slab): --slab-region and
  --slab-train add the render half-depths (15 for -n 31), so the rendered voxels are also
  >= 128 apart.
- Rigour: every distance is certified. For each training sample, certified = d_nn - h_i - h_R,
  where h_i and h_R are proven sampling bounds of the bilinear surfaces (per-quad bound
  max(|e1|/2, |e2|/2, |e1+e2+d|/4); convexity proof in the code). A PASS therefore holds for the
  continuous meshes, not just the samples.
- "All windings and re-traces": 3-D distance covers every winding. Re-traces can also be added
  explicitly (retrace_meshes): each training patch's papyrus as traced on every other organizer
  mesh is added to the training set.

## P4. Training-patch registry of the base checkpoint (needed before any real FL-09 certificate)

- The repo has no patch-level registry for scrollprize/ink_9um step-075000. The HF label bucket
  uses names such as pherc0139-w029 that do not map one-to-one onto S3 segment ids (for
  example, S3 w045's own meta.json has seed_surface_id w029_202601261946).
- Until a patch-level registry exists (built from the official training config or the label
  zarr extents, numbers only), use the conservative superset: whole segments (rect_px null) for
  every 0139 segment in the base-training list of DECL-READCAL-A2, plus every member of their
  papyrus units (REPORT, table U).
- The registry format is fixed in contam3d.load_registry (checkpoint, frame {scroll, volume_id,
  voxel_size_mm}, patches [{id, segment, mesh_dir, mesh_sha256, rect_px, label_source}]). Its
  sha256 is recorded in every certificate.

## P5. Integrity rule I7 (training/evaluation pairs)

For every D2 training/evaluation pair, run `fl09_cert.py cert` with the pair's training registry
and the evaluation window. Commit the JSON (registry sha256, mesh sha256s, raw and certified
minimum, offending points). Any FAIL voids the pair.
