2026-10-01T02:10:05Z env FAILED (setup_env rc=0; see /work/fl2gate/setup_env.log)
2026-10-01T02:10:49Z env fix: docker/env/hv-ink-freeze.txt installed without its editable git line (uv rejects it) and without the torch/torchvision pins (torch 2.14.0+cpu no longer offered; installed 2.14.1+cpu from the official CPU index); vesuvius infer importable; relaunching the gate
2026-10-01T02:10:59Z env OK (villa 41701aa, ckpt sha e635558a verified, vesuvius infer importable)
2026-10-01T02:11:04Z segment 20260422000000-title_2026042222_zmid_flatboi fetched (9.362 um tifxyz; sha256 in tifxyz/sha256.txt); measure.json written
2026-10-01T02:12:28Z render done (voxel 9.362 um from metadata.json)
2026-10-01T02:15:28Z TRAINING CHECK (DECL-FL-2-E1): gate segment 20260422000000-title_2026042222_zmid_flatboi listed in official ink_9um training: NO. Sources: villa 41701aa vesuvius/src/vesuvius/ink_detection/configs/aligned21_hybrid_3d2d.json (sha256 f9925e20...; datasets: pherc0139 w016 w017 w028 w029 w035 w039 w040 w041 w043; native9 w035 w039 w040 w041 w044; pherc0814-46527; pherc1667 w013 w018 w023 w028 w029 w031; phercparis4 w00 w01 w02 w03 w05 w06 w07 w09) and HF scrollprize/ink_9um README @7109667e (sha256 ef0f3cf3...; 'PHerc. 0139 (9)'). Same-papyrus note: none of the other 38 organizer PHerc0139 9.362 um meshes (incl. every listed 0139 training window) intersects the title mesh bbox +-50 vox (w030 has no 9.362 um mesh; not a training segment). DENSE arm withdrawn (DECL-FL-2-E1): official model only; no Nieuwlaar code or crop used.
2026-10-01T02:22:25Z DECL-FL-2-E2 accepted. Held-out ranking (organizer PHerc0139 9.362 um meshes not in the ink_9um training list; fraction of vertices within 4 / 10 vox of any training mesh vertex): w054 61.61 cm2 0/0, w055 58.68 0/0, w052 57.81 0/0, w053 57.33 0/0.0001, w051 56.49 0/0, w057 56.17 0/0.0001 (full list heldout_rank.json; training w016 and w017 have no 9.362 um mesh and could not be checked). Chosen: w054, w055, w051, w057 (w052 and w053 skipped as known re-traces of w054, RULES READCAL bank attempt 1). Queued after the title job.
2026-10-01T02:25:05Z official infer done (both directions)
2026-10-01T02:25:13Z tiles_official: 0 kept; canvas 1780 x 5360 px (1.67 x 5.02 cm), tile 2136 px (2 cm); grid rows 0, cols 2; mesh area 7.20 cm2
2026-10-01T02:25:28Z tiles_title_supp: 4 strip cells (both directions), supplementary per DECL-FL-2-E2 item 2
2026-10-01T02:25:32Z 20260206000002-w054_2026020617 tifxyz fetched (sha256 in 20260206000002-w054_2026020617/tifxyz/sha256.txt), area 61.61 cm2
2026-10-01T02:33:28Z 20260206000002-w054_2026020617 render FAILED rc=1
2026-10-01T02:33:31Z 20251226000000-w055_2025122611 tifxyz fetched (sha256 in 20251226000000-w055_2025122611/tifxyz/sha256.txt), area 58.68 cm2
2026-10-01T02:40:30Z 20251226000000-w055_2025122611 render FAILED rc=1
2026-10-01T02:40:34Z 20260306000001-w051_2026030600 tifxyz fetched (sha256 in 20260306000001-w051_2026030600/tifxyz/sha256.txt), area 56.49 cm2
2026-10-01T02:47:00Z 20260306000001-w051_2026030600 render FAILED rc=1
2026-10-01T02:47:04Z 20260127000000-w057_2026012713 tifxyz fetched (sha256 in 20260127000000-w057_2026012713/tifxyz/sha256.txt), area 56.17 cm2
2026-10-01T02:52:41Z 20260127000000-w057_2026012713 render FAILED rc=1
2026-10-01T02:52:43Z GATE2 END: segments done: 0 of 4
2026-10-01T02:54:50Z gate2 renders 1-4 failed: 'No space left on device' at ~55 % of w054 (render 11140 x 7660 x 31). Failed partial render zarrs (own scratch, 4.7 GB) and the title render (predictions kept) deleted; a 6 GB test write then succeeded (df avail 16 GB). Rerunning gate2 (idempotent) with a disk monitor (/work/fl2gate/disk.log).
2026-10-01T03:02:12Z 20260206000002-w054_2026020617 render FAILED rc=1
2026-10-01T03:09:37Z 20251226000000-w055_2025122611 render FAILED rc=1
2026-10-01T03:16:01Z 20260306000001-w051_2026030600 render FAILED rc=1
2026-10-01T03:22:05Z 20260127000000-w057_2026012713 render FAILED rc=1
2026-10-01T03:22:07Z GATE2 END: segments done: 0 of 4
2026-10-01T03:25:02Z gate2 rerun failed again for all 4 (disk). Cause: render remote chunk cache in the container (/work/docker grows ~6 -> ~30 GB). Large held-out segments need ~21-40 GB; only w050 (15.64 cm2, ~12 GB est) fits. Running w050 now (GATE_SEGS); ASK.md section 3.
2026-10-01T03:25:11Z 20260302000001-w050_2026030220 tifxyz fetched (sha256 in 20260302000001-w050_2026030220/tifxyz/sha256.txt), area 15.64 cm2
2026-10-01T03:29:25Z 20260302000001-w050_2026030220 render done
2026-10-01T03:55:48Z 20260302000001-w050_2026030220 official infer done (both directions)
2026-10-01T03:55:52Z 20260302000001-w050_2026030220 tiles_official: 4 tiles (both directions; template cmd_tiles unchanged)
2026-10-01T03:55:54Z GATE2 END: segments done: 1 (20260302000001-w050_2026030220)
2026-10-01T03:56:33Z GATE STATE: tiles_official = 4 tiles from held-out w050 (2 cells x 2 directions, template tiler unchanged); tiles_title_supp = 4 supplementary strip tiles. w050 cache peak ~19 GB (free fell to 7.6 GB), so no larger held-out segment fits; see ASK.md section 3. Stopping until a decision.
2026-10-01T05:42:23Z DECL-FL-2-E3 accepted: pieces of <= ~12 cm2 (vertical cell pairs; margin 256-319 px <= 0.3 cm; crop origin on the 64-px infer stride grid so sliding-window positions coincide with the full canvas). Unit 0 = w050 piece re-make compared byte-for-byte with the full-canvas w050 tiles. Then held-out segments in heldout_rank order (w054, w055, w052 first; 2 pieces each), then segment after segment. Note: w052 and w053 are recorded re-traces of w054 (same papyrus), kept because the order says heldout_rank order.
2026-10-01T06:00:38Z PIECE CHECK w050: 0 of 4 piece tiles byte-identical to the full-canvas tiles (full-canvas has 4)
2026-10-01T06:16:43Z 20260206000002-w054_2026020617 piece 0 ([[0, 0], [1, 0]] 9.493 cm2): 4 tiles; gate tiles_official total 8
2026-10-01T06:26:56Z 20260206000002-w054_2026020617 piece 1 ([[2, 0]] 5.652 cm2): 2 tiles; gate tiles_official total 10
2026-10-01T06:43:01Z 20251226000000-w055_2025122611 piece 0 ([[0, 0], [1, 0]] 9.493 cm2): 4 tiles; gate tiles_official total 14
2026-10-01T06:53:54Z 20251226000000-w055_2025122611 piece 1 ([[2, 0]] 5.652 cm2): 2 tiles; gate tiles_official total 16
2026-10-01T07:09:52Z 20260227000000-w052_2026022705 piece 0 ([[0, 0], [1, 0]] 9.493 cm2): 4 tiles; gate tiles_official total 20
2026-10-01T07:21:18Z 20260227000000-w052_2026022705 piece 1 ([[2, 0]] 5.652 cm2): 2 tiles; gate tiles_official total 22
2026-10-01T07:41:35Z 20260206000002-w054_2026020617 piece 2 ([[0, 1], [1, 1]] 10.604 cm2): 4 tiles; gate tiles_official total 26
2026-10-01T07:42:58Z PIECE CHECK detail (numbers only): r0c0 forward: 5 of 1140624 px differ, max 1, ink_score equal True; r0c0 reverse: 3 of 1140624 px differ, max 1, ink_score equal True; r1c0 forward: 6 of 1140624 px differ, max 1, ink_score equal True; r1c0 reverse: 4 of 1140624 px differ, max 1, ink_score equal True. Pearson 1.00000 for all 4. Not byte-identical, differing by at most 1 grey level on a few px; most likely floating-point non-determinism in CPU inference (not tested by repeating the full-canvas run). The piece method reproduces the full-canvas tiles to +-1 grey level.
2026-10-01T07:54:52Z 20260206000002-w054_2026020617 piece 3 ([[2, 1]] 6.314 cm2): 2 tiles; gate tiles_official total 28
2026-10-01T08:15:30Z 20260206000002-w054_2026020617 piece 4 ([[0, 2], [1, 2]] 10.7 cm2): 4 tiles; gate tiles_official total 32
2026-10-01T08:29:03Z 20260206000002-w054_2026020617 piece 5 ([[2, 2]] 6.371 cm2): 2 tiles; gate tiles_official total 34
2026-10-01T08:49:45Z 20260206000002-w054_2026020617 piece 6 ([[0, 3], [1, 3]] 10.541 cm2): 4 tiles; gate tiles_official total 38
2026-10-01T09:03:35Z 20260206000002-w054_2026020617 piece 7 ([[2, 3]] 6.276 cm2): 2 tiles; gate tiles_official total 40
2026-10-01T09:21:12Z 20260206000002-w054_2026020617 piece 8 ([[0, 4], [1, 4]] 10.636 cm2): 4 tiles; gate tiles_official total 44
2026-10-01T09:35:00Z 20260206000002-w054_2026020617 piece 9 ([[2, 4]] 6.333 cm2): 2 tiles; gate tiles_official total 46
2026-10-01T09:56:44Z 20251226000000-w055_2025122611 piece 2 ([[0, 1], [1, 1]] 10.604 cm2): 4 tiles; gate tiles_official total 50
2026-10-01T10:11:03Z 20251226000000-w055_2025122611 piece 3 ([[2, 1]] 6.314 cm2): 2 tiles; gate tiles_official total 52
2026-10-01T10:33:43Z 20251226000000-w055_2025122611 piece 4 ([[0, 2], [1, 2]] 10.7 cm2): 4 tiles; gate tiles_official total 56
2026-10-01T10:48:13Z 20251226000000-w055_2025122611 piece 5 ([[2, 2]] 6.371 cm2): 2 tiles; gate tiles_official total 58
2026-10-01T11:10:07Z 20251226000000-w055_2025122611 piece 6 ([[0, 3], [1, 3]] 10.541 cm2): 4 tiles; gate tiles_official total 62
2026-10-01T11:23:59Z 20251226000000-w055_2025122611 piece 7 ([[2, 3]] 6.276 cm2): 2 tiles; gate tiles_official total 64
2026-10-01T11:46:10Z 20260227000000-w052_2026022705 piece 2 ([[0, 1], [1, 1]] 10.604 cm2): 4 tiles; gate tiles_official total 68
2026-10-01T12:00:36Z 20260227000000-w052_2026022705 piece 3 ([[2, 1]] 6.314 cm2): 2 tiles; gate tiles_official total 70
2026-10-01T12:23:49Z 20260227000000-w052_2026022705 piece 4 ([[0, 2], [1, 2]] 10.7 cm2): 4 tiles; gate tiles_official total 74
2026-10-01T12:38:04Z 20260227000000-w052_2026022705 piece 5 ([[2, 2]] 6.371 cm2): 2 tiles; gate tiles_official total 76
2026-10-01T13:00:26Z 20260227000000-w052_2026022705 piece 6 ([[0, 3], [1, 3]] 10.541 cm2): 4 tiles; gate tiles_official total 80
2026-10-01T13:14:49Z 20260227000000-w052_2026022705 piece 7 ([[2, 3]] 6.276 cm2): 2 tiles; gate tiles_official total 82
2026-10-01T13:33:37Z 20260220000000-w053_2026022021 piece 0 ([[0, 0], [1, 0]] 9.493 cm2): 4 tiles; gate tiles_official total 86
2026-10-01T13:46:04Z 20260220000000-w053_2026022021 piece 1 ([[2, 0]] 5.652 cm2): 2 tiles; gate tiles_official total 88
2026-10-01T14:07:44Z 20260220000000-w053_2026022021 piece 2 ([[0, 1], [1, 1]] 10.604 cm2): 4 tiles; gate tiles_official total 92
2026-10-01T14:21:52Z 20260220000000-w053_2026022021 piece 3 ([[2, 1]] 6.314 cm2): 2 tiles; gate tiles_official total 94
2026-10-01T14:43:40Z 20260220000000-w053_2026022021 piece 4 ([[0, 2], [1, 2]] 10.7 cm2): 4 tiles; gate tiles_official total 98
2026-10-01T14:56:59Z 20260220000000-w053_2026022021 piece 5 ([[2, 2]] 6.371 cm2): 2 tiles; gate tiles_official total 100
2026-10-01T15:20:09Z 20260220000000-w053_2026022021 piece 6 ([[0, 3], [1, 3]] 10.541 cm2): 4 tiles; gate tiles_official total 104
2026-10-01T15:32:54Z 20260220000000-w053_2026022021 piece 7 ([[2, 3]] 6.276 cm2): 2 tiles; gate tiles_official total 106
2026-10-01T15:48:48Z 20260306000001-w051_2026030600 piece 0 ([[0, 0], [1, 0]] 9.493 cm2): 4 tiles; gate tiles_official total 110
2026-10-01T16:00:14Z 20260306000001-w051_2026030600 piece 1 ([[2, 0]] 5.652 cm2): 2 tiles; gate tiles_official total 112
2026-10-01T16:21:18Z gate3 (ink_9um pieces) STOPPED by hand at 16:12Z for DECL-FL-4 priority (112 official gate tiles; w051 piece 2 was in progress and is redone on resume; the runner is idempotent).
