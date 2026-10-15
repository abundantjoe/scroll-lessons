Settled decisions, section 6.0, adopted verbatim as project rules:
1. Chance correction: every readout scored as C_net (5000-permutation identity null), p_max over the decision's best arm (max-T over arms with a shared permutation index); CHANCE arm and blanks read in the same run; each window's prize proximity (net count versus 10) reported. Archive PASS-A dropped.
2. All training starts from base ink_9um hybrid_3d2d seed42 step-075000. The V-lineage is not rebuilt. No MEM arms.
3. Known-text pool: 0139 minus clean controls (w024, w047, w053, title region) and their 3-D neighbours (w025, w048, w052 and any found by the KD-tree tool) -> training; 0814 -> training; 0500P2 and 0332 -> held-out JULY scrolls only if their protocol matches field by field, else training only; 0009B -> never trained on (MAY benchmark KTLB-M); 1451 -> MAY candidate via own traces; 0343P -> benchmark only, never trained on. Hecate and ink_canonical_2um weights never initialise a 9 um model evaluated on 0841.
4. Cross-pair rescan use only: 1203 labels may train a reader that never reads 1203, and vice versa (same for 0846A). Windows found with 2.4 um help are benchmarks only; submission regions stay >= 128 vox from them. RESCAN-LOOP is forbidden.
5. Pseudo-labels only after D4 passes. Bulk eligible reading only with a USABLE arm, or for presence with a* measured and TRIBUNAL live. Renders cached regardless.
6. PY-GATE superseded by in-code gated tracer builds (section 5.1). 0343P is benchmark-only by this decision (not an archive fact).
7. Priority proof: form timestamp, sha256 manifest, signed commits.
8. Half-pitch for controls: measured by code per region (median distance to the nearest neighbouring m7 sheet along the local normal); never hard-coded.
