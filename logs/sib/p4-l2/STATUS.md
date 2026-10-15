Provenance: Project HERCULES | owner the owner | [id removed]

# p4-l2 STATUS (DECL-P4-12 + A2, P4-L builder)

- L2 (DECL-P4-12, global T_mid 93 / T_hi 203): DONE. 160 of 160 tiles, manifest.json complete ("partial": false) at 152c0bb (19:04Z). Checks all true: eligible set = pairs0814b e2 (160), valid_fraction and valid_px identical, png sha256 recomputed, IHDR/IDAT/IEND only. 682,668 level-0 chunk reads, 17,199 absent (404, fill 0).
- L2S (DECL-P4-12-A2): DONE. 160/160, l2s/manifest.json partial=false. Every tile's L2 PNG rebuilt from recomputed max = pushed L2 sha256 (160/160, deterministic). valid_fraction = L2 mesh-valid fraction (identical, eligible set = L2's 160); the stretch domain (valid & max>0) is stats.stretch_px. r0-r1 partial tiles unchanged (sha kept).
- raw store: unstretched slab max (uint8 8343 x 8343) + mesh-valid mask per tile, npz compressed, ~41 MB each (~6.5 GB total), kept locally at /work/l2/raw (too large for git); npz sha256 and raw-array sha256 per tile in l2s/manifest.json.
- thresholds (frozen before any tile, ca715bc1...): control w028-037 2.4 um, 17 of 168 tiles, T_mid 93, T_hi 203.
- row-baseline effect on L2 (numbers only), per-row median of E2 slab voxel median / L2 out_mean: r0 68 / 52.7, r1 74 / 62.6, r2 80 / 66.5, r3 86 / 69.5, r4 96 / 77.0, r5 87 / 74.8, r6 101 / 80.1, r7 98 / 76.7.
- unit tests: all pass (unit_tests.json).
- sub-siblings: none (one container is fast enough; see earlier note).
- per band:
- r0-r1: n 40; median over tiles of the per-tile median raw max 119.0 (range 112-123); median raw max mean 109.0; stretch p1 median 39.0 (range 37.0-40.0), p99 median 177.0 (range 168.0-188.0); L2S out_mean median 119.6; known-text columns c0-c8: n 18, median raw max 119.5
- r2-r7: n 120; median over tiles of the per-tile median raw max 127.0 (range 102-134); median raw max mean 119.2; stretch p1 median 42.0 (range 39.0-47.0), p99 median 176.0 (range 168.0-193.0); L2S out_mean median 146.2; known-text columns c0-c8: n 54, median raw max 127.0

Per-tile stretch p1 / p99 (raw uint8 slab-max scale), r c: p1 p99

- r0: c0 38/181, c1 37/176, c2 38/172, c3 38/174, c4 38/173, c5 38/175, c6 38/174, c7 38/175, c8 38/175, c9 38/186, c10 39/181, c11 38/181, c12 38/180, c13 38/179, c14 39/187, c15 38/178, c16 38/180, c17 38/180, c18 38/184, c19 38/185
- r1: c0 39/176, c1 39/172, c2 39/168, c3 39/170, c4 39/169, c5 40/170, c6 40/170, c7 40/171, c8 40/172, c9 40/184, c10 40/181, c11 39/178, c12 39/177, c13 39/178, c14 39/188, c15 39/176, c16 39/177, c17 39/177, c18 39/181, c19 39/181
- r2: c0 41/177, c1 40/175, c2 41/169, c3 40/172, c4 40/171, c5 42/169, c6 41/171, c7 40/171, c8 41/170, c9 41/184, c10 41/184, c11 40/179, c12 40/179, c13 40/180, c14 40/190, c15 40/177, c16 40/179, c17 40/174, c18 40/178, c19 39/173
- r3: c0 42/176, c1 41/172, c2 42/169, c3 41/171, c4 41/170, c5 42/170, c6 42/169, c7 41/171, c8 42/172, c9 42/187, c10 42/188, c11 41/185, c12 41/181, c13 42/181, c14 42/193, c15 41/181, c16 41/177, c17 41/178, c18 40/180, c19 40/180
- r4: c0 43/174, c1 43/171, c2 43/170, c3 42/168, c4 42/170, c5 42/170, c6 43/168, c7 42/170, c8 43/176, c9 43/182, c10 44/180, c11 43/178, c12 43/178, c13 43/177, c14 43/186, c15 42/177, c16 42/177, c17 41/179, c18 41/180, c19 42/179
- r5: c0 42/179, c1 41/172, c2 42/172, c3 41/172, c4 41/174, c5 41/174, c6 41/171, c7 41/174, c8 42/176, c9 41/183, c10 42/180, c11 41/180, c12 41/178, c13 41/179, c14 41/185, c15 40/179, c16 41/180, c17 40/182, c18 41/182, c19 40/181
- r6: c0 44/177, c1 45/173, c2 44/175, c3 45/171, c4 44/171, c5 45/173, c6 45/170, c7 44/172, c8 47/175, c9 46/177, c10 46/175, c11 45/174, c12 45/176, c13 45/176, c14 45/181, c15 45/176, c16 45/175, c17 45/178, c18 45/178, c19 45/179
- r7: c0 44/177, c1 46/173, c2 46/177, c3 46/169, c4 45/169, c5 45/170, c6 46/170, c7 45/174, c8 45/180, c9 45/179, c10 46/179, c11 45/175, c12 44/173, c13 44/175, c14 44/176, c15 44/174, c16 44/175, c17 44/177, c18 44/181, c19 44/186

- DECL-P4-17 item 1 (P4-W, L2S): DONE. w_l2s 70/70 windows (title zone, top-left c9-c18, r0-r6) and wpc_l2s 56/56 (control, c0-c7), all eligible, uuid4 ids unique, sha256 recomputed. The display is the L2S rule per window, INTER_AREA 16686 -> 1068.
  - Incident: two window processes were OOM-killed (the float64 stretch peaked at ~9.7 GB). The fix computes the same stretch from the uint8 histogram plus a LUT. It is byte-identical to builder.linear_window_ct: 30/30 synthetic cases and a real window (wpc r0 c0 sha equal). Killed runs resumed, with no duplicate windows.
- DECL-P4-17 item 2 (block detector, L2S depth): FAIL. On the control strip, held-out recall is 0.089 at FPR 0.032 (T_d 161); see BLOCK_FREEZE.md. No title-zone cell was computed.
- L3: none (P4-L3-CALIB-RESULT STOP, no d*).
- DECL-P4-18 L4 (level 1, params_l4.json a3fb174): unit tests pass. Faces are found within 1 slice; ink planted 10 um outside is recovered, +88 u8. Disclosed: a deposit brighter than T_mid is bridged into the sheet run, and when the deposit lies nearer the mesh than the sheet it is taken as the sheet (7 % / 21 % of ink px), which leaks ink into the other face.
  - Control pre-gate (PREGATE_L4.json): L4- T_d 250, held-out recall 0.074, FPR 0.054, rot90 0.070; L4+ T_d 219, recall 0.033, FPR 0.022, rot90 0.038. Synthetic 1.0 on both faces (a generator weakness, see ASK.md). Both faces FAIL, so no w010-027 L4 number, tile or window is computed.
  - Control face offsets (median over tiles of p10 / p50 / p90, um) are in PREGATE_L4.json.
- blockers: none
