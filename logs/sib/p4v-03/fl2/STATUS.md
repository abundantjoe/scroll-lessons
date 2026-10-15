# p4v-03 FL2 STATUS: PHerc0268 primary (seed lane 0), RULES.md DECL-FL-2 (main 7a315a65), brief tools/fl2/BRIEF_FL2.md sha256 0e07b757..., assign.json sha256 ffb22500...
Provenance: Project HERCULES | [id removed]
2026-10-01T02:13:31Z p4v-03 PHerc0268: START. Old jobs: none running (all verso lists complete and pushed).
- volume 20251110183117-8.640um-1.2m-116keV-masked (samplePixelSize 0.00864 mm); surface 20251110183117-surface-20260413222639-surface-m7-L0-th0.2.zarr; bucket has no organizer segments or umbilicus (UMB=none, CT-mask centroid axis).
- code: tools/sib/p4v-03/fl2/ = fl-pherc0257 54b29c96 pipeline.sh/fl.py/watchdog.sh, parameters only. Disclosed deviations: (a) voxel 8.640 um, not the template's 9.362 (grow voxelsize, render --voxel-size, fl.py VOX_UM -> tile T = 2315 px at 20 mm, 1068 px out); (b) the template seed plan has 8 entries, so "seeds 48" could yield at most 8; plan extended to 48 exactly as the pilot's fl-pherc0257 fl2/fl.py (6 z-fractions x 8 azimuths offset 22.5 deg), first 8 unchanged; (c) manifest rows gain scroll/volume/model/model_sha256/segment_area_cm2 and direction labels forward|reverse; tiles under <SEG>/tiles_official/.
- model applied at 8.640 um with no rescale (ink_9um is a 9.362 um-class model; DECL-FL-1 declares the same chain for 8.64 um volumes): about 8 % scale mismatch, disclosed.
- env: docker/env/vc_build.sh hard-codes proxy port 46883; this container's proxy is on another port, so VC was built from a copy with the port changed (no code or option change).
80ae19b3ff85b5cb5d52e66253af690d98c57518f10c04c003b84a480acbab09  tools/sib/p4v-03/fl2/fl.py
7b80f3ca5047fd6521e63356dadb723ecc397870ec249abf86259985bdea9893  tools/sib/p4v-03/fl2/pipeline.sh
08489b97b4ee22ca0456142ed7894f244616b55a08d274db73517dd08253ffd4  tools/sib/p4v-03/fl2/watchdog.sh
- TRAINING overlap: pilot TRAINING_SCROLLS.json lists official ink_9um training scrolls PHerc0139, PHerc1667, PHercParis4, PHerc0814: PHerc0268 not among them, eligible under OFFICIAL. DENSE: pilot DENSE_FAIL.json (download refused; I10 question open); no DENSE_OK, so OFFICIAL only.
2026-10-01T02:17:21Z p4v-03 PHerc0268: env fixes (BRIEF item 3): vesuvius -e via pip --ignore-requires-python --no-deps; hv-ink-freeze.txt installed without its git editable line, with the PyTorch CPU index (torch 2.14.0+cpu, as the pilot); imagecodecs in /opt/hv; checkpoint sha256 e635558a verified. Watchdog relaunched (attempt 1 had stopped at the env check).
2026-10-01T02:17:29Z p4v-03 PHerc0268 unit: s3 listing
2026-10-01T02:20:16Z p4v-03 PHerc0268: orchestrator 02:19Z env fixes (21bf4bd3 proxy, 7168f33d freeze) were already applied here by hand (same effect; torch 2.14.0+cpu kept); voxel size from metadata (8.640 um) already in use; DENSE withdrawn (DECL-FL-2-E1): OFFICIAL only, as running.
2026-10-01T02:20:50Z p4v-03 PHerc0268 unit: seeds
2026-10-01T02:21:46Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s0 rc=0 area=26.51511599952747 cm2 selfx=0 kept=true
2026-10-01T02:22:43Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s2 rc=0 area=26.516360614212005 cm2 selfx=0 kept=true
2026-10-01T02:24:29Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s4 rc=0 area=26.59154761016421 cm2 selfx=1129 kept=false
2026-10-01T02:25:25Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s6 rc=0 area=26.513741809913085 cm2 selfx=0 kept=true
2026-10-01T02:26:33Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s8 rc=0 area=26.517704882417465 cm2 selfx=0 kept=true
2026-10-01T02:27:43Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s10 rc=0 area=26.54997654299893 cm2 selfx=0 kept=true
2026-10-01T02:28:41Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s12 rc=0 area=26.520179415878978 cm2 selfx=0 kept=true
2026-10-01T02:29:47Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s14 rc=0 area=26.51670948820483 cm2 selfx=0 kept=true
2026-10-01T02:30:42Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s16 rc=0 area=26.51437163648433 cm2 selfx=0 kept=true
2026-10-01T02:31:36Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s18 rc=0 area=26.51761388247821 cm2 selfx=0 kept=true
2026-10-01T02:32:31Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s20 rc=0 area=26.514839193144557 cm2 selfx=0 kept=true
2026-10-01T02:33:28Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s22 rc=0 area=26.514755097486024 cm2 selfx=0 kept=true
2026-10-01T02:34:52Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s24 rc=0 area=26.582827578531486 cm2 selfx=0 kept=true
2026-10-01T02:35:57Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s26 rc=0 area=26.543032349923195 cm2 selfx=0 kept=true
2026-10-01T02:36:54Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s28 rc=0 area=26.51389895955543 cm2 selfx=0 kept=true
2026-10-01T02:37:51Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s30 rc=0 area=26.515205377254297 cm2 selfx=0 kept=true
2026-10-01T02:39:15Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s32 rc=0 area=26.539714977169247 cm2 selfx=456 kept=false
2026-10-01T02:40:15Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s34 rc=0 area=26.514331235071865 cm2 selfx=0 kept=true
2026-10-01T02:41:34Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s36 rc=0 area=26.54101268495341 cm2 selfx=0 kept=true
2026-10-01T02:42:31Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s38 rc=0 area=26.51488865278381 cm2 selfx=0 kept=true
2026-10-01T02:43:26Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s40 rc=0 area=26.514984840264734 cm2 selfx=0 kept=true
2026-10-01T02:44:24Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s42 rc=0 area=26.515984828666628 cm2 selfx=0 kept=true
2026-10-01T02:45:24Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s44 rc=0 area=26.518419979782543 cm2 selfx=0 kept=true
2026-10-01T02:46:29Z p4v-03 PHerc0268 unit: grow pherc0268_p4v-03_s46 rc=0 area=26.516807184523287 cm2 selfx=0 kept=true
2026-10-01T03:28:58Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s0 official: 8 tiles
2026-10-01T04:15:23Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s2 official: 8 tiles
2026-10-01T05:03:37Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s6 official: 8 tiles
2026-10-01T05:43:50Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s8 official: 8 tiles
2026-10-01T06:18:49Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s10 official: 8 tiles
2026-10-01T07:05:18Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s12 official: 8 tiles
2026-10-01T07:56:46Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s14 official: 8 tiles
2026-10-01T08:47:07Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s16 official: 8 tiles
2026-10-01T09:36:31Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s18 official: 8 tiles
2026-10-01T10:26:53Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s20 official: 8 tiles
2026-10-01T11:15:23Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s22 official: 8 tiles
2026-10-01T12:03:20Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s24 official: 8 tiles
2026-10-01T12:48:10Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s26 official: 8 tiles
2026-10-01T12:49:17Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s28 failed
2026-10-01T12:50:22Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s30 failed
2026-10-01T12:51:27Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s34 failed
2026-10-01T12:52:32Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s36 failed
2026-10-01T12:53:37Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s38 failed
2026-10-01T12:54:42Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s40 failed
2026-10-01T12:55:47Z p4v-03 PHerc0268 unit: render pherc0268_p4v-03_s42 failed
2026-10-01T12:56:32Z p4v-03 PHerc0268: container restart changed the proxy port (37747 -> 38625); the running pipeline kept the old one, so from 12:48Z the s26 push and the renders of s28-s42 failed in seconds (no data produced, no DONE markers). Pipeline restarted with the current environment; it redoes those units.
2026-10-01T13:50:57Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s28 official: 8 tiles
2026-10-01T14:41:47Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s30 official: 8 tiles
2026-10-01T15:29:00Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s34 official: 8 tiles
2026-10-01T16:20:12Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s36 official: 8 tiles
2026-10-01T17:07:33Z p4v-03 PHerc0268 unit: tiles pherc0268_p4v-03_s38 official: 8 tiles
2026-10-01T17:19:05Z p4v-03 PHerc0268: FL-2 STOPPED by DECL-FL-4-A1 (orchestrator order 17:18Z, go.sh). Final: 18 of 22 kept segments complete, 144 official tiles pushed; s38 done; s40, s42, s44, s46 not done (never rendered).
