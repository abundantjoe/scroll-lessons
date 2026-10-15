# First Letters push, worker brief (RULES.md DECL-FL-2)
Provenance: Project HERCULES | [id removed]

Goal: produce as many eligible 2 x 2 cm ink-prediction tiles of YOUR scroll as possible in the next ~20 h. The orchestrator pre-screens your tiles by numbers and sends the best to blind readers. You never open, display or describe any image, tile or CT slice: numbers, hashes and file lists only. Push only to your own branch claude/gifted-bell-gavnl5-sib-<you>.

Economy (important): the whole fleet shares one usage limit. Launch the pipeline DETACHED (setsid nohup ... &), then keep ONE harness-tracked Bash run_in_background wait (timeout 7200000) on it, re-armed when it returns. Do not poll in short loops or narrate progress. The pipeline itself commits and pushes after every unit.

1. Your scroll: logs/fl2/assign.json on origin/claude/gifted-bell-gavnl5 (key scrolls.<SCROLL>). You are either its "primary" (seed lane 0) or its "second" (seed lane 1). Volume id is given there; CT = s3://vesuvius-challenge-open-data/<SCROLL>/volumes/<volume>-*.zarr (find the exact name with the template's `fl.py list`), surface prediction = the newest representations/predictions/surfaces/*surface-m7*L0*.zarr of that volume.
2. Code template (unchanged logic, parameters only): git fetch origin claude/gifted-bell-gavnl5-sib-fl-pherc0257 && git checkout 54b29c9661afac1e661211175bf2bbd816f21cce -- tools/sib/fl-pherc0257/ ; copy pipeline.sh, fl.py, watchdog.sh to tools/sib/<you>/fl2/ and change ONLY:
   - SCROLL, CT, SURF, UMB (organizer umbilicus if the bucket has one, else none), branch, paths (W=/work/fl2, L=logs/sib/<you>/fl2), commit-message names;
   - seeds: `fl.py seeds ... 48` (48 candidate seeds); you take the seeds with index % 2 == your lane (primary 0, second 1), segment names <SCROLLlower>_<you>_s<k>;
   - NSEEDS (max grow attempts) = 40, MIN_AREA = 16 cm^2, 0 self-intersections (unchanged gate);
   - if the bucket has organizer tifxyz segments, use ALL of them (largest first), primary takes even ranks, second odd ranks, before any auto-grow;
   - tiles: every 2 x 2 cm grid cell with valid >= 50 % (unchanged cmd_tiles), both directions.
3. Environment (known fixes): docker/env/setup_env.sh from the repo; install villa's vesuvius package with `pip install --ignore-requires-python -e /work/villa/vesuvius` on Python 3.13 if it demands 3.14 (fl-pherc0257 env.txt); `uv pip install imagecodecs` into /opt/hv (LZW tifs fail without it). Official checkpoint sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab.
4. Models: run the OFFICIAL checkpoint on every segment as soon as it is rendered. When logs/sib/fl-pherc0257/fl2/DENSE_OK.json exists on origin/claude/gifted-bell-gavnl5-sib-fl-pherc0257 (git fetch it each time your wait returns), also run the DENSE checkpoint on every segment (earlier ones too), using that file's instructions (converter script + sha256). Never change model weights, inference options or the tiling.
5. Outputs, pushed per segment: logs/sib/<you>/fl2/<SEG>/tiles_<official|dense>/<SEG>_<forward|reverse>_rRR_cCC.png and a manifest.json there with one row per tile: file, png_sha256, scroll, volume, segment, model, model_sha256, direction, r, c, valid_fraction, ink_score_ge128 (fraction of valid px >= 128), px_per_mm, segment_area_cm2. Keep the tifxyz (x/y/z.tif + meta.json) of each accepted segment under logs/sib/<you>/fl2/<SEG>/tifxyz/. One line per unit in logs/sib/<you>/fl2/STATUS.md.
6. Keep going until stopped: grow -> render -> infer -> tile -> push, segment after segment, all day. If a step fails, record it in STATUS.md and continue with the next seed.
Every commit message ends with "Provenance: Project HERCULES | [id removed]".
