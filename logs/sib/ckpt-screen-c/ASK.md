Provenance: Project HERCULES | owner the owner | [id removed]

# ckpt-screen-c ASK (2026-09-26T21:35Z): P4-O third PHerc.1667 iteration

## A. Iteration choice is blocked: no card documents a held-out metric
The assignment (P4-O-PROVENANCE-2): "the iteration with the best documented held-out metric in the family table
(excluding the latest and iteration-0)". The candidates are iterations 1-4.
- The family table in every card (README sha256: it1 c872ad88..., it2 7ec327ed..., it3 31821460..., it4 5b5e1f77...,
  it5 197fb980...) has the columns "model | training segment(s) | label | tiles | effective epochs". It has no metric.
- The only per-iteration numbers are TRAINING losses ("Final train loss (`_epoch`)"): it1 0.4219, it2 0.4841,
  it3 0.5075, it4 0.5256. They are not held-out, and they fall with label sparsity and epochs (3,396 tiles x ~30 epochs
  for it1), so they would rank overfitting.
- The held-out segment l_5 appears only as a preview PNG (preview_l_5.png), which may not be viewed and is not a metric.
I have not chosen, and no inference has run. Please rule one of:
  (1) a named iteration;
  (2) a declared rule not based on results, e.g. the median label size it3 (15,286 tiles, ~7 epochs), or it4 (the
      largest label short of it5, 24,773 tiles);
  (3) a numbers-only held-out metric computed by a builder on l_5 against its official labels, if l_5 labels are
      public (declared before computing).

## B. Compute and data at the documented geometry
Card geometry: 62 layers, 256 x 256 window, stride 128 (card: "128 = 2x oversample"), 2 um class, run at 2.4 um level 0.
- Per 20 mm strip tile (8343 px + 128 px margin): 66^2 = 4,356 windows x 4.05 s (measured, p4o/smoke) = ~4.9 CPU-h at 4 threads fp32 per depth order.
- c0-c17 x r0-r5 = 108 tiles: ~530 CPU-h per order, ~130 h wall with me plus 3 sub-siblings. The pipeline is built and smoke-tested (tools/sib/ckpt-screen-c/p4o_tile.py), so it can start the moment the iteration is ruled.
- Data: 62 slices x 8343^2 = ~4.3 GB of level-0 CT per tile (~466 GB in all); streamed per tile, since disk is 26 GB.
Proposed order (please confirm or amend): rows r0-r1 first (DECL-P4-12 item 5), columns c10-c17 (title zone) together
with c5-c9 (known-text gate columns), then r2-r5. Gate reads need >= some c0-c8 tiles, so they are interleaved.

## C. Depth order
The relation of this surface volume's slice order to l_2's native order is undocumented (iterations 1-5 use l_2 native,
reverse_layers False; iteration-0 uses the reverse). I will follow whatever convention ckpt-screen-b declares for
iteration-5 on this same volume, so that the family materials match. If it is undeclared, I will use the
surface-volume index order (centre slice 54, slices 23..84), and record that as a choice made before any inference.

## D. Normalisation discrepancy (both are official)
The card training text reads clip(0, 200) then Normalize (/255). The card tiling snippet feeds raw uint8 .float() with
no scaling. Proposed: clip(0, 200)/255, the training convention and ckpt-screen-b's recorded choice.
