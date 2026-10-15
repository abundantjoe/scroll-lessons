# p4v-09 fl2 STATUS (RULES.md DECL-FL-2 + E1; tools/fl2/BRIEF_FL2.md 0e07b757)
PHerc1218 primary (seed lane 0), volume 20250521120456-8.640um-1.2m-116keV-masked.zarr; surface 20250521120456-surface-20260413222639-surface-m7-L0-th0.2.zarr; UMB none; no organizer tifxyz (bucket 2026-10-01). assign.json ffb22500.
Code: template fl-pherc0257 @54b29c96 via the pilot's fl2 copy @fc6dd108; parameters only (VOX 8.640, scroll/volume/paths/names, lane 0, NSEEDS 40, MIN_AREA 16, 48 seeds); render/infer/tiles run per segment right after its grow. OFFICIAL model only (E1: DENSE withdrawn), ckpt sha e635558a.
fl.py 2b89c14410a4b6f7; pipeline.sh 0c5db5cb79d28c1d; watchdog.sh fa85fe6a92dbebe3
2026-10-01T02:15:28Z start (verso job p4v-09 finished and pushed at 2fc3a85f; no old lanes running)
2026-10-01T02:21:47Z env: setup_env.sh + fixes (environment only, no pipeline change): vc_build.sh run from a /work copy with this container's proxy (repo copy hard-codes 127.0.0.1:46883; 7 apps built at villa 41701aa0); vesuvius via pip --ignore-requires-python -e (Py 3.13); hv-ink-freeze.txt installed minus its -e git+ vesuvius line, torch 2.14.0+cpu/torchvision 0.29.0+cpu from the PyTorch CPU index; imagecodecs in /opt/hv; ckpt e635558a verified
2026-10-01T02:24:34Z pherc1218_p4v-09_s0 grow: rc=0 area=26.51457080821179 cm2 selfx=0 kept=true
2026-10-01T02:49:09Z pherc1218_p4v-09_s0 official tiles: 8 (both directions)
2026-10-01T02:50:12Z pherc1218_p4v-09_s2 grow: rc=0 area=24.40959417215827 cm2 selfx=0 kept=true
2026-10-01T03:11:48Z pherc1218_p4v-09_s2 official tiles: 8 (both directions)
2026-10-01T03:12:53Z pherc1218_p4v-09_s4 grow: rc=0 area=26.514824708546694 cm2 selfx=0 kept=true
2026-10-01T03:39:41Z pherc1218_p4v-09_s4 official tiles: 8 (both directions)
2026-10-01T03:40:50Z pherc1218_p4v-09_s6 grow: rc=0 area=26.51458975882959 cm2 selfx=0 kept=true
2026-10-01T04:12:44Z pherc1218_p4v-09_s6 official tiles: 8 (both directions)
2026-10-01T04:13:49Z pherc1218_p4v-09_s8 grow: rc=0 area=26.514459025802193 cm2 selfx=0 kept=true
2026-10-01T06:05:06Z note: an untracked repo-root dir '2/' (x.tif sha f348e3a6, = pushed pherc1218_p4v-09_s0 tifxyz) written at s0 render start 02:24:36 was moved out of the repo to /work/fl2/stray/; nothing else changed. Segments s0-s8 hit the template generation cap (302x302 grid, ~26.5 cm2; s2 290x290); seeds and x.tif sha256 all distinct.
2026-10-01T06:05:49Z container restarted (up since 06:04:10Z); processes lost during s8 infer (started 04:18:52Z, no output); /work intact; watchdog relaunched (resumes: s8 render marker kept, s8 infer re-run)
2026-10-01T06:07:44Z keepalive armed with WD=tools/sib/p4v-09/fl2/watchdog.sh (relative, matching the running watchdog's command line so pgrep does not double-launch; quoted so the harness wrapper's own command line cannot self-match); manifests already carry model official + model_sha256 e635558a
2026-10-01T06:21:20Z pherc1218_p4v-09_s8 official tiles: 8 (both directions)
2026-10-01T06:22:44Z pherc1218_p4v-09_s10 grow: rc=0 area=26.51429731493683 cm2 selfx=0 kept=true
2026-10-01T06:48:21Z pherc1218_p4v-09_s10 official tiles: 8 (both directions)
2026-10-01T06:49:13Z pherc1218_p4v-09_s12 grow: rc=0 area=20.78175534896942 cm2 selfx=0 kept=true
2026-10-01T07:10:05Z pherc1218_p4v-09_s12 official tiles: 8 (both directions)
2026-10-01T07:11:05Z pherc1218_p4v-09_s14 grow: rc=0 area=26.514613158799424 cm2 selfx=548 kept=false
2026-10-01T07:12:08Z pherc1218_p4v-09_s16 grow: rc=0 area=26.520211485402776 cm2 selfx=0 kept=true
2026-10-01T07:33:35Z pherc1218_p4v-09_s16 official tiles: 8 (both directions)
2026-10-01T07:34:34Z pherc1218_p4v-09_s18 grow: rc=0 area=26.515060772688077 cm2 selfx=0 kept=true
2026-10-01T08:00:13Z pherc1218_p4v-09_s18 official tiles: 8 (both directions)
2026-10-01T08:01:12Z pherc1218_p4v-09_s20 grow: rc=0 area=26.51390687900063 cm2 selfx=0 kept=true
2026-10-01T08:27:19Z pherc1218_p4v-09_s20 official tiles: 8 (both directions)
2026-10-01T08:28:22Z pherc1218_p4v-09_s22 grow: rc=0 area=26.514440439172297 cm2 selfx=0 kept=true
2026-10-01T08:52:26Z pherc1218_p4v-09_s22 official tiles: 8 (both directions)
2026-10-01T08:53:26Z pherc1218_p4v-09_s24 grow: rc=0 area=26.513973865174943 cm2 selfx=0 kept=true
2026-10-01T09:10:57Z pherc1218_p4v-09_s24 official tiles: 8 (both directions)
2026-10-01T09:11:57Z pherc1218_p4v-09_s26 grow: rc=0 area=26.516887105265994 cm2 selfx=0 kept=true
2026-10-01T09:34:22Z pherc1218_p4v-09_s26 official tiles: 8 (both directions)
2026-10-01T09:35:39Z pherc1218_p4v-09_s28 grow: rc=0 area=26.525912217637902 cm2 selfx=0 kept=true
2026-10-01T10:02:39Z pherc1218_p4v-09_s28 official tiles: 8 (both directions)
2026-10-01T10:03:41Z pherc1218_p4v-09_s30 grow: rc=0 area=26.515792065567535 cm2 selfx=0 kept=true
2026-10-01T10:22:50Z pherc1218_p4v-09_s30 official tiles: 8 (both directions)
2026-10-01T10:24:18Z pherc1218_p4v-09_s32 grow: rc=0 area=26.546002618554763 cm2 selfx=0 kept=true
2026-10-01T10:43:29Z pherc1218_p4v-09_s32 official tiles: 8 (both directions)
2026-10-01T10:44:30Z pherc1218_p4v-09_s34 grow: rc=0 area=26.514474900610942 cm2 selfx=0 kept=true
2026-10-01T11:06:34Z pherc1218_p4v-09_s34 official tiles: 8 (both directions)
2026-10-01T11:07:34Z pherc1218_p4v-09_s36 grow: rc=0 area=26.51525786390682 cm2 selfx=0 kept=true
2026-10-01T11:26:26Z pherc1218_p4v-09_s36 official tiles: 8 (both directions)
2026-10-01T11:27:30Z pherc1218_p4v-09_s38 grow: rc=0 area=26.513539697558674 cm2 selfx=0 kept=true
2026-10-01T11:46:03Z pherc1218_p4v-09_s38 official tiles: 8 (both directions)
2026-10-01T11:47:03Z pherc1218_p4v-09_s40 grow: rc=0 area=26.51552969379954 cm2 selfx=0 kept=true
2026-10-01T12:07:21Z pherc1218_p4v-09_s40 official tiles: 8 (both directions)
2026-10-01T12:08:23Z pherc1218_p4v-09_s42 grow: rc=0 area=26.51598645559918 cm2 selfx=0 kept=true
2026-10-01T12:27:22Z pherc1218_p4v-09_s42 official tiles: 8 (both directions)
2026-10-01T12:28:29Z pherc1218_p4v-09_s44 grow: rc=0 area=26.515728382077338 cm2 selfx=0 kept=true
2026-10-01T12:52:21Z pherc1218_p4v-09_s44 official tiles: 8 (both directions)
2026-10-01T12:53:23Z pherc1218_p4v-09_s46 grow: rc=0 area=26.516327395868824 cm2 selfx=0 kept=true
2026-10-01T13:18:01Z pherc1218_p4v-09_s46 official tiles: 8 (both directions)
2026-10-01T13:22:07Z round 0 complete: 24 lane-0 seeds tried, 23 kept (s14 rejected: 548 self-intersections), 184 official tiles. Seed list extended (orchestrator 06:00Z step 2): fl.py FL_ROUND=1 plan = 7 heights (0.16-0.88, step 0.12) x 8 azimuths (45 deg), no round-0 position repeated; round 1 = seeds_r1.json, names pherc1218_p4v-09_r1s<k>, lane rule k%2==0, NSEEDS 40->80; model, inference options and tiler unchanged; PIPELINE_DONE removed. fl.py 4d716389e81e9657 pipeline.sh ab68df0e8b808191
2026-10-01T13:24:56Z pherc1218_p4v-09_r1s0 grow: rc=0 area=26.515194319769403 cm2 selfx=0 kept=true
2026-10-01T13:48:05Z pherc1218_p4v-09_r1s0 official tiles: 8 (both directions)
2026-10-01T13:49:06Z pherc1218_p4v-09_r1s2 grow: rc=0 area=26.514228357263345 cm2 selfx=0 kept=true
2026-10-01T14:09:53Z pherc1218_p4v-09_r1s2 official tiles: 8 (both directions)
2026-10-01T14:10:25Z pherc1218_p4v-09_r1s4 grow: rc=0 area=11.196846013199904 cm2 selfx=0 kept=false
2026-10-01T14:11:29Z pherc1218_p4v-09_r1s6 grow: rc=0 area=26.515197442287974 cm2 selfx=0 kept=true
2026-10-01T14:40:58Z pherc1218_p4v-09_r1s6 official tiles: 8 (both directions)
2026-10-01T14:41:58Z pherc1218_p4v-09_r1s8 grow: rc=0 area=26.514986930756898 cm2 selfx=0 kept=true
2026-10-01T15:06:08Z pherc1218_p4v-09_r1s8 official tiles: 8 (both directions)
2026-10-01T15:07:09Z pherc1218_p4v-09_r1s10 grow: rc=0 area=26.51531682109504 cm2 selfx=0 kept=true
2026-10-01T15:32:59Z pherc1218_p4v-09_r1s10 official tiles: 8 (both directions)
2026-10-01T15:33:51Z pherc1218_p4v-09_r1s12 grow: rc=0 area=20.788914780383653 cm2 selfx=0 kept=true
2026-10-01T15:56:28Z pherc1218_p4v-09_r1s12 official tiles: 8 (both directions)
2026-10-01T15:57:38Z pherc1218_p4v-09_r1s14 grow: rc=0 area=26.517400838837418 cm2 selfx=0 kept=true
2026-10-01T16:23:06Z pherc1218_p4v-09_r1s14 official tiles: 8 (both directions)
2026-10-01T16:24:03Z pherc1218_p4v-09_r1s16 grow: rc=0 area=26.51383438790912 cm2 selfx=0 kept=true
2026-10-01T16:47:07Z pherc1218_p4v-09_r1s16 official tiles: 8 (both directions)
2026-10-01T16:48:08Z pherc1218_p4v-09_r1s18 grow: rc=0 area=26.51595057236852 cm2 selfx=0 kept=true
2026-10-01T17:13:09Z pherc1218_p4v-09_r1s18 official tiles: 8 (both directions)
2026-10-01T17:14:03Z pherc1218_p4v-09_r1s20 grow: rc=0 area=23.061307330418344 cm2 selfx=0 kept=true
2026-10-01T17:24:42Z FL-2 compute stopped by DECL-FL-4-A1 (orchestrator order 17:24Z; fleet moves to PHerc0268/PHerc0490A). Pushed at stop: round 0 23 segments + round 1 segments with DONE, 8 official tiles each; the in-progress unit was abandoned (not pushed).
