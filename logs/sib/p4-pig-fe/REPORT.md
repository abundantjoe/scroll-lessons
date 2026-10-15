Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-fe REPORT: FE family (red/yellow ochre, green earth); DECL-P4-10 steps 1-4, DECL-P4-12 addendum

Numbers only. No image, tile or CT pixel was opened, viewed or described.
- Memo: MEMO.md (d8f8acf).
- Detector: frozen in params.json (4a927a1, sha256 b9eeda42...) before any title-strip number.
- Outputs: scores.json, hotspots.json, summary.json, 1129/* (C, E1) and 24/* (C2, E2; sub-sibling p4-pig-fe-e2, with no
  code or parameter change).

## Verdict

**The FE detector is INSENSITIVE at the plausible ochre-ink thickness (5-10 um) in the conservative regime. It is
insensitive at every thickness up to 20 um in the electron-density regimes, on all four materials. The detector
limit is not the same as absence.**

In the optimistic mu regime (hematite attenuation), the detector detects ochre letters **>= 20 um** thick reliably
at both voxel sizes, and letters **~10 um** thick only partly.

The title strips show nothing beyond what the carbon-ink control produces. One E1 tile and one E2 tile exceed theta,
both marginally, as the ~1 % null rate predicts. Both are labelled-adjacent.

## Why (physics, MEMO.md; calibration calib_control.json)
- The papyrus-minus-gap contrast is only 15.0 (1.129 um) and 12.4 (2.4 um L1) grey levels in the control depth
  profiles. The voxel noise sd is 36-43. A full voxel of standard ochre ink is therefore expected at:
  - about +52 over papyrus in the electron-density regime (x4.5);
  - about +148 over papyrus in the mu regime (x10.9).
- Natural surface structure (papyrus relief, misregistration, grains) already gives stroke-shaped matched-filter
  responses of about 9 sigma (median control tile) to 14-16 sigma (max).
- A 5-10 um electron-density-regime layer adds < 0.5 sigma (median dz below), so it disappears under that structure.
- Ochre, Vesuvius glass (x4.7-6.5) and Ti-magnetite (x9.6-31) cannot be told apart per voxel at 78 keV, and Fe has
  no K-edge between 60 and 100 keV. Only morphology separates them.

## Control, nulls, thresholds (per family)
| | 1.129 um (C -> E1) | 2.4 um L1 (C2 -> E2) |
|---|---|---|
| control tiles | 63 | 188 |
| sigma0 (1.4826 MAD of r) | 2.933 | 2.220 |
| theta = p99(control z U rot-90 z) | 14.016 | 13.844 |
| control z median / max | 8.66 / 14.23 | 9.27 / 16.16 |
| control FP, leave-one-out theta | 1/63 (0.016) | 2/188 (0.011) |
| rot-90 null: max abs z difference | 0.0 | 0.0 |
| injection-window baseline FP (control / title) | 0/12 / 0/12 | 0/12 / 0/12 |

Rot-90 disclosure: the 4-orientation kernel set is closed under 90 degree rotation, so the rot-90 null reproduces z
exactly. It is an implementation check, not an independent null. Theta is effectively the p99 of the control tiles
(noted in params.json and by the sub-sibling).

## Injection-recovery (Greek capitals 2-4 mm, stroke 0.3-0.6 mm, 12 locations per material)
Sensitivity = planted-letter window z > theta. In brackets: also f_in >= 0.8. The lean regime (x3.1) gave 0/12 at
every thickness on every material (median dz < 0.05). The last number in each cell is the median dz.

| regime, t | C (1.129) | E1 (1.129, title) | C2 (2.4) | E2 (2.4, title) |
|---|---|---|---|---|
| rho_e x4.5, 2 um | 0/12 | 0/12 | 0/12 | 0/12 |
| rho_e x4.5, 5 um | 0/12 (+0.01) | 0/12 (+0.03) | 0/12 (+0.03) | 0/12 (-0.01) |
| rho_e x4.5, 10 um | 0/12 (+0.04) | 0/12 (+0.10) | 0/12 (+0.37) | 0/12 (+0.51) |
| rho_e x4.5, 20 um | 0/12 (+2.6) | 0/12 (+3.5) | 0/12 (+4.7) | 0/12 (+4.3) |
| mu x10.9, 2 um | 0/12 | 0/12 | 0/12 | 0/12 |
| mu x10.9, 5 um | 0/12 (+1.6) | 0/12 (+1.6) | 0/12 (+2.2) | 0/12 (+2.7) |
| mu x10.9, 10 um | 4/12 [2] (+7.0) | 6/12 [1] (+9.2) | **12/12** [7] (+10.6) | 9/12 [2] (+10.8) |
| mu x10.9, 20 um | **12/12** [11] | **12/12** [12] | **12/12** [12] | **12/12** [10] |

Detection limit (smallest thickness with sensitivity >= 0.8):
- rho_e regimes: none <= 20 um, on all materials.
- mu regime: **20 um** on C, E1 and E2; **10 um** on C2.
- **At the 2.4 um voxel (addendum item 3): 20 um on the title strip E2 (10 um reaches 0.75) and 10 um on the
  control C2**, for standard ochre in the mu regime only.

The f_in >= 0.8 in-sheet requirement cuts the 10 um recoveries roughly in half. This is expected: the S/D split
blurs for a thin layer near the band edge.

## Title-strip scores (scores.json; hotspots.json)
- E1: 60 tiles; median z 9.04, max 14.63 (r4_c16, f_in 0.84, labelled-adjacent, excl_d_a). 1 tile above theta.
  - That z exceeds all 63 control tiles (empirical per-tile p ~ 1/64).
  - With 60 tiles tested, the expected number of null exceedances is ~0.9, so the result is not significant.
- E2 (all 160 strip-a tiles, priority per addendum): median z 9.11, max 14.04 (r5_c16, f_in 0.875, labelled-adjacent).
  1 tile above theta. 3 of 188 control tiles are >= 14.04 (per-tile p ~ 0.016; ~2.5 expected in 160 tiles), so this
  is not significant.
- **Title zone c10-c17 on E2 (addendum item 1):**
  - 64 tiles; median z 9.41, max 14.04;
  - 1 above theta: r5_c16. The next are r5_c14 13.26, r5_c13 13.21, r5_c12 13.06 and r5_c17 12.98, all below theta
    and inside the control range.
- Labelled adjacency is reported but not excluding (DECL-P4-12 item 3). Both hotspots are adjacent, so the
  DECL-P4-10 strict (non-adjacent) hotspot count is 0 on both strips.
- **Reading of the numbers:** the E1 and E2 score distributions match the carbon-ink control (medians 9.0-9.4 vs
  8.7-9.3). The two threshold crossings are at the level the null predicts. A targeted look at r5_c16 (E2) or
  r4_c16 (E1) would test the null rather than a lead. Any such look needs its own declaration.

## What this rules out, and what it does not
- **Ruled out (within this detector's reach):** a mu-regime-contrast ochre title of >= 20 um layer thickness, drawn
  as 2-4 mm letters, on the traced recto surface of the E1 and E2 tiles. It would have given z of about 25-30 at
  12/12 injected locations, and nothing above 14.6 exists.
- **Not ruled out:**
  - ochre ink of 5-10 um, the plausible range;
  - any ochre whose voxel contrast follows electron density (Paganin-type reconstruction);
  - lean or clay-rich ochre;
  - green earth;
  - anything on an untraced surface, or outside the 0 to +20 um layer on the gap side of the mesh.
- The organizers report that the Paris 4 ink is visible in the 2.4 um volume as bright 10-20 um deposits
  (addendum; Angelotti et al. 2026, not re-checked here). A pigment title as bright as that ink would sit near this
  detector's mu-regime limit.

## Integrity notes
- The params freeze preceded every E1/E2 byte read. The only pre-freeze numbers were control-only calibration and a
  1-location control smoke test.
- Deviation, disclosed: the SUBSIBS session ids were filled in right after creation. The branch and task rows were
  pushed before creation.
- Environment incidents:
  - the e2 sub-sibling crashed once on a missing remote ref; it fetched the ref and reran unchanged (24/STATUS.md);
  - the params reference branch tips, not pinned shas: pairs0814b cc81a67, p4-tiles-b 8687bf4 at fetch time;
  - this container restarted after the E1 scores were pushed; no data loss.
- Sub-sibling p4-pig-fe-e1 (E1 maps) turned out redundant, because this container finished E1 first. If it pushes
  scores_E1_raw.json, it serves as an independent re-run for comparison.
