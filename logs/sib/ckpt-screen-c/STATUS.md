Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c status (2026-09-26T21:35Z)

## P4-O PHerc.1667-iteration-4 (DECL-P4-14-A2), running since 2026-09-27T01:06Z
- 2026-09-28T07:55Z: INTERIM MANIFEST pushed (DECL-P4-14-A3 item 2 threshold met): 12 tiles, all fp32, gate r0 c5-c8 +
[line withheld: prize-candidate detail under review]
  Stage (i) still open: r1 c7-c14 (sub-siblings). Parent now on stage (ii) r2 (see SUBSIBS.md).
- The merge loop's fetch had stopped merging after the container restarts (merged [] while tiles existed); it was run by
  hand and restarted.
- Iteration 4 was ruled in DECL-P4-14-A2 item 3 (a rule that does not depend on results). Weights sha256
  a1612b1fc97dea039aec3a1d06ff65fe0ee217b91dbe6db9785eb2e5befb3ffe, verified against the catalogue and ckpt-screen-b SPECS.
- Method: ckpt-screen-b p4o_tiles.py / infer_1667.py unchanged (pinned sha256 199937ad / 29444f37), via
  tools/sib/ckpt-screen-c/p4o_run.py: level 0 2.4 um, slices 23..84, forward (b's convention for iterations 1-5),
  clip(0,200)/255, card tiling 256/128, 128 px halo, raw u8 at 1068 px, 0 outside mesh-valid.
- Stage (i), 20 tiles, split across the parent and s1-s3 (p4o/SUBSIBS.md).
- Done: r0 c5 fp32 (03:42Z, 2.6 h, 3,631 windows, coverage of valid 0.989; commit 81d0bd3).
- bf16 equivalence check (DECL-P4-14-A2 item 2): FAIL (p4o/bf16_check.json, 12:35Z). On r0 c5 over 59,719,609
  mesh-valid px, frac |bf16 - fp32| > 2/255 = 0.0894 (limit 0.01); frac > 0 = 0.551; mean |diff| 0.93; max 16/255.
  So all P4-O iteration-4 tiles are fp32. The bf16 copy stays outside the material (/work only, never pushed).
[line withheld: prize-candidate detail under review]
  tiles (DECL-P4-14-A3), written automatically by the merge loop.
- INCIDENT 12:37Z: the parent's r1 c5 run was OOM-killed (cgroup, anon-rss 14.0 GB) by the unbounded chunk-read map in
  ckpt-screen-b p4o_tiles.py at fd13b7e (r0 c5 fitted because its halo lies partly outside the canvas). b fixed it in
  4741d69/98cd075 (output-identical). The worktree was moved to 98cd075, the pin updated, and the parent restarted at
  18:55Z (r1 c5, r0 c6, r1 c6). ~6 h of parent compute was lost.
[line withheld: prize-candidate detail under review]
  r0 c7). Resume messages were sent at ~19:00Z with the 98cd075 update.
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
