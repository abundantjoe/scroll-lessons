# baseline_dense PHerc0343P 20250511003658 (DECL-FL-7 item 3(ii))

Public dense-native 9 um ink model `dense_native_016000` (HF Nieuwlaar/ink9um-dense-native @ b894a04, sha256 d3d95dc4...) run with villa `vesuvius.ink_detection.inference.infer` (41701aa) on the 8.64 um organizer surface volume; scored by `tools/master/baseline_eval.py` at the shard crop positions (`build_data.py --stride 48 --max 600`). Recipe, checksums, window mapping and input mismatch: `recipe.json`. Log: `pipeline.log`.

| map | pixel AUC | pixel AP | tile AUC (p95) |
|---|---|---|---|
| dense016k_for_z11-28 | 0.7441 | 0.3939 | 0.6594 |
| dense016k_for_z3-20 | 0.7533 | 0.3968 | 0.6632 |
| dense016k_for_z6-23 | 0.7605 | 0.4154 | 0.6889 |
| dense016k_for_z9-26 | 0.7520 | 0.4057 | 0.6798 |
| dense016k_for_zavg | 0.7694 | 0.4529 | 0.6891 |
| dense016k_fwd | 0.7605 | 0.4082 | 0.6884 |
| dense016k_mean | 0.7441 | 0.3807 | 0.6761 |
| dense016k_rev | 0.5847 | 0.1822 | 0.5497 |
| dense016k_rev_z11-28 | 0.6446 | 0.2404 | 0.6002 |
| dense016k_rev_z3-20 | 0.5550 | 0.1550 | 0.5047 |
| dense016k_rev_z6-23 | 0.5789 | 0.1687 | 0.5465 |
| dense016k_rev_z9-26 | 0.6158 | 0.2103 | 0.5572 |
| dense016k_rev_zavg | 0.6135 | 0.2043 | 0.5621 |
| ink9um_s42_75k_fwd | 0.6539 | 0.3123 | 0.5812 |
| ink9um_s42_75k_mean | 0.6484 | 0.2779 | 0.5783 |
| ink9um_s42_75k_rev | 0.5352 | 0.1665 | 0.4995 |

FL-7 bars for the master model (reference only): pixel AUC >= 0.9, AP >= 0.5, tile AUC >= 0.85. Best dense recipe: `dense016k_for_zavg`.

Names: `dense016k_fwd/rev` = default center 17-layer window (slices 7-23) forward / reversed layer order; `_mean` = pixel mean of fwd and rev; `dense016k_for_z<a>-<b>` / `rev_z` = card z-windows mapped to 31 layers; `_zavg` = mean of the 4 windows; `ink9um_s42_75k_*` = released scrollprize/ink_9um hybrid_3d2d seed42 step-075000 on the same input, default window (comparator for the comparator; the full item-3(ii) record of that model is the baseline lane).

Scorer sanity (not committed as files): shard labels pasted onto the canvas score pixel AUC 1.0000 / AP 1.0000; a uniform random map scores 0.4993 / 0.1434 (= label prevalence).

- The public dense-native model is a comparator record (item 3(ii)); the bars in item 3(i)/(iii) apply to the master model, not to it. Its best recipe here (forward z-window ensemble) sits below all three bars on this scroll.
- Direction: forward (organizer layer order) beats reverse on every window (pixel AUC 0.74-0.77 vs 0.55-0.64), the same orientation sensitivity the model card reports (reversal collapses its benchmark to 0.51); the organizer volume therefore has the recto-facing order the model expects, and the fwd/rev mean is worse than forward alone.
- z-window ensemble (card recipe mapped to 31 layers): +0.009 pixel AUC, +0.045 AP over the default center window, in line with the card (+0.015 AUC on its benchmark).
- Input mismatch (recipe.json): 8.64 um / 116 keV / 31 layers vs the model native domain 9.362 um / 113 keV / 28 layers (8.4 % finer sampling, same slab thickness), fed natively without resampling as the card recipe does; PHerc0343P is outside every public ink_9um/dense label set.
- Labels are the organizers 2026 2.4 um pseudo-labels rescaled to the coarse canvas, not human marks; the reference PNG pseudolabel_organizers2026_q4.png shows them on the same canvas as the maps.
- No letters and no readings are claimed from any map here.
