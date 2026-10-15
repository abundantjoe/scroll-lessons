Provenance: Project HERCULES | owner the owner | [id removed]
# p4-purple-de REPORT: 78/137 keV dual-energy feasibility (DECL-P4-16 item 3), control only
Frozen method and every number: DUAL_FREEZE.md (commit 6d12337). Pre-registration: PROTOCOL.md (A, A-1, B, B-1). No image viewed.
1. Inventory: both 2.4 um volumes are Paganin (delta/beta 1000 / 2000) + unsharp; polychromatic beam; float units unpublished.
   Physics consequence: voxel ratios carry no composition; only depth columns (+-60 um, 7 Paganin lengths) are used.
2. Overlap: w010-027 (geometry only, no 137 keV byte fetched) 3.01 % of vertices inside the 137 keV extent, identical per tile
   to p4-highz (r3_c10-c17 14-27 %). Control w028-037 4.40 % (1.29 M vertices), rows r3-r4.
3. Registration (control): published affine off by 7.8 um (median); affine correction -> held-out blocks 1.7 um median,
   3.2 um p90; sheet-surface residual 2.4 um median (goal < 5 um met), 18 um p90 (heavy tail).
4. Calibration FAILS the unit checks: 137 keV void 0.044, gain ~0.63 vs 78 keV; decomposition uses the empirical papyrus line
   (k 0.679), so it does not need units. Statistic: patch (0.2 mm) column residual Z, hotspot |z| > 3.07 and on-sheet.
5. Validation (40 held-out sites): known-text carbon ink AUC 0.48 [0.33, 0.63] (no composition difference, as expected);
   rot-90 null 0.48 (chance); false-positive rate 0.022/patch (nominal 0.01); misregistered 250 um: FPR 0.118 (registration needed).
6. Injection (480 patches per cell; worse of Paganin and 137-gain-corrected models):
   detectable >= 0.8: CuO, orpiment, gold at 10-20 um.
   NOT detectable at <= 20 um: Tyrian purple (0/50/90 % Br loss; best 0.24-0.29 at 20 um, 0 % loss), purpurissum (0.00),
   alumina and gypsum lakes, carbon ink, Fe2O3 (0.76 at 20 um), cinnabar and lead white (0.39-0.50 at 20 um in the
   primary model; heavy pigments saturate the 8-bit windows; the p4-highz density screen already covers them).
7. Verdict: the 137 keV dual-energy route cannot detect a purple (Br or Ca-lake) title in these published scans at
   realistic paint thicknesses; for purple it is "untestable with published data", never "absent". It adds sensitivity only
   for As and Cu pigments. Any title-zone use must apply DUAL_FREEZE.md unchanged, after the orchestrator's METRIC-HASH.
Disclosures: metadata files were fetched before PROTOCOL A (no voxel); the bbox fence refused every read and was replaced
before any 137 keV byte (A-1); B-1 added after fit.json, before validation; one validation run was killed by a container
restart and rerun unchanged; a JSON-serialisation crash in the fit step was fixed and rerun (deterministic).
Commit of the frozen method: 6d12337.
Integrity: no issues
