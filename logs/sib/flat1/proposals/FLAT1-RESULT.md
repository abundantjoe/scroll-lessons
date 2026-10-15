Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal: FLAT-1 result record (for the orchestrator; not a declaration)

1. FLAT-1 (DECL-FACTORY) primary set: 5 seeded PHerc0139 4.00 cm^2 rectangles on the 9.362 um organizer meshes. By the pre-declared rule, vc_flatten (ABF++) is adopted: 5/5 >= 93.1 % (98.59 to 99.67). SLIM passes 5/5 (99.59 to 100), ARAP 5/5, the grid baseline 97.39 to 99.55. Evidence: logs/sib/flat1/flat1_summary.json.
2. Limitation to record: the primary set does not discriminate (the grid baseline passes). On the hard set (most curved / least isometric bank windows) vc_flatten passes 0/10, SLIM 3/10, ARAP 4/10. The official ABF++ collapsed in 3 of 33 runs (27.9 %, 22.2 %, 33.9 %; flips). The fallback trim changed no verdict (max +-1 point).
3. Proposed amendment to SG item 10: "R's own flattening" = libigl SLIM (symmetric Dirichlet, start from the levelled grid, free boundary, stop at relative energy decrease <= 1e-7 per 5 iterations), code tools/sib/flat1/flatlib.py. vc_flatten is reported alongside it. Reason: SLIM >= vc_flatten in 33/33 measured cases, 0 flips, no collapse, and it is insensitive to the start (<= 0.011 points).
4. Record: eligible organizer meshes (PHerc0800, PHerc1447) have no fully valid 4 cm^2 window; the 1 cm^2 windows score 100 % for all methods.
