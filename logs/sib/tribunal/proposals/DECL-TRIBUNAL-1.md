Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal DECL-TRIBUNAL-1 (for the orchestrator to declare, amend or reject)

Implementation of the DECL-EMPNULL TRIBUNAL controls, code under `tools/sib/tribunal/tribunal/`
(sha256 of every module in `logs/sib/tribunal/results.json`, key `code_sha256`). Proposed text:

1. **Pre-read gate.** Before any image derived from a render record reaches a reader,
   `preread.preread_gate` runs on that record and `wiring.assert_images_certified` runs in
   `hercules.harness.jobs.make` (hook: `HARNESS-HOOK.md`). Checks, all fail-closed:
   provenance (mesh tree hash, stack content hash, shape), voxel size, window offset, mirror,
   depth order, slice index, re-trace, and map order for ink maps.
   Thresholds: shift search 12 px, offset tolerance 1 px (Chebyshev), minimum reference NCC 0.5,
   mirror margin 0.05, depth margin 0.02, slice margin 0.02, lags +-3, crop 256 px,
   voxel relative tolerance 1e-6.
2. **Re-trace rule form (correction to the literal rule).** Meshes are densified 5 x 5 as declared.
   A training segment is SAME papyrus if EITHER (a) the literal nearest-densified-vertex form
   or (b) the same bins computed with point-to-triangulated-surface distance gives
   >= 1000 window points within 2 vox and count[0,1) >= 2 count[2,3).
   Reason, measured: at the official 20-vox grid step the densified vertex spacing is 4 vox, so
   form (a) alone caught 4 of 200 random re-traces (1 of 50 and 0 of 50 in the stress runs).
   An exact re-trace offset by half a dense cell scores counts [0, 0, 20736], which form (a)
   calls NOT SAME. Form (b) caught 300 of 300, with 0 false alarms on neighbouring sheets
   3-20 vox away and on far same-sheet segments.
   The FL-09 certificate (SG 8) and RCBANK-style KD-tree work should use the same form.
3. **Voxel size.** The value used in the record, in the render command (`--voxel-size`), in the
   display key (`px_per_mm_image`) and in stack attributes must equal
   `voxel_size_from_metadata(metadata.json)`. The metadata file must also be sha256-pinned and
   recorded as `<volume url>/metadata.json`.
4. **Batch validity definitions** (DECL-EMPNULL leaves these open):
   - rows found is ABSOLUTE (>= 0.8 of reader-item panels answer rows = Y). Only letter recall
     is relative to the REF ceiling (>= 0.5 x ceiling). Set `rows_relative=True` if the
     declaration means both.
   - Letter recall: per reader, one-to-one same-kind matches within R = 250 canvas px (the
     scorer's R_PRIMARY), pooled over the canary's items, averaged over readers.
   - Bait rate: every named letter (known or unknown kind) on bait panels per 4 cm^2 of panel
     area, averaged over readers. A single firm naming by any reader voids the batch.
   - Mirror detection: fraction of (reader, mirror canary) answers that are correct; a missing
     answer is wrong. Readers answer per mirror-canary item "mirrored" or "normal" (a field the
     reader schema does not yet carry, so the brief needs it).
   - A batch with < 3 schema-valid readers, or without at least one positive canary, one bait and
     one mirror canary, is void.
   - I16 is evaluated after every batch on the running fraction: more than 1/3 void halts, so a
     void FIRST batch halts the run. Declare a minimum batch count if that is not intended.
5. **Empirical null (section 8.2).** For each candidate R: the non-text-order map, the NULL-arm map,
   and two half-pitch off-sheet re-renders (+ and - normal, labelled outward/inward).
   Pitch = median over R vertices of the centre-to-centre distance from the vertex's own m7 run
   to the nearest neighbouring m7 run along the unit normal (dt 0.25 vox, own run must touch
   |t| <= 4 vox, truncated runs excluded).
   Band tiles, >= max(20, 40 - 4) of them: same volume, |r - r_R| <= 10 % r_R, >= 192 vox from R,
   >= 144 vox from every exclusion cloud (J windows), >= 64 vox apart, chosen by seeded permutation.
   Status INSUFFICIENT, never silently fewer tiles, if < 40 in total, < 20 band tiles, or no pitch.
6. **Controls.** Canary blur: `cv2.GaussianBlur` with BORDER_REFLECT at sigma_mm x px_per_mm
   (identical to `metrics.pixel.sigma_eq`, verified to round-trip).
   Display: maps raw 0-255, CT 1-99 % linear, INTER_AREA only.
   Mirror glyphs E K R C G B N in DejaVu Sans (sha256 ae7b7855...7280), mirrored left-right.
   PNGs carry only IHDR/IDAT/IEND and use UUID names.

Not yet validated on real data: see `REAL-TRIB-1.md`. Until that gate passes, the thresholds in
item 1 are synthetic-calibrated only.
