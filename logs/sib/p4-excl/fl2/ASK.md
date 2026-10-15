Provenance: Project HERCULES | [id removed]

# p4-excl FL2 ASK-1 (2026-10-01): seed count is capped at 8 by the template logic

The brief (tools/fl2/BRIEF_FL2.md item 2) says: `fl.py seeds ... 48`, 48 candidate seeds, and up to 40 grow attempts.

The template's `fl.py cmd_seeds` (fl-pherc0257 @54b29c96) walks a fixed 8-entry plan of (z_frac, azimuth). It breaks only when len(seeds) >= nseeds, so it returns at most 8 seeds, whatever nseeds is.

- PHerc0826 seeds.json: 8 of 8 positions gave a seed. The second lane (odd indices) had 4 seeds (s1, s3, s5, s7). All 4 grew, were kept, and are each about 31.13 cm2 with 0 self-intersections.
- The 4-segment list then ends. The pipeline will mark PIPELINE_DONE after s7, at about 32 official tiles in all, and stop. It will not run all day.
- Extending the plan (more z_frac x azimuth positions) changes the template's logic, which the brief forbids. So I have not done it.

Needed, one of:
- (a) A fleet-wide ruling that gives the extended plan (for example 6 z_frac x 8 azimuths = 48 positions, the first 8 identical to the current ones). Every worker then uses the same seeds, and the existing segments keep their names.
- (b) Confirm that 8 seeds per scroll is the intended scope.

Every other worker using this template has the same cap.

Also, for the record: the grow app wrote a stray copy of segment s1 (x/y/z.tif, meta.json) into the repo root as `2/`. It was moved out to /work/fl2/stray and never committed.
