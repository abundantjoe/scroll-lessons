2026-10-01T02:13:57Z fl-pherc0306b PHerc0306B FL2 primary (lane 0) START: template fl-pherc0257@54b29c96 parameters only (8.64 um, 48-seed plan, NSEEDS 40, MIN_AREA 16, 0 selfx), official model e635558a; DENSE when DENSE_OK.json appears
2026-10-01T02:18:05Z grow pherc0306b_fl-pherc0306b_s0: area=26.51437506763865 cm2 selfx=0 kept=true
2026-10-01T02:19:15Z grow pherc0306b_fl-pherc0306b_s2: area=26.514958513518724 cm2 selfx=0 kept=true
2026-10-01T02:20:24Z grow pherc0306b_fl-pherc0306b_s4: area=26.513249881283407 cm2 selfx=0 kept=true
2026-10-01T02:21:32Z grow pherc0306b_fl-pherc0306b_s6: area=26.515666197260174 cm2 selfx=0 kept=true
2026-10-01T02:22:38Z grow pherc0306b_fl-pherc0306b_s8: area=26.51565371214201 cm2 selfx=0 kept=true
2026-10-01T02:23:36Z grow pherc0306b_fl-pherc0306b_s10: area=21.427095074935263 cm2 selfx=0 kept=true
2026-10-01T02:24:44Z grow pherc0306b_fl-pherc0306b_s12: area=26.513673165836188 cm2 selfx=0 kept=true
2026-10-01T02:25:42Z HOLD (data quality): grown segments do not follow the surface prediction (SURFACE_CHECK.json: on-mesh support = off-sheet support); their tiles should not enter the census. Fix proposed: normal_grid_path in grow params.
2026-10-01T02:25:59Z grow pherc0306b_fl-pherc0306b_s14: area=26.515837660182157 cm2 selfx=0 kept=true
2026-10-01T02:27:11Z grow pherc0306b_fl-pherc0306b_s16: area=26.51844743635584 cm2 selfx=0 kept=true
2026-10-01T02:28:16Z grow pherc0306b_fl-pherc0306b_s18: area=26.514408512066172 cm2 selfx=0 kept=true
2026-10-01T02:29:27Z grow pherc0306b_fl-pherc0306b_s20: area=26.51506119479531 cm2 selfx=0 kept=true
2026-10-01T02:30:23Z grow pherc0306b_fl-pherc0306b_s22: area=22.40165571112339 cm2 selfx=0 kept=true
2026-10-01T02:31:42Z grow pherc0306b_fl-pherc0306b_s24: area=26.523553241229557 cm2 selfx=0 kept=true
2026-10-01T02:32:52Z grow pherc0306b_fl-pherc0306b_s26: area=26.515660709505077 cm2 selfx=0 kept=true
2026-10-01T02:34:00Z grow pherc0306b_fl-pherc0306b_s28: area=26.515413687916126 cm2 selfx=0 kept=true
2026-10-01T02:35:29Z grow pherc0306b_fl-pherc0306b_s30: area=26.542065215692602 cm2 selfx=0 kept=true
2026-10-01T02:36:37Z grow pherc0306b_fl-pherc0306b_s32: area=26.513932485697644 cm2 selfx=0 kept=true
2026-10-01T02:37:47Z grow pherc0306b_fl-pherc0306b_s34: area=26.514528967382613 cm2 selfx=0 kept=true
2026-10-01T02:38:58Z grow pherc0306b_fl-pherc0306b_s36: area=26.516488405160175 cm2 selfx=0 kept=true
2026-10-01T02:39:58Z grow pherc0306b_fl-pherc0306b_s38: area=23.72332249200517 cm2 selfx=0 kept=true
2026-10-01T02:41:07Z grow pherc0306b_fl-pherc0306b_s40: area=26.51464457295849 cm2 selfx=0 kept=true
2026-10-01T02:42:12Z grow pherc0306b_fl-pherc0306b_s42: area=26.514818009442486 cm2 selfx=0 kept=true
2026-10-01T02:43:34Z grow pherc0306b_fl-pherc0306b_s44: area=26.52796209909611 cm2 selfx=0 kept=true
2026-10-01T02:44:43Z grow pherc0306b_fl-pherc0306b_s46: area=26.159133158715676 cm2 selfx=0 kept=true
2026-10-01T03:27:48Z pherc0306b_fl-pherc0306b_s0: official tiles pushed (8)
2026-10-01T04:05:04Z pherc0306b_fl-pherc0306b_s2: official tiles pushed (8)
2026-10-01T06:02:50Z HOLD continues: pipeline stopped by container restart after pushing official tiles of s0 and s2 (16 PNGs); these come from segments that fail SURFACE_CHECK and must not enter the census. Not relaunched: grows s0-s46 (24, all 'kept') share the defect; awaiting decision on normal_grid_path.
2026-10-01T06:04:18Z r2 launched under orchestrator 06:00Z order: normal_grid_path (organizer normal grids) + support gate (f0>=0.5 and f0>=1.5x off-sheet; rejects old s0: f0 0.20 vs 0.27); r1 segments s0-s46 and their 16 pushed tiles stay excluded
2026-10-01T08:27:04Z grow pherc0306b_fl-pherc0306b_r2_s0: area=34.57470748236932 cm2 selfx=240488 kept=false
2026-10-01T10:05:14Z r2_s0 (normal grids): 8524 s, 34.6 cm2, 240488 transverse self-intersections, support f0 0.20 vs off-sheet 0.23: NOT kept. Normal grids alone do not make the grow follow the sheet on this prediction; r2 continues seed by seed under the gate.
2026-10-01T11:03:48Z grow pherc0306b_fl-pherc0306b_r2_s2: area=27.568720586546597 cm2 selfx=22027 kept=false
2026-10-01T14:28:12Z grow pherc0306b_fl-pherc0306b_r2_s4: area=33.01428619352787 cm2 selfx=82109 kept=false
2026-10-01T17:21:31Z FL-2 PHerc0306B stopped by DECL-FL-4-A1 (r2: 3/3 rejected, 0 tiles kept)
