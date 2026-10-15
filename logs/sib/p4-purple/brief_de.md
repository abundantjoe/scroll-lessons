Provenance: Project HERCULES | owner the owner | [id removed]

# Brief p4-purple-de: DECL-P4-16 item 3, 78/137 keV dual-energy feasibility (numbers only)

Branch: claude/gifted-bell-gavnl5-sib-p4-purple-de (from origin/claude/gifted-bell-gavnl5-sib-p4-purple). Files: logs/sib/p4-purple/de/, tools/sib/p4-purple/de/. Follow logs/sib/p4-purple/brief_common.md.

## HARD FENCE (read twice)
NEVER compute, read or sample any 137 keV value, and never compute any dual-energy number, anywhere inside w010-027 canvas columns c9-c19 (any row), before the orchestrator has recorded the METRIC-HASH of your DUAL_FREEZE.md in RULES.md on origin/claude/gifted-bell-gavnl5. For w010-027 you compute GEOMETRY ONLY (mesh vertices vs the 137 keV array extent), for the whole strip, and you never fetch a 137 keV chunk for it. All method design, fitting and validation use the control strip 20260701183125-w028-037 only. Stop after the freeze.

## 1. Inventory (inventory.json)
For 20260323153942-2.400um-0.2m-137keV-masked and, for comparison, 20260411134726-2.400um-0.2m-78keV-masked (PHercParis4/volumes/<v>.zarr): metadata.json fields (voxel size, energy, propagation distance, detector, date, reconstruction: phase retrieval method and delta/beta, filters, ring correction, grey scaling/dtype, masking), shape and chunking of every level, transform.json, and sha256 of every fetched file. Note anything missing as "not published".

## 2. Overlap (overlap.json)
- w010-027: per E2 tile (grid as tools/sib/p4-highz/kedge_cov.py), fraction of valid mesh vertices inside the 137 keV level-0 extent after the composed affine. Geometry only. Compare with p4-highz (14-27 % of r3_c10-c17) and explain any difference.
- w028-037 control: the same per C2 tile (grid logs/sib/p4-tiles-b/grid.json on origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b), plus the fraction of those vertices with non-zero (unmasked) 137 keV data (sampled, >= 1000 points per covered tile or all if fewer).

## 3. Registration (control only)
Start from the composed published affine (scans.json). Refine locally with 3-D block matching between the 78 keV 2.4 um volume (the mesh frame) and the 137 keV volume: blocks of about 128^3 voxels centred on control mesh vertices inside the non-zero 137 keV region; normalised cross-correlation or phase correlation; fit a smooth model (translation field or local affine; declare which in PROTOCOL.md). Split blocks spatially into fit and held-out sets. Residual, on held-out blocks, measured on sheet surfaces: the difference in papyrus/void boundary position along the mesh normal between the two registered volumes (median, p90). Goal < 5 um; report the value whatever it is.

## 4. Two-material decomposition
- Grey to mu calibration per scan: state the model (e.g. linear through the void and papyrus modes of control voxels) and its assumptions (unknown papyrus density cancels in the energy ratio).
- Basis: photoelectric-like and Compton-like, or directly the ratio R = mu137/mu78; use the colourant predictions in logs/sib/p4-purple/colourants.json on origin/claude/gifted-bell-gavnl5-sib-p4-purple (pushed by the parent; wait for it or compute the same from xraylib 4.3.0 and cite). Note: Au/Hg/Pb K-edges (80.7/83.1/88.0 keV) lie between 78 and 137 keV; Br (13.5), Ca (4.0), As (11.9), Cu, Fe edges lie below both.
- Detector statistic, frozen before validation: e.g. per 0.2 x 0.2 mm surface patch, the mean of the high-Z estimate over the +-15 um slab about the mesh (and at d* if p4-depth or p4-tiles-b has frozen one; cite the file and commit).

## 5. Validation (control only)
- (a) Known-text carbon ink vs blank papyrus (ink = official 2.4 um prediction of w028-037 >= its p90, background <= p50, 50 um boundary exclusion; the DECL-P4-9 recipe): expected no composition difference; report the AUC and CI.
- (b) Synthetic injection into both registered volumes, with each energy's own mu from colourants.json and the same blur: Tyrian purple (0/50/90 % Br loss), purpurissum (dye on CaCO3), alumina and gypsum lakes, orpiment, lead white, cinnabar, gold, CuO, Fe2O3, carbon ink; 5, 10, 20 um layers; letter-shaped strokes 0.4 mm wide; >= 20 control locations. Report sensitivity (recovery >= 0.8) per class and thickness, and the false-positive rate.
- (c) Nulls: rot-90 copies, and a deliberately misregistered pairing (shift >= 200 um): the statistic must be at chance.
- Report the registration residual's effect: repeat (b) with the residual added as a random shift.

## 6. Freeze
Write logs/sib/p4-purple/de/DUAL_FREEZE.md: inventory summary, registration method and every parameter, decomposition, statistic, thresholds (hotspot rule: e.g. patch statistic above the control+null p99 and on-sheet), the control results of section 5, and the sha256 of every tool file. Push it and stop. The parent copies it to logs/sib/p4-purple/DUAL_FREEZE.md for the orchestrator's METRIC-HASH. No title-zone number, ever, in this task.
