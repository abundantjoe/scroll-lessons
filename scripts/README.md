# Research pipeline scripts

These are the scripts that produced the release's results, at the paths the drivers and the lab notebook
([`docs/RULES.md`](../docs/RULES.md)) refer to. Superseded scripts (the w028 calibration era, the papyrus-subtraction route's extras,
old drivers, diagnostics and the E1 exploration code) are in [`archive/scripts/`](../archive/scripts). The reusable evaluation code is the
[`inkeval`](../inkeval) package; the research copies of the metrics here (`s1_judge.py`, `stroke_test.py`, `local_stroke_test.py`,
`ensemble_e.py`) are kept verbatim because the published numbers were produced by them; `check_toolkit_records.py` and
`tests/test_published.py` check that `inkeval` reproduces their judge, stroke and L records of E, v8, GP-R1, v7 and the team
comparator on the 13 judged crops exactly (stroke and L at the 4 decimals stored), and `check_reproducibility.py` that `inkeval`'s
`rank_mean` reproduces `ensemble_e.py`'s E maps of the 7 evaluation crops bit for bit. Every parameter is listed in [`docs/METHODS.md`](../docs/METHODS.md).

All scripts run from the repository root with the project venv (`python scripts/<name>`). Data live under `data/` (not versioned).
The original drivers are kept as they ran: `run_c1.sh` and `run_r1.sh` read the weights from `data/s1/v8_unet.pt` (and `run_c1.sh`
from `data/s1/gpr1.pt`; copy `models/*.pt` there first), `run_gpr1.sh` and `run_e.sh` wait for markers in `/tmp/v8.log` and
`/tmp/gpr1.log`, and `run_s1_seg.sh` needs the v5 weights, which are not released. In a fresh clone use `run_judge_crops.sh` and
`run_s1_prep.sh` ([`docs/REPRODUCE.md`](../docs/REPRODUCE.md)).

## Drivers (start here)

| driver | does | runtime |
|---|---|---|
| `run_judge_crops.sh SEG K0 K1 CROPS.json [names]` | prepare crops from the public CT and judge E, v8, GP-R1, v7, v1b and the team comparator with the released weights | ≈ 13.6–15.1 min per crop, estimated (same steps as `run_c1.sh`, `results/logs/c1.log`; no run of this driver is logged) |
| `run_s1_prep.sh SEG K0 K1` | prepare training crops (pooled depth stacks + classes) | 4.8–5.8 min per crop (`results/logs/s1prep.log`, `v8.log`) |
| `run_v8.sh`, `run_gpr1.sh`, `run_e.sh` | the original v8 / GP-R1 / E runs (training + one-shot judging) | training 3.1 h (11 458 s, `results/logs/v8.log`; the driver first prepares 7 crops) / training 2.3 h (8 334 s on shared CPUs, `results/logs/gpr1.log`) / minutes (not logged) |
| `run_v7_v6b.sh`, `run_v6c.sh`, `run_fix_veto.sh` | v7 fit, v6b, the v6c control, the veto repair | |
| `run_s1_seg.sh SEG K0 K1` | the original evaluation-crop driver (also runs the old baselines v0.1b, v1a/b, v2, v3, v5, v0.3p) | 14.8–18.7 min per crop (`results/logs/s1seg1b.log`, `s1seg2.log`) |
| `run_r1.sh` | reading run R1 on unread windows | |
| `run_c1.sh` | confirmation test C1 on untouched windows | 13.6–15.1 min per crop after the first (`results/logs/c1.log`) |

## Stages

| stage | script | in → out |
|---|---|---|
| inputs | `fetch_inputs.py` | public labels + overviews → `data/`, SHA-256 verified against `results/input_manifest.json` |
| | `manifest_inputs.py` | builds that manifest (with `--verify-remote`) |
| | `fetch_zarr_region.py` | one window of a 2.4 µm OME-zarr surface volume → local zarr (chunk presence verified) |
| reference | `s1_register_label.py` | Grand-Prize label (7.91 µm UV) → global scale + offset on the 2.4 µm canvas |
| | `s1_refine_reg.py` | per-crop translation of the registered label (`local_offset` in the crop file) |
| | `s1_local_reg_check.py` | residual-shift audit of the registration |
| crops | `s1_select_crops.py` | deterministic crop selection (densest non-overlapping labelled windows) |
| | `count_train_windows.py` | how many more windows a criterion admits (diagnostic for v8's data rule) |
| | `select_unread.py`, `select_confirm.py` | R1 unread windows; C1 untouched labelled windows |
| geometry | `topo_faces.py` | thick render → per-pixel sheet faces `k_top`, `k_bot`, crest, validity |
| | `residual.py` (`--edge-margin-mm 0.1`) | the judge mask J (on-sheet, damage, grains); also the v0.1b papyrus-subtraction score |
| | `s1_score.py --dump` | face-anchored depth stacks (11 offsets per face) and the v1 depth-template score |
| | `s1_ds_stack.py` | pooled 19.2 µm stack `ds8_x.npy` (22 depth channels + coverage) and classes `ds8_y.npy` |
| classes | `s1_judge.py` | registered label → text/blank classes; judges a score map (pixel AUC, legacy letter AUC) |
| | `build_noveto_y.py`, `rebuild_ds8_y.py` | pooled classes without / with the team-model veto |
| methods | `s1_v5.py` | 2-D U-Net (v5, v6b, v6c, v8): `train` / `predict` |
| | `gpr.py` | Grand-Prize-style 3-D→2-D detector (GP-R1): `train` / `predict` with 8-fold dihedral TTA |
| | `ensemble_e.py` | E: rank-mean of v8 and GP-R1, smoothed 0.08 mm |
| | `s1_v7.py`, `s1_v3.py`, `s1_v2.py`, `s1_template.py`, `v03p.py` | hand-built baselines v7, v3, v2, v1a/b templates, v0.3p |
| | `s1_team_comparator.py` | the team's published prediction on the crop (positive control) |
| evaluation | `stroke_test.py`, `local_stroke_test.py` | stroke AUC and local stroke test L (records in `stats/`) |
| | `release_stats.py` | crop-level bootstrap CIs, paired differences, label-swap null → `results/stats_*.json` |
| | `c1_analysis.py` | C1: the pre-registered prediction checked mechanically, shrinkage vs the evaluation set |
| | `d3_decompose.py` | post-hoc: ensembling vs smoothing in E (`--from-json` recomputes the statistics only) |
| | `n1_reading_null.py` | post-hoc: null for the reading-run agreement statistic |
| | `s1_summary.py` | per-segment summary of judge records |
| checks | `check_reproducibility.py` | regenerate v8/GP-R1/E from released weights and compare hashes |
| | `check_toolkit_records.py` | `inkeval` vs the published judge, stroke and L records of E, v8, GP-R1, v7 and the team comparator on the crops given |
| | `check_preregistration.py` | every declaration committed before its result (git history) |
| figures | `release_figures.py`, `render_reading.py`, `r1_team_view.py`, `s1_evidence.py` | `docs/figures/` |
| | `release_banner.py` | the README banner `docs/figures/banner.png` (E on held-out read crop 20231005123336/held2, verified letters outlined; numbers read from `results/`) |
| | `release_facts.py` | the headline numbers (evaluation set, C1, D3, N1, pre-registration order), generated from the results files (`python scripts/release_facts.py > results/FACTS.md`) |
