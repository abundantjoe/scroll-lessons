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
