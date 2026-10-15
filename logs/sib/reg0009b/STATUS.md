Provenance: Project HERCULES | owner the owner | [id removed]

# reg0009b status (sibling builder)

Updated 2026-09-26 ~05:35Z.

- DONE (commit efb6d19): inventory; registration, 18/18 pass after depth correction; fail-closed re-trace grouping, 28 SAME of 119 pairs, 6 units; 23 deduplicated candidate windows; REPORT.md; summary.json; proposal.
- Registry v3 same-papyrus (DECL-DEVLOOP-A1 item 1) is the union of the vertex, point-to-surface and normal-distance forms. All three are already computed in overlap_frame9.json. Union = 28 SAME pairs: vertex form 0, surface form 28, normal form 28, and the pair sets are identical. Units are unchanged.
- DONE: devzone.py, numbers only. It measures the 0009B area and the 2 x 2 cm windows / 1 x 1 cm blanks outside every KTLB-M candidate window + 144 vox, as preparation for the 0009B DEV registry extension (DECL-DEVLOOP-A1 item 7). Result: strict reading = 0 inked 2 x 2 cm DEV windows (99.4 / 34.1 cm^2 allowed, 5 / 0 blanks). Decision needed -> ASK.md. The extension itself is the orchestrator's to declare.
- Open decisions: see REPORT.md, "What the orchestrator needs to declare next".
- 2026-09-26 06:15Z: the orchestrator ruled 05:59Z (native 2.401 um vox, point-to-surface; ASK resolved). The devzone rerun reproduces the earlier numbers. Registry-extension proposal pushed: proposals/DECL-DEVLOOP-0009B-EXT-proposal.md (+ devreg_0009b_extension.json).
  - PRIMARY (all 76 dense candidates excluded): 1 x 2 cm window (ink150 0.013, no text) + 6 blanks, minimum clearance 187 2.4-um vox (>= 173 required).
  - ALTERNATIVE (23-window pool): 4 windows (none with ink150 >= 0.05) + 7 blanks.
  - 0009B supplies no text DEV window. It awaits the orchestrator's record; no map has been made.
