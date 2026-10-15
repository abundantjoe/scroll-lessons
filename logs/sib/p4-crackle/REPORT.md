Provenance: Project HERCULES | owner the owner | [id removed]

# p4-crackle report: DECL-P4-9 (P4-H 1 um crackle channel) validation gate: FAIL

Builder role only. No image, tile or CT pixel was opened, viewed, displayed or described. Only numbers were computed.

## Result
- **GATE: FAIL.** Pooled pixel AUC of crackle energy vs the official 1 um prediction (M2b) is **0.584**. The tile-bootstrap 95 % CI is [0.565, 0.603]. The bar is >= 0.70.
- Rot-90 sanity AUC: **0.485**, CI [0.469, 0.503]. It is inside 0.50 +- 0.03, so it passes. The pipeline is not producing spurious alignment.
- Under DECL-P4-9 item 2, P4-H stops. No title-strip (w010-027) P4-H tile was computed. The M2a report is not produced, and there is no census.

## What was run (pre-registered in gate_plan.json, commit 44b77c3, before any crackle number existed)
- **Control:** 20260623142658-w028-037, 1.129 um L1 surface volume at level 0 (2.258 um px).
  - 16 tiles were drawn from the 64 DECL-P4-4-A1-eligible M2b tiles with default_rng(20260926): r2_c4, r2_c5, r2_c8, r2_c10, r2_c17, r3_c7, r3_c8, r3_c11, r3_c15, r3_c20, r4_c0, r4_c2, r4_c4, r4_c7, r4_c8, r4_c14.
- **Channel (DECL-P4-9 item 1):**
  - slices 50..66 (+-18.1 um);
  - per slice, DoG with sigma 1.5 / 6 px, squared, then the mean over slices;
  - INTER_AREA to the 1068 px M2b grid;
  - A1 stretch over fully mesh-valid pixels with CT > 0.
- **Classes:**
  - ink = prediction >= pooled p90 (186), background = <= pooled p50 (32);
  - pixels within 50 um of a class boundary were excluded;
  - 1,194,031 ink and 6,099,191 background pixels remained.
- **Inputs:**
  - the M2b PNG bytes were sha256-checked against the p4-tiles-b m2b manifest (manifest sha 427821cb...);
  - the mesh x.tif sha matched the M2b manifest;
  - a Range read equalled the full-chunk bytes on a test chunk.

## Per-tile AUC (display values; the float energy gives identical values)
| tile | ink px | bg px | AUC | rot-90 AUC |
|---|---|---|---|---|
| r2_c4 | 54687 | 320407 | 0.604 | 0.489 |
| r2_c5 | 115032 | 375246 | 0.528 | 0.508 |
| r2_c8 | 92801 | 527364 | 0.635 | 0.493 |
| r2_c10 | 140420 | 482446 | 0.600 | 0.490 |
| r2_c17 | 88402 | 456948 | 0.530 | 0.506 |
| r3_c7 | 12457 | 432374 | 0.659 | 0.531 |
| r3_c8 | 84543 | 509072 | 0.614 | 0.525 |
| r3_c11 | 33347 | 251502 | 0.611 | 0.513 |
| r3_c15 | 21764 | 350634 | 0.645 | 0.462 |
| r3_c20 | 131224 | 370896 | 0.595 | 0.448 |
| r4_c0 | 87415 | 234345 | 0.579 | 0.516 |
| r4_c2 | 43656 | 204900 | 0.577 | 0.478 |
| r4_c4 | 41863 | 199524 | 0.628 | 0.531 |
| r4_c7 | 9128 | 464504 | 0.500 | 0.506 |
| r4_c8 | 103961 | 457284 | 0.622 | 0.503 |
| r4_c14 | 133331 | 461745 | 0.589 | 0.485 |

The full record is in gate.json (per-tile thresholds, stretch values, fetch and compute info, and display sha256).

## Reading of the numbers (scientific humility)
- The association is real but weak:
  - 15 of 16 tiles have an aligned AUC above 0.5 (r4_c7 = 0.500);
  - the best tile reaches 0.659;
  - the rot-90 control sits at chance.
- At the fixed DoG scales, crackle energy carries some ink information on known text, but far too little to serve as an independent ink channel (bar 0.70).
- No alternative sigma, slab or statistic was tried after seeing the result. Any change would need a new declaration before any computation.
- Caveat: the reference is the model's prediction, not ground truth, so the AUC measures agreement with the model. A crackle channel could in principle be right where the model is wrong, but this gate cannot show it.

## Unit tests (item 3; tools/sib/p4-crackle/test_crackle.py): 7 passed
- Synthetic crackle vs smooth patches: AUC 1.0 at crack contrast 2x the per-voxel noise.
- Sensitivity sweep: AUC 0.604 / 0.870 / 0.994 / 1.000 at contrast / noise ratios of 0.25 / 0.5 / 1 / 2.
- DoG peak period: 35 um. The amplitude transfer relative to the peak is 0.13 / 0.47 / 0.73 / 0.98 / 0.98 at 10 / 15 / 20 / 30 / 40 um.
- Crack-network energy over smooth patches: 1.63 / 2.50 / 3.25 / 3.53 / 3.60 / 3.13 at 10 / 15 / 20 / 25 / 30 / 40 um spacing. The 10 um response is the weakest.

## Not done (gate FAIL)
- No h1 tiles, no h1 manifest and no M2a AUC. tools/sib/p4-crackle/build_h1.py was prepared but never run. It asserts gate PASS before any title-strip computation.
- No sub-siblings were created (SUBSIBS.md).
