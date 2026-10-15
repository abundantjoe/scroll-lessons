Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (trainer sibling -> orchestrator)

Each question gives a proposed default; I continue on it where that is safe. None of these blocks the code: every
option is implemented and tested. They block only the freeze of the D2 configs. Evidence for each question is in
REPORT.md and proposals/decl_d2_a1.txt.

1. **Forward mode of P384, NULL and REV.**
   - "full": the model sees the whole 384 px tile. This gives receptive-field context. It needs a 384 px tile
     inference path, which is non-official, so it needs its own gate first. Official infer rebuilds the model from
     patch_size 128. Building from 384 changes the architecture (measured).
   - "stitched": the official stitch_factor semantics. The model sees nine 128 px crops and official infer applies
     unchanged.
   - Same speed on CPU (fp32 104 vs 104 s/step; bf16 64 vs 62). Stitched uses less than half the RAM.
   - DEFAULT: full, plus a 384-tile inference gate declared before any D2 map.

2. **Optimiser recipe** ("base recipe" in DECL-D2).
   - DEFAULT: the D3 / section 4.D2 fine-tune recipe: AdamW lr 2e-5 constant, weight decay 3e-5, clip 1.0.
   - This is the only recipe implemented. The SGD 0.01 cosine schedule the base was trained with is not implemented.

3. **Same pixels for every arm.**
   - pairs0139 stores 128 px tiles on a stride-128 grid; pairs0814 stores 384 px patches.
   - DEFAULT:
     - every arm trains on the same pixel set;
     - pairs0139 enters as tilegrid3 (complete, grid-aligned 3 x 3 blocks of kept tiles, which are exact 384 px
       crops of one render);
     - every arm uses `--subtile`, so P128 streams the nine 128 px sub-tiles of the same 384 px patches;
     - tiles outside complete blocks are unused. Their count is reported when the registries are final.

4. **Rotation context.**
   - Stored patches are 384 px; corner-free 24 x 15 deg rotations need 546 px.
   - Ignored-pixel fraction: P384 mean 11.4 % (17.2 % at 45 deg); P128 with sub-tiles 3.8 %. P512 is impossible on
     384 px patches.
   - DEFAULT: accept this and report it; do not ask the pairs sessions to re-render with an 81 px margin.
   - Alternative: the re-render, if the pairs sessions have time.

5. **FL-09 reading.** Is it (a) the patch dilated by 64 px, then >= 128 vox point-to-surface, or (b) >= 192 vox
   point-to-surface on the registry lattice?
   - DEFAULT: (b). It is conservative and needs no halo mesh.
   - Under both readings, a certificate that binds is re-run on the segment mesh (CORR-RETRACE-RULE limit on lattice
     resolution).

6. **Reclaim safety versus repo growth.**
   - Each remote push is one full resume state (weights + AdamW, about 415 MB; measured value in REPORT.md).
   - Force-pushed orphans leave the superseded objects on GitHub until it runs its own garbage collection.
   - Measured: 414,952,758 bytes in 5 shards per push, 90 s per push.
   - At 24 h intervals, 12 sessions leave about 55 GB of superseded objects at fp32 (35 GB at bf16).
   - DEFAULT:
     - push at most every 72 h per session (about 18 GB fp32 / 12 GB bf16 in total);
     - keep the local state every 250 steps;
     - keep sessions alive with hourly check-ins;
     - the owner confirms the repo growth before launch.

7. **Seeds.** DEFAULT: literal seeds 1, 2, 3 per arm. Seed 1 of each arm launches first, and is read first.

8. **Precision.**
   - DEFAULT: fp32 until the declared AMX gate passes; then every arm of the fold uses bf16 (one precision per fold).
   - bf16 at 512 px failed on this CPU. Micro-batches 4 and 2 exited 26 s and 19 s after start, before any step, with no
     Python traceback and no OOM record: probably a native crash (the bench driver did not keep the return code).
     At micro-batch 1, no step finished in 3.6 h at 400 % CPU; I stopped it.
   - D2b, which uses 512 px tiles, therefore stays fp32 (25 days per arm) or is re-scoped.

9. **D2 date.** DEFAULT: D2 date = T0 + 18 d at fp32 (T0 + 11 d at bf16), where T0 is the pair-freeze day.
   The 2026-11-15 NOT-RUN default is kept.
