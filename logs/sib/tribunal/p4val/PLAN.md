Provenance: Project HERCULES | owner the owner | [id removed]

# P4 anti-hallucination validation package (P4-L, DECL-P4-12; P4-O, DECL-P4-14)

Task: orchestrator dispatch 2026-09-26 18:48Z. Prize requirement: "demonstrate the letters and words are
not hallucinated - for example by validating on a held-out region with known ground-truth".

Code: `src/hercules/tribunal/p4val.py`. Tests: `tests/test_tribunal_p4val.py` (21 tests, synthetic
only; the test lines are invented Greek, not any edition). Locator: `tools/sib/tribunal/p4val_locate.py`
produces `known_text_map.json`. No image was opened, nothing was decrypted, and no reader saw anything.

## 1. Held-out ground truth: where the published final columns lie (numbers only)

- Source text: Nicolardi, Delattre, Del Mastro, Janko, Fowler 2024, *CErc* 54, 9-27, "portions of sixteen
  columns from the final part of the roll". It is not accessible in the project (DOSSIER 7.2 GAP). The
  orchestrator or owner supplies it later, as a JSON `{column_id: [line, ...]}` of the edited Greek
  (diacritics, underdots and brackets allowed; see section 2).
- **It must never enter any reader brief, key sheet or display.** It is held out from readers by
  construction; only the scorer sees it.
- Tile location, from the P4-B census letter counts (`census_a_summary.json`, orchestrator branch;
  unconfirmed counts, used only as a text/no-text profile) and the column pitch of 4 tiles (DOSSIER 4.2).
  The rebuilt census grid equals the DOSSIER 4.2 table.

| Published column (from the end) | strip-a tile columns | tolerance | note |
|---|---|---|---|
| col -1 | c7-c9 | c6-c10 | last text column: text-like counts at every height r0-r5 |
| col -2 | c3-c5 | c2-c6 | |
| col -3 | c0-c1 | c0-c2 | continues onto w028-037 c17-c20 (strip join, DOSSIER 4.1) |

- Alternative (UNCERTAIN, from DOSSIER H1/H2): if the r0-r1 block in c11-c13 is the short last column,
  every published column number shifts by one (col -1 = the block, col -2 = c7-c9, and so on). The
  scorer therefore aligns each tile against a WINDOW of candidate columns (default: the slot's column
  and both neighbours), and the null includes the same maximisation. The column assignment then emerges
  from the data, and the p-values remain valid under that search.
- Rows: published columns are full height, so every row r0-r5 of a slot is a known-text tile. Rows r6-r7
  (low counts) are the column foot or margin and are scored with the same method.
- P4-L gate tiles: c0-c8 (DECL-P4-12 item 2). P4-O: the same slots, per checkpoint (DECL-P4-14 item 3).

## 2. Scoring of reader outputs against the published text (`score_known_text`)

Input (on decrypted answers, run by the orchestrator only):
- per known-text tile, each reader's letters (displayed-image px, tile unrotated; the key gives the tile);
- the candidate published columns' lines.

1. Published text normalisation:
   - Greek letters are reduced to the 24 canonical kinds (all sigmas -> lunate, as the scorer does).
   - Diacritics are removed.
   - An underdotted letter counts as a visible trace.
   - Letters inside [ ] are editorial restorations: they are never targets, and a reader naming one scores
     nothing there.
   - Punctuation, editorial signs, spaces and numbers are dropped.
2. Reader letters are grouped into lines by y (a new line where the gap exceeds 0.6 x the median box
   height) and ordered by x.
3. Letter identity and position agreement:
   - Each reader line is aligned to a published line by Smith-Waterman: match +2 for identical kinds only,
     mismatch -1, gap -1, local.
   - Lines are mapped monotonically, top to bottom, with at most 3 published lines skipped between
     consecutive mapped reader lines. This is the alignment tolerance: it absorbs missed lines and
     partial columns.
   - Reversed letter order (a mirror) and reversed line order both lose most matches (tests: mirror
     < 1/2, reversed lines < 1/2).
4. Statistic: M = the total matched letters, maximised over the candidate columns. Also reported:
   precision M / named letters, the chosen column, and the line path.
5. Nulls (paired permutations, n = 1000 by default, seed 20260926; p = (1 + #null >= obs) / (n + 1)):
   - text shuffle: each candidate column's visible letters are permuted across its visible slots, keeping
     line lengths and letter frequencies. This controls letter frequency and alignment flexibility.
   - reader shuffle: the reader's own letter identities are permuted over its positions. This controls
     the reader's letter repertoire.
   - Both are computed per reader and pooled (the sum over readers).
6. Proposed validation bar (for the orchestrator to declare): the channel is VALIDATED on held-out
   known text when both hold:
   - pooled p_text < 0.01 and p_reader < 0.01 over the known-text tiles of one census batch;
   - at least half of the gate tiles have per-tile p_text < 0.05.
   Otherwise, letters it names in the title zone are not claimed.

## 3. Planted faults and canaries adapted to P4-L

- `check_l2_manifest`: checks the declared thresholds (T_mid 93, T_hi 203), the slab (48-60, centre 54,
  n 13) and the display rule (INTER_AREA 8343 -> 1068). Per tile it checks origin (0, 0) and extent,
  valid fraction >= 0.5, eligibility, file name, duplicates, and the builder's flags.
  - On the real l2 manifest at 3f0dcfc (72 of 160 tiles; numbers only): **all checks pass**
    (`known_text_map.json`).
  - Planted manifest faults (tests): 8 px origin, T_mid changed, slab off by one, duplicate tile, valid
    fraction below 0.5, swapped r/c. All are caught.
- `verify_l2_tile`: bit-exact recomputation of the P4-L display tile (slab max -> declared window ->
  0 outside mesh-valid -> INTER_AREA -> keyed rotation). It runs where the slab data are held (the builder).
  - Planted pixel faults on synthetic stacks: 8 px offset, 90-degree rotation, mirror, wrong threshold,
    slab off by one slice. All are caught; the clean tile passes.
- Canaries:
  - The known-text gate (`known_text_gate`, DECL-P4-12 item 2 / DECL-P4-14 item 3) is the positive
    control.
  - N0 (rotated) tiles are the null and bait.
  - The TRIBUNAL batch scorer (`validity.score_batch`) and I16 apply per batch unchanged.
  - The mirror canaries need the MIRROR-ADDENDUM brief field (still a proposal).

## 4. P4-O (DECL-P4-14) checks

- `check_p4o_provenance` enforces DECL-P4-14 item 1 and fails closed. A checkpoint may be eligible only
  with all of: a source URL, a 64-hex weights sha256, quoted documentation, and an explicit
  no-Paris-4/Scroll-1 statement. A documented Paris 4 exposure contradicts eligibility.
- Run on the three real provenance files (`p4o_provenance_check.json`; inputs in `p4o_inputs/` with
  sha256 and source commits): **all consistent**.
  - Eligible: PHerc.1667 iterations 0-5 (ckpt-screen-b).
  - Not eligible: ckpt-screen-a (ink_9um seed43, hecate 9.6 um, ink_3d_dino_guided: each documents
    Paris 4) and ckpt-screen-c (none).
- `check_p4o_manifest` runs once P4-O tile manifests exist (none yet). It checks:
  - the checkpoint sha256 is one of the eligible ones;
  - the strip-a grid (T 8343, origin (0, 0));
  - the raw 0-255 prediction display at 1068 px (a windowed display is rejected);
  - that native-voxel resampling is recorded;
  - per-tile origin, extent, valid fraction, duplicates and file name.
  Planted faults (tests): wrong checkpoint, windowed display, 8 px origin, no resampling record, wrong
  segment. All are caught.
- The pixel verifier for raw-prediction tiles is `tiles.verify_tile`, the same as P4-B, including the N0
  rotation. It is tested on synthetic arrays (REAL-TRIB-2 iv: 200/200 per fault, 0/200 clean false
  alarms).
- Held-out validation per checkpoint: `score_known_text` on that checkpoint's known-text tiles (section 2),
  with its own nulls. There is no pooling across checkpoints (DECL-P4-14 item 5).

## Integrity

Integrity: no issues.
- No image, tile, map or CT pixel was opened or viewed.
- Nothing was decrypted.
- The dossier's EXPECTED-TEXT section was not read.
- The published text was not obtained or used; the tests use invented lines.
