# Reproducing this release

Five levels, from about 16 seconds to days. All of them except Level 3 were run on 2026-10-15 in a **fresh
container**. It started from an empty disk with no access to the September data, and the outputs quoted below come
from those runs. What each run did and did not exercise:

- **Level 0** (quick start) and **Level 1** were run as written below. For Level 1 that means the whole suite
  without data, and the 3 integration tests on their own with the public inputs.
- **Level 2** (the w040 control). The inputs were fetched with an earlier, uncommitted helper, and the inference was
  run with the identical call, before `scripts/reproduce_control.sh` existed. The script was then run on those files
  in resume mode, 07:02:33 to 07:05:38 UTC
  ([console](../records/release/repro_2026-10-15/reproduce_control_console.txt)). It skipped its fetch and inference
  commands because their outputs existed, and ran everything from `map_integrity.py` on (the end of step 2, then
  steps 3–7). **Later the same day the committed script ran end to end from an empty work directory**, 10:12:13 to
  12:00:42 UTC, in two invocations ([console](../records/release/e2e_2026-10-15/reproduce_control_console.txt)). The
  first fetched every input (10:12:13 to 10:15:31) and was killed by a container restart during inference. The
  relaunch at 10:25:30 skipped the fetch because its outputs existed, ran the inference for both orders from the
  start, and ran every check. Both prediction maps are byte-identical to the resume-mode run and to September, every
  score and verdict is the same, and every JSON file equals the resume-mode run's except for file paths (see
  "Fresh-container results").
- **Level 2b** (held-out PHerc0841). It ran from the recorded scripts in
  [`records/release/heldout_2026-10-15/`](../records/release/heldout_2026-10-15/). The scoring was re-run while this
  page was being checked, using the commands given below, and it reproduced the recorded outputs.
- **Level 3** (the corpus reads) was not re-run.

| Level | What it reproduces | Needs | CPU time (4-core Xeon, measured 2026-10-15) |
|---|---|---|---|
| 0 | the core QC tools (reader, truncated-map guard, layout power) on real known text, checked against recorded values | `requirements.txt` | ~16 s |
| 1 | the full test suite (295 tests), incl. 3 integration tests on public data | `requirements.txt` (+ network, the 1.5 MB w040 mesh and the bucket catalogue for the 3) | 270.11 s without data (on the 293 tests before `d097884`); the 3 integration tests 57.65 s |
| 2 | the known-text control (a training-set sheet) from public data: Gate A AUC and the frozen-rule candidate | + `requirements-infer.txt`, `boto3`; ~1.41 GB download (stack + mesh 1.27 GB, checkpoint 0.138 GB, labels 1.2 MB in 8496 files) | 5958 s inference (1 h 39 min, both orders) + 3 min 5 s scoring, plus download time; the end-to-end relaunch took 5526 s of inference for both orders, with other work on the box (the killed first attempt's ~5.5 min not included) |
| 2b | the pre-registered held-out known-text test on PHerc0841 (R-HELDOUT): pixel AUC and the frozen rule on text the model has not seen | the Level 2 environments and checkpoint; level 2 of three surface volumes, streamed from the bucket; labels 1.36 MB | 6039 s inference (1825 + 2274 + 1940 s) + 66 s pooling + ~2 min scoring |
| 3 | the corpus reads on eligible scrolls (tracing, rendering, reading) | + VC3D tools built from source, Docker | days (see below) |

## Environment

| Item | Version used on 2026-10-15 |
|---|---|
| Hardware | 4 CPU cores (Intel Xeon), 15 GB RAM, no GPU (the same class of machine as September) |
| Analysis tools | Python 3.13.16; versions pinned in `requirements.txt`; full freeze `records/release/env_tools_freeze.txt` |
| Fetching | `boto3==1.43.114` (pinned in `requirements-infer.txt`, **not** in `requirements.txt`): `scripts/fetch_control_w040.py` and `records/release/heldout_2026-10-15/fetch_labels.py` need it. The `hf` CLI comes with `huggingface-hub==2.2.0` in the inference environment. |
| Inference | Python 3.14.6 (villa requires ≥ 3.14, < 3.15); torch **2.14.0+cpu**, torchvision **0.29.0+cpu**; versions pinned in `requirements-infer.txt`; full freeze `records/release/env_infer_freeze.txt` |
| villa (`vesuvius` package) | `5ab585ffee54331a3362b9ce6b2929b20dcde2c6` (2026-09-16), the commit used in September (RULES.md, "Disk: `external/villa/.git` removed") |
| Ink model | `scrollprize/ink_9um` `hybrid_3d2d-seed42/step-075000.pth`, sha256 `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab` (equal to the Hugging Face LFS record; repo revision `7109667e2607db1b90c37c8b09cb876ea7fe7bb1`) |
| VC3D tools (level 3 only) | built from villa `5ab585f` with `scripts/build_vc3d.sh` inside `ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04`. **Do not use the published `:edge`/`:main` image.** On 2026-10-15 it was still the 2026-05-13 build (villa `1e3f4c0`), and it rejects `--flip-normals` (`records/release/edge_image_check_2026-10-15.md`). It also predates remote normal grids (`scripts/build_vc3d.sh` header). This pipeline's own render step does not pass `--flip-normals` (Level 3, step 4). |

```bash
git clone --depth 1 https://github.com/abundantjoe/hercules && cd hercules
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

The depth-1 clone is 157.5 MB of packed objects (157.6 MB for all of `.git`) plus a 217.6 MB checkout (measured on `main` at `aa9576a`). A full
clone is larger (the pack was 1.26 GiB at the same commit) because history holds review overlays removed from `HEAD`.

All commands below run from the root of the clone. Keep data, work directories, the inference environment and the
villa checkout **outside the clone** (`../hercules_work`, `../venv-infer`, `../villa` below). None of them is
git-ignored, so inside the clone they would fill `git status` with thousands of files.

## Level 0: quick start (≈ 16 s)

```bash
bash examples/quickstart.sh
```

Expected: `ALL CHECKS PASSED`, then a final line naming the contact sheet; exit status 0. The ten assertions and the
recorded values are listed in [`examples/README.md`](../examples/README.md). The input arrays are verified by pixel
sha256 before use:

| Array | Pixel sha256 (uint8, row-major) | Recorded in |
|---|---|---|
| forward window | `4eced8f47248bc97917fde970faf912c2f2f0f2fc4e7ca77cdbe60b752c443a2` | `packages/DRYRUN_PHerc0139_w040/package.json` (`forward_window_sha256`, 2026-09-17) |
| reverse window | `2522e6827513f358270a5b2fc72d70565a6239cf940357ceb47a747d276630f5` | same file (`reverse_window_sha256`) |
| CT slice 14 window | `7d62c816e04126ba28c2a9f2379764c2de81b38762a46b44c76270a8728ae8dc` | re-derived 2026-10-15 from the public stack; equals the September `ct_window.png` |

## Level 1: test suite (≈ 4.5 min)

```bash
HERCULES_DATA=/tmp/no_data python -m pytest scripts/tests -q -rs   # without data: 292 passed, 3 skipped; -rs prints each skip's reason
```

Point `HERCULES_DATA` at a directory you can create, as CI does (`.github/workflows/ci.yml`). Nine
`test_run_patch_dir.py` tests drive `run_patch_dir.process_patch` in-process as far as its inference stage, where
`acquire_slot` creates the directory `$HERCULES_DATA/logs/infer_slots` and the lock file `slot0` in it; if that
directory cannot be created, those nine tests fail. Unset,
`HERCULES_DATA` defaults to `/home/user/hercules_data`.

Measured on 2026-10-15: **292 passed, 3 skipped** in 296.63 s at `106d3ec` (which added the `map_integrity --json`
regression test); 291 passed, 3 skipped in 325.28 s at `82409f4` (after `d097884` added `test_window_label_stats.py`). Earlier the same day, before that test existed: **290 passed, 3 skipped** (317 s on the release tree; 281 s in a separate clone at another
path with no repository venv and no `HERCULES_ROOT`, the way CI sees it). An earlier draft of this page needed
`export VC_PYTHON=...` in such a clone, because `scripts/vc_tools.sh` defaulted its helper interpreter to
`/home/user/hercules/.venv/bin/python` and two `test_vc_tools.py::test_render_is_zero` cases failed (2 failed, 288
passed, 3 skipped). Fixed before release: `vc_tools.sh` now defaults to the repository's own `.venv` and falls back
to the `python3` on `PATH`, so no variable is needed. `VC_PYTHON` still overrides it.

The 3 integration tests need the public w040 mesh (four files, 1.5 MB) and the bucket catalogue. To run them as well:

```bash
export HERCULES_DATA=$PWD/../hercules_work/data
M=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0139/segments/20250831000000-w040_2025083102/mesh/20250831000000-on-20250728140407-9.362um.tifxyz
mkdir -p "$HERCULES_DATA/controls/w040/mesh" "$HERCULES_DATA/cat"
for f in meta.json x.tif y.tif z.tif; do curl -fsS -o "$HERCULES_DATA/controls/w040/mesh/$f" "$M/$f"; done
sha256sum "$HERCULES_DATA"/controls/w040/mesh/*      # compare with the mesh row of the data-input table below
curl -sS https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/metadata.min.json | gunzip > "$HERCULES_DATA/cat/metadata.min.json"
python -m pytest scripts/tests -q -rs
```

With these inputs, the 3 integration tests alone gave **3 passed in 57.65 s** (2026-10-15). The four mesh files
fetched this way have the sha256 values in the table below. Final counts for the release:
[the fresh-container results](#fresh-container-results-2026-10-15) below.

## Level 2: the known-text control from public data (≈ 1 h 42 min CPU)

`scripts/reproduce_control.sh` covers the whole run: fetch, inference in both depth orders, Gate A, the frozen rule
(two code paths), a bit-identity check against September, and checksums. Each step is skipped if its output
exists, so the script resumes after an interruption. On 2026-10-15 its fetch and inference commands were skipped
because their outputs already existed (see the top of this page).

```bash
# fetch_control_w040.py needs boto3; reproduce_control.sh runs it with $INFER_PY, and requirements-infer.txt pins
# boto3==1.43.114. Install boto3 in the analysis environment only to run fetch_control_w040.py by hand:
# pip install boto3==1.43.114
# inference environment (Python 3.14), outside the clone
python3.14 -m venv ../venv-infer
../venv-infer/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0 torchvision==0.29.0
../venv-infer/bin/pip install -r requirements-infer.txt
git clone https://github.com/ScrollPrize/villa ../villa && git -C ../villa checkout 5ab585ffee54331a3362b9ce6b2929b20dcde2c6
../venv-infer/bin/pip install --no-deps -e ../villa/vesuvius
# run
INFER_PY=$PWD/../venv-infer/bin/python PY=python bash scripts/reproduce_control.sh ../hercules_work/w040
```

### Data inputs

| Input | URL | Checksum |
|---|---|---|
| w040 native surface volume, level 0 (28 × 6400 × 7980 uint8, uncompressed) + group metadata; 1,270,287,992 B | `s3://vesuvius-challenge-open-data/PHerc0139/segments/20250831000000-w040_2025083102/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr/` (anonymous; HTTPS: `https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/...`) | `fetch_control_w040.py` (needs `boto3`) writes `MANIFEST.sha256` (2776 files incl. the mesh) and prints its digest: `cf8b283adee7af62bba3a8e11d19c0682dce2723a0a153134ae5a1d210258d84`. The recorded manifest is [`w040_inputs_MANIFEST.sha256`](../records/release/repro_2026-10-15/w040_inputs_MANIFEST.sha256). |
| w040 tifxyz mesh (4 files, 1,532,981 B) | `.../mesh/20250831000000-on-20250728140407-9.362um.tifxyz/` | `x.tif` `4cc50b835663e35f00accd7e12b2e2eea2f1ac8c60c140601974752105128573`, `y.tif` `45ed92a905f13752fc027fe857b2cd8ce0505bf64a0f9ebd3d7ea7ab27f802a5`, `z.tif` `aafc0207e6713280e1dd50863976998225ab911a3c4a528ff3add21b10f9a755` (identical to the September package record); `meta.json` `477f6a6f120fd5c612a103d76d1a9b09a18d2121242f7324474eadd592bfcc56` |
| w040 labels (1,218,126 B in 8496 files) | `hf buckets sync hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w040 <dir>` | manifest digest `dfb49aa7d10f84f88c1df12aacfe8231520b04678b13d83900a448a302c71d98`; check it with `python scripts/fetch_control_w040.py ../hercules_work/w040/labels/w040 --manifest-only` (no download, no `boto3`; prints `MANIFEST.sha256: 8496 files; manifest digest dfb49aa7…`, VERIFIED 2026-10-15 on a copy of the fetched labels). 1,629,734 supervised px on slice 14 |
| checkpoint (138,360,039 B) | `hf download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth --revision 7109667e2607db1b90c37c8b09cb876ea7fe7bb1 --local-dir <dir>` (`reproduce_control.sh` does not pass `--revision`; the sha256 it prints is the check) | `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab` |

### Commands run by `reproduce_control.sh`

```bash
python -m vesuvius.ink_detection.inference.infer <stack.zarr> step-075000.pth out/w040_full_plain.tif \
    --direction both --batch-size 4 --no-compile --num-workers 3          # writes ..._reverse.tif too
python scripts/map_integrity.py --pair out/w040_full_plain.tif out/w040_full_plain_reverse.tif
python scripts/score_auc.py out/w040_full_plain.tif         w040_inklabels.zarr w040_supervision_mask.zarr --slice 14 --ink-thr 128
python scripts/score_auc.py out/w040_full_plain_reverse.tif w040_inklabels.zarr w040_supervision_mask.zarr --slice 14 --ink-thr 128
python scripts/rctrl55.py --forward out/w040_full_plain.tif --reverse out/w040_full_plain_reverse.tif --labels w040_inklabels.zarr
python scripts/read_chart.py <footprint mask> out/w040_full_plain.tif out/w040_full_plain_reverse.tif --maps-only --um 9.362 ...
```

### Expected outputs (bars declared 05:30:27 UTC, before any output existed; the inference had started at 05:01:22 UTC: RULES.md R-REPRO)

The declaration records the start time itself:
[`RULES.md:3220`](https://github.com/abundantjoe/hercules/blob/c700273/RULES.md?plain=1#L3220) `@c700273`. The forward pass
ended at about 05:54 UTC: the reverse pass starts at 05:54:01 in
[`infer_stderr.log`](../records/release/repro_2026-10-15/infer_stderr.log).

| Output | September record | Bar |
|---|---|---|
| Gate A forward AUC | 0.99659 | within 0.01 |
| Gate A reverse AUC | 0.49633 | < 0.70 |
| R-CTRL55, both code paths | 71 valid, 7 flagged, clusters [4, 2, 1], origin (94, 188) | exact |
| window [1500:3636, 2000:4136] of each map | pixel sha256 above | reported, not a bar |

### Result of the fresh-container run (2026-10-15): both bars PASS, and the maps are byte-identical

Recorded in [`RULES.md:3271`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3271) `@eed0fac`; every
output is in [`records/release/repro_2026-10-15/`](../records/release/repro_2026-10-15/). **VERIFIED.**

| Output | September record | 2026-10-15, fresh container | |
|---|---|---|---|
| Gate A forward AUC (1,629,734 supervised px) | 0.99659 | **0.99659** | PASS (bar: within 0.01) |
| Gate A reverse AUC | 0.49633 | **0.49633** | PASS (bar: < 0.70) |
| mean on ink / blank, forward | 0.758 / 0.252 | 0.758 / 0.252 | |
| R-CTRL55 via `rctrl55.py` | 71 valid, 7 flagged, [4, 2, 1], origin (94, 188) | **71 valid, 7 flagged, [4, 2, 1], origin (94, 188)** | PASS (bar: exact) |
| R-CTRL55 via `read_chart.py --maps-only` | 7/71, PROMISING CANDIDATE | **7/71, largest cluster 4, PROMISING CANDIDATE** | PASS |
| window pixel sha256, forward / reverse | `4eced8f4…` / `2522e682…` | identical | |
| **whole-file sha256, forward** | `31f001f4f90d42b679d8f57a363ce0b90c4926ec0737dc436db4d7c376d671dc` (`package.json`, 2026-09-17) | **identical** | |
| **whole-file sha256, reverse** | `a5425879eb1a1999c15c6c4fde18cdf3aa3e8f2cf5c3e561c1470a06da51b2af` | **identical** | |
| inference wall time, both orders | "~1.9 h per direction under contention" | **5958 s** (forward 52 min, reverse 47 min) | |
| scoring + both rule paths + checksums | | 3 min 5 s | |

**The prediction maps a month later, in a different container, are the same files bit for bit.** The code, the
versions and the inputs were the same. If your run gives different hashes, your environment differs from the table
above (most likely torch, numpy or the villa commit). The two bars are the test that matters.

The first scoring attempt stopped at `map_integrity.py` with `COMPRESSION.LZW requires the 'imagecodecs' package`.
The inference writes LZW-compressed TIFFs, and the release's `requirements.txt` had omitted the decoder. The pin was
added and the run repeated. No number comes from the failed attempt, and the guard refused the unreadable pair as
designed.

**What this establishes, and what it does not.** The September control numbers are exactly reproducible from public
data with the committed code. The control is still a training-set sheet of the model (`RULES.md` R-HELDOUT), so this
is a reproduced best case, not a held-out validation. The held-out test is
[Level 2b](#level-2b-held-out-known-text-pherc0841-pre-registered-r-heldout--1-h-43-min-cpu), next.

## Level 2b: held-out known text, PHerc0841 (pre-registered R-HELDOUT; ≈ 1 h 43 min CPU)

w040 is one of the model's training segments (VERIFIED,
[`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`). This level runs
the same checkpoint and call on known text from a scroll outside the training config. The test and its bars were
declared before any of its data was downloaded
([`RULES.md:3231`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3231) `@661ff64`, committed 05:38:48
UTC; pooling began 05:39:10 UTC, `prep_timing.txt`). The analysis script `scripts/rheldout.py` was committed in
`d8c39a3` before any output existed. VERIFIED (commit and log times).

### Inputs

Segments: `20260220213127-w00`, `20260220214732-auto_grown_20260220144552896`,
`20260221022814-auto_grown_20260220174252405`.

| Input | URL | Checksum (from [`checksums.sha256`](../records/release/heldout_2026-10-15/checksums.sha256)) |
|---|---|---|
| surface volume, level 2 (2.403 µm × 4 = 9.612 µm/px), pooled by the preparation step to 21 slices | `https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0841/segments/<segment>/surface-volumes/2.403um-0.22m-77keV-volume-20260319124803.zarr`. On the bucket, level 2 is 895 / 902 / 861 objects, 4,741,448,298 B in all (listed 2026-10-15). How much of it the pooling step reads was not recorded. | the pooled output `<segment>/pooled.zarr`: digests `6f7806c2…`, `e7c7ce90…`, `59fb55b5…` |
| ink labels (`inklabels.zarr`, `supervision.zarr`, `validation.zarr`; 39 files per segment, 1,364,991 B in all) | `s3://vesuvius-challenge-open-data/PHerc0841/segments/<segment>/ink-labels/2.403um-volume-20260319124803/20260918/` | `<segment>/labels`: digests `d2e24f1e…`, `7678dc75…`, `d7528210…` |
| checkpoint | as Level 2 | as Level 2 |

A directory digest is `find <segment>/<dir> -type f | LC_ALL=C sort | xargs sha256sum | sha256sum`, run from the
directory that holds the three segment directories. This command reproduces all six recorded digests (VERIFIED
2026-10-15).

### Commands

The scripts that ran are committed: [`prep.sh`](../records/release/heldout_2026-10-15/prep.sh),
[`fetch_labels.py`](../records/release/heldout_2026-10-15/fetch_labels.py) and
[`run_infer.sh`](../records/release/heldout_2026-10-15/run_infer.sh). They are records of this machine. They hard-code
`/home/user/hdata/heldout`, `/home/user/ext/venv-infer` and the checkpoint path, and `run_infer.sh` waits for
R-REPRO's timing file so that the two runs never shared the CPU. Two scoring steps were not recorded as scripts: the
derivation of `ct_mid.tif` and the `rheldout.py` / `read_chart.py` command lines. The portable form below has the
same arguments. Steps 1–3 were not run in this form. Step 5 was re-run in this form on 2026-10-15 from the recorded
inputs (see Expected outputs).

```bash
R=$PWD; IPY=$PWD/../venv-infer/bin/python
CKPT=$PWD/../hercules_work/w040/models/ink_9um/hybrid_3d2d-seed42/step-075000.pth      # fetched by Level 2
SEGS="20260220213127-w00 20260220214732-auto_grown_20260220144552896 20260221022814-auto_grown_20260220174252405"
U=https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc0841/segments
mkdir -p ../hercules_work/heldout && cd ../hercules_work/heldout
# 1. pool level 2 of each surface volume to 21 slices                     [prep.sh; it also retries, under nice -n 5]
for s in $SEGS; do
  "$IPY" -m vesuvius.ink_detection.preprocessing.prepare_9um_isotropic_input \
      $U/$s/surface-volumes/2.403um-0.22m-77keV-volume-20260319124803.zarr $s/pooled.zarr --level 2 --workers 6
done
# 2. labels into <segment>/labels/ (anonymous S3; boto3 is in the inference environment)   [fetch_labels.py]
"$IPY" "$R/records/release/heldout_2026-10-15/fetch_labels.py"
# 3. inference, both depth orders, the same call as Level 2               [run_infer.sh]
for s in $SEGS; do
  "$IPY" -m vesuvius.ink_detection.inference.infer $s/pooled.zarr "$CKPT" $s/pred.tif \
      --direction both --batch-size 4 --no-compile --num-workers 3        # writes $s/pred_reverse.tif too
done
# 4. checksums: compare with records/release/heldout_2026-10-15/checksums.sha256
for s in $SEGS; do
  sha256sum $s/pred.tif $s/pred_reverse.tif
  for d in pooled.zarr labels; do echo "$(find $s/$d -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)  $s/$d"; done
done
# 5. scoring, analysis environment
for s in $SEGS; do python "$R/scripts/map_integrity.py" --pair $s/pred.tif $s/pred_reverse.tif; done   # SOUND x 3
python "$R/scripts/rheldout.py" $SEGS --json rheldout.json              # --um defaults to 9.612 (2.403 x 4)
for s in $SEGS; do    # second code path, the ordinary reader; on-sheet mask = pooled CT middle slice > 0
  python -c "import sys,zarr,tifffile,numpy as np; a=zarr.open_group(sys.argv[1]+'/pooled.zarr',mode='r')['0']; tifffile.imwrite(sys.argv[1]+'/ct_mid.tif', np.asarray(a[a.shape[0]//2]))" $s
  python "$R/scripts/read_chart.py" $s/ct_mid.tif $s/pred.tif $s/pred_reverse.tif --maps-only --um 9.612 \
      --out $s/read_chart --key "PHerc0841|$s|0|ink9um_seed42+plain|both" --ledger LEDGER_heldout.md
done
```

The `ct_mid.tif` files used on 2026-10-15 equal the middle slice (index 10 of 21) of each `pooled.zarr`, pixel for
pixel (VERIFIED 2026-10-15).

### Expected outputs

The recorded checksums:

```
b22ec32c0eb22476e163b0710cafbf297fed88e20fd8151a674a5951c52a3294  20260220213127-w00/pred.tif
595f91f028cc74e4edbc50eb89d39ff46f7b6b70f60759d7a8db4fa9c2fc8eea  20260220213127-w00/pred_reverse.tif
6f7806c283dc1d63b65c621728c861f2ca8b203a5416c1eb9a68e64fbb79d9c7  20260220213127-w00/pooled.zarr (digest of sorted per-file sha256 list)
d2e24f1edf85629a7c26d484a4b78257c8c061d077982cb2469717d8f245e4bb  20260220213127-w00/labels (digest of sorted per-file sha256 list)
9fcd62121d6ca30d3e5aba7923b0a58e4d847d86a8f3639f22de797be95c3f9f  20260220214732-auto_grown_20260220144552896/pred.tif
a4e9e608e33b01fba30c070a25f1669541bbc9c4dc543b6b6bc1227af0bdcf67  20260220214732-auto_grown_20260220144552896/pred_reverse.tif
e7c7ce90fcdb559a1634c211f08e9b207ba1e6ab648a0f1aeab5ddf72969b4fc  20260220214732-auto_grown_20260220144552896/pooled.zarr (digest of sorted per-file sha256 list)
7678dc75f88ea520a45f32c42efd0bbeee6864ab394b43579c3480436e72018c  20260220214732-auto_grown_20260220144552896/labels (digest of sorted per-file sha256 list)
44d150c6cfc994c94bc7cd3a2ab33483a91300564b5bb7ae1a5e95d1e672d921  20260221022814-auto_grown_20260220174252405/pred.tif
2b92dceea1f6c41f880f2292676919df7febfc6b5ad9ab70ac35209858c4e1e3  20260221022814-auto_grown_20260220174252405/pred_reverse.tif
59fb55b52bdcbd5e49aa23cdcf1737c5e755d419e42f2ac045d664b2be7a84cc  20260221022814-auto_grown_20260220174252405/pooled.zarr (digest of sorted per-file sha256 list)
d7528210d5b66945e972410f3cbb0f3087ea6f5c3e369d3ccc967038f034d845  20260221022814-auto_grown_20260220174252405/labels (digest of sorted per-file sha256 list)
```

The console of `rheldout.py` ([`rheldout_console.txt`](../records/release/heldout_2026-10-15/rheldout_console.txt)):

```
20260220213127-w00                             AUC fwd 0.8531 rev 0.5324 | valid 20 flagged 0 clusters [] | swapped flagged 0 | text units 0/5 | blank units 0/0 | BLANK
20260220214732-auto_grown_20260220144552896    AUC fwd 0.8176 rev 0.5938 | valid 20 flagged 1 clusters [1] | swapped flagged 0 | text units 1/5 | blank units 0/0 | NOT ESTABLISHED
20260221022814-auto_grown_20260220174252405    AUC fwd 0.8294 rev 0.5363 | valid 20 flagged 0 clusters [] | swapped flagged 0 | text units 0/5 | blank units 0/0 | BLANK
POOLED  AUC fwd 0.8392875361254155 rev 0.548640970286383 | valid 60 flagged 1 (swapped 0) | text units 1/15 CP95 [0.0016864302413527013, 0.3194845665783034] | blank units 0/0
HELDOUT-AUC: TRANSFERS   HELDOUT-RULE: PASS
```

Re-run on 2026-10-15 from the recorded inputs, step 5 produced a `rheldout.json` identical to
[`records/release/heldout_2026-10-15/rheldout.json`](../records/release/heldout_2026-10-15/rheldout.json). The three
reader stats matched the committed `*_read_chart_stats.json` in every field except the file paths (`inputs`,
`contact_sheet`), and each pair was SOUND. VERIFIED.

### Result (2026-10-15): HELDOUT-AUC TRANSFERS, HELDOUT-RULE PASS (not STRONG)

Recorded in [`RULES.md:3296`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3296) `@7925b3a`, with a
correction to two ranges at [`RULES.md:3334`](https://github.com/abundantjoe/hercules/blob/091c2fa/RULES.md?plain=1#L3334)
`@091c2fa`. **MEASURED** (pre-registered bars).

| Output | Bar (declared) | 2026-10-15 |
|---|---|---|
| pooled forward AUC (3,669,681 supervised px, 914,943 ink) | TRANSFERS: forward ≥ 0.75 and reverse ≤ 0.60 | **0.8393** |
| pooled reverse AUC | | **0.5486** |
| per segment, forward / reverse | | w00 0.8531 / 0.5324; auto_grown_20260220144552896 0.8176 / 0.5938; auto_grown_20260220174252405 0.8294 / 0.5363 |
| frozen rule 5.5 (auto grid): valid units, flagged, largest cluster | STRONG: a ≥ 3 cluster; PASS: ≥ 1 flagged | 60 (20 per segment), **1 flagged**, largest cluster 1 → **PASS, not STRONG** |
| depth orders swapped | | 0 flagged; tripwire silent |
| text-bearing units (φ ≥ 0.02) flagged | reported | 1 of 15 (exact 95 % CI 0.0017–0.3195, as printed in RULES.md) |
| supervised blank units (φ = 0, ≥ 50 % supervised) | reported | none exist (0 of 0): the blank arm is empty, not passed |
| on-sheet area per segment | | 12.5338, 12.5625 and 11.9985 cm² |
| `read_chart.py --maps-only` (second path, both grids) | | NOT ESTABLISHED, NOT ESTABLISHED, BLANK; flags 0, 1, 0 on the auto grid and 1, 2, 0 on the (0, 0) grid; no ≥ 3 cluster on either |
| pooling wall time ([`prep_timing.txt`](../records/release/heldout_2026-10-15/prep_timing.txt)) | | 24 s, 22 s, 20 s |
| inference wall time, both orders ([`infer_timing.txt`](../records/release/heldout_2026-10-15/infer_timing.txt)) | | 1825 s, 2274 s, 1940 s |
| scoring (`rheldout.py`; the three reads) | | 58 s; 75 s (the 2026-10-15 re-run, while another job shared the CPU) |

**What this establishes, and what it does not.** The model's pixel signal transfers to a scroll it has not seen.
The frozen 0.5 cm² unit screen almost never fires on that text. The eligible-scroll negatives are therefore what this
screen returns on real unseen text, and they are not evidence that the eligible canvas carries no ink (INFERENCE,
[`RULES.md:3324`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3324) `@7925b3a`).

## Level 3: the corpus reads (days of CPU; not re-run for this release)

The prediction maps of the corpus reads are not committed (several GB of TIFFs, and the project rule forbids
committing maps). Their per-read statistics are committed in `LEDGER.md` and `review_sheets/INDEX.md`. Every verdict
was produced by the pipeline below and can be re-run. That was not done for this release, and whether the tracer
reproduces the same surfaces has not been tested.

1. Build the VC3D tools from source: `VILLA=<villa checkout at 5ab585f> bash scripts/build_vc3d.sh` (Docker; the
   default is `$HERCULES_ROOT/external/villa`). The build bind-mounts the proxy CA bundle `/root/.ccr/ca-bundle.crt`.
   That path is hard-coded in `build_vc3d.sh`, `build_vc3d_extra.sh`, `vc_consensus.sh` and `vc_tools.sh`, so on
   another host edit their `-v /root/.ccr/ca-bundle.crt:/ca.crt:ro` lines.
2. Seeds: `scripts/seeds.py` (surface-prediction volumes from the bucket catalogue).
3. Trace: `scripts/vc_tools.sh trace ...` (`vc_grow_seg_from_seed`), consensus with `scripts/vc_consensus.sh`
   (`vc_grow_seg_from_segments`). Or use the team's published segments (`scripts/fetch_team_segments.py`). For
   scrolls that publish the team's own renders (PHerc1447, PHerc0800), `scripts/fetch_surface_volumes.py` fetches
   them as `render.zarr`, and the render step is skipped.
4. QC: `scripts/patch_qc.py`. Render: `scripts/vc_tools.sh render ...` (`vc_render_tifxyz`, 28 slices, **no
   `--flip-normals`**). On a team mesh that we render ourselves, "forward" is therefore presumably the untrained
   order. Both depth orders are always read, and the depth-swap tripwire covers a mirrored surface (RULES.md R-FLIP).
5. Infer both orders and read: `scripts/run_patch_dir.py` (calls the inference, then `read_chart.py`, and appends
   to `LEDGER.md` and `records/throughput.jsonl`).

Measured throughput on this class of machine is recorded per read in `records/throughput.jsonl` (199 rows).
Example: a 4.7174 cm² PHerc0139 surface took 124 s to render and 2589 s to infer in both orders (row of
2026-09-19T10:11:31Z). [`docs/METHODS.md`](METHODS.md) gives every parameter of every step.

## Fresh-container results, 2026-10-15

Everything below was run in the release container, starting from an empty disk and a fresh clone. **VERIFIED**
unless marked.

| Check | Result |
|---|---|
| Level 0, `bash examples/quickstart.sh` | `ALL CHECKS PASSED` (10 checks), about 16 s |
| Level 1, test suite, no data | **290 passed, 3 skipped** (the three integration tests, with their reasons), 317 s; after `test_window_label_stats.py` was added (`d097884`): **291 passed, 3 skipped**, 325.28 s; at `106d3ec` (one more test): **292 passed, 3 skipped**, 296.63 s |
| Level 1, test suite, public data staged (`HERCULES_DATA` with the w040 mesh and the bucket catalogue) | **293 passed, 0 failed**, 301 s (before `d097884` added one test) |
| Level 1 in a relocated clone (no repo venv, no `HERCULES_ROOT`, as on CI) | 290 passed, 3 skipped, 281 s (before `d097884`); quick start `ALL CHECKS PASSED` |
| `scripts/release_stats.py` | all 10 statistics printed in `RULES.md` reproduce at their printed precision |
| Level 2, R-REPRO | both bars PASS; both prediction maps byte-identical to the September files (above) |
| Level 2, `scripts/reproduce_control.sh` end to end from an empty directory (R-REPRO addendum) | inputs manifest byte-identical to the record (the console prints its digest `cf8b283a…`); labels manifest byte-identical to the record (digest `dfb49aa7…`, computed outside the script with `fetch_control_w040.py <labels dir> --manifest-only`, [`manifest_check.txt`](../records/release/e2e_2026-10-15/manifest_check.txt)); checkpoint sha256 equal to the Hugging Face LFS record; inference 5526 s; integrity SOUND; Gate A 0.99659 / 0.49633 on 1,629,734 px; R-CTRL55 7/71, clusters [4, 2, 1]; the reader 7/71, largest cluster 4; window and whole-file sha256 identical to September (`31f001f4…`, `a5425879…`); every JSON output identical to the resume-mode run except file paths ([`records/release/e2e_2026-10-15/`](../records/release/e2e_2026-10-15/)) |
| Level 2b, R-HELDOUT | TRANSFERS / PASS; `rheldout.py` re-run on the recorded maps gives an identical `rheldout.json` (above) |

What was **not** re-run: Level 3. The first end-to-end attempt of Level 2 was killed by a container restart about
five and a half minutes into inference (started 10:15:31 UTC; restart at about 10:21 UTC, from the operator's NOTE line
in the console). No map can have been written by then (INFERENCE: villa writes each map only after all of that order's
patches, and the relaunch's forward order alone took 10:25:54 to 11:11:16 UTC;
[`first_attempt_note.md`](../records/release/e2e_2026-10-15/first_attempt_note.md)). The relaunch ran the inference for
both orders from the start, because the script skips step 2 only when `out/.infer_complete` exists. The
end-to-end inference time (5526 s) is not a clean timing: documentation checks, short test runs, two local clones and
a figure regeneration ran on the same box meanwhile.

