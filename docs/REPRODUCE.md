# Reproduce

## The headline result: blank margins halve the strong ink in the letters of a positive control; the margin fill (exploratory) brings the in-box strong fraction back, but only part of the full-context strong pixels

`scripts/reproduce.sh` reruns the PHerc0343 positive-control strip experiment at d = +1 from fresh inputs: all
pre-registered d = +1 arms plus the exploratory fill arms `F13` and `FD8`, i.e. 29 strip surfaces, 3 models, 87 ink
runs, about 1 GB of CT. It compares the result with the committed original run. Not rerun: the original run's d = −2
depth arm (pre-registered decision 6, report only) and its exploratory `X13` arm; their values are in
[`original_results.json`](../results/control_strips/original_results.json) and RESULTS §1.

Our own rerun, from a fresh clone of `main` with fresh CT and weight downloads, is committed in
[`results/control_strips_rerun/`](../results/control_strips_rerun/). The match is reported in
[RESULTS.md §2](RESULTS.md#2-rerun-with-fresh-inputs).

## 1. Environment (versions of the reference run)

| component | version | how |
|---|---|---|
| Analysis Python | Python 3.11.15; numpy 2.4.6, scipy 1.17.1, zarr 2.18.7, tifffile 2026.3.3, Pillow 12.3.0, pytest 9.1.1, s3fs (any recent); the DejaVu Sans font at `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` (used by `scripts/pipeline/make_panel.py`; Debian/Ubuntu: `apt install fonts-dejavu-core`) | `pip install -e '.[test]' numpy==2.4.6 scipy==1.17.1 zarr==2.18.7 tifffile==2026.3.3 pillow==12.3.0 pytest==9.1.1 s3fs` |
| Ink Python | Python 3.13.12; torch 2.14.0+cpu; numpy 2.5.3; zarr 3.4.0; safetensors 0.8.0; villa `vesuvius` 0.2.4 at ScrollPrize/villa commit `41701aa` | `git clone https://github.com/ScrollPrize/villa && git -C villa checkout 41701aa`, then `pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu && pip install numpy==2.5.3 zarr==3.4.0 safetensors==0.8.0 && pip install --ignore-requires-python -e villa/vesuvius`. villa `41701aa` declares Python ≥ 3.14, < 3.15; the reference run used 3.13.12, so the editable install needs `--ignore-requires-python` (checked with pip 25.3). |
| Renderer | volume-cartographer at villa `41701aa`, CMake `Release`, `VC_BUILD_APPS=ON`, g++, built inside `ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f` | `cmake -S villa/volume-cartographer -B <build> -DCMAKE_BUILD_TYPE=Release -DVC_BUILD_APPS=ON && cmake --build <build> -j` inside the image; `scripts/pipeline/vc.sh` runs the built apps in the same image |
| Hardware | 4 CPU cores, 16 GB RAM, about 3 GB of fast scratch (we used a RAM disk), docker; no GPU | |

## 2. Data inputs

| input | where | integrity |
|---|---|---|
| PHerc0343 CT, level 0 | `s3://vesuvius-challenge-open-data/PHerc0343/volumes/20250521140437-8.640um-1.2m-116keV-masked.zarr` (anonymous). Only the chunks the strips touch are fetched: 1.05 GB in our run | chunks are copied byte for byte |
| Control segment, letter boxes, scroll axis | `git clone https://github.com/Nieuwlaar/pherc343-first-letters && git -C pherc343-first-letters checkout e8370f1` | `outputs/SHA256SUMS` (Erwin's own) and [`docs/inputs.sha256`](inputs.sha256), both checked by `reproduce.sh` |
| ink_9um seed 42 / seed 43, step 75 000 | `huggingface.co/scrollprize/ink_9um` | sha256 in `scripts/get_weights.sh` |
| dense_native, step 16 000 | `huggingface.co/Nieuwlaar/ink9um-dense-native` (safetensors + training config), rebuilt to a villa checkpoint by `scripts/rebuild_dense_native.py` | sha256 of the inputs in `scripts/get_weights.sh`; the rebuild is bit-identical to our checkpoint (METHODS §1) |

Total download, measured in our run: 1.05 GB of CT plus 0.55 GB of weights.

## 3. Commands

```bash
git clone --depth 1 --single-branch --branch main https://github.com/abundantjoe/dominion-release && cd dominion-release
pip install -e '.[test]' s3fs && pytest                      # 27 synthetic tests, under 5 s
git clone https://github.com/Nieuwlaar/pherc343-first-letters /data/pherc343 && git -C /data/pherc343 checkout e8370f1

export WORK=/data/work                        # scratch for CT mirror, renders, maps (about 3 GB)
export ERWIN=/data/pherc343
export PYH=$(which python)                    # analysis python (this package + s3fs)
export PYI=/path/to/ink-env/bin/python        # python with villa vesuvius + torch
export VC_BIN=/path/to/villa/volume-cartographer/<build>/bin
export VC_MOUNTS="/data /path/to/villa"       # host dirs the renderer container must see (WORK and the villa build tree)
export DOCKER_DATA_ROOT=/var/lib/docker       # only used if dockerd has to be started
bash scripts/reproduce.sh
```

`reproduce.sh` does five things:
1. Verifies the input checksums.
2. Fetches and verifies the weights and rebuilds dense_native (`scripts/get_weights.sh`).
3. Builds the arms (`scripts/control_strips/make_arms.py`).
4. Runs the reference pipeline (`scripts/pipeline/batch_ink.sh`): first on the plain arms, then on the fill arms with
   `RENDER_FILL=reflect`.
5. Scores (`scripts/control_strips/score_arms.py`) and compares with `results/control_strips/original_results.json`.

It stops on a checksum mismatch, a failed strip or incomplete scoring. It writes to `$WORK/out` (set `OUT` to change
this), never over the committed `results/control_strips_rerun/`.

## 4. Expected outputs

`$WORK/out/results.json` holds per arm (compare it with the committed `results/control_strips_rerun/results.json`):
- f_in, f_out, E, recall with its 95 % letter-bootstrap CI, r, coverage, band, box AUC;
- the pre-registered decisions;
- a `reproduction_vs_original` block.

Our run's values are in [RESULTS.md](RESULTS.md). The sha256 of every ensemble map we produced is in
[`results/control_strips_rerun/ens_sha256.txt`](../results/control_strips_rerun/ens_sha256.txt); check yours with
`(cd $WORK/bi && sha256sum -c /path/to/results/control_strips_rerun/ens_sha256.txt)`. CPU inference with the same inputs
and versions should give identical maps. A different torch or BLAS build may change the last bits of p, which can move
individual pixels across the p > 0.55 threshold.

Two optional checks on the same work directory (each under a minute):

```bash
python scripts/control_strips/box_shift_check.py --bi $WORK/bi --erwin $ERWIN --out box_shift_check.json   # expect "decisions_changed": []
python scripts/control_strips/ink_runtime.py $WORK/bi --out ink_runtime.json
```

## 5. Runtime

Our run took 71.4 min of wall time on 4 cores with three ink runs at a time; the breakdown is in RESULTS §2. Most of it
is ink inference: 92.5 s per Mpx per model run on one thread, over the 87 runs
([`ink_runtime.json`](../results/control_strips_rerun/ink_runtime.json), from `scripts/control_strips/ink_runtime.py`).

## 6. Figures and the other results

```bash
pip install matplotlib
python scripts/make_figures.py --bi $WORK/bi       # fig. 1-5 into figures/
```

- Figures 1 and 2 and the PHerc0268 aggregates come from committed JSON
  (`results/margin_artifact/*.json`). The PHerc0268 strip images behind those aggregates are not public
  (PHerc0268 has not been officially read), so `scripts/natural_experiment.py` cannot be rerun from this repository alone.
- Figure 3 comes from your `$WORK/bi`; figure 4 always from the committed `results/control_strips_rerun/results.json`,
  not from your run (copy your `$WORK/out/results.json` there to plot your own).
- Figure 5 comes from `results/blind_read/read2_calibrated_controls.json`.
