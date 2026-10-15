Provenance: Project HERCULES | owner the owner | [id removed]

# p4-pig-fe STATUS
- Step 1 done: MEMO.md (+ mu_table.json, nist_mu_elements.json). Key numbers: standard ochre ink = 4.5x papyrus in electron density (conservative) and 10.9x in mu at 78 keV. Vesuvius glass is 4.7-6.5x and Ti-magnetite 9.6-31x, so per voxel the ochre is NOT separable from ash or magnetite; only surface confinement plus stroke morphology can separate them.
- Throughput measured: ~570 range-req/s, ~210 MB/s (6 proc x 48 thr, 28-slice ranges).
- Next: params.json (frozen) before any title-strip number; then injection-recovery.
- Blockers: none.
- Step 2: params.json FROZEN (commit below), from control-only calibration (calib_control.json). The family constants: 1.129 um v_air 66.9, v_pap 81.8 (delta 15.0), band [82, 230]; 2.4 um v_air 76.4, v_pap 88.7 (delta 12.4), band [89, 211]. The voxel noise sd is 36-43. No title-strip number exists yet.
