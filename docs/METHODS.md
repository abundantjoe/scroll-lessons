# Methods

This document lists every step and every parameter behind the results in [RESULTS.md](RESULTS.md).

Each statement carries a label:
- **VERIFIED**: checked against code or data in this repository;
- **MEASURED**: a number produced by a script here;
- **INFERENCE**: our interpretation.

## 1. Data

| input | value |
|---|---|
| CT volume (positive control) | PHerc0343, `s3://vesuvius-challenge-open-data/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr`, level 0, 8.64 µm voxels, anonymous S3 |
| Control surface | Erwin Nieuwlaar's public First Letters segment `outputs/concat_w047-w048_R5B2_z9500-11000.tifxyz` (128 × 336 nodes, tifxyz scale 0.05 = 20 px per node), repository `github.com/Nieuwlaar/pherc343-first-letters` at commit `e8370f1`, verified with its `outputs/SHA256SUMS` |
| Letter boxes | `inputs/concat_w047-w048_R5B2_z9500-11000_letter_boxes.json` (18 boxes, raw render frame, locations only), same repository, sha256 in [inputs.sha256](inputs.sha256) |
| Scroll axis | `inputs/umbilicus_PHerc0343.json`, same repository, sha256 in [inputs.sha256](inputs.sha256) |
| Ink models | `scrollprize/ink_9um` hybrid_3d2d seed 42 and seed 43, step 75 000; `Nieuwlaar/ink9um-dense-native` step 16 000. Hugging Face URLs and sha256 are in [`scripts/get_weights.sh`](../scripts/get_weights.sh) |
| PHerc0268 strips (artifact diagnosis only) | 56 strips cut from spiral fits of PHerc0268 (`20251110183117-8.640um-1.2m-116keV-masked.zarr`). Only aggregate numbers and anonymised per-strip value pairs are published, never images (confidentiality, see [README](../README.md#confidentiality)) |

- **dense_native checkpoint.** villa loads `{model, config, step}`. [`scripts/rebuild_dense_native.py`](../scripts/rebuild_dense_native.py) rebuilds it from the public safetensors file and training config. **MEASURED (private record):** all 508 tensors and the config were bit-identical to the checkpoint of the original run. The rerun, which used the rebuilt checkpoint, matches the original to its stored precision (RESULTS §2).

## 2. Strip geometry

**Cut** (`scripts/pipeline/bi_prep.py`).
- Nodes outside the requested `rows=a:b cols=c:d` are set invalid (-1).
- All-invalid leading and trailing rows and columns are trimmed. The trim offset is written to `prep.json` as `crop.src_row0` / `src_col0`; scoring uses it to place each strip in the source frame.
- Normals are flipped when fewer than half point away from the scroll axis.

**Arms of the control experiment** (`scripts/control_strips/make_arms.py`; all use node cols 34:166, which hold letters 6-18):

| arm | node rows | what it tests |
|---|---|---|
| REF | 40:110 | full context: the reference map |
| Z13 | 42:55, 55:68, 68:81, 81:94, 94:107 | 13-row strips, the geometry of a typical mass run |
| Z20 | 42:62, 62:82, 82:102 | 20-row strips |
| P13 | the Z13 rows plus 2 real node rows each side | real padding; only the target rows are scored |
| F13 (exploratory) | the Z13 rows, rendered as Z13 | the blank margin reflect-filled for the ink models (`RENDER_FILL=reflect`) |
| D8 | the Z13 rows on a copy moved +8 vox along the outward normal | negative arm ("no-ink arm" in the pre-registration): the window centre moves between sheets (but see below) |
| FD8 (exploratory) | D8 with the fill | the fill's floor on the negative arm |
| X13 (original run only, exploratory) | the Z13 rows plus 2 linearly extrapolated node rows each side (`stripqc.geometry.xpad`) | padding without new CT; not rerun (RESULTS §1) |

- **What the +8 vox copy still sees (INFERENCE from the geometry, §3-4):** at d = +1 the models read layers 26-42,
  which sample −6.5 to +9.5 vox around the surface. After a +8 vox outward move the original sheet's CT peak (layer 35,
  +2.5 vox) sits at −5.5 vox of the moved surface, i.e. in layer 27, inside the window. `D8`/`FD8` are therefore
  conservative negatives, not ink-free inputs (RESULTS §1).
- **Displacement** (`stripqc.geometry.displace`): unit normals from `np.gradient` of the node grid (one-sided at the grid border). A valid node next to an invalid one gets no normal and is dropped from the copy. The sign is chosen so that the majority point away from the axis. **VERIFIED** on the control: every kept node moved 8.000 vox; 606 of 27 598 valid nodes were dropped (78 of 8 800 in the arm window, 57 in the D8 rows); outward majority 0.997.

## 3. Render

- **Tool:** `vc_render_tifxyz` from ScrollPrize/villa commit `41701aa`, run inside `ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f` (`scripts/pipeline/vc.sh`).
- **Arguments:** `--num-slices 66 --slice-step 1 --scale 1 --pyramid 0 --group-idx 0 --cache-gb 2`.
- **Layers:** layer k samples the CT at k − 32.5 vox along the outward normal.
- **CT input:** the exact level-0 chunks a render touches are listed (`crop_and_chunks.py`: normal offsets −32.5 … +33.5 vox in 2 vox steps, each with the 8 corner voxels of its floor cell; surface sub-sampled at 2 vox), filtered to ±64 vox around the valid nodes (`bi_chunkfilter.py`), and copied byte for byte from S3 into a local zarr v2 mirror (`bi_mirror.py`, `vol.py`).
- **Blank margin** (**VERIFIED** on the renders):
  - border mesh nodes have no central-difference normal (`stripqc.tifxyz.normals_central`), and the last cell is not rendered;
  - so a strip render carries all-zero rows at its edges: at least 30 at the bottom (more where the last node rows are invalid); at the top, 30 where node row 0 is invalid, otherwise 10. The control arms have 10 at the top.
  - The valid area of a 260 px (13-row) render is therefore at most rows 10-229 (30-229 where node row 0 is invalid). In the ragged bottom strip r94-107 of the control it is shorter in about a third of the columns.

## 4. Ink inference (the stage with the bug)

- **Command:** villa `vesuvius.ink_detection.inference.infer` (commit `41701aa`) through `scripts/pipeline/run_ink_local.py` on CPU, one thread per run, 3 runs at a time.
- **Arguments:** `--overlap 0.5 --blend-mode hann --batch-size 4 --direction reverse --layer-start S --layer-end S+17 --no-compile --num-workers 0`, with S = 25 + d.
- **Depth:** the models read layers S to S + 16, centred on layer 33 + d. The control uses d = +1 (S = 26, Erwin's d = +1): the centre (layer 34) sits one layer inside its CT sheet peak at layer 35. The PHerc0268 mass runs used d = −2.
- **Patch geometry:** 17 × 128 × 128 voxels. The stride is 64, from overlap 0.5. Patch starts follow `range(0, L − 128 + 1, 64)`, with L − 128 appended when it is missing (`stripqc.patchgrid.positions`). **VERIFIED** against the villa source for L = 240, 260, 380 and 400.
- **Blending:** Hann blending of the patch outputs.
- **Normalisation:**
  - all three checkpoints declare `image_normalization: robust_mad`, percentiles 1-99 (**VERIFIED**);
  - villa maps this to `normalize_robust(patch)` with its defaults (`mask=None, use_mask=False`), so the median, MAD and percentiles of a patch include its blank voxels;
  - the networks use `nn.InstanceNorm2d`, logged at load.
- **Empty patches:** villa skips patches that are entirely empty (`nonempty` flag, computed before normalisation). A partly blank patch is normalised with its zeros included. That is the defect this release documents.
- **Still current (VERIFIED, 14 Oct 2026):** `vesuvius/src/vesuvius/ink_detection/inference/infer.py` and
  `vesuvius/src/vesuvius/image_proc/intensity/normalization.py` are byte-identical between `41701aa` and villa `main` at
  `5432721` (14 Oct 2026, 20:30 UTC); the call is still `normalize_robust(patch_ZYX)`. The renderer *has* changed since
  `41701aa` (208 files under `volume-cartographer/apps` and `core`). We have not rebuilt it, so the blank margin is
  verified at `41701aa` only.
- **Ensemble:** the mean of the three models' reverse maps at depth d, stored as uint8 p × 255 (`ens_d<d>.tif`). The ink maps are non-zero over the blank margin too (about p = 0.31), so validity always comes from the CT (`ctlayers_31-35.tif > 0`).

## 5. The partial fix: reflect fill

`stripqc.fill.reflect_fill` (batch_ink stage `RENDER_FILL=reflect`):
1. For each column, the blank rows above the first valid row t0 take the 66-layer vector of row 2 t0 − r, clamped to the valid run; the blank rows below the last valid row t1 take row 2 t1 − r.
2. Pixels still blank (empty columns, holes) take their nearest valid pixel (Euclidean distance transform).
3. Valid pixels are unchanged (**VERIFIED**: bit-identical on a real 66 × 400 × 2640 render; unit tests).

The ink models read the filled copy (`render_fill.zarr`). Validity, scoring and overlays keep the original render.

## 6. Scoring the positive control

`stripqc.score`, `scripts/control_strips/score_arms.py`.

**Frames.** Render pixel (i, j) of an arm cut at node (r0, c0) is raw pixel (i + 20 r0, j + 20 c0), the frame of the letter boxes.
- The renderer's half-pixel node offset is common to all arms and the boxes.
- Moving every box by ±20 px (one node) in x and y, 9 positions, changes no decision (**MEASURED**:
  `scripts/control_strips/box_shift_check.py`, [`box_shift_check.json`](../results/control_strips_rerun/box_shift_check.json)).

**Pixel set S:** pixels valid in the arm AND in REF, within the arm's target node rows (for REF itself, node rows 42-107). "Strong" means p > 0.55.

**Metrics:**

| metric | definition |
|---|---|
| f_in, f_out | strong fraction inside / outside the letter boxes |
| E | f_in / max(f_out, 10⁻⁴) |
| recall | \|arm strong ∧ REF strong ∧ box\| / \|REF strong ∧ box\| |
| r | Pearson correlation of arm vs REF p over S |
| coverage | box pixels scored / box pixels in the target rows |
| band | strong fraction outside the boxes, 20-80 px from the column's valid edge, arm vs REF at the same pixels |
| box AUC (exploratory) | ROC AUC of p for box vs non-box pixels |
| matched-rate recall (exploratory) | recall with the arm thresholded at the quantile that flags as many pixels as REF's p > 0.55 |

- **CIs:** 95 % recall intervals come from a letter-cluster bootstrap: the 13 letters are resampled with replacement, 2 000 replicates, seed 0.
- **Decisions:** the pre-registered rules are in [prereg/DECL-FL-STRIP.md](prereg/DECL-FL-STRIP.md).

## 7. Diagnosing the artifact on real data (PHerc0268, aggregate only)

**Natural experiment** (`stripqc.margins.top_margin_experiment`, `scripts/natural_experiment.py`).
- Ink proxy: α = clip(R − B, 0) / 224 of the fixed-scale overlay. The orange alpha equals (p − 0.40)/0.30 on grey CT.
- Validity: non-black pixels.
- Column classes:
  - a column belongs to a class when its blank top margin is 30 (or 10) rows, ±2;
  - it must also be constant over a centred 129-column window;
  - a strip needs at least 129 such columns per class.
- The mean α over render rows 50-90 is compared between the two classes inside the same strip.
- **Logic:** a physical feature sits at fixed node rows and cannot depend on the blank margin; an artifact can.

**Patch-share model** (`stripqc.patchgrid.blank_share`): for each render row, the Hann-weighted share of the patches covering it that contain a blank row. It is compared with the pooled row profile of the ink proxy.

## 8. Blind reads with hidden controls

`stripqc.blindread`, [results/blind_read](../results/blind_read).

- **Readers** were three independent Claude sub-agents, not humans. Each was restricted to viewing the coded image files and returning structured JSON: letter-like yes/no, letter-row yes/no, confidence 0-1 that the image contains writing.
- **Images:**
  - overlays cut into 1 000 px segments stacked vertically;
  - every image re-encoded identically (JPEG q 88), so the file format gives nothing away;
  - coded in a fixed hash order;
  - each reader saw a different order.
- **Read #2 (calibrated)**:
  - 8 hidden positives: PHerc0343 control strips, 3 × 20-row and 5 × 13-row;
  - 5 hidden negatives: the `D8` strips (displaced +8 vox, no fill; no letter-located signal, RESULTS §1);
  - unknown PHerc0268 strips (reads not reported, whatever they showed; not evidence either way, RESULTS §4);
  - Metric: per-reader AUC, positives vs negatives.
- **Read #1 (uncalibrated)**: unknown strips and 2 hidden positives, no negatives. See RESULTS for why it failed.
- **Source of this section:** the image-preparation script handled PHerc0268 images, which are not published, and is not part of
  this release. The procedure above is described from the project record; the committed JSON holds the control reads
  and the per-reader AUCs, which `stripqc.blindread.reader_auc` recomputes.

## 9. Geometry checks used along the way

- **3-D seam test** (`stripqc.seam`). Two surfaces fit independently are matched point to point within 4 vox (bilinear samples, 3 × 3 per quad). The Pearson r of their maps at matched points is compared with a circular-shift null: B's columns are shifted by 200 … W − 200 px in steps of 25, so every shift has equal n.
- **Interpretation** (**INFERENCE**): agreement validates the pixel-to-3-D mapping and shows a reproducible CT response. It does not certify ink, because both maps read the same CT.

## 10. Software versions (reference run)

| item | version |
|---|---|
| Python (analysis) | 3.11.15; numpy 2.4.6, scipy 1.17.1, zarr 2.18.7, tifffile 2026.3.3, Pillow 12.3.0, pytest 9.1.1; matplotlib 3.11.2 for figures |
| Python (ink) | 3.13.12; torch 2.14.0+cpu, numpy 2.5.3, zarr 3.4.0, safetensors 0.8.0; villa `vesuvius` 0.2.4 (editable install) at commit `41701aa` |
| Renderer | volume-cartographer at villa `41701aa`, built in the pinned vc3d-deps image; run with Docker 29.3.1 |
| Hardware | 4 CPU cores, 16 GB RAM, no GPU |
