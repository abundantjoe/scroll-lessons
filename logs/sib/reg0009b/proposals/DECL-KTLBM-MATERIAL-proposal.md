Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal (for the orchestrator; not a declaration): KTLB-M material on PHerc0009B

1. Registration: for each of the 18 PHerc0009B segments, the 2.401 um reference/label canvas maps to the 8.640 um canvas by c9 = (c2 + 10) * N9 / N2 - 10 + d_seg, with d_seg the depth-corrected CT-NCC shift in logs/sib/reg0009b/summary.json (registration.<seg>.shift_depth_corrected). Gate as measured: whole-segment NCC >= 0.80 and median tile residual <= 2 px; 18/18 pass (minimum 0.802, 131642). Optional stricter step before sealing: a held-out-depth recheck of any segment carrying a sealed window.
2. Papyrus units: the CORR-RETRACE-RULE fail-closed grouping (U01-U06), with 172639 and 200236 treated as U01 for every exclusion and FL-09 purpose (sensitivity S01; 5 offset-field pairs).
3. Candidate pool: the 23 windows of windows_dedupe.json (tol 10), with their 2.401 um canvas boxes. The picker chooses from 2.4 um reference displays only; >= 5 nameable letters per window; the seal precedes any 9 um map of those windows. Windows 2 and 16 (partly inside official supervision on 125754) are admitted or excluded by explicit decision.
4. No bar changes are implied.
