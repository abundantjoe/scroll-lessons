Provenance: Project HERCULES | owner the owner | [id removed]

STATUS: DONE (open decisions with defaults in `logs/sib/amx/ASK.md`)

# Sibling task amx: AMX bf16/int8 speed of the official base ink model, and the equivalence gate

Date: 2026-09-25, 18:20-19:31Z. Container: 4 vCPU Intel Xeon 2.1 GHz with AMX-BF16/INT8 (1 thread per core), 15 GB RAM, no GPU.

Scope and integrity:
- Every model input here is random (N(0,1) tiles, or a random uint8 volume). No scroll data was read, rendered, inferred or mapped.
- No image was opened or viewed.
- Nothing touched PHerc0841, the J windows, seals, readers or any eligible volume.
- Machine-readable roll-up: `logs/sib/amx/report.json`, with the sha256 of every result file and script. Every command is in `logs/sib/amx/runs.jsonl`, which holds the utc, command, exit code and output sha256; the outputs are in `logs/sib/amx/out/`.

## Summary

| Question | Answer (measured) |
|---|---|
| Is AMX actually used? | Yes. With bf16 autocast, oneDNN 3.12 dispatches `brg_conv_fwd:avx10_1_512_amx` for every conv and deconv. fp32 runs on `jit:avx512_core`. |
| bf16 inference speed-up (batch 4) | 1.60-1.74x at the same memory format (two passes). At 4 threads, fp32 takes 0.345-0.347 s per batch (0.087 s per tile) and bf16 takes 0.199-0.217 s. |
| bf16 full training step speed-up (batch 8, D3 recipe) | 4 threads: 1.83-2.06x (fp32 2.76-2.87 s, bf16 1.34-1.57 s). 1-2 threads: 2.1-2.5x. |
| channels_last | Never helps fp32 (0.85-1.01x). With bf16 it gains up to about 10 % at 4 threads, which is within run-to-run noise. Not worth adopting. |
| Peak RSS | Inference: fp32 about 830 MB, bf16 about 735 MB. Training: fp32 about 2.79 GB, bf16 about 2.13 GB. |
| int8 | Not feasible in the pinned environment. Dynamic quantization is a no-op (0 Linear modules), FX tracing fails, and PT2E needs `torchao` (not installed). |
| Where the time goes | The 3-D stem (7,425 params, 24 % of FLOPs) takes 55 % of fp32 inference time and 60 % of the training step. |
| Frozen-encoder cache | Bitwise equal to the full model: max \|diff\| = 0 in fp32 and in bf16, also after re-batching. A decoder-only training step is 14.6x (fp32) or 13.3x (bf16) faster than a full step. With the new 3 x 3-tile letter-context block it is 8.3x or 7.7x faster. |
| bf16 equivalence (forecast) | End to end through the official CLI on a random volume: Pearson 0.9994 / 0.9991, but only 98.18 % / 97.72 % of pixels within +-2 grey levels, max \|diff\| 5 / 7. The proposed 99.9 % bar would FAIL on this input. |

## 1. Environment bootstrap (item 1)

Rebuilt in this fresh container per `docker/TOOLING.md` and `docker/env/setup_env.sh` (Docker and the C++ apps are not needed here). Commands are in `runs.jsonl` under the `boot_*` tags.

- Villa: sparse clone of ScrollPrize/villa at `41701aa0eaa1aa765523db3f9f972b5830abf549` (`vesuvius`, `ink-detection`), under `/work/villa`.
- `/opt/hv-ink`: Python 3.13.12 with torch 2.14.0+cpu and torchvision 0.29.0+cpu from download.pytorch.org.
  - `vesuvius` was installed editable with `pip --ignore-requires-python --no-deps`. The first two attempts failed because uv cannot ignore the `>=3.14` pin; they are logged as `boot_pip` and `boot_pip2`.
  - The rest came from `docker/env/hv-ink-freeze.txt` with `--no-deps`.
  - `uv pip freeze` matches the freeze exactly, apart from name normalisation (for example `huggingface-hub` / `huggingface_hub`) and the added `pip`.
- The official trainer imports `cc3d`, which is not in the freeze. I followed the D3 timing-test precedent (`logs/d1/d3_timing.json`): the same versions were installed with `--no-deps --target /work/amx/pylib` (scipy 1.18.1, scikit-image 0.26.0, lazy_loader 0.6, fft-conv-pytorch 1.2.0, SimpleITK 2.5.6, pandas 3.0.6, connected-components-3d 4.1.0, numba 0.67.0, llvmlite 0.49.0).
- `/opt/hv` (Python 3.11 test env per `setup_env.sh` step 4) was created for pytest and the gate.
- Checkpoint (item 2): HF `scrollprize/ink_9um` at revision 7109667e..., file `hybrid_3d2d-seed42/step-075000.pth`, 138,360,039 B.
  - sha256 `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab`: verified OK (`boot_ckpt`). It matches D0-HW and DECL-C3.
  - Every benchmark re-verifies the hash on load (`tools/sib/amx/common.py`). The weights load with `strict=True`.
- AMX check (`out/onednn_isa.log`): oneDNN v3.12.0 reports "Intel AVX10.1 and Intel AMX with bfloat16 and 8-bit integer support".
  - bf16 forward: 60 x `brg_conv_fwd:avx10_1_512_amx`, 6 x `brgconv_1x1:avx10_1_512_amx`, 5 x `brg_deconv:avx10_1_512_amx`.
  - fp32 forward: the same layers on `jit:avx512_core`.

## 2. Speed grid (item 3)

Script: `tools/sib/amx/bench.py`, driven by `run_grid.sh`.
- One process per configuration, pinned with `taskset` to cores 0..N-1, with `OMP_NUM_THREADS` = `torch.set_num_threads` = N.
- 5 warm-up and 20 timed iterations. Median, IQR and peak RSS (`ru_maxrss` of the whole process, model included).
- Inputs are random, shaped as in the checkpoint config: (B, 1, 17, 128, 128).

Inference: `model.eval()`, `torch.inference_mode()`, batch 4.

Training: exactly the `tools/d3/d3_train.py` step (D3 recipe), batch 8. The config batch is 64; batch 8 was used as the task specifies.
- Official `prepare_model_input`, `run_model_forward`, `prepare_loss_inputs` and `concatenate_deep_supervision_ignore`.
- Loss: `create_loss` (smoothed BCE 0.5 + 0.25 Dice with the ignore channel) on `.float()` logits.
- Backward, `clip_grad_norm_(1.0)`, then the official `create_training_optimizer` (AdamW, lr 2e-5, wd 3e-5).
- Random labels: 30 % ink, 95 % supervised.

bf16 means `torch.autocast('cpu', dtype=torch.bfloat16)` around the forward only. AdamW keeps fp32 master weights and no grad scaler is used.

CL means channels_last_3d for the stem and input, and channels_last for the 2-D network, including its input via a pre-hook.

Pass 1 (`bench_grid.jsonl`):

| mode | thr | CL | batch | fp32 median s (IQR) | bf16 median s (IQR) | bf16/fp32 speed-up | vs fp32 contiguous | fp32 CL gain | peak RSS fp32 / bf16 MB |
|---|---|---|---|---|---|---|---|---|---|
| infer | 1 | no | 4 | 1.003 (0.018) | 0.578 (0.036) | 1.74x | 1.74x | - | 831 / 730 |
| infer | 1 | yes | 4 | 1.179 (0.076) | 0.579 (0.022) | 2.04x | 1.73x | 0.85x | 816 / 739 |
| infer | 2 | no | 4 | 0.612 (0.046) | 0.353 (0.040) | 1.73x | 1.73x | - | 796 / 732 |
| infer | 2 | yes | 4 | 0.686 (0.038) | 0.338 (0.033) | 2.03x | 1.81x | 0.89x | 836 / 738 |
| infer | 4 | no | 4 | 0.347 (0.025) | 0.217 (0.027) | 1.60x | 1.60x | - | 827 / 731 |
| infer | 4 | yes | 4 | 0.381 (0.031) | 0.204 (0.033) | 1.86x | 1.70x | 0.91x | 836 / 734 |
| train | 1 | no | 8 | 9.307 (0.408) | 3.933 (0.080) | 2.37x | 2.37x | - | 2784 / 2119 |
| train | 1 | yes | 8 | 9.630 (0.569) | 4.204 (0.111) | 2.29x | 2.21x | 0.97x | 2795 / 2135 |
| train | 2 | no | 8 | 5.688 (0.457) | 2.265 (0.081) | 2.51x | 2.51x | - | 2774 / 2126 |
| train | 2 | yes | 8 | 5.638 (0.177) | 2.333 (0.135) | 2.42x | 2.44x | 1.01x | 2787 / 2139 |
| train | 4 | no | 8 | 2.872 (0.259) | 1.571 (0.218) | 1.83x | 1.83x | - | 2790 / 2123 |
| train | 4 | yes | 8 | 2.924 (0.405) | 1.409 (0.078) | 2.08x | 2.04x | 0.98x | 2807 / 2140 |

Pass 2 (`bench_grid_rep.jsonl`) repeated the whole grid with nothing else running. It gives bf16/fp32 speed-ups of:
- infer (no CL): 1.70x at 1 thread, 1.70x at 2 threads, 1.74x at 4 threads;
- train (no CL): 2.14x at 1 thread, 2.32x at 2 threads, 1.98x at 4 threads.

Run-to-run reproducibility of the medians between the two passes is median |rel diff| 3.3 %, max 12.4 % (infer bf16, 4 threads, CL). Pass 1's 1- and 2-thread inference rows overlapped light side jobs pinned to core 3 (a venv install, pytest, a shape probe). Pass 2 had none. Quote speed-ups as ranges over both passes.

Consequences at 4 threads, compute only:
- One 2 x 2 cm window, both orders (2178 tiles): fp32 about 3.2 min, bf16 about 1.8 min.
- A 2000-step D3-recipe fine-tune: fp32 about 1.6 h, bf16 about 0.75-0.87 h.
- The D3 runs used 3 threads (3.1 s per step fp32).

int8 feasibility, report only (`int8_feas.py`; results in `int8_feas.json` and `int8_feas_fxparts.json`):

| Attempt | Result |
|---|---|
| Dynamic (`quantize_dynamic`, {Linear}) | Runs, but it is a no-op. The model has 0 Linear and 71 conv/deconv modules, so the output is bitwise equal to fp32 and the time is the same (0.326 s against 0.360 s fp32 in the same process, which is noise). Dynamic quantization has no conv path. |
| FX static PTQ, whole 2-D network | FAIL: `TraceError: symbolically traced variables cannot be used as inputs to control flow`, raised by input checks in `NetworkFromConfig.forward`. |
| FX static PTQ, encoder and decoder sub-modules | FAIL: `TypeError: float() argument must be ... not 'Proxy'` at `vesuvius/models/build/encoder.py:163` (`alpha = float(feature_gate_alpha)`). |
| PT2E (`X86InductorQuantizer`) | FAIL: `torch.ao` PT2E has moved to `torchao`, which is not in the pinned environment. I did not install it: it is an unpinned new dependency, and that choice belongs to the orchestrator. |

Verdict: int8 is not feasible without new dependencies or tracing-friendly model code. Given the bf16 fidelity in section 5, int8 fidelity would also be expected to be worse.

## 3. Time and FLOP split per module (item 4)

Script: `tools/sib/amx/profile_split.py` (output `profile_split.json`), 4 threads.
- The model's forward is run piecewise:
  - stem = `depth_fusion` (the only 3-D part: 2 Conv3d plus attention/max depth pooling);
  - enc2d = the 2-D residual encoder;
  - dec2d = the 2-D decoder plus the 1x1 head.
- The piecewise output equals `model(x)` bitwise (max |diff| 0, in fp32 and bf16).
- Training backward runs through detached boundary leaves, so each segment's backward is timed separately.
- FLOPs come from `torch.utils.flop_counter` (conv, matmul and deconv only).

| | stem (3-D) | enc2d | dec2d + head | total |
|---|---|---|---|---|
| Params | 7,425 | 30,216,608 | 4,322,465 | 34.55 M |
| Forward GFLOP per tile | 4.10 | 10.11 | 2.91 | 17.12 |
| FLOP share (forward; backward is the same to +-0.5 %) | 23.9 % | 59.1 % | 17.0 % | |
| Inference fp32, batch 4: s (share) | 0.207 (55 %) | 0.123 (33 %) | 0.041 (11 %) | 0.376 |
| Inference bf16, batch 4: s (share) | 0.123 (59 %) | 0.071 (34 %) | 0.015 (7 %) | 0.209 |
| bf16 speed-up | 1.68x | 1.74x | 2.80x | 1.80x |
| Achieved GFLOP/s, fp32 / bf16 | 79 / 133 | 330 / 574 | 284 / 797 | |
| Training fp32, batch 8: fwd / bwd s | 0.357 / 1.229 | 0.245 / 0.483 | 0.091 / 0.142 | 2.619 (AdamW 0.054) |
| Training bf16, batch 8: fwd / bwd s | 0.238 / 0.594 | 0.117 / 0.224 | 0.027 / 0.066 | 1.356 (AdamW 0.054) |
| Share of training step, fp32 / bf16 | 60.5 / 61.4 % | 27.8 / 25.1 % | 9.0 / 7.0 % | AdamW 2.1 / 4.0 % |

Reading:
- The 3-D stem is the bottleneck. At 16 channels on a 17 x 128 x 128 volume, with InstanceNorm3d, it has low arithmetic intensity and reaches only 79 GFLOP/s, about a quarter of the 2-D encoder's rate.
- AMX helps the stem least (1.68x inference). Its backward alone is 47 % of an fp32 training step.
- Any further CPU speed-up has to come from the stem, and that would mean changing the official model code (outside this task).

## 4. Frozen-encoder cached-feature path (item 5)

Script: `tools/sib/amx/cache_path.py` (output `cache_path.json`), 4 threads.
- Encoder = stem + 2-D encoder (30.22 M params). Decoder = 2-D decoder + head (4.32 M).
- The cache stores the six encoder skips per tile: 32x128², 64x64², 128x32², 256x16², 320x8² and 320x4², i.e. 1,008,640 values. That is 4.04 MB (fp32) or 2.02 MB (bf16) per tile on disk, 3.6x or 7.2x the raw input's 278,528 values.

Equivalence on 16 random tiles, eval mode. The cache was written to disk and reloaded.

| Comparison | max \|logit diff\| | uint8 map max \|diff\| | uint8 within +-2 |
|---|---|---|---|
| fp32 cached vs fp32 full, same batching (4) | **0** | 0 | 100 % |
| fp32 cached vs fp32 full, re-batched to 8 and to 1 | **0** | 0 | 100 % |
| bf16 cached vs bf16 full (same, re-batched 8, re-batched 1) | **0** | 0 | 100 % |
| bf16 full vs fp32 full (single tiles, no blending) | 0.0893 (mean 0.0137) | 6 | 96.58 % (39.6 % identical) |
| fp32 decode of bf16-stored fp32 features vs fp32 full | 0.00236 | 1 | 100 % (98.3 % identical) |

- Storing the cache in bf16 halves the disk use and costs at most 1 grey level.
- Running the model in bf16 costs up to 6 grey levels.

Training throughput, batch 8, D3 recipe (official loss, clip 1.0, AdamW), 4 threads:

| Step | fp32 median s | bf16 median s | tiles/s fp32 / bf16 | 2000 steps (h) fp32 / bf16 | vs full step, same dtype |
|---|---|---|---|---|---|
| B1: full model (reference) | 2.983 | 1.332 | 2.7 / 6.0 | 1.66 / 0.74 | 1x |
| B2: decoder-only from cache | 0.205 | 0.100 | 39 / 80 | 0.11 / 0.06 | 14.6x / 13.3x |
| B3: decoder + letter-context block from cache | 0.358 | 0.172 | 22 / 46 | 0.20 / 0.10 | 8.3x / 7.7x |
| One-off: encoder pass to build the cache (inference, per tile) | 0.067 | 0.032 | | | |

The letter-context block is a new prototype of 4.35 M params, defined in `cache_path.py`.
- It takes 3 x 3 adjacent 128 px tiles, i.e. 384 px of context.
- It stitches the cached level-4 (320 x 8²) and level-5 (320 x 4²) skips of the nine tiles into 24² and 12² mosaics.
- At each level it applies two 3x3 conv blocks (dilation 1 and 2; InstanceNorm and LeakyReLU as in the base model). Level 5 also gets 8-head self-attention over the 144 mosaic cells, which covers the full 384 px.
- A zero-initialised 1x1 projection adds the centre-tile crop back to the centre tile's skips, which then go through the base decoder.
- Validation: at initialisation the block is an exact identity. Decoder output with and without it: max |diff| = 0 in fp32 and in bf16.

Caveats before anyone relies on this path:
1. The official augmentations act on the input volume (flips, rotations, intensity) and cannot be applied to cached features. The only exception is caching every dihedral variant, which costs 8x storage.
2. The cache is on a 128 px grid. The official inference blends at stride 64 with Hann weights, which would need 4x the tiles.
3. Decoder-only training cannot adapt the stem, which is where the depth information enters.
4. Cache size for a D3-sized pool of 3000 tiles is 6.1 GB in bf16. Neighbours for the context block need only levels 4 and 5 (25,600 values, about 51 KB per tile in bf16).

Measurable validation for any future use:
- the identity-at-init check (max |diff| 0);
- the cached-vs-full bitwise check on the actual cache files;
- a held-out loss parity check against full fine-tuning under the D3 recipe.

## 5. Equivalence gate (item 6) and precision forecast

`tools/sib/amx/amx_gate.py` (sha256 `3138ce1c...60b1`).
- Inputs: fp32 and bf16 uint8 map pairs (forward, and optionally reverse), labels and a valid mask, as .npy or .tif.
- Pearson and AUC use `hercules.metrics.pixel` (the code hashed in DECL-C3).
- Label rule as `tools/c3/auc_eval.py`: ink = label > (min + max)/2, blank = label == 0, other values ignored.
- Outputs:
  - Pearson per order, bf16 forward/reverse AUC, and fp32 AUC with the delta;
  - fraction within +-2 grey levels, max and mean |diff|, and a |diff| histogram;
  - input sha256s, the verdict (PASS / FAIL / INCOMPLETE) and the code's own sha256.
- Unit tests `tests/sib_amx_test_gate.py`: **12 passed** (`source /opt/hv/bin/activate && PYTHONPATH=src pytest -q tests/sib_amx_test_gate.py`; `out/pytest_gate.log`). The file name was set by the task and does not match pytest's default `test_*.py` pattern, so it runs only when named explicitly. The repo suite also passes (585 passed, 6 skipped; `out/pytest_all.log`). The tests cover:
  - identity, jitter, and Pearson against numpy;
  - the within-2 bar both failing and at the inclusive boundary;
  - invalid-pixel masking;
  - the reverse- and forward-AUC bars;
  - INCOMPLETE when the reverse pair is missing, and type/shape errors;
  - C3 label binarisation;
  - the CLI end to end, with input hashes.

Full-chain smoke on synthetic data (`synth_chain.py`, output `synth_chain_gate.json`).
- Input: a random uint8 volume, 21 x 640 x 640 (sha256 `f3e71f91...6213`).
- The fp32 run is the official CLI with the C2-NT flags (`--direction both --batch-size 4 --num-workers 1 --no-compile`, 4 threads).
- The bf16 run is `tools/sib/amx/infer_bf16.py` (sha256 `fe77a9a8...b188`). It runs the unchanged `infer.main` inside CPU bf16 autocast, because the official CLI autocasts only on CUDA (`infer.py:748`).
- The fp32 chain is **bitwise deterministic** across two runs (identical map sha256s, both orders).
- bf16 against fp32, all 409,600 pixels:

| order | Pearson | max \|diff\| | mean \|diff\| | identical | within +-2 | \|diff\| histogram 0/1/2/3/4/5+ |
|---|---|---|---|---|---|---|
| forward | 0.99943 | 5 | 0.563 | 53.6 % | **98.18 %** | 219382 / 158346 / 24410 / 6617 / 816 / 29 |
| reverse | 0.99910 | 7 | 0.670 | 46.7 % | **97.72 %** | 191445 / 174559 / 34250 / 6640 / 2025 / 681 |

The gate verdict on this input is FAIL: within-2 is below 99.9 %, and the AUCs fail as expected because the labels are synthetic.

Which segment causes the drift (`precision_ablation.py`, output `precision_ablation.json`; 32 random tiles, batch 4, 4 threads, no blending):

| bf16 segments | within +-2 | max \|diff\| | speed-up vs fp32 |
|---|---|---|---|
| none (fp32) | 100 % | 0 | 1.00x |
| decoder only | **100 %** | 2 | 0.99x |
| encoder only | 99.43 % | 5 | 1.18x |
| encoder + decoder | 99.53 % | 5 | 1.31x |
| stem only | 98.63 % | 5 | 1.26x |
| stem + decoder | 98.62 % | 6 | 1.37x |
| stem + encoder | 96.62 % | 7 | 1.54x |
| all | 96.06 % | 7 | 1.76x |

Reading: no bf16 placement both speeds up inference and keeps 99.9 % of pixels within +-2 on random input. The stem, which does the depth softmax and max pooling, contributes the most drift.

Random N(0,1) input is out of distribution for real robust_mad-normalised papyrus, so this is a forecast, not a result. The forecast is that the inference gate fails bar (d) and C2-NT stays fp32. Only the declared gate on the w044 crop can decide.

## 6. Proposal (item 7)

`logs/sib/amx/proposals/decl_amx_1.txt` (draft, not declared). It covers:
- **AMX-INF**:
  - the C3 bars on the C3-NT-R1 w044 crop: Pearson >= 0.999, forward AUC >= 0.987 and reverse AUC < 0.60, each for the bf16 map;
  - plus >= 99.9 % of valid pixels within +-2 grey levels, in each order;
  - an fp32 reference that must reproduce the C3-NT-R1 map sha256s bitwise (`1d540b92...`, `addbb866...`).
- **AMX-TRAIN**:
  - a paired bf16 re-run of the D3 CTRL recipe (DECL-D3-A1, DECL-D3-A2) against the existing fp32 CTRL run;
  - bar: final-window loss within 2 %;
  - the window is set to the last 200 steps. The reason, measured from the committed CTRL log: consecutive 50-step window means move by median 0.7 % and up to 3.0 %, so a single 50-step window would put a 2 % bar inside the run's own noise.
- The forecast above, disclosed before declaration.

## Failures and deviations (all logged)

- `boot_pip`, `boot_pip2` (exit 1): uv cannot ignore `requires-python >=3.14`. Fixed by installing pip into the venv and using `--ignore-requires-python`, as TOOLING.md did.
- The first `bench.py` training smoke failed with `ModuleNotFoundError: cc3d`. Fixed with the D3-precedent side target `/work/amx/pylib`.
- `synth_chain` failed twice (exit 1), both in the gate step, while the maps themselves were fine:
  - the py3.13 side-library path leaked into the py3.11 gate;
  - `/opt/hv` has no `imagecodecs` for the official LZW TIFFs. Fixed by converting to .npy in hv-ink, as `tools/c3/tif2npy.py` does.
- int8 FX and PT2E attempts failed as described in section 2. No workaround was made to official code.
- In pass 1, the 1- and 2-thread inference rows overlapped light jobs pinned to another core. Pass 2 was clean, and both passes are reported.

## What the orchestrator needs to decide next

1. **Whether to declare DECL-AMX-1**, as drafted or amended. The within-2 bar at 99.9 % is forecast to fail on real data too. Options:
   - keep the bar and expect C2-NT to stay fp32. It costs only about 3.2 min per 2 x 2 cm window at 4 threads anyway.
   - drop the inference half and declare only AMX-TRAIN. This is where AMX matters most: about 2x on fine-tunes, 0.75-0.87 h against 1.6 h per 2000-step arm.
2. **If AMX-INF is declared:**
   - the w044 C3 crop must be re-rendered and re-inferred, because the container was reset and `/work/c3` is gone;
   - that is a map of real (base-trained, non-eligible) data, which this sibling was not permitted to produce;
   - cost: about 20 min fp32 plus about 11 min bf16 at 4 threads, plus the render.
3. **If AMX-TRAIN is declared:**
   - it needs the D3 replay pool (`/work/d3/pool_replay`, rebuilt by `tools/d3/build_pools.py` if the container lost it);
   - it needs a one-file autocast wrapper around `tools/d3/d3_train.py`, which I have not written, so the D3 trainer stays untouched until a declaration pins it;
   - cost: about 1 h.
4. **int8:** drop it, unless `torchao` is approved as a new pinned dependency. Even then, expect worse fidelity than bf16.
5. **Cached-feature / letter-context path:** it is fast (8-15x per step) and exact (max |diff| 0). Any use for letter-context training is a new method and needs its own declaration, validation (held-out parity, augmentation handling) and data rules. No eligible-scroll data may be used for training.
