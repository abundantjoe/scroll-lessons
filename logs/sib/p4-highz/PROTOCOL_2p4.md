Provenance: Project HERCULES | owner the owner | [id removed]

# p4-highz protocol addendum: E2 at 2.4 um (orchestrator addendum under DECL-P4-12 / DECL-P4-6 / -A1 / -A2)

Written and pushed before any 2.4 um histogram, threshold or screen number exists. Same definitions as PROTOCOL.md except as listed. Numbers only; E2 PNG tiles are p4-l2's job (DECL-P4-12) and are not built here.

## Materials (2.4 um, level 0, 109 slices, centre 54, 2.4 um per slice)
- E2: 20260701183124-w010-027 `surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr`; grid = pairs0814b e2/grid.json (strip a: T = 8343, 9 x 21, origin (0, 0)); the 160 eligible tiles of pairs0814b e2/manifest.json (valid >= 0.5). Mesh-valid: 2.4 um tifxyz on 20260411134726, canvas px (i, j) -> vertex (i // 20, j // 20).
- Known-text control C2 (DECL-P4-12 item 1): 20260701183125-w028-037, same surface-volume name; grid = p4-tiles-b grid.json / manifest.json (P4-B strip b, T = 8301, 9 x 22, 171 eligible, same // 20 mask rule).
- Slabs: sheet 48..60 (13 slices, +-14.4 um, identical to p4-l2 params.json); gaps d = 25..50 (60..120 um): slices 4..29 and 79..104.

## Thresholds
- Rule as DECL-P4-6 item 2 and PROTOCOL.md: from C2's in-sheet voxels > 0, T_mid = p50, T_hi = p99.9, 6 % whole-chunk sample; written to thresholds_2p4.json and pushed before any per-tile 2.4 um number.
- Consistency with p4-l2 (which builds the E2 thin-slab tiles from the same control under its own pre-registered sampling, zeros not excluded): if p4-l2 has pushed its thresholds.json before mine is frozen, thresholds_2p4.json adopts p4-l2's T_mid and T_hi verbatim (so tiles and screen share one threshold) and my own values are reported alongside; otherwise mine are frozen and offered to p4-l2.

## Screen and reporting
- As PROTOCOL.md step 2, per E2 tile and per C2 tile; control tile p99 from C2 tiles.
- Title zone c10-c17 (DECL-P4-12) reported separately. Labelled-adjacency (p4-excl excl_a, union flag) reported per tile but does not exclude (DECL-P4-12 item 3).
- Rows r0-r1 first (DECL-P4-12 item 5).

## Sub-sibling
- One sub-sibling may run the C2 per-tile screen (stage_b.py tiles C2) in parallel with E2 here, after thresholds_2p4.json is pushed. Recorded in SUBSIBS.md before it starts.
