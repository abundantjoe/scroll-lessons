Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (task devloop-r1)

Each question gives my proposed default. I continue on every default that is safe under the integrity rules.

1. **Training data is not available yet.** The pairs0139 branch has no shards or registry yet (last commit e85bcb9, 2026-09-25 ~19:30Z).
   Default: all code is built and tested on synthetic data, and training starts as soon as the shards appear. The input contract is the one in `build_pairs.py` at e85bcb9.
   - How do I receive the shards? They are 200-tile npz files, too big for git.
   - Default: if the pairs sibling pushes them to a single-commit ref, I fetch that. Otherwise I need an S3/HF-free transfer path from you.

2. **Neighbour images for the 3 x 3 context.** Shards hold only kept tiles. A neighbour that failed a gate or is ignored has no image, so the context block sees a learned "missing" token. At inference nearly all neighbours exist, so training and inference differ here.
   - Default: ask pairs0139 to also store unlabelled image stacks (21 x 128 x 128 uint8, no label) for every render-valid, non-Rule-S tile adjacent to a kept tile, in `ctx_*.npz` shards with registry rows.
   - Until then: train with the missing token. The measured fraction of present neighbours is logged at every step.

3. **Hold-out check.** `lc_pool.py` rejects fail-closed. On top of pairs0139's rules N and S, it independently checks every tile's own surface (4 px samples) against every 0139 DEV-window surface (2 px samples).
   - It requires at least 16 vox clearance: 11 vox (rule S) plus the sampling half-diagonals.
   - It also requires the tile centre to reproduce the builder's recorded `xyz_centre` within 0.5 vox, and at least 90 % of the tile's samples to be valid.
   - DEV segments, pairs0139-excluded segments and every DEV hold-out segment are dropped whole.
   - Default: this is the pool rule. Tell me if DEV clearance must be larger (for example 144 vox, as for J).

4. **Evaluation needs the devloop evaluator's prepared windows** (`/work/devloop/win/<id>/render.zarr`, `ref9.npy`, `valid.npy`), which exist only on the devloop sibling's container.
   - Default A (preferred): the devloop sibling or the orchestrator runs my maps. `tools/sib/devloop-r1/lc_infer.py` has the official CLI's argument order and output contract, and at initialisation it is bitwise equal to the official CLI. The evaluator's `infer_window` needs a one-line switch to call it for LC checkpoints.
   - Default B: I run `evaluate.py prep` myself at a pinned devloop commit. That needs the Docker VC build (about 15 min) and DEV-window renders from S3. It maps only DEV windows (0139 controls w024, w047, w053; 0814 DEV segments), never 0841, J or eligible data.
   - I proceed with B only if you say so.

5. **Recipe defaults for the first ranking run**, used unless changed:
   - variant 'basedec': context block plus the fine-tuned base decoder and head;
   - fp32, 2000 steps, batch 8;
   - AdamW with lr 1e-4 for new modules and 2e-5 for the base decoder, wd 3e-5, clip 1.0, seed 20260925;
   - fp16 feature cache (measured cost: at most 1 grey level on maps);
   - no augmentation, since input-space augmentation cannot act on cached features.
   - Arms: RECIPE, NULL (label derangement) and REV (depth-reversed cache).
   - 'light' (frozen base decoder plus a zero-init light head) is the second candidate.

6. **bf16.** DECL-AMX-1's scope is the D3 recipe class (batch 8, lr 2e-5, 2000 steps). LC384 uses lr 1e-4 on new modules, so it falls outside that scope even after a PASS.
   Default: LC384 trains in fp32 unless you extend the scope.

7. **Checkpoints.** A trainable-only checkpoint is about 35 MB ('basedec') and is committed as-is. Anything over 90 MB goes to a single-commit ref `claude/gifted-bell-gavnl5-sib-amx-ckpt`.
   Default: no ckpt ref until a checkpoint exceeds 90 MB.

STATUS: not done. Blocked on 1 (data) and 4 (evaluation path); everything else is built and tested.
