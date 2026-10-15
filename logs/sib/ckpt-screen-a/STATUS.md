Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-a status (2026-09-26 21:30Z)

## P4-O (DECL-P4-14): PHerc.1667-iteration-0, claimed by ckpt-screen-a
- Split (orchestrator 21:17Z, ckpt-screen-b SUBSIBS.md at ca732ae): ckpt-screen-b runs iteration-5 (then iteration-1 if -c has not taken it); ckpt-screen-a runs iteration-0 only. Never the same checkpoint twice.
- Ready and verified, no CT read, no tile made:
  - weights model.safetensors sha256 62c43b98... = catalogue and ckpt-screen-b provenance.json; config.json, configuration_inkdetection.py, modeling_inkdetection.py git blob oids = catalogue (commit 06c30644);
  - mesh tifxyz (meta, x, y, z) and SV .zattrs / 0/.zarray sha256 = pairs0814b e2 manifest input_sha256;
  - env: python 3.11, torch 2.14.0+cpu, transformers 4.57.6.
- Geometry (same as ckpt-screen-b's iteration-5 run): level 0 at 2.4 um, slices 23..84 (official centre crop of 62 of 109), order REVERSE for iteration-0 (card: "l_2 inference uses reverse_layers=True"), clip(0,200)/255, card tiling 256 / stride 128 on the tile + 128 px halo, fmask = strip-a mesh-valid, raw u8, 0 outside mesh-valid, INTER_AREA 8343 -> 1068.
- Self-test (tools/sib/ckpt-screen-a/p4o_selftest.py, synthetic data only): a banded chunk reader (tools/sib/ckpt-screen-a/p4o_tiles.py) reproduces the card loop exactly (max abs diff 0.0, counts equal, both orders); 3.5-4.1 s per model window at 4 threads fp32. Plan was to run ckpt-screen-b's builder (tools/sib/ckpt-screen-b/p4o_tiles.py @ ca732ae) byte-identically so both P4-O materials are built the same way.
- Cost: ~4,300 windows per 2 x 2 cm tile -> ~4-4.5 h per tile per order on 4 vCPU; r0-r5 x c0-c17 = 108 eligible tiles -> ~450-480 h on one worker (~120 h with 4 workers).
- BLOCKED 21:28Z: launching the inference was refused by this session's permission layer (reason given: "Code from External"). Recorded, not worked around. No tile, map or manifest exists for iteration-0. No sub-sibling has been spawned.
- Needed to proceed: an owner/orchestrator decision to allow this session to run the official HF model code (trust_remote_code) and the ckpt-screen-b builder, or to hand iteration-0 to a sibling that can run them (ckpt-screen-b's workers already run the same code for iteration-5).

## DEV screen (DECL-DEVLOOP-SCREEN)
PHASE 1 done (SPECS.json, commit abb3f8e). Gate closed: waiting for GO SCREEN and its METRIC-HASH.

## P4-O family provenance
p4o/provenance.json (commit 4521415): ink_9um seed43, hecate_9.6um, ink_3d_dino_guided all NOT eligible (documented Paris 4 training).

## 2026-09-30 04:08Z: First Letters PASS 3, PHerc0483A (tools/fl/BRIEF_PASS.md @ dcb6a6ba): NOT LAUNCHED
Held for an explicit owner go. The brief asks for a self-restarting, self-pushing detached pipeline that renders and maps an eligible volume with no later review turn. This session's original rules forbid maps of eligible volumes, and its last launch of official model code (P4-O, 2026-09-26) was refused by the permission layer. The fleet log at 2873940 also records that the fan-out was stopped after an Auto-Mode Bypass signal. Nothing was rendered, mapped or downloaded for PHerc0483A.
