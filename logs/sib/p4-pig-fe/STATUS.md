Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-fe STATUS
- Step 1 done: MEMO.md (+ mu_table.json, nist_mu_elements.json). Key numbers: standard ochre ink = 4.5x papyrus in electron density (conservative) and 10.9x in mu at 78 keV. Vesuvius glass is 4.7-6.5x and Ti-magnetite 9.6-31x, so per voxel the ochre is NOT separable from ash or magnetite; only surface confinement plus stroke morphology can separate them.
- Throughput measured: ~570 range-req/s, ~210 MB/s (6 proc x 48 thr, 28-slice ranges).
- Next: params.json (frozen) before any title-strip number; then injection-recovery.
- Blockers: none.
- Step 2: params.json FROZEN (commit below), from control-only calibration (calib_control.json). The family constants: 1.129 um v_air 66.9, v_pap 81.8 (delta 15.0), band [82, 230]; 2.4 um v_air 76.4, v_pap 88.7 (delta 12.4), band [89, 211]. The voxel noise sd is 36-43. No title-strip number exists yet.
- 18:31Z: sub-siblings created: e2 (2.4 um family C2+E2) and e1 (E1 level-0 maps). Here: control C full run, then injection C/E1 (12+12). Smoke test on control row 2 (numbers): natural tile-max r of about 21-28 raw vs MAD-sigma of about 2.4, so the natural structure reaches about 10 sigma. A single injection smoke test on C: the standard_mu 5 um letter adds about +9.5 raw, and the standard_rho_e 5 um letter does not beat the window's natural maximum. Expectation: probably insensitive in the conservative regime (to be measured).
- DONE (2026-09-27). Verdict: INSENSITIVE at 5-10 um (conservative rho_e regime: 0/12 at every thickness up to 20 um on C, E1, C2 and E2). In the mu regime the detection limit is 20 um (C, E1, E2) and 10 um (C2). Title strips: E1 max z 14.63 (r4_c16), E2 max 14.04 (r5_c16, title zone c10-c17); theta 14.02 / 13.84. Both are labelled-adjacent and consistent with the ~1 % null rate. No lead. See REPORT.md.
- Next: none for this sibling. A targeted look at a hotspot would need its own declaration, and the numbers do not justify one.
