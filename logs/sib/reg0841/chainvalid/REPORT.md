Provenance: Project HERCULES | owner the owner | [id removed]

# chainvalid-prep (PHerc0841 CHAIN VALID, DECL-CHAINVALID): preparation report

STATUS: WAITING FOR GO. The preparation, including plan v2 on the stricter defaults, is complete. No ink map of PHerc0841 exists. Step 2 waits for the appended declaration, the chain2um gate report and the orchestrator's GO (ASK.md, including its 2026-09-26 update).

Numbers only. No image, render slice or map was viewed. No ink model has been run on 0841 data; the model was timed on synthetic random input only.

## 1. Organizer meshes mapped to 2.4 um with the frozen non-affine map (`map_meshes.json`)
The three organizer 9.366 um meshes were mapped with field_final.json (REG-0841-NA) on the organizer's own 2.4 um UV grid (c9 = (c2 + 10) N9/N2 - 10), so every pixel lines up with the organizer ink map and the human labels.

Kept nodes are >= 172 vox from the J points (see section 2).

Consistency check against the organizer's own 2.4 um meshes, per-node 3-D residual:

| segment | median, rescan vox | p95 | max | median, 9 um vox | max, 9 um vox |
|---|---|---|---|---|---|
| w00 | 5.07 | 8.68 | 11.9 | 1.30 | 3.05 |
| 214732 | 5.00 | 8.53 | 11.8 | 1.28 | 3.03 |
| 022814 | 5.52 | 9.42 | 11.9 | 1.41 | 3.05 |

(These are the 168-threshold values. The 172 re-run changes only the node set; see map_meshes.json.)

This matches the organizer-offset result of REG-0841-NA: about 1.3 vox (9 um), mostly in-surface.

## 2. J exclusion (>= 144 vox point-to-surface for every rendered sample)
- **Method.** Nodes are kept only if they are >= THR vox from the J points. Every kept node is then checked fail-closed with jsurf.JSurf (CORR-RETRACE-RULE): its point is grown by the -n 63 slab half-depth (8 vox, 9 um) plus the pixel interpolation margin (5.2 vox), and 10 x 10 node blocks whose box fails are re-checked node by node.
- **168 failed.** With THR = 168 the check found a minimum of 143.83 vox in 5 blocks, so the threshold was raised to **172**.
- **172 passes.** Minimum clearance **144.07 vox**, all >= 144 (`clearance_check.json`).
- **Benchmark renders.** The two CT-only benchmark renders were made before the change, from the 168 mesh. A per-node retro-check of those crops found a minimum of **145.8 vox** (`bench_render_clearance.json`), so nothing was rendered within 144 vox. Both renders are deleted.
- **Renderable area** (`area.json`): w00 1.224, 214732 1.233, 022814 1.000 cm^2.
- **Human labels inside it:** only on 214732, 943,443 px (353,304 ink, 590,139 blank; 0.054 cm^2), within 2 crops.

## 3. Chain (C5)
- **Render.** Official vc_render_tifxyz (villa 41701aa, built here with the unchanged setup_env / chain2um bootstrap) with -n 63, --flip-normals, 2048 px crops. --flip-normals matches the chain2um gate run, whose render fidelity was 0.999998.
- **Inference.** infer2um.py is a verbatim copy of the chain2um sibling's driver; hashes are in tools/sib/reg0841na/chain2um_copy/SOURCE.txt. Settings: reverse = start 0, 62 layers, clip 0..200, 256 px tiles, stride 128, Hann (official code), both orders.
- **Checkpoint.** ink_canonical_2um r152_3ddec_v2_l5_epoch13.ckpt, sha256 36dd0de8... (verified).
- **Levelling.** None (ASK 1).
- **Environment.** The bootstrap's `vesuvius` install fails under Python 3.13 (it needs 3.14; uv has no --ignore-requires-python there). infer2um.py does not import it. The chain2um package freeze was installed with --no-deps instead.

## 4. Cost measurements (no 0841 inference)
- **Render, CT only, 0841 outside T:** 512 x 512 x 63 in 14 s; 2048 x 2048 x 63 in 52 s (195 MB).
- **Model:** real weights on synthetic random input, 4 threads, AMX host. bf16 3.8 s/tile, fp32 5.1 s/tile (2 tiles each).
- **Plan, both orders:**
  - primary (2 label crops): about 0.95 h bf16 / 1.3 h fp32
  - secondary (6 crops): about 2.9 h bf16
  - all 47 crops: about 22 h bf16

## 5. Metrics and rule R (tested on synthetic data)
- **Metrics.** cv_eval.py, tested by tests/sib_reg0841_cv_eval_test.py. It uses the repo's `hercules.metrics.pixel`: AUC vs labels and r vs the organizer map on E = renderable & supervision, pooled over the evaluated crop cores. Bar: one order r_org_E >= 0.60 and AUC >= 0.90, and the other order AUC <= 0.60.
- **Rule R geometry** (`rule_r_geom.json`). With --flip-normals the render normal points toward the umbilicus proxy (the scroll-mask centroid; no official umbilicus exists for 0841): n.r_out < 0 on 98 % of nodes in all 3 segments and on 100 % in both label crops. Rule R on 0841 will be recorded as (sign -, winning order) once the run exists.

## 6. Plan v2 (2026-09-26, stricter defaults; `chainvalid_plan.json` version 2)
**Levelled chain.** The mapped meshes are levelled with src/hercules/geometry/level_mesh (step 20 vox, global median angle).
- Rotation: 81.9 / 81.9 / 82.9 deg (spread 3.1-3.5 deg).
- Edges within +-10 % of 20 vox: 94 / 95 / 90 %.

**Correspondence to the organizer canvas** (`levelmap.py`, `level_check.json`). Tested on 20,000 real renderable pixels per segment, the 3-D points agree to a median of 0.023 rescan vox (p99 1.2-1.4, max 5.7, at curved or edge quads). The pixel round trip is exact to 1e-11. Scoring samples the levelled map at the mapped organizer pixels (`cv_eval_lev.py`, synthetic test `tests/sib_reg0841_cv_eval_lev_test.py`).

**J clearance of the levelled meshes** (fail-closed, `clearance_check_lev.json`): minimum **144.29 vox**; all >= 144.

**Area.** Of the 943,443 labelled px on 214732, 922,836 (340,876 ink) map into renderable levelled pixels. They lie in 2 levelled crops, both on 214732: origin (0, 5248), size 1920 x 1672, and origin (1664, 5248), size 2048 x 1672.

**Compute, both orders:** primary about 0.73 h bf16 / 1.0 h fp32; secondary (6 crops) about 2.8 h bf16.

**Rule R geometry, levelled** (`rule_r_geom_lev.json`): unchanged, because levelling is det +1. n.r_out < 0 on 98 % of nodes, and on 100 % in both label crops.

**Runner:** `run_chainvalid_lev.sh primary <precision>`. It refuses without /work/cv/GO; the dry run was checked. The v1 plan and runner (unlevelled) are kept only as the alternative, not planned.

## What the orchestrator needs to do
Answer ASK.md. Give GO once the chain2um gate is reported; the runner then needs `touch /work/cv/GO`. Primary run: `tools/sib/reg0841/chainvalid/run_chainvalid_lev.sh primary <precision>` (plan v2).
