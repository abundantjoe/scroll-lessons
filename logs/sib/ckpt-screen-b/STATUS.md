Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-b status (2026-09-26 05:40Z)

Checkpoints: scrollprize/PHerc.1667-iteration-0 .. -5.

PHASE 1: DONE (commit 7138721). Details are in SPECS.json.
- Weights are sha256-verified (6/6), and last.ckpt is bit-identical to model.safetensors.
- The official HF code runs unchanged (transformers 4.57.6).
- Wrapper: tools/sib/ckpt-screen-b/infer_1667.py; smoke.json shows 6/6 pass.
- Input spec: 62 layers x 256 x 256, clip(0, 200)/255, ~2 um voxel class. The card is silent on voxel size, so it comes from villa code.
- Text order is undocumented relative to the devloop render; both orders will be mapped.
- Training data: iteration-0 = PHerc0500P2, PHerc0343P, PHerc0009B (2 segments); iterations 1-5 = l_2 on PHerc1667 only.
- Cost per 2x2 cm window per order, at 4 threads fp32: spec mode ~394 CPU-min; native 9.362 um mode ~7 CPU-min (out of the documented voxel size).

In-sample status per DEV window: insample.json (current devloop registry, 9 windows on PHerc0139 and PHerc0814). All six checkpoints are OUT-OF-SAMPLE for all nine. iteration-0 becomes UNKNOWN on any PHerc0009B or PHerc0500P2 window. Recompute on the frozen v3 registry.

GATE: CLOSED. No DEV-LOOP METRIC-HASH is recorded in RULES.md (latest is METRIC-HASH-23, P4-B), EVAL_API.md does not exist yet, and no GO SCREEN has been received. No map has been made.

Open decisions for the orchestrator: listed in SPECS.json open_decisions_for_orchestrator (geometry mode vs cost; iteration-0 0009B/0500P2 certification).

## Orchestrator ruling 2026-09-26 05:59Z (recorded 06:05Z)
The proposed defaults are accepted as written, under DECL-DEVLOOP-SCREEN:
- Geometry = spec mode (the wrapper default). The input voxel size comes from code: ~2 um class, run at 2.399 um in x, y and z, with 62 layers centred on the render surface. Native 9.362 um mode is not used for the screen.
- Both depth orders are mapped and reported, because the text order relative to the devloop render is undocumented. The order is not chosen from DEV.
- iteration-0 on any PHerc0009B or PHerc0500P2 DEV window = UNKNOWN (never counts toward FINALIST). IN-SAMPLE and UNKNOWN never count.
- Runtime at the ruled geometry: ~394 CPU-min per order per 2x2 cm window and ~144 CPU-min per order per 1x1 cm blank, at 4 threads fp32. For 6 checkpoints x 2 orders x 8 text windows that is ~630 CPU-h before blanks, so the order of work will be reported with the first GO.
Gate still CLOSED: waiting for the METRIC-HASH of devloop FREEZE.md and GO SCREEN.

## P4-O (DECL-P4-14), 2026-09-26 21:25Z
- provenance.json is pushed (ee5d83e). All 6 iterations are eligible: their documented training data is PHerc1667 (iterations 1-5) or PHerc0500P2/0343P/0009B (iteration 0), with a Kinetics initialisation. No Paris 4 / Scroll 1 data is documented.
- iteration-5 is running on the strip-a tiles at the 2.4 um level 0, slices 23..84, card stride 128. Four workers (the parent plus sub-siblings s1-s3; see p4o/SUBSIBS.md) cover r0-r1 of c0-c17 first. That takes ~3.3-4 h per tile, so r0-r1 finishes in ~35-40 h wall.
- iteration-1 comes next. The open cost/order questions are in p4o/ASK.md.
- Precheck: mesh-valid 0.9519 (= e2); normalised input mean 0.217 (training scale 0.22-0.30).

## P4-O update 2026-09-27 01:35Z
- iteration-5 tiles done (3): r0 c10 (parent), r0 c14 (s1), r1 c10 (s2). manifest.json is interim (3 tiles); checks: valid_fraction equals e2, all tiles eligible, png sha256 re-verified.
- Fixed: log() crash after each tile (b87d9dd); 15-min resumable in-tile checkpoints (9b0c5b3; resume bit-identical on test); read_stack memory bound (4741d69; S3 was cgroup-OOM-killed, 14.3 GB; output-identical on a 361-chunk test). Sub-siblings were messaged to sync both files and relaunch.
- Parent W0 resumed r0 c11 from window 283 after the relaunch. Next check-in 05:26Z.

## P4-O update 2026-09-27 05:58Z
- iteration-5 manifest: 7 tiles, interim. Gate c5-c8: r0 c7, r0 c8 (fleet). Title zone: r0 c10, r0 c11, r0 c14, r1 c10, r1 c15. Stage threshold NOT met yet (gate 2/3); r1 c7 (o5w3) is running.
- Fleet tiles are merged by tools/sib/ckpt-screen-b/p4o_merge.py (sha256 + code commit 98cd075 checked; the fleet writes under logs/sib/o5wN/p4o/).
- W0 on r0 c12. S1 on r0 c15, S2 on r1 c11, S3 on r1 c14 (all synced to 98cd075).

## 06:35Z: manifest 9 tiles (+ r1 c16 o5w6, r2 c16 o5w8). Gate 2/3 (r1 c7, o5w3, is at window 3855/4356, ~06:45Z). Title zone 7. Threshold not yet met; a watcher merges and pushes every 5 min.

## 06:44Z: STAGE THRESHOLD MET (DECL-P4-14-A3 item 2). iteration-5 interim manifest: 10 tiles; gate [(0, 7), (0, 8), (1, 7)]; title zone [(0, 10), (0, 11), (0, 14), (1, 10), (1, 15), (1, 16), (2, 16)]. pairs0814b may read this manifest as its first stage batch.

## 07:00Z: P4-O-STAGE-O2S1-RESULT: iteration-5 known-text gate FAIL (uninformative)
- No new iteration-5 tile will start. W0 was relaunched with r0 c12 only (71% done, it finishes). S1-S3 are told: finish only a tile more than half done, then stop. The A4 tiles are cancelled.
- Manifest: 11 tiles, interim (1c3440a). Tiles that finish later are still merged.
- Running: an undeclared numbers-only re-normalisation test on the centre of r0 c7 (tools/sib/ckpt-screen-b/renorm_test.py -> p4o/renorm_test.json).

## 2026-09-30 04:10Z: P4-O iteration-5 closed. Final manifest has 13 tiles (+ r0 c12 W0, r1 c11 S2). r2 c15 (o5w7) and further S1/S3 tiles never landed. Workers stopped. Reassigned to First Letters pass 3 (PHerc0483B).
