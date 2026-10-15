Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal: first recipes to rank on DEV (task devloop, for the orchestrator to declare or reject)

DEV ranks only. No recipe below is a letter claim, and a DEV rank is never evidence of letters. A recipe that
becomes a FINALIST (DECL-DEVLOOP) gets a freshly sealed decision with NULL + REV + reference arms (K6).

## Common protocol (every recipe)

- Start: the official base ink_9um hybrid_3d2d seed42 step-075000 (sha256 e635558a...9cab; D0-SETTLED item 2).
- Training data: organizer 2.4 um maps on non-0841, non-eligible scrolls only, via the D2 pair definitions of
  the pairs0139 and pairs0814 siblings. Always EXCLUDED from training: the DEV windows, their segments, and every
  trace that is same-papyrus with them (dev_registry.json, `holdout_segments` for 0814; the controls and
  their neighbours for 0139, which pairs0139 already excludes by its rules N and S). The 0009B DEV windows are
  never trained on (D0-SETTLED item 3).
- Controls per recipe, identical except for one factor. Both are evaluated by the same DEV evaluator:
  - NULL: the target tiles are permuted across tiles, with one fixed permutation (seed 20260925) in which no
    tile keeps its own label.
  - REV: every input stack is reversed in depth; labels are unchanged.
- ALARM (proposed): the recipe is shelved if NULL or REV reaches the FINALIST bar on any DEV scroll, or if
  NULL's pooled r_best is at least half of the recipe's.
- Seeds: 1 seed for ranking. A recipe within 0.025 mm (one grid step) of the best gets 2 more seeds before any
  finalist call, and the seed spread is reported.
- CPU budget: D3 measured 1.69 h per 2000 steps at batch 8 (fp32, 3 threads; logs/d1/d3_timing.json). The AMX
  sibling measured bf16 at about 0.54 x the fp32 time per tile (docker/TOOLING.md).

## Recipes, in proposed order

1. **LC384-FROZEN**: frozen-encoder letter-context head.
   - The base 3-D stem and encoder are frozen. A new 2-D head sees 384 px of context (3.6 mm, about one
     letter height plus neighbours) on cached encoder features, using the AMX sibling's feature-cache
     prototype. Only the head is trained, so it is the cheapest recipe on CPU.
   - Targets: organizer 2.4 um map area-averaged to 9 um. Ink >= 150, blank <= 100, the rest ignored.
   - Hypothesis: the base stem already detects ink (0841 AUC 0.73), but its 128 px tiles lack stroke context.
   - Measured by: sigma_eq falls toward sigma_crit, and r_best rises.
2. **LC384-SOFT**: recipe 1 with soft-teacher targets.
   - The target is the continuous organizer value / 255, trained with BCE on soft targets (no thresholds and no
     ignored band).
   - Hypothesis: the ignore band throws away the stroke-edge gradient that sigma_eq measures.
3. **DIST-FT**: full fine-tune distillation from the organizer 2.4 um maps.
   - Setup: 128 px tiles, 12k steps (DECL-D2 P128) scaled to the CPU budget. Train on the pairs0139 and
     pairs0814 tiles with soft targets.
   - This is the D2 recipe run at CPU scale, and it is the reference for recipes 1-2.
4. **DIST-FT-384**: recipe 3 with 384 px tiles (DECL-D2 P384).
   - It runs only if recipe 3 or 1 moves sigma_eq by at least 0.05 mm, because its cost is 9x per step.

Every recipe also reports, per DEV scroll: pooled sigma_eq and r_best, the per-window sigma_eq spread, AUC in both
orders, and non-text-order blob-f180 on the blank.

## Validation of the ranking itself (measurable)

- Positive control (real data, no model): calib_summary.json. The registered reference blurred by 0, 0.15 and
  0.30 mm returns exactly that sigma_eq. A 2 px shift raises it.
- Negative controls: the NULL and REV of every recipe, and CHANCE, where the base map of window i is scored
  against the reference of window j (proposed; still to be run).
- Stability: the per-window sigma_eq spread, and seed repeats for near-ties.
