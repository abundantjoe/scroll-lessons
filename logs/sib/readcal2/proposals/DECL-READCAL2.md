Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal: DECL-READCAL2 (reader-acuity programme) and READCAL2-BANK-1 (its material)

Drafted by the readcal2 builder for the orchestrator to declare. The builder never reads, views or scores. Every
number below comes from committed files in logs/sib/readcal2/ (hashes in REPORT.md).

## 0. Scope, and what this cannot change

- READCAL-2 is calibration on KNOWN TEXT only. Nothing it produces is evidence of letters on any scroll.
- Nothing here changes the frozen D* = K_D2, P* = configs/briefs/k_d2_task.txt / k_d2_pairs_task.txt or the frozen
  reader model (READCAL-FREEZE) for D3 or for any decision already declared. READCAL-2 can only define a NEW frozen
  display (D**) for LATER decisions, and only by a separate freeze record appended before those decisions' reads.
- No reader reads a map of an eligible scroll, a PHerc0841 window or any sealed set in READCAL-2.

## 1. Question and metric

Can in-context calibration raise the blind readers' acuity, measured as sigma_crit, without raising hallucination?

- sigma_crit(arm, model) = the Gaussian blur (mm) of the official reference at which the arm's summed mean C_net
  falls to 50 % of its sigma-0 value, linearly interpolated between ladder steps
  (tools/sib/readcal2/score_rc2.py interp_sigma_crit). The D1 discrete rule (largest ladder sigma >= 50 %) is
  reported beside it (D1-REF-RESULT gives 0.30 mm discrete, 0.35 mm interpolated for the same ladder).
- Secondary endpoints: summed mean C_net at 0.30 and at 0.45 mm.
- Letters become readable in a model map when sigma_eq(map) <= sigma_crit(reader). A reader gain therefore moves
  the bar every model map must meet (DECL-DEVLOOP FINALIST uses sigma_crit + 0.05 mm).

## 2. Arms (each = display + brief; drafts in tools/sib/readcal2/briefs/, hashed in REPORT.md)

All arms show the same REF ladder images of the same windows (state A, 2 x 2 cm, INTER_AREA 1/2, 1068 px, raw
0-255, invalid = 0, flat uuid names, new uuids per arm), preceded by the METRIC-HASH-12 key sheet (regenerated
byte-exact by rc2lib.keysheet; SIG2 uses the v2 sheet instead). Only the key/extra sheets and the brief differ.
The scorer already maps every sigma form to one letter kind (hercules.scorer.letters), so SIG2 is scored unchanged.

| Arm | Extra images | Brief |
|---|---|---|
| K_D2 | none | configs/briefs/k_d2_task.txt (frozen control, unchanged) |
| EX | 3 exemplar sheets (sigma 0.15, 0.30, 0.45 mm), after the key sheet | ex_task_DRAFT.txt |
| EXPL | 3 placebo sheets (same noise field, same labels, glyphs replaced by random stroke blobs of matched ink area and stroke width) | ex_task_DRAFT.txt (identical to EX: the reader cannot tell the arms apart) |
| MS | none; each window is 5 images: the K_D2 overview + its 4 quadrants at full scale (1068 px each) | ms_task_DRAFT.txt |
| ROW | none | row_task_DRAFT.txt (step 1 row baselines, step 2 letters along rows) |
| SIG2 | the both-sigma key sheet configs/briefs/keysheet_sigma2.png (sha256 164262e6...db438, DECL-P4-2-A2) REPLACES the METRIC-HASH-12 sheet | configs/briefs/k_d2_task_sigma2.txt (sha256 71b133f4...9f7bb) |

Exemplar / placebo sheets (tools/sib/readcal2/build_sheets.py, manifest logs/sib/readcal2/sheets_manifest.json):
the key sheet's 24 glyphs (DejaVu Serif Bold, lunate sigma) at 2.5 mm cap height, ink level 229 (RCPICK-1 median
99th percentile of reference displays), background and noise from the measured blank base maps (noise_psd.json:
C2-NT base maps of the two SEAL-J-D1 w053 blanks, mean 76.8, variance 501 u8^2, 82 % of power below 0.01
cycles/px), Gaussian blur at canvas resolution then INTER_AREA 1/2, i.e. the REF-ladder operator. Placebo blobs:
area within 1 % of each glyph's, max IoU with any glyph 0.54 (glyph-glyph pairs reach 0.89); sheet mean brightness
EX 114.3 vs EXPL 114.3.

Reader model factor: M1 = the frozen reader model (READCAL-FREEZE), M2 = <one other model version, named by the
orchestrator before declaration>.

## 3. Material (READCAL2-BANK-1)

1. Candidates: logs/sib/readcal2/candidates.json (numbers only; builder rules R1-R6 in tools/sib/readcal2/cand.py):
   2136 px windows on a 256 px grid of the organizer 9.362 um canvas, coverage >= 0.90 (0814 ribbons >= 0.75,
   flagged), not SAME papyrus with any base-training trace (CORR-RETRACE-RULE forms (a) OR (b)), no pixel within
   2 vox of a base trace (+64 px halo), no 2-D overlap and no SAME papyrus with any earlier HANDED / PROBE / C3 /
   canary / D1-blank window, point-to-surface lower bound >= 128 vox from the SEAL-J-D1 blank windows (J1-J5 are on
   PHerc0841). Text candidates carry coverage only; they are never ranked or filtered by ink.
   Result (candidates.json): 4016 text candidates on 18 segments (0139 tier N 3720, 0814 296 flagged ribbon), 46
   blanks, a 95-window picker tiling; 1125 windows held (item 2). Full declaration text: READCAL2-BANK-1.md.
2. RCPICK-1 hold: the 33 READ-CAL picker windows' coordinates are not in the repo; the recorded rule does not
   reproduce (rcpick1_reconstruction.json: 310 / 161 / 490 candidates vs recorded 251 / 165 / 1731). Every E0
   (w024 / w047 / w053) window and every tier-N window SAME papyrus with E0 is therefore HELD (candidates.json
   held_rcpick1) until the orchestrator publishes the 33 (segment, y0, x0) or declares that one picker's view of a
   reference image does not disqualify fresh readers (the DECL-D1-A4 argument). Default: held.
3. Picker: one fresh picker (DECL-SEAL; key sheet first; references only) sees the picker_tiling windows (a
   non-overlapping geometric tiling of the candidates, built by build_ref_windows.py --which picker_tiling
   --displays picker) and names letters; a window qualifies with >= 5 named letters; take up to 8 (<= 3 per
   segment) in picker-output order. Blanks: the 2 first blank_candidates confirmed by the picker (rows N, <= 1 letter).
4. Seal: 3 fresh sealers (configs/briefs/sealer.txt) on the qualifying windows' state-A sigma-0 images; consensus
   hercules.scorer.sealpos (no human labels exist on these segments, so seal positions are sealer consensus);
   age-encrypted, hash committed before any ladder image is built. S' = seal letters over the bank.
5. VOID: fewer than 4 qualifying windows or S' < 20 -> READCAL-2 is VOID on this bank (record and stop; no reads).

## 4. Reads

- Cell = (arm, model, sigma), sigma in {0, 0.15, 0.30, 0.45, 0.60} mm; 3 fresh readers per cell, each reading all
  bank windows + both blanks of ONE cell in random order, sealed-output mode, DECL-HARNESS-A1 audit.
- Stage 1: model M1, all 6 arms x 5 sigmas = 90 readers. Stage 2: model M2, same = 90 readers. Stage 2 runs only if
  stage 1 audits VALID; its results never change stage 1's verdict.
- A reader never sees the same window at two sigmas and never sees two arms.

## 5. Scoring (tools/sib/readcal2/score_rc2.py, unit-tested; hash it in a METRIC-HASH entry before any read)

- One hercules.scorer.score.score_decision per (model, sigma) over the 5 arms (METRIC-HASH-0 unchanged: radius
  250, identity-permutation null, 5000 permutations, seed 20260924). MS answers are merged per window
  (merge_ms_answer: 5 images -> canvas px, same identity within 60 px = one letter); ROW answers are split
  (split_row_answer) and scored on letters only; row-baseline residuals are reported, not scored.
- CHANCE per arm, computed without extra readers: the arm's namings scored against the next bank window's seal
  (cyclic, chance_maps); CHANCE C_all at R250.
- Contrast X vs K_D2 (same model): T = sum over sigma in {0.30, 0.45} of (mean X - mean K_D2) per-reader summed
  C_net; exact one-sided reader-relabelling p over all 400 relabelings (permutation_contrast; minimum p 1/400).
  Family = {EX, EXPL, MS, ROW, SIG2} within a model, Holm step-down at alpha 0.05 (holm()).

## 6. Bars (per arm X, within model M1; M2 reported, and decides only its own model's freeze)

GAIN_PENDING_REPLICATION iff all hold:
 a. sigma_crit(X) >= sigma_crit(K_D2) + 0.075 mm (half a ladder step);
 b. summed mean C_net of X at 0.30 and at 0.45 mm each >= K_D2's;
 c. contrast X vs K_D2 rejected by Holm (family of 5, alpha 0.05);
 d. hallucination guard rails: mean blank namings per reader (all sigmas) <= K_D2's + 1/3; CHANCE C_all <= K_D2's
    + 1.0; precision C_all(R250) / namings at 0.30 and 0.45 >= K_D2's - 0.10;
 e. for EX only: gain(EX) > gain(EXPL) in sigma_crit AND contrast EX vs EXPL p < 0.05 (the placebo control; if
    EXPL itself passes a-d, the effect is priming and EX cannot pass).
Otherwise NO_GAIN. SG bars are untouched; firm-letter rates are reported only.

## 7. Replication before any freeze (PROBE-3 precedent)

An arm with GAIN_PENDING_REPLICATION is re-tested once on a FRESH bank (READCAL2-BANK-2: new windows under the same
rules, sharing no papyrus with BANK-1) with the arm, K_D2 and (for EX) EXPL at sigma {0, 0.30, 0.45}, 3 fresh M1
readers each. REPLICATED iff bars a (on this 3-step ladder), b, d (and e) hold again and T > 0 with p < 0.05.
Only then may a freeze record READCAL2-FREEZE define D** (= the arm's display + brief, hashed) for decisions
declared AFTER it; every decision declared before it keeps D* = K_D2.

## 8. Default

Missing, void or ambiguous at 2026-10-10: NO_GAIN; D* = K_D2 stays the only frozen display; sigma_crit stays
0.30 mm (D1-REF-RESULT).

## 9. Costs and risks (disclosed)

- 180 reader agents for the full factorial (90 per model), plus 1 picker, 3 sealers, and up to 27 replication
  readers. A lean alternative (declare instead if budget binds): stage 1 only, sigma {0, 0.30, 0.45, 0.60}
  (72 readers), sigma_crit interpolated on that ladder.
- Exemplar glyphs are font shapes, not ancient hands: EX teaches degradation, not letter forms; its 0.30 mm sheet is
  sharper than REF030 because the font starts sharper than the reference.
- The exemplar noise is a stationary Gaussian with the blank base-map spectrum and variance; real base-map blanks
  also carry sparse ink-like blobs (3.8 % of pixels >= 150 on one blank), which the model does not reproduce.
- The EX/EXPL brief is identical and neutral ("ink shapes"), so the placebo is blind; the sheets differ only in shape.
