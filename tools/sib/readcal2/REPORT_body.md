# readcal2 REPORT (READCAL-2 builder)

STATUS: {STATUS}

Builder only: no reader, picker or sealer ran; no image, rendered slice or map was opened, displayed or described;
no seal, key, scorer path or encrypted file was touched; nothing from PHerc0841 or an eligible scroll was fetched.
Official data only (s3://vesuvius-challenge-open-data, anonymous; HF scrollprize/ink_9um step-075000 sha256
e635558a...9cab; villa 41701aa); every download hashed in downloads.jsonl (257 objects). Every run is in runs.jsonl
(three container restarts killed jobs; each kill is logged and the job resumed from its caches).
Host: 4 vCPU Xeon 2.1 GHz with AMX (amx_bf16, amx_int8, amx_tile), 15 GB RAM, no GPU.

## Deliverables

| Item | Where | Validation (measured) |
|---|---|---|
| Declaration drafts | proposals/DECL-READCAL2.md, proposals/READCAL2-BANK-1.md | arms, metric, bars, guard rails, replication, default NO_GAIN; frozen D* untouched |
| Arms K_D2, EX, EXPL, MS, ROW, SIG2 | rc2lib.py, build_sheets.py, build_ref_windows.py, briefs/*_DRAFT.txt | 30 unit tests (tests/sib_readcal2_*_test.py) pass |
| Key sheet | rc2lib.keysheet | byte-exact regeneration of METRIC-HASH-12 (5da96bde...) |
| Exemplar / placebo sheets (0.15, 0.30, 0.45 mm) | sheets_manifest.json (build_sheets.py; PNGs rebuilt on demand) | two builds byte-identical; blob area within 1 % of each glyph; max blob-glyph IoU 0.54 (glyph-glyph up to 0.89); EX/EXPL mean 114.3/114.3; identical noise field per sigma |
| Noise model | noise_psd.json, noise_psd_2d.npz | C2-NT base maps of the 2 SEAL-J-D1 w053 blanks: mean {NOISE_MEAN}, variance {NOISE_VAR} u8^2; masked vs tile estimator median ratio 1.01 (0.91-1.08) |
| REF ladder / MS / ROW builders | rc2lib.ref_ladder_images, ms_images, row_letter_residuals | sigma-0 ladder equals hercules.display.builder path; blur second moment within 2 % of sigma; MS frames equal scorer DisplayMap convention |
| Bank candidates | candidates.json | {N_TEXT} text, {N_BLANK} blank, {N_TILING}-window picker tiling, {N_HELD} held (RCPICK-1) |
| REF renders of the tiling | refwin_manifest.json (arrays /work/rc2/refwin/arrays, displays /work/rc2/refwin/img) | {N_REFWIN} PHerc0139 windows, {N_REFIMG} picker images (state A, K_D2); valid 0.899-1.000; no flips; 5 ambiguous-sign windows excluded from the picker; 17 PHerc0814 not built |
| Scoring glue | score_rc2.py | synthetic end-to-end on score_decision; D1 ladder reproduces sigma_crit 0.30 (discrete) / 0.35 mm (interpolated) |

## Findings that matter for the orchestrator

1. Same-papyrus check reproduces the record: w047 vs base w045 / w046 = 1.34e5 / 1.38e5 vox^2 (RCBANK-1: 1.39e5 /
   1.44e5). New: w053 has ~1250 vox^2 within 2 vox of base w039 (pixel-excluded with halo; no w053 window is SAME).
2. RCPICK-1 cannot be reconstructed from the record (rcpick1_reconstruction.json: 310 / 161 / 490 candidates vs
   recorded 251 / 165 / 1731), so all E0 papyrus is held fail-closed (ASK 1). The bank therefore comes from tier N
   (non-base neighbours of the clean controls, excluded from D2) and PHerc0814 unless the 33 windows are published.
3. The centre curve for state A reproduces PROBE-3's recorded ranges exactly (centre0139.json).
4. The reference mapping (declared +10 offset) leaves the last ~7 canvas px of each axis without source; those
   pixels count as uncovered.
5. Blank base maps are not white noise: 82 % of their power lies below 0.01 cycles/px (> 1 mm), and one blank has
   3.8 % of pixels >= 150 (ink-like false positives). The exemplar noise reproduces the spectrum, not the blobs.
6. The multi-scale arm's quadrants are 1068 px at full scale, so MS shows the same pixels at 106.8 px/mm; the
   letter heights in its brief (214-427 px) follow from that.

## Known limitations (disclosed)

- Noise maps came from the organizer SV (official infer centre-crops slices 6..22: centre 14 vs surface 13.5), not
  from the -n 31 render path of D1; a half-voxel shift.
- Exemplar glyphs are a modern font (DejaVu Serif Bold), sharper than the reference; EX teaches degradation, not
  ancient letter forms.
- PHerc0814 windows reach only coverage 0.75-0.90 (ribbons); their state-A build needs a 0814 centre curve (not built).
- ASK 1-6 still unanswered at report time; the report follows their defaults.
- HANDED-1 windows (1 x 1 cm) were treated as 2 x 2 cm squares in the used-window test (conservative).
