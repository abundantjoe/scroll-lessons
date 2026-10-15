Provenance: Project HERCULES | owner the owner | [id removed]

# DECL-FL-1: First Letters screen, PHerc0175A (sibling tracer)

STATUS: DONE, **0 tiles**. No segment met the DECL-FL-1 item 1 bar (0 self-intersections and ≥ 16 cm²), so nothing was rendered or tiled. No image, tile or CT pixel was opened.

## What ran (`tools/sib/fl-pherc0175a/`; every rule fixed in `fl.py` before any PHerc0175A data was read)
- **Segments.** The bucket has **no organizer segments** for PHerc0175A (only photos/, representations/, volumes/), so the pipeline auto-grew them per DECL-FL-1 item 1.
- **Seeds.** 4 seeds from the m7 L4 prediction (rule in `fl.py`; `seeds.json`), each snapped to a prediction voxel of 255.
- **Growth.**
  - Input: local crops of m7 level 1 (17.28 um) with official vc_gen_normalgrids.
  - Tracer: gated build c5, preset L15 (task P + space_line_weight 0.1, reject_dist_th 1.5), step 20, 80 generations.
  - Why level 1: the L0 normal-grid band for 80+ generations would need 10-20 GB of the 8.8 GB free.
- **Environment.** Ink venv on Python 3.14, because vesuvius at villa 41701aa requires it. The installed packages are recorded in `hv-ink-freeze-actual.txt`. The checkpoint sha256 e635558a…9cab was verified. This environment was never exercised, since no segment qualified.

## Result per seed (`seg*/post.json`, `seg*/trace_meta.json`)

| seed | accepted | distance-gate rejects / evaluated | audit removed | raw area cm² | crossings (raw → after v2) | final area cm² | kept |
|---|---|---|---|---|---|---|---|
| 0 | 522 | 381 / 903 | 133 | 0.19 | 0 | 0.19 | no |
| 1 | 1429 | 816 / 2255 | 826 | 0.33 | 5 → 0 | 0.12 | no |
| 2 | 1279 | 832 / 2123 | 643 | 0.30 | 0 | 0.30 | no |
| 3 | 267 | 254 / 526 | 265 | 0.00 | 0 | 0.00 | no |

- All four ran the full 80 generations. The fringe stayed at about 20-40 candidates per generation, and about 40 % of candidates failed the distance gate.
- **Reading.** At m7 level 1 (17.28 um, twice the voxel size where L15 was validated: 9.36-9.6 um), the gated tracer does not hold the sheet on this scroll. Points 0.35 mm apart fall off the thresholded prediction and the audit removes them.
- The sheet pitch of PHerc0175A and the sharpness of its prediction at level 1 were not measured. That would be the first diagnostic for any rerun.

## Options (the orchestrator's decision; none were run, because each changes the declared method after this scroll's data was seen)
1. Grow at m7 L0 (8.64 um) with the official normal grids, syncing a band per seed. This needs about 10-20 GB of disk (11 GB free now) and several hours per seed.
2. Official ungated GrowPatch at level 1, then v2 truncation, then the same ≥ 16 cm² / 0-crossing bar. This is faster, but it bridged sheets in the tracer's synthetic tests.
3. Skip PHerc0175A in the First Letters fan-out.

Integrity: no issues.
