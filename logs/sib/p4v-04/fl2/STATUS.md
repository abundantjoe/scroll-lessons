# p4v-04 FL2 STATUS: PHerc0343 primary (seed lane 0), RULES.md DECL-FL-2 (7a315a65)
Provenance: Project HERCULES | [id removed]
Brief tools/fl2/BRIEF_FL2.md sha256 0e07b757bafd383c24b3e426a60be95d34690057d7c6117e9f4264e9691142a0 (verified); logs/fl2/assign.json sha256 ffb22500... (verified; scrolls.PHerc0343 = {volume 20250521140437, primary p4v-04, second none}).
Template fl-pherc0257 @54b29c9661afac1e661211175bf2bbd816f21cce -> tools/sib/p4v-04/fl2/ (pipeline.sh, fl.py, watchdog.sh, + annotate.py).
Inputs: CT s3://.../PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr (L0 17998x8595x8595, u8); surface 20250521140437-surface-20260413222639-surface-m7-L0-th0.2.zarr (same L0 shape). Bucket: no organizer tifxyz segments, no umbilicus (UMB=none: CT-mask centroid axis, template rule).
Deviations from the template, disclosed (all parameters/bookkeeping; grow, self-intersection gate, render, infer and tiling commands unchanged):
- D1 voxel size 8.640 um (this volume) instead of the template's hardcoded 9.362: fl.py VOX_UM via env FL_VOX_UM, grow "voxelsize", render --voxel-size. Effect: 2 x 2 cm tile = 2315 src px (template 2136), px_per_mm and area_cm2 correct for this scan. The official ink_9um model is applied to 8.64 um data without rescaling (no resampling step exists in the template; ~8% finer than 9.362).
- D2 48 candidate seeds: template fl.py seeds has a fixed 8-ray plan, so "seeds ... 48" would cap at 8. The plan keeps the 8 template rays first, unchanged, and appends 40 rays on the same rule (z fractions 0.25/0.42/0.57/0.72/0.85 x azimuths 22.5+45k). Result: 48 of 48 rays gave a seed; lane 0 takes indices 0,2,...,46 (24 seeds <= NSEEDS 40).
- D3 order: each kept segment goes render -> infer -> tile -> push right after its grow (brief item 6), instead of the template's grow-all-then-render.
- D4 outputs per brief item 5: <SEG>/tiles_official/<SEG>_<forward|reverse>_rRR_cCC.png (forward = <SEG>.tif, reverse = <SEG>_reverse.tif from infer --direction both); manifest rows gain scroll, volume, model, model_sha256, segment_area_cm2 (annotate.py); <SEG>/tifxyz/ + tifxyz_sha256.txt.
- D5 environment: docker/env/vc_build.sh hardcodes proxy port 46883; this container's proxy is 35979, so the build ran from a port-substituted copy (/work/fl2/vc_build_port.sh, only that line differs). Repo env scripts unchanged.
- D6 seeds.json computed with the same fl.py command in a scratch venv (numpy/requests/numcodecs) while the build ran; the pipeline skips its seeds unit when seeds.json exists.
- DENSE arm: off until logs/sib/fl-pherc0257/fl2/DENSE_OK.json exists on the pilot branch; then run on every segment per its instructions.
2026-10-01T02:26:29Z START: seeds 48/48 (lane 0: 24)
2026-10-01T02:27:39Z UPDATE (orchestrator 02:19Z; DECL-FL-2-E1 verified in RULES.md @9c280796): DENSE arm withdrawn -> pipeline is OFFICIAL only (PIPELINE_DONE after the official pass). docker/env/setup_env.sh + vc_build.sh taken from origin/claude/gifted-bell-gavnl5 @9c280796 (proxy from $HTTPS_PROXY; hv-ink freeze fix; pip --ignore-requires-python for vesuvius; imagecodecs). D5 is now moot for the remaining setup (the build already in flight used the port-substituted copy, identical apart from the port). Voxel size checked against the volume's metadata.json: scan.tomo.acquisition.detector.samplePixelSize = 0.00864 mm = 8.640 um (= D1 value).
2026-10-01T02:28:42Z env OK
2026-10-01T02:28:43Z s3 list: 0 organizer tifxyz segments
2026-10-01T02:29:50Z grow pherc0343_p4v-04_s0: rc=0 area_cm2=26.51539936238492 selfx=0 kept=true
2026-10-01T03:07:21Z tiles pherc0343_p4v-04_s0 official: 8 tiles ( 4 fwd / 4 rev )
2026-10-01T03:08:29Z grow pherc0343_p4v-04_s2: rc=0 area_cm2=26.514679242994042 selfx=0 kept=true
2026-10-01T03:42:30Z tiles pherc0343_p4v-04_s2 official: 8 tiles ( 4 fwd / 4 rev )
2026-10-01T03:43:44Z grow pherc0343_p4v-04_s4: rc=0 area_cm2=26.515501400654422 selfx=0 kept=true
2026-10-01T04:13:35Z tiles pherc0343_p4v-04_s4 official: 8 tiles ( 4 fwd / 4 rev )
2026-10-01T04:15:49Z grow pherc0343_p4v-04_s6: rc=0 area_cm2=26.66402917614304 selfx=0 kept=true
2026-10-01T06:04:51Z container restart ~06:04Z interrupted render of s6 (docker down); watchdog relaunched (pipeline re-runs setup_env, resumes from markers)
2026-10-01T06:49:45Z tiles pherc0343_p4v-04_s6 official: 8 tiles ( 4 fwd / 4 rev )
2026-10-01T06:50:57Z grow pherc0343_p4v-04_s8: rc=0 area_cm2=26.51644573258451 selfx=0 kept=true
2026-10-01T07:25:55Z tiles pherc0343_p4v-04_s8 official: 8 tiles ( 4 fwd / 4 rev )
2026-10-01T07:27:08Z grow pherc0343_p4v-04_s10: rc=0 area_cm2=26.514952738359412 selfx=0 kept=true
2026-10-01T08:09:28Z tiles pherc0343_p4v-04_s10 official: 8 tiles ( 4 fwd / 4 rev )
2026-10-01T17:21:02Z STOP: FL-2 compute on PHerc0343 stopped by DECL-FL-4-A1 (owner order: whole fleet on PHerc0268/PHerc0490A inner windings); p4v-04 -> PHerc0490A lane 6/16. Segments with tiles pushed: 6
