# p4v-01 fl2 STATUS (RULES.md DECL-FL-2; tools/fl2/BRIEF_FL2.md sha256 0e07b757...; assign.json ffb22500...)
Provenance: Project HERCULES | [id removed]
Role: PHerc0125 primary (seed lane 0); second = p4v-10. Volume 20250821151825 (9.362 um, 1.2 m, 113 keV, masked).
Source: auto-grow. Bucket PHerc0125/: photos/, representations/{predictions/{lasagna,surfaces},umbilicus}/, volumes/; no organizer tifxyz segments.
CT  s3://vesuvius-challenge-open-data/PHerc0125/volumes/20250821151825-9.362um-1.2m-113keV-masked.zarr/
SURF .../representations/predictions/surfaces/20250821151825-surface-20260413222639-surface-m7-L0-th0.2.zarr/ (the only surface-m7 L0 zarr)
UMB  .../representations/umbilicus/20250821151825-umbilicus-20260808111524.json (organizer, 83 control points)
Code: tools/sib/p4v-01/fl2/ from fl-pherc0257 @54b29c96. Parameter changes per brief item 2 (SCROLL, CT, SURF, UMB, branch, paths, names,
  48 candidate seeds with lane 0 = even indices, NSEEDS=40, MIN_AREA=16, selfx=0, all cells valid>=50%, both directions).
DISCLOSED deviations beyond pure parameters (logic of grow/render/infer/tiles unchanged):
  D1 fl.py cmd_seeds: the template plan has only 8 (z, azimuth) entries, so "seeds ... 48" would cap at 8. For nseeds > 8 the
     template's 8 entries are kept verbatim as indices 0-7, plus a fixed grid z in {0.25,0.40,0.55,0.70,0.85} x azimuth
     22.5+45k (k=0..7) = 48 entries. The per-ray seed rule (0.35-0.65 R, surface >= 128) is unchanged.
     The second worker (p4v-10) should use the same seeds.json (pushed here) so the lanes partition one list.
  D2 pipeline.sh order: per seed grow -> render -> infer -> tiles -> push (brief item 6), not grow-all-first.
  D3 outputs: <SEG>/tiles_<official|dense>/, direction labels forward|reverse; manifest rows annotated with the brief item 5
     fields (scroll, volume, model, model_sha256, segment_area_cm2) plus tifxyz_x_sha256 by a post-step; cmd_tiles unchanged.
  D4 watchdog: reruns every 10 min until /work/fl2/STOP (all day; picks up the dense arm late), not 6 attempts.
  D5 if organizer tifxyz segments appear in the bucket the pipeline stops for review instead of mixing sources.
2026-10-01T02:12:03Z start (env setup running)
2026-10-01T02:18:11Z DECL-FL-2-E1 applied: DENSE arm withdrawn; pipeline runs the OFFICIAL model (e635558a) only (D3 'dense' dir and D4 'picks up the dense arm' no longer apply). vc_build.sh taken from 21bf4bd3 (proxy from $HTTPS_PROXY); the running build already uses an equivalent port-substituted copy (/work/scripts/vc_build_port.sh, only line 14 differs: this container's proxy port).
2026-10-01T02:20:03Z env OK (villa 41701aa0eaa1aa765523db3f9f972b5830abf549)
2026-10-01T02:20:04Z s3 list: 0 organizer tifxyz segments
2026-10-01T02:22:46Z grow pherc0125_p4v-01_s0: rc=0 area=31.239048156712204 cm2 selfx=1706 kept=false (160 s)
2026-10-01T02:23:37Z grow pherc0125_p4v-01_s2: rc=0 area=23.305779695412816 cm2 selfx=0 kept=true (49 s)
2026-10-01T02:24:47Z env scripts taken from 9c280796 for provenance (not re-run: env already OK). Live env: villa 41701aa0, vesuvius editable (pip --ignore-requires-python, py3.13), hv-ink freeze minus editable line, torch 2.14.0+cpu / torchvision 0.29.0+cpu (= pilot env.txt), imagecodecs in /opt/hv, ckpt e635558a verified.
2026-10-01T02:28:02Z render pherc0125_p4v-01_s2 ok (263 s)
2026-10-01T02:48:24Z tiles pherc0125_p4v-01_s2 official: 8 tiles (1222 s infer+tile)
2026-10-01T02:49:34Z grow pherc0125_p4v-01_s4: rc=0 area=31.133995638435298 cm2 selfx=0 kept=true (66 s)
2026-10-01T02:55:28Z render pherc0125_p4v-01_s4 ok (352 s)
2026-10-01T03:19:40Z tiles pherc0125_p4v-01_s4 official: 8 tiles (1452 s infer+tile)
2026-10-01T03:20:47Z grow pherc0125_p4v-01_s6: rc=0 area=31.131598356091843 cm2 selfx=0 kept=true (64 s)
2026-10-01T03:26:34Z render pherc0125_p4v-01_s6 ok (345 s)
2026-10-01T03:54:44Z tiles pherc0125_p4v-01_s6 official: 8 tiles (1690 s infer+tile)
2026-10-01T03:55:52Z grow pherc0125_p4v-01_s8: rc=0 area=31.132568128458914 cm2 selfx=0 kept=true (65 s)
2026-10-01T04:00:26Z render pherc0125_p4v-01_s8 ok (272 s)
2026-10-01T04:19:05Z tiles pherc0125_p4v-01_s8 official: 8 tiles (1119 s infer+tile)
2026-10-01T04:20:10Z grow pherc0125_p4v-01_s10: rc=0 area=31.131462035141183 cm2 selfx=0 kept=true (61 s)
2026-10-01T04:25:45Z render pherc0125_p4v-01_s10 ok (332 s)
2026-10-01T06:04:25Z container restart detected (uptime 0 min; s10 infer interrupted ~04:38Z, no marker); watchdog relaunched; s10 infer redone from the kept render
2026-10-01T06:05:37Z keepalive (tools/fl2/keepalive.sh, orchestrator 06:00Z) adopted; watchdog relaunched by absolute path so keepalive's pgrep sees it (avoids a duplicate pipeline); s10 infer restarted. PIPELINE_DONE absent (no seed extension). Manifest rows already carry model=official, model_sha256=e635558a...
2026-10-01T06:38:07Z tiles pherc0125_p4v-01_s10 official: 8 tiles (1945 s infer+tile)
2026-10-01T06:39:56Z grow pherc0125_p4v-01_s12: rc=0 area=27.857462905137645 cm2 selfx=0 kept=true (104 s)
2026-10-01T06:44:59Z render pherc0125_p4v-01_s12 ok (300 s)
2026-10-01T07:10:34Z tiles pherc0125_p4v-01_s12 official: 8 tiles (1535 s infer+tile)
2026-10-01T07:13:01Z grow pherc0125_p4v-01_s14: rc=0 area=31.14684350052406 cm2 selfx=0 kept=true (143 s)
2026-10-01T07:19:41Z render pherc0125_p4v-01_s14 ok (398 s)
2026-10-01T07:52:06Z tiles pherc0125_p4v-01_s14 official: 8 tiles (1945 s infer+tile)
2026-10-01T07:54:19Z grow pherc0125_p4v-01_s16: rc=0 area=31.156399562656702 cm2 selfx=0 kept=true (128 s)
2026-10-01T08:00:07Z render pherc0125_p4v-01_s16 ok (346 s)
2026-10-01T08:28:34Z tiles pherc0125_p4v-01_s16 official: 8 tiles (1707 s infer+tile)
2026-10-01T08:30:18Z grow pherc0125_p4v-01_s18: rc=0 area=31.131255705965916 cm2 selfx=0 kept=true (100 s)
2026-10-01T08:36:38Z render pherc0125_p4v-01_s18 ok (377 s)
2026-10-01T09:07:48Z tiles pherc0125_p4v-01_s18 official: 8 tiles (1870 s infer+tile)
2026-10-01T09:09:18Z grow pherc0125_p4v-01_s20: rc=0 area=27.86406871977433 cm2 selfx=730 kept=false (86 s)
2026-10-01T09:10:57Z grow pherc0125_p4v-01_s22: rc=0 area=31.132215536384884 cm2 selfx=0 kept=true (97 s)
2026-10-01T09:17:01Z render pherc0125_p4v-01_s22 ok (362 s)
2026-10-01T09:47:39Z tiles pherc0125_p4v-01_s22 official: 8 tiles (1838 s infer+tile)
2026-10-01T09:49:11Z grow pherc0125_p4v-01_s24: rc=0 area=31.13059240849469 cm2 selfx=0 kept=true (88 s)
2026-10-01T09:54:22Z render pherc0125_p4v-01_s24 ok (308 s)
2026-10-01T10:20:07Z tiles pherc0125_p4v-01_s24 official: 8 tiles (1545 s infer+tile)
2026-10-01T10:21:38Z grow pherc0125_p4v-01_s26: rc=0 area=31.1316555348143 cm2 selfx=0 kept=true (87 s)
2026-10-01T10:27:21Z render pherc0125_p4v-01_s26 ok (341 s)
2026-10-01T10:56:16Z tiles pherc0125_p4v-01_s26 official: 8 tiles (1735 s infer+tile)
2026-10-01T10:57:48Z grow pherc0125_p4v-01_s28: rc=0 area=31.130289067405286 cm2 selfx=0 kept=true (87 s)
2026-10-01T11:03:12Z render pherc0125_p4v-01_s28 ok (322 s)
2026-10-01T11:26:00Z tiles pherc0125_p4v-01_s28 official: 8 tiles (1368 s infer+tile)
2026-10-01T11:27:41Z grow pherc0125_p4v-01_s30: rc=0 area=31.133437064660345 cm2 selfx=0 kept=true (96 s)
2026-10-01T11:34:26Z render pherc0125_p4v-01_s30 ok (402 s)
2026-10-01T12:12:01Z tiles pherc0125_p4v-01_s30 official: 8 tiles (2255 s infer+tile)
2026-10-01T12:13:47Z grow pherc0125_p4v-01_s32: rc=0 area=31.129913082012653 cm2 selfx=0 kept=true (98 s)
2026-10-01T12:20:33Z render pherc0125_p4v-01_s32 ok (403 s)
2026-10-01T12:52:25Z tiles pherc0125_p4v-01_s32 official: 8 tiles (1912 s infer+tile)
2026-10-01T12:55:24Z grow pherc0125_p4v-01_s34: rc=0 area=31.163134039591203 cm2 selfx=0 kept=true (173 s)
2026-10-01T13:02:11Z render pherc0125_p4v-01_s34 ok (405 s)
2026-10-01T13:35:07Z tiles pherc0125_p4v-01_s34 official: 8 tiles (1976 s infer+tile)
2026-10-01T13:36:45Z grow pherc0125_p4v-01_s36: rc=0 area=31.13212331362602 cm2 selfx=0 kept=true (92 s)
2026-10-01T13:42:59Z render pherc0125_p4v-01_s36 ok (371 s)
2026-10-01T14:08:35Z tiles pherc0125_p4v-01_s36 official: 8 tiles (1536 s infer+tile)
2026-10-01T14:10:12Z grow pherc0125_p4v-01_s38: rc=0 area=31.131194510621825 cm2 selfx=0 kept=true (92 s)
2026-10-01T14:18:29Z render pherc0125_p4v-01_s38 ok (495 s)
2026-10-01T15:00:09Z tiles pherc0125_p4v-01_s38 official: 8 tiles (2500 s infer+tile)
2026-10-01T15:01:56Z grow pherc0125_p4v-01_s40: rc=0 area=31.132063932382337 cm2 selfx=0 kept=true (101 s)
2026-10-01T15:09:04Z render pherc0125_p4v-01_s40 ok (425 s)
2026-10-01T15:35:51Z tiles pherc0125_p4v-01_s40 official: 8 tiles (1607 s infer+tile)
2026-10-01T15:37:23Z grow pherc0125_p4v-01_s42: rc=0 area=31.130010137359015 cm2 selfx=0 kept=true (87 s)
2026-10-01T15:44:04Z render pherc0125_p4v-01_s42 ok (398 s)
2026-10-01T16:15:05Z tiles pherc0125_p4v-01_s42 official: 8 tiles (1861 s infer+tile)
2026-10-01T16:16:36Z grow pherc0125_p4v-01_s44: rc=0 area=31.13578943206756 cm2 selfx=0 kept=true (86 s)
2026-10-01T16:22:23Z render pherc0125_p4v-01_s44 ok (344 s)
2026-10-01T16:45:11Z tiles pherc0125_p4v-01_s44 official: 8 tiles (1368 s infer+tile)
2026-10-01T16:46:38Z grow pherc0125_p4v-01_s46: rc=0 area=31.131761072219934 cm2 selfx=0 kept=true (82 s)
2026-10-01T16:52:53Z render pherc0125_p4v-01_s46 ok (372 s)
2026-10-01T17:19:19Z STOPPED by orchestrator order DECL-FL-4-A1 (fleet to PHerc0268/PHerc0490A). Final: 21 segments done (168 official tiles), 2 rejected (selfx); s42 infer interrupted (render/grow kept, no tiles); s44, s46 not attempted.
2026-10-01T17:21:21Z tiles pherc0125_p4v-01_s46 official: 8 tiles (1708 s infer+tile)
2026-10-01T17:21:26Z seed list exhausted (24 attempts)
2026-10-01T17:21:40Z ERRATUM to the 17:19:19Z line: s42 and s44 were already done and s46 finished at 17:21:21Z, so the lane-0 seed list is COMPLETE: 22 segments, 176 official tiles, 2 rejected (s0, s? selfx); FL-2 then stopped for DECL-FL-4-A1.
2026-10-01T17:21:50Z clarification: the 2 rejected grows are s0 (selfx 1706) and s20 (selfx 730).
