Provenance: Project HERCULES | owner the owner | [id removed]

# chain2um: the 2.4 um truth chain on CPU (ink_canonical_2um), PHerc0139 control, cost

Sibling builder report. Numbers only: no image, slice or map was displayed or viewed. No PHerc0841 and no eligible-scroll data were touched. Machine-readable files are listed at the end.

## 1. Verdict-relevant numbers (for the orchestrator; no verdict given here)

Control: PHerc0139 w043 (`20260112000000-w043_2026011217`), 2.399 um volume 20260102150214. The region was chosen by code before any inference (commit e370e3d, `control_selection.json`). It is the largest 8-connected component of 128 px blocks with > 50 % organizer supervision (label_set 20260918). Region E = the supervised pixels inside that component's bbox: 3,210,543 px = 0.185 cm^2, 43.7 % ink. The render and inference crop adds a 128 px context margin: 1408 x 3456 px = 0.280 cm^2, 260 tiles per pass.

Chain run as specified: `vc_render_tifxyz -n 63` centred at n//2 = 31. Then official ink_canonical_2um inference with layers [0, 62) (start 0, 62 layers), clip 0..200, /200, 256 px tiles, stride 128, Hann blending, and the official reduce (sum pred / sum weight, clip 0..1, x255).

Metrics use src/hercules/metrics/pixel.py (sha256 a5ab7fed..., METRIC-HASH): Mann-Whitney AUC over region E (ink = label 255, blank = 0), and Pearson r.

| Map | AUC vs labels | r vs labels | r vs organizer map (E) | r vs organizer map (bbox) |
|---|---|---|---|---|
| Organizer map (model 20260417190342, the ceiling) | 0.88798 | 0.65469 | 1 | 1 |
| Ours, official FORWARD order, fp32 | **0.88795** | **0.65455** | **0.999986** | 0.999986 |
| Ours, official REVERSE order, fp32 | 0.47070 | -0.03874 | -0.06023 | -0.03118 |
| Ours, official FORWARD order, bf16 autocast (report only) | 0.88749 | 0.65370 | 0.99995 | 0.99996 |
| Ours, render WITHOUT --flip-normals, official REVERSE order, fp32 (order-naming check) | 0.88270 | 0.64113 | 0.97220 | 0.97424 |

bf16 vs fp32 map, same control, text order: Pearson **0.99997** over the whole crop, the bbox and E. uint8 max abs diff 7, mean abs diff 0.31, 1.6 % of pixels differ by more than 2. Against the DECL-AMX-1 part I (AMX-INF) criterion: 98.41 % of crop pixels lie within +-2 grey levels (bar 99.9 %). This is real-data evidence consistent with the sibling synthetic forecast (98.2 % / 97.7 %) and with the decision not to declare bf16 inference; fp32 stays the chain of record. Note that bf16 here was emulated (no AMX), not AMX-native; the numerics of the bf16 casts are the same, but not the kernels.

### The order-naming finding (must be resolved before CHAIN VALID is declared)
- Our render uses `--flip-normals`. With it, the -n 63 render equals the organizer 2.399 um surface volume slices 23..85. Four 256 x 256 regions give pooled Pearson 0.999997-0.999998, per-slice min >= 0.99992 and 99.2-99.4 % of voxels bit-identical, at offset exactly 23 = 54 - 31. Without the flip the best pooled r is 0.22 (`fidelity_*.json`).
- In that organizer frame, the text order is the official code's **FORWARD** order (infer `is_reverse_segment=False`). Its map reproduces the organizer ink map at r = 0.99999, which is essentially the organizer's own map. The official REVERSE order carries no ink signal (AUC 0.47).
- The recorded GATE-E2E-style values (REVERSE r ~0.68, AUC ~0.92; FORWARD r ~0) therefore describe a render in the opposite normal convention, where "reverse" is the text order. Tested directly: the render without --flip-normals is the exact slice-reverse of the flipped render (bit-identical, noflip_render_check.json). The official REVERSE order on it recovers the text order: AUC 0.883, r vs labels 0.641, r vs organizer map 0.972. It is not 0.99999 because that window is flipped-frame layers 1..62, one layer off the organizer window 0..61. So the recorded "REVERSE" convention is confirmed as the unflipped frame. A one-layer window shift costs about 0.03 in r vs the organizer map and 0.005 in AUC.
- Consequence: "REVERSE" is not a convention-free name. A declaration should name the order by the render frame, e.g. "the order in which the official code reproduces the organizer map on a render whose slice stack matches the organizer SV".

### Bars as literally written (DECL-CHAINVALID GATE-E2E-0139 text), on this control
- Text order: r vs organizer map 0.99999 (>= 0.60), but AUC vs labels 0.888, which is **below 0.90**. The organizer's own map scores 0.888 on the same pixels, so the 0.90 bar is unreachable on this control even for the reference. The other order has AUC 0.47 (<= 0.60).
- The declared gate names "the team text-window overlaps", which are not defined in anything this task could read. w043 is a code-selected organizer-labelled control, not those overlaps. The orchestrator decides whether this control counts; a proposal is in `proposals/`.
- Training contamination: whether ink_canonical_2um was trained on w043 labels is unknown. This is a chain-reproduction check, not evidence of generalisation.

## 2. Cost (CPU, measured)

Host of these runs: `lscpu | grep -o 'amx[a-z_0-9]*'` returns **nothing**. The CPU is Intel Xeon model 85 @ 2.80 GHz, 4 vCPU, avx512f/bw/vl/vnni, **no AMX, no avx512_bf16** (`host_cpu.txt`). This is not the AMX host the brief and TOOLING.md describe, so bf16 autocast is emulated here.

Tiles per cm^2 per order at 2.399 um, stride 128 = (1e4 / (2.399 x 128))^2 = **1060.5**. Batch 1, 4 threads, in-RAM input, official code path.

| Pass (this host) | s/tile (wall) | Per-part range | h wall per cm^2, one order | Core-h per cm^2, one order | h wall per cm^2, both orders |
|---|---|---|---|---|---|
| fp32 REVERSE | 8.06 | 7.89-8.28 | 2.38 | 9.50 | 4.75 |
| fp32 FORWARD | 8.21 | 7.48-8.55 | 2.42 | 9.68 | 4.84 |
| bf16 FORWARD | 15.54 | 15.38-15.65 | 4.58 | 18.31 | 9.16 |
| fp32 REVERSE on no-flip render (check; uninterrupted, nothing else running) | 7.38 | 7.29-7.47 | 2.17 | 8.69 | 4.35 |

- Render (vc_render_tifxyz, streaming S3, docker --cpus 3): 98 s for 0.280 cm^2, i.e. 0.097 h per cm^2. That is negligible next to inference.
- Peak RSS 2.7 GB per inference process.
- Run-to-run spread of fp32 on this host is 7.3-8.6 s/tile (4 passes), about +-8 %.
- **fp32 projection for the chain of record: about 2.4 h wall (about 9.6 core-h) per cm^2 per order on 4 cores; both orders about 4.8 h wall (about 19 core-h) per cm^2; plus about 0.1 h render.**
- AMX host, for reference only and NOT re-measured in this task: TOOLING.md section 5 (3 threads, random weights) gives bf16 5.25 s/tile, i.e. 1.55 h wall / 4.6 core-h per cm^2 per order, and fp32 8.0 s/tile, i.e. 2.36 h / 7.1 core-h. On an AMX host bf16 would be about 1.5x faster than fp32. Here it is 1.9x slower.
- Examples at the fp32 rate on this host, both orders: a 2 x 2 cm window takes about 19 h wall. The CHAIN VALID 0841 area outside the shells (about 1.3-1.5 cm^2 per segment, B0841-BANK) takes about 6-7 h wall per segment.

## 3. What was done (commands)

All runs, including failures, are in `runs.jsonl` (utc, command, exit code, output sha256).

1. Bootstrap: `tools/sib/chain2um/bootstrap.sh`, a copy of docker/env/setup_env.sh with the current proxy port. Docker, the deps image and the villa 41701aa sparse clone came up, and the 7 CLI apps built in 3.5 min. See failure F1 for the Python env.
2. Checkpoint: `curl https://huggingface.co/scrollprize/ink_canonical_2um/resolve/075855bc69317ef6febf39a0d9d687b27d2b7c29/{r152_3ddec_v2_l5_epoch13.ckpt,README.md,config.json}`.
   - ckpt sha256 36dd0de84b7b7aa6590184192c7415466cd8a1ba7c1e59f42c6373846373c3e0 (1,549,556,213 B; matches the catalogue).
   - README a9eaef93... (licence MIT; data CC BY-NC 4.0).
   - config 19b38c27...
   - Loaded with no missing or unexpected keys.
3. Organizer data (anonymous S3):
   - w043 2.399 um ink map `...-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif`, sha256 08b60302c6c5d6e8d0a254eabf6e1da82fce272f558f7b65ceb2b8dd68268079.
   - Labels `ink-labels/2.399um-volume-20260102150214/20260918/{inklabels,supervision}.zarr`. There is no validation.zarr for w043. The attributes record `canvas_offset_yx` [30.02, -49.95], already applied by the organizers.
   - Mesh `mesh/20260112000000-on-20260102150214-2.399um.tifxyz`: x/y/z sha256 239dbef3... / 85e9f814... / 3de0b451...; meta 8308d5f7...
   - Volume metadata.json sha256 c788219f... (matches the catalogue). samplePixelSize 0.002399 mm, so voxel size 2.399 um was taken from metadata.
   - Organizer SV raw chunks were fetched only for the fidelity checks.
4. Render: `/work/bin/vc vc_render_tifxyz -v <vol> --remote-url <vol> --segmentation <mesh> --scale 1 --group-idx 0 --num-slices 63 --slice-step 1 --voxel-size 2.399 --voxel-unit micrometer --flip-normals --crop-x 22016 --crop-y 14208 --crop-width 3456 --crop-height 1408 --cache-gb 4 --zarr-output /work/c2um/render/w043_n63.zarr` (`<vol>` = s3://vesuvius-challenge-open-data/PHerc0139/volumes/20260102150214-2.399um-0.2m-78keV-masked.zarr/).
5. Inference: `tools/sib/chain2um/run_passes.sh <dir>:<prec>`, which runs `infer2um.py --direction {forward,reverse} --precision {fp32,bf16} --start 0 --layers 62 --tile 256 --stride 128 --batch 1 --threads 4 --parts 10`.
   - `infer2um.py` imports the official `inference.py` and `model_resnet3d_3d_decoder.py` unchanged.
   - The official predict_fn always wraps the forward in CPU autocast (bf16). fp32 = nested `torch.autocast('cpu', enabled=False)` inside the model wrapper.
   - Workers 0 (in-RAM array input).
   - Resumable via the official partitions.
   - Semantics are pinned by `tests/sib_chain2um_test_official_semantics.py` (3 passed): reverse = channel flip after the [start, end) slice; clip 200 then /200; the nested autocast-off gives exact fp32.
6. Scoring: `eval2um.py` (above). Cost: `project2um.py`. Fidelity: `fidelity2um.py`.

## 4. Failures and deviations (all logged)

- F1 `setup_env.sh` stopped at `uv pip install -e /work/villa/vesuvius --no-deps`. vesuvius 0.2.4 requires Python >= 3.14 and the venv is 3.13, and uv has no ignore-requires-python. Not needed for the 2 um chain. Completed by hand:
  - freeze minus vesuvius, torch 2.14.0+cpu as frozen;
  - plus albumentations 2.0.8 and opencv-python-headless (imported by the official optimized_inference code) and pytest;
  - full freeze in `hv-ink-freeze-chain2um.txt`.
  - The 9 um base checkpoint step of setup_env therefore did not run; it is not needed here.
- F2 `/usr/bin/time` is not installed: the first full-render launch exited rc 127 and nothing ran. Rerun without it.
- F3 Host is not AMX (section 2). The first bf16 attempt was killed within part 0 to reorder the passes, and a 4-tile fp32/bf16 benchmark was run (`bench_*` rows).
- F4 The container restarted during forward fp32 part 9 of 10. Parts 0-8 had been saved, and the pass resumed from them. The docker daemon did not survive the restart, so the first no-flip render and its inference failed (rc 1) before dockerd was restarted.
- F5 A reverse-bf16 pass was started and killed within part 0: the bf16 comparison was moved to the text order, where the map carries signal. The final bf16 pass is FORWARD.
- F6 The first eval failed (rc 1: cv2 missing in the eval venv); rerun after installing it.
- F7 Two `pkill -f` calls matched the calling shell (exit 144). The target processes were then killed by PID; no data was affected.
- Deviation: the README of optimized_inference suggests START_LAYER=1, END_LAYER=63. This task specified start 0 with 62 layers and was run as specified. Our map reproduces the organizer map at r 0.99999, so start 0 appears to match the organizer's production setting for this segment.

## 5. What the orchestrator needs to declare next

1. Order naming for C5 / CHAIN VALID / rule R. Name the text order by render frame, not by the word "reverse"; for our renders, `--flip-normals` = organizer SV frame and the text order is official FORWARD. Proposal: `proposals/DECL-CHAIN-ORDER-proposal.md`.
2. GATE-E2E-0139 on this control: the AUC >= 0.90 bar is above the organizer map's own AUC (0.888) here. Either declare the gate's scoring overlaps explicitly, or make the AUC bar relative to the organizer map on the same pixels. This is proposal text only; any change tightens or specifies, it does not loosen.
3. Budget CHAIN VALID at about 2.4 h wall per cm^2 per order (fp32, this 4-vCPU non-AMX host), or about 1.5 h in bf16 on an AMX host if a bf16 inference declaration is ever made (DECL-AMX-1 does not cover inference; fp32 stays the chain of record).

## 6. Files
`control_selection.json`, `fidelity_test_{flip,noflip}.json`, `fidelity_full_*.json`, `summary_{reverse_fp32,forward_fp32,forward_bf16,noflip_reverse_fp32}.json`, `noflip_render_check.json`, `eval_all.json`, `eval_fp32_both.json`, `cost_projection.json`, `host_cpu.txt`, `hv-ink-freeze-chain2um.txt`, `runs.jsonl`, `chain2um_results.json`. Maps (npz) stay under /work/c2um/maps and are not committed.
