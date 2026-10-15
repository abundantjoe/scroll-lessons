# PHerc0268 pipeline specification (post-audit, ordered)

Scope: umbilicus first, unrolling second, data plan third. Every number below is either a project fact, a measured value from `logs/umb/`, or a declared provisional threshold marked (prov.) that must be fixed from the phantom and the clean-zone distribution before it is quoted as a bar. Refutations from the seven verdicts are kept; nothing refuted is reused.

## 0. Standing facts that override the original proposals

- Frame (logs/umb/UMB-GEOMETRY-RESULT.md): PHerc0268 is a roll crushed flat; former roll axis is the volume **y** axis; windings stacked along **z** (level-4 3-D tensor: |n_z| median 0.76, 45 % of coherent voxels > 0.8), closing in nested hairpins at the x extremes; the y extremes are slanted end faces, not clean windings. Sections to analyse are **xz planes indexed by y**. Every xy-ray product (19 centroid axis_points, FL-4/FL-5 seed grids, the 27-slab xy run) is void on frame grounds, not on mask-tightness grounds.
- Scales (level 3, 69.1 um): 1855 (z) x 1519 (y) x 1519 (x); 95 y-slabs of 16 sections; chunks 128^3, compressor null, 2,097,152 B each, only in-mask chunks stored (~2.4 GB of the 4.28 GB box); a y chunk-row is 128 x 1855 x 1519 = 361 MB. Level 2: 3709 x 3037 x 3037, y-row 1.44 GB, 24 rows, 34.2 GB total. Level 4: 928 x 760 x 760, 0.54 GB. Level 3 resolves packet-scale layering and open seams (every 1-4 mm) but not single winding gaps (mostly < 70 um or ash-filled): level 3 gives the stacking direction and the slit, never a winding count.
- Hardware: tmpfs is RAM; `free -m` recorded before every launch; no launch below 8 GB available; 1.1 GB disk holds JSON/PNG only; proxy: 0.9-1.7 MB/s single stream, ~12 MB/s with >= 32 threads (tools/umb/fetch_zarr.py), to be re-measured per container.
- Measured timings (logs/umb/PHerc0268/st_axis.log): y-run in `--no_models` mode ~11 s per 16-section slab steady state, ~3.5 min for the first slabs including the first row fetch; full model fits ~26 s per slab in the discarded xy run. The 15 y-slabs completed so far (y 0-224, end faces) have confidence 0.0, admissible voters 4-25 % of the mask, residual 1-7.5 mm: they are not evidence about the interior, and the clean fraction of y is unknown until the full pass completes.
- Artefacts in xz sections: ring artefacts are **z-invariant vertical x-stripes**, not rings; the polar high-pass about the image centre (still applied by st_axis.py, `polar_fallbacks` recorded) is the wrong operator in this frame.

## 1. UMBILICUS pipeline

Mapping to the owner's directive: U1 survives as the piecewise-smooth along-y curve with explicit breaks and envelopes; U2 survives with the carrier changed from fibres to sheet layering (fibres: resolution at 8.64 um marginal, absent at 34.6/69 um; cost 2.2e12 voxels; redundant with the layering field; the "fibres miss the axis by R" argument is dropped); U3 survives as secondary foci from hairpin residual clusters tracked along y (no gap-space skeleton, no mean-shift of curvature centres).

### U0. Frame test (level 4, once; repeated for every control scroll and every phantom)
- 3-D structure tensor on the 0.54 GB volume (coherence >= 0.4); roll-axis direction a = eigenvector of the smallest eigenvalue of sum(c n n^T) over coherent voxels.
- Bars: smallest/middle eigenvalue <= 0.5; a within 15 deg of a volume axis (else re-slice along a); face-on strip/crack direction field at level 3 within 15 deg of a (recto strips run around the roll). A phantom written in the wrong frame must fail this test.
- Output: slicing axis (y for 0268), tilt of a to that axis (applied as oblique section geometry if > 3 deg, estimated once per 10-20 mm from full-section slabs, cylindricity ratio >= 3 required or the band is flagged non-cylindrical).

### U1. Section evidence pass (level 3, 95 y-slabs of 16 xz sections, `st_axis.py --axis y`)
1. Fetch level 3 once per container life with >= 32 threads into /dev/shm (4.28 GB box, ~2.4 GB stored) plus level 4; siblings take 12 y-rows each. All later passes (injection, split-half, lambda sweeps) read the cache.
2. Per section, not per slab mean (slab means smear 0.5-1.6 pitches under 9-24 deg tilt): mask eroded >= 1.0 mm (14 vox; the edge gradient outweighs layering ~20x at 3 vox); saturated debris masked (p99.5 dilated 3 vox; `debris_frac` logged, 24-45 % in 10 of 12 earlier slabs, so this is not sparse); **stripe removal** = subtract from each x-column its z-median inside the mask; no polar high-pass.
3. 2-D structure tensor sigma_d 1.2, sigma_i 5 vox; tensors summed over the 16 sections. Coherence gate = 99th percentile of the phase-randomised null of the same slab (measured 0.47-0.54), never an air/ash null (exterior is zero-filled). Contrast gate from the slab's own distribution, effect reported.
4. Voters: stratified subsample <= 300k per slab by sector; residual defined on the **angle** between the observed normal and the model field, Tukey coarse-to-fine 30 -> 10 -> 5 deg; no distance kernel; no lever-arm (1/R^2) weighting; per-band fits with equal weight per band.
5. Outputs per slab: admissible fraction, null threshold, debris fraction, stripe-energy removed, timing, `free -m`.

### U2. Per-section geometry (slit primary)
- Model set, all on the same voters: **slit** = segment F1F2 (half-length c, orientation phi) with the direction field "towards the nearest point of the segment" (offset curves): hairpin voters (|n_x| > 0.7 in the slit frame) fix F1, F2 by robust line concurrency; flat-run voters (normals parallel to the stacking direction) fix phi and the stacking direction only. The confocal-ellipse field is not used (aspect varies with radius; shoulders miss by 20-30 deg). **Affine squeeze** M(v - c) for ovalised, non-flat sections. **Point** = slit with c < 0.5 mm.
- Selection: simpler model kept unless the richer one lowers the median angular residual by >= 10 % (slit over point) / >= 30 % (affine over point) AND split-half agrees (A1 rule). No MDL cost (the Tukey energy is not a likelihood).
- Radial bands by distance to the slit: 0.1-0.25, 0.25-0.5, 0.5-0.85 of the stack half-height; foci reported per band; the umbilicus at y is the **innermost coherent band's** slit; outer band reported separately; "core unobserved at L3" when the inner band has no coherent voters (then no seeds_inner).
- Core envelope: innermost closed streamline of the gap-free smoothed doubled-angle tangent field (index computed only where |v| > v_min on the loop, extended to the full mask); r_core = that loop; half-integer defects stored as U3 seeds; voters inside r_core excluded and the fit iterated fit -> r_core -> refit (convergence to be shown on the phantom, oscillation = flag).
- Sector consistency: sectors >= 45 deg about the nearest focus, scored only on the component of the sector offset perpendicular to the sector's mean normal (10-deg sectors are ill-conditioned by 1/sin 10 deg).
- Multi-centre (U3 mini-umbilici): refit the residual set (angular residual > 10 deg, >= 10 % of voters); accept a secondary slit/point when conditioning >= 0.1 and inlier fraction >= 0.5; "multi-slit" only from hairpin residual clusters > 1 mm from both foci exceeding 10 % of voters, never from accumulator peak counts (a single flattened roll would otherwise be "multi-core" everywhere). Secondary foci are tracked along y by assignment with a footprint term (gate 1.5 mm per 2.2 mm), with birth/death, and become local frames for unrolling.
- Split-half: (a) top vs bottom half of the stack, (b) first 8 vs last 8 sections (`half_first_last_mm`); odd/even sections reported only as the pixel-noise floor (not independent).
- Decoy distances per section: image centre [759, 927], mask centroid, stripe-only foci (foci fitted to the stripe map alone, columns with z-median deviation > 3 MAD).
- Confidence (prov.) = well-conditioned sector coverage x (1 - clip(median angular residual / 15 deg, 0, 1)) x [inner/outer band foci within 0.5 mm ? 1 : 0.5]. "Clean" = full-section slab (mask area within 10 % of the y-median) with coverage >= 0.75 and confidence >= 0.5; the clean fraction of y is reported before any bar is quoted; conditioning/inlier thresholds (0.3 / 0.5 in the audits) have no measured basis and are set from the real-scale phantom and the clean-zone distribution.

### U3. Along-y curve (`axis_spline.py`)
- Cubic B-splines F1(y), F2(y) (and c, phi) with knots every 2 mm (29 sections), weights = confidence, Huber loss (IRLS), lambda by leave-one-slab-out cross-validation (never hand-set or transferred).
- Change points (PELT) on the foci sequence **and on its first differences**: a jump >= 1 mm sustained >= 3 slabs with confidence >= 0.6 both sides inserts a C0 knot (multiplicity 3); a sustained slope change with the same confidence inserts a C1 knot (double); each knot is listed for audit and must coincide with a sector-centre jump.
- No-fit zones: a run >= 5 slabs with confidence < 0.3 is not fitted; output = the two one-sided extrapolations plus an envelope (their disagreement plus slab spread), labelled `bridged, confidence 0`; `ambiguous` if they disagree > 0.5 mm at the midpoint. Bridging is expected outward from the middle, not inward from the ends (end faces are the least constrained part).
- Winding numbers are never assigned from axis agreement across a bridge (agreement is necessary, not sufficient).

### U4. Fine-scale passes (targeted only)
- Level 2 refinement (slit re-fit, sigma_i 8) only for slabs with r_core <= 6 mm, per-slab crops <= 8 mm half-width, one 1.44 GB y-row resident at a time; elsewhere "skipped" is recorded.
- Level 1 windows (20 mm, ~11 MB per station) over low-confidence slabs: along-stacking density profiles, to see whether fused laminae carry signal that level 3 discards; the m7-L3 structure tensor is a reported cross-check in those windows, never a fusion member.
- Sheet counting (M5b) at level 1 along vertical rays up and down from 5 points on the slit: counting-noise floor = count difference between two rays 0.1 mm apart; this is the only place a sheet count is produced by the umbilicus stage.
- Optional fibre direction gate: twelve 384^3 level-0 blocks (54 MB each) in coherent sheets; if line-likeness c_l >= 0.3 in >= 20 % of sheet voxels, the axial mode must agree with a within 5 deg; direction cross-check only, never a position.

### U5. Outputs (committed JSON, replaces `umbilicus_xy()`; downstream must read the flag)
- Per level-3 section y: F1, F2, c, phi (or centre + M for affine), model, confidence, coverage, median angular residual, band foci and their disagreement, split-half distances, decoy distances, stripe energy, r_core or `core unobserved`, secondary foci list, segment_id, flag in {clean, kink(C0/C1), multi-slit, bridged, ambiguous, non-cylindrical, core unobserved}; knot list, break list, lambda, validation table.
- Mini-umbilici: secondary foci tracks with y-range, footprint, gate values.
- **Winding-number field definition**: the radial coordinate of a point p is its distance to the slit segment along the local stacking direction (integral curve of the normal field), in the frame of the segment/mini-umbilicus that owns p. The winding number is a property of the sheet graph, not of the axis: w(p) = the unwrapped index of a tangent-tracked sheet from a reference crossing, with the spiral closure integer reported (closure +1 = one sheet; +N = N sheets wound together; 0 = closed tube, not a roll); it is defined per frame, assigned only where the identity field (section 2) is OBSERVED, counted at level 1/0 where laminae are fused, and crosses a bridged band only when a traced sheet closes the count on both sides. Inside `bridged`, `ambiguous` and `multi-slit` bands only (frame id, local index) is delivered.

### U6. Validation protocol (no ground truth; all computed on PHerc0268 itself)
| id | metric | pass (clean segments unless stated) |
|---|---|---|
| V0 | frame test (U0) | eigenvalue ratio <= 0.5; axis within 15 deg; strip-direction cross-check <= 15 deg |
| V1 | null: phase-randomised slab and a real xy section | confidence 0, no focus; coherence gate = null p99 |
| V2 | well-conditioned sector coverage | >= 0.75; any slab < 0.5 carries a non-clean flag |
| V3 | median angular residual | <= 10 deg (prov., from phantom) |
| V4 | inner vs outer band foci | <= 0.3 mm; sustained larger offset = displaced core, labelled |
| V5 | split-half top/bottom; first/last 8 sections | <= 0.3 mm; median <= 0.15 mm, p95 <= 0.4 mm |
| V6 | M5b sheet balance at level 1 | \|N_up - N_down\| <= 1 on >= 80 % of the 5 points; max - min(N_up + N_down) <= 2; imbalance <= 2x the measured counting-noise floor; run identically on the voided centroid points as the comparator |
| V7 | lasagna (nx, ny at L2) and normal-grid agreement with the (c, Q)/slit normal field | median <= 15 deg; > 30 deg handed to U3; `not computable` if nz sign cannot be decoded after the code audit |
| V8 | decoys: (a) stripe-only foci distance; (b) injected x-stripes at the amplitude measured in air cracks; (c) 20 injected 0.5 mm blobs per slab within 3 mm; (d) voters within 1 mm of the mask edge; (e) image-centre and mask-centroid distances | (a) > 1 mm; (b),(c) shift <= 0.1 mm; (d) < 1 %; (e) reported, with the DECL-UMB-1 M7 rule (no concentricity with the image centre over > 10 mm while the mask centroid is > 2 mm away) |
| V9 | lambda/3 and 3 lambda sensitivity; knot audit | <= 0.2 mm; every knot coincides with a sector jump >= 1 mm with confidence >= 0.6 both sides |
| V10 | leave-10 %-y-band-out | <= 0.3 mm; a band is bridged only if its residual <= 0.3 mm, stored as its envelope |
| V11 | level 3 vs level 2 (where run) | <= 0.3 mm |
| V12 | end-to-end | a seed placed from the slit grows (section 2) a surface whose identity index is constant over >= 20 mm; a closed loop traced at fixed index around the slit closes; sheet count along a fixed x varies smoothly with y except at declared breaks |
| V13 | run record | per-slab timing, `free -m`, `df` on / and /dev/shm, fetch MB/s |

### U7. Phantom protocol (code-path and robustness test only; never evidence about 0268)
- Flattened family (`phantom.py --flat --axis y`), real scale: xz sections >= 1200 (x) x 1400 (z) L3 voxels (83 x 97 mm), >= 192 y-sections, generated section-wise (no 3-D float temporaries; 760^3 phantoms need > 5 GB and cannot carry 1.4-2.9-voxel sheets). Inextensional (perimeter-conserving) folds of radius 0.3-3 mm with a flat contact side, aspect ~0.25, hairpins, roll-axis tilt 10-20 deg, swirls, a C0 kink and a C1 slope break, a two-block oblique shear (30-60 deg to y, 2-6 mm), delamination, ash fill 0-100 %, synthetic blobs plus real debris crops with halos, z-invariant x-stripes at the measured amplitude, PSF sigma 0.7 vox + unsharp, uint8, tight and cylinder masks.
- Upright/eccentric family (point and affine paths): sections >= 1200^2 x 64 at aspect 1.0, 1.3, 2.0, R up to 40 mm.
- Bars: foci within 0.3 mm over >= 90 % of y and slit length within 20 %; no spurious multi-slit on single-roll sections; eccentric centres within 0.15 mm at every aspect; kink/slope break localised within 1 mm; shear band bounded by two C0 knots with no single centre inside; confidence <= 0.3 everywhere in two-lobe zones; wrong-frame phantom fails V0.
- Freeze: generator parameters and seeds hashed (METRIC-HASH) before any further y-run record is read. Because y-run records were read before a flattened-phantom freeze existed, the flattened sweep is recorded as **post-hoc** relative to that run and counts only as a code-path test; the "cannot be iterated into agreement" guarantee holds for estimator changes made after the hash.

### U8. Compute (umbilicus)
Level-3 fetch ~4-6 min at ~12 MB/s; one evidence pass 95 slabs x 11-26 s = 20-45 min per container, or < 10 min split by y-range over 8 containers; curve fit seconds; V8 perturbation passes re-use the cache (~3 passes); level-2 crops and level-1 windows a few hundred MB to ~3 GB of reads; phantoms <= 10 per family per sweep on siblings; one worker per container, working set <= 3 GB plus 4.8 GB of /dev/shm cache. Rejected for cost: full-volume 3-D GVF/Hough at level 3 (51 GB), level-0 anything volumetric.

### U9. Rejected outright (failure mode)
1. One global C2 spline with silent interpolation through the crushed band, or any bridge without envelope/confidence (mode 1).
2. Point concurrency with a distance-based Tukey kernel as the primary estimator (converges on the evolute; mode 1); confocal-ellipse slit field (mode 1).
3. Raw-intensity ring/Hough/GVF energies and the xy polar high-pass in xz sections (mode 4).
4. Fibre-orientation tensor inversion at any level (mode 3: resolution, 2.2e12 voxels, redundancy).
5. Inter-layer-gap skeletonisation and mean-shift of curvature centres (modes 1, 4).
6. Slab-mean tensors, lever-arm weighting, odd/even adjacent-slice split-half as an independence test, air/ash nulls from a zero-filled volume (methodological).
7. Level-4 orientation for pitch (Nyquist) and level-3 ray counts as winding numbers (mode 3).
8. Learned centre regressors, parchment in any role, stiffness or priors transferred from other scrolls' umbilici or single-style replicas (modes 2, 5).
9. The 19 centroid axis_points as axis or initialiser (wrong frame; point z = 14096 is off the scroll).
10. m7 or lasagna as fusion members (shared gradient field; m7 is blind in the core: 0.676 papyrus fraction for correct and jumped surfaces alike).

## 2. UNROLLING pipeline

Owner strategies, one sentence each:

| strategy | status | reason (failure mode) |
|---|---|---|
| R1 deep voxels + fluid optical flow | rejected; the per-section re-anchored ridge tracker survives inside stage X1 | a global smooth/fluid field averages across gaps, shear planes and fragments and drifts 6 mm over the stack without re-anchoring (mode 1); fluid mechanics is the wrong constitutive model and learned flow inherits parchment/replica/organiser-mesh statistics (modes 2, 5); dense flow is 137 GB at level 2 and infeasible at level 0 (mode 3) |
| R2 nnUNet-like micro-density segmentation | rejected; the recto/verso 90-deg alternation survives as stage X3 | the net is untrainable here (100-200 CPU-days, no labels but m7), resamples to foreign spacings and at level 2 degenerates into an air-gap detector (mode 3); cross-beamline grey values are not density (mode 2); ink as a geometric density class is circular and selects surfaces on hallucinated text (mode 4/benchmark rule) |
| R3 constrained-curvature tracing | rejected as a jump preventer; the identity-field idea survives as stage X1 feeding the unchanged grower (X4) | a jumped surface is a geometrically valid surface on another sheet, so curvature/strain caps and every surface-only score are blind to layer identity (mode 1), and the cap only relocates jumps into fused sectors; elasticity limits would come from parchment, fresh papyrus or non-existent replicas (mode 2) |
| umbilicus as origin of straight radial rays | transformed | the radial search direction is the local normal field / distance-to-slit along the stacking direction; straight rays from a point are tangent to sheets in a flattened stack (mode 1) |

### X0. Prerequisites (measured before any run; each recorded)
- Validated slit for at least one y-band (confidence >= 0.5) and the frame test; today no band qualifies, so no winding number can be claimed anywhere yet.
- Level-2 census along the stacking direction on 20 sections: pitch/thickness/gap histogram (assumed 9-17 vox is unsupported; Paris-4 measured ~0.22 mm outside the core, 0.07-0.15 mm inside); separability fraction per y-row (two peaks with a >= 1-voxel dip before smoothing); debris density; coherent-ridge coverage per 256^2 tile every 16th section.
- m7 level-2/3 `.zarray` (chunks, compressor, dtype), level-3 histogram and pyramid pooling method recorded (level 1 is binary 0/255 at th0.2; "m7 > 0.5" is a rule on a model output, not on papyrus).
- One timed read of a level-2 CT y-row (1.44 GB) and one m7 row through the proxy; durable store for outputs named (JSON to the repo; large arrays have no home: deliverables are decimated).

### X1. Sheet identity field (level 2, xz sections tracked along y; replaces R1's tracker and R3's index)
- Stream chunk-aligned y-rows (CT + m7, ~2.6 GB resident) with the halo from the cached adjacent row; split 3 rows per container.
- Per section: stripe removal (column z-median), 1-D along-ray high-pass (no 3-D 1 mm Gaussian: 10-14 GB per row), oriented anisotropic structure tensor (sigma across the normal <= 0.8 vox, along the tangent 3-4 vox; an isotropic sigma_i 2.5 already spans two sheets at 9-vox pitch), 3-D tensor on 16-section sub-slabs for |n_z| and tilt, computed on tiles with halos inside the row.
- Rays along the local layering normal (mostly z): raw-CT lamina/gap peaks primary (prominence >= 3 MAD, width 2-8 vox, > 8 = FUSED, < 2 = debris/fringe), m7 peaks secondary; raw-only vs m7-only index agreement reported and m7 bridging across open seams tested explicitly.
- Linking across sections: gated nearest-neighbour/Hungarian on |dz|/gate + |dwidth|/w0 with gate = 0.5 x locally measured spacing (no pitch assumed); prediction from the segment's own previous displacement plus a mask-envelope prior (no level-3 block-match prior: periodic blocks fail the ratio test and the prior becomes a debris-motion field); measurable displacement is +-2 vox per section (9-sample template in a 13-sample window), rank/sign correlation (not raw ZNCC: debris dominates variance), re-anchor to the ridge within min(1.5 vox, 0.3 x spacing); robust smoothing in-section only; nothing smoothed across sections beyond one step or across segments.
- Events, never interpolation: cut after >= 3 lost points or coherence < 0.5; split (delamination) and contact (two ids kept, never fused); break on thickness change > 50 % or |d| > 2 vox; a sheet carried over an unobserved gap <= 2 mm (converted to grid cells at the actual spacing: 0.122 mm per 0.5-deg ray at 14 mm, so 2 mm = 16 rays, not 60) only when both neighbours link across it; status OBSERVED / BRIDGED / TERMINATED.
- Shear-line detector per section (ridge-phase discontinuity across a line plus coherence drop), tracked along y; every segment it sweeps is cut (integer-spacing slip has |d| ~ 0 and perfect correlation, so forward-backward and two-direction checks cannot see it). Sparse tangential 9 x 9 texture anchors every ~2 mm along each segment, matched every 8 sections, to measure in-sheet slip.
- Translational faults from crossing-label residues (loop counts around a terminating fault tip give the inter-bundle offset; through-going faults stay UNKNOWN); tears tested on the un-eroded crossing field, never by erosion connectivity (a 3^3 erosion deletes every 1.5-3-voxel sheet).
- Independent +y and -y passes; disagreements flagged, never averaged.
- Domain: only where spacing >= 7 vox with a visible gap, coherence >= 0.5, |d| <= 2 vox and the ray-normal angle <= 30 deg; hairpin zones, FUSED slabs, ash and debris-dominated profiles are `no data` (handed to X3/U3). Branch-local ordinal index counted from the top/bottom envelope; no absolute winding number from this stage.
- Outputs: per-branch height maps z_k(x, y) int16 with status, decimated tifxyz grids (10-vox cells), a full-resolution sparse event table, segment-length and fragmentation statistics from a 128-section pilot before any full run.

### X2. Fused-core sheet count (level 0/1 windows, separate declared stage)
Where X0's census says laminae are fused, count sheets inside 1 mm y-slabs of the core (~0.6 GB uint8 at 8.64 um per ROI) by the along-stacking density periodicity (autocorrelation) from the slit outward to the first gap-resolved sheet, where the X1 index takes over; reported with its own confidence.

### X3. Half-layer orientation alternation (level 0, screened tiles only; from R2)
- Gate 0 (existence test, before any operator): in-plane power spectrum of the CT texture on >= 20 clean m7 slabs at level 0, per depth quartile, against a phase-randomised null; the reconstruction's phase-retrieval parameter (delta/beta or filter length) read from the scan metadata and recorded, since it sets the surviving texture scale. If the two depth quartiles do not differ by ~90 deg above the null, X3 is closed with the number recorded (DECL-UMB-1 rejected fibre tensors on mode-3 grounds; this reopens the question only with this measurement).
- Screening from binary m7-L1 run-lengths along organiser normals (~1-3 h per container, CT not read): flag tiles with slab thickness > 1.7x the regional median two-layer thickness (kollesis exception below), two slabs closer than 0.5x regional spacing, low planar coherence, or inside the core; flagged fraction measured (core alone ~14 % of the ~5100 mm^2 mid-section), not assumed.
- Operator: normal-steered anisotropic tensor (sigma_n ~1 vox along the sheet normal, 6-10 vox in-plane; per-half-layer thickness measured ~35 um from one probed m7 chunk, so an isotropic 3-vox window averages both halves), in-plane scale from the measured bundle period (50-100 um); or 2-D orientation on depth-resolved shells of each slab.
- Feature: relative in-plane angle between the two depth quartiles (axis-free); absolute R/V names only where |n . a| < 0.5 and a validated axis direction exists.
- Grammar over half-layers: R|V = one sheet; V|R = sheet-sheet contact (fusion); R|R or V|V = fold (if an in-plane hairpin is traced in adjacent tiles) else cleavage (halves summing to one layer); a 4-layer stack that loses one sheet at a step edge within < 2.5 cm on each side is a **kollesis** (one winding index; measured join spacing declared first); a split into two windings only if both sheets persist > 3 cm in-plane; otherwise AMBIGUOUS. Thickness priors = robust p10-p90 of thickness measured twice (m7 runs and CT along-normal) per region, declared before the core is processed.
- Artefacts: per-section stripe removal before any tensor; line structures removed with a Frangi-type filter at 50-80 um; crack faces identified by their grey profile (air both sides), not by orientation; H/M voxels excluded, never bridged.
- Output per slab: alternation state, winding index contribution, confidence, AMBIGUOUS flag; shear offsets and floating fragments are reported AMBIGUOUS. Ink is never upstream of geometry (sealed-benchmark and circularity grounds only; no claim about what ink_9um learned).

### X4. Grow and render (VC3D unchanged, per piece)
- Per sheet piece: sparse level-0 copy of m7 in rewritten 192^3 chunks with voxel-level zeroing outside +-0.5 x local spacing of the X1 height map (chunk-granular keeping leaves 3-5 windings in place; VC3D's `Slicing.cpp` zero-fills missing blocks); ~220-290 chunks (1.6-2 GB) per 2 x 2 cm patch; `vc_grow_seg_from_seed` in seed mode with ring_run.sh parameters (step 20, 60 generations, normal grids on); `--skip-overlap-check` is a no-op in seed mode and is not a topological check; `cache_root` and the render in /dev/shm counted against RAM, or on siblings with verified disk; per-seed wall time recorded (1275 s measured on i98), no radial-reference option claimed until VC3D's source for this build is read.
- One unmasked far-side grow per patch from a seed chosen by the index map; an external mesh self-intersection/crossing test (the grower has none); arc-length parametrisation along the tracked polyline at assembly (unroll_ring.py's cylindrical projection is not arc-length); render mask carries BRIDGED / TERMINATED / UNVERIFIED; pieces.py remains the trust unit.

### X5. Frames and winding numbers
Per bundle/branch: tangent-tracked sheets with closure integer reported (+1 expected); ply pairs (two crossings closer than half the local spacing with no gap) counted as one; cross-bundle offsets measured only by a traced bridge or a loop count around a terminating fault, else UNKNOWN; absolute numbers only for the adjacency component containing the primary track with all offsets known and all cycles closing; everything else (frame id, local index). A zero count of local-only frames in the core triggers review.

### X6. Validation (unrolling)
| id | metric | pass |
|---|---|---|
| W1 | synthetic suite on the flattened phantom (>= 192 sections) with sheared cracks 0-0.5 spacing, fused sectors, hairpins, delamination, translational fault, debris-filled crack along y, 1.5-vox partial-volume sheets, x-stripes, integer-spacing shear | correct bridge >= 95 % of cracks <= 2 mm; false termination on hairpins <= 5 %; 0 bridges across fused sectors; one origin for continuous squeezed/stadium sections; frame-with-offset for terminating faults, UNKNOWN for through-going; no bundle along a debris crack; stripes rejected; shear line detected and no track crosses unflagged; injected one-sheet jump flagged on 100 % of cases |
| W2 | index continuity along the mesh (raw-CT rays along the layering normal) | >= 98 % of vertices in the modal class per piece; 0 index steps inside a piece; FUSED fraction < 10 % or the piece is split; retrospective on ring1 i98/i96/i99/i101/i103 after re-cutting them in xz and yz (`xsec` cuts z only today): must reproduce the owner's marks or the detector is not used |
| W3 | neighbour clearance | >= 0.5 x local spacing for >= 98 % of vertices; FUSED counts as fail; < 0.3 masked from the render |
| W4 | coverage | per slab and per 5 mm band: voting fraction of the mask and fraction of rays with >= 1 crossing; no winding numbers where coverage is below the declared fraction; alignment bars never reported without coverage |
| W5 | raw-only vs m7-only index agreement; m7 seam-bridging test | reported; disagreement is a finding about m7 |
| W6 | masked grow vs unmasked far-side grow | >= 95 % of overlapping vertices within 0.25 x spacing; bimodal separation fails the crack |
| W7 | fibre-bundle continuity across BRIDGED cracks (2-D template, lags to +-0.5 mm, equal tensor direction within 10 deg, one-spacing null) | >= 80 % of cracks above the null p95; failures relabelled UNVERIFIED |
| W8 | forward/backward and +y/-y agreement | necessary only: median <= 0.5 vox, p95 <= 1.5 vox; no hop-detection claim |
| W9 | drift: chained level-3 block matches at 16-section steps with loop closure, plus a >= 512-section real-slab phantom with real debris, stripes and an integer-spacing shear | <= 2 vox at level 2 for 95 % of blocks; z/z+500 direct matching is unmeasurable and dropped |
| W10 | normal gate against the slit/affine model field (not raw radial cos; sheetcheck.py uses one z-constant centre) | withheld where axis confidence < 0.5 |
| W11 | X3 metrics: separability AUC on depth quartiles (>= 0.80 at level 0), in-plane-isotropisation null (<= 0.60) with a synthetic bilayer positive control, outcome fractions with the kollesis class (clean >= 90 % one-sheet, AMBIGUOUS <= 2 %; core reported), contamination injection incl. kollesis and hairpin inserts (count unchanged on >= 98 % of rays), tile-shift reproducibility (>= 99 %), lasagna normal agreement (<= 15 deg) | as stated; a core AMBIGUOUS fraction > 50 % is itself the disclosed result |
| W12 | external reference-only check | run X1 on a scroll with an audited organiser segmentation never used for anything else and report absolute hop/distance statistics |
| W13 | seam ZNCC in the unrolled strip | median >= 0.5, no seam offset > 2 px |
| W14 | owner cross-section audit in xz and yz | retained final gate until W2-W7 reproduce the owner's verdict on the nine ring1 patches |

### X7. Compute (unrolling)
Identity pass: 24 level-2 CT y-rows (34.2 GB, uncompressed bytes unavoidable) plus m7 rows (size unverified), I/O-bound and unscheduled until one row is timed; ~1.4-4e9 trilinear samples (minutes of CPU per row); tracker mechanics 4-8 s per section single-core, 12-25 CPU-h for both directions over 8 containers; outputs decimated (< 1 GB). Per patch: 1.6-2 GB of m7 chunks, 100-300 MB sparse zarr, two 21-min grows, metrics < 10 min; level-0 lamina orientation inside the band 1.2e9 voxels, 10-20 min. X3: 7k-21k 256^3 tiles at ~20 s wall with 2 workers <= 2 GB each, 50-150 GB per container per pass with a <= 2 GB chunk LRU, RSS + tmpfs <= 12 GB. Infeasible and struck: nnUNet training/inference (25 CPU-days per container before overlap and TTA), dense flow, any level-0 volumetric pass.

## 3. DATA plan (what is actually usable)

Usable, with role and gate:
- **PHerc0268 masked CT** `20251110183117-8.640um-1.2m-116keV-masked.zarr`, levels 0-5, compressor null, 128^3 chunks: the only data any deployed component is fitted on. Level 3 + 4 cached per container life in /dev/shm; level 2 as y-rows (identity field) or crops; level 1 as 20 mm windows and core ROIs; level 0 as chunk-aligned tiles only.
- **m7 surface** `...surface-m7-L0-th0.2.zarr`: binary 0/255 at level 1 (probed), 192^3 zstd chunks at level 3; pyramid pooling method unverified; audited by sampling against the CT before use; roles: X1 secondary channel, X4 grower surface volume (masked copy), cross-check comparator; never a fusion member, never "probability".
- **lasagna** (`PHerc0268.lasagna.json` v2: cos at level 1, grad_mag/nx/ny at level 2, no nz, umbilicus_json empty, computed under a z-axis assumption): cross-check of normal directions only (V7, W11) after a line-by-line decode audit; `not computable` if the xz in-plane direction cannot be recovered with sign. It is not a winding-index field.
- **normal grids** (level 0, grid-step 64, > 1000 files, undocumented format): consumed by VC3D as today (weight 10); any other use only after the generating code is audited; the ~10-29 GB download is budgeted when scheduled.
- **Same-protocol controls** PHerc1451, 0800, 1447 (MAY) and 0841, 0139 (JULY), streamed at levels 3-4: upright/point code path only, each after its own frame test; no evidence about the slit path. Check whether PHerc0490A is a second crushed example before claiming any cross-scroll evidence for the slit path.
- **Organiser umbilicus for PHerc. Paris 4 (Scroll 1)** on the 2.4 um ESRF volume 20260411134726 (146 control points, logs/p4/recon.json; EduceLab licence): licence-gated intact-roll control of the point path at level 5 (~77 um) against the umbilicus divided by 32, parsed by our own code; recorded NOT RUN otherwise. This corrects the project fact: no organiser umbilicus exists for PHerc0268; one exists for Paris 4. Scroll 1 is Paris 4, not Paris 3.
- **HF checkpoints** (ink_9um, dinovol ps8, fiber_dinoguided, ink_3d_dino_guided; all 2.2-2.4 um except ink_9um): no role in the umbilicus or in geometry; the resolution-gap gate is deferred to the ink stage, made sparse (<= 8 matched crops per region, comparing only overlapping tokens; a 128^3 crop is 0.5-1 winding at 2.4 um and 2-4 at 8.64 um), and preceded by a bucket listing proving a 2.4 um <-> 8.64 um transform exists for PHerc0009B and PHerc0343P (RULES.md records a transform only for 0841). No upsampling of 0268.
- **Computational phantoms** (section 1, U7 and section 2, W1): both frames, seeded, hashed; test code paths and robustness; explicit non-roles: texture realism, ink contrast, real collapse mechanics, real artefacts, real sheet count; never training data, never evidence about 0268.
- **Synthetic perturbations of real 0268 data** (injected stripes, blobs, real debris crops, known warps, one-sheet jumps): tests only (V8, W1, W9, W11).

Struck:
- En-Gedi in any role including "reference" (the scroll is charred, not uncharred; the strike is on material grounds: collagen, no laminated gaps, radio-dense ink, lab micro-CT ~18 um; owner's toxic-data rule; the 2016 paper may be cited, its bytes may not be used). All parchment and vellum.
- "Unreleased ESRF/Diamond raw volumes" and any 3-D MAE or nnUNet training (no data, no GPU, no labels but m7).
- Physical "synthetic carbonised papyrus replicas" as ground truth (none exist; a single fabricator's collapse style would be memorised).
- Legacy EduceLab DLS volumes as training data; as a control they would need an extra 2.4 um <-> 7.91 um transform and a fresh licence scope, so the Paris-4 ESRF control replaces them.
- Pooling MAY, JULY, 2.4 um and DLS volumes as one domain for any fine-scale model; any learned axis estimator; organiser products of other scrolls as priors.

## 4. Execution order and gates

1. U0 frame test and V0 (hours). 2. Phantom freeze/hash and U7 sweep in both frames (post-hoc status recorded). 3. Full U1-U3 y-pass across 8 containers; report the clean fraction of y, V1-V5, V8-V10 before any bar is quoted or any seed placed. 4. U4 fine-scale passes and V6 (M5b), V7, V11, V13. 5. Only then X0 census and X1 pilot (128 sections) with W1, W2 retrospective, W4, W5; X3 gate 0 may run in parallel on clean outer slabs because it is axis-free. 6. X1 full pass, X2 where fused, X4-X6 per piece with W2-W10, W13, W14; no ink model and no text claim before a piece passes W2, W3 and W14, and never across a BRIDGED or UNVERIFIED crack or inside a `bridged`/`ambiguous`/`multi-slit` band.