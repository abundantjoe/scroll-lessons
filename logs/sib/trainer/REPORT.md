Provenance: Project HERCULES | owner the owner | [id removed]

# Trainer sibling report (task `trainer`)

STATUS: DONE

The D2 trainer is built and tested on synthetic data only. No real data was trained on. No image, rendered slice or
ink map was opened, written or described. Machine-readable version: `report.json`. Questions for the orchestrator:
`ASK.md` (9 items, each with the default I continue on). Proposal: `proposals/decl_d2_a1.txt`.

## 1. What was built (tools/sib/trainer/)

| File | Role |
|---|---|
| `d2_train.py` | Trainer (`make-config`, `train`, `bench`). Generalises tools/d3/d3_train.py; official villa 41701aa components; starts only from base ink_9um seed42 step-075000 (sha256 e635558a...9cab, checked at start). |
| `d2_data.py` | Data interface. Adapters: `pairs` (my schema, DATA_INTERFACE.md), `stagec` (pairs0814 layout), `tilegrid` / `tilegrid3` / `tilegrid4` (pairs0139 layout; k x k grid-aligned mosaics), `d3_pool`. Implements the DECL-D2 label rule (ink >= 150, blank <= 100, rest ignored), checked against the stored labels. Also writes the patch registry. |
| `ckpt_shards.py` | Resume state split into < 90 MB shards, stored as one parentless commit, force-pushed to a dedicated ref; fetch, verify and restore. |
| `contam_check.py` | CORR-RETRACE-RULE checks on the patch registry: point-to-triangulated-surface clearance, and the fail-closed same-papyrus rule (vertex OR surface form). |
| `bench_throughput.py`, `runlog.sh` | Throughput matrix; run logger (writes runs.jsonl). |

The flags cover task item 1:
- `--tile 128|384|512`, `--batch`, `--micro-batch`, `--steps`;
- `--rot24` (k x 15 deg: multiples of 90 deg exact; otherwise bilinear image and nearest labels, with pixels from outside the stored patch ignored);
- `--null` (one derangement over all pooled role=train patches: `default_rng(seed)`, redrawn until no fixed point);
- `--rev` (the 21-slice stack reversed in depth, labels unchanged);
- `--z-centre-offset` and `--z-jitter` (official 17-of-21 window, jitter +-2 by default);
- `--precision fp32|bf16` (bf16 training is refused unless the config carries an AMX gate record with `pass: true`);
- `--forward full|stitched`, `--subtile`;
- arm presets P128 / P384 / NULL / REV.

The checkpoint registry (`checkpoint_registry.json`, task item 3) holds:
- the config sha256 and lineage (base sha256, DECL);
- the data-registry sha256;
- the patch registries: `patch_registry_pool.npz` (every pool patch, the conservative set) and `patch_registry.npz`
  (the same, plus draw counts), with each patch's segment, canvas box and 3-D mesh lattice;
- the final model sha256.

The final model uses the D3 `model_final` format: `{'model', 'config': base config, 'step', 'd2': metadata}`, so the
official infer loads it.

## 2. Tests (26 passed, 0 failed; runs.jsonl label `pytest_all_2`, 775 s)

Run with `/opt/hv-ink/bin/python -m pytest -q tests/sib_trainer_units_test.py tests/sib_trainer_integration_test.py`.

- **D3 equivalence.** Arms CTRL, FA, NULLA and REVA were run by tools/d3/d3_train.py (paths redirected to synthetic
  pools) and by this trainer in the D3 layout. Per-step losses and final weights are **bitwise equal**.
- **Determinism** (task item 2). The same config and data twice give identical loss curves and bitwise-identical
  weights (fp32, 1 thread). Configurations tested: P128; NULL with micro-batching; REV with stitched forward. A
  different seed gives a different run.
- **Paired sampling.** P384, NULL and REV with one seed have an identical chained digest of the
  (patch, z offset, rotation) draws, and their losses differ.
- **Resume** (task item 4). Runs killed after step 3 (last save at step 2) were resumed two ways:
  - (a) from the local state;
  - (b) from the remote shards alone, after deleting the whole run directory (local bare git remote).

  Both give losses and final weights bitwise equal to an uninterrupted run. There is also a unit test: save, push,
  delete local, fetch, compare tensors bitwise.
- **Units.**
  - label rule;
  - registry sha256 tamper checks;
  - rotation (all 24 angles; 90 deg multiples exact; margin and padding);
  - sub-tile crop and padding;
  - shard cap and tamper checks;
  - `stagec` and `tilegrid` adapters (a label-rule mismatch is refused; mosaic pixel placement);
  - exact point-triangle distance (against brute force);
  - the half-cell re-trace, which is caught by the surface form;
  - clearance on synthetic sheets;
  - config rules.

## 3. Throughput (task item 6; synthetic data, batch 32, rotations on, 4 threads; throughput.json)

| Tile / forward | fp32 s/step (micro-batch) | bf16 s/step (micro-batch) | 12k steps fp32 | 12k steps bf16 |
|---|---|---|---|---|
| 128 | 11.94 (32), 7.2 GB | 6.79 (32), 5.1 GB | 39.8 h | 22.6 h |
| 384 full | 103.98 (4), 9.9 GB | 64.11 (8), 10.4 GB | 346.6 h (14.4 d) | 213.7 h (8.9 d) |
| 384 stitched | 103.66 (8), 4.4 GB | 62.17 (8), 3.7 GB | 345.5 h | 207.2 h |
| 512 full | 180.85 (2), 9.8 GB | failed | 602.8 h (25.1 d) | n/a |

From the AMX sibling's numbers (batch 8: fp32 2.87 s, bf16 1.57 s, bf16 + channels_last 1.41 s), scaled x4 for batch
32 and x9 for 384 px:
- P128: 38.3 / 20.9 / 18.8 h;
- P384, NULL, REV: 344 / 188 / 169 h.

These agree with my fp32 figures within 4 %. My bf16 figures are 8-12 % slower.

Totals for 12 arm-seeds: 135 session-days at fp32, 83 at bf16.

Failures:
- 384 fp32 at micro-batch 8, and 512 fp32 at micro-batch 4: OOM-killed.
- 512 bf16 at micro-batches 4 and 2: exited within 26 s and 19 s, before any step. There was no traceback and no OOM
  record, so this was probably a native crash (the driver did not keep the return code).
- 512 bf16 at micro-batch 1: no step finished in 3.6 h at 400 % CPU. I stopped it (rc -15).

## 4. Reclaim survival, measured on GitHub (task item 4)

- The ref is `refs/heads/claude/gifted-bell-gavnl5-sib-trainer-ckpt`, accepted by the orchestrator.
- A real full resume state (weights + AdamW + RNG) is 414,952,758 bytes, split into 5 shards of at most 90,000,000
  bytes. Save + push + prune took 90.3 s.
- The final weights (138,362,143 bytes, 2 shards) then replaced it.
- A fresh fetch returned them byte-identical (sha256 4e3572c7...). The ref holds exactly 1 commit.
- The ref currently holds only the final weights of a synthetic 2-step test run.
- Risk: superseded states stay on GitHub as unreachable objects. Pushing every 24 h would leave about 55 GB at fp32
  across 12 sessions, so ASK 6 proposes pushing every 72 h, subject to the owner's OK.

## 5. Findings the orchestrator needs before declaring D2

1. **Forward mode for P384 (ASK 1).**
   - The base architecture runs a 384 x 384 tile fully convolutionally.
   - Building the model from patch_size 384 changes the parameter shapes.
   - So official infer (128 px tiles, built from config) cannot use a "full" model's 384 px context. That needs a
     gated 384-tile inference path.
   - "stitched" keeps official inference and costs the same on CPU.
2. **Data layouts differ.** pairs0139 has 128 px tiles; pairs0814 has 384 px patches.
   - With `tilegrid3` and `--subtile`, every arm trains on the same pixels (ASK 3).
   - Rotation on 384 px patches ignores 11.4 % of pixels at P384 against 3.8 % at P128 (ASK 4).
   - P512 (D2b) cannot run on 384 px patches.
3. **FL-09 input under CORR-RETRACE-RULE.**
   - Clearances are exact point-to-surface distances on the registry lattice: every 24 px for pairs0814, tile corners
     for pairs0139.
   - Neither pairs layout stores the 64 px halo (ASK 5).
   - A binding certificate is re-run on the segment mesh.
4. **Optimiser (ASK 2).** Only the D3 fine-tune recipe (AdamW 2e-5, constant) is implemented. DECL-D2's "base recipe"
   must be pinned.
5. **Timeline (proposal section 6).**
   - D2 date = T0 + 11 d (bf16) or T0 + 18 d (fp32), where T0 is the pair freeze.
   - It meets the 2026-11-15 NOT-RUN default only if T0 <= 2026-11-04 (bf16) or <= 2026-10-28 (fp32).
   - bf16 needs the declared AMX gate first.

## 6. Commands (exact; also in runs.jsonl)

```
source: bash /work/setup_trainer_env.sh (villa 41701aa sparse vesuvius, /opt/hv-ink py3.13 torch 2.14.0+cpu, .pth path to
        villa src, hv-ink-freeze deps + scipy/scikit-image/... as D3's pylib, base ckpt from HF rev 7109667e, sha256 verified)
tests:  /opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider --basetemp=/work/sib/pt3 tests/sib_trainer_units_test.py tests/sib_trainer_integration_test.py
bench:  /opt/hv-ink/bin/python tools/sib/trainer/bench_throughput.py --steps 3 --with-512
push:   d2_train.py make-config --arm P128 --seed 1 --batch 1 --steps 2 --threads 4 --ckpt-every 1 --log-every 1 \
          --remote-ref refs/heads/claude/gifted-bell-gavnl5-sib-trainer-ckpt --source syn=pairs:/work/sib/bench/syn560/registry.json --out /work/sib/pushcfg.json
        d2_train.py train --config /work/sib/pushcfg.json --out /work/sib/pushrun
        ckpt_shards.py fetch --remote-url <origin> --ref refs/heads/claude/gifted-bell-gavnl5-sib-trainer-ckpt --out /work/sib/fetched_final.pth
D2 arm: d2_train.py make-config --arm P384 --seed 1 --subtile --micro-batch 4 --forward <F384> --remote-ref refs/heads/<branch>-ckpt \
          --source p0139=tilegrid3:<dir> --source p0814=stagec:<dir> --hash-sources --out cfg.json
        nohup d2_train.py train --config cfg.json --out /work/d2/<arm>_s1 &     (re-run the same command to resume)
```

## 7. Deviations and failures (all recorded)

- **Environment setup.**
  - The editable install of villa vesuvius was refused (it requires Python 3.14; the venv is 3.13). I used a `.pth`
    path entry, equivalent to TOOLING.md's `--ignore-requires-python`.
  - pytest needed pygments.
- **Denied action.** One read-only grep over villa's augmentation source was denied by the session's safety check. I
  did not work around it. Completeness of the RNG state was instead shown empirically by the bitwise resume tests.
- **Test and make-config defects**, fixed and logged:
  - rotation coverage in a test;
  - bilinear tolerance in a test;
  - defaults for custom arm names in make-config.
- **Superseded helper.** A point-to-sampled-point FL-09 helper was replaced after CORR-RETRACE-RULE and removed.
- **Retroactive log rows.** Retroactive runs.jsonl rows (marked, output not captured) cover runs made before
  runlog.sh existed.
- **Code changes during the bench.** `d2_train.py` changed while the bench was running (sample digest, sub-tiles,
  adapters). All of these are logging or off-by-default paths, so the timed code path did not change.

## 8. What the orchestrator needs to declare next

- Answer ASK 1-9, or accept the defaults.
- Declare DECL-D2-A1: the CPU session plan and D2 date, the F384 mode (and the 384-tile inference gate if "full"),
  the optimiser, the filters as allowlists, the FL-09 reading, the precision, and the push interval.
- Freeze the trainer hashes (report.json `code_sha256`).
- Launch the seed-1 sessions once both pair registries are final.

## Addendum 2026-09-26 ~00:50Z (after the interim rulings)

STATUS: DONE (support round complete; waiting for the pair freeze).

1. **Q6 (no weights on git).**
   - `d2_train.py` now refuses any network remote for the shard store. Only a local bare repo path is accepted
     (unit test `test_network_remote_weights_refused`).
   - My deletion of `refs/heads/claude/gifted-bell-gavnl5-sib-trainer-ckpt` was refused by the session's safety
     check ([Git Destructive]). I did not work around it. That ref holds a 138 MB synthetic 2-step test model, and
     the owner or orchestrator should delete it.
2. **Q1 check.** `full_conv_check.json`: the unchanged base (strict load, "All keys matched") runs 17 x 384 x 384
   and 17 x 512 x 512 inputs fully convolutionally, with finite outputs and a working backward pass. So "full" mode
   satisfies the ruling's condition. Full and stitched outputs differ (max abs 2.0 / 2.1 logits), as expected from
   the different context.
3. **New `blockpairs` adapter** for the pairs0814 / 0814b stage-B layout. It was verified on the real pairs0814
   commit c5fe80c (load and hash checks only, no training): 329 patches, 11 segments, 0 label-rule mismatches.
4. **`pair_freeze.py` and PAIR_FREEZE_SPEC.md.** The pair-freeze record holds:
   - the registry and data-file sha256s of pairs0139/0139b/0139c/0814/0814b;
   - in-block and out-of-block counts;
   - the D2 date;
   - hold-out lists;
   - the allowlists consumed by the arm configs.

   A dry run on pairs0814 is in `freeze_dryrun/` (DRY RUN, not a freeze).
5. **Tests.** The full suite, re-run after the Q6 guard (runs.jsonl `pytest_all_3`, 00:45:04Z-01:00:07Z): **29 passed,
   0 failed**, 902 s. That is 17 unit tests + 12 integration tests, including D3 bitwise equivalence, determinism and
   bitwise resume.


## Addendum 2026-09-26 ~05:40Z

STATUS: DONE (preparation on the stated defaults; synthetic data only for training; no real-data training step).

1. **Q1 stays OPEN**, per the orchestrator at 05:25Z. `param_diff_384.json` compares two builds:
   - the base-config build: patch 128, strict load OK, fully convolutional at 384 and 512 per `full_conv_check.json`;
   - a build from patch 384.

   The patch-384 build has 614 vs 508 state tensors: +106 new tensors (encoder stage 6: 96; decoder stage 5: 8;
   transposed conv 5: 2) and 40 shape mismatches, 146 in total. It has 47,871,298 vs 34,546,498 parameters
   (+13,324,800), and strict loading of the base weights fails.
2. **Freeze spec, pairs0814 layout.** The `stagec` adapter and pair_freeze now handle the final stage C, whose shards
   are the staged block files on two branches: `data_root`, pair_registry.json for segments, listed patch_ids only.
   The real union dry run gives 564 patches, 180/180 file hashes and 0 label mismatches, and matches the pairs0814
   summary. Hold-out candidate lists per rule come from `holdouts_from_registry.py`.
3. **Tests.**
   - 19 unit tests pass (runs.jsonl `units_holdouts`).
   - The last full suite ran 29/29 (`pytest_all_3`, before this round's adapter change).
   - The integration tests do not use the `stagec` adapter; it is covered by its unit tests.
4. **Unchanged.** The ckpt test ref still needs deletion by the owner or orchestrator: my delete was refused and I
   did not work around it. I made no deletion without approval.
