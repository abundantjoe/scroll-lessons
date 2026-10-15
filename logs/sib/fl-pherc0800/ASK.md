# fl-pherc0800 ASK

Provenance: Project HERCULES | owner the owner | [id removed]

## ASK-FL-1 (2026-09-30 ~04:10Z): the organizer segments are too small; the specified grow path has no input. Which way?
- The bucket has 6 organizer tifxyz segments (all auto_grown_2025102x, overlapping bboxes). Their mesh-valid areas are 2.45, 1.93, 1.80, 1.68, 1.62 and 0.41 cm^2 (segments.json).
  - Every one is smaller than one 2 x 2 cm tile (4 cm^2, the prize area).
  - The 3 largest are running through the declared pipeline (DECL-FL-1 item 1: organizer segments if the bucket has them). They will yield about 0-3 tiles at valid >= 50 %.
- The fallback in the task ("vc_grow_seg_from_seed on the organizer surface-m7 prediction, >= 16 cm^2") has no input. PHerc0800/representations/ holds only predictions/lasagna/20250521135224-lasagna-20260419180421 (PHerc0800_cos.ome.zarr); there is no surface-m7.
- Growing from the lasagna representation, with an untested GrowPatch configuration, would be a new material and method. It needs its own declaration before data. So I have not started it.
- Question: after the organizer-segment tiles land, should PHerc0800 (a) stop there, or (b) move to a declared grow path, and on which representation and parameters?
