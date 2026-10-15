Provenance: Project HERCULES | owner the owner | [id removed]

STATUS: DONE (2026-09-26)

# KTLB-4P preparation: PHerc0500P2

Sibling builder report. Nothing here is a declaration. Throughout:
- only numbers were computed: no image, slice, render or reference map was viewed or displayed;
- no ink model was run on 0500P2;
- every download is sha256-logged (`downloads_*.json`, `/work/k4p/chunk_sha256.jsonl.gz` for CT chunks);
- every run is in `logs/sib/handed/runs.jsonl` (the shared sibling logger).

Machine-readable summary: `ktlb4p_summary.json`.

## Headline

1. **Registration 9.362 <-> 2.215 um PASSES** on the pre-registered attempt 2 (affine + linear RBF field): median r 0.929, RMS 0.40 vox, control 15/16. Attempt 1 (affine alone) FAILED median r (0.834 < 0.85) on its own 16 held-out patches. A post-hoc diagnostic shows the affine alone gives median r 0.915 on the attempt-2 patches, so most of the pass-vs-fail difference is the patch population, not the field. Alignment is sub-voxel under both models.
2. **20 mutually independent 2 x 2 cm candidate windows** pass mesh-valid >= 0.90, reference-mapped >= 0.90, window zero-CT <= 5 % and CORR-RETRACE-RULE certification. They come from 13 of the 27 papyrus units. **S estimate (not a measurement): 20 x {2, 4, 7} letters = 40 / 80 / 140.** That clears S >= 30 on paper, subject to items 3 and 4.
3. **The mirror state of 0500P2 is NOT geometrically settled (FLAG).** The organizer `text_side` source gives chirality +1 on all 20 windows. On the only 2 windows where the mesh's curvature centre is a valid source (500P2_front, condition 5.8 and 6.6), it gives -1 at agreement about 1.0. The sources contradict each other. By the accepted rule, both mirror states must be read.
4. **No blank candidate exists.** Among 1,624 gated candidate windows the lowest reference-ink fraction is 2.26 % (bar: < 1 %). Blanks for this fold must come from elsewhere, or the blank definition must be decided (ASK 6).
5. **The "blob field" worry is not supported by the numeric structure of the reference maps.** They look like 0139's known-text maps from the same model, with somewhat smaller components and thinner strokes (table in section 5). Whether they are legible can only be measured by the sealing readers (REF VOID check).

## 1. Inventory (inventory.json, downloads_meshes.json, downloads_refmaps.json)

- **Sample.** PHerc0500P2, catalogued as a **fragment**.
- **Volumes** (voxel size from each metadata.json):
  - 20250820143440 9.362 um: JULY protocol. L0 (z, y, x) 7057 x 4196 x 4196. metadata.json sha256 5c630ced... Its top-to-bottom flag is null and it has no text_side.
  - 20250528085330 4.317 um: the frame all 46 meshes were traced in. top-to-bottom True, `text_side = -y`.
  - 20250526151718 2.215 um: the reference-map frame. L0 28096 x 18209 x 18209. metadata.json sha256 b2b4e120...
  - 20250821110041 0.55 um: flagged left_handed = true. The organizer affines to it have det < 0, consistent with the flag.
- **Segments.** 46 organizer segments. Each has tifxyz meshes on 4.317, 9.362 and 2.215 um (one also on 0.55 um), surface volumes on all three (9.362 um: 12.4 GB total), and an organizer reference ink map (model 20260417190342, on the 2.215 um canvas, 46 files, 545 MB, sha256 each).
- **Second model.** 2 segments also have maps from model 20260709123958 (not used).
- **Human labels.** One set, on segment 20250825181859--1 (2.215 um, label_set 20260918).
- **Photos.** One organizer photo exists (not opened).
- **Canvases.** Each frame's mesh is re-sampled at a 20-vox step (scale 0.05), so the 9.362 and 2.215 um canvases differ by F and correspond only through 3-D geometry. The reference rasters are exactly the 2.215 um grid x 20.

## 2. Frame checks (frame_9um.json, frame_9um_L2.json, frame_4um_L4.json)

- **In the 9.362 um frame:** 0-0.1 % of vertices are outside the volume for all 46 meshes. 14 meshes lie 5.1-14.6 % on zero CT.
- **Partial volume at an air boundary is ruled out as the cause:** the same numbers appear at level 2 (37 um) and with a +-1 voxel dilation (for example 0.146 / 0.149 / 0.146).
- **In the native 4.317 um frame:**
  - 3 meshes (00308, 00377, 00346) are 11-15 % on zero CT as well. Their traces extend beyond the mask.
  - About 10 others are <= 5 % natively. The larger zero fraction in the 9 um frame points to a tighter 9 um mask (the registration shows the frame mapping itself is sub-voxel).
- **Default applied (ASK 1):** the 5 % gate is applied per window. 1,941 lattice candidates go to 1,624 after the gate.

## 3. Registration (reg/; CT only)

- **Coarse check** (coarse_check.json). With the organizer affine 20250820143440 -> 20250526151718 (det 74.79 vs F^3 = 75.5; a remount of about 163 degrees plus a 14-degree tilt, no flip), the median slab NCC is 0.758 against <= 0.28 for every rotated or flipped control.
- **Protocol.**
  - 40 patches (48 x 256 x 256 at 9 um) were chosen by code from level-3 and level-5 CT only (patch_plan.json).
  - Pre-registered and pushed before any level-0 read: `prereg_heldout.md` + `prereg_clarification.md` (commits e52d5b4, b37a3cc).
  - The 2.215 um volume is read at level 1, with the C6 prefilter sigma kept in total (disclosed).
- **Attempt 1 (affine).**
  - Selected on the 24 fit patches: 2 passes, fit LOO RMS 0.86 vox, so the affine is kept by the rule.
  - Frozen as model_final.json (sha256 9a777170...) before any held-out read.
  - Held-out (16): median r **0.834 FAIL**, RMS 0.82 PASS, control drop 0.74 with 16/16 clear PASS. Verdict **FAIL** (heldout_result.json, commit fee8ba5).
- **Attempt 2 (non-affine; REG-0841-NA precedent).**
  - Pre-registered (prereg_attempt2.md, new_heldout_plan.json, commit bc1ef45): 16 NEW stratified patches at least 32 vox from all 40 earlier blocks.
  - The field was selected by LOO over the 40 existing correspondences: linear-kernel RBF, smoothing 0.1, LOO RMS 0.693 vs 0.748 for the affine alone.
  - Frozen (field_final.json, sha256 40def3d7...; commit 235a17b) before any new block was read.
  - New held-out (16): median r **0.929**, min 0.607, RMS **0.40 vox** (max 1.03), control drop 0.90 with 15/16 clear. **PASS** (heldout2_result.json).
- **Post-hoc diagnostic** (labelled as such; not a bar). The affine alone on the attempt-2 blocks gives median r 0.915, RMS 0.51. The r bar is therefore sensitive to which patches are drawn: the local-shift NCC ceiling was 0.863 on the attempt-1 patches and 0.926 on the attempt-2 patches. The registration itself is sub-voxel under either model.
- **Map for use:** `f(p) = A (p + u(p)) + c`, with A and c from model_final.json and u from field_final.json. Level-0 voxels, (x, y, z).

## 4. Candidate windows and certification (candidate_windows.json, certification.json)

- **Mapping onto the reference.** For every 8-px sample of each 9 um canvas: 3-D mesh point, then the registered map, then the nearest vertex of the 5x5-densified 2.215 um mesh of the same segment. The median distance is 2.2 vox (2.215 um), about 0.5 vox at 9 um. 96.7-99.7 % of valid samples map per segment.
- **Candidate criteria.** 2136 x 2136 px windows on a 128-px lattice with mesh-valid >= 0.90, reference-mapped >= 0.90 and window zero-CT <= 5 %. The reference value never selects. It is used only for the blank flag the brief asks for.
- **Totals.** 1,941 lattice windows on 27 segments. The 13 `wrapNN` segments are all smaller than 2 cm, so they give none. 1,624 remain after the frame gate.
- **Certification.** CORR-RETRACE-RULE: literal nearest-densified-vertex form OR point-to-surface form, >= 1000 points within 2 vox and count[0,1) >= 2 x count[2,3). The test runs on 4-px-lattice points against 5x5-densified surfaces. Windows on the same segment conflict if their canvases overlap.
- **Papyrus units.** Segments whose smaller member has >= 20 % of its points within 2 vox of the other are clustered. That gives 27 units: 5 clusters of 3-8 re-traced segments, and the other 22 segments are singletons.
- **Independent windows.** A greedy maximal set ordered only by (segment, y0, x0) gives **20 mutually independent windows**:

| segment | y0 | x0 | mesh-valid | ref-mapped | zero CT |
|---|---|---|---|---|---|
| 20250611132918-z_dbg_gen_00302 | 768 | 512 | 0.91 | 0.91 | 0.000 |
| 20250611134135-z_dbg_gen_00331 | 1792 | 384 | 0.92 | 0.91 | 0.004 |
| 20250611153346-z_dbg_gen_00286 | 256 | 256 | 0.94 | 0.94 | 0.029 |
| 20250611161415-z_dbg_gen_00411 | 384 | 256 | 0.91 | 0.90 | 0.048 |
| 20250611172135-z_dbg_gen_00346 | 896 | 128 | 0.91 | 0.90 | 0.015 |
| 20250611173014-z_dbg_gen_00506 | 2176 | 1920 | 0.91 | 0.91 | 0.000 |
| 20250628074500-500P2_front | 896 | 640 | 0.92 | 0.90 | 0.006 |
| 20250628074500-500P2_front | 3072 | 128 | 0.96 | 0.94 | 0.001 |
| 20250716055235-z_dbg_gen_00779 | 1152 | 2816 | 0.91 | 0.90 | 0.003 |
| 20250825181859--1 | 1024 | 384 | 0.92 | 0.92 | 0.009 |
| 20250825181859--1 | 3200 | 0 | 0.93 | 0.92 | 0.001 |
| 20250825181907-0 | 1024 | 512 | 0.92 | 0.92 | 0.008 |
| 20250825181907-0 | 3200 | 0 | 0.91 | 0.91 | 0.030 |
| 20250825181917--2 | 1152 | 256 | 0.90 | 0.90 | 0.000 |
| 20250825181917--2 | 3328 | 128 | 0.91 | 0.90 | 0.046 |
| 20250825181922-1 | 896 | 384 | 0.90 | 0.90 | 0.010 |
| 20250825181922-1 | 3072 | 0 | 0.90 | 0.90 | 0.014 |
| 20250825181928-2 | 1280 | 256 | 0.90 | 0.90 | 0.000 |
| 20250825181934-3 | 1536 | 256 | 0.91 | 0.91 | 0.000 |
| 20250825181939-4 | 1408 | 256 | 0.91 | 0.91 | 0.003 |

- **Caveats on these windows:**
  - The greedy set is one maximal set, not the maximum one.
  - Coverages sit near the 0.90 floor.
  - The 20250825181859-939 segments ("-2" to "4") are separate units, most likely adjacent layers. The rule allows that: different text.
  - Blank candidates (reference ink < 1 %): **0 of 1,624**. The minimum is 2.26 %, the 5th percentile 3.3 %, and 39 windows are below 3 %.
- **The picker should choose from `candidate_windows.json`,** with conflicts judged by the certification rule; the recorded independent set is one valid choice.

## 5. "Blob field" measured (blob_metrics.json; numbers only)

Binary ink (>= 150) is block-reduced to about 10 um. Medians over maps with >= 1 cm^2 valid area:

| | 0500P2 (33 maps) | 0139 known text, same model (w035 w039 w041 w044) |
|---|---|---|
| ink fraction | 0.072 | 0.101 |
| components per cm^2 | 29.2 | 24.9 |
| component area q50 / q90 (mm^2) | 0.107 / 0.58 | 0.153 / 1.01 |
| ink fraction in components > 10 mm^2 | 0.0 | 0.0 |
| stroke width (um) | 313 | 407 |

There are no merged blobs. The 0500P2 components are about 30-40 % smaller and its strokes about 23 % thinner. That is consistent either with finer script or with fragmented ink. The metrics cannot decide legibility; the sealing REF readers (VOID bar) must.

## 6. Handedness of the candidate windows (window_handedness.json)

- **Source (a): organizer `text_side = -y`** (4.317 um), carried to 9 um as a normal through the organizer affine (det > 0). It gives chirality +1 on 20/20 windows, agreement >= 0.99.
- **Source (b): the window's own normal-line centre.** It is valid (condition <= 10) only on the 2 500P2_front windows, and there it gives -1 at agreement 1.00 and 0.999. It is ill-conditioned elsewhere (condition 10-47, nearly flat fragment); even there the estimate says -1 on 17 of those 18 windows (+1 on 00506 only).
- **So the two sources contradict each other wherever both are valid.** Either the `text_side` field means something other than "direction the inked face points to", or on this fragment the inked face is on the convex side.
- **Decision under the accepted rule: FLAG.** The seal and every read must use both mirror states as separate declared arms (ASK 5).
- **Up/down.** The 4.317 um +z maps to a 9 um direction with z component +0.97, so top-to-bottom = True carries over: image top = low z (MEDIUM, carried).

## 7. Feasible seal size S (estimate only)

- **Formula:** S = N_independent_text_windows x letters per window.
- **Letters per window:** J-seal range 0-7, mean 4.0 on J1-J5. With N = 20: **S of about 40 (2 per window), 80 (4) or 140 (7)**. S >= 30 needs >= 8 windows at 4 letters per window, or >= 15 at 2.
- **Risks that could shrink S after sealing:**
  - (i) Reference legibility is unknown (section 5).
  - (ii) Mirror state is FLAG, so sealers must name letters in the correct state, and a mirrored-state seal counts nothing.
  - (iii) No blank from 0500P2 exists.
  - (iv) Coverages sit at 0.90-0.96.

## 8. Commands

```
python tools/sib/ktlb4p-prep/inventory.py /work/handed/root_metadata.json logs/sib/ktlb4p-prep/inventory.json
python tools/sib/handed/fetch_meshes.py ... (9.362, 2.215 and 4.317 um tifxyz; downloads_meshes.json)
python tools/sib/handed/ct_occupancy.py PHerc0500P2 <v9> logs/sib/ktlb4p-prep/frame_9um.json --dz-max 0 --glob '*9.362um.tifxyz'   (+ --level 2 --dilate 1; + 4.317 um frame)
python tools/sib/ktlb4p-prep/reg/coarse_check.py ; reg/plan_patches.py ; reg/fetch_blocks.py fit ; reg/fit_model.py
python tools/sib/ktlb4p-prep/reg/fetch_blocks.py heldout ; reg/heldout_eval.py
python tools/sib/ktlb4p-prep/reg/plan_new_heldout.py ; reg/select_field.py ; reg/heldout2_eval.py ; reg/posthoc_affine_on_new.py
python tools/sib/ktlb4p-prep/fetch_refmaps.py ; windows.py ; certify.py ; fetch_ref0139.py ; blob_metrics.py ; window_handedness.py
```

## 9. Failures and corrections (plainly)

- **My first window mapper** measured distance to the nearest 2.215 um mesh vertex (20-vox spacing), which undercounted mapping (88-93 %). It was fixed by 5x5 densification (99 %) before any window list was produced.
- **Wait loops using `pgrep -f` or `pkill -f`** matched their own command lines twice. This caused exit-144 notices and no data effect; those tools are now used by PID only.
- **Attempt 1 of the registration failed its pre-registered r bar.** It was recorded as FAIL and pushed. Attempt 2 was pre-registered anew with new patches, exactly as REG-0841-NA did.

## 10. What the orchestrator needs to decide

See ASK.md 1-6. The mirror-state FLAG (ASK 5) and the missing blanks (ASK 6) decide whether L-0500P2 can give S >= 30 with valid controls.

## 11. Geometry package for the 20-window set (window_geometry.json; added 2026-09-26, after the orchestrator's 05:25Z rulings)

No render was read. The package lists, per window K4P-00..K4P-19:
- segment and 9.362 um tifxyz path, with the sha256 of x.tif, y.tif, z.tif and meta.json;
- organizer canvas box (2136 x 2136 px) and grid sub-box;
- 3-D bbox and centre;
- level_mesh angle and spread (0.6-3.2 deg) and z trend per row;
- chirality under the carried text_side and the normal-line-centre record;
- flips for BOTH declared mirror states;
- the mapped box on the 2.215 um reference canvas under the frozen registration (model_final.json sha256 9a777170..., field_final.json sha256 40def3d7...), with mapped fraction 0.981-0.999 and median surface distance.

Orientation:
- **up/down:** image top = low z (carried from 4.317 um, MEDIUM). Rows already run with increasing z in all 20 windows, so `flip_v = False`.
- **state A** (organizer text_side convention): `mirror_u = False` in all 20. The organizer grid as stored is state A.
- **state B:** `mirror_u = True` in all 20.
- Per the orchestrator ruling (ASK 5), any reading of 0500P2 is a declared both-states reading, declared in RULES.md before any render is read.

**Blanks** (ASK 6, orchestrator ruling "follow the proposed default"): the L-0500P2 fold borrows its blank windows from the already-declared blank pool (0139 w053 type). No 0500P2 window is a blank candidate (minimum reference ink 2.26 %), and the blank definition is not relaxed.

## 12. Accepted defaults (orchestrator 05:25Z and 05:58Z, 2026-09-26)

All ASK defaults are accepted as written: items 1-7 here, and handed-2 Q6. In force:
- **Frame gate:** the 5 % zero-CT test is applied per window; whole-mesh numbers are still reported.
- **Registration:** level-1 registration as pre-registered.
- **Up/down:** image top = low z (carried, MEDIUM).
- **Mirror:** FLAG. Any reading of 0500P2 renders requires its OWN RULES.md declaration first, as a both-states (A and B) reading, using `window_geometry.json`.
- **Blanks:** borrowed from the declared 0139 blank pool; no relaxation.
- **Window set:** the 20 windows are an S-feasibility basis, not a selection.
- **S:** a stated estimate (40 / 80 / 140).
- **handed-2 Q6:** no organizer contact; up/down stays unknown where unknown until own traces spanning more than one turn exist.

Nothing further is pending from this session until such a declaration exists.
