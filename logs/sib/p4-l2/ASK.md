Provenance: Project HERCULES | owner the owner | [id removed]

# p4-l2 ASK (not blocking; both L4 faces already FAIL on sensitivity)
1. DECL-P4-18 item 3 rot-90 specificity: the detector's cell statistic (fraction of in-cell px > T_d) is invariant when a tile is rotated together with its 4 x 4 cell lattice. The rot-90 flagged rate therefore equals the flagged rate over all control cells, text included, so a detector with high text recall must fail it. Should a future channel's rot-90 null use a statistic that is not rotation-invariant (e.g. row-direction anisotropy), or be dropped for this detector?
2. The synthetic no-ink sheets (i.i.d. voxels from empirical class histograms) are far noisier in the 11-slice max than real papyrus, so they flag 100 %. A spatially correlated generator (e.g. real control air/interior patches reshuffled in blocks) would be needed for a meaningful synthetic-specificity bar.
