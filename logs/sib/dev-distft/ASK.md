Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (dev-distft sibling -> orchestrator)

first_recipes.md defines DIST-FT as: full fine-tune distillation from the organizer 2.4 um maps; 128 px tiles;
12k steps (DECL-D2 P128) scaled to the CPU budget; train on the pairs0139 and pairs0814 tiles with soft targets;
common protocol (base seed42 step-075000; NULL, REV, CHANCE controls; 1 seed; hold-outs). Every parameter it leaves
open is listed here with the default this session implements and continues on. Every default is a config field, so
changing one changes the config sha256 and nothing else in the code. Nothing here has touched real data.

## A1. Steps and batch ("12k steps scaled to the CPU budget")

- DEFAULT: batch 32 (DECL-D2 P128), 2500 steps per arm (80,000 samples, 0.21 of P128's 384,000), constant lr. Only the
  final step's weights are kept and evaluated: no checkpoint selection of any kind, least of all on DEV.
- Why: the fp32 4-thread rate on this container varied from 12.65 to 17.26 s/step between runs (READY.md section 3).
  2500 steps at the slowest measured rate is 12.0 h, the D0-HW bar of <= 12 h per arm; at the fastest it is 8.8 h.
  The three arms (recipe, NULL, REV) run one after another on this container: 26 to 36 h in total.
- Coverage: the current pairs0814 pool alone is 564 gated 384 px patches = 5,076 sub-tiles of 128 px, so 80,000
  samples is about 16 epochs of pairs0814 alone (fewer once pairs0139 is added).
- Alternatives:
  - 12,000 steps: 42 to 58 h per arm;
  - match D3: 2000 steps at batch 8.

## A2. The soft target and the loss

- DEFAULT target: `ref9 / 255`, where ref9 is the pairs sessions' area-averaged organizer map on the 9 um canvas. It is
  supervised on every pair-valid pixel, with no threshold and no ignored band (as LC384-SOFT defines "soft").
  - Measured on the synthetic smoke pool: 27.1 % more pixels are supervised than under the DECL-D2 rule (the band
    100..150), i.e. 1,887,435 of 6,959,925.
  - On the real pairs0814 pool (564 gated patches, registry counts): at most 7.5 % more (n_ignore 5,795,005 against
    ink + blank 77,370,179). This is an upper bound, because n_ignore also counts invalid pixels.
  - Ink is 16.5 % of the pinned-supervised pixels.
- DEFAULT loss: the official loss unchanged, i.e. BCE with the base's `bce_label_smoothing` 0.5 plus Dice
  (`dice_label_smoothing` 0.0), with the ignore channel. With smoothing 0.5, a soft target t trains BCE toward
  0.25 + 0.5 t. Keeping smoothing leaves the loss identical to the base's on binary targets.
  - Alternative: smoothing 0 for DIST-FT, which is pure distillation. That is a second change beyond the target.
- DEFAULT deep supervision: the official nearest-neighbour target pyramid. The alternative is area-averaged soft
  targets at the coarse levels, which would be a further change.

## A3. Seeds

- DEFAULT: seed 20260925 for DIST-FT, DIST-FT-NULL and DIST-FT-REV. All three draw the identical (patch, z-window,
  rotation) sequence (paired sampling, tested by the sample digest).
- The NULL derangement is always drawn with `default_rng(20260925)`, independent of the run seed, per
  DECL-DEVLOOP-A1 item 2. The code refuses any other derangement seed.
- If DECL-DEVLOOP-A1 item 4 triggers (within 0.025 mm of the best), the 2 extra seeds are 20260926 and 20260927.
  They are applied to the recipe arm only unless told otherwise.

## A4. Tile, rotation and pair layout

- DEFAULT:
  - tile 128;
  - 24 x 15 deg rotations (the P128 preset);
  - z window 17 of 21 with jitter +-2;
  - `--subtile` on 384 px patches: the nine 128 px sub-tiles of each patch, with rotation context taken from the
    neighbouring pixels of the patch. This is the trainer sibling's ASK 3 default.
- Source layouts:
  - pairs0814 enters as `stagec` (384 px patches, `ref9` + `valid`);
  - pairs0139 enters as `tilegrid3` (complete grid-aligned 3 x 3 blocks of kept 128 px tiles).
- Why tilegrid3 is needed: NULL permutes targets across the concatenated patches of all sources, which needs one
  patch size across sources. Tiles outside complete blocks are unused, and their count is reported when the
  registry is final.
- Alternative: pairs0139 as single 128 px tiles, with one derangement per source.
- Sampling: pooled, one epoch-wise stream over all patches (DECL-D2 pooled), so each source is weighted by its patch
  count. Alternative: per-source quotas.

## A5. Precision

- DEFAULT: fp32, 4 threads.
- DECL-AMX-1 scopes a bf16 pass to the batch 8 / lr 2e-5 / 2000-step recipe class. DIST-FT (batch 32, soft target)
  is outside that scope, so it would need its own parity run first.

## A6. Replay

- DEFAULT: no replay. first_recipes.md and DECL-D2 P128 specify none.
- Alternative: the D3 replay pool (PHerc0139 base-training papyrus, official human labels), as a forgetting control.
  That would change the recipe into a mixed-target run.

## A7. pairs0139 validity mask

- tilegrid shards store `label` (1 / 0 / 255) and `inkmap`, but no explicit validity mask.
- DEFAULT: valid = `label != 255` OR `100 < inkmap < 150`.
- An invalid pixel whose rounded inkmap happens to lie in 101..149 would be wrongly supervised. Its count cannot be
  measured from the shards.
- REQUEST: the pairs0139 session stores `valid` explicitly (or confirms that `inkmap` is 0 wherever the pixel is
  invalid). The loader already checks that the soft target reproduces the pinned DECL-D2 labels exactly on every
  source, and refuses the source otherwise.

## A8. Which pairs, and the hold-outs

- DEFAULT: exactly the training-pair registry named in GO, filtered by the frozen hold-out list.
- The filter is fail-closed:
  - a patch is dropped if its segment is a DEV segment, or is same-papyrus (+16 vox) with one, per the frozen list;
  - it is also dropped if its patch_id is listed.
- The resulting allowlist is sha256-pinned in the config through the pinned trainer's `allow_ids` mechanism.
- pairs0814 base-papyrus and duplicate flags (its Q5): no default of mine. Whatever the named registry keeps is used.
- Still pending:
  - pairs0814's stage-C shards (`shards.json`) do not exist yet (stage B staged blocks only);
  - pairs0139's shards are not on git.

## A9. Evaluation path

- DEFAULT: each arm's final weights are passed to EVAL_API.md unchanged, with evaluate.py unchanged.
- Nothing is evaluated before all three arms finish. No DEV number feeds back into any training choice.
- EVAL_API.md and the frozen hold-out list do not exist yet on the devloop branch (checked at commit 5e7fd18).
