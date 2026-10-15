2026-10-01T02:14:49Z fl-pherc0211: FL2 start (DECL-FL-2), PHerc0211 primary seed lane 0; template fl-pherc0257 54b29c96 (parameters only + item-5 tile names/manifest fields); 48 seeds (12 heights x 4 azimuths), even indices, NSEEDS 40, MIN_AREA 16 cm2, 0 self-x; env fix: vesuvius pip --ignore-requires-python on py3.13 (+ freeze deps without the git editable line); official ckpt e635558a...9cab verified
2026-10-01T02:40Z fl-pherc0211: GEOMETRY WARNING (numbers only, unresolved): all kept auto-grown segments pass the declared gate (0 self-x, >= 16 cm2) but every one spans ~50-56 x 51-56 mm in x-y (z 9-37 mm), i.e. nearly the full scroll cross-section (~74 mm), and s0/s2/s6 have vertices outside the volume (x up to 8014 > 7948, x down to -21). On the masked CT (level 3, 400 random valid vertices each) only 0.29 (s0), 0.35 (s2), 0.32 (s4), 0.36 (s6), 0.37 (s8), 0.65 (s10) of vertices sit on nonzero voxels. Either the meshes leave the papyrus / cross windings, or inter-winding air reads 0 in the masked u8 volume; this check cannot tell which. Self-intersection is not a sheet-fidelity test. Proposed validation before any read is trusted: per-segment winding-consistency (radius from the umbilicus vs unrolled u, monotonic per winding; no jumps > half the inter-sheet pitch) and fraction of vertices on the surface-prediction mask (should be ~1 for a traced sheet). Pipeline continues under the declared gate.
2026-10-01T02:50Z fl-pherc0211: GEOMETRY CHECK 2 (numbers only): fraction of 150 random valid vertices on the organizer surface prediction (surface-m7 L0-th0.2, read at level 2): on-voxel / within 1 level-2 voxel (~37 um, ~4 vox): s0 0.15/0.33, s2 0.22/0.37, s10 0.23/0.60, s12 0.13/0.39. A traced sheet should be near 1 within ~4 vox. Caveat: level 2 is a downsampled pyramid level (thin sheets can vanish there), so this under-counts; a level-0 check is the definitive version. Reading: most of each auto-grown mesh is probably NOT on a predicted papyrus surface (wandering / winding jumps), so its tiles are unlikely to show text even if ink is present. Recommendation to the orchestrator: weight PHerc0211 auto-grown tiles low in the census, or add a fidelity gate (>= 0.8 of vertices within 4 vox of the level-0 surface prediction) via a declaration. Pipeline continues under the declared gate meanwhile (compute only).
2026-10-01T03:05:49Z pherc0211_fl-pherc0211_s0: official tiles 8 pushed
2026-10-01T03:25:08Z pherc0211_fl-pherc0211_s2: official tiles 8 pushed
2026-10-01T03:47:14Z pherc0211_fl-pherc0211_s4: official tiles 8 pushed
2026-10-01T04:08:42Z pherc0211_fl-pherc0211_s6: official tiles 8 pushed
2026-10-01T06:02:59Z fl-pherc0211: container restart ~06:02Z killed the pipeline during infer s8; watchdog relaunched (resumes; s0-s6 tiles already pushed)
2026-10-01T06:17:37Z pherc0211_fl-pherc0211_s8: official tiles 8 pushed
2026-10-01T06:49:17Z pherc0211_fl-pherc0211_s10: official tiles 8 pushed
2026-10-01T07:05:28Z pherc0211_fl-pherc0211_s12: official tiles 8 pushed
2026-10-01T07:23:38Z pherc0211_fl-pherc0211_s14: official tiles 8 pushed
2026-10-01T07:43:38Z pherc0211_fl-pherc0211_s16: official tiles 8 pushed
2026-10-01T07:59:28Z pherc0211_fl-pherc0211_s18: official tiles 8 pushed
2026-10-01T08:17:11Z pherc0211_fl-pherc0211_s20: official tiles 8 pushed
2026-10-01T08:32:27Z pherc0211_fl-pherc0211_s22: official tiles 8 pushed
2026-10-01T08:57:38Z pherc0211_fl-pherc0211_s24: official tiles 8 pushed
2026-10-01T09:15:04Z pherc0211_fl-pherc0211_s26: official tiles 8 pushed
2026-10-01T09:50:16Z pherc0211_fl-pherc0211_s28: official tiles 8 pushed
2026-10-01T10:11:56Z pherc0211_fl-pherc0211_s32: official tiles 8 pushed
2026-10-01T10:28:25Z pherc0211_fl-pherc0211_s34: official tiles 8 pushed
2026-10-01T10:52:41Z pherc0211_fl-pherc0211_s36: official tiles 8 pushed
2026-10-01T11:23:35Z pherc0211_fl-pherc0211_s38: official tiles 8 pushed
2026-10-01T11:56:15Z pherc0211_fl-pherc0211_s42: official tiles 8 pushed
2026-10-01T12:20:35Z pherc0211_fl-pherc0211_s44: official tiles 8 pushed
2026-10-01T12:44:56Z pherc0211_fl-pherc0211_s46: official tiles 8 pushed
2026-10-01T12:47:55Z fl-pherc0211: round 1 exhausted (24 own-lane seeds, 22 kept+tiled); round 2 seeds added (FL_ROUND=2: heights +0.035, azimuths +45 deg; indices 48+), NSEEDS 40->80, PIPELINE_DONE removed
2026-10-01T14:48:50Z fl-pherc0211: pipeline idle 12:45-14:50Z (keepalive pgrep matched its own launching shell because WD was given on the command line); watchdog relaunched by absolute path, keepalive now uses its default WD
2026-10-01T15:35:05Z pherc0211_fl-pherc0211_s48: official tiles 8 pushed
2026-10-01T16:01:21Z pherc0211_fl-pherc0211_s50: official tiles 8 pushed
2026-10-01T16:26:30Z pherc0211_fl-pherc0211_s52: official tiles 8 pushed
2026-10-01T16:44:59Z pherc0211_fl-pherc0211_s54: official tiles 8 pushed
2026-10-01T17:03:13Z pherc0211_fl-pherc0211_s56: official tiles 8 pushed
2026-10-01T17:21:23Z fl-pherc0211: FL4 (DECL-FL-4-A1, PHerc0268 lane 4/16) NOT started: running tools/fl4/go.sh was refused by the session's auto-mode permission classifier; not routed around. Needs the owner to allow it (or run go.sh) in this session. FL2 PHerc0211 pipeline left as it was (round 2 running).
2026-10-01T17:22:36Z pherc0211_fl-pherc0211_s58: official tiles 8 pushed
