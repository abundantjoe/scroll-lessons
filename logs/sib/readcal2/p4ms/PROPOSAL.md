Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal: DECL-P4-SCALE (READCAL-style display-scale check on P4-L known-text columns c0-c8)

Drafted by the readcal2 builder for the orchestrator to declare. The builder never reads, views or scores.
Code: logs/sib/readcal2/p4ms/p4ms.py (tests: tests/sib_readcal2_p4ms_test.py, 7 pass).

## 0. Question and what it cannot do

Which display scale lets fresh blind readers name the most letters that are consistently perceived (agreed between
independent readers) on KNOWN-TEXT papyrus of Paris 4, net of the N0 null? The answer fixes the display scale of
later title-zone reads, declared before those reads. It is calibration only:
- nothing read here is evidence of a title or of any word;
- no expected words anywhere: no brief, key, scorer or report uses a lexicon, a known text, a title hypothesis or a
  letter prior beyond the key sheet; tiles are never compared with any transcription; readers are not told what the
  papyrus says;
- the title zone (c10-c17) is never shown in this check.

## 1. Scales (p4ms.py; same canvas, same channel, same value map; downscale only, INTER_AREA, 1068 px)

| Scale | Window | px/mm | Letters 2-6 mm appear as |
|---|---|---|---|
| S4 | 2 x 2 tiles = 16686 canvas px (4 x 4 cm) | 26.7 | 53-160 px |
| S2 | the existing tile, 8343 px (2 x 2 cm) | 53.4 | 107-320 px |
| S1 | one tile quadrant, 4171/4172 px (1 x 1 cm) | 106.8 | 214-641 px |

S2 images are byte-identical to the existing P4-L tile PNGs (verify_s2_against_manifest must report all_equal
before any read; otherwise stop).

Validated on the real material (p4l2_verify.py; verify_l2.json, verify_l2s.json; numbers and hashes only):
[line withheld: prize-candidate detail under review]
  L2S r0 c0 and r1 c1 (4 of 4). The channel source is p4-l2's own l2.py (sha256 recorded), mesh hashes checked
  against the L2 manifest.
- Smoke on block (r0-r1, c0-c1): 1 S4 image (16686 px, 26.70 px/mm, 91 % valid) and 16 S1 zooms (4171/4172 px,
  106.81/106.78 px/mm, 57-100 % valid), 0 skipped; 6.5 min with 16 range threads. Images stay in /work, unopened.

## 2. Material

- Channel and value map: P4-L L2 (DECL-P4-12 item 1: level-0 max over slices 48..60, global T_mid 93 / T_hi 203).
  The global map makes S4, S2 and S1 differ ONLY in scale. If L2 fails its own known-text gate (DECL-P4-12 item 2),
  use L2S (DECL-P4-12-A2) instead, and disclose that its per-window stretch then differs between scales.
- Blocks: 2 non-overlapping 4 x 4 cm blocks (all 4 tiles eligible) in columns c0-c8, one in rows r0-r1 and one in
  r2-r7 (the DECL-P4-12-A2 row bands), drawn by seed 20260926 among eligible blocks, by geometry only (never by any
  pixel value, census count or prior read). Their 8 tiles and 32 quadrants are the S2 and S1 material: identical
  papyrus at every scale.
- Exclusions: no block may contain a tile already read in any P4 batch (fresh papyrus for fresh readers), a
  labelled-adjacent tile (excl_a union flag), or any c9+ tile.

## 3. Reads

- Readers: the P4 reader model (DECL-P4-2-A1), fresh, sealed-output mode (DECL-HARNESS-A1), key sheet v2
  (configs/briefs/keysheet_sigma2.png) first, task text k_d2_task_sigma2t with only its px/mm and "about N-M px
  tall (2-6 mm)" phrase set per scale (26.7 / 53.4 / 106.8 px/mm; 53-160 / 107-320 / 214-641 px).
- Arm S4: 3 readers, each reads both block images. Arm S2: 3 readers, each reads all 8 tiles. Arm S1: 6 readers, 3 per
  block, each reads that block's 16 zooms. Image order random per reader; uuid names; flat folders.
- N0 per scale: every session also reads N0 images of its own scale = its scale's images of the OTHER block rotated
  90 degrees (S4: 1, S2: 2, S1: 4 per session), never shown unrotated in that session. N0 is scored like material.
- Total 12 readers.

## 4. Scoring (hercules.scorer, unchanged code)

- Canvas coordinates via the p4ms key (scale_canvas_px_per_image_px, y0, x0; the scorer's half-pixel convention).
- Agreement radius 1.404 mm = 586 canvas px at 417.13 px/mm (the physical radius of the PROBE/SG 150 px rule at
  9.362 um), identical at every scale.
- Per scale and block: agreed letters (same identity within the radius from >= 2 of 3 readers,
  hercules.scorer.consensus) and the between-reader identity-shuffle p (2000 permutations); per reader: namings,
  and "agreed namings" (namings matched by >= 1 other reader of the same arm).
- N0 per scale: agreed letters and namings per reader on the rotated images.
- Primary per scale: NET = agreed letters summed over both blocks minus N0 agreed letters (rescaled to the same area).
- Reported only: cross-scale convergence (agreed letters of one scale matched by an agreed letter of another scale at
  the same canvas place with the same identity), per row band.

## 5. Bars

S2 (the current display) is the default. A scale X in {S4, S1} replaces S2 for later title-zone reads iff all hold:
 a. NET(X) >= NET(S2) + max(3, 0.2 NET(S2));
 b. identity-shuffle p < 0.05 for X in at least one block;
 c. N0(X) agreed letters <= 1 and N0 namings per reader of X <= those of S2 + 1;
 d. X passes a-c in BOTH row bands' blocks in direction (NET(X) >= NET(S2) per block).
If both S4 and S1 pass, the larger NET wins; exact ties keep S2. If S2 itself shows NET <= 0 or no block with
p < 0.05, record "no scale informative on c0-c8" and keep S2 (nothing is interpreted in the title zone from this).

## 6. Default and scope

Default: S2 stays. The result changes only the display scale of P4 title-zone reads declared after it; it changes no
bar, null or candidate rule of DECL-P4-2 / -5 / -12, and nothing for First Letters decisions (READCAL-FREEZE D*).

## 7. Costs and limits

- 12 readers + the builder run (S4: 2 images; S2: reuse; S1: 32 images; each S4/S1 window needs its canvas channel:
  level-0 max over 13 slices, ~4.5 GB of range reads per block, both blocks ~9 GB streamed, nothing stored whole).
- 2 blocks is small; the bars are directional, and the result is a display choice, not evidence.
- S1 zooms show a letter-sized context only; readers may lose row context (why S1 must also beat S2, not just exist).
