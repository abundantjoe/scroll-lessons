Provenance: Project HERCULES | owner the owner | [id removed]

# chainvalid-prep: request for GO, and questions (work continues on each default)

0. GO REQUEST. Plan: logs/sib/reg0841/chainvalid_plan.json.
   - It covers the exact area, the crop list, the chain, the metrics and the compute estimate.
   - No 0841 inference has run. The runner refuses to start without /work/cv/GO.
   - Two conditions are open: (a) your GO, and (b) the chain2um GATE-E2E-0139 report.
   - On (b): chain2um has no REPORT.md yet. Its interim 0139 reverse fp32 eval gives AUC 0.47 and r_org_E -0.06 (eval_reverse_fp32.json on its branch), and its forward pass was interrupted by a container restart. The gate is therefore unresolved.
   DEFAULT: wait. Inference starts only after both conditions hold, and then only the 2 primary crops, in both orders.
1. Levelling. Levelling rotates the UV canvas, so pixels would no longer line up with the organizer map and labels.
   DEFAULT: no levelling. Render on the organizer UV grid, as the chain2um GATE-E2E-0139 run did.
   Alternative on request: level, then map the prediction back to the organizer canvas for scoring.
2. Shells. DECL-CHAINVALID names the T, C4 and K shells. I found no C4 or K windows defined on 0841 in RULES.md.
   DEFAULT: only the T shell applies on 0841, enforced as >= 144 vox point-to-surface for every rendered sample (checked fail-closed).
   If C4/K windows exist on 0841, please give their coordinates.
3. Precision.
   DEFAULT: the precision with which the chain2um gate passes. If the gate passes in both, use bf16, which is the official CPU autocast path (infer2um.py --precision bf16).
4. Area.
   - The human labels outside the T shell exist only on 214732: 943,443 px (353,304 ink, 590,139 blank; 0.054 cm^2), within 2 crops (the primary set).
   - w00 and 022814 have no labels there.
   DEFAULT: the bar (AUC and r_org_E) is decided on the pooled primary set E.
   - Also reported, not deciding: r_org_all on the 6 secondary crops (the 2 largest per segment, about 2.9 h of bf16 CPU).
   - All 47 crops would take about 22 h of bf16 CPU; not planned unless you ask.
5. The reference model. The organizer map on 0841 was made by "new_canon_autoresearch_recipe" (20260417190342), which may have been trained on 0841 labels. Per DECL-CHAINVALID that would make this a chain check only.
   DEFAULT: report it as a chain check, with that caveat stated.

## Update 2026-09-26 (orchestrator resume 00:36Z): items answered on the STRICTER default, pending the full rulings
0. GO: no ink map of PHerc0841 of any kind until the declaration (DECL-CHAINVALID-A1 or its revision) is appended and GO is given. The runner refuses without /work/cv/GO. No 0841 inference has run.
1. Levelling: LEVELLED, as the task specified. Plan v2 renders the levelled mapped meshes and scores on the organizer canvas through the exact levelled <-> organizer correspondence.
   Verified on the real meshes: median 3-D disagreement 0.023 rescan vox (p99 1.2), pixel round trip 1e-11 (level_check.json).
2. Shells: only the T shell exists on 0841. In RULES.md, C4 refers to the 0139/0814 clean controls and K to fold K; neither has windows on 0841.
   Every rendered sample of the levelled meshes is >= 144 vox point-to-surface from J, checked fail-closed (minimum 144.29; clearance_check_lev.json).
3. Precision: only a precision with which the chain2um GATE-E2E-0139 passes. If it passes in neither, there is no 0841 run.
4. Area: the bar is decided on the pooled primary E only: 922,836 labelled px (340,876 ink) on 214732, all mapped into 2 levelled crops. The secondary crops report r_org_all only, never deciding.
5. Reference model: the result is recorded as a chain check only, because the organizer map model may have seen 0841 labels.
