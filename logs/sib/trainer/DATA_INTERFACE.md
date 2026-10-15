Provenance: Project HERCULES | owner the owner | [id removed]

# D2 trainer data interface

This file lists what `tools/sib/trainer/d2_data.py` reads. Updated 2026-09-26 ~01:15Z.

## Adapters (the `kind` in `--source name=kind:path`)

| kind | Layout | Producer | Tested on |
|---|---|---|---|
| `blockpairs` | `registry/*.jsonl` + `blockpairs/<seg>/<by>_<bx>.npz` (images, ref9, labels 0/1/255, valid, xyz 17x17, patch_id), 384 px | pairs0814, pairs0814b (stage B) | synthetic fixture, **and the real pairs0814 commit c5fe80c: 329 patches, 11 segments, every block sha256 and label OK** |
| `stagec` | `shards.json` {shard, branch, n, bytes, sha256, patch_ids} + `pair_registry.json`. Since pairs0814 ede21e3 the shards ARE the staged block files, given by repo-relative paths on two branches (`logs/sib/pairs0814/blockpairs/...`, `data/sib/pairs0814b/blockpairs/...`); pass `--data-root name=<tree holding both>`. npz has no `segment`; it comes from pair_registry.json. Only listed patch_ids are used | pairs0814 stage C (union of 0814 + 0814b) | synthetic fixtures of both the packed and the block-file layouts |
| `tilegrid` / `tilegrid3` / `tilegrid4` | `registry/*.jsonl` + `shards/<seg>_sNN.npz` (images, label 0/1/255, inkmap, human, tile_id), 128 px tiles; k = 3/4 builds complete grid-aligned k x k mosaics | pairs0139, 0139b, 0139c | synthetic fixture (no real shards yet) |
| `pairs` | the schema below | (none yet) | synthetic |
| `d3_pool` | tools/d3 pools | D3 | D3 equivalence test |

Every adapter:
- checks every file's sha256 against its registry;
- recomputes labels by the DECL-D2 rule and refuses any mismatch;
- accepts a declared allowlist (`--allow-ids name=file`, sha256 pinned). The allowlists are produced by
  `pair_freeze.py` (see PAIR_FREEZE_SPEC.md).

## Orchestrator rulings applied (2026-09-26 00:36Z, interim)

- **Q3.** Every arm uses the same pixels: pairs0139 enters as `tilegrid3`, and every arm uses `--subtile`.
  In-block and out-of-block counts go in the pair-freeze record.
- **Q4.** Rotated-in pixels are IGNORE (supervision 0), never blank.
  - `_rotate` zeroes supervision where the rotated source falls outside the stored patch; sub-tile padding also has
    supervision 0 (tests `test_rotation_exact_multiples_and_margin`, `test_subtile_crop_padding`).
- **Q5 (b).** FL-09 clearance is >= 192 vox point-to-surface on the registry lattice (contam_check.clearance with
  threshold 192).
- **Q6.** No weights or optimiser state go to any git branch.
  - `d2_train.py train` refuses any `--remote-url` that is not an existing local bare-repo path; the local resumable
    state is kept every 250 steps.
  - The earlier test ref `claude/gifted-bell-gavnl5-sib-trainer-ckpt` (synthetic 2-step weights, 138 MB) still
    exists: my deletion push was refused by the session's safety check and was not worked around. It needs deleting
    by the owner or orchestrator.
- **Q8.** D2 runs at fp32.
- **Q1 (OPEN; orchestrator 05:25Z).** It stays open until DECL-D2-A1. The trainer implements both modes.
  Measured evidence:
  - `full_conv_check.json`: the base-config build (patch 17 x 128 x 128, strict load "All keys matched") runs
    17 x 384 x 384 and 17 x 512 x 512 fully convolutionally, with finite outputs and a working backward pass.
  - `param_diff_384.json`: building from patch 17 x 384 x 384 instead gives a different network:
    - 614 vs 508 state tensors;
    - +106 tensors (encoder stage 6: 96; decoder stage 5: 8; transposed conv 5: 2) and 40 same-name shape
      mismatches, 146 differing in total;
    - 47,871,298 vs 34,546,498 parameters (+13,324,800);
    - strict load of the base weights fails.

## Schema `hercules-d2-pairs/1` (for new producers)

### registry.json

```json
{
  "schema": "hercules-d2-pairs/1",
  "source": "pairs0139",
  "scroll": "PHerc0139",
  "volume": "<volume id>",
  "voxel_um": 9.362,
  "voxel_um_source": "<path of the volume's metadata.json + its sha256>",
  "stack_depth": 21,
  "render": {"n": 31, "stack_first_slice": 5},
  "mesh_stride_px": 16,
  "halo_px": 64,
  "shards": [{"file": "shard_0000.npz", "sha256": "<hex>", "n": 64}]
}
```

- `voxel_um` must come from the volume's `metadata.json` (I9). The loader refuses a registry that has no `voxel_um`.
- Every shard's sha256 is checked on load, so a changed shard is refused.

### shard_XXXX.npz (np.savez, no pickle)

| key | dtype / shape | meaning |
|---|---|---|
| image | uint8 (N, 21, S, S) | 9 um render stack: slices 5..25 of an official `vc_render_tifxyz -n 31` render (the same convention as D3) |
| target | uint8 (N, S, S) | teacher map on the 9 um canvas: the organizer 2.4 um map, mapped through the fitted affine |
| valid | uint8 (N, S, S) | 1 where both image and target are defined |
| patch_id | str (N,) | unique within the registry |
| segment | str (N,) | organizer segment id |
| canvas_yx | int64 (N, 2) | top-left corner of the S x S patch on the segment canvas (px) |
| mesh_xyz | float32 (N, G, G, 3) | volume-frame mesh points (voxels, x y z). The grid covers the patch dilated by `halo_px` on every side, sampled every `mesh_stride_px` px, so G = (S + 2 halo) // stride + 1. NaN = no mesh. |

- **Labels (DECL-D2):** ink = target >= 150; blank = target <= 100; everything else, and valid == 0, is ignored.
  The trainer applies this rule itself, so do not pre-threshold.
- **Patch size S:** S must be at least the largest trained tile. With 24 x 15 deg rotations, the corner-free crop needs
  S >= ceil(T * sqrt 2) + 2 (same parity as T): 184 for T = 128, 546 for T = 384, 727 -> 728 for T = 512.
  A smaller S still trains, but the rotated corners that fall outside the patch are marked ignored. This is recorded
  in `checks.rot_margin_full`.
- **Pair filters** (DECL-D2: 9 vs 2.4 um CT NCC >= 0.8, and >= 7 of 9 windows aligned within 1 px) are applied by
  the pairs session. Its registry should record them.

## Contamination (FL-09) input

The trainer writes `patch_registry_pool.npz` (every pool patch) and `patch_registry.npz` (the same, plus per-patch
draw counts) next to each run. It hashes both into `checkpoint_registry.json`, which also holds the config sha256,
the lineage and the data-registry sha256.

Checks follow RULES.md CORR-RETRACE-RULE and are done by `tools/sib/trainer/contam_check.py`, which triangulates
the registry lattices ("grid" = mesh_xyz (N, G, H, 3); "tilequads" = per tile the 2 x 2 corner lattice).
- `clearance(registry, query_xyz)` gives the exact point-to-triangulated-surface minimum distance (vox) per segment.
- `same_papyrus(triangles, window_xyz)` applies the fail-closed rule: vertex form (5 x 5 densified) OR surface form.
  SAME if >= 1000 points lie within 2 vox and count[0,1) >= 2 x count[2,3).
- Resolution limit: the surface is planar between lattice points (every 24 px for pairs0814, tile corners only for
  pairs0139). A binding certificate at that scale is re-run on the segment mesh; the registry keeps segment and
  canvas box for this.

Two readings of "128 vox plus a 64 px halo" are possible:
- (a) the patch is dilated by 64 px on its canvas, then the distance must be >= 128 vox;
- (b) the distance must be >= 192 vox.

Neither pairs layout stores the halo, so reading (a) needs the halo re-sampled from the mesh; (b) works on the
registry directly. The orchestrator declares which reading applies.
