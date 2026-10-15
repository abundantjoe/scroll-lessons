Provenance: Project HERCULES | owner the owner | [id removed]

# p4-depth ASK (non-blocking)

1. DECL-P4-12-A3 item 1 says "compute the same on the control's rot-90 copies ... and on its gap depths". "Gap depths" is not defined.
   Interpretation used (frozen in calib_params.json before any number): offsets outside the papyrus sheet = slices whose pooled median voxel
   value at mesh-valid px is < T_mid (93). f(o) there is reported as an off-sheet reference only; it does not enter the PASS/STOP verdict.
   If the orchestrator meant something else, say so and it will be recomputed from the stored per-slice histograms (no new reads needed).

2. BLOCKING for interpretation (not for computation): the declared DECL-P4-12-A3 peak rule fails the task's "no layer -> STOP"
   unit test on realistic synthetic sheets (tools/sib/p4-depth/test_depth.py, unit_tests.json):
   - b2: a papyrus body (+-50 um) between darker gaps with NO ink layer gives PASS on 10/10 seeds (z 5.2-7.7, d* anywhere
     in the body). The median over all 109 offsets is set by the gap slices, so the sheet body itself is a "peak".
     On real data T_hi is the 99.9 % of the +-14.4 um mesh slab, so f(o) is ~1e-3 in the sheet and near 0 in gaps by
     construction: the literal rule is expected to PASS on the sheet whether or not ink exists.
   - b1: a uniform noisy sheet (no structure at all) gives PASS on 25/100 seeds: the MAXIMUM of 109 offsets is compared
     with a single 3-robust-SD bar (family-wise error; scale-invariant, so more voxels do not fix it).
   - b0 (noise-free uniform) gives STOP, and the positive test passes (a bright 15 um layer with a 2.4 um PSF: d* within
     2.4 um of truth in 21/21 cases; without PSF, a flat-topped layer, the argmax error reaches 7.2 um, reported).
   I have NOT changed the rule. calib.json will carry the literal verdict plus these diagnostics. Candidate amendments
   for the orchestrator to declare (or not), all computable from the stored per-slice histograms with no new reads:
   (i) baseline = median/MAD over ON-SHEET offsets only (pooled median voxel >= T_mid), peak required to exceed it;
   (ii) family-wise bar: z >= 3 after Bonferroni over 109 offsets (z >= ~3.9), or a tile-bootstrap null;
   (iii) per-tile consistency: the pooled d* is the per-tile argmax (+-5 um) in >= 50 % of the 24 tiles;
   (iv) shape: peak FWHM <= 25 um (a 10-20 um deposit), clearly narrower than the sheet body.
   Question: does a literal PASS authorise the L3 build, or must an amended specificity rule pass first?
   Default if no answer: build L3 on a literal PASS (tiles are a display; the DECL-P4-12 item 2 known-text gate on
   w010-027 c0-c8 remains the binding test of informativeness), with every manifest carrying "calibration_specificity":
   "FAILED unit test b1/b2 under the declared rule".

3. Update after the run: the verdict is STOP (z 1.94).
   - Item 2's question is moot for this run.
   - Item 1's gap rule marks all 109 slices as gap (median < 93 everywhere), so it is uninformative.
   - No action is needed unless an amendment is declared.
