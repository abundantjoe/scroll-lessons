Provenance: Project HERCULES | owner the owner | [id removed]

# Official Vesuvius tooling on this machine (CPU only)

Date: 2026-09-24. Machine: 4 cores (Intel Xeon @ 2.1 GHz, AVX-512 + AMX-BF16), 15 GB RAM, no GPU, Ubuntu 24.04 host.
All large artefacts live under /work (not in this repo). Nothing was committed or pushed.

## 1. Docker

| Check | Result |
|---|---|
| Daemon at start | Not running (no /var/run/docker.sock). |
| Started by us | `dockerd --data-root /work/docker` with HTTPS_PROXY=http://127.0.0.1:46883 (PID 2869, log /work/logs/dockerd.log). containerd snapshotter, cgroup v1, runc. |
| `docker run --rm hello-world` | OK ("Hello from Docker!"). |
| Docker Hub pull via proxy | OK (hello-world). |
| ghcr.io pull via proxy | OK (anonymous pull of a 1.07 GB public image). |
| Caveat | Containers cannot raise RLIMIT_NOFILE above the host hard limit (20000). `--ulimit nofile=65536` fails. |

### Official ScrollPrize images (ghcr.io, public, anonymous pull; sizes from registry manifests, nothing > 6 GB pulled)

| Image:tag | What it is | Compressed size (amd64) | Built / revision |
|---|---|---|---|
| ghcr.io/scrollprize/villa/volume-cartographer:edge (= :main, same digest sha256:bad516f6...) | Full VC3D + all vc_* tools runtime image (README "docker pull ... :edge"). amd64 + arm64. | 2.76 GB (41 layers) | 2026-05-13, villa commit 1e3f4c0 (about 4 months old). NOT pulled. |
| ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04 | CI builder (Ubuntu 26.04 + apt build deps). deps-hash label 47ac1cbc03eccce2 = matches current tree. | 1.12 GB | 2026-08-12 |
| ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-24.04 | Older builder | 0.94 GB | 2026-05-19 |
| ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f (= :ubuntu-26.04) | Build/runtime deps image used by current CI (.github/workflows/vc3d-ci.yml, vc3d-codeql.yml). Ubuntu 26.04, gcc 15.2, clang 21, cmake 4.2.3, Qt6, Ceres, CGAL, OpenCV, Boost 1.90, python3.14. | 1.07 GB (about 3.9 GB unpacked) | 2026-07-12, revision 0c371b1. PULLED (used for our build). |
| ghcr.io/scrollprize/vc3d-deps/macos, /windows | oras artefacts for mac/win CI (need login in CI) | n/a | not relevant |
| ghcr.io/.../volume-cartographer:buildcache | buildx cache | n/a | not relevant |

Other: GitHub Releases (VC3D Linux AppImage, which bundles the vc_* CLIs) are UNAVAILABLE from this session: api.github.com and github.com web for ScrollPrize/villa return 403 at the proxy (only anonymous git reads are served). ink-detection/optimized_inference has a Dockerfile (GPU target FROM pytorch/pytorch:2.10.0-cuda12.8; CPU target is utility-only) but no published image was found.

## 2. Villa source

* Clone: /work/villa, `git clone --depth 1 --filter=blob:none`, sparse checkout of `.github volume-cartographer vesuvius ink-detection` (73 MB).
* Commit: **41701aa0eaa1aa765523db3f9f972b5830abf549** (2026-09-24T16:38:47Z, "VC3D line annotation: break tag on control points...").

### (a) C++ apps (volume-cartographer/apps/src, targets in apps/CMakeLists.txt)

All seven exist under exactly these names; the CMake target name equals the binary name. They are also members of the aggregate target `vc_cli_all`.

| Target | Links |
|---|---|
| vc_render_tifxyz | vc_core, vc_flattening, Boost::program_options, TIFF |
| vc_grow_seg_from_seed | vc_core, vc_tracer, Boost::program_options |
| vc_grow_seg_from_segments | vc_core, vc_tracer, Boost::program_options |
| vc_tifxyz_selfcross | vc_core, Boost::program_options, opencv_core |
| vc_calc_surface_metrics | vc_core, Boost::program_options |
| vc_flatten | vc_core, vc_flattening, Boost::program_options |
| vc_gen_normalgrids | vc_core, Boost::program_options, opencv_core/imgproc/ximgproc, OpenMP, Ceres |

Configure needs Qt6 (Widgets Gui Core Network Concurrent OpenGLWidgets) even for CLI-only builds, because VC_BUILD_APPS=ON also enables the Qt UI/tracer libraries. The build fetches the following at configure time: ScrollPrize/vc-delta3d v0.1.0 (official), libigl @ae8f959e and libbacktrace (upstream GitHub, pulled by the official CMake; not ScrollPrize repos).
System packages (official list, scripts/install_build_deps.sh, Ubuntu 26.04): build-essential clang lld llvm flang-21 mold cmake(>=3.28) ninja-build ccache pkg-config qt6-base-dev libboost-system/program-options-dev libceres-dev libsuitesparse-dev libopencv-dev libopencv-contrib-dev libcgal-dev libmpfr-dev libgmp-dev libblosc-dev libzstd-dev libcurl4-openssl-dev nlohmann-json3-dev libavahi-client-dev liblz4-dev libtiff-dev zlib1g-dev gfortran libopenblas-dev liblapack-dev liblapacke-dev libomp-dev libscotch-dev libscotchmetis-dev libhwloc-dev. Not installed on the host; we used the official deps image.

### (b) Python `vesuvius` package

* Location: /work/villa/vesuvius (version 0.2.4). pyproject says `requires-python >=3.14,<3.15`; the host has at most Python 3.13. All sources parse under 3.11 and 3.13, so we installed with `--ignore-requires-python`.
* Module confirmed: `vesuvius.ink_detection.inference.infer` (flat surface-volume inference). Also present: `...inference.infer_full3d_tifxyz` (native tifxyz 3D).
* CLI help (verbatim; saved at /work/logs/infer_help.txt):

```
usage: infer.py [-h] [--folder FOLDER] [--checkpoint-path CHECKPOINT_PATH]
                [--output-prefix OUTPUT_PREFIX] [--mask-path MASK_PATH]
                [--resolution RESOLUTION] [--num-workers NUM_WORKERS]
                [--prefetch-factor PREFETCH_FACTOR] [--overlap OVERLAP]
                [--stride STRIDE] [--blend-mode {auto,constant,gaussian,hann}]
                [--layer-start LAYER_START] [--layer-end LAYER_END]
                [--batch-size BATCH_SIZE] [--direction {forward,reverse,both}]
                [--amp-dtype {auto,default,fp16,bf16}] [--tta-mirror]
                [--tta-batch-size TTA_BATCH_SIZE] [--gpus GPUS]
                [--compile-mode COMPILE_MODE] [--no-compile]
                [input_zarr] [checkpoint] [output_tiff]
```

Flag semantics, from reading infer.py and inference_runtime.py:
* `--direction both` runs forward and then reverse layer order. It writes `<out>.tif` plus `<out>_reverse.tif`, so compute is 2x.
* `--tta-mirror` averages all flips of the equal-length patch axes. For a 17x128x128 patch that is Y and X, giving 4 variants and 4x compute.
* `--batch-size` defaults to 1. `--num-workers` (alias `--workers`) defaults to 4. `--overlap` defaults to 0.5, giving stride 64 for a 128 patch. `--stride` overrides it.
* `--gpus` takes a comma list of CUDA ids. On this machine it errors ("CUDA is unavailable"), so omit it.
* CPU: with no `--gpus` and no CUDA, the device falls back to CPU automatically. AMP autocast applies only on CUDA, so a CPU run is fp32.
* torch.compile is on by default (`--compile-mode reduce-overhead`). On CPU it works but costs 30-45 s per batch shape and gives no speed-up, so use `--no-compile`.
* Recommended CPU call: `/opt/hv-ink/bin/python -m vesuvius.ink_detection.inference.infer IN.zarr CKPT.pth OUT.tif --direction both [--tta-mirror] --batch-size 4 --num-workers 1 --no-compile` with `OMP_NUM_THREADS=3`.

## 3. C++ build (no GUI target), DONE

* Route: the official CI deps image (the same one vc3d-ci.yml uses), GCC Release. GCC links real OpenMP; the Clang build uses a serial OpenMP shim. PCH on, flatboi off, `--cpus 3`, `--parallel 3`.
* Command: `nohup /work/scripts/vc_build.sh > /work/logs/vc_build.log 2>&1 &` (PID 4550, now exited, rc=0). The script runs `docker run ... vc3d-deps/linux:sha-0c371b1d... cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DVC_TESTING=OFF -DVC_BUILD_APPS=ON -DVC_BUILD_FLATBOI=OFF -DVC_USE_PCH=ON && cmake --build --parallel 3 --target <7 apps>`.
* Time: configure 6 s, build 3 min 46 s wall (123 steps). Output: /work/villa/volume-cartographer/build/hrc-release-gcc/bin/ (1.5 GB build tree).
* The binaries link against Ubuntu 26.04 libraries, so run them inside the deps image. Wrapper: `/work/bin/vc <app> [args]`. It mounts /work and /home/user at the same paths, uses host network plus the proxy CA, and defaults to `--cpus 3` / `OMP_NUM_THREADS=3`.
* All 7 apps pass `--help` with rc=0. Full help texts: /work/logs/vc_apps_help_full.txt.

## 4. Python ink inference on CPU

* venv: /opt/hv-ink (Python 3.13.12). It has torch 2.14.0+cpu and torchvision 0.29.0+cpu from download.pytorch.org/whl/cpu, plus `pip install -e /work/villa/vesuvius --ignore-requires-python` with the base deps, tifffile, imagecodecs, einops and timm from PyPI. Full list: /work/logs/hv-ink-freeze.txt. The full `[models]` extra was NOT installed: it pulls cucim-cu13, nnunetv2, wandb and a monorepo-only volume-cartographer package, none of which flat inference needs. /opt/hv is untouched.
* Checkpoint "ink_9um hybrid_3d2d seed42 step-075000": found on HF model repo **scrollprize/ink_9um** (public, not gated; revision 7109667e2607db1b90c37c8b09cb876ea7fe7bb1).
  * Path: /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth (model card copied to /work/ckpt/ink_9um/README.md)
  * Size: 138,360,039 bytes
  * sha256: e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab (matches the HF LFS hash)
  * Licence: **MIT** (model-card metadata `license: mit`; no separate LICENSE file in the repo)
  * Labels bucket hf://buckets/scrollprize/datasets/ink_9um is publicly listable (not downloaded).
* Embedded config:
  * model_type vesuvius_unet_3d_stem_2d (local 3D stem into a 2D U-Net), 34.5 M params, EMA off, step 74999.
  * crop/patch 17 x 128 x 128: a 17-of-21 z-window, center-cropped from a (21, Y, X) surface volume at about 9.6 um (level-2 XY, 4x z mean), or native 9.362 um.
  * Normalisation robust_mad (p1/p99 clip, median/MAD) applied per patch at inference ("tifxyz_robust").
  * Trained in fp16 mixed precision; BCE label smoothing 0.5, so no-ink sits near p = 0.25.
  * Default inference stride 64 (overlap 0.5), Hann blending.
* Measured CPU forward pass: random N(0,1) input, `torch.set_num_threads(3)`, inference_mode, no other heavy load. Raw results: /work/logs/bench_ink9um_cpu.jsonl. Script: /work/scripts/bench_ink9um_cpu.py.

| Mode | Batch 1 | Batch 4 |
|---|---|---|
| eager fp32 (official CPU path, `--no-compile`) | 0.114 s/tile | 0.114 s/tile |
| torch.compile (CLI default) | 0.118 s/tile (+44 s compile) | 0.121 s/tile (+28 s compile) |
| bf16 CPU autocast (NOT used by the CLI on CPU; would need a code change) | 0.073 s/tile | 0.061 s/tile |

* Extrapolation for one 2 x 2 cm window at 9.366 um: 2136 x 2136 px, patch 128, stride 64, which is 33 x 33 = 1089 tiles per direction. Figures are model compute only, wall-clock with 3 threads; multiply by 3 for core-hours. Zarr reads, normalisation and blending are extra and likely +10-30% from local disk, more if streamed from S3.
  * Both depth orders, no TTA: 2178 tiles, **0.069 h (about 4 min)**.
  * Both depth orders with `--tta-mirror`: 8712 forward passes, **0.28 h (about 17 min)**.
  * One direction without TTA: 0.034 h.
  * With bf16 (not the official CPU path): 0.037 h and 0.15 h.

## 5. ink_canonical_2um r152_3ddec_v2_l5_epoch13.ckpt

* Found: HF model repo **scrollprize/ink_canonical_2um** (public, not gated; revision 075855bc69317ef6febf39a0d9d687b27d2b7c29). The file r152_3ddec_v2_l5_epoch13.ckpt is 1,549,556,213 bytes (1.55 GB), LFS sha256 36dd0de84b7b7aa6590184192c7415466cd8a1ba7c1e59f42c6373846373c3e0. Licence **MIT** per the model card (tomographic data CC BY-NC 4.0). Not downloaded, to save shared disk; it is under 3 GB and can be fetched later if needed.
* Model: ResNet3D-152 encoder plus 3D decoder, Lightning checkpoint (config: size 256, enc r152, with_norm true). Code: villa ink-detection/optimized_inference (model_resnet3d_3d_decoder.py; README suggests TILE_SIZE=256 and a 62-layer window).
  * Official support: the docs say `STEP=inference` is GPU-image only.
  * Code path outside that image: `entrypoint.py` picks cuda if available, else cpu, and autocasts on CPU (bf16).
  * The entrypoint is S3-oriented (S3_PATH layers/*.tif), so local use needs a small driver.
* Measured on CPU with random weights (compute does not depend on weight values): 130.4 M params, input 1x1x62x256x256, output 64x64, 3 threads. Raw results: /work/logs/bench_r152_3ddec_cpu.jsonl.
  * bf16 autocast: **5.25 s/tile**, peak RSS 1.6 GB
  * fp32: 8.0 s/tile
* Per 2 x 2 cm window, one pass, bf16:

| Pixel size | Stride 128 | Stride 64 |
|---|---|---|
| 2.4 um (8337 px) | 6.2 h | 24 h |
| 2.0 um | 8.9 h | 35 h |

  * It also needs a 62-layer 2 um surface volume, about 4+ GB uint8 per window.
* Verdict: a CPU run is plausible only for small ROIs or a single overnight pass. It is not practical for multi-pass, TTA or multi-window work; use the 9 um model on CPU.

## Disk used by this work (budget 14 GB)

| Path | Size |
|---|---|
| /work/docker (dockerd data-root, deps image) | 4.9 GB |
| /work/villa (sparse clone plus 1.5 GB build tree) | 1.5 GB |
| /opt/hv-ink | 1.3 GB |
| /work/ckpt | 0.13 GB |
| logs and scripts | < 1 MB |
| **Total** | **about 7.8 GB** |

Free disk on / afterwards: 22 GB.

## Blockers / notes

* GitHub Releases, including the Linux AppImage with bundled CLIs, and api.github.com are blocked for ScrollPrize/villa in this session (403 at the proxy). Git clone works.
* vesuvius requires Python 3.14. We ran it on 3.13 with `--ignore-requires-python`, and the model build and CLI work. Python 3.14 exists only inside the vc3d-deps image.
* The dockerd started by this work (PID 2869) keeps running. Stop it with `kill 2869`, and delete /work/docker to reclaim 4.9 GB.
* The ink_9um HF card still names the old module `koine_machines.inference.infer`. In villa at 41701aa it is `vesuvius.ink_detection.inference.infer`.
