# p4v-02 FL2 STATUS (RULES.md DECL-FL-2): PHerc0175A primary, seed lane 0

2026-10-01T02:11:54Z p4v-02 start: trigger trig_011mYNs1X7NAc2fR8jJ4itfL (02:08Z), DECL-FL-2 @7a315a65, BRIEF_FL2 sha256 0e07b757bafd383c24b3e426a60be95d34690057d7c6117e9f4264e9691142a0, assign.json sha256 ffb225004d0b0a0e3af3216b1f2b9858c1c49c8b19850014f432356d99dd37b5. Template fl-pherc0257 @54b29c96: pipeline.sh 7c85a0f8a20a191b, fl.py cc129e8f4b236d1d. Volume 20250521115057 (8.640 um, zarr 12748x9363x9363), surface-m7-L0 20260413222639; no organizer umbilicus or tifxyz segments -> auto-grow. Parameters changed (beyond names/paths): voxel 9.362 -> 8.640 um (grow, render, fl.py VOX_UM; tile = 2315 src px = 20.0 mm); seed plan extended 8 -> 64 (z-frac x azimuth) entries so seeds 48 is reachable (original 8 first); watchdog attempts 6 -> 12; per-segment flow (grow -> render -> infer -> tiles -> push per seed). Previous job (DECL-P4-26-A2 verso maps) finished at 01:24Z; nothing to stop.
2026-10-01T02:18:35Z p4v-02 env OK (villa 41701aa0eaa1aa765523db3f9f972b5830abf549)
2026-10-01T02:18:36Z p4v-02 s3 list: 0 organizer tifxyz segments
2026-10-01T02:20:42Z p4v-02 DECL-FL-2-E1 noted (orchestrator 02:16Z): DENSE arm withdrawn, OFFICIAL only (pipeline runs dense only if /work/fl2/dense/dense.env exists; it is never created). Env already OK: vc_build proxy port fixed locally the same way (build from a copy with the container's $HTTPS_PROXY port); vesuvius via pip --ignore-requires-python --no-deps, freeze minus vesuvius/torch lines, torch 2.14.0+cpu, imagecodecs in /opt/hv.
2026-10-01T02:20:48Z p4v-02 seeds: 48 candidate seeds; lane 0 takes k % 2 == 0
2026-10-01T02:21:58Z p4v-02 pherc0175a_p4v-02_s0 grow: rc=0 area=26.51811964065521 cm2 selfx=0 kept=true
2026-10-01T02:27:57Z p4v-02 pherc0175a_p4v-02_s0 render OK
2026-10-01T02:55:54Z p4v-02 pherc0175a_p4v-02_s0 infer official OK
2026-10-01T02:55:56Z p4v-02 pherc0175a_p4v-02_s0 tiles official: 8 tiles (area 26.51811964065521 cm2)
2026-10-01T02:57:06Z p4v-02 pherc0175a_p4v-02_s2 grow: rc=0 area=26.515914303220235 cm2 selfx=0 kept=true
2026-10-01T03:03:11Z p4v-02 pherc0175a_p4v-02_s2 render OK
2026-10-01T03:36:59Z p4v-02 pherc0175a_p4v-02_s2 infer official OK
2026-10-01T03:37:00Z p4v-02 pherc0175a_p4v-02_s2 tiles official: 8 tiles (area 26.515914303220235 cm2)
2026-10-01T03:38:23Z p4v-02 pherc0175a_p4v-02_s4 grow: rc=0 area=26.518757743832893 cm2 selfx=0 kept=true
2026-10-01T03:44:16Z p4v-02 pherc0175a_p4v-02_s4 render OK
2026-10-01T04:16:04Z p4v-02 pherc0175a_p4v-02_s4 infer official OK
2026-10-01T04:16:06Z p4v-02 pherc0175a_p4v-02_s4 tiles official: 8 tiles (area 26.518757743832893 cm2)
2026-10-01T04:17:21Z p4v-02 pherc0175a_p4v-02_s6 grow: rc=0 area=26.51649567052565 cm2 selfx=0 kept=true
2026-10-01T04:24:05Z p4v-02 pherc0175a_p4v-02_s6 render OK
2026-10-01T06:04:30Z p4v-02 container restart detected (uptime 0 min at 06:03Z; last unit s6 infer started 04:24Z, interrupted); /work and /opt intact, dockerd down; watchdog relaunched (pipeline re-runs setup_env.sh, resumes at s6 infer)
2026-10-01T06:06:19Z p4v-02 keepalive adopted (orchestrator 06:00Z): watchdog stopped (it was launched with a relative path that keepalive's pgrep would not match -> duplicate pipeline risk); keepalive relaunches it by absolute path; s6 infer restarts (resumable)
2026-10-01T06:43:37Z p4v-02 pherc0175a_p4v-02_s6 infer official OK
2026-10-01T06:43:45Z p4v-02 pherc0175a_p4v-02_s6 tiles official: 8 tiles (area 26.51649567052565 cm2)
2026-10-01T06:45:43Z p4v-02 pherc0175a_p4v-02_s8 grow: rc=0 area=26.514526486374272 cm2 selfx=0 kept=true
2026-10-01T06:52:34Z p4v-02 pherc0175a_p4v-02_s8 render OK
2026-10-01T07:33:22Z p4v-02 pherc0175a_p4v-02_s8 infer official OK
2026-10-01T07:33:25Z p4v-02 pherc0175a_p4v-02_s8 tiles official: 8 tiles (area 26.514526486374272 cm2)
2026-10-01T07:35:38Z p4v-02 pherc0175a_p4v-02_s10 grow: rc=0 area=26.543996968083643 cm2 selfx=0 kept=true
2026-10-01T07:42:19Z p4v-02 pherc0175a_p4v-02_s10 render OK
2026-10-01T08:22:34Z p4v-02 pherc0175a_p4v-02_s10 infer official OK
2026-10-01T08:22:36Z p4v-02 pherc0175a_p4v-02_s10 tiles official: 8 tiles (area 26.543996968083643 cm2)
2026-10-01T08:25:10Z p4v-02 pherc0175a_p4v-02_s12 grow: rc=0 area=23.775631814801198 cm2 selfx=0 kept=true
2026-10-01T08:31:13Z p4v-02 pherc0175a_p4v-02_s12 render OK
2026-10-01T09:03:31Z p4v-02 pherc0175a_p4v-02_s12 infer official OK
2026-10-01T09:03:33Z p4v-02 pherc0175a_p4v-02_s12 tiles official: 8 tiles (area 23.775631814801198 cm2)
2026-10-01T09:05:08Z p4v-02 pherc0175a_p4v-02_s14 grow: rc=0 area=26.515279925924197 cm2 selfx=0 kept=true
2026-10-01T09:12:46Z p4v-02 pherc0175a_p4v-02_s14 render OK
2026-10-01T09:59:11Z p4v-02 pherc0175a_p4v-02_s14 infer official OK
2026-10-01T09:59:14Z p4v-02 pherc0175a_p4v-02_s14 tiles official: 8 tiles (area 26.515279925924197 cm2)
2026-10-01T10:00:47Z p4v-02 pherc0175a_p4v-02_s16 grow: rc=0 area=26.514875603384212 cm2 selfx=0 kept=true
2026-10-01T10:08:55Z p4v-02 pherc0175a_p4v-02_s16 render OK
2026-10-01T10:58:37Z p4v-02 pherc0175a_p4v-02_s16 infer official OK
2026-10-01T10:58:39Z p4v-02 pherc0175a_p4v-02_s16 tiles official: 8 tiles (area 26.514875603384212 cm2)
2026-10-01T11:00:08Z p4v-02 pherc0175a_p4v-02_s18 grow: rc=0 area=24.07116028552581 cm2 selfx=0 kept=true
2026-10-01T11:06:47Z p4v-02 pherc0175a_p4v-02_s18 render OK
2026-10-01T11:47:51Z p4v-02 pherc0175a_p4v-02_s18 infer official OK
2026-10-01T11:47:53Z p4v-02 pherc0175a_p4v-02_s18 tiles official: 8 tiles (area 24.07116028552581 cm2)
2026-10-01T11:49:28Z p4v-02 pherc0175a_p4v-02_s20 grow: rc=0 area=26.514948962947102 cm2 selfx=0 kept=true
2026-10-01T11:56:38Z p4v-02 pherc0175a_p4v-02_s20 render OK
2026-10-01T12:41:54Z p4v-02 pherc0175a_p4v-02_s20 infer official OK
2026-10-01T12:41:56Z p4v-02 pherc0175a_p4v-02_s20 tiles official: 8 tiles (area 26.514948962947102 cm2)
2026-10-01T12:43:34Z p4v-02 pherc0175a_p4v-02_s22 grow: rc=0 area=26.51839055902985 cm2 selfx=0 kept=true
2026-10-01T12:50:51Z p4v-02 pherc0175a_p4v-02_s22 render OK
2026-10-01T13:26:28Z p4v-02 pherc0175a_p4v-02_s22 infer official OK
2026-10-01T13:26:30Z p4v-02 pherc0175a_p4v-02_s22 tiles official: 8 tiles (area 26.51839055902985 cm2)
2026-10-01T13:28:34Z p4v-02 pherc0175a_p4v-02_s24 grow: rc=0 area=26.547401728681294 cm2 selfx=0 kept=true
2026-10-01T13:35:18Z p4v-02 pherc0175a_p4v-02_s24 render OK
2026-10-01T14:16:35Z p4v-02 pherc0175a_p4v-02_s24 infer official OK
2026-10-01T14:16:38Z p4v-02 pherc0175a_p4v-02_s24 tiles official: 8 tiles (area 26.547401728681294 cm2)
2026-10-01T14:18:14Z p4v-02 pherc0175a_p4v-02_s26 grow: rc=0 area=26.515149006696458 cm2 selfx=0 kept=true
2026-10-01T14:26:05Z p4v-02 pherc0175a_p4v-02_s26 render OK
2026-10-01T15:03:52Z p4v-02 pherc0175a_p4v-02_s26 infer official OK
2026-10-01T15:03:54Z p4v-02 pherc0175a_p4v-02_s26 tiles official: 8 tiles (area 26.515149006696458 cm2)
2026-10-01T15:05:26Z p4v-02 pherc0175a_p4v-02_s28 grow: rc=0 area=26.514568395598957 cm2 selfx=0 kept=true
2026-10-01T15:13:56Z p4v-02 pherc0175a_p4v-02_s28 render OK
2026-10-01T16:05:34Z p4v-02 pherc0175a_p4v-02_s28 infer official OK
2026-10-01T16:05:38Z p4v-02 pherc0175a_p4v-02_s28 tiles official: 8 tiles (area 26.514568395598957 cm2)
2026-10-01T16:07:17Z p4v-02 pherc0175a_p4v-02_s30 grow: rc=0 area=26.51502874400607 cm2 selfx=0 kept=true
2026-10-01T16:14:43Z p4v-02 pherc0175a_p4v-02_s30 render OK
2026-10-01T16:53:54Z p4v-02 pherc0175a_p4v-02_s30 infer official OK
2026-10-01T16:53:56Z p4v-02 pherc0175a_p4v-02_s30 tiles official: 8 tiles (area 26.51502874400607 cm2)
2026-10-01T16:55:50Z p4v-02 pherc0175a_p4v-02_s32 grow: rc=0 area=26.516634919277934 cm2 selfx=0 kept=true
2026-10-01T17:03:39Z p4v-02 pherc0175a_p4v-02_s32 render OK
