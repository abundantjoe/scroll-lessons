Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal: READCAL2-BANK-1 (material for DECL-READCAL2), declaration-ready text

READCAL2-BANK-1, the known-text material of DECL-READCAL2, declared before any picker, sealer or reader sees any of
its images (none exists outside /work/rc2 of the builder, who never opened one; logs/views.tsv has no entry).

1. Candidate list: logs/sib/readcal2/candidates.json (sha256 in REPORT.md), built by tools/sib/readcal2/cand.py
   (rules R1-R6 in its docstring), numbers only:
   - 2136 px windows on a 256 px grid of the organizer 9.362 um canvas (voxel size from the volume metadata.json).
   - Segments: tier E0 = clean controls w024, w047, w053; tier N = their non-base 3-D neighbours w023 w025 w026
     w037 w048 w049 w050 w051 w052 w054 w055 w056 w057 (all excluded from D2 training by the pairs0139 rule);
     PHerc0814 segments >= 184 vox from 46527 (JULY protocol match).
   - Coverage (mesh-valid, reference-covered, not base-excluded) >= 0.90 (0814 ribbons >= 0.75, flagged).
   - Base: no window SAME papyrus with any base-training trace (w028 w029 w030 w035 w039 w040 w041 w043 w044 w045
     w046; 0814 46527) by CORR-RETRACE-RULE form (a) OR (b); samples within 2 vox (point-to-surface) + 64 px halo
     are excluded from coverage.
   - Used windows: no 2-D overlap and no SAME papyrus with any HANDED-1/-R2/-R3B, PROBE-1/2/3, C3, D1 canary or D1
     blank window (2136 px squares, conservative).
   - Sealed: point-to-surface lower bound >= 128 vox from both SEAL-J-D1 w053 blank windows (minimum among the
     candidates 128.75 vox); J1-J5 are on PHerc0841.
   - RCPICK-1: coordinates unavailable; every E0 window (885) and every tier-N window SAME papyrus with E0 (240) is
     HELD (held_rcpick1), not a candidate, until the orchestrator publishes the 33 windows.
   Result: 4016 text candidates (0139 tier N 3720, 0814 296), 46 blank candidates (reference ink < 1 %), on 18
   segments. Text candidates carry coverage only: nobody ranks or filters them by ink or by any 9 um map.
2. Picker tiling: the 95 non-overlapping windows of picker_tiling (per segment, greedy in (y0, x0) order; geometry
   only). REF displays: tools/sib/readcal2/build_ref_windows.py --which picker_tiling --displays picker (state A,
   run_window margin 256 / step 20 / z_ascending / convention_sign +1, PHerc0139 CT mask-centroid centre curve that
   reproduces the PROBE-3 record; K_D2 1/2 INTER_AREA, raw 0-255, invalid 0; uuid names; manifest
   logs/sib/readcal2/refwin_manifest.json): 78 PHerc0139 windows built, state-A valid fraction 0.899-1.000 (median
   1.000), no mirror or flip, map singular values 0.987-1.003. 5 windows have an ambiguous normal sign (w023 (2304,
   1024), w023 (4608, 1280), w025 (2304, 256), w025 (4608, 256), w026 (4608, 512)) and are NOT shown (73 remain).
   The 17 PHerc0814 tiling windows have no state-A build (no 0814 centre curve); they are shown only after that
   build is declared, or dropped.
3. Picker (DECL-SEAL): one fresh picker of the frozen reader model, key sheet METRIC-HASH-12 first, the tiling
   displays in random order, references only; a window qualifies with >= 5 named letters; the bank is up to 8
   qualifying windows, <= 3 per segment, <= 2 per tier-N segment pair that are SAME papyrus with each other, taken in
   picker-output order. Blanks: the first 2 blank_candidates (ink ascending) with no 2-D overlap or SAME papyrus with
   a bank window, confirmed by the picker (rows N, <= 1 letter).
4. Seal: 3 fresh sealers (configs/briefs/sealer.txt) on the bank's state-A sigma-0 images; hercules.scorer.sealpos
   consensus (no human labels on these segments); age-encrypted; sha256 committed and pushed before any ladder image
   is built.
5. VOID: < 4 qualifying windows or S' < 20 -> READCAL-2 VOID on BANK-1 (record; no reads).
6. Hold-outs created: every bank window and every segment SAME papyrus with it (+16 vox) is excluded from any later
   training (D2, DEV-LOOP recipes) and from DEV windows.
Default: VOID if not executed by 2026-10-10.
