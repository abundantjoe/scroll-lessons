Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (task dev-lcsoft)

Each item has a default. I act on a default only after GO.

1. **Recipe reading.**
   - The task text says "encoder unfrozen / soft". first_recipes.md recipe 2 (cited by DECL-DEVLOOP-A1) says "soft-teacher targets", with the encoder frozen.
   - Default: the declared soft-target recipe.
   - The unfrozen encoder costs about 4.3 h per arm (READY.md section 4) and would need its own declaration.
2. **Soft-target loss.**
   - Default: plain masked BCE-with-logits against inkmap/255, the literal "BCE on soft targets".
   - The alternative is the official composite (smoothed BCE 0.5 plus 0.25 soft Dice) on soft targets. That would be a change of recipe.
3. **Disk.**
   - Both fp16 caches take 4 MB per tile, and 30 GB is free.
   - Default: if the pool exceeds about 6000 tiles, build the reverse cache after RECIPE and NULL finish, and ask before deleting the forward cache. Nothing is deleted without approval.
4. **0139 label-valid mask.**
   - Default: the fail-closed recovery rule (READY.md section 2).
   - Better: pairs0139 adds a `valid` (lv) array to its shards. soft_targets.py uses it automatically when present.
5. **0814 pairs.**
   - Default: 0139 only, unless the training registry lists 0814. In that case I write a 384 px → 128 px tile adapter and hash it before use.
6. **DEV maps.**
   - Default: produced only via EVAL_API.md. lc_infer.py is the map producer; at initialisation it is bitwise equal to the official CLI (upstream test).

## Ruling (orchestrator, 05:58Z)
The defaults are accepted, except where one would change a bar, a control, the hold-out list or the recipe of DECL-DEVLOOP-A1; that text wins.
- Item 1 (recipe): the declared soft-target recipe with the frozen encoder. This matches DECL-DEVLOOP-A1 and first_recipes.md.
- Item 2 (loss): plain masked BCE on soft targets, the literal first_recipes.md text.
- Items 3-6: the defaults as written. Nothing is deleted without approval.
