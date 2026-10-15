Provenance: Project HERCULES | owner the owner | [id removed]

# p4-purple additions to logs/p4/HYPOTHESES.md (for merge; priors are uncertain judgements)

| id | hypothesis | prior | CT physics (COLOURANTS.md) | test | validation | status |
|---|---|---|---|---|---|---|
| I3a | Tyrian purple title with Br retained (0-50 % loss) | inside I3 | Paganin 78 keV peak 1.1-1.3x carbon ink; absorption 1.9-2.9x; dual-energy R 0.43-0.52 vs papyrus 0.85 (column dR -0.12 to -0.20 per 10 um) | L3 at d* (deposit), 78/137 keV column ratio on r3 band | control column-ratio null; injection via registered pair | dual energy: NOT sensitive at <= 20 um (DUAL_FREEZE 6d12337): untestable by dual energy; deposit channel L3 only |
| I3b | Purple with Br almost gone (90 % loss) or purpurissum dye lost, CaCO3 carrier left | inside I3 | peak ~0.9-1.4x carbon ink; R 0.66-0.73 (dR -0.03 to -0.07) | as I3a | as I3a | dual energy NOT sensitive (purpurissum recovery 0.00): L3 only |
| I6 | Dye-wash title: organic dye soaked into fibres, no deposit thickness | 0.005 | peak = carbon ink x (areal mass ratio), likely << 1; R = papyrus (0.85) | morphology (p4-purple-mo) | control AUC gate: FAIL 0/9 (best 0.656) | untestable with published data (no deposit channel, no composition channel) |
| I7 | Heavy (Pb/Hg/Au) title outside +-15 um of the mesh | inside I2 | peak 6-17x carbon ink; R ~1.0 | P4-F re-run at d* or offset sweep (DECL-P4-6-A3) | p4-highz injection limits | pending d* |

## Blind spots (OWNER-STANDING-ORDER-2 item 5)
- Colour is nearly invisible in the published Paganin volumes: thin deposits are seen by electron density. At 78 keV, purple, organic and lake inks are 0.9-1.4x carbon ink. A single-energy channel therefore cannot tell a purple title from a black one. It can only find a deposit; composition needs the 137 keV pair.
- Dual-energy coverage is only the E2 r3 band (14-27 % of r3_c10-c17). Everything else is composition-blind.
- Dual energy is measured on the control and insensitive to purple, lakes and carbon ink at <= 20 um (FPR 0.022/patch; 137 keV calibration fails the unit checks). Mineral grains and ash in the papyrus (Ca, Fe, Si) have R 0.4-0.7 and are the expected false positives.
- Dye loss during carbonisation (dibromoindigo sublimes near 390 C), and the unknown dye content of lakes.
- The absolute model contradicts the control. A 5 um carbon deposit should saturate the scale, but only 0.064 % of slab maxima saturate. Absolute detection limits are upper bounds until d* is calibrated.
- Organic dyes and carbon ink have identical R, so dual energy cannot separate a purple organic title from black text.
