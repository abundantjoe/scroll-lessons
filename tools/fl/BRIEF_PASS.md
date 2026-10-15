# First Letters extra-pass worker brief (RULES.md DECL-FL-1; OWNER-STANDING-ORDER-5)
Provenance: Project HERCULES | [id removed]
You are a COMPUTE WORKER, dispatched at the owner's explicit request. Your assignment (SCROLL, PASS) is in the message that sent you here. You are not the orchestrator; skip the repo SessionStart checklist. Never open, view or describe any image, tile or CT pixel: numbers, hashes and file lists only.
Write tools/sib/fl<PASS>-<scroll_lower>/pipeline.sh and run it in the background (nohup) with a restart loop. It must be idempotent (skip finished units) and must commit and push to YOUR branch after each unit.
1. Environment: docker/env/setup_env.sh + docker/env/vc_build.sh (VC3D apps from villa 41701aa; TOOLING.md); vesuvius on CPU. Reuse an existing build if present.
2. Segments: list s3://vesuvius-challenge-open-data/<SCROLL>/ anonymously and rank the organizer tifxyz segments by area.
   - PASS 2: organizer segments ranked 4-9. If the scroll has none, auto-grow up to 4 segments (vc_grow_seg_from_seed on the organizer surface-m7 prediction) seeded in the OUTER third of the scroll radius.
   - PASS 3: organizer segments ranked 10-15. If none, auto-grow up to 4 seeded in the INNER third of the radius.
   - PASS 4: organizer segments ranked 16-21. If none, auto-grow up to 4 at mid radius, restricted to the upper half of the scroll's z extent.
   Keep only segments with 0 self-intersections and an area of at least 16 cm^2. If your rank range is empty and the auto-grow rule does not apply, write STATUS "DONE: no segments in range" and stop.
3. Render with the C2-NT chain: vc_render_tifxyz -n 31 --flip-normals (see tools/c3/run_infer.sh). Ink model: the official ink_9um step-075000 (HF scrollprize/ink_9um, sha256 e635558a...9cab), official infer, both directions, no TTA, CPU.
4. Tiles: 2 x 2 cm, u8 prediction, INTER_AREA to 1068 px, PNG; keep tiles with valid >= 50 %. Push them under logs/sib/fl<PASS>-<scroll_lower>/<segment>/tiles/ with manifest.json (segment, r, c, png_sha256, valid_fraction, px_per_mm, source organizer|auto, pass).
5. When the pipeline has finished every unit, it appends "DONE <n tiles>" to logs/sib/fl<PASS>-<scroll_lower>/STATUS.md and pushes (no AI turn needed).
After launching, write one STATUS.md line and end your turn. The background job pushes on its own.
