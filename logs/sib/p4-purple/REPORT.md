Provenance: Project HERCULES | owner the owner | [id removed]
# p4-purple REPORT: DECL-P4-16 items 1, 3, 4 (numbers only; no image, tile or CT pixel viewed by p4-purple or its sub-siblings)
1. Physics (item 1; colourants.json, COLOURANTS.md, 143e1e6). xraylib 4.3.0; 25 colourants x 5/10/20 um; mu at 78 and 137 keV, delta; papyrus 0.3-1.0 g/cm3.
   - Recon metadata: 78 keV Paganin delta/beta 1000 + unsharp 4; 137 keV 2000 + unsharp 5. Grey calibration implies papyrus 0.43 g/cm3.
   - Noise sigma 29.2 grey (p4-highz C2 p50/p99, not re-measured).
   - In the published Paganin volume, thin deposits are seen by electron density: purple, lake and organic inks give 0.9-1.4x carbon ink of equal thickness.
     Colour is invisible; a deposit is not. Absorption-only: intact Tyrian purple 2.9x carbon ink.
   - Absolute CNRs are upper bounds: a 5 um carbon layer should saturate, yet only 0.064 % of control slab maxima do (d* pending).
2. Dual energy (item 3; sub-sibling de, DUAL_FREEZE.md 6d12337, copied verbatim to logs/sib/p4-purple/DUAL_FREEZE.md, sha256 93d04a4d...9427).
   - Overlap: w010-027 geometry only, 3.01 % of vertices, r3_c10-c17 14-27 %; control 4.40 % (rows r3-r4).
   - Registration (control): residual median 1.7 um, p90 3.2 um. Sheet-surface median 2.4 um; p90 18 um.
   - The 137 keV unit calibration fails, so the empirical papyrus line (k 0.679) is used. Statistic: depth-column residual z per 0.2 mm patch; hotspot |z| > 3.07, on-sheet.
   - Control: carbon ink AUC 0.48 [0.33, 0.63]; rot-90 null 0.48; FPR 0.022/patch; 250 um misregistration gives FPR 0.118.
   - Injection: CuO, orpiment and gold detected at 10-20 um. Tyrian purple (any Br loss), purpurissum, lakes, carbon ink, Fe2O3, Pb/Hg: NOT detected at <= 20 um.
   - No 137 keV or dual-energy number exists in w010-027. The orchestrator must hash DUAL_FREEZE.md before any title-zone use.
3. Morphology (item 4; sub-sibling mo, gate.json 161da9d, REPORT 5d805a0): GATE FAIL, 0/9 tests.
   - Best: F5+ crackle at the + face, AUC 0.656 [0.636, 0.675]. Relief and thickness: 0.48-0.53. Nulls 0.47-0.53.
   - Positive control: a 10 um deposit is measured at 6-7 um, but its glyph AUC is only 0.60.
   - Labels are the official prediction (no human labels on w028-037).
4. Register (REGISTER_ADD.md): I3a/I3b (purple) are testable only as a deposit via L3 at d*; composition is untestable in published scans.
   - I6 (dye wash, no deposit): untestable with published data. I7: heavy pigment off-mesh, via DECL-P4-6-A3.
Answer to the owner: a purple title that left a deposit is as visible as the black body text in the 2.4 um Paganin scan, but cannot be told apart from it.
   - The best test is the colour-agnostic deposit channel at the calibrated ink depth (L3 / P4-W).
   - A dye that soaked in without thickness cannot be seen in any published scan; it needs XRF or hyperspectral imaging (organizers only).
Sub-siblings: de session_011VjFd3F6ozjCmeTsQp9osM, mo session_01QUid9UJ6DPeNJ8uFaN9YPd (SUBSIBS.md, recorded before start). Both stopped at usage limits and were resumed.
Integrity: no issues
