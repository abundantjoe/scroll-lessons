Provenance: Project HERCULES | owner the owner | [id removed]

# p4-purple-de PROTOCOL (DECL-P4-16 item 3: 78/137 keV dual-energy feasibility)

Brief: logs/sib/p4-purple/brief_de.md and brief_common.md. Numbers only; no image, tile or CT pixel is viewed.
This protocol is staged. Each part is pushed before the first number it governs. Nothing in an earlier part is changed after
numbers exist; changes are dated amendments at the end.

## HARD FENCE (restated)
- w010-027 (seg 20260701183124-w010-027 and any other w010-027 mesh): GEOMETRY ONLY. No 137 keV chunk or byte is ever fetched
  at or near any w010-027 vertex; no dual-energy number is computed there. Mesh xyz arrays and the published affines are the only inputs.
- All method design, fitting and validation use the control strip 20260701183125-w028-037 only.
- Enforcement in code: every 137 keV read goes through one function (tools/sib/p4-purple/de/fence.py) that refuses any request
  whose level-0 box lies within 2 mm (833 voxels) of the axis-aligned bounding box of the w010-027 vertices that fall inside the
  137 keV extent (margin at level 0 of the 137 keV frame). If a control location is refused, it is skipped and counted.
- Pre-protocol disclosure: before this file was written, the metadata.json, transform.json, .zattrs, .zgroup and 0/.zarray files
  of the two volumes were fetched to design it. No voxel of either volume was read and no statistic computed.

## Part A: inventory and overlap (pushed before any number of Part A)
### A1 inventory.json
Volumes: 20260323153942-2.400um-0.2m-137keV-masked (V137) and 20260411134726-2.400um-0.2m-78keV-masked (V78), under
PHercParis4/volumes/<v>.zarr. For each: metadata.json fields (voxel size, energy, propagation distance, detector, scintillator,
optics, dates, helical parameters, attenuators and comment, phase retrieval method and delta/beta, unsharp mask, reconstruction
method, flat-field / double-flat (ring) correction, distortion correction, 32-bit histogram and 8-bit window f32 min/max,
masking), shape/chunks/dtype/compressor of every level (0..N), transform.json summary (fixed volume, matrix, landmark count,
residuals), sha256 and byte size of every fetched file. Absent fields are recorded as "not published".
Derived physics numbers (from the published fields only): wavelength, Paganin cutoff length
L_P = sqrt(lambda * z * (delta/beta)) / (2 pi) (nabu transfer 1 / (1 + pi lambda z (delta/beta) f^2)), 8-bit to float mapping
f = w_min + g (w_max - w_min) / 255, and the float value per grey level.

### A2 overlap.json
- Composed affine: to_ref = inv(A(M_78)) @ A(M_137), exactly as p4-highz kedge_cov.py / scans.json; a REF (V78 level-0 xyz)
  point P maps to V137 level-0 xyz Q = inv(to_ref) P.
- Inside extent: 0 <= Qx < 8431, 0 <= Qy < 8431, 0 <= Qz < 6625 (V137 level-0 shape zyx 6625, 8431, 8431).
- Secondary geometric criterion (reported, not primary): inside the reconstruction cylinder,
  (Qx - cx)^2 + (Qy - cy)^2 <= R^2 with cx = cy = 4215 and R = 4215 (from rotation_axis_position 4214.75, square 8431 slices).
- w010-027: mesh 20260701183124-w010-027 on 20260411134726-2.4um, all valid vertices (x, y, z all != -1 and finite);
  tile = (gi * 20 // T, gj * 20 // T) with T and grid from logs/sib/pairs0814b/e2/grid.json on
  origin/claude/gifted-bell-gavnl5-sib-pairs0814b (same as kedge_cov.py). Per tile: fraction inside the extent and inside the
  cylinder. Geometry only. Compared with p4-highz kedge_coverage_e2.json (r3_c10-c17, 14-27 %); any difference > 0.001 absolute
  is explained.
- Control w028-037: mesh 20260701183125-w028-037 on 20260411134726-2.4um, grid logs/sib/p4-tiles-b/grid.json on
  origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b (T_px, canvas/grid scale 20), tile = (gi * 20 // T, gj * 20 // T).
  Per tile: fraction inside extent and cylinder; for every tile with >= 1 inside vertex, a uniform random sample (numpy
  default_rng(20260926 + 1000 r + c)) of min(1000, n_inside) inside vertices; for each, the V137 level-0 byte at
  round(Q) (single-byte HTTP range read of the uncompressed chunk) and the V78 level-0 byte at round(P). Reported: fraction
  non-zero (137), fraction non-zero (78), fraction non-zero in both.

## Amendment A-1 (2026-09-26, before any 137 keV byte was read)
Event: the Part A bounding-box fence (bbox of the w010-027 vertices within 2 mm of the 137 keV extent, dilated 2 mm) spans
x 4700-10097, y 966-10097, z -1666-8291 of the 137 keV frame, i.e. essentially the whole ROI, because the nested inner windings
of w010-027 and w028-037 share the same xyz box. overlap.py therefore refused all 36,382 control samples; no 137 keV byte was
fetched (fence_refused_samples = 36382 in the first overlap.json run). The w010-027 geometry numbers of that run are unaffected.
Change (it narrows nothing that the brief protects; it replaces a box by an exact distance test):
- Fenced set F: every valid vertex of the w010-027 2.4 um mesh (20260701183124, ALL columns and rows, not only c9-c19),
  mapped to the 137 keV frame, kept if within 2 mm of the 137 keV extent.
- A 137 keV read of a level-0 box B (a single voxel is a 1-voxel box) is allowed only if every point of B is at least
  D_f = 146 voxels (0.35 mm) from every vertex of F: 0.131 mm (half-thickness of the w010-027 surface volume, 109 slices at
  2.4 um) + 0.05 mm (vertex spacing, 20 voxels) + 0.17 mm safety. Test: KD-tree of F; exact point-to-box distances for all
  vertices of F within (half-diagonal of B + D_f) of the box centre. Refused reads are skipped and counted, never retried
  elsewhere. fence_box.json is replaced by fence.json (sha256 of the F vertex array, D_f, counts).
- The same function guards every 137 keV read of every later part. The 78 keV volume is not fenced (it is not a 137 keV or
  dual-energy number), but no 78 keV read is made for a dual-energy computation outside the allowed control locations.
- Reported in overlap.json: for the control vertices inside the extent, the distance to F (p1, p5, p50) and the fraction
  that are readable (>= D_f + 0 for single bytes, >= D_f + 266 voxels for 128^3 blocks).

## Part B (2026-09-27; pushed before any 137 keV block or site is read, and before any number below exists)
Inputs fixed now: overlap.json (commit c23c298), fence (amendment A-1, D_f 146 voxels),
colourants.json on origin/claude/gifted-bell-gavnl5-sib-p4-purple commit 143e1e6 (cross-checked, see B4).
No d* has been frozen (p4-depth, p4-tiles-b: no d* freeze file at this time), so no d* statistic is computed.
Physics basis (inventory.json): both volumes are single-material Paganin reconstructions (delta/beta 1000 at 78 keV,
2000 at 137 keV, z 0.22 m) with a Gaussian unsharp mask (4 / 1.2 px; 5 / 2.5 px). In the linear regime the retrieved
value of a thin layer at spatial frequency k is [mu + z k^2 delta] / (1 + z c k^2) U(k); its peak is dominated by delta,
whose 137/78 ratio is about the same for every material, so PER-VOXEL ratios carry almost no composition. The transfer is
exactly 1 at k = 0: the DEPTH-INTEGRATED value of a layer equals mu t at each energy. The decomposition therefore works on
depth-integrated (column) means over a window much wider than the Paganin kernel (L 16.7 / 17.8 um), never on voxels.

### B1 Sites and blocks (control w028-037 only; all reads through the fence)
- Canvas: mesh grid x 20 (1 canvas px ~ 1 voxel, 2.4 um). A SITE is a 498 x 498 canvas-px square (about 1.2 mm), split into
  6 x 6 PATCHES of 83 x 83 px (0.2 mm). Candidate site centres: grid vertices (step 5) whose 25 x 25 grid window is all
  mesh-valid, inside the 137 keV extent and cylinder, and whose 3-D footprint box (window vertices +- 60 um along the normals,
  in 137 keV coordinates) passes the fence. Sites are drawn at random (numpy default_rng(16)) with centres >= 1.5 mm apart,
  until 40 FIT and 40 HELD-OUT sites exist or candidates run out. FIT = the site's tile column c (logs/sib/p4-tiles-b grid)
  even; HELD-OUT = c odd (spatial split). The site centre must also have non-zero 137 and 78 keV data (single-byte reads).
- Flattened sampling: canvas px (i, j) -> mesh point p by bilinear interpolation of the grid; unit normal n from the cross
  product of the grid tangents (central differences), oriented so that n has the same sign convention as the grid
  (d/dj x d/di). Samples at offsets s = -60 .. +60 um in 2.4 um steps (51 samples) at p + s n; 78 keV sampled at the REF
  point, 137 keV at the registered point (B2); trilinear interpolation of the uint8 grey; float f = w_min + g (w_max - w_min)/255.
- Pixel validity: mesh valid and every one of the 51 samples > 0.5 grey in BOTH volumes (masked voxels are 0). A patch is used
  if >= 50 % of its px are valid.
- Registration BLOCKS: 128^3 at 78 keV level 0, centred on control vertices (random, rng 8, >= 0.6 mm apart) whose whole
  137 keV counterpart box (128 + 2 x 24 margin) passes the fence and whose centre is non-zero in both volumes. 30 FIT
  (tile column even) and 30 HELD-OUT (odd) blocks.

### B2 Registration (control only)
- Start: published composed affine (overlap.json composed_affine_ref_to_137_xyz).
- Block match: for each block, 137 keV grey resampled (trilinear) onto the 78 keV block grid through the current model; both
  converted to float, Gaussian sigma 1.5 voxels, standardised; normalised cross-correlation by FFT over shifts +-16 voxels
  (central 96^3 of the 128^3 block); sub-voxel peak by a 3-point parabola per axis. Accepted if peak NCC >= 0.30 and the
  integer peak is not on the search boundary. Output: displacement d (REF voxels) such that 78 keV at P matches 137 keV at
  M(P + d).
- Models (both fitted on FIT blocks only): M-A, affine correction d(P) = A P + b (12 parameters, least squares, iterated
  3-sigma rejection, max 3 rounds); M-T, M-A plus a local translation from inverse-distance-weighted (power 2, 6 nearest)
  FIT-block residuals. The PRIMARY model is the one with the smaller leave-one-out median residual norm on the FIT blocks.
- Residuals on HELD-OUT blocks (after re-matching with the chosen model): norm of the measured remaining d, median and p90 (um).
- Sheet-surface residual (the brief's goal metric) on HELD-OUT sites: every 8th px in both directions, the 1-D profile
  along n in each volume (float, Gaussian sigma 1 sample along the profile); level = midpoint of that volume's void and
  papyrus modes (B3); the crossing nearest to s = 0 on each side (+ and -) with linear interpolation; difference
  137 - 78 of each crossing position (um). Reported: median |diff|, p90 |diff|, signed median, n. Goal < 5 um;
  reported whatever it is.

### B3 Grey-to-mu calibration and two-material decomposition
- Units: float value = linear attenuation in cm^-1 (hypothesis; not published). Void and papyrus modes per volume: the modes
  of the float histograms (bins 1 grey) of all valid samples of the FIT sites, below and above the histogram's Otsu threshold.
- Calibration checks (reported, pass/fail): (i) void mode within +-0.01 cm^-1 of 0 in both volumes; (ii) implied papyrus
  density rho = mode / (mu/rho of C0.70 O0.25 H0.05, xraylib 4.3.0 CS_Total_CP) from each volume at its nominal energy agrees
  within 20 %. (iii) the papyrus-line slope k (below) within 15 % of the monochromatic prediction mu137/mu78 = 0.845.
  Failure of (ii) or (iii) is reported as evidence of polychromatic effective energies or unit differences; the decomposition
  still uses the EMPIRICAL line, which does not need the units.
- Two-material basis: carbonised papyrus (any density; every papyrus/void mixture lies on one line in (C78, C137)) and an
  EXCESS component. Per patch: C_E = mean over valid px and the 51 depth samples (+-60 um) of f_E. Papyrus line fitted on
  FIT-site patches: C137 = k C78 + k0 (Theil-Sen). Patch statistic Z = C137 - (k C78 + k0) in cm^-1 (the high-Z / composition
  estimate). Physics: Z = sum over a layer of (mu137 - k mu78) t / W with W = 122.4 um (51 x 2.4 um). Heavy K-edge elements
  (Au, Hg, Pb: R = mu137/mu78 ~ 1.0) give Z > 0; Br, Ca, As, Fe, Cu (R 0.4-0.7, photoelectric falls with energy) give Z < 0;
  carbon ink (R 0.85) gives Z ~ 0.
- Standardisation: z = (Z - median) / (1.4826 MAD) over FIT-site patches. Secondary statistic (reported only): the same with a
  +-15 um window (13 samples).
- HOTSPOT rule (two-sided): |z| > T, with T = p99 of |z| over FIT-site patches, AND on-sheet: patch C78 >= 0.25 x papyrus
  mode (a sheet fills >= a quarter of the window).

### B4 Validation (HELD-OUT sites only; thresholds come from FIT sites)
- Colourants: compositions, densities and phi = 0.5 binder model of colourants.json 143e1e6; mu, delta, beta recomputed here with
  xraylib 4.3.0 and required to match the file within 1 % (CuO, not in the file: CuO, 6.31 g/cm3, same binder model).
- (a) Known text: official 2.4 um prediction of w028-037 (ink-detection tif on the bucket). ink px = prediction >= strip p90,
  background px = prediction <= strip p50 (percentiles over mesh-valid canvas px of the whole strip, every 8th row and column),
  excluding px within 50 um (21 px) of the other class. Patch label: INK if >= 25 % of px are ink; BLANK if >= 90 % are
  background and none is ink. AUC of Z (ink scored as positive), 95 % CI by site-cluster bootstrap (2000 resamples, rng 5).
  Expected: 0.5 (no composition difference). Also |z| hotspot rate in ink and blank patches.
- (b) Synthetic injection into both volumes' sampled profiles, same position: a "+" glyph in each site (bars 0.4 mm wide,
  1.0 mm long, centred); injected patches = >= 80 % inside the glyph (12 per site). Layer from the + side sheet surface
  (the + crossing of B2 in the 78 keV profile, or +30 um if none) outward, thickness t = 5, 10, 20 um, phi 0.5.
  Forward model per energy: the 1-D linear Paganin model of colourants.json (published delta/beta, z, unsharp, detector PSF
  Gaussian sigma 1 voxel, box average 2.4 um), relative to void, converted to grey, added to the sampled grey, clipped to
  [0, 255]. Classes: Tyrian purple 0/50/90 % Br loss, purpurissum (5 wt % dye on CaCO3), alumina lake, gypsum lake,
  orpiment, lead white, cinnabar, gold, CuO, red ochre Fe2O3, carbon ink. Recovery = fraction of injected patches that are
  hotspots; sensitivity threshold = recovery >= 0.8. False-positive rate = hotspot fraction of uninjected held-out patches.
  Secondary: the same with the pure-absorption model (mu only, same PSF).
- (b') Registration residual: (b) repeated with the 137 keV layer displaced along n by a value drawn (rng 11) per pixel
  column-block (83 px) from the held-out signed surface differences of B2.
- (c) Nulls: (c1) rot-90: the (a) AUC with each site's label map rotated 90 degrees about its centre; must include 0.5 in its
  CI. (c2) misregistered pairing: 137 keV sampled with an extra in-plane displacement of 250 um along the site's i-axis;
  reported: the (a) AUC, the hotspot rate of uninjected patches and the (b) recovery at t = 10 um.
- The run order is fixed: registration -> site sampling -> calibration and FIT statistics (k, k0, median, MAD, T) written
  to fit.json and committed -> held-out validation. No FIT quantity is changed after held-out numbers exist.

### B5 Freeze
DUAL_FREEZE.md: inventory summary, registration model and parameters, calibration, decomposition, statistic, T, the section
B4 results and the sha256 of every tool file. Then REPORT.md and stop. No title-zone number is computed in this task.

## Amendment B-1 (2026-09-27 02:41Z; after fit.json, BEFORE any held-out/validation number)
fit.json: all three calibration checks FAIL (137 keV void 0.044 cm^-1; papyrus-void contrast ratio 137/78 = 0.535 vs
monochromatic 0.849; k = 0.679). The 137 keV float scale is therefore not mu in cm^-1 (unknown offset and gain, or
polychromatic effective energy). Primary injection model (B4 b) is kept unchanged. ADDED variant "paganin_gain137": the
137 keV injected Delta-f is multiplied by g137 = (measured papyrus-void contrast ratio) / (monochromatic ratio) =
0.535 / 0.849 = 0.630 (empirical 137 keV gain, assuming the 78 keV scale is correct, as its void ~0 and density 0.43
g/cm3 suggest). Reported for every class and thickness. The detectability claim in DUAL_FREEZE.md uses the WORSE of the
primary and gain-corrected recoveries.
