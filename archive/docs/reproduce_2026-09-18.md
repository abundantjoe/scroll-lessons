# How to reproduce every number in RULES.md

All results come from scripts in `scripts/`, run by the drivers listed below. Raw CT is never kept: each driver fetches one crop of a
published surface volume, derives maps, and deletes the raw chunks. Nothing here needs a GPU.

## Pipeline
1. `scripts/fetch_zarr_region.py <zarr-url> <level> <y0> <y1> <x0> <x1> <local-store>` — fetch one window of a surface volume.
   Verifies chunk presence even when a completion marker exists (a marker that hid missing chunks caused the w028 text3/text4 incident).
2. `scripts/topo_faces.py <store> <level> <y0> <y1> <x0> <x1> <k0> <k1> <outdir>` — per pixel: crest of the bright band, its 50 %
   ends (`k_top`, `k_bot`, sub-slice), face intensities, mid CT slice, validity. Outputs float16.
3. `scripts/residual.py <outdir> <pitch_um> --tag <tag> [--edge-margin-mm M]` — relief, oriented fibre background, damage/grain mask,
   band-pass, and the v0.1/v0.1b/v0.2 score. `--edge-margin-mm 0.1` is mask J (declared 2026-09-18); the default 0.4 is the v0.1b mask.
4. Scoring: `scripts/s1_score.py` (depth-template projection, `--dump` writes the per-depth stacks), `scripts/v03p.py` (peak
   brightness), `scripts/s1_v2.py` (band-passed projection), `scripts/s1_v3.py` (66-feature ridge), `scripts/s1_v5.py` (surface-aligned
   U-Net; `V5_LR`, `V5_WD`, `V5_VAL_DIR` env overrides), `scripts/s1_ds_stack.py` (19.2 µm pooled stacks used by the net).
5. Judging: `scripts/s1_judge.py <dir> <crops.json> <crop> <label.png> <tag> <pitch>` (pixel and letter AUC, writes the class masks);
   `scripts/stroke_test.py <seg>:<crop> ...` (stroke AUC, the declared replacement for the letter test);
   `scripts/gate_eval.py` (w028 gates); `scripts/s1_summary.py` (per-segment means).
6. Reference placement: `scripts/s1_register_label.py` (global scale+offset by zone-restricted FFT correlation),
   `scripts/s1_refine_reg.py` (per-crop translation), `scripts/s1_local_reg_check.py` (residual shift audit).
   `scripts/s1_select_crops.py` freezes the crop coordinates; both are copied into `stats/` as the record.

## Drivers
`scripts/run_w028_crops.sh`, `run_chain_w028.sh`, `run_v03p.sh`, `run_v03php.sh` (w028 gates T1);
`scripts/run_s1.sh`, `run_s1_v2.sh`, `run_s1_v3.sh`, `run_s1_v5.sh`, `run_s1_seg.sh`, `run_s1_prep.sh`, `run_s1_v6.sh`,
and the sequential wrappers `run_s1_master*.sh` (Scroll 1). All are idempotent and disk-bounded: one raw crop at a time.

## Records
`RULES.md` — every bar declared before its run, every result as run, every incident. Append-only.
`stats/` — per-gate JSON, crop coordinates, registrations, model weights, the stroke test.
`review_sheets/s1/` — the registration overlays and per-crop evidence images.

## Known caveats that travel with the numbers
- The w028 reference is a model prediction, not read text: those AUCs measure agreement with that model.
- The Scroll 1 labels were hand-drawn on an earlier model's output and then read by papyrologists. The team's 2.4 µm model is trained
  on that same label family, so its 0.93–0.98 against them is partly circular; it is used as an alignment sanity check and an upper
  reference, not as ground truth.
- w028 text3/text4 were computed on 61 % of their area (rows deleted before topography); the repair was dropped for disk.

## Operational note: orphaned background jobs
Killing a driver shell does not kill the Python child it launched. Three v7 fits once ran concurrently on a 4-core box because two
earlier drivers had been stopped with `pkill -f <driver>.sh` while their children kept running, and progress stalled to a crawl.
Before relaunching any driver, check for survivors with `ps -eo pid,etime,args | grep "[s]cripts/"` and kill the PIDs, not the shell.
