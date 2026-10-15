# Reproducing this release

Six levels, from 2.5 seconds to about half a day for all of them on the release machine. Each level states what it proves, the exact
commands, the expected output (with checksums where outputs are deterministic) and the runtime on the release machine: measured
unless marked as an estimate (logs are cited where they exist). Labels: **VERIFIED** = re-run for this
release and checked; **MEASURED** = recorded when the original run happened (log or record cited), not re-run; **NOT VERIFIED** = we
did not re-run it and make no claim.

| Level | What it checks | Needs | Runtime |
|---|---|---|---|
| 0 | the toolkit runs on real held-out data | nothing but `pip install` | 2.5 s |
| 1 | the toolkit passes its 15 unit tests (synthetic data, bundled demo); with crop `20231005123336/held2` on disk, it equals the research scripts' records of that crop (pixel AUC: the same float; stroke AUC and L: the 4 decimals stored) | level 0; the 3 record tests need held2 prepared at level 4 and are skipped otherwise | 9.1–10.1 s (46–64 s with data) |
| 2 | the 12 downloaded label, ink-overview and surface-render files are byte-identical to their public sources (the CT volumes are pinned by versioned URL and metadata hash, not byte-verified) | network | 35 s (≈ 97 MB) |
| 3 | the released weights regenerate the published v8, GP-R1 and E maps and E's pixel AUC | level 2 + the full pipeline; one prepared evaluation crop | ≈ 13.6–15.1 min prep (estimated) + 80–97 s check |
| 4 | the pixel AUCs of E, v8, GP-R1, v7, v1b and the team comparator on the 7 evaluation and 6 C1 crops, regenerated from public data with the released weights; the statistics built on them; the toolkit check | level 2 + 13 prepared crops, ≈ 57 GB transient download | ≈ 3.1–3.6 h (estimated) |
| 5 | retraining v8 and GP-R1 from scratch (commands only: not re-run, no comparison with the released weights) | level 2 + 16 prepared crops (15 for training + the validation crop `20231012184424/held4`) | 5.49 h training (logs) + ≈ 1.4–1.7 h prep (estimated) |

## Environment

**MEASURED** on the release machine: Python 3.11.15, Ubuntu 24.04.4 LTS, Linux 6.18 x86_64, 4 vCPU Intel Xeon @ 2.10 GHz, 15 GB RAM,
no GPU. The exact package set is [`requirements-lock.txt`](../requirements-lock.txt) (pip freeze; numpy 2.4.6, scipy 1.17.1,
pillow 12.3.0, torch 2.14.0+cpu, opencv-python-headless 5.0.0.93, zarr 3.1.6, matplotlib 3.11.2, pytest 9.1.1).

```bash
git clone https://github.com/abundantjoe/megara && cd megara
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"                     # levels 0-1: the toolkit only (numpy, scipy, pillow, pytest)
pip install -r requirements-lock.txt --extra-index-url https://download.pytorch.org/whl/cpu   # levels 2-5: the full pipeline
```

## Level 0 — demo on bundled real data (2.5 s in a fresh clone)

```bash
inkeval demo                                  # or: python -m inkeval demo
```

**VERIFIED** expected output (two held-out Scroll 1 crops pooled to 19.2 µm; values truncated, never rounded up):

```
crop                         method   pixel  stroke  local L
20231005123336_held2         e        0.929   0.988    0.997
20231005123336_held2         v7       0.800   0.878    0.913
20231005123336_held2         team     0.954   0.996    0.995
20231210121321_held1         e        0.875   0.973    0.966
20231210121321_held1         v7       0.571   0.562    0.735
20231210121321_held1         team     0.943   0.997    1.000

negative control - label swap between the two crops (should sit near 0.5):
  e     mean 0.502 over 2 ordered pairs
  v7    mean 0.462 over 2 ordered pairs
  team  mean 0.473 over 2 ordered pairs
```

These differ from the published 2.4 µm numbers because the bundled crops are pooled 8× to keep the package at 3.1 MB.

## Level 1 — test suite (9.1–10.1 s; 46–64 s with the research data)

```bash
pytest -q
```

**VERIFIED**: `18 passed in 46.11s` on the release machine with the research data present (53.61 s on a re-run of 2026-10-15);
`15 passed, 3 skipped in 9.93s` in a fresh clone of the repository without `data/` (9.13 s and 10.14 s on re-runs, the latter from a clone of `main` on GitHub), where the three tests in
`tests/test_published.py` that compare against the full-resolution judge records are skipped. Those three tests assert that
`inkeval` recomputes, for crop `20231005123336/held2`, the published pixel AUC of E and team **exactly** (the same float, not a
tolerance), and E's stroke AUC and local L to the 4 decimals the research scripts stored, with identical disk counts. The full-resolution data of held2 exist only after level 4.

## Level 2 — fetch and verify the downloadable inputs (35 s)

```bash
python scripts/fetch_inputs.py               # downloads labels and overviews, verifies SHA-256, copies the crop records into data/
```

**VERIFIED** (2026-10-15): all 12 downloadable inputs are byte-identical to the copies used for every Scroll 1 result
([`results/input_manifest.json`](../results/input_manifest.json), built by
`scripts/manifest_inputs.py results/input_manifest.json --verify-remote`); run in an empty directory on the release machine,
`fetch_inputs.py` printed `ALL INPUTS VERIFIED` and exited 0 in 35 s (97 514 361 bytes). The script discards any download whose hash
differs (it is never written to its destination; an existing local copy with a wrong hash is left in place, but the run fails) and
exits non-zero. The 2.4 µm surface volumes are streamed per crop and pinned by their versioned URL
(`2.4um-0.22m-78keV-volume-20260411134726`) and the SHA-256 of their `.zarray`/`.zattrs`, recorded in the manifest (no release script
re-checks them; `fetch_zarr_region.py` checks only that every chunk is present).

| segment | input | SHA-256 |
|---|---|---|
| 20231005123336 | Grand-Prize label `all_labels/20231005123336_inklabels.png` | `7e8f577fe511e8e160799baf00120277a72dcd93b595aaa2edac74c90c521cc6` |
| 20231210121321 | Grand-Prize label `all_labels/20231210121321_inklabels.png` | `19f73026a1bdf0baffe8d103f27d5dd0a0ffeb6121ae260de5b3b8ff602d3e74` |
| 20230929220926 | Grand-Prize label `all_labels/20230929220926_inklabels.png` | `7521f4d9dae002a9c59e11b8eb68f8a5c4aaa9cb687ba82e3acebc26f76d8437` |
| 20231012184424 | Grand-Prize label **`all_labels/20231012184423_inklabels.png`** (adjacent ID; recorded at declaration) | `57d266cfcd4988eb16c4e3506a563ada5cb8e794f1c211d48230ed70b491e8c8` |
| 20231005123336 | team ink overview `…-ds8.jpg` | `a8e19a0a3e64b571b75abed0ff3da28afe0be1fea5054fb6462b53b1e2ebca39` |
| 20231210121321 | team ink overview `…-ds8.jpg` | `8fdf696eb72be2bbb5c54d49014613c9f6a8727d8203ea375ece0f83c204208c` |
| 20230929220926 | team ink overview `…-ds8.jpg` | `935b1e02fea8d800bbabdc65ec9a4e3cd41033654261d5cc3508006262750b0c` |
| 20231012184424 | team ink overview `…-ds8.jpg` | `4f78e361cb5885fdb8a4cf81217e1368a7928d30ab83848014f931967d1527a3` |

Full URLs, byte sizes, surface renders and zarr metadata hashes are in the manifest. Label URLs:
`https://raw.githubusercontent.com/younader/Vesuvius-Grandprize-Winner/main/all_labels/<id>_inklabels.png`. Overview URLs:
`https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/<seg>/ink-detection/downsampled/PHercParis4-<seg>-2.4um-0.22m-78keV-volume-20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128-ds8.jpg`.
The pipeline reads `<seg>_inklabels_L.png`, a grayscale conversion that `fetch_inputs.py` creates; **VERIFIED** pixel-identical to the
published file after `convert('L')`.

## Level 3 — regenerate the published maps from the released weights (≈ 13.6–15.1 min, estimated from the C1 log, + 80–97 s)

```bash
scripts/run_judge_crops.sh 20231005123336 2 82 data/s1/20231005123336/crops.json held1    # prepare one evaluation crop (≈ 13.6–15.1 min, estimated)
python scripts/check_reproducibility.py 20231005123336 held1
```

The preparation time is estimated from the C1 run, which used the same steps (13.6–15.1 min per crop after the first,
[`results/logs/c1.log`](../results/logs/c1.log)); no run of `run_judge_crops.sh` itself is logged.

**VERIFIED** on the release machine for the second command, on the 7 evaluation crops as prepared by the original driver
`scripts/run_s1_seg.sh` (preparation by `run_judge_crops.sh` was not re-run for the release: NOT VERIFIED) — every array regenerated
bit-for-bit ([`results/reproducibility_check.json`](../results/reproducibility_check.json)); re-run on held1 on 2026-10-15, 97 s, with
this output:

```
v8_sha256      OK  0c21bedadcc0fa9d3e2af4124b8672aeddd1f0b8865a70d88a31f1db7a26139f
gpr1_sha256    OK  91c57f59f295298a4ab996644c584544302381fbc66a037afec591af840560d5
e_sha256       OK  8e960deea3c4c8e4b8f668bdda5dd4c40ca2d4d0688cc1bbed79cf5653c92efc
e_pixel_auc    OK  0.8828924602993242
RESULT: bit-identical to the release
```

PyTorch CPU kernels can differ across processor types. On other hardware the hashes may differ; the check then passes if E's pixel AUC
is within 0.001 of the published value and says so. **NOT VERIFIED** on any machine other than the release machine.

Released weights ([`models/SHA256SUMS`](../models/SHA256SUMS)):

```
7e5304589356e3fc3782f06242752e6560159c69a9d783f43021a8a2b201774a  v8_unet.pt
0453fcfc8d276d135632c09ada32e04aec3fc50f2e829af75c27cd84bb9d851b  gpr1.pt
fc9c8449c6af44d75b59a85989ff533e0b36ccf13a513e33b37dc3ab0579e92d  v6b_unet.pt
d0617677d164c8e2b8b52ce46475941ed0e96bd83dd1946205805d0c19cf7d47  v6c_unet.pt
```

## Level 4 — the released methods' pixel AUCs from public data, and the statistics (≈ 3.1–3.6 h, estimated)

```bash
# the 7 evaluation crops (K0 K1 = slice range searched for the sheet faces)
scripts/run_judge_crops.sh 20231005123336 2 82  data/s1/20231005123336/crops.json held1 held2 held3
scripts/run_judge_crops.sh 20231210121321 24 84 data/s1/20231210121321/crops.json held1 held2 held3 held4
# the 6 untouched confirmation crops (C1)
scripts/run_judge_crops.sh 20231005123336 2 82  data/s1/20231005123336/confirm.json
scripts/run_judge_crops.sh 20231210121321 24 84 data/s1/20231210121321/confirm.json
EV="20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4"
CF="20231005123336:conf1 20231005123336:conf2 20231005123336:conf3 20231210121321:conf1 20231210121321:conf2 20231210121321:conf3"
# the toolkit against the published judge, stroke and L records of these crops (release_stats.py reads its full-precision values)
python scripts/check_toolkit_records.py results/toolkit_vs_records.json --jobs 3 $EV $CF
# statistics: crop-level bootstrap CIs, paired differences, label-swap null
python scripts/release_stats.py evaluation7 results/stats_evaluation7.json $EV
python scripts/release_stats.py confirmation results/stats_confirmation.json $CF
python scripts/c1_analysis.py results/stats_evaluation7.json results/stats_confirmation.json results/c1_analysis.json
```

These commands overwrite the committed files in `results/`; `git diff` shows what changed.

Expected: `check_toolkit_records.py` prints `65 method-crop comparisons, 0 failures` (VERIFIED on the release machine against the
maps of the original runs, not against maps regenerated by these commands; 728–803 s with 3 workers, the re-run of 2026-10-15
writing a file identical to [`results/toolkit_vs_records.json`](../results/toolkit_vs_records.json)). `results/stats_confirmation.json` as committed;
`results/stats_evaluation7.json` as committed for E, v8, GP-R1, v7, v1b and the team comparator, but without v0.1b, v2, v3, v6b and v6c
and the paired differences that use them (`run_judge_crops.sh` does not write their judge records; see below). The stroke AUC and L
records keep their committed values: `stroke_test.py` and `local_stroke_test.py` skip every crop and method already in `stats/stroke_test.json`
and `stats/local_stroke_test.json`, and `release_stats.py` takes stroke and L from those records, at full precision from the toolkit
check where it equals them at 4 decimals. That the regenerated pixel AUCs equal the committed values is
**NOT VERIFIED** end to end: the 13 crops were not re-prepared for the release (level 3 shows the v8, GP-R1 and E maps of the 7
evaluation crops regenerated bit for bit from their prepared stacks). On the release machine, with the maps of the original runs,
the three statistics commands regenerate the committed `stats_evaluation7.json`, `stats_confirmation.json` and both per-crop CSVs byte
for byte, and `c1_analysis.json` identical apart from the input paths it records (VERIFIED 2026-10-15; 69 s, 49 s and 1 s).

**MEASURED** runtimes: 57–136 s per 4.29–4.46 GB crop download in the original runs of these 13 crops
([`results/logs/s1seg1b.log`](../results/logs/s1seg1b.log), [`s1seg2.log`](../results/logs/s1seg2.log),
[`c1.log`](../results/logs/c1.log)); 13.6–15.1 min per crop end to end after the first in the C1 run, which used the same steps
([`results/logs/c1.log`](../results/logs/c1.log); the first C1 crop finished 22.4 min after the C1 declaration commit, its start is
not logged). Estimated total: ≈ 3.1–3.6 h for the 13 crops, the toolkit check and the statistics. Disk: one raw crop (≈ 4.4 GB) plus
its depth stack (≈ 1.7 GB) at a time; each prepared crop keeps 0.87 GB (879 483 738 bytes for C1 crop
`20231005123336/conf1`, prepared by the same steps).

`run_judge_crops.sh` regenerates the maps and judge records of E, v8, GP-R1, v7, the team comparator and v1b (it also recomputes the
v0.1b map but does not judge it). The other baselines in the results table (v0.1b, v2, v3, v6b, v6c) come from the judge records
written when they were judged. v6b and v6c can be regenerated on a prepared evaluation crop from their released weights, as in
[`scripts/run_v7_v6b.sh`](../scripts/run_v7_v6b.sh) and [`scripts/run_v6c.sh`](../scripts/run_v6c.sh)
(`OMP_NUM_THREADS=2 python scripts/s1_v5.py predict <crop_dir> models/v6b_unet.pt v6b`, then `python scripts/s1_judge.py <crop_dir>
data/s1/<seg>/crops.json <crop> data/s1/labels/<seg>_inklabels_L.png v6b 2.4`; NOT VERIFIED). v0.1b, v2 and v3 require the drivers in
[`archive/scripts/`](../archive/scripts) and [`scripts/run_s1_seg.sh`](../scripts/run_s1_seg.sh) (which also needs the v5 weights,
which are not released because v5 is a failed method).

## Level 5 — retrain from scratch (5.49 h training, measured; ≈ 1.4–1.7 h preparation, estimated)

```bash
# 1. training crops on the two pure-training segments: 4 + 11 windows from the committed crop records (copied to
#    data/s1/<seg>/crops.json by fetch_inputs.py); 4.8–5.8 min each (MEASURED, results/logs/s1prep.log, results/logs/v8.log)
scripts/run_s1_prep.sh 20230929220926 24 84
scripts/run_s1_prep.sh 20231012184424 24 84
# 2. the segment-1 TRAIN crop (its pooled stack and label are needed before step 3)
scripts/run_judge_crops.sh 20231005123336 2 82 data/s1/20231005123336/crops.json train
# 3. no-veto labels on all 16 crops (15 for training + the validation crop 20231012184424/held4)
python scripts/build_noveto_y.py data/s1/20231005123336/derived/train data/s1/20230929220926/derived/held* data/s1/20231012184424/derived/held*
# 4. v8: 12 000 steps on the 15 training crops (MEASURED 11 458 s, results/logs/v8.log)
DIRS=$(python -c "import json;print(','.join(['data/s1/20231005123336/derived/train']+[f'data/s1/{s}/derived/{c[\"name\"]}' for s in ('20230929220926','20231012184424') for c in json.load(open(f'data/s1/{s}/crops.json'))['crops'] if not (s=='20231012184424' and c['name']=='held4')]))")
V5_Y=ds8_y_noveto.npy V5_SELECT=auc V5_LR=3e-4 V5_WD=1e-4 V5_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=3 \
  python scripts/s1_v5.py train "$DIRS" models/v8_retrained.pt 12000
# 5. GP-R1: 4 000 steps (MEASURED 8 334 s while sharing the CPUs with another run, results/logs/gpr1.log)
GPR_X=ds8_x.npy GPR_Y=ds8_y_noveto.npy GPR_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=3 \
  python scripts/gpr.py train "$DIRS" models/gpr1_retrained.pt 4000
```

These are the training commands of the original drivers `scripts/run_v8.sh` (which also re-selects the windows and judges) and
`scripts/run_gpr1.sh` (which also judges), with the output written to `models/v8_retrained.pt` and `models/gpr1_retrained.pt` (the
originals wrote `data/s1/v8_unet.pt` and `data/s1/gpr1.pt`; the released copies are `models/v8_unet.pt` and `models/gpr1.pt`). The
preparation estimate is 15 crops at the times above plus the train crop at the C1 per-crop time.

**NOT VERIFIED**: we did not retrain for the release, and no comparison of retrained with released weights is given. Seeds are fixed
(`torch.manual_seed(0)` and `np.random.seed(0)` in both scripts; v8 samples patches with the seeded `np.random`, GP-R1 with
`default_rng(0)`), but bit-identical retraining across machines or thread counts is not claimed.

## Pre-registration order

```bash
python scripts/check_preregistration.py      # exit 0 = each of the 18 listed declarations committed before its result
```

**VERIFIED**: for all 18 tests in the list (16 pre-registered, including C1, plus the post-hoc D3 and N1), the commit introducing the
declaration heading precedes the commit introducing the result heading
([`results/preregistration_order.json`](../results/preregistration_order.json)). The check is necessary, not sufficient: for the stroke
test and L the declaration commit already contains results, and R2's maps were computed before its declaration commit (RESULTS §1).
The times typed into notebook headings are not used — they were written by hand and some disagree with the commit times.

## The 2026-09 calibration work on PHerc. 1667 (w028)

The early papyrus-subtraction gates ran on segment w028 of PHerc. 1667 (see [`docs/RULES.md`](RULES.md), GATE-T1). Their scripts are in
[`archive/scripts/`](../archive/scripts) with their original paths inside the drivers; run them from commit `bde701a`, the last commit
before the release reorganisation (`b370331`), where every script path is as the drivers expect. Drivers of that era `cd` to
`/home/user/megara` (the release machine's checkout path); clone there or edit that line. Their GATE-T1 results for v0.1b, v0.2 and
v0.3p are recorded in `stats/w028_gate_t1_*.json`; the v0.1 and GATE-T2(b) (w040) results only in [`docs/RULES.md`](RULES.md). The
w028 inputs the drivers read (`data/w028/crops.json`, the team prediction `data/w028/pred_2.4um_team.tif`,
`data/labels/w028_inklabels.zarr`) are not fetched by any release script (NOT VERIFIED).
