Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c status (2026-09-26T21:35Z)

## P4-O third PHerc.1667 iteration (P4-O-PROVENANCE-2), dispatched 18:51Z / 21:19Z
- ITERATION CHOICE: BLOCKED, and no inference. No card documents a held-out metric: the family table has
  segment/label/tiles/epochs only, and the cards give training losses only. See ASK.md A.
- Cost at the card geometry: ~4.2 CPU-h per 20 mm tile per order; 108 tiles = ~456 CPU-h (ASK.md B).
- Pipeline READY (iteration-independent): tools/sib/ckpt-screen-c/p4o_tile.py. It uses the unchanged ckpt-screen-b
  infer_1667.py (sha256 431067ee...) for model load and card tiling, and pairs0814b's strip-a grid, mask rule and
  level-0 range reads (slices 23..84), and writes 1068 px raw-prediction PNGs + census in the e2 format.
  Synthetic smoke passed (p4o/smoke/smoke_synth.json); the real reader was checked read-only. Measured 4.05 s/window
  -> ~4.9 CPU-h per tile.
- Coordination: the depth order and normalisation follow ckpt-screen-b's iteration-5 conventions on this volume
  (ASK.md C, D).


## P4-O (DECL-P4-14), dispatched 18:43Z
- p4o/provenance.json: 0 of 5 checkpoints eligible. GP and large (Scroll 1 = Paris 4), resnet50_frags ("Pretrained on
  Pherc.Paris4"), fiber_4class (trained on the Paris 4 2.4 um volume): NOT eligible. july_retreat: AMBIGUOUS (own card
  silent on pretraining; the same-family PHerc 172 timesformer card says "Pretrained on Pherc.Paris4 (Scroll 1)") -> NOT
  eligible. No new public release (HF listing 18:46Z: 43 = catalogue).
- No P4-O inference, tile or manifest produced; no sub-sibling (p4o/SUBSIBS.md).

## DEV screen (DECL-DEVLOOP-SCREEN), paused by the P4-O dispatch

Phase 1 complete; waiting on the gate. No screen map exists; no CT, render or image was opened.

Gate: (a) METRIC-HASH of the frozen DEV-LOOP evaluator + v3 registry: NOT YET in RULES.md (latest METRIC-HASH-22 is P4-B);
(b) "GO SCREEN": not received.

Ready:
- Weights, sha256-verified against checkpoints.json (downloads.jsonl): july_retreat, GP, large, resnet50_frags, fiber_4class.
- Input specs, documented text order, training data: SPECS.json (sha256 2d0f87a309df90eea8104be9bc386cbe3a4e4fd7b88e784278433fc1b6f9fb4e).
- Wrapper tools/sib/ckpt-screen-c/screen_infer.py (sha256 b9d421f4166970217d225bb147fd3f7b06f1c84ddc6a2e0c82cf8189b83ad24f), smoke passed (smoke/).
- In-sample guard per window: insample.json against the devloop registry draft a6af0cb (not frozen; to be re-run on the hashed one).
  july_retreat, GP, large: OUT-OF-SAMPLE on all 9 current entries; resnet50_frags: UNKNOWN (unresolved training ids); fiber: not screened (spec mismatch).
- Runtime (4 threads fp32, both orders): per 2 cm window july 117, GP 133, large 295, resnet 79 CPU-min (624 total);
  per 1 cm blank 214 total. Current registry draft (8 windows + 1 blank): ~87 h on this 4-vCPU box. See ASK.md.

Open questions for the orchestrator: ASK.md.
