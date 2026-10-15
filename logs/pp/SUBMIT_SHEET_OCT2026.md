# Progress Prize submission sheet (October 2026 round)
Provenance: Project HERCULES | [id removed]

**Form:** the current month's Progress Prizes form, linked from https://scrollprize.org/prizes (the September form, https://docs.google.com/forms/d/e/1FAIpQLScNBMj25FMnphngRG1Ciryv_2_Mkdq2YPJOD9WqPfZExII2iQ/viewform, closed 2026-10-01 06:59Z; if the same form is reused for October it is fine to use). One form per tool; not the Grand Prize, First Letters or Title forms.

| Tool | Public repo (owner creates, empty, public) | Status |
|---|---|---|
| xsec | https://github.com/abundantjoe/xsec | READY (public, main 87850267b9dd; fresh clone 3/3 tests; reproduce.sh verified against the public bucket; figures embedded; tifxyz included; pyproject; 3/3 tests; citation, MIT, data licence, AI line verified; no leaks) |
| ringstrip | https://github.com/abundantjoe/ringstrip | READY (public, main d56b90a5c1db; fresh clone 2/2 tests; reproduce.sh verified; 5 patches included; figure embedded; pyproject; 2/2 tests; same checks) |
| orgseg-ink | https://github.com/abundantjoe/orgsec-ink | READY (public, main aa903cea9d5c; fresh clone 3/3 tests; reproduce_tests.sh verified; all 26 sheet maps included at half resolution; figure embedded; pyproject; 3/3 tests; same checks; repo name as created by the owner) |

**Fields, the same for all three:**
- Email / full name / Discord: yours.
- Team description: `Individual. Built with the help of AI coding agents (Claude Code); all code, tests and numbers are in the linked repository.`
- URL: the repo link above.
- What is your contribution?: the text below, pasted as-is.
- Terms and Conditions: "Yes, I agree".

---
## 1. xsec: contribution text
xsec shows, in one picture, whether an auto-grown tifxyz surface really follows one papyrus sheet. It draws the surface on raw CT slices at several heights, and it documents the failure the usual numeric check cannot see.

(1) Scroll data: public PHerc0268 (volume 20251110183117, 8.64 µm, 116 keV) from the open-data bucket, with surfaces grown by the organizers' vc_grow_seg_from_seed and the organizers' published normal grids (Vesuvius Challenge - CT Scans of Herculaneum Papyri, Angelotti et al.).

(2) Every render and every ink map inherits the surface under it. If the surface steps from one winding to the next, the render is a collage of sheets and the ink map on it means nothing. The common gate (median |cos| between the surface normal and the radial direction) cannot catch this: a jumped surface still faces outward. xsec gives a person the cross-section instead: four raw-CT slices through the surface's height range with the surface drawn in colour, from a local zarr or straight from s3://, plus the radial gate for comparison and synthetic surfaces with known geometry.

(3) Results on real data: a 2 × 2 cm PHerc0268 patch grown with normal grids scored median |cos| 0.928, 75 % of normals above 0.8 and 0.90 mm per cm radial spread (it passed every numeric bar), yet the cross-section shows it holding one layer between cracks and jumping to the neighbouring layer at every crack. The same seed grown without normal grids cuts straight across windings (both images in results/). An automated "fraction of surface points on predicted papyrus" check did not separate good from jumped surfaces on this crushed scroll (0.676 vs 0.676 vs 0.628 for a cross-winding surface); it is included so nobody repeats it. Five more patches at 70 % radius show fibres radiating from the seed in their centre layers, the signature of a surface that is not flat on a sheet.

(4) Evidence: scripts/reproduce.sh regenerates the real figure from the public bucket in about two minutes (the grown surface is included); 3 tests on synthetic cylinders and shells (the radial gate passes both an on-sheet and a layer-jumping patch; the cross-section tool reads a known on-bright fraction of 1.0 vs ~0.5); the real images with segment seed coordinates and volume IDs; a CLI and a Python API. Code MIT; results CC BY-NC 4.0.
---
## 2. ringstrip: contribution text
ringstrip turns many small grown patches of one winding into one continuous strip, so ink maps computed patch by patch can be read as a sheet. It also stitches overlapping tiles of a flat grid with feathered seams.

(1) Scroll data: public PHerc0268 (volume 20251110183117, 8.64 µm, 116 keV); patches grown with the organizers' volume-cartographer; ink maps from the organizers' public ink_9um model (Vesuvius Challenge - CT Scans of Herculaneum Papyri, Angelotti et al.).

(2) CPU pipelines grow 2 × 2 cm patches because that is what finishes in minutes; readers need centimetres of continuous text. ringstrip places every pixel of every patch's map at its true position on the unrolled winding (azimuth about the scroll axis × a reference radius, and height), averaging overlaps and closing small holes, with a JSON of the cut azimuth, offsets and coverage. Patches from different grows, even different machines and sessions, merge into the same strip; new patches extend it.

(3) On real data it unrolled five patches of PHerc0268 (band r/R = 0.70, mid-height) into one 10,513 × 2,507 px strip (results/). The ink map on that strip is uniform speckle, which is a statement about the surfaces and the models, not about the tool; the companion package xsec shows why.

(4) Evidence: scripts/reproduce.sh rebuilds the real strip from the five included patches; 2 tests on synthetic cylinder patches (a bright line at one height stays continuous across the seam of two overlapping patches, > 90 % of its length; three overlapping tiles of a gradient reassemble to within 2 grey levels); CLI and Python API. Code MIT; results CC BY-NC 4.0.
---
## 3. orgseg-ink: contribution text
orgseg-ink runs the two public Herculaneum ink models on segments the organizers already published, straight from the open-data bucket on CPU, tests what their maps mean, and reports the result honestly: on 26 organizer sheets of two eligible scrolls, nothing.

(1) Scroll data: PHerc0800 (volume 20250521135224, 8.64 µm, 116 keV; 6 organizer auto-grown segments with published surface volumes), PHerc1203 (volume 20250820131727, 9.362 µm, 113 keV, the ink_9um model's native scan; 20 organizer auto-grown tifxyz segments, rendered here), PHerc0139 organizer segments for the known-text calibration, PHerc0268 for a junk calibration (Vesuvius Challenge - CT Scans of Herculaneum Papyri, Angelotti et al.).

(2) It gives a reproducible, scripted path from a segment ID to ink maps from both the organizers' ink_9um checkpoint (both layer orders) and the 2023 Grand Prize TimeSformer (Youssef Nader; organizer-hosted weights and villa inference code), 5-15 minutes per segment on 4 CPUs; an agreement test (Pearson r of 0.5 mm-smoothed maps against rotated and flipped controls) for whether two models mark the same places; a row-periodicity score; and a piece map that splits a render at dark seams.

(3) Results: across the 26 sheets (1.7-4.1 cm wide), the fraction of each ink_9um map above 0.5 is 0.018-0.060 (PHerc0800) and 0.012-0.158 (PHerc1203), no pixel above 0.90, blobs of 1-3 mm with no row alignment, forward and reverse unrelated. The two models do not agree with each other on the same sheets (r = 0.13 vs control 0.10 on PHerc0800; PHerc1203 values in results/). The row-periodicity score, calibrated on 112 known-text tiles of PHerc0139 against 144 cross-winding junk tiles, is NOT a text detector: only 1.8 % of text tiles beat the junk 99th percentile; fibre and crush periodicity score as high as text. We report the nulls because nobody should read a null from these models on a new scroll as blank papyrus, and because the next entrant should start where this stopped.

(4) Evidence: all 26 sheet maps (both layer orders) and the two Grand Prize maps are included at half resolution, and scripts/reproduce_tests.sh re-runs the agreement and row-score tests on them without any model; 3 synthetic tests (identical maps score r = 1 and independent noise ~0 with matching controls; periodic 5 mm rows beat noise by > 5× with the pitch recovered; a dark seam splits a render into 2 pieces); the per-segment CSV with organizer segment IDs, sizes and statistics; the calibration JSON; montages of all sheets. Code MIT; results CC BY-NC 4.0.
