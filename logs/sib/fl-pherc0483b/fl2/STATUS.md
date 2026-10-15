2026-10-01T02:12:18Z fl-pherc0483b fl2: START (DECL-FL-2, brief 0e07b757..., assign.json ffb22500...: PHerc0483B primary, seed lane 0, no second). Template fl-pherc0257 @54b29c96 copied to tools/sib/fl-pherc0483b/fl2/; parameter changes only, disclosed: (1) voxel size 8.64 um (grow voxelsize, render --voxel-size, fl.py FL_VOX_UM; template value 9.362 is another protocol); (2) fl.py seeds plan extended from 8 to 48 positions (the template's 8 first, then 5 z fractions x 8 azimuths offset 22.5 deg), because the template plan caps at 8; (3) no second worker for this scroll, so after the even (lane 0) seed indices the odd ones follow, max 40 grow attempts; (4) grow-render-infer-tile per seed in turn (brief item 6) instead of all grows first; (5) tiles_<model>/ dirs, file names <SEG>_<forward|reverse>_rRR_cCC.png and manifest fields per brief item 5. Gate (16 cm2, 0 transverse self-intersections), tiler, render and infer options unchanged.
2026-10-01T02:12:18Z fl-pherc0483b fl2: environment fix: docker/env/vc_build.sh hard-coded the build container's proxy as 127.0.0.1:46883; this container's proxy is on another port, so CMake could not fetch vc-delta3d (cause of the DECL-FL-1 setup failure here on 2026-09-30 03:51Z). vc_build.sh now takes $HTTPS_PROXY (as setup_env.sh already does). Build restarted 02:20Z.
2026-10-01T02:15:16Z fl-pherc0483b fl2: env FAILED: vesuvius infer not importable
2026-10-01T02:20:22Z fl-pherc0483b fl2: env FAILED: vesuvius infer not importable
2026-10-01T02:21:18Z fl-pherc0483b fl2: env: took origin/claude/gifted-bell-gavnl5 docker/env/setup_env.sh and vc_build.sh (7168f33, 21bf4bd); setup_env still stopped at the editable vesuvius install (villa vesuvius 0.2.4 requires Python >=3.14; venv is 3.13.12) and uv venv has no ensurepip; fixed per brief item 3: uv pip install pip, then pip install --ignore-requires-python --no-deps -e /work/villa/vesuvius, then the cleaned freeze. vesuvius infer importable; torch 2.14.1+cpu (pilot env.txt: 2.14.0+cpu, no longer offered). setup_env OK 02:33Z. DENSE arm withdrawn (DECL-FL-2-E1): official model only; /work/fl2/dense.env will not be created.
2026-10-01T02:25:41Z fl-pherc0483b fl2: env OK (villa 41701aa0eaa1aa765523db3f9f972b5830abf549 ckpt_sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab torch 2.14.1+cpu python 3.13.12 )
2026-10-01T02:27:49Z fl-pherc0483b fl2: seeds: 48 of 48 candidate positions gave a seed
2026-10-01T02:29:52Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s0 (seed 0): rc 0, area 26.616634930080966 cm2, self-intersections 0, kept true
2026-10-01T02:58:26Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s0 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.616634930080966 cm2
2026-10-01T02:59:16Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s2 (seed 2): rc 0, area 19.849445181168136 cm2, self-intersections 0, kept true
2026-10-01T03:25:56Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s2 official: 8 tiles kept (forward 4 , reverse 4 ), area 19.849445181168136 cm2
2026-10-01T03:27:01Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s4 (seed 4): rc 0, area 26.513386612378987 cm2, self-intersections 0, kept true
2026-10-01T03:53:49Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s4 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.513386612378987 cm2
2026-10-01T03:54:54Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s6 (seed 6): rc 0, area 26.51421527407995 cm2, self-intersections 0, kept true
2026-10-01T06:03:07Z fl-pherc0483b fl2: container restarted ~06:02Z during the s6 official inference (started 04:00Z); /work survived. Restarting the watchdog: the pipeline re-runs setup_env when docker is down and redoes the s6 inference (no partial state used). Also removed an untracked 2/ dir in the repo root: a byte-identical copy of segment s0's tifxyz written at 02:29Z (x.tif sha256 38e859c2... = the pushed s0 tifxyz); moved to /work/fl2/stray, not committed. So far: s0, s2, s4 tiled, 8 official tiles each (4 forward + 4 reverse); areas 26.62, 19.85, 26.51 cm2; s6 grown (26.51 cm2).
2026-10-01T06:04:06Z fl-pherc0483b fl2: keepalive (owner zero-turn order): tools/fl2/keepalive.sh run with WD=tools/sib/fl-pherc0483b/fl2/watchdog.sh (relative path, matching the running watchdog's command line, so no second watchdog starts) and DONE=/work/fl2/state/pass.done (this pipeline's end-of-pass marker; it writes no PIPELINE_DONE). Manifest rows already carry model official + model_sha256 e635558a.
2026-10-01T06:27:28Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s6 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.51421527407995 cm2
2026-10-01T06:28:57Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s8 (seed 8): rc 0, area 26.515491398902636 cm2, self-intersections 0, kept true
2026-10-01T06:54:13Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s8 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.515491398902636 cm2
2026-10-01T06:55:52Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s10 (seed 10): rc 0, area 26.5738992192277 cm2, self-intersections 0, kept true
2026-10-01T07:23:51Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s10 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.5738992192277 cm2
2026-10-01T07:25:17Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s12 (seed 12): rc 0, area 26.55382835087217 cm2, self-intersections 0, kept true
2026-10-01T07:54:02Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s12 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.55382835087217 cm2
2026-10-01T07:55:25Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s14 (seed 14): rc 0, area 26.519742420440956 cm2, self-intersections 0, kept true
2026-10-01T08:26:32Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s14 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.519742420440956 cm2
2026-10-01T08:28:01Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s16 (seed 16): rc 0, area 26.537485687726956 cm2, self-intersections 0, kept true
2026-10-01T09:06:00Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s16 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.537485687726956 cm2
2026-10-01T09:07:17Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s18 (seed 18): rc 0, area 26.51976947767225 cm2, self-intersections 0, kept true
2026-10-01T09:38:13Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s18 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.51976947767225 cm2
2026-10-01T09:39:10Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s20 (seed 20): rc 0, area 20.156720349891046 cm2, self-intersections 0, kept true
2026-10-01T10:09:17Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s20 official: 8 tiles kept (forward 4 , reverse 4 ), area 20.156720349891046 cm2
2026-10-01T10:10:27Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s22 (seed 22): rc 0, area 26.515194901530112 cm2, self-intersections 0, kept true
2026-10-01T10:44:09Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s22 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.515194901530112 cm2
2026-10-01T10:45:15Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s24 (seed 24): rc 0, area 26.51469531564244 cm2, self-intersections 0, kept true
2026-10-01T11:16:26Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s24 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.51469531564244 cm2
2026-10-01T11:17:45Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s26 (seed 26): rc 0, area 26.526379455695054 cm2, self-intersections 0, kept true
2026-10-01T11:51:16Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s26 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.526379455695054 cm2
2026-10-01T11:52:19Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s28 (seed 28): rc 0, area 19.85706942702253 cm2, self-intersections 0, kept true
2026-10-01T12:18:58Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s28 official: 8 tiles kept (forward 4 , reverse 4 ), area 19.85706942702253 cm2
2026-10-01T12:20:12Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s30 (seed 30): rc 0, area 26.514470115396303 cm2, self-intersections 0, kept true
2026-10-01T13:00:09Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s30 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.514470115396303 cm2
2026-10-01T13:01:25Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s32 (seed 32): rc 0, area 26.515874729753214 cm2, self-intersections 0, kept true
2026-10-01T13:35:48Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s32 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.515874729753214 cm2
2026-10-01T13:37:38Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s34 (seed 34): rc 0, area 26.569644181479003 cm2, self-intersections 0, kept true
2026-10-01T14:11:10Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s34 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.569644181479003 cm2
2026-10-01T14:12:27Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s36 (seed 36): rc 0, area 26.51886832103753 cm2, self-intersections 0, kept true
2026-10-01T14:50:27Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s36 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.51886832103753 cm2
2026-10-01T14:51:38Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s38 (seed 38): rc 0, area 25.451480672397842 cm2, self-intersections 0, kept true
2026-10-01T15:27:52Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s38 official: 8 tiles kept (forward 4 , reverse 4 ), area 25.451480672397842 cm2
2026-10-01T15:29:02Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s40 (seed 40): rc 0, area 26.51525908757463 cm2, self-intersections 0, kept true
2026-10-01T16:00:40Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s40 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.51525908757463 cm2
2026-10-01T16:01:42Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s42 (seed 42): rc 0, area 26.51439333665935 cm2, self-intersections 0, kept true
2026-10-01T16:32:38Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s42 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.51439333665935 cm2
2026-10-01T16:34:03Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s44 (seed 44): rc 0, area 26.531076621301942 cm2, self-intersections 0, kept true
2026-10-01T17:09:08Z fl-pherc0483b fl2: pherc0483b_fl-pherc0483b_s44 official: 8 tiles kept (forward 4 , reverse 4 ), area 26.531076621301942 cm2
2026-10-01T17:10:05Z fl-pherc0483b fl2: grow pherc0483b_fl-pherc0483b_s46 (seed 46): rc 0, area 24.40760955300674 cm2, self-intersections 0, kept true
