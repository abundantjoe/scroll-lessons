Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-red ADDENDUM-1 (orchestrator addendum 18:19Z; RULES.md DECL-P4-12)

Recorded 2026-09-26 before any title-strip number exists; no CT has been read by this sibling.
The detector parameters in params.json are unchanged. Only the priority, the reporting and the flag use change, as the orchestrator directed.

1. Priority: E2 (2.4 um, all 160 strip-a tiles, grid pairs0814b e2/grid.json) is scored before E1. The c10-c17 title zone (DECL-P4-12, p4-research DOSSIER v2) is reported separately from the rest, and rows r0-r1 first (they lie outside the 1.129 um scan).
2. Labelled-adjacency (DECL-P4-12 item 3): this is a model-free channel. The excl flags are reported per tile but do not exclude a tile from hotspot candidacy. This supersedes the "non-labelled-adjacent" clause of params.json "hotspot". The score rule, the threshold rule and the in-sheet rule are unchanged.
3. Detection limit at the 2.4 um voxel: this is required per pigment. The injection-recovery that measures it is still BLOCKED (ASK-1).
   - detlim_model_2p4.json gives only the ANALYTIC prediction from the MEMO section 4 gray model. It is not a measured result and must not be quoted as "ruled out down to X um".
   - Pessimistic calibration, depth PSF sigma 2 voxels:
     - HgS exceeds 233 above about 1.5 um solid-equivalent and saturates above about 1.7 um;
     - PbO exceeds 233 above about 1.1 um and saturates above about 1.3 um.
   - Optimistic calibration: 0.03-0.08 um.
   - Caveat: the 2.4 um scan has its own uint8 mapping, not yet measured. The model reuses the 1.129 um control's gray levels (80/65).
   - The organizers' reported 10-20 um deposits lie far above both predictions. A cinnabar or red-lead layer of that thickness would, by this model, be a saturated surface sheet.
